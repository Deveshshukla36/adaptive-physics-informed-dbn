# Summary of Scientific and Technical Revisions

This document outlines the scientific clarifications, technical corrections, and reproducible experimental results incorporated into the revised manuscript and implementation.

All revisions maintain scientific consistency between the text, mathematical equations, and computational results.

---

## 1. Experimental Results and Protocol Clarification

### 1.1 Numerical Protocol and Results
The experimental evaluation reports results from 30 matched runs (seeds 0–29, 9,990 pipelines, 121,091 scored RUL forecasts per model):
- **API-DBN vs. Static DBN**:
  - MAE is reduced from $1.38 \pm 0.09$ yr to $1.12 \pm 0.04$ yr (an **18.6% reduction**, paired $t_{29} = 17.7$, $p < 10^{-16}$).
  - CRPS is reduced from $1.12 \pm 0.08$ yr to $0.80 \pm 0.03$ yr (a **28.7% reduction**).
  - 95% prediction interval coverage (PICP) is **95.3%** for API-DBN (Wilson 95% CI $[95.2\%, 95.4\%]$) versus **59.9%** for the Static DBN.
- **Scientific Interpretation**:
  The primary advantage of API-DBN lies in uncertainty calibration. Because the Static DBN cannot adjust to asset-specific drift or parameters, its intervals remain narrow and severely under-cover true lifetimes. API-DBN learns individual degradation rates, yielding well-calibrated prediction intervals.

### 1.2 Scenario A vs. Scenario B Distinction
- **Scenario A (Literal Parameters)**: Every pipeline uses exactly the nominal Table IV parameters without drift. In this setting, the Static DBN matches the Oracle (MAE 0.48 yr) and outperforms API-DBN (MAE 0.93 yr), because parameter updating is unnecessary when parameters are homogeneous and known.
- **Scenario B (Adaptive Setting)**: Asset-specific baseline parameters vary by $\exp(\mathcal{N}(0, 0.25^2))$ and drift annually by log-random walks ($\sigma_{\mathrm{rw}} = 0.05$/yr). This represents the intended adaptive condition where parameter learning is essential.
- Reporting both scenarios clarifies *when* and *why* adaptive Bayesian updating provides value.

---

## 2. Algorithmic Findings

### 2.1 Role of MCMC Rejuvenation
In the 2x2 factorial ablation (Coupling $\times$ MCMC):
- With coupling: MAE is $1.12$ yr with or without MCMC rejuvenation ($t = -0.05, p = 0.96$).
- Without coupling: MAE is $2.29$ yr with or without MCMC rejuvenation.
- Under the current formulation where the latent state path is held fixed, the Metropolis-Hastings move can only refresh parameters within the random-walk spread around the previous step, which is already provided by state propagation.
- MCMC is therefore documented as an algorithmic component without measurable impact on accuracy, rather than a headline performance driver.

### 2.2 Role of Corrosion-Shock Coupling
Removing the state-dependent corrosion-shock coupling doubles prognostic error (MAE increases from $1.12$ yr to $2.29$ yr, $t = 90.5, p < 10^{-36}$). Without coupling, the model cannot anticipate acceleration and substantially overestimates RUL (mean bias $+2.1$ yr). This quantitatively demonstrates the importance of coupling.

---

## 3. Maintenance Optimization Corrections

- **Evaluation Basis**: Maintenance costs are evaluated closed-loop against ground-truth pipeline evolution over a 20-year horizon with 5% discounting, rather than against internal model predictions.
- **Policy Comparison**:
  - The previously noted policy ($I=2$ yr, $\gamma=1.5$ yr) allows 12.8%–20.5% of pipelines to fail because $\gamma < I$ leaves pipelines unprotected between inspections.
  - On the extended search grid ($\gamma \le 5.0$ yr):
    - Static DBN optimum: $I^* = 2.5$ yr, $\gamma^* = 4.5$ yr ($\$425\mathrm{k} \pm 4\mathrm{k}$, failure rate $0.07\%$).
    - API-DBN optimum: $I^* = 4.0$ yr, $\gamma^* = 5.0$ yr ($\$353\mathrm{k} \pm 5\mathrm{k}$, failure rate $0.07\%$).
    - Oracle optimum: $I^* = 4.0$ yr, $\gamma^* = 4.5$ yr ($\$342\mathrm{k} \pm 11\mathrm{k}$, failure rate $0.27\%$).
  - API-DBN achieves a **16.8% cost reduction** relative to the Static DBN and approaches the Oracle cost.
  - The API-DBN and Oracle optima lie on the boundary of the searched grid ($I = 4.0$ yr), which is explicitly documented as a limitation rather than an unconstrained global minimum.

