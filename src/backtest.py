"""
Stage 4: the actual test of the repo's core question.

Can a driver-based forecast, built only from data available as of a past
period, beat a naive top-down extrapolation at predicting what actually
happened?

With three fiscal years (2023-2025) there is exactly one honest backtest
point: build the model as of FY2024 (using only 2023-2024 drivers and
adidas's own stated FY2025 guidance as the planning assumptions), forecast
FY2025, and compare both the driver-based and naive-extrapolation forecasts
against FY2025 actuals. That is a thin sample — say so in the README rather
than dressing it up as more than one data point.

TODO:
- naive_baseline(): extrapolate FY2025 from the FY2024 run-rate only
- driver_based(): src.model.forecast() using 2023-2024 facts + stated ambitions
- compare both against actual FY2025 results, report error for each
- whichever forecast wins, or by how little, is the finding — not assumed
"""

from __future__ import annotations


def naive_baseline(facts: dict) -> dict:
    raise NotImplementedError


def run() -> dict:
    raise NotImplementedError


if __name__ == "__main__":
    run()
