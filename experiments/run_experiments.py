"""Master experiment runner and reproducibility dispatcher.

Coordinates and reproduces the experiments reported in the paper:
1. Closed-form checks and verification (Fig. 4 & 5 replicas)
2. RUL prognostics evaluation (Scenario A & B, Table VI)
3. 2x2 Factorial ablation study (Table VII)
4. Closed-loop maintenance optimization (Fig. 6 & Table V/VI)
5. Parameter sensitivity analysis
6. Paper figures and LaTeX tables generation

Usage:
    python experiments/run_experiments.py --all-summaries   # Re-generate tables and figures from results
    python experiments/run_experiments.py --checks          # Run physical checks (~30s)
    python experiments/run_experiments.py --ablation        # Inspect 2x2 ablation
    python experiments/run_experiments.py --latex           # Generate LaTeX tables
    python experiments/run_experiments.py --figures         # Generate paper figures
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def run_cmd(script: str, *args):
    cmd = [sys.executable, str(ROOT / "experiments" / script)] + list(args)
    print(f"\n>>> Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(description="Master experiment dispatcher")
    parser.add_argument("--checks", action="store_true", help="Run closed-form physics checks")
    parser.add_argument("--ablation", action="store_true", help="Show 2x2 factorial ablation")
    parser.add_argument("--latex", action="store_true", help="Re-generate LaTeX tables")
    parser.add_argument("--figures", action="store_true", help="Re-generate paper figures")
    parser.add_argument("--sensitivity", action="store_true", help="Run sensitivity analysis")
    parser.add_argument("--all-summaries", action="store_true", help="Run all summary and artifact generators")
    args = parser.parse_args()

    # If no flags provided, display help and summary
    if not any(vars(args).values()):
        parser.print_help()
        print("\nDisplaying current 2x2 ablation summary as a check:")
        run_cmd("run_ablation.py", "--scenario", "B")
        return

    if args.checks or args.all_summaries:
        run_cmd("run_checks.py")

    if args.ablation or args.all_summaries:
        run_cmd("run_ablation.py", "--scenario", "B")

    if args.latex or args.all_summaries:
        run_cmd("make_latex.py")

    if args.figures or args.all_summaries:
        run_cmd("make_paper_figures.py")

    if args.sensitivity:
        run_cmd("run_sensitivity.py")


if __name__ == "__main__":
    main()
