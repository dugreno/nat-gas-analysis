# Claim 03 — Did natural-gas adoption raise electricity costs?

**CCEA report:** *How Did We Get Here?* (CCEA / Fred Carstensen)
**Companion article:** CBIA, "Natural Gas Does Not Make Electricity More Expensive."

> "…the well-intended expansion of generation capacity … **delivered no reduction
> in rates** …"
> — *How Did We Get Here?*, Executive Summary

This is the data-driven counterpart to the interpretive [Claim 02](../02-economic-benefit/).
The question is empirical and answerable: **as states adopted natural gas over the
past ~15–20 years, what happened to the price of electricity?** And does
Connecticut's experience look like a gas problem, or like something else?

## The question, stated carefully

There are three different things people collapse into "gas made power expensive,"
and the whole analysis turns on keeping them apart:

1. **Adoption** — *how much* of a state's electricity comes from gas (a quantity:
   share of net generation). Also, secondarily, how many buildings switched to
   gas at the meter (end-use adoption).
2. **Delivered gas price** — what the gas a state burns actually *costs*
   (Henry Hub plus regional basis; New England's winter pipeline constraint blows
   this out for a few weeks a year).
3. **The non-energy bill** — transmission, distribution, and policy / public-
   benefit charges, which make up much of a Connecticut bill and have nothing to
   do with gas.

CCEA's framing runs adoption and price together. The point of this claim is not
to answer one bare correlation with another — that is the exact error
[Claim 02](../02-economic-benefit/) identifies — but to **locate where the cost
actually lives.**

## The trap we are deliberately avoiding

A naïve scatter of "gas share vs. retail price" would show New England high on
both axes and invite the conclusion that gas drove the price. That inference is
unsound, and the design is built to expose why:

- It ignores that gas is the *cheap* marginal fuel almost everywhere — adoption
  rose nationwide while real wholesale prices **fell** after the shale era.
- It conflates burning gas with the *constrained delivered price* of gas in a
  pipeline-limited corner of the country.
- It attributes to generation fuel a bill that is mostly transmission,
  distribution, and policy charges.

So the comparison set is chosen to make the naïve story falsifiable on sight (see
below), and the later layers decompose the bill rather than correlate aggregates.

## Comparison set (three tiers)

| Tier | States | Role in the argument |
|------|--------|----------------------|
| Subject | **CT** | the state in question |
| Restructured Northeast / ISO-NE peers | MA, RI, NH, ME, VT, NY, NJ | same grid and/or same restructured-market design as CT |
| Gas-heavy, low-price contrast | TX, PA, OH | the **falsification tier** — high gas share, *low* prices |

The third tier is the load-bearing one. If "more gas → higher price" were true,
Texas — which generates a large majority of its power from gas — should be among
the most expensive states. It is among the cheapest. A single chart with all
three tiers on it shows that the price gap between Connecticut and Texas cannot be
the gas, because they sit at similar gas shares and opposite prices.

## Metrics

- **Adoption (primary):** natural gas as a share of in-state net generation (%),
  from EIA net-generation-by-fuel. Both the *level* and the *rate of change*
  (percentage-point change over the window).
- **Adoption (secondary):** end-use adoption — share of homes on utility gas
  (Census ACS B25040) and residential gas customer counts (EIA) — to look at the
  separate "convert buildings to gas" story (Connecticut's post-2013 Comprehensive
  Energy Strategy push).
- **Cost:** all-sector average retail price of electricity (cents/kWh), nominal
  and **CPI-deflated to real terms**, from EIA. All-sector is the cleanest single
  cross-state measure; it blends residential, commercial, and industrial.

## Analysis layers

The analysis is built in three runnable layers so each stands on its own and the
cheap, decisive picture comes first.

