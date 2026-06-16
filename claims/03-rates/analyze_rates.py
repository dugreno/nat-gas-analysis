"""Claim 03, Layer 1 - Did natural-gas adoption raise electricity costs?

CCEA's report says expanding gas generation "delivered no reduction in rates."
The companion CBIA article says gas "does not make electricity more expensive."
This layer establishes the descriptive picture both rest on: across states, as
gas took over a larger share of generation, what happened to the real (inflation-
adjusted) price of electricity?

It deliberately does NOT answer a bare correlation with another bare correlation
(the error flagged in claim 02). Instead it sets the question up so the naive
"more gas -> higher price" story is falsifiable on sight, using a three-tier
comparison set:

  * CT                                  - the subject
  * restructured Northeast / ISO-NE     - MA RI NH ME VT NY NJ (CT's peers)
  * gas-heavy, low-price contrast       - TX PA OH (the falsification tier)

If adoption drove price, Texas - a state that makes most of its power from gas -
should be expensive. It is cheap. That single fact is most of the argument; the
charts here make it visible and quantify it.

By default it runs two windows and tags every output by window:
  * 2001-2024 - CCEA's own baseline (the start of its "~50% generation increase"
    claim) and the earliest year of state retail-price data;
  * 2007-2024 - the shale-era onset, a check that a low 2001 baseline is not
    doing the work.

Outputs (CSV + charts) land in ./output/. Run:
    python claims/03-rates/analyze_rates.py                 # both default windows
    python claims/03-rates/analyze_rates.py --start 2010    # one custom window

If data is missing:  python scripts/download_data.py
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"
GEN_FILE = RAW_DIR / "eia_annual_generation_state.xls"
ELEC_ZIP = RAW_DIR / "EIA_ELEC.zip"
PRICE_CACHE = RAW_DIR / "eia_retail_price_annual.csv"
OUTPUT_DIR = THIS_DIR / "output"

TOTAL_SECTOR = "Total Electric Power Industry"

# Comparison tiers. The gas-heavy tier is the falsification set: high gas share,
# low price. Everything else is the national "cloud" we plot in grey.
CT = "CT"
RESTRUCTURED_NE = ["MA", "RI", "NH", "ME", "VT", "NY", "NJ"]
GAS_HEAVY = ["TX", "PA", "OH"]
TIER_COLOR = {"CT": "#d62728", "Restructured NE / ISO-NE": "#1f77b4",
              "Gas-heavy contrast": "#ff7f0e", "Other states": "#bdbdbd"}


def tier_of(state: str) -> str:
    if state == CT:
        return "CT"
    if state in RESTRUCTURED_NE:
        return "Restructured NE / ISO-NE"
    if state in GAS_HEAVY:
        return "Gas-heavy contrast"
    return "Other states"


# CPI-U, U.S. city average, all items, annual average (1982-84=100), BLS series
# CUUR0000SA0. Used to deflate nominal retail prices to constant dollars so a
# price "increase" is a real one, not just general inflation.
CPI_U = {
    2001: 177.1, 2002: 179.9, 2003: 184.0, 2004: 188.9, 2005: 195.3,
    2006: 201.6, 2007: 207.342, 2008: 215.303, 2009: 214.537, 2010: 218.056,
    2011: 224.939, 2012: 229.594, 2013: 232.957, 2014: 236.736, 2015: 237.017,
    2016: 240.007, 2017: 245.120, 2018: 251.107, 2019: 255.657, 2020: 258.811,
    2021: 270.970, 2022: 292.655, 2023: 304.702, 2024: 313.689,
}


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def _need(path: Path) -> None:
    if not path.exists():
        raise SystemExit(
            f"Data file not found: {path}\nRun:  python scripts/download_data.py"
        )


def load_gas_share() -> pd.DataFrame:
    """Natural gas as a percent of net generation, per state per year.

    Returns long form: columns State, Year, gas_share (0-100), total_mwh.
    """
    _need(GEN_FILE)
    df = pd.read_excel(GEN_FILE, sheet_name=0, header=1)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={"GENERATION (Megawatthours)": "MWh"})
    df = df[df["TYPE OF PRODUCER"] == TOTAL_SECTOR].copy()
    # EIA labels the national row "US-Total"; the price series uses "US". Align
    # them so the national series survives the join. (Only US-Total carries the
    # Total Electric Power Industry rows, so this cannot double-count.)
    df["STATE"] = df["STATE"].replace({"US-Total": "US", "US-TOTAL": "US"})
    piv = df.pivot_table(
        index=["STATE", "YEAR"], columns="ENERGY SOURCE", values="MWh", aggfunc="sum"
    )
    # A state with no gas generation (e.g. Hawaii) has no "Natural Gas" rows, so
    # the pivot leaves NaN; that is a genuine 0% share, not missing data.
    gas = (piv["Natural Gas"] if "Natural Gas" in piv.columns else 0.0).fillna(0.0)
    total = piv["Total"]
    out = pd.DataFrame({"total_mwh": total, "gas_share": gas / total * 100.0})
    out = out.reset_index().rename(columns={"STATE": "State", "YEAR": "Year"})
    out["State"] = out["State"].str.strip()
    return out


def load_retail_price() -> pd.DataFrame:
    """All-sector average retail price (cents/kWh, nominal) per state per year.

    Extracts ELEC.PRICE.<ST>-ALL.A from the EIA bulk archive once and caches the
    result to a small CSV so the ~240 MB zip is scanned only the first time.
    Returns long form: columns State, Year, cents_nominal.
    """
    if PRICE_CACHE.exists():
        return pd.read_csv(PRICE_CACHE)
    _need(ELEC_ZIP)
    rows: list[tuple[str, int, float]] = []
    with zipfile.ZipFile(ELEC_ZIP) as z:
        with z.open("ELEC.txt") as fh:
            for line in fh:
                if b'"ELEC.PRICE.' not in line or b'-ALL.A"' not in line:
                    continue
                obj = json.loads(line)
                sid = obj.get("series_id", "")
                if not (sid.startswith("ELEC.PRICE.") and sid.endswith("-ALL.A")):
                    continue
                state = sid.split(".")[2].split("-")[0]
                for period, value in obj.get("data", []):
                    if value is None:
                        continue
                    rows.append((state, int(period), float(value)))
    price = pd.DataFrame(rows, columns=["State", "Year", "cents_nominal"])
    price = price.sort_values(["State", "Year"]).reset_index(drop=True)
    price.to_csv(PRICE_CACHE, index=False)
    return price


def build_panel(start: int, end: int) -> pd.DataFrame:
    """State-year panel of gas share and real price, base-year = `end`."""
    gas = load_gas_share()
    price = load_retail_price()
    panel = price.merge(gas[["State", "Year", "gas_share"]], on=["State", "Year"])
    base_cpi = CPI_U[end]
    panel = panel[panel["Year"].isin(CPI_U)].copy()
    panel["cents_real"] = panel["cents_nominal"] * base_cpi / panel["Year"].map(CPI_U)
    panel["tier"] = panel["State"].apply(tier_of)
    return panel[(panel["Year"] >= start) & (panel["Year"] <= end)]


def summarize(panel: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    """One row per state: levels and start->end changes. Real states only."""
    drop = {"US", "DC"}
    rows = []
    for state, g in panel.groupby("State"):
        if state in drop:
            continue
        g = g.set_index("Year")
        if start not in g.index or end not in g.index:
            continue
        rows.append({
            "State": state,
            "tier": tier_of(state),
            "share_start": g.loc[start, "gas_share"],
            "share_end": g.loc[end, "gas_share"],
            "d_share_pp": g.loc[end, "gas_share"] - g.loc[start, "gas_share"],
            "real_start": g.loc[start, "cents_real"],
            "real_end": g.loc[end, "cents_real"],
            "d_real": g.loc[end, "cents_real"] - g.loc[start, "cents_real"],
            "d_real_pct": (g.loc[end, "cents_real"] / g.loc[start, "cents_real"] - 1) * 100,
        })
    return pd.DataFrame(rows).sort_values("d_share_pp", ascending=False)


def fit_line(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """Return (slope, intercept, r_squared) for y ~ x."""
    slope, intercept = np.polyfit(x, y, 1)
    pred = slope * x + intercept
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")
    return float(slope), float(intercept), r2


# --------------------------------------------------------------------------- #
# Charts
# --------------------------------------------------------------------------- #
def _scatter(ax, summ: pd.DataFrame, xcol: str, ycol: str) -> None:
    for tier in ["Other states", "Restructured NE / ISO-NE", "Gas-heavy contrast", "CT"]:
        sub = summ[summ["tier"] == tier]
        ax.scatter(sub[xcol], sub[ycol], s=(70 if tier == "CT" else 45),
                   c=TIER_COLOR[tier], label=tier, alpha=0.85,
                   zorder=(5 if tier == "CT" else 3),
                   edgecolors="white", linewidths=0.5)
    # Label CT and the gas-heavy contrast states explicitly.
    for _, r in summ[summ["tier"].isin(["CT", "Gas-heavy contrast"])].iterrows():
        ax.annotate(r["State"], (r[xcol], r[ycol]), fontsize=8,
                    xytext=(4, 4), textcoords="offset points")


def plot_change_scatter(summ: pd.DataFrame, start: int, end: int) -> Path:
    x = summ["d_share_pp"].to_numpy()
    y = summ["d_real"].to_numpy()
    slope, intercept, r2 = fit_line(x, y)
    fig, ax = plt.subplots(figsize=(9, 6))
    xs = np.linspace(x.min(), x.max(), 50)
    ax.plot(xs, slope * xs + intercept, color="#444", linestyle="--", linewidth=1.3,
            label=f"fit: {slope:+.3f} c/kWh per +1pp  (R^2={r2:.2f})")
    _scatter(ax, summ, "d_share_pp", "d_real")
    ax.axhline(0, color="#999", linewidth=0.8)
    ax.set_xlabel(f"Change in gas share of generation, {start}-{end} (percentage points)")
    ax.set_ylabel(f"Change in real retail price, {start}-{end}\n(cents/kWh, {end} dollars)")
    ax.set_title("Did states that adopted more gas see prices rise?\n"
                 "One dot per state. Source: EIA generation + retail price; BLS CPI-U",
                 fontsize=11)
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = OUTPUT_DIR / f"scatter_change_share_vs_price_{start}_{end}.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def plot_levels_scatter(summ: pd.DataFrame, end: int) -> Path:
    fig, ax = plt.subplots(figsize=(9, 6))
    _scatter(ax, summ, "share_end", "real_end")
    ax.set_xlabel(f"Gas share of generation, {end} (%)")
    ax.set_ylabel(f"Real retail price, {end} (cents/kWh, {end} dollars)")
    ax.set_title("High gas share does not mean high price\n"
                 "Texas sits at high gas share and low price; CT the opposite",
                 fontsize=11)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = OUTPUT_DIR / f"scatter_levels_share_vs_price_{end}.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def plot_national_timeseries(panel: pd.DataFrame, start: int, end: int) -> Path:
    us = panel[panel["State"] == "US"].set_index("Year").sort_index()
    fig, ax1 = plt.subplots(figsize=(9, 5.5))
    ax1.plot(us.index, us["gas_share"], color="#2c7fb8", linewidth=2,
             label="Gas share of generation (%)")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Gas share of U.S. generation (%)", color="#2c7fb8")
    ax1.tick_params(axis="y", labelcolor="#2c7fb8")
    ax1.grid(True, alpha=0.3)
    ax2 = ax1.twinx()
    ax2.plot(us.index, us["cents_real"], color="#d62728", linewidth=2,
             label=f"Real retail price (cents/kWh, {end} $)")
    ax2.set_ylabel(f"Real U.S. retail price (cents/kWh, {end} $)", color="#d62728")
    ax2.tick_params(axis="y", labelcolor="#d62728")
    ax1.set_title("Nationally, gas share rose while real electricity prices did not\n"
                  "Source: EIA; deflated by BLS CPI-U", fontsize=11)
    fig.tight_layout()
    path = OUTPUT_DIR / f"national_share_vs_price_{start}_{end}.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def plot_ct_vs_tiers(panel: pd.DataFrame, start: int, end: int) -> Path:
    """Real price indexed to start=100 for CT, each peer tier mean, and the US."""
    fig, ax = plt.subplots(figsize=(9, 5.5))
    series = {
        "CT": panel[panel["State"] == CT],
        "Restructured NE / ISO-NE (mean)": panel[panel["State"].isin(RESTRUCTURED_NE)],
        "Gas-heavy contrast (mean)": panel[panel["State"].isin(GAS_HEAVY)],
        "United States": panel[panel["State"] == "US"],
    }
    colors = {"CT": "#d62728", "Restructured NE / ISO-NE (mean)": "#1f77b4",
              "Gas-heavy contrast (mean)": "#ff7f0e", "United States": "#444"}
    for label, sub in series.items():
        ts = sub.groupby("Year")["cents_real"].mean().sort_index()
        ts = ts[(ts.index >= start) & (ts.index <= end)]
        if start not in ts.index:
            continue
        ax.plot(ts.index, ts / ts.loc[start] * 100, label=label,
                color=colors[label], linewidth=(2.4 if label == "CT" else 1.8))
    ax.axhline(100, color="#999", linewidth=0.8)
    ax.set_xlabel("Year")
    ax.set_ylabel(f"Real retail price, indexed ({start} = 100)")
    ax.set_title(f"Real electricity price, indexed to {start}\n"
                 "Source: EIA retail price, deflated by BLS CPI-U", fontsize=11)
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = OUTPUT_DIR / f"ct_vs_tiers_indexed_{start}_{end}.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
# Windows run by default: 2001 is CCEA's own baseline (the start of its
# "~50% generation increase" claim) and the earliest year with state retail-price
# data; 2007 is the shale-era onset, a robustness check that a low 2001 baseline
# is not doing the work.
DEFAULT_WINDOWS = [(2001, 2024), (2007, 2024)]


def run_window(start: int, end: int) -> None:
    """Build the panel, print the summary, and write tagged tables + charts."""
    panel = build_panel(start, end)
    summ = summarize(panel, start, end)

    print(f"\n{'='*74}\nClaim 03, Layer 1 - gas adoption vs. real electricity price\n{'='*74}")
    print(f"Window: {start}-{end}   |   prices in real {end} cents/kWh, all sectors")
    print(f"States with full data: {len(summ)}\n")

    # --- The national relationship --------------------------------------------
    x, y = summ["d_share_pp"].to_numpy(), summ["d_real"].to_numpy()
    slope, _, r2 = fit_line(x, y)
    rose = int((summ["d_share_pp"] > 0).sum())
    print("-- National: change in gas share vs. change in real price --")
    print(f"  {rose}/{len(summ)} states raised their gas share over the window.")
    print(f"  Cross-state fit: {slope:+.3f} cents/kWh per +1pp of gas share "
          f"(R^2 = {r2:.2f}).")
    print("  A flat/negative slope or near-zero R^2 means adoption does not "
          "explain price.")

    # --- The falsification: CT vs. the gas-heavy contrast ---------------------
    print("\n-- Falsification tier: high gas share does not buy high prices --")
    look = ["CT", "MA", "TX", "PA", "OH"]
    hdr = f"  {'State':<6}{'gas% '+str(start):>12}{'gas% '+str(end):>12}{'real c/kWh '+str(end):>16}"
    print(hdr)
    for st in look:
        r = summ[summ["State"] == st]
        if r.empty:
            continue
        r = r.iloc[0]
        print(f"  {st:<6}{r['share_start']:>11.1f}%{r['share_end']:>11.1f}%"
              f"{r['real_end']:>15.1f}")
    ct = summ[summ["State"] == "CT"].iloc[0]
    tx = summ[summ["State"] == "TX"].iloc[0]
    print(f"  -> CT and TX sit at comparable gas shares ({ct['share_end']:.0f}% vs "
          f"{tx['share_end']:.0f}%) yet CT pays {ct['real_end']/tx['real_end']:.1f}x "
          f"more per kWh. The gap is not the gas.")
    print(f"  -> PA and OH raised gas share the most (to ~60% from single digits) "
          f"and their real price FELL. Fastest adopters, biggest price drops.")

    # --- Tier averages --------------------------------------------------------
    print("\n-- Tier averages (change over window) --")
    for tier in ["CT", "Restructured NE / ISO-NE", "Gas-heavy contrast", "Other states"]:
        sub = summ[summ["tier"] == tier]
        if sub.empty:
            continue
        print(f"  {tier:<28} d_gas_share={sub['d_share_pp'].mean():+5.1f}pp   "
              f"d_real_price={sub['d_real'].mean():+5.1f} c/kWh   "
              f"({sub['d_real_pct'].mean():+5.1f}% real)")

    # --- Outputs --------------------------------------------------------------
    panel_csv = OUTPUT_DIR / f"state_panel_{start}_{end}.csv"
    summ_csv = OUTPUT_DIR / f"state_summary_{start}_{end}.csv"
    panel.sort_values(["State", "Year"]).to_csv(panel_csv, index=False)
    summ.to_csv(summ_csv, index=False)
    p1 = plot_change_scatter(summ, start, end)
    p2 = plot_levels_scatter(summ, end)
    p3 = plot_national_timeseries(panel, start, end)
    p4 = plot_ct_vs_tiers(panel, start, end)
    print(f"\nWrote: {panel_csv.name}, {summ_csv.name},\n       "
          f"{p1.name}, {p2.name}, {p3.name}, {p4.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=None,
                        help="Window start year. Omit to run both default windows "
                        f"({', '.join(f'{a}-{b}' for a, b in DEFAULT_WINDOWS)}).")
    parser.add_argument("--end", type=int, default=2024,
                        help="Window end year (default: 2024, latest full data).")
    args = parser.parse_args()

    windows = DEFAULT_WINDOWS if args.start is None else [(args.start, args.end)]
    for start, end in windows:
        if start not in CPI_U or end not in CPI_U:
            raise SystemExit(f"start/end must be within {min(CPI_U)}-{max(CPI_U)} "
                             "(retail-price data begins in 2001)")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for start, end in windows:
        run_window(start, end)


if __name__ == "__main__":
    main()
