# Misurazioni e riproducibilità

Il [protocollo del 19 settembre](PROTOCOLLO_2026-09-19.md) descrive le campagne principali, ripartite il 20 settembre dopo la correzione della doppia generazione. Il [confronto degli stimatori](../docs/STIMA_LATENZA.md) descrive la prova successiva sulla RTX. Il [rapporto corrente](../reports/valutazione_mac_rtx_2026-09-26/RAPPORTO_COMPARATIVO.md) riporta i risultati e i limiti dell'archivio.

Per verificare ciò che è già presente, dalla root del repository:

```sh
python3 poc/scripts/verify_experiments.py
```

Questo controllo non esegue inferenze e non chiama provider. Verifica 623 hash, ricalcola le 112 celle dalle 600 richieste correnti e confronta le 120 celle C2 con i dieci file originari. Controlla anche corpora, risposte, annotazioni, benchmark complementari e provenienza del codice eseguito. Usa solo la libreria standard di Python. Il confronto corrente è interamente verificabile dai grezzi conservati.

Per rigenerare gli aggregati e il rapporto dai dati archiviati, senza nuove richieste ai modelli:

```sh
poc/.venv/bin/python -m pip install -r poc/requirements-analysis.txt
poc/.venv/bin/python poc/reports/valutazione_mac_rtx_2026-09-26/analizza.py
poc/.venv/bin/python poc/reports/valutazione_mac_rtx_2026-09-26/genera_rapporto.py
python3 poc/scripts/verify_experiments.py
```

Questi due programmi riscrivono solo gli output derivati nell’analisi corrente. I grezzi e le annotazioni rimangono gli input della riproduzione. Per la campagna Mac sono conservati anche [sorgenti e ambiente eseguiti](../reports/replica_mac_2026-09-26_sorgenti/).

Da `poc/`, la verifica software è:

```sh
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest -q
.venv/bin/python run_pipeline.py --dry-run
```

Per nuove misure, i programmi conservati hanno scopi diversi:

| Programma | Scopo |
|---|---|
| `campaign_measurements.py` | Griglia principale su ticket e salari, con calibrazione legacy |
| `benchmark_latency.py` | Confronto fra stima legacy, diretta statica, diretta aggiornata e N=20 |
| `misurazioni/run_campaign.sh` | Raccolte complementari per macchina; salta i file già esistenti |
| `misurazioni/latency_campaign.py` | Campione di probe cloud |
| `benchmark_scheduler.py` | Confronto adattivo/fisso su casi e riferimenti espliciti |
| `benchmark_ticket_demo.py`, `benchmark_salary_demo.py` | Prove sui corpora sintetici e repliche condizionali |

Consultare `--help` dei programmi prima di una nuova campagna e usare una directory diversa da quelle storiche. Le opzioni cloud eseguono chiamate reali. Non rieseguire esperimenti per aggiornare soltanto il testo.

La riproducibilità riguarda metodo, configurazione e dati: due esecuzioni non devono necessariamente produrre le stesse parole. Il filtro è casuale, i tempi variano e i backend possono generare bozze diverse. Il seed dell'ordine non fissa il rumore DP. Le simulazioni cloud non forniscono una misura di qualità del provider.

I risultati principali comprendono 600 richieste nei riepiloghi, non 60.000 richieste: le 60.000 repliche C2 riutilizzano bozze congelate. Test software, campioni C2 e prove reali vanno sempre riportati separatamente.
