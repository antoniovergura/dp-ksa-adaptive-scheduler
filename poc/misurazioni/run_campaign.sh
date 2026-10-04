#!/usr/bin/env bash
# Campagna di misurazioni — eseguire da poc/ con venv attivo.
# Uso: ./misurazioni/run_campaign.sh <label> [--cloud]
#
#   <label>   Suffisso per i report (es. "mac" o "linux")
#   --cloud   Esegue anche le sezioni con cloud reale (richiede .env)
#
# I report vanno in reports/<label>/ e sono saltati se già esistenti
# (per riprendere una campagna interrotta).

set -euo pipefail

LABEL="${1:?Uso: run_campaign.sh <label> [--cloud]}"
WITH_CLOUD="${2:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
POC_DIR="$(dirname "$SCRIPT_DIR")"
REPORTS="reports/${LABEL}"

cd "$POC_DIR"
mkdir -p "$REPORTS"

PY=".venv/bin/python"

log() { echo -e "\n\033[1;36m>>> $*\033[0m"; }
skip() { echo "   SKIP (già fatto): $1"; }

run() {
    local outfile="$1"; shift
    if [[ -f "$REPORTS/$outfile" ]]; then
        skip "$outfile"
        return 0
    fi
    log "$outfile"
    if ! "$@" --output "$REPORTS/$outfile"; then
        echo "   ERRORE: $outfile fallito (continuo con le altre sezioni)"
        return 0
    fi
}

