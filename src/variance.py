"""
Stage 4b: why the forecast missed, not just by how much.

`src/backtest.py` establishes that the driver-based FY2025 forecast landed
€37.2m below actual free cash flow and €306m below actual operating profit.
That is the question a controller asks first and stops caring about
immediately. The second question — *which assumption was wrong* — is the one
that changes what anyone does next, and it is the one FP&A is actually paid to
answer.

This module walks the forecast's five drivers to their realised FY2025 values
one at a time, in a fixed order, and attributes the resulting movement in the
chosen metric to the driver that was changed. The same sequential-bridge
mechanic the Scenario Planner already uses between base and scenario, pointed
at forecast versus actual instead.

Two properties make it honest rather than decorative:

**It is order-dependent, and says so.** Drivers interact — margin applied to a
different revenue base gives a different euro impact — so a sequential bridge
assigns interaction effects to whichever driver moves later. That is a
standard limitation of the method, not a defect of this implementation, and
the fixed order is stated rather than tuned to make a particular driver look
decisive.

**It carries a residual line.** Substituting every realised driver does not
reproduce actual exactly: the model scales D&A with revenue, product-division
revenue sums to €23,690m against a reported group figure of €23,683m, and FCF
here is a derived construction. Whatever is left over after all five drivers is
reported as residual rather than silently absorbed into the last step. A bridge
that always closes to zero is hiding something.
"""

from __future__ import annotations

from dataclasses import dataclass

from src import drivers, model

#: The order drivers are substituted in. Revenue first because every other
#: driver is applied to a revenue base, so walking it first means the remaining
#: steps are measured against the revenue that actually happened. Within the
#: rest, income-statement drivers precede cash drivers, which is the order a
#: P&L-to-cash-flow bridge is normally read in.
DRIVER_ORDER: tuple[str, ...] = (
    "revenue_growth",
    "ebitda_margin",
    "tax_rate_pct",
    "working_capital_pct",
    "capex_eur_m",
)

METRICS: tuple[str, ...] = ("free_cash_flow", "operating_profit", "revenue")

#: Where each realised driver value comes from. Reported figures are used in
#: preference to model-implied ones: back-solving a driver so the bridge closes
#: exactly would bury the model's own error inside a number labelled "actual".
REALISED_SOURCES: dict[str, str] = {
    "revenue_growth": "FY2025 net sales over FY2024 net sales, as reported",
    "ebitda_margin": "FY2025 EBITDA over FY2025 net sales, as reported",
    "tax_rate_pct": "FY2025 effective tax rate, as reported",
    "working_capital_pct": "FY2025 operating working capital as a percentage of net sales, as disclosed",
    "capex_eur_m": "FY2025 capital expenditure, as reported",
}


@dataclass(frozen=True)
class BridgeStep:
    """One driver moved from its forecast value to what actually happened."""

    driver_id: str
    label: str
    unit: str
    forecast_value: float
    actual_value: float
    metric_before: float
    metric_after: float

    @property
    def impact(self) -> float:
        return self.metric_after - self.metric_before


def realised_drivers(facts: dict) -> dict[str, float]:
    """FY2025 as reported, expressed in the same five drivers the forecast used.

    This is what makes the comparison meaningful: the forecast and the outcome
    are described in one vocabulary, so "the margin assumption was wrong by
    2.1 points" is a statement about the same quantity in both.
    """
    g24, g25 = facts["group"]["2024"], facts["group"]["2025"]
    return {
        "revenue_growth": (g25["net_sales"] / g24["net_sales"] - 1) * 100,
        "ebitda_margin": g25["ebitda"] / g25["net_sales"] * 100,
        "tax_rate_pct": g25["effective_tax_rate_pct"],
        "working_capital_pct": g25["operating_working_capital_pct"],
        "capex_eur_m": g25["capex"],
    }


def forecast_drivers(facts: dict) -> dict[str, float]:
    """The driver-based forecast's own assumptions.

    Read from drivers.build_driver_config() rather than restated here, so the
    bridge starts from the same numbers the Scenario Planner's Base case and
    the backtest use. A second copy would drift.
    """
    config = drivers.build_driver_config(facts)
    return {driver_id: config[driver_id]["default"] for driver_id in DRIVER_ORDER}


def _metric(facts: dict, driver_values: dict[str, float], metric: str) -> float:
    division24 = {k: v for k, v in facts["product_division"]["2024"].items() if k != "source"}
    assumptions = drivers.defaults_to_assumptions(driver_values, division24)
    result = model.forecast(facts["group"]["2024"], facts["product_division"]["2024"], assumptions)
    return float(result[metric])


