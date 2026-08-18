"""
Pre-generates management commentary for the Base case and all four named
presets, verifies it, and writes data/commentary.json.

Run once (or after any model or prompt change) with `make commentary`. The
live app serves these instantly rather than calling the LLM on every page
load — custom (non-preset) scenarios still get a live, on-demand call from the
Scenario Planner, gated behind an explicit "Generate" action, not triggered
automatically on every slider move.

**This is a gate, not a report.** Two checks run on every paragraph: grounding
(is each number in the output table?) and coherence (is it used to say
something the table supports?). If any paragraph fails either, nothing is
written and the command exits non-zero. The previous version printed a
grounding rate and wrote the file regardless, which is how five paragraphs
carrying seven false statements came to be committed with a perfect score
next to each of them.

`--allow-findings` writes anyway, for inspecting what a prompt change did
before deciding whether it is an improvement. It is deliberately not the
default.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from datetime import datetime, timezone

from api import service
from src import config as C, drivers


def _jobs() -> list[tuple[str, Callable[[], dict]]]:
    """Every paragraph to generate, as (key, producer).

    Presets describe what the numbers were; the variance entry says which
    assumption was responsible for the miss. Both go through the same two
    checks and the same gate — a second kind of commentary must not come with
    a second, weaker standard.
    """
    jobs: list[tuple[str, Callable[[], dict]]] = []
    for scenario_id in drivers.PRESETS:  # "base" is itself one of the presets
        # "base" is the driver-based forecast itself; every other preset is a
        # scenario and is labelled as one, so the commentary does not describe
        # a stress case as the driver-based model.
        series_name = "driver_based" if scenario_id == "base" else scenario_id
        values = (
            service.base_driver_values()
            if scenario_id == "base"
            else service.resolve_preset(scenario_id)
        )
        jobs.append(
            (
                scenario_id,
                lambda v=values, s=series_name: service.generate_live_commentary(v, series_name=s),
            )
        )
    jobs.append(("variance", service.generate_variance_commentary))
    return jobs


def _accepted(paragraph: dict) -> bool:
    return paragraph["coherence"]["clean"] and paragraph["grounding"]["grounding_rate"] == 1.0


def run(allow_findings: bool = False, attempts: int = 3) -> int:
    """Generate every paragraph, resampling the ones that fail verification.

    Resampling is per paragraph, not per run. Generation is sampled, so a
    paragraph fails occasionally on its own — measured at roughly one in six
    against the current model, almost always a single ungrounded figure. With
    six paragraphs and one shared verdict, re-rolling all of them on any single
    failure rarely converges and throws away five good paragraphs each time.

    The gate does not soften: a paragraph still has to pass both checks
    outright. It just gets a bounded number of tries to do so, and the count is
    reported, because "clean on the third attempt" is a different quality
    signal from "clean first time".
    """
    results = {}
    failed: list[str] = []

    for key, produce in _jobs():
        paragraph = None
        for attempt in range(1, attempts + 1):
            paragraph = produce()
            if _accepted(paragraph):
                break

        assert paragraph is not None
        paragraph["attempts"] = attempt
        results[key] = {**paragraph, "generated_at": datetime.now(timezone.utc).isoformat()}

        grounding = paragraph["grounding"]["grounding_rate"]
        coherence = paragraph["coherence"]
        status = "ok" if _accepted(paragraph) else "REJECTED"
        suffix = f"  (attempt {attempt} of {attempts})" if attempt > 1 else ""
        print(
            f"{key:20s} grounding {grounding}  "
            f"coherence {coherence['finding_count']} finding(s)  {status}{suffix}"
        )
        for finding in coherence["findings"]:
            print(f"    [{finding['kind']}] {finding['detail']}")
            print(f"      in: {finding['sentence']}")
        if status == "REJECTED":
            failed.append(key)

    if failed and not allow_findings:
        print(
            f"\nRejected {len(failed)} of {len(results)} paragraph(s): {', '.join(failed)}.\n"
            f"Nothing written, after {attempts} attempt(s) each. Adjust the prompt in "
            "src/commentary.py, raise --attempts, or pass --allow-findings to write anyway "
            "and inspect the output."
        )
        return 1

    (C.DATA / "commentary.json").write_text(json.dumps(results, indent=2))
    print(f"\nWrote {C.DATA / 'commentary.json'}")
    if failed:
        print(f"WARNING: written with findings in {', '.join(failed)} (--allow-findings).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="generate_commentary",
        description="Generate and verify the preset management commentary.",
    )
    parser.add_argument(
        "--allow-findings",
        action="store_true",
        help="Write the file even if a paragraph fails verification.",
    )
    parser.add_argument(
        "--attempts",
        type=int,
        default=3,
        help="How many times to resample a paragraph that fails verification.",
    )
    args = parser.parse_args()
    return run(allow_findings=args.allow_findings, attempts=args.attempts)


if __name__ == "__main__":
    raise SystemExit(main())
