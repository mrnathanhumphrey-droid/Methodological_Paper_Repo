"""Option 1 refit: pooled 4-season LOO per-stat playoff multiplier.

Pools 22-23 + 23-24 + 24-25 (from backtest_playoff_residuals.csv) with 25-26
(reconstructed from R1 + extra_rounds traditional + v6.1 ship per_game).

Per-stat formula: mult = sum_all_seasons(actual) / sum_all_seasons(proj_A).

LOO across 4 seasons: hold out one season, refit on remaining 3. Reports
per-season LOO + pooled for stability inspection.

Outputs:
  runs/run_nba_playoffs_backtest_22_25/playoff_regime_multipliers.json (v3)
  runs/run_nba_playoffs_backtest_22_25/playoff_regime_multipliers_v2_2025_26_implied.json (archive of v2)
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("D:/NBA Projections")
RUN_DIR = REPO / "runs" / "run_nba_playoffs_backtest_22_25"
SHIP_PATH = REPO / "audit_runs" / "unified_ship_v6_1_2025_26" / "per_player_projections_2025-26.csv"
RESIDUALS = RUN_DIR / "backtest_playoff_residuals.csv"
R1 = REPO / "data" / "parquet" / "playoffs" / "round1"
EXTRA = REPO / "data" / "parquet" / "playoffs" / "extra_rounds"

PRIMARY = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FG3M"]
DERIVED = {
    "PRA": ["PTS", "REB", "AST"],
    "PR":  ["PTS", "REB"],
    "PA":  ["PTS", "AST"],
    "RA":  ["REB", "AST"],
}
ALL_STATS = PRIMARY + list(DERIVED.keys())

STAT_COL = {
    "PTS": "points", "REB": "reboundsTotal", "AST": "assists",
    "STL": "steals", "BLK": "blocks", "TOV": "turnovers",
    "FG3M": "threePointersMade",
}


def _parse_min(m):
    if pd.isna(m) or m == "" or m is None:
        return 0.0
    if isinstance(m, (int, float)):
        return float(m)
    try:
        parts = str(m).split(":")
        return float(parts[0]) + (float(parts[1]) / 60.0 if len(parts) > 1 else 0.0)
    except (ValueError, TypeError):
        return 0.0


def load_25_26_box():
    frames = []
    for src in [R1, EXTRA]:
        for fn in ["traditional_t0.parquet", "traditional_t1.parquet"]:
            p = src / fn
            if not p.exists():
                continue
            df = pd.read_parquet(p)
            if "personId" not in df.columns:
                continue
            df = df[df["season"] == "2025-26"].copy()
            df = df.dropna(subset=["personId"])
            df["personId"] = df["personId"].astype(int)
            df["min_played"] = df["minutes"].apply(_parse_min)
            df = df[df["min_played"] > 0]
            wanted = ["personId", "gameId", "min_played"] + list(STAT_COL.values())
            wanted = [c for c in wanted if c in df.columns]
            frames.append(df[wanted])
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates(["personId", "gameId"])
    return df


def build_25_26_actuals_and_projA():
    """Per-stat: total actual + total proj_A across 25-26 player-games.

    proj_A_for_game = v6.1_per_game * (game_minutes / rs_mpg)
    """
    box = load_25_26_box()
    if box.empty:
        return pd.DataFrame(columns=["stat", "sum_actual", "sum_proj", "n"])

    ship = pd.read_csv(SHIP_PATH)
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    ship_cols = ["nba_api_id", "mpg"] + [f"{s}_per_game" for s in PRIMARY]
    ship = ship[[c for c in ship_cols if c in ship.columns]]

    merged = box.merge(ship, left_on="personId", right_on="nba_api_id", how="inner")
    merged = merged[merged["mpg"] > 0]
    merged["mpg_ratio_game"] = merged["min_played"] / merged["mpg"]

    rows = []
    for stat in PRIMARY:
        actual_col = STAT_COL[stat]
        proj_col = f"{stat}_per_game"
        if actual_col not in merged.columns or proj_col not in merged.columns:
            continue
        sub = merged[[actual_col, proj_col, "mpg_ratio_game"]].dropna()
        proj_A = sub[proj_col] * sub["mpg_ratio_game"]
        actual = sub[actual_col]
        rows.append({
            "stat": stat,
            "sum_actual": float(actual.sum()),
            "sum_proj": float(proj_A.sum()),
            "n": int(len(sub)),
        })

    # Derived stats: sum actuals + proj_A from primary components per row
    df_25 = merged.copy()
    df_25["actual_PTS"] = df_25.get("points", 0)
    df_25["actual_REB"] = df_25.get("reboundsTotal", 0)
    df_25["actual_AST"] = df_25.get("assists", 0)
    for derived, comps in DERIVED.items():
        sum_actual = 0.0
        sum_proj = 0.0
        n_ok = 0
        for _, r in df_25.iterrows():
            try:
                a = sum(float(r[STAT_COL[c]]) for c in comps)
                p = sum(float(r[f"{c}_per_game"]) for c in comps) * float(r["mpg_ratio_game"])
                if not (np.isnan(a) or np.isnan(p)):
                    sum_actual += a
                    sum_proj += p
                    n_ok += 1
            except (KeyError, TypeError, ValueError):
                continue
        rows.append({"stat": derived, "sum_actual": sum_actual,
                     "sum_proj": sum_proj, "n": n_ok})
    return pd.DataFrame(rows)


def build_22_25_actuals_and_projA():
    """From residuals: per-season per-stat sum(actual) + sum(proj_A).

    Residuals file has PRIMARY + PR + PRA + RA. PA needs to be derived from
    component player-game-stat rows (PTS + AST per row).
    """
    res = pd.read_csv(RESIDUALS,
                      usecols=["season", "stat", "actual", "proj_A",
                               "nba_api_id", "gameId"])

    # Aggregate as-is for stats present
    agg = res.groupby(["season", "stat"]).agg(
        sum_actual=("actual", "sum"),
        sum_proj=("proj_A", "sum"),
        n=("actual", "size"),
    ).reset_index()

    # Derive PA per season per (nba_api_id, gameId)
    pa_rows = []
    for season, g in res.groupby("season"):
        wide = g.pivot_table(index=["nba_api_id", "gameId"],
                             columns="stat",
                             values=["actual", "proj_A"]).dropna(
                                 subset=[("actual", "PTS"), ("actual", "AST"),
                                         ("proj_A", "PTS"), ("proj_A", "AST")])
        if wide.empty:
            continue
        pa_actual = (wide[("actual", "PTS")] + wide[("actual", "AST")]).sum()
        pa_proj = (wide[("proj_A", "PTS")] + wide[("proj_A", "AST")]).sum()
        pa_rows.append({
            "season": season, "stat": "PA",
            "sum_actual": float(pa_actual),
            "sum_proj": float(pa_proj),
            "n": int(len(wide)),
        })
    if pa_rows:
        agg = pd.concat([agg, pd.DataFrame(pa_rows)], ignore_index=True)
    return agg


def compute_pooled_and_loo(by_season_by_stat: pd.DataFrame) -> dict:
    """For each stat, return pooled mult + per-season LOO."""
    out = {}
    for stat, g in by_season_by_stat.groupby("stat"):
        seasons = sorted(g["season"].unique())
        total_a = g["sum_actual"].sum()
        total_p = g["sum_proj"].sum()
        if total_p <= 0:
            continue
        pooled = total_a / total_p
        per_season = {}
        loo = {}
        for s in seasons:
            row = g[g["season"] == s]
            ia = float(row["sum_actual"].iloc[0])
            ip = float(row["sum_proj"].iloc[0])
            per_season[s] = round(ia / ip, 4) if ip > 0 else None
            held_out_a = total_a - ia
            held_out_p = total_p - ip
            loo[s] = round(held_out_a / held_out_p, 4) if held_out_p > 0 else None
        out[stat] = {
            "pooled": round(pooled, 4),
            "per_season_implied": per_season,
            "per_season_LOO": loo,
            "total_n": int(g["n"].sum()),
        }
    return out


def main():
    print("=" * 70)
    print("Option 1 refit: pooled 4-season LOO playoff multiplier")
    print("=" * 70)

    print("\n[1/3] Loading 22-25 actuals + proj_A from residuals...")
    df_22_25 = build_22_25_actuals_and_projA()
    print(f"  {len(df_22_25)} (season, stat) cells")
    print(f"  seasons: {sorted(df_22_25['season'].unique())}")
    print(f"  stats: {sorted(df_22_25['stat'].unique())}")

    print("\n[2/3] Computing 25-26 actuals + proj_A from playoff box + v6.1 ship...")
    df_25_26_only = build_25_26_actuals_and_projA()
    df_25_26 = df_25_26_only.copy()
    df_25_26["season"] = "2025-26"
    print(f"  {len(df_25_26)} (stat) cells, n={df_25_26['n'].iloc[0] if len(df_25_26) else 0} player-games")
    print("\n  25-26 implied per-stat (sanity check vs v2):")
    df_25_26["implied"] = df_25_26["sum_actual"] / df_25_26["sum_proj"]
    print(df_25_26[["stat", "implied", "n"]].to_string(index=False))

    print("\n[3/3] Pooling + LOO across 4 seasons...")
    pooled_input = pd.concat([df_22_25, df_25_26[["season", "stat", "sum_actual", "sum_proj", "n"]]],
                              ignore_index=True)
    result = compute_pooled_and_loo(pooled_input)

    print("\n=== POOLED 4-SEASON RESULTS ===")
    print(f"{'stat':<6} {'pooled':>8} {'22-23':>8} {'23-24':>8} {'24-25':>8} {'25-26':>8}  n")
    for stat in ALL_STATS:
        if stat not in result:
            continue
        r = result[stat]
        ps = r["per_season_implied"]
        print(f"{stat:<6} {r['pooled']:>8.4f} "
              f"{ps.get('2022-23', 0):>8.4f} "
              f"{ps.get('2023-24', 0):>8.4f} "
              f"{ps.get('2024-25', 0):>8.4f} "
              f"{ps.get('2025-26', 0):>8.4f}  {r['total_n']}")

    print("\n=== PER-SEASON LOO (mult when that season held out) ===")
    print(f"{'stat':<6} {'L22-23':>8} {'L23-24':>8} {'L24-25':>8} {'L25-26':>8}")
    for stat in ALL_STATS:
        if stat not in result:
            continue
        loo = result[stat]["per_season_LOO"]
        print(f"{stat:<6} "
              f"{loo.get('2022-23', 0):>8.4f} "
              f"{loo.get('2023-24', 0):>8.4f} "
              f"{loo.get('2024-25', 0):>8.4f} "
              f"{loo.get('2025-26', 0):>8.4f}")

    # Build v3 multiplier JSON
    pooled_mults = {stat: result[stat]["pooled"] for stat in ALL_STATS if stat in result}
    v3 = {
        "variant": "A_adj_v3_pooled_4season_LOO_2026_05_19",
        "description": "Pooled 4-season per-stat playoff multiplier. Method: "
                       "sum(actual) / sum(proj_A) across 22-23 + 23-24 + 24-25 (from "
                       "backtest_playoff_residuals.csv) + 25-26 (reconstructed from "
                       "R1+extra_rounds traditional × v6.1 ship per_game × min/RS_mpg). "
                       "Includes 25-26 in-period live data → calibrated to NBA scoring "
                       "regime through 2026-05-19 R3 cutoff. LOO across 4 seasons "
                       "verifies stability; v2 (25-26-only) archived as "
                       "playoff_regime_multipliers_v2_2025_26_implied.json.",
        "multipliers": pooled_mults,
        "per_season_implied": {s: result[s]["per_season_implied"] for s in result},
        "per_season_LOO": {s: result[s]["per_season_LOO"] for s in result},
        "total_observations_per_stat": {s: result[s]["total_n"] for s in result},
        "coverage": {
            "seasons": ["2022-23", "2023-24", "2024-25", "2025-26"],
            "rounds_22_25": "R1+R2+R3+R4 full playoffs",
            "rounds_25_26": "R1+R2+R3 through 2026-05-19 cutoff",
        },
        "caveats": [
            "25-26 share weights toward most recent regime; pooled formula doesn't season-weight equally — newer seasons with more observations contribute more.",
            "Variance miscalibration persists; do not consume proj_sd as predictive-interval source without ~1.8x-2.0x sd inflation OR empirical residual quantiles.",
            "Per-cohort multipliers not differentiated; uniform per-stat applied across rookie/soph/early_vet/mid_vet/deep_vet.",
            "FG3M baselines for 22-23 and 24-25 use prior-season per-game regular-season FG3M rate (Stan refit not in compute budget); 23-24 uses full v4-lite Stan ship.",
            "TRACKING RESET POINT: bets after this fire are under v3. Cash-rate evaluation sample restarts here.",
        ],
        "deployed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "previous_v2_2025_26_implied": {
            "PTS": 0.9097, "REB": 0.9166, "AST": 0.8271, "STL": 0.929,
            "BLK": 1.0197, "TOV": 0.9808, "FG3M": 0.9103, "PRA": 0.8993,
            "PR": 0.9116, "PA": 0.8939, "RA": 0.8826,
        },
        "previous_v1_22_25_LOO": {
            "PTS": 0.7527, "REB": 0.7596, "AST": 0.6724, "STL": 0.7434,
            "BLK": 0.8045, "TOV": 0.7293, "FG3M": 0.8708, "PRA": 0.742,
            "PR": 0.7545, "PA": 1.0000, "RA": 0.7247,
        },
    }

    # Archive v2 + write v3
    mult_path = RUN_DIR / "playoff_regime_multipliers.json"
    v2_archive = RUN_DIR / "playoff_regime_multipliers_v2_2025_26_implied.json"
    if mult_path.exists():
        shutil.copy2(mult_path, v2_archive)
        print(f"\n  archived v2 -> {v2_archive.name}")
    with open(mult_path, "w") as f:
        json.dump(v3, f, indent=2)
    print(f"  wrote v3   -> {mult_path.name}")

    print("\n=== v3 vs v2 vs v1 ===")
    print(f"{'stat':<6} {'v1':>8} {'v2':>8} {'v3':>8}  Δ(v3-v2)  Δ(v3-v1)")
    v2 = v3["previous_v2_2025_26_implied"]
    v1 = v3["previous_v1_22_25_LOO"]
    for stat in ALL_STATS:
        if stat not in pooled_mults:
            continue
        m3 = pooled_mults[stat]
        m2 = v2.get(stat, 0)
        m1 = v1.get(stat, 0)
        print(f"{stat:<6} {m1:>8.4f} {m2:>8.4f} {m3:>8.4f}  "
              f"{m3 - m2:+.4f}  {m3 - m1:+.4f}")


if __name__ == "__main__":
    main()
