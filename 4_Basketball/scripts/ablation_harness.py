"""Per-feature ablation harness.

Takes a baseline v6 ship CSV and a per-player MPG adjustment dict, propagates
the adjustment proportionally through volume stats, and reports per-stat MAE
delta vs the baseline.

This is a pandas-only "feature shock" harness — it does NOT refit the model.
It assumes the v6 cascade structure where volume stats scale roughly with MPG
within a season.

Usage (programmatic):
    from scripts.ablation_harness import run_ablation, load_baseline
    base = load_baseline()
    adj = {1629029: +1.0, 203999: -2.0}  # nba_api_id -> mpg delta
    result = run_ablation(base, adj, label="absorption_top10")
    print(result["mae_delta"])

CLI:
    python scripts/ablation_harness.py baseline
    python scripts/ablation_harness.py absorption --top-n 10
    python scripts/ablation_harness.py rookie_prior
    python scripts/ablation_harness.py chronic_variance
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
SHIP_CSV = REPO / "audit_runs" / "unified_ship_v6" / "per_player_projections_2023-24.csv"

VOLUME_STATS = ["PTS", "REB", "AST", "STL", "BLK", "TOV",
                "FGA", "FGM", "FG3A", "FG3M", "FTA", "FTM"]
RATE_STATS = ["FG_PCT", "FG3_PCT", "FT_PCT"]
ALL_STATS = VOLUME_STATS + RATE_STATS


def load_baseline() -> pd.DataFrame:
    df = pd.read_csv(SHIP_CSV)
    if "MPG_proj" not in df.columns:
        for cand in ["mpg_proj", "MPG", "mpg"]:
            if cand in df.columns:
                df["MPG_proj"] = df[cand]
                break
    return df


def per_stat_mae(df: pd.DataFrame, stats=ALL_STATS) -> dict:
    out = {}
    for s in stats:
        proj = f"{s}_proj"
        actual = f"{s}_actual"
        if proj not in df.columns or actual not in df.columns:
            continue
        sub = df[[proj, actual]].dropna()
        if len(sub) == 0:
            continue
        out[s] = float(np.mean(np.abs(sub[proj] - sub[actual])))
    return out


def apply_mpg_shock(base: pd.DataFrame,
                    mpg_adjust: dict,
                    scale_volume: bool = True) -> pd.DataFrame:
    """Apply a per-player MPG adjustment, scale volume stats proportionally."""
    df = base.copy()
    if "MPG_proj" not in df.columns:
        # Synthesize: estimate MPG from PTS / pts_per_min if available; else error
        raise RuntimeError("Baseline missing MPG_proj column; cannot scale.")

    df["MPG_proj_orig"] = df["MPG_proj"]
    df["mpg_delta"] = df["nba_api_id"].map(mpg_adjust).fillna(0.0)
    df["MPG_proj_new"] = df["MPG_proj"] + df["mpg_delta"]
    # Don't allow negative or absurd
    df["MPG_proj_new"] = df["MPG_proj_new"].clip(lower=0, upper=44)

    if scale_volume:
        # ratio = new_mpg / old_mpg, with safe-divide
        df["scale"] = df["MPG_proj_new"] / df["MPG_proj_orig"].replace(0, np.nan)
        df["scale"] = df["scale"].fillna(1.0).clip(lower=0.0, upper=2.5)
        for stat in VOLUME_STATS:
            col = f"{stat}_proj"
            if col in df.columns:
                df[col] = df[col] * df["scale"]
        # Rate stats: unchanged (FG%, FG3%, FT% are MPG-invariant)

    return df


def run_ablation(base: pd.DataFrame, mpg_adjust: dict, label: str = "ablation"):
    """Run a single ablation and return results dict."""
    base_mae = per_stat_mae(base)
    shocked = apply_mpg_shock(base, mpg_adjust, scale_volume=True)
    new_mae = per_stat_mae(shocked)

    rows = []
    for s in sorted(base_mae.keys()):
        b = base_mae[s]
        n = new_mae.get(s, np.nan)
        rows.append({
            "stat": s,
            "baseline_mae": b,
            "ablated_mae": n,
            "delta": n - b,
            "pct_change": 100 * (n - b) / b if b > 0 else np.nan,
        })
    res = pd.DataFrame(rows)
    return {
        "label": label,
        "n_players_adjusted": int(sum(1 for v in mpg_adjust.values() if v != 0)),
        "mae_table": res,
    }


def print_result(result):
    print(f"\n=== Ablation: {result['label']} ===")
    print(f"Players adjusted: {result['n_players_adjusted']}")
    print()
    df = result["mae_table"].copy()
    df["baseline_mae"] = df["baseline_mae"].apply(lambda x: f"{x:.4f}")
    df["ablated_mae"] = df["ablated_mae"].apply(lambda x: f"{x:.4f}")
    df["delta"] = df["delta"].apply(lambda x: f"{x:+.4f}")
    df["pct_change"] = df["pct_change"].apply(lambda x: f"{x:+.2f}%")
    print(df.to_string(index=False))


# ---- Feature loaders: build candidate adjustments from new parquets

def adjust_from_absorption(top_n: int = 10) -> dict:
    """Use top star-out absorbers to predict MPG bumps for the season.

    Strategy: for each (team, season) star-injury absorption row, the teammate
    received +lift_mpg in absent games. Weight that by P(star_out) using the
    chronic injury features for the star. Feed that as a season-level MPG
    bump for the teammate.
    """
    abs_team = pd.read_parquet(PQ / "star_injury_absorption_team_season.parquet")
    chronic = pd.read_parquet(PQ / "chronic_injury_features_path1.parquet")
    chronic_ty = chronic[chronic["target_year"] == 2024].copy()  # for 23-24 season
    p_out = dict(zip(chronic_ty["nba_api_id"].astype(int),
                     chronic_ty["pct_games_missed_3y"]))

    # Filter to stable evidence
    cands = abs_team[(abs_team["total_absent_games"] >= 20) &
                     (abs_team["weighted_lift_mpg"] >= 2.0) &
                     (abs_team["season"] == "2023-24")].copy()
    cands["p_star_out"] = cands["star_id"].astype(int).map(p_out).fillna(0.10)
    cands["expected_mpg_bump"] = cands["weighted_lift_mpg"] * cands["p_star_out"]

    # Sum bumps across multiple absorptions per teammate
    by_teammate = cands.groupby("teammate_id")["expected_mpg_bump"].sum().reset_index()
    by_teammate = by_teammate.sort_values("expected_mpg_bump", ascending=False).head(top_n)
    print(f"Top {top_n} expected mpg bumps from absorption:")
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    name_map = dict(zip(meta["nba_api_id"].astype(int), meta["name"]))
    for _, r in by_teammate.iterrows():
        nm = name_map.get(int(r["teammate_id"]), str(r["teammate_id"]))
        print(f"  {nm:<24} +{r['expected_mpg_bump']:.2f} mpg")
    return dict(zip(by_teammate["teammate_id"].astype(int),
                    by_teammate["expected_mpg_bump"]))


def adjust_zero() -> dict:
    """Zero-shock baseline — sanity check that MAE doesn't change."""
    return {}


