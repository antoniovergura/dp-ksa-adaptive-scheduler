"""Avvia una nuova replica con sorgenti storiche e credenziali esterne allo snapshot."""

import hashlib
import json
import os
import runpy
import sys
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
POC = HERE.parent.parent
RUNTIME = HERE / "runtime"
OUTPUT = POC / "reports/campagna_mac_replica_2026-09-26"

if OUTPUT.exists():
    raise SystemExit("Directory già esistente: una campagna non viene ripresa con nuovi account.")
provenance = json.loads((HERE / "provenienza.json").read_text())
for entry in provenance["snapshot_files"]:
    source = RUNTIME / entry["path"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != entry["sha256"]:
        raise SystemExit(f"Sorgente storica modificata: {entry['path']}")

load_dotenv(POC / ".env")
expected = json.loads((POC / "reports/campagna_rtx_2026-09-21/metadata.json").read_text())
model = os.environ.get("CLOUD_MODEL") or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
host = urlsplit(os.environ.get("CLOUD_BASE_URL") or os.environ.get("OPENAI_BASE_URL", "")).hostname
if model != expected["provider"]["model"] or host != expected["provider"]["host"]:
    raise SystemExit("Provider o modello diversi dalla campagna di riferimento.")
model_path = RUNTIME / "models" / expected["model_config"]["filename"]
with model_path.open("rb") as handle:
    if hashlib.file_digest(handle, "sha256").hexdigest() != expected["model_sha256"]:
        raise SystemExit("Il modello locale non corrisponde all'hash storico.")

sys.path.insert(0, str(RUNTIME))
from benchmark_salary_demo import verify_corpus  # noqa: E402
from core.dataset import DatasetLoader  # noqa: E402

corpora = {
    "ticket": verify_corpus(RUNTIME / "docs/ticket_demo")[0],
    "salary": verify_corpus(RUNTIME / "docs/azienda_demo")[0],
    "squad": DatasetLoader().as_corpus(),
}
for name, corpus in corpora.items():
    digest = hashlib.sha256("\n".join(d.id for d in corpus.documents).encode()).hexdigest()
    if digest != expected["corpus_hashes"][name]:
        raise SystemExit(f"Il corpus {name} non corrisponde all'hash storico.")

os.chdir(RUNTIME)
sys.argv = [str(RUNTIME / "campaign_measurements.py"), "--cloud", "--trials", "500", "--output", str(OUTPUT)]
runpy.run_path(str(RUNTIME / "campaign_measurements.py"), run_name="__main__")
