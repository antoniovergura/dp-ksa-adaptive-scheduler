# Campagna sul Mac — protocollo del 19 settembre 2026

Esecuzione autorizzata dall'utente con provider e Langfuse configurati nel `.env`.
Solo i corpus sintetici verificati contro i manifest e il benchmark pubblico
SQuAD; nessuna lettura del resto del vault. Il runner è `campaign_measurements.py`,
che richiama `core.pipeline.run_request`, come la CLI supportata `run_pipeline.py`.
Non modifica scheduler, prompt, retrieval o filtro DP-KSA.

Prima esecuzione interrotta dopo 20 richieste offline: l'engine ripeteva
la generazione quando mancava `usage` nello stream. I report originali
erano registrati in `reports/campagna_2026-09-19` (non presente in questa copia) come prova preliminare,
esclusa dai confronti finali. La correzione `9d6bdb0` elimina la seconda
generazione e identifica i conteggi ottenuti dal testo ritokenizzato.
La campagna completa è ripartita il 20 settembre in una directory nuova,
con nuova calibrazione e nuovo probe; non si mescolano le due esecuzioni.

## Disegno fissato prima delle misure

| Blocco | Configurazione | Ripetizioni / richieste |
| --- | --- | ---: |
| C4 | Decisioni default/calibrazione; SLA 1,5/5/15/30 s; soli input pubblici | 8 decisioni |
| C3 offline | Ticket E42 e salario T2; SLA 5/15/30 s; adattivo e N=5/10/20/40; ε=4, δ PTR=0,0001 | 5 per cella, 150 richieste |
| C1 cloud | Super Bowl ε=1 δ=0,0001 ed ε=8 δ=0,01; ticket procedura e codice ε=8 δ=0,01; SLA 60 s | 5 per caso, 20 richieste |
| C3 cloud | Ticket E42; SLA 15/30 s; adattivo e N=20/40; ε=4 δ=0,0001, come offline | 5 per cella, 30 richieste |
| C3 cloud budget ampio | Stessa griglia, ε=8 δ=0,01, come prove preliminari | 5 per cella, 30 richieste |
| B cloud | E42; k=0/0,1/0,25/0,5; SLA=piano minimo−0,2×probe; ε=4 δ=0,0001 | 10 per k, 40 richieste |
| D cloud | Identificativo condiviso e errore assente E99; ε=8 δ=0,01; SLA 60 s | 5 per caso, 10 richieste |
| C2 offline | 4 query ticket e salario A1; N=5/10/20/40 × ε=1/4/8; δ PTR=0,0001 | 500 rumori per cella, 30.000 repliche |

Totale pianificato: 280 richieste alla pipeline (150 offline, 130 cloud),
una chiamata pubblica di probe, 200 inferenze locali aggiuntive per C2 e tre
prove pubbliche di calibrazione. Nelle repliche C2 le bozze sono congelate:
non sono 30.000 nuove inferenze né misure di latenza end-to-end.

Ordine casuale entro ciascun blocco, seed 20260919; inferenze e richieste in
sequenza per evitare concorrenza sul modello. Modello precaricato una volta,
calibrazione e probe una volta nella sessione; relativi costi separati.
I blocchi restano in ordine dichiarato: possibili derive termiche/temporali
fra blocchi sono un limite. I tempi offline escludono un provider reale;
non attribuire qualità al testo simulato. Nel confronto cloud/offline usare
ε e δ identici; tenere separata la condizione con budget ampio.

## Accounting e osservabilità

Un account cumulativo per corpus e coppia (ε,δ), condiviso tra query e blocchi
della pipeline. Limiti fissati dal numero pianificato di chiamate; scala del
rumore sempre riferita all'ε per richiesta. Nessun reset durante la campagna,
nessun aumento di budget motivato dagli esiti. I consumi effettivi e i limiti
sono nel manifest finale. Le diverse configurazioni hanno account distinti:
non interpretare il solo ε di una richiesta come protezione dell'intera campagna.
Per i corpus comuni si possono sommare conservativamente ε e δ dei relativi
account, ottenendo limiti molto ampi; questi sono esperimenti pubblici,
non impostazioni raccomandate per un deployment riservato.

Le repliche C2 con seed e account nuovi sono diagnostica su dati sintetici
pubblici e restano locali. Non attribuire loro la protezione di una sessione.
Langfuse è attivo nelle prove cloud se l'autenticazione riesce, secondo la
configurazione esistente. Report, bozze, tempi e trace sono diagnostica
sperimentale fuori dalla garanzia DP del rilascio al provider.

Client cloud con timeout 60 s e zero retry: ogni errore resta nei risultati;
dopo tre errori consecutivi si interrompe la parte cloud, conservando la
campagna offline. Nessuna sostituzione di provider o dei risultati falliti.
Si registrano modello restituito, token fatturabili se esposti e stato HTTP
sanitizzato. Il costo monetario non è deducibile senza tariffa verificata.

## Misure e limiti dello strumento

Per richiesta: N, inferenze effettive, token locali, tempo totale, retrieval,
inferenze, filtro, chiamata cloud, stima, frequenza/entità sforamenti, rilascio,
risposta e label euristica. Revisione dell'utilità separata dalle label: ordine
e completezza della procedura, fatti sbagliati, astensioni e dettagli inventati.
Report e risposte sono salvati dopo ogni richiesta; errore del provider non
equivale a risposta utile. Le cinque repliche danno indicazioni esplorative,
non stime robuste di eventi rari.

L'attuale calibrazione usa una separazione euristica fra prefill e generazione:
le velocità così ottenute non sono misure indipendenti delle due fasi.
`prefill_real_ms` registra il tempo al primo elemento dello stream locale,
distinto dalla stima del prefill; non coincide con il TTFT cloud, non disponibile.
Il probe usa 16 token, la risposta fino a 1024: misurare l'errore di previsione
senza sostituire a posteriori il probe con tempi osservati su query del corpus.
I byte dei report sono volumi di testo, non traffico effettivo di rete.

Hardware: flusso JSON originale di `macmon` ogni 5 s, mantenendo nomi, unità,
frequenze, rapporti di utilizzo, memoria, potenze e temperature disponibili.
Si conserva il formato originale perché alcuni campi del modulo del PoC
chiamati `*_pct` riportano i rapporti ricevuti senza conversione percentuale.
Valori mancanti e temperature sentinella zero non sono misure valide.
La potenza del sistema include altri processi del Mac: non attribuirla tutta
al modello. Nessuna conclusione cross-platform: l'utente ha scelto solo il Mac.

## Esecuzione

Da `poc/`, con accesso a rete, acceleratore Metal e sensori:

```bash
.venv/bin/python campaign_measurements.py --cloud --trials 500 \
  --output reports/campagna_2026-09-20

.venv/bin/python analyze_campaign.py reports/campagna_2026-09-20 \
  --output reports/campagna_2026-09-20/analysis
```

La directory deve essere nuova. Le esecuzioni interrotte restano consultabili;
non riprenderle creando silenziosamente un nuovo account. Il manifest contiene
hash del modello e dei corpus, versione del codice e dipendenze effettive.
