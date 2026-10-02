# API-DBN replica

An independent re-implementation of the method and experiments in
*"An Adaptive Physics-Informed Framework for Subsea Pipeline Reliability and
Maintenance"* (`../Version_1__API_DBN_overleaf_project.pdf`). It was built from
the manuscript text alone, without the authors' code, to check which reported
numbers a faithful implementation reproduces. The manuscript is not modified.

The list of manuscript changes that follow from these results is in
[`CHANGES_TO_PAPER.md`](CHANGES_TO_PAPER.md).

## Layout

| Path | Contents |
|---|---|
| `apidbn/core.py` | Physics: Eqs. (1)–(9) with Table IV values |
| `apidbn/truth.py` | Ground-truth simulator and the two simulation scenarios |
| `apidbn/filters.py` | Algorithm 1 (SMC with MH rejuvenation), all compared models, fixed-Wiener baseline |
| `apidbn/metrics.py` | MAE, RMSE, CRPS (Eq. 19), Brier (Eq. 20), PICP (Eq. 21), paired t-test (Eq. 22) |
| `apidbn/maintenance.py` | Closed-loop evaluation of the (I, γ) policy, Eqs. (17)–(18) |
| `experiments/run_checks.py` | Closed-form checks, Fig. 4 and Fig. 5 replicas |
| `experiments/run_rul.py` | Table VI/VII replica: 30 matched seeds, all models |
| `experiments/aggregate_rul.py` | Builds the tables, t-tests, coverage, diagnostics |
| `experiments/run_maintenance.py` | Sec. V-B / Fig. 6 replica: policy grid with ground-truth costs |
| `experiments/extend_gamma.py` | Extends that grid from γ ≤ 3 to γ ≤ 5 yr; gives the maintenance numbers used in the revised paper |
| `experiments/run_sensitivity.py` | W₀ / α / r_s sensitivity, convergence in M and J |
| `experiments/make_latex.py` | Replacement LaTeX tables, generated from the result files |
| `experiments/make_paper_figures.py` | The six figures of the revised paper, written to `paper_figures/` |
| `experiments/bsee_records.py` | Sec. IV-A and Table III of the revised paper: summaries of the NETL pipeline and incident records |
| `tests/` | Unit tests (failure depth, sigmoid, shock damage, Wiener moments, MCMC exactness, CRPS, filter tracking) |
| `results/`, `figures/` | Outputs; `results/raw_results.zip` holds the per-task files behind every table |

## Running it

Keep the Python environment **outside** Desktop and Documents. On this Mac
those folders sync to iCloud with "Optimize Mac Storage", and iCloud evicts
files it considers unused. An environment inside the synced folder then fails
with `[Errno 60] Operation timed out` when Python tries to load an evicted
library, which is what interrupted one run here.

```bash
uv venv --python 3.14 ~/.venvs/api-dbn
uv pip install --python ~/.venvs/api-dbn/bin/python numpy scipy matplotlib pytest
cd API-DBN_replica
PY=~/.venvs/api-dbn/bin/python
$PY -m pytest -q                                     # 10 tests
$PY experiments/run_checks.py                        # about 30 s
$PY experiments/run_sensitivity.py                   # a few minutes
$PY experiments/run_rul.py --scenario B --pipes 333  # about 1.5 h on 10 cores
$PY experiments/run_rul.py --scenario A --pipes 100 --chunks 10
$PY experiments/run_maintenance.py --scenario B --pipes 1500
$PY experiments/run_maintenance.py --scenario A --pipes 500
$PY experiments/extend_gamma.py --scenario B --pipes 1500
$PY experiments/aggregate_rul.py B
$PY experiments/aggregate_rul.py A
$PY experiments/make_latex.py
$PY experiments/make_paper_figures.py
```

