"""
Stage 2: the driver-based forecast.

Takes the extracted historical drivers (channel and category
currency-neutral growth, plus the reported-vs-currency-neutral FX gap) plus
a set of explicit, visible planning assumptions for the forecast period,
and traces them through to EBITDA and free cash flow — the same separation
of reported facts vs. planning assumptions vs. calculated outputs used
throughout this portfolio.

TODO:
- load data/facts/adidas_drivers.json
- define the planning-assumption schema (one file per scenario, human-edited)
- build the driver -> revenue -> EBITDA -> FCF calculation chain
- keep every calculated output traceable back to which fact or assumption
  produced it (no number in the output that can't be explained)
"""

from __future__ import annotations


def forecast(facts: dict, assumptions: dict) -> dict:
    raise NotImplementedError
