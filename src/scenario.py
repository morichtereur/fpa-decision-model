"""
Stage 3: scenario ranges and Monte Carlo.

Uncertainty ranges for each driver should come from the historical
volatility already visible in the three extracted fiscal years, not from
assumed spreads — same principle as gbs-business-case's measured baseline.
With only three data points that volatility estimate will be wide and
should be reported as such, not hidden behind a tight-looking distribution.

TODO:
- derive each driver's historical volatility from data/facts
- run N simulations through src.model.forecast()
- report which assumption's variance explains the most output variance
  (the point of this stage is that finding, not the simulation itself)
"""

from __future__ import annotations


def run_monte_carlo(facts: dict, assumption_ranges: dict, n: int = 10_000) -> dict:
    raise NotImplementedError