---

## 4. Role of External BSEE / PHMSA Data

The BSEE/PHMSA records are **not** used as training, validation, or test data (no longitudinal inspection or failure-time series exist in the public repository). Instead, they are used strictly for three external consistency checks:
1. **Pipe Dimension**: The 24-inch case study is documented as a large trunkline (representing only ~1.5% of installed Gulf of Mexico segments).
2. **Shock Rate**: Reported incident frequency is $\le 0.0051$ per segment-year, approximately 160 times lower than $\lambda = 0.8$/yr; therefore $\lambda$ is explicitly identified as an analytical assumption.
3. **Failure Cost**: The assumed $C_{\mathrm{fail}} = \$5\mathrm{M}$ is higher than 91.7% of reported incident cleanup costs.

All occurrences of terms such as "held-out test set" or "external validation dataset" have been removed.

---

## 5. Technical Equation and Notation Corrections

1. **Critical Failure Depth**: Exact solution of the burst failure equation gives $d_{\mathrm{crit}} = 12.07$ mm $\approx 12.1$ mm (63.2% wall thickness), correcting the earlier 11 mm approximation.
2. **Burst Pressure Model**: Described accurately as a "simplified DNV-RP-F101 / ASME B31G-type formulation" to reflect the specific Folias factor and SMYS coefficients used.
3. **Sigmoid Formulation**: Clarified that at zero damage ($Z = 0$), the drift multiplier is $1.38$, so baseline drift $\mu^{(0)}$ represents a reference parameter rather than the initial effective rate.
4. **Notation Disambiguation**: Sigmoid steepness is denoted $r_s$ (units $\mathrm{mm}^{-1}$) to avoid notation collision with the discount rate $r = 0.05$.
5. **Shock Equivalent Damage**: Clarified that shock magnitude $Y$ has mean $0.32$ mm, while equivalent damage $\Delta S = \kappa Y^\eta$ has expectation $\mathbb{E}[\Delta S] \approx 0.17$ mm.
6. **Units**: Explicitly stated: $\sigma_B$ in $\mathrm{mm}/\sqrt{\mathrm{yr}}$, $r_s$ in $\mathrm{mm}^{-1}$.

---

## 6. Figure Revisions

- **Figure 1 (Workflow)**: Corrected BSEE acronym, aligned section references, and clarified closed-loop inspection feedback arrow.
- **Figure 2 (DBN Topology)**: Removed directed cycles; properly ordered temporal transitions: $\theta_{k-1} \to \theta_k$, $\theta_k \to (X_{k+1}, S_{k+1})$, $Z_k \to X_{k+1}$, $X_k \to S_{k+1}$, and added diffusion parameter $\sigma_B$.
- **Figure 3 (SMC Workflow)**: Replaced "ISS" with "ESS" (Effective Sample Size), included parameter-evolution step, and added temporal iteration loop.
- **Figure 4 (Degradation Trajectories)**: Generated directly from Table IV parameters showing the 12.1 mm failure threshold and stochastic trajectories.
- **Figure 5 (Reliability Curves)**: Corrected population reliability curves to start at $R(0) = 1.0$ and reflect true simulated failure distributions.
- **Figure 6 (Cost Heatmaps)**: Aligned axes ($I$ in years, $\gamma$ in years) and plotted verified Monte Carlo closed-loop costs.

---

## 7. Reference Audit and Bibliographic Corrections

Checked against Crossref and publisher databases:
- Replaced unverified references ([7], [8], [9], [11], [19]):
  - Cited Zhang et al. (EJOR 2018) for Wiener degradation modeling.
  - Cited Kantas et al. (Statist. Sci. 2015) for parameter estimation in state-space models.
  - Cited Gilks & Berzuini (JRSS-B 2001) for sequential Bayesian rejuvenation moves.
  - Added Pfander et al. (*Data in Brief* 2024) for the NETL Gulf of Mexico pipeline dataset.
- Corrected author lists and bibliographic details for Cai et al. (China Ocean Eng. 2020) and Cai et al. (IEEE Trans. Ind. Electron. 2020).
- Removed uncited entries.
- Bibliographic details were checked against Crossref and publisher databases, ensuring all references are verified and properly cited in citation order.
