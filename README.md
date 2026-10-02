# Adaptive Physics-Informed Dynamic Bayesian Network (API-DBN)

Implementation, reproduction scripts, and manuscript files for the study:

> **"An Adaptive Physics-Informed Framework for Subsea Pipeline Reliability and Maintenance"**  
> Devesh Shukla and Vinay Kumar  
> Department of Computer Science and Engineering, IIIT Naya Raipur, India

---

## Overview

Subsea pipelines are subject to gradual corrosion thinning and discrete external or operational shock damage. These two degradation processes interact: corrosion weakens the pipe wall, making it more vulnerable to shock effects, while shocks remove protective coatings and accelerate subsequent corrosion drift.

This repository provides an independent implementation and experimental evaluation of the **Adaptive Physics-Informed Dynamic Bayesian Network (API-DBN)**. The method combines:
1. Continuous-time corrosion physics (Wiener process) coupled with Poisson shock arrivals.
2. Burst failure criterion adapted from simplified DNV-RP-F101 / ASME B31G formulations.
3. Sequential Monte Carlo (SMC) particle filtering with Metropolis-Hastings (MH) rejuvenation to jointly estimate latent degradation states and update evolving drift and arrival parameters as inspection data arrive.
4. Monte Carlo forward propagation for remaining useful life (RUL) prediction.
5. Closed-loop evaluation of risk- and cost-based maintenance policies.

---

## Key Contributions

- **Parametric Corrosion–Shock Coupling**: Direct two-way coupling via continuous sigmoid drift acceleration and exponential shock vulnerability.
- **Sequential Joint State–Parameter Updating**: Simultaneous tracking of latent defect depths and online adaptation of drifting degradation rates from periodic in-line inspections.
- **Uncertainty Calibration**: API-DBN's primary advantage over static DBN models is calibrated uncertainty estimation (95.3% prediction interval coverage vs. 59.9% for static DBN).
- **Closed-Loop Maintenance Evaluation**: Empirical policy optimization under true simulated asset degradation rather than self-consistent forecast scoring.

---

## Repository Structure

```
adaptive-physics-informed-dbn/
├── README.md               # Main project documentation
├── LICENSE                 # MIT License
├── CITATION.cff            # Citation metadata
├── requirements.txt        # Python package dependencies
├── pyproject.toml          # Package installation config
├── pytest.ini              # Test configuration
│
├── src/                    # Implementation source code
│   ├── apidbn/             # Core library package
│   │   ├── core.py         # Physics, burst pressure, coupling equations
│   │   ├── truth.py        # Ground truth pipeline degradation simulator
│   │   ├── filters.py      # SMC filter, MCMC rejuvenation, baseline models
│   │   ├── maintenance.py  # Closed-loop maintenance simulator and cost functions
│   │   └── metrics.py      # RUL, CRPS, Brier, PICP, and statistical tests
│   ├── model/              # Model and physics interfaces
│   ├── inference/          # Filtering and prognostic forecasting interfaces
│   ├── maintenance/        # Maintenance optimization interfaces
│   └── baselines/          # Baseline configurations (Fixed Wiener, Static DBN, Oracle)
│
├── experiments/            # Experiment execution scripts
│   ├── run_experiments.py  # Master dispatcher and summary runner
│   ├── run_scenario_a.py   # Scenario A runner (literal static parameters)
│   ├── run_scenario_b.py   # Scenario B runner (heterogeneous drifting parameters)
│   ├── run_ablation.py     # 2x2 factorial ablation analysis
│   ├── run_checks.py       # Closed-form physics checks and figure replicas
│   ├── run_maintenance.py  # Maintenance policy evaluation
│   ├── extend_gamma.py     # Extended maintenance grid evaluation (gamma <= 5 yr)
│   ├── run_rul.py          # Parallel RUL simulation driver
│   ├── aggregate_rul.py    # Aggregation and statistical testing
│   ├── make_latex.py       # LaTeX table generator
│   ├── make_paper_figures.py # Paper figure generator
│   └── bsee_records.py     # BSEE/PHMSA external consistency checks
│
├── configs/                # Configuration files
│   ├── model_params.json   # Physical degradation parameters (Table IV)
│   ├── cost_params.json    # Economic and maintenance parameters (Table V)
│   └── experiment_params.json # Simulation and inference settings
│
├── results/                # Deterministic outputs and evaluation summaries
│   ├── rul/                # RUL summary tables (Scenario A & B)
│   ├── maintenance/        # Maintenance optimization results
│   ├── ablation/           # Ablation study summaries
│   ├── sensitivity/        # Parameter sensitivity analysis (W0, alpha, rs, M, J)
│   ├── bsee/               # BSEE/PHMSA consistency summary (with SHA-256 hashes)
│   ├── latex_tables.tex    # Generated publication tables
│   └── raw_results.zip     # Complete per-task arrays for all 30 seeds
│
├── figures/                # Standalone replica output figures
├── paper/                  # Manuscript files and publication figures
│   ├── manuscript.pdf      # Compiled manuscript
│   ├── manuscript.tex      # LaTeX source
│   ├── references.bib      # Verified BibTeX references
│   └── figures/            # Manuscript figures (fig1 to fig6)
│
├── data/
│   └── README.md           # Dataset download instructions and file checksums
│
├── docs/                   # Detailed documentation
│   ├── methodology.md      # Mathematical derivation and algorithm details
│   ├── reproducibility.md  # Step-by-step reproduction instructions
│   └── changes.md          # Log of scientific revisions and clarifications
│
└── tests/
    └── test_core.py        # 10 unit tests for physics, filters, and metrics
```

