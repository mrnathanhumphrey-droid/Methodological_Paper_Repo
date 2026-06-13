"""Test a single 3-season candidate offset for shipability.

Runs the full methodology gate:
  1. Per-season magnitudes (stability check)
  2. Additive-vs-multiplicative regression on combined 3-season cohort
  3. Cohort-level MAE impact estimate
  4. Rule-4 conflict check vs currently-shipping offsets

Usage:
  python scripts/test_candidate_3season.py PTS age_bucket 25-26
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")

from pathlib import Path
import re
import argparse
import numpy as np
import pandas as pd
from scipy import stats

from _class_features import attach_class_features

REPO = Path(".")
PQ = REPO / "data" / "parquet"
SHIP_2324 = REPO / "audit_runs" / "unified_ship_v6" / "per_player_projections_2023-24.csv"

CURRENTLY_SHIPPING = {
    "PTS": [("position", "Center"), ("mid_season_change", True)],
    "AST": [("years_pro_bucket", "13+")],
    "REB": [],
    "TOV": [],
    "BLK": [],
    "STL": [],
}


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


def load_3season(stat):
    rows = []
    for ts, year in [("2022-23", 2022), ("2024-25", 2024)]:
        p = find_audit(stat, ts)
        df = pd.read_csv(p)
        df["nba_api_id"] = df["nba_api_id"].astype(int)
        df = df.dropna(subset=["actual", "proj_mean"]).copy()
        df["residual"] = df["actual"] - df["proj_mean"]
        df = df.rename(columns={"proj_mean": "proj"})
        df = attach_class_features(df, target_year=year)
        df["season"] = ts
        rows.append(df)

    s24 = pd.read_csv(SHIP_2324)
    s24["nba_api_id"] = s24["nba_api_id"].astype(int)
    actual_col = f"{stat}_actual"; proj_col = f"{stat}_proj"
    s24 = s24.dropna(subset=[actual_col, proj_col]).copy()
    s24["residual"] = s24[actual_col] - s24[proj_col]
    s24 = s24.rename(columns={proj_col: "proj"})
    s24 = attach_class_features(s24, target_year=2023)
    s24["season"] = "2023-24"
    rows.append(s24)

    common_cols = ["nba_api_id", "proj", "residual", "position", "age_bucket",
                    "years_pro_bucket", "draft_pick_tier", "offseason_traded",
                    "mid_season_change", "new_coach_this_season", "season"]
    return pd.concat([r[common_cols] for r in rows], ignore_index=True)


def regress(x, y, label):
    n = len(x)
    if n < 5:
        return None
    alpha_only = y.mean()
    sse_alpha = ((y - alpha_only) ** 2).sum()
    X = np.column_stack([np.ones(n), x])
    a, b = np.linalg.lstsq(X, y, rcond=None)[0]
    yhat = a + b * x
    sse_full = ((y - yhat) ** 2).sum()
    sigma2 = sse_full / (n - 2) if n > 2 else np.nan
    var_beta = sigma2 * np.linalg.inv(X.T @ X)
    se_a = np.sqrt(var_beta[0, 0]); se_b = np.sqrt(var_beta[1, 1])
    t_a = a / se_a if se_a > 0 else np.nan
    t_b = b / se_b if se_b > 0 else np.nan
    p_a = 2 * (1 - stats.t.cdf(abs(t_a), n - 2))
    p_b = 2 * (1 - stats.t.cdf(abs(t_b), n - 2))
    c = (x * y).sum() / (x * x).sum() if (x * x).sum() > 0 else np.nan
    sse_mult = ((y - c * x) ** 2).sum()
    return {
        "n": n, "alpha": alpha_only, "c": c,
        "sse_add": sse_alpha, "sse_mult": sse_mult, "sse_lin": sse_full,
        "lin_a": a, "lin_b": b, "t_a": t_a, "t_b": t_b, "p_a": p_a, "p_b": p_b,
        "y_mean": y.mean(), "y_sd": y.std(ddof=1),
        "x_mean": x.mean(), "x_min": x.min(), "x_max": x.max(),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("stat")
    p.add_argument("class_name")
    p.add_argument("class_value")
    args = p.parse_args()

    print("=" * 80)
    print(f"3-SEASON CANDIDATE TEST: {args.stat} x {args.class_name} = {args.class_value}")
    print("=" * 80)

    df = load_3season(args.stat)

    if args.class_value in ("True", "False"):
        cv = args.class_value == "True"
        sub = df[df[args.class_name] == cv]
    else:
        sub = df[df[args.class_name].astype(str) == args.class_value]

    if len(sub) == 0:
        print(f"No matching rows.")
        return

    print(f"\n--- Per-season cohort ---")
    for s in sorted(sub["season"].unique()):
        ss = sub[sub["season"] == s]
        print(f"  {s}: n={len(ss)}, residual mean = {ss['residual'].mean():+.3f}, "
              f"SD = {ss['residual'].std(ddof=1):.3f}, proj mean = {ss['proj'].mean():.2f}")

    # 3-season regression
    res = regress(sub["proj"].values, sub["residual"].values,
                   label=f"{args.stat} x {args.class_name}={args.class_value} 3-season combined")
    if res is None:
        print("Too few observations.")
        return
    print(f"\n--- 3-season combined regression (n={res['n']}) ---")
    print(f"  proj range: [{res['x_min']:.2f}, {res['x_max']:.2f}], mean {res['x_mean']:.2f}")
    print(f"  residual mean: {res['y_mean']:+.3f}, SD: {res['y_sd']:.3f}")
    print(f"  ADDITIVE-only: alpha = {res['alpha']:+.4f}, SSE = {res['sse_add']:.2f}")
    print(f"  MULT-only:     c = {res['c']*100:+.3f}%, SSE = {res['sse_mult']:.2f}")
    print(f"  LINEAR:        alpha = {res['lin_a']:+.3f} (t={res['t_a']:+.2f}, p={res['p_a']:.4f})")
    print(f"                 beta  = {res['lin_b']:+.4f} (t={res['t_b']:+.2f}, p={res['p_b']:.4f})")
    if abs(res['t_a']) > 2 and abs(res['t_b']) < 1:
        verdict = "ADDITIVE strongly preferred"
    elif abs(res['t_a']) < 1 and abs(res['t_b']) > 2:
        verdict = "MULTIPLICATIVE strongly preferred"
    elif abs(res['t_a']) > 2 and abs(res['t_b']) > 2:
        verdict = "MIXED (both significant)"
    elif res['sse_add'] < res['sse_mult']:
        verdict = "additive (lower SSE; t-stats noisy)"
    else:
        verdict = "multiplicative (lower SSE; t-stats noisy)"
    print(f"  Verdict: {verdict}")

    # Per-season form check
    print(f"\n--- Per-season form regression ---")
    print(f"  {'season':<10} {'n':>4} {'alpha':>8} {'c%':>8} {'lin_alpha':>10} {'lin_beta':>10} {'t_a':>6} {'t_b':>6}")
    for s in sorted(sub["season"].unique()):
        ss = sub[sub["season"] == s]
        r = regress(ss["proj"].values, ss["residual"].values, "")
        if r is None:
            continue
        print(f"  {s:<10} {r['n']:>4} {r['alpha']:>+8.3f} {r['c']*100:>+7.2f}% "
              f"{r['lin_a']:>+10.3f} {r['lin_b']:>+10.4f} {r['t_a']:>+6.2f} {r['t_b']:>+6.2f}")

    # Cohort-level MAE impact estimate (on 23-24 ship cohort)
    s23 = pd.read_csv(SHIP_2324)
    s23["nba_api_id"] = s23["nba_api_id"].astype(int)
    s23 = attach_class_features(s23, target_year=2023)
    actual_col = f"{args.stat}_actual"; proj_col = f"{args.stat}_proj"
    s23 = s23.dropna(subset=[actual_col, proj_col]).copy()

    if args.class_value in ("True", "False"):
        cv = args.class_value == "True"
        cohort_mask = s23[args.class_name] == cv
    else:
        cohort_mask = s23[args.class_name].astype(str) == args.class_value
    n_cohort = cohort_mask.sum()
    print(f"\n--- 23-24 ship cohort (n={n_cohort} affected by class) ---")
    if n_cohort == 0:
        print("  No 23-24 players in this class — can't estimate ship MAE.")
        return

    # Try both forms: additive and multiplicative
    base_mae = (s23[actual_col] - s23[proj_col]).abs().mean()
    n_full = len(s23)
    print(f"  Baseline {args.stat} MAE (full cohort): {base_mae:.4f}")

    # Additive
    s_add = s23.copy()
    s_add.loc[cohort_mask, proj_col] = s_add.loc[cohort_mask, proj_col] + res['alpha']
    add_mae = (s_add[actual_col] - s_add[proj_col]).abs().mean()
    print(f"  Apply ADDITIVE alpha={res['alpha']:+.3f}: MAE = {add_mae:.4f} ({100*(add_mae-base_mae)/base_mae:+.2f}%)")

    # Multiplicative
    s_mult = s23.copy()
    s_mult.loc[cohort_mask, proj_col] = s_mult.loc[cohort_mask, proj_col] * (1 + res['c'])
    mult_mae = (s_mult[actual_col] - s_mult[proj_col]).abs().mean()
    print(f"  Apply MULT c={res['c']*100:+.2f}% (mult={1+res['c']:.4f}): MAE = {mult_mae:.4f} "
          f"({100*(mult_mae-base_mae)/base_mae:+.2f}%)")

    # Rule-4 conflict check
    print(f"\n--- Rule-4 conflict check ---")
    shipping = CURRENTLY_SHIPPING.get(args.stat, [])
    if not shipping:
        print(f"  No offsets currently shipping for {args.stat}. Clear.")
    else:
        print(f"  Currently shipping for {args.stat}: {shipping}")
        # Check overlap with affected cohort
        for sh_class, sh_value in shipping:
            if sh_class == args.class_name:
                print(f"  ⚠ SAME CLASS as {sh_class} — would violate rule 4 (one class per stat).")
                continue
            if isinstance(sh_value, bool):
                sh_mask = s23[sh_class] == sh_value
            else:
                sh_mask = s23[sh_class].astype(str) == str(sh_value)
            overlap = (cohort_mask & sh_mask).sum()
            sh_n = sh_mask.sum()
            print(f"  vs {sh_class}={sh_value}: {overlap} players overlap "
                  f"(this candidate: n={n_cohort}, currently shipping: n={sh_n})")


if __name__ == "__main__":
    main()
