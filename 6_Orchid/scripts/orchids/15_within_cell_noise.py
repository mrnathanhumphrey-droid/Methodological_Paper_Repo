"""Within-cell noise inspection — all 4 dig steps.

Step 1: Joint 7-D GMM per cell, k=1..4, BIC select.
Step 2: Hierarchical clustering on raw 26-trait z-matrix per cell.
Step 3: Histograms of x1 and x2 per cell (the two PCs most often Fragmenting).
Step 4: Characterize any cluster splits — which raw traits drive them.

Run on v2.0 K=8 partition; uses inherited rotation v11.

Output:
  results/within_cell/<cell>_gmm.parquet
  results/within_cell/<cell>_hier.parquet
  results/within_cell/<cell>_cluster_traits.parquet
  results/within_cell/histograms.png
  results/within_cell/summary.parquet
"""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from scipy import stats

ROOT = Path(r"D:/Phenotype_Research")
DERIVED = ROOT / "data/orchids/gymnadenia/derived"
RAW = ROOT / "data/orchids/gymnadenia/raw"
RESULTS = ROOT / "results"
OUT = RESULTS / "within_cell"
OUT.mkdir(parents=True, exist_ok=True)

OBS = [f"x{i+1}" for i in range(7)]
MORPH = ["PlantHeight_cm","InflorescenceLength_cm","NrFlowers"]
SCENT = ["Z3Hexen1Ol_ngPerL","Styrene_ngPerL","Heptanal_ngPerL","alphaPinene_ngPerL",
         "Benzaldehyde_ngPerL","Sabinene_ngPerL","betaPinene_ngPerL",
         "6Methyl5Hepten2One_ngPerL","Z3HexenylAcetate_ngPerL","HexylAcetate_ngPerL",
         "Limonene_ngPerL","BenzylAlcohol_ngPerL","Phenylacetaldehyde_ngPerL",
         "PhenylethylAlcohol_ngPerL","BenzylAcetate_ngPerL",
         "1Phenyl12Propanedione_ngPerL","Phenylethylacetate_ngPerL",
         "1Phenyl23Butanedione_ngPerL","Eugenol_ngPerL","MethylEugenol_ngPerL",
         "GeranylAcetone_ngPerL","Benzylbenzoate_ngPerL"]
COL = "ColourCode"
TRAITS = MORPH + SCENT + [COL]


def build_raw():
    df = pd.read_excel(RAW / "Data__SelectionAnalysis.xlsx", sheet_name="SelectionAnalysis")
    morph = df[MORPH].apply(pd.to_numeric, errors="coerce")
    scent = df[SCENT].apply(pd.to_numeric, errors="coerce")
    scent_log = np.log1p(scent.clip(lower=0))
    colour = pd.to_numeric(df[COL], errors="coerce")
    raw = pd.concat([df[["PlantID"]], morph, scent_log, colour.rename(COL)], axis=1)
    return raw


def gmm_bic(X, max_k=4):
    n = len(X)
    results = []
    for k in range(1, max_k+1):
        if n < k * 25:   # need at least 25 per component for stability
            results.append({"k": k, "bic": np.inf, "labels": None}); continue
        try:
            g = GaussianMixture(n_components=k, random_state=0,
                                covariance_type="full", n_init=5, reg_covar=1e-3).fit(X)
            results.append({"k": k, "bic": g.bic(X), "labels": g.predict(X),
                            "weights": g.weights_, "loglik": g.score(X)*n})
        except Exception as e:
            results.append({"k": k, "bic": np.inf, "labels": None, "error": str(e)})
    rdf = pd.DataFrame(results)
    rdf["delta_bic_vs_k1"] = rdf["bic"] - rdf.loc[rdf["k"]==1, "bic"].iloc[0]
    return rdf


def hier_explore(X, max_k=4):
    """Hierarchical clustering at k=2..max_k; report silhouette."""
    n = len(X)
    out = []
    for k in range(2, max_k+1):
        if n < k * 10: continue
        try:
            lab = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(X)
            sil = silhouette_score(X, lab) if k > 1 else float("nan")
            sizes = np.bincount(lab, minlength=k).tolist()
            out.append({"k": k, "silhouette": sil, "sizes": sizes,
                        "min_size": min(sizes), "labels": lab})
        except Exception as e:
            out.append({"k": k, "silhouette": np.nan, "error": str(e)})
    return pd.DataFrame(out)


