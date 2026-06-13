"""Test 1 cross-season replication for BLK x Center — completes the 4-cell argument.

Runs the same Levene's + Bartlett's + F-test sensitivity audit applied to PTS in
the multi_season_replication run, on BLK residuals from today's BLK chain.
Also includes 25-26 from the v6.1 LOCKED ship (with box-score actuals enrichment
matching the Section 5 methodology).
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(".")
PQ = REPO / "data" / "parquet"
OUT_DIR = REPO / "audit_runs" / "test_1_blk_center"
OUT_DIR.mkdir(parents=True, exist_ok=True)

V6_1_SHIP = REPO / "audit_runs" / "unified_ship_v6_1_2025_26" / "per_player_projections_2025-26.csv"
ROOKIE_SUP = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "rookie_metadata_supplement.parquet"

BLK_PROJ = {
    "2024-25": "audit_runs/20260506T140025Z/skill_backtest_BLK_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/per_player_projections.csv",
    "2023-24": "audit_runs/20260506T150621Z/skill_backtest_BLK_phase4_v4_quadratic_tq_g_2017-18-2018-19-2019-20-2020-21-2021-22-2022-23__2023-24/per_player_projections.csv",
}


def position_class(p):
    if pd.isna(p) or not p or str(p).strip() == "": return "Forward"
    s = str(p).lower()
    if "center" in s: return "Center"
    if "guard" in s: return "Guard"
    return "Forward"


def f_test_two_sided(arr_in, arr_out):
    a = np.asarray(arr_in, dtype=float)
    b = np.asarray(arr_out, dtype=float)
    var_a = a.var(ddof=1)
    var_b = b.var(ddof=1)
    if var_b == 0 or var_a == 0:
        return np.nan
    F = var_a / var_b
    cdf = stats.f.cdf(F, len(a) - 1, len(b) - 1)
    return 2 * min(cdf, 1 - cdf)


def run_cell(r_in, r_out):
    n_in, n_out = len(r_in), len(r_out)
    if n_in < 5 or n_out < 5:
        return {"n_in": n_in, "n_out": n_out, "ratio": np.nan,
                 "p_levene": np.nan, "p_bartlett": np.nan, "p_F": np.nan}
    sd_in = float(r_in.std(ddof=1))
    sd_out = float(r_out.std(ddof=1))
    ratio = sd_in / sd_out if sd_out > 0 else np.nan
    try:
        _, p_lev = stats.levene(r_in, r_out, center="median")
    except Exception:
        p_lev = np.nan
    try:
        _, p_bart = stats.bartlett(r_in, r_out)
    except Exception:
        p_bart = np.nan
    p_F = f_test_two_sided(r_in, r_out)
    return {
        "n_in": n_in, "n_out": n_out,
        "mean_in": float(r_in.mean()), "mean_out": float(r_out.mean()),
        "sd_in": sd_in, "sd_out": sd_out,
        "ratio": float(ratio),
        "p_levene": float(p_lev), "p_bartlett": float(p_bart),
        "p_F_two_sided": float(p_F),
    }


def main():
    print("[load] metadata + box scores")
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    if ROOKIE_SUP.exists():
        sup = pd.read_parquet(ROOKIE_SUP)
        cols = ["nba_api_id", "name", "position", "draft_year", "debut_year"]
        meta = pd.concat([meta[cols], sup[cols]], ignore_index=True)
    meta["nba_api_id"] = meta["nba_api_id"].astype(int)

    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx_2526 = bx[(bx["season"] == "2025-26") &
                   (bx["season_type"] == "Regular Season")].copy()
    bx_2526["minutes"] = pd.to_numeric(bx_2526["minutes"], errors="coerce")
    bx_2526 = bx_2526[bx_2526["minutes"] > 0]
    bx_2526["nba_api_id"] = bx_2526["nba_api_id"].astype(int)

    rows = []

    # 23-24 + 24-25 from Stan backtest CSVs
    for season, path in BLK_PROJ.items():
        df = pd.read_csv(path)
        df["nba_api_id"] = df["nba_api_id"].astype(int)
        df["resid"] = df["actual"] - df["proj_mean"]
        df = df.merge(meta[["nba_api_id", "position"]], on="nba_api_id", how="left")
        df["pos_class"] = df["position"].apply(position_class)
        in_mask = df["pos_class"] == "Center"
        result = run_cell(df.loc[in_mask, "resid"].dropna().values,
                            df.loc[~in_mask, "resid"].dropna().values)
        result.update({"season": season, "test_set": "Stan vets only (200 cap)"})
        rows.append(result)

    # 25-26 full-ship cohort with box-score actuals
    ship = pd.read_csv(V6_1_SHIP)
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    actuals = bx_2526.groupby("nba_api_id").agg(
        BLK_actual=("BLK", "mean")).reset_index()

    rookie_real_id = {}
    if ROOKIE_SUP.exists():
        sup = pd.read_parquet(ROOKIE_SUP)
        meta_base = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
        real_name_id = dict(zip(meta_base["name"].str.lower().fillna(""),
                                  meta_base["nba_api_id"].astype(int)))
        for _, r in sup.iterrows():
            nm = (r["name"] or "").strip().lower()
            if nm in real_name_id:
                rookie_real_id[int(r["nba_api_id"])] = real_name_id[nm]
    ship["real_id"] = ship["nba_api_id"].map(
        lambda x: rookie_real_id.get(int(x), int(x))).astype(int)
    stale = [c for c in ship.columns if c.endswith("_actual")]
    ship = ship.drop(columns=stale)
    df = ship.merge(actuals, left_on="real_id", right_on="nba_api_id",
                      how="left", suffixes=("", "_act"))
    df["resid"] = df["BLK_actual"] - df["BLK_per_game"]
    df = df.merge(meta[["nba_api_id", "position"]], left_on="real_id",
                    right_on="nba_api_id", how="left", suffixes=("", "_m"))
    df["pos_class"] = df["position"].apply(position_class)
    in_mask = df["pos_class"] == "Center"
    result = run_cell(df.loc[in_mask, "resid"].dropna().values,
                        df.loc[~in_mask, "resid"].dropna().values)
    result.update({"season": "2025-26 (full ship)",
                     "test_set": "Full ship (n=567)"})
    rows.append(result)

    print()
    out = pd.DataFrame(rows)
    out = out[["season", "test_set", "n_in", "n_out",
                 "mean_in", "mean_out", "sd_in", "sd_out", "ratio",
                 "p_levene", "p_bartlett", "p_F_two_sided"]]
    print("=" * 80)
    print("TEST 1 cross-season replication — BLK × Center (the 4th cell)")
    print("=" * 80)
    print(out.to_string(index=False))

    out.to_csv(OUT_DIR / "blk_center_cross_season.csv", index=False)
    print(f"\n[save] {OUT_DIR / 'blk_center_cross_season.csv'}")

    print()
    print("=== ASYMMETRY CHECK against pre-registered scenarios ===")
    print("Predicted: position cells couple (sd_in != sd_out, p < 0.05)")
    print("           career-stage cells do NOT couple (sd_in ≈ sd_out, p > 0.05)")
    print()
    for _, r in out.iterrows():
        confirm_couple = r["p_levene"] < 0.05
        emoji = "✓ COUPLED" if confirm_couple else "✗ NOT SIGNIFICANT"
        print(f"  {r['season']:>20} BLK×Center: ratio={r['ratio']:.3f}, "
              f"Levene's p={r['p_levene']:.4f} → {emoji}")


if __name__ == "__main__":
    main()
