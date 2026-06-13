"""Higher-moment diagnostic on per-class residuals (Collatz Stage 4 analog).

Direct port of B&B's higher-moment finding: per-class variance, skewness, and
kurtosis carry signal that mean-residual SNR diagnostic misses. This is the
uncertainty-calibration layer — high within-class variance means widen the
posterior interval, not shift the point estimate.

For each (stat, class) combination on 23-24 cohort:
  1. mean residual
  2. within-class variance
  3. variance ratio vs baseline (overall residual variance)
  4. F-statistic-style significance: does within-class variance differ from baseline?
  5. skewness, kurtosis (excess) within class
  6. cross-season check: variance ratios for class True vs False in 22-23 vs 23-24

Output: per-class moments + identification of classes with stable HIGHER variance
that should drive uncertainty calibration (e.g., for Wonka variance multiplier).
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(".")
PQ = REPO / "data" / "parquet"
SHIP_2324 = REPO / "audit_runs" / "unified_ship_v6" / "per_player_projections_2023-24.csv"
AUDIT_2223_PTS = REPO / "audit_runs" / "20260501T222551Z" / "skill_backtest_PTS_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22__2022-23" / "per_player_projections.csv"

STATS_WITH_ACTUAL = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FTA", "FTM"]


def attach_features(df, target_year):
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    df = df.merge(meta[["nba_api_id", "position", "birth_date", "draft_year"]],
                  on="nba_api_id", how="left")
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
    df["age"] = (pd.Timestamp(f"{target_year}-10-24") - df["birth_date"]).dt.days / 365.25
    df["age_bucket"] = pd.cut(df["age"], bins=[0, 24, 27, 30, 33, 50],
                                labels=["<=24", "25-26", "27-29", "30-32", "33+"]).astype(str)
    df["years_pro"] = target_year - df["draft_year"]
    df["years_pro_bucket"] = pd.cut(df["years_pro"], bins=[-1, 0, 3, 7, 12, 30],
                                      labels=["rookie", "1-3", "4-7", "8-12", "13+"]).astype(str)
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    season_label = f"{target_year}-{str(target_year+1)[2:]}"
    s = box[box["season"] == season_label]
    team = s.groupby("nba_api_id")["team_abbr"].agg(
        lambda x: x.value_counts().idxmax()).reset_index()
    team.columns = ["nba_api_id", "team_for_season"]
    df = df.merge(team, on="nba_api_id", how="left")

    cf = pd.read_parquet(PQ / "coaching_change_flags.parquet")
    cf_s = cf[cf["season"] == season_label][["team_abbr", "new_coach_this_season",
                                                "mid_season_change"]]
    df = df.merge(cf_s, left_on="team_for_season", right_on="team_abbr",
                   how="left", suffixes=("", "_cf"))
    df["new_coach_this_season"] = df["new_coach_this_season"].fillna(False).astype(bool)
    df["mid_season_change"] = df["mid_season_change"].fillna(False).astype(bool)

    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    traded = set(tx[(tx["transaction_type"] == "trade") &
                    (tx["event_date"] >= pd.Timestamp(f"{target_year}-04-15")) &
                    (tx["event_date"] <= pd.Timestamp(f"{target_year}-10-24")) &
                    (tx["nba_api_id"].notna())]["nba_api_id"].astype(int))
    df["offseason_traded"] = df["nba_api_id"].astype(int).isin(traded)
    return df


def class_moments(df, class_col, res_col, baseline_var=None):
    """For each class value, compute mean / var / skew / kurtosis of residuals."""
    sub = df.dropna(subset=[class_col, res_col]).copy()
    rows = []
    overall_var = baseline_var if baseline_var is not None else sub[res_col].var(ddof=1)
    for cls_val, grp in sub.groupby(class_col, observed=True):
        if len(grp) < 3:
            continue
        r = grp[res_col].values
        n = len(r)
        m = np.mean(r)
        v = np.var(r, ddof=1)
        sk = stats.skew(r, bias=False) if n >= 3 else np.nan
        kt = stats.kurtosis(r, bias=False) if n >= 4 else np.nan
        # F-statistic for variance equality (var(class) vs var(overall))
        if v > 0 and overall_var > 0:
            F_stat = max(v, overall_var) / min(v, overall_var)
            f_p = 2 * (1 - stats.f.cdf(F_stat, n-1, len(sub) - n))
        else:
            F_stat, f_p = np.nan, np.nan
        rows.append({
            "class_value": cls_val, "n": n, "mean_resid": m,
            "var": v, "var_ratio": v / overall_var if overall_var > 0 else np.nan,
            "F_stat": F_stat, "F_p": f_p,
            "skew": sk, "ex_kurt": kt,
        })
    return pd.DataFrame(rows)


def main():
    # 23-24 ship + actuals
    s24 = pd.read_csv(SHIP_2324)
    s24["nba_api_id"] = s24["nba_api_id"].astype(int)
    s24 = s24.dropna(subset=["PTS_actual"]).copy()
    for stat in STATS_WITH_ACTUAL:
        s24[f"{stat}_residual"] = s24[f"{stat}_actual"] - s24[f"{stat}_proj"]
    s24 = attach_features(s24, target_year=2023)

    classes = ["position", "age_bucket", "years_pro_bucket", "offseason_traded",
               "new_coach_this_season", "mid_season_change"]

    # ============== STAGE 1: per-class higher moments on 23-24 ==============
    print("=" * 100)
    print("STAGE 1: PER-CLASS RESIDUAL MOMENTS ON 23-24 (PTS focus)")
    print("=" * 100)

    pts_baseline_var = s24["PTS_residual"].var(ddof=1)
    pts_baseline_skew = stats.skew(s24["PTS_residual"].dropna(), bias=False)
    pts_baseline_kurt = stats.kurtosis(s24["PTS_residual"].dropna(), bias=False)
    print(f"\nPTS overall residual moments:")
    print(f"  variance: {pts_baseline_var:.4f}  (SD={np.sqrt(pts_baseline_var):.3f})")
    print(f"  skew:     {pts_baseline_skew:+.3f}")
    print(f"  ex_kurt:  {pts_baseline_kurt:+.3f}")

    print(f"\n{'class':<22} {'value':<14} {'n':>4} {'mean':>7} {'var':>7} {'var_ratio':>9} {'F_p':>7} {'skew':>7} {'kurt':>7}")
    print("-" * 100)
    for c in classes:
        moments = class_moments(s24, c, "PTS_residual", baseline_var=pts_baseline_var)
        for _, r in moments.iterrows():
            flag = ""
            if r["var_ratio"] > 1.5 and r["F_p"] < 0.10:
                flag = " HIGH-VAR"
            elif r["var_ratio"] < 0.67 and r["F_p"] < 0.10:
                flag = " LOW-VAR"
            print(f"{c:<22} {str(r['class_value']):<14} {r['n']:>4} "
                  f"{r['mean_resid']:>+7.3f} {r['var']:>7.3f} "
                  f"{r['var_ratio']:>9.2f}x {r['F_p']:>7.4f} "
                  f"{r['skew']:>+7.2f} {r['ex_kurt']:>+7.2f}{flag}")
        print()

    # ============== STAGE 2: cross-season variance stability (PTS) ==============
    print("=" * 100)
    print("STAGE 2: CROSS-SEASON VARIANCE STABILITY (PTS, 22-23 vs 23-24)")
    print("=" * 100)
    a22 = pd.read_csv(AUDIT_2223_PTS)
    a22["nba_api_id"] = a22["nba_api_id"].astype(int)
    a22 = a22.dropna(subset=["actual", "proj_mean"]).copy()
    a22["PTS_residual"] = a22["actual"] - a22["proj_mean"]
    a22 = attach_features(a22, target_year=2022)

    a22_baseline_var = a22["PTS_residual"].var(ddof=1)
    print(f"\n22-23 PTS residual variance: {a22_baseline_var:.3f} (SD={np.sqrt(a22_baseline_var):.3f})")
    print(f"23-24 PTS residual variance: {pts_baseline_var:.3f} (SD={np.sqrt(pts_baseline_var):.3f})")
    print()
    print(f"{'class':<22} {'value':<14} {'22 var_ratio':>12} {'24 var_ratio':>12} {'agree?':>8}")
    print("-" * 80)
    for c in classes:
        m22 = class_moments(a22, c, "PTS_residual", baseline_var=a22_baseline_var)
        m24 = class_moments(s24, c, "PTS_residual", baseline_var=pts_baseline_var)
        m22_d = dict(zip(m22["class_value"], m22["var_ratio"]))
        m24_d = dict(zip(m24["class_value"], m24["var_ratio"]))
        all_keys = sorted(set(m22_d.keys()) | set(m24_d.keys()), key=str)
        for k in all_keys:
            v22 = m22_d.get(k, np.nan)
            v24 = m24_d.get(k, np.nan)
            agrees = ""
            if not (np.isnan(v22) or np.isnan(v24)):
                # Both > 1.3 or both < 0.77 → consistent direction
                if (v22 > 1.3 and v24 > 1.3):
                    agrees = "BOTH-HI"
                elif (v22 < 0.77 and v24 < 0.77):
                    agrees = "BOTH-LO"
                elif (v22 > 1.3 and v24 < 0.77) or (v22 < 0.77 and v24 > 1.3):
                    agrees = "FLIP"
                elif abs(v22 - v24) < 0.3:
                    agrees = "stable"
            print(f"{c:<22} {str(k):<14} {v22:>12.2f} {v24:>12.2f}  {agrees}")
        print()

    # ============== STAGE 3: across all stats — within-class variance heatmap ==============
    print("=" * 100)
    print("STAGE 3: VARIANCE RATIO HEATMAP (23-24, all stats × surviving classes)")
    print("=" * 100)
    heat_rows = []
    for stat in STATS_WITH_ACTUAL:
        rcol = f"{stat}_residual"
        if rcol not in s24.columns:
            continue
        baseline = s24[rcol].var(ddof=1)
        for c in classes:
            moments = class_moments(s24, c, rcol, baseline_var=baseline)
            for _, r in moments.iterrows():
                heat_rows.append({
                    "stat": stat, "class": c, "value": str(r["class_value"]),
                    "n": r["n"], "var_ratio": r["var_ratio"],
                    "mean_resid": r["mean_resid"],
                })
    heat = pd.DataFrame(heat_rows)
    # Identify high-variance classes (ratio >= 1.4 with n >= 5)
    high_var = heat[(heat["var_ratio"] >= 1.4) & (heat["n"] >= 5)].sort_values(
        "var_ratio", ascending=False)
    print("\nHIGH-variance (stat, class, value) combinations (var_ratio >= 1.4, n >= 5):")
    print(high_var.to_string(index=False))

    print("\n--- Implication: classes flagged HIGH-VAR are uncertainty-calibration targets ---")
    print("Apply via wonka_variance_multiplier.parquet (widen posterior intervals on these")
    print("subgroups, do NOT shift point estimates).")

    # Save
    heat.to_parquet(PQ / "higher_moments_per_stat_class_2023_24.parquet", index=False)
    print(f"\nSaved -> {PQ / 'higher_moments_per_stat_class_2023_24.parquet'}")


if __name__ == "__main__":
    main()
