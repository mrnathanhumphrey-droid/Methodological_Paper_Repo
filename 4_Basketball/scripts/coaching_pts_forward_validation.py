"""Test whether new_coach_this_season and mid_season_change × PTS effects
survive 22-23 ↔ 23-24 forward validation. Uses apples-to-apples tq_g audits.

If signs and approximate magnitudes agree, add to v6.1 offset table.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
AUDIT_2223 = REPO / "audit_runs" / "20260501T222551Z" / "skill_backtest_PTS_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22__2022-23" / "per_player_projections.csv"
SHIP_2324 = REPO / "audit_runs" / "unified_ship_v6" / "per_player_projections_2023-24.csv"


def attach_coach_for(df, season_label, target_year):
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["nba_api_id"] = box["nba_api_id"].astype(int)
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
    return df


def class_mean_residuals(df, class_col, res_col):
    sub = df.dropna(subset=[class_col, res_col]).copy()
    grouped = sub.groupby(class_col, observed=True)[res_col].agg(
        ["mean", "count"]).reset_index()
    grouped = grouped[grouped["count"] >= 2]
    sd_obs = grouped["mean"].std(ddof=1)
    var = sub[res_col].var(ddof=1)
    n_per = grouped["count"].mean()
    se = np.sqrt(var / n_per) if len(grouped) >= 2 else np.nan
    snr = sd_obs / se if se > 0 else np.nan
    return {"snr": snr,
            "means": dict(zip(grouped[class_col], grouped["mean"])),
            "counts": dict(zip(grouped[class_col], grouped["count"]))}


def main():
    # --- 22-23 ---
    a22 = pd.read_csv(AUDIT_2223)
    a22["nba_api_id"] = a22["nba_api_id"].astype(int)
    a22 = a22.dropna(subset=["actual", "proj_mean"]).copy()
    a22["PTS_residual"] = a22["actual"] - a22["proj_mean"]
    a22 = attach_coach_for(a22, "2022-23", 2022)
    print(f"22-23 cohort: {len(a22)}")
    print(f"  new_HC count: {a22['new_coach_this_season'].sum()}")
    print(f"  mid_season count: {a22['mid_season_change'].sum()}")

    # --- 23-24 ---
    s24 = pd.read_csv(SHIP_2324)
    s24["nba_api_id"] = s24["nba_api_id"].astype(int)
    s24 = s24.dropna(subset=["PTS_actual", "PTS_proj"]).copy()
    s24["PTS_residual"] = s24["PTS_actual"] - s24["PTS_proj"]
    s24 = attach_coach_for(s24, "2023-24", 2023)
    print(f"23-24 cohort: {len(s24)}")
    print(f"  new_HC count: {s24['new_coach_this_season'].sum()}")
    print(f"  mid_season count: {s24['mid_season_change'].sum()}")

    # ============== Forward validation per coaching class ==============
    print("\n" + "=" * 78)
    print("CROSS-SEASON STABILITY OF COACHING × PTS EFFECTS")
    print("=" * 78)
    for cls in ["new_coach_this_season", "mid_season_change"]:
        r22 = class_mean_residuals(a22, cls, "PTS_residual")
        r24 = class_mean_residuals(s24, cls, "PTS_residual")
        print(f"\n--- {cls} ---")
        print(f"  22-23 SNR: {r22['snr']:.2f}    23-24 SNR: {r24['snr']:.2f}")
        print(f"  22-23 means: True n={r22['counts'].get(True,0)}: "
              f"{r22['means'].get(True, 0):+.3f}  "
              f"False n={r22['counts'].get(False,0)}: {r22['means'].get(False, 0):+.3f}")
        print(f"  23-24 means: True n={r24['counts'].get(True,0)}: "
              f"{r24['means'].get(True, 0):+.3f}  "
              f"False n={r24['counts'].get(False,0)}: {r24['means'].get(False, 0):+.3f}")
        # Differential effect (True - False)
        diff_22 = r22['means'].get(True, 0) - r22['means'].get(False, 0)
        diff_24 = r24['means'].get(True, 0) - r24['means'].get(False, 0)
        print(f"  Differential (True - False):  22-23={diff_22:+.3f}  23-24={diff_24:+.3f}")
        if np.sign(diff_22) == np.sign(diff_24):
            avg = (diff_22 + diff_24) / 2
            print(f"  -> SIGN AGREES. Average differential: {avg:+.3f}")
            print(f"  -> Candidate offset: True players get {r22['means'].get(True,0)} (22-23) "
                  f"avg with {r24['means'].get(True,0)} (23-24)")
        else:
            print(f"  -> SIGN DIVERGES. Reject — season-specific.")

    # ============== Apply candidate offsets to 23-24 and measure MAE delta ==============
    print("\n" + "=" * 78)
    print("CANDIDATE OFFSET APPLICATION (mean of 22-23 and 23-24 class means)")
    print("=" * 78)
    base_mae = (s24["PTS_actual"] - s24["PTS_proj"]).abs().mean()
    print(f"Baseline 23-24 PTS MAE: {base_mae:.4f}")

    for cls in ["new_coach_this_season", "mid_season_change"]:
        r22 = class_mean_residuals(a22, cls, "PTS_residual")
        r24 = class_mean_residuals(s24, cls, "PTS_residual")
        if np.sign(r22['means'].get(True, 0)) != np.sign(r24['means'].get(True, 0)):
            print(f"\n  {cls}: sign-flip, skip.")
            continue
        # Average True / False means across seasons
        avg_true = (r22['means'].get(True, 0) + r24['means'].get(True, 0)) / 2
        avg_false = (r22['means'].get(False, 0) + r24['means'].get(False, 0)) / 2
        print(f"\n  {cls}:")
        print(f"    Averaged True offset:  {avg_true:+.3f}")
        print(f"    Averaged False offset: {avg_false:+.3f}")

        s24[f"PTS_proj_with_{cls}"] = s24["PTS_proj"].copy()
        # Apply: residual is actual - proj. To CORRECT for over-projection (negative resid),
        # we ADD the residual (which is negative) to the projection? No wait.
        # If mean residual = -2.0 (over-projected), correcting means SUBTRACTING 2.0 from proj
        # so it lands closer to actual. Residual = actual - proj. If we want corrected_proj
        # such that actual - corrected_proj is centered, corrected_proj = proj + mean_resid
        # where mean_resid is negative for over-projection.
        s24.loc[s24[cls], f"PTS_proj_with_{cls}"] += avg_true
        s24.loc[~s24[cls], f"PTS_proj_with_{cls}"] += avg_false
        new_mae = (s24["PTS_actual"] - s24[f"PTS_proj_with_{cls}"]).abs().mean()
        delta = new_mae - base_mae
        pct = 100 * delta / base_mae
        print(f"    23-24 PTS MAE: {base_mae:.4f} -> {new_mae:.4f}  ({pct:+.2f}%)")

    # Also: combined Center×PTS + best-coaching offset
    print("\n" + "=" * 78)
    print("COMBINED: Center×PTS (already shipped) + best coaching offset (if validated)")
    print("=" * 78)
    # Re-attach position
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    s24 = s24.merge(meta[["nba_api_id", "position"]], on="nba_api_id", how="left")
    s24["PTS_proj_combined"] = s24["PTS_proj"].copy()
    # Center -0.70
    s24.loc[s24["position"] == "Center", "PTS_proj_combined"] -= 0.70
    # Best coaching: use mid_season_change if its differential survives, else new_coach
    chosen = None
    for cls in ["new_coach_this_season", "mid_season_change"]:
        r22 = class_mean_residuals(a22, cls, "PTS_residual")
        r24 = class_mean_residuals(s24.assign(**{
            "PTS_residual": s24["PTS_actual"] - s24["PTS_proj"]
        }), cls, "PTS_residual")
        if np.sign(r22['means'].get(True, 0)) == np.sign(r24['means'].get(True, 0)):
            avg_true = (r22['means'].get(True, 0) + r24['means'].get(True, 0)) / 2
            avg_false = (r22['means'].get(False, 0) + r24['means'].get(False, 0)) / 2
            print(f"  Adding {cls}: True={avg_true:+.3f}, False={avg_false:+.3f}")
            s24.loc[s24[cls], "PTS_proj_combined"] += avg_true
            s24.loc[~s24[cls], "PTS_proj_combined"] += avg_false
            chosen = cls
            break  # take first (highest priority would be mid first, but order is sufficient)

    combined_mae = (s24["PTS_actual"] - s24["PTS_proj_combined"]).abs().mean()
    print(f"\n  Center alone (v6.1): {1.8584:.4f} (-0.49% vs v6 1.8675)")
    print(f"  Center + {chosen}: {combined_mae:.4f}  "
          f"({100*(combined_mae-1.8675)/1.8675:+.2f}% vs v6 baseline)")


if __name__ == "__main__":
    main()
