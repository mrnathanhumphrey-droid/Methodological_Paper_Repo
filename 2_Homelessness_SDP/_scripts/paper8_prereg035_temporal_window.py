"""
Paper 8 — PRE_REG_035 temporal-window / synchronized-shock test.

Is ETH's triple-coupling window-transient (driven by the 2020-2024 synchronized
shock: Tigray war + Rift Valley flood + Horn drought) or structural?

Set A: split-window ETH pre-2018 (2008-2017) vs 2018-2024 per pair.
       Predicted: coupling concentrates in 2018-2024 (early ρ weaker by >=0.25).
Set B: leave-window-out -- drop 2020-2022 triple-peak years, recompute full ρ.
       Predicted: ETH CD ρ collapses below 0.5. Plus bootstrap 90% CI.
Set C: shock-overlap predictor -- correlate max|ρ| with shock_overlap across
       all testable countries.
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
CENSUS = Path("D:/IDP/analysis/paper8_prereg033_census_2026_05_28.json")
OUT = Path("D:/IDP/analysis/paper8_prereg035_2026_05_28.json")

PAIRS = [("Conflict", "Flood", "CF"), ("Conflict", "Drought", "CD"), ("Flood", "Drought", "FD")]
DROP_WINDOW = [2020, 2021, 2022]  # ETH triple-peak (Tigray war opening + flood + drought)
SPLIT_YEAR = 2018


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


def srho(sub, a, b):
    if sub[a].std() > 0 and sub[b].std() > 0 and (sub[a] > 0).sum() >= 3 and (sub[b] > 0).sum() >= 3:
        r, _ = stats.spearmanr(sub[a], sub[b])
        return None if np.isnan(r) else float(r)
    return None


def main():
    panel = build_panel()
    eth = panel[panel["ISO3"] == "ETH"].sort_values("Year")

    # ---- Set A: split-window ETH ----
    early = eth[eth["Year"] < SPLIT_YEAR]
    late = eth[eth["Year"] >= SPLIT_YEAR]
    full = eth
    setA = {}
    print("=" * 76)
    print(f"PRE_REG_035 Set A — ETH split-window (early 2008-{SPLIT_YEAR-1} n={len(early)} vs {SPLIT_YEAR}-2024 n={len(late)})")
    print("=" * 76)
    print(f"{'pair':<6}{'full':<10}{'early':<10}{'late':<10}{'drop(early-from-full)'}")
    for a, b, name in PAIRS:
        rf, re_, rl = srho(full, a, b), srho(early, a, b), srho(late, a, b)
        setA[name] = {"full": rf, "early": re_, "late": rl}
        def f(x): return "n/a" if x is None else f"{x:+.2f}"
        drop = None if (rf is None or re_ is None) else round(rf - re_, 2)
        print(f"{name:<6}{f(rf):<10}{f(re_):<10}{f(rl):<10}{drop}")

    # ---- Set B: leave-window-out (drop 2020-2022) + bootstrap ----
    lwo = eth[~eth["Year"].isin(DROP_WINDOW)]
    print(f"\n--- Set B: leave-window-out (drop {DROP_WINDOW}, n={len(lwo)}) + bootstrap ---")
    setB = {}
    rng = np.random.default_rng(42)
    for a, b, name in PAIRS:
        full_r = srho(full, a, b)
        lwo_r = srho(lwo, a, b)
        # bootstrap full-window
        boots = []
        arr = full[[a, b]].values
        for _ in range(2000):
            idx = rng.integers(0, len(arr), len(arr))
            s = arr[idx]
            if np.std(s[:, 0]) > 0 and np.std(s[:, 1]) > 0:
                rr, _ = stats.spearmanr(s[:, 0], s[:, 1])
                if not np.isnan(rr):
                    boots.append(rr)
        ci = (round(float(np.percentile(boots, 5)), 2), round(float(np.percentile(boots, 95)), 2)) if boots else None
        setB[name] = {"full": full_r, "leave_window_out": lwo_r,
                      "boot_90ci": ci,
                      "collapsed": (full_r is not None and lwo_r is not None and full_r > 0.5 and lwo_r < 0.5)}
        def f(x): return "n/a" if x is None else f"{x:+.2f}"
        print(f"  {name}: full={f(full_r)} leave-out={f(lwo_r)} boot90CI={ci} collapsed={setB[name]['collapsed']}")

    cd_collapsed = setB["CD"]["collapsed"]
    print(f"\n  PRED B (ETH CD collapses <0.5 when 2020-22 dropped): {'SUPPORTED' if cd_collapsed else 'NOT SUPPORTED'}")

    # ---- Set C: shock-overlap predictor across testable countries ----
    census = json.loads(CENSUS.read_text())
    xs, ys = [], []
    for iso, r in census["rows"].items():
        vals = [abs(v) for v in r["cor"].values() if v is not None]
        if vals:
            xs.append(r["shock_overlap"]); ys.append(max(vals))
    rho_c, p_c = stats.spearmanr(xs, ys)
    print(f"\n--- Set C: shock_overlap vs max|ρ| across {len(xs)} testable countries ---")
    print(f"  Spearman ρ = {rho_c:+.3f} (p={p_c:.4f})")

    # ---- Verdicts ----
    cd_drop = (setA["CD"]["full"] - setA["CD"]["early"]) if (setA["CD"]["full"] is not None and setA["CD"]["early"] is not None) else None
    setA_supported = cd_drop is not None and cd_drop >= 0.25
    print("\n" + "=" * 76)
    print("VERDICTS")
    print("=" * 76)
    print(f"  Set A (CD early weaker by >=0.25): drop={cd_drop} -> {'SUPPORTED' if setA_supported else 'CHECK'}")
    print(f"  Set B (CD collapses on leave-window-out): {'SUPPORTED' if cd_collapsed else 'NOT SUPPORTED'}")
    print(f"  Set C (shock_overlap predicts coupling): ρ={rho_c:+.2f} p={p_c:.4f} -> {'SUPPORTED' if p_c < 0.05 and rho_c > 0 else 'CHECK'}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "setA_split": setA, "setA_cd_drop": cd_drop, "setA_supported": bool(setA_supported),
        "setB_leave_window_out": setB, "setB_cd_collapsed": bool(cd_collapsed),
        "setC_shock_overlap_rho": float(rho_c), "setC_p": float(p_c), "setC_n": len(xs),
        "drop_window": DROP_WINDOW, "split_year": SPLIT_YEAR,
    }, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
