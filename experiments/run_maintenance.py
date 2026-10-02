"""Sec. V-B replica: grid search of (I, gamma) with closed-loop, ground-truth costs.

Usage: python experiments/run_maintenance.py --scenario B --pipes 2000
Writes one .npz per (model, chunk) to results/maint_<scenario>/, then summarises
to results/maintenance_<scenario>.json and figures/fig6_replica_<scenario>.png.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))

from apidbn.core import Physics, critical_depth  # noqa: E402
from apidbn.maintenance import Costs, PipelineWorld, run_policy  # noqa: E402
from apidbn.truth import SCENARIOS  # noqa: E402

MODELS_M = ["SDBN", "API", "ORACLE"]
I_GRID = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
G_GRID = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
SCEN_CODE = {"A": 0, "B": 1}


def run_task(args) -> str:
    scen_name, model, chunk, pipes, J, outdir = args
    out = Path(outdir) / f"{scen_name}_{model}_c{chunk:03d}.npz"
    if out.exists():
        return str(out)
    p, costs, scen = Physics(), Costs(), SCENARIOS[scen_name]
    dcrit = critical_depth(p)
    code, m_idx = SCEN_CODE[scen_name], MODELS_M.index(model)
    res = np.zeros((len(I_GRID), len(G_GRID), len(pipes), 4))
    for k, i in enumerate(pipes):
        world = PipelineWorld(scen, p, np.random.default_rng([code, 777, int(i)]), costs.horizon)
        for a, I in enumerate(I_GRID):
            for b, g in enumerate(G_GRID):
                rng = np.random.default_rng([code, 778, int(i), m_idx, a, b])
                res[a, b, k] = run_policy(model, I, g, world, p, dcrit, costs, rng, J=J,
                                          drift_sd=scen.drift_sd)
    np.savez(out, res=res, pipes=np.asarray(pipes))
    return str(out)


def summarise(scen_name: str, outdir: Path) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    summary = {"scenario": scen_name, "I_grid": I_GRID, "gamma_grid": G_GRID, "models": {}}
    fig, axes = plt.subplots(1, len(MODELS_M), figsize=(4.2 * len(MODELS_M), 3.6), dpi=200)
    all_costs = {}
    for model in MODELS_M:
        files = sorted(outdir.glob(f"{scen_name}_{model}_c*.npz"))
        if not files:
            continue
        res = np.concatenate([np.load(f)["res"] for f in files], axis=2)
        cost = res[..., 0]
        mean, se = cost.mean(axis=2), cost.std(axis=2, ddof=1) / np.sqrt(cost.shape[2])
        all_costs[model] = mean
        a, b = np.unravel_index(np.argmin(mean), mean.shape)
        at_paper = (I_GRID.index(2.0), G_GRID.index(1.5))
        summary["models"][model] = {
            "n_pipelines": int(cost.shape[2]),
            "optimum": {"I": I_GRID[a], "gamma": G_GRID[b], "cost_k$": float(mean[a, b]),
                        "se_k$": float(se[a, b]),
                        "P_any_failure": float(np.mean(res[a, b, :, 1] > 0)),
                        "failures_per_pipeline": float(res[a, b, :, 1].mean()),
                        "replacements_per_pipeline": float(res[a, b, :, 2].mean()),
                        "inspections_per_pipeline": float(res[a, b, :, 3].mean())},
            "paper_policy_I2_g1.5": {"cost_k$": float(mean[at_paper]), "se_k$": float(se[at_paper]),
                                     "P_any_failure": float(np.mean(res[at_paper][:, 1] > 0))},
            "cost_grid_k$": np.round(mean, 1).tolist(),
            "failure_prob_grid": np.round(np.mean(res[..., 1] > 0, axis=2), 4).tolist(),
        }
        ax = axes[MODELS_M.index(model)]
        im = ax.imshow(mean.T, origin="lower", aspect="auto", cmap="viridis",
                       extent=[I_GRID[0] - 0.25, I_GRID[-1] + 0.25, G_GRID[0] - 0.25, G_GRID[-1] + 0.25],
                       vmin=np.min(mean), vmax=min(np.max(mean), 4 * np.min(mean)))
        ax.plot(I_GRID[a], G_GRID[b], marker="*", color="red", ms=12)
        ax.set_title({"SDBN": "Static DBN", "API": "API-DBN", "ORACLE": "Oracle (true parameters)"}[model]
                     + f"\noptimum I={I_GRID[a]}, γ={G_GRID[b]}: {mean[a, b]:.0f} k$", fontsize=9)
        ax.set_xlabel("Inspection interval $I$ (years)")
        ax.set_ylabel(r"PM threshold $\gamma$ on 10th-pct RUL (years)")
        fig.colorbar(im, ax=ax, label="Expected discounted cost (k$)")
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / f"fig6_replica_{scen_name}.png")
    plt.close(fig)
    if "API" in all_costs and "SDBN" in all_costs:
        s, a = summary["models"]["SDBN"]["optimum"], summary["models"]["API"]["optimum"]
        summary["API_vs_SDBN_reduction"] = (s["cost_k$"] - a["cost_k$"]) / s["cost_k$"]
    (ROOT / "results" / f"maintenance_{scen_name}.json").write_text(json.dumps(summary, indent=2))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True, choices=list(SCENARIOS))
    ap.add_argument("--pipes", type=int, default=2000)
    ap.add_argument("--chunk", type=int, default=25, help="pipelines per task")
    ap.add_argument("--J", type=int, default=2000, help="forecast paths per decision")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--out", default=None)
    ap.add_argument("--summarise-only", action="store_true")
    args = ap.parse_args()
    outdir = Path(args.out) if args.out else ROOT / "results" / f"maint_{args.scenario}"
    outdir.mkdir(parents=True, exist_ok=True)
    if not args.summarise_only:
        chunks = [list(range(s, min(s + args.chunk, args.pipes))) for s in range(0, args.pipes, args.chunk)]
        tasks = [(args.scenario, m, c, pipes, args.J, str(outdir))
                 for c, pipes in enumerate(chunks) for m in MODELS_M]
        start = time.time()
        with Pool(args.workers) as pool:
            for n_done, path in enumerate(pool.imap_unordered(run_task, tasks), 1):
                el = time.time() - start
                print(f"[maint {args.scenario}] {n_done}/{len(tasks)} done, {el / 60:.1f} min elapsed, "
                      f"~{el / n_done * (len(tasks) - n_done) / 60:.1f} min left ({Path(path).name})", flush=True)
    s = summarise(args.scenario, outdir)
    print(json.dumps({m: {"optimum": v["optimum"], "paper_policy": v["paper_policy_I2_g1.5"]}
                      for m, v in s["models"].items()}, indent=1))
    if "API_vs_SDBN_reduction" in s:
        print(f"API-DBN vs static DBN cost reduction: {100 * s['API_vs_SDBN_reduction']:.1f}%")


if __name__ == "__main__":
    main()
