"""
PRE_REG_037 fit: spatially-resolved (area-fraction-in-drought) SPEI ENSO test.
Drought year = fraction of region land area with SPEI<=-1.0 (the f10 column) >= 0.30
(locked primary). Sensitivity on the area-fraction cutoff (0.20/0.30/0.40), both bands.
Set A (Horn La Nina enrichment), Set B (Amazon El Nino), Set C (does 2020-22 register
+ does the spatial metric exceed the box-mean 50%).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
CSV = Path("D:/IDP/data/spei/spei210_spatial_ETH_SOM_BRA_1950_2023.csv")
ONI = Path("D:/IDP/data/oni.txt")
OUT = Path("D:/IDP/analysis/paper8_prereg037_spatial_enso_2026_05_28.json")
FRAC_CUTS = [0.20, 0.30, 0.40]
PRIMARY_CUT = 0.30
BOXMEAN_036 = 50.0  # PRE_REG_036 Horn box-mean La Nina share


def load_oni():
    df = pd.read_csv(ONI, sep=r"\s+")
    ond = df[df["SEAS"] == "OND"][["YR", "ANOM"]].rename(columns={"YR": "year", "ANOM": "oni"})
    ph = lambda o: "LaNina" if o <= -0.5 else ("ElNino" if o >= 0.5 else "neutral")
    ond["phase"] = ond["oni"].apply(ph)
    return ond.set_index("year")


def share(years, oni):
    if not years:
        return None, 0, 0, 0
    ph = [oni.loc[y, "phase"] for y in years if y in oni.index]
    nl = sum(p == "LaNina" for p in ph); ne = sum(p == "ElNino" for p in ph)
    return round(100 * nl / len(ph), 1), nl, ne, len(ph)


def main():
    df = pd.read_csv(CSV).set_index("year")
    oni = load_oni()
    yrs = [y for y in range(1950, 2024) if y in oni.index]
    base = round(100 * sum(oni.loc[y, "phase"] == "LaNina" for y in yrs) / len(yrs), 1)
    print(f"baseline La Nina 1950-2023: {base}%\n")

    out = {"baseline": base, "cuts": {}}
    for cut in FRAC_CUTS:
        print("=" * 84)
        print(f"AREA-FRACTION cutoff >= {cut}  (drought year = >= {int(cut*100)}% of land area SPEI<=-1.0)")
        print("=" * 84)
        cutd = {}
        for band, lbl in [("12", "annual SPEI_12"), ("03", "OND SPEI_03")]:
            def dyears(rg):
                col = f"{rg}_{band}_f10"
                s = df[col]
                return sorted(s[s >= cut].index.tolist())
            eth, som, bra = dyears("ETH"), dyears("SOM"), dyears("BRA")
            horn = sorted(set(eth + som))
            hp, hnl, hne, hn = share(horn, oni)
            bp, bnl, bne, bn = share(bra, oni)
            print(f"  [{lbl}]")
            print(f"    ETH  {eth}")
            print(f"    SOM  {som}")
            print(f"    HORN {horn} -> La Nina {hp}% ({hnl}LN/{hne}EN of {hn})")
            print(f"    BRA  {bra} -> La Nina {bp}% / El Nino {round(100*bne/bn,1) if bn else None}%")
            recent = [y for y in horn if y >= 2017]
            print(f"    >> Horn 2017+ drought-years registering: {recent}")
            cutd[band] = {"ETH": eth, "SOM": som, "HORN": horn, "horn_lanina_pct": hp,
                          "horn_nl": hnl, "horn_ne": hne, "n_horn": hn, "BRA": bra,
                          "bra_lanina_pct": bp, "bra_ne": bne, "n_bra": bn, "horn_recent": recent}
        out["cuts"][str(cut)] = cutd
        print()

    # verdicts: primary cut 0.30, annual band
    p = out["cuts"][str(PRIMARY_CUT)]["12"]
    hp = p["horn_lanina_pct"]; bp = p["bra_lanina_pct"]; bne = p["bra_ne"]; nbra = p["n_bra"]
    enrich = round(hp - base, 1) if hp is not None else None
    setA = hp is not None and hp >= 60 and enrich is not None and enrich >= 15
    bra_en = round(100 * bne / nbra, 1) if nbra else None
    setB = bp is not None and bp < 30 and bra_en is not None and bra_en > bp and (hp is None or bp < hp)
    setC_reg = len(p["horn_recent"]) > 0
    setC_exceed = hp is not None and (hp - BOXMEAN_036) >= 15
    print("=" * 84)
    print("VERDICTS (locked primary: area-fraction >= 0.30, annual SPEI_12, 1950-2023)")
    print("=" * 84)
    print(f"  Set A (Horn >=60% La Nina & enrich>=15pp): {hp}% (enrich {enrich}pp vs {base}%) -> {'SUPPORTED' if setA else 'NOT (F1)'}")
    print(f"  Set B (BRA El-Nino <30% La Nina): {bp}% LN / {bra_en}% EN -> {'SUPPORTED' if setB else 'NOT'}")
    print(f"  Set C-reg (2020-22 Horn drought registers): recent={p['horn_recent']} -> {'YES (metric fixed dilution)' if setC_reg else 'NO (F2 — metric still blind)'}")
    print(f"  Set C-exceed (spatial > box-mean 50% by >=15pp): {hp}% vs 50% -> {'YES (box-mean diluted real signal)' if setC_exceed else 'NO (weak signal robust to resolution)'}")
    out["verdicts"] = {"horn_lanina_pct": hp, "bra_lanina_pct": bp, "baseline": base,
                       "enrichment_pp": enrich, "setA": bool(setA), "setB": bool(setB),
                       "setC_registers": bool(setC_reg), "setC_exceeds_boxmean": bool(setC_exceed),
                       "horn_recent_drought_years": p["horn_recent"], "boxmean_036_pct": BOXMEAN_036}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
