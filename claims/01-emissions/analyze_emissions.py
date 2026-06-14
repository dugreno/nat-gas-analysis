"""Claim 01 - "Emissions are up."

This script tests that claim against the U.S. Energy Information
Administration's official record of electric-power-sector emissions
(CO2, SO2, NOx) by state, fuel, and year (1990-present).

What it does:
  1. Loads the EIA "Emissions by State" workbook from data/raw/.
  2. Builds the emissions time series for a chosen state (default: Connecticut,
     the focus of CCEA's analysis) plus the U.S. total for context.
  3. Reports, for each pollutant: the 1990 baseline, the all-time peak, the
     latest year, and the percent change across each.
  4. Breaks the CO2 trend down by fuel to show the coal/oil -> natural gas
     fuel switch that drove the criteria-pollutant collapse.
  5. Writes machine-readable CSVs, a Markdown summary table, and charts to
     ./output/ so the findings are fully reproducible.

Run from anywhere:
    python claims/01-emissions/analyze_emissions.py
    python claims/01-emissions/analyze_emissions.py --state MA

If the data file is missing, first run:  python scripts/download_data.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: write image files, never open a window
import matplotlib.pyplot as plt
import pandas as pd

# --- Paths --------------------------------------------------------------------
THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
DATA_FILE = REPO_ROOT / "data" / "raw" / "eia_emission_annual.xlsx"
OUTPUT_DIR = THIS_DIR / "output"

# --- Constants describing the EIA schema --------------------------------------
SHEET = "State Emissions"
# We want the whole power sector, not a single producer category, and the
# fuel-aggregated row when we look at totals.
TOTAL_SECTOR = "Total Electric Power Industry"
ALL_FUELS = "All Sources"
# EIA reports these three pollutants; column names contain embedded newlines.
POLLUTANTS = {
    "CO2 (Metric Tons)": "CO2",
    "SO2 (Metric Tons)": "SO2",
    "NOx (Metric Tons)": "NOx",
}
# The fossil fuels whose CO2 we break out to tell the fuel-switching story.
FOSSIL_FUELS = ["Coal", "Petroleum", "Natural Gas"]


def load_data() -> pd.DataFrame:
    """Load and tidy the EIA workbook (normalizing the newline-laden headers)."""
    if not DATA_FILE.exists():
        raise SystemExit(
            f"Data file not found: {DATA_FILE}\n"
            "Run:  python scripts/download_data.py"
        )
    df = pd.read_excel(DATA_FILE, sheet_name=SHEET)
    df.columns = [str(c).replace("\n", " ").strip() for c in df.columns]
    return df


def sector_totals(df: pd.DataFrame, state: str) -> pd.DataFrame:
    """Whole-power-sector, all-fuels emissions time series for one state."""
    mask = (
        (df["State"] == state)
        & (df["Producer Type"] == TOTAL_SECTOR)
        & (df["Energy Source"] == ALL_FUELS)
    )
    out = df.loc[mask, ["Year", *POLLUTANTS]].sort_values("Year").set_index("Year")
    return out.rename(columns=POLLUTANTS)


def co2_by_fuel(df: pd.DataFrame, state: str) -> pd.DataFrame:
    """CO2 by fossil fuel (Coal / Petroleum / Natural Gas) for one state."""
    mask = (
        (df["State"] == state)
        & (df["Producer Type"] == TOTAL_SECTOR)
        & (df["Energy Source"].isin(FOSSIL_FUELS))
    )
    piv = df.loc[mask].pivot_table(
        index="Year", columns="Energy Source", values="CO2 (Metric Tons)", aggfunc="sum"
    )
    # Stable, intuitive column order; fill gaps (a fuel may drop to zero).
    return piv.reindex(columns=FOSSIL_FUELS).fillna(0.0)


def pct(old: float, new: float) -> float:
    return float("nan") if old == 0 else (new - old) / old * 100.0


def summarize(series: pd.DataFrame, label: str) -> pd.DataFrame:
    """Per-pollutant baseline/peak/latest summary for a totals time series.

    Column names are fixed (not f-strings of the year) so summaries for
    different regions/pollutants concatenate cleanly into one table.
    """
    rows = []
    base_year, latest_year = int(series.index.min()), int(series.index.max())
    for pol in series.columns:
        s = series[pol]
        base, latest = s.loc[base_year], s.loc[latest_year]
        peak_year = int(s.idxmax())
        peak = s.loc[peak_year]
        rows.append(
            {
                "Region": label,
                "Pollutant": pol,
                "Baseline Year": base_year,
                "Baseline": round(base),
                "Peak Year": peak_year,
                "Peak": round(peak),
                "Latest Year": latest_year,
                "Latest": round(latest),
                "% chg vs baseline": round(pct(base, latest), 1),
                "% chg vs peak": round(pct(peak, latest), 1),
            }
        )
    return pd.DataFrame(rows)


def to_markdown_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a GitHub-flavored Markdown table (no extra deps)."""
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    divider = "| " + " | ".join("---" for _ in cols) + " |"
    lines = [header, divider]
    for _, row in df.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            # Thousands separators for counts, but not for year columns.
            if isinstance(v, int) and "Year" not in c:
                cells.append(f"{v:,}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def plot_pollutant_trends(series: pd.DataFrame, state: str) -> Path:
    """Three stacked panels: CO2, SO2, NOx over time, each indexed to 1990=100."""
    fig, axes = plt.subplots(3, 1, figsize=(9, 10), sharex=True)
    base_year = series.index.min()
    for ax, pol in zip(axes, ["CO2", "SO2", "NOx"]):
        s = series[pol]
        indexed = s / s.loc[base_year] * 100.0
        ax.plot(s.index, indexed, color="#1f4e79", linewidth=2)
        ax.axhline(100, color="#999", linestyle="--", linewidth=1)
        ax.set_ylabel(f"{pol}\n({base_year} = 100)")
        ax.grid(True, alpha=0.3)
        latest_year = s.index.max()
        ax.annotate(
            f"{indexed.loc[latest_year]:.0f}",
            xy=(latest_year, indexed.loc[latest_year]),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            fontsize=9,
            color="#1f4e79",
        )
    axes[0].set_title(
        f"{state} electric-power-sector emissions, indexed to {base_year}=100\n"
        "Source: EIA, Emissions by State by Year",
        fontsize=11,
    )
    axes[-1].set_xlabel("Year")
    fig.tight_layout()
    path = OUTPUT_DIR / f"{state}_pollutant_trends.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def plot_co2_fuel_mix(fuel: pd.DataFrame, state: str) -> Path:
    """Stacked area of CO2 by fuel: the coal/oil -> gas switch over time."""
    fig, ax = plt.subplots(figsize=(9, 5.5))
    colors = {"Coal": "#4d4d4d", "Petroleum": "#b5651d", "Natural Gas": "#2c7fb8"}
    ax.stackplot(
        fuel.index,
        *[fuel[f] / 1e6 for f in FOSSIL_FUELS],
        labels=FOSSIL_FUELS,
        colors=[colors[f] for f in FOSSIL_FUELS],
        alpha=0.9,
    )
    ax.set_title(
        f"{state} power-sector CO2 by fuel (million metric tons)\n"
        "Source: EIA, Emissions by State by Year",
        fontsize=11,
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("CO2 (million metric tons)")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = OUTPUT_DIR / f"{state}_co2_fuel_mix.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state",
        default="CT",
        help="Two-letter state code to analyze (default: CT). Use US-TOTAL for the nation.",
    )
    args = parser.parse_args()
    state = args.state.upper()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()

    valid_states = set(df["State"].unique())
    if state not in valid_states:
        raise SystemExit(f"Unknown state '{state}'. Options: {sorted(valid_states)}")

    state_totals = sector_totals(df, state)
    us_totals = sector_totals(df, "US-TOTAL")
    fuel = co2_by_fuel(df, state)

    # Console report -----------------------------------------------------------
    base_year, latest_year = state_totals.index.min(), state_totals.index.max()
    print(f"\n{'='*70}\nClaim 01 - 'Emissions are up'\n{'='*70}")
    print(f"State: {state}   |   Range: {base_year}-{latest_year}")
    print(f"Source: EIA, Emissions by State by Year ({DATA_FILE.name})\n")

    summary = pd.concat(
        [summarize(state_totals, state), summarize(us_totals, "US-TOTAL")],
        ignore_index=True,
    )
    print(summary.to_string(index=False))

    co2 = state_totals["CO2"]
    print(f"\n-- Fuel switch ({state}, CO2 in metric tons) --")
    for yr in [base_year, latest_year]:
        row = {f: int(fuel.loc[yr, f]) for f in FOSSIL_FUELS}
        print(f"  {yr}: {row}")
    print(
        f"\n  CO2:  {int(co2.loc[base_year]):,} -> {int(co2.loc[latest_year]):,} t "
        f"({pct(co2.loc[base_year], co2.loc[latest_year]):+.1f}% vs {base_year}; "
        f"{pct(co2.max(), co2.loc[latest_year]):+.1f}% vs peak {co2.idxmax()})"
    )
    for pol in ["SO2", "NOx"]:
        s = state_totals[pol]
        print(
            f"  {pol}:  {int(s.loc[base_year]):,} -> {int(s.loc[latest_year]):,} t "
            f"({pct(s.loc[base_year], s.loc[latest_year]):+.1f}% vs {base_year})"
        )

    # File outputs -------------------------------------------------------------
    state_totals.to_csv(OUTPUT_DIR / f"{state}_sector_totals.csv")
    fuel.to_csv(OUTPUT_DIR / f"{state}_co2_by_fuel.csv")
    summary.to_csv(OUTPUT_DIR / "summary_table.csv", index=False)
    with open(OUTPUT_DIR / "summary_table.md", "w") as fh:
        fh.write(f"# Claim 01 - Emissions ({state}) - EIA data\n\n")
        fh.write(to_markdown_table(summary))
        fh.write("\n")

    trends_png = plot_pollutant_trends(state_totals, state)
    mix_png = plot_co2_fuel_mix(fuel, state)

    print(f"\nWrote outputs to {OUTPUT_DIR}/")
    for p in [
        f"{state}_sector_totals.csv",
        f"{state}_co2_by_fuel.csv",
        "summary_table.csv",
        "summary_table.md",
        trends_png.name,
        mix_png.name,
    ]:
        print(f"  - {p}")


if __name__ == "__main__":
    main()
