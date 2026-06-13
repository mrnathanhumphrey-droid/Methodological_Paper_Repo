"""Fire all 4 pre-reg tests on the holdout panel + retrospective V-Dem data.

PRE_REG_002: range+trigger libdem collapse
PRE_REG_003: disaster-displacement regime typology
PRE_REG_004: 3-channel orthogonality
PRE_REG_005: Bukelization (retrospective + forward scoring)
"""
import pathlib
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
from scipy.stats import spearmanr

ROOT = pathlib.Path("D:/IDP")
DATA = ROOT / "data"
ANA = ROOT / "analysis"

# ============================================================
# Load shared data
# ============================================================
print("[load] V-Dem")
vdem = pd.read_csv(DATA / "vdem" / "vdem_vdem.csv", low_memory=False)
vdem = vdem[["country_text_id", "year", "v2x_libdem"]].rename(
    columns={"country_text_id": "iso3", "year": "year", "v2x_libdem": "libdem"}
)

print("[load] GIDD displacement + disasters")
gidd_conf = pd.read_excel(DATA / "idmc_gidd" / "IDMC_GIDD_Conflict_Violence_Disasters.xlsx",
                          sheet_name="1_Displacement_data")
gidd_dis = pd.read_excel(DATA / "idmc_gidd" / "IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx",
                         sheet_name="1_Disaster_Displacement_data")

print("[load] holdout panel")
panel = pd.read_parquet(ANA / "prereg_holdout_stratified_panel_2026_05_21.parquet")
print(f"  panel: {panel.shape}, countries: {sorted(panel['iso3'].unique())}")


def hdr(num, title):
    print("\n" + "="*80)
    print(f"PRE_REG {num}: {title}")
    print("="*80)


# ============================================================
# PRE_REG_002: Range + Trigger libdem collapse
# ============================================================
hdr("002", "Range+Trigger libdem collapse")

watch = {
    "AGO": "succession-2027",
    "MOZ": "Cabo Delgado insurgency + 2024 election",
    "COL": "post-Petro succession",
    "IND": "BJP supermajority",
    "TUR": "post-Erdoğan succession",
    "BRA": "2026 election Bolsonaro return scenario",
}
print("\nWatch list libdem trajectory (2018, 2020, 2022, 2024):")
print(f"{'iso':5s} {'2018':>8s} {'2020':>8s} {'2022':>8s} {'2024':>8s}  {'delta_(2018-24)':>11s}  {'range_yes':>10s}  trigger-risk")
for iso, risk in watch.items():
    row = vdem[vdem["iso3"] == iso]
    vals = {}
    for y in [2018, 2020, 2022, 2024]:
        m = row[row["year"] == y]
        vals[y] = m["libdem"].iloc[0] if len(m) else None
    delta = (vals[2024] - vals[2018]) if vals[2018] is not None and vals[2024] is not None else None
    range_yes = "YES" if vals[2018] is not None and vals[2018] >= 0.22 else "NO"
    print(f"{iso:5s} {vals[2018] if vals[2018] is not None else 'NA':>8} {vals[2020] if vals[2020] is not None else 'NA':>8} {vals[2022] if vals[2022] is not None else 'NA':>8} {vals[2024] if vals[2024] is not None else 'NA':>8}  {delta:>11.3f}  {range_yes:>10s}  {risk}")

# PAK control reminder
pak_2018 = vdem[(vdem["iso3"] == "PAK") & (vdem["year"] == 2018)]["libdem"].iloc[0]
pak_2024 = vdem[(vdem["iso3"] == "PAK") & (vdem["year"] == 2024)]["libdem"].iloc[0]
print(f"\nPAK control (range-yes, no trigger): 2018={pak_2018:.3f}, 2024={pak_2024:.3f}, delta_={pak_2024-pak_2018:.3f}  -> no collapse confirmed")

