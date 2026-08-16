"""
Stage 5: LLM-written management commentary, grounded against the outputs.

The LLM writes prose from the calculated output table only — it never sees
raw source text and cannot introduce a number that isn't already in that
table. Every numeric claim in its output is then regex-extracted and
checked back against the table, and the grounding rate is reported as a
real metric, the same rigor dax-intelligence applies to its citations.

TODO:
- write() takes the forecast/backtest/scenario outputs, returns commentary
- verify_grounding() extracts every number the commentary states and
  confirms it appears in the output table it was given
- report commentary grounding rate alongside the forecast, not separately
"""

from __future__ import annotations

from src import config as C


def write(outputs: dict) -> str:
    raise NotImplementedError


def verify_grounding(commentary: str, outputs: dict) -> dict:
    raise NotImplementedError
