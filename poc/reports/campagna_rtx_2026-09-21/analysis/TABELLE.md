# Tabelle della campagna

Stato esecuzione: `complete`. Richieste presenti: 280.

Tempi in secondi; intervalli min–max su cinque repliche (dieci per k). Le frequenze sono osservazioni su questi campioni. Gli intervalli di Wilson al 95% sono in `summary.json`; non correggono dipendenze temporali.

## B_cloud

| Corpus/caso | ε / δ PTR | SLA s | Variante | n | N medio | Tempo medio [min–max] s | Locale s | Cloud s | Rilascio | Sforamenti | Sforamento medio* / max s | Errori |
|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|---|---:|
| ticket/procedura_e42 | 4 / 0.0001 | 2.54 | k_0 | 10 | 0.0 | 10.99 [9.12–13.72] | 0.00 | 10.99 | 0/10 | 10/10 | 8.45 / 11.18 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 2.54 | k_0.1 | 10 | 0.0 | 9.49 [7.28–11.74] | 0.00 | 9.49 | 0/10 | 10/10 | 6.95 / 9.20 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 2.54 | k_0.25 | 10 | 5.0 | 11.61 [8.09–21.76] | 0.67 | 10.93 | 0/10 | 10/10 | 9.07 / 19.22 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 2.54 | k_0.5 | 10 | 5.0 | 11.53 [9.11–13.24] | 0.73 | 10.78 | 0/10 | 10/10 | 8.99 / 10.70 | 0 |
## C1_cloud

| Corpus/caso | ε / δ PTR | SLA s | Variante | n | N medio | Tempo medio [min–max] s | Locale s | Cloud s | Rilascio | Sforamenti | Sforamento medio* / max s | Errori |
|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|---|---:|
| squad/super_bowl | 1 / 0.0001 | 60.00 | adaptive | 5 | 40.0 | 5.22 [4.67–6.27] | 2.80 | 2.41 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| squad/super_bowl | 8 / 0.01 | 60.00 | adaptive | 5 | 40.0 | 10.40 [6.43–15.09] | 2.79 | 7.59 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/dettaglio_unico | 8 / 0.01 | 60.00 | adaptive | 5 | 40.0 | 8.42 [6.47–12.02] | 2.74 | 5.65 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 8 / 0.01 | 60.00 | adaptive | 5 | 40.0 | 13.11 [9.80–16.88] | 5.13 | 7.96 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
## C3_cloud

| Corpus/caso | ε / δ PTR | SLA s | Variante | n | N medio | Tempo medio [min–max] s | Locale s | Cloud s | Rilascio | Sforamenti | Sforamento medio* / max s | Errori |
|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|---|---:|
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | adaptive | 5 | 40.0 | 16.44 [13.33–22.55] | 5.16 | 11.26 | 0/5 | 3/5 | 2.09 / 7.55 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | fixed_20 | 5 | 20.0 | 15.41 [11.90–23.21] | 2.64 | 12.75 | 0/5 | 1/5 | 1.64 / 8.21 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | fixed_40 | 5 | 40.0 | 14.59 [13.22–17.28] | 5.19 | 9.39 | 0/5 | 1/5 | 0.46 / 2.28 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | adaptive | 5 | 40.0 | 16.93 [14.92–20.84] | 5.24 | 11.67 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | fixed_20 | 5 | 20.0 | 11.82 [11.01–12.39] | 2.58 | 9.23 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | fixed_40 | 5 | 40.0 | 16.88 [12.90–22.74] | 5.09 | 11.78 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
## C3_high_cloud

| Corpus/caso | ε / δ PTR | SLA s | Variante | n | N medio | Tempo medio [min–max] s | Locale s | Cloud s | Rilascio | Sforamenti | Sforamento medio* / max s | Errori |
|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|---|---:|
| ticket/procedura_e42 | 8 / 0.01 | 15.00 | adaptive | 5 | 40.0 | 15.38 [10.45–24.72] | 5.13 | 10.24 | 5/5 | 2/5 | 2.26 / 9.72 | 0 |
| ticket/procedura_e42 | 8 / 0.01 | 15.00 | fixed_20 | 5 | 20.0 | 12.66 [9.90–14.59] | 2.62 | 10.02 | 1/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 8 / 0.01 | 15.00 | fixed_40 | 5 | 40.0 | 12.62 [9.87–14.33] | 5.17 | 7.44 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 8 / 0.01 | 30.00 | adaptive | 5 | 40.0 | 12.95 [10.29–15.48] | 5.14 | 7.80 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 8 / 0.01 | 30.00 | fixed_20 | 5 | 20.0 | 15.25 [9.32–28.39] | 2.59 | 12.65 | 2/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 8 / 0.01 | 30.00 | fixed_40 | 5 | 40.0 | 12.16 [9.20–14.01] | 5.18 | 6.96 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
## C3_offline