---

## Main Results

The table below reports RUL forecasting performance under **Scenario B** (mean $\pm$ standard deviation across 30 matched runs; 9,990 pipelines; 121,091 forecasts per model):

| Model | MAE (yr) | RMSE (yr) | CRPS (yr) | Brier (2-yr) | PICP (95% Interval) |
|---|---|---|---|---|---|
| Fixed Wiener | 1.37 $\pm$ 0.08 | 1.96 $\pm$ 0.14 | 1.04 $\pm$ 0.07 | 0.031 $\pm$ 0.002 | 75.0% |
| Static DBN | 1.38 $\pm$ 0.09 | 2.05 $\pm$ 0.16 | 1.12 $\pm$ 0.08 | 0.032 $\pm$ 0.002 | 59.9% |
| PF w/o MCMC | 1.12 $\pm$ 0.04 | 1.73 $\pm$ 0.08 | 0.80 $\pm$ 0.03 | 0.022 $\pm$ 0.001 | 95.2% |
| No coupling | 2.29 $\pm$ 0.07 | 3.39 $\pm$ 0.10 | 1.67 $\pm$ 0.05 | 0.027 $\pm$ 0.001 | 77.5% |
| **API-DBN** | **1.12 $\pm$ 0.04** | **1.72 $\pm$ 0.08** | **0.80 $\pm$ 0.03** | **0.021 $\pm$ 0.001** | **95.3%** |
| Oracle (true parameters) | 0.70 $\pm$ 0.03 | 1.04 $\pm$ 0.06 | 0.50 $\pm$ 0.02 | 0.018 $\pm$ 0.001 | 95.4% |

### Key Observations:
- **API-DBN vs. Static DBN**:
  - MAE is reduced by **18.6%** ($1.38 \to 1.12$ yr; paired $t_{29} = 17.7, p < 10^{-16}$).
  - CRPS is reduced by **28.7%** ($1.12 \to 0.80$ yr; paired $t_{29} = 23.6, p < 10^{-20}$).
  - PICP: 95% central intervals cover true RUL in **95.3%** of forecasts for API-DBN (Wilson 95% CI $[95.2\%, 95.4\%]$), compared to only **59.9%** for the Static DBN.
- **Scientific Takeaway**: The main strength of adaptive Bayesian parameter updating is uncertainty calibration. Because the Static DBN assumes constant fleet-wide rates, it produces overconfident, poorly calibrated prediction intervals. API-DBN adapts to asset-specific drift, restoring correct nominal coverage.

---

## Maintenance Optimization Results

Closed-loop lifecycle maintenance evaluation over a 20-year horizon for 1,500 simulated pipelines (inspections cost $30k, preventive replacements $100k, failures $15M total, discounted at 5%):

