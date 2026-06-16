"""Claim 03, Layer 3 (part 1) - what is in a Connecticut electric bill, and where
did the stranded-cost (CTA) piece go?

Layer 1 showed the cross-state correlation CCEA leans on does not exist, and that
Connecticut's *level* gap lives on the delivery/policy side of the bill, not in
the energy (gas) component. This script opens up that delivery side using the
actual published bill components for CL&P / Eversource residential service at
three sourced anchor years (2006, 2019, 2022), and isolates the Competitive
Transition Assessment (CTA) - the non-bypassable charge that recovered the
utilities' restructuring-era stranded costs.

The finding:
  * Supply (the gas-sensitive energy charge) is flat in nominal terms and *down*
    in real terms across 2006-2022.
  * The CTA was ~1 cent/kWh in the mid-2000s, was fully recovered by 2011 (CL&P)
    / 2013 (UI), and is now a tiny credit. It is a transitional cost of the OLD
    pre-restructuring generation fleet and 1980s-90s purchased-power contracts -
    the opposite of a natural-gas-adoption cost.
  * Total delivery kept rising anyway, because transmission, distribution, and
    public-benefit/reliability charges (incl. the Millstone contract) grew far
    more than the CTA shrank.

Sources are primary (CT OLR reports and CT Office of Consumer Counsel bill-
component sheets); see claims/03-rates/README.md for the full citations. Data
lives in ./data/ct_bill_components.csv.

Outputs (charts) land in ./output/. Run:
    python claims/03-rates/analyze_bill_components.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

THIS_DIR = Path(__file__).resolve().parent
COMPONENTS_CSV = THIS_DIR / "data" / "ct_bill_components.csv"
OUTPUT_DIR = THIS_DIR / "output"

# Bottom-to-top stacking order and colors. Supply is the only gas-sensitive
# piece; the CTA (stranded costs) is highlighted in red.
GROUP_ORDER = [
    "Supply (energy)",
    "Wires (transmission & distribution)",
    "Public-benefit & reliability",
    "Stranded-cost transition (CTA)",
]
GROUP_COLOR = {
    "Supply (energy)": "#2c7fb8",
    "Wires (transmission & distribution)": "#7f7f7f",
    "Public-benefit & reliability": "#ff7f0e",
    "Stranded-cost transition (CTA)": "#d62728",
}

# CPI-U annual average (BLS CUUR0000SA0); base = 2024, to show supply in real
# terms. Only the years this script needs.
CPI_U = {2006: 201.6, 2019: 255.657, 2022: 292.655, 2024: 313.689}

# CTA trajectory anchor points, cents/kWh, CL&P / Eversource residential. These
# are sparse sourced anchors, not a continuous series: the CTA reconciles yearly
# and swung between credit and charge as stranded costs were over/under-recovered.
#   2004: ~ -0.63  (credit, 2003 over-recovery, ran through Apr 2005) - OLR 2005-R-0102
#   2006: +1.02                                                       - OLR 2006-R-0477
#   2011:  ~0      (CL&P stranded costs "majority recovered by 2011") - OCC 2019/2022
#   2019:  ~0      (no residential CTA rate listed)                   - OCC 2019-08
#   2022: -0.116   (small credit; residual legacy-PPA reconciliation) - OCC 2022-01
CTA_ANCHORS = [(2004, -0.63), (2006, 1.02), (2011, 0.0), (2019, 0.0), (2022, -0.116)]


def load_components() -> pd.DataFrame:
    if not COMPONENTS_CSV.exists():
        raise SystemExit(f"Missing data file: {COMPONENTS_CSV}")
    return pd.read_csv(COMPONENTS_CSV)


def group_totals(df: pd.DataFrame) -> pd.DataFrame:
    """cents/kWh by group x year (years as columns), in GROUP_ORDER."""
    piv = df.pivot_table(index="group", columns="year", values="cents_per_kwh",
                         aggfunc="sum").reindex(GROUP_ORDER).fillna(0.0)
    return piv


def plot_stack(piv: pd.DataFrame) -> Path:
    years = list(piv.columns)
    x = range(len(years))
    fig, ax = plt.subplots(figsize=(8.5, 6))
    # Stack only the non-negative groups cleanly; the CTA segment is tiny and is
    # labeled explicitly rather than relied on for height.
    bottom = [0.0] * len(years)
    for grp in GROUP_ORDER:
        vals = [max(v, 0.0) for v in piv.loc[grp]]
        ax.bar(x, vals, bottom=bottom, color=GROUP_COLOR[grp], label=grp,
               width=0.6, edgecolor="white", linewidth=0.6)
        bottom = [b + v for b, v in zip(bottom, vals)]
    # Annotate each bar's total and the CTA value.
    for i, yr in enumerate(years):
        total = piv[yr].sum()
        ax.text(i, bottom[i] + 0.3, f"{total:.1f}c total", ha="center",
                fontsize=9, fontweight="bold")
        cta = piv.loc["Stranded-cost transition (CTA)", yr]
        ax.text(i, -1.4, f"CTA: {cta:+.2f}c", ha="center", fontsize=8,
                color="#d62728")
    ax.set_xticks(list(x))
    ax.set_xticklabels(years)
    ax.set_ylabel("Residential bill (cents/kWh, nominal)")
    ax.set_ylim(-2.2, max(piv.sum()) * 1.12)
    ax.set_title("Where a Connecticut electric bill went, by component\n"
                 "CL&P / Eversource residential. Supply (gas-sensitive) is flat;\n"
                 "the rise is wires + policy. The CTA shrank to nothing.",
                 fontsize=11)
    ax.legend(loc="upper left", fontsize=8)
    ax.axhline(0, color="#999", linewidth=0.8)
    fig.tight_layout()
    path = OUTPUT_DIR / "ct_bill_components_stacked.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def plot_cta(piv: pd.DataFrame) -> Path:
    yrs = [y for y, _ in CTA_ANCHORS]
    vals = [v for _, v in CTA_ANCHORS]
    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.axhline(0, color="#999", linewidth=0.9)
    ax.plot(yrs, vals, color="#d62728", marker="o", linewidth=1.6,
            linestyle="--", label="CTA (sourced anchor points)")
    for yr, v in CTA_ANCHORS:
        ax.annotate(f"{v:+.2f}", (yr, v), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=8)
    ax.axvspan(2003, 2005, color="#d62728", alpha=0.06)
    ax.annotate("2003 over-recovery\n-> credit through Apr 2005", (2004, -0.63),
                textcoords="offset points", xytext=(20, 30), fontsize=8,
                color="#777")
    ax.annotate("CL&P stranded costs\nfully recovered by 2011", (2011, 0.0),
                textcoords="offset points", xytext=(6, 18), fontsize=8,
                color="#777")
    ax.set_xlabel("Year")
    ax.set_ylabel("CTA charge (cents/kWh)")
    ax.set_title("The stranded-cost piece (CTA), CL&P / Eversource residential\n"
                 "A transitional restructuring charge - paid off, not a gas cost.\n"
                 "Sources: CT OLR reports; CT Office of Consumer Counsel",
                 fontsize=11)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = OUTPUT_DIR / "ct_cta_trajectory.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_components()
    piv = group_totals(df)

    print(f"\n{'='*72}\nClaim 03, Layer 3 - CL&P/Eversource residential bill components\n{'='*72}")
    print("cents/kWh (nominal) by group:\n")
    show = piv.copy()
    show.loc["TOTAL"] = show.sum()
    print(show.round(2).to_string())

    # Supply in real terms: flat nominal == down in real.
    base = CPI_U[2024]
    s06 = piv.loc["Supply (energy)", 2006] * base / CPI_U[2006]
    s22 = piv.loc["Supply (energy)", 2022] * base / CPI_U[2022]
    print("\n-- The gas-sensitive piece (supply) --")
    print(f"  Supply 2006: {piv.loc['Supply (energy)',2006]:.2f}c nominal "
          f"= {s06:.1f}c in real 2024 dollars")
    print(f"  Supply 2022: {piv.loc['Supply (energy)',2022]:.2f}c nominal "
          f"= {s22:.1f}c in real 2024 dollars   ({(s22/s06-1)*100:+.0f}% real)")

    # What actually grew.
    print("\n-- What grew, 2006 -> 2022 (nominal cents/kWh) --")
    for grp in GROUP_ORDER:
        a, b = piv.loc[grp, 2006], piv.loc[grp, 2022]
        print(f"  {grp:<40} {a:+5.2f} -> {b:+5.2f}   ({b-a:+.2f})")
    print("\n  The CTA (stranded costs) shrank to a credit; wires and "
          "public-benefit/reliability\n  charges more than replaced it. Supply "
          "fell in real terms.")

    p1 = plot_stack(piv)
    p2 = plot_cta(piv)
    print(f"\nWrote: {p1.name}, {p2.name}")


if __name__ == "__main__":
    main()
