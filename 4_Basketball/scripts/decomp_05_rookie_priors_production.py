"""★ PRODUCTION rookie_priors.parquet — per-player Year-1 NBA projection.

Goal: produce the empirical-Bayes anchor that the v6 projection pipeline uses for
incoming rookies (replaces the "no signal" league-mean fallback).

Per rookie:
  - Point estimate for each Y1 stat (pts/reb/ast/stl/blk/fg3m/tov per-36 + mpg + GP)
  - 50% / 80% / 95% intervals (empirical from cluster member distribution, recentered)
  - Archetype label + nearest 3 comps from 2014-2024 history
  - Confidence score (0-1) based on data completeness

Methodology (in plain language):
  1. For each rookie, take their archetype cluster's historical Y1 distribution
     as the BASE prior (point + percentiles).
  2. Translation-factor adjustment: their pre-NBA stats nudge them above/below
     archetype mean by the size of their pre-NBA z-score × per-stat slope.
  3. Draft-pick adjustment: usage (mpg) and scoring rate adjusted by the
     draft_pick → mpg/pts coefficients from Signal-Source.
  4. The intervals are re-centered around the adjusted point + same per-archetype
     spread (heuristic — calibrated empirically in step 06).

Outputs:
    data/parquet/rookie_priors.parquet (one row per nba_api_id)
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics.pairwise import euclidean_distances

PQ = Path("D:/NBA Projections/data/parquet")
OUT = PQ / "rookie_priors.parquet"
MIN_Y1_GP_FOR_TRAIN = 25
N_COMPS = 3

STATS_PER36 = ["pts_per36", "reb_per36", "ast_per36", "stl_per36", "blk_per36",
                       "fg3m_per36", "tov_per36"]
EXTRA = ["mpg", "gp", "fg_pct", "fg3_pct", "ft_pct"]
ALL_STATS = STATS_PER36 + EXTRA

PCT_LEVELS = [0.025, 0.10, 0.25, 0.50, 0.75, 0.90, 0.975]

CLUSTER_FEATURES = [
    "combine_height_with_shoes_inches", "combine_weight_lbs",
    "combine_wingspan_inches", "combine_standing_reach_inches",
    "combine_max_vertical_inches", "combine_lane_agility_seconds",
    "ppg_pre", "rpg_pre", "apg_pre", "spg_pre", "bpg_pre", "tov_pre", "fg3m_pre",
    "fg_pct_pre", "fg3_pct_pre", "ft_pct_pre",
]


def collapse_pre_nba(m):
    for stat, lbl in [("pts_per40", "ppg_pre"), ("reb_per40", "rpg_pre"),
                                ("ast_per40", "apg_pre"), ("stl_per40", "spg_pre"),
                                ("blk_per40", "bpg_pre"), ("tov_per40", "tov_pre"),
                                ("fg3m_per40", "fg3m_pre"),
                                ("fg_pct", "fg_pct_pre"), ("fg3_pct", "fg3_pct_pre"),
                                ("ft_pct", "ft_pct_pre")]:
        ncaa_c, intl_c = f"ncaa_{stat}", f"intl_{stat}"
        m[lbl] = np.nan
        if ncaa_c in m.columns: m[lbl] = m[ncaa_c]
        if intl_c in m.columns: m[lbl] = m[lbl].where(m[lbl].notna(), m[intl_c])
    return m


def confidence_score(row):
    score = 0.0
    if row.get("has_ncaa") or row.get("has_intl"): score += 0.40
    if row.get("has_combine"): score += 0.30
    if pd.notna(row.get("draft_pick")): score += 0.20
    if row.get("has_ncaa") and row.get("has_intl"): score += 0.10
    return min(score, 1.0)


def main():
    print("=== loading ===")
    m = pd.read_parquet(PQ / "rookies_master.parquet")
    arch = pd.read_parquet(PQ / "rookie_archetypes.parquet")[["nba_api_id", "archetype", "cluster_idx"]]
    tf = pd.read_parquet(PQ / "rookie_translation_factors.parquet")
    ss = pd.read_parquet(PQ / "rookie_signal_source.parquet")
    m = collapse_pre_nba(m)
    m = m.merge(arch, on="nba_api_id", how="left")
    print(f"  master+arch: {len(m):,}")

    # ---- 1. Per-archetype Y1 percentile table (the base prior)
    trained = m[m["has_nba_y1"] & (m["nba_y1_gp"] >= MIN_Y1_GP_FOR_TRAIN)].copy()
    cluster_priors = {}
    for arch_lbl, grp in trained.groupby("archetype"):
        d = {"n": len(grp)}
        for stat in ALL_STATS:
            col = f"nba_y1_{stat}"
            if col in grp.columns:
                vals = grp[col].dropna()
                if len(vals) >= 5:
                    d[f"{stat}_mean"] = float(vals.mean())
                    d[f"{stat}_sd"] = float(vals.std(ddof=0))
                    for p in PCT_LEVELS:
                        d[f"{stat}_p{int(p*1000)}"] = float(vals.quantile(p))
        cluster_priors[arch_lbl] = d

    # ---- 2. Translation-factor lookup (ALL-bucket slope+intercept per source per stat)
    tf_lookup = {}
    for _, r in tf[tf["bucket"] == "ALL"].iterrows():
        tf_lookup[(r["source"], r["stat"])] = (r["slope"], r["intercept"], r["mean_x"], r["mean_y"])

    # ---- 3. Draft-pick → mpg+pts slopes from signal-source (univariate)
    def get_slope(target, inp):
        sub = ss[(ss["target"] == target) & (ss["input"] == inp)]
        if not len(sub): return (0.0, np.nan)
        return (float(sub["slope"].iloc[0]), float(sub["intercept"].iloc[0]))

    mpg_dp_slope, mpg_dp_int = get_slope("mpg", "draft_pick")
    pts_dp_slope, pts_dp_int = get_slope("pts_per36", "draft_pick")

    # ---- 4. Nearest comps in z-space
    f_present = [c for c in CLUSTER_FEATURES if c in m.columns]
    Xraw = m[f_present].apply(pd.to_numeric, errors="coerce")
    imp = SimpleImputer(strategy="median").fit(Xraw)
    scaler = StandardScaler().fit(imp.transform(Xraw))
    Xz = scaler.transform(imp.transform(Xraw))
    train_mask = m["has_nba_y1"].fillna(False).values & (m["nba_y1_gp"].fillna(0).values >= MIN_Y1_GP_FOR_TRAIN)
    train_idx = np.where(train_mask)[0]
    Xz_train = Xz[train_idx]

    name_arr = m["player_name_raw"].astype(str).values
    nba_id_arr = m["nba_api_id"].values
    py_arr = m["draft_year"].values

    # ---- 5. Per-rookie projection
    print("\n=== projecting all 501 rookies ===")
    rows = []
    pre_means = m[["ppg_pre", "rpg_pre", "apg_pre", "spg_pre", "bpg_pre", "tov_pre", "fg3m_pre"]].mean()
    pre_sd = m[["ppg_pre", "rpg_pre", "apg_pre", "spg_pre", "bpg_pre", "tov_pre", "fg3m_pre"]].std(ddof=0)

    for i, row in m.reset_index(drop=True).iterrows():
        arch_lbl = row.get("archetype")
        if arch_lbl is None or arch_lbl not in cluster_priors:
            continue
        base = cluster_priors[arch_lbl]
        out = {
            "nba_api_id": int(row["nba_api_id"]) if pd.notna(row["nba_api_id"]) else None,
            "player_name": row.get("player_name_raw"),
            "draft_year": row.get("draft_year"),
            "draft_pick": row.get("draft_pick"),
            "archetype": arch_lbl,
            "n_cluster_training": base.get("n", 0),
            "confidence": confidence_score(row),
        }

        for stat in ALL_STATS:
            base_mean = base.get(f"{stat}_mean", np.nan)
            base_sd = base.get(f"{stat}_sd", np.nan)
            adj_mean = base_mean

            # Translation adjustment: nudge based on z of pre-NBA source for matching stat
            stat_key_map = {"pts_per36": "pts", "reb_per36": "reb", "ast_per36": "ast",
                                       "stl_per36": "stl", "blk_per36": "blk",
                                       "fg3m_per36": "fg3m", "tov_per36": "tov"}
            if stat in stat_key_map and not np.isnan(adj_mean):
                tf_stat = stat_key_map[stat]
                src = "ncaa" if pd.notna(row.get("ncaa_pts_per40")) else "intl"
                pre_col_map = {"pts": "ppg_pre", "reb": "rpg_pre", "ast": "apg_pre",
                                          "stl": "spg_pre", "blk": "bpg_pre", "tov": "tov_pre",
                                          "fg3m": "fg3m_pre"}
                pre_val = row.get(pre_col_map.get(tf_stat))
                tf_key = (src, tf_stat)
                if tf_key in tf_lookup and pd.notna(pre_val):
                    slope, intercept, mu_x, mu_y = tf_lookup[tf_key]
                    tf_pred = slope * pre_val + intercept
                    adj_mean = 0.5 * base_mean + 0.5 * tf_pred

            # Draft pick adjustment for pts_per36 and mpg
            if stat == "mpg" and pd.notna(row.get("draft_pick")) and not np.isnan(adj_mean):
                dp_pred = mpg_dp_slope * row["draft_pick"] + mpg_dp_int
                adj_mean = 0.5 * base_mean + 0.5 * dp_pred
            if stat == "pts_per36" and pd.notna(row.get("draft_pick")) and not np.isnan(adj_mean):
                dp_pred = pts_dp_slope * row["draft_pick"] + pts_dp_int
                adj_mean = 0.5 * adj_mean + 0.5 * dp_pred

            out[f"{stat}_mean"] = adj_mean
            for p in PCT_LEVELS:
                base_p = base.get(f"{stat}_p{int(p*1000)}", np.nan)
                if not np.isnan(base_p) and not np.isnan(base_mean) and not np.isnan(adj_mean):
                    out[f"{stat}_p{int(p*1000)}"] = base_p + (adj_mean - base_mean)

        # Nearest comps in z-space
        if len(train_idx) > 0:
            xz_row = Xz[i].reshape(1, -1)
            d = euclidean_distances(xz_row, Xz_train).ravel()
            order = np.argsort(d)[:N_COMPS + 1]
            comp_names = []
            for k in order:
                m_idx = int(train_idx[k])
                if nba_id_arr[m_idx] == out["nba_api_id"]:
                    continue
                comp_names.append(f"{name_arr[m_idx]} ({int(py_arr[m_idx]) if not pd.isna(py_arr[m_idx]) else '?'})")
                if len(comp_names) >= N_COMPS:
                    break
            out["nearest_comps"] = " | ".join(comp_names)

        rows.append(out)

    priors = pd.DataFrame(rows)
    priors.to_parquet(OUT, index=False)
    print(f"  wrote: {OUT}")
    print(f"  rows: {len(priors):,}, cols: {len(priors.columns)}")

    print("\n=== sample 2024 class (top 12 by pick) ===")
    s = priors[(priors["draft_year"] == 2024)].sort_values("draft_pick").head(12)
    show_cols = ["player_name", "draft_pick", "archetype", "confidence",
                       "mpg_mean", "pts_per36_mean", "reb_per36_mean", "ast_per36_mean",
                       "blk_per36_mean", "nearest_comps"]
    show_cols = [c for c in show_cols if c in s.columns]
    print(s[show_cols].round(2).to_string(index=False))

    print("\n=== confidence distribution ===")
    print(priors["confidence"].describe().round(2).to_string())


if __name__ == "__main__":
    main()