`bsee_records.py` needs the NETL files, which are not included (the locations table is 493 MB).
Download `pipeline_incidents.csv`, `pipeline_locations.csv` and the two `*_data_dictionary.csv` files
from the EDX submission "U.S. Offshore Pipeline and Reported Incident Datasets" (doi:10.18141/2280823,
<https://edx.netl.doe.gov/dataset/us-offshore-pipeline-and-reported-incident-datasets>) into one folder
outside Desktop and Documents, then run:

```bash
$PY experiments/bsee_records.py --data ~/data/netl_pipelines   # a few seconds
```

It writes `results/bsee_records.json`, including the SHA-256 of each file, so a later download can be
checked against the version used in the paper (downloaded 29 Sep 2026).

Every run is seeded and resumable: each finished task is a file in `results/`,
and rerunning skips it. The per-task files behind the reported tables are in
`results/raw_results.zip`. Unzip it inside `results/` to re-aggregate
(`aggregate_rul.py`, `run_maintenance.py --summarise-only`, `extend_gamma.py --summarise-only`) without rerunning
anything. Results are deterministic. Recomputing a task on the
same software versions reproduces its file bit for bit, which was checked for
one RUL task and one maintenance task. The versions used were Python 3.14.7,
NumPy 2.5.3, SciPy 1.18.1 and Matplotlib 3.11.2.

## What is taken from the manuscript

Eqs. (1)–(10), (12)–(17), Algorithm 1, every value in Tables IV and V,
M = 1,000 particles, J = 10,000 RUL trajectories, K = 200 time steps, resampling
at ESS < M/2, the priors of Algorithm 1, 30 runs with seeds 0–29, and the five
model configurations of Sec. IV-B.

## What the manuscript leaves open, and the choice made here

Each is a single named constant, so it can be changed in one place.

| Open point | Choice | Where |
|---|---|---|
| Step size Δt | 0.1 yr (K = 200 → the 20-yr horizon of Fig. 4) | `core.DT` |
| Order of rate evaluation in Eqs. (2), (5), (6) | Rates use the state at the start of each step | `core.step` |
| Environmental covariate E_k | 0, so exp(γ₂E) = 1 | `Physics.E_cov` |
| Shock mapping | Eq. (4) as printed, ΔS = κY^η with Y ~ N(0.32, 0.15²) truncated at 0 | `Physics.shock_map` |
| Prior "Γ(2, 0.2, 5)" | Gamma, shape 2, scale 0.4 (mean 0.8 yr⁻¹ = Table IV), truncated to [0.2, 5] | `filters.sample_prior` |
| σ_σ in Eq. (14) (missing from Table IV) | 0.05 per year, like σ_µ and σ_λ | `FilterConfig.rw_sd` |
| Time unit of the random-walk s.d. | Per year; a slice of length Δ uses s.d. × √Δ | `ParticleFilter.propagate` |
| MCMC proposal and number of sweeps | Gaussian random walk in log-parameters with the slice's random-walk s.d.; 5 sweeps | `FilterConfig.n_mcmc` |
| Inspection schedule in the RUL study | Annual inspections from t = 1 yr, within the 20-yr window | `Scenario.insp_interval` |
| When RUL is scored | At every inspection before the true failure | `run_rul.run_task` |
| Point prediction | Median of the J RUL samples | `metrics.summarize` |
| Brier "evaluation window" | Failure within 2 years | `metrics.BRIER_WINDOW` |
| How the ground truth varies | Scenario A (literal) and scenario B (heterogeneous, drifting); see below | `truth.SCENARIOS` |
| Fixed-Wiener baseline | Linear Wiener on Z with drift and diffusion fitted offline to 2,000 training pipelines; state = latest observation | `FixedWiener.calibrate` |
| Static DBN | Same physics and filter with the Table IV parameters held fixed | `MODELS["SDBN"]` |
| Planning horizon, maintenance | 20 years; inspections at kI < 20; replacement resets damage to 0 | `maintenance.Costs` |
| Decision forecast size | 2,000 paths per decision (the 10% exceedance probability has SE ≈ 0.007) | `run_maintenance --J` |

## Simulation scenarios

- **A, literal.** Every pipeline has exactly the Table IV parameters, which
  never change. This is what Sec. IV-B says ("generated using the model
  parameters in Table IV"). A static model calibrated offline then has the
  true parameters, so parameter adaptation cannot help.
- **B, heterogeneous and drifting.** Each pipeline draws its own
  (µ, λ, σ_B) = Table IV × exp(N(0, 0.25²)), and these drift by a yearly
  log-random walk with the Table IV s.d. of 0.05. This is the situation that
  Sec. II-B and Gap 1 use to motivate adaptive updating.

## Models

Besides the five configurations of the manuscript, two references are added:

- **No coupling, w/o MCMC.** Completes Table VII as a true 2 × 2 factorial.
- **Oracle.** Knows the true parameters. Its error is the floor that no
  model can beat, because the future corrosion noise and shocks are random.
