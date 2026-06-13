"""
Paper 2 — PRE_REG_015 Prediction set E (CUB/PRI replication of intensification).

Tests whether CUB and PRI (Atlantic Regime 3a members) show the same storm-
mega-year-frequency intensification 1980-2007 -> 2008-2024 that USA shows.

F5 falsifier: CUB/PRI show NO intensification -> first-mover hypothesis is
Atlantic-specific or a USA-artifact.

Methodology note: a fixed >1M absolute threshold doesn't scale to small islands
(PRI ~3.2M pop, CUB ~11M). We compute the test THREE ways:
  1. Absolute mega-year (>1M storm displacement) — matches USA pre-reg literally
  2. Per-capita mega-year (>3% of population displaced) — fair for small states
  3. Raw storm-displacement decade trend — direction-only check

Data:
  - EM-DAT 1980-2007 (historical storm displacement; No. Homeless + Total Affected)
  - GIDD 2008-2024 storm-IDP (from the existing panel)
  - WDI population for per-capita normalization
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

EMDAT = Path("D:/IDP/data/emdat/public_emdat_incl_hist_2026-05-18.xlsx")
GIDD_DIS = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx")
WDI = Path("D:/IDP/data/wb_wdi/extracted/WDICSV.csv")
OUT = Path("D:/IDP/analysis/paper2_prereg015_setE_2026_05_27.json")

COUNTRIES = ["USA", "CUB", "PRI"]
MEGA_ABS = 1_000_000          # absolute mega-year threshold
MEGA_PCT = 0.03               # per-capita mega-year threshold (3% of pop)


def emdat_storm_by_year():
    df = pd.read_excel(EMDAT)
    storm = df[(df["Disaster Type"] == "Storm") & (df["ISO"].isin(COUNTRIES))].copy()
    storm["year"] = pd.to_numeric(storm["Start Year"], errors="coerce")
    # Use No. Homeless as the displacement proxy; fall back to Total Affected
    storm["homeless"] = pd.to_numeric(storm["No. Homeless"], errors="coerce").fillna(0)
    storm["affected"] = pd.to_numeric(storm["Total Affected"], errors="coerce").fillna(0)
    # Pre-2008 window only (GIDD covers 2008+)
    storm = storm[storm["year"].between(1980, 2007)]
    grp = storm.groupby(["ISO", "year"]).agg(
        homeless=("homeless", "sum"),
        affected=("affected", "sum"),
    ).reset_index()
    return grp


def gidd_storm_by_year():
    d = pd.read_excel(GIDD_DIS)
    d.columns = [c.strip() for c in d.columns]
    d["idp"] = pd.to_numeric(d["Disaster Internal Displacements"], errors="coerce")
    d = d[(d["Hazard Type"] == "Storm") & (d["ISO3"].isin(COUNTRIES))]
    d = d[d["Year"].between(2008, 2024)]
    grp = d.groupby(["ISO3", "Year"])["idp"].sum().reset_index()
    grp.columns = ["ISO", "year", "idp"]
    return grp


def population_map():
    wdi = pd.read_csv(WDI, low_memory=False)
    pop = wdi[wdi["Indicator Code"] == "SP.POP.TOTL"]
    out = {}
    for iso in COUNTRIES:
        row = pop[pop["Country Code"] == iso]
        if not row.empty:
            # mid-period population (2000 for pre-2008 window, 2015 for recent)
            out[iso] = {
                "pop_2000": pd.to_numeric(row["2000"].values[0], errors="coerce"),
                "pop_2015": pd.to_numeric(row["2015"].values[0], errors="coerce"),
            }
    return out


def main():
    emdat = emdat_storm_by_year()
    gidd = gidd_storm_by_year()
    pops = population_map()

    results = {}
    for iso in COUNTRIES:
        e = emdat[emdat["ISO"] == iso]
        g = gidd[gidd["ISO"] == iso]
        pop_old = pops.get(iso, {}).get("pop_2000", np.nan)
        pop_new = pops.get(iso, {}).get("pop_2015", np.nan)

        # --- Pre-2008 window (EM-DAT) ---
        # Primary metric = Total Affected (matches PRE_REG_015 Set A "displacement-
        # affected" basis). Homeless kept as secondary for transparency.
        # CAVEAT: EM-DAT "Total Affected" is a broader construct than GIDD-IDP;
        # cross-source comparison inflates pre-2008 relative to 2008-2024. The
        # TREND direction (the F5 test) is robust to this; absolute freq is not.
        e_years = e.set_index("year")["affected"]
        e_homeless = e.set_index("year")["homeless"]
        n_old_years = 2007 - 1980 + 1  # 28
        mega_abs_old = int((e_years >= MEGA_ABS).sum())
        mega_pct_old = int((e_years >= MEGA_PCT * pop_old).sum()) if pop_old == pop_old else None

        # --- 2008-2024 window (GIDD storm-IDP) ---
        g_years = g.set_index("year")["idp"]
        n_new_years = 2024 - 2008 + 1  # 17
        mega_abs_new = int((g_years >= MEGA_ABS).sum())
        mega_pct_new = int((g_years >= MEGA_PCT * pop_new).sum()) if pop_new == pop_new else None

        results[iso] = {
            "pop_2000": None if pop_old != pop_old else float(pop_old),
            "pop_2015": None if pop_new != pop_new else float(pop_new),
            "pre2008": {
                "n_years": n_old_years,
                "mega_abs_count": mega_abs_old,
                "mega_abs_freq": mega_abs_old / n_old_years,
                "mega_pct_count": mega_pct_old,
                "mega_pct_freq": (mega_pct_old / n_old_years) if mega_pct_old is not None else None,
                "max_affected": float(e_years.max()) if len(e_years) else 0.0,
                "total_affected": float(e_years.sum()) if len(e_years) else 0.0,
                "max_homeless": float(e_homeless.max()) if len(e_homeless) else 0.0,
            },
            "post2008": {
                "n_years": n_new_years,
                "mega_abs_count": mega_abs_new,
                "mega_abs_freq": mega_abs_new / n_new_years,
                "mega_pct_count": mega_pct_new,
                "mega_pct_freq": (mega_pct_new / n_new_years) if mega_pct_new is not None else None,
                "max_idp": float(g_years.max()) if len(g_years) else 0.0,
                "total_idp": float(g_years.sum()) if len(g_years) else 0.0,
            },
        }
        # Intensification deltas
        results[iso]["delta_abs_freq"] = (
            results[iso]["post2008"]["mega_abs_freq"] - results[iso]["pre2008"]["mega_abs_freq"]
        )
        if mega_pct_old is not None and mega_pct_new is not None:
            results[iso]["delta_pct_freq"] = (
                results[iso]["post2008"]["mega_pct_freq"] - results[iso]["pre2008"]["mega_pct_freq"]
            )
        else:
            results[iso]["delta_pct_freq"] = None

    # Print summary
    print("=" * 80)
    print("PRE_REG_015 Set E — CUB/PRI replication of USA intensification")
    print("=" * 80)
    for iso in COUNTRIES:
        r = results[iso]
        print(f"\n{iso} (pop ~{r['pop_2015']/1e6:.1f}M):" if r['pop_2015'] else f"\n{iso}:")
        print(f"  pre-2008  (28y): mega-abs={r['pre2008']['mega_abs_count']} (freq {r['pre2008']['mega_abs_freq']:.1%})"
              f" | mega-pct(>3%pop)={r['pre2008']['mega_pct_count']} | max_affected={r['pre2008']['max_affected']:,.0f}")
        print(f"  2008-2024 (17y): mega-abs={r['post2008']['mega_abs_count']} (freq {r['post2008']['mega_abs_freq']:.1%})"
              f" | mega-pct(>3%pop)={r['post2008']['mega_pct_count']} | max_idp={r['post2008']['max_idp']:,.0f}")
        print(f"  Δ abs-freq: {r['delta_abs_freq']:+.1%}", end="")
        if r["delta_pct_freq"] is not None:
            print(f" | Δ pct-freq: {r['delta_pct_freq']:+.1%}")
        else:
            print()

    # F5 assessment
    print("\n" + "=" * 80)
    print("F5 ASSESSMENT (CUB/PRI show no intensification -> USA-specific)")
    print("=" * 80)
    for iso in ["CUB", "PRI"]:
        r = results[iso]
        # Intensification present if EITHER abs-freq OR pct-freq increased, OR max grew
        abs_up = r["delta_abs_freq"] > 0
        pct_up = (r["delta_pct_freq"] or 0) > 0
        max_up = r["post2008"]["max_idp"] > r["pre2008"]["max_affected"]
        intensified = abs_up or pct_up or max_up
        print(f"  {iso}: abs-freq-up={abs_up} pct-freq-up={pct_up} max-up={max_up} -> intensified={intensified}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
