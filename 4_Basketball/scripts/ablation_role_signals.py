"""Ablate three role-signal candidates for closing the preseason MPG gap.

For 23-24 ship cohort:
    1. Preseason-MPG blend: w * (preseason_mpg - current_mpg), sweep w
    2. Depth-rank ceilings: cap mpg by 22-23 depth_order
    3. Trade dampening: reduce mpg for off-season-traded players

Calls into ablation_harness.run_ablation() for each candidate.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
from ablation_harness import load_baseline, run_ablation, print_result, per_stat_mae

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


# ============== TEST 1: Preseason MPG blend ==============
def build_preseason_mpg_2023_24(min_games: int = 2) -> dict:
    """Per nba_api_id, average preseason MPG across 2023-24 preseason games."""
    pre = pd.read_parquet(PQ / "preseason_player_boxes.parquet")
    pre = pre[pre["season"] == "2023-24"].copy()
    pre["min_num"] = pre["min"].apply(parse_min)
    pre = pre.dropna(subset=["min_num", "player_id"])
    pre["player_id"] = pre["player_id"].astype(int)
    agg = pre.groupby("player_id").agg(
        gp=("game_id", "nunique"),
        preseason_mpg=("min_num", "mean"),
    ).reset_index()
    agg = agg[agg["gp"] >= min_games]
    return dict(zip(agg["player_id"], agg["preseason_mpg"]))


def test_preseason_blend():
    print("\n" + "=" * 70)
    print("TEST 1: PRESEASON-MPG BLEND")
    print("=" * 70)
    base = load_baseline()
    pre_map = build_preseason_mpg_2023_24(min_games=2)
    print(f"Players with >= 2 preseason games (23-24): {len(pre_map)}")

    base_in_pre = base[base["nba_api_id"].isin(pre_map)]
    print(f"Of {len(base)} ship cohort, {len(base_in_pre)} have preseason data")

    base_mae = per_stat_mae(base)
    print(f"\nBaseline PTS MAE: {base_mae.get('PTS', float('nan')):.4f}")

    weights = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60]
    rows = []
    for w in weights:
        adj = {}
        for pid, pre_mpg in pre_map.items():
            cur_mpg = base.loc[base["nba_api_id"] == pid, "MPG_proj"]
            if len(cur_mpg) == 0:
                continue
            cur_mpg = float(cur_mpg.values[0])
            delta = w * (pre_mpg - cur_mpg)
            adj[int(pid)] = delta
        result = run_ablation(base, adj, label=f"preseason_blend_w{w}")
        mae_table = result["mae_table"].set_index("stat")["ablated_mae"]
        rows.append({
            "weight": w,
            "n_adjusted": result["n_players_adjusted"],
            "PTS": mae_table.get("PTS"),
            "REB": mae_table.get("REB"),
            "AST": mae_table.get("AST"),
            "STL": mae_table.get("STL"),
            "BLK": mae_table.get("BLK"),
            "TOV": mae_table.get("TOV"),
        })
    df = pd.DataFrame(rows)
    print("\n--- MAE by blend weight (lower is better) ---")
    for c in ["PTS", "REB", "AST", "STL", "BLK", "TOV"]:
        df[c] = df[c].apply(lambda x: f"{x:.4f}")
    print(df.to_string(index=False))


# ============== TEST 2: Depth-rank ceilings ==============
def test_depth_rank_ceilings():
    print("\n" + "=" * 70)
    print("TEST 2: DEPTH-RANK CEILINGS (22-23 depth -> 23-24 cap)")
    print("=" * 70)
    base = load_baseline()
    dc = pd.read_parquet(PQ / "derived_depth_chart.parquet")
    dc = dc[dc["season"] == "2022-23"].copy()
    # Per player, take their dominant team-rank from 22-23
    dc = dc.sort_values("mins_total", ascending=False).drop_duplicates("nba_api_id")
    rank_map = dict(zip(dc["nba_api_id"].astype(int), dc["depth_order"]))

    # depth_order ceilings
    CEILINGS = {1: 36.0, 2: 30.0, 3: 22.0, 4: 16.0, 5: 12.0, 6: 8.0}

    base_mae = per_stat_mae(base)
    print(f"Baseline PTS MAE: {base_mae.get('PTS', float('nan')):.4f}")

    # Try several ceiling profiles
    profiles = {
        "tight":   {1: 34.0, 2: 28.0, 3: 20.0, 4: 14.0, 5: 10.0, 6: 6.0},
        "default": {1: 36.0, 2: 30.0, 3: 22.0, 4: 16.0, 5: 12.0, 6: 8.0},
        "loose":   {1: 38.0, 2: 33.0, 3: 26.0, 4: 20.0, 5: 14.0, 6: 10.0},
        "floor_only": None,  # special: enforce a FLOOR, not a ceiling
    }

    for name, ceiling in profiles.items():
        adj = {}
        n_capped = 0
        for _, row in base.iterrows():
            pid = int(row["nba_api_id"])
            mpg = float(row["MPG_proj"])
            rk = rank_map.get(pid)
            if rk is None or pd.isna(rk):
                continue
            rk = int(rk)
            if name == "floor_only":
                # If player was rank-1 but is projected < 24 mpg, lift them
                if rk == 1 and mpg < 24.0:
                    adj[pid] = 24.0 - mpg
                    n_capped += 1
                elif rk == 2 and mpg < 18.0:
                    adj[pid] = 18.0 - mpg
                    n_capped += 1
            else:
                cap = ceiling.get(rk)
                if cap is None:
                    continue
                if mpg > cap:
                    adj[pid] = cap - mpg
                    n_capped += 1
        result = run_ablation(base, adj, label=f"depth_rank_{name}")
        mae = result["mae_table"].set_index("stat")["ablated_mae"]
        delta = result["mae_table"].set_index("stat")["pct_change"]
        print(f"\n--- profile={name}  (n_adjusted={n_capped}) ---")
        for s in ["PTS", "REB", "AST", "STL", "BLK", "TOV"]:
            v = mae.get(s)
            d = delta.get(s)
            print(f"  {s:<5} {v:.4f}  ({d:+.2f}%)")


# ============== TEST 3: Trade dampening ==============
def get_offseason_traded_2023() -> set:
    """Players traded between Apr 1 2023 and Oct 24 2023 (offseason before 23-24)."""
    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    tx = tx[(tx["transaction_type"] == "trade") &
            (tx["event_date"] >= "2023-04-15") &
            (tx["event_date"] <= "2023-10-24") &
            (tx["nba_api_id"].notna())]
    return set(tx["nba_api_id"].astype(int))


def test_trade_dampening():
    print("\n" + "=" * 70)
    print("TEST 3: OFFSEASON-TRADE DAMPENING")
    print("=" * 70)
    base = load_baseline()
    traded = get_offseason_traded_2023()
    print(f"Players traded Apr-Oct 2023: {len(traded)}")
    overlap = base[base["nba_api_id"].isin(traded)]
    print(f"Of {len(base)} ship cohort, {len(overlap)} were offseason-traded")
    print(f"Sample: {overlap['name'].head(15).tolist()}")

    for damp in [-1.0, -2.0, -3.0, -4.0, -5.0]:
        adj = {int(pid): damp for pid in traded if pid in set(base["nba_api_id"])}
        result = run_ablation(base, adj, label=f"trade_dampen_{damp}")
        mae = result["mae_table"].set_index("stat")["ablated_mae"]
        delta = result["mae_table"].set_index("stat")["pct_change"]
        print(f"\n--- damp={damp} mpg  (n={result['n_players_adjusted']}) ---")
        for s in ["PTS", "REB", "AST", "STL", "BLK", "TOV"]:
            v = mae.get(s)
            d = delta.get(s)
            print(f"  {s:<5} {v:.4f}  ({d:+.2f}%)")


def main():
    test_preseason_blend()
    test_depth_rank_ceilings()
    test_trade_dampening()


if __name__ == "__main__":
    main()
