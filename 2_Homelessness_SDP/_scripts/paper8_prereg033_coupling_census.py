"""
Paper 8 — PRE_REG_033 Phase 1 coupling census.

For every corpus country with >=10 country-years of multi-channel data, compute
all-pairs Spearman correlations of annual displacement by channel
(conflict / flood / drought / storm). Classify:
  coupling      = any pair |rho| > 0.5
  triple-couple = all of CF, CD, FD > 0.5

Prediction set A: <=15% of countries couple; predicted set ETH/SOM/BRA/SDN
Prediction set B: coupling countries lower libdem OR higher shock-window overlap
Prediction set C: ETH is the only triple-coupler
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")

GIDD_DIS = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx")
GIDD_CONF = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Conflict_Violence_Disasters.xlsx")
VDEM = Path("D:/IDP/data/vdem/vdem_vdem.csv")
OUT = Path("D:/IDP/analysis/paper8_prereg033_census_2026_05_28.json")

MIN_YEARS = 10
COUPLE_THRESH = 0.5
PREDICTED_SET = {"ETH", "SOM", "BRA", "SDN"}


def build_panel():
    d = pd.read_excel(GIDD_DIS)
    d.columns = [c.strip() for c in d.columns]
    d["idp"] = pd.to_numeric(d["Disaster Internal Displacements"], errors="coerce")
    d = d[d["Year"].between(2008, 2024)].dropna(subset=["idp", "ISO3", "Hazard Type"])
    dis = (d[d["Hazard Type"].isin(["Flood", "Drought", "Storm"])]
           .groupby(["ISO3", "Year", "Hazard Type"])["idp"].sum().reset_index())
    dis = dis.pivot_table(index=["ISO3", "Year"], columns="Hazard Type", values="idp", fill_value=0).reset_index()

    c = pd.read_excel(GIDD_CONF)
    c.columns = [col.strip() for col in c.columns]
    c["idp"] = pd.to_numeric(c["Conflict Internal Displacements"], errors="coerce")
    c = c[c["Year"].between(2008, 2024)].dropna(subset=["idp", "ISO3"])
    conf = c.groupby(["ISO3", "Year"])["idp"].sum().reset_index().rename(columns={"idp": "Conflict"})

    panel = dis.merge(conf, on=["ISO3", "Year"], how="outer").fillna(0)
    for ch in ["Flood", "Drought", "Storm", "Conflict"]:
        if ch not in panel.columns:
            panel[ch] = 0.0
    return panel


def shock_overlap(sub):
    """Max channels whose peak-year falls within any 3-year window."""
    peaks = {}
    for ch in ["Flood", "Drought", "Storm", "Conflict"]:
        if sub[ch].sum() > 0:
            peaks[ch] = int(sub.loc[sub[ch].idxmax(), "Year"])
    if not peaks:
        return 0
    yrs = sorted(peaks.values())
    best = 1
    for i in range(len(yrs)):
        cnt = sum(1 for y in yrs if yrs[i] <= y <= yrs[i] + 2)
        best = max(best, cnt)
    return best


def main():
    panel = build_panel()
    pairs = [("Conflict", "Flood", "CF"), ("Conflict", "Drought", "CD"), ("Flood", "Drought", "FD")]

    rows = {}
    for iso, sub in panel.groupby("ISO3"):
        sub = sub.sort_values("Year")
        if len(sub) < MIN_YEARS:
            continue
        cor = {}
        for a, b, name in pairs:
            if sub[a].std() > 0 and sub[b].std() > 0 and (sub[a] > 0).sum() >= 3 and (sub[b] > 0).sum() >= 3:
                rho, p = stats.spearmanr(sub[a], sub[b])
                cor[name] = None if np.isnan(rho) else round(float(rho), 3)
            else:
                cor[name] = None
        coupled_pairs = [k for k, v in cor.items() if v is not None and abs(v) > COUPLE_THRESH]
        rows[iso] = {
            "n_years": int(len(sub)),
            "cor": cor,
            "coupled_pairs": coupled_pairs,
            "is_coupling": len(coupled_pairs) >= 1,
            "is_triple": all(cor.get(k) is not None and cor[k] > COUPLE_THRESH for k in ["CF", "CD", "FD"]),
            "shock_overlap": shock_overlap(sub),
        }

    n_total = len(rows)
    coupling = [iso for iso, r in rows.items() if r["is_coupling"]]
    triple = [iso for iso, r in rows.items() if r["is_triple"]]
    pct = 100 * len(coupling) / n_total if n_total else 0

    print("=" * 80)
    print(f"PRE_REG_033 coupling census — {n_total} countries with >={MIN_YEARS} country-years")
    print("=" * 80)
    print(f"\nCOUPLING countries ({len(coupling)} = {pct:.0f}%):")
    for iso in sorted(coupling, key=lambda x: -max(abs(v) for v in rows[x]["cor"].values() if v is not None)):
        r = rows[iso]
        cc = " ".join(f"{k}={r['cor'][k]:+.2f}" for k in ["CF", "CD", "FD"] if r["cor"][k] is not None)
        flag = " [TRIPLE]" if r["is_triple"] else ""
        inpred = " *predicted*" if iso in PREDICTED_SET else ""
        print(f"  {iso} (n={r['n_years']}, shock_overlap={r['shock_overlap']}): {cc}{flag}{inpred}")

    # Set A verdict
    print(f"\n--- Set A: {pct:.0f}% couple (predicted <=15%; F1 if >25%) ---")
    verdict_A = "SUPPORTED" if pct <= 15 else ("F1 FIRED" if pct > 25 else "WEAK")
    predicted_hits = [iso for iso in PREDICTED_SET if iso in coupling]
    print(f"Predicted set {PREDICTED_SET} -> found coupling: {predicted_hits}")
    print(f"Set A verdict: {verdict_A}")

    # Set C verdict
    print(f"\n--- Set C: triple-couplers = {triple} (predicted: ETH only) ---")
    verdict_C = "SUPPORTED" if triple == ["ETH"] else f"CHECK ({triple})"
    print(f"Set C verdict: {verdict_C}")

    # Set B: coupling vs orthogonal on libdem + shock_overlap
    v = pd.read_csv(VDEM, usecols=["country_text_id", "year", "v2x_libdem"], low_memory=False)
    libdem_mean = (v[v["year"].between(2008, 2024)].groupby("country_text_id")["v2x_libdem"].mean())
    coup_lib = [libdem_mean.get(iso) for iso in coupling if iso in libdem_mean.index]
    orth = [iso for iso in rows if iso not in coupling]
    orth_lib = [libdem_mean.get(iso) for iso in orth if iso in libdem_mean.index]
    coup_so = [rows[iso]["shock_overlap"] for iso in coupling]
    orth_so = [rows[iso]["shock_overlap"] for iso in orth]

    print(f"\n--- Set B: coupling vs orthogonal ---")
    print(f"  mean libdem: coupling {np.nanmean(coup_lib):.3f} vs orthogonal {np.nanmean(orth_lib):.3f}")
    if len(coup_lib) >= 3 and len(orth_lib) >= 3:
        u, pu = stats.mannwhitneyu([x for x in coup_lib if x == x], [x for x in orth_lib if x == x], alternative="less")
        print(f"  Mann-Whitney (coupling libdem < orthogonal): U={u:.0f} p={pu:.3f}")
    print(f"  mean shock_overlap: coupling {np.mean(coup_so):.2f} vs orthogonal {np.mean(orth_so):.2f}")
    if len(coup_so) >= 3 and len(orth_so) >= 3:
        u2, pu2 = stats.mannwhitneyu(coup_so, orth_so, alternative="greater")
        print(f"  Mann-Whitney (coupling shock_overlap > orthogonal): U={u2:.0f} p={pu2:.3f}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "n_total": n_total, "coupling": coupling, "triple": triple, "pct_coupling": pct,
        "predicted_set_hits": predicted_hits, "verdict_A": verdict_A, "verdict_C": verdict_C,
        "coupling_mean_libdem": float(np.nanmean(coup_lib)), "orthogonal_mean_libdem": float(np.nanmean(orth_lib)),
        "coupling_mean_shock_overlap": float(np.mean(coup_so)), "orthogonal_mean_shock_overlap": float(np.mean(orth_so)),
        "rows": rows,
    }, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
