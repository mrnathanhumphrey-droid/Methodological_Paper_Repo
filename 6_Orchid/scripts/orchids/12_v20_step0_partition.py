"""RMD-SRC v2.0 Step 0 -- ℙ₀ partition freeze (Region × Pop, K=8, time-invariant).

Per LOCKED PRE_REG_v2.0_RMD_SRC_gymnadenia.md §2.4.
"""
from pathlib import Path
import hashlib, datetime
import pandas as pd

ROOT = Path(r"D:/Phenotype_Research")
RAW = ROOT / "data/orchids/gymnadenia/raw"
DERIVED = ROOT / "data/orchids/gymnadenia/derived"
PREREG = ROOT / "prereg"
SEL = RAW / "Data__SelectionAnalysis.xlsx"
PART = DERIVED / "P0_partition_v20.parquet"
HASH = PREREG / "P0_hash_v20.txt"

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1<<16), b""): h.update(c)
    return h.hexdigest()

def main():
    df = pd.read_excel(SEL, sheet_name="SelectionAnalysis")
    df["Region_norm"] = df["Region"].str.lower()
    df["Population_norm"] = df["Population"].astype(str)
    df["Year_int"] = df["Year"].astype(int)
    df["P0_cell"] = df["Region_norm"].str[0].str.upper() + "_" + df["Population_norm"].str[:4]
    print(f"K = {df['P0_cell'].nunique()} cells")
    print(df.groupby(["P0_cell","Year_int"]).size().unstack(fill_value=0))
    print()
    n_per = df.groupby("P0_cell").size().rename("n")
    print(n_per.to_string())
    assert (n_per >= 50).all(), "All cells must be ≥ 50"

    out = df[["PlantID","Region_norm","Population_norm","Year_int","P0_cell"]].copy()
    out.columns = ["PlantID","Region","Population","Year","P0_cell"]
    out = out.sort_values("PlantID").reset_index(drop=True)
    out.to_parquet(PART, index=False)

    src = sha(SEL); rot = sha(DERIVED / "observable_rotation_W_v11.parquet")
    sco = sha(DERIVED / "observable_scores_v11.parquet")
    p0  = sha(PART)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    HASH.write_text(
        f"# RMD-SRC Gymnadenia v2.0 Step 0 ℙ₀ freeze\n"
        f"# Generated: {ts}\n"
        f"# Per PRE_REG_v2.0 §2.4 (Region × Pop, K=8, time-invariant)\n\n"
        f"P0_partition_v20.parquet sha256       = {p0}\n"
        f"P0_partition rows                      = {len(out)}\n"
        f"P0_partition K                         = {out['P0_cell'].nunique()}\n"
        f"P0_partition merges                    = 0\n\n"
        f"inherited rotation W_v11 sha256       = {rot}\n"
        f"inherited scores_v11 sha256           = {sco}\n"
        f"source SelectionAnalysis.xlsx sha256  = {src}\n",
        encoding="utf-8")
    print(f"\nWrote {PART}\nWrote {HASH}")

if __name__ == "__main__":
    main()
