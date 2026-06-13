"""
Paper 2 — PRE_REG_015 Set B: r(USA storm-IDP, Atlantic MDR Aug-Oct SST).

The pre-reg window is 1980-2024. HadISST text release stops at 2003 and the GIDD
panel starts at 2008. Two windows are testable separately:
  WINDOW 1 (1980-2003, n=24): EM-DAT USA storm-affected x HadISST MDR SST
                              -- both on disk; fires now
  WINDOW 2 (2008-2024, n=17): GIDD USA storm-IDP x HadISST MDR SST
                              -- requires HadISST 2004-2024 (attempted separately)

This script fires WINDOW 1. USA storm-displacement is heavily right-skewed
(1999 Floyd ~3M vs most years <300K), so we report Pearson (the pre-reg metric)
plus log-Pearson and Spearman rank for robustness.

Pre-reg threshold: Pearson r >= +0.4 -> Set B supported. F2: r < 0.2 -> walk back.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")

SST_CSV = Path("D:/IDP/analysis/paper2_mdr_sst_monthly_2026_05_27.csv")
EMDAT = Path("D:/IDP/data/emdat/public_emdat_incl_hist_2026-05-18.xlsx")
OUT = Path("D:/IDP/analysis/paper2_prereg015_setB_2026_05_27.json")


def main():
    # --- MDR Aug-Oct SST per year ---
    sst = pd.read_csv(SST_CSV)
    ao = (
        sst[sst["month"].between(8, 10)]
        .groupby("year", as_index=False)["mdr_sst_c"]
        .mean()
        .rename(columns={"mdr_sst_c": "sst"})
    )

    # --- EM-DAT USA storm by year ---
    e = pd.read_excel(EMDAT)
    es = e[(e["Disaster Type"] == "Storm") & (e["ISO"] == "USA")].copy()
    es["year"] = pd.to_numeric(es["Start Year"], errors="coerce")
    es["affected"] = pd.to_numeric(es["Total Affected"], errors="coerce").fillna(0)
    es["homeless"] = pd.to_numeric(es["No. Homeless"], errors="coerce").fillna(0)
    ey = es.groupby("year").agg(
        affected=("affected", "sum"), homeless=("homeless", "sum")
    ).reset_index()

    # --- Merge on 1980-2003 overlap ---
    m = ey.merge(ao, on="year", how="inner")
    m = m[m["year"].between(1980, 2003)].sort_values("year")
    n = len(m)
    print(f"Window 1 (1980-2003): n={n} years")

    results = {"window_1980_2003": {"n": int(n)}}
    for metric in ["affected", "homeless"]:
        x = m[metric].values.astype(float)
        s = m["sst"].values.astype(float)
        # raw Pearson
        r_p, p_p = stats.pearsonr(x, s)
        # log Pearson
        r_l, p_l = stats.pearsonr(np.log1p(x), s)
        # Spearman rank
        r_s, p_s = stats.spearmanr(x, s)
        results["window_1980_2003"][metric] = {
            "pearson_r": float(r_p), "pearson_p": float(p_p),
            "log_pearson_r": float(r_l), "log_pearson_p": float(p_l),
            "spearman_r": float(r_s), "spearman_p": float(p_s),
        }
        print(f"\n  metric = {metric}:")
        print(f"    Pearson (raw):  r={r_p:+.3f} (p={p_p:.3f})")
        print(f"    Pearson (log):  r={r_l:+.3f} (p={p_l:.3f})")
        print(f"    Spearman rank:  r={r_s:+.3f} (p={p_s:.3f})")

    # ===== WINDOW 2 (2008-2024): GIDD-native storm-IDP x SST =====
    gidd = pd.read_excel(Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx"))
    gidd.columns = [c.strip() for c in gidd.columns]
    gidd["idp"] = pd.to_numeric(gidd["Disaster Internal Displacements"], errors="coerce")
    gs = gidd[(gidd["Hazard Type"] == "Storm") & (gidd["ISO3"] == "USA")]
    gy = gs.groupby("Year")["idp"].sum().reset_index().rename(columns={"Year": "year"})
    m2 = gy.merge(ao, on="year", how="inner")
    m2 = m2[m2["year"].between(2008, 2024)].sort_values("year")
    n2 = len(m2)
    print(f"\nWindow 2 (2008-2024, GIDD-native): n={n2} years")
    x2 = m2["idp"].values.astype(float)
    s2 = m2["sst"].values.astype(float)
    r2_p, p2_p = stats.pearsonr(x2, s2)
    r2_l, p2_l = stats.pearsonr(np.log1p(x2), s2)
    r2_s, p2_s = stats.spearmanr(x2, s2)
    results["window_2008_2024"] = {
        "n": int(n2),
        "idp": {
            "pearson_r": float(r2_p), "pearson_p": float(p2_p),
            "log_pearson_r": float(r2_l), "log_pearson_p": float(p2_l),
            "spearman_r": float(r2_s), "spearman_p": float(p2_s),
        },
    }
    print(f"    Pearson (raw):  r={r2_p:+.3f} (p={p2_p:.3f})")
    print(f"    Pearson (log):  r={r2_l:+.3f} (p={p2_l:.3f})")
    print(f"    Spearman rank:  r={r2_s:+.3f} (p={p2_s:.3f})")

    # ===== POOLED (1980-2024): z-scored within-segment to bridge metric change =====
    seg1 = m[["year", "affected", "sst"]].rename(columns={"affected": "disp"})
    seg2 = m2[["year", "idp", "sst"]].rename(columns={"idp": "disp"})
    # z-score displacement within each segment (different source metrics)
    seg1 = seg1.assign(disp_z=(np.log1p(seg1["disp"]) - np.log1p(seg1["disp"]).mean()) / np.log1p(seg1["disp"]).std())
    seg2 = seg2.assign(disp_z=(np.log1p(seg2["disp"]) - np.log1p(seg2["disp"]).mean()) / np.log1p(seg2["disp"]).std())
    pooled = pd.concat([seg1[["year", "disp_z", "sst"]], seg2[["year", "disp_z", "sst"]]])
    npool = len(pooled)
    rp_p, pp_p = stats.pearsonr(pooled["disp_z"], pooled["sst"])
    rp_s, ps_s = stats.spearmanr(pooled["disp_z"], pooled["sst"])
    results["pooled_1980_2024"] = {
        "n": int(npool),
        "method": "log + within-segment z-score (bridges EM-DAT affected <-> GIDD IDP metric change)",
        "pearson_r": float(rp_p), "pearson_p": float(pp_p),
        "spearman_r": float(rp_s), "spearman_p": float(ps_s),
    }
    print(f"\nPooled (1980-2024, z-scored within segment): n={npool}")
    print(f"    Pearson: r={rp_p:+.3f} (p={pp_p:.3f}) | Spearman: r={rp_s:+.3f} (p={ps_s:.3f})")

    # ===== VERDICT =====
    print("\n" + "=" * 70)
    print("PRE_REG_015 Set B verdict")
    print("=" * 70)
    r_w1 = results["window_1980_2003"]["affected"]["pearson_r"]
    r_w2 = r2_p
    print(f"  Window 1 (1980-2003, EM-DAT): r={r_w1:+.3f}")
    print(f"  Window 2 (2008-2024, GIDD):   r={r_w2:+.3f}  <- GIDD-native, primary")
    print(f"  Pooled  (1980-2024, z-score): r={rp_p:+.3f}")
    print(f"  Threshold >= +0.4 | F2 (r<0.2)")

    def classify(r):
        if r >= 0.4:
            return "SUPPORTED"
        if r < 0.2:
            return "F2 FIRED"
        return "INCONCLUSIVE"

    verdict = {
        "window_1980_2003": classify(r_w1),
        "window_2008_2024_primary": classify(r_w2),
        "pooled_1980_2024": classify(rp_p),
    }
    for k, v in verdict.items():
        print(f"    {k}: {v}")

    results["verdict"] = verdict
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
