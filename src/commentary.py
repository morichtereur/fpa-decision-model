"""
Stage 5: LLM-written management commentary, grounded against the outputs.

The LLM writes prose from a flattened table of calculated outputs only —
it never sees raw source text or the source PDFs, and is instructed not to
introduce any number that isn't already in that table. Every numeric claim
in its output is then regex-extracted and checked back against the table,
and the grounding rate is reported alongside the forecast — the same
standard dax-intelligence applies to its citations.

verify_grounding() is the part that actually matters and is fully unit
tested without an API call (tests/test_commentary.py). write() makes a
real API call and is exercised separately, since testing it in CI would
mean either a live call on every push (costs money, network-dependent) or
a mock that verifies nothing real.
"""

from __future__ import annotations

import re

from anthropic import Anthropic

from src import config as C

SYSTEM_PROMPT = """You write short management commentary (3-5 sentences) on an FP&A \
forecast, for a reader who will see the numbers table alongside your text.

The table prefixes each number with the series it belongs to. Call each series \
by the name it is given: `actual_` is what happened, `naive_` is the top-down \
extrapolation, and the third prefix names the forecast under discussion. When \
that third series is a named scenario rather than the driver-based forecast, \
describe it as that scenario — a stress case is not the forecast.

Rules:
- Use ONLY the numbers in the table you are given. Do not compute, estimate, \
round to a different precision than shown, or bring in any figure not present \
in the table.
- State the comparison plainly: what the forecast said, what actually happened, \
and by how much it missed, in the direction it missed.
- No hedging language ("may", "could suggest") about numbers that are already \
known facts in the table.
- Plain prose, no headers or bullet points."""


def _flatten_outputs(backtest_result: dict) -> dict:
    """Turn a nested {series: {metric: value}} result into a flat
    label -> number table, which is both what the LLM is given and what
    verify_grounding() checks claims against.

    Series names are taken from the caller rather than hardcoded: the
    backtest passes `driver_based`, while the Scenario Planner passes the
    scenario's own name, so a stress case is not tabled under a label that
    invites the model to call it the driver-based forecast.
    """
    flat = {}
    for series, metrics in backtest_result.items():
        for key, value in metrics.items():
            # bool is an int subclass, so a flag would otherwise enter the
            # table as 1 — a number the model is then free to cite, and
            # verify_grounding() would accept it.
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            flat[f"{series}_{key}"] = round(value, 1)
    return flat


def write(backtest_result: dict) -> tuple[str, dict]:
    """Returns (commentary_text, outputs_table) — the table is returned
    alongside the text because verify_grounding() needs the exact same
    table the LLM was shown, not a freshly recomputed one that could have
    drifted."""
    outputs = _flatten_outputs(backtest_result)
    client = Anthropic(api_key=C.ANTHROPIC_API_KEY)
    table_text = "\n".join(f"{k}: {v}" for k, v in outputs.items())
    msg = client.messages.create(
        model=C.COMMENTARY_MODEL,
        max_tokens=450,  # headroom so a longer scenario (more divergent metrics) doesn't truncate mid-number
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Numbers table:\n{table_text}"}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text")
    return text, outputs


_NUMBER_RE = re.compile(
    r"[-−]?\s*€?\s*[\d,]+(?:\.\d+)?\s*(?:million|billion|%|pp)?", re.IGNORECASE
)


def _parse_claim(raw: str) -> float | None:
    raw = raw.strip().replace("−", "-").replace("€", "").replace(",", "")
    multiplier = 1.0
    if re.search(r"billion", raw, re.IGNORECASE):
        multiplier = 1000.0
    raw = re.sub(r"(million|billion|%|pp)", "", raw, flags=re.IGNORECASE).strip()
    if not raw or raw == "-":
        return None
    try:
        return float(raw) * multiplier
    except ValueError:
        return None


def verify_grounding(commentary: str, outputs: dict, tolerance: float = 0.05) -> dict:
    """Extracts every number-shaped token from the commentary and checks it
    against the outputs table (within a relative tolerance, since the LLM
    may write "2,056" for a value stored as 2056.0). A claim that matches
    nothing in the table is ungrounded — either hallucinated or computed
    from table values rather than copied, both of which the system prompt
    forbids.
    """
    values = list(outputs.values())
    claims = []
    for match in _NUMBER_RE.finditer(commentary):
        parsed = _parse_claim(match.group(0))
        if parsed is not None and abs(parsed) >= 1:  # skip stray single digits ("3-5 sentences")
            claims.append((match.group(0).strip(), parsed))

    grounded, ungrounded = [], []
    for raw, parsed in claims:
        # Natural-language error phrasing ("missed by 22.3%") states a
        # negative table value's magnitude without its sign, so a claim
        # grounds against either the signed or the absolute table value.
        is_grounded = any(
            v != 0 and (abs(parsed - v) / abs(v) <= tolerance or abs(abs(parsed) - abs(v)) / abs(v) <= tolerance)
            for v in values
        )
        (grounded if is_grounded else ungrounded).append(raw)

    total = len(claims)
    return {
        "total_claims": total,
        "grounded": len(grounded),
        "ungrounded": ungrounded,
        "grounding_rate": (len(grounded) / total) if total else None,
    }
