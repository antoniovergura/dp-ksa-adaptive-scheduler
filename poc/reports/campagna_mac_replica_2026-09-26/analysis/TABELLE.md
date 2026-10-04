# Tabelle della campagna

Stato esecuzione: `complete`. Richieste presenti: 280.

Tempi in secondi; intervalli min–max su cinque repliche (dieci per k). Le frequenze sono osservazioni su questi campioni. Gli intervalli di Wilson al 95% sono in `summary.json`; non correggono dipendenze temporali.

## B_cloud

| Corpus/caso | ε / δ PTR | SLA s | Variante | n | N medio | Tempo medio [min–max] s | Locale s | Cloud s | Rilascio | Sforamenti | Sforamento medio* / max s | Errori |
|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|---|---:|
| ticket/procedura_e42 | 4 / 0.0001 | 5.63 | k_0 | 10 | 0.0 | 19.17 [13.53–23.57] | 0.00 | 19.17 | 0/10 | 10/10 | 13.54 / 17.94 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 5.63 | k_0.1 | 10 | 0.0 | 15.30 [11.41–19.46] | 0.00 | 15.30 | 0/10 | 10/10 | 9.67 / 13.83 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 5.63 | k_0.25 | 10 | 5.0 | 18.24 [14.66–22.79] | 2.95 | 15.28 | 0/10 | 10/10 | 12.61 / 17.16 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 5.63 | k_0.5 | 10 | 5.0 | 19.48 [14.90–25.19] | 3.03 | 16.44 | 0/10 | 10/10 | 13.85 / 19.56 | 0 |
## C1_cloud

| Corpus/caso | ε / δ PTR | SLA s | Variante | n | N medio | Tempo medio [min–max] s | Locale s | Cloud s | Rilascio | Sforamenti | Sforamento medio* / max s | Errori |
|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|---|---:|
| squad/super_bowl | 1 / 0.0001 | 60.00 | adaptive | 5 | 40.0 | 17.86 [16.58–21.51] | 13.15 | 4.70 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| squad/super_bowl | 8 / 0.01 | 60.00 | adaptive | 5 | 40.0 | 22.82 [20.37–25.00] | 13.05 | 9.76 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/dettaglio_unico | 8 / 0.01 | 60.00 | adaptive | 5 | 40.0 | 24.56 [22.04–29.15] | 15.81 | 8.74 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 8 / 0.01 | 60.00 | adaptive | 5 | 40.0 | 35.64 [34.29–37.36] | 24.64 | 10.98 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
## C3_cloud

| Corpus/caso | ε / δ PTR | SLA s | Variante | n | N medio | Tempo medio [min–max] s | Locale s | Cloud s | Rilascio | Sforamenti | Sforamento medio* / max s | Errori |
|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|---|---:|
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | adaptive | 5 | 20.0 | 30.88 [27.76–33.95] | 13.16 | 17.71 | 0/5 | 5/5 | 15.88 / 18.95 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | fixed_20 | 5 | 20.0 | 28.52 [26.04–32.66] | 11.70 | 16.81 | 0/5 | 5/5 | 13.52 / 17.66 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | fixed_40 | 5 | 40.0 | 41.81 [34.72–50.93] | 26.54 | 15.26 | 2/5 | 5/5 | 26.81 / 35.93 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | adaptive | 5 | 40.0 | 45.84 [40.85–50.75] | 26.02 | 19.81 | 1/5 | 5/5 | 15.84 / 20.75 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | fixed_20 | 5 | 20.0 | 28.23 [26.70–30.09] | 11.96 | 16.26 | 0/5 | 1/5 | 0.02 / 0.09 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | fixed_40 | 5 | 40.0 | 41.02 [38.82–43.55] | 24.92 | 16.09 | 1/5 | 5/5 | 11.02 / 13.55 | 0 |
## C3_high_cloud

| Corpus/caso | ε / δ PTR | SLA s | Variante | n | N medio | Tempo medio [min–max] s | Locale s | Cloud s | Rilascio | Sforamenti | Sforamento medio* / max s | Errori |
|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|---|---:|
| ticket/procedura_e42 | 8 / 0.01 | 15.00 | adaptive | 5 | 20.0 | 25.04 [20.52–27.33] | 12.19 | 12.84 | 4/5 | 5/5 | 10.04 / 12.33 | 0 |
| ticket/procedura_e42 | 8 / 0.01 | 15.00 | fixed_20 | 5 | 20.0 | 23.41 [19.36–26.74] | 11.93 | 11.47 | 4/5 | 5/5 | 8.41 / 11.74 | 0 |
| ticket/procedura_e42 | 8 / 0.01 | 15.00 | fixed_40 | 5 | 40.0 | 37.41 [35.04–39.53] | 24.43 | 12.97 | 5/5 | 5/5 | 22.41 / 24.53 | 0 |
| ticket/procedura_e42 | 8 / 0.01 | 30.00 | adaptive | 5 | 40.0 | 41.01 [38.63–47.98] | 23.93 | 17.08 | 5/5 | 5/5 | 11.01 / 17.98 | 0 |
| ticket/procedura_e42 | 8 / 0.01 | 30.00 | fixed_20 | 5 | 20.0 | 29.08 [27.43–30.94] | 11.81 | 17.26 | 4/5 | 2/5 | 0.33 / 0.94 | 0 |
| ticket/procedura_e42 | 8 / 0.01 | 30.00 | fixed_40 | 5 | 40.0 | 37.75 [32.47–51.11] | 24.43 | 13.31 | 5/5 | 5/5 | 7.75 / 21.11 | 0 |
## C3_offline

