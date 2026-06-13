"""
PRE_REG_038 — sub-national spatial co-location of compound-crisis coupling.
IDU event-level displacement (cause-tagged + geolocated) -> per-country spatial
co-location of Conflict-IDP vs Disaster-IDP across 1-degree grid cells (Spearman).
Cross-country: does spatial co-location track the national temporal coupling
(recomputed from GIDD, Conflict-IDP vs Disaster-IDP pooled, apples-to-apples)?

Set A: COD & SOM rho_spatial > +0.3 (positive cases co-locate)
Set B: UKR substitution (disaster<10% of IDP, or rho<=0)
Set C: cross-country rho_spatial ~ rho_national (positive)
Set D: PHL control rho_spatial ~ 0
"""
from __future__ import annotations
import glob, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
IDU_DIR = Path("D:/IDP/data/idmc_gidd/idu")
GIDD_DIS = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx")
GIDD_CONF = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Conflict_Violence_Disasters.xlsx")
OUT = Path("D:/IDP/analysis/paper8_prereg038_colocation_2026_05_28.json")
GRID = 1.0
MIN_EVENTS = 30  # per channel to compute a co-location


def load_idu():
    frames = []
    for f in glob.glob(str(IDU_DIR / "*.csv")):
        try:
            d = pd.read_csv(f, low_memory=False)
            frames.append(d)
        except Exception as e:
            print(f"  skip {Path(f).name}: {e}")
    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates(subset=["id"])
    df["figure"] = pd.to_numeric(df["figure"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df[df["displacement_type"].isin(["Conflict", "Disaster"])]
    df = df.dropna(subset=["figure", "latitude", "longitude", "iso3"])
    df = df[df["figure"] > 0]
    return df


def colocation(sub):
    sub = sub.copy()
    sub["cy"] = np.floor(sub["latitude"] / GRID) * GRID
    sub["cx"] = np.floor(sub["longitude"] / GRID) * GRID
    piv = sub.pivot_table(index=["cy", "cx"], columns="displacement_type",
                          values="figure", aggfunc="sum", fill_value=0.0)
    for c in ["Conflict", "Disaster"]:
        if c not in piv.columns:
            piv[c] = 0.0
    nc = int((sub["displacement_type"] == "Conflict").sum())
    nd = int((sub["displacement_type"] == "Disaster").sum())
    conff = float(sub.loc[sub["displacement_type"] == "Conflict", "figure"].sum())
    disf = float(sub.loc[sub["displacement_type"] == "Disaster", "figure"].sum())
    dis_share = round(disf / (conff + disf), 3) if (conff + disf) > 0 else None
    rho = None
    if nc >= MIN_EVENTS and nd >= MIN_EVENTS and len(piv) >= 5:
        if piv["Conflict"].std() > 0 and piv["Disaster"].std() > 0:
            r, p = stats.spearmanr(piv["Conflict"], piv["Disaster"])
            rho = (round(float(r), 3), round(float(p), 4))
    # top-quartile Jaccard
    jac = None
    if len(piv) >= 8:
        cq = piv["Conflict"] >= piv["Conflict"].quantile(0.75)
        dq = piv["Disaster"] >= piv["Disaster"].quantile(0.75)
        inter = int((cq & dq).sum()); uni = int((cq | dq).sum())
        jac = round(inter / uni, 3) if uni else None
    return {"n_conflict_ev": nc, "n_disaster_ev": nd, "n_cells": len(piv),
            "disaster_idp_share": dis_share, "rho_spatial": rho[0] if rho else None,
            "rho_p": rho[1] if rho else None, "topq_jaccard": jac}


def national_coupling():
    d = pd.read_excel(GIDD_DIS); d.columns = [c.strip() for c in d.columns]
    d["idp"] = pd.to_numeric(d["Disaster Internal Displacements"], errors="coerce")
    dis = d[d["Year"].between(2008, 2024)].groupby(["ISO3", "Year"])["idp"].sum().reset_index()
    c = pd.read_excel(GIDD_CONF); c.columns = [x.strip() for x in c.columns]
    c["idp"] = pd.to_numeric(c["Conflict Internal Displacements"], errors="coerce")
    con = c[c["Year"].between(2008, 2024)].groupby(["ISO3", "Year"])["idp"].sum().reset_index()
    out = {}
    for iso in set(dis["ISO3"]) | set(con["ISO3"]):
        a = dis[dis["ISO3"] == iso].set_index("Year")["idp"]
        b = con[con["ISO3"] == iso].set_index("Year")["idp"]
        yrs = sorted(set(range(2008, 2025)))
        av = a.reindex(yrs, fill_value=0).values
        bv = b.reindex(yrs, fill_value=0).values
        if np.std(av) > 0 and np.std(bv) > 0:
            r, _ = stats.spearmanr(av, bv)
            out[iso] = None if np.isnan(r) else round(float(r), 3)
    return out


def main():
    print("loading IDU...")
    idu = load_idu()
    print(f"  {len(idu)} cause-tagged geolocated events across {idu['iso3'].nunique()} countries")
    print("computing national temporal coupling from GIDD (pooled conflict vs disaster)...")
    natl = national_coupling()

    rows = {}
    for iso in sorted(idu["iso3"].unique()):
        sub = idu[idu["iso3"] == iso]
        co = colocation(sub)
        co["rho_national"] = natl.get(iso)
        rows[iso] = co

    # report table
    print("\n" + "=" * 100)
    print(f"{'ISO':4} {'nConf':>6} {'nDis':>6} {'disShr':>7} {'cells':>6} {'rho_spatial':>12} {'p':>7} {'jac':>6} {'rho_natl':>9}")
    print("=" * 100)
    for iso, r in sorted(rows.items(), key=lambda kv: (kv[1]["rho_spatial"] is None, -(kv[1]["rho_spatial"] or -9))):
        print(f"{iso:4} {r['n_conflict_ev']:>6} {r['n_disaster_ev']:>6} {str(r['disaster_idp_share']):>7} "
              f"{r['n_cells']:>6} {str(r['rho_spatial']):>12} {str(r['rho_p']):>7} {str(r['topq_jaccard']):>6} {str(r['rho_national']):>9}")

    # ---- verdicts ----
    def rs(iso): return rows.get(iso, {}).get("rho_spatial")
    print("\n" + "=" * 100); print("VERDICTS"); print("=" * 100)
    cod, som, ukr, phl = rs("COD"), rs("SOM"), rs("UKR"), rs("PHL")
    setA = cod is not None and som is not None and cod > 0.3 and som > 0.3
    ukr_share = rows.get("UKR", {}).get("disaster_idp_share")
    setB = (ukr_share is not None and ukr_share < 0.10) or (ukr is not None and ukr <= 0)
    print(f"  Set A (COD & SOM rho_spatial>+0.3): COD={cod} SOM={som} -> {'SUPPORTED' if setA else 'NOT (F1 if both ~0)'}")
    print(f"  Set B (UKR substitution: dis-share<10% OR rho<=0): dis_share={ukr_share} rho={ukr} -> {'SUPPORTED' if setB else 'NOT'}")
    print(f"  Set D (PHL control rho_spatial ~ 0): PHL={phl}")
    # Set C cross-country
    pairs = [(r["rho_spatial"], r["rho_national"]) for r in rows.values()
             if r["rho_spatial"] is not None and r["rho_national"] is not None]
    setC = None
    if len(pairs) >= 5:
        xs, ys = zip(*pairs)
        rc, pc = stats.spearmanr(xs, ys)
        setC = (round(float(rc), 3), round(float(pc), 4), len(pairs))
        print(f"  Set C (spatial co-location ~ national coupling, n={len(pairs)} countries): "
              f"Spearman rho={setC[0]} p={setC[1]} -> {'TRACKS' if rc > 0 and pc < 0.10 else 'does NOT track (F3)'}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"grid_deg": GRID, "rows": rows,
        "setA": bool(setA), "setB": bool(setB), "setC": setC,
        "cod": cod, "som": som, "ukr": ukr, "phl": phl}, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
