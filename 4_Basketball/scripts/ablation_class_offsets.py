"""B&B head-to-head: replace random per-player effects with deterministic class offsets.

For 195-cohort, classes that survived the noise-floor diagnostic:
  - age_bucket (5 levels)
  - position    (3 levels)

Adjustments derived from per-class mean MPG residuals.

Models:
  M0  baseline (v6 alone)
  M1  + position offset (3 levels)
  M2  + age_bucket offset (5 levels)
  M3  + age + position (composed)
  M3-loo  same but leave-one-out per-class means (honesty check)
  M4  + age + position + winning preseason_blend at w=0.05
  M5  + age + position + offseason_traded as PTS-side per-min flag (excluded for now,
       since flagged separately above as a non-MPG signal)
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


def attach_features(base):
    """Add position, age_bucket, mpg_actual, mpg_residual, preseason_mpg."""
    df = base.copy()
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    df = df.merge(meta[["nba_api_id", "position", "birth_date"]],
                  on="nba_api_id", how="left")
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
    df["age_2023"] = (pd.Timestamp("2023-10-24") - df["birth_date"]).dt.days / 365.25
    df["age_bucket"] = pd.cut(df["age_2023"],
                               bins=[0, 24, 27, 30, 33, 50],
                               labels=["<=24", "25-26", "27-29", "30-32", "33+"]).astype(str)

    # actual mpg
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["minutes"] = pd.to_numeric(box["minutes"], errors="coerce")
    box = box.dropna(subset=["minutes"])
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    s23 = box[box["season"] == "2023-24"]
    actual = s23.groupby("nba_api_id").agg(
        gp=("game_id", "nunique"),
        total_min=("minutes", "sum"),
    ).reset_index()
    actual["mpg_actual"] = actual["total_min"] / actual["gp"]
    df = df.merge(actual[["nba_api_id", "mpg_actual"]], on="nba_api_id", how="left")
    df["mpg_residual"] = df["mpg_actual"] - df["MPG_proj"]

    # preseason mpg
    pre = pd.read_parquet(PQ / "preseason_player_boxes.parquet")
    pre = pre[pre["season"] == "2023-24"].copy()
    pre["min_num"] = pre["min"].apply(parse_min)
    pre = pre.dropna(subset=["min_num", "player_id"])
    pre["player_id"] = pre["player_id"].astype(int)
    pre_agg = pre.groupby("player_id").agg(
        gp=("game_id", "nunique"),
        preseason_mpg=("min_num", "mean"),
    ).reset_index()
    pre_agg = pre_agg[pre_agg["gp"] >= 2]
    df = df.merge(pre_agg[["player_id", "preseason_mpg"]],
                  left_on="nba_api_id", right_on="player_id",
                  how="left")
    return df


def class_means(df, col):
    """Class -> mean mpg_residual."""
    g = df.dropna(subset=[col, "mpg_residual"]).groupby(col)["mpg_residual"].mean()
    return g.to_dict()


def class_means_loo(df, col):
    """For each row, compute the class mean EXCLUDING that row.
    Returns Series indexed by row index."""
    sub = df.dropna(subset=[col, "mpg_residual"]).copy()
    out = pd.Series(index=sub.index, dtype=float)
    grouped = sub.groupby(col)
    for cls, idx in grouped.groups.items():
        idx = list(idx)
        for i in idx:
            others = [j for j in idx if j != i]
            if len(others) == 0:
                out[i] = 0.0
            else:
                out[i] = sub.loc[others, "mpg_residual"].mean()
    return out


def build_adjustment_from_class_means(df, col_to_means: dict, loo_for=None):
    """Compose adjustments from one or more class -> mean mappings.
    The adjustment for a player is sum across class types of the class's mean residual.

    A POSITIVE class-mean-residual = under-projected (actual > projected). To CORRECT
    the projection, we ADD the class mean residual to the projection.

    Returns dict[nba_api_id -> mpg_delta].
    """
    adj = {}
    for _, row in df.iterrows():
        pid = int(row["nba_api_id"])
        delta = 0.0
        for col, means in col_to_means.items():
            if loo_for is not None and col == loo_for:
                v = loo_for_series.get(_)
                if v is not None and not pd.isna(v):
                    delta += float(v)
                continue
            cls = row.get(col)
            if cls is None or (isinstance(cls, float) and np.isnan(cls)):
                continue
            v = means.get(cls)
            if v is not None:
                delta += float(v)
        if delta != 0.0:
            adj[pid] = delta
    return adj


def build_adjustment_loo(df, cols):
    """Leave-one-out version: each player's class means computed excluding self.
    Returns dict[nba_api_id -> mpg_delta]."""
    sub = df.dropna(subset=["mpg_residual"]).copy()
    adj = {}
    # Precompute LOO per-class-mean per row for each column
    loo_maps = {}
    for col in cols:
        loo_maps[col] = class_means_loo(sub, col)
    for idx, row in sub.iterrows():
        pid = int(row["nba_api_id"])
        delta = 0.0
        for col in cols:
            v = loo_maps[col].get(idx)
            if v is not None and not pd.isna(v):
                delta += float(v)
        if delta != 0.0:
            adj[pid] = delta
    return adj


def report_result(name, base, result):
    mae = result["mae_table"].set_index("stat")
    base_mae = per_stat_mae(base)
    deltas = mae["pct_change"].to_dict()
    comp = np.mean([deltas[s] for s in ["PTS","AST","TOV","REB","STL","BLK","FTA","FTM"]
                    if s in deltas])
    pts_pct = deltas.get("PTS", 0.0)
    pts_v = mae.loc["PTS", "ablated_mae"]
    ast_pct = deltas.get("AST", 0.0)
    tov_pct = deltas.get("TOV", 0.0)
    reb_pct = deltas.get("REB", 0.0)
    stl_pct = deltas.get("STL", 0.0)
    blk_pct = deltas.get("BLK", 0.0)
    print(f"\n--- {name}  (n_adj={result['n_players_adjusted']}) ---")
    print(f"  PTS={pts_v:.4f} ({pts_pct:+.2f}%)  AST({ast_pct:+.2f}%)  TOV({tov_pct:+.2f}%)")
    print(f"  REB({reb_pct:+.2f}%)  STL({stl_pct:+.2f}%)  BLK({blk_pct:+.2f}%)")
    print(f"  composite avg: {comp:+.2f}%")


def main():
    base = load_baseline()
    df = attach_features(base)
    df = df.dropna(subset=["mpg_residual"])
    print(f"Cohort: {len(df)} (with actual mpg)")
    print(f"Mean residual:  {df['mpg_residual'].mean():+.4f}")

    pos_means = class_means(df, "position")
    age_means = class_means(df, "age_bucket")
    print(f"\nPosition class offsets:  {pos_means}")
    print(f"Age class offsets:       {age_means}")

    base_mae = per_stat_mae(base)
    print(f"\nBaseline MAE -- PTS={base_mae['PTS']:.4f}  AST={base_mae['AST']:.4f}  "
          f"TOV={base_mae['TOV']:.4f}  REB={base_mae['REB']:.4f}")

    # ---- M1: position only (in-sample)
    adj_pos = {int(r["nba_api_id"]): pos_means.get(r["position"], 0.0)
               for _, r in df.iterrows() if r["position"] in pos_means}
    res = run_ablation(base, adj_pos, label="M1_pos")
    report_result("M1: position offset (in-sample)", base, res)

    # ---- M2: age only (in-sample)
    adj_age = {int(r["nba_api_id"]): age_means.get(r["age_bucket"], 0.0)
               for _, r in df.iterrows() if r["age_bucket"] in age_means}
    res = run_ablation(base, adj_age, label="M2_age")
    report_result("M2: age offset (in-sample)", base, res)

    # ---- M3: age + position (in-sample)
    adj_3 = {}
    for _, r in df.iterrows():
        pid = int(r["nba_api_id"])
        d = pos_means.get(r["position"], 0.0) + age_means.get(r["age_bucket"], 0.0)
        if d != 0.0:
            adj_3[pid] = d
    res = run_ablation(base, adj_3, label="M3_age_pos")
    report_result("M3: age + position (in-sample, biased upward)", base, res)

    # ---- M3-LOO: leave-one-out (honest)
    adj_loo = build_adjustment_loo(df, ["position", "age_bucket"])
    res = run_ablation(base, adj_loo, label="M3_loo")
    report_result("M3-LOO: age + position (LEAVE-ONE-OUT, honest)", base, res)

    # ---- M4: M3-LOO + preseason blend at w=0.05
    adj_4 = dict(adj_loo)
    sub_pre = df.dropna(subset=["preseason_mpg"]).copy()
    for _, r in sub_pre.iterrows():
        pid = int(r["nba_api_id"])
        bonus = 0.05 * (r["preseason_mpg"] - r["MPG_proj"])
        adj_4[pid] = adj_4.get(pid, 0.0) + bonus
    res = run_ablation(base, adj_4, label="M4_age_pos_loo_plus_preseason05")
    report_result("M4: M3-LOO + preseason_blend(0.05)", base, res)

    # ---- M5: just preseason blend, for reference
    adj_5 = {}
    for _, r in sub_pre.iterrows():
        pid = int(r["nba_api_id"])
        adj_5[pid] = 0.05 * (r["preseason_mpg"] - r["MPG_proj"])
    res = run_ablation(base, adj_5, label="M5_preseason05_only")
    report_result("M5: preseason blend only (w=0.05)", base, res)

    # ---- Tau check: how much per-class structure remains after applying M3-LOO?
    print("\n" + "=" * 70)
    print("Residual structure AFTER applying M3-LOO offsets")
    print("=" * 70)
    df["adj_loo"] = df["nba_api_id"].astype(int).map(adj_loo).fillna(0.0)
    df["mpg_residual_after"] = df["mpg_residual"] - df["adj_loo"]
    for col in ["position", "age_bucket"]:
        g = df.groupby(col, observed=True)["mpg_residual_after"].agg(["mean", "count"])
        print(f"\n  After M3-LOO [{col}]:")
        print(g.to_string())


if __name__ == "__main__":
    main()
