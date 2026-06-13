"""
Probe 2 (23_PREREG_v1.0_FleetPLR_PVCZ) — Step §14.2 + §14.3
Cohort assembly + ℙ₀ partition assignment from PVDAQ systems index.

EXOGENOUS ONLY. No outcome (PLR / yield / performance) quantity is computed
here. This script must run and lock the ℙ₀ assignment BEFORE any time-series
acquisition, per RMD-SRC §Step 0 and pre-reg §0 integrity note.

Inputs:  data/raw/datasets/PVDAQ_systems_20250729.csv
Outputs: data/processed/probe2_cohort_p0.csv   (one row per cohort system, with ℙ₀ cell)
         data/processed/probe2_p0_cell_counts.csv  (populated-cell census)
"""
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # Solar/
IDX = ROOT / "data/raw/datasets/PVDAQ_systems_20250729.csv"
OUT_DIR = ROOT / "data/processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---- load index (drop trailing unnamed cols) ----
df = pd.read_csv(IDX).iloc[:, :26]
n_raw = len(df)

# ---- §1 inclusion filters (exogenous) ----
f_qa = df["qa_status"] == "pass"
f_years = df["years"] >= 5.0
f_chan = df["available_sensor_channels"] >= 1
cohort = df[f_qa & f_years & f_chan].copy()

# ---- §3 ℙ₀ exogenous categorical axes ----

# A_MOUNT (from `type`); NaN/unknown -> UNKNOWN
def mount(t):
    if pd.isna(t):
        return "UNKNOWN"
    t = str(t).strip().lower()
    if t in ("roof",):
        return "roof"
    if t in ("ground",):
        return "ground"
    if t in ("carport",):
        return "carport"
    if "tracker" in t:
        return "ground"  # trackers are ground-class for mounting; tracking captured by A_TRACK
    return "UNKNOWN"
cohort["A_MOUNT"] = cohort["type"].map(mount)

# A_TRACK (from `tracking`)
def track(t):
    if pd.isna(t):
        return "UNKNOWN"
    return "tracking" if str(t).strip().lower() == "tracking" else "fixed"
cohort["A_TRACK"] = cohort["tracking"].map(track)

# §3.1 mounting-coherent temperature zone: roof -> pvcz_t_roof, else pvcz_t_rack
tz = pd.Series(
    np.where(cohort["A_MOUNT"] == "roof", cohort["pvcz_t_roof"], cohort["pvcz_t_rack"]),
    index=cohort.index,
).astype("Int64")
cohort["A_PVCZ_T"] = "T" + tz.astype(str)

# A_PVCZ_H
cohort["A_PVCZ_H"] = "H" + cohort["pvcz_humidity"].astype("Int64").astype(str)

# A_TILT bins: low [0,15) / mid [15,35) / high [35,90]; NaN -> UNKNOWN
def tiltbin(x):
    if pd.isna(x):
        return "UNKNOWN"
    if x < 15:
        return "low"
    if x < 35:
        return "mid"
    return "high"
cohort["A_TILT"] = cohort["tilt"].map(tiltbin)

# A_AZ bins: south[135,225) east[45,135) west[225,315) north[else]; -1 sentinel & NaN -> UNKNOWN
def azbin(x):
    if pd.isna(x) or x < 0:
        return "UNKNOWN"
    x = x % 360
    if 135 <= x < 225:
        return "south"
    if 45 <= x < 135:
        return "east"
    if 225 <= x < 315:
        return "west"
    return "north"
cohort["A_AZ"] = cohort["azimuth"].map(azbin)

# A_CAP: residential[<20] commercial[20,1000) utility[>=1000]; NaN -> UNKNOWN
def capbin(x):
    if pd.isna(x):
        return "UNKNOWN"
    if x < 20:
        return "residential"
    if x < 1000:
        return "commercial"
    return "utility"
cohort["A_CAP"] = cohort["dc_capacity_kW"].map(capbin)

# A_VINT from first_timestamp year
yr = pd.to_datetime(cohort["first_timestamp"], errors="coerce").dt.year
def vintbin(y):
    if pd.isna(y):
        return "UNKNOWN"
    if y < 2010:
        return "pre-2010"
    if y < 2015:
        return "2010-2014"
    if y < 2020:
        return "2015-2019"
    return "2020+"
cohort["A_VINT"] = yr.map(vintbin)

# ---- full 8-axis ℙ₀ cell id + 2D primary (replication) cell ----
AXES = ["A_PVCZ_T", "A_PVCZ_H", "A_MOUNT", "A_TRACK", "A_TILT", "A_AZ", "A_CAP", "A_VINT"]
cohort["P0_cell"] = cohort[AXES].astype(str).agg("|".join, axis=1)
cohort["P0_primary_TH"] = cohort["A_PVCZ_T"] + ":" + cohort["A_PVCZ_H"]

# ---- write cohort assignment ----
keep = ["system_id", "system_public_name", "latitude", "longitude",
        "dc_capacity_kW", "years", "number_records", "dataset_size_mb",
        "available_sensor_channels", "kg_climate"] + AXES + ["P0_cell", "P0_primary_TH"]
cohort[keep].to_csv(OUT_DIR / "probe2_cohort_p0.csv", index=False)

# ---- cell census ----
print(f"Raw systems: {n_raw}")
print(f"Cohort (qa pass + years>=5 + channels>=1): {len(cohort)}")
print()
print("=== Primary 2D replication partition (T:H) census ===")
th = cohort["P0_primary_TH"].value_counts().sort_index()
print(th.to_string())
print(f"\nCells with n>=50 (VERIFIED-eligible per §11): {(th>=50).sum()} of {len(th)}")
print(f"Data volume in those cells: "
      f"{cohort.loc[cohort['P0_primary_TH'].isin(th[th>=50].index),'dataset_size_mb'].sum()/1024:.1f} GB")
print()
print("=== Full 8-axis ℙ₀ ===")
fc = cohort["P0_cell"].value_counts()
print(f"Populated full cells: {len(fc)}")
print(f"Full cells with n>=50: {(fc>=50).sum()}")
print(f"Full cells with n>=20: {(fc>=20).sum()}")
print()
print("=== Axis marginals ===")
for a in AXES:
    print(f"-- {a} --")
    print(cohort[a].value_counts().sort_index().to_string())
    print()

# census file
census = pd.DataFrame({"P0_primary_TH": th.index, "n": th.values})
census.to_csv(OUT_DIR / "probe2_p0_cell_counts.csv", index=False)
print("Wrote: data/processed/probe2_cohort_p0.csv + probe2_p0_cell_counts.csv")
