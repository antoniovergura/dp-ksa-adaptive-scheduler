# Inventario dei dati sperimentali

Stato aggiornato al 26 settembre 2026. Il confronto corrente usa la **replica Mac del 26 settembre** e i grezzi RTX già conservati. I nomi `mac/` e `linux/` designano raccolte complementari; non identificano le campagne principali da 280 richieste usate nell’analisi corrente.

| Percorso | Contenuto verificato |
|---|---|
| [mac/](mac/) | 35 JSON: 31 report di singole richieste, due benchmark con rispettivamente 18 e 47 richieste conservate, due snapshot di configurazione/hardware |
| [linux/](linux/) | La stessa struttura: 35 JSON, con benchmark da 18 e 47 richieste conservate |
| [latenza_cloud_mac.json](latenza_cloud_mac.json) | 20 osservazioni individuali di probe cloud e statistiche |
| [latenza_cloud_linux.json](latenza_cloud_linux.json) | 20 osservazioni individuali di probe cloud e statistiche |
| [valutazione_mac_rtx_2026-09-26/](valutazione_mac_rtx_2026-09-26/) | **Analisi corrente**: 600 richieste tutte disponibili in forma grezza, 112 celle, 120 celle C2, 300 giudizi e 292 testi distinti; 623 file nel manifest, annotazioni, CSV e grafici |
| [campagna_mac_replica_2026-09-26/](campagna_mac_replica_2026-09-26/) | Nuova campagna completa: 280 richieste (150 con cloud simulato, 130 reale), cinque file C2 con 30.000 repliche condizionali, metadata e 1.031 campioni hardware; 291 file nel manifest |
| [replica_mac_2026-09-26_sorgenti/](replica_mac_2026-09-26_sorgenti/) | Snapshot storico eseguito, corpus, hash, ambiente effettivo, log e verifica preliminare |
| [valutazione_mac_rtx_2026-09-22/](valutazione_mac_rtx_2026-09-22/) | **Analisi storica conservata**: 600 richieste, 112 celle, 120 celle C2, 300 giudizi e 290 testi distinti. La parte Mac del 20 settembre resta priva dei grezzi originari |
| [campagna_rtx_2026-09-21/](campagna_rtx_2026-09-21/) | 280 risultati grezzi, metadata, cinque file C2 e dati ausiliari. Tutti i 291 file elencati dal manifest presenti e con hash corrispondente |
| [confronto_rtx_2026-09-21/](confronto_rtx_2026-09-21/) | 40 risultati grezzi e metadata. Tutti i 41 file elencati dal manifest presenti e con hash corrispondente |
| `campagna_2026-09-20/` | **Assente nella copia attuale**: il manifest richiede 291 file, fra cui i 280 risultati della campagna principale Mac |

I due benchmark in ogni cartella complementare pianificavano 150 e 50 richieste, ma ne conservano rispettivamente 18 e 47. Il numero di file non coincide con il numero di richieste e le raccolte non vanno sommate o sostituite fra loro senza considerare il protocollo.

Il [verificatore](../scripts/verify_experiments.py) ricalcola tutte le 112 celle dalle 600 richieste correnti, confronta le 120 celle C2 con i dieci file originari e controlla i 623 hash del [manifest corrente](valutazione_mac_rtx_2026-09-26/manifest_input.json). Verifica inoltre che i 332 file storici RTX/confronto e i relativi 170 giudizi siano invariati e che lo snapshot eseguito corrisponda agli hash registrati.

La nuova esecuzione sostituisce la campagna Mac perduta nel confronto corrente, senza ricostruire o sovrascrivere le misure del 20 settembre. I valori delle due esecuzioni differiscono e rimangono separati. I 35 JSON di `mac/` non sono un recupero di quella campagna.

I controlli e la rigenerazione delle analisi non richiedono nuove inferenze. Le repliche C2 sono ripetizioni del filtro su bozze congelate, distinte dalle richieste ai modelli e dai test software.
