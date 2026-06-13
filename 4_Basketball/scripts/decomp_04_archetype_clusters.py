"""Rookie Archetype Clusters — KMeans on pre-NBA + combine + position features.

Features used (z-scored within draft year):
  - combine height_with_shoes, weight, wingspan, standing_reach, max_vertical, lane_agility
  - pre-NBA per-40 pts, reb, ast, stl, blk, tov, fg3m (NCAA or intl, picking primary source)
  - pre-NBA fg_pct, fg3_pct, ft_pct

Cluster count: 8 (covers PG/score-G/wing/wing-shooter/forward/stretch-big/rim-big/rim-rotation).
Cluster labels assigned post-hoc from feature centroids.

Outputs:
    data/parquet/rookie_archetypes.parquet  (per-rookie cluster label + dist to nearest 5 comps)
    docs/ROOKIE_DECOMP_ARCHETYPES.md (cluster labels + Y1 distribution per cluster)
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

PQ = Path("D:/NBA Projections/data/parquet")
DOCS = Path("D:/NBA Projections/docs")
OUT_PQ = PQ / "rookie_archetypes.parquet"
OUT_DOC = DOCS / "ROOKIE_DECOMP_ARCHETYPES.md"
N_CLUSTERS = 8
RNG = 42

FEATURES = [
    "combine_height_with_shoes_inches", "combine_weight_lbs",
    "combine_wingspan_inches", "combine_standing_reach_inches",
    "combine_max_vertical_inches", "combine_lane_agility_seconds",
    "ppg_pre", "rpg_pre", "apg_pre", "spg_pre", "bpg_pre", "tov_pre", "fg3m_pre",
    "fg_pct_pre", "fg3_pct_pre", "ft_pct_pre",
]

Y1_OUTCOMES = [
    "nba_y1_pts_per36", "nba_y1_reb_per36", "nba_y1_ast_per36",
    "nba_y1_stl_per36", "nba_y1_blk_per36", "nba_y1_fg3m_per36",
    "nba_y1_mpg", "nba_y1_gp", "nba_y1_fg_pct", "nba_y1_fg3_pct",
]


def collapse_pre_nba(m: pd.DataFrame) -> pd.DataFrame:
    """Pick primary source per-40 (NCAA preferred, fall back to intl)."""
    for stat, lbl in [("pts_per40", "ppg_pre"), ("reb_per40", "rpg_pre"),
                                ("ast_per40", "apg_pre"), ("stl_per40", "spg_pre"),
                                ("blk_per40", "bpg_pre"), ("tov_per40", "tov_pre"),
                                ("fg3m_per40", "fg3m_pre"),
                                ("fg_pct", "fg_pct_pre"), ("fg3_pct", "fg3_pct_pre"),
                                ("ft_pct", "ft_pct_pre")]:
        ncaa_c = f"ncaa_{stat}"
        intl_c = f"intl_{stat}"
        m[lbl] = np.nan
        if ncaa_c in m.columns:
            m[lbl] = m[ncaa_c]
        if intl_c in m.columns:
            m[lbl] = m[lbl].where(m[lbl].notna(), m[intl_c])
    return m


def label_cluster(centroid: pd.Series, feature_names: list) -> str:
    """Heuristic post-hoc cluster label from centroid z-scores."""
    z = dict(zip(feature_names, centroid))
    height = z.get("combine_height_with_shoes_inches", 0)
    reach = z.get("combine_standing_reach_inches", 0)
    apg = z.get("apg_pre", 0)
    rpg = z.get("rpg_pre", 0)
    bpg = z.get("bpg_pre", 0)
    ppg = z.get("ppg_pre", 0)
    fg3 = z.get("fg3m_pre", 0)
    fg3_pct = z.get("fg3_pct_pre", 0)
    vert = z.get("combine_max_vertical_inches", 0)

    if height > 0.8 and (bpg > 0.5 or rpg > 0.5):
        if vert > 0.3 and rpg > 0.7:
            return "Rim-runner Big"
        if fg3 > 0.3 or fg3_pct > 0.3:
            return "Stretch Big"
        return "Defensive Big"
    if height > 0.3 and apg < 0:
        if fg3 > 0.3:
            return "Stretch Forward"
        return "Wing Defender"
    if -0.3 < height < 0.5 and (fg3 > 0.3 or fg3_pct > 0.4):
        return "Wing Shooter"
    if -0.3 < height < 0.5 and ppg > 0.3 and apg < 0.3:
        return "Score-First Wing"
    if height < -0.3 and apg > 0.5:
        if ppg > 0.3:
            return "Combo Guard"
        return "Pass-First PG"
    if height < -0.3 and ppg > 0.3:
        return "Scoring Guard"
    return "Utility Wing"


def main():
    m = pd.read_parquet(PQ / "rookies_master.parquet")
    print(f"  master rows: {len(m):,}")
    m = collapse_pre_nba(m)

    feat_present = [c for c in FEATURES if c in m.columns]
    print(f"  using {len(feat_present)} features")

    has_features = m[feat_present].notna().any(axis=1)
    m = m[has_features].copy()
    print(f"  with at least one feature: {len(m):,}")

    X = m[feat_present].copy()
    for c in feat_present:
        X[c] = pd.to_numeric(X[c], errors="coerce")

    imputer = SimpleImputer(strategy="median")
    X_imp = imputer.fit_transform(X)
    scaler = StandardScaler()
    X_z = scaler.fit_transform(X_imp)

    km = KMeans(n_clusters=N_CLUSTERS, random_state=RNG, n_init=20)
    m["cluster_idx"] = km.fit_predict(X_z)
    centroids = pd.DataFrame(km.cluster_centers_, columns=feat_present)
    cluster_labels = {}
    for i in range(N_CLUSTERS):
        cluster_labels[i] = label_cluster(centroids.iloc[i], feat_present)
    m["archetype"] = m["cluster_idx"].map(cluster_labels)

    if len(set(cluster_labels.values())) < N_CLUSTERS:
        counts = {}
        for i in range(N_CLUSTERS):
            base = cluster_labels[i]
            counts[base] = counts.get(base, 0) + 1
            if counts[base] > 1:
                cluster_labels[i] = f"{base} {counts[base]}"
        m["archetype"] = m["cluster_idx"].map(cluster_labels)

    print(f"\n=== cluster sizes ===")
    print(m["archetype"].value_counts().to_string())

    m_y1 = m[m["has_nba_y1"] & (m["nba_y1_gp"] >= 25)].copy()
    print(f"\n=== Y1 OUTCOMES PER ARCHETYPE (n + means) ===")
    summary_rows = []
    for arch, grp in m_y1.groupby("archetype"):
        row = {"archetype": arch, "n": len(grp)}
        for stat in Y1_OUTCOMES:
            if stat in grp.columns:
                row[stat] = grp[stat].mean()
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows).sort_values("n", ascending=False)
    print(summary.round(2).to_string(index=False))

    keep = ["nba_api_id", "draft_year", "player_name_raw", "cluster_idx", "archetype",
                  "combine_height_with_shoes_inches", "combine_wingspan_inches",
                  "combine_standing_reach_inches"] + Y1_OUTCOMES
    keep = [c for c in keep if c in m.columns]
    out = m[keep].copy()
    out.to_parquet(OUT_PQ, index=False)
    print(f"\nwrote: {OUT_PQ}")

    lines = ["# Rookie Decomp — Archetype Clusters",
                 "",
                 f"K-means K={N_CLUSTERS} on {len(feat_present)} features (combine + pre-NBA per-40).",
                 f"Window: 2014-2024 draft years.",
                 "",
                 "## Cluster sizes",
                 "",
                 m["archetype"].value_counts().to_markdown(),
                 "",
                 "## Y1 outcome means per archetype",
                 "",
                 summary.round(2).to_markdown(index=False),
                 "",
                 "## Sample players per cluster (top 5 by draft pick)",
                 ""]
    for arch in summary["archetype"].tolist():
        sub = m_y1[m_y1["archetype"] == arch].copy()
        sub["dp"] = pd.to_numeric(sub.get("draft_pick"), errors="coerce")
        top = sub.sort_values("dp").head(8)[["player_name_raw", "draft_year", "draft_pick",
                                                                        "combine_height_with_shoes_inches",
                                                                        "nba_y1_pts_per36", "nba_y1_reb_per36",
                                                                        "nba_y1_ast_per36"]]
        lines.append(f"### {arch}")
        lines.append("")
        lines.append(top.round(1).to_markdown(index=False))
        lines.append("")

    OUT_DOC.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote: {OUT_DOC}")


if __name__ == "__main__":
    main()