**Layer 1 — Descriptive (national + tiers).** *(built — `analyze_rates.py`)*
- Run over two baselines — **2001** (CCEA's own) and **2007** (shale onset) — so a
  low starting year is never silently doing the work; every output is tagged by
  window.
- One dot per state: change in gas generation share (percentage points) vs. change
  in real all-sector retail price over the window, tiers color-coded, CT labeled.
- A levels scatter (latest year) and a national time series (gas share vs. real
  price) to show the post-shale direction of travel.
- Indexed (start-year = 100) real-price trajectories for CT and each tier.

**Layer 2 — Panel regression (rigor).** *(planned)*
- State-year panel with **state fixed effects** (absorb fixed state traits) and
  **year fixed effects** (absorb national fuel-price and macro shocks); the
  within-state coefficient on gas share is the estimate of interest.
- Add **delivered gas price** as a control, plus a share × price interaction, to
  separate "adopting gas" from "the gas got expensive."
- Split restructured vs. regulated states (gas only sets the clearing price in
  restructured markets; CT is restructured).

**Layer 3 — Decomposition.** *(parts 1 & 1b built)*
- **Part 1 (built — `analyze_bill_components.py`):** decompose the actual published
  CL&P / Eversource residential bill into supply vs. wires vs. policy vs. the
  stranded-cost (CTA) charge, at sourced anchor years (2006, 2019, 2022), to show
  *which* part of the bill grew.
- **Part 1b (built — `analyze_delivery_vs_gas.py`):** a spurious-correlation guard
  — across states, does gas adoption track delivery-cost growth? (It does not.)
- **Part 2 (planned):** extend the supply-vs-delivery split across all states and
  past 2024, and add the winter gas *basis* (Algonquin Citygate vs. Henry Hub) to
  separate the regional pipeline-constraint cost from adoption.

## Honesty guardrails

- This is **observational**. Fixed effects narrow the confounding but do not prove
  causation.
- Cheap shale gas plausibly drove *both* higher adoption and lower wholesale
  prices, so "the effect of adoption" and "the effect of cheap gas" are entangled;
  Layer 2 controls for gas price precisely because of this, rather than pretending
  adoption is clean.
- A state's generation mix is not identical to what its consumers pay (interstate
  power trade), though ISO-NE is a tight, import-aware market.
- Regulated and restructured states set retail prices by fundamentally different
  mechanisms; the analysis flags which is which.

## Findings — Layer 1 (prices in real 2024 ¢/kWh, all sectors)

Two windows are run: **2001–2024** (CCEA's own baseline — the start of its
"~50% generation increase" claim, and the first year of state retail-price data)
and **2007–2024** (the shale-era onset). The cross-state result is the same in
both; the level-change result depends on the baseline, in a way that is itself
revealing.

**Nationally, adoption and price do not move together.** The U.S. gas share of
generation roughly *doubled* (2001: 17% → 2024: 43%; 2007: 22% → 43%) while the
real all-sector retail price ended *below* where it started in real terms.
Across the 50 states, how much a state raised its gas share explains essentially
none of how its real price changed:

| Window | Cross-state slope | R² | States that raised gas share |
|--------|-------------------|----|------------------------------|
| 2001–2024 | −0.02 ¢/kWh per +1 pp | 0.02 | 44 / 50 |
| 2007–2024 | −0.04 ¢/kWh per +1 pp | 0.09 | 45 / 50 |

The slope is slightly **negative** and the R² is near zero either way — adoption
is not a predictor of price changes. (`national_share_vs_price_*.png`,
`scatter_change_share_vs_price_*.png`.)

**The falsification tier settles the level question.** If gas drove price, the
gas-heaviest states would be the most expensive. The opposite holds (2024 levels,
same regardless of baseline):

| State | Gas share 2001 → 2024 | Real price 2024 (¢/kWh) |
|-------|------------------------|--------------------------|
| CT | 13% → 58% | 24.4 |
| MA | 30% → 78% | 23.9 |
| TX | 51% → 52% | 9.8 |
| PA | 2% → 60% | 12.5 |
| OH | 1% → 60% | 11.3 |

Connecticut and Texas sit at **comparable gas shares (58% vs. 52%)** yet CT's
average price is **2.5× higher**. Pennsylvania and Ohio went from ~1–2% gas to
~60% — the **largest adoption increases in the country — and their real prices
fell.** Whatever makes Connecticut expensive, it is not that the state burns gas.

**The baseline matters — and that is the point.** Tier-average change differs
sharply between the two windows:

| Tier | Δ real price, 2001–24 | Δ real price, 2007–24 |
|------|-----------------------|-----------------------|
| CT | **+43%** | −2% |
| Restructured NE / ISO-NE | +5% | −3% |
| Gas-heavy contrast (TX, PA, OH) | **−13%** | −17% |
| All other states | +6% | +1% |

