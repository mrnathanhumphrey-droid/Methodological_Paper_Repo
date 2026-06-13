"""
Step-3 prep: species stock per (destination MIGPUMA, year), PERWT-weighted.

The response function (PRE_REG §3.3) uses:
  rho_s = prior-year (t-1) SAME-species resident density at destination MIGPUMA
  rho_x = prior-year (t-1) CROSS-species resident density at destination MIGPUMA
Both are stocks (where people already live), computed from ALL in-scope
residents (not just migrants), using the same ℙ₀ cell_id assignment.

This script produces the per-(state, migpuma, year, cell_id) weighted resident
count; the t-1 lookup + per-km2 normalization happens at attach time.

Output: data/derived/migpuma_species_stock_2010.parquet
  cols: statefip, migpuma, year, cell_id, stock   (stock = sum PERWT)
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

DERIVED = Path(r"D:\Migration\data\derived")


def main():
    p0 = pd.read_parquet(DERIVED / "P0_partition.parquet")
    cw = pd.read_parquet(DERIVED / "puma_to_migpuma_2010.parquet").rename(
        columns={"statefip": "STATEFIP", "puma": "PUMA"})
    p0 = p0.merge(cw, on=["STATEFIP", "PUMA"], how="left")
    miss = int(p0.migpuma.isna().sum())
    p0 = p0.dropna(subset=["migpuma"]).copy()
    p0["migpuma"] = p0.migpuma.astype(int)

    stock = (p0.groupby(["STATEFIP", "migpuma", "YEAR", "cell_id"]).PERWT.sum()
             .reset_index()
             .rename(columns={"STATEFIP": "statefip", "YEAR": "year", "PERWT": "stock"}))
    stock.to_parquet(DERIVED / "migpuma_species_stock_2010.parquet", index=False)

    tot = stock.groupby(["statefip", "migpuma", "year"]).stock.sum()
    print(f"residents unmapped to MIGPUMA: {miss}")
    print(f"stock rows (state,migpuma,year,species): {len(stock):,}")
    print(f"distinct migpuma-year cells: {stock.groupby(['statefip','migpuma','year']).ngroups:,}")
    print(f"species present per migpuma-year: mean {stock.groupby(['statefip','migpuma','year']).cell_id.nunique().mean():.1f}")
    print(f"total resident weight (all years): {stock.stock.sum():,.0f}")
    print(f"written: {DERIVED / 'migpuma_species_stock_2010.parquet'}")


if __name__ == "__main__":
    main()
