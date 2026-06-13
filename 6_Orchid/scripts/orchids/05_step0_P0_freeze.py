"""
RMD-SRC Step 0 — ℙ₀ partition freeze for Gymnadenia odoratissima.

Per locked PRE_REG_v1.0_RMD_SRC_gymnadenia.md §2.4:
  ℙ₀_raw cell := (Region, Population, Year)
  Collapse rule: any cell with n < 50 plants is merged with within-region
    same-year nearest-elevation population. Deterministic tie-break by
    population code (alphabetical).

This script computes ℙ₀ assignment per plant on the LOCKED phenotype table
(Data__SelectionAnalysis.xlsx, 1028 plants). No phenotype statistic is
computed. Output parquet hash + timestamp is locked before Step 1.

Outputs:
  data/orchids/gymnadenia/derived/P0_partition.parquet
  prereg/P0_hash.txt
"""

from pathlib import Path
import hashlib
import datetime
import pandas as pd

ROOT = Path(r"D:/Phenotype_Research")
RAW = ROOT / "data/orchids/gymnadenia/raw"
DERIVED = ROOT / "data/orchids/gymnadenia/derived"
PREREG = ROOT / "prereg"

SELECTION_XLSX = RAW / "Data__SelectionAnalysis.xlsx"
ENV_CSV = DERIVED / "gymnadenia_pop_env_v2.csv"
PARTITION_PARQUET = DERIVED / "P0_partition.parquet"
HASH_FILE = PREREG / "P0_hash.txt"

MIN_CELL_N = 50

