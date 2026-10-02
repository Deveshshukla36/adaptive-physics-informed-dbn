# Changes to the API-DBN manuscript

This list comes from three things:
1. An independent replica of the paper's method and experiments, built from the manuscript text alone. It lives in this folder; see `README.md`.
2. Direct calculation of every number that can be checked by hand.
3. A check of the reference list against Crossref, DataCite and publisher records.

The earlier chat's items are included where they still apply. All numbers below are final: 30 matched runs, 9,990 test pipelines and 121,091 RUL forecasts per model, plus 1,500 pipelines for the maintenance study.

**Update:** the maintenance study (Sec. 3.3) was rerun with the replacement threshold γ searched up to 5 yr instead of 3 yr, and the maintenance numbers below come from that run. Every change in this list has been applied to the manuscript in `../Revised_Paper/`.

---

## 1. The short version, in priority order

1. **Five references could not be found** ([7], [8], [9], [11], [19]). For two of them the cited article number belongs to a different paper, and [8] is also the stated source of a Table IV parameter. Replace them (Sec. 7).
2. **Table VI, Table VII and the headline numbers cannot be reproduced.** A faithful implementation gives an **18.6%** MAE reduction over the static DBN, not 65.7%. It also gives a **28.7%** CRPS reduction, and **95.3%** interval coverage against **59.9%** for the static DBN. MCMC rejuvenation has **no measurable effect**, and removing the coupling **doubles** the error (Sec. 3).
3. **The simulation design as written makes the main claim impossible.** If every trajectory uses the Table IV parameters (Sec. IV-B, literally), the static DBN *is* the true model: it ties the oracle (MAE 0.48 yr) and beats API-DBN (0.93 yr). Describe pipeline-to-pipeline variation and drift, as in scenario B (Sec. 2, 3.2).
4. **The maintenance result is not reproducible, and the reported optimum is a poor policy.** At I = 2, γ = 1.5, 13–21% of pipelines fail. The API-DBN's real advantage is **17%** ($425k → $353k). Its best policy, I = 4.0, γ = 5.0, lies on the edge of the searched grid (Sec. 3.3).
5. **Figs. 4–6 cannot come from the stated model and parameters, and Fig. 2 contains a directed cycle.** Replacement figures are in `figures/` (Sec. 5).
6. **Technical corrections:** failure depth (12.1 mm, not 11 mm), the sigmoid at zero damage, the shock-damage labels, the DNV formula and algorithm details (Sec. 4).
7. **Novelty:** Sun et al. [18] already model two-way degradation–shock dependence. Reword Gap 2, Contribution 1 and Table I (Sec. 6).
8. **The held-out BSEE case study (Sec. V-C) reports no result.** Add one or remove the claim from the abstract, contributions and conclusion.

---

## 2. What was run

