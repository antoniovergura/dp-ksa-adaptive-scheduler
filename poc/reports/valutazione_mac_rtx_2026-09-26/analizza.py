#!/usr/bin/env python3
"""Offline reproduction: uses saved runs and explicit assistant annotations; no model/API calls.
Run from anywhere with poc/.venv/bin/python3 /absolute/path/to/analizza.py.
Source runs are never modified. Figures require matplotlib.
"""

import csv
import hashlib
import json
import math
import os
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent
BASE = OUT.parent
CAMPS = {
    "Mac": "campagna_mac_replica_2026-09-26",
    "RTX": "campagna_rtx_2026-09-21",
    "Confronto": "confronto_rtx_2026-09-21",
}


def read(p):
    return json.loads(p.read_text())


def save(name, x):
    (OUT / name).write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def csvout(name, rows):
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with (OUT / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                    for k, v in r.items()
                }
            )


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def stats(xs):
    xs = list(xs)
    return (
        {
            "count": len(xs),
            "mean": st.mean(xs),
            "median": st.median(xs),
            "min": min(xs),
            "max": max(xs),
            "sd": st.stdev(xs) if len(xs) > 1 else 0,
        }
        if xs
        else {"count": 0}
    )


def wilson(k, n):
    if not n:
        return None
    z = 1.959963984540054
    den = 1 + z * z / n
    c = (k / n + z * z / (2 * n)) / den
    h = z * math.sqrt(k / n * (1 - k / n) / n + z * z / (4 * n * n)) / den
    return [max(0, c - h), min(1, c + h)]


required = [OUT / "annotazioni.json", *[BASE / camp / "metadata.json" for camp in CAMPS.values()]]
missing = [str(p.relative_to(BASE)) for p in required if not p.exists()]
if missing:
    raise SystemExit(
        "Riproduzione integrale non disponibile: mancano "
        + ", ".join(missing)
        + ". Consultare poc/reports/LEGGIMI.md per la provenienza dei dati."
    )
ANNOT = read(OUT / "annotazioni.json")
unique = read(OUT / "risposte_uniche.json")
codes = ANNOT["codes"]
assert set(codes) == {x["id"] for x in unique}
lookup = {}
for u in unique:
    assert hashlib.sha256(u["response"].encode()).hexdigest() == u["sha256"]
    for ref in u["runs"]:
        key = (ref["campaign"], ref["file"])
        assert key not in lookup
        lookup[key] = u
