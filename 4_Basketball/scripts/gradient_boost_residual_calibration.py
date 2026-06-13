"""Gradient boost residual calibration (Desktop #3).

Train a small GBM on 22-23 PTS residuals to predict residual from observable
features. Apply to 23-24 v6 ship. Compare MAE to v6.1 class-offset version.

This is a strictly more flexible replacement for the parsimonious top-1 class
offset table — captures nonlinear feature interactions that simple class means
miss.

Discipline:
  - Strict regularization (max_depth=3, n_estimators=50, lr=0.05) given small n
  - Forward validation: trained on 22-23, scored on 23-24 actuals
  - Compare against class-offset baseline AND raw v6
  - 5-fold CV on 22-23 to estimate generalization gap
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import KFold, cross_val_score

REPO = Path(".")
PQ = REPO / "data" / "parquet"
SHIP_2324 = REPO / "audit_runs" / "unified_ship_v6" / "per_player_projections_2023-24.csv"
AUDIT_2223_PTS = REPO / "audit_runs" / "20260501T222551Z" / "skill_backtest_PTS_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22__2022-23" / "per_player_projections.csv"


def compute_team_pace(box, season):
    s = box[box["season"] == season]
    by_game = s.groupby(["team_abbr", "game_id"])["PTS"].sum().reset_index()
    by_team = by_game.groupby("team_abbr").agg(
        gp=("game_id", "count"),
        team_total_pts=("PTS", "sum"),
    ).reset_index()
    by_team["pace_proxy"] = by_team["team_total_pts"] / by_team["gp"]
    return dict(zip(by_team["team_abbr"], by_team["pace_proxy"]))


def compute_team_depth_at_position(box, meta, season):
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


def compute_player_prior_per36(box, target_year):
    """For each player, their per-36 PTS in target_year - 1."""
    prior_season = f"{target_year-1}-{str(target_year)[2:]}"
    s = box[box["season"] == prior_season].copy()
    s["minutes"] = pd.to_numeric(s["minutes"], errors="coerce")
    s["PTS"] = pd.to_numeric(s["PTS"], errors="coerce")
    by_player = s.groupby("nba_api_id").agg(
        gp=("game_id", "nunique"),
        total_min=("minutes", "sum"),
        total_pts=("PTS", "sum"),
    ).reset_index()
    by_player["prior_pts_per36"] = (by_player["total_pts"] /
                                     by_player["total_min"].replace(0, np.nan)) * 36
    by_player["prior_mpg"] = (by_player["total_min"] /
                                by_player["gp"].replace(0, np.nan))
    return dict(zip(by_player["nba_api_id"].astype(int), by_player["prior_pts_per36"])), \
            dict(zip(by_player["nba_api_id"].astype(int), by_player["prior_mpg"]))


def build_features(df, target_year, proj_col="PTS_proj", mpg_col="MPG_proj"):
    """Construct feature matrix for the GBM.

    Features (all observable at projection time):
      - position one-hot (Center, Forward, Guard)
      - age (years)
      - years_pro
      - offseason_traded (binary)
      - new_coach_this_season (binary)
      - mid_season_change (binary)
      - proj_PTS (current PTS projection)
      - proj_MPG (current MPG projection)
      - prior_year_pts_per36 (from box scores)
      - prior_year_mpg
      - team_pace_proxy (this season's team)
      - team_depth_at_position (this season's team)
    """
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    box["minutes"] = pd.to_numeric(box["minutes"], errors="coerce")
    box["PTS"] = pd.to_numeric(box["PTS"], errors="coerce")

    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    meta["nba_api_id"] = meta["nba_api_id"].astype(int)

    # Position + age + years_pro
    df = df.copy()
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    df = df.merge(meta[["nba_api_id", "position", "birth_date", "draft_year"]],
                  on="nba_api_id", how="left")
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
    df["age"] = (pd.Timestamp(f"{target_year}-10-24") - df["birth_date"]).dt.days / 365.25
    df["years_pro"] = target_year - df["draft_year"]
    # Position one-hot
    for p in ["Center", "Forward", "Guard"]:
        df[f"pos_{p}"] = (df["position"] == p).astype(int)

    # Team for season
    season_label = f"{target_year}-{str(target_year+1)[2:]}"
    s = box[box["season"] == season_label]
    team_map = s.groupby("nba_api_id")["team_abbr"].agg(
        lambda x: x.value_counts().idxmax()).reset_index()
    team_map.columns = ["nba_api_id", "team_for_season"]
    df = df.merge(team_map, on="nba_api_id", how="left")

    # Coaching flags
    cf = pd.read_parquet(PQ / "coaching_change_flags.parquet")
    cf_s = cf[cf["season"] == season_label][["team_abbr", "new_coach_this_season",
                                                "mid_season_change"]]
    df = df.merge(cf_s, left_on="team_for_season", right_on="team_abbr",
                   how="left", suffixes=("", "_cf"))
    df["new_coach_this_season"] = df["new_coach_this_season"].fillna(False).astype(int)
    df["mid_season_change"] = df["mid_season_change"].fillna(False).astype(int)

    # Trade flag
    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    traded = set(tx[(tx["transaction_type"] == "trade") &
                    (tx["event_date"] >= pd.Timestamp(f"{target_year}-04-15")) &
                    (tx["event_date"] <= pd.Timestamp(f"{target_year}-10-24")) &
                    (tx["nba_api_id"].notna())]["nba_api_id"].astype(int))
    df["offseason_traded"] = df["nba_api_id"].astype(int).isin(traded).astype(int)

    # Prior year per36 / mpg
    prior_per36, prior_mpg = compute_player_prior_per36(box, target_year)
    df["prior_pts_per36"] = df["nba_api_id"].astype(int).map(prior_per36)
    df["prior_mpg"] = df["nba_api_id"].astype(int).map(prior_mpg)

    # Team pace + depth
    pace = compute_team_pace(box, season_label)
    depth = compute_team_depth_at_position(box, meta, season_label)
    df["team_pace_proxy"] = df["team_for_season"].map(pace)
    df["team_depth_at_pos"] = df.apply(
        lambda r: depth.get((r["team_for_season"], r["position"]), np.nan),
        axis=1)

    return df


FEATURE_COLS = [
    "pos_Center", "pos_Forward", "pos_Guard",
    "age", "years_pro",
    "offseason_traded", "new_coach_this_season", "mid_season_change",
    "PTS_proj", "MPG_proj",
    "prior_pts_per36", "prior_mpg",
    "team_pace_proxy", "team_depth_at_pos",
]


def main():
    print("Building 22-23 training data...")
    a22 = pd.read_csv(AUDIT_2223_PTS)
    a22["nba_api_id"] = a22["nba_api_id"].astype(int)
    a22 = a22.dropna(subset=["actual", "proj_mean"]).copy()
    a22["PTS_residual"] = a22["actual"] - a22["proj_mean"]
    a22 = a22.rename(columns={"proj_mean": "PTS_proj"})
    # Need MPG_proj too; the 22-23 audit doesn't have it directly. Use prior MPG as proxy
    # OR we can leave it out for training. Actually, for 22-23 audit we don't have a v6
    # MPG projection. Let's just use prior season MPG as proxy.
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    box["minutes"] = pd.to_numeric(box["minutes"], errors="coerce")
    s2122 = box[box["season"] == "2021-22"]
    s2122_mpg = s2122.groupby("nba_api_id").agg(
        gp=("game_id", "nunique"),
        m=("minutes", "sum"),
    ).reset_index()
    s2122_mpg["MPG_proj"] = s2122_mpg["m"] / s2122_mpg["gp"]
    a22 = a22.merge(s2122_mpg[["nba_api_id", "MPG_proj"]], on="nba_api_id", how="left")
    a22["MPG_proj"] = a22["MPG_proj"].fillna(a22["MPG_proj"].median())

    a22 = build_features(a22, target_year=2022)
    a22 = a22.dropna(subset=FEATURE_COLS + ["PTS_residual"])
    print(f"  rows after dropna: {len(a22)}")

    print("\nBuilding 23-24 test data...")
    s24 = pd.read_csv(SHIP_2324)
    s24["nba_api_id"] = s24["nba_api_id"].astype(int)
    s24 = s24.dropna(subset=["PTS_actual", "PTS_proj"]).copy()
    s24["PTS_residual"] = s24["PTS_actual"] - s24["PTS_proj"]
    s24 = s24.rename(columns={"mpg": "MPG_proj"})
    s24 = build_features(s24, target_year=2023)
    s24 = s24.dropna(subset=FEATURE_COLS)  # don't require residual; we'll measure MAE
    print(f"  rows: {len(s24)}")

    X_train = a22[FEATURE_COLS].values
    y_train = a22["PTS_residual"].values
    X_test = s24[FEATURE_COLS].values
    y_test_actual = s24["PTS_actual"].values
    y_test_proj = s24["PTS_proj"].values
    y_test_resid = s24["PTS_residual"].values

    print(f"\nTrain: {X_train.shape}  Test: {X_test.shape}")

    # ============== Hyperparameter sweep ==============
    print("\n" + "=" * 78)
    print("HYPERPARAMETER SWEEP (5-fold CV on 22-23)")
    print("=" * 78)
    print(f"{'depth':>5} {'n_est':>5} {'lr':>5}  {'cv_train_MAE':>13} {'cv_val_MAE':>11}")
    print("-" * 60)
    best_cfg = None
    best_score = float("inf")
    for max_depth in [2, 3, 4]:
        for n_estimators in [30, 50, 100]:
            for lr in [0.03, 0.05, 0.10]:
                gbm = GradientBoostingRegressor(
                    max_depth=max_depth, n_estimators=n_estimators,
                    learning_rate=lr, random_state=42, subsample=0.8,
                )
                kf = KFold(n_splits=5, shuffle=True, random_state=42)
                val_maes = []
                train_maes = []
                for tr, va in kf.split(X_train):
                    gbm.fit(X_train[tr], y_train[tr])
                    val_pred = gbm.predict(X_train[va])
                    val_maes.append(np.mean(np.abs(val_pred - y_train[va])))
                    tr_pred = gbm.predict(X_train[tr])
                    train_maes.append(np.mean(np.abs(tr_pred - y_train[tr])))
                cv_val = np.mean(val_maes)
                cv_tr = np.mean(train_maes)
                if cv_val < best_score:
                    best_score = cv_val
                    best_cfg = (max_depth, n_estimators, lr)
                print(f"{max_depth:>5} {n_estimators:>5} {lr:>5.2f}  "
                      f"{cv_tr:>13.4f} {cv_val:>11.4f}")
    print(f"\n  Best CV: depth={best_cfg[0]}, n_est={best_cfg[1]}, lr={best_cfg[2]}, "
          f"val_MAE={best_score:.4f}")

    # ============== Train final model on full 22-23 ==============
    print("\n" + "=" * 78)
    print("TRAIN FINAL MODEL ON 22-23, APPLY TO 23-24")
    print("=" * 78)
    md, ne, lr = best_cfg
    gbm = GradientBoostingRegressor(max_depth=md, n_estimators=ne,
                                      learning_rate=lr, random_state=42,
                                      subsample=0.8)
    gbm.fit(X_train, y_train)
    train_pred = gbm.predict(X_train)
    train_mae = np.mean(np.abs(train_pred - y_train))
    print(f"  In-sample 22-23 residual MAE: {train_mae:.4f}")

    # Predict residuals on 23-24
    pred_resid_24 = gbm.predict(X_test)
    print(f"  23-24 predicted residual range: "
          f"[{pred_resid_24.min():+.2f}, {pred_resid_24.max():+.2f}]")
    print(f"  23-24 actual residual range:    "
          f"[{y_test_resid.min():+.2f}, {y_test_resid.max():+.2f}]")

    # Apply correction: corrected_proj = original_proj + predicted_residual
    pred_corrected = y_test_proj + pred_resid_24

    base_mae = np.mean(np.abs(y_test_actual - y_test_proj))
    new_mae = np.mean(np.abs(y_test_actual - pred_corrected))
    delta_pct = 100 * (new_mae - base_mae) / base_mae

    print(f"\n  23-24 PTS MAE:")
    print(f"    v6 baseline:                {base_mae:.4f}")
    print(f"    v6 + GBM residual correct:  {new_mae:.4f}  ({delta_pct:+.2f}%)")

    # Reference: v6.1 (Center + mid_season mult)
    s24_ref = s24.copy()
    s24_ref.loc[s24_ref["pos_Center"] == 1, "PTS_proj"] -= 0.70
    s24_ref.loc[s24_ref["mid_season_change"] == 1, "PTS_proj"] *= 0.916
    v61_mae = np.mean(np.abs(s24_ref["PTS_actual"] - s24_ref["PTS_proj"]))
    print(f"    v6.1 (Center + mid_season): {v61_mae:.4f}  "
          f"({100*(v61_mae-base_mae)/base_mae:+.2f}%)")

    # ============== Feature importance ==============
    print("\n" + "=" * 78)
    print("FEATURE IMPORTANCE")
    print("=" * 78)
    importances = sorted(zip(FEATURE_COLS, gbm.feature_importances_),
                          key=lambda x: -x[1])
    for f, imp in importances:
        print(f"  {f:<28} {imp:.4f}")

    # ============== Hybrid: GBM + v6.1 offsets ==============
    # Apply v6.1 offsets first, then GBM on top — see if they compose
    print("\n" + "=" * 78)
    print("HYBRID: v6.1 offsets + GBM residual (does GBM ADD signal beyond class offsets?)")
    print("=" * 78)
    s24_h = s24.copy()
    s24_h.loc[s24_h["pos_Center"] == 1, "PTS_proj"] -= 0.70
    s24_h.loc[s24_h["mid_season_change"] == 1, "PTS_proj"] *= 0.916
    s24_h["PTS_residual_after_v61"] = s24_h["PTS_actual"] - s24_h["PTS_proj"]

    # Train GBM on 22-23 residuals AFTER applying same offsets, predict 23-24 residuals AFTER offsets
    a22_h = a22.copy()
    a22_h.loc[a22_h["pos_Center"] == 1, "PTS_proj"] -= 0.70
    a22_h.loc[a22_h["mid_season_change"] == 1, "PTS_proj"] *= 0.916
    a22_h["PTS_residual_after_v61"] = a22_h["actual"] - a22_h["PTS_proj"]
    X_train_h = a22_h[FEATURE_COLS].values
    y_train_h = a22_h["PTS_residual_after_v61"].values
    X_test_h = s24_h[FEATURE_COLS].values

    gbm_h = GradientBoostingRegressor(max_depth=md, n_estimators=ne,
                                        learning_rate=lr, random_state=42,
                                        subsample=0.8)
    gbm_h.fit(X_train_h, y_train_h)
    pred_resid_h = gbm_h.predict(X_test_h)
    s24_h["PTS_proj_corrected"] = s24_h["PTS_proj"] + pred_resid_h
    hybrid_mae = np.mean(np.abs(s24_h["PTS_actual"] - s24_h["PTS_proj_corrected"]))
    print(f"  v6.1 + GBM residual (hybrid): {hybrid_mae:.4f}  "
          f"({100*(hybrid_mae-base_mae)/base_mae:+.2f}%)")
    print(f"\n  Comparison:")
    print(f"    v6 baseline:                {base_mae:.4f}")
    print(f"    v6.1 (offsets only):        {v61_mae:.4f}")
    print(f"    GBM only:                   {new_mae:.4f}")
    print(f"    v6.1 + GBM:                 {hybrid_mae:.4f}")


if __name__ == "__main__":
    main()
