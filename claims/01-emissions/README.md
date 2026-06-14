# Claim 01 — "Emissions are up"

## The claim

> _"[Paste the exact CCEA / Carstensen quote here, with citation and date.]"_

The claim, as commonly stated, is that the shift toward natural gas in the power
sector has **driven emissions up**. This page tests that against the official
record.

## The data

**Source:** U.S. Energy Information Administration (EIA), *Emissions by State by
Year* — the federal government's official accounting of **electric-power-sector**
emissions of CO₂, SO₂, and NOx, by state and fuel, from 1990 to 2024.

- URL: <https://www.eia.gov/electricity/data/state/emission_annual.xlsx>
- Scope: **electric power sector only** (not economy-wide; transportation and
  building heating are not included here).
- Geography: Connecticut, with the U.S. total for context. (CCEA is the
  Connecticut Center for Economic Analysis, so Connecticut is the natural focus.)

Reproduce everything on this page:

```bash
python scripts/download_data.py
python claims/01-emissions/analyze_emissions.py          # Connecticut
python claims/01-emissions/analyze_emissions.py --state US-TOTAL
```

## What the data shows

Connecticut power-sector emissions, EIA *Total Electric Power Industry*:

| Pollutant | 1990 | Peak | Latest (2024) | vs 1990 | vs peak |
|-----------|-----:|-----:|--------------:|--------:|--------:|
| CO₂ (metric tons) | 12,103,268 | 14,495,967 (1997) | 11,001,595 | **−9.1%** | **−24.1%** |
| SO₂ (metric tons) | 52,235 | 53,078 (1997) | 313 | **−99.4%** | **−99.4%** |
| NOx (metric tons) | 31,512 | 31,512 (1990) | 4,363 | **−86.2%** | **−86.2%** |

The national picture moves the same direction (U.S. power-sector CO₂ −21% vs
1990 and −40% vs its 2007 peak; SO₂ −95%; NOx −86%).

![Connecticut power-sector emissions indexed to 1990=100](output/CT_pollutant_trends.png)

### The fuel switch behind it

Connecticut's power sector ran on **coal and oil** in 1990. By 2024 those were
almost entirely displaced by natural gas — and that switch is exactly what drove
the emissions down:

| Fuel (CO₂, metric tons) | 1990 | 2024 |
|-------------------------|-----:|-----:|
| Coal | 3,560,469 | 0 |
| Petroleum (oil) | 7,382,393 | 81,131 |
| Natural Gas | 697,643 | 10,214,445 |

![Connecticut power-sector CO₂ by fuel](output/CT_co2_fuel_mix.png)

## Verdict

**The claim that power-sector emissions are "up" is not supported by the EIA
record.** Every pollutant EIA tracks is *below* its 1990 level and far below its
peak:

- **SO₂ is down 99.4%** and **NOx is down 86%** — the criteria pollutants most
  directly tied to public health (smog, acid rain, fine particulates).
- **CO₂ is down 9% from 1990 and 24% from its peak**, even though Connecticut's
  power sector generates more electricity today than it did then.

The driver is unambiguous in the fuel data: natural gas displaced the coal and
oil that Connecticut's grid used to burn.

## An honest caveat

Intellectual honesty requires noting the one place the trend is *not* monotonic:
Connecticut power-sector **CO₂ rose from its 2017 low (~7.9M t) back to ~11.0M t
in 2024**. So a critic could cherry-pick "CO₂ is up since 2017" — but that is a
selective baseline. Against the standard 1990 reference, and against the
all-time peak, CO₂ is down, and the health-relevant criteria pollutants have
collapsed. The choice of baseline year, pollutant, and scope (power sector vs.
economy-wide) determines the answer, which is precisely why this analysis states
all three explicitly.

> **To finalize:** drop the exact CCEA quote (with its baseline year and whether
> it refers to the power sector or the whole economy) into "The claim" above so
> the rebuttal addresses their wording precisely.
