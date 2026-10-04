#!/usr/bin/env python3
"""Summarize saved campaign measurements without new model/provider calls."""
from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from campaign_measurements import save


def stats(values):
    values = sorted(v for v in values if v is not None and math.isfinite(v))
    if not values:
        return {'n': 0}
    return {'n': len(values), 'mean': statistics.mean(values),
            'median': statistics.median(values), 'min': values[0], 'max': values[-1],
            'sd': statistics.stdev(values) if len(values) > 1 else None}


def wilson(successes, n):
    """Descriptive 95% binomial interval, including zero observed events."""
    if not n:
        return None
    z = 1.959963984540054
    p = successes / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return [max(0, center - half), min(1, center + half)]


def aggregate(rows):
    releases = sum(bool(r['released_keywords']) for r in rows)
    violations = sum(r['sla_violated'] for r in rows)
    errors = sum(r['provider_error'] is not None for r in rows)
    overshoots = [max(0, r['request_ms'] - r['config']['sla_ms']) for r in rows]
    local = [item for row in rows for item in row['local_outputs']]
    return {
        'runs': len(rows), 'release_count': releases,
        'release_rate': releases / len(rows), 'release_wilson95': wilson(releases, len(rows)),
        'sla_violation_count': violations, 'sla_violation_rate': violations / len(rows),
        'sla_violation_wilson95': wilson(violations, len(rows)),
        'provider_errors': errors, 'provider_error_types': dict(Counter(
            r['provider_error'] for r in rows if r['provider_error'])),
        'n_planned': stats([r['decision']['n_ensemble'] for r in rows]),
        'local_inferences': stats([len(r['local_outputs']) for r in rows]),
        'request_ms': stats([r['request_ms'] for r in rows]),
        'edge_ms': stats([r['edge_ms'] for r in rows]),
        'cloud_call_ms': stats([r['cloud_call_ms'] for r in rows]),
        'privacy_ms': stats([r['privacy_ms'] for r in rows]),
        'retrieval_ms': stats([r['retrieval_ms'] for r in rows]),
        'estimated_ms': stats([r['decision']['tempo_stimato_ms'] for r in rows]),
        'signed_estimation_error_ms': stats([
            r['request_ms'] - r['decision']['tempo_stimato_ms'] for r in rows]),
        'overshoot_all_ms': stats(overshoots),
        'overshoot_when_violated_ms': stats([v for v in overshoots if v > 0]),
        'accepted_minimum_plans': sum(r['decision']['sforamento_accettato'] for r in rows),
        'completion_tokens_visible': stats([sum(item['completion_tokens']
                                              for item in r['local_outputs']) for r in rows]),
        'prompt_tokens': stats([sum(item['prompt_tokens']
                                   for item in r['local_outputs']) for r in rows]),
        'local_inference_ms': stats([item['durata_totale_sec'] * 1000 for item in local]),
        'first_text_ms': stats([item['tempo_prefill_reale_sec'] * 1000 for item in local
                               if item['tempo_prefill_reale_sec'] is not None]),
        'token_count_sources': dict(Counter(item.get('token_counts_source', 'unspecified')
                                           for item in local)),
        'labels': dict(Counter(r['esito']['label'] for r in rows)),
        'quality': None if all(r['cloud_simulated'] for r in rows) else 'See reviewed answers',
        'prompt_text_bytes': stats([r['prompt_text_bytes'] for r in rows]),
        'context_text_bytes': stats([r['context_text_bytes'] for r in rows]),
        'driver_minus_request_ms': stats([r['driver_total_ms'] - r['request_ms'] for r in rows]),
        'trace_urls_present': sum(bool(r['trace_url']) for r in rows),
        'run_ids': [r['run_id'] for r in rows],
    }


