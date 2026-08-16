"""
Pre-generates management commentary for the Base case and all four named
presets, verifies grounding on each, and writes data/commentary.json.

Run once (or after any model change) with `make commentary`. The live app
serves these instantly rather than calling the LLM on every page load —
custom (non-preset) scenarios still get a live, on-demand call from the
Scenario Planner, gated behind an explicit "Generate" action, not
triggered automatically on every slider move.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from api import service
from src import config as C, drivers


def run() -> None:
    results = {}
    for scenario_id in drivers.PRESETS.keys():  # "base" is itself one of the presets
        values = service.base_driver_values() if scenario_id == "base" else service.resolve_preset(scenario_id)
        commentary = service.generate_live_commentary(values)
        results[scenario_id] = {
            **commentary,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        print(f"{scenario_id}: grounding {commentary['grounding']['grounding_rate']}")

    (C.DATA / "commentary.json").write_text(json.dumps(results, indent=2))
    print(f"Wrote {C.DATA / 'commentary.json'}")


if __name__ == "__main__":
    run()
