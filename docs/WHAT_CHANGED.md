# Revised paper: what changed

Your original `main (3).tex` is untouched. This folder holds the revised version.

| File | What it is |
|---|---|
| `main.tex` | The revised paper |
| `fig1_workflow.png` … `fig6_cost.png` | The six figures it uses: three redrawn diagrams and three regenerated results |
| `Revised_Paper_Overleaf.zip` | `main.tex` plus the six figures, ready for Overleaf |

## How to use it

- **New project:** in Overleaf choose **New Project → Upload Project** and select the zip.
- **Existing project:** replace `main.tex` and upload the six PNG files. The old images (`fig1.jpg`, `figure2_dbngraph.png`, …) are no longer used.

Compile with pdfLaTeX. It could not be compiled on this Mac, which has no LaTeX installed. A script checked the source for balanced environments, braces and math, unresolved references and citations, and leftover text from the old version, and found no problems.

## Where the numbers come from

Every result in the paper now comes from the independent re-implementation in `../API-DBN_replica/`. That replica ran 30 matched runs of 333 pipelines each (9,990 pipelines and 121,091 forecasts per model), plus 3,000 pipelines with identical parameters and 1,500 pipelines for maintenance.

The methods section now describes exactly that experiment: pipeline-specific parameters with yearly drift, Δt = 0.1 yr, annual inspections, the baselines, the priors, the MCMC settings and the maintenance loop. If you later rerun your own code instead, replace the numbers and keep the description consistent with what your code does. Sharing the replica code (for example in a code-availability statement) would strengthen the paper.

The numbers in Section IV-A and Table III come from NETL's public files, downloaded on 29 Sep 2026. The replica's `experiments/bsee_records.py` computes them, and `results/bsee_records.json` holds the output with each file's SHA-256. The data files are not copied into the replica, because the locations table alone is 493 MB; the script's header says where to download them.

## What changed, by the professor's marks

| Where | Mark | Change |
|---|---|---|
| II-A | Literature check | The novelty paragraph is rewritten. Sun et al. already model two-way dependence, so the paper now claims the specific parametric coupling inside an adaptive DBN rather than two-way dependence itself. |
| II-B | Literature check | The MCMC sentence now cites Gilks & Berzuini (resample–move) and Kantas et al.; no claims are made about what other studies update. |
| II-C | CITATION REQUIRED | Added Seo et al. 2015 (risk-based inspection of corroded subsea pipelines), verified on Crossref. |
| Table I | Literature check × 17 | Suggested values from abstracts sit next to each flag. The flags stay, because the professor requires full-text checks. The Melchers row is removed, since that reference does not exist. The Sun et al. row now reads "Nonlinear Wiener" and "Two-way (copula-based)", and that coupling cell has an extra flag, which makes 18. |
| III-A, shocks | Literature check | States that arrivals are conditionally independent given λ_eff. Defines Y's distribution and gives E[ΔS] = 0.17 mm. |
| III-A, Eq. (6) | AUTHOR INPUT | States that Eₖ = 0 in the experiments; γ₂ is no longer used. |
| III-B, Eq. (11) | Literature check | Adds p(s₀)p(θ₀) and the propagation order; Algorithm 1 is reordered to match. |
| III-B, Eq. (15) | AUTHOR INPUT + Literature check | Corrected acceptance ratio. Gives the proposal, 5 sweeps, 44% acceptance and systematic resampling, and defines the Γ(2, 0.2, 5) prior. |
| III-C | AUTHOR INPUT | Maintenance loop fully specified: grid, horizon, the 10th-percentile rule, failures between inspections, and what replacement does. Eq. (17) is rewritten as a closed-loop average. |
| IV-A | CITATION REQUIRED | Dataset cited correctly (Romeo et al., NETL 2024, doi:10.18141/2280823), together with its data article (Pfander et al., *Data in Brief* 55, 2024), which was verified on Crossref. |
| IV-A, Table III | AUTHOR INPUT × 3 | Replaced with exact details from the NETL files. Gives the four file names, their upload dates and the download date (29 Sep 2026), and states each processing rule. Every count is recomputed. The old table said 934 incidents; the files have 943. It said ">200" lease blocks; there are 487. Its "1,247 segments with geometry" can't be reproduced; the files have 14,202 installed segments, 13,792 of them with a size code. Nothing is imputed and the records are not split, because nothing is fitted to them and no held-out evaluation is reported. |
| IV-A, Table IV | Literature check, EXPERIMENT × 2, CITATION | Unsupported sources are relabelled as assumptions. Adds the W₀/α/r_s sensitivity analysis and the M/J convergence evidence. σ_v is now "idealized inspection accuracy". Notation r → r_s. |
| IV-B | AUTHOR INPUT × 3 + Literature check | Δt, horizon, inspection schedule, noise, how pipelines differ, and a statement that the results are model-consistent only. The five models are defined precisely, and a true 2 × 2 ablation plus an oracle are added. |
| IV-C | AUTHOR INPUT × 2 | N = 121,091, a 2-yr Brier window, and the median as point prediction. |
| IV-C | AUTHOR INPUT + Literature check | Prediction-interval construction stated; "prediction interval" is used throughout. |
| IV-C, Table V | CITATION × 2, AUTHOR INPUT × 5 | Costs and discount rate are labelled assumptions, with grid increments, horizon and policy logic stated. |
| IV-C | AUTHOR INPUT + Literature check | Hardware and software stated (Apple M4, Python 3.14, NumPy, SciPy). |
| V-A | AUTHOR INPUT + Literature check | New Tables VI and VII, exact t-tests, PICP with N and a Wilson interval, and the identical-parameter comparison. |
| V-A, Figs. 4–5 | Literature check × 2 | Figures regenerated from the model, with new text. The failure depth is 12.1 mm. |
| V-B, Fig. 6 | AUTHOR INPUT + high-priority note | New closed-loop maintenance results, table and heat maps. The γ search now runs to 5 yr. Best policies: static DBN I = 2.5, γ = 4.5 ($425k); API-DBN I = 4.0, γ = 5.0 ($353k), 17% cheaper than the static DBN and 3% above the oracle ($342k). The API-DBN and oracle optima sit at the longest interval searched (4 yr), and the text says so. Under the paper's old policy (I = 2, γ = 1.5), 13–21% of pipelines fail. |
| V-C | EXPERIMENT + AUTHOR INPUT | The held-out case-study claims are removed, as the professor's note asks when no results exist. The section now states that historical validation is future work. Section IV-A no longer reserves validation and test records for an evaluation that V-C doesn't report, so the two sections agree. |
| V-D | AUTHOR INPUT + Literature check | Measured runtimes; the RUL forecasts, not the O(MK) filter, dominate. |
| V-E | Literature check × 2 | Discussion rewritten around the results. The Gaussian-prior and fleet-scale statements are resolved. |

