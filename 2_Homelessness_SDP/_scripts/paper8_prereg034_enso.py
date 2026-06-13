"""
Paper 8 — PRE_REG_034 ENSO teleconnection test.

Horn-of-Africa drought works through East-African short-rains (Oct-Dec) failure,
which is driven by La Nina. So each year is classified by its OND-season ONI
(La Nina <= -0.5, El Nino >= +0.5, neutral between).

Set A: ETH+SOM drought-displacement mega-years fall disproportionately in
       La Nina years (predicted >=60%).
Set B: conflict-displacement peaks lag drought peaks by 0-1 yr (cross-corr).
Set C: BRA (Amazon) CD coupling LESS ENSO-aligned than Horn (different driver).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")

ONI = Path("D:/IDP/data/oni.txt")
GIDD_DIS = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx")
GIDD_CONF = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Conflict_Violence_Disasters.xlsx")
OUT = Path("D:/IDP/analysis/paper8_prereg034_enso_2026_05_28.json")


def load_oni_ond():
    df = pd.read_csv(ONI, sep=r"\s+")
    ond = df[df["SEAS"] == "OND"][["YR", "ANOM"]].rename(columns={"YR": "year", "ANOM": "oni"})
    def phase(o):
        if o <= -0.5: return "LaNina"
        if o >= 0.5: return "ElNino"
        return "neutral"
    ond["phase"] = ond["oni"].apply(phase)
    return ond.set_index("year")


def gidd_channel(iso, hazard=None, conflict=False):
    if conflict:
        c = pd.read_excel(GIDD_CONF); c.columns = [x.strip() for x in c.columns]
        c["idp"] = pd.to_numeric(c["Conflict Internal Displacements"], errors="coerce")
        c = c[(c["ISO3"] == iso) & c["Year"].between(2008, 2024)]
        return c.groupby("Year")["idp"].sum()
    d = pd.read_excel(GIDD_DIS); d.columns = [x.strip() for x in d.columns]
    d["idp"] = pd.to_numeric(d["Disaster Internal Displacements"], errors="coerce")
    d = d[(d["ISO3"] == iso) & (d["Hazard Type"] == hazard) & d["Year"].between(2008, 2024)]
    return d.groupby("Year")["idp"].sum()


def main():
    oni = load_oni_ond()
    # cache conflict workbook reads
    drought = {iso: gidd_channel(iso, hazard="Drought") for iso in ["ETH", "SOM", "BRA"]}
    conflict = {iso: gidd_channel(iso, conflict=True) for iso in ["ETH", "SOM", "BRA"]}

    # ---- Set A: drought mega-years vs ENSO phase (ETH + SOM) ----
    print("=" * 76)
    print("PRE_REG_034 Set A — Horn drought mega-years vs ENSO (OND ONI)")
    print("=" * 76)
    setA = {}
    horn_mega_phases = []
    for iso in ["ETH", "SOM"]:
        s = drought[iso]
        s = s[s > 0]
        if len(s) == 0:
            continue
        med = s.median()
        mega_years = sorted(s[s >= med].index.tolist())  # drought years at/above country median
        phases = {y: oni.loc[y, "phase"] if y in oni.index else "?" for y in mega_years}
        n_lanina = sum(1 for p in phases.values() if p == "LaNina")
        setA[iso] = {"mega_years": mega_years, "phases": phases,
                     "n_lanina": n_lanina, "n_total": len(mega_years),
                     "pct_lanina": round(100 * n_lanina / len(mega_years), 1) if mega_years else None}
        horn_mega_phases.extend(phases.values())
        print(f"  {iso}: drought mega-years (>=median) = {mega_years}")
        print(f"       phases = {phases}")
        print(f"       La Nina: {n_lanina}/{len(mega_years)} = {setA[iso]['pct_lanina']}%")
    horn_pct = round(100 * sum(1 for p in horn_mega_phases if p == "LaNina") / len(horn_mega_phases), 1) if horn_mega_phases else None
    # baseline: fraction of all 2008-2024 years that are La Nina
    base_lanina = round(100 * sum(1 for y in range(2008, 2025) if oni.loc[y, "phase"] == "LaNina") / 17, 1)
    print(f"\n  Horn combined drought-mega La Nina share: {horn_pct}% (baseline all-years: {base_lanina}%)")
    setA_supported = horn_pct is not None and horn_pct >= 60

    # ---- Set B: conflict lags drought (cross-correlation) ----
    print("\n" + "=" * 76)
    print("Set B — conflict lags drought (ETH+SOM), lags 0/1/2 yr")
    print("=" * 76)
    setB = {}
    for iso in ["ETH", "SOM"]:
        dser = drought[iso].reindex(range(2008, 2025), fill_value=0)
        cser = conflict[iso].reindex(range(2008, 2025), fill_value=0)
        lags = {}
        for lag in [0, 1, 2]:
            d_v = dser.values[:len(dser) - lag] if lag else dser.values
            c_v = cser.values[lag:] if lag else cser.values
            if np.std(d_v) > 0 and np.std(c_v) > 0:
                r, _ = stats.spearmanr(d_v, c_v)
                lags[lag] = None if np.isnan(r) else round(float(r), 3)
            else:
                lags[lag] = None
        best_lag = max([l for l in lags if lags[l] is not None], key=lambda l: lags[l], default=None)
        setB[iso] = {"lag_corr": lags, "best_lag": best_lag}
        print(f"  {iso}: lag0={lags[0]} lag1={lags[1]} lag2={lags[2]} -> best lag = {best_lag}")

    # ---- Set C: BRA control ----
    print("\n" + "=" * 76)
    print("Set C — BRA (Amazon) drought-mega ENSO alignment (control)")
    print("=" * 76)
    s = drought["BRA"]; s = s[s > 0]
    bra_pct = None
    if len(s) > 0:
        med = s.median()
        mega = sorted(s[s >= med].index.tolist())
        phases = {y: oni.loc[y, "phase"] if y in oni.index else "?" for y in mega}
        n_l = sum(1 for p in phases.values() if p == "LaNina")
        bra_pct = round(100 * n_l / len(mega), 1) if mega else None
        print(f"  BRA drought mega-years = {mega}")
        print(f"       phases = {phases}")
        print(f"       La Nina: {n_l}/{len(mega)} = {bra_pct}%")
    print(f"\n  BRA La Nina share {bra_pct}% vs Horn {horn_pct}% -> BRA {'LESS' if (bra_pct or 0) < (horn_pct or 0) else 'NOT less'} ENSO(La Nina)-aligned")

    # ---- Verdicts ----
    print("\n" + "=" * 76)
    print("VERDICTS")
    print("=" * 76)
    print(f"  Set A (Horn drought-mega >=60% La Nina): {horn_pct}% -> {'SUPPORTED' if setA_supported else 'NOT SUPPORTED (F1)'}")
    print(f"     (vs {base_lanina}% baseline La Nina rate — enrichment {'YES' if horn_pct and horn_pct > base_lanina else 'NO'})")
    b_ok = any(setB[i]["best_lag"] in (0, 1) for i in setB)
    print(f"  Set B (conflict lags drought 0-1yr): best lags {[setB[i]['best_lag'] for i in setB]} -> {'consistent' if b_ok else 'CHECK'}")
    print(f"  Set C (BRA less La-Nina-aligned than Horn): BRA {bra_pct}% vs Horn {horn_pct}%")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "setA": setA, "horn_lanina_pct": horn_pct, "baseline_lanina_pct": base_lanina,
        "setA_supported": bool(setA_supported), "setB": setB,
        "setC_bra_lanina_pct": bra_pct,
    }, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
