"""Produce il rapporto comparativo da grezzi, metriche e giudizi verificabili."""

import json
import re
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
BASE = OUT.parent


def read(path):
    return json.loads(path.read_text())


def fmt(value, digits=2):
    return f"{value:.{digits}f}".replace(".", ",")


settings = read(OUT / "campagne.json")
campaigns = settings["campaigns"]
metrics = read(OUT / "metriche.json")
cells = read(OUT / "celle.json")
c2 = read(OUT / "C2_condizionale.json")
checks = read(OUT / "verifica_dati.json")
reviews = read(OUT / "valutazioni_risposte.json")
metas = {p: read(BASE / c / "metadata.json") for p, c in campaigns.items()}
old = read(BASE / "valutazione_mac_rtx_2026-09-22/metriche.json")

lines = [
    "# Valutazione delle campagne Mac e RTX — replica Mac del 26 settembre 2026", "",
    "Il confronto principale usa la nuova campagna Mac del 26 settembre e le campagne RTX e confronto degli stimatori del 21 settembre. Sono nuove soltanto le misure Mac. L'archivio Mac del 20 settembre resta mancante: i suoi aggregati sono conservati nel [rapporto storico](../valutazione_mac_rtx_2026-09-22/RAPPORTO_COMPARATIVO.md), senza essere mescolati alla replica.", "",
    "## Dati e provenienza", "",
    "| Raccolta | Richieste | Cloud reale | Cloud simulato | Repliche C2 | Campioni hardware |",
    "|---|---:|---:|---:|---:|---:|",
]
for p, row in checks["campaigns"].items():
    lines.append(f"| {p} | {row['requests']} | {row['cloud']} | {row['offline']} | {row['conditional_trials']} | {row['hardware_samples']} |")
lines += [
    "", f"Sono conservati i grezzi delle 600 richieste usate nel confronto, le 112 celle, le 120 celle C2 e i 300 giudizi riferiti a {checks['unique_reviewed_texts']} testi distinti. Errori del provider: " + ", ".join(f"{p} {r['provider_errors']}" for p, r in checks["campaigns"].items()) + ".", "",
    "La replica utilizza sorgenti archiviate del commit `8b770e0`. Gli hash dei componenti sperimentali principali coincidono con quelli nei metadata RTX; runner e telemetria differiscono. Modello, configurazione e corpus sono uguali secondo i rispettivi hash. Le versioni dei pacchetti e le condizioni reali vengono registrate nuovamente: il metadata Mac originale manca, quindi non si certifica l'identità completa dell'ambiente del 20 settembre.", "",
    "Modello locale Qwen2.5 0.5B Q4_K_M, contesto 4.096, limite di 30 token e temperatura 0,2. Provider `xiaomi/mimo-v2.5` su `api.commandcode.ai`, timeout 60 secondi, zero retry. Solo dati sintetici o pubblici. Report, bozze, tempi e telemetria non sono output DP.", "",
    "| Ambiente | Mac replica | RTX originale |", "|---|---|---|",
    f"| Piattaforma | {metas['Mac']['platform']} | {metas['RTX']['platform']} |",
    f"| Python | {metas['Mac']['python']} | {metas['RTX']['python']} |",
]
for package in metas["Mac"]["packages"]:
    lines.append(f"| {package} | {metas['Mac']['packages'][package]} | {metas['RTX']['packages'].get(package, 'non registrato')} |")
lines += ["", "Il confronto è fra sistemi completi osservati in giorni diversi; non isola la GPU e non controlla il carico del provider. Il seed governa l'ordine delle prove, non garantisce identità delle risposte o del rumore della pipeline.", "",
          "Fonti: [protocollo della replica](../../misurazioni/REPLICA_MAC_2026-09-26.md), [provenienza dei sorgenti](../replica_mac_2026-09-26_sorgenti/provenienza.json), [manifest dei dati](manifest_input.json), [metadata Mac](../campagna_mac_replica_2026-09-26/metadata.json), [metadata RTX](../campagna_rtx_2026-09-21/metadata.json).", "",
          "## Tempi locali a N fisso", "",
          "Ogni valore comprende 15 richieste offline, distribuite sui tre SLA. Il rapporto usa le medie della componente locale.", "",
          "| Caso | N | Mac (s) | RTX (s) | Mac/RTX |", "|---|---:|---:|---:|---:|"]