| Decision Model | Best Policy ($I^*$, $\gamma^*$) | Expected Cost | Pipeline Failure Rate | Cost at Paper's Policy ($I=2, \gamma=1.5$) |
|---|---|---|---|---|
| Static DBN | $I=2.5$ yr, $\gamma=4.5$ yr | $\$425.0\mathrm{k} \pm 4.2\mathrm{k}$ | 0.07% | $\$2,324\mathrm{k}$ (20.5% fail) |
| **API-DBN** | **$I=4.0$ yr, $\gamma=5.0$ yr** | **$\$353.5\mathrm{k} \pm 4.8\mathrm{k}$** | **0.07%** | $\$1,449\mathrm{k}$ (12.8% fail) |
| Oracle | $I=4.0$ yr, $\gamma=4.5$ yr | $\$342.1\mathrm{k} \pm 11.1\mathrm{k}$ | 0.27% | $\$1,457\mathrm{k}$ (13.2% fail) |

*(Note on initial grid $\gamma \le 3.0$ yr: Static DBN was $\$573\mathrm{k}$ at $I=2.0, \gamma=3.0$; API-DBN was $\$394\mathrm{k}$ at $I=2.5, \gamma=3.0$; Oracle was $\$385\mathrm{k}$ at $I=2.5, \gamma=3.0$.)*

### Important Limitations:
1. **Grid Boundary**: The API-DBN and Oracle optima lie on the boundary of the evaluated grid ($I = 4.0$ yr, $\gamma = 5.0$ yr). They should not be claimed as unconstrained global optima without searching wider intervals.
2. **Policy Thresholds**: Under policies where $\gamma < I$ (such as $I=2.0, \gamma=1.5$), pipelines that degrade to near-failure between inspections are left unreplaced, resulting in 13–21% of pipelines experiencing burst failure.

---

## Experimental Setup

- **Matched Runs**: 30 independent runs with seeds 0 to 29.
- **Sample Sizes**:
  - Scenario B: 333 pipelines per seed (9,990 pipelines total, 121,091 RUL evaluations).
  - Scenario A: 100 pipelines per seed (3,000 pipelines total, 36,090 RUL evaluations).
  - Maintenance: 1,500 pipelines operated over 20 years.
- **Discretization**: Time step $\Delta t = 0.1$ yr ($K = 200$ steps over 20-year horizon).
- **Inspections**: Annual in-line inspections from $t = 1.0$ yr with noise $\sigma_v = 0.10$ mm.
- **Particles**: $M = 1,000$ particles per filter; resampling when $\mathrm{ESS} < M / 2$.
- **Prognostics**: $J = 10,000$ Monte Carlo forward trajectories per forecast; point prediction is the predictive median.
- **Brier Score Window**: Failure within 2.0 years.

---

## Scenario A vs. Scenario B

- **Scenario B (Adaptive Setting)**: Asset-specific baseline parameters vary across pipelines according to $(\mu^{(0)}, \lambda^{(0)}, \sigma_B) = \text{Table IV} \times \exp(\mathcal{N}(0, 0.25^2))$, drifting annually via log-random walks ($\sigma_{\mathrm{rw}} = 0.05$/yr). This represents the real-world condition where operating environments differ and evolve.
- **Scenario A (Literal Baseline Setting)**: All pipelines share identical, fixed Table IV parameters. Under this setting:
  - Fixed Wiener: $\mathrm{MAE} = 0.58 \pm 0.03$ yr
  - Static DBN: $\mathrm{MAE} = 0.48 \pm 0.03$ yr
  - API-DBN: $\mathrm{MAE} = 0.93 \pm 0.04$ yr
  - Oracle: $\mathrm{MAE} = 0.48 \pm 0.03$ yr
  
  When the true parameters are constant and already known, the Static DBN matches the Oracle, and online parameter estimation adds unnecessary sampling variance. Both scenarios are documented to demonstrate *when* adaptation is beneficial.

---

## Ablation Study

A 2x2 factorial evaluation of adaptive configurations (Scenario B, MAE in years):