# Locked from S1 Table of Schiestl et al. 2016 (PRE_REG §2)
# Used for the deterministic collapse rule (nearest-elevation neighbor)
POP_ALTITUDE = {
    "Doettingen": 500, "Remigen": 600, "Linn": 500, "Rossweid": 650,
    "Schatzalp": 1800, "Muenstertal": 1800, "Albulapass": 2250, "Corviglia": 2200,
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    # --- load primary table ---
    print("Loading SelectionAnalysis.xlsx ...")
    df = pd.read_excel(SELECTION_XLSX, sheet_name="SelectionAnalysis")
    n_plants = len(df)
    print(f"  {n_plants} plants, {len(df.columns)} cols")

    # Normalize region casing -- raw has 'lowland'/'mountain' (lowercase)
    df["Region_norm"] = df["Region"].str.lower()
    df["Population_norm"] = df["Population"].astype(str)
    df["Year_int"] = df["Year"].astype(int)

    # --- ℙ₀_raw cells: (region, pop, year) ---
    raw_cells = (df.groupby(["Region_norm", "Population_norm", "Year_int"])
                   .size().rename("n").reset_index())
    raw_cells = raw_cells.sort_values(["Region_norm", "Year_int", "Population_norm"])
    print(f"\nℙ₀_raw cells: {len(raw_cells)} non-empty / 16 max")
    print(raw_cells.to_string(index=False))

    # --- apply collapse rule ---
    print(f"\nCollapse rule: n < {MIN_CELL_N} -> within-region same-year nearest-elevation neighbor")
    raw_cells["pop_alt"] = raw_cells["Population_norm"].map(POP_ALTITUDE)
    if raw_cells["pop_alt"].isna().any():
        missing = raw_cells.loc[raw_cells["pop_alt"].isna(), "Population_norm"].unique()
        raise RuntimeError(f"Missing altitude for: {missing}")

    cell_to_id = {}   # (region, pop, year) -> P0_cell_id
    merges = []       # audit log of merges

    for region in sorted(raw_cells["Region_norm"].unique()):
        for year in sorted(raw_cells["Year_int"].unique()):
            sub = raw_cells[(raw_cells["Region_norm"] == region)
                            & (raw_cells["Year_int"] == year)].copy()
            if sub.empty:
                continue
            # process small cells (n < MIN_CELL_N) first, in order of pop code,
            # merging each into nearest-altitude same-(region, year) anchor
            anchors = sub[sub["n"] >= MIN_CELL_N].copy()
            smalls = sub[sub["n"] < MIN_CELL_N].copy()

            # every anchor gets its own cell_id
            for _, a in anchors.sort_values("Population_norm").iterrows():
                cid = f"{region[0].upper()}_{a['Population_norm'][:4]}_{year}"
                cell_to_id[(region, a["Population_norm"], year)] = cid

            # if no anchor in this (region, year), the smalls merge with each other
            # by chained nearest-elevation; pick the smallest-altitude pop as the
            # seed deterministically
            if anchors.empty and not smalls.empty:
                seed = smalls.sort_values(["pop_alt", "Population_norm"]).iloc[0]
                cid = f"{region[0].upper()}_{seed['Population_norm'][:4]}_{year}_merged"
                for _, s in smalls.iterrows():
                    cell_to_id[(region, s["Population_norm"], year)] = cid
                    if s["Population_norm"] != seed["Population_norm"]:
                        merges.append({
                            "from_pop": s["Population_norm"],
                            "from_n": int(s["n"]),
                            "to_pop": seed["Population_norm"],
                            "region": region, "year": year,
                            "rationale": f"no anchor in ({region},{year}); seed = smallest-alt + alphabetical",
                        })
                continue

            # smalls merge into the within-region same-year nearest-altitude anchor;
            # tie-break alphabetical by population code
            for _, s in smalls.sort_values("Population_norm").iterrows():
                anchors["dalt"] = (anchors["pop_alt"] - s["pop_alt"]).abs()
                target = anchors.sort_values(["dalt", "Population_norm"]).iloc[0]
                target_pop = target["Population_norm"]
                cell_to_id[(region, s["Population_norm"], year)] = cell_to_id[(region, target_pop, year)]
                merges.append({
                    "from_pop": s["Population_norm"], "from_n": int(s["n"]),
                    "to_pop": target_pop, "region": region, "year": year,
                    "rationale": f"|Δalt| = {int(target['dalt'])} m",
                })

    # --- assign per plant ---
    df["P0_cell"] = df.apply(
        lambda r: cell_to_id[(r["Region_norm"], r["Population_norm"], r["Year_int"])],
        axis=1,
    )

    # --- audit ---
    print(f"\nMerges executed: {len(merges)}")
    for m in merges:
        print(f"  {m['region']:9s} {m['year']}: {m['from_pop']:14s} (n={m['from_n']:3d}) -> {m['to_pop']:14s}  ({m['rationale']})")

    final_cells = (df.groupby(["P0_cell"]).size().rename("n_plants")
                     .reset_index().sort_values("P0_cell"))
    print(f"\nℙ₀ (post-collapse): K = {len(final_cells)} cells")
    print(final_cells.to_string(index=False))

    if (final_cells["n_plants"] < MIN_CELL_N).any():
        offenders = final_cells[final_cells["n_plants"] < MIN_CELL_N]
        print(f"\nWARN: {len(offenders)} cells still below MIN_CELL_N after collapse")
        print(offenders.to_string(index=False))

    # --- write partition ---
    partition = df[["PlantID", "Region_norm", "Population_norm", "Year_int", "P0_cell"]].copy()
    partition.columns = ["PlantID", "Region", "Population", "Year", "P0_cell"]
    partition = partition.sort_values("PlantID").reset_index(drop=True)
    partition.to_parquet(PARTITION_PARQUET, index=False)
    print(f"\nWrote {PARTITION_PARQUET}  ({len(partition)} plants assigned)")

    # --- hash + timestamp ---
    sha = sha256_file(PARTITION_PARQUET)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    env_sha = sha256_file(ENV_CSV)
    src_sha = sha256_file(SELECTION_XLSX)
    hash_body = (
        "# RMD-SRC Gymnadenia Step 0 ℙ₀ freeze\n"
        f"# Locked per PRE_REG_v1.0_RMD_SRC_gymnadenia.md §2.4 + §3.1\n"
        f"# Generated: {ts}\n\n"
        f"P0_partition.parquet sha256       = {sha}\n"
        f"P0_partition rows                  = {len(partition)}\n"
        f"P0_partition K cells               = {len(final_cells)}\n"
        f"P0_partition MIN_CELL_N            = {MIN_CELL_N}\n"
        f"P0_partition merges_executed       = {len(merges)}\n\n"
        f"source SelectionAnalysis.xlsx sha = {src_sha}\n"
        f"source gymnadenia_pop_env_v2.csv  = {env_sha}\n"
    )
    HASH_FILE.write_text(hash_body, encoding="utf-8")
    print(f"\nWrote {HASH_FILE}")
    print("\n--- hash body ---")
    print(hash_body)


if __name__ == "__main__":
    main()
