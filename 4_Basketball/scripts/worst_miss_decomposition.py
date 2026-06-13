"""Worst-miss decomposition: where does the remaining PTS MAE actually live?

After the v6.1 Center×PTS offset, PTS MAE is 1.8584. To get to 1.7xx we need
another ~5% reduction. This script identifies the cluster of biggest residuals
and looks for shared characteristics so we can target a sub-class fix.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")

from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"


def attach_features(df, target_year=2023):
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
    s = box[box["season"] == "2023-24"]
    team = s.groupby("nba_api_id")["team_abbr"].agg(
        lambda x: x.value_counts().idxmax()).reset_index()
    team.columns = ["nba_api_id", "team_2324"]
    df = df.merge(team, on="nba_api_id", how="left")

    cf = pd.read_parquet(PQ / "coaching_change_flags.parquet")
    cf_23 = cf[cf["season"] == "2023-24"][["team_abbr", "new_coach_this_season",
                                              "mid_season_change"]]
    df = df.merge(cf_23, left_on="team_2324", right_on="team_abbr", how="left")
    df["new_coach_this_season"] = df["new_coach_this_season"].fillna(False).astype(bool)
    df["mid_season_change"] = df["mid_season_change"].fillna(False).astype(bool)

    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    traded = set(tx[(tx["transaction_type"] == "trade") &
                    (tx["event_date"] >= "2023-04-15") &
                    (tx["event_date"] <= "2023-10-24") &
                    (tx["nba_api_id"].notna())]["nba_api_id"].astype(int))
    df["offseason_traded"] = df["nba_api_id"].astype(int).isin(traded)

    return df


def main():
    # Load v6.1 corrected ship (post Center offset) so we look at REMAINING residuals
    ship = pd.read_csv(REPO / "audit_runs" / "unified_ship_v6_1" / "per_player_projections_2023-24.csv")
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    ship = ship.dropna(subset=["PTS_actual", "PTS_proj"]).copy()
    ship["PTS_residual"] = ship["PTS_actual"] - ship["PTS_proj"]
    ship["PTS_abs_resid"] = ship["PTS_residual"].abs()

    df = attach_features(ship, target_year=2023)
    df = df.sort_values("PTS_abs_resid", ascending=False)

    print(f"Cohort: {len(df)}")
    print(f"PTS mean residual: {df['PTS_residual'].mean():+.4f}")
    print(f"PTS MAE:           {df['PTS_abs_resid'].mean():.4f}")
    print(f"PTS RMSE:          {np.sqrt((df['PTS_residual']**2).mean()):.4f}")

    # ============== Top 30 worst misses ==============
    print("\n" + "=" * 100)
    print("TOP 30 WORST PTS MISSES (post v6.1 Center offset)")
    print("=" * 100)
    print(f"{'name':<24} {'pos':<8} {'age_b':<6} {'yrs_pro':<8} "
          f"{'team':<5} {'traded':<6} {'mid_HC':<7} {'new_HC':<7} "
          f"{'proj':>6} {'actual':>7} {'resid':>7} {'|res|':>6}")
    print("-" * 110)
    for _, r in df.head(30).iterrows():
        nm = r["name"][:24] if isinstance(r["name"], str) else "?"
        print(f"{nm:<24} {r['position']!s:<8} {r['age_bucket']!s:<6} "
              f"{r['years_pro_bucket']!s:<8} {r['team_2324']!s:<5} "
              f"{'Y' if r['offseason_traded'] else '.':<6} "
              f"{'Y' if r['mid_season_change'] else '.':<7} "
              f"{'Y' if r['new_coach_this_season'] else '.':<7} "
              f"{r['PTS_proj']:>6.2f} {r['PTS_actual']:>7.2f} "
              f"{r['PTS_residual']:>+7.2f} {r['PTS_abs_resid']:>6.2f}")

    # ============== Stratify by residual tier ==============
    print("\n" + "=" * 100)
    print("RESIDUAL TIER STRATIFICATION")
    print("=" * 100)
    df["tier"] = pd.cut(df["PTS_abs_resid"],
                          bins=[-0.01, 0.5, 1.0, 2.0, 4.0, 100],
                          labels=["<0.5", "0.5-1", "1-2", "2-4", "4+"])
    tier_summary = df.groupby("tier", observed=True).agg(
        n=("PTS_abs_resid", "count"),
        mean_abs=("PTS_abs_resid", "mean"),
        mean_resid=("PTS_residual", "mean"),
        contrib_to_total=("PTS_abs_resid", "sum"),
    ).reset_index()
    tier_summary["pct_of_mae"] = 100 * tier_summary["contrib_to_total"] / df["PTS_abs_resid"].sum()
    print(tier_summary.to_string(index=False))

    # Most of MAE concentrated where?
    print()
    big = df[df["PTS_abs_resid"] >= 2.0]
    print(f"Players with |residual| >= 2.0: {len(big)} ({100*len(big)/len(df):.1f}% of cohort)")
    print(f"  Their share of total |residual| sum: {100*big['PTS_abs_resid'].sum()/df['PTS_abs_resid'].sum():.1f}%")

    # ============== Direction of miss ==============
    print("\n" + "=" * 100)
    print("DIRECTION: over-projected (positive proj-actual) vs under-projected")
    print("=" * 100)
    over = df[df["PTS_residual"] < -1.0]  # actual < proj
    under = df[df["PTS_residual"] > 1.0]   # actual > proj
    print(f"Over-projected (|resid| > 1, proj too high): {len(over)} players")
    print(f"  Mean over: {over['PTS_residual'].mean():.2f}  Total: {over['PTS_residual'].sum():.1f}")
    print(f"Under-projected (|resid| > 1, actual exceeded): {len(under)} players")
    print(f"  Mean under: {under['PTS_residual'].mean():.2f}  Total: {under['PTS_residual'].sum():.1f}")
    print(f"Net imbalance: over {len(over)} vs under {len(under)} = "
          f"asymmetry of {len(over) - len(under)} → suggests systematic bias")

    # ============== Class-mean over the high-residual subset ==============
    print("\n" + "=" * 100)
    print("CLASS BREAKDOWN OF |residual| >= 2.0 cohort (n={})".format(len(big)))
    print("=" * 100)
    for col in ["position", "age_bucket", "years_pro_bucket",
                  "offseason_traded", "mid_season_change", "new_coach_this_season"]:
        vc = big[col].value_counts(dropna=False)
        # Compare distribution to full cohort
        full_vc = df[col].value_counts(dropna=False)
        print(f"\n  {col}:")
        for k in vc.index:
            n_big = vc[k]
            n_full = full_vc.get(k, 0)
            pct_big = 100 * n_big / len(big)
            pct_full = 100 * n_full / len(df)
            enrichment = pct_big / pct_full if pct_full > 0 else 0
            mean_resid = big[big[col] == k]["PTS_residual"].mean()
            flag = "ENRICHED" if enrichment >= 1.5 else ("DEPLETED" if enrichment <= 0.5 else "")
            print(f"    {str(k):<14}  n_big={n_big:>3} ({pct_big:>5.1f}%)  "
                  f"n_full={n_full:>3} ({pct_full:>5.1f}%)  "
                  f"x{enrichment:.2f}  mean_resid={mean_resid:+.2f}  {flag}")

    # ============== Volume tier (ship's projected PTS quartile) ==============
    print("\n" + "=" * 100)
    print("PROJECTED-PTS QUARTILE × RESIDUAL")
    print("=" * 100)
    df["pts_quartile"] = pd.qcut(df["PTS_proj"], 4,
                                    labels=["Q1 (low scorers)", "Q2", "Q3", "Q4 (top scorers)"])
    qsum = df.groupby("pts_quartile", observed=True).agg(
        n=("PTS_actual", "count"),
        proj_mean=("PTS_proj", "mean"),
        actual_mean=("PTS_actual", "mean"),
        mean_resid=("PTS_residual", "mean"),
        mae=("PTS_abs_resid", "mean"),
    ).reset_index()
    print(qsum.to_string(index=False))


if __name__ == "__main__":
    main()
