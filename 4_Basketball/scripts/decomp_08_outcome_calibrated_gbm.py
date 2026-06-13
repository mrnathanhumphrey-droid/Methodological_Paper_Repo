"""Idea 2 — Outcome-calibrated GBM with league as a categorical feature.

Per target stat (Y1 per-36 + mpg + gp + draft_slot), fit LightGBM with:
  - Pre-NBA per-40 features (ppg/rpg/apg/spg/bpg/tov/fg3m, fg/3p/ft %)
  - pre_nba_league_label (categorical)
  - position_bucket (categorical)
  - pre_nba_age (numeric)

The league coefficient FALLS OUT as a learned model feature. Per-stat compression
is naturally captured (BBL pts compress differently than BBL ast).

Holdout: train on 2014-22 draft years, validate on 2023-24 (51 + 50 prospects).
Surface per-league marginal effect via SHAP / partial dependence.

Outputs:
    data/parquet/rookies_outcome_gbm_predictions.parquet  (per-prospect predicted Y1 + draft_slot)
    data/parquet/rookies_outcome_gbm_league_effects.parquet  (per-league × per-stat effect)
    models/rookies_outcome_gbm_<target>.txt  (LightGBM model artifacts)
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb

PQ = Path("D:/NBA Projections/data/parquet")
MODELS = Path("D:/NBA Projections/data/models")
MODELS.mkdir(parents=True, exist_ok=True)
PRED_OUT = PQ / "rookies_outcome_gbm_predictions.parquet"
LEAGUE_OUT = PQ / "rookies_outcome_gbm_league_effects.parquet"

NUMERIC_FEATS = ["ppg_pre", "rpg_pre", "apg_pre", "spg_pre", "bpg_pre", "tov_pre", "fg3m_pre",
                                "fg_pct_pre", "fg3_pct_pre", "ft_pct_pre",
                                "pre_nba_age"]
CAT_FEATS = ["pre_nba_league_label", "position_bucket"]

TARGETS = [
    ("nba_y1_pts_per36", 25),
    ("nba_y1_reb_per36", 25),
    ("nba_y1_ast_per36", 25),
    ("nba_y1_stl_per36", 25),
    ("nba_y1_blk_per36", 25),
    ("nba_y1_fg3m_per36", 25),
    ("nba_y1_tov_per36", 25),
    ("nba_y1_mpg", 25),
    ("nba_y1_gp", 0),
    ("draft_pick", 0),
]

HOLDOUT_YEARS = {2023, 2024}


def main():
    df = pd.read_parquet(PQ / "rookies_outcome_training.parquet")
    print(f"  training set: {len(df):,}")

    for c in CAT_FEATS:
        df[c] = df[c].fillna("unknown").astype(str).astype("category")

    pred_rows = []
    league_effect_rows = []
    summary_rows = []

    for target, min_gp in TARGETS:
        if target not in df.columns:
            continue
        sub = df.dropna(subset=[target]).copy()
        if min_gp > 0:
            sub = sub[sub.get("nba_y1_gp", 0) >= min_gp]
        if len(sub) < 100:
            continue

        train = sub[~sub["draft_year"].isin(HOLDOUT_YEARS)].copy()
        test = sub[sub["draft_year"].isin(HOLDOUT_YEARS)].copy()
        if len(train) < 50:
            continue

        X_tr = train[NUMERIC_FEATS + CAT_FEATS]
        y_tr = train[target].astype(float)
        X_te = test[NUMERIC_FEATS + CAT_FEATS]
        y_te = test[target].astype(float)
        X_all = sub[NUMERIC_FEATS + CAT_FEATS]

        dtr = lgb.Dataset(X_tr, y_tr, categorical_feature=CAT_FEATS, free_raw_data=False)
        dval = lgb.Dataset(X_te, y_te, categorical_feature=CAT_FEATS, free_raw_data=False, reference=dtr)
        params = {
            "objective": "regression",
            "metric": "rmse",
            "learning_rate": 0.05,
            "num_leaves": 16,
            "min_data_in_leaf": 5,
            "feature_fraction": 0.85,
            "bagging_fraction": 0.85,
            "bagging_freq": 5,
            "verbose": -1,
        }
        model = lgb.train(params, dtr, num_boost_round=400,
                                            valid_sets=[dtr, dval], valid_names=["train", "test"],
                                            callbacks=[lgb.early_stopping(40), lgb.log_evaluation(0)])

        model_path = MODELS / f"outcome_gbm_{target}.txt"
        model.save_model(str(model_path))

        rmse_te = float(np.sqrt(((model.predict(X_te) - y_te) ** 2).mean()))
        rmse_baseline = float(np.sqrt(((y_te - y_tr.mean()) ** 2).mean()))
        lift = (rmse_baseline - rmse_te) / rmse_baseline * 100.0
        summary_rows.append({"target": target, "n_train": len(train), "n_test": len(test),
                                            "rmse_te": rmse_te, "rmse_baseline": rmse_baseline,
                                            "lift_pct": lift})
        print(f"  {target:<22} train_n={len(train):>3} test_n={len(test):>3}  "
                    f"RMSE_te={rmse_te:.3f}  baseline={rmse_baseline:.3f}  lift={lift:+.1f}%")

        pred_all = model.predict(X_all)
        sub_out = sub[["nba_api_id", "player_name_raw", "draft_year", "pre_nba_league_label",
                                  "pre_nba_conference", "position_bucket"]].copy()
        sub_out[f"actual_{target}"] = y_tr.tolist() + y_te.tolist() if False else sub[target].values
        sub_out[f"pred_{target}"] = pred_all
        pred_rows.append(sub_out)

        for lg in df["pre_nba_league_label"].cat.categories:
            mask = sub["pre_nba_league_label"] == lg
            if mask.sum() < 5:
                continue
            actual = sub.loc[mask, target].mean()
            pred = float(pred_all[mask.values].mean())
            league_effect_rows.append({
                "target": target, "league": lg, "n": int(mask.sum()),
                "mean_actual": float(actual), "mean_pred": pred,
            })

    if pred_rows:
        merged = pred_rows[0][["nba_api_id", "player_name_raw", "draft_year",
                                                        "pre_nba_league_label", "pre_nba_conference", "position_bucket"]].copy()
        for tdf in pred_rows:
            tcols = [c for c in tdf.columns if c.startswith(("actual_", "pred_"))]
            merged = merged.merge(tdf[["nba_api_id"] + tcols].drop_duplicates("nba_api_id"),
                                                    on="nba_api_id", how="outer")
        merged.to_parquet(PRED_OUT, index=False)
        print(f"\nwrote: {PRED_OUT}")

    if league_effect_rows:
        eff = pd.DataFrame(league_effect_rows)
        eff.to_parquet(LEAGUE_OUT, index=False)
        print(f"wrote: {LEAGUE_OUT}")

        print("\n=== LEAGUE EFFECT TABLE — mean actual Y1 outcome by league ===")
        print("(reveals which leagues compress production vs NBA Y1 most)")
        for target in ["nba_y1_pts_per36", "nba_y1_reb_per36", "nba_y1_ast_per36",
                                  "nba_y1_blk_per36", "nba_y1_mpg", "draft_pick"]:
            sub = eff[eff["target"] == target].sort_values("mean_actual", ascending=(target == "draft_pick"))
            if len(sub):
                print(f"\n  {target}:")
                print(sub[["league", "n", "mean_actual", "mean_pred"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
