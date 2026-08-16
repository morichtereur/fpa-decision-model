"""Central config. All secrets come from the environment — nothing is hardcoded."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
FACTS = DATA / "facts"
DB_PATH = DATA / "fpa.duckdb"

COMPANY = "adidas AG"

# adidas doesn't disclose a price/volume bridge (checked — see
# data/raw/README.md). The real driver structure it reports is channel and
# category splits of currency-neutral growth, so that's what this models.
CHANNELS = ["Wholesale", "Direct-to-Consumer"]
CATEGORIES = ["Footwear", "Apparel", "Accessories and Gear"]
FISCAL_YEARS = [2023, 2024, 2025]

# LLM — only used for the grounded commentary layer, never for the forecast
# numbers themselves.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
COMMENTARY_MODEL = os.getenv("COMMENTARY_MODEL", "claude-sonnet-5")
