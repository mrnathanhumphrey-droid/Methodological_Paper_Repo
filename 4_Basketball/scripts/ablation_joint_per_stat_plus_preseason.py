"""Joint composition: per-stat class offsets (SNR>=1.5, LOO) + preseason MPG blend (w=0.05).

Apply preseason blend FIRST (scales volume stats via mpg cascade), then layer
per-stat class offsets on top (additive on each stat).

This composes two informationally-disjoint layers:
  - Per-stat class offsets: structural bias by (offseason_traded, age_bucket, position)
  - Preseason MPG blend:    individual role-change signal not in career data

Reports per-stat MAE deltas vs baseline AND vs each layer alone, so we see
whether they truly compose or interfere.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
from ablation_harness import load_baseline, apply_mpg_shock, per_stat_mae

REPO = Path(".")
PQ = REPO / "data" / "parquet"

STATS_WITH_ACTUAL = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FTA", "FTM"]


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


def build_features(base):
    df = base.copy()
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    df = df.merge(meta[["nba_api_id", "position", "birth_date"]],
                  on="nba_api_id", how="left")
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
    df["age_2023"] = (pd.Timestamp("2023-10-24") - df["birth_date"]).dt.days / 365.25
    df["age_bucket"] = pd.cut(df["age_2023"],
                               bins=[0, 24, 27, 30, 33, 50],
                               labels=["<=24", "25-26", "27-29", "30-32", "33+"]).astype(str)
    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    traded = set(tx[(tx["transaction_type"] == "trade") &
                    (tx["event_date"] >= "2023-04-15") &
                    (tx["event_date"] <= "2023-10-24") &
                    (tx["nba_api_id"].notna())]["nba_api_id"].astype(int))
    df["offseason_traded"] = df["nba_api_id"].isin(traded)
    # per-stat residuals
    for stat in STATS_WITH_ACTUAL:
        proj = f"{stat}_proj"
        actual = f"{stat}_actual"
        if proj in df.columns and actual in df.columns:
            df[f"{stat}_residual"] = df[actual] - df[proj]
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
                  left_on="nba_api_id", right_on="player_id", how="left")
    return df


def loo_class_means(df, class_col, residual_col):
    sub = df.dropna(subset=[class_col, residual_col]).copy()
    out = {}
    for cls, idx in sub.groupby(class_col, observed=True).groups.items():
        idx = list(idx)
        for i in idx:
            others = [j for j in idx if j != i]
            mean = sub.loc[others, residual_col].mean() if others else 0.0
            out[i] = mean
    return out


def noise_floor(df, class_col, stat):
    res_col = f"{stat}_residual"
    if res_col not in df.columns:
        return None
    sub = df.dropna(subset=[class_col, res_col]).copy()
    grouped = sub.groupby(class_col, observed=True)[res_col].agg(["mean", "count"]).reset_index()
    grouped = grouped[grouped["count"] >= 2]
    if len(grouped) < 2:
        return None
    sd_obs = grouped["mean"].std(ddof=1)
    overall_var = sub[res_col].var(ddof=1)
    n_per_class = grouped["count"].mean()
    se_samp = np.sqrt(overall_var / n_per_class)
    snr = sd_obs / se_samp if se_samp > 0 else np.nan
    return snr


def build_per_stat_class_offsets(df, snr_threshold=1.5):
    """Returns dict[stat -> dict[pid -> offset]]."""
    classes = ["position", "age_bucket", "offseason_traded"]
    offsets = {}
    for stat in STATS_WITH_ACTUAL:
        surviving_cols = []
        for c in classes:
            snr = noise_floor(df, c, stat)
            if snr is not None and snr >= snr_threshold:
                surviving_cols.append(c)
        if not surviving_cols:
            continue
        res_col = f"{stat}_residual"
        sub = df.dropna(subset=[res_col]).copy()
        loo_per_class = {c: loo_class_means(sub, c, res_col) for c in surviving_cols}
        per_stat = {}
        for idx, row in sub.iterrows():
            pid = int(row["nba_api_id"])
            d = sum(loo_per_class[c].get(idx, 0.0) for c in surviving_cols)
            per_stat[pid] = d
        offsets[stat] = per_stat
    return offsets


def build_preseason_blend_mpg_adjust(df, w=0.05):
    """w * (preseason_mpg - MPG_proj) per player who has preseason data."""
    sub = df.dropna(subset=["preseason_mpg", "MPG_proj"]).copy()
    return {int(r["nba_api_id"]): w * (r["preseason_mpg"] - r["MPG_proj"])
            for _, r in sub.iterrows()}


def apply_per_stat_offsets(df, offsets):
    """offsets: dict {stat: dict[pid -> delta]}; additive to {stat}_proj."""
    out = df.copy()
    for stat, pid_to_delta in offsets.items():
        col = f"{stat}_proj"
        if col not in out.columns:
            continue
        out[col] = out.apply(
            lambda r: r[col] + pid_to_delta.get(int(r["nba_api_id"]), 0.0)
            if pd.notna(r[col]) else r[col],
            axis=1
        )
    return out


def report(label, base_mae, ablated_mae):
    rows = []
    for s in STATS_WITH_ACTUAL:
        b = base_mae.get(s, np.nan)
        a = ablated_mae.get(s, np.nan)
        if np.isnan(b) or np.isnan(a):
            continue
        delta = a - b
        pct = 100 * delta / b if b > 0 else np.nan
        rows.append({"stat": s, "base": b, "abl": a, "delta": delta, "pct": pct})
    df = pd.DataFrame(rows)
    print(f"\n--- {label} ---")
    fmt = df.copy()
    fmt["base"] = fmt["base"].apply(lambda x: f"{x:.4f}")
    fmt["abl"] = fmt["abl"].apply(lambda x: f"{x:.4f}")
    fmt["delta"] = fmt["delta"].apply(lambda x: f"{x:+.4f}")
    fmt["pct"] = fmt["pct"].apply(lambda x: f"{x:+.2f}%")
    print(fmt.to_string(index=False))
    comp = df["pct"].mean()
    print(f"  composite avg: {comp:+.2f}%")
    return comp


def main():
    base = load_baseline()
    df = build_features(base)
    print(f"Cohort: {len(df)}")
    base_mae = per_stat_mae(base)

    # Build the two ingredients
    print("\nBuilding per-stat class offsets (LOO, SNR>=1.5)...")
    per_stat_offsets = build_per_stat_class_offsets(df, snr_threshold=1.5)
    print(f"  surviving stats: {list(per_stat_offsets.keys())}")

    print("\nBuilding preseason MPG blend (w=0.05)...")
    preseason_adj = build_preseason_blend_mpg_adjust(df, w=0.05)
    print(f"  players with preseason adjustment: {len(preseason_adj)}")

    # ---- Layer A alone: per-stat class offsets only
    shocked_A = apply_per_stat_offsets(base, per_stat_offsets)
    mae_A = per_stat_mae(shocked_A)
    comp_A = report("LAYER A: per-stat class offsets only (LOO, SNR>=1.5)",
                     base_mae, mae_A)

    # ---- Layer B alone: preseason MPG blend only
    shocked_B = apply_mpg_shock(base, preseason_adj, scale_volume=True)
    mae_B = per_stat_mae(shocked_B)
    comp_B = report("LAYER B: preseason MPG blend only (w=0.05, mpg cascade)",
                     base_mae, mae_B)

    # ---- A + B: preseason first, then class offsets layered on top
    shocked_AB = apply_mpg_shock(base, preseason_adj, scale_volume=True)
    shocked_AB = apply_per_stat_offsets(shocked_AB, per_stat_offsets)
    mae_AB = per_stat_mae(shocked_AB)
    comp_AB = report("JOINT: A + B (preseason cascade, then class offsets)",
                      base_mae, mae_AB)

    # ---- Marginal-only check: just preseason and trade-only offsets
    trade_only_offsets = {
        stat: {pid: d for pid, d in pid_map.items() if True}
        for stat, pid_map in per_stat_offsets.items()
    }
    # Actually: rebuild offsets restricted to offseason_traded class
    print("\n\nSensitivity: reduce to offseason_traded class only (SNR>3 on 5 stats)...")
    sub_df = df.dropna(subset=["PTS_residual"]).copy()
    trade_only = {}
    for stat in STATS_WITH_ACTUAL:
        snr = noise_floor(df, "offseason_traded", stat)
        if snr is None or snr < 1.5:
            continue
        loo_map = loo_class_means(sub_df, "offseason_traded", f"{stat}_residual")
        trade_only[stat] = {int(sub_df.loc[i, "nba_api_id"]): v
                             for i, v in loo_map.items()}

    shocked_T = apply_per_stat_offsets(base, trade_only)
    mae_T = per_stat_mae(shocked_T)
    comp_T = report("LAYER T: trade-class only offsets (LOO, SNR>=1.5)",
                     base_mae, mae_T)

    shocked_TB = apply_mpg_shock(base, preseason_adj, scale_volume=True)
    shocked_TB = apply_per_stat_offsets(shocked_TB, trade_only)
    mae_TB = per_stat_mae(shocked_TB)
    comp_TB = report("JOINT: T + B (preseason + trade-only)",
                      base_mae, mae_TB)

    # ---- Summary
    print("\n" + "=" * 70)
    print("COMPOSITE SUMMARY (lower better)")
    print("=" * 70)
    print(f"  A (full per-stat offsets):     {comp_A:+.2f}%")
    print(f"  B (preseason blend only):      {comp_B:+.2f}%")
    print(f"  A + B joint:                   {comp_AB:+.2f}%")
    print(f"  T (trade-class offsets only):  {comp_T:+.2f}%")
    print(f"  T + B joint:                   {comp_TB:+.2f}%")
    print()
    if comp_AB < min(comp_A, comp_B):
        print("  -> A + B compose: joint better than either alone")
    else:
        print("  -> A + B do NOT compose cleanly")


if __name__ == "__main__":
    main()
