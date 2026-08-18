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
- Every `_error_pct` value is a FORECAST ERROR measured against actual. Write \
it that way: "the forecast missed actual by X%", "the forecast overstated \
revenue by X%". Never re-express it as actual beating or exceeding a forecast \
by that percentage. That is a different quantity with a different denominator, \
it is always larger, and you are not permitted to compute it — so if you want \
to say actual came in above a forecast, say so without attaching a percentage.
- Check direction against the figures themselves before writing it: the larger \
number is the larger one. A forecast below actual understated it; a forecast \
above actual overstated it.
- No hedging language ("may", "could suggest") about numbers that are already \
known facts in the table.
- Plain prose, no headers or bullet points."""


VARIANCE_SYSTEM_PROMPT = """\
You write short management commentary (3-5 sentences) explaining why an FP&A \
forecast missed, for a reader who will see the variance bridge alongside your \
text.

The table gives, for each driver, what was assumed, what actually happened, \
and what that difference was worth on the metric. `variance_*_net` is the \
overall miss, `variance_*_gross_driver_error` is the total absolute movement \
across drivers, and `variance_*_residual` is the part no driver explains.

Rules:
- Use ONLY the numbers in the table you are given. Do not compute, estimate, \
round to a different precision than shown, or bring in any figure not present \
in the table.
- Lead with the driver whose impact is largest in absolute terms, and name it.
- Where the gross driver error is much larger than the net variance, say so \
plainly: the drivers offset, and a small net miss is not evidence the \
assumptions were sound. This is the most important thing the table shows and \
it is the thing a reader will otherwise get wrong.
- Mention the residual and what it means: the part of the variance no driver \
accounts for.
- Match the verb to the SIGN of each impact, not to whether the assumption was \
too high or too low. A positive impact increased the metric; a negative impact \
reduced it. These come apart: revenue growth below assumption builds less \
working capital and therefore ADDS cash. Read the sign in the table before \
choosing between "added" and "reduced".
- Write magnitudes, not signed numbers, after a direction word. "reduced free \
cash flow by 372.3" — never "added -372.3", which states the direction twice \
and contradicts itself once.
- Do not speculate about causes outside the table. You know what moved, not why \
the business moved it.
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


def write(backtest_result: dict) -> tuple[str, dict, dict]:
    """Returns (commentary_text, outputs_table, provenance).

    The table is returned alongside the text because verify_grounding() needs
    the exact same table the LLM was shown, not a freshly recomputed one that
    could have drifted.

    Provenance names the provider and model that produced the text. Without
    it, a stored commentary is a paragraph of prose with no way to tell which
    vendor wrote it — and "which model produced this number" is the first
    question anyone asks of generated financial text.
    """
    # Resolved here rather than at module scope: verify_grounding() is the
    # tested half of the trust layer and must import without an SDK or a key.
    from src.provider import get_provider

    outputs = _flatten_outputs(backtest_result)
    table_text = "\n".join(f"{k}: {v}" for k, v in outputs.items())
    provider = get_provider()
    # Empty config means "this provider's own default": a model id is only
    # meaningful relative to the endpoint that serves it.
    model = C.COMMENTARY_MODEL or provider.default_model
    completion = provider.complete(
        system=SYSTEM_PROMPT,
        user=f"Numbers table:\n{table_text}",
        model=model,
        # Headroom so a longer scenario (more divergent metrics) doesn't
        # truncate mid-number — a cut-off figure would fail verification and
        # look like a hallucination.
        max_tokens=450,
    )
    provenance = {"provider": provider.name, "model": model, "usage": completion.usage}
    return completion.text, outputs, provenance


def write_variance(bridge_result: dict) -> tuple[str, dict, dict]:
    """Commentary explaining a forecast-to-actual variance bridge.

    Same contract as write(): text, the exact table it was written from, and
    provenance. The verifiers that run on the result are the same ones — the
    guardrail is a property of the pipeline, not of one prompt.
    """
    from src import variance
    from src.provider import get_provider

    outputs = _flatten_outputs(variance.commentary_table(bridge_result))
    table_text = "\n".join(f"{k}: {v}" for k, v in outputs.items())
    provider = get_provider()
    model = C.COMMENTARY_MODEL or provider.default_model
    completion = provider.complete(
        system=VARIANCE_SYSTEM_PROMPT,
        user=f"Numbers table:\n{table_text}\n\n{_direction_legend(bridge_result)}",
        model=model,
        max_tokens=450,
    )
    provenance = {"provider": provider.name, "model": model, "usage": completion.usage}
    return completion.text, outputs, provenance


def _direction_legend(bridge_result: dict) -> str:
    """State each driver's direction outright instead of asking for it.

    Sign is where this prompt kept failing, and the reason is not carelessness:
    the direction of an impact contradicts intuition in exactly the case that
    matters. Revenue growth below assumption reads as bad news, and it releases
    cash, because less growth builds less working capital. A model reasoning
    from the business meaning will get that backwards however firmly the rules
    say to read the sign.

    So the pipeline states it, having already computed it. Same lesson as the
    forecast-error framing: a rule that asks a model to derive something the
    system already knows is a rule that manufactures errors.

    This is guidance, not table content — the verified table stays numeric, so
    grounding and coherence check exactly what they checked before.
    """
    metric = bridge_result["metric"].replace("_", " ")
    lines = [
        f"Direction of each driver's effect on {metric} (already determined — do not re-derive):"
    ]
    for step in bridge_result["steps"]:
        verb = "ADDED" if step["impact"] >= 0 else "REDUCED"
        lines.append(f"  {step['label']}: {verb} {abs(step['impact'])}")
    lines.append(
        "Use these verbs. State magnitudes after them, never a signed number."
    )
    return "\n".join(lines)


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