| Corpus/caso | ε / δ PTR | SLA s | Variante | n | N medio | Tempo medio [min–max] s | Locale s | Cloud s | Rilascio | Sforamenti | Sforamento medio* / max s | Errori |
|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|---|---:|
| salary/base_t | 4 / 0.0001 | 5.00 | adaptive | 5 | 23.0 | 1.33 [1.32–1.33] | 1.32 | 0.00 | 2/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 5.00 | fixed_10 | 5 | 10.0 | 0.58 [0.58–0.59] | 0.57 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 5.00 | fixed_20 | 5 | 20.0 | 1.15 [1.14–1.15] | 1.14 | 0.00 | 4/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 5.00 | fixed_40 | 5 | 40.0 | 2.30 [2.28–2.32] | 2.29 | 0.00 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 5.00 | fixed_5 | 5 | 5.0 | 0.30 [0.29–0.31] | 0.29 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 15.00 | adaptive | 5 | 40.0 | 2.30 [2.29–2.31] | 2.29 | 0.00 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 15.00 | fixed_10 | 5 | 10.0 | 0.58 [0.58–0.58] | 0.57 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 15.00 | fixed_20 | 5 | 20.0 | 1.15 [1.15–1.16] | 1.14 | 0.00 | 2/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 15.00 | fixed_40 | 5 | 40.0 | 2.30 [2.30–2.31] | 2.30 | 0.00 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 15.00 | fixed_5 | 5 | 5.0 | 0.29 [0.29–0.30] | 0.29 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 30.00 | adaptive | 5 | 40.0 | 2.30 [2.29–2.32] | 2.29 | 0.00 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 30.00 | fixed_10 | 5 | 10.0 | 0.58 [0.58–0.58] | 0.57 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 30.00 | fixed_20 | 5 | 20.0 | 1.15 [1.15–1.16] | 1.15 | 0.00 | 2/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 30.00 | fixed_40 | 5 | 40.0 | 2.29 [2.28–2.30] | 2.28 | 0.00 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 30.00 | fixed_5 | 5 | 5.0 | 0.29 [0.29–0.30] | 0.28 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 5.00 | adaptive | 5 | 23.0 | 2.94 [2.87–3.02] | 2.93 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 5.00 | fixed_10 | 5 | 10.0 | 1.26 [1.20–1.30] | 1.25 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 5.00 | fixed_20 | 5 | 20.0 | 2.59 [2.44–2.73] | 2.58 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 5.00 | fixed_40 | 5 | 40.0 | 5.10 [5.02–5.26] | 5.09 | 0.00 | 1/5 | 5/5 | 0.10 / 0.26 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 5.00 | fixed_5 | 5 | 5.0 | 0.61 [0.56–0.68] | 0.60 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | adaptive | 5 | 40.0 | 5.18 [5.09–5.24] | 5.17 | 0.00 | 1/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | fixed_10 | 5 | 10.0 | 1.27 [1.10–1.36] | 1.26 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | fixed_20 | 5 | 20.0 | 2.55 [2.45–2.63] | 2.54 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | fixed_40 | 5 | 40.0 | 5.12 [5.06–5.17] | 5.11 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | fixed_5 | 5 | 5.0 | 0.65 [0.55–0.70] | 0.64 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | adaptive | 5 | 40.0 | 5.15 [4.96–5.25] | 5.14 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | fixed_10 | 5 | 10.0 | 1.28 [1.23–1.34] | 1.27 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | fixed_20 | 5 | 20.0 | 2.54 [2.40–2.68] | 2.53 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | fixed_40 | 5 | 40.0 | 5.15 [4.88–5.32] | 5.14 | 0.00 | 1/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | fixed_5 | 5 | 5.0 | 0.67 [0.62–0.70] | 0.66 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
## D_cloud

| Corpus/caso | ε / δ PTR | SLA s | Variante | n | N medio | Tempo medio [min–max] s | Locale s | Cloud s | Rilascio | Sforamenti | Sforamento medio* / max s | Errori |
|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|---|---:|
| ticket/dettaglio_condiviso | 8 / 0.01 | 60.00 | adaptive | 5 | 40.0 | 6.08 [4.76–8.07] | 2.34 | 3.73 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/errore_assente | 8 / 0.01 | 60.00 | adaptive | 5 | 40.0 | 9.42 [6.93–12.10] | 4.31 | 5.11 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |

*Media dello sforamento su tutte le richieste, includendo gli zeri. La media condizionata agli sforamenti è nel JSON. La qualità delle risposte simulate non è valutata.
