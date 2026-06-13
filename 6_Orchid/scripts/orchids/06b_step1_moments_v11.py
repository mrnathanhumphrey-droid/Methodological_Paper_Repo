"""
RMD-SRC Step 1 -- v1.1 amendment.

Re-derives the d=7 observable rotation on the pooled cohort's
z-standardized raw trait matrix per PRE_REG_v1.1 §2.5, then computes
moments per (cell, observable) per locked v1.0 §3.2.

Outputs:
  data/orchids/gymnadenia/derived/observable_rotation_W_v11.parquet
  data/orchids/gymnadenia/derived/observable_scores_v11.parquet
  results/moment_trajectories.parquet            (v1.1 overwrite)
"""

from pathlib import Path
import hashlib
import datetime
import numpy as np
import pandas as pd

ROOT = Path(r"D:/Phenotype_Research")
RAW = ROOT / "data/orchids/gymnadenia/raw"
DERIVED = ROOT / "data/orchids/gymnadenia/derived"
RESULTS = ROOT / "results"
PREREG = ROOT / "prereg"

SELECTION_XLSX = RAW / "Data__SelectionAnalysis.xlsx"
PARTITION_PARQUET = DERIVED / "P0_partition.parquet"
W_PARQUET = DERIVED / "observable_rotation_W_v11.parquet"
SCORES_PARQUET = DERIVED / "observable_scores_v11.parquet"
OUT_PARQUET = RESULTS / "moment_trajectories.parquet"

