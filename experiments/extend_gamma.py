"""Extend the maintenance grid of run_maintenance.py to gamma in {3.5, 4.0, 4.5, 5.0}.

The original grid stops at gamma = 3.0, where every model's optimum sat. Each
(pipeline, model, I, gamma) cell uses the seed it would have had in one run
over the full grid, and every pipeline's world is seeded by its index, so
merging the new columns with the existing ones equals running the full grid.

Usage: python experiments/extend_gamma.py --scenario B --pipes 1500
Writes results/maint_<s>_ext/, results/maintenance_<s>_full.json and
figures/fig6_replica_<s>_full.png.
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
sys.path.insert(0, str(ROOT / "experiments"))

from apidbn.core import Physics, critical_depth  # noqa: E402
from apidbn.maintenance import Costs, PipelineWorld, run_policy  # noqa: E402
from apidbn.truth import SCENARIOS  # noqa: E402
from run_maintenance import G_GRID, I_GRID, MODELS_M, SCEN_CODE  # noqa: E402

G_EXT = [3.5, 4.0, 4.5, 5.0]
G_FULL = G_GRID + G_EXT


def run_task(args) -> str:
    scen_name, model, chunk, pipes, J, outdir = args
    out = Path(outdir) / f"{scen_name}_{model}_c{chunk:03d}.npz"
    if out.exists():
        return str(out)
    p, costs, scen = Physics(), Costs(), SCENARIOS[scen_name]
    dcrit = critical_depth(p)
    code, m_idx = SCEN_CODE[scen_name], MODELS_M.index(model)
    res = np.zeros((len(I_GRID), len(G_EXT), len(pipes), 4))
    for k, i in enumerate(pipes):
        world = PipelineWorld(scen, p, np.random.default_rng([code, 777, int(i)]), costs.horizon)
        for a, I in enumerate(I_GRID):
            for bb, g in enumerate(G_EXT):
                b = G_FULL.index(g)  # the seed index it has in the full grid
                rng = np.random.default_rng([code, 778, int(i), m_idx, a, b])
                res[a, bb, k] = run_policy(model, I, g, world, p, dcrit, costs, rng, J=J,
                                           drift_sd=scen.drift_sd)
    np.savez(out, res=res, pipes=np.asarray(pipes))
    return str(out)


def merged(scen: str, model: str) -> np.ndarray:
    base = ROOT / "results" / f"maint_{scen}"
    ext = ROOT / "results" / f"maint_{scen}_ext"
    old = np.concatenate([np.load(f)["res"] for f in sorted(base.glob(f"{scen}_{model}_c*.npz"))], axis=2)
    new = np.concatenate([np.load(f)["res"] for f in sorted(ext.glob(f"{scen}_{model}_c*.npz"))], axis=2)
    return np.concatenate([old, new], axis=1)  # (I, gamma_full, pipes, 4)


def summarise(scen: str) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = {"SDBN": "Static DBN", "API": "API-DBN", "ORACLE": "Oracle (true parameters)"}
    out = {"scenario": scen, "I_grid": I_GRID, "gamma_grid": G_FULL, "models": {}}
    means = {m: merged(scen, m)[..., 0].mean(axis=2) for m in MODELS_M}
    vmin = min(v.min() for v in means.values())
    fig, axes = plt.subplots(1, 3, figsize=(12.6, 3.9), dpi=200)
    for ax, model in zip(axes, MODELS_M):
        res = merged(scen, model)
        cost = res[..., 0]
        mean, se = cost.mean(axis=2), cost.std(axis=2, ddof=1) / np.sqrt(cost.shape[2])
        a, b = np.unravel_index(np.argmin(mean), mean.shape)
        pa, pb = I_GRID.index(2.0), G_FULL.index(1.5)
        out["models"][model] = {
            "n_pipelines": int(cost.shape[2]),
            "optimum": {"I": I_GRID[a], "gamma": G_FULL[b], "cost_k$": float(mean[a, b]), "se_k$": float(se[a, b]),
                        "P_any_failure": float(np.mean(res[a, b, :, 1] > 0)),
                        "replacements_per_pipeline": float(res[a, b, :, 2].mean()),
                        "inspections_per_pipeline": float(res[a, b, :, 3].mean())},
            "paper_policy_I2_g1.5": {"cost_k$": float(mean[pa, pb]), "se_k$": float(se[pa, pb]),
                                     "P_any_failure": float(np.mean(res[pa, pb, :, 1] > 0))},
            "cost_grid_k$": np.round(mean, 1).tolist(),
            "failure_prob_grid": np.round(np.mean(res[..., 1] > 0, axis=2), 4).tolist(),
        }
        im = ax.imshow(mean.T, origin="lower", aspect="auto", cmap="viridis",
                       extent=[I_GRID[0] - 0.25, I_GRID[-1] + 0.25, G_FULL[0] - 0.25, G_FULL[-1] + 0.25],
                       vmin=vmin, vmax=3 * vmin)
        ax.plot(I_GRID[a], G_FULL[b], marker="*", color="red", ms=13, mec="white", mew=0.8)
        ax.plot(2.0, 1.5, marker="x", color="white", ms=8, mew=2)
        ax.set_title(f"{names[model]}\nminimum at I = {I_GRID[a]:.1f} yr, γ = {G_FULL[b]:.1f} yr: "
                     f"{mean[a, b]:.0f} k$", fontsize=9)
        ax.set_xlabel("Inspection interval $I$ (yr)")
        ax.set_ylabel(r"Threshold $\gamma$ on 10th-percentile RUL (yr)")
    cb = fig.colorbar(im, ax=axes, shrink=0.9, pad=0.015)
    cb.set_label("Expected discounted cost (k$), capped at 3× minimum")
    fig.savefig(ROOT / "figures" / f"fig6_replica_{scen}_full.png", bbox_inches="tight")
    plt.close(fig)
    s, a = out["models"]["SDBN"]["optimum"], out["models"]["API"]["optimum"]
    out["API_vs_SDBN_reduction"] = (s["cost_k$"] - a["cost_k$"]) / s["cost_k$"]
    (ROOT / "results" / f"maintenance_{scen}_full.json").write_text(json.dumps(out, indent=2))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="B", choices=list(SCENARIOS))
    ap.add_argument("--pipes", type=int, default=1500)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--J", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--summarise-only", action="store_true")
    args = ap.parse_args()
    outdir = ROOT / "results" / f"maint_{args.scenario}_ext"
    outdir.mkdir(parents=True, exist_ok=True)
    if not args.summarise_only:
        chunks = [list(range(s, min(s + args.chunk, args.pipes))) for s in range(0, args.pipes, args.chunk)]
        tasks = [(args.scenario, m, c, pipes, args.J, str(outdir)) for c, pipes in enumerate(chunks) for m in MODELS_M]
        start = time.time()
        with Pool(args.workers) as pool:
            for n, path in enumerate(pool.imap_unordered(run_task, tasks), 1):
                el = time.time() - start
                print(f"[ext {args.scenario}] {n}/{len(tasks)} done, {el / 60:.1f} min, "
                      f"~{el / n * (len(tasks) - n) / 60:.1f} min left", flush=True)
    s = summarise(args.scenario)
    print(json.dumps({m: v["optimum"] for m, v in s["models"].items()}, indent=1))
    print(f"API-DBN vs static DBN: {100 * s['API_vs_SDBN_reduction']:.1f}% lower cost")


if __name__ == "__main__":
    main()
