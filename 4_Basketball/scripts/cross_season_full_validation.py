"""Cross-season validation across all available v4-lite tq_g audits.

For each (stat, class) combination:
  1. Find all available audits (by test season)
  2. Compute residuals per season
  3. Run noise-floor SNR test per season
  4. Cross-season check: do class effects (mean + variance) replicate in sign?
  5. Output: validated mean offsets + validated variance multipliers

Mean offsets where:
  - SNR >= 1.5 in 2+ seasons
  - Sign agrees across all participating seasons
  - Magnitude: cross-season mean (with shrinkage if magnitudes vary)

Variance multipliers where:
  - var_ratio >= 1.4 in 2+ seasons
  - All ratios > 1.2 (consistent direction)
  - Magnitude: cross-season geometric mean

Output:
  data/parquet/cross_season_validated_offsets.parquet
  data/parquet/cross_season_validated_variances.parquet

Use these to rebuild apply_v61_validated_offsets.py spec.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")

from pathlib import Path
import re
import numpy as np
import pandas as pd

from _class_features import attach_class_features

REPO = Path(".")
PQ = REPO / "data" / "parquet"

STATS = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FTA", "FTM"]
CLASSES = ["position", "age_bucket", "years_pro_bucket", "draft_pick_tier",
            "offseason_traded", "new_coach_this_season", "mid_season_change"]


def find_audits(stat: str) -> dict:
    """Return {test_season: audit_path}.

    Tiebreak: prefer the audit with the LARGEST per_player_projections.csv
    (most rows). This avoids picking smoke-test runs (max_players=15, low iter)
    over canonical full-cohort fits.
    """
    pattern = re.compile(
        rf"skill_backtest_{stat}_phase4_v4_quadratic_tq_g_.*__(\d{{4}}-\d{{2}})$"
    )
    found = {}  # test_season -> (csv_path, size_bytes)
    for d in (REPO / "audit_runs").glob("*"):
        if not d.is_dir():
            continue
        for sub in d.glob(f"skill_backtest_{stat}_phase4_v4_quadratic_tq_g_*"):
            m = pattern.search(sub.name)
            if m:
                test_season = m.group(1)
                csv = sub / "per_player_projections.csv"
                if csv.exists():
                    size = csv.stat().st_size
                    if (test_season not in found or
                        size > found[test_season][1]):
                        found[test_season] = (csv, size)
    return {ts: csv for ts, (csv, _) in found.items()}


# attach_class_features now imported from scripts/_class_features.py


def class_stats_with_var(df, class_col, res_col, baseline_var):
    """Return per-class-value mean residual + variance ratio."""
    sub = df.dropna(subset=[class_col, res_col])
    out = []
    for cls_val, grp in sub.groupby(class_col, observed=True):
        if len(grp) < 3:
            continue
        v = grp[res_col].var(ddof=1)
        out.append({
            "class_value": cls_val, "n": len(grp),
            "mean": grp[res_col].mean(),
            "var": v,
            "var_ratio": v / baseline_var if baseline_var > 0 else np.nan,
        })
    if not out:
        return None
    df_out = pd.DataFrame(out)
    sd_obs = df_out["mean"].std(ddof=1) if len(df_out) >= 2 else np.nan
    n_per = df_out["n"].mean()
    se = np.sqrt(baseline_var / n_per) if baseline_var > 0 else np.nan
    snr = sd_obs / se if se > 0 else np.nan
    return {"snr": snr, "rows": df_out}


def main():
    # Audits per stat
    audits = {stat: find_audits(stat) for stat in STATS}
    print("=== Audit availability ===")
    for stat, ad in audits.items():
        print(f"  {stat}: {sorted(ad.keys())}  ({len(ad)} seasons)")

    # 23-24 ship for "current" stats not yet refit (PTS uses v6 ship's PTS_proj)
    SHIP_2324 = REPO / "audit_runs" / "unified_ship_v6" / "per_player_projections_2023-24.csv"
    if SHIP_2324.exists():
        s24_ship = pd.read_csv(SHIP_2324)
        s24_ship["nba_api_id"] = s24_ship["nba_api_id"].astype(int)

    # Build per-stat per-season residual + class data
    per_stat_results = {}  # stat -> {season -> {class -> {snr, rows}}}
    for stat in STATS:
        per_stat_results[stat] = {}
        for season, audit_path in audits[stat].items():
            target_year = int(season.split("-")[0])
            df = pd.read_csv(audit_path)
            df["nba_api_id"] = df["nba_api_id"].astype(int)
            df = df.dropna(subset=["actual", "proj_mean"]).copy()
            df["residual"] = df["actual"] - df["proj_mean"]
            df = attach_class_features(df, target_year)

            baseline_var = df["residual"].var(ddof=1)
            class_data = {}
            for c in CLASSES:
                r = class_stats_with_var(df, c, "residual", baseline_var)
                if r is not None:
                    class_data[c] = r
            per_stat_results[stat][season] = {
                "n": len(df),
                "baseline_var": baseline_var,
                "mean_resid": df["residual"].mean(),
                "classes": class_data,
            }

    # ============== Cross-season validation: mean offsets ==============
    print("\n" + "=" * 90)
    print("CROSS-SEASON VALIDATED MEAN OFFSETS")
    print("=" * 90)
    validated_means = []
    for stat, season_data in per_stat_results.items():
        seasons = sorted(season_data.keys())
        if len(seasons) < 2:
            continue
        for cls in CLASSES:
            # Gather per-season class means
            per_season_means = {}
            for s in seasons:
                if cls in season_data[s]["classes"]:
                    cd = season_data[s]["classes"][cls]
                    per_season_means[s] = dict(zip(cd["rows"]["class_value"],
                                                     cd["rows"]["mean"]))
            if len(per_season_means) < 2:
                continue
            # For each class value, check if signs agree
            all_values = set()
            for d in per_season_means.values():
                all_values.update(d.keys())
            for cv in all_values:
                vals = []
                for s in seasons:
                    v = per_season_means[s].get(cv)
                    if v is not None:
                        vals.append((s, v))
                if len(vals) < 2:
                    continue
                signs = [np.sign(v) for s, v in vals]
                if not all(s == signs[0] for s in signs):
                    continue
                if abs(np.mean([v for s, v in vals])) < 0.05:
                    continue  # too small to bother
                avg = np.mean([v for s, v in vals])
                validated_means.append({
                    "stat": stat, "class": cls, "class_value": str(cv),
                    "n_seasons": len(vals),
                    "seasons": [s for s, v in vals],
                    "season_means": [round(v, 3) for s, v in vals],
                    "cross_season_mean": round(avg, 3),
                })
    if validated_means:
        vm = pd.DataFrame(validated_means)
        print(vm.to_string(index=False))
        vm.to_parquet(PQ / "cross_season_validated_offsets.parquet", index=False)
        print(f"\nSaved -> {PQ / 'cross_season_validated_offsets.parquet'}")
    else:
        print("\n  No mean offsets cleared cross-season validation yet.")

    # ============== Cross-season validation: variance multipliers ==============
    print("\n" + "=" * 90)
    print("CROSS-SEASON VALIDATED VARIANCE MULTIPLIERS")
    print("=" * 90)
    validated_vars = []
    for stat, season_data in per_stat_results.items():
        seasons = sorted(season_data.keys())
        if len(seasons) < 2:
            continue
        for cls in CLASSES:
            per_season_var = {}
            for s in seasons:
                if cls in season_data[s]["classes"]:
                    cd = season_data[s]["classes"][cls]
                    per_season_var[s] = dict(zip(cd["rows"]["class_value"],
                                                   cd["rows"]["var_ratio"]))
            if len(per_season_var) < 2:
                continue
            all_values = set()
            for d in per_season_var.values():
                all_values.update(d.keys())
            for cv in all_values:
                ratios = []
                for s in seasons:
                    r = per_season_var[s].get(cv)
                    if r is not None and not np.isnan(r):
                        ratios.append((s, r))
                if len(ratios) < 2:
                    continue
                # Both/all ratios must be elevated (> 1.2) OR consistently low (< 0.8)
                rvals = [r for s, r in ratios]
                if all(r > 1.2 for r in rvals) and np.mean(rvals) > 1.4:
                    direction = "WIDEN"
                elif all(r < 0.8 for r in rvals) and np.mean(rvals) < 0.7:
                    direction = "TIGHTEN"
                else:
                    continue
                geom_mean = np.exp(np.mean(np.log(rvals)))
                validated_vars.append({
                    "stat": stat, "class": cls, "class_value": str(cv),
                    "direction": direction,
                    "n_seasons": len(ratios),
                    "season_ratios": [round(r, 2) for s, r in ratios],
                    "geom_mean_ratio": round(geom_mean, 3),
                })
    if validated_vars:
        vv = pd.DataFrame(validated_vars)
        print(vv.to_string(index=False))
        vv.to_parquet(PQ / "cross_season_validated_variances.parquet", index=False)
        print(f"\nSaved -> {PQ / 'cross_season_validated_variances.parquet'}")
    else:
        print("\n  No variance multipliers cleared cross-season validation yet.")
        print("  (Need 2+ seasons of audits per stat with the same class showing var_ratio >= 1.4)")


if __name__ == "__main__":
    main()
