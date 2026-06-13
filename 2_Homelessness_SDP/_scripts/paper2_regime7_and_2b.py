"""
Paper 2 — two typology-refinement tests (decision rules pre-committed in header).

THREAD 1 (PATTERN_029): Regime 7 wildfire-dominant?
  - Confirm GRC wildfire-IDP >= 60% of its disaster-IDP
  - Regime 7 REAL if >= 2 additional Mediterranean countries
    (ESP/PRT/CYP/ITA/TUR/FRA/HRV) have wildfire share >= 30%
  - WALKS BACK to GRC-anomaly if GRC is the only one >= 30%

THREAD 2 (PATTERN_030): Regime 2b flood-dominant transitional?
  - Confirm ARG/KHM: flood >= 70% AND storm in [10%, 30%] (multi-mechanism)
  - R2b REAL if >= 2 additional candidates (COL/IRQ/VNM/BGD) also fall in
    flood >= 70% + storm in [10%, 30%] gap
  - WALKS BACK to boundary-doc if only ARG/KHM qualify

Uses the FULL GIDD hazard taxonomy (Wildfire is a real top-level hazard type,
not lumped into "Other").
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

GIDD = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx")
OUT = Path("D:/IDP/analysis/paper2_regime7_2b_2026_05_27.json")

MED_CANDIDATES = ["GRC", "ESP", "PRT", "CYP", "ITA", "TUR", "FRA", "HRV"]
FLOOD_CANDIDATES = ["ARG", "KHM", "COL", "IRQ", "VNM", "BGD", "THA", "PAK"]


def load():
    d = pd.read_excel(GIDD)
    d.columns = [c.strip() for c in d.columns]
    d["idp"] = pd.to_numeric(d["Disaster Internal Displacements"], errors="coerce")
    d = d[d["Year"].between(2008, 2024)].dropna(subset=["idp", "ISO3", "Hazard Type"])
    return d


def channel_shares(d, iso):
    sub = d[d["ISO3"] == iso]
    total = sub["idp"].sum()
    if total <= 0:
        return None
    shares = (sub.groupby("Hazard Type")["idp"].sum() / total * 100).sort_values(ascending=False)
    return total, shares


def flood_max_median(d, iso):
    sub = d[(d["ISO3"] == iso) & (d["Hazard Type"] == "Flood")]
    yearly = sub.groupby("Year")["idp"].sum()
    if len(yearly) < 2 or yearly.median() == 0:
        return None
    return float(yearly.max() / yearly.median())


def main():
    d = load()

    # ===== THREAD 1: Regime 7 wildfire =====
    print("=" * 80)
    print("THREAD 1 — Regime 7 (Wildfire-dominant)?")
    print("=" * 80)
    med = {}
    for iso in MED_CANDIDATES:
        res = channel_shares(d, iso)
        if res is None:
            print(f"  {iso}: no data")
            continue
        total, shares = res
        wildfire = float(shares.get("Wildfire", 0.0))
        top_channel = shares.index[0]
        med[iso] = {
            "total_idp": float(total),
            "wildfire_share": wildfire,
            "top_channel": top_channel,
            "top_share": float(shares.iloc[0]),
            "all_shares": {k: float(v) for k, v in shares.items()},
        }
        print(f"  {iso}: total={total:>10,.0f} | wildfire={wildfire:5.1f}% | top={top_channel} ({shares.iloc[0]:.1f}%)")

    grc_wildfire = med.get("GRC", {}).get("wildfire_share", 0)
    grc_confirmed = grc_wildfire >= 60
    others_30 = [iso for iso, m in med.items() if iso != "GRC" and m["wildfire_share"] >= 30]
    regime7_real = len(others_30) >= 2
    print(f"\n  GRC wildfire share: {grc_wildfire:.1f}% -> GRC wildfire-dominant: {grc_confirmed}")
    print(f"  Other Mediterranean countries with wildfire >= 30%: {others_30}")
    print(f"  REGIME 7 VERDICT: {'REAL (>=2 co-validators)' if regime7_real else 'GRC-ANOMALY (walks back)'}")

    # ===== THREAD 2: Regime 2b flood-transitional =====
    print("\n" + "=" * 80)
    print("THREAD 2 — Regime 2b (Flood-dominant transitional)?")
    print("=" * 80)
    flood = {}
    for iso in FLOOD_CANDIDATES:
        res = channel_shares(d, iso)
        if res is None:
            print(f"  {iso}: no data")
            continue
        total, shares = res
        flood_sh = float(shares.get("Flood", 0.0))
        storm_sh = float(shares.get("Storm", 0.0))
        fmm = flood_max_median(d, iso)
        in_gap = (flood_sh >= 70) and (10 <= storm_sh <= 30)
        flood[iso] = {
            "total_idp": float(total),
            "flood_share": flood_sh,
            "storm_share": storm_sh,
            "flood_max_median": fmm,
            "in_transitional_gap": in_gap,
        }
        gap_flag = " <-- GAP" if in_gap else ""
        fmm_str = f"{fmm:.1f}x" if fmm is not None else "n/a"
        print(f"  {iso}: flood={flood_sh:5.1f}% storm={storm_sh:5.1f}% flood-max/med={fmm_str}{gap_flag}")

    anchor_qualify = all(flood.get(i, {}).get("in_transitional_gap", False) for i in ["ARG", "KHM"])
    additional = [iso for iso in FLOOD_CANDIDATES if iso not in ("ARG", "KHM")
                  and flood.get(iso, {}).get("in_transitional_gap", False)]
    r2b_real = len(additional) >= 2
    print(f"\n  ARG + KHM both in gap (flood>=70% + storm 10-30%): {anchor_qualify}")
    print(f"  Additional candidates in gap: {additional}")
    print(f"  REGIME 2b VERDICT: {'REAL (>=2 additional members)' if r2b_real else 'BOUNDARY-DOC (walks back to documentation)'}")

    out = {
        "thread1_regime7": {
            "mediterranean": med,
            "grc_wildfire_share": grc_wildfire,
            "grc_confirmed_dominant": grc_confirmed,
            "co_validators_30pct": others_30,
            "regime7_real": regime7_real,
        },
        "thread2_regime2b": {
            "flood_candidates": flood,
            "anchor_arg_khm_qualify": anchor_qualify,
            "additional_in_gap": additional,
            "regime2b_real": r2b_real,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
