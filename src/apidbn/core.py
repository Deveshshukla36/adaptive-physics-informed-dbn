"""Degradation physics of the manuscript (Sec. III-A, Eqs. 1-9) with Table IV values.

Everything the manuscript states is copied from it. Every choice it leaves open
is a named field marked OPEN, so it can be changed in one place.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# OPEN: Table IV gives K = 200 time steps but no step size. 0.1 yr reproduces the
# 20-yr horizon of Fig. 4 (200 x 0.1 yr).
DT = 0.1
STEPS_PER_YEAR = 10
SQRT_DT = np.sqrt(DT)


@dataclass(frozen=True)
class Physics:
    # --- Table IV -----------------------------------------------------------
    mu_base: float = 0.44     # mm/yr      baseline corrosion drift mu^(0)
    sigma_B: float = 0.20     # mm/yr^0.5  diffusion coefficient
    lam: float = 0.8          # 1/yr       baseline shock rate lambda^(0)
    mu_y0: float = 0.32       # mm         mean shock magnitude Y
    sigma_y0: float = 0.15    # mm         s.d. of Y
    W0: float = 1.0           # mm         sigmoid midpoint ("coating-breakdown threshold")
    alpha: float = 2.0        # -          acceleration factor
    r_sig: float = 0.5        # 1/mm       sigmoid steepness
    kappa: float = 0.30       # -          Eq. (4) scaling
    eta: float = 0.50         # -          Eq. (4) exponent
    gamma1: float = 0.05      # 1/mm       corrosion effect on shock intensity
    gamma2: float = 0.02      # -          environmental covariate coefficient
    sigma_v: float = 0.10     # mm         inspection error s.d.
    D: float = 610.0          # mm
    t_nom: float = 19.1       # mm
    L: float = 500.0          # mm
    SMYS: float = 358.0       # MPa
    P_op: float = 10.0        # MPa
    # --- OPEN choices -------------------------------------------------------
    E_cov: float = 0.0        # E_k of Eq. (6) is never specified; E = 0 gives exp(gamma2 E) = 1.
    folias_coef: float = 0.8  # Eq. (8) as printed. DNV-RP-F101 itself uses 0.31 (with SMTS).
    strength: float | None = None  # MPa used in Eq. (7); None = SMYS as printed.
    shock_map: str = "eq4"    # "eq4": dS = kappa * Y**eta (Eq. 4); "direct": dS = Y.

    @property
    def theta_nominal(self) -> np.ndarray:
        """(mu^(0), lambda^(0), sigma_B) from Table IV, in the order used everywhere."""
        return np.array([self.mu_base, self.lam, self.sigma_B])


# --- Structural failure, Eqs. (7)-(9) ---------------------------------------

def folias_factor(p: Physics) -> float:
    return float(np.sqrt(1.0 + p.folias_coef * p.L**2 / (p.D * p.t_nom)))


def intact_burst_pressure(p: Physics) -> float:
    strength = p.SMYS if p.strength is None else p.strength
    return 2.0 * p.t_nom * strength / (p.D - p.t_nom)


def burst_pressure(d, p: Physics):
    """Eq. (7) for defect depth d (mm)."""
    M = folias_factor(p)
    return intact_burst_pressure(p) * (1.0 - d / p.t_nom) / (1.0 - d / (p.t_nom * M))


def critical_depth(p: Physics) -> float:
    """Depth at which Eq. (9) holds with equality. P_burst decreases in d, so failure <=> Z >= d_crit."""
    q = p.P_op / intact_burst_pressure(p)
    M = folias_factor(p)
    return p.t_nom * (1.0 - q) / (1.0 - q / M)


# --- Coupling, Eqs. (5)-(6) ---------------------------------------------------

def drift_gain(Z, p: Physics, coupling: bool = True):
    """mu_eff / mu^(0) from Eq. (5)."""
    if not coupling:
        return np.ones_like(Z)
    return 1.0 + (p.alpha - 1.0) / (1.0 + np.exp(-p.r_sig * (Z - p.W0)))


def shock_gain(X, p: Physics, coupling: bool = True):
    """lambda_eff / lambda^(0) from Eq. (6)."""
    if not coupling:
        return np.ones_like(X)
    return np.exp(p.gamma1 * X + p.gamma2 * p.E_cov)


# --- Shocks, Eq. (4) ----------------------------------------------------------

def shock_magnitudes(k: int, p: Physics, rng: np.random.Generator) -> np.ndarray:
    """Equivalent wall loss of k shocks. Y ~ N(mu_y0, sigma_y0^2) truncated at 0."""
    y = p.mu_y0 + p.sigma_y0 * rng.standard_normal(k)
    neg = y <= 0.0
    while neg.any():
        y[neg] = p.mu_y0 + p.sigma_y0 * rng.standard_normal(int(neg.sum()))
        neg = y <= 0.0
    return p.kappa * y**p.eta if p.shock_map == "eq4" else y


def shock_increments(n: np.ndarray, p: Physics, rng: np.random.Generator) -> np.ndarray:
    """Total equivalent damage of n[i] shocks on path i."""
    k = int(n.sum())
    if k == 0:
        return np.zeros(n.shape)
    owner = np.repeat(np.arange(n.size), n)
    return np.bincount(owner, weights=shock_magnitudes(k, p, rng), minlength=n.size)


def step(X, S, mu, lam, sig, p: Physics, rng: np.random.Generator, coupling: bool = True):
    """One Euler step of Eqs. (1)-(6). Rates use the state at the start of the step.

    Returns (dX, dS, g, h, n): the corrosion and shock increments plus the drift
    gain, shock gain and shock count, which the MCMC move needs as sufficient
    statistics.
    """
    g = drift_gain(X + S, p, coupling)
    h = shock_gain(X, p, coupling)
    dX = mu * g * DT + sig * SQRT_DT * rng.standard_normal(X.shape)
    n = rng.poisson(lam * h * DT)
    return dX, shock_increments(n, p, rng), g, h, n