def characterize_split(cell_id, labels, raw_z, traits):
    """For each cluster, mean raw trait values (z-standardized). Identify
    top-5 traits with largest between-cluster differences."""
    df = raw_z.copy()
    df["cluster"] = labels
    means = df.groupby("cluster")[traits].mean()
    # rank traits by total between-cluster spread (max - min mean over clusters)
    spread = (means.max() - means.min()).sort_values(ascending=False)
    top = spread.head(5)
    return means, top


def main():
    # load
    p0 = pd.read_parquet(DERIVED / "P0_partition_v20.parquet")
    scores = pd.read_parquet(DERIVED / "observable_scores_v11.parquet")
    raw = build_raw()

    df = p0.merge(scores, on="PlantID").merge(raw, on="PlantID")
    print(f"loaded {len(df)} plants × {len(df.columns)} cols")

    # global z-standardize raw traits (same fit-set logic as v1.1 rotation)
    fit_idx = df[TRAITS].dropna().index
    fit_mat = df.loc[fit_idx, TRAITS].to_numpy(dtype=float)
    col_mean = fit_mat.mean(axis=0)
    col_sd = fit_mat.std(axis=0, ddof=1)
    z_raw = df.copy()
    for i, t in enumerate(TRAITS):
        z_raw[t + "_z"] = (df[t] - col_mean[i]) / col_sd[i]
    Z_cols = [t + "_z" for t in TRAITS]

    cells = sorted(df["P0_cell"].unique())
    print(f"\ncells: {cells}\n")

    summary_rows = []
    fig, axes = plt.subplots(8, 2, figsize=(11, 22), sharex="col")
    for ax_row, cell in enumerate(cells):
        sub = df[df["P0_cell"] == cell]
        sub_z = z_raw[z_raw["P0_cell"] == cell].dropna(subset=Z_cols)
        n = len(sub)
        n_z = len(sub_z)
        pop = sub["Population"].iloc[0]
        region = sub["Region"].iloc[0]
        print(f"=== {cell}  pop={pop}  n={n}  n_with_all_traits={n_z} ===")

        # ---- STEP 1: joint 7-D GMM on (x1..x7) ----
        Xobs = sub[OBS].dropna().to_numpy()
        gmm_results = gmm_bic(Xobs, max_k=4)
        valid = gmm_results[gmm_results["bic"] != np.inf]
        best_k_gmm = int(valid.loc[valid["bic"].idxmin(), "k"]) if len(valid) else 1
        print(f"  joint 7-D GMM (n={len(Xobs)}):")
        for _, r in gmm_results.iterrows():
            mark = "  ←best" if r["k"] == best_k_gmm else ""
            print(f"    k={r['k']}  BIC={r['bic']:.1f}  ΔBIC_vs_k1={r['delta_bic_vs_k1']:+.1f}{mark}")
        gmm_results.drop(columns=["labels"]).to_parquet(OUT / f"{cell}_gmm.parquet", index=False)

        # ---- STEP 2: hierarchical clustering on 26 raw z-traits ----
        if len(sub_z) >= 20:
            Xraw_z = sub_z[Z_cols].to_numpy()
            hier_results = hier_explore(Xraw_z, max_k=4)
            print(f"  hierarchical clustering on 26 raw z-traits (n={n_z}):")
            for _, r in hier_results.iterrows():
                print(f"    k={r['k']}  silhouette={r['silhouette']:.3f}  sizes={r['sizes']}")
            valid_hier = hier_results[hier_results["silhouette"].notna()]
            best_k_hier = int(valid_hier.loc[valid_hier["silhouette"].idxmax(), "k"]) if len(valid_hier) else 1
            hier_to_save = hier_results.copy()
            hier_to_save["labels"] = hier_to_save["labels"].apply(lambda x: x.tolist() if x is not None else None)
            hier_to_save.drop(columns=["labels"]).to_parquet(OUT / f"{cell}_hier.parquet", index=False)
        else:
            best_k_hier = 1
            hier_results = pd.DataFrame()

        # ---- STEP 4: characterize the best non-trivial split (if any) ----
        characterized = False
        if best_k_gmm > 1:
            best_gmm_labels = gmm_results.loc[gmm_results["k"] == best_k_gmm, "labels"].iloc[0]
            obs_idx = sub[OBS].dropna().index
            cluster_df = sub.loc[obs_idx, ["PlantID","Year"]].copy()
            cluster_df["gmm_cluster"] = best_gmm_labels
            # join raw z-traits
            gmm_means = (cluster_df.merge(z_raw[["PlantID"] + Z_cols], on="PlantID")
                                   .groupby("gmm_cluster")[Z_cols].mean())
            spread = (gmm_means.max() - gmm_means.min()).sort_values(ascending=False)
            print(f"  GMM k={best_k_gmm} top-5 distinguishing traits (between-cluster z-mean spread):")
            for trait, val in spread.head(5).items():
                print(f"    {trait[:-2]:30s}  spread={val:+.3f}")
            characterized = True
            cluster_df.to_parquet(OUT / f"{cell}_gmm_labels.parquet", index=False)
            gmm_means.to_parquet(OUT / f"{cell}_gmm_cluster_traits.parquet")

        if best_k_hier > 1 and len(hier_results) > 0:
            best_hier_labels = hier_results.loc[hier_results["k"] == best_k_hier, "labels"].iloc[0]
            cluster_df_h = sub_z.copy()
            cluster_df_h["hier_cluster"] = best_hier_labels
            hier_means = cluster_df_h.groupby("hier_cluster")[Z_cols].mean()
            spread_h = (hier_means.max() - hier_means.min()).sort_values(ascending=False)
            print(f"  hier k={best_k_hier} silhouette={hier_results.loc[hier_results['k']==best_k_hier,'silhouette'].iloc[0]:.3f} top-5 traits:")
            for trait, val in spread_h.head(5).items():
                print(f"    {trait[:-2]:30s}  spread={val:+.3f}")
            hier_means.to_parquet(OUT / f"{cell}_hier_cluster_traits.parquet")
            characterized = True

        # ---- STEP 3: visualize x1 + x2 ----
        for col_idx, obs in enumerate(["x1","x2"]):
            ax = axes[ax_row, col_idx]
            for year, color in [(2010, "tab:blue"), (2011, "tab:orange")]:
                vals = sub[sub["Year"] == year][obs].dropna()
                if len(vals) > 0:
                    ax.hist(vals, bins=20, alpha=0.5, color=color,
                             label=f"{year} (n={len(vals)})", density=False)
            ax.set_title(f"{cell}  {obs}  ", fontsize=9)
            if ax_row == 7:
                ax.set_xlabel(obs, fontsize=8)
            ax.tick_params(labelsize=7)
            if col_idx == 0:
                ax.set_ylabel(f"{cell}", fontsize=8)
            if ax_row == 0 and col_idx == 1:
                ax.legend(fontsize=7, loc="upper right")

        summary_rows.append({
            "cell": cell, "population": pop, "region": region, "n_plants": n,
            "best_k_gmm_7d": best_k_gmm,
            "best_k_hier_26raw": best_k_hier,
            "delta_bic_gmm_k2_vs_k1": float(gmm_results.loc[gmm_results["k"]==2, "delta_bic_vs_k1"].iloc[0]) if 2 in gmm_results["k"].values else None,
            "best_silhouette_hier": float(hier_results.loc[hier_results["k"]==best_k_hier, "silhouette"].iloc[0]) if best_k_hier > 1 else None,
            "non_trivial_split": characterized,
        })
        print()

    plt.tight_layout()
    plt.savefig(OUT / "histograms_x1_x2.png", dpi=110)
    print(f"\nWrote {OUT / 'histograms_x1_x2.png'}")

    summary = pd.DataFrame(summary_rows)
    summary.to_parquet(OUT / "summary.parquet", index=False)
    print(f"\n=== SUMMARY ===")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
