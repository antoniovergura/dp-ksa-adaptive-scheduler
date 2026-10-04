#!/usr/bin/env python3
"""Sequential campaign on verified public fixtures; reports are non-DP diagnostics.

Run from poc with .venv/bin/python. No production mechanism or prompt is changed.
Each invocation creates a new output directory and explicitly scoped accounts.
Never resume by silently resetting a privacy account on confidential data.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import logging
import math
import platform
import random
import shutil
import subprocess
import threading
import time
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

from dotenv import load_dotenv

from benchmark_salary_demo import release_trials, verify_corpus
from benchmark_ticket_demo import conditional_trials, sensitive_token_sets
from core.calibration import calibra
from core.cloud import CloudGenerator
from core.dataset import DatasetLoader
from core.engine import LocalNeuralEngine
from core.etichette import PatternRiferimento
from core.model_config import DEFAULT_LOCAL_MODEL_CONFIG, percorso_modello_predefinito
from core.pipeline import RequestConfig, run_request
from core.privacy import DP_KSA_Filter, deriva_sigma_da_budget
from core.scheduler import AdaptiveScheduler
from core.telemetry import LangfuseTracer
from core.telemetry_hw import snapshot as hw_snapshot

ROOT = Path(__file__).resolve().parent
ORDER_SEED = 20260919


def clean(value):
    """Keep missing measurements explicit and write strict JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean(v) for v in value]
    return value


def save(path, data):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(clean(data), ensure_ascii=False, indent=2,
                                    allow_nan=False), encoding='utf-8')
    temporary.replace(path)


class ObservedEngine:
    """Record token counts and actual durations, without changing generation."""

    def __init__(self, engine):
        self.engine = engine
        self.records = []

    def limita_contesto(self, *args):
        return self.engine.limita_contesto(*args)

    def genera_bozza(self, *args, **kwargs):
        output = self.engine.genera_bozza(*args, **kwargs)
        self.records.append(asdict(output))
        return output


class ObservedClient:
    """Record provider usage/status, never credentials or outbound raw documents."""

    def __init__(self, client):
        self.client = client
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        start = time.time()
        record = {'started_at': start, 'max_tokens': kwargs.get('max_tokens')}
        try:
            result = self.client.chat.completions.create(**kwargs)
            record.update(model=result.model,
                          usage=result.usage.model_dump() if result.usage else None,
                          finish_reason=result.choices[0].finish_reason)
            return result
        except Exception as exc:
            record.update(error_type=type(exc).__name__,
                          status_code=getattr(exc, 'status_code', None))
            raise
        finally:
            record['elapsed_ms'] = (time.time() - start) * 1000
            self.calls.append(record)


def schedule(config):
    return AdaptiveScheduler(max_tokens=config.max_tokens).schedule(
        [config.prompt_token_budget] * config.candidates, config.epsilon,
        delta=config.delta, latenza_rete_ms=config.rtt_ms,
        latenza_massima_ms=config.sla_ms, tempo_cloud_ms=config.cloud_ms,
        tok_per_sec_prefill=config.prefill_tps,
        tok_per_sec_generazione=config.generation_tps, fixed_n=config.fixed_n,
        k_sforamento=config.k_sforamento, e2e_cloud_ms=config.e2e_cloud_ms)


def make_account(epsilon, delta, calls):
    """Preallocate cumulative limits; per-call noise remains calibrated to epsilon."""
    return DP_KSA_Filter(
        epsilon=epsilon * calls, delta=delta, delta_budget=(calls + 1) * delta,
        sigma=deriva_sigma_da_budget(epsilon, epsilon / 2, epsilon / 2, delta),
        epsilon_find_best_k=epsilon / 2, epsilon_top_k_ptr=epsilon / 2)


