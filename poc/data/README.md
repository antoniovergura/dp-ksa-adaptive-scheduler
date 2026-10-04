# Corpora pubblici

`squad_real_benchmark.json` contiene 100 contesti distinti campionati dal set di sviluppo SQuAD 1.1. Ogni record conserva l’identificativo della domanda, l’argomento, il contesto e le risposte di riferimento. `cases_benchmark.json` seleziona le domande e le risposte attese dei primi dieci record per i benchmark complementari. `corpus/` conserva gli estratti testuali usati come documenti locali.

La fonte è il [dataset SQuAD di Stanford](https://rajpurkar.github.io/SQuAD-explorer/), di Pranav Rajpurkar e collaboratori, distribuito con licenza [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). I brani provengono da Wikipedia. Questi dati mantengono la propria licenza, distinta dalla BSD del codice del prototipo.

Il campionamento e la conversione dei campi sono descritti in [fetch_real_dataset.py](../scripts/fetch_real_dataset.py), che scarica il [set di sviluppo originale](https://rajpurkar.github.io/SQuAD-explorer/dataset/dev-v1.1.json). Per riprodurre i risultati archiviati usare la copia conservata, senza sovrascriverla con un nuovo download.

I corpora principali di ticket IT e salari sono sintetici e si trovano in [ticket_demo](../docs/ticket_demo/README.md) e [azienda_demo](../docs/azienda_demo/README.md), con manifest e hash dei documenti.
