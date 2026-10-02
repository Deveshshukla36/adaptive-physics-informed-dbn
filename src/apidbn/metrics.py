"""Evaluation metrics of Sec. IV-C, Eqs. (19)-(22)."""
from __future__ import annotations

import numpy as np
from scipy import stats

BRIER_WINDOW = 2.0   # yr. OPEN: "failure within the evaluation window" has no stated window.
CAP = 60.0           # forecasts that never fail are censored here


def crps_samples(x_sorted: np.ndarray, y: float) -> float:
    """Eq. (19) from sorted samples: E|X - y| - 0.5 E|X - X'|."""
    n = x_sorted.size
    spread = np.dot(2.0 * np.arange(1, n + 1) - n - 1, x_sorted) / (n * n)
    return float(np.mean(np.abs(x_sorted - y)) - spread)


# Columns of the per-case summary returned by summarize().
FIELDS = ("median", "mean", "q025", "q10", "q975", "crps", "p_window")


def summarize(samples: np.ndarray, y: float) -> tuple:
    """Everything the metrics need from one predictive RUL sample, given the true RUL y."""
    x = np.sort(np.minimum(samples, CAP))
    q025, q10, med, q975 = np.quantile(x, [0.025, 0.10, 0.5, 0.975])
    return (med, x.mean(), q025, q10, q975, crps_samples(x, y), np.mean(x <= BRIER_WINDOW))


def run_metrics(y, med, crps, p_window, q025, q975) -> dict:
    """MAE, RMSE (point = predictive median), CRPS, Brier (Eq. 20), PICP (Eq. 21)."""
    err = med - y
    return {
        "MAE": float(np.mean(np.abs(err))),
        "RMSE": float(np.sqrt(np.mean(err**2))),
        "CRPS": float(np.mean(crps)),
        "Brier": float(np.mean((p_window - (y <= BRIER_WINDOW)) ** 2)),
        "PICP": float(np.mean((y >= q025) & (y <= q975))),
        "N": int(y.size),
    }


def paired_t(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    """Eq. (22): paired t statistic and two-sided p-value for per-run metrics."""
    res = stats.ttest_rel(a, b)
    return float(res.statistic), float(res.pvalue)


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    phat = k / n
    denom = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    half = z * np.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / denom
    return centre - half, centre + half
