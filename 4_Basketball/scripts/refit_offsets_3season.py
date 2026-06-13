"""Refit additive/multiplicative magnitudes on the 3-season cohort.

For each currently-shipping offset that SURVIVED the 3-season cross-season
validation, recompute alpha (additive) or c (multiplicative) from the combined
22-23 + 23-24 + 24-25 cohort. This gives honest 3-season-anchored magnitudes
for the spec update.

Surviving offsets (per cross_season_full_validation 3-season output):
  - PTS x position=Center        (currently -0.70 additive; 3-season mean -0.566)
  - PTS x mid_season_change=True (currently -8.4% mult; 3-season mean -1.135)
  - AST x years_pro_bucket=13+   (currently -9.1% mult; 3-season mean -0.265)

Dropped (didn't survive 3-season validation, will be removed from spec):
  - REB x mid_season_change=True
  - TOV x years_pro_bucket=13+
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")

from pathlib import Path
import re
import numpy as np
import pandas as pd
from scipy import stats

from _class_features import attach_class_features

REPO = Path(".")
PQ = REPO / "data" / "parquet"
SHIP_2324 = REPO / "audit_runs" / "unified_ship_v6" / "per_player_projections_2023-24.csv"


def find_audit(stat: str, test_season: str) -> Path:
    pattern = re.compile(
        rf"skill_backtest_{stat}_phase4_v4_quadratic_tq_g_.*__{test_season}$"
    )
    candidates = []
    for d in (REPO / "audit_runs").glob("*"):
        if not d.is_dir():
            continue
        for sub in d.glob(f"skill_backtest_{stat}_phase4_v4_quadratic_tq_g_*"):
            if pattern.search(sub.name):
                csv = sub / "per_player_projections.csv"
                if csv.exists():
                    candidates.append((csv, csv.stat().st_size))
    if not candidates:
        raise FileNotFoundError(f"No audit for {stat} {test_season}")
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


# attach_class_features now imported from scripts/_class_features.py


def regress(x, y, label):
    n = len(x)
    if n < 5:
        print(f"\n--- {label} (n={n}) — TOO FEW ---")
        return None
    alpha_only = y.mean()
    sse_alpha = ((y - alpha_only) ** 2).sum()
    X = np.column_stack([np.ones(n), x])
    a, b = np.linalg.lstsq(X, y, rcond=None)[0]
    yhat = a + b * x
    sse_full = ((y - yhat) ** 2).sum()
    sigma2 = sse_full / (n - 2) if n > 2 else np.nan
    var_beta = sigma2 * np.linalg.inv(X.T @ X)
    se_a = np.sqrt(var_beta[0, 0])
    se_b = np.sqrt(var_beta[1, 1])
    t_a = a / se_a if se_a > 0 else np.nan
    t_b = b / se_b if se_b > 0 else np.nan
    p_a = 2 * (1 - stats.t.cdf(abs(t_a), n - 2))
    p_b = 2 * (1 - stats.t.cdf(abs(t_b), n - 2))
    c = (x * y).sum() / (x * x).sum() if (x * x).sum() > 0 else np.nan
    sse_mult = ((y - c * x) ** 2).sum()

    print(f"\n--- {label} (n={n}) ---")
    print(f"  proj range: [{x.min():.2f}, {x.max():.2f}], mean {x.mean():.2f}")
    print(f"  residual mean: {y.mean():+.3f}, SD: {y.std(ddof=1):.3f}")
    print(f"  ADDITIVE-only:  alpha={alpha_only:+.3f}  SSE={sse_alpha:.2f}")
    print(f"  MULT-only:      c={c*100:+.2f}%        SSE={sse_mult:.2f}")
    print(f"  LINEAR:         alpha={a:+.3f} (t={t_a:+.2f}, p={p_a:.3f})")
    print(f"                  beta ={b:+.4f} (t={t_b:+.2f}, p={p_b:.3f})")
    if sse_alpha < sse_mult:
        verdict = f"ADDITIVE  (alpha = {alpha_only:+.3f})"
    else:
        verdict = f"MULT  (c = {c*100:+.2f}%, mult={1+c:.4f})"
    print(f"  -> {verdict}")
    return {"alpha": alpha_only, "c_mult": c, "n": n,
             "sse_add": sse_alpha, "sse_mult": sse_mult,
             "t_a": t_a, "t_b": t_b}


def load_3season(stat):
    """Load 3-season cohort with class features attached."""
    rows = []
    # 22-23 audit
    p22 = find_audit(stat, "2022-23")
    df = pd.read_csv(p22)
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    df = df.dropna(subset=["actual", "proj_mean"]).copy()
    df["residual"] = df["actual"] - df["proj_mean"]
    df = df.rename(columns={"proj_mean": "proj"})
    df = attach_class_features(df, target_year=2022)
    df["season"] = "2022-23"
    rows.append(df[["nba_api_id", "proj", "residual", "position",
                     "mid_season_change", "years_pro_bucket", "season"]])

    # 23-24 from ship CSV
    s24 = pd.read_csv(SHIP_2324)
    s24["nba_api_id"] = s24["nba_api_id"].astype(int)
    actual_col = f"{stat}_actual"; proj_col = f"{stat}_proj"
    s24 = s24.dropna(subset=[actual_col, proj_col]).copy()
    s24["residual"] = s24[actual_col] - s24[proj_col]
    s24 = s24.rename(columns={proj_col: "proj"})
    s24 = attach_class_features(s24, target_year=2023)
    s24["season"] = "2023-24"
    rows.append(s24[["nba_api_id", "proj", "residual", "position",
                      "mid_season_change", "years_pro_bucket", "season"]])

    # 24-25 audit
    p24 = find_audit(stat, "2024-25")
    df = pd.read_csv(p24)
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    df = df.dropna(subset=["actual", "proj_mean"]).copy()
    df["residual"] = df["actual"] - df["proj_mean"]
    df = df.rename(columns={"proj_mean": "proj"})
    df = attach_class_features(df, target_year=2024)
    df["season"] = "2024-25"
    rows.append(df[["nba_api_id", "proj", "residual", "position",
                     "mid_season_change", "years_pro_bucket", "season"]])

    return pd.concat(rows, ignore_index=True)


def main():
    print("=" * 80)
    print("3-SEASON REFIT: surviving offsets, recomputed magnitudes")
    print("=" * 80)

    # PTS x Center (additive)
    pts = load_3season("PTS")
    sub = pts[pts["position"] == "Center"]
    print(f"\nPTS x Center, 3-season cohort:")
    for s in sorted(sub["season"].unique()):
        ssub = sub[sub["season"] == s]
        print(f"  {s}: n={len(ssub)}, residual mean = {ssub['residual'].mean():+.3f}")
    regress(sub["proj"].values, sub["residual"].values,
            label="PTS x Center, 3-season combined")

    # PTS x mid_season_change=True (mult)
    sub = pts[pts["mid_season_change"] == True]
    print(f"\nPTS x mid_season_change=True, 3-season cohort:")
    for s in sorted(sub["season"].unique()):
        ssub = sub[sub["season"] == s]
        print(f"  {s}: n={len(ssub)}, residual mean = {ssub['residual'].mean():+.3f}")
    regress(sub["proj"].values, sub["residual"].values,
            label="PTS x mid_season_change=True, 3-season combined")

    # AST x years_pro 13+ (mult)
    ast = load_3season("AST")
    sub = ast[ast["years_pro_bucket"] == "13+"]
    print(f"\nAST x years_pro_bucket=13+, 3-season cohort:")
    for s in sorted(sub["season"].unique()):
        ssub = sub[sub["season"] == s]
        print(f"  {s}: n={len(ssub)}, residual mean = {ssub['residual'].mean():+.3f}")
    regress(sub["proj"].values, sub["residual"].values,
            label="AST x years_pro_bucket=13+, 3-season combined")


if __name__ == "__main__":
    main()
