"""Direction-of-effect diagnostic.

For each surviving (stat, class) at SNR>=1.5, decompose the per-game residual into:
  per_game_residual  = MPG_residual * (per_min projected) + per_min_residual * MPG_proj
                       + cross term

Approximation (linearization):
  PTS_per_game = PTS_per_min * MPG
  PTS_residual_per_game ~ MPG_residual * PTS_per_min_proj + PTS_per_min_residual * MPG_proj

So we can compute per-min residual from the joint:
  PTS_per_min_actual    = PTS_actual / MPG_actual  (when MPG_actual > 0)
  PTS_per_min_projected = PTS_proj / MPG_proj
  PTS_per_min_residual  = PTS_per_min_actual - PTS_per_min_projected

For each class, report mean(MPG_residual), mean(per_game_residual),
mean(per_min_residual) — and check whether MPG and per-min have OPPOSITE signs
(confirms cascade-compensation theory) or SAME signs (cascade-compensation theory
rejected; both layers off in same direction).
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
from ablation_harness import load_baseline
from expanded_class_diagnostic import attach_features

PQ = Path(".") / "data" / "parquet"

STATS_WITH_ACTUAL = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FTA", "FTM"]


def main():
    base = load_baseline()
    df = attach_features(base)

    # Add MPG_actual (we computed inside attach_features as residual? Let's verify)
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["minutes"] = pd.to_numeric(box["minutes"], errors="coerce")
    box = box.dropna(subset=["minutes"])
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    s23 = box[box["season"] == "2023-24"]
    actual_mpg = s23.groupby("nba_api_id").agg(
        gp=("game_id", "nunique"),
        total_min=("minutes", "sum"),
    ).reset_index()
    actual_mpg["mpg_actual"] = actual_mpg["total_min"] / actual_mpg["gp"]
    df = df.merge(actual_mpg[["nba_api_id", "mpg_actual"]], on="nba_api_id", how="left")
    df["mpg_residual"] = df["mpg_actual"] - df["MPG_proj"]

    # Per-stat per-min residuals
    for stat in STATS_WITH_ACTUAL:
        proj_pg = f"{stat}_proj"
        actual_pg = f"{stat}_actual"
        if proj_pg not in df.columns or actual_pg not in df.columns:
            continue
        df[f"{stat}_perMin_proj"] = df[proj_pg] / df["MPG_proj"].replace(0, np.nan)
        df[f"{stat}_perMin_actual"] = df[actual_pg] / df["mpg_actual"].replace(0, np.nan)
        df[f"{stat}_perMin_residual"] = df[f"{stat}_perMin_actual"] - df[f"{stat}_perMin_proj"]

    # Load SNR matrix to find surviving combos
    snr_df = pd.read_parquet(PQ / "per_stat_class_snr_matrix.parquet")
    surviving = snr_df[snr_df["snr"] >= 1.5].sort_values("snr", ascending=False)

    print(f"Cohort: {len(df)}")
    print(f"Surviving (stat, class) at SNR>=1.5: {len(surviving)}\n")

    # ============== For each surviving combo, decompose ==============
    print("=" * 110)
    print("DECOMPOSITION: per-game residual = MPG channel + per-min channel")
    print("=" * 110)
    print()
    rows = []
    for _, r in surviving.iterrows():
        stat = r["stat"]
        cls = r["class"]
        snr = r["snr"]
        sub = df.dropna(subset=[cls, f"{stat}_residual", "mpg_residual",
                                  f"{stat}_perMin_residual"])
        if len(sub) == 0:
            continue
        for cls_val, grp in sub.groupby(cls, observed=True):
            if len(grp) < 2:
                continue
            n = len(grp)
            mpg_res = grp["mpg_residual"].mean()
            pg_res = grp[f"{stat}_residual"].mean()
            pm_res = grp[f"{stat}_perMin_residual"].mean()
            # Linearization channel decomposition:
            mpg_proj = grp["MPG_proj"].mean()
            pm_proj = grp[f"{stat}_perMin_proj"].mean()
            mpg_channel = mpg_res * pm_proj
            pm_channel = pm_res * mpg_proj
            recon = mpg_channel + pm_channel
            rows.append({
                "stat": stat, "class": cls, "value": cls_val, "n": n, "snr": snr,
                "mpg_resid": mpg_res, "per_game_resid": pg_res, "per_min_resid": pm_res,
                "mpg_channel_pg": mpg_channel, "pm_channel_pg": pm_channel,
                "reconstructed_pg": recon,
                "channel_dominant": "PER_MIN" if abs(pm_channel) > 1.5 * abs(mpg_channel)
                                   else ("MPG" if abs(mpg_channel) > 1.5 * abs(pm_channel)
                                         else "MIXED"),
                "signs_opposite": np.sign(mpg_channel) != np.sign(pm_channel)
                                   and abs(mpg_channel) > 0.05 and abs(pm_channel) > 0.05,
            })
    out = pd.DataFrame(rows)

    # Print decomposition table
    print(f"{'stat':<5} {'class':<22} {'value':<14} {'n':>4} {'snr':>5} "
          f"{'mpg_res':>7} {'pg_res':>7} {'pm_res':>7} "
          f"{'mpg_ch':>7} {'pm_ch':>7} {'recon':>7} dominant signs")
    print("-" * 110)
    for _, r in out.iterrows():
        opp = "OPP" if r["signs_opposite"] else "same"
        print(f"{r['stat']:<5} {r['class']:<22} {str(r['value']):<14} {r['n']:>4} "
              f"{r['snr']:>5.2f} "
              f"{r['mpg_resid']:>+7.3f} {r['per_game_resid']:>+7.3f} {r['per_min_resid']:>+7.3f} "
              f"{r['mpg_channel_pg']:>+7.3f} {r['pm_channel_pg']:>+7.3f} {r['reconstructed_pg']:>+7.3f} "
              f"{r['channel_dominant']:<8} {opp}")

    # ============== Summary: which channel dominates per (stat, class)? ==============
    print("\n" + "=" * 80)
    print("CHANNEL DOMINANCE SUMMARY (per surviving combo, weighted by class size)")
    print("=" * 80)
    summary_rows = []
    for (stat, cls), grp in out.groupby(["stat", "class"]):
        # Per-class-value channel magnitudes weighted by n
        total_n = grp["n"].sum()
        avg_mpg_ch = (grp["mpg_channel_pg"].abs() * grp["n"]).sum() / total_n
        avg_pm_ch = (grp["pm_channel_pg"].abs() * grp["n"]).sum() / total_n
        ratio = avg_pm_ch / max(avg_mpg_ch, 0.001)
        n_opp = (grp["signs_opposite"]).sum()
        summary_rows.append({
            "stat": stat, "class": cls,
            "avg_mpg_channel": avg_mpg_ch,
            "avg_pm_channel": avg_pm_ch,
            "pm_to_mpg_ratio": ratio,
            "n_classes_opp_sign": int(n_opp),
            "n_classes": len(grp),
            "verdict": ("PER_MIN dominant" if ratio > 1.5 else
                        "MPG dominant" if ratio < 0.67 else
                        "MIXED"),
        })
    summary = pd.DataFrame(summary_rows).sort_values(["stat", "pm_to_mpg_ratio"],
                                                       ascending=[True, False])
    fmt = summary.copy()
    fmt["avg_mpg_channel"] = fmt["avg_mpg_channel"].apply(lambda x: f"{x:.3f}")
    fmt["avg_pm_channel"] = fmt["avg_pm_channel"].apply(lambda x: f"{x:.3f}")
    fmt["pm_to_mpg_ratio"] = fmt["pm_to_mpg_ratio"].apply(lambda x: f"{x:.2f}x")
    print()
    print(fmt.to_string(index=False))

    # ============== Higher-order diagnostic: do MPG and per-min anti-correlate
    # at the player level (not just class level)? This is the cascade-compensation
    # signature ==============
    print("\n" + "=" * 80)
    print("PLAYER-LEVEL: Pearson(mpg_residual, per-min residual) per stat")
    print("=" * 80)
    for stat in STATS_WITH_ACTUAL:
        col = f"{stat}_perMin_residual"
        if col not in df.columns:
            continue
        sub = df.dropna(subset=["mpg_residual", col])
        if len(sub) < 10:
            continue
        r = sub["mpg_residual"].corr(sub[col])
        print(f"  {stat:<5}  Pearson r = {r:+.4f}  (n={len(sub)})  "
              f"{'  <- CASCADE COMP (anti-corr)' if r < -0.20 else ''}")

    out.to_parquet(PQ / "direction_of_effect_diagnostic.parquet", index=False)
    print(f"\nSaved -> {PQ / 'direction_of_effect_diagnostic.parquet'}")


if __name__ == "__main__":
    main()
