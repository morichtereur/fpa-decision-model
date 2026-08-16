"""
Stage 1: pull the currency-neutral growth breakdown out of the two source
PDFs.

adidas doesn't disclose a price/volume bridge (see data/raw/README.md for
how that was checked before this design was picked). What it discloses,
consistently, is currency-neutral revenue growth broken down by:

    - channel: Wholesale, Direct-to-Consumer
    - category: Footwear, Apparel, Accessories and Gear

plus narrative call-outs for one-off effects (e.g. the Yeezy wind-down)
that aren't quantified in a table the way Henkel quantifies
acquisitions/divestments.

TODO: parse this out of data/raw/Adidas_Report_2024.pdf (FY2023/FY2024) and
data/raw/Adidas_Report_2025.pdf (FY2024/FY2025), by channel and category,
and write the result to data/facts/adidas_drivers.json.

Since there's no numeric FX or one-off effect to subtract out cleanly, the
extraction needs to record reported (nominal) growth AND currency-neutral
growth side by side, and treat the gap between them as the FX effect —
rather than pretending a precision the disclosure doesn't support.
"""

from __future__ import annotations

from src import config as C


def extract_growth_breakdown(pdf_path) -> list[dict]:
    """Locate the channel/category currency-neutral growth figures in an
    adidas annual report PDF.

    Returns one dict per breakdown found: dimension (channel/category),
    value (e.g. "Wholesale"), fiscal year, reported growth, currency-neutral
    growth.
    """
    raise NotImplementedError


def run() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    run()
