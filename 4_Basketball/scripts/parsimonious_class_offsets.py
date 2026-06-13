"""Parsimonious version: pick the SINGLE highest-SNR class per stat (>=1.5).
This is the Collatz B&B discipline: one deterministic feature per class structure,
not summed across correlated features.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
from ablation_harness import load_baseline, per_stat_mae

PQ = Path(".") / "data" / "parquet"
STATS_WITH_ACTUAL = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FTA", "FTM"]


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


def apply_per_stat_offsets(base, offsets):
    out = base.copy()
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


def main():
    # Reuse the feature-attached cohort from expanded_class_diagnostic
    sys.path.insert(0, "scripts")
    from expanded_class_diagnostic import attach_features
    base = load_baseline()
    df = attach_features(base)

    # Load SNR matrix
    snr_df = pd.read_parquet(PQ / "per_stat_class_snr_matrix.parquet")
    base_mae = per_stat_mae(base)

    # For each stat, pick the single class with highest SNR (must be >=1.5)
    print("=" * 70)
    print("PARSIMONIOUS: top-1 class per stat, SNR>=1.5")
    print("=" * 70)
    top_per_stat = {}
    for stat in STATS_WITH_ACTUAL:
        sub = snr_df[(snr_df["stat"] == stat) & (snr_df["snr"] >= 1.5)]
        if len(sub) == 0:
            top_per_stat[stat] = None
            continue
        top = sub.sort_values("snr", ascending=False).iloc[0]
        top_per_stat[stat] = top["class"]
        print(f"  {stat:<5} -> {top['class']:<24} SNR={top['snr']:.2f}")
    print()

    # Build single-class LOO offsets
    offsets = {}
    for stat, cls in top_per_stat.items():
        if cls is None:
            continue
        res_col = f"{stat}_residual"
        sub = df.dropna(subset=[res_col]).copy()
        loo_map = loo_class_means(sub, cls, res_col)
        per_stat = {int(sub.loc[i, "nba_api_id"]): v for i, v in loo_map.items()}
        offsets[stat] = per_stat

    shocked = apply_per_stat_offsets(base, offsets)
    new_mae = per_stat_mae(shocked)
    rows = []
    for stat in STATS_WITH_ACTUAL:
        b = base_mae.get(stat, np.nan)
        a = new_mae.get(stat, np.nan)
        rows.append({"stat": stat,
                      "class_used": top_per_stat.get(stat) or "—",
                      "base": b, "abl": a,
                      "pct": 100 * (a - b) / b if b > 0 else np.nan})
    out = pd.DataFrame(rows)
    out["base"] = out["base"].apply(lambda x: f"{x:.4f}")
    out["abl"] = out["abl"].apply(lambda x: f"{x:.4f}")
    out["pct"] = out["pct"].apply(lambda x: f"{x:+.2f}%")
    print(out.to_string(index=False))
    pcts = [100 * (new_mae[s] - base_mae[s]) / base_mae[s]
            for s in STATS_WITH_ACTUAL if s in new_mae and base_mae.get(s, 0) > 0]
    comp = np.mean(pcts)
    print(f"\n  Composite avg pct: {comp:+.2f}%")

    # =================== Sensitivity: try top-2 with controls ===================
    print("\n" + "=" * 70)
    print("SENSITIVITY: top-2 classes per stat, requiring NON-CORRELATED")
    print("=" * 70)
    # Heuristic: if top-1 is offseason_traded, second class can be anything
    # If top-1 is age/career/years/draft, EXCLUDE other career-arc proxies
    CAREER_PROXIES = {"age_bucket", "years_pro_bucket", "career_mpg_tier",
                       "draft_pick_tier"}

    second_per_stat = {}
    for stat in STATS_WITH_ACTUAL:
        sub = snr_df[(snr_df["stat"] == stat) & (snr_df["snr"] >= 1.5)
                     ].sort_values("snr", ascending=False)
        if len(sub) < 2:
            second_per_stat[stat] = None
            continue
        first = top_per_stat.get(stat)
        first_in_career = first in CAREER_PROXIES
        for _, r in sub.iloc[1:].iterrows():
            cand = r["class"]
            if first_in_career and cand in CAREER_PROXIES:
                continue
            second_per_stat[stat] = cand
            break

    print("\nFirst + Second per stat:")
    for s in STATS_WITH_ACTUAL:
        f = top_per_stat.get(s)
        sec = second_per_stat.get(s)
        print(f"  {s:<5}  1st={f or '—':<22}  2nd={sec or '—'}")

    offsets2 = {}
    for stat in STATS_WITH_ACTUAL:
        cls_list = []
        if top_per_stat.get(stat) is not None:
            cls_list.append(top_per_stat[stat])
        if second_per_stat.get(stat) is not None:
            cls_list.append(second_per_stat[stat])
        if not cls_list:
            continue
        res_col = f"{stat}_residual"
        sub = df.dropna(subset=[res_col]).copy()
        loo_per_class = {c: loo_class_means(sub, c, res_col) for c in cls_list}
        per_stat = {}
        for idx, row in sub.iterrows():
            pid = int(row["nba_api_id"])
            d = sum(loo_per_class[c].get(idx, 0.0) for c in cls_list)
            per_stat[pid] = d
        offsets2[stat] = per_stat

    shocked2 = apply_per_stat_offsets(base, offsets2)
    new_mae2 = per_stat_mae(shocked2)
    rows = []
    for stat in STATS_WITH_ACTUAL:
        b = base_mae.get(stat, np.nan)
        a = new_mae2.get(stat, np.nan)
        rows.append({"stat": stat, "base": b, "abl": a,
                      "pct": 100 * (a - b) / b if b > 0 else np.nan})
    out = pd.DataFrame(rows)
    out["base"] = out["base"].apply(lambda x: f"{x:.4f}")
    out["abl"] = out["abl"].apply(lambda x: f"{x:.4f}")
    out["pct"] = out["pct"].apply(lambda x: f"{x:+.2f}%")
    print("\n" + out.to_string(index=False))
    pcts2 = [100 * (new_mae2[s] - base_mae[s]) / base_mae[s]
             for s in STATS_WITH_ACTUAL if s in new_mae2 and base_mae.get(s, 0) > 0]
    comp2 = np.mean(pcts2)
    print(f"\n  Composite avg pct (top-2 non-correlated): {comp2:+.2f}%")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  3-class summed (original):     -1.34%")
    print(f"  Top-1 per stat:                {comp:+.2f}%")
    print(f"  Top-2 non-correlated per stat: {comp2:+.2f}%")
    print(f"  All-classes (8) summed:        +7.30%")


if __name__ == "__main__":
    main()