def plot_results(summary, samples, c2, output):
    """Optional publication/export figures; matplotlib is an analysis-only dependency."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'savefig.dpi': 180})
    for corpus in ('ticket', 'salary'):
        fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True, constrained_layout=True)
        for ax, sla in zip(axes, (5000, 15000, 30000), strict=True):
            group = [r for r in summary if r['phase'] == 'C3_offline'
                     and r['corpus'] == corpus and r['sla_ms'] == sla]
            order = ['adaptive', 'fixed_5', 'fixed_10', 'fixed_20', 'fixed_40']
            group.sort(key=lambda r: order.index(r['variant']))
            means = [r['request_ms']['mean'] / 1000 for r in group]
            low = [m - r['request_ms']['min'] / 1000 for m, r in zip(means, group, strict=True)]
            high = [r['request_ms']['max'] / 1000 - m for m, r in zip(means, group, strict=True)]
            x = np.arange(len(group))
            ax.bar(x, means, yerr=[low, high], capsize=3,
                   color=['#007a78' if r['variant'] == 'adaptive' else '#6e8fa8' for r in group])
            ax.axhline(sla / 1000, color='#c45b33', linestyle='--', label='SLA')
            ax.set_xticks(x, [r['variant'].replace('fixed_', 'N=')
                              .replace('adaptive', 'Adattivo') for r in group], rotation=30)
            ax.set_title(f'SLA {sla / 1000:g} s')
            ax.set_ylabel('Tempo richiesta (s)')
            ax.grid(axis='y', alpha=.2)
        fig.suptitle(f'{corpus}: cloud simulato \u2014 media e min\u2013max, n=5 per cella')
        for extension in ('png', 'svg'):
            fig.savefig(output / f'latency_offline_{corpus}.{extension}')
        plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    for index, phase in enumerate(('C3_cloud', 'C3_high_cloud')):
        for column, sla in enumerate((15000, 30000)):
            ax = axes[index, column]
            group = [r for r in summary if r['phase'] == phase and r['sla_ms'] == sla]
            group.sort(key=lambda r: ['adaptive', 'fixed_20', 'fixed_40'].index(r['variant']))
            x = np.arange(len(group))
            local = [r['edge_ms']['mean'] / 1000 for r in group]
            cloud = [r['cloud_call_ms']['mean'] / 1000 for r in group]
            other = [max(0, r['request_ms']['mean'] - r['edge_ms']['mean']
                         - r['cloud_call_ms']['mean']) / 1000 for r in group]
            ax.bar(x, local, label='Locale', color='#007a78')
            ax.bar(x, cloud, bottom=local, label='Cloud', color='#b895c9')
            ax.bar(x, other, bottom=np.array(local) + cloud, label='Altre fasi', color='#a8a8a8')
            ax.axhline(sla / 1000, color='#c45b33', linestyle='--')
            ax.set_xticks(x, [r['variant'].replace('fixed_', 'N=')
                              .replace('adaptive', 'Adattivo') for r in group])
            params = '\u03b5=4, \u03b4 PTR=0,0001' if index == 0 else '\u03b5=8, \u03b4 PTR=0,01'
            ax.set_title(f'{params}; SLA {sla / 1000:g} s')
            ax.set_ylabel('Tempo medio richiesta (s)')
            ax.grid(axis='y', alpha=.2)
    axes[0, 0].legend()
    fig.suptitle('Ticket E42 con provider reale \u2014 n=5 per cella')
    for extension in ('png', 'svg'):
        fig.savefig(output / f'latency_cloud.{extension}')
    plt.close(fig)
    if samples:
        fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True, constrained_layout=True)
        x = [(s['received_at'] - samples[0]['received_at']) / 60 for s in samples]
        axes[0].plot(x, [s.get('temp', {}).get('cpu_temp_avg', float('nan')) for s in samples],
                     color='#c45b33')
        axes[0].set_ylabel('Temperatura CPU (\u00b0C)')
        for field, label, color in [('sys_power', 'Sistema', '#555555'),
                                     ('gpu_power', 'GPU', '#007a78')]:
            axes[1].plot(x, [s.get(field, float('nan')) for s in samples],
                         label=label, color=color)
        axes[1].set_ylabel('Potenza (W)')
        axes[1].legend()
        axes[2].plot(x, [s.get('gpu_freq_mhz', float('nan')) for s in samples], color='#6e8fa8')
        axes[2].set_ylabel('Frequenza GPU (MHz)')
        axes[2].set_xlabel('Minuti dalla prima lettura')
        for ax in axes:
            ax.grid(alpha=.2)
        fig.suptitle('Mac: misure dell\u2019intero dispositivo, campionamento ogni 5 s')
        for extension in ('png', 'svg'):
            fig.savefig(output / f'hardware.{extension}')
        plt.close(fig)
    procedure = [r for r in c2 if r['case'] == 'procedura_e42']
    if procedure:
        matrix = np.array([[next(r['all_step_terms_rate'] * 100 for r in procedure
                                 if r['n'] == n and r['epsilon'] == epsilon)
                            for n in (5, 10, 20, 40)] for epsilon in (1, 4, 8)])
        fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
        picture = ax.imshow(matrix, vmin=0, vmax=100, cmap='YlGnBu', aspect='auto')
        ax.set_xticks(range(4), [5, 10, 20, 40])
        ax.set_yticks(range(3), [1, 4, 8])
        ax.set_xlabel('Numero di bozze N')
        ax.set_ylabel('\u03b5 per replica')
        for i in range(3):
            for j in range(4):
                ax.text(j, i, f'{matrix[i, j]:.1f}%', ha='center', va='center',
                        color='white' if matrix[i, j] > 55 else 'black')
        fig.colorbar(picture, ax=ax, label='Repliche con termini di tutti i passaggi (%)')
        ax.set_title('E42: copertura lessicale del rilascio, non qualit\u00e0 cloud\n'
                     '500 rumori/cella su bozze congelate; \u03b4 PTR=0,0001')
        for extension in ('png', 'svg'):
            fig.savefig(output / f'procedure_release.{extension}')
        plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--plots', action='store_true', help='Requires matplotlib')
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(path.read_text()) for path in sorted(args.directory.glob('run_*.json'))]
    metadata = json.loads((args.directory / 'metadata.json').read_text())
    review_path = args.directory / 'review.json'
    review = json.loads(review_path.read_text()) if review_path.exists() else {'reviews': {}}
    groups = defaultdict(list)
    for row in rows:
        key = (row['phase'], row['corpus'], row['case']['id'], row['config']['epsilon'],
               row['config']['delta'], row['config']['sla_ms'], row['variant'])
        groups[key].append(row)
    summary = []
    for key, group in sorted(groups.items()):
        phase, corpus, case, epsilon, delta, sla, variant = key
        item = {'phase': phase, 'corpus': corpus, 'case': case, 'epsilon': epsilon,
                'delta_ptr': delta, 'sla_ms': sla, 'variant': variant, **aggregate(group)}
        reviewed = [r for r in group if r['run_id'] in review['reviews']]
        if not all(r['cloud_simulated'] for r in group):
            item['review'] = {
                'reviewer': review.get('reviewer'), 'reviewed': len(reviewed),
                'task_successes': sum(review['reviews'][r['run_id']]['task_success']
                                      for r in reviewed),
                'successful_without_release': sum(
                    review['reviews'][r['run_id']]['task_success'] and not r['released_keywords']
                    for r in reviewed),
                'unsupported_additions': sum(review['reviews'][r['run_id']].get(
                    'unsupported_additions', False) for r in reviewed),
                'verdicts': dict(Counter(review['reviews'][r['run_id']]['verdict']
                                         for r in reviewed)),
                'completo_but_task_failed': sum(r['esito']['label'] == 'completo'
                    and not review['reviews'][r['run_id']]['task_success'] for r in reviewed),
            }
        summary.append(item)
    save(args.output / 'summary.json', summary)
    table = ['# Tabelle della campagna', '',
             f'Stato esecuzione: `{metadata["status"]}`. Richieste presenti: {len(rows)}.', '',
             'Tempi in secondi; intervalli min–max su cinque repliche (dieci per k). '
             'Le frequenze sono osservazioni su questi campioni. Gli intervalli di Wilson '
             'al 95% sono in `summary.json`; non correggono dipendenze temporali.', '']
    phase = None
    for group in summary:
        if group['phase'] != phase:
            phase = group['phase']
            table += [f'## {phase}', '',
                      '| Corpus/caso | ε / δ PTR | SLA s | Variante | n | N medio | '
                      'Tempo medio [min–max] s | Locale s | Cloud s | Rilascio | '
                      'Sforamenti | Sforamento medio* / max s | Errori |',
                      '|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|---|---:|']
        req = group['request_ms']
        over = group['overshoot_all_ms']
        table.append(f'| {group["corpus"]}/{group["case"]} | '
                     f'{group["epsilon"]:g} / {group["delta_ptr"]:g} | '
                     f'{group["sla_ms"] / 1000:.2f} | {group["variant"]} | '
                     f'{group["runs"]} | {group["n_planned"]["mean"]:.1f} | '
                     f'{req["mean"] / 1000:.2f} [{req["min"] / 1000:.2f}–'
                     f'{req["max"] / 1000:.2f}] | {group["edge_ms"]["mean"] / 1000:.2f} | '
                     f'{group["cloud_call_ms"]["mean"] / 1000:.2f} | '
                     f'{group["release_count"]}/{group["runs"]} | '
                     f'{group["sla_violation_count"]}/{group["runs"]} | '
                     f'{over["mean"] / 1000:.2f} / {over["max"] / 1000:.2f} | '
                     f'{group["provider_errors"]} |')
    table += ['', '*Media dello sforamento su tutte le richieste, includendo gli zeri. '
              'La media condizionata agli sforamenti è nel JSON. '
              'La qualità delle risposte simulate non è valutata.', '']
    (args.output / 'TABELLE.md').write_text('\n'.join(table), encoding='utf-8')
    answers = ['# Risposte cloud da revisionare', '',
               'Confrontare ogni risposta con il riferimento; le etichette automatiche '
               'non certificano utilità, astensione o correttezza.', '']
    for row in rows:
        if row['cloud_simulated']:
            continue
        answers += [f'## {row["run_id"]} — {row["phase"]} / {row["case"]["id"]}', '',
                    f'Variante `{row["variant"]}`; N={row["decision"]["n_ensemble"]}; '
                    f'ε={row["config"]["epsilon"]}; δ PTR={row["config"]["delta"]}; '
                    f'label `{row["esito"]["label"]}`; errore `{row["provider_error"]}`.', '',
                    'Keyword: ' + ', '.join(row['released_keywords']), '',
                    '> ' + row['response'].replace('\n', '\n> '), '']
    (args.output / 'RISPOSTE_CLOUD.md').write_text('\n'.join(answers), encoding='utf-8')
    review_table = ['# Revisione delle risposte', '',
                   'Revisione dell\u2019assistente, da sottoporre a revisione umana indipendente. '
                   'Non \u00e8 un giudizio umano indipendente. Nei casi negativi, successo '
                   'significa astensione appropriata; nei casi positivi significa soddisfare '
                   'il quesito. Le aggiunte non supportate sono segnalate separatamente. '
                   'Nessun punteggio viene assegnato alla simulazione.', '',
                   '| Prova | Caso | N | Keyword | Etichetta | Valutazione | Successo | Nota |',
                   '|---|---|---:|---:|---|---|---|---|']
    for row in rows:
        assessment = review['reviews'].get(row['run_id'])
        if assessment is None:
            continue
        success_str = 'sì' if assessment['task_success'] else 'no'
        review_table.append(f'| {row["run_id"]} | {row["case"]["id"]} | '
                            f'{row["decision"]["n_ensemble"]} | {len(row["released_keywords"])} | '
                            f'{row["esito"]["label"]} | {assessment["verdict"]} | '
                            f'{success_str} | '
                            f'{assessment["note"].replace("|", "/")} |')
    (args.output / 'REVISIONE_RISPOSTE.md').write_text('\n'.join(review_table) + '\n',
                                                    encoding='utf-8')
    c2 = []
    c2_table = ['# Repliche condizionali del filtro', '',
                '500 rumori per cella su bozze pubbliche congelate; δ PTR=0,0001 '
                'e δ totale della singola replica=0,0002. Nessuna valutazione di risposta cloud.', '',
                '| Caso | N | ε | Rilascio % | Procedura/target % | Dettaglio unico % | '
                'Identificativo condiviso % |', '|---|---:|---:|---:|---:|---:|---:|']
    for path in sorted(args.directory.glob('c2_*.json')):
        result = json.loads(path.read_text())
        for cell in result['conditional_trials']:
            epsilon = cell.get('epsilon', cell.get('epsilon_per_trial'))
            utility = cell.get('all_step_terms_rate', cell.get('target_recovery_rate'))
            record = {'case': result['case']['id'], 'corpus': result['corpus'], **cell}
            for key, value in list(cell.items()):
                if key.endswith('_rate') and value is not None:
                    record[key + '_wilson95'] = wilson(round(value * cell['trials']), cell['trials'])
            c2.append(record)

            def percent(value):
                return '—' if value is None else f'{100 * value:.1f}'

            c2_table.append(f'| {result["case"]["id"]} | {cell["n"]} | {epsilon:g} | '
                            f'{percent(cell["release_rate"])} | {percent(utility)} | '
                            f'{percent(cell.get("unique_identifier_rate"))} | '
                            f'{percent(cell.get("shared_identifier_rate"))} |')
    save(args.output / 'conditional_summary.json', c2)
    (args.output / 'FILTRO.md').write_text('\n'.join(c2_table) + '\n', encoding='utf-8')
    samples = []
    hardware_path = args.directory / 'hardware.jsonl'
    if hardware_path.exists():
        for line in hardware_path.read_text().splitlines():
            try:
                samples.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    hw = {'samples': len(samples), 'sample_interval_s': 5,
          'scope': 'Whole-machine measurements, not model-only power; zero temperatures omitted'}
    for field in ('cpu_power', 'gpu_power', 'sys_power', 'gpu_freq_mhz',
                  'cpu_active_ratio', 'gpu_active_ratio', 'cpu_scaled_ratio', 'gpu_scaled_ratio'):
        hw[field] = stats([s.get(field) for s in samples])
    for kind in ('cpu', 'gpu'):
        values = [s.get('temp', {}).get(f'{kind}_temp_avg') for s in samples]
        valid = [v for v in values if v is not None and v > 0]
        hw[f'{kind}_temperature_c'] = stats(valid)
        hw[f'{kind}_temperature_first_last_c'] = [valid[0], valid[-1]] if valid else None
    for kind in ('ram_usage', 'ram_total', 'swap_usage'):
        hw[kind + '_gib'] = stats([s['memory'][kind] / 1024 ** 3 for s in samples
                                   if kind in s.get('memory', {})])
    if len(samples) >= 2:
        hw['duration_s'] = samples[-1]['received_at'] - samples[0]['received_at']
        for field in ('sys_power', 'cpu_power', 'gpu_power'):
            hw[field + '_integral_wh'] = sum(
                (b['received_at'] - a['received_at']) * (a[field] + b[field]) / 2 / 3600
                for a, b in zip(samples, samples[1:], strict=False) if field in a and field in b)
    save(args.output / 'hardware_summary.json', hw)
    drift = []
    for corpus in ('ticket', 'salary'):
        comparable = sorted([r for r in rows if r['phase'] == 'C3_offline'
                             and r['corpus'] == corpus and r['variant'] == 'fixed_40'],
                            key=lambda r: r['started_at'])
        if len(comparable) < 10:
            continue
        for label, subset in [('first_five', comparable[:5]), ('last_five', comparable[-5:])]:
            readings = [sample for sample in samples if any(
                r['started_at'] <= sample['received_at'] <= r['ended_at'] for r in subset)]
            drift.append({'corpus': corpus, 'window': label, 'run_ids': [
                r['run_id'] for r in subset], 'edge_ms': stats([r['edge_ms'] for r in subset]),
                'completion_tokens_visible': stats([sum(i['completion_tokens']
                                                        for i in r['local_outputs'])
                                                     for r in subset]),
                'gpu_frequency_mhz': stats([s.get('gpu_freq_mhz') for s in readings]),
                'cpu_temperature_c': stats([s.get('temp', {}).get('cpu_temp_avg')
                                            for s in readings]),
                'scope': 'Same corpus/query/fixed N=40; observational association, not causality'})
    save(args.output / 'thermal_drift.json', drift)
    calls_path = args.directory / 'provider_calls.json'
    calls = json.loads(calls_path.read_text()) if calls_path.exists() else []
    provider = {'calls_including_probe': len(calls),
                'http_errors': dict(Counter(str(c.get('status_code')) for c in calls
                                            if c.get('error_type'))),
                'returned_models': dict(Counter(c.get('model') for c in calls if c.get('model'))),
                'tokens': {key: sum((c.get('usage') or {}).get(key, 0) or 0 for c in calls)
                           for key in ('prompt_tokens', 'completion_tokens', 'total_tokens')},
                'usage_available_calls': sum(c.get('usage') is not None for c in calls),
                'probe_ms': metadata.get('probe', {}).get('e2e_cloud_ms')}
    save(args.output / 'provider_summary.json', provider)
    overview = {'pipeline_requests': len(rows), 'groups': len(summary),
                'local_inferences': sum(len(row['local_outputs']) for row in rows),
                'offline_requests': sum(row['cloud_simulated'] for row in rows),
                'provider': provider, 'hardware': hw,
                'conditional_trials': sum(row['trials'] for row in c2)}
    save(args.output / 'overview.json', overview)
    if args.plots:
        plot_results(summary, samples, c2, args.output)
    print(json.dumps({key: value for key, value in overview.items() if key != 'hardware'}, indent=2))


if __name__ == '__main__':
    main()
