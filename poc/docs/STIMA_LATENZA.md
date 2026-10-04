# Stima diretta della latenza — esperimento del 21 settembre 2026

CLI e REPL usano per default `--stima-latenza diretta`. `--stima-latenza legacy`
conserva la precedente calibrazione per throughput e il probe cloud breve.
`--no-calibration` mantiene il percorso manuale precedente, incluso il probe storico.
Le campagne storiche e `benchmark_scheduler.py` conservano il metodo legacy.

La modalità diretta misura sei inferenze complete su contesti pubblici diversi,
troncati con il tokenizer reale al cap configurato, includendo il troncamento nel
costo. Due query richiedono risposte brevi, quattro sequenze di identificativi
pubblici che esercitano il limite di output. I token realmente osservati sono nel
profilo; se nessuna prova raggiunge il limite (tolleranza due token per il
riconteggio del testo), CLI/REPL segnalano copertura incompleta. Non si forza la
lunghezza, non si separano artificialmente prefill e generazione. Il profilo è
valido solo con gli stessi limiti e il modello precaricato che lo ha prodotto.

Il cloud viene misurato con tre richieste pubbliche attraverso `genera`, stesso
template, modello, temperatura e limite di output delle richieste reali: sintesi
di procedura, identificativo breve e risposta senza keyword. Rete già inclusa.
Una risposta vuota o un errore invalida il setup, senza selezionare soltanto le
prove riuscite. In simulazione il costo cloud è zero; non rappresenta un provider.

`tempo_atteso_ms` somma le medie locali e cloud e la riserva accessoria.
`tempo_stimato_ms` conserva il ruolo storico di stima usata per pianificare, ora
somma dei massimi osservati e della riserva. `margine_stima_ms` ne è la differenza.
Capacità, fattibilità, piano minimo, tolleranza e sforamento previsto usano sempre
la stessa stima prudenziale. N fisso può superarla; N=0 può comunque sforare se il
cloud da solo eccede lo SLA. I massimi sono riserve empiriche, non percentili o
garanzie statistiche. Il margine non elimina la necessità di validazione separata.

`--overhead-ms` aggiunge una riserva pubblica per retrieval, filtro e altri costi;
default zero, **non misurati automaticamente**. Il tempo reale include questi
costi. Il caricamento del modello è fuori dalle misure a modello caldo; con
calibrazione disattivata il primo caricamento può essere dentro `request_ms`.

La REPL aggiorna il profilo locale ogni cinque domande (`--ricalibra-ogni`, zero
disabilita), mediante tre nuove prove pubbliche prima dello scheduler. Il report
`public_recalibration` registra costo ed eventuale fallimento; un fallimento
conserva il profilo precedente fino al prossimo intervallo. Il cloud resta
calibrato all'avvio. Nessun tempo, testo o lunghezza del corpus alimenta il profilo.

## Prova e confronto

Da `poc/`:

```bash
.venv/bin/python run_pipeline.py --documents docs/ticket_demo/documenti \
  --query 'Come si risolve E42?' --epsilon 8 --delta 0.01 \
  --max-latency-ms 30000 --offline-cloud --no-telemetry \
  --output reports/prova_stima_diretta.json

.venv/bin/python benchmark_latency.py --cloud \
  --output reports/confronto_stima
```

Il secondo comando esegue 40 richieste: E42, SLA 15/30 s, cinque ripetizioni di
legacy, diretto fisso, diretto aggiornato e N=20 fisso. Ordine mescolato per
replica, stesso modello precaricato e account cumulativo per l'intera campagna.
Le impostazioni privacy sono fissate a ε=8, δ PTR=0,01 per richiesta; il corpus
sintetico viene verificato tramite manifest. I tre probe di aggiornamento sono
eseguiti ogni cinque richieste della variante aggiornata. Non si cambia N durante
una richiesta. La campagna è continua, senza pause per raffreddamento.

Il confronto riporta errore medio con segno, errore assoluto medio, sforamenti,
sottostime della previsione prudenziale, N e rilascio. Gli errori provider sono
contati e non trattati come risposte utili o campioni validi di accuratezza.
La correttezza delle risposte richiede revisione: rilascio e label non bastano.
Il costo delle calibrazioni è salvato separatamente. Timeout cloud 60 s, zero
retry e arresto dopo tre errori consecutivi. Ogni richiesta è salvata subito;
un riepilogo parziale viene scritto anche in caso di errore. I report non sono DP.

La campagna completa storica (`campaign_measurements.py`) aggiunge su Linux
snapshot CPU/GPU e frequenza NVIDIA, mantenendo il percorso di macmon su Mac.
I sensori assenti restano mancanti; la potenza GPU non è attribuita alla CPU,
e la VRAM NVIDIA viene convertita da MiB a GiB. La durata effettiva fra campioni
comprende il costo delle letture, oltre all'attesa di cinque secondi.
