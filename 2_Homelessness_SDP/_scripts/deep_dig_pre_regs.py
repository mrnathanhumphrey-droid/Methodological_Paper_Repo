"""Deep dig into all 4 pre-regs.

002: trigger operationalization + watch-list year-by-year
003: Regime 6 expansion (NPL/CHL/MEX/IDN/JPN/NZL/ECU/PER) + within-Regime-3 bimodality
004: BRA year-by-year decomp + more 3-channel countries
005: sliding 10-year windows for HUN/TUR/VEN/RUS + IND/USA forward
"""
import pathlib
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
from scipy.stats import spearmanr

ROOT = pathlib.Path("D:/IDP")
DATA = ROOT / "data"

print("[load]")
vdem = pd.read_csv(DATA / "vdem" / "vdem_vdem.csv", low_memory=False)
vdem = vdem[["country_text_id", "year", "v2x_libdem"]].rename(columns={"country_text_id": "iso3", "v2x_libdem": "libdem"})
ged = pd.read_csv(DATA / "ucdp" / "GEDEvent_v25_1.csv", low_memory=False)
gidd_conf = pd.read_excel(DATA / "idmc_gidd" / "IDMC_GIDD_Conflict_Violence_Disasters.xlsx",
                          sheet_name="1_Displacement_data")
gidd_dis = pd.read_excel(DATA / "idmc_gidd" / "IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx",
                         sheet_name="1_Disaster_Displacement_data")
print("[load] done")


def hdr(num, title):
    print("\n" + "="*80)
    print(f"DIG {num}: {title}")
    print("="*80)


# ============================================================
# DIG 002a: Trigger operationalization via UCDP fatality jumps
# ============================================================
hdr("002a", "Trigger operationalization: UCDP state-based fatality 5x YoY jumps per country")

def fatality_jumps(country_name, threshold=5.0, min_base=100):
    """Find years where state-based fatalities jumped >=threshold x YoY (min base for noise reduction)."""
    sub = ged[(ged["country"] == country_name) & (ged["type_of_violence"] == 1)]
    yr = sub.groupby("year")["best"].sum().sort_index()
    yr = yr[yr.index >= 2000]
    if len(yr) < 2:
        return []
    ratio = yr / yr.shift(1)
    jumps = ratio[(ratio >= threshold) & (yr >= min_base)]
    return list(zip(jumps.index.tolist(), yr.loc[jumps.index].values.tolist(), ratio.loc[jumps.index].values.tolist()))

watch_country_map = {
    "AGO": "Angola", "MOZ": "Mozambique", "COL": "Colombia",
    "IND": "India", "TUR": "Turkey", "BRA": "Brazil",
    "BFA": "Burkina Faso", "MLI": "Mali", "NER": "Niger",
    "AFG": "Afghanistan", "ETH": "Ethiopia", "MMR": "Myanmar (Burma)",
    "SLV": "El Salvador", "HTI": "Haiti", "CAF": "Central African Republic",
    "PAK": "Pakistan", "BEN": "Benin",
}
print(f"\n{'iso':5s} {'fatal_jumps (year, fatalities, ratio)':80s}")
for iso, name in watch_country_map.items():
    jumps = fatality_jumps(name)
    if jumps:
        s = ", ".join([f"({y}, {int(f):,}, {r:.1f}x)" for y, f, r in jumps])
        print(f"{iso:5s} {s}")
    else:
        print(f"{iso:5s} (no qualifying jumps)")


# ============================================================
# DIG 002b: Watch-list year-by-year libdem 2014-2024 with annotation
# ============================================================
hdr("002b", "Watch-list year-by-year libdem 2014-2024")

watch = ["AGO","MOZ","COL","IND","TUR","BRA","PAK"]
print(f"\n{'iso':5s} " + " ".join([f"{y:>6d}" for y in range(2014, 2025)]))
for iso in watch:
    vals = []
    for y in range(2014, 2025):
        r = vdem[(vdem["iso3"] == iso) & (vdem["year"] == y)]
        vals.append(r["libdem"].iloc[0] if len(r) else None)
    print(f"{iso:5s} " + " ".join([f"{v:>6.3f}" if v is not None else "  NaN " for v in vals]))