LABELS = {
    "C": "Procedura corretta, senza aggiunte",
    "C_generic": "Procedura corretta, consigli generici accessori",
    "C_extra": "Nucleo corretto, dettagli o operazioni non documentati",
    "P": "Procedura incompleta o ordine errato",
    "A": "Astensione sul caso E42 rispondibile",
    "A_extra": "Astensione con cause non documentate",
    "G": "Astensione con operazioni speculative",
    "X": "Risposta degenerata/inutilizzabile",
    "unique_abstention": "Astensione, codice privato non inventato; domanda ambigua",
    "target_correct": "Risposta principale corretta",
    "target_wrong": "Risposta principale errata",
    "contradictory": "Risposta contraddittoria",
    "identifier_correct": "Identificativo esatto",
    "negative_correct": "Astensione corretta su E99 assente",
    "negative_unsupported": "Procedura attribuita a E99 senza riscontro",
    "provider_error": "Richiesta cloud fallita; nessuna risposta utilizzabile",
}
CORRECT = {"C", "C_generic", "C_extra", "target_correct", "identifier_correct", "negative_correct"}
rows = []
reviews = []
metas = {}
checks = {}
manifest = []
for platform, camp in CAMPS.items():
    root = BASE / camp
    meta = read(root / "metadata.json")
    metas[platform] = meta
    fs = sorted(root.glob("run_*.json"))
    assert len(fs) == (40 if platform == "Confronto" else 280)
    assert meta["status"] == "complete" and meta["completed_runs"] == len(fs)
    for f in fs:
        r = read(f)
        cfg = r["config"]
        dec = r["decision"]
        online = not r["cloud_simulated"]
        actual = r["request_ms"] / 1000
        expected = dec.get("tempo_atteso_ms", dec["tempo_stimato_ms"]) / 1000
        planning = dec["tempo_stimato_ms"] / 1000
        assert bool(r["sla_violated"]) == (r["request_ms"] > cfg["sla_ms"])
        case = r.get("case", meta.get("case", {}))["id"]
        row = {
            "platform": platform,
            "campaign": camp,
            "file": f.name,
            "phase": r.get("phase", "confronto"),
            "corpus": r.get("corpus", "ticket"),
            "case": case,
            "variant": r["variant"],
            "repeat": r["repeat"],
            "epsilon": cfg["epsilon"],
            "delta_ptr": cfg["delta"],
            "sla_s": cfg["sla_ms"] / 1000,
            "n": dec["n_ensemble"],
            "online": online,
            "request_s": actual,
            "edge_s": r["edge_ms"] / 1000,
            "cloud_s": r["cloud_call_ms"] / 1000,
            "privacy_s": r["privacy_ms"] / 1000,
            "retrieval_s": r["retrieval_ms"] / 1000,
            "expected_s": expected,
            "planning_s": planning,
            "error_s": actual - expected,
            "planning_error_s": actual - planning,
            "overrun_s": max(0, actual - cfg["sla_ms"] / 1000),
            "violation": r["sla_violated"],
            "release": bool(r["released_keywords"]),
            "keywords": r["released_keywords"],
            "raw_label": r.get("esito", {}).get("label"),
            "local_output_tokens": sum(x["completion_tokens"] for x in r.get("local_outputs", []))
            if "local_outputs" in r
            else None,
            "started_at": r.get("started_at"),
            "refresh_ms": r.get("public_recalibration", {}).get("elapsed_ms", 0),
            "refresh_performed": r.get("public_recalibration", {}).get("performed", False),
            "raw_sha256": sha(f),
            "provider_error": r["provider_error"],
        }
        if online:
            u = lookup[(camp, f.name)]
            assert u["response"] == r["response"] and u["case"] == case
            code = codes[u["id"]]
            success = None if code == "unique_abstention" else code in CORRECT
            row.update(
                {
                    "review_id": u["id"],
                    "review_code": code,
                    "target_success": success,
                    "e42_core_success": success if case == "procedura_e42" else None,
                    "e42_strict": code == "C" if case == "procedura_e42" else None,
                    "e42_no_material_extra": code in {"C", "C_generic"}
                    if case == "procedura_e42"
                    else None,
                    "success_within_sla": bool(success and not row["violation"])
                    if success is not None
                    else None,
                }
            )
            reviews.append(
                {
                    k: row[k]
                    for k in [
                        "platform",
                        "campaign",
                        "file",
                        "phase",
                        "case",
                        "variant",
                        "repeat",
                        "epsilon",
                        "delta_ptr",
                        "sla_s",
                        "n",
                        "review_id",
                        "review_code",
                        "raw_label",
                        "target_success",
                        "e42_core_success",
                        "e42_strict",
                        "e42_no_material_extra",
                        "success_within_sla",
                        "release",
                        "keywords",
                        "raw_sha256",
                    ]
                }
                | {
                    "response_sha256": u["sha256"],
                    "reviewer": ANNOT["reviewer"],
                    "note": ANNOT["notes"].get(u["id"], LABELS[code]),
                    "review_origin": ANNOT["origins"][u["id"]],
                }
            )
        rows.append(row)
        manifest.append({"path": str(f.relative_to(BASE)), "sha256": sha(f)})
    manifest.append(
        {
            "path": str((root / "metadata.json").relative_to(BASE)),
            "sha256": sha(root / "metadata.json"),
        }
    )
    if platform != "Confronto":
        for name in ["thermal_drift.json", "conditional_summary.json"]:
            f = root / "analysis" / name
            manifest.append({"path": str(f.relative_to(BASE)), "sha256": sha(f)})
    c2s = sorted(root.glob("c2_*.json"))
    trials = sum(sum(t["trials"] for t in read(f)["conditional_trials"]) for f in c2s)
    if platform != "Confronto":
        assert len(c2s) == 5 and trials == 30000
        hw = [
            json.loads(s) for s in (root / "hardware.jsonl").read_text().splitlines() if s.strip()
        ]
        assert len(hw) > 0
        for f in [
            root / "hardware.jsonl",
            root / "provider_calls.json",
            root / "c4_decisions.json",
            *c2s,
        ]:
            manifest.append({"path": str(f.relative_to(BASE)), "sha256": sha(f)})
    else:
        hw = []
    checks[platform] = {
        "requests": len(fs),
        "cloud": sum(r["online"] for r in rows if r["platform"] == platform),
        "offline": sum(not r["online"] for r in rows if r["platform"] == platform),
        "C2_files": len(c2s),
        "conditional_trials": trials,
        "hardware_samples": len(hw),
        "provider_errors": sum(r["provider_error"] is not None for r in rows if r["platform"] == platform),
        "complete": True,
    }
