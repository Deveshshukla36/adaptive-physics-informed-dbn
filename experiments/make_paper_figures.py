"""Publication-size figures for the revised manuscript (IEEE column width 3.5 in).

Figs. 1-3 are the method diagrams, redrawn; Figs. 4-6 come from the replica with
the same seeds as run_checks.py and extend_gamma.py, so the numbers quoted in
the text match the plots. Usage: python experiments/make_paper_figures.py [--fig6]
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))
OUT = ROOT / "paper" / "figures"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8,
    "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7, "xtick.labelsize": 7,
    "ytick.labelsize": 7, "savefig.dpi": 400,
})
INK = "#1f1f1f"
BLUE = "#2166ac"
RED = "#b2182b"
GREEN = "#1b7837"


# ------------------------------------------------------------------ diagram helpers
def box(ax, x, y, w, h, text, fc="#eef3fa", ec=BLUE, fs=7.5):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fc, ec=ec, lw=0.9))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.15)


def diamond(ax, x, y, w, h, text, fs=7.5):
    ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)],
                         closed=True, fc="#fdf3e7", ec="#b35806", lw=0.9))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=INK)


def arrow(ax, p, q, rad=0.0, dashed=False, color=INK, lw=0.9, shrink=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=8, lw=lw, color=color,
                                 linestyle=(0, (4, 2.5)) if dashed else "solid",
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=shrink, shrinkB=shrink))


def polyline_arrow(ax, pts, color=INK, lw=0.9, dashed=False):
    xs, ys = zip(*pts)
    ax.plot(xs[:-1], ys[:-1], color=color, lw=lw, linestyle="--" if dashed else "-", solid_capstyle="butt")
    arrow(ax, pts[-2], pts[-1], color=color, lw=lw, dashed=dashed)


def fig1_workflow():
    fig, ax = plt.subplots(figsize=(3.5, 4.3))
    ax.set_xlim(0, 3.5)
    ax.set_ylim(0, 4.3)
    ax.axis("off")
    steps = [
        "(1) BSEE/NETL data collection and\npreprocessing (Sec. IV-A)",
        "(2) Physics-informed corrosion–shock\nmodel (Sec. III-A)",
        "(3) Time-sliced DBN construction\n(Sec. III-B)",
        "(4) Sequential SMC–MCMC updating of\nstate and parameters (Alg. 1)",
        "(5) Monte Carlo RUL forecast\n(Sec. III-C, Eq. (16))",
        "(6) Risk–cost inspection and replacement\ndecision (Eqs. (17)–(18))",
        "(7) Evaluation on controlled\nsimulations (Sec. V)",
    ]
    x, w, h = 1.45, 2.55, 0.43
    ys = np.linspace(3.95, 0.35, len(steps))
    for y, s in zip(ys, steps):
        box(ax, x, y, w, h, s, fc="#f7f1e3" if s.startswith("(7)") else "#eef3fa",
            ec="#8c6d31" if s.startswith("(7)") else BLUE)
    for y0, y1 in zip(ys[:-1], ys[1:]):
        arrow(ax, (x, y0 - h / 2), (x, y1 + h / 2))
    # feedback: decision at (6) schedules the next inspection, whose data re-enter (4)
    xr = x + w / 2
    polyline_arrow(ax, [(xr, ys[5]), (xr + 0.32, ys[5]), (xr + 0.32, ys[3]), (xr + 0.02, ys[3])], color=RED)
    ax.text(xr + 0.37, (ys[3] + ys[5]) / 2, "next\ninspection:\nnew data $o_k$", color=RED, fontsize=7,
            va="center", ha="left")
    fig.savefig(OUT / "fig1_workflow.png", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def fig2_dbn():
    fig, ax = plt.subplots(figsize=(3.5, 3.15))
    ax.set_xlim(-0.35, 5.35)
    ax.set_ylim(-0.75, 4.55)
    ax.set_aspect("equal")
    ax.axis("off")
    R = 0.3
    cols = {"k": 1.0, "k+1": 4.0}
    rows = {"th": 4.0, "X": 3.0, "S": 2.0, "Z": 1.0, "O": 0.0}
    labels = {"th": r"\theta", "X": "X", "S": "S", "Z": "Z", "O": "O"}
    pos = {}
    for sl, cx in cols.items():
        for key, cy in rows.items():
            pos[(key, sl)] = (cx, cy)
        pos[("F", sl)] = (cx + 0.95, 0.0)
    for (key, sl), (cx, cy) in pos.items():
        fc = "#fdf3e7" if key == "th" else ("#e8f1e4" if key in ("O", "F") else "#eef3fa")
        ax.add_patch(plt.Circle((cx, cy), R, fc=fc, ec=INK, lw=0.8))
        name = labels.get(key, "F")
        ax.text(cx, cy, f"${name}_{{{sl}}}$", ha="center", va="center", fontsize=8)
    for sl, cx in cols.items():
        ax.text(cx + 0.45, 4.45, f"slice $t_{{{sl}}}$", ha="center", fontsize=7.5, color="#555555")

    def edge(a, b, rad=0.0, dashed=False, color=INK):
        (x0, y0), (x1, y1) = pos[a], pos[b]
        d = np.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / d, (y1 - y0) / d
        arrow(ax, (x0 + ux * R, y0 + uy * R), (x1 - ux * R, y1 - uy * R), rad=rad, dashed=dashed, color=color)

    for sl in cols:
        edge(("th", sl), ("X", sl))
        edge(("th", sl), ("S", sl), rad=0.45)
        edge(("X", sl), ("Z", sl), rad=-0.45)
        edge(("S", sl), ("Z", sl))
        edge(("Z", sl), ("O", sl))
        edge(("Z", sl), ("F", sl))
    for key in ("th", "X", "S"):
        edge((key, "k"), (key, "k+1"))
    edge(("Z", "k"), ("X", "k+1"), dashed=True, color=RED)
    edge(("X", "k"), ("S", "k+1"), dashed=True, color=RED)
    lab = dict(color=RED, fontsize=7, ha="center", va="center",
               bbox=dict(fc="white", ec="none", pad=0.4))
    ax.text(2.02, 1.64, "Eq. (5)", rotation=36.9, **lab)
    ax.text(2.0, 2.66, "Eq. (6)", rotation=-18.3, **lab)
    ax.text(2.5, -0.62, r"$\theta_k=(\mu^{(0)}_k,\lambda^{(0)}_k,\sigma_{B,k})$;  dashed: lagged coupling",
            ha="center", fontsize=7, color="#333333")
    fig.savefig(OUT / "fig2_dbn.png", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def fig3_flow():
    fig, ax = plt.subplots(figsize=(3.5, 5.1))
    ax.set_xlim(0, 3.5)
    ax.set_ylim(-0.25, 4.9)
    ax.axis("off")
    x, w, h = 1.6, 2.35, 0.4
    y = {"init": 4.6, "evolve": 3.95, "prop": 3.3, "obs": 2.6, "weight": 1.9, "ess": 1.25, "rm": 0.62, "fc": 0.05}
    box(ax, x, y["init"], w, h, "Initialize $M$ particles: $X_0=S_0=0$,\n"
        r"$\theta_0$ from the priors (Alg. 1)")
    box(ax, x, y["evolve"], w, h, "Evolve parameters by log-random\nwalks (Eqs. (12)–(14))")
    box(ax, x, y["prop"], w, h, "Propagate state over the slice with\ncoupled rates (Eqs. (2)–(6))")
    diamond(ax, x, y["obs"], 1.9, 0.5, "Inspection $o_k$ available?")
    box(ax, x, y["weight"], w, h, r"Weight $w\propto\mathcal{N}(o_k;X+S,\sigma_v^2)$" + "\n(Eq. (10)); normalize")
    diamond(ax, x, y["ess"], 1.6, 0.46, r"ESS $<M/2$?")
    box(ax, x, y["rm"], w, h, "Systematic resampling and MH\nrejuvenation of $\\theta_k$ (Eq. (15))")
    box(ax, x, y["fc"] + 0.05, w, h, "Forecast RUL from $J$ paths (Eq. (16));\nmaintenance decision (Eq. (18))",
        fc="#e8f1e4", ec=GREEN)
    for a, b in [("init", "evolve"), ("evolve", "prop")]:
        arrow(ax, (x, y[a] - h / 2), (x, y[b] + h / 2))
    arrow(ax, (x, y["prop"] - h / 2), (x, y["obs"] + 0.25))
    arrow(ax, (x, y["obs"] - 0.25), (x, y["weight"] + h / 2))
    ax.text(x + 0.06, (y["obs"] - 0.25 + y["weight"] + h / 2) / 2, "yes", fontsize=7, va="center")
    arrow(ax, (x, y["weight"] - h / 2), (x, y["ess"] + 0.23))
    arrow(ax, (x, y["ess"] - 0.23), (x, y["rm"] + h / 2))
    ax.text(x + 0.06, (y["ess"] - 0.23 + y["rm"] + h / 2) / 2, "yes", fontsize=7, va="center")
    arrow(ax, (x, y["rm"] - h / 2), (x, y["fc"] + 0.05 + h / 2))
    # "no" at ESS: skip resampling, go to forecast
    xr = x + w / 2 + 0.12
    polyline_arrow(ax, [(x + 0.8, y["ess"]), (xr, y["ess"]), (xr, y["fc"] + 0.05), (x + w / 2, y["fc"] + 0.05)])
    ax.text(x + 0.84, y["ess"] + 0.06, "no", fontsize=7)
    # "no" at observation: next slice
    xl = x - w / 2 - 0.12
    polyline_arrow(ax, [(x - 0.95, y["obs"]), (xl, y["obs"]), (xl, y["evolve"]), (x - w / 2, y["evolve"])])
    ax.text(x - 1.12, y["obs"] + 0.06, "no", fontsize=7)
    # loop back from forecast to next slice
    xll = xl - 0.16
    polyline_arrow(ax, [(x - w / 2, y["fc"] + 0.05), (xll, y["fc"] + 0.05), (xll, y["evolve"] + 0.1),
                        (x - w / 2, y["evolve"] + 0.1)], color=RED)
    ax.text(xll - 0.04, 1.2, "next slice $k+1$", rotation=90, color=RED, fontsize=7, ha="right", va="center")
    fig.savefig(OUT / "fig3_smcflow.png", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


# ------------------------------------------------------------------ result figures
def fig4_fig5():
    from apidbn.core import DT, Physics, critical_depth
    from apidbn.filters import MODELS, ParticleFilter, forecast_failure, sample_prior
    from apidbn.truth import SCENARIOS, simulate_paths, simulate_truth

    P = Physics()
    dcrit = critical_depth(P)
    # Fig. 4: same RNG sequence as run_checks.py
    rng = np.random.default_rng(2024)
    regimes = {"low": 0.3, "moderate": 0.8, "high": 1.5}
    paths = {}
    for name, lam in regimes.items():
        paths[name] = simulate_paths(10_000, P, rng, years=20, lam=lam)
        simulate_paths(10_000, P, rng, years=40, lam=lam)  # failure-time draws of run_checks.py
    t = np.arange(paths["low"].shape[0]) * DT
    colors = {"low": GREEN, "moderate": BLUE, "high": RED}
    fig, ax = plt.subplots(figsize=(3.5, 2.45))
    for name, z in paths.items():
        lo, hi = np.quantile(z, [0.05, 0.95], axis=1)
        ax.fill_between(t, lo, hi, color=colors[name], alpha=0.15, lw=0)
        ax.plot(t, z.mean(axis=1), color=colors[name], lw=1.0, ls=":")
        ax.plot(t, z[:, 0], color=colors[name], lw=0.9,
                label=rf"$\lambda={regimes[name]}$ yr$^{{-1}}$ ({name})")
    ax.axhline(dcrit, color=INK, ls="--", lw=0.8)
    ax.text(0.3, dcrit + 0.45, f"Eq. (9) failure depth, {dcrit:.1f} mm", fontsize=7)
    ax.set(xlim=(0, 20), ylim=(0, 28), xlabel="Time (years)", ylabel=r"Equivalent damage $Z(t)$ (mm)")
    ax.legend(loc="upper left", frameon=False, handlelength=1.6)
    fig.savefig(OUT / "fig4_trajectories.png", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)

    # Fig. 5: same seeds as run_checks.py
    grid = np.arange(0, 40.01, 0.1)
    rel = {}
    for s in ("A", "B"):
        tr = simulate_truth(10_000, SCENARIOS[s], P, dcrit, np.random.default_rng([7, ord(s)]))
        rel[s] = np.array([np.mean(tr["fail"] > g) for g in grid])
    rng = np.random.default_rng(11)
    n = 10_000
    ft_s = forecast_failure(np.zeros(n), np.zeros(n), np.repeat(np.log(P.theta_nominal)[:, None], n, axis=1),
                            P, dcrit, rng, True, None, 60)
    ft_a = forecast_failure(np.zeros(n), np.zeros(n), np.log(sample_prior(n, rng)), P, dcrit, rng, True,
                            np.full((3, 1), 0.05), 60)
    prior_rel = {k: np.array([np.mean(v > g) for g in grid]) for k, v in {"s": ft_s, "a": ft_a}.items()}
    scen = SCENARIOS["B"]
    tr = simulate_truth(200, scen, P, dcrit, np.random.default_rng(12))
    i = int(np.argmin(np.abs(tr["fail"] - np.quantile(tr["fail"], 0.2))))
    cond = {}
    for name in ("SDBN", "API", "ORACLE"):
        r = np.random.default_rng(13)
        kw = {"theta_path": tr["theta_year"][:, :, i]} if name == "ORACLE" else {"theta": P.theta_nominal}
        pf = ParticleFilter(MODELS[name], P, dcrit, r, **kw)
        for k, tk in enumerate(tr["insp_times"][:6]):
            pf.propagate(tk)
            pf.update(tr["obs"][i, k])
        drift = np.full((3, 1), scen.drift_sd) if name == "ORACLE" else None
        ft = 6.0 + pf.predict_rul(10_000, r, drift=drift)
        cond[name] = np.array([np.mean(ft > g) for g in grid])
    fig, axes = plt.subplots(2, 1, figsize=(3.5, 4.3), sharex=True)
    ax = axes[0]
    ax.plot(grid, rel["A"], color=INK, lw=1.3, label="True (Table IV)")
    ax.plot(grid, rel["B"], color="0.55", lw=1.3, label="True (heterogeneous)")
    ax.plot(grid, prior_rel["s"], color=BLUE, ls="--", lw=1.0, label="Static DBN prior")
    ax.plot(grid, prior_rel["a"], color=RED, ls="--", lw=1.0, label="API-DBN prior")
    ax.set_title("(a) Population reliability")
    ax = axes[1]
    for name, lab, col in (("ORACLE", "Oracle (true parameters)", INK), ("API", "API-DBN", RED),
                           ("SDBN", "Static DBN", BLUE)):
        ax.plot(grid, cond[name], color=col, lw=1.2, label=lab)
    ax.axvline(tr["fail"][i], color=INK, ls=":", lw=0.9)
    ax.text(tr["fail"][i] - 0.3, 0.3, "true\nfailure", fontsize=7, ha="right")
    ax.set_title("(b) One pipeline after inspections at years 1–6")
    for ax in axes:
        ax.set(xlim=(0, 30), ylim=(0, 1.03), ylabel=r"Reliability $R(t)$")
        ax.legend(loc="upper right", frameon=False)
    axes[1].set_xlabel("Time (years)")
    fig.tight_layout(h_pad=0.8)
    fig.savefig(OUT / "fig5_reliability.png", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    return {"fig5_example_true_failure": float(tr["fail"][i])}


def fig6():
    sys.path.insert(0, str(ROOT / "experiments"))
    from extend_gamma import G_FULL, I_GRID, MODELS_M, merged

    names = {"SDBN": "Static DBN", "API": "API-DBN", "ORACLE": "Oracle (true parameters)"}
    means = {m: merged("B", m)[..., 0].mean(axis=2) for m in MODELS_M}
    vmin = min(v.min() for v in means.values())
    fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.35), sharey=True)
    for ax, m in zip(axes, MODELS_M):
        mean = means[m]
        a, b = np.unravel_index(np.argmin(mean), mean.shape)
        im = ax.imshow(mean.T, origin="lower", aspect="auto", cmap="viridis", vmin=vmin, vmax=3 * vmin,
                       extent=[I_GRID[0] - 0.25, I_GRID[-1] + 0.25, G_FULL[0] - 0.25, G_FULL[-1] + 0.25])
        ax.plot(I_GRID[a], G_FULL[b], marker="*", color="red", ms=10, mec="white", mew=0.6)
        ax.plot(2.0, 1.5, marker="x", color="white", ms=6, mew=1.5)
        ax.set_title(f"{names[m]}\nminimum {mean[a, b]:.0f} k\\$ at $I$ = {I_GRID[a]:.1f}, "
                     f"$\\gamma$ = {G_FULL[b]:.1f} yr", fontsize=7.5)
        ax.set_xlabel("Inspection interval $I$ (yr)")
    axes[0].set_ylabel(r"Threshold $\gamma$ (yr)")
    cb = fig.colorbar(im, ax=axes, shrink=0.95, pad=0.012)
    cb.set_label("Expected discounted cost (k\\$)\n(scale capped at 3× minimum)")
    fig.savefig(OUT / "fig6_cost.png", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


if __name__ == "__main__":
    fig1_workflow()
    fig2_dbn()
    fig3_flow()
    if "--fig6" in sys.argv:
        fig6()
    else:
        print(fig4_fig5())
    print("figures in", OUT)
