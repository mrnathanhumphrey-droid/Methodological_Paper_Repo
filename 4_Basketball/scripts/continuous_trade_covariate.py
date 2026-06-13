"""Replace binary `offseason_traded` with continuous covariates that capture
the DIRECTION of the trade (pace, depth, role).

Hypothesis: the trade-class residual flips sign because trades aren't a
single thing. A trade from a slow rebuild team to a fast contender has a
different residual signature than the reverse. Binary `traded` averages
over heterogeneous events.

Test:
  1. Compute pace_delta (new team - old team) and depth_delta (new team
     position group - old team position group) for each offseason-traded
     player in 23-24.
  2. Within trade cohort, regress PTS_residual ~ pace_delta + depth_delta
  3. If R^2 is meaningful (>0.15) and signs are interpretable, this is a
     viable continuous feature.
  4. Repeat for 22-23 cohort (apples-to-apples PTS audit). If signs and
     coefficients agree across seasons → cross-season-stable continuous
     covariate.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
SHIP_2324 = REPO / "audit_runs" / "unified_ship_v6" / "per_player_projections_2023-24.csv"
AUDIT_2223_PTS = REPO / "audit_runs" / "20260501T222551Z" / "skill_backtest_PTS_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22__2022-23" / "per_player_projections.csv"


def compute_team_pace_proxy(box, season):
    """For (team, season), compute average team total points scored per team-game.

    This is a pace × efficiency proxy. High pps = fast & efficient team.
    """
    s = box[box["season"] == season]
    # Per (team, game), sum points across all team players
    by_game = s.groupby(["team_abbr", "game_id"])["PTS"].sum().reset_index()
    by_team = by_game.groupby("team_abbr").agg(
        gp=("game_id", "count"),
        team_total_pts=("PTS", "sum"),
    ).reset_index()
    by_team["pace_proxy"] = by_team["team_total_pts"] / by_team["gp"]
    return dict(zip(by_team["team_abbr"], by_team["pace_proxy"]))


def compute_team_depth_at_position(box, meta, season):
    """For (team, season, position), sum mpg at position from box scores.
    Returns dict[(team, position) -> total team mpg at position]."""
    s = box[box["season"] == season].copy()
    s = s.merge(meta[["nba_api_id", "position"]], on="nba_api_id", how="left")
    s = s.dropna(subset=["position"])
    s["minutes"] = pd.to_numeric(s["minutes"], errors="coerce")
    by_player = s.groupby(["team_abbr", "position", "nba_api_id"]).agg(
        gp=("game_id", "nunique"),
        total_min=("minutes", "sum"),
    ).reset_index()
    by_player["mpg"] = by_player["total_min"] / by_player["gp"]
    by_team_pos = by_player.groupby(["team_abbr", "position"])["mpg"].sum().reset_index()
    return dict(zip(zip(by_team_pos["team_abbr"], by_team_pos["position"]),
                     by_team_pos["mpg"]))


def compute_player_team_per_season(box):
    """For each (player, season), dominant team."""
    by_pst = box.groupby(["nba_api_id", "season", "team_abbr"]).size().reset_index(name="games")
    by_pst = by_pst.sort_values("games", ascending=False).drop_duplicates(["nba_api_id", "season"])
    return by_pst[["nba_api_id", "season", "team_abbr"]]


def build_trade_features(target_year, residual_df, target_residual_col):
    """For each offseason-traded player in target_year, compute continuous features."""
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["minutes"] = pd.to_numeric(box["minutes"], errors="coerce")
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    box["PTS"] = pd.to_numeric(box["PTS"], errors="coerce")
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    meta["nba_api_id"] = meta["nba_api_id"].astype(int)

    prior_season = f"{target_year-1}-{str(target_year)[2:]}"
    target_season = f"{target_year}-{str(target_year+1)[2:]}"

    pace_prior = compute_team_pace_proxy(box, prior_season)
    pace_target = compute_team_pace_proxy(box, target_season)
    depth_prior = compute_team_depth_at_position(box, meta, prior_season)
    depth_target = compute_team_depth_at_position(box, meta, target_season)

    player_team = compute_player_team_per_season(box)
    pt_prior = player_team[player_team["season"] == prior_season]
    pt_target = player_team[player_team["season"] == target_season]
    team_prior = dict(zip(pt_prior["nba_api_id"], pt_prior["team_abbr"]))
    team_target = dict(zip(pt_target["nba_api_id"], pt_target["team_abbr"]))

    # Identify offseason traded
    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    traded = set(tx[(tx["transaction_type"] == "trade") &
                    (tx["event_date"] >= pd.Timestamp(f"{target_year}-04-15")) &
                    (tx["event_date"] <= pd.Timestamp(f"{target_year}-10-24")) &
                    (tx["nba_api_id"].notna())]["nba_api_id"].astype(int))

    rows = []
    for _, r in residual_df.iterrows():
        pid = int(r["nba_api_id"])
        if pid not in traded:
            continue
        old_team = team_prior.get(pid)
        new_team = team_target.get(pid)
        pos = meta.loc[meta["nba_api_id"] == pid, "position"].values
        if len(pos) == 0:
            continue
        pos = pos[0]
        if old_team is None or new_team is None or old_team == new_team:
            continue  # didn't actually move teams (PST may have noise)
        pace_d = pace_target.get(new_team, np.nan) - pace_prior.get(old_team, np.nan)
        depth_d = (depth_target.get((new_team, pos), np.nan) -
                    depth_prior.get((old_team, pos), np.nan))
        rows.append({
            "nba_api_id": pid,
            "name": r.get("name", str(pid)),
            "position": pos,
            "old_team": old_team, "new_team": new_team,
            "pace_old": pace_prior.get(old_team, np.nan),
            "pace_new": pace_target.get(new_team, np.nan),
            "pace_delta": pace_d,
            "depth_old": depth_prior.get((old_team, pos), np.nan),
            "depth_new": depth_target.get((new_team, pos), np.nan),
            "depth_delta": depth_d,
            "residual": r[target_residual_col],
        })
    return pd.DataFrame(rows)


def main():
    # 23-24 cohort
    s24 = pd.read_csv(SHIP_2324)
    s24["nba_api_id"] = s24["nba_api_id"].astype(int)
    s24 = s24.dropna(subset=["PTS_actual"]).copy()
    s24["PTS_residual"] = s24["PTS_actual"] - s24["PTS_proj"]
    s24_features = build_trade_features(2023, s24, "PTS_residual")
    print(f"23-24 traded cohort with features: {len(s24_features)}")

    # 22-23 cohort (apples-to-apples PTS audit)
    a22 = pd.read_csv(AUDIT_2223_PTS)
    a22["nba_api_id"] = a22["nba_api_id"].astype(int)
    a22 = a22.dropna(subset=["actual", "proj_mean"]).copy()
    a22["PTS_residual"] = a22["actual"] - a22["proj_mean"]
    a22_features = build_trade_features(2022, a22, "PTS_residual")
    print(f"22-23 traded cohort with features: {len(a22_features)}")

    # ============== Show the data ==============
    print("\n" + "=" * 100)
    print("23-24 TRADED COHORT WITH CONTINUOUS FEATURES")
    print("=" * 100)
    print(s24_features.sort_values("residual").to_string(index=False))

    print("\n" + "=" * 100)
    print("22-23 TRADED COHORT WITH CONTINUOUS FEATURES")
    print("=" * 100)
    print(a22_features.sort_values("residual").to_string(index=False))

    # ============== Correlation analysis ==============
    print("\n" + "=" * 78)
    print("CORRELATIONS WITHIN TRADE COHORT")
    print("=" * 78)
    for label, df in [("23-24", s24_features), ("22-23", a22_features)]:
        sub = df.dropna(subset=["pace_delta", "depth_delta", "residual"])
        if len(sub) < 5:
            print(f"  {label}: n too small ({len(sub)})")
            continue
        r_pace = sub["pace_delta"].corr(sub["residual"])
        r_depth = sub["depth_delta"].corr(sub["residual"])
        print(f"\n  {label} (n={len(sub)}):")
        print(f"    Pearson r(pace_delta, residual):    {r_pace:+.3f}")
        print(f"    Pearson r(depth_delta, residual):   {r_depth:+.3f}")
        # Interpretation hint
        if abs(r_pace) > 0.3:
            sign = "FASTER team -> HIGHER PTS" if r_pace > 0 else "FASTER team -> LOWER PTS"
            print(f"    -> pace effect: {sign}")
        if abs(r_depth) > 0.3:
            sign = "MORE depth -> HIGHER PTS" if r_depth > 0 else "MORE depth -> LOWER PTS"
            print(f"    -> depth effect: {sign}")

    # ============== Joint OLS: residual ~ pace_delta + depth_delta ==============
    print("\n" + "=" * 78)
    print("JOINT OLS: residual ~ intercept + pace_delta + depth_delta")
    print("=" * 78)
    for label, df in [("23-24", s24_features), ("22-23", a22_features)]:
        sub = df.dropna(subset=["pace_delta", "depth_delta", "residual"])
        if len(sub) < 5:
            continue
        X = np.column_stack([np.ones(len(sub)),
                              sub["pace_delta"].values,
                              sub["depth_delta"].values])
        y = sub["residual"].values
        beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        y_pred = X @ beta
        ss_res = ((y - y_pred) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        print(f"\n  {label} (n={len(sub)}):")
        print(f"    intercept:        {beta[0]:+.3f}")
        print(f"    beta_pace_delta:  {beta[1]:+.3f}  (per +1 pps team-pts/game)")
        print(f"    beta_depth_delta: {beta[2]:+.3f}  (per +1 mpg position group)")
        print(f"    R^2:              {r2:.3f}")

    # ============== Cross-season comparison ==============
    print("\n" + "=" * 78)
    print("DIAGNOSIS")
    print("=" * 78)
    print("""
If R^2 in both seasons > 0.15 with same coefficient signs:
  -> CONTINUOUS COVARIATE WORKS. Replace binary trade flag with pace_delta / depth_delta.
If R^2 < 0.10 in either season or sign flips:
  -> Continuous features don't add either. Trade-class is genuinely noisy at any granularity.
""")


if __name__ == "__main__":
    main()