MORPHOLOGY_TRAITS = ["PlantHeight_cm", "InflorescenceLength_cm", "NrFlowers"]
SCENT_TRAITS = [
    "Z3Hexen1Ol_ngPerL", "Styrene_ngPerL", "Heptanal_ngPerL",
    "alphaPinene_ngPerL", "Benzaldehyde_ngPerL", "Sabinene_ngPerL",
    "betaPinene_ngPerL", "6Methyl5Hepten2One_ngPerL",
    "Z3HexenylAcetate_ngPerL", "HexylAcetate_ngPerL", "Limonene_ngPerL",
    "BenzylAlcohol_ngPerL", "Phenylacetaldehyde_ngPerL",
    "PhenylethylAlcohol_ngPerL", "BenzylAcetate_ngPerL",
    "1Phenyl12Propanedione_ngPerL", "Phenylethylacetate_ngPerL",
    "1Phenyl23Butanedione_ngPerL", "Eugenol_ngPerL", "MethylEugenol_ngPerL",
    "GeranylAcetone_ngPerL", "Benzylbenzoate_ngPerL",
]
COLOUR_TRAIT = "ColourCode"
D = 7


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    # --- partition hash check ---
    p0_sha = sha256_file(PARTITION_PARQUET)
    locked = next(
        (l for l in (PREREG / "P0_hash.txt").read_text(encoding="utf-8").splitlines()
         if "P0_partition.parquet sha256" in l), "")
    if p0_sha != locked.split("=")[1].strip():
        raise RuntimeError("P0 hash mismatch")
    print(f"P0 hash verified: {p0_sha[:16]}...")

    # --- load ---
    part = pd.read_parquet(PARTITION_PARQUET)
    df = pd.read_excel(SELECTION_XLSX, sheet_name="SelectionAnalysis")
    print(f"loaded {len(df)} plants")

    # --- build raw trait matrix ---
    morph = df[MORPHOLOGY_TRAITS].apply(pd.to_numeric, errors="coerce")
    scent = df[SCENT_TRAITS].apply(pd.to_numeric, errors="coerce")
    scent_log = np.log1p(scent.clip(lower=0))
    colour = pd.to_numeric(df[COLOUR_TRAIT], errors="coerce")

    raw = pd.concat([morph, scent_log, colour.rename(COLOUR_TRAIT)], axis=1)
    trait_cols = list(raw.columns)
    print(f"raw trait matrix: {raw.shape}")

    # --- handle colour NA -- drop from rotation fit, impute via partial projection ---
    colour_na = raw[COLOUR_TRAIT].isna()
    print(f"  ColourCode NA: {colour_na.sum()} plants")

    # any remaining NA in scent/morph?
    other_na = raw.drop(columns=[COLOUR_TRAIT]).isna().any(axis=1)
    print(f"  other-trait NA: {other_na.sum()} plants")
    rotation_keep = ~(colour_na | other_na)
    n_fit = int(rotation_keep.sum())
    print(f"  rotation fit on n = {n_fit} plants (complete cases)")

    # --- z-standardize on pooled cohort (rotation-fit subset) ---
    fit_mat = raw.loc[rotation_keep].to_numpy(dtype=float)
    col_mean = fit_mat.mean(axis=0)
    col_sd = fit_mat.std(axis=0, ddof=1)
    Z_fit = (fit_mat - col_mean) / col_sd
    print(f"  per-trait sd on fit set (showing 5): {col_sd[:5].round(3)}")

    # --- PCA ---
    U, S, Vt = np.linalg.svd(Z_fit, full_matrices=False)
    explained = (S ** 2) / (S ** 2).sum()
    cum_explained = np.cumsum(explained)
    W = Vt[:D].T  # shape (26, 7)
    print(f"\nVariance explained by first {D} PCs (cumulative):")
    for k in range(D):
        print(f"  PC{k+1}: {explained[k]*100:5.2f}%  (cum {cum_explained[k]*100:5.2f}%)")
    print(f"  total {D} PCs cumulative: {cum_explained[D-1]*100:.2f}%")

    # --- project all 1028 plants (impute via partial projection for NA-colour) ---
    # For complete cases: x_i = (z_i) @ W
    # For ColourCode-NA: drop ColourCode column from raw + standardize using saved col_mean/sd
    # then project via the rotation's first 25 rows.
    full = raw.copy()
    # use saved mean/sd from fit; for NA-colour rows we'll skip the colour col in projection
    scores = np.full((len(full), D), np.nan)

    complete_idx = full.dropna().index
    Zc = (full.loc[complete_idx].to_numpy(dtype=float) - col_mean) / col_sd
    scores[complete_idx] = Zc @ W

    partial_idx = full.index.difference(complete_idx)
    if len(partial_idx) > 0:
        # restrict to non-colour cols
        non_colour_cols = [i for i, c in enumerate(trait_cols) if c != COLOUR_TRAIT]
        partial = full.loc[partial_idx].drop(columns=[COLOUR_TRAIT])
        partial_complete = partial.dropna()
        if len(partial_complete) > 0:
            Zp = ((partial_complete.to_numpy(dtype=float)
                   - col_mean[non_colour_cols])
                  / col_sd[non_colour_cols])
            W_nc = W[non_colour_cols]      # (25, 7)
            # least-squares projection: minimize ||z - (s @ W^T)||^2 over s
            # s = z @ pinv(W^T)
            s_partial = Zp @ np.linalg.pinv(W_nc.T)
            scores[partial_complete.index] = s_partial
        print(f"  projected {len(partial_idx)} ColourCode-NA plants via partial fit")

    n_scored = (~np.isnan(scores).any(axis=1)).sum()
    print(f"  fully scored: {n_scored}/{len(full)} plants")

    score_df = pd.DataFrame(scores, columns=[f"x{i+1}" for i in range(D)],
                            index=df.index)
    score_df.insert(0, "PlantID", df["PlantID"].values)
    score_df.to_parquet(SCORES_PARQUET, index=False)
    print(f"  wrote {SCORES_PARQUET}")

    # --- save rotation ---
    W_df = pd.DataFrame(W, index=trait_cols,
                        columns=[f"x{i+1}" for i in range(D)])
    W_df.index.name = "trait"
    W_df.to_parquet(W_PARQUET)
    print(f"  wrote {W_PARQUET}")

    # --- moments per (cell, observable) ---
    obs_cols = [f"x{i+1}" for i in range(D)]
    full_df = part.merge(score_df, on="PlantID", how="left",
                         validate="one_to_one")

    rows = []
    for cell, sub in full_df.groupby("P0_cell"):
        region = sub["Region"].iloc[0]
        year = int(sub["Year"].iloc[0])
        pops = sorted(sub["Population"].unique())
        n_cell = len(sub)
        for j in obs_cols:
            x = sub[j].dropna()
            n_j = len(x)
            rows.append({
                "P0_cell": cell, "region": region, "year": year,
                "source_pops": "|".join(pops), "observable": j,
                "n_cell": n_cell, "n_obs": n_j,
                "mu":  float(x.mean()) if n_j > 0 else None,
                "var": float(x.var(ddof=1)) if n_j > 1 else None,
                "sd":  float(x.std(ddof=1)) if n_j > 1 else None,
                "min": float(x.min()) if n_j > 0 else None,
                "max": float(x.max()) if n_j > 0 else None,
            })
    moments = pd.DataFrame(rows)
    moments.to_parquet(OUT_PARQUET, index=False)
    print(f"\nWrote {OUT_PARQUET} ({len(moments)} rows)")

    # --- summary ---
    print("\n=== μ per (cell, observable) ===")
    mu_w = moments.pivot(index="P0_cell", columns="observable", values="mu")
    print(mu_w.round(3).to_string())
    print("\n=== σ per (cell, observable) ===")
    sd_w = moments.pivot(index="P0_cell", columns="observable", values="sd")
    print(sd_w.round(3).to_string())

    # --- region-level summary
    print("\n=== μ pooled within region ===")
    reg_mu = (full_df.groupby("Region")[obs_cols].mean()).round(3)
    print(reg_mu.to_string())

    # --- hash log ---
    sha_m = sha256_file(OUT_PARQUET)
    sha_w = sha256_file(W_PARQUET)
    sha_s = sha256_file(SCORES_PARQUET)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log_lines = [
        "",
        "# RMD-SRC Gymnadenia Step 1 v1.1 -- re-derived observables",
        f"# Generated: {ts}",
        f"# Per PRE_REG_v1.1_amendment.md §2.5",
        "",
        f"moment_trajectories.parquet sha256 (v1.1)   = {sha_m}",
        f"observable_rotation_W_v11.parquet sha256    = {sha_w}",
        f"observable_scores_v11.parquet sha256        = {sha_s}",
        f"raw trait dim                                = {len(trait_cols)}",
        f"rotation fit n                               = {n_fit}",
        f"d (PCs retained)                             = {D}",
        f"cumulative variance explained by {D} PCs     = {cum_explained[D-1]*100:.2f}%",
    ]
    log_path = PREREG / "step1_log.txt"
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    log_path.write_text(existing + "\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"\nAppended hashes to {log_path}")


if __name__ == "__main__":
    main()
