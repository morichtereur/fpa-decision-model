"""Central config. All secrets come from the environment — nothing is hardcoded."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
FACTS = DATA / "facts"

COMPANY = "adidas AG"

# adidas doesn't disclose a price/volume bridge (checked — see
# data/raw/README.md). The real driver structure it reports is channel and
# category splits of currency-neutral growth, so that's what this models.
CHANNELS = ["Wholesale", "Direct-to-Consumer"]
CATEGORIES = ["Footwear", "Apparel", "Accessories and Gear"]
FISCAL_YEARS = [2023, 2024, 2025]

# LLM — only used for the grounded commentary layer, never for the forecast
# numbers themselves. Deliberately absent on the public deployment: preset
# commentary is served from the committed data/commentary.json, and the live
# endpoint returns a 503 rather than putting a billable key behind an open
# button.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
COMMENTARY_MODEL = os.getenv("COMMENTARY_MODEL", "claude-sonnet-5")

# Browser origins allowed to call the API. Local dev by default; the deployed
# frontend's origin is added through the environment so the host is not
# hardcoded here.
_DEFAULT_ORIGINS = "http://localhost:3000,http://localhost:3001"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _DEFAULT_ORIGINS).split(",")
    if origin.strip()
]