# ============================================================
# DIG 003a: Regime 6 expansion test (NPL/CHL/MEX/IDN/JPN/NZL/ECU/PER)
# ============================================================
hdr("003a", "Regime 6 EQ-dominant expansion test")

def classify_regime(iso):
    sub = gidd_dis[gidd_dis["ISO3"] == iso]
    if not len(sub):
        return None
    annual = sub.groupby(["Year", "Hazard Type"])["Disaster Internal Displacements"].sum().unstack(fill_value=0)
    annual = annual[(annual.index >= 2008) & (annual.index <= 2024)]
    total = annual.sum().sum()
    if total < 100_000:
        return {"regime": "INSUFFICIENT", "total": int(total), "shares": {}}
    shares = {h: annual.get(h, pd.Series(dtype=float)).sum() / total for h in ["Flood", "Storm", "Earthquake", "Drought", "Mass Movement", "Volcanic activity"]}
    flood = annual.get("Flood", pd.Series([0]*len(annual), index=annual.index))
    storm = annual.get("Storm", pd.Series([0]*len(annual), index=annual.index))
    eq = annual.get("Earthquake", pd.Series([0]*len(annual), index=annual.index))
    drought = annual.get("Drought", pd.Series([0]*len(annual), index=annual.index))
    flood_max_med = flood.max() / flood.median() if flood.median() > 0 else 0
    flood_mega = (flood > 1_000_000).sum()
    if flood_max_med > 30 and flood_mega >= 2 and shares["Storm"] < 0.10:
        regime = "1_BIMODAL_MEGA_FLOOD"
    elif flood_mega >= 7 and flood_max_med < 5 and shares["Flood"] > 0.50:
        regime = "2_STEADY_HIGH_FLOOD"
    elif shares["Storm"] > 0.70:
        regime = "3_STORM_DOMINANT"
    elif shares["Earthquake"] > 0.50:
        regime = "6_EARTHQUAKE_DOMINANT"
    elif shares["Drought"] > 0.50:
        regime = "5_DROUGHT_DOMINANT"
    else:
        regime = "4_MIXED"
    return {"regime": regime, "total": int(total), "shares": shares, "flood_max_med": round(flood_max_med, 1), "flood_mega": int(flood_mega)}

regime6_test = ["NPL", "CHL", "MEX", "IDN", "JPN", "NZL", "ECU", "PER", "TUR", "GRC", "AFG", "ITA", "PHL"]
print(f"\n{'iso':5s} {'regime':30s} {'total':>11s} {'flood%':>7s} {'storm%':>7s} {'eq%':>6s} {'drght%':>7s}")
for iso in regime6_test:
    r = classify_regime(iso)
    if r is None:
        print(f"{iso:5s} NO_DATA")
        continue
    if "shares" not in r or not r["shares"]:
        print(f"{iso:5s} {r['regime']:30s} {r['total']:>11,}")
        continue
    s = r["shares"]
    print(f"{iso:5s} {r['regime']:30s} {r['total']:>11,} {s['Flood']*100:>6.1f}% {s['Storm']*100:>6.1f}% {s['Earthquake']*100:>5.1f}% {s['Drought']*100:>6.1f}%")


# ============================================================
# DIG 003b: USA + PHL + CUB within-Regime-3 bimodality (the storm channel itself)
# ============================================================
hdr("003b", "USA / PHL / CUB year-by-year storm displacement (find Katrina/Sandy/Harvey/Ian-scale events)")