for row in metrics["fixed_n"]:
    case = "Procedura E42" if row["corpus"] == "ticket" else "Retribuzione T2"
    lines.append(f"| {case} | {row['n']} | {fmt(row['Mac']['edge_s']['mean'], 3)} | {fmt(row['RTX']['edge_s']['mean'], 3)} | {fmt(row['speedup_edge_ratio_means'])} |")
lines += ["", "![Tempi locali](01_tempi_locali.png)", "", "### Variazione durante le campagne", "",
          "Prime e ultime cinque richieste a N=40 per corpus; le frequenze sono medie sui campioni hardware che ricadono nelle finestre delle richieste. Il confronto è osservazionale.", "",
          "| Piattaforma | Caso | Finestra | Locale (s) | Token visibili | Frequenza GPU (MHz) |", "|---|---|---|---:|---:|---:|"]
for p, rows in metrics["drift"].items():
    for row in rows:
        freq = row["gpu_frequency_mhz"].get("mean")
        lines.append(f"| {p} | {row['corpus']} | {row['window']} | {fmt(row['edge_ms']['mean'] / 1000)} | {fmt(row['completion_tokens_visible']['mean'], 1)} | {fmt(freq, 0) if freq is not None else 'n.d.'} |")
lines += ["", "![Variazione dei tempi durante le campagne](02_deriva.png)", "", "## Pianificazione e cloud", "",
          "I probe iniziali misurano " + ", ".join(f"{fmt(metas[p]['probe']['e2e_cloud_ms'] / 1000, 3)} s per {p}" for p in ["Mac", "RTX"]) + ". Hanno limite di 16 token, contro 1.024 per le risposte. Gli otto calcoli C4 per macchina sono decisioni senza nuove richieste alla pipeline.", "",
          "| Piattaforma | SLA C4 (s) | N predefinito | N calibrato |", "|---|---:|---:|---:|"]
for p in ["Mac", "RTX"]:
    decisions = read(BASE / campaigns[p] / "c4_decisions.json")
    for sla in sorted({r["config"]["sla_ms"] for r in decisions}):
        selected = {r["mode"]: r["decision"]["n_ensemble"] for r in decisions if r["config"]["sla_ms"] == sla}
        lines.append(f"| {p} | {fmt(sla / 1000, 1)} | {selected['default']} | {selected['calibrated']} |")
