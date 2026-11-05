"""Controlled-simulation ground truth generator (Sec. IV-B).

Two simulation settings are evaluated:
  Scenario A: All pipelines share identical, fixed Table IV parameters without drift.
  Scenario B: Asset-specific baseline parameters vary log-normally around Table IV
              and drift annually via log-random walks with standard deviation 0.05/yr.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .core import DT, STEPS_PER_YEAR, Physics, step


@dataclass(frozen=True)
class Scenario:
    name: str
    het_sd: float                 # log-s.d. of pipeline-specific parameters around Table IV
    drift_sd: float               # yearly log-random-walk s.d. of the true parameters
    insp_interval: float = 1.0    # Annual inspection interval (Sec. IV-B)
    horizon: float = 20.0         # monitoring window, K = 200 steps of DT
    t_max: float = 80.0           # truth is simulated until failure or t_max


SCENARIOS = {
    "A": Scenario("A", het_sd=0.0, drift_sd=0.0),
    "B": Scenario("B", het_sd=0.25, drift_sd=0.05),
}


def draw_pipeline_parameters(n, scen: Scenario, p: Physics, rng) -> np.ndarray:
    """(3, n) array of initial (mu, lambda, sigma_B)."""
    theta = np.repeat(p.theta_nominal[:, None], n, axis=1)
    if scen.het_sd > 0:
        theta = theta * np.exp(scen.het_sd * rng.standard_normal((3, n)))
    return theta


def simulate_truth(n: int, scen: Scenario, p: Physics, dcrit: float, rng,
                   theta0: np.ndarray | None = None) -> dict:
    """Simulate n pipelines to failure (Z >= dcrit) or scen.t_max.

    Returns failure times, the true state and noisy observations at the
    inspection epochs inside the monitoring horizon (NaN once failed), and the
    parameter value in force during each year, which the oracle model uses.
    """
    theta = draw_pipeline_parameters(n, scen, p, rng) if theta0 is None else theta0.copy()
    n_steps = int(round(scen.t_max / DT))
    n_years = int(np.ceil(scen.t_max)) + 1
    insp_every = int(round(scen.insp_interval / DT))
    n_insp = int(round(scen.horizon / scen.insp_interval))

    X = np.zeros(n)
    S = np.zeros(n)
    fail = np.full(n, np.inf)
    alive = np.ones(n, dtype=bool)
    Z_insp = np.full((n, n_insp), np.nan)
    theta_year = np.empty((n_years, 3, n))

    for j in range(n_steps):
        if j % STEPS_PER_YEAR == 0:
            year = j // STEPS_PER_YEAR
            if year > 0 and scen.drift_sd > 0:
                theta = theta * np.exp(scen.drift_sd * rng.standard_normal((3, n)))
            theta_year[year] = theta
        dX, dS, *_ = step(X, S, theta[0], theta[1], theta[2], p, rng)
        X += dX
        S += dS
        newly = alive & (X + S >= dcrit)
        fail[newly] = (j + 1) * DT
        alive &= ~newly
        if (j + 1) % insp_every == 0:
            k = (j + 1) // insp_every - 1
            if k < n_insp:
                Z_insp[alive, k] = (X + S)[alive]
        if not alive.any():
            theta_year[year + 1:] = theta
            break

    obs = Z_insp + p.sigma_v * rng.standard_normal(Z_insp.shape)
    out = {
        "fail": fail,
        "Z": Z_insp,
        "obs": obs,
        "theta_year": theta_year,
        "insp_times": scen.insp_interval * np.arange(1, n_insp + 1),
    }
    return out


def simulate_paths(n: int, p: Physics, rng, years: float = 20.0, lam: float | None = None,
                   coupling: bool = True) -> np.ndarray:
    """Z(t) on the DT grid for n pipelines with the Table IV parameters, not stopped at failure.

    Returns an array of shape (steps + 1, n); row 0 is t = 0.
    """
    lam = p.lam if lam is None else lam
    n_steps = int(round(years / DT))
    X = np.zeros(n)
    S = np.zeros(n)
    out = np.zeros((n_steps + 1, n))
    for j in range(n_steps):
        dX, dS, *_ = step(X, S, p.mu_base, lam, p.sigma_B, p, rng, coupling)
        X += dX
        S += dS
        out[j + 1] = X + S
    return out
