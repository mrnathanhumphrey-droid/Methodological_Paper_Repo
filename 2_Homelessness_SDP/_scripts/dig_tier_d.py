"""Tier D dig: 005 MLI strife sequencing + 006 BEN periphery."""
import pathlib
import warnings
warnings.filterwarnings("ignore")
import pandas as pd

ROOT = pathlib.Path("D:/IDP")
DATA = ROOT / "data"

print("[load] UCDP-GED")
ged = pd.read_csv(DATA / "ucdp" / "GEDEvent_v25_1.csv", low_memory=False)


def hdr(num, title):
    print()
    print("=" * 80)
    print(f"DIG {num}: {title}")
    print("=" * 80)


# ====================================================================
# DIG 005: MLI strife sequencing — when did the strife signature first emerge?
# ====================================================================
hdr("005", "MLI strife sequencing — early vs late emergence vs peers")

# For each Sahel + other strife-dominant cluster country, get year-by-year:
# strife (type=2) fatalities and event count
peers = ["Mali", "Burkina Faso", "Niger", "Benin", "South Sudan", "Haiti",
         "Central African Republic"]
for c in peers:
    sub = ged[(ged["country"] == c) & (ged["type_of_violence"] == 2)]
    if not len(sub):
        print(f"\n{c}: no non-state-strife events")
        continue
    yr = sub.groupby("year").agg(events=("id","count"), fatalities=("best","sum"))
    yr = yr[yr.index >= 1998]
    first_year_with_signal = yr[yr["fatalities"] >= 50].index.min() if (yr["fatalities"] >= 50).any() else None
    total = yr["fatalities"].sum()
    print(f"\n{c}: total strife fatalities 1998+ = {total:,}; first year with >=50 strife fatal = {first_year_with_signal}")
    print(yr[yr["fatalities"] > 0].tail(15).to_string())

# Dyad-level for MLI
print("\n=== MLI strife dyads (top 10 by lifetime fatalities) ===")
mli_strife = ged[(ged["country"] == "Mali") & (ged["type_of_violence"] == 2)]
print(mli_strife.groupby("dyad_name")["best"].sum().sort_values(ascending=False).head(10).to_string())

print("\n=== MLI strife admin-1 acute fatalities ===")
mli_acute = mli_strife[(mli_strife["year"] >= 2020) & (mli_strife["year"] <= 2024)]
print(mli_acute.groupby("adm_1")["best"].sum().sort_values(ascending=False).head(10).to_string())


# ====================================================================
# DIG 006: BEN periphery — admin-1 fatalities + cross-border BFA
# ====================================================================
hdr("006", "BEN periphery — Atakora/Alibori admin-1 trajectory + BFA-Est mirror")

ben = ged[ged["country"] == "Benin"].copy()
print(f"BEN GED events: {len(ben):,}")

print("\nBEN annual events + fatalities (1998+):")
print(ben.groupby("year").agg(events=("id","count"), fatalities=("best","sum")).to_string())

print("\nBEN acute (2020-2024) admin-1 fatalities:")
ben_acute = ben[(ben["year"] >= 2020) & (ben["year"] <= 2024)]
print(ben_acute.groupby("adm_1")["best"].sum().sort_values(ascending=False).head(10).to_string())

print("\nBEN acute actor side_a:")
print(ben_acute.groupby("side_a")["best"].sum().sort_values(ascending=False).head(10).to_string())

# Mirror: BFA Est region acute (cross-border)
print("\n=== BFA Est region (adjacent to BEN) acute fatalities by year ===")
bfa_est = ged[(ged["country"] == "Burkina Faso") & (ged["adm_1"] == "Est region")
              & (ged["year"] >= 2018) & (ged["year"] <= 2024)]
print(bfa_est.groupby("year").agg(events=("id","count"), fatalities=("best","sum")).to_string())

# Cross-border distance — are BEN events near the BFA border?
print("\n=== BEN acute events, latitude band (north > 11.5 = near BFA border) ===")
ben_acute_geo = ben_acute.copy()
ben_acute_geo["band"] = pd.cut(ben_acute_geo["latitude"],
                                bins=[6, 9, 11, 11.5, 12.5],
                                labels=["south", "mid", "north_central", "north_BF_border"])
print(ben_acute_geo.groupby("band", observed=True).agg(events=("id","count"), fatalities=("best","sum")).to_string())

print()
print("=" * 80)
print("TIER D DIG COMPLETE")
print("=" * 80)
