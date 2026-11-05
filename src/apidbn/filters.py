"""The five compared models of Sec. IV-B, plus an oracle reference.

ParticleFilter implements Algorithm 1: evolve the baseline parameters by
log-random walks (Eqs. 12-14), propagate the state (Eqs. 1-6), weight with
Eq. (10), resample when ESS < M/2, then apply Metropolis-Hastings rejuvenation
(Eq. 15). The static DBN, the PF without MCMC, the no-coupling model, the full
API-DBN and the oracle are configurations of that one class, so they differ
only in the component being ablated.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .core import DT, STEPS_PER_YEAR, Physics, step


@dataclass(frozen=True)
class FilterConfig:
    name: str
    adaptive: bool       # (mu, lambda, sigma_B) are in the particle state and follow Eqs. (12)-(14)
    coupling: bool       # Eqs. (5)-(6); off means alpha = 1 and gamma1 = 0 inside the model
    mcmc: bool           # MH rejuvenation after resampling, Eq. (15)
    M: int = 1000
    rw_sd: tuple = (0.05, 0.05, 0.05)  # per year (Eqs. 12-14, Table IV)
    n_mcmc: int = 5      # MH sweeps per rejuvenation (Algorithm 1)
    forecast_drift: bool = True  # adaptive models keep their random walk when forecasting


MODELS = {
    "SDBN": FilterConfig("Static DBN", adaptive=False, coupling=True, mcmc=False),
    "PF": FilterConfig("PF w/o MCMC", adaptive=True, coupling=True, mcmc=False),
    "NC": FilterConfig("No coupling", adaptive=True, coupling=False, mcmc=True),
    "API": FilterConfig("API-DBN", adaptive=True, coupling=True, mcmc=True),
    "NC0": FilterConfig("No coupling, w/o MCMC", adaptive=True, coupling=False, mcmc=False),
    "ORACLE": FilterConfig("Oracle (true parameters)", adaptive=False, coupling=True, mcmc=False),
}


def sample_prior(M: int, rng) -> np.ndarray:
    """Algorithm 1, line 1: (3, M) draws of (mu, lambda, sigma_B).
    lambda ~ Gamma(shape 2, scale 0.4) truncated to [0.2, 5].
    """
    lam = rng.gamma(2.0, 0.4, M)
    bad = (lam < 0.2) | (lam > 5.0)
    while bad.any():
        lam[bad] = rng.gamma(2.0, 0.4, int(bad.sum()))
        bad = (lam < 0.2) | (lam > 5.0)
    return np.vstack([rng.uniform(0.2, 0.8, M), lam, rng.uniform(0.1, 0.3, M)])


def systematic_resample(w: np.ndarray, rng) -> np.ndarray:
    M = w.size
    c = np.cumsum(w)
    c[-1] = 1.0
    return np.searchsorted(c, (rng.random() + np.arange(M)) / M)


def forecast_failure(X, S, lt, p: Physics, dcrit: float, rng, coupling: bool,
                     drift, max_ahead: float) -> np.ndarray:
    """Eq. (16): time until Z >= dcrit for each path, or inf if beyond max_ahead.

    lt is the (3, J) log-parameter array; drift is the yearly log-random-walk
    s.d. (3, 1) applied at the start of every forecast year, or None.
    """
    J = X.size
    rul = np.full(J, np.inf)
    done = X + S >= dcrit
    rul[done] = 0.0
    alive = np.flatnonzero(~done)
    X, S, lt = X[alive].copy(), S[alive].copy(), lt[:, alive].copy()
    th = np.exp(lt)
    for j in range(int(round(max_ahead / DT))):
        if alive.size == 0:
            break
        if drift is not None and j % STEPS_PER_YEAR == 0:
            lt = lt + drift * rng.standard_normal(lt.shape)
            th = np.exp(lt)
        dX, dS, *_ = step(X, S, th[0], th[1], th[2], p, rng, coupling)
        X += dX
        S += dS
        failed = X + S >= dcrit
        if failed.any():
            rul[alive[failed]] = (j + 1) * DT
            keep = ~failed
            X, S, alive, lt, th = X[keep], S[keep], alive[keep], lt[:, keep], th[:, keep]
    return rul


class ParticleFilter:
    def __init__(self, cfg: FilterConfig, p: Physics, dcrit: float, rng,
                 theta: np.ndarray | None = None, theta_path: np.ndarray | None = None):
        """theta: fixed parameters for a non-adaptive model.
        theta_path: (years, 3) true parameters per calendar year, for the oracle."""
        self.cfg, self.p, self.dcrit, self.rng = cfg, p, dcrit, rng
        M = cfg.M
        self.X = np.zeros(M)
        self.S = np.zeros(M)
        self.logw = np.full(M, -np.log(M))
        self.w = np.full(M, 1.0 / M)
        self.theta_path = theta_path
        if cfg.adaptive:
            self.lt = np.log(sample_prior(M, rng))
        else:
            base = theta if theta_path is None else theta_path[0]
            self.lt = np.repeat(np.log(np.asarray(base, float))[:, None], M, axis=1)
        self.lt_prev = self.lt.copy()
        self.rw = np.asarray(cfg.rw_sd, float)[:, None]
        self.rw_slice = self.rw
        self.t = 0.0
        self.stats = None
        self.crossed = np.zeros(M, dtype=bool)
        self.n_resample = 0
        self.acceptance = []

    # -- Algorithm 1, lines 3-4 ------------------------------------------------
    def propagate(self, t_next: float) -> None:
        cfg, M = self.cfg, self.cfg.M
        n_sub = int(round((t_next - self.t) / DT))
        if cfg.adaptive:
            self.lt_prev = self.lt.copy()
            self.rw_slice = self.rw * np.sqrt(t_next - self.t)
            self.lt = self.lt + self.rw_slice * self.rng.standard_normal(self.lt.shape)
        track = cfg.adaptive and cfg.mcmc
        if track:
            A, B, C, N, H = (np.zeros(M) for _ in range(5))
        crossed = np.zeros(M, dtype=bool)
        year = -1
        mu, lam, sig = np.exp(self.lt)
        for j in range(n_sub):
            if self.theta_path is not None:
                y = int(np.floor(self.t + j * DT + 1e-9))
                if y != year:
                    year = y
                    self.lt[:] = np.log(self.theta_path[min(y, len(self.theta_path) - 1)])[:, None]
                    mu, lam, sig = np.exp(self.lt)
            dX, dS, g, h, n = step(self.X, self.S, mu, lam, sig, self.p, self.rng, cfg.coupling)
            if track:
                A += dX * dX
                B += dX * g
                C += g * g
                N += n
                H += h
            self.X += dX
            self.S += dS
            crossed |= self.X + self.S >= self.dcrit
        self.stats = (A, B, C, N, H * DT, n_sub) if track else None
        self.crossed = crossed
        self.t = t_next

    # -- Algorithm 1, lines 5-8 ------------------------------------------------
    def update(self, obs: float) -> None:
        M = self.cfg.M
        logw = self.logw - 0.5 * ((obs - self.X - self.S) / self.p.sigma_v) ** 2
        if not self.crossed.all():
            # The pipeline was found intact, so paths that already failed are impossible.
            logw = np.where(self.crossed, -np.inf, logw)
        logw -= logw.max()
        w = np.exp(logw)
        w /= w.sum()
        if 1.0 / np.sum(w * w) < 0.5 * M:
            idx = systematic_resample(w, self.rng)
            self.X, self.S = self.X[idx], self.S[idx]
            self.lt, self.lt_prev = self.lt[:, idx], self.lt_prev[:, idx]
            if self.stats is not None:
                self.stats = tuple(a[idx] for a in self.stats[:5]) + (self.stats[5],)
            w = np.full(M, 1.0 / M)
            self.n_resample += 1
            if self.cfg.adaptive and self.cfg.mcmc:
                self._rejuvenate()
        self.w = w
        with np.errstate(divide="ignore"):
            self.logw = np.log(w)

    def _rejuvenate(self) -> None:
        """Eq. (15): MH on this slice's parameters given the particle's own path.

        With the state held fixed, p(o_k | s_k) cancels, leaving the path density
        p(s_k | s_{k-1}, theta) times the random-walk prior p(theta | theta_{k-1}).
        The path density is exact: Gaussian corrosion increments and Poisson shock
        counts, summarised per particle by (A, B, C, N, H).
        """
        A, B, C, N, H, n_sub = self.stats
        prev, rw2 = self.lt_prev, self.rw_slice**2

        def log_target(lt):
            mu, lam, sig = np.exp(lt)
            loglik = (-n_sub * lt[2]
                      - (A - 2.0 * mu * DT * B + mu * mu * DT * DT * C) / (2.0 * sig * sig * DT)
                      + N * lt[1] - lam * H)
            return loglik - 0.5 * np.sum((lt - prev) ** 2 / rw2, axis=0)

        cur = log_target(self.lt)
        accepted = 0.0
        for _ in range(self.cfg.n_mcmc):
            prop = self.lt + self.rw_slice * self.rng.standard_normal(self.lt.shape)
            new = log_target(prop)
            acc = np.log(self.rng.random(self.cfg.M)) < new - cur
            self.lt[:, acc] = prop[:, acc]
            cur[acc] = new[acc]
            accepted += acc.mean()
        self.acceptance.append(accepted / self.cfg.n_mcmc)

    # -- Eq. (16) ----------------------------------------------------------------
    def predict_rul(self, J: int, rng, max_ahead: float = 60.0, drift=None) -> np.ndarray:
        idx = rng.choice(self.cfg.M, size=J, p=self.w)
        if drift is None and self.cfg.adaptive and self.cfg.forecast_drift:
            drift = self.rw
        return forecast_failure(self.X[idx], self.S[idx], self.lt[:, idx], self.p, self.dcrit,
                                rng, self.cfg.coupling, drift, max_ahead)

    def posterior_mean_theta(self) -> np.ndarray:
        return np.exp(self.lt) @ self.w


class FixedWiener:
    """Model 1: linear-drift Wiener process on Z with fixed, offline-calibrated parameters.

    The current state is the latest observation; RUL is the inverse-Gaussian
    first-passage time to dcrit. No shocks, no coupling, no updating.
    """

    def __init__(self, mu: float, sig: float, dcrit: float):
        self.mu, self.sig, self.dcrit = float(mu), float(sig), float(dcrit)

    @classmethod
    def calibrate(cls, obs: np.ndarray, insp_interval: float, sigma_v: float, dcrit: float):
        """Pooled moment estimates from training pipelines' inspection increments."""
        full = np.hstack([np.zeros((obs.shape[0], 1)), obs])
        inc = np.diff(full, axis=1)
        inc = inc[np.isfinite(inc)]
        mu = inc.mean() / insp_interval
        var = max(inc.var() - 2.0 * sigma_v**2, 1e-6) / insp_interval
        return cls(mu, np.sqrt(var), dcrit)

    def predict_rul(self, obs_now: float, J: int, rng, max_ahead: float = 60.0) -> np.ndarray:
        a = self.dcrit - obs_now
        if a <= 0:
            return np.zeros(J)
        rul = rng.wald(a / self.mu, a * a / self.sig**2, J)
        return np.where(rul > max_ahead, np.inf, rul)