- **Ground truth.** Eqs. (1)–(9) with every Table IV value, Δt = 0.1 yr (K = 200 → 20 yr), and failure when Z ≥ 12.07 mm.
- **Two readings of "generated using the model parameters in Table IV":**
  - **Scenario A (literal):** every pipeline has exactly the Table IV parameters, which never change.
  - **Scenario B (what the paper's motivation needs):** each pipeline gets (µ⁽⁰⁾, λ⁽⁰⁾, σ_B) = Table IV × exp(N(0, 0.25²)), and these drift yearly by the log-random walks of Eqs. (12)–(14) with the Table IV s.d. of 0.05.
- **Models.** The five of Sec. IV-B, plus "no coupling w/o MCMC" (to make Table VII a real 2 × 2) and an oracle that knows the true parameters (the error floor). The static DBN, PF w/o MCMC, no-coupling model and API-DBN share one particle-filter code (Algorithm 1), so each differs only in the ablated component.
- **Protocol.** 30 matched runs (seeds 0–29). Scenario B: 333 pipelines per run (9,990 in total). Scenario A: 100 per run. Annual inspections with σ_v = 0.1 mm. At every inspection before failure: filter update, then an RUL forecast from J = 10,000 paths with M = 1,000 particles. Point prediction = predictive median. Brier window = 2 yr.
- **Maintenance.** Each model *operates* 1,500 simulated pipelines for 20 years. It inspects every I years, replaces when its 10th-percentile RUL ≤ γ, and pays Table V costs for what actually happens to the true pipeline. The grid is I ∈ {1, 1.5, …, 4}, γ ∈ {0.5, 1, …, 3}. Every model faces the same pipelines, shocks and inspection errors.
- **Tests.** 10 unit tests pass, including an exact check of the MCMC move against a grid-computed posterior. Results are deterministic: recomputing a task reproduces its file bit for bit.

Every assumption made where the paper is silent is listed in `README.md`, each with the one constant that controls it.

---

## 3. Results that replace the manuscript's numbers

### 3.1 Table VI (scenario B; mean ± s.d. over 30 runs)

| Model | Paper MAE | **Replica MAE (yr)** | RMSE (yr) | CRPS (yr) | Brier | PICP |
|---|---|---|---|---|---|---|
| Fixed Wiener | 3.12 | 1.37 ± 0.08 | 1.96 ± 0.14 | 1.04 ± 0.07 | 0.031 ± 0.002 | 75.0% |
| Static DBN | 2.45 | 1.38 ± 0.09 | 2.05 ± 0.16 | 1.12 ± 0.08 | 0.032 ± 0.002 | 59.9% |
| PF w/o MCMC | 1.67 | 1.12 ± 0.04 | 1.73 ± 0.08 | 0.80 ± 0.03 | 0.022 ± 0.001 | 95.2% |
| No coupling | 1.23 | 2.29 ± 0.07 | 3.39 ± 0.10 | 1.67 ± 0.05 | 0.027 ± 0.001 | 77.5% |
| **API-DBN** | **0.84** | **1.12 ± 0.04** | **1.72 ± 0.08** | **0.80 ± 0.03** | **0.021 ± 0.001** | **95.3%** |
| No coupling, w/o MCMC | – | 2.29 ± 0.06 | 3.38 ± 0.10 | 1.67 ± 0.05 | 0.027 ± 0.002 | 77.3% |
| Oracle (true parameters) | – | 0.70 ± 0.03 | 1.04 ± 0.06 | 0.50 ± 0.02 | 0.018 ± 0.001 | 95.4% |

Paired t-tests against API-DBN (df = 29):

| Comparison | ΔMAE (yr) | t | p |
|---|---|---|---|
| Static DBN | +0.26 | 17.7 | 5 × 10⁻¹⁷ |
| Fixed Wiener | +0.25 | 17.8 | 4 × 10⁻¹⁷ |
| PF w/o MCMC | 0.00 | −0.1 | 0.96 |
| No coupling | +1.17 | 90.5 | 4 × 10⁻³⁷ |

For the static DBN, CRPS gives t = 23.6 and Brier t = 29.7.

What changes in the story:
- **API-DBN vs static DBN:** MAE −18.6% and CRPS −28.7%. The gain is real and highly significant, but the main benefit is **calibration**. API-DBN's 95% intervals cover the true RUL in 95.3% of 121,091 forecasts (Wilson 95% CI 95.2–95.4%), with average width 6.1 yr. The static DBN's intervals are only 2.4 yr wide and cover 59.9%: it cannot learn pipeline-specific rates, so it is overconfident.
- **MCMC rejuvenation has no measurable effect** (ΔMAE < 0.001 yr, p = 0.96, in both scenarios). With the state held fixed, the MH move of Eq. (15) can only refresh θ_k within the random-walk spread around θ_{k−1}, which the random walk of Eqs. (12)–(14) already provides. Either report this, or use a move that targets the parameter posterior given the whole history (resample-move, Gilks & Berzuini 2001) and show that it helps. Do not keep MCMC as a headline contribution without that evidence.
- **No coupling is the worst adaptive model (2.29 yr), not the second best.** Its baseline drift has to absorb an acceleration it cannot anticipate, so it overestimates RUL by 2.1 yr on average. This strongly supports keeping the coupling. Reword Sec. V-E ("The no-coupling configuration performs better than the static approaches" is false in the replica).
- **Fixed Wiener ≈ static DBN.** An offline-calibrated linear Wiener model is a strong baseline, and it is not 2.3× worse than API-DBN. If your Fixed Wiener used µ = 0.44 mm/yr without shocks or acceleration, it is a straw man. State how its parameters were set.
- **The oracle's MAE of 0.70 yr is the floor.** API-DBN closes 38% of the gap between the static DBN and the oracle. Its posterior error in µ falls from 21% (year 1) to 12.5% (year 10) and then stops improving, because the random walk forgets old evidence.

Replacement LaTeX tables are generated from the result files by `experiments/make_latex.py` into `results/latex_tables.tex`.

### 3.2 Scenario A (literal reading): adaptation cannot win

| Model | MAE (yr) | CRPS (yr) | PICP |
|---|---|---|---|
| Fixed Wiener | 0.58 ± 0.03 | 0.41 ± 0.02 | 92.7% |
| **Static DBN** | **0.48 ± 0.03** | **0.34 ± 0.02** | 95.6% |
| PF w/o MCMC | 0.93 ± 0.04 | 0.66 ± 0.03 | 97.5% |
| No coupling | 2.13 ± 0.11 | 1.52 ± 0.08 | 83.5% |
| API-DBN | 0.93 ± 0.04 | 0.66 ± 0.03 | 97.6% |
| Oracle (true parameters) | 0.48 ± 0.03 | 0.34 ± 0.02 | 95.6% |

(30 runs, 3,000 pipelines, 36,090 forecasts per model.) When every pipeline has the Table IV parameters, the static DBN *is* the oracle. API-DBN is worse by 0.44 yr (t₂₉ = −56.0, p = 4 × 10⁻³¹), because it has to learn parameters that are already known. **Adaptation pays off only when parameters differ between pipelines or drift.** The paper must say so, and must describe a design like scenario B. Reporting both scenarios is actually a strength: it shows *when* the method helps.

### 3.3 Maintenance (Sec. V-B; scenario B, 1,500 pipelines)

Policy grid: I = 1, 1.5, …, 4 yr and γ = 0.5, 1, …, 5 yr.

| Decision model | Best policy | Expected cost | Pipelines failing | At the paper's policy (I = 2, γ = 1.5) |
|---|---|---|---|---|
| Static DBN | I = 2.5, γ = 4.5 | $425k ± 4k | 0.07% | $2,324k, 20.5% fail |
| **API-DBN** | **I = 4.0, γ = 5.0** | **$353k ± 5k** | **0.07%** | $1,449k, 12.8% fail |
| Oracle | I = 4.0, γ = 4.5 | $342k ± 11k | 0.27% | $1,457k, 13.2% fail |

- **The API-DBN policy is 16.8% cheaper than the static-DBN policy,** about half your 34.4%, and 3.3% more expensive than the oracle's. It is also at a different policy and cost level: $315.4k is below even the oracle's cost.
- **The reported optimum, γ* = 1.5 < I* = 2.0, is a bad policy.** A pipeline whose 10th-percentile RUL falls between 1.5 and 2 years is left alone until the next inspection, and with C_fail + C_env = $15M those failures dominate the cost (`figures/fig6_replica_B_full.png`: everything below the diagonal γ < I is expensive).
- **The optimum depends on the search range.** On the first grid (γ ≤ 3 yr), every model's best γ was 3.0, the top of the range, and the advantage looked like 31% ($573k → $394k). With γ up to 5 yr (`experiments/extend_gamma.py`), all three costs fall and the advantage shrinks to 17%. The API-DBN and oracle optima still lie at the longest interval searched (I = 4 yr), and the API-DBN optimum also lies at γ = 5 yr. The paper must say that these minima lie on the boundary of the searched domain.
- **The horizon must be stated.** Inspection cost alone at I = 2 over 20 years is $304k, and every pipeline needs at least one replacement in that time (lifetime ≈ 12.5 yr). A total of $315.4k is therefore only possible with a much shorter horizon. State the horizon and when inspections start.
- **Score costs against the simulated truth (closed loop), as here.** Averaging costs over the model's *own* forecasts rewards models that forecast longer lives.
- **Scenario A (500 pipelines) confirms the pattern.** When every pipeline has the Table IV parameters, the static DBN (= oracle) gives the cheapest policy, $349k at I = 2.5, γ = 3.0. The API-DBN costs 4.0% more ($363k). Even here, the paper's policy lets 8–11% of pipelines fail ($1.08–1.27M). This scenario was run on the first grid (γ ≤ 3 yr) only.

### 3.4 Other numbers

- **PICP:** report 95.3% with N = 121,091 and the Wilson interval [95.2, 95.4]. 94.8% cannot be reached with N = 30 (the nearest possible values are 93.3% and 96.7%).
- **p < 0.01:** replace it with the exact values, for example "paired t₂₉ = 17.7, p < 10⁻¹⁶".
- **Runtime (V-D):** filtering 200 steps with M = 1,000 takes 0.05–0.07 s per pipeline in the replica, and a full evaluation including about 12 RUL forecasts with J = 10,000 takes about 1 s (Apple M4, one core per pipeline, vectorized NumPy). Your 3.2 s is plausible for less vectorized code, but name the CPU and say whether RUL forecasting is included.

---

## 4. Technical corrections

**T1. Failure depth is 12.1 mm, not 11 mm.** P₀ = 2t·SMYS/(D − t) = 23.14 MPa, M = 4.262, and Eq. (9) holds at d = 12.07 mm (63% of the wall). Change the Fig. 4 caption, the sentence "Pipeline B remains below the 11 mm reference level", and the plotted line.

**T2. Eqs. (7)–(8) are not DNV-RP-F101.** DNV-RP-F101 uses the tensile strength (SMTS) and Q = √(1 + 0.31(L/√(Dt))²). The printed form (0.8, SMYS) is closer to the ASME B31G Folias factor. Recommended: keep the equations and write "a simplified DNV-RP-F101/B31G-type burst-pressure model". Adopting DNV's own form would move d_crit to 12.86 mm (0.31, SMYS) or 14.37 mm (0.31, SMTS = 455 MPa) and change every result.

**T3. Eq. (5) is not at the baseline at zero damage.** The factor at Z = 0 is 1 + 1/(1 + e^{0.5}) = 1.378, so the drift never falls below 0.606 mm/yr, and the 10–90% transition spans 2 ln 9 / r_s = 8.8 mm. Text-only fix (all results unchanged):

```latex
where $W_0$ is the midpoint of the sigmoid transition, $\alpha$ the asymptotic
acceleration factor and $r_s$ (mm$^{-1}$) its steepness. At zero damage the
factor equals $1+(\alpha-1)/(1+e^{r_sW_0})=1.38$ for the values in
Table~\ref{tab:simparams}, so $\mu^{(0)}_k$ is a baseline parameter rather than
the initial effective drift; the transition spans about $2\ln 9/r_s=8.8$~mm
between 10\% and 90\% of the full acceleration.
```

Rename r in Eq. (5) to r_s, because r is also the discount rate in Eq. (17) and Table V. Delete "gradual transition from the baseline" and "coating-breakdown threshold" or reword them to match.

**T4. Shock labels in Table IV.** µ_y0 and σ_y0 describe the shock *magnitude* Y. Through Eq. (4), the equivalent damage per shock is E[κY^η] = 0.166 mm, not 0.32 mm. Relabel both rows, and add:

```latex
$Y_i\sim\mathcal{N}(\mu_{y_0},\sigma_{y_0}^2)$ truncated at zero, so that
$\mathbb{E}[\Delta S_i]=\kappa\,\mathbb{E}[Y_i^{\eta}]\approx0.17$~mm.
```

If your code uses ΔS = Y instead, the median life drops from 12.5 to 10.9 yr. The text must match the code.

**T5. The failure clause is redundant.** "Or when the equivalent damage from a single shock exceeds the residual capacity" adds nothing: P_burst decreases in d, so failure ⟺ Z ≥ d_crit. Delete it or define "residual capacity".

**T6. λ = 0.8 yr⁻¹ does not follow from Table III.** Table III gives 934 incidents over 36 years for 1,247 segments, which is at most 0.02 incidents per segment-year, 40 times lower than λ. Explain how reported incidents map to "shocks", or label λ an assumption. *Update:* computed from the NETL files themselves (`experiments/bsee_records.py`), the records hold 943 incidents, not 934. Over the exposure of the installed BSEE segments, that is at most 0.0051 incidents per segment-year, about 160 times lower than λ. The revised paper labels λ an assumption and gives this check in Sec. IV-A.

**T7. Table IV provenance claims need evidence.** The replica supplies the missing analyses (`results/sensitivity.json`):
- **W₀, "verified by sensitivity analysis":** median life is 12.3–12.9 yr for W₀ = 0.25–2 mm, and 14.0 / 16.4 yr at 4 / 8 mm. Life is insensitive to W₀ below about 2 mm.
- **r_s:** negligible effect (12.2–13.0 yr for r_s = 0.25–5 mm⁻¹).
- **α, "calibrated (SMC posterior mean)":** it dominates the lifetime (α = 1 / 2 / 3 → 19.9 / 12.5 / 9.2 yr). Describe the calibration data and procedure, or label it an assumption. The same applies to γ₁, γ₂ and σ_B.
- **M, "convergence tuning":** API-DBN accuracy is flat from 250 to 2,000 particles (MAE 1.01–1.04 yr, PICP 96%).
- **J, "Monte Carlo convergence":** at J = 10,000 the Monte Carlo s.d. of the 2.5% and 97.5% RUL quantiles is 0.02 and 0.06 yr, against 0.07 and 0.15 yr at J = 1,000.
- σ_σ of Eq. (14) is missing from Table IV.

**T8. Algorithm 1 / Eq. (15) need to be stated precisely.**
- λ₀ ~ Γ(2, 0.2, 5) is ambiguous. State shape, scale or rate, and truncation (the replica used shape 2, scale 0.4, truncated to [0.2, 5]).
- Eq. (5) uses Z_{k−1} for µ_eff_k, while line 3 of Algorithm 1 propagates x_k with µ_eff_{k−1}, which is a double lag. Pick one convention.
- In Eq. (15), p(o_k | s_k, θ) cancels when the state is fixed, and p(θ) must be the random-walk density:

```latex
With the state path held fixed, the move targets
$p(\theta_k\mid\theta_{k-1},s_{k-1},s_k)\propto
p(s_k\mid s_{k-1},\theta_k)\,p(\theta_k\mid\theta_{k-1})$; the observation
likelihood does not depend on $\theta_k$ and cancels. Gaussian corrosion
increments and Poisson shock counts make $p(s_k\mid s_{k-1},\theta_k)$
available in closed form. Proposals are Gaussian random walks on
$\log\theta_k$ with the standard deviations of Eqs.~(12)--(14), and five
Metropolis--Hastings sweeps follow each resampling step.
```

- Give units: σ_B in mm/√yr, r_s in mm⁻¹.

**T9. Add the missing experimental details to Sec. IV-B.** Whether you adopt the replica's protocol or rerun your own code, Sec. IV-B must state:
- how true parameters vary between pipelines and over time;
- Δt and the horizon;
- the inspection schedule;
- when RUL is scored;
- N (pipelines and forecasts);
- the point estimator;
- the Brier window;
- how the Fixed Wiener and static DBN parameters were set.

Replica wording you can adapt:

```latex
\textit{Ground truth.} Each simulated pipeline receives its own baseline
parameters $(\mu^{(0)},\lambda^{(0)},\sigma_B)$, equal to the Table~IV values
multiplied by independent $\exp(\varepsilon)$, $\varepsilon\sim\mathcal{N}(0,0.25^2)$,
which then drift annually by the log-random walks of Eqs.~(12)--(14) with the
standard deviations in Table~IV. Degradation is simulated with
$\Delta t=0.1$~yr ($K=200$ steps over a 20-yr monitoring window) until
$Z\ge d_{\mathrm{crit}}=12.07$~mm, the depth at which Eq.~(9) holds.
Each pipeline is inspected annually from $t=1$~yr through Eq.~(10). At every
inspection before failure, each model forecasts the RUL from $J=10{,}000$
trajectories, and the median is the point prediction. We use 30 runs
(seeds 0--29) of 333 pipelines each; within a run, all models see the same
pipelines and inspections. A second design, in which every pipeline has
exactly the Table~IV parameters, is reported for comparison.

\textit{Baselines.} The fixed-Wiener model is a linear Wiener process on $Z$
whose drift and diffusion are fitted by moments to the inspection increments
of 2{,}000 separately simulated training pipelines; it takes the latest
observation as the current state and gives an inverse-Gaussian RUL. The static
DBN is the proposed model and filter with the parameters fixed at the Table~IV
values. The no-coupling model sets $\alpha=1$ and $\gamma_1=0$. An oracle that
knows each pipeline's true parameters is included as a lower bound on error.
```

---

## 5. Figures

| Fig. | Problem | Fix |
|---|---|---|
| 1 | "BSIE" → "BSEE"; "(Sec. V-A)" → "(Sec. III-B)"; the feedback arrow has heads at both (4) and (7). | Draw it from an "inspection o_k" input into (4) only. |
| 2 | The red dashed arrow Z_{k+1} → λ⁽⁰⁾_{k+1} makes the cycle λ⁽⁰⁾ → S → Z → λ⁽⁰⁾ **inside one slice**, contradicting the caption. The dashed arrows point into the *baseline* parameters, but Eqs. (5)–(6) change only the *effective* rates. The arrow µ⁽⁰⁾_k → λ⁽⁰⁾_k contradicts "no coupling among innovations". σ_B is missing, and the labels "n₂,(0)" and "n₃,(T)" are unexplained. | Redraw: θ_{k−1} → θ_k; θ_k → X_{k+1}, S_{k+1}; Z_k → X_{k+1} (Eq. 5); X_k → S_{k+1} (Eq. 6); X_k, S_k → Z_k → O_k, F_k. |
| 3 | "ISS" → "ESS" (twice). The parameter-evolution step is missing, although the caption lists it, and there is no loop back for k + 1. | Add both. |
| 4 | Impossible under Table IV. Corrosion alone gives Z(20) = 16.4 ± 1.0 mm (the drift is ≥ 0.606 mm/yr), yet the low-shock curve ends at 7.5 mm, about 9 s.d. below. With Table IV, mean Z(20) = 18.0 / 20.6 / 24.4 mm for λ = 0.3 / 0.8 / 1.5, and every pipeline fails by 16 yr. The curves are smooth (no Wiener noise or shock jumps) and concave at first, but the model's drift grows with damage. The legend's dashed style for Pipeline C does not match its solid curve, and the line drawn at about 10.8 mm is labelled 11 mm. | Use `figures/fig4_replica.png` or regenerate from your code with Table IV. |
| 5 | R(0) ≈ 0.975 but must be 1. The legend says "Base model" but the caption says static DBN. Under Table IV the true R(t) is 0.998 at 10 yr and 0.007 at 15 yr (median life 12.5 yr, 5–95%: 11.0–14.2), not a slow decay to 25–30 yr. A higher *predicted* reliability is not a merit. | Use `figures/fig5_replica.png`: true vs model reliability, and one pipeline's conditional reliability. |
| 6 | One panel carries both "(a) RUL distribution" and "(b) Cost heatmap (Z$)". The y-axis is "Threshold τ (mm)" although γ is in years, the colour bar says "Count (×10³)" instead of cost, the x-axis says Δ where the text uses I, and the surface is too smooth for Monte Carlo output. | Use `figures/fig6_replica_B.png` (closed-loop costs for each model). |

Suggested captions:

```latex
% Fig. 4
\caption{Equivalent damage simulated with the Table~\ref{tab:simparams}
parameters for shock rates $\lambda=0.3$, $0.8$ and $1.5$~yr$^{-1}$: one path
(solid), the mean (dotted) and the 5--95\% band of 10{,}000 paths (shaded).
The dashed line is the depth at which Eq.~\eqref{eq:burstfail} holds (12.1~mm);
median times to failure are 14.0, 12.5 and 11.0~yr.}

% Fig. 5
\caption{(a) Reliability of the simulated population with the Table~IV
parameters (scenario A) and with pipeline-to-pipeline variation (scenario B),
and the reliability implied by the static DBN and by the API-DBN prior before
any inspection. (b) Conditional reliability of one scenario-B pipeline after
inspections at years 1--6; the dotted line marks its true failure time.}

% Fig. 6
\caption{Expected discounted lifecycle cost (k\$) when each model makes the
inspection and replacement decisions for the same 1{,}500 simulated pipelines,
over inspection interval $I$ and threshold $\gamma$ on the 10th-percentile RUL.
Stars mark the minima; policies with $\gamma<I$ allow failures between
inspections.}
```

---

## 6. Novelty wording (from the earlier chat; the key claim is now verified)

The abstract of Sun et al. [18] confirms that they model how random shocks affect degradation increments and rates, and also how degradation affects the shocks. That is two-way dependence. So:
- **Sec. II-A:** replace "For subsea pipelines, however…", the red flag, and "This limitation motivates…" with the earlier chat's paragraph. It says the study does *not* claim to introduce two-way dependence; its distinguishing elements are the specific parametric forms (sigmoid drift acceleration; exponential shock-intensity dependence) embedded in a sequentially updated DBN.
- **Gap 2:** retitle it "Limited integration of dependent corrosion–shock evolution within adaptive inference".
- **Contribution 1:** lead with "a continuous parametric corrosion–shock coupling (sigmoid drift acceleration; exponential shock-intensity dependence)".
- **Contribution 2:** drop "MCMC" as a source of accuracy unless you add the evidence described in Sec. 3.1.
- **Table I, Sun row:** Nonlinear Wiener | Random shocks | Two-way, copula-based. **API-DBN row:** "Two-way; continuous parametric (sigmoid / exponential)".
- Delete the Table I row for Melchers [7] (reference not found).
- The Table I cells for Wang [1] and Peng [2] still need you to read those papers.

---

## 7. References

Checked on 2026-09-24 against Crossref, DataCite and publisher records.

**Could not be found. Replace or delete before submission:**

| Ref | As cited | What the record shows | Used for | Action |
|---|---|---|---|---|
| [7] | Melchers, Corros. Sci. 163, 108215, 2020 | Article 108215 of Corrosion Science is Liu et al., "Pseudoalteromonas lipolytica accelerated corrosion of low alloy steel…" (vol. 162). No such Melchers paper found. | Sec. I (external hazards); Table I row | Delete the Table I row; cite a verified source for dropped objects / anchors / trawling (e.g. DNV-RP-F107, after checking the edition). |
| [8] | Wang & Soares, RESS 191, 106554, 2019 | RESS 191, 106554 is Raoni & Secchi, "Procedures to model and solve probabilistic dynamic system problems". | 5 citations, including **Table IV's source for µ_base = 0.44** | Use Z. Zhang, X. Si, C. Hu, Y. Lei, EJOR 271(3):775–796, 2018, doi:10.1016/j.ejor.2018.02.033 for Wiener modelling. Give the true source of 0.44 mm/yr or call it an assumption. |
| [9] | Shen et al., Mar. Struct. 84, 201–218, 2022 | Not found (Marine Structures uses article numbers, not pages) | Sec. I (MIC, fatigue) | Cite [10] (verified) alone. |
| [11] | Sanz-Bobi, Springer Reliab. Eng. Ser. 44(3), 2018 | Not found; also not cited in the text | – | Delete. |
| [19] | Chiquet et al., Technometrics 64(2):189–201, 2022 | Not found; J. Chiquet has no such paper | Eqs. (12)–(14) | Use N. Kantas, A. Doucet, S. S. Singh, J. Maciejowski, N. Chopin, "On particle methods for parameter estimation in state-space models," Statist. Sci. 30(3), 2015, doi:10.1214/14-STS511. |

**Exist, but details are wrong:**
- **[6]** Add the missing author: B. Cai, Y. Zhang, X. Yuan, C. Gao, Y. Liu, G. Chen, **Z. Liu**, R. Ji (doi:10.1007/s13344-020-0054-0).
- **[12]** Authors are B. Cai, **X. Shao**, **Y. Liu**, X. Kong, H. Wang, **H. Xu**, W. Ge (doi:10.1109/TIE.2019.2931491).
- **[20]** The DOI is L. Romeo *et al.*, "U.S. Offshore Pipeline and Reported Incident Datasets," NETL, 2024, doi:10.18141/2280823. It is an NETL dataset built from BSEE records. Adjust the acknowledgment.
- **[14]** Not cited in the text. Delete.
- **[17]** For MCMC rejuvenation after resampling, cite W. R. Gilks, C. Berzuini, "Following a moving target—Monte Carlo inference for dynamic Bayesian models," JRSS-B 63(1):127–146, 2001 (doi:10.1111/1467-9868.00280). Andrieu et al. is particle MCMC, a different method.

**Verified as cited:** [5], [10], [13], [15], [18]. **Standard and well known, not individually checked:** [1]–[4], [16], [21], [22].

---

## 8. Replacement text for the results

**Abstract** (replace the two sentences starting "Quantitative evaluation…" and "The resulting maintenance policy…"; delete the held-out case-study clause unless you add its result):

```latex
In controlled simulations of 9{,}990 pipelines whose degradation parameters
differ between pipelines and drift over time, API-DBN reduces the RUL mean
absolute error by 19\% and the continuous ranked probability score by 29\%
relative to a static-parameter DBN, and its 95\% prediction intervals contain
the true RUL in 95.3\% of forecasts, against 59.9\% for the static DBN. When
each model makes the inspection and replacement decisions for the same
simulated pipelines, the API-DBN-based policy lowers the expected
discounted lifecycle cost by 17\% relative to the static-DBN-based
policy.
```

**Sec. V-A**, first paragraphs:

```latex
Table~\ref{tab:rul} summarizes RUL prediction over the 30 matched runs
(9{,}990 pipelines; 121{,}091 forecasts per model). API-DBN attains an MAE of
$1.12\pm0.04$~yr against $1.38\pm0.09$~yr for the static DBN, a 19\%
reduction (paired $t_{29}=17.7$, $p<10^{-16}$), and reduces the CRPS by 29\%.
The larger difference is in calibration: its 95\% prediction intervals contain
the true RUL in 95.3\% of forecasts (Wilson 95\% CI 95.2--95.4\%), whereas the
static DBN, which cannot learn pipeline-specific rates, covers only 59.9\%.
An oracle that knows each pipeline's true parameters reaches 0.70~yr, which
bounds what any model can achieve; API-DBN closes 38\% of the gap between the
static DBN and this bound.

Removing the corrosion--shock coupling doubles the MAE (2.29~yr): the adaptive
drift then has to absorb an acceleration it cannot anticipate, and the RUL is
overestimated by 2.1~yr on average. MCMC rejuvenation, in contrast, has no
measurable effect with or without coupling (Table~\ref{tab:ablation};
$p=0.96$). With the state held fixed, the move of Eq.~(15) only refreshes
$\theta_k$ within the random-walk spread around $\theta_{k-1}$, which the random
walk of Eqs.~(12)--(14) already provides.

When all pipelines share the Table~IV parameters, the static DBN coincides with
the oracle and outperforms API-DBN (MAE 0.48 versus 0.93~yr), because the
adaptive model must learn parameters that are already known. Sequential
parameter updating therefore pays off when parameters differ between assets
or drift over time, which is the situation it is designed for.
```

**Sec. V-B:**

```latex
Each model operated the same 1{,}500 simulated pipelines over a 20-yr horizon:
inspection every $I$ years, preventive replacement when the 10th percentile of
its RUL forecast was at most $\gamma$, and corrective replacement at failure,
with the costs of Table~V discounted at 5\%. With the static DBN, the expected
cost is minimized at $I=2.5$~yr and $\gamma=4.5$~yr (\$425k $\pm$ 4k; 0.07\% of
pipelines fail); with API-DBN at $I=4.0$~yr and $\gamma=5.0$~yr (\$353k $\pm$ 5k;
0.07\% fail), 17\% lower and 3\% above a policy based on the true
parameters (\$342k). The API-DBN and oracle minima lie at the longest
inspection interval searched ($I=4$~yr), so policies beyond the searched
domain could lower these costs further. Policies with $\gamma<I$ leave degraded pipelines
unprotected until the next inspection: at $I=2$~yr and $\gamma=1.5$~yr,
13--21\% of pipelines fail and the cost rises to \$1.4--2.3M.
```

These numbers come from the extended grid (γ ≤ 5 yr; see Sec. 3.3). The revised manuscript contains this paragraph with Table `tab:maint` and the new Fig. 6.

**Sec. V-E:** replace "The no-coupling configuration performs better than the static approaches but remains less accurate than the complete API-DBN" with the coupling sentence above. Replace "The progressive reduction in prediction error from the fixed Wiener and static-DBN configurations to the sequentially updated models is consistent with this interpretation" with the scenario-A/B contrast.

**Conclusion:** mirror the abstract; remove "reduces RUL MAE by 65.7%", "94.8%", "$315.4k" and "34.4%".

---

## 9. What the replica cannot settle (needs you)

1. **Your own code.** If it differs from the manuscript text, the text must describe the code. If your code reproduces Table VI under a protocol you can state, report that protocol. The replica shows the current numbers do not follow from the text as written.
2. **The BSEE held-out case study.** It needs the data and an actual metric.
3. **The source of µ_base = 0.44 mm/yr, and how α, γ₁, γ₂ and σ_B were "calibrated".**
4. **Wang [1] and Peng [2]:** their dependency structure for Table I.

**Using the replica's numbers honestly.** They are real results of a fully specified experiment. If you adopt them, adopt its protocol (Sec. 4, T9), describe it, and share the code (for example in a code-availability statement). Do not pair these numbers with a different description.
