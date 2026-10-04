# DP-KSA Adaptive Scheduler

Prototipo Python per studiare uno scheduler adattivo in un sistema RAG ibrido con privacy differenziale. La domanda sperimentale è se scegliere il numero di generazioni locali in base al tempo disponibile sia preferibile a un numero fisso, considerando latenza e utilità delle risposte.

La pipeline parte da una query pubblica, recupera documenti locali e genera una bozza per documento. Un istogramma conta ogni parola al massimo una volta per bozza; FindBestK e TopKWithPTR selezionano le keyword da inviare al modello remoto. L'adattamento di DP-KSA, i riferimenti scientifici e le condizioni della garanzia sono descritti in [Privacy accounting](poc/docs/PRIVACY_ACCOUNTING.md).

## Codice, metodo e dati

- [Architettura](poc/ARCHITECTURE.md): fasi della pipeline e confini di fiducia.
- [Configurazione](poc/docs/CONFIGURATION.md) e [stima della latenza](poc/docs/STIMA_LATENZA.md): opzioni, provider e calibrazione.
- [Protocolli e riproducibilità](poc/misurazioni/PIANO_MISURAZIONI.md): procedure, controlli e comandi per ricalcolare i risultati.
- [Risultati del confronto Mac/RTX](poc/reports/valutazione_mac_rtx_2026-09-26/RAPPORTO_COMPARATIVO.md): analisi corrente, annotazioni, CSV e grafici.
- [Inventario dei dati](poc/reports/LEGGIMI.md): grezzi, manifest, snapshot del codice eseguito e raccolte storiche.

L'analisi corrente comprende **600 richieste alla pipeline**, tutte corredate dai grezzi, e **60.000 repliche condizionali del filtro** su bozze congelate. Le richieste cloud reali sono 300; le altre 300 usano il cloud simulato. I 300 giudizi semantici sono annotazioni dell'assistente e richiedono una revisione umana indipendente. Le celle principali hanno cinque ripetizioni: i risultati descrivono queste configurazioni e non dimostrano una superiorità generale dello scheduler adattivo.

Il confronto usa la campagna Mac del 26 settembre 2026 e le campagne RTX del 21 settembre 2026. Provenienza, differenze degli ambienti e analisi precedenti restano documentate nell'inventario. Il codice corrente e lo snapshot usato negli esperimenti sono identificati separatamente.

Il repository conserva codice, corpora pubblici o sintetici e risultati scientifici. Documenti privati, credenziali, pesi dei modelli e nuovi report locali sono esclusi dal versionamento. La licenza del codice è [BSD 3-Clause](LICENSE); il campione SQuAD conserva la [documentazione del dataset](poc/data/README.md).

## Avvio

Dalla directory `poc/`, con Python 3.10 o successivo. Per creare un ambiente locale:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python run_pipeline.py --dry-run
```

Per documenti propri, specificare un percorso e una query:

```bash
.venv/bin/python run_pipeline.py --documents ./private_documents \
  --query "Qual è la scadenza del progetto?" --dry-run

.venv/bin/python run_pipeline.py --documents ./private_documents \
  --query "Qual è la scadenza del progetto?" --max-latency-ms 60000 \
  --offline-cloud --no-telemetry --output reports/request.json
```

`--dry-run` non esegue modello, provider o telemetria. La seconda esecuzione
usa il modello locale (con download automatico se manca) e simula il cloud.
Per un provider reale configurare `.env` seguendo
[Configurazione](poc/docs/CONFIGURATION.md) e omettere `--offline-cloud`.
Il percorso dei documenti da usare deve essere indicato esplicitamente.

Il caso applicativo principale è un assistente su
[ticket IT sintetici](poc/docs/ticket_demo/README.md): 80 documenti locali
con procedure ricorrenti, clienti, IP, domini e identificativi fittizi.
L'esperimento misura separatamente conservazione della procedura e rilascio
dei dettagli, includendo un identificativo condiviso e un errore assente.
I [risultati locali](poc/docs/ticket_demo/RISULTATI.md) mostrano anche i limiti
del modello e della rappresentazione a keyword.

### Interfaccia interattiva

`poc/repl_interattiva.py` permette di fare domande a turno su un corpus
locale, riusando la stessa pipeline di `run_pipeline.py` ma con un **unico
account privacy cumulativo per tutta la sessione** (epsilon di sessione =
`--epsilon` × `--max-queries`, delta cumulativo esplicito). A budget esaurito
le domande successive passano al fallback zero-shot senza consultare i
documenti e senza addebiti. Il modello locale viene caricato una volta sola.

```bash
.venv/bin/python repl_interattiva.py \
  --documents docs/ticket_demo/documenti --epsilon 4 --max-queries 10
```

I comandi disponibili sono `/help`, `/stats` (stato dell'account), `/docs`
(dimensione del corpus) e `/exit`. Il cloud è simulato per default; con
`--online` si usa il provider configurato in `.env`. I test sono in
`poc/tests/test_repl_interattiva.py`.

Come prova dei limiti, il corpus
[Aurora Demo](poc/docs/azienda_demo/README.md) contiene 80 schede salariali
interamente fittizie, domande con risposte note e comandi per testare il modello
locale, il filtro e lo scheduler. Usare solo la sua sottocartella `documenti/`
come corpus: i risultati e la guida devono restare fuori dal retrieval.

## Scelte sperimentali

CLI e REPL usano per default la stima diretta su probe pubblici. I benchmark storici conservano la stima per throughput/RTT. Lo scheduler usa soltanto limiti e calibrazioni pubblici. Se lo
SLA stimato non consente cinque inferenze, va in zero-shot senza consultare i
documenti. Non promette un limite rigido sulla latenza reale. `--fixed-n` consente
una baseline a N fisso; `benchmark_scheduler.py` confronta le due modalità a
parità di calibrazione, con un account privacy cumulativo e report locali.

FindBestK usa il dominio pubblico 1..10 e conteggi zero impliciti; la scala
Gumbel è 4/epsilon, scelta conservativa ricondotta alla Definizione A.7 del
paper DP-KSA rispetto alla scala 2/epsilon dello pseudocodice. I token rilasciati sono
in ordine alfabetico, così non espongono l'ordine delle frequenze private.
Query diverse sullo stesso corpus non azzerano il budget. La CLI singola
contabilizza una richiesta; un servizio reale deve persistere l'account.

Langfuse permette di osservare le fasi degli esperimenti. Il servizio cloud
si usa con dati pubblici o sintetici autorizzati; con documenti riservati
la telemetria deve restare nel perimetro fidato. La diagnostica, anche redatta, non viene
presentata come output DP.

I tempi della richiesta sono misurati, il prefill rimane stimato e i byte
riguardano il volume del testo, non il traffico effettivo. Le simulazioni cloud
sono esplicite e non ricevono punteggi di qualità.

## Verifiche

```bash
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest -q
```

Il benchmark pubblico si rigenera con
`.venv/bin/python scripts/fetch_real_dataset.py` (SQuAD 1.1, un record per
contesto, campione distribuito nel corpus).

I test usano dati sintetici e dipendenze simulate: non misurano le prestazioni del modello reale e non certificano formalmente la privacy. Per il protocollo delle campagne consultare [le misurazioni](poc/misurazioni/PIANO_MISURAZIONI.md).
