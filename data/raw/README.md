# Source reports

This project uses adidas AG's published annual reports, which are not
committed here (see `.gitignore`) because they are large and third-party.

Download the following two PDFs and place them in this folder:

- `Adidas_Report_2024.pdf` — FY2023 and FY2024 figures
  https://report.adidas-group.com/2024/en/_assets/downloads/annual-report-adidas-ar24.pdf
- `Adidas_Report_2025.pdf` — FY2024 and FY2025 figures
  (same pattern under https://report.adidas-group.com/2025/en/ — check the
  Downloads page there if the direct link has moved)

## Why channel/category, not price/volume

Henkel was the original candidate for this project because it discloses an
explicit quantitative price/volume/FX bridge. adidas does not — checked
directly against its FY2024 annual report before committing to it. What
adidas reports instead, consistently, is:

- currency-neutral revenue growth (isolates FX)
- growth by channel: Wholesale vs. Direct-to-Consumer (own retail + e-commerce)
- growth by category: Footwear, Apparel, Accessories and Gear
- one-off effects called out narratively (e.g. the Yeezy line's wind-down
  in 2023–2024), not quantified in a table the way Henkel quantifies M&A

No unit/pairs-sold volume metric is disclosed either, so there is no way to
separately isolate "more units" from "higher price per unit" — channel and
category growth are the finest driver split actually available. This is
itself worth stating in the README as a limitation, not smoothed over: the
model's granularity is bounded by what the company discloses, and that
bound is part of the finding.
