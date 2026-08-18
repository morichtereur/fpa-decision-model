"""The forecast-to-actual variance bridge.

The load-bearing test is the identity one: what the drivers explain plus the
residual must equal the total variance. A bridge whose parts do not add up to
the whole is worse than no bridge, because it looks like an explanation.
"""

from __future__ import annotations

import json

import pytest

from src import config as C, drivers, variance

FACTS = json.loads((C.FACTS / "adidas_drivers.json").read_text())


# ------------------------------------------------------------------- drivers
def test_realised_drivers_come_from_reported_figures():
    """Reported, not back-solved: a driver tuned to make the bridge close
    would hide the model's own error inside a number labelled 'actual'."""
    realised = variance.realised_drivers(FACTS)
    g24, g25 = FACTS["group"]["2024"], FACTS["group"]["2025"]
    assert realised["working_capital_pct"] == g25["operating_working_capital_pct"]
    assert realised["capex_eur_m"] == g25["capex"]
    assert realised["tax_rate_pct"] == g25["effective_tax_rate_pct"]
    assert realised["ebitda_margin"] == pytest.approx(g25["ebitda"] / g25["net_sales"] * 100)
    assert realised["revenue_growth"] == pytest.approx(
        (g25["net_sales"] / g24["net_sales"] - 1) * 100
    )


def test_the_bridge_starts_where_the_backtest_starts():
    """Forecast-side values are read from the shared driver config, so the
    bridge, the Scenario Planner's Base case and the backtest cannot drift
    apart."""
    config = drivers.build_driver_config(FACTS)
    forecast = variance.forecast_drivers(FACTS)
    for driver_id, value in forecast.items():
        assert value == config[driver_id]["default"]


def test_every_driver_is_walked_exactly_once():
    steps = variance.bridge(FACTS)["steps"]
    assert [s["driver_id"] for s in steps] == list(variance.DRIVER_ORDER)
    assert len(set(s["driver_id"] for s in steps)) == len(variance.DRIVER_ORDER)


# ------------------------------------------------------------------ identity
@pytest.mark.parametrize("metric", variance.METRICS)
def test_the_parts_add_up_to_the_whole(metric):
    result = variance.bridge(FACTS, metric)
    assert result["explained_by_drivers"] + result["residual"] == pytest.approx(
        result["total_variance"], abs=0.15
    )


@pytest.mark.parametrize("metric", variance.METRICS)
def test_step_impacts_sum_to_what_the_drivers_explain(metric):
    result = variance.bridge(FACTS, metric)
    assert sum(s["impact"] for s in result["steps"]) == pytest.approx(
        result["explained_by_drivers"], abs=0.15
    )


@pytest.mark.parametrize("metric", variance.METRICS)
def test_the_endpoints_match_the_backtest(metric):
    from src import backtest

    bt = backtest.run()
    result = variance.bridge(FACTS, metric)
    assert result["forecast"] == pytest.approx(bt["driver_based"][metric], abs=0.15)
    assert result["actual"] == pytest.approx(bt["actual"][metric], abs=0.15)


# ------------------------------------------------------------- causal shape
def test_only_revenue_growth_moves_revenue():
    """A margin or capex assumption cannot change revenue. If one appears to,
    the substitution is leaking."""
    steps = {s["driver_id"]: s["impact"] for s in variance.bridge(FACTS, "revenue")["steps"]}
    assert abs(steps["revenue_growth"]) > 100
    for driver_id in ("ebitda_margin", "tax_rate_pct", "working_capital_pct", "capex_eur_m"):
        assert steps[driver_id] == 0.0


def test_cash_only_drivers_do_not_move_operating_profit():
    """Tax, working capital and capex all sit below operating profit."""
    steps = {s["driver_id"]: s["impact"] for s in variance.bridge(FACTS, "operating_profit")["steps"]}
    for driver_id in ("tax_rate_pct", "working_capital_pct", "capex_eur_m"):
        assert steps[driver_id] == 0.0


def test_working_capital_is_the_largest_driver_of_the_cash_flow_miss():
    """The finding the repository already argues from its Monte Carlo: the
    assumption nobody debates is the one that moves the answer."""
    largest = variance.largest_driver(variance.bridge(FACTS, "free_cash_flow"))
    assert largest["driver_id"] == "working_capital_pct"
    assert largest["impact"] < 0


# ---------------------------------------------------------------- disclosure
def test_the_residual_is_reported_rather_than_absorbed():
    """Substituting every realised driver does not reproduce actual exactly.
    A bridge that always closes to zero has hidden its model error."""
    result = variance.bridge(FACTS, "operating_profit")
    assert abs(result["residual"]) > 1
    assert "D&A" in result["residual_note"]


def test_order_dependence_is_disclosed():
    assert "order" in variance.bridge(FACTS)["order_note"].lower()


def test_offsetting_errors_are_called_out_when_they_dominate():
    """A net variance of +37 built from 808 of gross movement is not a sign
    the assumptions were sound, and the output has to say so."""
    result = variance.bridge(FACTS, "free_cash_flow")
    assert result["gross_driver_movement"] > abs(result["total_variance"]) * 3
    assert result["offsetting_note"] is not None
    assert "offset" in result["offsetting_note"]


def test_no_offsetting_note_when_one_driver_explains_the_variance():
    """Revenue moves on revenue growth alone, so the caveat would be noise."""
    assert variance.bridge(FACTS, "revenue")["offsetting_note"] is None


def test_each_step_cites_where_the_actual_value_came_from():
    for step in variance.bridge(FACTS)["steps"]:
        assert step["source"]
        assert "reported" in step["source"] or "disclosed" in step["source"]


def test_unknown_metric_is_rejected():
    with pytest.raises(ValueError, match="Unknown metric"):
        variance.bridge(FACTS, "ebitda")
