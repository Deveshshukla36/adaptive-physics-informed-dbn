"""Model and physics module for API-DBN.

Implements the continuous corrosion-shock physics, DNV burst pressure capacity,
and ground-truth pipeline simulation for Scenario A and Scenario B.
"""

from apidbn.core import (
    DT,
    STEPS_PER_YEAR,
    Physics,
    burst_pressure,
    critical_depth,
    drift_gain,
    folias_factor,
    intact_burst_pressure,
    shock_gain,
    shock_magnitudes,
    step,
)
from apidbn.truth import (
    SCENARIOS,
    Scenario,
    simulate_paths,
    simulate_truth,
)

__all__ = [
    "DT",
    "STEPS_PER_YEAR",
    "Physics",
    "burst_pressure",
    "critical_depth",
    "drift_gain",
    "folias_factor",
    "intact_burst_pressure",
    "shock_gain",
    "shock_magnitudes",
    "step",
    "SCENARIOS",
    "Scenario",
    "simulate_paths",
    "simulate_truth",
]
