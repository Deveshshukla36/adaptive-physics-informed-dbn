"""Baseline and benchmark models for comparative evaluation.

Includes Fixed Wiener process, Static DBN, ablated configurations (PF without MCMC,
No coupling), and the Oracle reference.
"""

from apidbn.filters import (
    MODELS,
    FixedWiener,
)

__all__ = [
    "MODELS",
    "FixedWiener",
]
