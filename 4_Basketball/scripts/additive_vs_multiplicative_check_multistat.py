"""Generalized additive-vs-multiplicative test across (stat, class) candidates.

For each candidate, regresses within-class residuals on projected stat and
reports whether the offset should be additive (intercept dominates) or
multiplicative (slope dominates).

Tests on 22-23 audit + 23-24 ship combined (apples-to-apples).

Candidates targeted (from cross-season validation, top magnitude per stat):
  - REB x mid_season_change=True (-0.59)
  - AST x years_pro 13+ (-0.36)
  - TOV x years_pro 13+ (-0.20)
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import re
import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(".")
PQ = REPO / "data" / "parquet"
SHIP_2324 = REPO / "audit_runs" / "unified_ship_v6" / "per_player_projections_2023-24.csv"


def find_22_23_audit(stat: str) -> Path:
    """Find the v4-lite tq_g audit for stat at 22-23 test season."""
    pattern = re.compile(
        rf"skill_backtest_{stat}_phase4_v4_quadratic_tq_g_.*__2022-23$"
    )
    for d in (REPO / "audit_runs").glob("*"):
        if not d.is_dir():
            continue
        for sub in d.glob(f"skill_backtest_{stat}_phase4_v4_quadratic_tq_g_*"):
            if pattern.search(sub.name):
                csv = sub / "per_player_projections.csv"
                if csv.exists():
                    return csv
    raise FileNotFoundError(f"No 22-23 audit found for {stat}")


def attach_class_features(df, target_year):
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


def regress_residual(df, proj_col, resid_col, label=""):
    sub = df.dropna(subset=[proj_col, resid_col]).copy()
    if len(sub) < 5:
        print(f"\n--- {label} (n={len(sub)}) — TOO FEW ---")
        return None
    n = len(sub)
    x = sub[proj_col].values
    y = sub[resid_col].values

    alpha_only = y.mean()
    sse_alpha = ((y - alpha_only) ** 2).sum()

    X = np.column_stack([np.ones(n), x])
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    a, b = beta
    yhat = X @ beta
    sse_full = ((y - yhat) ** 2).sum()
    sst = ((y - y.mean()) ** 2).sum()
    r2 = 1 - sse_full / sst if sst > 0 else np.nan

    sigma2 = sse_full / (n - 2) if n > 2 else np.nan
    var_beta = sigma2 * np.linalg.inv(X.T @ X)
    se_a = np.sqrt(var_beta[0, 0])
    se_b = np.sqrt(var_beta[1, 1])
    t_a = a / se_a if se_a > 0 else np.nan
    t_b = b / se_b if se_b > 0 else np.nan
    p_a = 2 * (1 - stats.t.cdf(abs(t_a), n - 2))
    p_b = 2 * (1 - stats.t.cdf(abs(t_b), n - 2))

    c = (x * y).sum() / (x * x).sum() if (x * x).sum() > 0 else np.nan
    yhat_mult = c * x
    sse_mult = ((y - yhat_mult) ** 2).sum()

    print(f"\n--- {label} (n={n}) ---")
    print(f"  proj range: [{x.min():.2f}, {x.max():.2f}], mean {x.mean():.2f}")
    print(f"  residual mean: {y.mean():+.3f}, SD: {y.std(ddof=1):.3f}")
    print(f"  ADDITIVE-only:  alpha={alpha_only:+.3f}, SSE={sse_alpha:.2f}")
    print(f"  MULT-only:      c={c*100:+.2f}%, SSE={sse_mult:.2f}")
    print(f"  LINEAR:         alpha={a:+.3f} (t={t_a:+.2f}, p={p_a:.3f})")
    print(f"                  beta ={b:+.4f} (t={t_b:+.2f}, p={p_b:.3f})")
    print(f"                  SSE={sse_full:.2f}, R^2={r2:.3f}")

    if abs(t_a) > 2 and abs(t_b) < 1:
        verdict = "ADDITIVE wins"
    elif abs(t_a) < 1 and abs(t_b) > 2:
        verdict = "MULTIPLICATIVE wins"
    elif abs(t_a) > 2 and abs(t_b) > 2:
        verdict = "MIXED (both significant)"
    elif sse_alpha < sse_mult:
        verdict = "additive (lower SSE, neither significant)"
    else:
        verdict = "multiplicative (lower SSE, neither significant)"
    print(f"  -> {verdict}")
    return {"a": a, "b": b, "t_a": t_a, "t_b": t_b,
             "alpha_only": alpha_only, "c_mult": c,
             "sse_add": sse_alpha, "sse_mult": sse_mult,
             "n": n, "verdict": verdict}


def load_22_23(stat):
    p = find_22_23_audit(stat)
    df = pd.read_csv(p)
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    df = df.dropna(subset=["actual", "proj_mean"]).copy()
    df[f"{stat}_residual"] = df["actual"] - df["proj_mean"]
    df = df.rename(columns={"proj_mean": f"{stat}_proj", "actual": f"{stat}_actual"})
    df = attach_class_features(df, target_year=2022)
    return df


def load_23_24(stat):
    df = pd.read_csv(SHIP_2324)
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    actual_col = f"{stat}_actual"
    proj_col = f"{stat}_proj"
    df = df.dropna(subset=[actual_col, proj_col]).copy()
    df[f"{stat}_residual"] = df[actual_col] - df[proj_col]
    df = attach_class_features(df, target_year=2023)
    return df


def test_candidate(stat, class_col, class_value):
    """Run the 3 regressions (combined, 22-23, 23-24) for one candidate."""
    print("\n" + "=" * 80)
    print(f"  CANDIDATE: {stat} x {class_col} = {class_value}")
    print("=" * 80)

    a22 = load_22_23(stat)
    a23 = load_23_24(stat)

    keep = ["nba_api_id", f"{stat}_proj", f"{stat}_residual", class_col]
    a22k = a22[keep].copy(); a22k["season"] = "2022-23"
    a23k = a23[keep].copy(); a23k["season"] = "2023-24"
    combined = pd.concat([a22k, a23k], ignore_index=True)

    if class_value in ("True", "False"):
        cv_actual = class_value == "True"
        c_combined = combined[combined[class_col] == cv_actual]
        c_22 = a22[a22[class_col] == cv_actual]
        c_23 = a23[a23[class_col] == cv_actual]
    else:
        c_combined = combined[combined[class_col].astype(str) == class_value]
        c_22 = a22[a22[class_col].astype(str) == class_value]
        c_23 = a23[a23[class_col].astype(str) == class_value]

    res = {}
    res["combined"] = regress_residual(
        c_combined, f"{stat}_proj", f"{stat}_residual",
        label=f"{stat} x {class_col}={class_value}, COMBINED")
    res["22-23"] = regress_residual(
        c_22, f"{stat}_proj", f"{stat}_residual",
        label=f"{stat} x {class_col}={class_value}, 22-23 only")
    res["23-24"] = regress_residual(
        c_23, f"{stat}_proj", f"{stat}_residual",
        label=f"{stat} x {class_col}={class_value}, 23-24 only")
    return res


def main():
    candidates = [
        ("REB", "mid_season_change", "True"),
        ("AST", "years_pro_bucket", "13+"),
        ("AST", "age_bucket", "33+"),
        ("TOV", "years_pro_bucket", "13+"),
        ("TOV", "age_bucket", "33+"),
    ]

    print("=" * 80)
    print("ADDITIVE vs MULTIPLICATIVE — top cross-season-validated candidates")
    print("=" * 80)

    summary = []
    for stat, cls, val in candidates:
        try:
            res = test_candidate(stat, cls, val)
            summary.append({
                "stat": stat, "class": cls, "value": val,
                "verdict": res["combined"]["verdict"] if res["combined"] else "n/a",
                "additive_alpha": res["combined"]["alpha_only"] if res["combined"] else np.nan,
                "mult_pct": res["combined"]["c_mult"] * 100 if res["combined"] else np.nan,
                "sse_add": res["combined"]["sse_add"] if res["combined"] else np.nan,
                "sse_mult": res["combined"]["sse_mult"] if res["combined"] else np.nan,
                "n_combined": res["combined"]["n"] if res["combined"] else 0,
            })
        except FileNotFoundError as e:
            print(f"\nSkip {stat}/{cls}={val}: {e}")

    print("\n\n" + "=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)
    s = pd.DataFrame(summary)
    if len(s) > 0:
        print(s.to_string(index=False))


if __name__ == "__main__":
    main()
