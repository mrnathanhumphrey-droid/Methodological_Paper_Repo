"""
RMD-SRC Step 1 — moment computation per (cell, observable) for Gymnadenia.

Per locked PRE_REG_v1.0_RMD_SRC_gymnadenia.md §3.2 + §2.5:
  For each (cell c, observable xⱼ): compute μ_{c,j}, σ²_{c,j}, n_{c,j}.
  Observables = published PC1-PC7 from SelectionAnalysis (d = 7).

ℙ₀ partition is locked at K = 12 (P0_partition.parquet, sha256 in P0_hash.txt).
Each cell already encodes (region, pop, year); the "time bin t" axis collapses
inside the cell label. The Step-2 trajectory-rule interpretation under this
encoding is the next decision after Step 1 — flagged for diagnostic
amendment at Step 2 boundary.

No regime classification or response-function fit in this step.

Output:
  results/moment_trajectories.parquet
"""

from pathlib import Path
import hashlib
import datetime
import pandas as pd

ROOT = Path(r"D:/Phenotype_Research")
RAW = ROOT / "data/orchids/gymnadenia/raw"
DERIVED = ROOT / "data/orchids/gymnadenia/derived"
RESULTS = ROOT / "results"
PREREG = ROOT / "prereg"

SELECTION_XLSX = RAW / "Data__SelectionAnalysis.xlsx"
PARTITION_PARQUET = DERIVED / "P0_partition.parquet"
OUT_PARQUET = RESULTS / "moment_trajectories.parquet"

OBSERVABLES = ["PC1", "PC2", "PC3", "PC4", "PC5", "PC6", "PC7"]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)

    # --- hash check against locked partition ---
    p0_sha = sha256_file(PARTITION_PARQUET)
    locked_hash_line = next(
        (l for l in (PREREG / "P0_hash.txt").read_text(encoding="utf-8").splitlines()
         if "P0_partition.parquet sha256" in l), "")
    locked_sha = locked_hash_line.split("=")[1].strip() if "=" in locked_hash_line else ""
    if p0_sha != locked_sha:
        raise RuntimeError(f"P0 partition hash mismatch.\n"
                           f"  computed = {p0_sha}\n"
                           f"  locked   = {locked_sha}")
    print(f"P0 partition hash verified: {p0_sha[:16]}...")

    # --- load partition + phenotype ---
    part = pd.read_parquet(PARTITION_PARQUET)
    pheno = pd.read_excel(SELECTION_XLSX, sheet_name="SelectionAnalysis")
    keep = ["PlantID"] + OBSERVABLES
    pheno = pheno[keep].copy()

    df = part.merge(pheno, on="PlantID", how="left", validate="one_to_one")
    if df[OBSERVABLES].isna().any().any():
        n_na = df[OBSERVABLES].isna().sum().sum()
        # SelectionAnalysis has 'NA' string values in some PC cols -- coerce
        for c in OBSERVABLES:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        n_na2 = df[OBSERVABLES].isna().sum().sum()
        print(f"  observable NA values: raw={n_na}, after numeric coerce={n_na2}")

    # --- compute moments per (cell, observable) ---
    rows = []
    for cell, sub in df.groupby("P0_cell"):
        # Region/Pop/Year recoverable for audit
        region = sub["Region"].iloc[0]
        year = int(sub["Year"].iloc[0])
        # cell may include >1 source population (e.g. M_Muen_2010 = Schatzalp + Muenstertal collapse)
        pops = sorted(sub["Population"].unique())
        n_cell = len(sub)
        for j in OBSERVABLES:
            x = sub[j].dropna()
            n_j = len(x)
            rows.append({
                "P0_cell": cell,
                "region": region,
                "year": year,
                "source_pops": "|".join(pops),
                "observable": j,
                "n_cell": n_cell,
                "n_obs": n_j,
                "mu": float(x.mean()) if n_j > 0 else None,
                "var": float(x.var(ddof=1)) if n_j > 1 else None,
                "sd": float(x.std(ddof=1)) if n_j > 1 else None,
                "min": float(x.min()) if n_j > 0 else None,
                "max": float(x.max()) if n_j > 0 else None,
            })

    moments = pd.DataFrame(rows)
    moments.to_parquet(OUT_PARQUET, index=False)
    print(f"\nWrote {OUT_PARQUET}  ({len(moments)} rows)")
    print(f"  cells = {moments['P0_cell'].nunique()}")
    print(f"  observables = {moments['observable'].nunique()}")
    print(f"  total plant-observable pairs: {int(moments['n_obs'].sum())}")

    # --- summary print ---
    print("\n=== μ per (cell, observable) ===")
    wide_mu = moments.pivot(index="P0_cell", columns="observable", values="mu")
    print(wide_mu.round(3).to_string())
    print("\n=== σ² per (cell, observable) ===")
    wide_var = moments.pivot(index="P0_cell", columns="observable", values="var")
    print(wide_var.round(3).to_string())

    # --- log + hash output ---
    sha = sha256_file(OUT_PARQUET)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log_path = PREREG / "step1_log.txt"
    log_path.write_text(
        f"# RMD-SRC Gymnadenia Step 1 -- moment trajectories\n"
        f"# Generated: {ts}\n"
        f"# Per PRE_REG_v1.0 §3.2 + §2.5 (d=7 published PCs)\n\n"
        f"moment_trajectories.parquet sha256 = {sha}\n"
        f"rows                                = {len(moments)}\n"
        f"cells                               = {moments['P0_cell'].nunique()}\n"
        f"observables                         = {moments['observable'].nunique()}\n"
        f"plant-observable pairs              = {int(moments['n_obs'].sum())}\n"
        f"P0_partition.parquet sha256 (input) = {p0_sha}\n",
        encoding="utf-8",
    )
    print(f"\nWrote {log_path}")


if __name__ == "__main__":
    main()