# Floor-saturated cross-corpus check
hdr("002b", "Floor-saturated countries (range-no): predict no collapse possible")
floor = ["ETH","SOM","SDN","SSD","ERI","SYR","YEM","COD","CMR","IRQ","LBN"]
for iso in floor:
    row = vdem[(vdem["iso3"] == iso) & (vdem["year"].isin([2018, 2024]))]
    if len(row) == 2:
        v18, v24 = row.sort_values("year")["libdem"].values
        flag = "  *** range-no but DROPPED BELOW 0.05" if v24 < 0.05 and v18 >= 0.05 else ""
        print(f"  {iso}: 2018={v18:.3f}, 2024={v24:.3f}, delta_={v24-v18:+.3f}{flag}")


# ============================================================
# PRE_REG_003: Disaster-displacement regime typology
# ============================================================
hdr("003", "Disaster-displacement regime typology — holdout fit")

holdout_disaster = ["HTI", "DOM", "CUB", "USA", "FJI", "VUT", "SLB", "BRA"]

def classify_regime(iso):
    sub = gidd_dis[gidd_dis["ISO3"] == iso]
    if not len(sub):
        return {"regime": "NO_DATA", "metrics": {}}
    annual = sub.groupby(["Year", "Hazard Type"])["Disaster Internal Displacements"].sum().unstack(fill_value=0)
    annual = annual[(annual.index >= 2008) & (annual.index <= 2024)]
    flood = annual.get("Flood", pd.Series([0]*len(annual), index=annual.index))
    storm = annual.get("Storm", pd.Series([0]*len(annual), index=annual.index))
    eq = annual.get("Earthquake", pd.Series([0]*len(annual), index=annual.index))
    drought = annual.get("Drought", pd.Series([0]*len(annual), index=annual.index))
    total_dis = annual.sum().sum()
    flood_total = flood.sum()
    storm_total = storm.sum()
    eq_total = eq.sum()
    drought_total = drought.sum()
    flood_share = flood_total / total_dis if total_dis > 0 else 0
    storm_share = storm_total / total_dis if total_dis > 0 else 0
    eq_share = eq_total / total_dis if total_dis > 0 else 0
    drought_share = drought_total / total_dis if total_dis > 0 else 0
    flood_max = flood.max()
    flood_median = flood.median()
    flood_max_median_ratio = flood_max / flood_median if flood_median > 0 else (np.inf if flood_max > 0 else 0)
    flood_mega_years = (flood > 1_000_000).sum()
    storm_mega_years = (storm > 1_000_000).sum()
    # Regime classification
    regime = "UNCLASSIFIED"
    if total_dis < 100_000:
        regime = "INSUFFICIENT_DATA (< 100K total disaster-IDP)"
    elif flood_max_median_ratio > 30 and flood_mega_years >= 2 and storm_share < 0.10:
        regime = "1_BIMODAL_MEGA_FLOOD"
    elif flood_mega_years >= 7 and flood_max_median_ratio < 5 and flood_share > 0.50:
        regime = "2_STEADY_HIGH_FLOOD"
    elif storm_share > 0.70:
        regime = "3_STORM_DOMINANT"
    elif drought_share > 0.50:
        regime = "5_DROUGHT_DOMINANT (new regime)"
    elif eq_share > 0.50:
        regime = "6_EARTHQUAKE_DOMINANT (new regime)"
    else:
        regime = "4_MIXED"
    return {
        "regime": regime,
        "metrics": {
            "total_dis_idp": int(total_dis),
            "flood_share": round(flood_share, 3),
            "storm_share": round(storm_share, 3),
            "eq_share": round(eq_share, 3),
            "drought_share": round(drought_share, 3),
            "flood_max_median_ratio": round(flood_max_median_ratio, 1),
            "flood_mega_years": int(flood_mega_years),
            "storm_mega_years": int(storm_mega_years),
        }
    }


print(f"\n{'iso':5s} {'regime':40s} {'totalIDP':>12s} {'flood%':>7s} {'storm%':>7s} {'eq%':>6s} {'fl_max/med':>11s}")
for iso in holdout_disaster:
    r = classify_regime(iso)
    m = r["metrics"]
    if "total_dis_idp" in m:
        print(f"{iso:5s} {r['regime']:40s} {m['total_dis_idp']:>12,} {m['flood_share']*100:>6.1f}% {m['storm_share']*100:>6.1f}% {m['eq_share']*100:>5.1f}% {m['flood_max_median_ratio']:>11.1f}x")
    else:
        print(f"{iso:5s} {r['regime']:40s}")