def bridge(facts: dict, metric: str = "free_cash_flow") -> dict:
    """Decompose the forecast-to-actual gap in ``metric`` across the drivers.

    Returns the steps, what they explain, and what they do not.
    """
    if metric not in METRICS:
        raise ValueError(f"Unknown metric {metric!r}. Available: {list(METRICS)}")

    config = drivers.build_driver_config(facts)
    forecast_values = forecast_drivers(facts)
    actual_values = realised_drivers(facts)

    current = dict(forecast_values)
    running = _metric(facts, current, metric)
    forecast_metric = running

    steps: list[BridgeStep] = []
    for driver_id in DRIVER_ORDER:
        before = running
        current[driver_id] = actual_values[driver_id]
        running = _metric(facts, current, metric)
        steps.append(
            BridgeStep(
                driver_id=driver_id,
                label=config[driver_id]["label"],
                unit=config[driver_id]["unit"],
                forecast_value=forecast_values[driver_id],
                actual_value=actual_values[driver_id],
                metric_before=before,
                metric_after=running,
            )
        )

    actual_metric = _actual_metric(facts, metric)
    explained = running - forecast_metric
    total = actual_metric - forecast_metric
    gross = sum(abs(s.impact) for s in steps)

    return {
        "metric": metric,
        "forecast": round(forecast_metric, 1),
        "actual": round(actual_metric, 1),
        "total_variance": round(total, 1),
        "explained_by_drivers": round(explained, 1),
        "residual": round(total - explained, 1),
        "gross_driver_movement": round(gross, 1),
        "offsetting_note": _offsetting_note(gross, total),
        "residual_note": (
            "Not attributable to a driver: the model scales D&A with revenue, "
            "product-division revenue does not sum exactly to reported group net "
            "sales, and free cash flow is a derived construction rather than a "
            "disclosed line item."
        ),
        "order_note": (
            "Sequential bridge: drivers are substituted in a fixed order, so "
            "interaction effects are attributed to whichever driver moves later."
        ),
        "steps": [
            {
                "driver_id": s.driver_id,
                "label": s.label,
                "unit": s.unit,
                "forecast_value": round(s.forecast_value, 2),
                "actual_value": round(s.actual_value, 2),
                "impact": round(s.impact, 1),
                "share_of_variance_pct": (
                    round(s.impact / total * 100, 1) if abs(total) > 1e-9 else None
                ),
                "source": REALISED_SOURCES[s.driver_id],
            }
            for s in steps
        ],
    }


def _offsetting_note(gross: float, total: float) -> str | None:
    """Flag a small net variance built from large, opposing driver errors.

    Without this the share-of-variance percentages read as a defect: a driver
    worth -372 against a net variance of +37 is -1001% of it. The percentages
    are right and the situation is the point — a forecast can land close to
    actual while every assumption behind it was wrong, and that is a materially
    different finding from a forecast that was simply accurate.
    """
    if abs(total) < 1e-9 or gross <= abs(total) * 3:
        return None
    return (
        f"Driver errors largely offset: {gross:,.1f} of gross movement nets to "
        f"{total:+,.1f}. The forecast landed close on this metric despite every "
        f"assumption behind it being wrong, so the small variance is not evidence "
        f"the assumptions were sound."
    )


def _actual_metric(facts: dict, metric: str) -> float:
    """Actual FY2025, derived exactly as src/backtest.py derives it."""
    from src import backtest

    result = backtest.run()
    return float(result["actual"][metric])


def largest_driver(bridge_result: dict) -> dict | None:
    """The single assumption that moved the metric most, in absolute terms.

    The headline a reviewer wants: not the size of the miss, but its cause.
    """
    steps = bridge_result["steps"]
    return max(steps, key=lambda s: abs(s["impact"])) if steps else None


def main() -> None:  # pragma: no cover - manual inspection
    import json
    from pathlib import Path

    facts = json.loads(
        (Path(__file__).resolve().parent.parent / "data" / "facts" / "adidas_drivers.json").read_text()
    )
    for metric in METRICS:
        result = bridge(facts, metric)
        print(f"\n{metric}: forecast {result['forecast']:,.1f} -> actual {result['actual']:,.1f} "
              f"(variance {result['total_variance']:+,.1f})")
        print(f"  {'driver':<22}{'forecast':>10}{'actual':>10}{'impact':>12}{'share':>9}")
        for step in result["steps"]:
            share = f"{step['share_of_variance_pct']:+.0f}%" if step["share_of_variance_pct"] is not None else "-"
            print(f"  {step['label']:<22}{step['forecast_value']:>10.2f}{step['actual_value']:>10.2f}"
                  f"{step['impact']:>+12.1f}{share:>9}")
        print(f"  {'residual':<22}{'':>20}{result['residual']:>+12.1f}")
        print(f"  {'gross movement':<22}{'':>20}{result['gross_driver_movement']:>12.1f}")
        if result["offsetting_note"]:
            print(f"  ! {result['offsetting_note']}")


if __name__ == "__main__":
    main()
