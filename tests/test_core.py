import numpy as np
import pytest
from scipy import integrate, stats

from apidbn.core import DT, Physics, burst_pressure, critical_depth, drift_gain, shock_magnitudes, step
from apidbn.filters import MODELS, FilterConfig, FixedWiener, ParticleFilter, forecast_failure
from apidbn.metrics import crps_samples
from apidbn.truth import SCENARIOS, simulate_truth

P = Physics()


def test_critical_depth_solves_eq9():
    d = critical_depth(P)
    assert burst_pressure(d, P) == pytest.approx(P.P_op, rel=1e-12)
    assert d == pytest.approx(12.07, abs=0.01)
    grid = np.linspace(0, 18, 50)
    assert np.all(np.diff(burst_pressure(grid, P)) < 0)


def test_sigmoid_is_not_baseline_at_zero_damage():
    assert drift_gain(np.array([0.0]), P)[0] == pytest.approx(1 + 1 / (1 + np.exp(0.5)))
    assert drift_gain(np.array([0.0]), P, coupling=False)[0] == 1.0


def test_mean_shock_damage_matches_integral():
    a = (0 - P.mu_y0) / P.sigma_y0
    tn = stats.truncnorm(a, np.inf, loc=P.mu_y0, scale=P.sigma_y0)
    exact = integrate.quad(lambda y: P.kappa * y**P.eta * tn.pdf(y), 0, np.inf)[0]
    mc = shock_magnitudes(400_000, P, np.random.default_rng(1)).mean()
    assert mc == pytest.approx(exact, rel=5e-3)
    assert exact == pytest.approx(0.165, abs=0.002)


def test_wiener_moments_without_shocks_or_coupling():
    rng = np.random.default_rng(2)
    n, years = 200_000, 5
    X = np.zeros(n)
    S = np.zeros(n)
    for _ in range(int(years / DT)):
        dX, dS, *_ = step(X, S, 0.44, 0.0, 0.2, P, rng, coupling=False)
        X += dX
        S += dS
    assert X.mean() == pytest.approx(0.44 * years, rel=5e-3)
    assert X.var() == pytest.approx(0.04 * years, rel=2e-2)
    assert S.max() == 0.0


def test_deterministic_forecast_hits_threshold_on_time():
    p = Physics(sigma_B=0.0, lam=0.0)
    dcrit = critical_depth(p)
    lt = np.log(np.array([[0.5], [1e-12], [1e-12]]))
    rul = forecast_failure(np.zeros(1), np.zeros(1), lt, p, dcrit, np.random.default_rng(0),
                           coupling=False, drift=None, max_ahead=60)
    assert rul[0] == pytest.approx(np.ceil(dcrit / 0.5 / DT - 1e-9) * DT)


def _pf_with_stats(A, B, C, N, H, n_sub, prev, rw, M=20_000):
    cfg = FilterConfig("t", adaptive=True, coupling=True, mcmc=True, M=M, rw_sd=rw, n_mcmc=1)
    pf = ParticleFilter(cfg, P, 12.0, np.random.default_rng(3))
    pf.lt_prev = np.repeat(np.log(prev)[:, None], M, axis=1)
    pf.lt = pf.lt_prev.copy()
    pf.rw_slice = np.asarray(rw)[:, None]
    pf.stats = tuple(np.full(M, v, float) for v in (A, B, C, N, H)) + (n_sub,)
    return pf


def test_mcmc_leaves_random_walk_prior_invariant_without_data():
    rw = (0.05, 0.08, 0.03)
    pf = _pf_with_stats(0, 0, 0, 0, 0, 0, np.array([0.44, 0.8, 0.2]), rw)
    for _ in range(200):
        pf._rejuvenate()
    dev = pf.lt - pf.lt_prev
    assert np.allclose(dev.mean(axis=1), 0, atol=0.004)
    assert np.allclose(dev.std(axis=1), rw, rtol=0.05)


def test_mcmc_samples_exact_shock_rate_posterior():
    # lambda-part of the target: lambda^N exp(-lambda H) x lognormal(prev, rw) prior.
    N_obs, H, prev, rw = 3.0, 1.2, 0.8, 0.3
    pf = _pf_with_stats(0, 0, 0, N_obs, H, 0, np.array([0.44, prev, 0.2]), (0.05, rw, 0.05))
    for _ in range(300):
        pf._rejuvenate()
    grid = np.linspace(np.log(prev) - 6 * rw, np.log(prev) + 6 * rw, 20_001)
    logd = N_obs * grid - np.exp(grid) * H - 0.5 * ((grid - np.log(prev)) / rw) ** 2
    d = np.exp(logd - logd.max())
    exact = np.sum(np.exp(grid) * d) / d.sum()
    assert np.exp(pf.lt[1]).mean() == pytest.approx(exact, rel=0.01)


def test_crps_matches_gaussian_closed_form():
    x = np.sort(np.random.default_rng(4).standard_normal(200_000))
    closed = 2 * stats.norm.pdf(0) - 1 / np.sqrt(np.pi)
    assert crps_samples(x, 0.0) == pytest.approx(closed, rel=0.01)


def test_fixed_wiener_mean_is_distance_over_drift():
    fw = FixedWiener(0.9, 0.3, 12.0)
    rul = fw.predict_rul(3.0, 400_000, np.random.default_rng(5))
    assert rul.mean() == pytest.approx(9.0 / 0.9, rel=5e-3)


def test_filter_tracks_state_and_learns_drift():
    dcrit = critical_depth(P)
    scen = SCENARIOS["A"]
    truth = simulate_truth(1, scen, P, dcrit, np.random.default_rng(6))
    pf = ParticleFilter(MODELS["API"], P, dcrit, np.random.default_rng(7))
    ref = ParticleFilter(MODELS["SDBN"], P, dcrit, np.random.default_rng(8), theta=P.theta_nominal)
    for k, t in enumerate(truth["insp_times"]):
        if t >= truth["fail"][0]:
            break
        for f in (pf, ref):
            f.propagate(t)
            f.update(truth["obs"][0, k])
            est = np.dot(f.w, f.X + f.S)
            assert abs(est - truth["Z"][0, k]) < 4 * P.sigma_v
    assert 0.25 < pf.posterior_mean_theta()[0] < 0.7
