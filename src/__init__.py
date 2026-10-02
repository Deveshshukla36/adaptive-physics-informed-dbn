"""API-DBN source package.

Contains:
- model: degradation physics and ground truth simulation
- inference: sequential Monte Carlo with MCMC rejuvenation
- maintenance: closed-loop lifecycle cost and policy optimization
- baselines: benchmark models (Fixed Wiener, Static DBN, ablations, Oracle)
- metrics: probabilistic prognostics evaluation metrics
"""

from apidbn.core import Physics, burst_pressure, critical_depth
from apidbn.filters import ParticleFilter, MODELS, FixedWiener
from apidbn.maintenance import Costs, run_policy
