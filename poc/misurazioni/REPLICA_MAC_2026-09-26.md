# Replica della campagna Mac — 26 settembre 2026

La campagna del 20 settembre resta un esperimento storico con grezzi mancanti: la replica ha una directory, una data, una calibrazione e account propri. I suoi risultati non vengono presentati come recupero dei file perduti. RTX, confronto degli stimatori e benchmark complementari vengono conservati.

## Protocollo fissato prima dell'esecuzione

Si applica la griglia del [protocollo originale](PROTOCOLLO_2026-09-19.md): 280 richieste alla pipeline, di cui 150 con cloud simulato e 130 con provider reale; cinque gruppi C2 con 200 nuove bozze locali e 30.000 repliche condizionali del filtro; otto decisioni C4, tre prove di calibrazione e un probe pubblico separati dalle richieste. Ordine dei blocchi e seed 20260919 invariati, nessuna concorrenza fra inferenze. Si conservano anche errori e interruzioni; non si ripetono selettivamente esiti sfavorevoli.

Si usa lo snapshot del commit `8b770e0`, successivo alla correzione della doppia generazione dello stream. Gli hash delle sorgenti di scheduler, pipeline, modello, generatore cloud, calibrazione, retrieval e privacy coincidono con i metadata della campagna RTX. Runner e telemetria appartengono alla versione Mac di quel commit. Mancando il metadata Mac originale, non si certifica l'identità dell'intero ambiente con quello del 20 settembre. Le dipendenze effettive e i loro numeri di versione saranno registrati nuovamente.

Il modello Qwen2.5 0.5B Q4_K_M, i corpus sintetici ticket/stipendi e il corpus pubblico SQuAD sono controllati contro manifest e hash conservati. Nessun altro documento del vault viene usato come input. Provider e modello devono coincidere con `api.commandcode.ai` e `xiaomi/mimo-v2.5`; timeout 60 secondi e nessun retry. Langfuse usa la configurazione esistente per dati sintetici/pubblici autorizzati. Report, bozze, telemetria e tempi non sono output DP.

## Archiviazione e integrazione

- Sorgenti e provenienza: `../reports/replica_mac_2026-09-26_sorgenti/`.
- Nuovi grezzi: `../reports/campagna_mac_replica_2026-09-26/`.
- Nuova analisi comparativa: `../reports/valutazione_mac_rtx_2026-09-26/`.

Il launcher carica le credenziali dal file locale del progetto senza copiarle nello snapshot. Richiede una directory di output nuova. La campagna salva ogni richiesta completata e il flusso hardware durante l'esecuzione.

Dopo l'esecuzione si verificano completezza, hash e account; si valutano le nuove risposte con la rubrica già usata; si ricalcolano celle, figure e confronti mantenendo i giudizi RTX conservati. Il rapporto corrente viene aggiornato sui nuovi risultati, comprese eventuali differenze rispetto alle conclusioni precedenti. Il rapporto storico del 22 settembre resta consultabile come tale.

## Esito dell’esecuzione

Campagna completata il 26 settembre in 5.164,71 secondi, circa 86 minuti: tutte le 280 richieste previste, senza errori del provider. Le 130 richieste cloud e il probe pubblico costituiscono 131 chiamate reali al provider. Sono state eseguite 6.080 inferenze locali nella pipeline, 200 per preparare le bozze C2 e tre per la calibrazione. Le 30.000 repliche condizionali C2 hanno riusato le bozze e non aggiungono chiamate ai modelli. Sono conservati 1.031 campioni hardware.

I metadata registrano l’ambiente effettivo e gli account entro i limiti configurati. La nuova analisi integra queste misure con le 320 richieste RTX/confronto già presenti: 600 richieste grezze, 623 file nel manifest, 300 giudizi riferiti a 292 testi distinti. I 170 giudizi RTX/confronto sono conservati; i nuovi testi Mac sono stati letti e annotati dall’assistente con la stessa rubrica, senza un valutatore umano indipendente.

La revisione riguarda i risultati nei capitoli 3 e 4, le conclusioni e i riferimenti. Gli aggregati Mac precedenti restano consultabili nel rapporto storico e non entrano nei nuovi calcoli.
