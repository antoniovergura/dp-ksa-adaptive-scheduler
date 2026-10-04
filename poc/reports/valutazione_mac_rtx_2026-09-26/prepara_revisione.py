"""Collega testi e origini; mantiene i giudizi storici e richiede quelli nuovi."""

import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
BASE = OUT.parent
OLD = BASE / "valutazione_mac_rtx_2026-09-22"
CAMPAIGNS = json.loads((OUT / "campagne.json").read_text())["campaigns"]


def read(path):
    return json.loads(path.read_text())


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


old_texts = read(OLD / "risposte_uniche.json")
old_reviews = read(OLD / "valutazioni_risposte.json")
known = {(row["case"], row["sha256"]): row for row in old_texts}
annotations_path = OUT / "annotazioni.json"
annotations = read(annotations_path) if annotations_path.exists() else {
    "reviewer": "Codex; revisione dell’assistente, non valutatore umano indipendente",
    "analysis_date": "2026-09-26",
    "codes": {},
    "notes": {},
    "origins": {},
}
existing_path = OUT / "risposte_uniche.json"
existing = read(existing_path) if existing_path.exists() else []
for row in existing:
    known.setdefault((row["case"], row["sha256"]), row)
next_id = 1 + max([int(row["id"][1:]) for row in existing if row["id"].startswith("M")], default=0)
old_judgments = {row["review_id"]: row for row in old_reviews}
texts = {}
requests = 0
for campaign in CAMPAIGNS.values():
    directory = BASE / campaign
    metadata = read(directory / "metadata.json")
    for source in sorted(directory.glob("run_*.json")):
        run = read(source)
        if run["cloud_simulated"]:
            continue
        requests += 1
        case = run.get("case", metadata.get("case", {}))["id"]
        response = run["response"]
        digest = hashlib.sha256(response.encode()).hexdigest()
        key = (case, digest)
        if key not in texts:
            if key in known:
                identifier = known[key]["id"]
                assert known[key]["response"] == response
            else:
                identifier = f"M{next_id:03d}"
                next_id += 1
            texts[key] = {"id": identifier, "case": case, "response": response,
                          "sha256": digest, "runs": []}
            if identifier in old_judgments:
                old = old_judgments[identifier]
                if identifier in annotations["codes"]:
                    assert annotations["codes"][identifier] == old["review_code"]
                annotations["codes"][identifier] = old["review_code"]
                annotations["notes"][identifier] = old["note"]
                annotations["origins"][identifier] = {
                    "date": "2026-09-22", "type": "giudizio_conservato_su_testo_identico",
                    "source": "../valutazione_mac_rtx_2026-09-22/valutazioni_risposte.json",
                }
        texts[key]["runs"].append({
            "campaign": campaign, "file": source.name,
            "n": run["decision"]["n_ensemble"], "keywords": run["released_keywords"],
            "label": run.get("esito", {}).get("label"),
        })

unique = sorted(texts.values(), key=lambda row: row["id"])
used = {row["id"] for row in unique}
for field in ["codes", "notes", "origins"]:
    annotations[field] = {key: value for key, value in annotations[field].items() if key in used}
save("risposte_uniche.json", unique)
save("annotazioni.json", annotations)
pending = [row for row in unique if row["id"] not in annotations["codes"]]
save("da_revisionare.json", pending)
print(f"{requests} richieste cloud presenti; {len(unique)} testi; {len(pending)} giudizi da completare.")