assert len(rows) == 600 and len(reviews) == 300 and len(lookup) == 300
save(
    "verifica_dati.json",
    {
        "campaigns": checks,
        "same_model_hash": metas["Mac"]["model_sha256"] == metas["RTX"]["model_sha256"],
        "same_model_config": metas["Mac"]["model_config"] == metas["RTX"]["model_config"],
        "same_corpora": metas["Mac"]["corpus_hashes"] == metas["RTX"]["corpus_hashes"],
        "same_order_seed": metas["Mac"]["order_seed"] == metas["RTX"]["order_seed"],
        "changed_source_hashes": [
            k
            for k, v in metas["Mac"]["source_hashes"].items()
            if metas["RTX"]["source_hashes"].get(k) != v
        ],
        "reviewed_cloud_responses": 300,
        "unique_reviewed_texts": len(unique),
        "reviewer": ANNOT["reviewer"],
    },
)
save("manifest_input.json", manifest)
save("valutazioni_risposte.json", reviews)
csvout("valutazioni_risposte.csv", reviews)
csvout("richieste.csv", rows)


def aggregate(rs):
    good = [r for r in rs if r.get("target_success") is not None]
    e42 = [r for r in rs if r.get("e42_core_success") is not None]
    return {
        "runs": len(rs),
        "n_mean": st.mean(r["n"] for r in rs),
        "request_s": stats(r["request_s"] for r in rs),
        "edge_s": stats(r["edge_s"] for r in rs),
        "cloud_s": stats(r["cloud_s"] for r in rs),
        "expected_s": stats(r["expected_s"] for r in rs),
        "planning_s": stats(r["planning_s"] for r in rs),
        "mae_s": st.mean(abs(r["error_s"]) for r in rs),
        "signed_error_s": st.mean(r["error_s"] for r in rs),
        "planning_mae_s": st.mean(abs(r["planning_error_s"]) for r in rs),
        "planning_underestimates": sum(r["planning_error_s"] > 0 for r in rs),
        "violations": sum(r["violation"] for r in rs),
        "max_overrun_s": max(r["overrun_s"] for r in rs),
        "release_count": sum(r["release"] for r in rs),
        "evaluable": len(good),
        "success": sum(r["target_success"] for r in good),
        "success_within_sla": sum(r["success_within_sla"] for r in good),
        "e42_strict": sum(r["e42_strict"] for r in e42),
        "e42_no_material_extra": sum(r["e42_no_material_extra"] for r in e42),
        "review_codes": dict(Counter(r.get("review_code") for r in rs if r.get("review_code"))),
        "violation_wilson95_exploratory": wilson(sum(r["violation"] for r in rs), len(rs)),
    }


groups = defaultdict(list)
for r in rows:
    groups[
        tuple(
            r[k]
            for k in [
                "platform",
                "phase",
                "corpus",
                "case",
                "variant",
                "epsilon",
                "delta_ptr",
                "sla_s",
            ]
        )
    ].append(r)
cells = []
for key, rs in sorted(groups.items()):
    cells.append(
        dict(
            zip(
                ["platform", "phase", "corpus", "case", "variant", "epsilon", "delta_ptr", "sla_s"],
                key,
                strict=False,
            )
        )
        | aggregate(rs)
    )