for iso in ["USA", "PHL", "CUB"]:
    sub = gidd_dis[(gidd_dis["ISO3"] == iso) & (gidd_dis["Hazard Type"] == "Storm")]
    yr = sub.groupby("Year")["Disaster Internal Displacements"].sum().sort_index()
    yr = yr[(yr.index >= 2008) & (yr.index <= 2024)]
    print(f"\n{iso} storm-displacement annual:")
    for y, v in yr.items():
        marker = "  *** mega-storm" if v > 1_000_000 else ""
        print(f"   {y}: {int(v):>10,}{marker}")
    if len(yr) > 0:
        print(f"   max/median: {yr.max() / yr.median():.1f}x; mega-years: {(yr > 1_000_000).sum()}")


# ============================================================
# DIG 004a: BRA year-by-year 3-channel breakdown
# ============================================================
hdr("004a", "BRA year-by-year 3-channel — which years drive conf-drought 0.697?")

bra_conf = gidd_conf[gidd_conf["ISO3"] == "BRA"][["Year", "Conflict Internal Displacements"]].rename(columns={"Year":"year","Conflict Internal Displacements":"conf"})
bra_dis = gidd_dis[gidd_dis["ISO3"] == "BRA"]
bra_flood = bra_dis[bra_dis["Hazard Type"] == "Flood"].groupby("Year")["Disaster Internal Displacements"].sum().reset_index().rename(columns={"Year":"year","Disaster Internal Displacements":"flood"})
bra_drought = bra_dis[bra_dis["Hazard Type"] == "Drought"].groupby("Year")["Disaster Internal Displacements"].sum().reset_index().rename(columns={"Year":"year","Disaster Internal Displacements":"drought"})
bra = bra_conf.merge(bra_flood, on="year", how="outer").merge(bra_drought, on="year", how="outer")
bra = bra[(bra["year"] >= 2008) & (bra["year"] <= 2024)].fillna(0).sort_values("year")
print(bra.to_string(index=False))
print(f"\nBRA Spearman: conf-drought = {spearmanr(bra['conf'], bra['drought'])[0]:.3f}")


# ============================================================
# DIG 004b: More countries through 3-channel where drought data exists
# ============================================================
hdr("004b", "Extended 3-channel test — which countries have meaningful drought data?")

extended = ["AGO","MOZ","COL","IND","TUR","BRA","HTI","DOM","CUB","USA","FJI","VUT","SLB","PHL","SOM","SDN","PAK","BFA","NER","KEN","ETH","AFG","HUN","VEN","RUS","UKR","COD","CAF","MEX","NPL"]
print(f"\n{'iso':5s} {'conf_years':>11s} {'flood_yrs':>11s} {'drought_yrs':>12s} {'rho(CF)':>9s} {'rho(CD)':>9s} {'rho(FD)':>9s}")
for iso in extended:
    c = gidd_conf[gidd_conf["ISO3"] == iso].groupby("Year")["Conflict Internal Displacements"].sum().reset_index().rename(columns={"Year":"year","Conflict Internal Displacements":"conf"})
    d_all = gidd_dis[gidd_dis["ISO3"] == iso]
    f = d_all[d_all["Hazard Type"]=="Flood"].groupby("Year")["Disaster Internal Displacements"].sum().reset_index().rename(columns={"Year":"year","Disaster Internal Displacements":"flood"})
    d = d_all[d_all["Hazard Type"]=="Drought"].groupby("Year")["Disaster Internal Displacements"].sum().reset_index().rename(columns={"Year":"year","Disaster Internal Displacements":"drought"})
    df = c.merge(f, on="year", how="outer").merge(d, on="year", how="outer")
    df = df[(df["year"] >= 2008) & (df["year"] <= 2024)].fillna(0)
    cf_y = (df["conf"] > 0).sum()
    fl_y = (df["flood"] > 0).sum()
    dr_y = (df["drought"] > 0).sum()
    if len(df) < 5 or dr_y < 3:
        print(f"{iso:5s} {cf_y:>11d} {fl_y:>11d} {dr_y:>12d}    (insufficient drought variance)")
        continue
    r1, _ = spearmanr(df["conf"], df["flood"])
    r2, _ = spearmanr(df["conf"], df["drought"])
    r3, _ = spearmanr(df["flood"], df["drought"])
    flag = ""
    if abs(r2) > 0.5: flag += " ***CD"
    if abs(r1) > 0.5: flag += " ***CF"
    if abs(r3) > 0.5: flag += " ***FD"
    print(f"{iso:5s} {cf_y:>11d} {fl_y:>11d} {dr_y:>12d} {r1:>9.3f} {r2:>9.3f} {r3:>9.3f}{flag}")


