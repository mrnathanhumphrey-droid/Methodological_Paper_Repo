"""Calibrate + validate three Collatz-prediction-derived Center variance levers.

The Collatz coupling test on 25-26 residuals showed: same class shifts both
mean and variance in position-driven cells. v6.1 has the position MEAN levers
but is missing 3 position VARIANCE levers:

  - PTS × Center: empirical sd 0.79× of non-Center (TIGHTEN)
  - REB × Center: empirical sd 1.69× of non-Center (WIDEN)
  - BLK × Center: empirical sd 1.62× of non-Center (WIDEN)

This script:
  1. Computes calibrated multipliers (proj_sd_per_game vs empirical residual sd)
  2. LOO interval-coverage check (hold one out, calibrate, predict)
  3. Logarithmic-compression test (does the cell distribution shape collapse?)
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
import os
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats as sstats

from models.skill.data_prep import _primary_position_class

REPO = Path(".")
PQ = REPO / "data" / "parquet"


def load_data():
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx = bx[(bx["season"] == "2025-26") & (bx["season_type"] == "Regular Season")].copy()
    bx["minutes"] = pd.to_numeric(bx["minutes"], errors="coerce")
    bx = bx.dropna(subset=["minutes"])
    bx = bx[bx["minutes"] > 0]
    actuals = bx.groupby("nba_api_id").agg(
        PTS_a=("PTS", "mean"), REB_a=("REB", "mean"), AST_a=("AST", "mean"),
        STL_a=("STL", "mean"), BLK_a=("BLK", "mean"), TOV_a=("TOV", "mean"),
        FGM_a=("FGM", "mean"), FGA_a=("FGA", "mean"),
        FG3M_a=("FG3M", "mean"), FG3A_a=("FG3A", "mean"),
        FTM_a=("FTM", "mean"), FTA_a=("FTA", "mean"),
    ).reset_index()
    actuals["nba_api_id"] = actuals["nba_api_id"].astype(int)

    ship = pd.read_csv("audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv")
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    ship = ship.drop(columns=[c for c in ship.columns if c.endswith("_actual")])

    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    cols = ["nba_api_id", "position", "draft_year", "debut_year"]
    sup = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "rookie_metadata_supplement.parquet"
    if sup.exists():
        sp = pd.read_parquet(sup)
        meta = pd.concat([meta[cols], sp[cols]], ignore_index=True)
    ship = ship.merge(meta[cols], on="nba_api_id", how="left")
    ship["pos_class"] = ship["position"].apply(_primary_position_class)
    ship["years_pro"] = ship["debut_year"].where(ship["debut_year"].notna(), ship["draft_year"] + 1)
    ship["years_pro"] = 2025 - ship["years_pro"]
    ship["ypb"] = pd.cut(ship["years_pro"], bins=[-1, 0, 3, 7, 12, 30],
                          labels=["rookie", "1-3", "4-7", "8-12", "13+"]).astype(str)

    real = ship[ship["nba_api_id"] < 9990000].merge(actuals, on="nba_api_id", how="inner")
    return ship, real


def calibrate_center_levers(real):
    print("=" * 88)
    print("CALIBRATION — proj_sd vs empirical residual sd, per class")
    print("=" * 88)
    print(f'{"Stat × Class":<24} {"n":>5} {"emp_sd":>8} {"avg_proj_sd_pg":>16} {"calibration_ratio":>18}')
    print("-" * 88)
    out = {}
    for stat in ["PTS", "REB", "BLK"]:
        for klass in ["C", "F", "G"]:
            sub = real[real["pos_class"] == klass].copy()
            if len(sub) < 10: continue
            resid = sub[f"{stat}_a"] - sub[f"{stat}_per_game"]
            emp_sd = resid.std()
            avg_proj_sd = sub[f"{stat}_per_game_sd"].mean()
            ratio = emp_sd / avg_proj_sd if avg_proj_sd > 0 else float("nan")
            label = f"{stat} × {klass}"
            print(f"{label:<24} {len(sub):>5} {emp_sd:>8.3f} {avg_proj_sd:>16.3f} {ratio:>18.3f}")
            out[(stat, klass)] = {"n": len(sub), "emp_sd": emp_sd,
                                   "avg_proj_sd": avg_proj_sd, "ratio": ratio}
    print()
    return out


def loo_coverage_check(real, calibration):
    """For each candidate (stat × class) pair, hold one player out, calibrate
    multiplier from N-1, apply to held-out, and check 50/80/90 coverage."""
    print("=" * 88)
    print("LOO — interval coverage of empirical-calibrated multiplier vs raw v6.1")
    print("=" * 88)
    print(f"{'lever':<24} {'cov50_raw':>10} {'cov50_calib':>12} {'cov80_raw':>10} {'cov80_calib':>12} {'cov90_raw':>10} {'cov90_calib':>12}")
    print("-" * 88)

    # Test the candidate Center levers
    candidates = [
        ("PTS", "C", "tighten"),
        ("REB", "C", "widen"),
        ("BLK", "C", "widen"),
    ]
    for stat, klass, direction in candidates:
        sub = real[real["pos_class"] == klass].copy().reset_index(drop=True)
        if len(sub) < 10: continue
        resid = (sub[f"{stat}_a"] - sub[f"{stat}_per_game"]).values
        proj_sd = sub[f"{stat}_per_game_sd"].values
        n = len(sub)
        # LOO calibrated multiplier per player
        mults = np.zeros(n)
        for i in range(n):
            mask = np.ones(n, dtype=bool); mask[i] = False
            other_resid = resid[mask]
            other_proj_sd = proj_sd[mask]
            # multiplier that brings avg proj_sd to empirical sd in the held-out N-1
            emp = other_resid.std()
            avg_proj = other_proj_sd.mean()
            mults[i] = emp / avg_proj if avg_proj > 0 else 1.0
        # Apply per-player calibrated multiplier; raw uses v6.1 sd as-is
        z_raw = np.abs(resid) / proj_sd
        z_calib = np.abs(resid) / (proj_sd * mults)
        # 50% CI = ±0.6745σ, 80% = ±1.2816σ, 90% = ±1.6449σ
        cov50_raw = (z_raw <= 0.6745).mean()
        cov80_raw = (z_raw <= 1.2816).mean()
        cov90_raw = (z_raw <= 1.6449).mean()
        cov50_c = (z_calib <= 0.6745).mean()
        cov80_c = (z_calib <= 1.2816).mean()
        cov90_c = (z_calib <= 1.6449).mean()
        label = f"{stat}×{klass} ({direction})"
        print(f"{label:<24} {cov50_raw:>10.1%} {cov50_c:>12.1%} {cov80_raw:>10.1%} {cov80_c:>12.1%} {cov90_raw:>10.1%} {cov90_c:>12.1%}")
        # Mean LOO multiplier (this becomes the lever value to ship)
        print(f"  → LOO-calibrated multiplier mean={mults.mean():.3f}, sd={mults.std():.3f}, range=[{mults.min():.3f}, {mults.max():.3f}]")
    print()


def log_compression_test(real):
    """Does cell-distribution shape compress to ~log2(N_cells) clusters?"""
    print("=" * 88)
    print("LOG-COMPRESSION — does cell distribution shape collapse to ~log2(N) groups?")
    print("=" * 88)
    real = real.copy()
    real["cell"] = real["pos_class"].astype(str) + "|" + real["ypb"].astype(str)
    n_cells = real["cell"].nunique()
    print(f"  Nominal cells (pos × ypb): {n_cells}")
    print(f"  Collatz log-compression prediction: ≈log2({n_cells}) = {np.log2(n_cells):.1f} distinct distributions per stat")
    print()

    for stat in ["PTS", "REB", "AST"]:
        resid_col = f"{stat}_resid"
        real[resid_col] = real[f"{stat}_a"] - real[f"{stat}_per_game"]
        moms = []
        for cell, grp in real.groupby("cell"):
            r = grp[resid_col].dropna()
            if len(r) < 8: continue
            moms.append((cell, len(r), float(r.mean()), float(r.std()),
                         float(sstats.skew(r)), float(sstats.kurtosis(r))))
        if len(moms) < 4: continue
        print(f'  {stat} per-cell moments:')
        print(f'  {"cell":<10} {"n":>4} {"mean":>8} {"sd":>7} {"skew":>8} {"kurt":>8}')
        for m in moms:
            mean_str = ('{:+.2f}').format(m[2])
            sd_str = ('{:.3f}').format(m[3])
            sk_str = ('{:+.2f}').format(m[4])
            kt_str = ('{:+.2f}').format(m[5])
            print(f'  {m[0]:<10} {m[1]:>4} {mean_str:>8s} {sd_str:>7s} {sk_str:>8s} {kt_str:>8s}')

        # Hierarchical cluster on (sd, skew, kurt)
        arr = np.array([(m[3], m[4], m[5]) for m in moms])
        arr_z = (arr - arr.mean(axis=0)) / arr.std(axis=0)
        from scipy.cluster.hierarchy import linkage, fcluster
        Z = linkage(arr_z, method="ward")
        print(f'  Compression by ward linkage (cells per cluster):')
        for k in [3, 4, 5]:
            clusters = fcluster(Z, t=k, criterion="maxclust")
            cells_per = {}
            for ci, c in enumerate(clusters):
                cells_per.setdefault(int(c), []).append(moms[ci][0])
            cluster_view = " | ".join(f"[{','.join(v)}]" for v in cells_per.values())
            print(f'    k={k}: {cluster_view}')
        print()


def main():
    ship, real = load_data()
    print(f"Sample: {len(real)} players matched to 25-26 actuals")
    print(f"  pos breakdown: {real['pos_class'].value_counts().to_dict()}")
    print(f"  ypb breakdown: {real['ypb'].value_counts().to_dict()}")
    print()
    cal = calibrate_center_levers(real)
    loo_coverage_check(real, cal)
    log_compression_test(real)


if __name__ == "__main__":
    main()