save("celle.json", cells)
csvout(
    "celle.csv",
    [
        {k: v for k, v in c.items() if not isinstance(v, dict)}
        | {
            f"{key}_mean": val["mean"]
            for key, val in c.items()
            if isinstance(val, dict) and "mean" in val
        }
        for c in cells
    ],
)
fixed = []
for corpus in ["ticket", "salary"]:
    for n in [5, 10, 20, 40]:
        pair = {
            p: aggregate(
                [
                    r
                    for r in rows
                    if r["platform"] == p
                    and not r["online"]
                    and r["corpus"] == corpus
                    and r["variant"] == f"fixed_{n}"
                ]
            )
            for p in ["Mac", "RTX"]
        }
        fixed.append(
            {
                "corpus": corpus,
                "n": n,
                "Mac": pair["Mac"],
                "RTX": pair["RTX"],
                "speedup_edge_ratio_means": pair["Mac"]["edge_s"]["mean"]
                / pair["RTX"]["edge_s"]["mean"],
            }
        )
quality = []
for platform in CAMPS:
    for case in sorted({r["case"] for r in rows if r["platform"] == platform and r["online"]}):
        quality.append(
            {"platform": platform, "case": case}
            | aggregate(
                [r for r in rows if r["platform"] == platform and r["online"] and r["case"] == case]
            )
        )
conditional = []
for platform in ["Mac", "RTX"]:
    conditional += [
        {"platform": platform} | x
        for x in read(BASE / CAMPS[platform] / "analysis/conditional_summary.json")
    ]
save("C2_condizionale.json", conditional)
csvout("C2_condizionale.csv", conditional)
drift = {p: read(BASE / CAMPS[p] / "analysis/thermal_drift.json") for p in ["Mac", "RTX"]}
metrics = {
    "fixed_n": fixed,
    "quality": quality,
    "drift": drift,
    "comparator": [c for c in cells if c["platform"] == "Confronto"],
    "cloud_overall": {
        p: aggregate([r for r in rows if r["platform"] == p and r["online"]]) for p in CAMPS
    },
    "conditional_scope": "60000 trials conditional on cached local drafts, not independent end-to-end requests",
    "refresh_count": sum(r["refresh_performed"] for r in rows),
}
save("metriche.json", metrics)
# One text review per distinct exact response, with every originating run linked.
md = [
    "# Revisione delle risposte cloud",
    "",
    f"Valutatore: {ANNOT['reviewer']}. Analisi: 26 settembre 2026. Giudizi RTX conservati dal 22 settembre; nuove risposte Mac dalla replica del 26 settembre.",
    "",
    f"300 risposte, {len(unique)} testi distinti. Lettura semantica dell’assistente confrontata con i casi di riferimento; nessun nuovo modello è stato chiamato. Duplicati esatti nello stesso caso condividono il giudizio. I dati grezzi e le loro etichette non vengono modificati.",
    "",
    "## Rubrica",
    "",
]
for k, v in LABELS.items():
    md.append(f"- **{k}**: {v}.")
md += [
    "",
    "Il successo E42 misura presenza e ordine dei tre passaggi, non l’assenza di istruzioni accessorie. C_extra richiede revisione prima dell’uso. La misura rigorosa ammette solo C; la misura senza aggiunte materiali ammette C e C_generic. Per Super Bowl si giudica il vincitore, non ogni fatto accessorio. Le contraddizioni valgono come insuccesso. Il codice privato ha target ambiguo e non entra nel denominatore di correttezza. Le astensioni su E42 sono prudenti ma non risolvono il compito.",
    "",
    "Riferimenti: [casi ticket](../../docs/ticket_demo/cases.json), [ticket esemplificativo](../../docs/ticket_demo/documenti/TKT-E42-001.md).",
    "",
]
for u in unique:
    code = codes[u["id"]]
    md += [
        f"## {u['id']} — {u['case']}",
        "",
        f"**{code} — {LABELS[code]}**",
        "",
        ANNOT["notes"].get(u["id"], LABELS[code]) + ".",
        "",
        f"SHA-256 risposta: `{u['sha256']}`",
        "",
        "Origini: "
        + ", ".join(
            f"[{r['campaign']}/{r['file']}](../{r['campaign']}/{r['file']})" for r in u["runs"]
        ),
        "",
    ]
    response = (
        u["response"]
        if code != "X"
        else u["response"][:500]
        + "\n[Anteprima abbreviata della ripetizione; testo integrale nel JSON originale e in risposte_uniche.json.]"
    )
    md += ["```text", response, "```", ""]
