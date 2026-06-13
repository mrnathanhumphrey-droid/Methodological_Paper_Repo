"""Joint sweep: preseason-blend × trade-dampen × (optional) asymmetric dampen.

Two-axis sweep over (preseason_blend_w, trade_dampen_mpg) on the 23-24 ship
cohort, plus an asymmetric variant where dampen depends on whether the traded
player was a starter (career mpg >= 28) vs bench.

Prints a grid of MAE for PTS/AST/TOV (the targeted gaps) and a composite.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
from ablation_harness import load_baseline, run_ablation, per_stat_mae

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


def build_preseason_mpg(min_games: int = 2) -> dict:
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


def get_offseason_traded() -> set:
    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    tx = tx[(tx["transaction_type"] == "trade") &
            (tx["event_date"] >= "2023-04-15") &
            (tx["event_date"] <= "2023-10-24") &
            (tx["nba_api_id"].notna())]
    return set(tx["nba_api_id"].astype(int))


def build_combined_adjustment(base, pre_map, traded, w_pre, damp,
                                asymmetric=False, damp_bench=None):
    """Compose: preseason_nudge for everyone with preseason data + trade_damp."""
    adj = {}
    base_dict = dict(zip(base["nba_api_id"].astype(int), base["MPG_proj"]))
    for pid, cur_mpg in base_dict.items():
        delta = 0.0
        if pid in pre_map:
            delta += w_pre * (pre_map[pid] - cur_mpg)
        if pid in traded:
            if asymmetric and cur_mpg < 25.0 and damp_bench is not None:
                delta += damp_bench
            else:
                delta += damp
        if delta != 0.0:
            adj[pid] = delta
    return adj


def main():
    base = load_baseline()
    pre_map = build_preseason_mpg(min_games=2)
    traded = get_offseason_traded()
    print(f"Baseline cohort: {len(base)}")
    print(f"With preseason data: {len(set(pre_map) & set(base['nba_api_id']))}")
    print(f"Offseason-traded in cohort: {len(traded & set(base['nba_api_id']))}")
    print()

    base_mae = per_stat_mae(base)
    base_pts = base_mae["PTS"]
    base_ast = base_mae["AST"]
    base_tov = base_mae["TOV"]
    base_reb = base_mae["REB"]
    base_stl = base_mae["STL"]
    base_blk = base_mae["BLK"]
    print(f"Baseline MAE -- PTS={base_pts:.4f}  AST={base_ast:.4f}  "
          f"TOV={base_tov:.4f}  REB={base_reb:.4f}  STL={base_stl:.4f}")

    # ---- 2-axis sweep: w_pre x damp
    print("\n" + "=" * 78)
    print("JOINT SWEEP: preseason_blend_w x trade_dampen_mpg")
    print("=" * 78)
    weights = [0.00, 0.05, 0.075, 0.10, 0.125, 0.15]
    damps = [0.0, -1.0, -1.5, -2.0, -2.5, -3.0, -3.5]

    rows = []
    for w in weights:
        for d in damps:
            adj = build_combined_adjustment(base, pre_map, traded, w, d)
            res = run_ablation(base, adj, label=f"w{w}_d{d}")
            mae = res["mae_table"].set_index("stat")["ablated_mae"]
            rows.append({
                "w_pre": w, "damp": d,
                "PTS": mae.get("PTS"),
                "AST": mae.get("AST"),
                "TOV": mae.get("TOV"),
                "REB": mae.get("REB"),
                "STL": mae.get("STL"),
                "BLK": mae.get("BLK"),
                "FTA": mae.get("FTA"),
                "FTM": mae.get("FTM"),
            })
    df = pd.DataFrame(rows)

    # Composite: average pct change across the 8 stats (lower better)
    for s in ["PTS", "AST", "TOV", "REB", "STL", "BLK", "FTA", "FTM"]:
        bm = base_mae.get(s)
        df[f"{s}_pct"] = 100 * (df[s] - bm) / bm
    df["composite_pct"] = df[[f"{s}_pct" for s in ["PTS","AST","TOV","REB","STL","BLK","FTA","FTM"]]].mean(axis=1)

    # PTS sweep table
    print("\n--- PTS MAE grid (rows=w_pre, cols=damp) ---")
    pivot_pts = df.pivot(index="w_pre", columns="damp", values="PTS")
    print(pivot_pts.applymap(lambda x: f"{x:.4f}").to_string())

    print("\n--- Composite avg pct change (rows=w_pre, cols=damp; lower better) ---")
    pivot_comp = df.pivot(index="w_pre", columns="damp", values="composite_pct")
    print(pivot_comp.applymap(lambda x: f"{x:+.2f}%").to_string())

    # Best on each metric
    for col, label in [("PTS", "PTS MAE"), ("composite_pct", "composite avg %")]:
        best = df.loc[df[col].idxmin()]
        print(f"\nBest by {label}: w_pre={best['w_pre']}, damp={best['damp']}")
        print(f"  PTS={best['PTS']:.4f} ({best['PTS_pct']:+.2f}%)  "
              f"AST={best['AST']:.4f} ({best['AST_pct']:+.2f}%)  "
              f"TOV={best['TOV']:.4f} ({best['TOV_pct']:+.2f}%)")
        print(f"  REB={best['REB']:.4f} ({best['REB_pct']:+.2f}%)  "
              f"STL={best['STL']:.4f} ({best['STL_pct']:+.2f}%)  "
              f"BLK={best['BLK']:.4f} ({best['BLK_pct']:+.2f}%)")
        print(f"  FTA={best['FTA']:.4f} ({best['FTA_pct']:+.2f}%)  "
              f"FTM={best['FTM']:.4f} ({best['FTM_pct']:+.2f}%)")
        print(f"  composite avg: {best['composite_pct']:+.2f}%")

    # ---- Asymmetric dampen: starters vs bench
    print("\n" + "=" * 78)
    print("ASYMMETRIC TRADE DAMPEN (starters vs bench, with preseason w=0.075)")
    print("=" * 78)
    for ds, db in [(-1.0, -3.0), (-1.5, -3.0), (-2.0, -3.0),
                    (-1.5, -3.5), (-2.0, -4.0), (-1.0, -4.0)]:
        adj = build_combined_adjustment(base, pre_map, traded,
                                         w_pre=0.075, damp=ds,
                                         asymmetric=True, damp_bench=db)
        res = run_ablation(base, adj, label=f"asym_s{ds}_b{db}")
        mae = res["mae_table"].set_index("stat")["ablated_mae"]
        deltas = res["mae_table"].set_index("stat")["pct_change"]
        comp = np.mean([deltas[s] for s in ["PTS","AST","TOV","REB","STL","BLK","FTA","FTM"]])
        print(f"\nstarter_damp={ds}  bench_damp={db}")
        for s in ["PTS","AST","TOV","REB","STL","BLK","FTA","FTM"]:
            print(f"  {s:<5} {mae[s]:.4f} ({deltas[s]:+.2f}%)")
        print(f"  composite avg: {comp:+.2f}%")


if __name__ == "__main__":
    main()
