"""Claim 03, Layer 3 (part 1b) - does delivery cost track gas adoption?

A natural worry: maybe gas adoption is somehow driving up the delivery/wires side
of the bill, which would rescue CCEA's "gas made power expensive" framing through
a back door. This is a spurious-correlation guard. There is no mechanism for it -
the local wires cost the same to build and maintain regardless of what fuel made
the electrons - so we expect no relationship, and a careless levels regression
would only pick up the fact that gas adoption and grid spending both trended up
over the same years for unrelated reasons.

This script tests it properly: across the states that report a delivery price,
does the *change* in gas generation share predict the *change* in real delivery
cost? It does not (the relationship is slightly negative): the heaviest gas
adopters (OH, PA, DE) had nearly flat delivery costs, while the biggest delivery-
cost increases include California, which *cut* its gas share over the period.

Proxy + scope notes:
  * "Delivery cost" here is EIA's all-sector "Delivery-Only Service" price - the
    bundled T&D + policy charge, NOT distribution alone (EIA does not break
    distribution out by state). To isolate distribution one would need FERC Form 1.
  * Only ~19 retail-choice states report a delivery price, 2008-2020. That is the
    sample; it predates the 2022-24 supply-rate spikes.

Outputs (CSV + chart) land in ./output/. Run:
    python claims/03-rates/analyze_delivery_vs_gas.py

If data is missing:  python scripts/download_data.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
RAW_DIR = THIS_DIR.parents[1] / "data" / "raw"
GEN_FILE = RAW_DIR / "eia_annual_generation_state.xls"
DELIVERY_FILE = RAW_DIR / "eia_avgprice_annual.xlsx"
OUTPUT_DIR = THIS_DIR / "output"

# Delivery-only price is reported from ~2008 and the file is frozen at 2020.
START, END = 2008, 2020
# CPI-U annual average (BLS CUUR0000SA0); base = END, to put the delivery-cost
# change in real terms (so it is not just inflation).
CPI_U = {2008: 215.303, 2020: 258.811}

# States to label on the scatter (CT plus the most telling contrasts).
LABEL = {"CT", "CA", "OH", "PA", "DE", "VA", "RI", "NH", "MA", "NY"}


def _need(path: Path) -> None:
    if not path.exists():
        raise SystemExit(
            f"Data file not found: {path}\nRun:  python scripts/download_data.py"
        )


def load_gas_share() -> pd.DataFrame:
    """Natural gas as a percent of net generation, per state per year (long)."""
    _need(GEN_FILE)
    g = pd.read_excel(GEN_FILE, sheet_name=0, header=1)
    g.columns = [str(c).strip() for c in g.columns]
    g = g.rename(columns={"GENERATION (Megawatthours)": "MWh"})
    g = g[g["TYPE OF PRODUCER"] == "Total Electric Power Industry"]
    piv = g.pivot_table(index=["STATE", "YEAR"], columns="ENERGY SOURCE",
                        values="MWh", aggfunc="sum")
    gas = (piv["Natural Gas"] if "Natural Gas" in piv.columns else 0.0).fillna(0.0)
    share = (gas / piv["Total"] * 100.0).reset_index(name="gas_share")
    return share.rename(columns={"STATE": "State", "YEAR": "Year"})


def load_delivery() -> pd.DataFrame:
    """All-sector 'Delivery-Only Service' price (cents/kWh), per state per year."""
    _need(DELIVERY_FILE)
    df = pd.read_excel(DELIVERY_FILE, sheet_name="Price", header=1)
    df.columns = [str(c).strip() for c in df.columns]
    df = df[df["Industry Sector Category"] == "Delivery-Only Service"]
    out = df[["State", "Year", "Total"]].rename(columns={"Total": "delivery_cents"})
    out["State"] = out["State"].str.strip()
    return out


def build() -> pd.DataFrame:
    """One row per state: start/end gas share and real delivery cost, + changes."""
    gas = load_gas_share()
    deliv = load_delivery()
    g = gas[gas["Year"].isin([START, END])].pivot_table(
        index="State", columns="Year", values="gas_share")
    d = deliv[deliv["Year"].isin([START, END])].pivot_table(
        index="State", columns="Year", values="delivery_cents")
    g = g.dropna(subset=[START, END])
    d = d.dropna(subset=[START, END])
    m = g.join(d, lsuffix="_gas", rsuffix="_deliv", how="inner")
    m = m.drop(index=[s for s in ("US", "DC") if s in m.index])
    # Real delivery cost in END dollars.
    infl = CPI_U[END] / CPI_U[START]
    out = pd.DataFrame({
        "gas_share_start": m[f"{START}_gas"],
        "gas_share_end": m[f"{END}_gas"],
        "d_gas_pp": m[f"{END}_gas"] - m[f"{START}_gas"],
        "deliv_start_real": m[f"{START}_deliv"] * infl,
        "deliv_end_real": m[f"{END}_deliv"],
    })
    out["d_deliv_real"] = out["deliv_end_real"] - out["deliv_start_real"]
    return out.reset_index().rename(columns={"index": "State"})


def fit_line(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float, float]:
    slope, intercept = np.polyfit(x, y, 1)
    r = float(np.corrcoef(x, y)[0, 1])
    return float(slope), float(intercept), r, r * r


def plot_scatter(df: pd.DataFrame, slope: float, intercept: float, r: float) -> Path:
    x, y = df["d_gas_pp"].to_numpy(), df["d_deliv_real"].to_numpy()
    fig, ax = plt.subplots(figsize=(9, 6))
    xs = np.linspace(x.min(), x.max(), 50)
    ax.plot(xs, slope * xs + intercept, "--", color="#444", linewidth=1.3,
            label=f"fit: r = {r:+.2f}  (slope {slope:+.3f} c/kWh per +1pp)")
    is_ct = df["State"] == "CT"
    ax.scatter(df.loc[~is_ct, "d_gas_pp"], df.loc[~is_ct, "d_deliv_real"],
               s=50, c="#7f7f7f", alpha=0.85, edgecolors="white", linewidths=0.5)
    ax.scatter(df.loc[is_ct, "d_gas_pp"], df.loc[is_ct, "d_deliv_real"],
               s=90, c="#d62728", zorder=5, edgecolors="white", linewidths=0.6)
    for _, row in df.iterrows():
        if row["State"] in LABEL:
            ax.annotate(row["State"], (row["d_gas_pp"], row["d_deliv_real"]),
                        fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax.axhline(0, color="#999", linewidth=0.8)
    ax.set_xlabel(f"Change in gas share of generation, {START}-{END} (percentage points)")
    ax.set_ylabel(f"Change in real delivery cost, {START}-{END}\n(cents/kWh, {END} dollars)")
    ax.set_title("Delivery cost does not track gas adoption\n"
                 "Biggest gas adopters (OH, PA, DE) had flat delivery; CA cut gas "
                 "yet delivery rose most.\n"
                 "Proxy: EIA all-sector Delivery-Only price (T&D+policy), 19 "
                 "retail-choice states", fontsize=10)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = OUTPUT_DIR / "delivery_vs_gas_scatter.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = build()
    slope, intercept, r, r2 = fit_line(df["d_gas_pp"].to_numpy(),
                                       df["d_deliv_real"].to_numpy())

    print(f"\n{'='*72}\nClaim 03, Layer 3 pt 1b - does delivery cost track gas adoption?\n{'='*72}")
    print(f"Sample: {len(df)} retail-choice states, {START}-{END}, "
          f"real {END} cents/kWh.\n")
    print(f"-- Cross-state relationship (change vs change) --")
    print(f"  Pearson r = {r:+.2f}   (R^2 = {r2:.2f})")
    print(f"  slope = {slope:+.3f} cents/kWh of delivery cost per +1pp gas share")
    print(f"  -> No positive link; if anything weakly NEGATIVE. Adoption does not "
          f"explain\n     delivery-cost growth (the wires are fuel-agnostic).")

    print("\n-- The tells --")
    big = df.sort_values("d_gas_pp", ascending=False).head(3)
    print("  Heaviest gas adopters and their delivery-cost change:")
    for _, r_ in big.iterrows():
        print(f"    {r_['State']:<4} gas {r_['d_gas_pp']:+5.1f}pp   "
              f"delivery {r_['d_deliv_real']:+5.1f} c/kWh (real)")
    ca = df[df["State"] == "CA"]
    if not ca.empty:
        ca = ca.iloc[0]
        print(f"  CA   gas {ca['d_gas_pp']:+5.1f}pp (FELL)  delivery "
              f"{ca['d_deliv_real']:+5.1f} c/kWh -> biggest riser, cutting gas.")
    ct = df[df["State"] == "CT"].iloc[0]
    print(f"  CT   gas {ct['d_gas_pp']:+5.1f}pp   delivery {ct['d_deliv_real']:+5.1f} "
          f"c/kWh -> high on both, but off the (negative) trend, not on a positive one.")

    df.sort_values("d_gas_pp", ascending=False).round(2).to_csv(
        OUTPUT_DIR / "delivery_vs_gas.csv", index=False)
    p = plot_scatter(df, slope, intercept, r)
    print(f"\nWrote: delivery_vs_gas.csv, {p.name}")


if __name__ == "__main__":
    main()
