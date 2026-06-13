"""
Quantifies the pivot-dimensions matrix from RIGHT_UNIT_TABLE_2026_05_30:
  - per-pivot frequency / rarity
  - pairwise pivot co-occurrence
  - paper-paper Jaccard similarity + hierarchical clustering
  - rarity-weighted (inverse-frequency) paper novelty score
  - pairwise mutual information between pivots
Saves to analysis/meta_pivot_quantification_2026_05_30.json
"""
from __future__ import annotations
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster

PAPERS = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
PIVOTS = ["a_finer", "b_downstream", "c_typed", "d_relational", "e_mediator"]
M = np.array([
    [0, 0, 1, 1, 0],  # P1 exec aggrandizement
    [1, 0, 1, 0, 0],  # P2 disaster regimes
    [1, 0, 0, 1, 0],  # P3 strife epicenter
    [1, 0, 1, 1, 0],  # P4 conflict typology
    [0, 0, 1, 1, 0],  # P5 democratic resilience
    [0, 0, 1, 1, 0],  # P6 methodology
    [1, 1, 0, 0, 1],  # P7 SDP / homelessness
    [1, 1, 0, 1, 1],  # P8 compound-crisis coupling
])


def MI(a, b):
    n = len(a)
    counts = np.zeros((2, 2))
    for ai, bi in zip(a, b):
        counts[int(ai), int(bi)] += 1
    p = counts / n
    px = p.sum(axis=1); py = p.sum(axis=0)
    mi = 0.0
    for i in range(2):
        for j in range(2):
            if p[i, j] > 0 and px[i] > 0 and py[j] > 0:
                mi += p[i, j] * np.log2(p[i, j] / (px[i] * py[j]))
    return round(float(mi), 3)


def main():
    n_papers = len(PAPERS)
    # 1. column (pivot) frequencies
    col_freq = M.sum(axis=0)
    print("Pivot frequencies (out of 8 papers):")
    for n, f in zip(PIVOTS, col_freq):
        print(f"  {n}: {int(f)}/8 = {f/n_papers:.2f}")

    # 2. row (paper) pivot counts
    row_counts = M.sum(axis=1)
    print("\nPivots per paper:")
    for p, c in zip(PAPERS, row_counts):
        print(f"  {p}: {int(c)}")

    # 3. pairwise pivot co-occurrence
    print("\nPivot pairwise co-occurrence (count of papers with BOTH):")
    cooc = M.T @ M
    for i in range(5):
        for j in range(i + 1, 5):
            print(f"  {PIVOTS[i]} & {PIVOTS[j]}: {cooc[i, j]}")

    # 4. paper Jaccard similarity + clustering
    jac_dist = pdist(M, metric="jaccard")
    sim_matrix = 1 - squareform(jac_dist)
    np.fill_diagonal(sim_matrix, 1.0)
    df_sim = pd.DataFrame(sim_matrix.round(3), index=PAPERS, columns=PAPERS)
    print("\nPaper Jaccard similarity matrix:")
    print(df_sim.to_string())

    Z = linkage(M, method="average", metric="jaccard")
    print("\nHierarchical clustering (linkage matrix):")
    print(Z.round(3))
    clusters_3 = fcluster(Z, t=3, criterion="maxclust")
    clusters_2 = fcluster(Z, t=2, criterion="maxclust")
    print(f"\nk=3 clusters: {dict(zip(PAPERS, clusters_3.tolist()))}")
    print(f"k=2 clusters: {dict(zip(PAPERS, clusters_2.tolist()))}")

    # 5. rarity-weighted novelty score per paper
    inv_freq = n_papers / col_freq.astype(float)
    print("\nInverse-frequency weights per pivot:")
    for n, w in zip(PIVOTS, inv_freq):
        print(f"  {n}: {w:.2f}")
    paper_novelty = M @ inv_freq
    print("\nPaper rarity-weighted novelty score (Σ inverse-frequency):")
    for p, s in sorted(zip(PAPERS, paper_novelty), key=lambda x: -x[1]):
        print(f"  {p}: {s:.2f}")

    # 6. pairwise mutual information
    print("\nMutual information between pivot pairs (bits):")
    mi_matrix = np.zeros((5, 5))
    for i in range(5):
        for j in range(5):
            mi_matrix[i, j] = MI(M[:, i], M[:, j])
    df_mi = pd.DataFrame(mi_matrix, index=PIVOTS, columns=PIVOTS)
    print(df_mi.to_string())

    out = {
        "matrix": M.tolist(),
        "papers": PAPERS,
        "pivots": PIVOTS,
        "pivot_frequency": col_freq.tolist(),
        "paper_pivot_count": row_counts.tolist(),
        "cooccurrence": cooc.tolist(),
        "jaccard_similarity": df_sim.values.tolist(),
        "clusters_k3": dict(zip(PAPERS, clusters_3.tolist())),
        "clusters_k2": dict(zip(PAPERS, clusters_2.tolist())),
        "inverse_freq_weights": inv_freq.tolist(),
        "paper_novelty_score": paper_novelty.tolist(),
        "mutual_information": mi_matrix.tolist(),
    }
    from pathlib import Path
    p = Path("D:/IDP/analysis/meta_pivot_quantification_2026_05_30.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved: {p}")


if __name__ == "__main__":
    main()