From a 2001 baseline Connecticut's real price rose 43%; from 2007 it was flat.
That is not a contradiction — it locates *when* the increase happened.
Connecticut's real all-sector price went **17.0 ¢ (2001) → 24.9 ¢ (2007) → 24.4 ¢
(2024)**. The entire real increase occurred **2001–2007**, while gas was still a
*minority* fuel (13% → 30% of generation) and pre-shale gas prices were high.
Once Connecticut actually leaned into gas — share doubling from 30% to 58% across
2007–2024 — real prices stopped rising. **The price run-up predates the gas
build-out.** Meanwhile the states that adopted the *most* gas (TX, PA, OH) saw
real prices *fall even from the 2001 low.* If adoption raised rates, those states
should have risen the most; they fell the most.

This is the same baseline trap [Claim 01](../01-emissions/) flags: 2001 is a
cyclical low (for prices, the pre-shale era before the mid-2000s gas-price spike),
so any metric measured from it shows a large "increase." The honest reading is
that the cross-state evidence is flat in *both* windows, and Connecticut's own
increase is a pre-2008 phenomenon that the subsequent gas era did not extend.
(`ct_vs_tiers_indexed_*.png`.)

**What this does and does not show.** Layer 1 establishes that the bare
correlation CCEA leans on does not exist — nationally or among CT's peers, more
gas did not mean higher prices, and CT's real increase came *before* its heavy
adoption. It does *not yet* explain CT's high *level*. That level gap is real and
predates the gas era; Layer 3 opens up the bill to locate it.

## Findings — Layer 3 part 1: what is *in* a Connecticut bill

Using the actual published CL&P / Eversource **residential** bill components at
three sourced anchor years (nominal cents/kWh):

| Group | 2006 | 2019 | 2022 |
|-------|-----:|-----:|-----:|
| Supply (energy — the gas-sensitive part) | 10.76 | 8.18 | 11.48 |
| Wires (transmission & distribution) | 2.94 | 8.67 | 9.85 |
| Public-benefit & reliability | 2.19 | 2.15 | 3.12 |
| Stranded-cost transition (CTA) | 1.02 | 0.00 | −0.12 |
| **Total** | **16.91** | **19.00** | **24.34** |

Of the **+7.4¢/kWh** rise in the bill from 2006 to 2022, **+6.9¢ is wires** —
overwhelmingly transmission, the New England build-out. The **supply** component
(the only gas-sensitive piece) is flat in nominal terms and **−26% in real
terms** (16.7 → 12.3 real 2024 ¢/kWh): the gas era pushed the energy charge
*down*. The price problem is the delivery side, not the gas.
(`ct_bill_components_stacked.png`.)

**The stranded-cost (CTA) piece specifically.** Connecticut's 1998 restructuring
(PA 98-28) let utilities recover **stranded costs** — the above-market book value
of pre-restructuring generation (legacy nuclear) and 1980s–90s purchased-power
contracts — through the **Competitive Transition Assessment (CTA)**, a
non-bypassable per-kWh charge collected from all distribution customers starting
Jan 1, 2000, partly securitized via rate-reduction bonds. It was ~1.0¢/kWh in the
mid-2000s (after a 2003 over-recovery credit), and — per the CT Office of Consumer
Counsel — the costs were **"majority recovered by 2011 for CL&P and 2013 for UI."**
By 2022 it is a small *credit* (−0.12¢). (`ct_cta_trajectory.png`.)

Two implications:
1. The CTA is, by definition, the cost of the **old** generation fleet and legacy
   contracts — a *restructuring* artifact, the **opposite** of a gas-adoption
   cost. It was elevated precisely across the 2005–09 window when CT diverged from
   its NE peers, then rolled off.
2. Its disappearance did **not** lower the bill, because wires + public-benefit
   charges (including the Millstone contract, carried in the post-2017 NBFMCC) grew
   far more than the CTA shrank. The CTA was the **first** wave of non-energy
   charges; others replaced and exceeded it.

