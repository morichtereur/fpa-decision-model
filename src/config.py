"""Central config. All secrets come from the environment — nothing is hardcoded."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
FACTS = DATA / "facts"
DB_PATH = DATA / "fpa.duckdb"

COMPANY = "Henkel AG & Co. KGaA"
SEGMENTS = ["Adhesive Technologies", "Consumer Brands"]
FISCAL_YEARS = [2023, 2024, 2025]

# LLM — only used for the grounded commentary layer, never for the forecast
# numbers themselves.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
COMMENTARY_MODEL = os.getenv("COMMENTARY_MODEL", "claude-sonnet-5")
