"""
PRE_REG_036 (P8-F) fit from the GEE v2.10 CSV (spei210_dec_ETH_SOM_BRA_1950_2023.csv).
December 12-month (locked primary) + 3-month OND (Horn secondary) SPEI area-means
vs OND-season NOAA ONI. Set A (Horn La Nina enrichment), Set B (Amazon El Nino),
Set C (vs displacement 50% from PRE_REG_034).

Diagnostic-first: prints the full series w/ ENSO phase and every drought-year before verdicts.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

CSV = Path("D:/IDP/data/spei/spei210_dec_ETH_SOM_BRA_1950_2023.csv")
ONI = Path("D:/IDP/data/oni.txt")
OUT = Path("D:/IDP/analysis/paper8_prereg036_spei210_enso_2026_05_28.json")
THRS = [-0.8, -1.0, -1.5]
PRIMARY = -1.0
DISP_034 = 50.0  # PRE_REG_034 Horn displacement La Nina share


def load_oni():
    df = pd.read_csv(ONI, sep=r"\s+")
    ond = df[df["SEAS"] == "OND"][["YR", "ANOM"]].rename(columns={"YR": "year", "ANOM": "oni"})
    def ph(o):
        return "LaNina" if o <= -0.5 else ("ElNino" if o >= 0.5 else "neutral")
    ond["phase"] = ond["oni"].apply(ph)
    return ond.set_index("year")


def drought_years(s, thr):
    return sorted(s[s <= thr].index.tolist())


def lanina_share(years, oni):
    if not years:
        return None, 0, 0
    ph = [oni.loc[y, "phase"] for y in years if y in oni.index]
    nl = sum(p == "LaNina" for p in ph)
    ne = sum(p == "ElNino" for p in ph)
    return round(100 * nl / len(ph), 1), nl, ne


def main():
    df = pd.read_csv(CSV).set_index("year")
    oni = load_oni()
    df["phase"] = [oni.loc[y, "phase"] if y in oni.index else "?" for y in df.index]

    yrs = [y for y in range(1950, 2024) if y in oni.index]
    base = round(100 * sum(oni.loc[y, "phase"] == "LaNina" for y in yrs) / len(yrs), 1)

    print("=" * 90)
    print("Full series (SPEI v2.10 Dec area-means) with OND ENSO phase")
    print("=" * 90)
    show = df[["phase", "ETH_12", "SOM_12", "BRA_12", "ETH_03", "SOM_03", "BRA_03"]]
    print(show.to_string())
    print(f"\nbaseline La Nina rate 1950-2023: {base}%")

    out = {"baseline_lanina_pct": base, "windows": {}}
    for (y0, y1, key) in [(1950, 2023, "full"), (2008, 2023, "w2008")]:
        print("\n" + "=" * 90)
        print(f"WINDOW {y0}-{y1}")
        print("=" * 90)
        sub = df[(df.index >= y0) & (df.index <= y1)]
        wbase = round(100 * sum(oni.loc[y, "phase"] == "LaNina" for y in range(y0, y1 + 1) if y in oni.index)
                      / len([y for y in range(y0, y1 + 1) if y in oni.index]), 1)
        wd = {"baseline": wbase, "thr": {}}
        for thr in THRS:
            print(f"\n  -- threshold SPEI <= {thr} --  (baseline La Nina {wbase}%)")
            entry = {}
            for band, label in [("12", "annual SPEI_12"), ("03", "OND SPEI_03")]:
                eth = drought_years(sub[f"ETH_{band}"], thr)
                som = drought_years(sub[f"SOM_{band}"], thr)
                bra = drought_years(sub[f"BRA_{band}"], thr)
                horn = sorted(set(eth + som))
                hpct, hnl, hne = lanina_share(horn, oni)
                bpct, bnl, bne = lanina_share(bra, oni)
                print(f"     [{label}]")
                print(f"       ETH drought-yrs {eth}")
                print(f"       SOM drought-yrs {som}")
                print(f"       HORN combined {horn}  -> La Nina {hpct}% ({hnl}LN/{hne}EN of {len(horn)})")
                print(f"       BRA  drought-yrs {bra}  -> La Nina {bpct}% / El Nino {round(100*bne/len(bra),1) if bra else None}%")
                entry[band] = {"ETH": eth, "SOM": som, "HORN": horn, "horn_lanina_pct": hpct,
                               "horn_nl": hnl, "horn_ne": hne, "BRA": bra, "bra_lanina_pct": bpct,
                               "bra_ne": bne, "n_horn": len(horn), "n_bra": len(bra)}
            wd["thr"][str(thr)] = entry
        out["windows"][key] = wd

    # ---- verdicts: primary = full window, thr -1.0, annual band (locked) ----
    prim = out["windows"]["full"]["thr"][str(PRIMARY)]["12"]
    hpct = prim["horn_lanina_pct"]; bpct = prim["bra_lanina_pct"]; bne = prim["bra_ne"]; nbra = prim["n_bra"]
    enrich = round(hpct - base, 1) if hpct is not None else None
    setA = hpct is not None and hpct >= 60 and enrich is not None and enrich >= 15
    bra_en_pct = round(100 * bne / nbra, 1) if nbra else None
    setB = bpct is not None and bpct < 30 and bra_en_pct is not None and bra_en_pct > bpct and (hpct is None or bpct < hpct)
    setC = hpct is not None and (hpct - DISP_034) >= 15
    print("\n" + "=" * 90)
    print("VERDICTS (locked primary: full window 1950-2023, annual SPEI_12, thr -1.0)")
    print("=" * 90)
    print(f"  Set A (Horn >=60% La Nina & enrich>=15pp): {hpct}% (enrich {enrich}pp vs {base}%) -> {'SUPPORTED' if setA else 'NOT SUPPORTED (F1)'}")
    print(f"  Set B (BRA El-Nino-aligned <30% La Nina): BRA {bpct}% LN / {bra_en_pct}% EN -> {'SUPPORTED' if setB else 'NOT'}")
    print(f"  Set C (Horn SPEI exceeds displacement 50% by >=15pp -> 034 artifact): {hpct}% vs 50% -> {'CONFIRMED' if setC else 'NOT (F2)'}")
    out["verdicts"] = {"horn_lanina_pct": hpct, "bra_lanina_pct": bpct, "baseline": base,
                       "enrichment_pp": enrich, "setA": bool(setA), "setB": bool(setB),
                       "setC_artifact": bool(setC), "displacement_034_pct": DISP_034}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
