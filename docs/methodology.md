# API-DBN Methodology

This document summarizes the mathematical formulation and computational algorithms of the Adaptive Physics-Informed Dynamic Bayesian Network (API-DBN) framework for subsea pipeline integrity management.

---

## 1. Physical Degradation and Capacity

Subsea pipelines experience continuous progressive corrosion along with discrete random external shocks (e.g., dropped objects, anchoring impacts, pressure surges).

### 1.1 Corrosion Degradation
Corrosion depth $X_t$ is modeled as a drift-diffusion Wiener process over discrete increments $\Delta t = 0.1$ yr:

$$\Delta X_k = \mu_{\mathrm{eff}, k} \Delta t + \sigma_B \sqrt{\Delta t} \, \varepsilon_k, \quad \varepsilon_k \sim \mathcal{N}(0, 1)$$

where:
- $\mu_{\mathrm{eff}, k}$ is the effective corrosion drift rate at step $k$.
- $\sigma_B = 0.20\ \mathrm{mm}/\sqrt{\mathrm{yr}}$ is the diffusion coefficient.

### 1.2 Discrete Shock Damage
Shock events follow a non-homogeneous Poisson process with effective arrival rate $\lambda_{\mathrm{eff}, k}$:

$$N_k \sim \mathrm{Poisson}(\lambda_{\mathrm{eff}, k} \Delta t)$$

For each shock $i \in \{1, \dots, N_k\}$, the shock magnitude $Y_i$ follows a Gaussian distribution truncated below at zero:

$$Y_i \sim \mathcal{N}(\mu_{y_0}, \sigma_{y_0}^2) \quad \text{with } Y_i > 0$$

with nominal parameters $\mu_{y_0} = 0.32$ mm and $\sigma_{y_0} = 0.15$ mm. The equivalent wall loss per shock is mapped via power-law scaling:

$$\Delta S_i = \kappa Y_i^\eta$$

where $\kappa = 0.30$ and $\eta = 0.50$. Under this mapping, the expected equivalent wall thinning per shock is:

$$\mathbb{E}[\Delta S] \approx 0.166\ \mathrm{mm} \approx 0.17\ \mathrm{mm}$$

### 1.3 Total Defect Depth and Failure Criterion
The cumulative equivalent wall loss is the sum of corrosion thinning and shock-induced damage:

$$Z_k = X_k + S_k$$

Structural burst failure is evaluated using a simplified DNV-RP-F101 / ASME B31G-type burst-pressure formulation:

$$P_{\mathrm{burst}}(d) = P_0 \frac{1 - d / t_{\mathrm{nom}}}{1 - (d / t_{\mathrm{nom}}) / M}$$

where:
- Intact burst pressure: $P_0 = \frac{2 t_{\mathrm{nom}} \mathrm{SMYS}}{D - t_{\mathrm{nom}}} = \frac{2(19.1)(358)}{610 - 19.1} \approx 23.14\ \mathrm{MPa}$.
- Folias factor: $M = \sqrt{1 + 0.8 \frac{L^2}{D t_{\mathrm{nom}}}} = \sqrt{1 + 0.8 \frac{500^2}{610 \times 19.1}} \approx 4.262$.
- Operating pressure: $P_{\mathrm{op}} = 10.0\ \mathrm{MPa}$.

Failure occurs when internal pressure exceeds burst capacity, $P_{\mathrm{op}} \ge P_{\mathrm{burst}}(Z)$. Setting $P_{\mathrm{burst}}(d_{\mathrm{crit}}) = P_{\mathrm{op}}$ yields the exact critical failure depth:

$$d_{\mathrm{crit}} = t_{\mathrm{nom}} \frac{1 - q}{1 - q / M} \approx 12.07\ \mathrm{mm} \approx 12.1\ \mathrm{mm}$$

where $q = P_{\mathrm{op}} / P_0 \approx 0.432$. The critical depth corresponds to $63.2\%$ wall thickness loss.

---

## 2. Two-Way State-Dependent Coupling

Corrosion and shocks interact dynamically:

### 2.1 Corrosion Acceleration from Cumulative Damage
Cumulative damage accelerates the effective corrosion drift rate through a continuous sigmoid transition:

$$\frac{\mu_{\mathrm{eff}}(Z)}{\mu^{(0)}} = 1 + \frac{\alpha - 1}{1 + \exp\left[-r_s (Z - W_0)\right]}$$

- $W_0 = 1.0$ mm is the midpoint of the sigmoid acceleration.
- $\alpha = 2.0$ is the asymptotic acceleration factor.
- $r_s = 0.5\ \mathrm{mm}^{-1}$ is the steepness parameter.
- At zero damage ($Z = 0$), the gain factor is $1 + 1 / (1 + e^{0.5}) \approx 1.378$, so the effective drift starts at $\approx 0.606$ mm/yr for a nominal baseline drift $\mu^{(0)} = 0.44$ mm/yr.

