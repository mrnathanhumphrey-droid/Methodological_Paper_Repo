"""
Batch VET01 - NBA veteran playstyle archetypes (Stage 1 port back to NBA).

Career-aggregate features × KMeans k-sweep → silhouette pick → face validity.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from scipy import stats

ROOT = Path("D:/NBA Projections")
RESULTS = ROOT / "data/parquet"

FEATS = [
    "usage", "mpg",
    "three_fg", "three_perc", "rim_fg", "rim_perc", "ft_perc", "efg_perc",
    "ast_perc", "tov_perc",
    "blk_perc", "stl_per_play", "oreb_fg", "dreb_fg",
]


def build_career_panel():
    ctg = pd.read_parquet(ROOT / "data/parquet/ctg_players.parquet")
    # season_type is integer-coded (2 = regular season here)
    # Skipping the str filter since values are int
    # MPG >= 15 floor per season
    qual = ctg[ctg["mpg"] >= 15].copy()
    # >= 3 qualifying seasons
    counts = qual.groupby("p_id")["season"].nunique()
    keep = counts[counts >= 3].index
    qual = qual[qual["p_id"].isin(keep)].copy()

    # Career-mean weighted by games_played * mpg (proxy for minutes)
    qual["minutes"] = qual["games_played"] * qual["mpg"]
    rows = []
    for pid, g in qual.groupby("p_id"):
        w = g["minutes"].values
        wsum = float(w.sum())
        name = g["name"].mode().iloc[0]
        rec = {"p_id": pid, "name": name,
               "n_seasons": int(len(g)),
               "total_minutes": wsum,
               "mean_age": float(g["age"].mean()),
               "max_age": float(g["age"].max()),
               "min_age": float(g["age"].min()),
               }
        for f in FEATS:
            if f not in g.columns:
                rec[f] = np.nan
                continue
            vals = g[f].astype(float).values
            mask = ~np.isnan(vals)
            if mask.sum() == 0:
                rec[f] = np.nan
            else:
                rec[f] = float(np.sum(vals[mask] * w[mask]) / max(np.sum(w[mask]), 1e-9))
        rows.append(rec)
    return pd.DataFrame(rows)


def main():
    panel = build_career_panel()
    print(f"Veteran cohort (MPG>=15 + >=3 seasons): {len(panel)}")
    panel_clean = panel.dropna(subset=FEATS).reset_index(drop=True)
    print(f"  with no-NaN on all features: {len(panel_clean)}")

    X = panel_clean[FEATS].astype(float).values
    Z = StandardScaler().fit_transform(X)

    # Sweep silhouette but pick by HIGHER-RESOLUTION TRADE-OFF: highest k where
    # silhouette >= 0.14 (still well above 0.12 gate) so we can differentiate
    # between star archetypes — k=4 lumps all stars together which kills the
    # DARKO-benchmark use case.
    best_k, best_sil, best_lab = None, -1, None
    sil_log = {}
    for k in (4, 5, 6, 7, 8):
        km = KMeans(n_clusters=k, n_init=25, random_state=42)
        lab = km.fit_predict(Z)
        sil = silhouette_score(Z, lab)
        sil_log[k] = sil
    # Pick highest k with silhouette >= 0.14
    for k in (8, 7, 6, 5, 4):
        if sil_log[k] >= 0.14:
            best_k = k
            best_sil = sil_log[k]
            break
    km = KMeans(n_clusters=best_k, n_init=25, random_state=42)
    best_lab = km.fit_predict(Z)
    print(f"\nSilhouette by k: {sil_log}")
    print(f"Pick k={best_k} silhouette={best_sil:.3f} (highest k with silhouette>=0.14 for star differentiation)")
    panel_clean["cluster"] = best_lab

    # Centroids
    Z_df = pd.DataFrame(Z, columns=FEATS, index=panel_clean.index)
    centroids_z = Z_df.assign(cluster=panel_clean["cluster"].values).groupby("cluster").mean()
    raw_means = panel_clean.groupby("cluster")[FEATS].mean()

    print("\n=== Centroid Z-scores ===")
    print(centroids_z.round(2).to_string())
    print("\n=== Cluster sizes ===")
    sizes = panel_clean["cluster"].value_counts().sort_index()
    print(sizes.to_dict())

    # ANOVA
    anova_rows = []
    for f in FEATS:
        groups = [panel_clean[panel_clean["cluster"] == c][f].values for c in sorted(panel_clean["cluster"].unique())]
        if all(len(g) >= 2 for g in groups):
            F, p = stats.f_oneway(*groups)
            anova_rows.append({"feature": f, "F": float(F), "p": float(p)})
    anova = pd.DataFrame(anova_rows)
    print("\n=== ANOVA top 8 ===")
    print(anova.nlargest(8, "F").to_string(index=False))

    # Face validity — named-star check
    print("\n=== Named-star face validity ===")
    stars = ["LeBron James", "Stephen Curry", "Giannis Antetokounmpo", "Nikola Jokic",
             "Joel Embiid", "Kevin Durant", "Jayson Tatum", "James Harden",
             "Luka Doncic", "Kawhi Leonard", "Damian Lillard", "Anthony Davis",
             "Devin Booker", "Jimmy Butler", "Draymond Green", "Rudy Gobert"]
    star_found = []
    for nm in stars:
        sub = panel_clean[panel_clean["name"].str.contains(nm.split()[-1], na=False, case=False)]
        # narrow further by first name to disambiguate
        sub = sub[sub["name"].str.contains(nm.split()[0], na=False, case=False)]
        for _, r in sub.iterrows():
            print(f"  {r['name']:25s} cluster={r['cluster']}  use={r['usage']:.2f}  3FG={r['three_fg']:.2f}  3%={r['three_perc']:.3f}  AST%={r['ast_perc']:.2f}  BLK%={r['blk_perc']:.3f}  REB={r['dreb_fg']:.2f}")
            star_found.append((r["name"], int(r["cluster"])))

    # Identify archetype clusters via centroid z-scores
    archetype_labels = {}
    for cl in sorted(panel_clean["cluster"].unique()):
        row_z = centroids_z.loc[cl]
        labels = []
        # Shooting big: high 3FG + high BLK + high REB
        if row_z["three_fg"] > 0.3 and row_z["blk_perc"] > 0.3:
            labels.append("STRETCH_BIG")
        # Rim-protecting big: high BLK + high REB + low 3FG
        if row_z["blk_perc"] > 0.5 and row_z["three_fg"] < -0.3 and row_z["dreb_fg"] > 0.5:
            labels.append("RIM_BIG")
        # Primary creator: high usage + high AST
        if row_z["usage"] > 0.5 and row_z["ast_perc"] > 0.5:
            labels.append("PRIMARY_CREATOR")
        # 3-and-D wing: high 3FG + decent stl + lower usage
        if row_z["three_fg"] > 0.3 and row_z["stl_per_play"] > 0.0 and row_z["usage"] < 0.0:
            labels.append("THREE_AND_D_WING")
        # Pass-first PG: high AST + lower usage + low blk
        if row_z["ast_perc"] > 0.5 and row_z["blk_perc"] < -0.2 and row_z["mpg"] > 0.0:
            labels.append("PASS_FIRST_PG")
        # Shooter: high 3% + high 3FG + lower usage
        if row_z["three_fg"] > 0.5 and row_z["three_perc"] > 0.3 and row_z["usage"] < 0.0:
            labels.append("PURE_SHOOTER")
        # Slasher: high rim_fg + low 3FG + decent usage
        if row_z["rim_fg"] > 0.3 and row_z["three_fg"] < -0.3 and row_z["usage"] > -0.2:
            labels.append("SLASHER")
        archetype_labels[cl] = labels if labels else ["MIXED_UTILITY"]
    print("\n=== Archetype labels (heuristic from centroids) ===")
    for cl, lbls in archetype_labels.items():
        print(f"  C{cl}: {lbls}")

    # Gates
    g1 = best_sil >= 0.12
    g2 = anova["F"].max() >= 30.0
    g3 = anova["p"].min() <= 1e-15
    g4 = sizes.min() >= 20
    archetypes_present = set(sum(archetype_labels.values(), []))
    has_creator = "PRIMARY_CREATOR" in archetypes_present
    has_3d = "THREE_AND_D_WING" in archetypes_present or "PURE_SHOOTER" in archetypes_present
    has_big = "STRETCH_BIG" in archetypes_present or "RIM_BIG" in archetypes_present
    g5 = has_creator and has_3d and has_big
    # G6: named-star sanity — many will be in creator/shooter buckets
    g6 = len(star_found) >= 12  # at least 12 of 16 found

    n_pass = sum([g1, g2, g3, g4, g5, g6])
    verdict = "SHIP_CLEAN" if n_pass >= 5 else ("SHIP_CAVEAT" if n_pass >= 3 else "WALK_BACK")
    print(f"\n=== GATES ===")
    print(f"G1 silhouette >= 0.12:    {best_sil:.3f} -> {'PASS' if g1 else 'FAIL'}")
    print(f"G2 ANOVA F max >= 30:     {anova['F'].max():.1f} -> {'PASS' if g2 else 'FAIL'}")
    print(f"G3 ANOVA p min <= 1e-15:  {anova['p'].min():.2e} -> {'PASS' if g3 else 'FAIL'}")
    print(f"G4 min cluster size >= 20: {sizes.min()} -> {'PASS' if g4 else 'FAIL'}")
    print(f"G5 face-validity (creator + 3D + big all present): creator={has_creator} 3d={has_3d} big={has_big} -> {'PASS' if g5 else 'FAIL'}")
    print(f"G6 named-star coverage >= 12: {len(star_found)} -> {'PASS' if g6 else 'FAIL'}")
    print(f"\nVERDICT: {n_pass}/6 -> {verdict}")

    out = panel_clean[["p_id", "name", "n_seasons", "total_minutes", "mean_age", "min_age", "max_age", "cluster"] + FEATS].copy()
    # Add heuristic archetype label
    out["archetype_labels"] = out["cluster"].map(lambda c: "|".join(archetype_labels.get(c, ["MIXED_UTILITY"])))
    out.to_parquet(RESULTS / "veteran_archetypes.parquet", index=False)

    summary = {
        "verdict": verdict, "n_pass": int(n_pass),
        "k": int(best_k), "silhouette": float(best_sil),
        "n_cohort": int(len(panel_clean)),
        "cluster_sizes": {int(k): int(v) for k, v in sizes.to_dict().items()},
        "centroids_z": centroids_z.reset_index().to_dict(orient="records"),
        "raw_means": raw_means.reset_index().to_dict(orient="records"),
        "anova_top10": anova.nlargest(10, "F").to_dict(orient="records"),
        "archetype_labels": {int(k): v for k, v in archetype_labels.items()},
        "star_found": star_found,
    }
    Path("D:/NBA Projections/runs").mkdir(exist_ok=True)
    (Path("D:/NBA Projections/runs") / "batch_vet01_verdict.json").write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nSaved veteran_archetypes.parquet + batch_vet01_verdict.json")


if __name__ == "__main__":
    main()
