"""Download the raw source datasets used in the natural-gas claims analysis.

Each entry in SOURCES records the canonical upstream URL, the local path we
save it to, and a short note on what claim it supports. Re-run this script to
refresh the data; downloaded files live in data/raw/ and are git-ignored so the
repository stays small and the analysis stays reproducible from the original
source.

Usage:
    python scripts/download_data.py            # download everything
    python scripts/download_data.py emissions  # download a single source by key
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

# Resolve paths relative to the repo root, not the caller's cwd.
REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"

SOURCES = {
    # EIA "Emissions by State by Year" — CO2, SO2, and NOx from the electric
    # power sector, broken out by state, producer type, and fuel, 1990-present.
    # Supports claim 01 (power-sector emissions).
    "emissions": {
        "url": "https://www.eia.gov/electricity/data/state/emission_annual.xlsx",
        "filename": "eia_emission_annual.xlsx",
        "note": "EIA State Electric Power Sector Emissions (CO2/SO2/NOx), 1990-present",
    },
    # EIA "Net Generation by State by Type of Producer by Energy Source" — the
    # electricity actually generated (MWh), broken out by fuel, 1990-present.
    # Lets us test *why* emissions moved (fuel switch vs. output growth) and
    # check CCEA's "generation rose ~50%" claim against the actual series.
    # Legacy .xls; reading it requires xlrd (see requirements.txt).
    "generation": {
        "url": "https://www.eia.gov/electricity/data/state/annual_generation_state.xls",
        "filename": "eia_annual_generation_state.xls",
        "note": "EIA State Net Generation by fuel (MWh), 1990-present",
    },
    # EIA bulk electricity archive — every published electricity series as JSON
    # (one object per line). We use it for the average retail price of
    # electricity by state and sector (series ELEC.PRICE.<ST>-ALL.A), because the
    # standalone state price file (avgprice_annual.xlsx) was frozen at 2020 while
    # this archive stays current through the latest annual release. No API key is
    # required. Supports claim 03 (rates). Large (~240 MB); claim 03's analysis
    # extracts just the price series into a small cache the first time it runs.
    "retail_price": {
        "url": "https://api.eia.gov/bulk/ELEC.zip",
        "filename": "EIA_ELEC.zip",
        "note": "EIA bulk electricity archive (retail price by state), current",
    },
    # EIA "Average Price by State by Provider" — the only state-level source that
    # splits price by provider category (Full-Service / Energy-Only / Delivery-
    # Only), which lets claim 03 separate the supply charge from the delivery
    # charge. EIA froze this file at 2020; we use it only for the provider-
    # category split (the current ELEC.zip lacks it). Supports claim 03 (rates).
    "delivery_price": {
        "url": "https://www.eia.gov/electricity/data/state/avgprice_annual.xlsx",
        "filename": "eia_avgprice_annual.xlsx",
        "note": "EIA state avg price by provider category (delivery-only), 1990-2020",
    },
}


def download(key: str) -> Path:
    src = SOURCES[key]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = RAW_DIR / src["filename"]
    print(f"[{key}] {src['note']}")
    print(f"  GET  {src['url']}")
    # A User-Agent header avoids the occasional 403 from eia.gov on bare requests.
    req = urllib.request.Request(src["url"], headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(dest, "wb") as fh:
        fh.write(resp.read())
    print(f"  SAVE {dest}  ({dest.stat().st_size:,} bytes)\n")
    return dest


def main(argv: list[str]) -> int:
    keys = argv[1:] or list(SOURCES)
    unknown = [k for k in keys if k not in SOURCES]
    if unknown:
        print(f"Unknown source(s): {', '.join(unknown)}")
        print(f"Available: {', '.join(SOURCES)}")
        return 1
    for key in keys:
        download(key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
