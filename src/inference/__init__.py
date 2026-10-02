"""Inference module for API-DBN.

Implements Sequential Monte Carlo (SMC) particle filtering, Metropolis-Hastings (MH)
rejuvenation, and remaining useful life (RUL) trajectory forecasting.
"""

from apidbn.filters import (
    FilterConfig,
    ParticleFilter,
    forecast_failure,
    sample_prior,
    systematic_resample,
)

__all__ = [
    "FilterConfig",
    "ParticleFilter",
    "forecast_failure",
    "sample_prior",
    "systematic_resample",
]