| Configuration | Coupling OFF | Coupling ON |
|---|---|---|
| **MCMC OFF (PF)** | 2.29 | 1.12 |
| **MCMC ON (API-DBN)** | 2.29 | 1.12 |

### Key Findings:
1. **Coupling**: Removing the corrosion-shock coupling roughly doubles the MAE ($1.12 \to 2.29$ yr; paired $t_{29} = 90.5, p < 10^{-36}$). Without coupling, the filter cannot anticipate acceleration, creating a persistent $+2.1$ yr forecast bias.
2. **MCMC Rejuvenation**: The Metropolis-Hastings rejuvenation step has no measurable effect under the current formulation ($\Delta\mathrm{MAE} < 0.001$ yr, paired $t_{29} = -0.05, p = 0.96$). With state paths held fixed during rejuvenation, the MH move only explores the local random-walk spread already provided by state propagation. It is documented as an ablation rather than a source of accuracy.

---

## Role of BSEE / PHMSA Data

The BSEE and PHMSA incident and location records from NETL ([doi:10.18141/2280823](https://doi.org/10.18141/2280823)) are **not** used as training, validation, or test data. They serve strictly for three external consistency checks:

1. **Pipe Dimension**: The 24-inch case study is a large trunkline (only ~1.5% of installed Gulf of Mexico segments are $\ge 24$ in).
2. **Shock Rate**: Historical incident frequency is $\le 0.0051$ per segment-year, approximately 160 times lower than $\lambda = 0.8$/yr; therefore $\lambda$ is treated as an analytical assumption.
3. **Failure Cost**: The assumed $C_{\mathrm{fail}} = \$5\mathrm{M}$ exceeds 91.7% of reported historical incident cleanup costs.

See [data/README.md](data/README.md) for data download details and SHA-256 verification hashes.

---

## Reproducibility

### Installation
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
```

### Reproduce Figures and Tables
```bash
# Re-generate LaTeX tables (results/latex_tables.tex)
python experiments/make_latex.py

# Re-generate publication figures (paper/figures/)
python experiments/make_paper_figures.py

# Inspect 2x2 ablation summary
python experiments/run_ablation.py --scenario B

# Or run all summary generators via the master script
python experiments/run_experiments.py --all-summaries
```

### Full Simulation Runs
```bash
# Physics verification checks (~30s)
python experiments/run_checks.py

# Scenario B RUL simulation (multiprocessed)
python experiments/run_scenario_b.py --pipes 333 --seeds 30

# Scenario A RUL simulation
python experiments/run_scenario_a.py --pipes 100 --seeds 30

# Closed-loop maintenance simulation
python experiments/run_maintenance.py --scenario B --pipes 1500
```

---

## Unit Tests

The test suite in [tests/test_core.py](tests/test_core.py) contains 10 unit tests:
1. `test_critical_depth_solves_eq9`: Confirms burst failure equation root equals $12.07$ mm.
2. `test_sigmoid_is_not_baseline_at_zero_damage`: Verifies drift multiplier is $1.38$ at $Z = 0$.
3. `test_mean_shock_damage_matches_integral`: Tests expected shock damage calculation ($0.166$ mm).
4. `test_wiener_moments_without_shocks_or_coupling`: Verifies Wiener process variance and drift scaling.
5. `test_deterministic_forecast_hits_threshold_on_time`: Checks trajectory stopping times.
6. `test_mcmc_leaves_random_walk_prior_invariant_without_data`: Checks MCMC proposal symmetry.
7. `test_mcmc_samples_exact_shock_rate_posterior`: Checks posterior convergence on known Poisson data.
8. `test_crps_matches_gaussian_closed_form`: Validates CRPS implementation against analytical normal distribution.
9. `test_fixed_wiener_mean_is_distance_over_drift`: Validates inverse-Gaussian baseline formula.
10. `test_filter_tracks_state_and_learns_drift`: Tests joint particle filter state tracking and drift estimation.

Run all tests:
```bash
pytest
```

---

## Citation

```bibtex
@article{shukla2026apidbn,
  author  = {Shukla, Devesh and Kumar, Vinay},
  title   = {An Adaptive Physics-Informed Framework for Subsea Pipeline Reliability and Maintenance},
  journal = {Preprint},
  year    = {2026}
}
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
