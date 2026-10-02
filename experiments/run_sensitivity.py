"""The sensitivity and convergence checks that Table IV's provenance column claims.

1. W0, alpha and r_s ("verified by sensitivity analysis"): effect on failure time.
2. M ("convergence tuning"): API-DBN accuracy with 250-2000 particles.
3. J ("Monte Carlo convergence"): Monte Carlo error of the RUL summaries.

Writes results/sensitivity.json.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import json
import sys
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))

from apidbn.core import DT, Physics, critical_depth  # noqa: E402
from apidbn.filters import MODELS, ParticleFilter  # noqa: E402
from apidbn.metrics import run_metrics, summarize  # noqa: E402
from apidbn.truth import SCENARIOS, simulate_paths, simulate_truth  # noqa: E402

P = Physics()
DCRIT = critical_depth(P)


def life(p: Physics, seed: int) -> dict:
    z = simulate_paths(10_000, p, np.random.default_rng(seed), years=40)
    hit = z >= DCRIT
    ft = np.where(hit.any(axis=0), np.argmax(hit, axis=0) * DT, np.inf)
    return {"median_yr": float(np.median(ft)), "p05_yr": float(np.quantile(ft, 0.05)),
            "p95_yr": float(np.quantile(ft, 0.95))}


def physics_sensitivity() -> dict:
    out = {"W0": {}, "alpha": {}, "r_s": {}}
    for w in (0.25, 0.5, 1.0, 2.0, 4.0, 8.0):
        out["W0"][str(w)] = life(replace(P, W0=w), 1)
    for a in (1.0, 1.5, 2.0, 2.5, 3.0):
        out["alpha"][str(a)] = life(replace(P, alpha=a), 2)
    for r in (0.25, 0.5, 1.0, 2.0, 5.0):
        out["r_s"][str(r)] = life(replace(P, r_sig=r), 3)
    return out


def m_task(args):
    M, pipes, n_total = args
    scen = SCENARIOS["B"]
    truth = simulate_truth(n_total, scen, P, DCRIT, np.random.default_rng([1, 500]))  # same pipelines for every M
    cfg = replace(MODELS["API"], M=M)
    ys, rows = [], []
    for i in pipes:
        rng = np.random.default_rng([5, M, i])
        pf = ParticleFilter(cfg, P, DCRIT, rng)
        for k, t in enumerate(truth["insp_times"]):
            if t >= truth["fail"][i]:
                break
            pf.propagate(t)
            pf.update(truth["obs"][i, k])
            y = truth["fail"][i] - t
            ys.append(y)
            rows.append(summarize(pf.predict_rul(10_000, rng), y))
    return M, np.array(ys), np.array(rows)


def particle_convergence(n_pipes: int = 80) -> dict:
    tasks = [(M, list(range(s, n_pipes, 4)), n_pipes) for M in (250, 500, 1000, 2000) for s in range(4)]
    acc = {}
    with Pool(min(8, os.cpu_count())) as pool:
        for M, y, r in pool.imap_unordered(m_task, tasks):
            acc.setdefault(M, []).append((y, r))
    out = {}
    for M in sorted(acc):
        y = np.concatenate([a[0] for a in acc[M]])
        r = np.vstack([a[1] for a in acc[M]])
        out[str(M)] = run_metrics(y, r[:, 0], r[:, 5], r[:, 6], r[:, 2], r[:, 4])
    return out


def forecast_convergence() -> dict:
    """Spread of the RUL summaries over repeated forecasts from one fixed filter state."""
    scen = SCENARIOS["B"]
    truth = simulate_truth(1, scen, P, DCRIT, np.random.default_rng(21))
    pf = ParticleFilter(MODELS["API"], P, DCRIT, np.random.default_rng(22))
    for k, t in enumerate(truth["insp_times"][:5]):
        pf.propagate(t)
        pf.update(truth["obs"][0, k])
    out = {}
    for J in (1_000, 10_000):
        reps = np.array([summarize(pf.predict_rul(J, np.random.default_rng(100 + r)), 5.0) for r in range(40)])
        out[str(J)] = {"sd_median_yr": float(reps[:, 0].std(ddof=1)), "sd_q025_yr": float(reps[:, 2].std(ddof=1)),
                       "sd_q975_yr": float(reps[:, 4].std(ddof=1)), "median_yr": float(reps[:, 0].mean())}
    return out


if __name__ == "__main__":
    res = {"physics": physics_sensitivity(), "forecast_J": forecast_convergence(),
           "particles_M_scenarioB_80pipes": particle_convergence()}
    (ROOT / "results" / "sensitivity.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
