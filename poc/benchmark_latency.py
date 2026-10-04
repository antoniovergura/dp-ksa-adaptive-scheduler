#!/usr/bin/env python3
"""Compare legacy, direct static, direct refreshed, and fixed N on public E42.

Same-session randomized blocks, warm model, shared cumulative privacy account.
Reports are experimental diagnostics, not DP releases. No telemetry uploads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import time
from dataclasses import asdict, replace
from pathlib import Path

from dotenv import load_dotenv

from benchmark_salary_demo import verify_corpus
from campaign_measurements import make_account, save
from core.calibration import calibra
from core.cloud import CloudGenerator
from core.engine import LocalNeuralEngine
from core.latency import PublicLatencyRefresh, calibrate_latency
from core.model_config import percorso_modello_predefinito
from core.pipeline import RequestConfig, run_request

ROOT = Path(__file__).resolve().parent


def summarize(rows):
    summary = {}
    for variant in sorted({row['variant'] for row in rows}):
        for sla in sorted({row['config']['sla_ms'] for row in rows}):
            group = [r for r in rows if r['variant'] == variant and r['config']['sla_ms'] == sla]
            if not group:
                continue
            valid = [r for r in group if not r['provider_error']]
            errors = [r['request_ms'] - r['decision']['tempo_atteso_ms'] for r in valid]
            summary[f'{variant}_{sla:g}ms'] = {
                'runs': len(group), 'provider_errors': len(group) - len(valid),
                'mean_error_ms': statistics.mean(errors) if errors else None,
                'mae_ms': statistics.mean(map(abs, errors)) if errors else None,
                'sla_violations': sum(r['sla_violated'] for r in group),
                'mean_overrun_ms': statistics.mean(
                    max(0, r['request_ms'] - sla) for r in group),
                'planning_underestimates': sum(
                    r['request_ms'] > r['decision']['tempo_stimato_ms'] for r in valid),
                'n_mean': statistics.mean(r['decision']['n_ensemble'] for r in group),
                'releases': sum(bool(r['released_keywords']) for r in group),
                'quality': 'manual review required; release is not correctness',
            }
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cloud', action='store_true')
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--recalibrate-every', type=int, default=5)
    args = parser.parse_args(argv)
    if not 1 <= args.repeats <= 5 or args.recalibrate_every < 0:
        parser.error('repeats: 1..5; recalibrate-every: >=0')
    load_dotenv(ROOT / '.env')
    corpus, _ = verify_corpus(ROOT / 'docs/ticket_demo')
    case = json.loads((ROOT / 'docs/ticket_demo/cases.json').read_text())[0]
    model = percorso_modello_predefinito()
    if not model.is_file():
        raise FileNotFoundError('Existing local model required')
    args.output.mkdir(parents=True, exist_ok=False)
    metadata = {'status': 'running', 'started_at': time.time(), 'seed': 20260921,
                'planned_runs': 8 * args.repeats, 'completed_runs': 0,
                'cloud_requested': args.cloud, 'case': case,
                'scope': 'verified synthetic corpus; reports are NOT DP',
                'source_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in [Path(__file__), *sorted((ROOT / 'core').glob('*.py'))]}}
    save(args.output / 'metadata.json', metadata)
    rows = []
    try:
        engine = LocalNeuralEngine(model_path=model)
        legacy = calibra(engine)
        direct = calibrate_latency(engine)
        cloud = CloudGenerator(offline=not args.cloud)
        if args.cloud:
            from openai import OpenAI
            if not cloud.api_key and not cloud.base_url:
                raise RuntimeError('Cloud configuration required')
            cloud._client = OpenAI(api_key=cloud.api_key or 'not-needed', base_url=cloud.base_url,
                                   max_retries=0, timeout=60)
        old_probe, new_probe = cloud.probe(), cloud.probe_representative()
        if args.cloud and (old_probe.errore or new_probe.errore or new_probe.simulato):
            raise RuntimeError('Public cloud calibration failed')
        base = RequestConfig(epsilon=8, delta=.01, e2e_cloud_ms=0 if not args.cloud else None)
        old = replace(base, prefill_tps=legacy.prefill_tps, generation_tps=legacy.generation_tps,
                      e2e_cloud_ms=old_probe.e2e_cloud_ms if args.cloud else 0)
        new = replace(base, local_latency_profile=direct,
                      e2e_cloud_ms=new_probe.e2e_cloud_ms if args.cloud else 0,
                      cloud_expected_ms=new_probe.expected_ms if args.cloud else 0)
        metadata.update(legacy_calibration=asdict(legacy), direct_calibration=asdict(direct),
                        legacy_cloud=asdict(old_probe), direct_cloud=asdict(new_probe),
                        output_cap_observed=direct.output_cap_observed)
        save(args.output / 'metadata.json', metadata)
        refresh = PublicLatencyRefresh(args.recalibrate_every)
        current = direct
        account = make_account(base.epsilon, base.delta, metadata['planned_runs'])
        rng = random.Random(metadata['seed'])
        failures = 0
        for repeat in range(args.repeats):
            jobs = [(variant, sla) for variant in ('legacy', 'direct_static', 'direct_refresh',
                                                   'fixed_20') for sla in (15000, 30000)]
            rng.shuffle(jobs)
            for variant, sla in jobs:
                refresh_info = {'performed': False, 'elapsed_ms': 0}
                config = old if variant == 'legacy' else new
                if variant == 'direct_refresh':
                    current, refresh_info = refresh.before_request(engine, current)
                    config = replace(new, local_latency_profile=current)
                config = replace(config, sla_ms=sla, fixed_n=20 if variant == 'fixed_20' else None)
                result = run_request(case['query'], corpus, config, cloud,
                                     engine=engine, privacy_filter=account)
                result.update(variant=variant, repeat=repeat, quality=None,
                              public_recalibration=refresh_info)
                rows.append(result)
                save(args.output / f'run_{len(rows):03d}.json', result)
                metadata['completed_runs'] = len(rows)
                save(args.output / 'metadata.json', metadata)
                print(f'{len(rows)}/{metadata["planned_runs"]} {variant} SLA={sla} '
                      f'N={result["decision"]["n_ensemble"]} '
                      f'{result["request_ms"]:.0f}ms error={result["provider_error"]}', flush=True)
                failures = failures + 1 if result['provider_error'] else 0
                if failures >= 3:
                    raise RuntimeError('Three consecutive provider errors; campaign stopped')
        metadata['status'] = 'complete'
        metadata['cumulative_epsilon'] = account.account.epsilon_dp
        metadata['cumulative_delta'] = account.account.delta_total
    except BaseException as exc:
        metadata.update(status='failed', failure_type=type(exc).__name__)
        raise
    finally:
        metadata['ended_at'] = time.time()
        save(args.output / 'metadata.json', metadata)
        save(args.output / 'summary.json', summarize(rows))


if __name__ == '__main__':
    main()
