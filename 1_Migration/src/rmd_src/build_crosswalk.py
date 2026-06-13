"""
Build a clean PUMA -> MIGPUMA (2010-vintage) crosswalk from the IPUMS
relationship file, for mapping destination (STATEFIP, PUMA) to its MIGPUMA.

Source: data/raw/crosswalks/puma_migpuma1_pwpuma00_2010.xls
  cols: State of Residence | PUMA | PW/Mig State | PWPUMA00 or MIGPUMA1
  (2010 MIGPUMAs and PWPUMAs are identical per IPUMS.)

Output: data/derived/puma_to_migpuma_2010.parquet
  cols: statefip, puma, migpuma  (all int)
Origin geography is taken directly from IPUMS MIGPLAC1+MIGPUMA1; this
crosswalk is only needed to assign destination PUMA -> MIGPUMA.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

SRC = Path(r"D:\Migration\data\raw\crosswalks\puma_migpuma1_pwpuma00_2010.xls")
OUT = Path(r"D:\Migration\data\derived\puma_to_migpuma_2010.parquet")


def main():
    raw = pd.read_excel(SRC, sheet_name="PUMA_POWPUMA_MIGPUMA", header=2, dtype=str)
    raw.columns = ["res_state", "puma", "mig_state", "migpuma"]
    raw = raw.dropna(subset=["res_state", "puma", "migpuma"]).copy()
    for c in raw.columns:
        raw[c] = raw[c].str.strip().astype(int)

    # PUMA -> MIGPUMA must stay within state (a PUMA lies in one state)
    assert (raw.res_state == raw.mig_state).all(), "PUMA-MIGPUMA crosses state!"

    cw = raw[["res_state", "puma", "migpuma"]].rename(columns={"res_state": "statefip"})
    # one MIGPUMA per (state, puma)
    dup = cw.groupby(["statefip", "puma"]).migpuma.nunique()
    assert (dup == 1).all(), "a PUMA maps to >1 MIGPUMA"
    cw = cw.drop_duplicates(["statefip", "puma"]).reset_index(drop=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    cw.to_parquet(OUT, index=False)

    n_puma = len(cw)
    n_mig = cw.groupby(["statefip", "migpuma"]).ngroups
    print(f"crosswalk rows (PUMAs): {n_puma}")
    print(f"distinct MIGPUMAs (state+migpuma): {n_mig}")
    print(f"avg PUMAs per MIGPUMA: {n_puma / n_mig:.2f}")
    print(f"written: {OUT}")


if __name__ == "__main__":
    main()
