"""RUL prediction experiment runner for Tables VI and VII across 30 matched seeds.

Each task (scenario, seed, chunk) writes one .npz, so an interrupted run resumes
where it stopped. Usage:
    python experiments/run_rul.py --scenario B --pipes 333 --chunks 20
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))

from apidbn.core import Physics, critical_depth  # noqa: E402
from apidbn.filters import MODELS, FixedWiener, ParticleFilter  # noqa: E402
from apidbn.metrics import summarize  # noqa: E402
from apidbn.truth import SCENARIOS, simulate_truth  # noqa: E402

MODEL_ORDER = ["FW", "SDBN", "PF", "NC", "API", "NC0", "ORACLE"]
SCEN_CODE = {"A": 0, "B": 1}
COLUMNS = ("model", "pipe", "t", "y", "median", "mean", "q025", "q10", "q975", "crps", "p_window",
           "mu_hat", "lam_hat", "sig_hat", "mu_true", "lam_true", "sig_true")
J = 10_000


def calibrate_fixed_wiener(scen_name: str, n_train: int = 2000) -> tuple[float, float]:
    """Offline calibration of model 1 on training pipelines that never enter the test set."""
    p = Physics()
    scen = SCENARIOS[scen_name]
    dcrit = critical_depth(p)
    train = simulate_truth(n_train, scen, p, dcrit, np.random.default_rng([SCEN_CODE[scen_name], 10_000]))
    fw = FixedWiener.calibrate(train["obs"], scen.insp_interval, p.sigma_v, dcrit)
    return fw.mu, fw.sig


def run_task(args) -> str:
    scen_name, seed, chunk, n_pipes, n_chunks, fw_params, outdir = args
    out = Path(outdir) / f"{scen_name}_s{seed:02d}_c{chunk:02d}.npz"
    if out.exists():
        return str(out)
    p = Physics()
    dcrit = critical_depth(p)
    scen = SCENARIOS[scen_name]
    code = SCEN_CODE[scen_name]
    # Same truth for every chunk of a seed: regenerate it from the seed alone.
    truth = simulate_truth(n_pipes, scen, p, dcrit, np.random.default_rng([code, seed, 0]))
    fw = FixedWiener(*fw_params, dcrit)
    drift = np.full((3, 1), scen.drift_sd) if scen.drift_sd > 0 else None

    rows, timing = [], []
    for i in np.array_split(np.arange(n_pipes), n_chunks)[chunk]:
        for m_idx, name in enumerate(MODEL_ORDER):
            rng = np.random.default_rng([code, seed, 1, int(i), m_idx])
            if name == "FW":
                pf = None
            elif name == "ORACLE":
                pf = ParticleFilter(MODELS[name], p, dcrit, rng, theta_path=truth["theta_year"][:, :, i])
            else:
                pf = ParticleFilter(MODELS[name], p, dcrit, rng, theta=p.theta_nominal)
            t_filter = t_total = 0.0
            for k, t in enumerate(truth["insp_times"]):
                if t >= truth["fail"][i]:
                    break
                y = truth["fail"][i] - t
                a = time.perf_counter()
                if pf is None:
                    rul = fw.predict_rul(truth["obs"][i, k], J, rng)
                    th = (np.nan, np.nan, np.nan)
                else:
                    pf.propagate(t)
                    pf.update(truth["obs"][i, k])
                    t_filter += time.perf_counter() - a
                    rul = pf.predict_rul(J, rng, drift=drift if name == "ORACLE" else None)
                    th = pf.posterior_mean_theta() if pf.cfg.adaptive else (np.nan, np.nan, np.nan)
                t_total += time.perf_counter() - a
                true_th = truth["theta_year"][int(t) - 1, :, i]
                rows.append((m_idx, i, t, y, *summarize(rul, y), *th, *true_th))
            acc = np.mean(pf.acceptance) if (pf is not None and pf.acceptance) else np.nan
            nres = pf.n_resample if pf is not None else 0
            timing.append((m_idx, i, t_filter, t_total, acc, nres))
    np.savez(out, rows=np.array(rows, dtype=float), timing=np.array(timing, dtype=float),
             columns=np.array(COLUMNS), models=np.array(MODEL_ORDER))
    return str(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True, choices=list(SCENARIOS))
    ap.add_argument("--pipes", type=int, default=333, help="test pipelines per seed")
    ap.add_argument("--chunks", type=int, default=20, help="tasks per seed")
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--out", default=None, help="output folder (default results/rul_<scenario>)")
    args = ap.parse_args()

    outdir = Path(args.out) if args.out else ROOT / "results" / f"rul_{args.scenario}"
    outdir.mkdir(parents=True, exist_ok=True)
    fw_params = calibrate_fixed_wiener(args.scenario)
    print(f"[{args.scenario}] fixed-Wiener calibration: mu={fw_params[0]:.4f} mm/yr, "
          f"sigma={fw_params[1]:.4f} mm/yr^0.5", flush=True)
    tasks = [(args.scenario, s, c, args.pipes, args.chunks, fw_params, str(outdir))
             for s in range(args.seeds) for c in range(args.chunks)]
    start = time.time()
    with Pool(args.workers) as pool:
        for n_done, path in enumerate(pool.imap_unordered(run_task, tasks), 1):
            el = time.time() - start
            print(f"[{args.scenario}] {n_done}/{len(tasks)} done, {el / 60:.1f} min elapsed, "
                  f"~{el / n_done * (len(tasks) - n_done) / 60:.1f} min left  ({Path(path).name})", flush=True)
    print(f"[{args.scenario}] finished in {(time.time() - start) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
