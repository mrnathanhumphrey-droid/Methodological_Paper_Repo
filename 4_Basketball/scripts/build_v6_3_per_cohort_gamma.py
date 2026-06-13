"""v6.3 per-cohort Galton de-shrinkage build.

Architecture:
  v6.2 used a single global γ per stat (over-corrects vets that were already
  calibrated under v6.1). v6.3 estimates γ separately per (cohort × stat),
  fit on out-of-sample residuals from prior-season backtests (23-24, 24-25)
  to avoid in-sample over-fitting.

Fit:
  For each (cohort, stat): linear regression `actual ~ alpha + gamma * proj`
  on pooled out-of-sample residuals from 23-24 + 24-25 Stan backtests.

Apply:
  v6.3_proj_i = alpha_{cohort(i), stat} + gamma_{cohort(i), stat} * v6.1_proj_i
  applied to the v6.1 LOCKED 25-26 ship.

Score:
  MAE per stat × cohort on 25-26 actuals — compare v6.1, v6.2 (global gamma),
  v6.3 (per-cohort gamma).

Stats covered: PTS, REB, AST (Test-1 stats; the only ones with multi-season
Stan residuals from today's chain).

Outputs at audit_runs/v6_3_per_cohort_gamma/:
  - gamma_coefficients.csv  (per cohort × stat: alpha, gamma, n, R^2)
  - v6_3_ship_25_26.csv     (per-player projections under v6.3)
  - mae_comparison.md       (v6.1 vs v6.2 vs v6.3 head-to-head on 25-26)
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from pathlib import Path
import json

import numpy as np
import pandas as pd
from scipy import stats as sstats

REPO = Path(".")
PQ = REPO / "data" / "parquet"
OUT_DIR = REPO / "audit_runs" / "v6_3_per_cohort_gamma"
OUT_DIR.mkdir(parents=True, exist_ok=True)

V6_1_SHIP = REPO / "audit_runs" / "unified_ship_v6_1_2025_26" / "per_player_projections_2025-26.csv"
ROOKIE_SUP = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "rookie_metadata_supplement.parquet"

# 23-24 + 24-25 per-player projection CSVs (out-of-sample residuals)
PROJ_PATHS = {
    ("PTS", "2024-25"): "audit_runs/20260505T154737Z/skill_backtest_PTS_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/per_player_projections.csv",
    ("REB", "2024-25"): "audit_runs/20260505T171359Z/skill_backtest_REB_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/per_player_projections.csv",
    ("AST", "2024-25"): "audit_runs/20260505T183718Z/skill_backtest_AST_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/per_player_projections.csv",
    ("PTS", "2023-24"): "audit_runs/20260505T211540Z/skill_backtest_PTS_phase4_v4_quadratic_tq_g_2017-18-2018-19-2019-20-2020-21-2021-22-2022-23__2023-24/per_player_projections.csv",
    ("REB", "2023-24"): "audit_runs/20260505T225045Z/skill_backtest_REB_phase4_v4_quadratic_tq_g_2017-18-2018-19-2019-20-2020-21-2021-22-2022-23__2023-24/per_player_projections.csv",
    ("AST", "2023-24"): "audit_runs/20260506T002014Z/skill_backtest_AST_phase4_v4_quadratic_tq_g_2017-18-2018-19-2019-20-2020-21-2021-22-2022-23__2023-24/per_player_projections.csv",
}

STATS = ["PTS", "REB", "AST"]


def load_metadata():
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    cols = ["nba_api_id", "name", "position", "draft_year", "debut_year"]
    if ROOKIE_SUP.exists():
        sup = pd.read_parquet(ROOKIE_SUP)
        meta = pd.concat([meta[cols], sup[cols]], ignore_index=True)
    meta["nba_api_id"] = meta["nba_api_id"].astype(int)
    return meta


def cohort_at_season(meta_df, season_label):
    """Return cohort tag (vet/soph/rookie) per nba_api_id at a given test season.
    soph = years_pro 1-3, rookie = 0, vet = 4+.
    """
    season_year = int(season_label[:4])
    yp = meta_df["debut_year"].where(meta_df["debut_year"].notna(),
                                       meta_df["draft_year"] + 1)
    yp = season_year - yp
    def label(y):
        if pd.isna(y): return "vet"
        if y <= 0: return "rookie"
        if y <= 3: return "soph"
        return "vet"
    return yp.apply(label)


def build_oos_residuals(meta):
    """Pool out-of-sample residuals across 23-24 + 24-25 per stat."""
    frames = []
    for (stat, season), path in PROJ_PATHS.items():
        df = pd.read_csv(path)
        df["nba_api_id"] = df["nba_api_id"].astype(int)
        df["season"] = season
        df["stat"] = stat
        df["resid"] = df["actual"] - df["proj_mean"]
        df = df.merge(meta[["nba_api_id", "draft_year", "debut_year", "position"]],
                        on="nba_api_id", how="left")
        df["cohort"] = cohort_at_season(df, season)
        frames.append(df[["nba_api_id", "season", "stat", "proj_mean",
                            "actual", "resid", "cohort"]])
    return pd.concat(frames, ignore_index=True)


def fit_per_cohort_gamma(oos):
    """Per (cohort × stat) fit `actual ~ alpha + gamma * proj` via OLS.
    Returns DataFrame of coefficients, residuals SD, R^2, n."""
    rows = []
    for cohort_v in ("vet", "soph", "rookie"):
        for stat in STATS:
            sub = oos[(oos["cohort"] == cohort_v) & (oos["stat"] == stat)]
            sub = sub.dropna(subset=["proj_mean", "actual"])
            n = len(sub)
            if n < 5:
                rows.append({"cohort": cohort_v, "stat": stat, "n": n,
                              "alpha": np.nan, "gamma": np.nan, "r2": np.nan,
                              "resid_sd": np.nan, "fit_status": "insufficient_n"})
                continue
            slope, intercept, r, _, _ = sstats.linregress(
                sub["proj_mean"].values, sub["actual"].values)
            yhat = intercept + slope * sub["proj_mean"].values
            resid = sub["actual"].values - yhat
            rows.append({
                "cohort": cohort_v, "stat": stat, "n": int(n),
                "alpha": float(intercept),
                "gamma": float(slope),
                "r2": float(r * r),
                "resid_sd": float(resid.std(ddof=2)),
                "fit_status": "ok",
            })
    return pd.DataFrame(rows)


def apply_v6_3_to_25_26_ship(gamma_df, ship_path, meta):
    """Apply per-cohort gamma to v6.1 LOCKED ship to produce v6.3 ship."""
    ship = pd.read_csv(ship_path)
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)

    # Map synthetic rookie IDs -> real IDs
    rookie_map = {}
    if ROOKIE_SUP.exists():
        sup = pd.read_parquet(ROOKIE_SUP)
        meta_base = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
        real_name_id = dict(zip(meta_base["name"].str.lower().fillna(""),
                                  meta_base["nba_api_id"].astype(int)))
        for _, r in sup.iterrows():
            nm = (r["name"] or "").strip().lower()
            if nm in real_name_id:
                rookie_map[int(r["nba_api_id"])] = real_name_id[nm]
    ship["real_id"] = ship["nba_api_id"].map(
        lambda x: rookie_map.get(int(x), int(x))).astype(int)

    # Cohort at 25-26 season
    ship = ship.merge(meta[["nba_api_id", "draft_year", "debut_year"]],
                        left_on="real_id", right_on="nba_api_id",
                        how="left", suffixes=("", "_m"))
    ship["cohort"] = cohort_at_season(ship, "2025-26")

    # Apply gamma per (cohort × stat)
    gamma_lookup = {(r["cohort"], r["stat"]): (r["alpha"], r["gamma"])
                     for _, r in gamma_df.iterrows()
                     if r["fit_status"] == "ok"}
    for stat in STATS:
        v6_1_col = f"{stat}_per_game"
        v6_3_col = f"{stat}_v6_3"
        out = []
        for _, r in ship.iterrows():
            key = (r["cohort"], stat)
            if key in gamma_lookup and pd.notna(r[v6_1_col]):
                a, g = gamma_lookup[key]
                out.append(a + g * r[v6_1_col])
            else:
                out.append(r[v6_1_col])  # fall back to v6.1 if no gamma
        ship[v6_3_col] = out
    return ship


def score_v6_1_vs_v6_3_on_25_26(ship_v6_3, meta):
    """Score v6.1 vs v6.3 on 25-26 actuals. Returns per-cohort MAE table."""
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx_2526 = bx[(bx["season"] == "2025-26") &
                   (bx["season_type"] == "Regular Season")].copy()
    bx_2526["minutes"] = pd.to_numeric(bx_2526["minutes"], errors="coerce")
    bx_2526 = bx_2526[bx_2526["minutes"] > 0]
    bx_2526["nba_api_id"] = bx_2526["nba_api_id"].astype(int)
    actuals = bx_2526.groupby("nba_api_id").agg(
        gp_actual=("game_id", "nunique"),
        PTS_actual=("PTS", "mean"), REB_actual=("REB", "mean"),
        AST_actual=("AST", "mean"),
    ).reset_index()

    # Drop stale ship-side actuals (only filled for original-vet cohort)
    stale = [c for c in ship_v6_3.columns if c.endswith("_actual")]
    ship_v6_3 = ship_v6_3.drop(columns=stale)

    df = ship_v6_3.merge(actuals, left_on="real_id",
                            right_on="nba_api_id", how="left",
                            suffixes=("", "_act"))
    df = df[df["gp_actual"].fillna(0) >= 10].copy()

    rows = []
    for cohort_v in ("vet", "soph", "rookie", "ALL"):
        for stat in STATS:
            sub = df if cohort_v == "ALL" else df[df["cohort"] == cohort_v]
            v6_1_col = f"{stat}_per_game"
            v6_3_col = f"{stat}_v6_3"
            actual_col = f"{stat}_actual"
            sub2 = sub.dropna(subset=[v6_1_col, v6_3_col, actual_col])
            n = len(sub2)
            if n < 5:
                continue
            v61_mae = (sub2[v6_1_col] - sub2[actual_col]).abs().mean()
            v63_mae = (sub2[v6_3_col] - sub2[actual_col]).abs().mean()
            v61_bias = (sub2[v6_1_col] - sub2[actual_col]).mean()
            v63_bias = (sub2[v6_3_col] - sub2[actual_col]).mean()
            d = v63_mae - v61_mae
            d_pct = d / v61_mae * 100 if v61_mae else 0
            rows.append({
                "cohort": cohort_v, "stat": stat, "n": n,
                "v6_1_MAE": v61_mae, "v6_1_bias": v61_bias,
                "v6_3_MAE": v63_mae, "v6_3_bias": v63_bias,
                "delta_MAE": d, "delta_pct": d_pct,
            })
    return pd.DataFrame(rows)


def main():
    print("[load] metadata + box scores")
    meta = load_metadata()

    print("[build] out-of-sample residuals (23-24 + 24-25 backtests)")
    oos = build_oos_residuals(meta)
    print(f"  total residual rows: {len(oos)}")
    print(f"  by season x stat:")
    print(oos.groupby(["season", "stat"]).size().to_string())
    print(f"  by cohort x stat (pooled across seasons):")
    print(oos.groupby(["cohort", "stat"]).size().to_string())

    print("\n[fit] per-cohort gamma")
    gamma_df = fit_per_cohort_gamma(oos)
    print(gamma_df.to_string(index=False))
    gamma_df.to_csv(OUT_DIR / "gamma_coefficients.csv", index=False)
    print(f"\n[save] {OUT_DIR / 'gamma_coefficients.csv'}")

    print("\n[apply] gamma to v6.1 LOCKED 25-26 ship")
    ship = apply_v6_3_to_25_26_ship(gamma_df, V6_1_SHIP, meta)
    out_cols = [c for c in ship.columns if c in
                  ("nba_api_id", "real_id", "name", "cohort", "mpg")
                  or c.endswith("_per_game") or c.endswith("_v6_3")
                  or c.endswith("_per_game_sd")]
    ship[out_cols].to_csv(OUT_DIR / "v6_3_ship_25_26.csv", index=False)
    print(f"[save] {OUT_DIR / 'v6_3_ship_25_26.csv'}")

    print("\n[score] v6.1 vs v6.3 on 25-26 actuals (>=10 GP)")
    score = score_v6_1_vs_v6_3_on_25_26(ship, meta)
    print()
    print(score.to_string(index=False))
    score.to_csv(OUT_DIR / "mae_comparison.csv", index=False)
    print(f"\n[save] {OUT_DIR / 'mae_comparison.csv'}")

    print("\n=== HEADLINES ===")
    print()
    print("v6.3 per-cohort gamma fitted on 23-24 + 24-25 OOS residuals.")
    print("Applied to v6.1 LOCKED 25-26 projections.")
    print("Scored on 25-26 actuals (n=451, >=10 GP filter).")
    print()
    overall = score[score["cohort"] == "ALL"]
    for _, r in overall.iterrows():
        print(f"  {r['stat']}: v6.1 MAE {r['v6_1_MAE']:.3f} -> "
              f"v6.3 MAE {r['v6_3_MAE']:.3f}  ({r['delta_pct']:+.1f}%)")

    print("\nDONE.")


if __name__ == "__main__":
    main()