lines += ["", "Le decisioni C4 mantengono il costo cloud predefinito e isolano il cambiamento dei coefficienti locali. Le richieste C3 seguenti includono invece il probe della piattaforma.", "",
          "| Piattaforma | SLA (s) | N | Totale (s) | Locale (s) | Cloud (s) | Sforamenti | Nucleo entro SLA |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
for row in cells:
    if row["phase"] == "C3_high_cloud" and row["variant"] == "adaptive":
        lines.append(f"| {row['platform']} | {row['sla_s']:g} | {row['n_mean']:g} | {fmt(row['request_s']['mean'])} | {fmt(row['edge_s']['mean'])} | {fmt(row['cloud_s']['mean'])} | {row['violations']}/{row['runs']} | {row['success_within_sla']}/{row['runs']} |")
lines += ["", "Il confronto degli stimatori resta quello RTX conservato, con cinque richieste per cella. Il MAE usa il tempo atteso; lo SLA e la previsione prudenziale sono controlli distinti.", "",
          "| Variante | SLA (s) | N medio | MAE (s) | Sforamenti | Rilasci | Nucleo entro SLA |", "|---|---:|---:|---:|---:|---:|---:|"]
for row in metrics["comparator"]:
    lines.append(f"| {row['variant']} | {row['sla_s']:g} | {row['n_mean']:g} | {fmt(row['mae_s'])} | {row['violations']}/{row['runs']} | {row['release_count']}/{row['runs']} | {row['success_within_sla']}/{row['runs']} |")
lines += ["", "La stima diretta statica riduce il MAE rispetto alla precedente di circa il 44% a 15 secondi e il 19% a 30 secondi nel confronto RTX. A 15 secondi riduce N da 40 a 31 e i nuclei corretti entro SLA passano da tre a due su cinque. Non è dimostrata una superiorità generale. La replica Mac misura lo scheduler storico e non estende al Mac la validazione della stima diretta.", "",
          "![Errore di previsione nel confronto RTX](03_stime.png)", "",
          "### Tolleranza sul piano minimo", "",
          "| Piattaforma | SLA (s) | k | N medio | Sforamenti | Nuclei corretti |", "|---|---:|---|---:|---:|---:|"]
for row in cells:
    if row["phase"] == "B_cloud":
        lines.append(f"| {row['platform']} | {fmt(row['sla_s'], 3)} | {row['variant']} | {row['n_mean']:g} | {row['violations']}/{row['runs']} | {row['success']}/{row['runs']} |")
lines += ["", "Le scadenze B derivano dalla calibrazione e dal probe di ogni macchina e quindi differiscono. Il fallback N=0 continua a chiamare il cloud.", "",
          "## Filtro condizionale e bozze", "",
          "Ogni cella C2 comprende 500 repliche del filtro su bozze congelate, con delta totale 0,0002. Non sono nuove richieste ai modelli e non formano una sessione protetta di 60.000 interrogazioni.", "",
          "| Piattaforma | Caso | N | ε | Almeno una parola | Tutti i gruppi E42 / target |", "|---|---|---:|---:|---:|---:|"]
for row in c2:
    if row["case"] in {"procedura_e42", "base_a", "errore_assente", "dettaglio_condiviso"} and row["n"] in {20, 40}:
        epsilon = row.get("epsilon", row.get("epsilon_per_trial"))
        if epsilon not in {4, 8}:
            continue
        target = row.get("all_step_terms_rate", row.get("target_recovery_rate"))
        lines.append(f"| {row['platform']} | {row['case']} | {row['n']} | {epsilon:g} | {fmt(row['release_rate'] * 100, 1)}% | {fmt(target * 100, 1) + '%' if target is not None else 'n.a.'} |")
draft_diagnostics = {}
for p in ["Mac", "RTX"]:
    drafts = read(BASE / campaigns[p] / "c2_ticket_procedura_e42.json")["local_outputs"]
    salary = read(BASE / campaigns[p] / "c2_salary_base_a.json")["local_outputs"]
    draft_diagnostics[p] = {
        "e42_drafts": len(drafts),
        "restart_mentions": sum(bool(re.search(r"riavvi|restart", row["testo"], re.I)) for row in drafts),
        "at_30_tokens": sum(row["completion_tokens"] == 30 for row in drafts),
        "salary_last_20_texts": dict(Counter(row["testo"] for row in salary[20:])),
    }
    d = draft_diagnostics[p]
    lines += ["", f"{p}: {d['restart_mentions']}/40 bozze E42 contengono un riferimento lessicale al riavvio; {d['at_30_tokens']}/40 raggiungono 30 token. Le bozze complete sono conservate nei file C2. Questi conteggi descrivono il testo e non attribuiscono causalmente le differenze al troncamento."]
    salary_counts = "; ".join(f"{count} volte `{value}`" for value, count in d["salary_last_20_texts"].items())
    lines += ["", f"{p}, controllo salariale A1: le venti bozze aggiunte passando da N=20 a N=40 contengono {salary_counts}. Sono valori degli altri reparti, distinti dal target 36.000."]
lines += ["", "![Filtro condizionale su bozze congelate](05_filtro_condizionale.png)", "",
          "Il rilascio di un termine condiviso non equivale a una violazione dimostrata della privacy per documento. Allo stesso modo, rilasciare parole per E99 non prova che la procedura richiesta sia presente nei documenti.", "",
          "## Utilità delle risposte", "",
          "La revisione è dell'assistente, non di un valutatore umano indipendente. I giudizi RTX e confronto sono conservati; quelli nuovi sono collegati ai testi Mac nella [revisione commentata](RISPOSTE_COMMENTATE.md). Le etichette automatiche non sostituiscono la lettura semantica.", "",
          "| Piattaforma | Caso | Risposte | Successi valutabili | Successi entro SLA | E42 senza aggiunte materiali |", "|---|---|---:|---:|---:|---:|"]
for row in metrics["quality"]:
    success = f"{row['success']}/{row['evaluable']}" if row["evaluable"] else "non valutabile"
    lines.append(f"| {row['platform']} | {row['case']} | {row['runs']} | {success} | {row['success_within_sla']} | {row['e42_no_material_extra'] if row['case'] == 'procedura_e42' else 'n.a.'} |")
lines += ["", "![Categorie della revisione E42](04_qualita.png)", "",
          "Il nucleo E42 richiede arresto, cancellazione della cache e riavvio nell'ordine previsto. La categoria C_extra ammette il nucleo ma segnala dettagli o operazioni non documentati; non equivale a una procedura affidabile da eseguire. Il codice individuale ha target ambiguo e resta escluso dal denominatore di correttezza.", "",
          "## Rapporto con la campagna Mac perduta", "",
          "La tabella seguente confronta i nuovi tempi locali con gli aggregati storici conservati, a fini di trasparenza. La colonna storica non è ricalcolabile dai grezzi Mac originari e non entra nelle tabelle del nuovo confronto.", "",
          "| Caso | N | Mac 20 settembre, aggregato storico (s) | Mac 26 settembre, nuovi grezzi (s) |", "|---|---:|---:|---:|"]
for row in metrics["fixed_n"]:
    previous = next(r for r in old["fixed_n"] if r["corpus"] == row["corpus"] and r["n"] == row["n"])
    lines.append(f"| {row['corpus']} | {row['n']} | {fmt(previous['Mac']['edge_s']['mean'], 3)} | {fmt(row['Mac']['edge_s']['mean'], 3)} |")
lines += ["", "## Limiti e riproduzione", "",
          f"Il confronto degli stimatori registra un consumo cumulativo ε={fmt(metas['Confronto']['cumulative_epsilon'])} e δ={fmt(metas['Confronto']['cumulative_delta'])}, nei [metadata originali](../confronto_rtx_2026-09-21/metadata.json). Questi valori diagnostici su dati sintetici non descrivono una forte protezione per un’intera sessione con dati riservati.", "",
          "Cinque ripetizioni per molte celle consentono una descrizione esplorativa, non garanzie di servizio. La variabilità del provider, le condizioni del Mac e le differenze fra backend rimangono confondenti. I giudizi semantici richiedono revisione umana; tempi, hardware e report sono fuori dalla garanzia DP. Le impostazioni diagnostiche e i budget cumulativi non sono raccomandazioni per dati riservati.", "",
          "Per ricalcolare i risultati senza nuove inferenze: eseguire `analizza.py` e `genera_rapporto.py` in questa cartella con l'ambiente Python del progetto. `annotazioni.json` conserva i giudizi, `risposte_uniche.json` i testi, `manifest_input.json` gli hash delle fonti. Il programma `poc/scripts/verify_experiments.py` ricalcola le celle dai 600 grezzi e verifica hash, annotazioni, corpora e provenienza.", ""]
(OUT / "RAPPORTO_COMPARATIVO.md").write_text("\n".join(lines))
(OUT / "diagnostica_bozze.json").write_text(json.dumps(draft_diagnostics, ensure_ascii=False, indent=2) + "\n")
print("Rapporto comparativo generato dai dati conservati.")
