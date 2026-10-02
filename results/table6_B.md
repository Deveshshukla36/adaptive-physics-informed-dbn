## Scenario B: RUL prediction (mean ± s.d. over 30 matched runs)

| Model | MAE (yr) | RMSE (yr) | CRPS (yr) | Brier (2-yr window) | PICP (pooled, Wilson 95%) | N cases |
|---|---|---|---|---|---|---|
| Fixed Wiener | 1.37 ± 0.08 | 1.96 ± 0.14 | 1.04 ± 0.07 | 0.031 ± 0.002 | 75.0% [74.7, 75.2] | 121091 |
| Static DBN | 1.38 ± 0.09 | 2.05 ± 0.16 | 1.12 ± 0.08 | 0.032 ± 0.002 | 59.9% [59.7, 60.2] | 121091 |
| PF w/o MCMC | 1.12 ± 0.04 | 1.73 ± 0.08 | 0.80 ± 0.03 | 0.022 ± 0.001 | 95.2% [95.0, 95.3] | 121091 |
| No coupling | 2.29 ± 0.07 | 3.39 ± 0.10 | 1.67 ± 0.05 | 0.027 ± 0.001 | 77.5% [77.2, 77.7] | 121091 |
| API-DBN | 1.12 ± 0.04 | 1.72 ± 0.08 | 0.80 ± 0.03 | 0.021 ± 0.001 | 95.3% [95.2, 95.4] | 121091 |
| No coupling, w/o MCMC | 2.29 ± 0.06 | 3.38 ± 0.10 | 1.67 ± 0.05 | 0.027 ± 0.002 | 77.3% [77.1, 77.5] | 121091 |
| Oracle (true parameters) | 0.70 ± 0.03 | 1.04 ± 0.06 | 0.50 ± 0.02 | 0.018 ± 0.001 | 95.4% [95.3, 95.5] | 121091 |

Paired t-tests against API-DBN over the matched runs (df = n_seeds - 1):

| Model | ΔMAE | t | p | ΔCRPS | t | p |
|---|---|---|---|---|---|---|
| Fixed Wiener | +0.248 | 17.8 | 3.7e-17 | +0.234 | 20.5 | 8.4e-19 |
| Static DBN | +0.256 | 17.7 | 4.6e-17 | +0.322 | 23.6 | 1.8e-20 |
| PF w/o MCMC | -0.000 | -0.1 | 9.6e-01 | +0.000 | 0.2 | 8.4e-01 |
| No coupling | +1.166 | 90.5 | 4.1e-37 | +0.870 | 89.8 | 5.1e-37 |
| No coupling, w/o MCMC | +1.166 | 92.0 | 2.5e-37 | +0.870 | 92.5 | 2.1e-37 |
| Oracle (true parameters) | -0.424 | -82.7 | 5.4e-36 | -0.306 | -83.8 | 3.7e-36 |

Table VII as a true 2x2 factorial (all four are adaptive; MAE, yr):

| | Coupling off | Coupling on |
|---|---|---|
| MCMC off | 2.29 | 1.12 |
| MCMC on | 2.29 | 1.12 |

MAE by true remaining life (yr):

| Model | RUL 0-2 | RUL 2-5 | RUL 5-10 | RUL 10-100 |
|---|---|---|---|---|
| Fixed Wiener | 0.36 | 1.00 | 1.51 | 2.37 |
| Static DBN | 0.32 | 0.84 | 1.39 | 2.84 |
| PF w/o MCMC | 0.24 | 0.57 | 1.21 | 2.32 |
| No coupling | 0.36 | 1.09 | 2.87 | 4.17 |
| API-DBN | 0.24 | 0.57 | 1.22 | 2.32 |
| No coupling, w/o MCMC | 0.36 | 1.09 | 2.87 | 4.17 |
| Oracle (true parameters) | 0.21 | 0.43 | 0.73 | 1.34 |
