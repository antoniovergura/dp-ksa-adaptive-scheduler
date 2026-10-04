#!/usr/bin/env python3
"""Campagna pulita di latenza cloud E2E — probe sequenziali senza concorrenza."""
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

LABEL = sys.argv[1] if len(sys.argv) > 1 else "mac"
N_PROBES = 20
OUT = Path(f"reports/latenza_cloud_{LABEL}.json")
PY = ".venv/bin/python"

results = []
for i in range(1, N_PROBES + 1):
    t0 = time.perf_counter()
    proc = subprocess.run(
        [PY, "run_pipeline.py", "--no-telemetry", "--no-calibration",
         "--query", "What is the capital of France?",
         "--epsilon", "4.0", "--delta", "1e-5",
         "--output", f"/tmp/probe_latency_{LABEL}_{i}.json"],
        capture_output=True, text=True, timeout=120,
    )
    wall = (time.perf_counter() - t0) * 1000
    try:
        d = json.loads(Path(f"/tmp/probe_latency_{LABEL}_{i}.json").read_text())
        probe_ms = d.get("cloud_probe_ms", 0)
        e2e = d.get("e2e_cloud_ms_ms") or d.get("e2e_cloud_ms") or 0
        req = d.get("request_ms", 0)
    except Exception:
        probe_ms = e2e = req = 0
    results.append({
        "run": i, "probe_ms": probe_ms, "e2e_cloud_ms": e2e,
        "request_ms": req, "wall_ms": wall, "ok": proc.returncode == 0,
    })
    print(f"  [{i:>2}/{N_PROBES}] probe={probe_ms:>8.1f}ms  e2e={e2e:>8.1f}ms  wall={wall:>8.1f}ms")

# Statistiche
probe_vals = [r["probe_ms"] for r in results if r["probe_ms"] > 0]
wall_vals = [r["wall_ms"] for r in results if r["wall_ms"] > 0]

def stats(vals, name):
    if not vals:
        return {}
    vals_sorted = sorted(vals)
    n = len(vals_sorted)
    p95_idx = int(n * 0.95)
    mean = statistics.mean(vals_sorted)
    sd = statistics.stdev(vals_sorted) if n > 1 else 0
    se = sd / (n ** 0.5) if n > 0 else 0
    ci95 = 1.96 * se
    return {
        "name": name, "n": n, "mean_ms": round(mean, 1),
        "median_ms": round(statistics.median(vals_sorted), 1),
        "min_ms": round(vals_sorted[0], 1), "max_ms": round(vals_sorted[-1], 1),
        "std_ms": round(sd, 1), "cv_pct": round(sd / mean * 100, 1) if mean else 0,
        "p95_ms": round(vals_sorted[min(p95_idx, n - 1)], 1),
        "ci95_low_ms": round(mean - ci95, 1), "ci95_high_ms": round(mean + ci95, 1),
    }

summary = {
    "label": LABEL, "n_probes": N_PROBES,
    "probe_e2e": stats(probe_vals, "probe_e2e"),
    "wall_total": stats(wall_vals, "wall_total"),
    "raw": results,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(summary, indent=2))

print(f"\n{'='*55}")
print(f"LATENZA CLOUD — {LABEL} ({N_PROBES} probe sequenziali)")
print(f"{'='*55}")
for s in [summary["probe_e2e"], summary["wall_total"]]:
    if s:
        print(f"\n  [{s['name']}]")
        print(f"    n={s['n']}, mean={s['mean_ms']}ms, median={s['median_ms']}ms")
        print(f"    min={s['min_ms']}ms, max={s['max_ms']}ms, std={s['std_ms']}ms, CV={s['cv_pct']}%")
        print(f"    p95={s['p95_ms']}ms, CI95=[{s['ci95_low_ms']}, {s['ci95_high_ms']}]ms")
print(f"\nSalvato in {OUT}")