def make_jobs(base, ticket_cases, salary_cases):
    """Predeclare comparisons before looking at outcomes; randomize within blocks."""
    jobs = []

    def add(phase, corpus, case, config, variant, repeats):
        for repeat in range(repeats):
            jobs.append({'phase': phase, 'corpus': corpus, 'case': case,
                         'config': config, 'variant': variant, 'repeat': repeat})

    for corpus, case in [('ticket', ticket_cases[0]), ('salary', salary_cases[0])]:
        for sla in (5000, 15000, 30000):
            for n in (None, 5, 10, 20, 40):
                add('C3_offline', corpus, case, replace(base, sla_ms=sla, fixed_n=n),
                    'adaptive' if n is None else f'fixed_{n}', 5)
    squad_case = {'id': 'super_bowl', 'query': 'Who won Super Bowl 50?',
                  'expected_answer': 'Denver Broncos'}
    for epsilon, delta in [(1.0, 1e-4), (8.0, .01)]:
        add('C1_cloud', 'squad', squad_case,
            replace(base, epsilon=epsilon, delta=delta, sla_ms=60000), 'adaptive', 5)
    for case in ticket_cases[:2]:
        add('C1_cloud', 'ticket', case,
            replace(base, epsilon=8, delta=.01, sla_ms=60000), 'adaptive', 5)
    # Match the preliminary high-budget condition, without changing it in response to utility.
    for sla in (15000, 30000):
        for n in (None, 20, 40):
            add('C3_cloud', 'ticket', ticket_cases[0],
                replace(base, sla_ms=sla, fixed_n=n),
                'adaptive' if n is None else f'fixed_{n}', 5)
            add('C3_high_cloud', 'ticket', ticket_cases[0],
                replace(base, epsilon=8, delta=.01, sla_ms=sla, fixed_n=n),
                'adaptive' if n is None else f'fixed_{n}', 5)
    for case in ticket_cases[2:]:
        add('D_cloud', 'ticket', case,
            replace(base, epsilon=8, delta=.01, sla_ms=60000), 'adaptive', 5)
    return jobs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cloud', action='store_true')
    parser.add_argument('--trials', type=int, default=500)
    args = parser.parse_args(argv)
    if args.trials < 1:
        parser.error('trials must be positive')
    args.output.mkdir(parents=True, exist_ok=False)
    out = args.output
    started = time.time()
    load_dotenv(ROOT / '.env')
    # Exceptions may contain service internals; record only sanitized status metadata.
    logging.disable(logging.CRITICAL)
    corpora, manifests = {}, {}
    for name, folder in [('ticket', 'ticket_demo'), ('salary', 'azienda_demo')]:
        corpora[name], manifests[name] = verify_corpus(ROOT / 'docs' / folder)
    corpora['squad'] = DatasetLoader().as_corpus()
    ticket_cases = json.loads((ROOT / 'docs/ticket_demo/cases.json').read_text())
    salary_cases = json.loads((ROOT / 'docs/azienda_demo/cases.json').read_text())
    model = percorso_modello_predefinito()
    if not model.is_file():
        raise FileNotFoundError('Campaign requires the existing model; no implicit download')
    metadata = {
        'started_at': started, 'order_seed': ORDER_SEED, 'status': 'running',
        'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'source_hashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [Path(__file__), *sorted((ROOT / 'core').glob('*.py'))]},
        'platform': platform.platform(), 'machine': platform.machine(),
        'python': platform.python_version(), 'model_sha256': hashlib.file_digest(
            model.open('rb'), 'sha256').hexdigest(),
        'model_config': asdict(DEFAULT_LOCAL_MODEL_CONFIG),
        'corpus_counts': {name: len(c.documents) for name, c in corpora.items()},
        'corpus_hashes': {name: hashlib.sha256(
            '\n'.join(d.id for d in c.documents).encode()).hexdigest()
            for name, c in corpora.items()},
        'packages': {name: importlib.metadata.version(name)
                     for name in ('llama-cpp-python', 'numpy', 'openai', 'langfuse')},
        'scope': 'Public/synthetic diagnostic experiment; reports and hardware traces are NOT DP',
        'cloud_quality_offline': None, 'hardware_period_ms': 5000,
        'calibration_note': 'Current calibration separates prefill using the fixed heuristic',
        'network_note': 'Text byte counts are not actual network bytes; cloud TTFT unavailable',
    }
    save(out / 'metadata.json', metadata)
    hardware_process = None
    hardware_thread = None
    hardware_stop = threading.Event()

    def linux_hardware_reader():
        # Keep explicit source/unit labels; use the analysis-compatible container.
        with (out / 'hardware.jsonl').open('w') as handle:
            while not hardware_stop.is_set():
                reading = hw_snapshot().to_dict()
                sample = {'received_at': reading['timestamp'], 'source': 'linux_snapshot',
                          'raw_snapshot': reading,
                          'temp': {'cpu_temp_avg': reading['cpu_temp_c'],
                                   'gpu_temp_avg': reading['gpu_temp_c']},
                          'memory': {}}
                for field, source in [('cpu_power', 'cpu_watt'), ('gpu_power', 'gpu_watt')]:
                    if reading[source] is not None:
                        sample[field] = reading[source]
                for field, source in [('ram_usage', 'ram_used_gb'),
                                      ('ram_total', 'ram_total_gb')]:
                    if reading[source] is not None:
                        sample['memory'][field] = reading[source] * 1024 ** 3
                for field, source in [('cpu_active_ratio', 'cpu_util_pct'),
                                      ('gpu_active_ratio', 'gpu_util_pct')]:
                    if reading[source] is not None:
                        sample[field] = reading[source] / 100
                try:
                    frequency = subprocess.run(
                        ['nvidia-smi', '--query-gpu=clocks.gr', '--format=csv,noheader,nounits'],
                        capture_output=True, text=True, timeout=2, check=True)
                    sample['gpu_freq_mhz'] = float(frequency.stdout.splitlines()[0])
                except (OSError, ValueError, IndexError, subprocess.SubprocessError):
                    pass
                handle.write(json.dumps(clean(sample), allow_nan=False) + '\n')
                handle.flush()
                hardware_stop.wait(5)

    def hardware_reader():
        with (out / 'hardware.jsonl').open('w') as handle:
            for line in hardware_process.stdout:
                try:
                    sample = json.loads(line)
                    sample['received_at'] = time.time()
                    handle.write(json.dumps(sample) + '\n')
                    handle.flush()
                except json.JSONDecodeError:
                    continue

    if shutil.which('macmon'):
        hardware_process = subprocess.Popen(['macmon', 'pipe', '-i', '5000'],
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.DEVNULL, text=True)
        hardware_thread = threading.Thread(target=hardware_reader, daemon=True)
        hardware_thread.start()
    elif platform.system() == 'Linux':
        hardware_thread = threading.Thread(target=linux_hardware_reader, daemon=True)
        hardware_thread.start()
    accounts = {}
    observed_client = None
    try:
        phase_start = time.perf_counter()
        engine = ObservedEngine(LocalNeuralEngine(model_path=model))
        metadata['model_setup_ms'] = (time.perf_counter() - phase_start) * 1000
        calibration = calibra(engine)
        metadata['calibration'] = asdict(calibration)
        metadata['calibration_outputs'] = engine.records[:]
        base = RequestConfig(epsilon=4, delta=1e-4, prefill_tps=calibration.prefill_tps,
                             generation_tps=calibration.generation_tps)
        offline = CloudGenerator(offline=True)
        cloud, tracer = None, None
        if args.cloud:
            from openai import OpenAI
            configured = CloudGenerator()
            if not configured.api_key and not configured.base_url:
                raise RuntimeError('Cloud requested but credentials/endpoint are missing')
            observed_client = ObservedClient(OpenAI(
                api_key=configured.api_key or 'not-needed', base_url=configured.base_url,
                max_retries=0, timeout=60))
            cloud = CloudGenerator(client=observed_client, model=configured.model)
            metadata['provider'] = {'model': configured.model,
                                    'host': urlsplit(str(observed_client.client.base_url)).hostname,
                                    'timeout_s': 60, 'max_retries': 0}
            probe_start = time.perf_counter()
            probe = cloud.probe()
            metadata['probe'] = asdict(probe)
            metadata['cloud_probe_ms'] = (time.perf_counter() - probe_start) * 1000
            if probe.errore:
                metadata['cloud_blocked'] = 'Initial public probe failed'
                cloud = None
            else:
                tracer = LangfuseTracer()
                metadata['langfuse_active'] = tracer.is_active
                metadata['langfuse_capture_sensitive'] = tracer.capture_sensitive
        print('SETUP', json.dumps({'calibration': asdict(calibration),
                                   'probe': metadata.get('probe'),
                                   'cloud_ready': cloud is not None}), flush=True)
        save(out / 'metadata.json', metadata)
        # Decision-only C4: same public caps; no retrieval or filter invocation.
        decisions = []
        for mode in ('default', 'calibrated'):
            for sla in (1500, 5000, 15000, 30000):
                config = replace(base, sla_ms=sla)
                if mode == 'default':
                    config = replace(config, prefill_tps=250, generation_tps=50)
                decisions.append({'mode': mode, 'config': asdict(config),
                                  'decision': asdict(schedule(config))})
        save(out / 'c4_decisions.json', decisions)
        jobs = make_jobs(base, ticket_cases, salary_cases)
        if cloud is not None:
            e2e = metadata['probe']['e2e_cloud_ms']
            jobs = [dict(job, config=replace(job['config'], e2e_cloud_ms=e2e))
                    if job['phase'].endswith('cloud') else job for job in jobs]
            minimum = schedule(replace(base, fixed_n=5, e2e_cloud_ms=e2e)).tempo_stimato_ms
            threshold_sla = minimum - .2 * e2e
            metadata['sweep_threshold'] = {'minimum_plan_ms': minimum,
                                          'sla_ms': threshold_sla, 'deficit_ratio': .2}
            for k in (0, .1, .25, .5):
                for repeat in range(10):
                    jobs.append({'phase': 'B_cloud', 'corpus': 'ticket',
                                 'case': ticket_cases[0], 'repeat': repeat,
                                 'variant': f'k_{k}', 'config': replace(
                                     base, sla_ms=threshold_sla, e2e_cloud_ms=e2e,
                                     k_sforamento=k)})
        phases = ['C3_offline', 'C1_cloud', 'C3_cloud', 'C3_high_cloud', 'B_cloud', 'D_cloud']
        rng = random.Random(ORDER_SEED)
        ordered = []
        for phase in phases:
            block = [job for job in jobs if job['phase'] == phase]
            rng.shuffle(block)
            ordered.extend(block)
        jobs = ordered
        save(out / 'planned_jobs.json', [dict(job, config=asdict(job['config'])) for job in jobs])
        counts = Counter((job['corpus'], job['config'].epsilon, job['config'].delta)
                         for job in jobs)
        for key, count in counts.items():
            accounts[key] = make_account(key[1], key[2], count)
        failures = 0
        completed = 0
        for index, job in enumerate(jobs):
            real = job['phase'].endswith('cloud')
            if real and (cloud is None or failures >= 3):
                continue
            config = job['config']
            # Reference strings are analysis-only metadata, never scheduler inputs.
            if job['case']['id'] == 'procedura_e42':
                config = replace(config, riferimenti_ticket=(PatternRiferimento(
                    ('arrest', 'cache', 'riavvi')),))
            key = (job['corpus'], config.epsilon, config.delta)
            engine.records.clear()
            t0 = time.time()
            call_index = len(observed_client.calls) if observed_client else 0
            result = run_request(job['case']['query'], corpora[job['corpus']], config,
                                 cloud if real else offline, engine=engine,
                                 privacy_filter=accounts[key], tracer=tracer if real else None)
            result.update(run_id=f'run_{index:03d}', phase=job['phase'], corpus=job['corpus'],
                          case=job['case'], repeat=job['repeat'], variant=job['variant'],
                          started_at=t0, ended_at=time.time(), local_outputs=engine.records[:],
                          driver_total_ms=(time.time() - t0) * 1000,
                          account_key=str(key), quality=None)
            if real:
                result['provider_calls'] = observed_client.calls[call_index:]
                failures = failures + 1 if result['provider_error'] else 0
            save(out / f'run_{index:03d}.json', result)
            completed += 1
            print(f'{index + 1}/{len(jobs)} {job["phase"]} {job["corpus"]} '
                  f'{job["case"]["id"]} {job["variant"]} '
                  f'N={result["decision"]["n_ensemble"]} '
                  f'{result["request_ms"]:.0f}ms release={len(result["released_keywords"])} '
                  f'error={result["provider_error"]}', flush=True)
            metadata['completed_runs'] = completed
            save(out / 'metadata.json', metadata)
            if observed_client:
                save(out / 'provider_calls.json', observed_client.calls)
        # C2: genuinely generate all drafts locally; only the noise repetitions are cached.
        sensitive, unique = sensitive_token_sets(manifests['ticket'])
        for corpus_name, case in [('ticket', case) for case in ticket_cases] + [
                ('salary', salary_cases[1])]:
            engine.records.clear()
            t0 = time.perf_counter()
            for doc in corpora[corpus_name].retrieve(case['query'], 40):
                context = engine.limita_contesto(doc.context, case['query'], 1000, base.max_tokens)
                engine.genera_bozza(context, case['query'], max_tokens=base.max_tokens)
            drafts = [row['testo'] for row in engine.records]
            generation_ms = (time.perf_counter() - t0) * 1000
            print(f'C2 {corpus_name} {case["id"]}: 40 drafts; {args.trials} trials/cell', flush=True)
            if corpus_name == 'ticket':
                trials = conditional_trials(drafts, case, sensitive, unique, trials=args.trials,
                                             seed=2042 + ticket_cases.index(case))
            else:
                trials = release_trials(drafts, case['target_token'], trials=args.trials)
            save(out / f'c2_{corpus_name}_{case["id"]}.json', {
                'case': case, 'corpus': corpus_name, 'local_outputs': engine.records[:],
                'generation_ms': generation_ms, 'conditional_trials': trials,
                'scope': 'Seeded conditional diagnostics on PUBLIC synthetic drafts; not session DP',
                'cloud_answer_quality': None})
        metadata['status'] = 'complete' if completed == len(jobs) else 'partial_cloud_blocked'
        metadata['planned_runs'] = len(jobs)
        metadata['provider_consecutive_failures'] = failures
    except BaseException as exc:
        metadata['status'] = 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed'
        metadata['failure_type'] = type(exc).__name__
        raise
    finally:
        hardware_stop.set()
        if hardware_process:
            hardware_process.terminate()
            hardware_process.wait(timeout=5)
            hardware_thread.join(timeout=5)
        elif hardware_thread:
            hardware_thread.join(timeout=15)
        metadata['accounts'] = {str(key): {
            'invocations': account.numero_invocazioni, 'epsilon_limit': account.epsilon,
            'delta_limit': account.delta_budget,
            'epsilon_consumed': account.account.epsilon_dp if account.numero_invocazioni else 0,
            'delta_consumed': account.account.delta_total if account.numero_invocazioni else 0,
        } for key, account in accounts.items()}
        metadata['ended_at'] = time.time()
        metadata['campaign_elapsed_s'] = time.time() - started
        save(out / 'metadata.json', metadata)
        if observed_client:
            save(out / 'provider_calls.json', observed_client.calls)
    print('DONE', metadata['status'], out, flush=True)
    return 0 if metadata['status'] == 'complete' else 2


if __name__ == '__main__':
    raise SystemExit(main())
