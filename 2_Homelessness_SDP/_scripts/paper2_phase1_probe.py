"""Quick probe of GIDD + EM-DAT columns before writing pre-regs / firing tests."""
import pandas as pd
from pathlib import Path

GIDD = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx")
EMDAT = Path("D:/IDP/data/emdat/public_emdat_incl_hist_2026-05-18.xlsx")

print("=== GIDD Disasters ===")
g = pd.read_excel(GIDD)
print(f"Shape: {g.shape}")
print(f"Columns: {list(g.columns)}")
print(g.head(3))
print()
print("Hazard types:", sorted(g["Hazard Type"].dropna().unique().tolist()) if "Hazard Type" in g.columns else "n/a")
print()
print(f"Years range: {g.iloc[:, [c for c in range(len(g.columns)) if 'year' in str(g.columns[c]).lower()][0]].agg(['min','max']) if any('year' in str(c).lower() for c in g.columns) else 'n/a'}")
print()

print("=== EM-DAT ===")
e = pd.read_excel(EMDAT, nrows=2000)
print(f"Shape (first 2000 rows): {e.shape}")
print(f"Columns: {list(e.columns)}")
print()
# Look for affected/displaced columns
affected_cols = [c for c in e.columns if "affect" in str(c).lower() or "displ" in str(c).lower() or "homeless" in str(c).lower()]
print(f"Affected-related cols: {affected_cols}")
