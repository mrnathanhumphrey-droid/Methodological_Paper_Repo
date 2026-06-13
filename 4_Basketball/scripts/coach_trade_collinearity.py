"""Check multicollinearity between offseason_traded and mid_season_change /
new_coach_this_season.

Tests:
  1. Co-occurrence and Pearson r of the binary flags
  2. Conditional SNR: after applying offseason_traded LOO offset to PTS/AST/STL/FTA/FTM,
     does mid_season_change still show SNR>=1.5 on those stats?
  3. After applying mid_season_change offset to REB, does any other class re-emerge?
  4. Partial regression: fit residual ~ trade_flag + coach_flag, report coefficients
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")

from pathlib import Path
import numpy as np
import pandas as pd

from ablation_harness import load_baseline

REPO = Path(".")
PQ = REPO / "data" / "parquet"
STATS = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FTA", "FTM"]


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


def nf(df, cls, res_col):
    sub = df.dropna(subset=[cls, res_col]).copy()
    grouped = sub.groupby(cls, observed=True)[res_col].agg(["mean", "count"]).reset_index()
    grouped = grouped[grouped["count"] >= 2]
    if len(grouped) < 2:
        return None
    sd_obs = grouped["mean"].std(ddof=1)
    var = sub[res_col].var(ddof=1)
    n_per = grouped["count"].mean()
    se = np.sqrt(var / n_per)
    return {"snr": sd_obs / se if se > 0 else np.nan,
            "means": dict(zip(grouped[cls], grouped["mean"]))}


def main():
    base = load_baseline()
    base["nba_api_id"] = base["nba_api_id"].astype(int)

    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    s23 = box[box["season"] == "2023-24"]
    team_23 = s23.groupby("nba_api_id")["team_abbr"].agg(
        lambda x: x.value_counts().idxmax()).reset_index()
    team_23.columns = ["nba_api_id", "team_2324"]
    df = base.merge(team_23, on="nba_api_id", how="left")

    cf = pd.read_parquet(PQ / "coaching_change_flags.parquet")
    cf_23 = cf[cf["season"] == "2023-24"][["team_abbr", "new_coach_this_season",
                                              "mid_season_change"]]
    df = df.merge(cf_23, left_on="team_2324", right_on="team_abbr", how="left",
                   suffixes=("", "_cf"))
    df["new_coach_this_season"] = df["new_coach_this_season"].fillna(False).astype(bool)
    df["mid_season_change"] = df["mid_season_change"].fillna(False).astype(bool)

    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    traded = set(tx[(tx["transaction_type"] == "trade") &
                    (tx["event_date"] >= "2023-04-15") &
                    (tx["event_date"] <= "2023-10-24") &
                    (tx["nba_api_id"].notna())]["nba_api_id"].astype(int))
    df["offseason_traded"] = df["nba_api_id"].astype(int).isin(traded)

    for s in STATS:
        proj, actual = f"{s}_proj", f"{s}_actual"
        if proj in df.columns and actual in df.columns:
            df[f"{s}_residual"] = df[actual] - df[proj]

    # ============== TEST 1: Co-occurrence ==============
    print("=" * 78)
    print("TEST 1: Co-occurrence and Pearson r")
    print("=" * 78)
    n_total = len(df)
    n_trade = df["offseason_traded"].sum()
    n_new_hc = df["new_coach_this_season"].sum()
    n_mid = df["mid_season_change"].sum()
    print(f"Cohort:                            {n_total}")
    print(f"offseason_traded:                  {n_trade}")
    print(f"new_coach_this_season:             {n_new_hc}")
    print(f"mid_season_change:                 {n_mid}")

    n_trade_AND_new_hc = ((df["offseason_traded"]) & (df["new_coach_this_season"])).sum()
    n_trade_AND_mid = ((df["offseason_traded"]) & (df["mid_season_change"])).sum()
    n_new_hc_AND_mid = ((df["new_coach_this_season"]) & (df["mid_season_change"])).sum()
    print(f"\nIntersections:")
    print(f"  trade & new_hc:  {n_trade_AND_new_hc}  "
          f"(of {n_trade} traded, {100*n_trade_AND_new_hc/max(n_trade,1):.1f}% on new-HC team)")
    print(f"  trade & mid:     {n_trade_AND_mid}  "
          f"(of {n_trade} traded, {100*n_trade_AND_mid/max(n_trade,1):.1f}% on mid-change)")
    print(f"  new_hc & mid:    {n_new_hc_AND_mid}")

    # Pearson r
    r_trade_newhc = df["offseason_traded"].astype(int).corr(df["new_coach_this_season"].astype(int))
    r_trade_mid = df["offseason_traded"].astype(int).corr(df["mid_season_change"].astype(int))
    r_newhc_mid = df["new_coach_this_season"].astype(int).corr(df["mid_season_change"].astype(int))
    print(f"\nPearson r:")
    print(f"  trade vs new_hc:  {r_trade_newhc:+.3f}")
    print(f"  trade vs mid:     {r_trade_mid:+.3f}")
    print(f"  new_hc vs mid:    {r_newhc_mid:+.3f}")

    # ============== TEST 2: Conditional SNR after applying trade offset ==============
    print("\n" + "=" * 78)
    print("TEST 2: After applying offseason_traded LOO offset, does coach effect remain?")
    print("=" * 78)
    print(f"{'stat':<5}  {'orig new_hc SNR':>15}  {'after trade SNR':>17}  "
          f"{'orig mid SNR':>13}  {'after trade SNR':>17}")
    print("-" * 80)
    for s in STATS:
        rcol = f"{s}_residual"
        if rcol not in df.columns:
            continue
        # Before
        orig_new = nf(df, "new_coach_this_season", rcol)
        orig_mid = nf(df, "mid_season_change", rcol)
        # Apply trade LOO offset
        loo = loo_class_means(df.dropna(subset=[rcol]), "offseason_traded", rcol)
        df[f"{s}_resid_after_trade"] = df[rcol] - df.index.map(loo).fillna(0.0)
        after_new = nf(df, "new_coach_this_season", f"{s}_resid_after_trade")
        after_mid = nf(df, "mid_season_change", f"{s}_resid_after_trade")
        on = orig_new["snr"] if orig_new else float("nan")
        an = after_new["snr"] if after_new else float("nan")
        om = orig_mid["snr"] if orig_mid else float("nan")
        am = after_mid["snr"] if after_mid else float("nan")
        print(f"{s:<5}  {on:>15.2f}  {an:>17.2f}  {om:>13.2f}  {am:>17.2f}")

    # ============== TEST 3: Conversely, does trade still show after mid_season offset? ==============
    print("\n" + "=" * 78)
    print("TEST 3: After applying mid_season_change offset, does trade effect remain?")
    print("=" * 78)
    print(f"{'stat':<5}  {'orig trade SNR':>15}  {'after mid SNR':>15}")
    print("-" * 50)
    for s in STATS:
        rcol = f"{s}_residual"
        if rcol not in df.columns:
            continue
        orig_trade = nf(df, "offseason_traded", rcol)
        loo = loo_class_means(df.dropna(subset=[rcol]), "mid_season_change", rcol)
        df[f"{s}_resid_after_mid"] = df[rcol] - df.index.map(loo).fillna(0.0)
        after_trade = nf(df, "offseason_traded", f"{s}_resid_after_mid")
        ot = orig_trade["snr"] if orig_trade else float("nan")
        at = after_trade["snr"] if after_trade else float("nan")
        print(f"{s:<5}  {ot:>15.2f}  {at:>15.2f}")

    # ============== TEST 4: Partial regression ==============
    print("\n" + "=" * 78)
    print("TEST 4: Joint OLS: residual ~ trade + new_hc + mid_change (per stat)")
    print("=" * 78)
    print(f"{'stat':<5}  {'beta_trade':>10}  {'beta_new_hc':>11}  "
          f"{'beta_mid':>9}  {'R^2':>5}")
    print("-" * 50)
    for s in STATS:
        rcol = f"{s}_residual"
        if rcol not in df.columns:
            continue
        sub = df.dropna(subset=[rcol]).copy()
        X = np.column_stack([
            np.ones(len(sub)),
            sub["offseason_traded"].astype(int),
            sub["new_coach_this_season"].astype(int),
            sub["mid_season_change"].astype(int),
        ])
        y = sub[rcol].values
        beta, res, rank, sv = np.linalg.lstsq(X, y, rcond=None)
        ss_tot = ((y - y.mean()) ** 2).sum()
        y_pred = X @ beta
        ss_res = ((y - y_pred) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        print(f"{s:<5}  {beta[1]:>+10.3f}  {beta[2]:>+11.3f}  "
              f"{beta[3]:>+9.3f}  {r2:>5.3f}")


if __name__ == "__main__":
    main()
