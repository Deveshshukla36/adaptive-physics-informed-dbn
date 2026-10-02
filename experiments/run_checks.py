"""Closed-form checks of the manuscript's numbers and replicas of Figs. 4 and 5.

Writes results/checks.json, figures/fig4_replica.png and figures/fig5_replica.png.
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy import integrate, stats  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))

from apidbn.core import DT, Physics, critical_depth, drift_gain, folias_factor, intact_burst_pressure  # noqa: E402
from apidbn.filters import MODELS, ParticleFilter, forecast_failure, sample_prior  # noqa: E402
from apidbn.truth import SCENARIOS, simulate_paths, simulate_truth  # noqa: E402

P = Physics()
DCRIT = critical_depth(P)
OUT = {}


def failure_times(paths: np.ndarray, dcrit: float) -> np.ndarray:
    """First grid time with Z >= dcrit (inf if never) for (steps + 1, n) paths."""
    hit = paths >= dcrit
    t = np.argmax(hit, axis=0) * DT
    return np.where(hit.any(axis=0), t, np.inf)


# 1. Failure depth, Eqs. (7)-(9) --------------------------------------------------
SMTS_X52 = 455.0
OUT["failure_depth"] = {
    "P0_MPa": intact_burst_pressure(P),
    "folias_M": folias_factor(P),
    "dcrit_as_printed_mm": DCRIT,
    "dcrit_fraction_of_wall": DCRIT / P.t_nom,
    "dcrit_0.31_SMYS_mm": critical_depth(replace(P, folias_coef=0.31)),
    "dcrit_0.31_SMTS455_mm": critical_depth(replace(P, folias_coef=0.31, strength=SMTS_X52)),
}

# 2. Sigmoid coupling, Eq. (5) ----------------------------------------------------
OUT["sigmoid"] = {
    "gain_at_Z0": float(drift_gain(np.array(0.0), P)),
    "gain_at_W0": float(drift_gain(np.array(P.W0), P)),
    "gain_at_dcrit": float(drift_gain(np.array(DCRIT), P)),
    "width_10_90_mm": 2 * np.log(9) / P.r_sig,
    "min_mean_drift_mm_per_yr": P.mu_base * float(drift_gain(np.array(0.0), P)),
}

# 3. Shock damage, Eq. (4) --------------------------------------------------------
a = (0 - P.mu_y0) / P.sigma_y0
tn = stats.truncnorm(a, np.inf, loc=P.mu_y0, scale=P.sigma_y0)
OUT["shock_damage"] = {
    "E_dS_eq4_mm": integrate.quad(lambda y: P.kappa * y**P.eta * tn.pdf(y), 0, np.inf)[0],
    "E_dS_direct_mm": tn.mean(),
    "P_Y_negative_untruncated": stats.norm.cdf(a),
}

# 4. Arithmetic in Sec. V ---------------------------------------------------------
table6 = {  # model: (MAE, sd), (RMSE, sd), (CRPS, sd), (Brier, sd)
    "Static DBN": [(2.45, 0.18), (3.34, 0.22), (1.42, 0.09), (0.28, 0.02)],
    "API-DBN": [(0.84, 0.07), (1.15, 0.09), (0.45, 0.03), (0.09, 0.01)],
}
OUT["arithmetic"] = {
    "MAE_reduction": (2.45 - 0.84) / 2.45,
    "RMSE_reduction": (3.34 - 1.15) / 3.34,
    "cost_reduction": (480.6 - 315.4) / 480.6,
}
bounds = {}
for j, metric in enumerate(["MAE", "RMSE", "CRPS", "Brier"]):
    (m1, s1), (m2, s2) = table6["Static DBN"][j], table6["API-DBN"][j]
    t_min = (m1 - m2) * np.sqrt(30) / (s1 + s2)  # sd of paired differences <= s1 + s2
    bounds[metric] = {"t_min": t_min, "p_max_two_sided": 2 * stats.t.sf(t_min, 29)}
OUT["paired_t_lower_bounds"] = bounds

reach = [n for n in range(1, 400) if any(0.9475 <= k / n < 0.9485 for k in range(n + 1))]
OUT["picp"] = {
    "values_reachable_with_N30": [round(k / 30, 4) for k in (28, 29)],
    "smallest_N_giving_94.8pct": reach[0],
    "binomial_se_at_N1000_pp": 100 * np.sqrt(0.95 * 0.05 / 1000),
}


def inspection_pv(interval: float, horizon: float, start: float, c_ins=50.0, r=0.05) -> float:
    times = np.arange(start, horizon + 1e-9, interval)
    return float(np.sum(c_ins / (1 + r) ** times))


OUT["costs"] = {
    "inspection_PV_I2_t2to20": inspection_pv(2, 20, 2),
    "inspection_PV_I2_t0to18": inspection_pv(2, 18, 0),
    "inspection_PV_I2_t2to18": inspection_pv(2, 18, 2),
    "failure_cost_PV_at_12.5yr": 15_000 / 1.05**12.5,
    "PM_cost_PV_at_11yr": 200 / 1.05**11,
}

# 5. Fig. 4: trajectories for the three shock regimes ------------------------------
rng = np.random.default_rng(2024)
regimes = {"low": 0.3, "moderate": 0.8, "high": 1.5}
fig4 = {}
paths = {}
for name, lam in regimes.items():
    z = simulate_paths(10_000, P, rng, years=20, lam=lam)
    paths[name] = z
    ft = failure_times(simulate_paths(10_000, P, rng, years=40, lam=lam), DCRIT)
    fig4[name] = {
        "lambda": lam,
        "mean_Z20_mm": float(z[-1].mean()),
        "p05_Z20_mm": float(np.quantile(z[-1], 0.05)),
        "p95_Z20_mm": float(np.quantile(z[-1], 0.95)),
        "median_failure_yr": float(np.median(ft)),
        "p05_failure_yr": float(np.quantile(ft, 0.05)),
        "p95_failure_yr": float(np.quantile(ft, 0.95)),
        "P_fail_by_20yr": float(np.mean(ft <= 20)),
    }
z0 = simulate_paths(10_000, P, rng, years=20, lam=0.0)
fig4["corrosion_only"] = {"mean_Z20_mm": float(z0[-1].mean()), "sd_Z20_mm": float(z0[-1].std())}
ft_direct = failure_times(simulate_paths(10_000, replace(P, shock_map="direct"), rng, years=40), DCRIT)
fig4["moderate_if_dS_equals_Y"] = {"median_failure_yr": float(np.median(ft_direct))}
OUT["fig4"] = fig4

t = np.arange(paths["low"].shape[0]) * DT
fig, ax = plt.subplots(figsize=(6.4, 4.0), dpi=200)
colors = {"low": "#1b7837", "moderate": "#2166ac", "high": "#b2182b"}
for name, z in paths.items():
    lo, hi = np.quantile(z, [0.05, 0.95], axis=1)
    ax.fill_between(t, lo, hi, color=colors[name], alpha=0.15, lw=0)
    ax.plot(t, z[:, 0], color=colors[name], lw=1.0,
            label=rf"$\lambda={regimes[name]}$ yr$^{{-1}}$ ({name})")
    ax.plot(t, z.mean(axis=1), color=colors[name], lw=1.0, ls=":")
ax.axhline(DCRIT, color="k", ls="--", lw=1)
ax.text(0.3, DCRIT + 0.4, f"Eq. (9) failure depth {DCRIT:.1f} mm", fontsize=8)
ax.set_xlabel("Time (years)")
ax.set_ylabel(r"Equivalent damage $Z(t)$ (mm)")
ax.set_xlim(0, 20)
ax.set_ylim(0, None)
ax.legend(fontsize=8, loc="upper left", title="solid: one path; dotted: mean; band: 5-95%",
          title_fontsize=7)
fig.tight_layout()
fig.savefig(ROOT / "figures" / "fig4_replica.png")
plt.close(fig)

# 6. Fig. 5: reliability ---------------------------------------------------------
rel = {}
grid = np.arange(0, 40.01, 0.1)
for sname in ("A", "B"):
    tr = simulate_truth(10_000, SCENARIOS[sname], P, DCRIT, np.random.default_rng([7, ord(sname)]))
    rel[sname] = np.array([np.mean(tr["fail"] > g) for g in grid])
    OUT.setdefault("fig5", {})[f"scenario_{sname}"] = {
        "R_at_10yr": float(np.interp(10, grid, rel[sname])),
        "R_at_15yr": float(np.interp(15, grid, rel[sname])),
        "median_life_yr": float(np.median(tr["fail"])),
        "p05_life_yr": float(np.quantile(tr["fail"], 0.05)),
        "p95_life_yr": float(np.quantile(tr["fail"], 0.95)),
    }

# Prior-predictive reliability of each model before any inspection.
rng = np.random.default_rng(11)
n = 10_000
lt_static = np.repeat(np.log(P.theta_nominal)[:, None], n, axis=1)
ft_static = forecast_failure(np.zeros(n), np.zeros(n), lt_static, P, DCRIT, rng, True, None, 60)
lt_api = np.log(sample_prior(n, rng))
ft_api = forecast_failure(np.zeros(n), np.zeros(n), lt_api, P, DCRIT, rng, True,
                          np.full((3, 1), 0.05), 60)
prior_rel = {k: np.array([np.mean(v > g) for g in grid]) for k, v in
             {"static": ft_static, "api": ft_api}.items()}

# Conditional reliability of one scenario-B pipeline after six annual inspections.
scen = SCENARIOS["B"]
tr = simulate_truth(200, scen, P, DCRIT, np.random.default_rng(12))
i = int(np.argmin(np.abs(tr["fail"] - np.quantile(tr["fail"], 0.2))))  # an early-failing pipeline
cond = {}
for name in ("SDBN", "API", "ORACLE"):
    r = np.random.default_rng(13)
    kw = {"theta_path": tr["theta_year"][:, :, i]} if name == "ORACLE" else {"theta": P.theta_nominal}
    pf = ParticleFilter(MODELS[name], P, DCRIT, r, **kw)
    for k, tk in enumerate(tr["insp_times"][:6]):
        pf.propagate(tk)
        pf.update(tr["obs"][i, k])
    drift = np.full((3, 1), scen.drift_sd) if name == "ORACLE" else None
    ft = 6.0 + pf.predict_rul(10_000, r, drift=drift)
    cond[name] = np.array([np.mean(ft > g) for g in grid])
OUT["fig5"]["example_pipeline"] = {"true_failure_yr": float(tr["fail"][i]),
                                   "true_mu": float(tr["theta_year"][5, 0, i])}

fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8), dpi=200)
ax = axes[0]
ax.plot(grid, rel["A"], color="k", lw=1.6, label="True, scenario A (Table IV)")
ax.plot(grid, rel["B"], color="0.5", lw=1.6, label="True, scenario B (heterogeneous)")
ax.plot(grid, prior_rel["static"], color="#2166ac", ls="--", lw=1.2, label="Static DBN, before inspection")
ax.plot(grid, prior_rel["api"], color="#b2182b", ls="--", lw=1.2, label="API-DBN prior, before inspection")
ax.set_title("(a) Population reliability", fontsize=10)
ax = axes[1]
labels = {"ORACLE": "Oracle (true parameters)", "API": "API-DBN", "SDBN": "Static DBN"}
cols = {"ORACLE": "k", "API": "#b2182b", "SDBN": "#2166ac"}
for name, r in cond.items():
    ax.plot(grid, r, color=cols[name], lw=1.4, label=labels[name])
ax.axvline(tr["fail"][i], color="k", ls=":", lw=1)
ax.text(tr["fail"][i] + 0.3, 0.9, "true failure", fontsize=8)
ax.set_title("(b) One scenario-B pipeline, after inspections at 1-6 yr", fontsize=10)
for ax in axes:
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Time (years)")
    ax.set_ylabel(r"Reliability $R(t)$")
    ax.legend(fontsize=7.5, loc="lower left")
fig.tight_layout()
fig.savefig(ROOT / "figures" / "fig5_replica.png")
plt.close(fig)


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return round(float(o), 6)
    if isinstance(o, np.integer):
        return int(o)
    return o


(ROOT / "results" / "checks.json").write_text(json.dumps(_clean(OUT), indent=2))
print(json.dumps(_clean(OUT), indent=2))
