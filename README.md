# Natural Gas Claims Analysis

A line-by-line, data-driven review of the claims about natural gas published by
**Fred Carstensen and the Connecticut Center for Economic Analysis (CCEA)**.

Each claim is examined against primary-source data (EIA, EPA, ISO-NE, etc.).
Every figure cited here is reproducible: the code that downloads the source
data and produces the numbers and charts lives in this repository, so anyone
can re-run it and check the result.

> **CCEA report under review:** *How Did We Get Here?*
> [[PDF]](https://www.conservationeducation.org/uploads/6/2/0/1/6201942/how_did_we_get_here_-_ccea_report.pdf)
>
> **Companion article:** "Natural Gas Does Not Make Electricity More Expensive,"
> published on the CBIA website
> [[link]](https://www.cbia.com/news/issues-policies/natural-gas-does-not-make-electricity-more-expensive).

## Why this exists

Energy policy debates should turn on the actual numbers. CCEA's natural-gas
analysis makes a series of empirical claims — about emissions, costs,
reliability, and economic impact. This repo takes them one at a time, quotes the
claim exactly, identifies the relevant primary data, and shows what that data
says. Where a claim holds up, it says so; where it doesn't, it shows why.

## Claims

| # | Claim (as stated by CCEA) | Status | Analysis |
|---|---------------------------|--------|----------|
| 01 | Connecticut is "worse off because of the environmental impact" of gas generation | Not supported — power-sector CO₂ −13%, NOx −77%, SO₂ −99% since 2000 even as generation rose ~50% | [`claims/01-emissions/`](claims/01-emissions/) |

_(More claims to be added.)_

## Repository layout

```
nat-gas-analysis/
├── README.md                     # this file
├── requirements.txt              # Python dependencies
├── scripts/
│   └── download_data.py          # fetches raw source data into data/raw/
├── data/
│   └── raw/                      # downloaded source files (git-ignored)
└── claims/
    └── 01-emissions/
        ├── README.md             # the written analysis of claim 01
        ├── analyze_emissions.py  # the code behind the numbers
        └── output/               # generated tables + charts
```

## Reproducing the analysis

```bash
# 1. install dependencies (a virtualenv is recommended)
pip install -r requirements.txt

# 2. download the primary-source data
python scripts/download_data.py

# 3. run a claim's analysis (writes tables + charts to its output/ folder)
python claims/01-emissions/analyze_emissions.py
```

Raw data files are intentionally git-ignored; re-running `download_data.py`
always pulls the current version straight from the source agency, so the
analysis stays anchored to the official record rather than a stale copy.

## Sources

- **EIA — Emissions by State by Year** (CO₂, SO₂, NOx from the electric power
  sector): <https://www.eia.gov/electricity/data/state/emission_annual.xlsx>

## Methodology notes

- Claims are quoted verbatim before they are evaluated.
- Each analysis names its primary source, its scope (e.g., *electric power
  sector*, not economy-wide), and its baseline year, because conclusions can
  hinge on all three.
- The goal is an honest reading of the data, including any nuance that cuts
  against the conclusion — not a one-sided rebuttal.
