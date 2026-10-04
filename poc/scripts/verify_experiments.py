"""Verify archived scientific data using the standard library, without writing files.

Run from the repository root: python3 poc/scripts/verify_experiments.py
The assertions cover source hashes, aggregates, annotations and experiment provenance.
Semantic judgments are checked for consistency, not independently re-evaluated.
"""

import csv
import hashlib
import json
import math
import re
import statistics
import tarfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "poc/reports/valutazione_mac_rtx_2026-09-26"


def main():
    if not __debug__:
        raise SystemExit("Eseguire senza -O: i controlli usano assert.")
    cells = list(csv.DictReader((DATA / "celle.csv").open()))
    full_cells = json.loads((DATA / "celle.json").read_text())
    c2 = list(csv.DictReader((DATA / "C2_condizionale.csv").open()))
    reviews = json.loads((DATA / "valutazioni_risposte.json").read_text())
    texts = json.loads((DATA / "risposte_uniche.json").read_text())
    checks = {}
    assert len(cells) == 112 and sum(int(r["runs"]) for r in cells) == 600
    assert len(c2) == 120 and sum(int(r["trials"]) for r in c2) == 60000
    assert len(reviews) == 300 and 0 < len(texts) <= 300
    assert len({r["id"] for r in texts}) == len(texts)
    assert sum(len(r["runs"]) for r in texts) == 300
    checks["numerosita_aggregati"] = {
        "celle_pipeline": 112,
        "richieste_pipeline": 600,
        "celle_C2": 120,
        "repliche_C2": 60000,
        "giudizi": 300,
        "testi_distinti": len(texts),
    }

    # The CSV and JSON are two representations of the same saved aggregates.
    assert len(full_cells) == len(cells)
    for flat, full in zip(cells, full_cells, strict=True):
        for key, value in flat.items():
            if key.endswith("_mean") and key[:-5] in full:
                expected = full[key[:-5]]["mean"]
            else:
                expected = full[key]
            if isinstance(expected, (int, float)):
                assert math.isclose(float(value), expected, abs_tol=1e-12), key
            elif isinstance(expected, list):
                assert json.loads(value) == expected, key
            else:
                assert value == expected, key
        assert math.isclose(
            full["signed_error_s"],
            full["request_s"]["mean"] - full["expected_s"]["mean"],
            abs_tol=1e-10,
        )
        assert full["mae_s"] + 1e-10 >= abs(full["signed_error_s"])
        assert 0 <= full["success_within_sla"] <= full["success"] <= full["runs"]
        assert 0 <= full["release_count"] <= full["runs"]
    checks["coerenza_aggregati"] = "112 celle: CSV/JSON, bias, MAE e conteggi coerenti"

    byid = {r["id"]: r for r in texts}
    for r in texts:
        assert hashlib.sha256(r["response"].encode()).hexdigest() == r["sha256"], r["id"]
    for r in reviews:
        assert byid[r["review_id"]]["sha256"] == r["response_sha256"]
    manifest = {
        r["path"]: r["sha256"] for r in json.loads((DATA / "manifest_input.json").read_text())
    }
    assert len({(r["campaign"], r["file"]) for r in reviews}) == 300
    for r in reviews:
        assert manifest[f"{r['campaign']}/{r['file']}"] == r["raw_sha256"]
        assert any(
            x["campaign"] == r["campaign"] and x["file"] == r["file"]
            for x in byid[r["review_id"]]["runs"]
        )
    for cell in full_cells:
        if cell["phase"] == "C3_offline":
            continue
        group = [
            r
            for r in reviews
            if all(
                r[k] == cell[k]
                for k in [
                    "platform",
                    "phase",
                    "case",
                    "variant",
                    "epsilon",
                    "delta_ptr",
                    "sla_s",
                ]
            )
        ]
        assert len(group) == cell["runs"]
        assert dict(Counter(r["review_code"] for r in group)) == cell["review_codes"]
        assert sum(bool(r["success_within_sla"]) for r in group) == cell["success_within_sla"]
        assert sum(r["release"] for r in group) == cell["release_count"]
    checks["hash_risposte"] = f"{len(texts)} testi e 300 collegamenti ai giudizi verificati"

    quality = {}
    for p in ["Mac", "RTX", "Confronto"]:
        rows = [r for r in reviews if r["platform"] == p and r["case"] == "procedura_e42"]
        codes = Counter(r["review_code"] for r in rows)
        quality[p] = {
            "n": len(rows),
            "nucleo": sum(codes[c] for c in ["C", "C_generic", "C_extra"]),
            "senza_aggiunte_materiali": sum(codes[c] for c in ["C", "C_generic"]),
            "senza_aggiunte": codes["C"],
            "codici": dict(codes),
        }
    assert [quality[p]["n"] for p in quality] == [105, 105, 40]
    checks["conteggi_revisione_semantica"] = quality

    for corpus in ["ticket_demo", "azienda_demo"]:
        base = ROOT / "poc/docs" / corpus
        corpus_manifest = json.loads((base / "manifest.json").read_text())
        assert corpus_manifest["synthetic"] and len(corpus_manifest["documents"]) == 80
        for entry in corpus_manifest["documents"]:
            assert (
                hashlib.sha256((base / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
            )
    checks["corpora"] = "160 documenti sintetici verificati contro i manifest"

    checks["benchmark_complementari"] = {}
    probe_values = {}
    public_cases = json.loads((ROOT / "poc/data/cases_benchmark.json").read_text())
    public_dataset = json.loads((ROOT / "poc/data/squad_real_benchmark.json").read_text())
    assert public_cases == [
        {"query": r["domanda"], "references": r["risposte_corrette"]} for r in public_dataset[:10]
    ]
    for p in ["mac", "linux"]:
        b = json.loads((ROOT / f"poc/reports/{p}/scheduler_benchmark_cloud.json").read_text())
        assert len(b["runs"]) == 47 and b["planned_runs"] == 50 and b["stopped_budget"]
        assert not any(r["released_keywords"] or r["ptr_passed"] for r in b["runs"])
        for r in b["runs"]:
            assert r["sla_violated"] == (r["request_ms"] > r["config"]["sla_ms"])
            assert not r["cloud_simulated"] and r["provider_error"] is None
            predicted = re.findall(r"\w+", r["response"].casefold())
            scores = []
            for reference in public_cases[r["case_index"]]["references"]:
                expected = re.findall(r"\w+", reference.casefold())
                overlap = sum((Counter(predicted) & Counter(expected)).values())
                scores.append(
                    (
                        float(predicted == expected),
                        2 * overlap / (len(predicted) + len(expected)),
                    )
                )
            assert r["quality"]["exact_match"] == max(score[0] for score in scores)
            assert math.isclose(r["quality"]["token_f1"], max(score[1] for score in scores))
        for variant, summary in b["summary"].items():
            rows = [r for r in b["runs"] if r["variant"] == variant]
            assert len(rows) == summary["runs"]
            assert math.isclose(
                statistics.mean(r["request_ms"] for r in rows), summary["request_ms_mean"]
            )
            assert math.isclose(
                statistics.mean(r["quality"]["token_f1"] for r in rows),
                summary["token_f1_mean"],
            )
            assert math.isclose(
                sum(r["sla_violated"] for r in rows) / len(rows),
                summary["sla_violation_rate"],
            )
        probe = json.loads((ROOT / f"poc/reports/latenza_cloud_{p}.json").read_text())
        vals = [r["probe_ms"] for r in probe["raw"]]
        probe_values[p] = vals
        assert len(vals) == 20
        for key, val in [
            ("mean_ms", statistics.mean(vals)),
            ("median_ms", statistics.median(vals)),
            ("std_ms", statistics.stdev(vals)),
            ("min_ms", min(vals)),
            ("max_ms", max(vals)),
        ]:
            assert abs(val - probe["probe_e2e"][key]) < 0.11, (p, key)
        checks["benchmark_complementari"][p] = {
            "completate": 47,
            "previste": 50,
            "rilasci": 0,
            "probe": 20,
            "probe_superiori_10s": sum(x > 10000 for x in vals),
            "media_probe_ms_ricalcolata": statistics.mean(vals),
            "qualita": "Exact match e token F1 ricalcolati sui testi e riferimenti conservati",
        }

    campaigns = {
        "Mac": "campagna_mac_replica_2026-09-26",
        "RTX": "campagna_rtx_2026-09-21",
        "Confronto": "confronto_rtx_2026-09-21",
    }
    raw_checks = {}
    review_lookup = {(r["campaign"], r["file"]): r for r in reviews}
    conditional_json = json.loads((DATA / "C2_condizionale.json").read_text())
    for platform, campaign in campaigns.items():
        base = ROOT / "poc/reports" / campaign
        assert base.is_dir(), f"Campagna usata nell’analisi assente: {campaign}"
        entries = {
            path: digest for path, digest in manifest.items() if path.startswith(campaign + "/")
        }
        for path, digest in entries.items():
            source = ROOT / "poc/reports" / path
            assert source.is_file(), path
            assert hashlib.sha256(source.read_bytes()).hexdigest() == digest, path
        metadata = json.loads((base / "metadata.json").read_text())
        runs = []
        for source in sorted(base.glob("run_*.json")):
            run = json.loads(source.read_text())
            cfg, decision = run["config"], run["decision"]
            assert run["provider_error"] is None
            assert run["sla_violated"] == (run["request_ms"] > cfg["sla_ms"])
            run["_case"] = run.get("case", metadata.get("case", {}))["id"]
            run["_expected_s"] = (
                decision.get("tempo_atteso_ms", decision["tempo_stimato_ms"]) / 1000
            )
            run["_planning_s"] = decision["tempo_stimato_ms"] / 1000
            if not run["cloud_simulated"]:
                review = review_lookup[(campaign, source.name)]
                assert (
                    hashlib.sha256(run["response"].encode()).hexdigest()
                    == review["response_sha256"]
                )
                assert run["released_keywords"] == review["keywords"]
                if review["target_success"] is not None:
                    assert review["success_within_sla"] == bool(
                        review["target_success"] and not run["sla_violated"]
                    )
            runs.append(run)
        assert metadata["status"] == "complete"
        assert len(runs) == metadata["completed_runs"] == (40 if platform == "Confronto" else 280)
        platform_cells = [r for r in full_cells if r["platform"] == platform]
        for cell in platform_cells:
            group = [
                r
                for r in runs
                if r.get("phase", "confronto") == cell["phase"]
                and r.get("corpus", "ticket") == cell["corpus"]
                and r["_case"] == cell["case"]
                and r["variant"] == cell["variant"]
                and r["config"]["epsilon"] == cell["epsilon"]
                and r["config"]["delta"] == cell["delta_ptr"]
                and r["config"]["sla_ms"] / 1000 == cell["sla_s"]
            ]
            assert len(group) == cell["runs"]
            for metric, values in {
                "request_s": [r["request_ms"] / 1000 for r in group],
                "edge_s": [r["edge_ms"] / 1000 for r in group],
                "cloud_s": [r["cloud_call_ms"] / 1000 for r in group],
                "expected_s": [r["_expected_s"] for r in group],
                "planning_s": [r["_planning_s"] for r in group],
            }.items():
                for stat, fn in [
                    ("mean", statistics.mean),
                    ("median", statistics.median),
                    ("min", min),
                    ("max", max),
                    ("sd", statistics.stdev),
                ]:
                    assert math.isclose(fn(values), cell[metric][stat], abs_tol=1e-10), (
                        platform,
                        cell["phase"],
                        cell["variant"],
                        metric,
                        stat,
                    )
            errors = [r["request_ms"] / 1000 - r["_expected_s"] for r in group]
            assert math.isclose(statistics.mean(map(abs, errors)), cell["mae_s"], abs_tol=1e-10)
            assert math.isclose(statistics.mean(errors), cell["signed_error_s"], abs_tol=1e-10)
            assert sum(r["sla_violated"] for r in group) == cell["violations"]
            assert sum(bool(r["released_keywords"]) for r in group) == cell["release_count"]
            assert math.isclose(
                statistics.mean(r["decision"]["n_ensemble"] for r in group), cell["n_mean"]
            )
        conditional_count = 0
        for source in sorted(base.glob("c2_*.json")):
            data = json.loads(source.read_text())
            for trial in data["conditional_trials"]:
                epsilon = trial.get("epsilon", trial.get("epsilon_per_trial"))
                saved = next(
                    r
                    for r in conditional_json
                    if r["platform"] == platform
                    and r["case"] == data["case"]["id"]
                    and r["n"] == trial["n"]
                    and r.get("epsilon", r.get("epsilon_per_trial")) == epsilon
                )
                assert all(saved[k] == v for k, v in trial.items()), source.name
                conditional_count += 1
        raw_checks[platform] = {
            "file_manifest_verificati": len(entries),
            "richieste_ricalcolate": len(runs),
            "celle_ricalcolate": len(platform_cells),
            "celle_C2_verificate": conditional_count,
        }
    checks["verifica_dati_grezzi_presenti"] = raw_checks
    assert set(raw_checks) == {"Mac", "RTX", "Confronto"}
    assert sum(r["richieste_ricalcolate"] for r in raw_checks.values()) == 600
    assert sum(r["celle_C2_verificate"] for r in raw_checks.values()) == 120

    # The original data and judgments are preserved independently of the replica.
    old_data = ROOT / "poc/reports/valutazione_mac_rtx_2026-09-22"
    old_reviews = json.loads((old_data / "valutazioni_risposte.json").read_text())
    old_lookup = {(r["campaign"], r["file"]): r for r in old_reviews}
    for review in reviews:
        if review["platform"] == "Mac":
            continue
        previous = old_lookup[(review["campaign"], review["file"])]
        for key in ["review_id", "review_code", "note", "response_sha256", "raw_sha256"]:
            assert review[key] == previous[key], (review["file"], key)
    old_manifest = json.loads((old_data / "manifest_input.json").read_text())
    preserved = 0
    for entry in old_manifest:
        if entry["path"].startswith("campagna_2026-09-20/"):
            continue
        source = ROOT / "poc/reports" / entry["path"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == entry["sha256"]
        preserved += 1
    assert preserved == 332
    checks["conservazione_storica"] = {
        "file_originali_invariati": preserved,
        "giudizi_RTX_e_confronto_invariati": 170,
    }

    snapshot = ROOT / "poc/reports/replica_mac_2026-09-26_sorgenti"
    provenance = json.loads((snapshot / "provenienza.json").read_text())
    mac_meta = json.loads((ROOT / "poc/reports" / campaigns["Mac"] / "metadata.json").read_text())
    rtx_meta = json.loads((ROOT / "poc/reports" / campaigns["RTX"] / "metadata.json").read_text())
    assert mac_meta["model_sha256"] == rtx_meta["model_sha256"]
    assert mac_meta["model_config"] == rtx_meta["model_config"]
    assert mac_meta["corpus_hashes"] == rtx_meta["corpus_hashes"]
    assert mac_meta["order_seed"] == rtx_meta["order_seed"] == 20260919
    assert mac_meta["provider"] == rtx_meta["provider"]
    source_hashes = {r["path"]: r["sha256"] for r in provenance["snapshot_files"]}
    with tarfile.open(snapshot / "sorgenti_e_input.tar.gz", "r:gz") as archive:
        for path, digest in source_hashes.items():
            handle = archive.extractfile("runtime/" + path)
            assert handle is not None
            assert hashlib.sha256(handle.read()).hexdigest() == digest, path
    for path, digest in mac_meta["source_hashes"].items():
        assert source_hashes[path] == digest, path
    for path in [
        "core/scheduler.py",
        "core/pipeline.py",
        "core/privacy.py",
        "core/cloud.py",
        "core/engine.py",
        "core/calibration.py",
        "core/model_config.py",
        "core/dataset.py",
        "core/documents.py",
    ]:
        assert mac_meta["source_hashes"][path] == rtx_meta["source_hashes"][path], path
    for account in mac_meta["accounts"].values():
        assert account["epsilon_consumed"] <= account["epsilon_limit"] + 1e-9
        assert account["delta_consumed"] <= account["delta_limit"] + 1e-9
    checks["provenienza_replica"] = {
        "commit_snapshot": provenance["baseline_commit"],
        "file_snapshot_verificati": len(source_hashes),
        "modello_configurazione_corpora_provider_uguali_RTX": True,
        "componenti_sperimentali_principali_uguali_RTX": True,
        "account_entro_limiti_registrati": True,
        "metadata_Mac_originale_disponibile": False,
    }

    entries = json.loads((DATA / "manifest_input.json").read_text())
    assert len(entries) == len(manifest) == 623
    assert sum(r["file_manifest_verificati"] for r in raw_checks.values()) == 623
    assert len(texts) == 292
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    print("Verificati 623 file, 600 richieste, 112 celle e 120 celle C2. Nessuna inferenza.")


if __name__ == "__main__":
    main()
