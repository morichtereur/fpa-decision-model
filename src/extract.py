"""
Stage 1: pull the organic sales bridge out of the two source PDFs.

Henkel's annual reports disclose, at Group and business-unit level, a
sales-development table shaped like:

    Change versus previous year   -3.9   0.3
    Foreign exchange              -4.3  -1.8
    Adjusted for foreign exchange  0.4   2.1
    Acquisitions/divestments      -3.9  -0.4
    Organic                        4.2   2.6
    Of which price                 9.6   2.0
    Of which volume               -5.4   0.6

TODO: parse this out of data/raw/Henkel_Report_2024.pdf (FY2023/FY2024) and
data/raw/Henkel_Report_2025.pdf (FY2024/FY2025), for the Group and both
segments, and write the result to data/facts/henkel_drivers.json.

The FY2025 report's restated FY2024 comparatives do not exactly match the
FY2024 report's own FY2024 figures (see data/raw/README.md) — this needs an
explicit reconciliation decision (which 2024 baseline is "the" baseline, and
why), recorded alongside the extracted numbers rather than silently
overwritten by whichever file is parsed second.
"""

from __future__ import annotations

from src import config as C


def extract_bridge(pdf_path, anchor_text: str = "Of which price") -> list[dict]:
    """Locate sales-bridge tables in a Henkel annual report PDF.

    Returns one dict per table found: segment, fiscal years covered, and the
    nominal/FX/M&A/organic/price/volume figures.
    """
    raise NotImplementedError


def run() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    run()
