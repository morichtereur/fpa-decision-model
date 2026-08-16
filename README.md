# FP&A Decision Model

[![Tests](https://github.com/morichtereur/fpa-decision-model/actions/workflows/test.yml/badge.svg)](https://github.com/morichtereur/fpa-decision-model/actions/workflows/test.yml)

**Can a driver-based FP&A model beat a naive top-down forecast, checked against what actually happened?**

FP&A models often look precise while hiding the assumptions that actually
drive the answer. This project separates reported facts, planning
assumptions and calculated outputs, then traces changes in price, volume,
FX and portfolio effects through to organic growth, EBITDA and free cash
flow for one real company — rather than presenting a forecast as if it were
a measurement.

## Status

Scaffolding only — no forecast has been run yet. This README states the
method and the company/data source now, and will be replaced by an actual
finding once `src/extract.py`, `src/model.py`, `src/scenario.py` and
`src/backtest.py` are implemented. Nothing below the Method section is a
result; it is a plan.

## The company

**Henkel AG & Co. KGaA** (Adhesive Technologies and Consumer Brands
segments), using the two annual reports already collected for
[dax-intelligence](https://github.com/morichtereur/dax-intelligence):
`Henkel_Report_2024.pdf` (FY2023/FY2024) and `Henkel_Report_2025.pdf`
(FY2024/FY2025). Both disclose a quantitative organic sales bridge —
nominal growth, FX effect, acquisitions/divestments, organic growth, and
its price/volume split — at Group and business-unit level. See
`data/raw/README.md` for where to get the PDFs and a known data-quality
wrinkle: the FY2025 report's restated FY2024 comparatives don't exactly
match what the FY2024 report itself disclosed for FY2024, which needs a
visible reconciliation decision, not a silent overwrite.

Three fiscal years is a thin backtest sample — one point, not a track
record. That limit is stated here rather than hidden behind a
confident-looking chart.

## Method

**Data → model → result → decision implication → evaluation**

1. **Facts** (`src/extract.py`) — the organic sales bridge, parsed out of
   the two source PDFs into `data/facts/`, kept separate from anything
   assumed.
2. **Model** (`src/model.py`) — a driver-based forecast: explicit planning
   assumptions for price, volume, FX and margin, traced through to EBITDA
   and free cash flow, with every output traceable back to the fact or
   assumption that produced it.
3. **Scenario** (`src/scenario.py`) — Monte Carlo over each driver, with
   ranges derived from the three years of measured historical volatility
   rather than assumed spreads. The point is which assumption explains the
   most output variance, not the simulation itself.
4. **Backtest** (`src/backtest.py`) — the actual test of the core question:
   build the model as of FY2024 using only 2023–2024 data and Henkel's own
   stated mid-term ambitions, forecast FY2025, and compare both the
   driver-based forecast and a naive top-down extrapolation against FY2025
   actuals. Whichever wins, or by how little, is the finding.
5. **Commentary** (`src/commentary.py`) — an LLM writes management
   commentary from the calculated output table only, never from raw source
   text. Every number it states is checked back against that table, and
   the grounding rate is reported alongside the forecast — the same
   standard dax-intelligence applies to its citations.

## Stack

`Python` · `DuckDB` · `NumPy` · `matplotlib` · `LLM API` · `pytest`

## Repository map

| path | responsibility |
|---|---|
| `src/config.py` | company/segment/fiscal-year scope, paths, env vars |
| `src/extract.py` | parse the organic sales bridge out of the source PDFs |
| `src/model.py` | driver-based forecast: facts + assumptions → EBITDA/FCF |
| `src/scenario.py` | Monte Carlo over historical driver volatility |
| `src/backtest.py` | driver-based vs. naive forecast, checked against actuals |
| `src/commentary.py` | grounded LLM commentary + numeric verification |
| `data/raw/` | source PDFs (not committed — see `data/raw/README.md`) |
| `data/facts/` | extracted, structured driver data |
| `tests/` | deterministic checks, no API calls |

## Run it

```bash
cp .env.example .env      # Anthropic key, needed only for src/commentary.py
python3 -m venv .venv && source .venv/bin/activate
make install
# place the two Henkel PDFs in data/raw/ — see data/raw/README.md
make extract
make backtest
make test
```

## What this is not

- **A finished forecast.** See Status above.
- **A multi-company benchmark.** One company, one segment pair, three
  fiscal years — depth over breadth, matching the rest of this portfolio.
- **A trading or investment signal.** This is a methodology exercise on
  public financial disclosures, not analysis intended to inform an
  investment decision.

---

Built by [Moritz Richter](https://www.linkedin.com/in/moritz-richter-28297119a/) · Finance & Strategy Consultant · Zürich
