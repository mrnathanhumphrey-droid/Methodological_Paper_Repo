"""Test whether class offsets should be ADDITIVE (flat -X PPG) or
MULTIPLICATIVE (flat -X%) by regressing within-class residuals on projected PTS.

For each surviving class:
  Fit: residual_PTS = α + β × proj_PTS
  - If α significant, β ~ 0 → additive (flat PPG offset)
  - If α ~ 0, β significant → multiplicative (% of projection)
  - Both significant → mixed model

Tests on 22-23 + 23-24 combined (apples-to-apples) for stability.
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


def attach_class(df, target_year):
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    df = df.merge(meta[["nba_api_id", "position"]], on="nba_api_id", how="left")
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    season_label = f"{target_year}-{str(target_year+1)[2:]}"
    s = box[box["season"] == season_label]
    team = s.groupby("nba_api_id")["team_abbr"].agg(
        lambda x: x.value_counts().idxmax()).reset_index()
    team.columns = ["nba_api_id", "team_for_season"]
    df = df.merge(team, on="nba_api_id", how="left")
    cf = pd.read_parquet(PQ / "coaching_change_flags.parquet")
    cf_s = cf[cf["season"] == season_label][["team_abbr", "mid_season_change"]]
    df = df.merge(cf_s, left_on="team_for_season", right_on="team_abbr",
                   how="left", suffixes=("", "_cf"))
    df["mid_season_change"] = df["mid_season_change"].fillna(False).astype(bool)
    return df


def regress_residual(df, proj_col, resid_col, label=""):
    """OLS fit: residual = α + β × proj. Report fits and t-stats."""
    sub = df.dropna(subset=[proj_col, resid_col]).copy()
    if len(sub) < 5:
        return None
    n = len(sub)
    x = sub[proj_col].values
    y = sub[resid_col].values

    # Constant-only model (additive)
    alpha_only = y.mean()
    sse_alpha = ((y - alpha_only) ** 2).sum()

    # Linear model: y = a + b*x
    X = np.column_stack([np.ones(n), x])
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    a, b = beta
    yhat = X @ beta
    sse_full = ((y - yhat) ** 2).sum()
    sst = ((y - y.mean()) ** 2).sum()
    r2 = 1 - sse_full / sst if sst > 0 else np.nan

    # t-stats
    sigma2 = sse_full / (n - 2) if n > 2 else np.nan
    var_beta = sigma2 * np.linalg.inv(X.T @ X)
    se_a = np.sqrt(var_beta[0, 0])
    se_b = np.sqrt(var_beta[1, 1])
    t_a = a / se_a if se_a > 0 else np.nan
    t_b = b / se_b if se_b > 0 else np.nan
    p_a = 2 * (1 - stats.t.cdf(abs(t_a), n - 2))
    p_b = 2 * (1 - stats.t.cdf(abs(t_b), n - 2))

    # Multiplicative-only fit: y = c * x  (no intercept)
    c = (x * y).sum() / (x * x).sum() if (x * x).sum() > 0 else np.nan
    yhat_mult = c * x
    sse_mult = ((y - yhat_mult) ** 2).sum()
    r2_mult = 1 - sse_mult / sst if sst > 0 else np.nan

    print(f"\n--- {label} (n={n}) ---")
    print(f"  proj range: [{x.min():.2f}, {x.max():.2f}], mean {x.mean():.2f}")
    print(f"  residual mean: {y.mean():+.3f}, SD: {y.std(ddof=1):.3f}")
    print()
    print(f"  ADDITIVE-only (y = α):")
    print(f"    α = {alpha_only:+.3f}")
    print(f"    SSE = {sse_alpha:.2f}")
    print()
    print(f"  MULTIPLICATIVE-only (y = c × proj_PTS):")
    print(f"    c = {c*100:+.3f}%  (i.e. residual is c% of projection)")
    print(f"    SSE = {sse_mult:.2f}")
    print(f"    R² (vs mean baseline) = {r2_mult:.3f}")
    print()
    print(f"  LINEAR (y = α + β × proj):")
    print(f"    α (intercept) = {a:+.3f}  t={t_a:+.2f}  p={p_a:.3f}")
    print(f"    β (slope)     = {b:+.4f}  t={t_b:+.2f}  p={p_b:.3f}  (residual per +1 PPG of proj)")
    print(f"    R² = {r2:.3f}")
    print(f"    SSE = {sse_full:.2f}")

    # Interpretation
    print()
    if abs(t_a) > 2 and abs(t_b) < 1:
        print(f"  -> ADDITIVE wins (intercept significant, slope not)")
    elif abs(t_a) < 1 and abs(t_b) > 2:
        print(f"  -> MULTIPLICATIVE wins (slope significant, intercept not)")
    elif abs(t_a) > 2 and abs(t_b) > 2:
        print(f"  -> MIXED (both significant)")
    else:
        print(f"  -> NEITHER strongly preferred (both noisy)")

    return {"a": a, "b": b, "t_a": t_a, "t_b": t_b, "p_a": p_a, "p_b": p_b,
            "r2": r2, "c_mult": c, "r2_mult": r2_mult, "n": n}


def main():
    # 22-23 cohort
    a22 = pd.read_csv(AUDIT_2223_PTS)
    a22["nba_api_id"] = a22["nba_api_id"].astype(int)
    a22 = a22.dropna(subset=["actual", "proj_mean"]).copy()
    a22["PTS_residual"] = a22["actual"] - a22["proj_mean"]
    a22 = a22.rename(columns={"proj_mean": "PTS_proj"})
    a22 = attach_class(a22, target_year=2022)

    # 23-24 cohort
    s24 = pd.read_csv(SHIP_2324)
    s24["nba_api_id"] = s24["nba_api_id"].astype(int)
    s24 = s24.dropna(subset=["PTS_actual"]).copy()
    s24["PTS_residual"] = s24["PTS_actual"] - s24["PTS_proj"]
    s24 = attach_class(s24, target_year=2023)

    # Combined apples-to-apples
    a22_keep = a22[["nba_api_id", "PTS_proj", "PTS_residual", "position", "mid_season_change"]].copy()
    a22_keep["season"] = "2022-23"
    s24_keep = s24[["nba_api_id", "PTS_proj", "PTS_residual", "position", "mid_season_change"]].copy()
    s24_keep["season"] = "2023-24"
    combined = pd.concat([a22_keep, s24_keep], ignore_index=True)

    print("=" * 80)
    print("ADDITIVE vs MULTIPLICATIVE: residual ~ projected PTS")
    print("=" * 80)

    # Center class
    centers_combined = combined[combined["position"] == "Center"]
    regress_residual(centers_combined, "PTS_proj", "PTS_residual",
                     label="ALL CENTERS, 22-23 + 23-24 combined")
    centers_22 = a22[a22["position"] == "Center"]
    regress_residual(centers_22, "PTS_proj", "PTS_residual",
                     label="Centers 22-23 only")
    centers_24 = s24[s24["position"] == "Center"]
    regress_residual(centers_24, "PTS_proj", "PTS_residual",
                     label="Centers 23-24 only")

    # Mid_season class
    mid_combined = combined[combined["mid_season_change"]]
    regress_residual(mid_combined, "PTS_proj", "PTS_residual",
                     label="ALL MID-SEASON-HC PLAYERS, 22-23 + 23-24 combined")
    mid_22 = a22[a22["mid_season_change"]]
    regress_residual(mid_22, "PTS_proj", "PTS_residual",
                     label="mid_season 22-23 only")
    mid_24 = s24[s24["mid_season_change"]]
    regress_residual(mid_24, "PTS_proj", "PTS_residual",
                     label="mid_season 23-24 only")

    # Comparison: additive vs multiplicative on the cohort overall
    print("\n" + "=" * 80)
    print("FULL COHORT (not class-restricted)")
    print("=" * 80)
    regress_residual(combined, "PTS_proj", "PTS_residual",
                     label="All players combined (22-23 + 23-24)")


if __name__ == "__main__":
    main()
