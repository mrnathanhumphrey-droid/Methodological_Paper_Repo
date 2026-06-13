"""2026 draft class projector — applies trained priors pipeline to candidate pool.

Loads:
  - draft_2026_candidate_pool.parquet (50 of 71 invitees w/ NCAA stats, 21 freshmen/intl unmatched)
  - rookie_translation_factors.parquet (NCAA per-40 → NBA Y1 per-36 slopes)
  - rookie_archetypes.parquet (the trained cluster centroids + historical archetype Y1 distributions)
  - rookies_master.parquet (historical 2014-24 for nearest-comp lookup)

Outputs:
  data/parquet/draft_2026_projections.parquet — one row per 2026 invitee w/
    archetype assignment + per-stat Y1 point estimate + 7-percentile intervals
    + nearest 3 historical comps + confidence + data-completeness flags
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics.pairwise import euclidean_distances

PQ = Path("D:/NBA Projections/data/parquet")
OUT = PQ / "draft_2026_projections.parquet"

STATS_PER36 = ["pts_per36", "reb_per36", "ast_per36", "stl_per36", "blk_per36",
                       "fg3m_per36", "tov_per36"]
EXTRA = ["mpg", "gp"]
ALL_STATS = STATS_PER36 + EXTRA
PCT_LEVELS = [0.025, 0.10, 0.25, 0.50, 0.75, 0.90, 0.975]

CLUSTER_FEATURES = [
    "combine_height_with_shoes_inches", "combine_weight_lbs",
    "combine_wingspan_inches", "combine_standing_reach_inches",
    "combine_max_vertical_inches", "combine_lane_agility_seconds",
    "ppg_pre", "rpg_pre", "apg_pre", "spg_pre", "bpg_pre", "tov_pre", "fg3m_pre",
    "fg_pct_pre", "fg3_pct_pre", "ft_pct_pre",
]

POS_TO_HEIGHT_PRIOR = {
    "PG": 75.5, "SG": 77.5, "SF": 79.5, "PF": 81.5, "C": 83.5,
    "PG/SG": 76.5, "SG/SF": 78.5, "SF/PF": 80.5, "PF/C": 82.5,
}


def collapse_pool(pool: pd.DataFrame) -> pd.DataFrame:
    """Pool → unified feature columns matching the trained pipeline."""
    rename = {
        "ncaa_pts_per40": "ppg_pre", "ncaa_reb_per40": "rpg_pre",
        "ncaa_ast_per40": "apg_pre", "ncaa_stl_per40": "spg_pre",
        "ncaa_blk_per40": "bpg_pre", "ncaa_tov_per40": "tov_pre",
        "ncaa_fg3m_per40": "fg3m_pre", "ncaa_fg_pct": "fg_pct_pre",
        "ncaa_fg3_pct": "fg3_pct_pre", "ncaa_ft_pct": "ft_pct_pre",
    }
    out = pool.copy()
    for src, dst in rename.items():
        if src in out.columns:
            out[dst] = out[src]
    intl_rename = {
        "intl_pts_per40": "ppg_pre", "intl_reb_per40": "rpg_pre",
        "intl_ast_per40": "apg_pre", "intl_stl_per40": "spg_pre",
        "intl_blk_per40": "bpg_pre", "intl_tov_per40": "tov_pre",
        "intl_fg3m_per40": "fg3m_pre", "intl_fg_pct": "fg_pct_pre",
        "intl_fg3_pct": "fg3_pct_pre", "intl_ft_pct": "ft_pct_pre",
    }
    for src, dst in intl_rename.items():
        if src in out.columns:
            out[dst] = out[dst].where(out[dst].notna(), out[src]) if dst in out.columns else out[src]

    for c in ["combine_height_with_shoes_inches", "combine_weight_lbs",
                       "combine_wingspan_inches", "combine_standing_reach_inches",
                       "combine_max_vertical_inches", "combine_lane_agility_seconds"]:
        out[c] = np.nan

    if "combine_height_with_shoes_inches" in out.columns:
        for pos, h in POS_TO_HEIGHT_PRIOR.items():
            mask = out["position"].astype(str).str.upper() == pos
            out.loc[mask & out["combine_height_with_shoes_inches"].isna(), "combine_height_with_shoes_inches"] = h
    return out


def confidence(row):
    s = 0.0
    if row.get("has_pre_nba"): s += 0.50
    if pd.notna(row.get("position")): s += 0.20
    if pd.notna(row.get("ncaa_match_score")) and row["ncaa_match_score"] >= 95: s += 0.20
    if row.get("has_intl"): s += 0.10
    return min(s, 1.0)


def position_archetype_floor(position, has_stats, ppg, bpg, fg3m):
    """Position-based archetype override when cluster assignment looks wrong for a big."""
    if position is None:
        return None
    p = str(position).upper()
    if p in ("C", "PF/C") and has_stats:
        if bpg is not None and not np.isnan(bpg) and bpg >= 2.0:
            return "Defensive Big"
        if fg3m is not None and not np.isnan(fg3m) and fg3m >= 1.0:
            return "Stretch Big"
        return "Stretch Big"
    if p == "C" and not has_stats:
        return "Defensive Big"
    if p == "PF" and has_stats and bpg is not None and bpg >= 1.5:
        return "Stretch Big"
    return None


def main():
    print("=== loading ===")
    pool = pd.read_parquet(PQ / "draft_2026_candidate_pool.parquet")
    print(f"  2026 pool: {len(pool)}")
    pool = collapse_pool(pool)

    historical = pd.read_parquet(PQ / "rookies_master.parquet")
    arch_hist = pd.read_parquet(PQ / "rookie_archetypes.parquet")
    tf = pd.read_parquet(PQ / "rookie_translation_factors.parquet")
    print(f"  historical 2014-24: {len(historical)}; archetypes: {len(arch_hist)}")

    historical = historical.merge(arch_hist[["nba_api_id", "archetype"]], on="nba_api_id", how="left")
    for stat, lbl in [("pts_per40", "ppg_pre"), ("reb_per40", "rpg_pre"),
                                ("ast_per40", "apg_pre"), ("stl_per40", "spg_pre"),
                                ("blk_per40", "bpg_pre"), ("tov_per40", "tov_pre"),
                                ("fg3m_per40", "fg3m_pre"), ("fg_pct", "fg_pct_pre"),
                                ("fg3_pct", "fg3_pct_pre"), ("ft_pct", "ft_pct_pre")]:
        ncaa_c, intl_c = f"ncaa_{stat}", f"intl_{stat}"
        historical[lbl] = np.nan
        if ncaa_c in historical.columns: historical[lbl] = historical[ncaa_c]
        if intl_c in historical.columns:
            historical[lbl] = historical[lbl].where(historical[lbl].notna(), historical[intl_c])

    feats = [c for c in CLUSTER_FEATURES if c in historical.columns]
    X_hist = historical[feats].apply(pd.to_numeric, errors="coerce")
    imputer = SimpleImputer(strategy="median").fit(X_hist)
    scaler = StandardScaler().fit(imputer.transform(X_hist))
    Xh_z = scaler.transform(imputer.transform(X_hist))

    X_pool = pool[feats].apply(pd.to_numeric, errors="coerce")
    Xp_z = scaler.transform(imputer.transform(X_pool))

    trained = historical[historical["has_nba_y1"].fillna(False) & (historical["nba_y1_gp"].fillna(0) >= 25)].copy()
    train_mask = historical.index.isin(trained.index)
    Xh_z_tr = Xh_z[train_mask]
    train_archetypes = historical.loc[train_mask, "archetype"].values
    train_idx_arr = historical.index[train_mask].values

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

    tf_lookup = {(r["source"], r["stat"]): (r["slope"], r["intercept"], r["mean_x"], r["mean_y"])
                       for _, r in tf[tf["bucket"] == "ALL"].iterrows()}

    name_arr = historical["player_name_raw"].astype(str).values
    py_arr = historical["draft_year"].values

    print("\n=== projecting 2026 prospects ===")
    out_rows = []
    for i, row in pool.reset_index(drop=True).iterrows():
        xp = Xp_z[i].reshape(1, -1)
        d_arch = euclidean_distances(xp, Xh_z_tr).ravel()
        kk = min(10, len(d_arch))
        top_k_idx = np.argsort(d_arch)[:kk]
        top_arch_labels = [train_archetypes[j] for j in top_k_idx if train_archetypes[j] is not None and not (isinstance(train_archetypes[j], float) and np.isnan(train_archetypes[j]))]
        if not top_arch_labels:
            arch_lbl = "Utility Wing 2"
        else:
            arch_vote = pd.Series(top_arch_labels).value_counts()
            arch_lbl = arch_vote.index[0]

        pos_override = position_archetype_floor(
            row.get("position"),
            bool(row.get("has_pre_nba")),
            row.get("bpg_pre"),
            row.get("bpg_pre"),
            row.get("fg3m_pre"),
        )
        if pos_override:
            arch_lbl = pos_override

        out = {
            "player_name": row.get("player_name"),
            "position": row.get("position"),
            "has_pre_nba": bool(row.get("has_pre_nba")),
            "ncaa_match_score": row.get("ncaa_match_score"),
            "ncaa_n_seasons": row.get("ncaa_n_seasons"),
            "ncaa_last_season": row.get("ncaa_last_season"),
            "archetype": arch_lbl,
            "confidence": confidence(row),
            "data_status": "FULL" if row.get("has_pre_nba") else "INSUFFICIENT_DATA_NEEDS_2025_26_SCRAPE",
        }

        for s in ["pts", "reb", "ast", "stl", "blk", "tov", "fg3m"]:
            out[f"ncaa_{s}_per40"] = row.get(f"ncaa_{s}_per40")

        base = cluster_priors.get(arch_lbl, {})
        for stat in ALL_STATS:
            base_mean = base.get(f"{stat}_mean", np.nan)
            base_sd = base.get(f"{stat}_sd", np.nan)
            adj_mean = base_mean

            stat_to_tf = {"pts_per36": "pts", "reb_per36": "reb", "ast_per36": "ast",
                                      "stl_per36": "stl", "blk_per36": "blk",
                                      "fg3m_per36": "fg3m", "tov_per36": "tov"}
            if stat in stat_to_tf and not np.isnan(adj_mean):
                tf_stat = stat_to_tf[stat]
                pre_col = {"pts": "ppg_pre", "reb": "rpg_pre", "ast": "apg_pre",
                                   "stl": "spg_pre", "blk": "bpg_pre", "tov": "tov_pre",
                                   "fg3m": "fg3m_pre"}.get(tf_stat)
                pre_val = row.get(pre_col)
                src = "ncaa" if row.get("has_ncaa") else ("intl" if row.get("has_intl") else None)
                if src and pd.notna(pre_val):
                    key = (src, tf_stat)
                    if key in tf_lookup:
                        slope, intercept, mu_x, mu_y = tf_lookup[key]
                        tf_pred = slope * pre_val + intercept
                        adj_mean = 0.5 * base_mean + 0.5 * tf_pred

            out[f"{stat}_mean"] = adj_mean
            out[f"{stat}_sd"] = base_sd
            for p in PCT_LEVELS:
                base_p = base.get(f"{stat}_p{int(p*1000)}", np.nan)
                if not np.isnan(base_p) and not np.isnan(base_mean) and not np.isnan(adj_mean):
                    out[f"{stat}_p{int(p*1000)}"] = base_p + (adj_mean - base_mean)

        comp_names, comp_archs, comp_dists = [], [], []
        order = np.argsort(d_arch)[:5]
        for k in order[:3]:
            h_idx = train_idx_arr[k]
            comp_names.append(f"{name_arr[h_idx]} ({int(py_arr[h_idx]) if not pd.isna(py_arr[h_idx]) else '?'})")
            comp_archs.append(train_archetypes[k])
            comp_dists.append(round(float(d_arch[k]), 3))
        out["nearest_comp_1"] = comp_names[0] if comp_names else None
        out["nearest_comp_2"] = comp_names[1] if len(comp_names) > 1 else None
        out["nearest_comp_3"] = comp_names[2] if len(comp_names) > 2 else None
        out["nearest_comp_dists"] = "|".join(map(str, comp_dists)) if comp_dists else None

        out_rows.append(out)

    proj = pd.DataFrame(out_rows)
    proj["production_per36"] = (
        proj["pts_per36_mean"].fillna(0)
        + proj["reb_per36_mean"].fillna(0)
        + proj["ast_per36_mean"].fillna(0) * 1.5
        + proj["stl_per36_mean"].fillna(0) * 2.0
        + proj["blk_per36_mean"].fillna(0) * 2.0
        + proj["fg3m_per36_mean"].fillna(0) * 0.5
        - proj["tov_per36_mean"].fillna(0) * 1.0
    )
    proj["projected_y1_value"] = proj["production_per36"] * (proj["mpg_mean"].fillna(0) / 36.0) * 65
    proj["rank_by_value"] = proj["projected_y1_value"].rank(ascending=False, method="dense")
    proj = proj.sort_values("projected_y1_value", ascending=False, na_position="last").reset_index(drop=True)
    proj["rank"] = proj.index + 1
    proj.to_parquet(OUT, index=False)
    proj.to_csv(OUT.with_suffix(".csv"), index=False)
    print(f"wrote: {OUT}")
    print(f"  rows: {len(proj)}, cols: {len(proj.columns)}")

    cols = ["rank", "player_name", "position", "archetype", "confidence",
                  "projected_y1_value", "mpg_mean", "pts_per36_mean", "reb_per36_mean",
                  "ast_per36_mean", "blk_per36_mean", "fg3m_per36_mean",
                  "nearest_comp_1", "nearest_comp_2"]
    print("\n=== 2026 DRAFT BOARD v1 (ranked by projected Year-1 value, top 40) ===")
    print(proj[cols].head(40).round(2).to_string(index=False))

    print("\n=== confidence distribution ===")
    print(proj["confidence"].describe().round(2).to_string())

    print(f"\n=== archetype distribution ===")
    print(proj["archetype"].value_counts().to_string())


if __name__ == "__main__":
    main()
