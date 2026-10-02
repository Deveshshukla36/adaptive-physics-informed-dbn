# Reproducibility Protocol

This guide outlines the exact environment, dependencies, commands, and expected numerical outputs to reproduce all results, figures, and tables reported in the manuscript.

---

## 1. Environment Setup

### 1.1 Requirements
- Python $\ge$ 3.10 (tested on Python 3.14.0 on Windows and macOS)
- Standard scientific stack: NumPy, SciPy, Matplotlib, pytest

### 1.2 Installation

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows PowerShell:
.venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

---

## 2. Experimental Protocol

### 2.1 Simulation Scenarios
The study reports two simulation settings:

1. **Scenario B (Primary Adaptive Setting)**:
   - Evaluates adaptive calibration and drift tracking.
   - Each pipeline draws unique baseline parameters:
     $(\mu^{(0)}, \lambda^{(0)}, \sigma_B) = \text{Table IV} \times \exp(\mathcal{N}(0, 0.25^2))$
   - Parameters drift annually via log-random walks with $\sigma_{\mathrm{rw}} = 0.05$ per year.
   - 30 matched runs (seeds 0–29), 333 pipelines per seed (9,990 pipelines total).
   - 121,091 scored RUL forecasts per model.

2. **Scenario A (Literal Baseline Setting)**:
   - Every pipeline has identical Table IV parameters that do not vary or drift.
   - 30 matched runs (seeds 0–29), 100 pipelines per seed (3,000 pipelines total).
   - Demonstrates that when parameters are homogeneous and known, static modeling is already optimal and parameter adaptation is unnecessary.

---

## 3. Running Experiments

### 3.1 Quick Physics and Model Verification (~10 seconds)

Run all 10 unit tests:
```bash
pytest
```

Run closed-form mathematical and physical checks (produces `results/checks.json` and verification curves):
```bash
python experiments/run_checks.py
```

### 3.2 2x2 Factorial Ablation Analysis

Inspect the 2x2 factorial ablation (Coupling on/off $\times$ MCMC on/off):
```bash
python experiments/run_ablation.py --scenario B
```

Expected output:
```
==================================================
  2x2 Factorial Ablation Study (Scenario B)
==================================================
                     |  Coupling OFF   |   Coupling ON  
--------------------------------------------------------
MCMC OFF (PF)        |      2.29       |      1.12      
MCMC ON (API-DBN)    |      2.29       |      1.12      
--------------------------------------------------------
```

### 3.3 Regenerating Paper Tables and Figures

To re-generate LaTeX tables and figures from stored deterministic results:
```bash
# Generate LaTeX tables -> results/latex_tables.tex
python experiments/make_latex.py

# Generate paper figures -> paper/figures/
python experiments/make_paper_figures.py
```

Or run the master dispatcher:
```bash
python experiments/run_experiments.py --all-summaries
```

### 3.4 Full End-to-End Simulation Reruns

Because full Monte Carlo evaluation across 30 seeds involves $9{,}990 \times 12 \times 10{,}000$ simulated trajectories, runs are chunked, seeded, and resumable:

```bash
# Run Scenario B RUL simulation (multiprocessed)
python experiments/run_scenario_b.py --pipes 333 --seeds 30 --chunks 20

# Run Scenario A RUL simulation
python experiments/run_scenario_a.py --pipes 100 --seeds 30 --chunks 10

# Run closed-loop maintenance simulation (Scenario B, 1500 pipelines)
python experiments/run_maintenance.py --scenario B --pipes 1500

# Extend maintenance gamma grid to gamma <= 5 yr
python experiments/extend_gamma.py --scenario B --pipes 1500
```

Raw task array files are saved in `.npz` format. Completed tasks are cached, so rerunning automatically resumes without repeating work.

### 3.5 BSEE/PHMSA Consistency Checks

To reproduce the three external consistency checks from official NETL records:
```bash
python experiments/bsee_records.py --data path/to/downloaded_csvs
```

See [data/README.md](data/README.md) for data download instructions and SHA-256 hashes.

---

## 4. Expected Numerical Benchmarks

### 4.1 Scenario B Prognostics (Table VI)
- **API-DBN**: $\mathrm{MAE} = 1.12 \pm 0.04$ yr, $\mathrm{CRPS} = 0.80 \pm 0.03$ yr, $\mathrm{PICP} = 95.3\%$ ($95\%$ Wilson CI $[95.2\%, 95.4\%]$).
- **Static DBN**: $\mathrm{MAE} = 1.38 \pm 0.09$ yr, $\mathrm{CRPS} = 1.12 \pm 0.08$ yr, $\mathrm{PICP} = 59.9\%$.
- **Fixed Wiener**: $\mathrm{MAE} = 1.37 \pm 0.08$ yr, $\mathrm{CRPS} = 1.04 \pm 0.07$ yr, $\mathrm{PICP} = 75.0\%$.
- **Oracle**: $\mathrm{MAE} = 0.70 \pm 0.03$ yr, $\mathrm{CRPS} = 0.50 \pm 0.02$ yr, $\mathrm{PICP} = 95.4\%$.

### 4.2 Maintenance Optimization (Extended Grid, $\gamma \le 5.0$ yr)
- **API-DBN**: Best policy $I^* = 4.0$ yr, $\gamma^* = 5.0$ yr, Expected Cost $= \$353.5\mathrm{k} \pm 4.8\mathrm{k}$, Failure rate $= 0.07\%$.
- **Static DBN**: Best policy $I^* = 2.5$ yr, $\gamma^* = 4.5$ yr, Expected Cost $= \$425.0\mathrm{k} \pm 4.2\mathrm{k}$, Failure rate $= 0.07\%$.
- **Oracle**: Best policy $I^* = 4.0$ yr, $\gamma^* = 4.5$ yr, Expected Cost $= \$342.1\mathrm{k} \pm 11.1\mathrm{k}$, Failure rate $= 0.27\%$.

---

## 5. Raw Result Archive

`results/raw_results.zip` contains the complete per-task `.npz` arrays for all 30 seeds
(1,325 files, approximately 61 MB). This archive is **not tracked in the Git repository**
because of its size. It is a generated artefact: the full simulation pipeline in Step 3.4
above reproduces it from scratch in approximately 2–4 hours on a multi-core workstation.

If the archive is needed without rerunning the simulation, it will be distributed as an
attachment on the GitHub release page. No external download URL is available at this time.