# ============================================================
# DIG 005a: Sliding 10-year windows for HUN/TUR/VEN/RUS + IND
# ============================================================
hdr("005a", "Bukelization sliding 10-year windows — find best-fit window for each")

def sliding_windows(iso, window_len=10, start_min_libdem=0.30, delta_max=-0.30):
    df = vdem[vdem["iso3"] == iso].sort_values("year")
    results = []
    for y_start in range(1990, 2016):
        s = df[df["year"] == y_start]
        e = df[df["year"] == y_start + window_len]
        if not (len(s) and len(e)):
            continue
        sv, ev = s["libdem"].iloc[0], e["libdem"].iloc[0]
        delta = ev - sv
        window = df[(df["year"] >= y_start) & (df["year"] <= y_start + window_len)].sort_values("year")
        yoy = window["libdem"].diff().dropna()
        n_increases = (yoy > 0.02).sum()
        monotonic = n_increases <= 2  # relaxed for 10y window
        range_ok = sv >= start_min_libdem
        delta_ok = delta <= delta_max
        if range_ok and delta_ok and monotonic:
            results.append((y_start, sv, ev, delta, monotonic, n_increases))
    return results

for iso in ["HUN","TUR","VEN","RUS","IND","BRA","USA","SLV","POL"]:
    res = sliding_windows(iso)
    if res:
        print(f"\n{iso}: {len(res)} fitting 10y windows")
        for y_start, sv, ev, delta, mono, n_inc in res:
            print(f"   {y_start}-{y_start+10}: {sv:.3f} -> {ev:.3f}, delta={delta:+.3f}, mono={mono}, up-yrs={n_inc}")
    else:
        print(f"\n{iso}: NO FITTING 10y windows (no Bukelization signature)")


# ============================================================
# DIG 005b: IND full trajectory 2000-2024 (the live candidate)
# ============================================================
hdr("005b", "IND full libdem trajectory 2000-2024 + monotonicity check")

ind_full = vdem[(vdem["iso3"] == "IND") & (vdem["year"] >= 2000)].sort_values("year")
print(ind_full[["year","libdem"]].to_string(index=False))
ind_yoy = ind_full["libdem"].diff().dropna()
print(f"\nMonotonicity (10-year tail 2014-2024): YoY changes")
recent = ind_full[ind_full["year"] >= 2014]
for _, row in recent.iterrows():
    yr = int(row["year"])
    prev = ind_full[ind_full["year"] == yr-1]
    if len(prev):
        delta = row["libdem"] - prev["libdem"].iloc[0]
        marker = " up" if delta > 0 else (" down" if delta < 0 else " flat")
        print(f"   {yr}: {row['libdem']:.3f} ({delta:+.3f}){marker}")


# ============================================================
# DIG 005c: USA + DEU + GBR retrospective check
# ============================================================
hdr("005c", "USA / DEU / GBR / FRA 10-year sliding windows (negative-control check)")
for iso in ["USA","DEU","GBR","FRA","CAN","NLD","JPN"]:
    res = sliding_windows(iso)
    if res:
        print(f"\n{iso}: {len(res)} fitting 10y windows  *** UNEXPECTED for negative control")
        for y_start, sv, ev, delta, mono, n_inc in res[:3]:
            print(f"   {y_start}-{y_start+10}: {sv:.3f} -> {ev:.3f}, delta={delta:+.3f}")
    else:
        print(f"{iso}: NO fitting windows (consistent with negative-control prediction)")


print("\n" + "="*80)
print("DEEP DIG COMPLETE")
print("="*80)