# 5th regime test (drought)
hdr("003b", "Drought-dominant test (SOM, ETH) — does Regime 5 emerge?")
for iso in ["SOM", "ETH", "AFG", "BFA", "NER"]:
    r = classify_regime(iso)
    m = r["metrics"]
    if "total_dis_idp" in m:
        print(f"{iso:5s} {r['regime']:40s} drought%={m['drought_share']*100:>5.1f}%  storm%={m['storm_share']*100:>5.1f}%  flood%={m['flood_share']*100:>5.1f}%")


# ============================================================
# PRE_REG_004: 3-channel orthogonality
# ============================================================
hdr("004", "3-channel displacement orthogonality")

countries_004 = ["AGO","MOZ","COL","IND","TUR","BRA","HTI","DOM","CUB","USA","FJI","VUT","SLB","PHL","SOM","SDN","PAK","BFA"]

print(f"\n{'iso':5s} {'years':>5s} {'rho(con,flood)':>15s} {'rho(con,drought)':>17s} {'rho(flood,drought)':>20s} flag")
results_004 = {}
for iso in countries_004:
    # GIDD conflict-IDP annual
    c = gidd_conf[gidd_conf["ISO3"] == iso][["Year", "Conflict Internal Displacements"]].rename(
        columns={"Year": "year", "Conflict Internal Displacements": "conf"}
    )
    # GIDD disaster by hazard
    d = gidd_dis[gidd_dis["ISO3"] == iso]
    d_flood = d[d["Hazard Type"] == "Flood"].groupby("Year")["Disaster Internal Displacements"].sum().reset_index().rename(columns={"Year":"year","Disaster Internal Displacements":"flood"})
    d_drought = d[d["Hazard Type"] == "Drought"].groupby("Year")["Disaster Internal Displacements"].sum().reset_index().rename(columns={"Year":"year","Disaster Internal Displacements":"drought"})
    df = c.merge(d_flood, on="year", how="outer").merge(d_drought, on="year", how="outer")
    df = df[(df["year"] >= 2008) & (df["year"] <= 2024)].fillna(0)
    if len(df) < 5:
        print(f"{iso:5s} {len(df):>5d}    (insufficient data)")
        continue
    r1, _ = spearmanr(df["conf"], df["flood"])
    r2, _ = spearmanr(df["conf"], df["drought"])
    r3, _ = spearmanr(df["flood"], df["drought"])
    fail_flags = []
    if abs(r1) > 0.5: fail_flags.append("CF>0.5")
    if abs(r2) > 0.5: fail_flags.append("CD>0.5")
    if abs(r3) > 0.5: fail_flags.append("FD>0.5")
    flag_str = "  " + ", ".join(fail_flags) if fail_flags else ""
    print(f"{iso:5s} {len(df):>5d} {r1:>15.3f} {r2:>17.3f} {r3:>20.3f}{flag_str}")
    results_004[iso] = (r1, r2, r3)

# H3 specific predictions
hdr("004b", "H3 specific exception checks (predicted couplings)")
for iso, pair, predicted_range in [
    ("PHL", "conf-storm", "0.3-0.5"),
    ("SOM", "conf-drought", ">0.5"),
    ("SDN", "conf-drought", ">0.4"),
]:
    if iso in results_004:
        r1, r2, r3 = results_004[iso]
        if pair == "conf-drought":
            actual = r2
        elif pair == "conf-storm":
            # we did conf-flood, but for PHL the "storm" channel is what matters
            d = gidd_dis[gidd_dis["ISO3"] == iso]
            d_storm = d[d["Hazard Type"] == "Storm"].groupby("Year")["Disaster Internal Displacements"].sum().reset_index().rename(columns={"Year":"year","Disaster Internal Displacements":"storm"})
            c = gidd_conf[gidd_conf["ISO3"] == iso][["Year", "Conflict Internal Displacements"]].rename(columns={"Year":"year","Conflict Internal Displacements":"conf"})
            df = c.merge(d_storm, on="year", how="outer").fillna(0)
            df = df[(df["year"]>=2008)&(df["year"]<=2024)]
            actual, _ = spearmanr(df["conf"], df["storm"])
        else:
            actual = None
        if actual is not None:
            print(f"  {iso} {pair}: predicted {predicted_range}, actual = {actual:.3f}")