| Corpus/caso | ε / δ PTR | SLA s | Variante | n | N medio | Tempo medio [min–max] s | Locale s | Cloud s | Rilascio | Sforamenti | Sforamento medio* / max s | Errori |
|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|---|---:|
| salary/base_t | 4 / 0.0001 | 5.00 | adaptive | 5 | 8.0 | 2.88 [2.48–3.40] | 2.87 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 5.00 | fixed_10 | 5 | 10.0 | 3.78 [3.48–4.01] | 3.77 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 5.00 | fixed_20 | 5 | 20.0 | 7.06 [6.56–7.25] | 7.05 | 0.00 | 3/5 | 5/5 | 2.06 / 2.25 | 0 |
| salary/base_t | 4 / 0.0001 | 5.00 | fixed_40 | 5 | 40.0 | 14.66 [12.56–17.82] | 14.65 | 0.00 | 5/5 | 5/5 | 9.66 / 12.82 | 0 |
| salary/base_t | 4 / 0.0001 | 5.00 | fixed_5 | 5 | 5.0 | 1.77 [1.51–2.01] | 1.76 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 15.00 | adaptive | 5 | 25.0 | 9.17 [7.71–9.84] | 9.16 | 0.00 | 4/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 15.00 | fixed_10 | 5 | 10.0 | 3.61 [3.44–3.78] | 3.60 | 0.00 | 1/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 15.00 | fixed_20 | 5 | 20.0 | 7.15 [6.00–8.92] | 7.14 | 0.00 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 15.00 | fixed_40 | 5 | 40.0 | 14.44 [13.81–15.02] | 14.43 | 0.00 | 5/5 | 1/5 | 0.00 / 0.02 | 0 |
| salary/base_t | 4 / 0.0001 | 15.00 | fixed_5 | 5 | 5.0 | 1.78 [1.57–1.92] | 1.77 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 30.00 | adaptive | 5 | 40.0 | 14.73 [13.07–16.48] | 14.72 | 0.00 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 30.00 | fixed_10 | 5 | 10.0 | 3.86 [3.48–4.38] | 3.86 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 30.00 | fixed_20 | 5 | 20.0 | 7.40 [6.70–7.78] | 7.39 | 0.00 | 2/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 30.00 | fixed_40 | 5 | 40.0 | 14.56 [12.75–16.36] | 14.55 | 0.00 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
| salary/base_t | 4 / 0.0001 | 30.00 | fixed_5 | 5 | 5.0 | 1.68 [1.51–1.79] | 1.67 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 5.00 | adaptive | 5 | 8.0 | 5.70 [4.64–6.83] | 5.69 | 0.00 | 0/5 | 4/5 | 0.77 / 1.83 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 5.00 | fixed_10 | 5 | 10.0 | 6.77 [6.31–7.47] | 6.76 | 0.00 | 0/5 | 5/5 | 1.77 / 2.47 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 5.00 | fixed_20 | 5 | 20.0 | 13.13 [12.40–14.30] | 13.12 | 0.00 | 0/5 | 5/5 | 8.13 / 9.30 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 5.00 | fixed_40 | 5 | 40.0 | 25.43 [22.73–29.65] | 25.42 | 0.00 | 3/5 | 5/5 | 20.43 / 24.65 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 5.00 | fixed_5 | 5 | 5.0 | 3.65 [2.77–4.05] | 3.65 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | adaptive | 5 | 25.0 | 16.54 [14.03–18.21] | 16.53 | 0.00 | 0/5 | 4/5 | 1.74 / 3.21 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | fixed_10 | 5 | 10.0 | 6.19 [5.63–7.06] | 6.18 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | fixed_20 | 5 | 20.0 | 12.63 [10.91–14.20] | 12.62 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | fixed_40 | 5 | 40.0 | 25.60 [23.44–27.64] | 25.59 | 0.00 | 0/5 | 5/5 | 10.60 / 12.64 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 15.00 | fixed_5 | 5 | 5.0 | 3.11 [2.77–3.53] | 3.10 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | adaptive | 5 | 40.0 | 26.12 [23.14–30.72] | 26.11 | 0.00 | 3/5 | 1/5 | 0.14 / 0.72 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | fixed_10 | 5 | 10.0 | 6.16 [5.41–6.73] | 6.15 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | fixed_20 | 5 | 20.0 | 13.15 [11.58–14.96] | 13.14 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | fixed_40 | 5 | 40.0 | 28.41 [26.78–30.93] | 28.40 | 0.00 | 1/5 | 1/5 | 0.19 / 0.93 | 0 |
| ticket/procedura_e42 | 4 / 0.0001 | 30.00 | fixed_5 | 5 | 5.0 | 3.41 [3.10–4.24] | 3.41 | 0.00 | 0/5 | 0/5 | 0.00 / 0.00 | 0 |
## D_cloud

| Corpus/caso | ε / δ PTR | SLA s | Variante | n | N medio | Tempo medio [min–max] s | Locale s | Cloud s | Rilascio | Sforamenti | Sforamento medio* / max s | Errori |
|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|---|---:|
| ticket/dettaglio_condiviso | 8 / 0.01 | 60.00 | adaptive | 5 | 40.0 | 17.66 [15.32–20.49] | 12.29 | 5.35 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |
| ticket/errore_assente | 8 / 0.01 | 60.00 | adaptive | 5 | 40.0 | 33.62 [30.52–37.50] | 21.56 | 12.04 | 5/5 | 0/5 | 0.00 / 0.00 | 0 |

*Media dello sforamento su tutte le richieste, includendo gli zeri. La media condizionata agli sforamenti è nel JSON. La qualità delle risposte simulate non è valutata.
