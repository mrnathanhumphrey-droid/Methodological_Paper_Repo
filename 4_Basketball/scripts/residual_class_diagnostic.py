"""Collatz-style noise-floor diagnostic: do residuals show real per-class structure?

Protocol:
  1. Compute residuals R(p) = actual - projected for each player in 195-cohort.
  2. For each class C (team, position, age, etc.):
       SD_observed = SD(mean(R) per class)
       SE_sampling = sqrt(Var(R) / mean(n_per_class))
       tau2_corrected = max(0, SD_observed^2 - SE_sampling^2)
  3. If tau2_corrected ~ 0 -> noise floor, no signal.
     If tau2_corrected > 0 -> real per-class structure, look for deterministic predictor.

Also report: per-class mean residuals + correlation with candidate features
(offseason_traded share, net_position_churn, age, etc.).
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
from ablation_harness import load_baseline

REPO = Path(".")
PQ = REPO / "data" / "parquet"


def parse_min(x):
    if pd.isna(x): return np.nan
    s = str(x)
    if ":" in s:
        try:
            a, b = s.split(":")
            return float(a) + float(b) / 60.0
        except Exception:
            return np.nan
    try:
        return float(s)
    except Exception:
        return np.nan


def compute_residuals(base, stat="MPG"):
    """Returns DataFrame with [nba_api_id, name, residual, projected, actual]
    for the chosen stat (MPG default since that's the upstream lever)."""
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["minutes"] = pd.to_numeric(box["minutes"], errors="coerce")
    box = box.dropna(subset=["minutes"])
    box["nba_api_id"] = box["nba_api_id"].astype(int)

    s23 = box[box["season"] == "2023-24"]
    actual_mpg = s23.groupby("nba_api_id").agg(
        gp=("game_id", "nunique"),
        total_min=("minutes", "sum"),
    ).reset_index()
    actual_mpg["mpg_actual"] = actual_mpg["total_min"] / actual_mpg["gp"]
    actual_map = dict(zip(actual_mpg["nba_api_id"], actual_mpg["mpg_actual"]))

    df = base.copy()
    df["mpg_actual"] = df["nba_api_id"].astype(int).map(actual_map)
    df["mpg_residual"] = df["mpg_actual"] - df["MPG_proj"]
    return df.dropna(subset=["mpg_residual"])


def noise_floor_test(df, class_col, label):
    """Run noise-floor test on a single class column."""
    grouped = df.groupby(class_col)["mpg_residual"].agg(
        mean_resid="mean",
        n="count",
        var="var",
    ).reset_index()
    grouped = grouped[grouped["n"] >= 2]
    if len(grouped) < 2:
        print(f"\n  [{label}] only {len(grouped)} valid classes — skip")
        return None

    sd_observed = grouped["mean_resid"].std(ddof=1)
    overall_var = df["mpg_residual"].var(ddof=1)
    n_per_class_mean = grouped["n"].mean()
    se_sampling = np.sqrt(overall_var / n_per_class_mean)
    tau2_corrected = max(0.0, sd_observed**2 - se_sampling**2)
    tau_corrected = np.sqrt(tau2_corrected)
    snr = sd_observed / se_sampling if se_sampling > 0 else np.nan

    print(f"\n  === [{label}] (n_classes={len(grouped)}, mean_n_per_class={n_per_class_mean:.1f}) ===")
    print(f"    SD(mean residual) observed:    {sd_observed:.4f}")
    print(f"    SE(sampling) theoretical:      {se_sampling:.4f}")
    print(f"    SNR (observed / sampling):     {snr:.3f}")
    print(f"    tau corrected:                 {tau_corrected:.4f}")
    print(f"    tau^2 corrected:               {tau2_corrected:.4f}")

    if snr < 1.05:
        print(f"    -> NOISE FLOOR: per-{label} structure not above sampling noise")
    elif snr < 1.5:
        print(f"    -> WEAK SIGNAL: marginal structure")
    elif snr < 3.0:
        print(f"    -> MODERATE SIGNAL: real structure")
    else:
        print(f"    -> STRONG SIGNAL: clear class structure")

    # Top/bottom 5 classes
    top = grouped.nlargest(5, "mean_resid")[[class_col, "mean_resid", "n"]]
    bot = grouped.nsmallest(5, "mean_resid")[[class_col, "mean_resid", "n"]]
    print(f"    Top-5 over-projected ({class_col}, mean residual, n):")
    for _, r in top.iterrows():
        print(f"      {r[class_col]!s:<20}  resid={r['mean_resid']:+.2f}  n={r['n']}")
    print(f"    Top-5 under-projected:")
    for _, r in bot.iterrows():
        print(f"      {r[class_col]!s:<20}  resid={r['mean_resid']:+.2f}  n={r['n']}")
    return grouped


def main():
    print("Computing residuals: actual_mpg_23-24 - v6_projected_mpg")
    base = load_baseline()
    df = compute_residuals(base, stat="MPG")
    print(f"  cohort with both projection and actual: {len(df)}")
    print(f"  overall mean residual: {df['mpg_residual'].mean():+.4f}")
    print(f"  overall SD residual:   {df['mpg_residual'].std(ddof=1):.4f}")

    # Attach candidate class features
    print("\nAttaching class features...")
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    df = df.merge(meta[["nba_api_id", "position", "draft_year", "birth_date"]],
                  on="nba_api_id", how="left")
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
    df["age_2023"] = (pd.Timestamp("2023-10-24") - df["birth_date"]).dt.days / 365.25
    df["age_bucket"] = pd.cut(df["age_2023"],
                               bins=[0, 24, 27, 30, 33, 50],
                               labels=["<=24", "25-26", "27-29", "30-32", "33+"])
    df["years_pro"] = 2023 - df["draft_year"]

    # Team for 23-24
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    s23 = box[box["season"] == "2023-24"]
    team_23 = s23.groupby("nba_api_id")["team_abbr"].agg(
        lambda x: x.value_counts().idxmax()).reset_index()
    team_23.columns = ["nba_api_id", "team_2324"]
    df = df.merge(team_23, on="nba_api_id", how="left")

    # Offseason traded
    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    traded = set(tx[(tx["transaction_type"] == "trade") &
                    (tx["event_date"] >= "2023-04-15") &
                    (tx["event_date"] <= "2023-10-24") &
                    (tx["nba_api_id"].notna())]["nba_api_id"].astype(int))
    df["offseason_traded"] = df["nba_api_id"].isin(traded)

    # Net position churn (precomputed)
    if (PQ / "offseason_roster_churn_2023_24.parquet").exists():
        churn = pd.read_parquet(PQ / "offseason_roster_churn_2023_24.parquet")
        # Map team+position from meta to net_churn
        churn_map = {(r["team"], r["position"]): r["net_churn_mpg"]
                     for _, r in churn.iterrows()}
        df["net_position_churn"] = [
            churn_map.get((row["team_2324"], row["position"]), 0.0)
            for _, row in df.iterrows()
        ]

    # ============== Run noise-floor tests ==============
    print("\n" + "=" * 78)
    print("NOISE-FLOOR DIAGNOSTIC (Collatz protocol)")
    print("=" * 78)
    noise_floor_test(df, "position", "position")
    noise_floor_test(df, "team_2324", "team_2324")
    noise_floor_test(df, "age_bucket", "age_bucket")
    noise_floor_test(df, "offseason_traded", "offseason_traded")

    # ============== Correlation tests ==============
    print("\n" + "=" * 78)
    print("DETERMINISTIC FEATURE CORRELATIONS WITH RESIDUAL")
    print("=" * 78)
    feats = ["age_2023", "years_pro", "net_position_churn"]
    for f in feats:
        if f not in df.columns:
            continue
        sub = df[[f, "mpg_residual"]].dropna()
        if len(sub) < 5:
            continue
        r = sub[f].corr(sub["mpg_residual"])
        print(f"  Pearson r ({f} vs residual, n={len(sub)}):  {r:+.4f}")

    # Trade flag binary
    sub = df.dropna(subset=["offseason_traded", "mpg_residual"])
    traded_mean = sub[sub["offseason_traded"]]["mpg_residual"].mean()
    not_traded_mean = sub[~sub["offseason_traded"]]["mpg_residual"].mean()
    diff = traded_mean - not_traded_mean
    print(f"\n  Mean residual:  traded={traded_mean:+.3f}  not_traded={not_traded_mean:+.3f}  "
          f"diff={diff:+.3f}")

    # Save
    df.to_parquet(PQ / "residual_class_diagnostic_2023_24.parquet", index=False)
    print(f"\nSaved -> {PQ / 'residual_class_diagnostic_2023_24.parquet'}")


if __name__ == "__main__":
    main()
