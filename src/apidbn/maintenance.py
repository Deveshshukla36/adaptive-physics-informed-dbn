"""Closed-loop evaluation of the (I, gamma) policy of Eqs. (17)-(18).

Each model inspects a simulated pipeline every I years, updates its filter, and
orders preventive replacement when the 10th percentile of its RUL forecast is
at most gamma (Sec. III-C). The cost is what the true pipeline then incurs:
inspections, preventive replacements and failures (C_fail + C_env), discounted
at r over the planning horizon. Scoring decisions against the truth, not
against the model's own forecast, is what makes models comparable: a model that
forecasts longer lives would otherwise report lower costs for that reason alone.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .core import DT, SQRT_DT, STEPS_PER_YEAR, Physics, shock_magnitudes
from .filters import MODELS, ParticleFilter
from .truth import Scenario, draw_pipeline_parameters


@dataclass(frozen=True)
class Costs:
    """Economic and maintenance lifecycle parameters (Table V, in k$)."""
    C_ins: float = 50.0
    C_prev: float = 200.0
    C_fail: float = 5000.0
    C_env: float = 10000.0
    r: float = 0.05
    horizon: float = 20.0
    quantile: float = 0.10


class PipelineWorld:
    """All randomness of one pipeline's environment, drawn once.

    Every policy and every model then faces the same corrosion noise, shocks,
    parameter drift and inspection errors (common random numbers). A replaced
    segment restarts from zero damage in the same environment.
    """

    def __init__(self, scen: Scenario, p: Physics, rng, horizon: float, max_shocks: int = 6):
        n = int(round(horizon / DT))
        years = int(math.ceil(horizon)) + 1
        theta0 = draw_pipeline_parameters(1, scen, p, rng)[:, 0]
        steps = scen.drift_sd * rng.standard_normal((years, 3))
        steps[0] = 0.0
        self.theta_year = theta0 * np.exp(np.cumsum(steps, axis=0))   # (years, 3)
        self.eps = rng.standard_normal(n)
        self.u = rng.random(n)
        self.shock = shock_magnitudes(n * max_shocks, p, rng).reshape(n, max_shocks)
        self.v = p.sigma_v * rng.standard_normal(n)
        self.n_steps = n


def _poisson_inv(u: float, m: float) -> int:
    k, prob = 0, math.exp(-m)
    cdf = prob
    while u > cdf and k < 50:
        k += 1
        prob *= m / k
        cdf += prob
    return k


def run_policy(model: str, interval: float, gamma: float, world: PipelineWorld, p: Physics,
               dcrit: float, costs: Costs, rng, J: int = 2000, M: int = 1000,
               drift_sd: float = 0.0) -> tuple[float, int, int, int]:
    """Discounted cost, failures, preventive replacements and inspections for one pipeline."""
    cfg = MODELS[model]
    if M != cfg.M:
        from dataclasses import replace
        cfg = replace(cfg, M=M)
    if model == "ORACLE":
        pf = ParticleFilter(cfg, p, dcrit, rng, theta_path=world.theta_year)
        drift = np.full((3, 1), drift_sd) if drift_sd > 0 else None
    else:
        pf = ParticleFilter(cfg, p, dcrit, rng, theta=p.theta_nominal)
        drift = None
    insp_every = int(round(interval / DT))
    disc = lambda t: (1.0 + costs.r) ** (-t)  # noqa: E731
    X = S = 0.0
    cost, n_fail, n_pm, n_insp = 0.0, 0, 0, 0
    for j in range(world.n_steps):
        mu, lam, sig = world.theta_year[j // STEPS_PER_YEAR]
        g = 1.0 + (p.alpha - 1.0) / (1.0 + math.exp(-p.r_sig * (X + S - p.W0)))
        h = math.exp(p.gamma1 * X + p.gamma2 * p.E_cov)
        X += mu * g * DT + sig * SQRT_DT * world.eps[j]
        S += float(world.shock[j, :_poisson_inv(world.u[j], lam * h * DT)].sum())
        t = (j + 1) * DT
        if X + S >= dcrit:
            cost += (costs.C_fail + costs.C_env) * disc(t)
            n_fail += 1
            X = S = 0.0
            _renew(pf, t)
            continue
        if (j + 1) % insp_every == 0 and t < costs.horizon - 1e-9:
            cost += costs.C_ins * disc(t)
            n_insp += 1
            pf.propagate(t)
            pf.update(X + S + world.v[j])
            rul = pf.predict_rul(J, rng, max_ahead=gamma, drift=drift)
            if np.mean(rul <= gamma + 1e-9) >= costs.quantile:
                cost += costs.C_prev * disc(t)
                n_pm += 1
                X = S = 0.0
                _renew(pf, t)
    return cost, n_fail, n_pm, n_insp


def _renew(pf: ParticleFilter, t: float) -> None:
    """Replacement at time t: the new segment's state is known to be zero damage.

    Adaptive models keep their parameter particles, because the environment is unchanged.
    """
    pf.X[:] = 0.0
    pf.S[:] = 0.0
    pf.t = t
    pf.w[:] = 1.0 / pf.cfg.M
    pf.logw[:] = -np.log(pf.cfg.M)
    pf.stats = None