(OUT / "RISPOSTE_COMMENTATE.md").write_text("\n".join(md))
# Plot the experimental cells, not invented fitted observations.
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-sla")
import matplotlib  # noqa: E402 — configure plotting only after input checks

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402 — Agg backend must be selected first

plt.rcParams.update(
    {
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 140,
        "savefig.facecolor": "white",
    }
)
colors = {"Mac": "#b65a37", "RTX": "#177a86"}


def figsave(fig, name):
    fig.savefig(OUT / (name + ".png"), dpi=180, bbox_inches="tight", pad_inches=0.25)
    fig.savefig(OUT / (name + ".svg"), bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


fig, axs = plt.subplots(1, 2, figsize=(10.8, 4.3))
for ax, corpus in zip(axs, ["ticket", "salary"], strict=False):
    for p in ["Mac", "RTX"]:
        xs = [x for x in fixed if x["corpus"] == corpus]
        ys = [x[p]["edge_s"]["mean"] for x in xs]
        lo = [y - x[p]["edge_s"]["min"] for x, y in zip(xs, ys, strict=False)]
        hi = [x[p]["edge_s"]["max"] - y for x, y in zip(xs, ys, strict=False)]
        ax.errorbar(
            [x["n"] for x in xs], ys, yerr=[lo, hi], label=p, marker="o", capsize=3, color=colors[p]
        )
    ax.set(
        title="Ticket E42" if corpus == "ticket" else "Retribuzione T2",
        xlabel="Numero di inferenze N",
        ylabel="Tempo locale (s)",
        xticks=[5, 10, 20, 40],
    )
    ax.grid(alpha=0.16)
    ax.legend()
fig.suptitle("Stesso N: media e intervallo osservato, 15 richieste per punto")
fig.tight_layout()
figsave(fig, "01_tempi_locali")
fig, axs = plt.subplots(1, 2, figsize=(10.8, 4.3))
for ax, corpus in zip(axs, ["ticket", "salary"], strict=False):
    for p in ["Mac", "RTX"]:
        rs = sorted(
            [
                r
                for r in rows
                if r["platform"] == p
                and r["phase"] == "C3_offline"
                and r["corpus"] == corpus
                and r["variant"] == "fixed_40"
            ],
            key=lambda r: r["started_at"],
        )
        ax.plot(
            range(1, len(rs) + 1), [r["edge_s"] for r in rs], marker="o", label=p, color=colors[p]
        )
    ax.set(
        title="Ticket E42" if corpus == "ticket" else "Retribuzione T2",
        xlabel="Ordine cronologico delle richieste N=40",
        ylabel="Tempo locale (s)",
    )
    ax.legend()
    ax.grid(alpha=0.16)
fig.suptitle("Deriva osservata durante la campagna: stesso corpus, stessa query, N=40")
fig.tight_layout()
figsave(fig, "02_deriva")
variants = ["legacy", "direct_static", "direct_refresh", "fixed_20"]
labels = ["Precedente", "Diretta statica", "Diretta aggiornata", "N fisso 20"]
fig, axs = plt.subplots(1, 2, figsize=(11.2, 4.6))
for ax, sla in zip(axs, [15, 30], strict=False):
    cs = [
        next(c for c in metrics["comparator"] if c["variant"] == v and c["sla_s"] == sla)
        for v in variants
    ]
    bars = ax.bar(
        range(4), [c["mae_s"] for c in cs], color=["#68768a", "#177a86", "#b65a37", "#b9a45c"]
    )
    for bar, c in zip(bars, cs, strict=False):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.11,
            f"{c['mae_s']:.2f}s\n{c['violations']}/5 fuori SLA",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    ax.set(
        title=f"SLA {sla} secondi",
        xticks=range(4),
        xticklabels=labels,
        ylabel="Errore assoluto medio: tempo atteso (s)",
        ylim=(0, 5.6),
    )
    ax.tick_params(axis="x", labelrotation=15)
    ax.grid(axis="y", alpha=0.15)
fig.suptitle("Confronto esplorativo RTX: 5 richieste per configurazione")
fig.tight_layout()
figsave(fig, "03_stime")
fig, ax = plt.subplots(figsize=(10.8, 4.6))
cats = [
    ("C", "Core senza aggiunte", "#146671"),
    ("C_generic", "Core + consigli generici", "#479b91"),
    ("C_extra", "Core + dettagli non documentati", "#e5b45a"),
    ("P", "Procedura errata/incompleta", "#c35b43"),
    ("A", "Astensione", "#b5b9bf"),
    ("G", "Astensione + operazioni speculative", "#8d749f"),
    ("A_extra", "Astensione + cause non documentate", "#654b7b"),
    ("X", "Inutilizzabile", "#292929"),
]
left = [0, 0, 0]
for code, label, color in cats:
    vals = [
        next(q for q in quality if q["platform"] == p and q["case"] == "procedura_e42")[
            "review_codes"
        ].get(code, 0)
        for p in CAMPS
    ]
    ax.barh(range(3), vals, left=left, color=color, label=label)
    for i, (left_edge, v) in enumerate(zip(left, vals, strict=False)):
        if v >= 4:
            ax.text(
                left_edge + v / 2,
                i,
                str(v),
                ha="center",
                va="center",
                fontsize=9,
                color="white" if code in ["C", "P", "X", "A_extra"] else "black",
            )
    left = [left_edge + v for left_edge, v in zip(left, vals, strict=False)]
ax.set(
    yticks=range(3),
    yticklabels=["Mac (105)", "RTX (105)", "Confronto RTX (40)"],
    xlabel="Numero di risposte E42",
    title="Correttezza del nucleo e aggiunte: revisione dell’assistente",
)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2, frameon=False, fontsize=9)
figsave(fig, "04_qualita")
fig, axs = plt.subplots(1, 2, figsize=(10.8, 4.4))
for ax, case, metric, title in [
    (axs[0], "procedura_e42", "all_step_terms_rate", "E42: termini di tutti i passaggi"),
    (axs[1], "base_a", "target_recovery_rate", "Retribuzione A1: recupero di 36000"),
]:
    for p in ["Mac", "RTX"]:
        cs = sorted(
            [
                c
                for c in conditional
                if c["platform"] == p
                and c["case"] == case
                and c.get("epsilon", c.get("epsilon_per_trial")) == 8
            ],
            key=lambda c: c["n"],
        )
        ax.plot([c["n"] for c in cs], [100 * c[metric] for c in cs], "-o", color=colors[p], label=p)
    ax.set(
        title=title,
        xlabel="Numero di bozze N",
        ylabel="Percentuale nelle simulazioni",
        xticks=[5, 10, 20, 40],
        ylim=(-3, 105),
    )
    ax.grid(alpha=0.15)
    ax.legend()
fig.suptitle("C2: 500 simulazioni per punto su bozze già generate, ε=8, δ totale=0,0002")
fig.tight_layout()
figsave(fig, "05_filtro_condizionale")
print(
    json.dumps(
        {
            "fixed": [
                (
                    x["corpus"],
                    x["n"],
                    round(x["Mac"]["edge_s"]["mean"], 3),
                    round(x["RTX"]["edge_s"]["mean"], 3),
                    round(x["speedup_edge_ratio_means"], 2),
                )
                for x in fixed
            ],
            "quality": [
                (
                    q["platform"],
                    q["case"],
                    q["runs"],
                    q["success"],
                    q["success_within_sla"],
                    q["review_codes"],
                )
                for q in quality
            ],
            "comparator": [
                (
                    c["variant"],
                    c["sla_s"],
                    c["runs"],
                    c["success"],
                    c["success_within_sla"],
                    c["e42_no_material_extra"],
                    c["e42_strict"],
                )
                for c in metrics["comparator"]
            ],
        },
        ensure_ascii=False,
        indent=2,
    )
)
