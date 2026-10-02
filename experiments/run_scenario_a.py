"""Run or summarize Scenario A: literal parameters (identical across pipelines).

In Scenario A, every pipeline is generated with the exact Table IV parameters
which do not vary or drift. This baseline demonstrates that sequential parameter
adaptation is unnecessary when the true parameters are already known and constant.

Usage:
    python experiments/run_scenario_a.py --pipes 100 --seeds 30
    python experiments/run_scenario_a.py --summarize-only
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
    parser = argparse.ArgumentParser(description="Scenario A evaluation (identical parameters)")
    parser.add_argument("--pipes", type=int, default=100, help="Pipelines per seed (default 100)")
    parser.add_argument("--seeds", type=int, default=30, help="Number of seeds (default 30)")
    parser.add_argument("--chunks", type=int, default=10, help="Task chunks per seed")
    parser.add_argument("--workers", type=int, default=None, help="Parallel worker processes")
    parser.add_argument("--summarize-only", action="store_true", help="Only build tables from existing results")
    args = parser.parse_args()

    if not args.summarize_only:
        cmd = [
            sys.executable,
            str(ROOT / "experiments" / "run_rul.py"),
            "--scenario", "A",
            "--pipes", str(args.pipes),
            "--seeds", str(args.seeds),
            "--chunks", str(args.chunks),
        ]
        if args.workers:
            cmd.extend(["--workers", str(args.workers)])
        print(f"[Scenario A] Running simulation: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

    # Run aggregation
    cmd_agg = [
        sys.executable,
        str(ROOT / "experiments" / "aggregate_rul.py"),
        "A"
    ]
    print(f"[Scenario A] Aggregating results: {' '.join(cmd_agg)}")
    subprocess.run(cmd_agg, check=True)


if __name__ == "__main__":
    main()
