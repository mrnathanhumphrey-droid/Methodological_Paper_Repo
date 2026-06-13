"""
Per-plant Gymnadenia analysis substrate:
  SelectionAnalysis.xlsx (1029 plants) LEFT JOIN gymnadenia_pop_env_v2.csv on (region, population)

Also outputs an aux table joining FloralTraitDifferences (1163 plants, has TotalScentAmount +
LN-transformed cols) and ReproductiveSuccessDifferences (1119 plants).

Output:
  data/orchids/gymnadenia/derived/plants_selection_with_env.csv
  data/orchids/gymnadenia/derived/plants_floraltrait_with_env.csv
  data/orchids/gymnadenia/derived/plants_reproductive_with_env.csv
  data/orchids/gymnadenia/derived/plants_herbivory_with_env.csv
"""

from pathlib import Path
import pandas as pd

ROOT = Path(r"D:/Phenotype_Research")
RAW = ROOT / "data/orchids/gymnadenia/raw"
DERIVED = ROOT / "data/orchids/gymnadenia/derived"

ENV_CSV = DERIVED / "gymnadenia_pop_env_v2.csv"

# (xlsx, sheet, region_col, pop_col, out_name)
TABLES = [
    ("Data__SelectionAnalysis.xlsx",          "SelectionAnalysis",        "Region", "Population", "plants_selection_with_env.csv"),
    ("Data__FloralTraitDifferences.xlsx",     "FloralTraitDifferences",   "Region", "Population", "plants_floraltrait_with_env.csv"),
    ("Data__ReproductiveSuccessDifferences.xlsx", "RSDifferences",        "Region", "Population", "plants_reproductive_with_env.csv"),
    ("Data__HerbivoryDifferences.xlsx",       "HerbivoryDifferences",     "Region", "Population", "plants_herbivory_with_env.csv"),
    ("Data__PollinatorLimitation.xlsx",       "PollinatiorLimitation",    "Region", "Population", "plants_pollim_with_env.csv"),
]


def main():
    env = pd.read_csv(ENV_CSV)
    # normalize join keys: env has region in lowercase; xlsx may have any case
    env["_join_region"] = env["region"].str.lower()
    env["_join_pop"] = env["population"].str.lower()

    print(f"env table: {len(env)} pops, {len(env.columns)} cols")

    for xlsx_name, sheet, rcol, pcol, out_name in TABLES:
        path = RAW / xlsx_name
        df = pd.read_excel(path, sheet_name=sheet)
        n_pre = len(df)
        df["_join_region"] = df[rcol].astype(str).str.lower()
        df["_join_pop"] = df[pcol].astype(str).str.lower()

        merged = df.merge(env.drop(columns=["region", "population", "code"]),
                          on=["_join_region", "_join_pop"], how="left")
        # check
        unmatched = merged["lat_dd"].isna().sum()
        merged = merged.drop(columns=["_join_region", "_join_pop"])
        out_path = DERIVED / out_name
        merged.to_csv(out_path, index=False)
        print(f"  {xlsx_name}: {n_pre} rows -> {len(merged)} rows, {len(merged.columns)} cols  unmatched={unmatched}  -> {out_name}")


if __name__ == "__main__":
    main()