## Other fixes the tags did not mark

- **References:**
  - Replaced or removed the 5 that could not be found: Melchers, Wang & Soares, Shen, Sanz-Bobi and Chiquet.
  - Removed the 2 that were never cited: Paris and Sanz-Bobi.
  - Replaced Andrieu (particle MCMC) with Gilks & Berzuini.
  - Corrected the author lists of the two Cai et al. papers.
  - Renumbered the list in citation order, as IEEE requires.
- **Abstract, introduction, contributions and conclusion:** new numbers, and no held-out case-study claim.
- **Eq. (5):** r → r_s, W₀ described as the sigmoid midpoint, and the 1.38 factor at zero damage explained.
- **Eqs. (7)–(9):** described as "adapted from DNV-RP-F101", with the differences stated. The failure depth, 12.07 mm, is now given, and the redundant single-shock clause is removed.
- **What the records are used for (Sec. IV-A):** three checks, not fitting.
  - The 24-in case pipe is a large trunkline: only 1.5% of installed segments are 24 in or larger. Table IV now says "24-in trunkline" instead of "representative Gulf of Mexico segment".
  - Reported incidents are at most 0.0051 per segment-year, far below λ = 0.8/yr, so λ stays an assumption.
  - C_fail = $5M is higher than 91.7% of reported incident costs, and Table V says so.
  - The abstract, introduction and Secs. III, IV, V-C and V-E now say the records are used for these checks rather than for parameterization. The acknowledgment adds PHMSA, which supplied 889 of the 943 incident reports.
- **Figs. 1–3:** redrawn. Fig. 1: BSEE and Sec. III-B, with a clear feedback arrow. Fig. 2: acyclic, arrows matching Eqs. (5)–(6), σ_B included. Fig. 3: ESS, the parameter-evolution step and the loop added.

## Still needs you (18 red flags left on purpose)

- **Table I literature check cells:** check each against the full paper. Abstract-based classifications for Liu et al. require full-text verification.

Invisible `%` comments in the source flag optional items:
- real sources for C_ins, C_prev and r, if you have them;
- how µ_base, α, γ₁ and σ_B were calibrated, if they were;
- the "Gamma" entries for Peng and Rafiee in Table I;
- the edition of DNV-RP-F107 you have.