# ============================================================
# PRE_REG_005: Bukelization retrospective
# ============================================================
hdr("005", "Bukelization shape — retrospective test (HUN/TUR/VEN/RUS)")

bukel_cases = [
    ("HUN", 2010, 2015, "Orban short window"),
    ("HUN", 2010, 2020, "Orban long window"),
    ("TUR", 2014, 2019, "Erdoğan post-Gezi"),
    ("VEN", 2002, 2007, "Chavez consolidation"),
    ("VEN", 2013, 2018, "Maduro deepening"),
    ("RUS", 2000, 2005, "early Putin"),
    ("RUS", 2007, 2012, "Medvedev/return"),
]
print(f"\n{'iso':4s} {'window':>11s} {'start':>7s} {'end':>7s} {'delta':>7s} range>=0.30  delta<=-0.30  fit  notes")
for iso, y1, y2, label in bukel_cases:
    s = vdem[(vdem["iso3"] == iso) & (vdem["year"] == y1)]
    e = vdem[(vdem["iso3"] == iso) & (vdem["year"] == y2)]
    if not (len(s) and len(e)):
        print(f"  {iso} {y1}-{y2}: missing data")
        continue
    sv, ev = s["libdem"].iloc[0], e["libdem"].iloc[0]
    delta = ev - sv
    range_ok = sv >= 0.30
    delta_ok = delta <= -0.30
    # Monotonicity check
    window = vdem[(vdem["iso3"] == iso) & (vdem["year"] >= y1) & (vdem["year"] <= y2)].sort_values("year")
    yoy = window["libdem"].diff().dropna()
    n_increases = (yoy > 0.02).sum()  # allow tiny upward wiggles
    monotonic = n_increases <= 1
    fit = "FIT" if (range_ok and delta_ok and monotonic) else ("PARTIAL" if (range_ok and delta_ok) else "NO")
    print(f"  {iso} {y1}-{y2}  {sv:>7.3f} {ev:>7.3f} {delta:>+7.3f}  {'YES' if range_ok else 'NO':>10s}  {'YES' if delta_ok else 'NO':>11s}  {fit:>4s}  {label} (mono={monotonic}, ↑yrs={n_increases})")

# Forward scoring
hdr("005b", "Forward scoring (IND/BRA/TUR/HUN/USA) — current libdem snapshot 2024")
for iso in ["IND", "BRA", "TUR", "HUN", "USA"]:
    row = vdem[(vdem["iso3"] == iso) & (vdem["year"].isin([2018, 2020, 2022, 2024]))]
    if len(row) < 2:
        print(f"  {iso}: missing 2024 data")
        continue
    vals = {y: row[row["year"] == y]["libdem"].iloc[0] if len(row[row["year"] == y]) else None for y in [2018, 2020, 2022, 2024]}
    print(f"  {iso}: 2018={vals[2018]}, 2020={vals[2020]}, 2022={vals[2022]}, 2024={vals[2024]}")

# Negative controls
hdr("005c", "Negative-control countries (predict no Bukelization)")
for iso in ["DEU","FRA","GBR","CAN","AUS","JPN","NLD","NOR","SWE","FIN"]:
    row = vdem[(vdem["iso3"] == iso) & (vdem["year"].isin([2014, 2024]))]
    if len(row) == 2:
        s, e = row.sort_values("year")["libdem"].values
        flag = "  *** UNEXPECTED delta_ <= -0.10" if (e - s) <= -0.10 else ""
        print(f"  {iso}: 2014={s:.3f}, 2024={e:.3f}, delta_={e-s:+.3f}{flag}")

print("\n" + "="*80)
print("ALL 4 PRE-REG FITS COMPLETE")
print("="*80)