*Scope note:* these are residential rate-class figures (the level at which CT
publishes component breakdowns), so they are not directly comparable to the
all-sector averages in Layer 1; they are used here to show bill *composition* and
its change, not absolute levels. Part 2 will generalize the supply-vs-delivery
split across states and add the winter gas basis.

## Findings — Layer 3 part 1b: delivery cost does not track gas adoption

If gas adoption were quietly driving up the *delivery* side of the bill, it would
rescue the "gas made power expensive" framing through a back door. It is not.
Across the 19 retail-choice states that report a delivery price, the **change** in
gas generation share is *not* a positive predictor of the **change** in real
delivery cost (2008–2020) — the relationship is weakly **negative**: Pearson
**r = −0.30**, slope −0.03 ¢/kWh per +1 pp. (`delivery_vs_gas_scatter.png`.)

The tells:
- **Heaviest gas adopters had flat delivery costs.** DE (+74 pp gas) +1.2¢, PA
  (+44 pp) +0.3¢, OH (+42 pp) −0.5¢, VA (+48 pp) −2.3¢.
- **California is the mirror image:** it *cut* its gas share (−10 pp) and had the
  *largest* delivery-cost rise (+6.5¢) — wildfire hardening and policy, not gas.
- **CT is high on both axes but sits *off* the trend**, not on a positive one
  (+31 pp gas, +4.0¢). Its delivery growth is CT-specific (storm hardening after
  2011, rate-case capital, grid-mod/ESI, FERC-rate transmission), not a gas effect.

This is the expected result: distribution and delivery are **fuel-agnostic** — the
wires cost the same regardless of what generated the power. The only thing a
careless analysis would catch is that gas adoption and grid spending both trended
up over the same years for unrelated reasons; the cross-state *change* test
removes that and the apparent link disappears.

*Scope note:* "delivery cost" here is the bundled all-sector Delivery-Only price
(T&D + policy), **not distribution alone** — EIA does not publish distribution
separately by state. Isolating distribution would require FERC Form 1.

## Reproducing

```bash
python scripts/download_data.py                      # pulls retail price + generation
python claims/03-rates/analyze_rates.py              # Layer 1: tables + charts
python claims/03-rates/analyze_bill_components.py    # Layer 3 pt 1: bill decomposition
python claims/03-rates/analyze_delivery_vs_gas.py    # Layer 3 pt 1b: delivery vs adoption
```

## Sources

- **EIA — Average retail price of electricity by state** (all sectors, cents/kWh),
  via the EIA bulk electricity archive (`ELEC.zip`, series `ELEC.PRICE.<ST>-ALL.A`).
  Current through the latest annual EIA release; no API key required.
- **EIA — Net Generation by State by fuel** (MWh): the gas-share numerator/
  denominator, shared with [Claim 01](../01-emissions/).
- **EIA — Average Price by State by Provider** (`avgprice_annual.xlsx`): the
  Delivery-Only provider category is the only state-level delivery-cost proxy;
  used in Layer 3 pt 1b. Frozen by EIA at 2020.
- **BLS — CPI-U** (deflator for real prices).
- **Connecticut bill components** (Layer 3 pt 1; data in `data/ct_bill_components.csv`):
  - CGA OLR Report [2006-R-0477](https://cga.ct.gov/2006/rpt/2006-R-0477.htm),
    *Components of Electric Bills* (CL&P residential, eff. Aug 2006).
  - CT Office of Consumer Counsel, *Electric Bill/Rate Components, August 2019*
    (Eversource Rate 1).
  - CT Office of Consumer Counsel, *Electric Bill/Rate Components, Effective
    January 1, 2022* (Eversource Rate 1).
  - CGA OLR Reports [98-R-0392](https://www.cga.ct.gov/PS98/rpt/olr/htm/98-R-0392.htm)
    and [2002-R-0973](https://www.cga.ct.gov/2002/olrdata/et/rpt/2002-R-0973.htm)
    (stranded costs / CTA mechanism), [2005-R-0102](https://www.cga.ct.gov/2005/rpt/2005-R-0102.htm)
    (2003 over-recovery CTA credit), and Conn. Gen. Stat. § 16-245g (CTA duration).
- *(Layer 3 pt 2)* EIA citygate gas price by state + Henry Hub; Algonquin Citygate
  basis; Census ACS B25040.
