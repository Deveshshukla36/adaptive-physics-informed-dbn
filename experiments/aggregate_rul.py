"""Build Tables VI and VII (and supporting diagnostics) from run_rul.py output.

Usage: python experiments/aggregate_rul.py A   (or B). Writes results/table6_<scenario>.{json,md}.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))

from apidbn.metrics import paired_t, run_metrics, wilson  # noqa: E402

NAMES = {"FW": "Fixed Wiener", "SDBN": "Static DBN", "PF": "PF w/o MCMC", "NC": "No coupling",
         "API": "API-DBN", "NC0": "No coupling, w/o MCMC", "ORACLE": "Oracle (true parameters)"}
METRICS = ("MAE", "RMSE", "CRPS", "Brier", "PICP")


def load(scen: str, folder: Path | None = None):
    folder = folder or ROOT / "results" / f"rul_{scen}"
    rows, timing, models, cols = [], [], None, None
    for f in sorted(folder.glob(f"{scen}_s*_c*.npz")):
        seed = int(re.search(r"_s(\d+)_", f.name).group(1))
        d = np.load(f)
        models, cols = list(d["models"]), list(d["columns"])
        r = d["rows"]
        rows.append(np.column_stack([np.full(len(r), seed), r]))
        tm = d["timing"]
        timing.append(np.column_stack([np.full(len(tm), seed), tm]))
    if not rows:
        raise SystemExit(f"no results in {folder}")
    cols = ["seed"] + cols
    data = np.vstack(rows)
    return {c: data[:, j] for j, c in enumerate(cols)}, np.vstack(timing), models


def per_seed(d, m_idx, point="median"):
    seeds = np.unique(d["seed"]).astype(int)
    out = {k: [] for k in METRICS}
    for s in seeds:
        sel = (d["model"] == m_idx) & (d["seed"] == s)
        r = run_metrics(d["y"][sel], d[point][sel], d["crps"][sel], d["p_window"][sel],
                        d["q025"][sel], d["q975"][sel])
        for k in METRICS:
            out[k].append(r[k])
    return {k: np.array(v) for k, v in out.items()}, seeds


def fmt(m, s, nd=2):
    return f"{m:.{nd}f} ± {s:.{nd}f}"


def main(scen: str):
    d, timing, models = load(scen)
    idx = {m: i for i, m in enumerate(models)}
    res = {"scenario": scen, "models": {}, "paired_t_vs_API": {}, "n_seeds": 0}
    seedwise = {}
    for m in models:
        ps, seeds = per_seed(d, idx[m])
        seedwise[m] = ps
        sel = d["model"] == idx[m]
        covered = int(np.sum((d["y"][sel] >= d["q025"][sel]) & (d["y"][sel] <= d["q975"][sel])))
        n = int(sel.sum())
        lo, hi = wilson(covered, n)
        err_mean = np.abs(d["mean"][sel] - d["y"][sel])
        res["models"][m] = {
            "name": NAMES[m],
            **{k: {"mean": float(ps[k].mean()), "sd": float(ps[k].std(ddof=1))} for k in METRICS},
            "PICP_pooled": covered / n, "PICP_wilson95": [lo, hi], "N_cases": n,
            "N_pipelines": int(len(np.unique(d["seed"][sel] * 100_000 + d["pipe"][sel]))),
            "MAE_using_mean": float(err_mean.mean()),
            "mean_interval_width": float(np.mean(d["q975"][sel] - d["q025"][sel])),
            "mean_bias": float(np.mean(d["median"][sel] - d["y"][sel])),
        }
        res["n_seeds"] = int(len(seeds))
    for m in models:
        if m == "API":
            continue
        res["paired_t_vs_API"][m] = {}
        for k in ("MAE", "RMSE", "CRPS", "Brier"):
            t, p = paired_t(seedwise[m][k], seedwise["API"][k])
            res["paired_t_vs_API"][m][k] = {"mean_diff": float(np.mean(seedwise[m][k] - seedwise["API"][k])),
                                            "t": t, "p": p}

    # MAE by remaining life: the error that matters for maintenance is near the end.
    bins = [(0, 2), (2, 5), (5, 10), (10, 100)]
    res["MAE_by_true_RUL"] = {}
    for m in models:
        sel = d["model"] == idx[m]
        y, med = d["y"][sel], d["median"][sel]
        res["MAE_by_true_RUL"][m] = {f"{a}-{b}": float(np.mean(np.abs(med - y)[(y > a) & (y <= b)]))
                                     for a, b in bins}

    # Parameter tracking of the adaptive models: relative error of the posterior mean of mu.
    res["mu_tracking_rel_error"] = {}
    for m in ("PF", "API"):
        sel = d["model"] == idx[m]
        rel = np.abs(d["mu_hat"][sel] / d["mu_true"][sel] - 1)
        t = d["t"][sel]
        res["mu_tracking_rel_error"][m] = {f"t={int(k)}": float(rel[t == k].mean()) for k in (1, 3, 5, 8, 10)
                                           if np.any(t == k)}

    # Runtime and MCMC diagnostics (timing columns: seed, model, pipe, t_filter, t_total, acc, n_resample).
    res["runtime"] = {}
    n_insp = {}
    for m in models:
        sel = d["model"] == idx[m]
        key = d["seed"][sel] * 100_000 + d["pipe"][sel]
        n_insp[m] = np.mean(np.unique(key, return_counts=True)[1])
    for m in models:
        tm = timing[timing[:, 1] == idx[m]]
        res["runtime"][m] = {
            "filter_s_per_pipeline": float(tm[:, 3].mean()),
            "filter_s_per_200_steps": float(tm[:, 3].mean() / n_insp[m] * 20),
            "total_s_per_pipeline_incl_RUL": float(tm[:, 4].mean()),
            "mean_inspections_per_pipeline": float(n_insp[m]),
            "mcmc_acceptance": float(np.nanmean(tm[:, 5])) if np.isfinite(tm[:, 5]).any() else None,
            "resampling_events_per_pipeline": float(tm[:, 6].mean()),
        }

    (ROOT / "results" / f"table6_{scen}.json").write_text(json.dumps(res, indent=2))

    # Markdown tables in the manuscript's layout.
    order = [m for m in ["FW", "SDBN", "PF", "NC", "API", "NC0", "ORACLE"] if m in models]
    lines = [f"## Scenario {scen}: RUL prediction (mean ± s.d. over {res['n_seeds']} matched runs)", "",
             "| Model | MAE (yr) | RMSE (yr) | CRPS (yr) | Brier (2-yr window) | PICP (pooled, Wilson 95%) | N cases |",
             "|---|---|---|---|---|---|---|"]
    for m in order:
        r = res["models"][m]
        lo, hi = r["PICP_wilson95"]
        lines.append(f"| {r['name']} | {fmt(r['MAE']['mean'], r['MAE']['sd'])} | "
                     f"{fmt(r['RMSE']['mean'], r['RMSE']['sd'])} | {fmt(r['CRPS']['mean'], r['CRPS']['sd'])} | "
                     f"{fmt(r['Brier']['mean'], r['Brier']['sd'], 3)} | {100 * r['PICP_pooled']:.1f}% "
                     f"[{100 * lo:.1f}, {100 * hi:.1f}] | {r['N_cases']} |")
    lines += ["", "Paired t-tests against API-DBN over the matched runs (df = n_seeds - 1):", "",
              "| Model | ΔMAE | t | p | ΔCRPS | t | p |", "|---|---|---|---|---|---|---|"]
    for m in order:
        if m == "API":
            continue
        a, c = res["paired_t_vs_API"][m]["MAE"], res["paired_t_vs_API"][m]["CRPS"]
        lines.append(f"| {NAMES[m]} | {a['mean_diff']:+.3f} | {a['t']:.1f} | {a['p']:.1e} | "
                     f"{c['mean_diff']:+.3f} | {c['t']:.1f} | {c['p']:.1e} |")
    t7 = {k: res["models"][k]["MAE"]["mean"] for k in ("NC0", "PF", "NC", "API") if k in res["models"]}
    if len(t7) == 4:
        lines += ["", "Table VII as a true 2x2 factorial (all four are adaptive; MAE, yr):", "",
                  "| | Coupling off | Coupling on |", "|---|---|---|",
                  f"| MCMC off | {t7['NC0']:.2f} | {t7['PF']:.2f} |",
                  f"| MCMC on | {t7['NC']:.2f} | {t7['API']:.2f} |"]
    lines += ["", "MAE by true remaining life (yr):", "",
              "| Model | " + " | ".join(f"RUL {b}" for b in res["MAE_by_true_RUL"][order[0]]) + " |",
              "|---|" + "---|" * len(bins)]
    for m in order:
        lines.append(f"| {NAMES[m]} | " + " | ".join(f"{v:.2f}" for v in res["MAE_by_true_RUL"][m].values()) + " |")
    (ROOT / "results" / f"table6_{scen}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\nruntime/diagnostics:", json.dumps(res["runtime"], indent=1))
    print("mu tracking:", json.dumps(res["mu_tracking_rel_error"]))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "B")
