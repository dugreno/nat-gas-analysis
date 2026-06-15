"""Claim 01, part 2 - Was it natural gas that *raised* emissions?

CCEA's report argues Connecticut became environmentally "worse off" as it
expanded natural-gas generation, and that "electricity generation 2001-2022/4
rose by nearly 50%." This script tests the causation behind that framing using
EIA's net-generation-by-fuel record (MWh), joined to the emissions data.

It answers two questions:

  1. Did natural gas drive emissions *up*?  No. As gas displaced coal and oil,
     the carbon intensity of Connecticut's power (tons CO2 per MWh) *fell*
     sharply. A counterfactual holds the older fuel mix's intensity constant and
     shows how much CO2 the switch to gas avoided. What modestly raised total
     CO2 after 2007 was the *volume* of generation, not the fuel.

  2. Where does the "~50% increase" actually start?  2001 - a cyclical low
     (Connecticut's Millstone nuclear units were offline 1996-1999), which
     inflates the growth rate. Measured from 1990, generation rose far less.

Outputs (CSV + charts) land in ./output/. Run:
    python claims/01-emissions/analyze_generation.py
    python claims/01-emissions/analyze_generation.py --state CT --baseline 2001

If data is missing:  python scripts/download_data.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
GEN_FILE = REPO_ROOT / "data" / "raw" / "eia_annual_generation_state.xls"
EMIT_FILE = REPO_ROOT / "data" / "raw" / "eia_emission_annual.xlsx"
OUTPUT_DIR = THIS_DIR / "output"

TOTAL_SECTOR = "Total Electric Power Industry"
# Fuels we show individually; everything renewable is folded into "Renewables".
FOSSIL = ["Coal", "Petroleum", "Natural Gas"]
RENEWABLE_SOURCES = [
    "Hydroelectric Conventional",
    "Wind",
    "Solar Thermal and Photovoltaic",
    "Wood and Wood Derived Fuels",
    "Other Biomass",
    "Geothermal",
]


def load_generation() -> pd.DataFrame:
    if not GEN_FILE.exists():
        raise SystemExit(
            f"Data file not found: {GEN_FILE}\nRun:  python scripts/download_data.py"
        )
    # Row 0 is a title banner; the real header is on row 1.
    df = pd.read_excel(GEN_FILE, sheet_name=0, header=1)
    df.columns = [str(c).strip() for c in df.columns]
    return df.rename(columns={"GENERATION (Megawatthours)": "MWh"})


def load_co2(state: str) -> pd.Series:
    df = pd.read_excel(EMIT_FILE, sheet_name="State Emissions")
    df.columns = [c.replace("\n", " ").strip() for c in df.columns]
    mask = (
        (df["State"] == state)
        & (df["Producer Type"] == TOTAL_SECTOR)
        & (df["Energy Source"] == "All Sources")
    )
    return df.loc[mask].set_index("Year")["CO2 (Metric Tons)"].sort_index()


def generation_mix(df: pd.DataFrame, state: str) -> pd.DataFrame:
    """MWh by fuel for one state, with renewables aggregated; index = Year."""
    sub = df[(df["STATE"] == state) & (df["TYPE OF PRODUCER"] == TOTAL_SECTOR)]
    piv = sub.pivot_table(
        index="YEAR", columns="ENERGY SOURCE", values="MWh", aggfunc="sum"
    ).fillna(0.0)
    out = pd.DataFrame(index=piv.index)
    for f in FOSSIL + ["Nuclear"]:
        out[f] = piv[f] if f in piv.columns else 0.0
    out["Renewables"] = piv[[c for c in RENEWABLE_SOURCES if c in piv.columns]].sum(axis=1)
    out["Total"] = piv["Total"] if "Total" in piv.columns else out.sum(axis=1)
    return out


def pct(old: float, new: float) -> float:
    return float("nan") if old == 0 else (new - old) / old * 100.0


def plot_generation_mix(mix: pd.DataFrame, state: str) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    order = ["Coal", "Petroleum", "Natural Gas", "Nuclear", "Renewables"]
    colors = {
        "Coal": "#4d4d4d",
        "Petroleum": "#b5651d",
        "Natural Gas": "#2c7fb8",
        "Nuclear": "#762a83",
        "Renewables": "#1a9850",
    }
    ax.stackplot(
        mix.index,
        *[mix[f] / 1e6 for f in order],
        labels=order,
        colors=[colors[f] for f in order],
        alpha=0.9,
    )
    ax.set_title(
        f"{state} net electricity generation by fuel (million MWh)\n"
        "Source: EIA, Net Generation by State",
        fontsize=11,
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("Generation (million MWh)")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = OUTPUT_DIR / f"{state}_generation_mix.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def plot_intensity_and_counterfactual(
    mix: pd.DataFrame, co2: pd.Series, state: str, baseline: int
) -> Path:
    """Top: CO2 intensity (t/MWh). Bottom: actual CO2 vs. a frozen-fuel-mix line."""
    years = [y for y in mix.index if y in co2.index]
    total = mix.loc[years, "Total"]
    actual = co2.loc[years]
    intensity = actual / total
    base_intensity = co2[baseline] / mix.loc[baseline, "Total"]
    counterfactual = total * base_intensity  # same output, frozen older intensity

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 8), sharex=True)

    ax1.plot(years, intensity, color="#1f4e79", linewidth=2)
    ax1.set_ylabel("CO2 intensity\n(t per MWh)")
    ax1.set_title(
        f"{state}: as gas displaced coal & oil, CO2 per MWh fell\n"
        "Sources: EIA emissions + net generation",
        fontsize=11,
    )
    ax1.grid(True, alpha=0.3)

    ax2.plot(years, actual / 1e6, color="#1f4e79", linewidth=2, label="Actual CO2")
    ax2.plot(
        years,
        counterfactual / 1e6,
        color="#c44",
        linestyle="--",
        linewidth=2,
        label=f"If {baseline} fuel mix held (same MWh)",
    )
    ax2.fill_between(
        years, actual / 1e6, counterfactual / 1e6, color="#c44", alpha=0.12
    )
    ax2.set_ylabel("CO2 (million t)")
    ax2.set_xlabel("Year")
    ax2.legend(loc="upper right", fontsize=9)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    path = OUTPUT_DIR / f"{state}_co2_intensity_counterfactual.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", default="CT", help="State code (default: CT).")
    parser.add_argument(
        "--baseline",
        type=int,
        default=2001,
        help="Reference year for the counterfactual and growth (default: 2001, "
        "the start of CCEA's '~50%% increase' window).",
    )
    args = parser.parse_args()
    state = args.state.upper()
    baseline = args.baseline

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    gen = load_generation()
    mix = generation_mix(gen, state)
    co2 = load_co2(state)

    total = mix["Total"]
    first_year, latest = int(total.index.min()), int(total.index.max())

    print(f"\n{'='*72}\nClaim 01b - did natural gas raise emissions, & where does '~50%%' start?\n{'='*72}")
    print(f"State: {state}   |   Range: {first_year}-{latest}\n")

    # --- Where does the "~50%" start? -----------------------------------------
    print("-- Generation growth depends entirely on the start year --")
    for y0 in [first_year, 2000, baseline, 2007, 2012]:
        if y0 in total.index:
            print(f"  {y0} -> {latest}: {pct(total[y0], total[latest]):+6.1f}%   "
                  f"({int(total[y0]):,} -> {int(total[latest]):,} MWh)")
    print(f"  NOTE: {baseline} is a cyclical low (CT's Millstone nuclear units "
          f"were offline 1996-1999).")

    # --- Fuel mix shift -------------------------------------------------------
    print("\n-- Generation mix (% of total) --")
    cols = ["Coal", "Petroleum", "Natural Gas", "Nuclear", "Renewables"]
    print("  Year  " + "".join(f"{c[:8]:>10}" for c in cols))
    for y in [first_year, baseline, 2007, 2012, latest]:
        if y in mix.index:
            shares = "".join(f"{mix.loc[y, c]/total[y]*100:>9.1f}%" for c in cols)
            print(f"  {y} {shares}")

    # --- Causation: intensity + counterfactual --------------------------------
    base_int = co2[baseline] / total[baseline]
    latest_int = co2[latest] / total[latest]
    cf = total[latest] * base_int
    print("\n-- Did gas raise emissions? CO2 per MWh tells the story --")
    print(f"  CO2 intensity {baseline}: {base_int:.4f} t/MWh")
    print(f"  CO2 intensity {latest}: {latest_int:.4f} t/MWh   ({pct(base_int, latest_int):+.1f}%)")
    print(f"  Counterfactual: {latest} output ({int(total[latest]):,} MWh) at the "
          f"{baseline} fuel mix\n    would have emitted {cf/1e6:.2f}M t CO2 vs "
          f"actual {co2[latest]/1e6:.2f}M t")
    print(f"  -> the switch to gas AVOIDED ~{(cf-co2[latest])/1e6:.2f}M t CO2 in "
          f"{latest} alone (plus the SO2/NOx collapse).")

    # --- Outputs --------------------------------------------------------------
    mix.to_csv(OUTPUT_DIR / f"{state}_generation_mix.csv")
    mix_png = plot_generation_mix(mix, state)
    cf_png = plot_intensity_and_counterfactual(mix, co2, state, baseline)
    print(f"\nWrote: {mix_png.name}, {cf_png.name}, {state}_generation_mix.csv")


if __name__ == "__main__":
    main()
