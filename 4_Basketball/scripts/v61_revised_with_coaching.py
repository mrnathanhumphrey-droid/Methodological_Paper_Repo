"""v6.1-LOO revised offset spec including coaching classes for REB and BLK.

Spec:
  PTS ← offseason_traded
  REB ← mid_season_change  (NEW — was no offset)
  AST ← offseason_traded
  STL ← offseason_traded
  BLK ← mid_season_change  (UPGRADED from position)
  TOV ← years_pro_bucket
  FTA ← offseason_traded
  FTM ← offseason_traded

Compare to previous -1.48% composite.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")

from pathlib import Path
import numpy as np
import pandas as pd

from ablation_harness import load_baseline, per_stat_mae

REPO = Path(".")
PQ = REPO / "data" / "parquet"
STATS = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FTA", "FTM"]


def attach_features(df, target_year=2023):
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    df = df.merge(meta[["nba_api_id", "position", "birth_date", "draft_year"]],
                  on="nba_api_id", how="left")
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
    season_start = pd.Timestamp(f"{target_year}-10-24")
    df["age"] = (season_start - df["birth_date"]).dt.days / 365.25
    df["years_pro"] = target_year - df["draft_year"]
    df["years_pro_bucket"] = pd.cut(df["years_pro"], bins=[-1, 0, 3, 7, 12, 30],
                                      labels=["rookie", "1-3", "4-7", "8-12", "13+"]).astype(str)

    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    s = box[box["season"] == f"{target_year}-{str(target_year+1)[2:]}"]
    team = s.groupby("nba_api_id")["team_abbr"].agg(
        lambda x: x.value_counts().idxmax()).reset_index()
    team.columns = ["nba_api_id", f"team_{target_year}"]
    df = df.merge(team, on="nba_api_id", how="left")

    cf = pd.read_parquet(PQ / "coaching_change_flags.parquet")
    cf_s = cf[cf["season"] == f"{target_year}-{str(target_year+1)[2:]}"][
        ["team_abbr", "new_coach_this_season", "mid_season_change"]]
    df = df.merge(cf_s, left_on=f"team_{target_year}", right_on="team_abbr", how="left")
    df["new_coach_this_season"] = df["new_coach_this_season"].fillna(False).astype(bool)
    df["mid_season_change"] = df["mid_season_change"].fillna(False).astype(bool)

    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    traded = set(tx[(tx["transaction_type"] == "trade") &
                    (tx["event_date"] >= f"{target_year}-04-15") &
                    (tx["event_date"] <= f"{target_year}-10-24") &
                    (tx["nba_api_id"].notna())]["nba_api_id"].astype(int))
    df["offseason_traded"] = df["nba_api_id"].astype(int).isin(traded)

    for s in STATS:
        proj, actual = f"{s}_proj", f"{s}_actual"
        if proj in df.columns and actual in df.columns:
            df[f"{s}_residual"] = df[actual] - df[proj]
    return df


def loo_class_means(df, class_col, residual_col):
    sub = df.dropna(subset=[class_col, residual_col]).copy()
    out = {}
    for cls, idx in sub.groupby(class_col, observed=True).groups.items():
        idx = list(idx)
        for i in idx:
            others = [j for j in idx if j != i]
            mean = sub.loc[others, residual_col].mean() if others else 0.0
            out[i] = mean
    return out


def apply_offsets(base, df, spec):
    """spec: dict[stat -> class_col]."""
    out = base.copy()
    for stat, cls in spec.items():
        proj_col = f"{stat}_proj"
        if proj_col not in out.columns:
            continue
        sub = df.dropna(subset=[f"{stat}_residual"]).copy()
        loo_map = loo_class_means(sub, cls, f"{stat}_residual")
        # Map idx -> nba_api_id for delta lookup
        idx_to_pid = dict(zip(sub.index, sub["nba_api_id"].astype(int)))
        pid_to_delta = {idx_to_pid[i]: v for i, v in loo_map.items()}
        out[proj_col] = out.apply(
            lambda r: r[proj_col] + pid_to_delta.get(int(r["nba_api_id"]), 0.0)
            if pd.notna(r[proj_col]) else r[proj_col], axis=1)
    return out


def main():
    base = load_baseline()
    base["nba_api_id"] = base["nba_api_id"].astype(int)
    df = attach_features(base, target_year=2023)
    df = df.dropna(subset=["PTS_residual"])
    print(f"Cohort: {len(df)}")

    base_mae = per_stat_mae(base)

    SPEC_PREV = {
        "PTS": "offseason_traded",
        "AST": "offseason_traded",
        "STL": "offseason_traded",
        "BLK": "position",
        "TOV": "years_pro_bucket",
        "FTA": "offseason_traded",
        "FTM": "offseason_traded",
    }
    SPEC_NEW = {
        "PTS": "offseason_traded",
        "REB": "mid_season_change",      # NEW
        "AST": "offseason_traded",
        "STL": "offseason_traded",
        "BLK": "mid_season_change",      # UPGRADED
        "TOV": "years_pro_bucket",
        "FTA": "offseason_traded",
        "FTM": "offseason_traded",
    }

    # Need position attached for SPEC_PREV
    df["position"] = df["position"].astype(str)

    print("\n--- SPEC_PREV (no coaching, REB blank, BLK=position) ---")
    out_prev = apply_offsets(base, df, SPEC_PREV)
    mae_prev = per_stat_mae(out_prev)
    for s in STATS:
        b = base_mae[s]
        p = mae_prev[s]
        pct = 100 * (p - b) / b if b > 0 else np.nan
        print(f"  {s:<5}  {b:.4f} -> {p:.4f}  ({pct:+.2f}%)")
    pcts_prev = [100 * (mae_prev[s] - base_mae[s]) / base_mae[s] for s in STATS]
    comp_prev = np.mean(pcts_prev)
    print(f"  composite avg: {comp_prev:+.2f}%")

    print("\n--- SPEC_NEW (REB=mid, BLK=mid, others same) ---")
    out_new = apply_offsets(base, df, SPEC_NEW)
    mae_new = per_stat_mae(out_new)
    for s in STATS:
        b = base_mae[s]
        n = mae_new[s]
        pct = 100 * (n - b) / b if b > 0 else np.nan
        print(f"  {s:<5}  {b:.4f} -> {n:.4f}  ({pct:+.2f}%)")
    pcts_new = [100 * (mae_new[s] - base_mae[s]) / base_mae[s] for s in STATS]
    comp_new = np.mean(pcts_new)
    print(f"  composite avg: {comp_new:+.2f}%")

    print("\n=== SUMMARY ===")
    print(f"  prev (no coaching):        {comp_prev:+.2f}%")
    print(f"  new (REB+BLK via mid):     {comp_new:+.2f}%")
    print(f"  improvement:               {comp_new - comp_prev:+.2f}pp")


if __name__ == "__main__":
    main()