def adjust_random_noise(scale: float = 1.0, seed: int = 42) -> dict:
    """Add gaussian noise to MPG — sanity check for harness sensitivity.
    Result should be: MAE should DEGRADE proportional to scale."""
    rng = np.random.default_rng(seed)
    base = load_baseline()
    return {int(pid): float(rng.normal(0, scale))
            for pid in base["nba_api_id"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["baseline", "zero", "noise",
                                          "absorption"])
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--noise-scale", type=float, default=1.0)
    args = parser.parse_args()

    base = load_baseline()
    print(f"Loaded baseline: {len(base)} players")

    if args.mode == "baseline":
        mae = per_stat_mae(base)
        print("\n=== Baseline MAE ===")
        for s, m in sorted(mae.items()):
            print(f"  {s:<8} {m:.4f}")
    elif args.mode == "zero":
        result = run_ablation(base, adjust_zero(), label="zero_shock")
        print_result(result)
    elif args.mode == "noise":
        result = run_ablation(base, adjust_random_noise(scale=args.noise_scale),
                              label=f"gaussian_noise_sigma_{args.noise_scale}")
        print_result(result)
    elif args.mode == "absorption":
        adj = adjust_from_absorption(top_n=args.top_n)
        result = run_ablation(base, adj, label=f"absorption_top{args.top_n}")
        print_result(result)


if __name__ == "__main__":
    main()
