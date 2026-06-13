"""Probe 7 — V3 sigma_within ATLAS

Build the cross-cohort sigma_within ladder that the published PV literature lacks.
V3 verification (memo 31 §4) found that NO peer-reviewed paper reports sigma_within
numerically by cohort (only means by stratum, e.g. Jordan 2022 / Deceglie 2019).

Substrate has the data to compute sigma_within at multiple cohort homogeneity levels
using a single methodology (Probe 2 PLR pipeline + Probe 4 DKA PLR pipeline). This
fills the literature gap.

The atlas computes sigma_within at progressively-tightened cohort definitions,
from "most heterogeneous" (full PVDAQ) down to "most homogeneous" (DKA single-site
fixed-mount c-Si). The expected pattern from the substrate's earlier findings
(CLM-078, CLM-083): sigma_within shrinks monotonically as cohort homogeneity
increases.

Outputs:
- probe7_sigma_atlas.csv (cohort | n | median | IQR | sigma | source)
- console table for review
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data/processed"
OUT = PROC / "probe7_sigma_atlas.csv"

# Filtering rules: drop PLR outliers that wreck sigma. Used downstream consistently.
PLR_MIN, PLR_MAX = -5.0, 2.0  # PLR realistic range (Jordan 2016 distributions)


def sigma_of(s):
    """Return n, median, IQR (75-25), sigma_within (sample SD), sigma_IQR-derived."""
    s = pd.Series(s).dropna()
    s = s[(s >= PLR_MIN) & (s <= PLR_MAX)]
    if len(s) < 5:
        return {"n": len(s), "median": np.nan, "iqr": np.nan, "sigma": np.nan, "sigma_iqr": np.nan}
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    sigma_iqr = iqr / 1.349   # normal-approximation conversion
    return {"n": int(len(s)), "median": float(s.median()), "iqr": float(iqr),
            "sigma": float(s.std(ddof=1)), "sigma_iqr": float(sigma_iqr)}


def main():
    # ----- Load PVDAQ + DKA PLR results -----
    pvdaq_plr = pd.read_csv(PROC / "probe2_plr_results_clean.csv")
    pvdaq_plr = pvdaq_plr[pvdaq_plr["status"] == "ok"].copy()

    cohort = pd.read_csv(PROC / "probe2_cohort_p0.csv")
    pvdaq = pvdaq_plr.merge(cohort, on="system_id", how="left")
    print(f"PVDAQ valid PLR: {len(pvdaq_plr)}  (after join with cohort: {len(pvdaq)})")

    dka = pd.read_csv(PROC / "probe4_dka_plr.csv")
    dka_ok = dka[dka["status"] == "ok"].copy()
    print(f"DKA valid PLR: {len(dka_ok)}")
    print()

    rows = []

    def add(label, plr_series, source, note=""):
        r = sigma_of(plr_series)
        r["cohort"] = label
        r["source"] = source
        r["note"] = note
        rows.append(r)
        if not np.isnan(r["sigma"]):
            print(f"  {label:<60s} n={r['n']:>4d}  med={r['median']:>+6.2f}  IQR={r['iqr']:>4.2f}  sigma={r['sigma']:>4.2f}  ({source})")

    # ===================================================================
    # Tier A — Most heterogeneous to less heterogeneous
    # ===================================================================
    print("=== TIER A: PVDAQ heterogeneity ladder ===")
    add("PVDAQ ALL (full fleet, mixed mount/track/tech/vintage)",
        pvdaq["plr_pct_yr"], "Probe 2")

    add("PVDAQ residential roof (mount=roof)",
        pvdaq[pvdaq["A_MOUNT"] == "roof"]["plr_pct_yr"], "Probe 2 stratified",
        "matches Deceglie 2019 'residential' stratum")

    add("PVDAQ ground-mount (mount=ground)",
        pvdaq[pvdaq["A_MOUNT"] == "ground"]["plr_pct_yr"], "Probe 2 stratified",
        "matches Deceglie 2019 'non-residential' direction")

    add("PVDAQ fixed-mount (track=fixed, n large)",
        pvdaq[pvdaq["A_TRACK"] == "fixed"]["plr_pct_yr"], "Probe 2 stratified")

    add("PVDAQ tracking (track=tracking)",
        pvdaq[pvdaq["A_TRACK"] == "tracking"]["plr_pct_yr"], "Probe 2 stratified",
        "small n; nominal Jordan 2022 tracker-null reference")

    # ===================================================================
    # Tier B — PVDAQ within climate zones (T-zone)
    # ===================================================================
    print("\n=== TIER B: PVDAQ within climate stratum (Karin PVCZ T) ===")
    for t in sorted(pvdaq["A_PVCZ_T"].dropna().unique()):
        sub = pvdaq[pvdaq["A_PVCZ_T"] == t]["plr_pct_yr"]
        if len(sub) >= 20:
            add(f"PVDAQ within PVCZ {t}", sub, "Probe 2 stratified",
                "within-climate-zone homogeneity (still heterogeneous in tech/mount)")

    # ===================================================================
    # Tier C — PVDAQ within capacity bucket
    # ===================================================================
    print("\n=== TIER C: PVDAQ within capacity bucket ===")
    pvdaq["cap_bin"] = pd.cut(pvdaq["dc_capacity_kW"], bins=[0, 5, 10, 25, 100, 1e6],
                              labels=["<5kW", "5-10kW", "10-25kW", "25-100kW", ">100kW"])
    for b in pvdaq["cap_bin"].dropna().unique():
        sub = pvdaq[pvdaq["cap_bin"] == b]["plr_pct_yr"]
        if len(sub) >= 20:
            add(f"PVDAQ {b} capacity bucket", sub, "Probe 2 stratified",
                "size-correlates-with-O&M sophistication")

    # ===================================================================
    # Tier D — DKA homogeneous single-site
    # ===================================================================
    print("\n=== TIER D: DKA single-site homogeneous cohorts ===")
    add("DKA Alice Springs ALL (single site, multi-tech)",
        dka_ok["plr_pct_yr"], "Probe 4")

    add("DKA Alice Springs fixed-mount only",
        dka_ok[dka_ok["mount"] == "Fixed"]["plr_pct_yr"], "Probe 4 stratified",
        "homogeneous-site x homogeneous-mount = HOMOGENEITY CEILING")

    add("DKA c-Si only (mono + poly)",
        dka_ok[dka_ok["technology"].isin(["mono-Si", "poly-Si"])]["plr_pct_yr"], "Probe 4 stratified",
        "single-tech narrow")

    add("DKA c-Si fixed-mount only (intersect)",
        dka_ok[(dka_ok["mount"] == "Fixed") &
               (dka_ok["technology"].isin(["mono-Si", "poly-Si"]))]["plr_pct_yr"],
        "Probe 4 stratified",
        "TIGHTEST cohort — both axes locked")

    # ===================================================================
    # Save + summary
    # ===================================================================
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    print(f"\nWrote {OUT}")

    print("\n=== σ_WITHIN LADDER (sorted descending — heterogeneity gradient) ===")
    df_sorted = df.dropna(subset=["sigma"]).sort_values("sigma", ascending=False)
    print(f"{'cohort':<60s} {'n':>4s}  {'sigma':>5s}  ratio_vs_tightest")
    tight_sigma = df_sorted["sigma"].min()
    for _, r in df_sorted.iterrows():
        ratio = r["sigma"] / tight_sigma if tight_sigma > 0 else float("inf")
        print(f"  {r['cohort']:<58s} n={r['n']:>4d}  sigma={r['sigma']:>4.2f}  {ratio:>4.1f}x")

    print(f"\nTightest cohort: σ={tight_sigma:.2f} %/yr")
    print(f"Loosest cohort: σ={df_sorted['sigma'].max():.2f} %/yr")
    print(f"Ratio (loosest / tightest): {df_sorted['sigma'].max() / tight_sigma:.1f}x")


if __name__ == "__main__":
    main()