# ── 0. Sanity check ──────────────────────────────────────────────────────────
log "Sanity check ($LABEL)"
$PY --version
ls models/*.gguf > /dev/null && echo "  modello OK"
ls data/squad_real_benchmark.json > /dev/null && echo "  dataset OK"
$PY -m ruff check . --quiet && echo "  ruff OK"
$PY -m pytest -q --tb=no 2>&1 | tail -1

# ── 1. Misure statiche ───────────────────────────────────────────────────────
log "Misure statiche"
$PY -c "
from core import model_config, scheduler
from core.privacy import DP_KSA_Filter
import json, dataclasses, inspect
cfg = model_config.DEFAULT_LOCAL_MODEL_CONFIG
out = {
    'modello': cfg.filename,
    'n_ctx': cfg.n_ctx,
    'max_tokens': cfg.max_tokens,
    'N_MIN': scheduler.N_MIN,
    'N_MAX': scheduler.N_MAX,
    'DEFAULT_EPSILON_SPLIT': scheduler.DEFAULT_EPSILON_SPLIT,
    'DEFAULT_DELTA': scheduler.DEFAULT_DELTA,
    'DEFAULT_LATENZA_MASSIMA_MS': scheduler.DEFAULT_LATENZA_MASSIMA_MS,
    'DEFAULT_RTT_MS': scheduler.DEFAULT_RTT_MS,
    'DEFAULT_TEMPO_CLOUD_MS': scheduler.DEFAULT_TEMPO_CLOUD_MS,
    'DEFAULT_SFORAMENTO_K': scheduler.DEFAULT_SFORAMENTO_K,
    'MIN_EPSILON_REQUIRED': scheduler.MIN_EPSILON_REQUIRED,
    'PTR_REPRESENTATIVE_GAP': scheduler.PTR_REPRESENTATIVE_GAP,
    'DP_KSA_signature': str(inspect.signature(DP_KSA_Filter.__init__)),
}
print(json.dumps(out, indent=2))
" | tee "$REPORTS/statici.json"

# ── 2. Smoke test offline ────────────────────────────────────────────────────
run "smoke_offline.json" \
    $PY run_pipeline.py --stima-latenza legacy --offline-cloud --no-telemetry \
    --query "What is the capital of France?" \
    --epsilon 4.0 --delta 1e-5

# ── 3.2 Variazione di N (offline) ────────────────────────────────────────────
# N=0 usa --force-zero-shot (fixed-n accetta solo >= 1)
run "n0_offline.json" \
    $PY run_pipeline.py --stima-latenza legacy --offline-cloud --no-telemetry \
    --query "Describe the role of attention in transformers." \
    --force-zero-shot --epsilon 8.0 --delta 1e-5

for N in 5 10 20 40; do
    run "n${N}_offline.json" \
        $PY run_pipeline.py --stima-latenza legacy --offline-cloud --no-telemetry \
        --query "Describe the role of attention in transformers." \
        --fixed-n "$N" --epsilon 8.0 --delta 1e-5
done

# ── 3.3 Variazione soglia sforamento (offline) ───────────────────────────────
for K in 0 1 2 5; do
    run "sforamento_k${K}_offline.json" \
        $PY run_pipeline.py --stima-latenza legacy --offline-cloud --no-telemetry \
        --query "Describe the role of attention in transformers." \
        --sforamento-k "$K" --epsilon 4.0 --delta 1e-5
done

# ── 4.1 Telemetria hardware ──────────────────────────────────────────────────
if [[ ! -f "$REPORTS/hw_snapshot.json" ]]; then
    log "Telemetria hardware"
    $PY -c "
from core.telemetry_hw import snapshot
import json
print(json.dumps(snapshot().to_dict(), indent=2, default=str))
" | tee "$REPORTS/hw_snapshot.json"
else
    skip "hw_snapshot.json"
fi

# ── 4.3 Benchmark scheduler ──────────────────────────────────────────────────
# Prepara cases e corpus se non esistono
if [[ ! -f "data/cases_benchmark.json" ]]; then
    $PY -c "
import json
data = json.load(open('data/squad_real_benchmark.json'))
cases = [{'query': d['domanda'], 'references': d['risposte_corrette']} for d in data[:10]]
json.dump(cases, open('data/cases_benchmark.json', 'w'), ensure_ascii=False, indent=2)
"
fi
if [[ ! -d "data/corpus" ]]; then
    $PY -c "
import json, os
data = json.load(open('data/squad_real_benchmark.json'))
os.makedirs('data/corpus', exist_ok=True)
seen = set()
for d in data:
    t = d.get('argomento', '')
    if t not in seen:
        seen.add(t)
        fname = t.replace(' ', '_') + '.txt'
        with open(os.path.join('data/corpus', fname), 'w') as fh:
            fh.write(d.get('contesto', '')[:500])
"
fi

run "scheduler_benchmark.json" \
    $PY benchmark_scheduler.py \
    --documents data/corpus --cases data/cases_benchmark.json \
    --offline-cloud --repeats 3 --order-seed 42

# ── 6. Riproducibilità ───────────────────────────────────────────────────────
for i in 1 2; do
    run "riproducibilita_run${i}.json" \
        $PY run_pipeline.py --stima-latenza legacy --offline-cloud --no-telemetry \
        --query "Who won Super Bowl 50?" --epsilon 4.0 --delta 1e-5
done

# ── 3.1 Cloud reale (opzionale) ──────────────────────────────────────────────
if [[ "$WITH_CLOUD" == "--cloud" ]]; then
    run "n0_cloud.json" \
        $PY run_pipeline.py --stima-latenza legacy --no-telemetry \
        --query "Describe the role of attention in transformers." \
        --force-zero-shot --epsilon 8.0 --delta 1e-5
    for N in 5 10 20 40; do
        run "n${N}_cloud.json" \
            $PY run_pipeline.py --stima-latenza legacy --no-telemetry \
            --query "Describe the role of attention in transformers." \
            --fixed-n "$N" --epsilon 8.0 --delta 1e-5
    done
    run "smoke_cloud.json" \
        $PY run_pipeline.py --stima-latenza legacy --no-telemetry \
        --query "What is the capital of France?" \
        --epsilon 4.0 --delta 1e-5

    # Sforamento con cloud reale
    for K in 0 1 2 5; do
        run "sforamento_k${K}_cloud.json" \
            $PY run_pipeline.py --stima-latenza legacy --no-telemetry \
            --query "Describe the role of attention in transformers." \
            --sforamento-k "$K" --epsilon 4.0 --delta 1e-5
    done

    # Benchmark scheduler con cloud reale (risposte reali → F1/EM)
    run "scheduler_benchmark_cloud.json" \
        $PY benchmark_scheduler.py \
        --documents data/corpus --cases data/cases_benchmark.json \
        --repeats 1 --order-seed 42 --session-epsilon 20.0

    # Ripetizioni per significatività statistica (3 run × config chiave)
    for rep in 1 2 3; do
        run "rep${rep}_n10_cloud.json" \
            $PY run_pipeline.py --stima-latenza legacy --no-telemetry \
            --query "Describe the role of attention in transformers." \
            --fixed-n 10 --epsilon 8.0 --delta 1e-5
        run "rep${rep}_adaptive_cloud.json" \
            $PY run_pipeline.py --stima-latenza legacy --no-telemetry \
            --query "Describe the role of attention in transformers." \
            --epsilon 8.0 --delta 1e-5
    done

    # Probe E2E esplicito (3 volte per varianza)
    for rep in 1 2 3; do
        run "probe_e2e_run${rep}.json" \
            $PY run_pipeline.py --stima-latenza legacy --no-telemetry --no-calibration \
            --query "What is the capital of France?" \
            --epsilon 4.0 --delta 1e-5
    done
else
    log "Cloud reale saltato (passa --cloud per eseguirlo)"
fi

# ── Riepilogo ────────────────────────────────────────────────────────────────
log "Campagna completata: $(ls "$REPORTS"/*.json 2>/dev/null | wc -l | tr -d ' ') report in $REPORTS/"
ls -la "$REPORTS/"
