"""Run or summarize Scenario B: heterogeneous, drifting degradation parameters.

In Scenario B, each pipeline receives its own baseline parameters:
    (mu^(0), lambda^(0), sigma_B) = Table IV * exp(N(0, 0.25^2))
which drift annually by the log-random walks of Eqs. (12)-(14).
This represents the realistic setting where assets vary and conditions change,
evaluating adaptive parameter updating and uncertainty quantification.

Usage:
    python experiments/run_scenario_b.py --pipes 333 --seeds 30
    python experiments/run_scenario_b.py --summarize-only
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description="Scenario B evaluation (heterogeneous drifting parameters)")
    parser.add_argument("--pipes", type=int, default=333, help="Pipelines per seed (default 333, total 9,990)")
    parser.add_argument("--seeds", type=int, default=30, help="Number of seeds (default 30)")
    parser.add_argument("--chunks", type=int, default=20, help="Task chunks per seed")
    parser.add_argument("--workers", type=int, default=None, help="Parallel worker processes")
    parser.add_argument("--summarize-only", action="store_true", help="Only build tables from existing results")
    args = parser.parse_args()

    if not args.summarize_only:
        cmd = [
            sys.executable,
            str(ROOT / "experiments" / "run_rul.py"),
            "--scenario", "B",
            "--pipes", str(args.pipes),
            "--seeds", str(args.seeds),
            "--chunks", str(args.chunks),
        ]
        if args.workers:
            cmd.extend(["--workers", str(args.workers)])
        print(f"[Scenario B] Running simulation: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

    # Run aggregation
    cmd_agg = [
        sys.executable,
        str(ROOT / "experiments" / "aggregate_rul.py"),
        "B"
    ]
    print(f"[Scenario B] Aggregating results: {' '.join(cmd_agg)}")
    subprocess.run(cmd_agg, check=True)


if __name__ == "__main__":
    main()
