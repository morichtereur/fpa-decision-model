# Source reports

This project uses Henkel AG & Co. KGaA's published annual reports, which are
not committed here (see `.gitignore`) because they are large and third-party.

Download the following two PDFs from Henkel's investor relations site and
place them in this folder:

- `Henkel_Report_2024.pdf` — FY2023 and FY2024 figures
- `Henkel_Report_2025.pdf` — FY2024 and FY2025 figures

Together they give three consecutive fiscal years (2023–2025) of the
Group and business-unit (Adhesive Technologies, Consumer Brands) organic
sales bridge: nominal growth, FX effect, acquisitions/divestments, organic
growth, and its price/volume split.

**Known data-quality wrinkle:** the FY2024 comparative figures restated in
the FY2025 report do not exactly match what the FY2024 report originally
disclosed for FY2024 (Henkel appears to have adjusted segment definitions
between the two filings). The extraction step needs to reconcile this
explicitly rather than silently pick one version — which numbers are used
for the 2024 baseline, and why, should be a visible decision, not a default.