### 2.2 Shock Vulnerability from Wall Thinning
As corrosion deepens, the pipeline becomes more susceptible to localized damage from shocks:

$$\frac{\lambda_{\mathrm{eff}}(X)}{\lambda^{(0)}} = \exp(\gamma_1 X + \gamma_2 E)$$

where $\gamma_1 = 0.05\ \mathrm{mm}^{-1}$ and environmental covariate $E = 0$ in the controlled setup.

---

## 3. Sequential Bayesian Inference (Algorithm 1)

At annual inspection intervals, noisy defect observations are acquired:

$$O_k = Z_k + v_k, \quad v_k \sim \mathcal{N}(0, \sigma_v^2)$$

with inspection accuracy $\sigma_v = 0.10$ mm.

### 3.1 Latent State and Dynamic Parameters
Each particle $m \in \{1, \dots, M\}$ carries:
- Latent physical state: $[X_k^{(m)}, S_k^{(m)}]^T$
- Evolving degradation parameters: $\theta_k^{(m)} = [\mu_k^{(0, m)}, \lambda_k^{(0, m)}, \sigma_{B, k}^{(m)}]^T$

Parameters follow log-random walk drift over annual intervals:

$$\log \theta_k^{(m)} = \log \theta_{k-1}^{(m)} + \boldsymbol{\sigma}_{\mathrm{rw}} \odot \boldsymbol{\xi}_k^{(m)}, \quad \boldsymbol{\xi}_k^{(m)} \sim \mathcal{N}(\mathbf{0}, \mathbf{I})$$

with $\boldsymbol{\sigma}_{\mathrm{rw}} = [0.05, 0.05, 0.05]^T$ per year.

### 3.2 Weighting and Resampling
Particles are weighted by inspection likelihood:

$$w_k^{(m)} \propto w_{k-1}^{(m)} \, \mathcal{N}(O_k \mid X_k^{(m)} + S_k^{(m)}, \sigma_v^2)$$

Systematic resampling is triggered when effective sample size falls below threshold:

$$\mathrm{ESS} = \frac{1}{\sum_{m=1}^M (w_k^{(m)})^2} < \frac{M}{2}$$

### 3.3 Metropolis-Hastings Rejuvenation
Following resampling, parameter diversity is refreshed via 5 Metropolis-Hastings sweeps. When the latent state path is held fixed, the observation likelihood cancels, targeting the conditional parameter posterior:

$$p(\theta_k \mid \theta_{k-1}, s_{k-1}, s_k) \propto p(s_k \mid s_{k-1}, \theta_k) \, p(\theta_k \mid \theta_{k-1})$$

Proposals are Gaussian random walks on $\log \theta_k$.

---

## 4. Probabilistic Remaining Useful Life (RUL) Prediction

At each inspection prior to failure:
1. $M = 1,000$ posterior particles are projected forward.
2. Across $J = 10,000$ Monte Carlo trajectories, future corrosion noise and Poisson shock arrivals are simulated until $Z \ge d_{\mathrm{crit}}$.
3. The point prediction is the **predictive median** of the RUL distribution.
4. Central 90% and 95% prediction intervals quantify prognostic uncertainty.

---

## 5. Closed-Loop Maintenance Optimization

The maintenance model evaluates policies defined by two operational parameters:
- **Inspection interval $I$** (years): frequency of condition monitoring.
- **Replacement threshold $\gamma$** (years): action trigger.

### 5.1 Decision Rule
At each inspection $k I$, the 10th-percentile RUL forecast is computed:

$$\mathrm{RUL}_{0.10} = Q_{0.10}(\widehat{\mathrm{RUL}})$$

If $\mathrm{RUL}_{0.10} \le \gamma$, preventive replacement is scheduled, resetting damage to $Z = 0$. If the pipeline fails between inspections ($Z \ge d_{\mathrm{crit}}$), corrective replacement is executed immediately.

### 5.2 Lifecycle Cost Criterion
Total expected discounted cost over a 20-year horizon at discount rate $r = 0.05$:

$$\mathbb{E}[C] = \mathbb{E}\left[ \sum_{j} \frac{C_{\mathrm{ins}}}{(1+r)^{t_{\mathrm{ins}, j}}} + \sum_{l} \frac{C_{\mathrm{prev}}}{(1+r)^{t_{\mathrm{prev}, l}}} + \sum_{m} \frac{C_{\mathrm{fail}} + C_{\mathrm{env}}}{(1+r)^{t_{\mathrm{fail}, m}}} \right]$$

Costs are evaluated closed-loop against ground-truth pipeline evolution rather than internal model forecasts.
