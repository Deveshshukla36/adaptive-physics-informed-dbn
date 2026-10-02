## Scenario A: RUL prediction (mean ± s.d. over 30 matched runs)

| Model | MAE (yr) | RMSE (yr) | CRPS (yr) | Brier (2-yr window) | PICP (pooled, Wilson 95%) | N cases |
|---|---|---|---|---|---|---|
| Fixed Wiener | 0.58 ± 0.03 | 0.75 ± 0.03 | 0.41 ± 0.02 | 0.019 ± 0.002 | 92.7% [92.5, 93.0] | 36090 |
| Static DBN | 0.48 ± 0.03 | 0.64 ± 0.04 | 0.34 ± 0.02 | 0.016 ± 0.002 | 95.6% [95.4, 95.9] | 36090 |
| PF w/o MCMC | 0.93 ± 0.04 | 1.38 ± 0.07 | 0.66 ± 0.03 | 0.019 ± 0.002 | 97.5% [97.4, 97.7] | 36090 |
| No coupling | 2.13 ± 0.11 | 3.15 ± 0.16 | 1.52 ± 0.08 | 0.022 ± 0.002 | 83.5% [83.1, 83.9] | 36090 |
| API-DBN | 0.93 ± 0.04 | 1.38 ± 0.06 | 0.66 ± 0.03 | 0.019 ± 0.002 | 97.6% [97.4, 97.7] | 36090 |
| No coupling, w/o MCMC | 2.13 ± 0.12 | 3.15 ± 0.17 | 1.52 ± 0.09 | 0.022 ± 0.002 | 83.2% [82.8, 83.6] | 36090 |
| Oracle (true parameters) | 0.48 ± 0.03 | 0.64 ± 0.04 | 0.34 ± 0.02 | 0.016 ± 0.002 | 95.6% [95.4, 95.8] | 36090 |

Paired t-tests against API-DBN over the matched runs (df = n_seeds - 1):

| Model | ΔMAE | t | p | ΔCRPS | t | p |
|---|---|---|---|---|---|---|
| Fixed Wiener | -0.350 | -41.8 | 1.8e-27 | -0.255 | -46.8 | 7.3e-29 |
| Static DBN | -0.443 | -56.0 | 4.2e-31 | -0.323 | -61.4 | 2.9e-32 |
| PF w/o MCMC | -0.001 | -0.4 | 7.0e-01 | -0.001 | -0.4 | 6.9e-01 |
| No coupling | +1.206 | 64.1 | 8.5e-33 | +0.860 | 64.1 | 8.5e-33 |
| No coupling, w/o MCMC | +1.207 | 60.6 | 4.4e-32 | +0.861 | 60.1 | 5.3e-32 |
| Oracle (true parameters) | -0.443 | -55.8 | 4.6e-31 | -0.323 | -61.5 | 2.9e-32 |

Table VII as a true 2x2 factorial (all four are adaptive; MAE, yr):

| | Coupling off | Coupling on |
|---|---|---|
| MCMC off | 2.13 | 0.93 |
| MCMC on | 2.13 | 0.93 |

MAE by true remaining life (yr):

| Model | RUL 0-2 | RUL 2-5 | RUL 5-10 | RUL 10-100 |
|---|---|---|---|---|
| Fixed Wiener | 0.24 | 0.51 | 0.73 | 0.63 |
| Static DBN | 0.20 | 0.38 | 0.56 | 0.72 |
| PF w/o MCMC | 0.22 | 0.49 | 1.06 | 1.94 |
| No coupling | 0.30 | 0.85 | 2.50 | 4.94 |
| API-DBN | 0.22 | 0.49 | 1.06 | 1.95 |
| No coupling, w/o MCMC | 0.30 | 0.85 | 2.50 | 4.94 |
| Oracle (true parameters) | 0.20 | 0.38 | 0.56 | 0.72 |
