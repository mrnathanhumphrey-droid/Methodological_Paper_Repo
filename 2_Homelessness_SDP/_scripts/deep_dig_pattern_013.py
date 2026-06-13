"""Deep extraction on PATTERN_013 Bukelization.

Bukelization = libdem collapse without coup, via civilian-authoritarian consolidation.
Firmed across 5 countries: SLV, HUN, TUR, VEN, POL.
Falsified for: RUS, IND, BRA, USA.

This script extracts:
A. Full V-Dem libdem trajectory 1990-2024 for all 5 confirming countries
B. Full trajectory for falsification cases (RUS/IND/BRA/USA) — why they DON'T fit
C. Sub-indicators of libdem: judicial independence, media freedom, civil liberties, elections clean
   — DOES the SHAPE generalize on each sub-indicator?
D. Displacement consequences: do Bukelization countries show displacement spikes?
E. UCDP fatality data: confirm no coup, no interstate war for each case
F. Recovery dynamics: POL 2023 + BRA 2023 deep look
G. New unpredicted candidates: SRB, BGR, ROU, NIC, BOL, PHL (Duterte era)
H. Forward look at IND (the slow-burn candidate)
I. Speed comparison: how fast do different countries Bukelize?
J. Leader-tenure alignment: when did each consolidation actually start?
"""
import pathlib
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np

ROOT = pathlib.Path("D:/IDP")
DATA = ROOT / "data"

print("[load] V-Dem full")
vdem = pd.read_csv(DATA / "vdem" / "vdem_vdem.csv", low_memory=False)
# Keep relevant sub-indicators
keep_cols = [
    "country_text_id", "country_name", "year",
    "v2x_libdem", "v2x_polyarchy",  # liberal democracy + electoral democracy
    "v2x_jucon",  # judicial constraints on executive
    "v2x_freexp_altinf",  # freedom of expression + alternative information
    "v2xcl_rol",  # equality before the law / rule of law index
    "v2x_clpol",  # political civil liberties
    "v2elfrfair",  # elections free and fair
    "v2juhcind",  # high court independence
    "v2mecenefm",  # gov censorship of media
    "v2cseeorgs",  # civil society entry/exit
]
existing = [c for c in keep_cols if c in vdem.columns]
print(f"  V-Dem cols available: {existing}")
vdem = vdem[existing].rename(columns={"country_text_id": "iso3"})

print("[load] UCDP-GED")
ged = pd.read_csv(DATA / "ucdp" / "GEDEvent_v25_1.csv", low_memory=False)
print("[load] GIDD displacement")
gidd_conf = pd.read_excel(DATA / "idmc_gidd" / "IDMC_GIDD_Conflict_Violence_Disasters.xlsx",
                          sheet_name="1_Displacement_data")

print("[load] done\n")


def hdr(letter, title):
    print("\n" + "="*80)
    print(f"DIG {letter}: {title}")
    print("="*80)


# Country name to UCDP-GED label
UCDP_NAME = {
    "SLV": "El Salvador", "HUN": "Hungary", "TUR": "Turkey", "VEN": "Venezuela",
    "POL": "Poland", "RUS": "Russia (Soviet Union)", "IND": "India", "BRA": "Brazil",
    "USA": "United States of America", "SRB": "Serbia (Yugoslavia)", "BGR": "Bulgaria",
    "ROU": "Romania", "NIC": "Nicaragua", "BOL": "Bolivia", "PHL": "Philippines",
}


# ============================================================
# A. Full libdem trajectory 1990-2024 for 5 confirming + 4 falsifying
# ============================================================
hdr("A", "Full libdem trajectory 1990-2024 — 5 confirming + 4 falsifying")

confirm = ["SLV", "HUN", "TUR", "VEN", "POL"]
falsify = ["RUS", "IND", "BRA", "USA"]
years_show = list(range(1990, 2026, 2))  # every other year
print(f"\n{'iso':5s}  " + "  ".join([f"{y:>4d}" for y in years_show]))
for iso in confirm + falsify:
    vals = []
    for y in years_show:
        r = vdem[(vdem["iso3"] == iso) & (vdem["year"] == y)]
        vals.append(r["v2x_libdem"].iloc[0] if len(r) else None)
    print(f"{iso:5s}  " + "  ".join([f"{v:.2f}" if v is not None else " NA " for v in vals]))


# ============================================================
# B. Sub-indicators on each Bukelization country — does the SHAPE generalize?
# ============================================================
hdr("B", "Sub-indicator generalization — judicial / media / civil liberties / elections")

subind = {
    "v2x_jucon": "judicial constraints",
    "v2x_freexp_altinf": "free expression + alt info",
    "v2elfrfair": "elections free + fair",
    "v2juhcind": "high court independence",
    "v2mecenefm": "media censorship (higher = MORE censorship)",
    "v2cseeorgs": "civil society entry/exit",
}

for iso, leader_window in [
    ("SLV", (2019, 2024)), ("HUN", (2010, 2024)), ("TUR", (2003, 2024)),
    ("VEN", (1999, 2018)), ("POL", (2015, 2024)),
]:
    y1, y2 = leader_window
    print(f"\n{iso} ({y1}-{y2}):  libdem  " + "  ".join([f"{name}" for col, name in subind.items() if col in vdem.columns]))
    row_start = vdem[(vdem["iso3"] == iso) & (vdem["year"] == y1)]
    row_end = vdem[(vdem["iso3"] == iso) & (vdem["year"] == y2)]
    if not (len(row_start) and len(row_end)):
        print(f"  missing endpoint data")
        continue
    libdem_d = row_end["v2x_libdem"].iloc[0] - row_start["v2x_libdem"].iloc[0]
    sub_deltas = []
    for col in subind:
        if col not in vdem.columns:
            continue
        s = row_start[col].iloc[0]
        e = row_end[col].iloc[0]
        sub_deltas.append(f"{e-s:+.3f}")
    print(f"  start   {row_start['v2x_libdem'].iloc[0]:.3f}   " + "   ".join([f"{row_start[c].iloc[0]:.3f}" for c in subind if c in vdem.columns]))
    print(f"  end     {row_end['v2x_libdem'].iloc[0]:.3f}   " + "   ".join([f"{row_end[c].iloc[0]:.3f}" for c in subind if c in vdem.columns]))
    print(f"  delta   {libdem_d:+.3f}   " + "   ".join(sub_deltas))


# ============================================================
# C. Displacement consequence — do Bukelization countries show displacement?
# ============================================================
hdr("C", "Displacement consequence — GIDD conflict-IDP during consolidation")

for iso in confirm:
    d = gidd_conf[gidd_conf["ISO3"] == iso][["Year", "Conflict Internal Displacements"]].sort_values("Year")
    if len(d) == 0:
        print(f"\n{iso}: no GIDD conflict-displacement data")
        continue
    print(f"\n{iso} conflict-displacement (GIDD):")
    print(d.to_string(index=False))


# ============================================================
# D. UCDP fatality data — confirm no coup signal during consolidation
# ============================================================
hdr("D", "UCDP fatality data — confirm no coup-like fatality jump during consolidation")

for iso, window in [("SLV", (2019,2024)), ("HUN", (2010,2024)), ("TUR", (2003,2024)),
                     ("VEN", (1999,2018)), ("POL", (2015,2024))]:
    name = UCDP_NAME[iso]
    y1, y2 = window
    sub = ged[(ged["country"] == name) & (ged["year"] >= y1) & (ged["year"] <= y2)]
    state = sub[sub["type_of_violence"] == 1].groupby("year")["best"].sum()
    one_sided = sub[sub["type_of_violence"] == 3].groupby("year")["best"].sum()
    print(f"\n{iso} ({y1}-{y2}) UCDP annual: events={len(sub)}, total_fatal={sub['best'].sum()}")
    if len(state):
        print(f"   state-based by year: {dict(state.astype(int))}")
    if len(one_sided):
        print(f"   one-sided by year: {dict(one_sided.astype(int))}")


# ============================================================
# E. Recovery dynamics — POL + BRA 2023
# ============================================================
hdr("E", "Recovery dynamics — POL 2023 (Tusk) + BRA 2023 (Lula)")

for iso in ["POL", "BRA"]:
    print(f"\n{iso} libdem 2015-2025:")
    sub = vdem[(vdem["iso3"] == iso) & (vdem["year"] >= 2015) & (vdem["year"] <= 2025)].sort_values("year")
    for _, row in sub.iterrows():
        print(f"   {int(row['year'])}: libdem={row['v2x_libdem']:.3f}")

    # Sub-indicator recovery check
    print(f"\n   sub-indicator changes 2022 -> 2024:")
    r22 = vdem[(vdem["iso3"] == iso) & (vdem["year"] == 2022)]
    r24 = vdem[(vdem["iso3"] == iso) & (vdem["year"] == 2024)]
    if len(r22) and len(r24):
        for col, name in subind.items():
            if col not in vdem.columns:
                continue
            d = r24[col].iloc[0] - r22[col].iloc[0]
            sign = "RECOVERY" if d > 0.05 else ("CONTINUED DECLINE" if d < -0.05 else "stable")
            print(f"      {name:35s}: {r22[col].iloc[0]:.3f} -> {r24[col].iloc[0]:.3f} ({d:+.3f}) {sign}")


# ============================================================
# F. New candidate scan — SRB, BGR, ROU, NIC, BOL, PHL
# ============================================================
hdr("F", "New unpredicted candidates — scan for Bukelization shape (sliding 10y windows)")

def sliding(iso, window_len=10):
    df = vdem[vdem["iso3"] == iso].sort_values("year")
    results = []
    for y_start in range(1990, 2016):
        s = df[df["year"] == y_start]
        e = df[df["year"] == y_start + window_len]
        if not (len(s) and len(e)):
            continue
        sv, ev = s["v2x_libdem"].iloc[0], e["v2x_libdem"].iloc[0]
        delta = ev - sv
        win = df[(df["year"] >= y_start) & (df["year"] <= y_start + window_len)].sort_values("year")
        yoy = win["v2x_libdem"].diff().dropna()
        n_up = (yoy > 0.02).sum()
        mono = n_up <= 2
        if sv >= 0.30 and delta <= -0.30 and mono:
            results.append((y_start, sv, ev, delta, n_up))
    return results

candidates = ["SRB", "BGR", "ROU", "NIC", "BOL", "PHL", "BIH", "TUN", "MDG", "ZWE", "BLR", "NPL", "ECU"]
for iso in candidates:
    res = sliding(iso)
    if res:
        print(f"\n{iso}: {len(res)} fitting 10y window(s)")
        for y, s, e, d, n in res[:3]:
            print(f"   {y}-{y+10}: {s:.3f} -> {e:.3f}, delta={d:+.3f}, up-years={n}")
    else:
        # Check if started high but didn't fit
        df = vdem[vdem["iso3"] == iso].sort_values("year")
        max_libdem = df[df["year"] >= 1995]["v2x_libdem"].max() if len(df) else None
        latest = df[df["year"] == 2024]["v2x_libdem"].iloc[0] if len(df[df["year"]==2024]) else None
        print(f"{iso}: NO fit; max libdem since 1995 = {max_libdem}, 2024 = {latest}")


# ============================================================
# G. IND deep look (the slow-burn candidate)
# ============================================================
hdr("G", "IND slow-burn — sub-indicators 2014-2024 + comparison with confirming cases")

ind = vdem[(vdem["iso3"] == "IND") & (vdem["year"] >= 2010)].sort_values("year")
print("\nIND year-by-year libdem + key sub-indicators:")
header = "year   libdem  jucon  freexp  el_ff   hcind  cens(hi=bad)"
print(header)
for _, row in ind.iterrows():
    y = int(row['year'])
    vals = []
    for c in ["v2x_libdem","v2x_jucon","v2x_freexp_altinf","v2elfrfair","v2juhcind","v2mecenefm"]:
        if c in vdem.columns:
            vals.append(f"{row[c]:.3f}" if pd.notna(row[c]) else " NA  ")
    print(f"{y}   " + "  ".join(vals))

# Sliding 14-year window for IND
print("\nIND extended sliding windows (12y, 14y, 16y):")
df = vdem[vdem["iso3"] == "IND"].sort_values("year")
for wlen in [12, 14, 16, 18, 20, 22, 24]:
    for y_start in range(1998, 2012):
        s = df[df["year"] == y_start]
        e = df[df["year"] == y_start + wlen]
        if not (len(s) and len(e)):
            continue
        sv, ev = s["v2x_libdem"].iloc[0], e["v2x_libdem"].iloc[0]
        delta = ev - sv
        if sv >= 0.30 and delta <= -0.30:
            win = df[(df["year"] >= y_start) & (df["year"] <= y_start + wlen)]
            yoy = win["v2x_libdem"].diff().dropna()
            n_up = (yoy > 0.02).sum()
            mono = n_up <= 3
            mark = " FITS" if mono else " non-mono"
            print(f"   {wlen}y window {y_start}-{y_start+wlen}: {sv:.3f} -> {ev:.3f}, delta={delta:+.3f}, up-yrs={n_up}{mark}")


# ============================================================
# H. Speed comparison — how fast does each Bukelization country fall?
# ============================================================
hdr("H", "Bukelization speed — Δ per year for each confirming country")

speed = []
for iso, window in [("SLV", (2019,2024)), ("HUN", (2010,2020)), ("TUR", (2007,2017)),
                     ("VEN", (1997,2007)), ("POL", (2010,2020))]:
    y1, y2 = window
    s = vdem[(vdem["iso3"] == iso) & (vdem["year"] == y1)]["v2x_libdem"].iloc[0]
    e = vdem[(vdem["iso3"] == iso) & (vdem["year"] == y2)]["v2x_libdem"].iloc[0]
    delta = e - s
    rate = delta / (y2 - y1)
    speed.append((iso, y1, y2, s, e, delta, rate))
print(f"\n{'iso':5s} {'window':>11s} {'start':>7s} {'end':>7s} {'delta':>7s} {'delta/yr':>10s}")
for iso, y1, y2, s, e, d, r in sorted(speed, key=lambda x: x[6]):
    print(f"{iso:5s} {y1}-{y2}  {s:>7.3f} {e:>7.3f} {d:>+7.3f} {r:>+10.4f}")


# ============================================================
# I. Leader-tenure alignment
# ============================================================
hdr("I", "Leader-tenure alignment — when did consolidation actually start?")

leaders = {
    "SLV": [("Bukele FMLN→Nuevas Ideas", 2019, "state-of-exception 2022")],
    "HUN": [("Orbán return (Fidesz)", 2010, "2/3 supermajority + 2011 Fundamental Law")],
    "TUR": [("Erdoğan PM/AKP", 2003, "2007 const referendum; 2017 const referendum")],
    "VEN": [("Chávez", 1999, "1999 const + Bolivarian Revolution")],
    "POL": [("PiS (Kaczyński/Duda/Morawiecki)", 2015, "2015 Constitutional Tribunal capture")],
}
for iso, evs in leaders.items():
    for name, start_yr, key_event in evs:
        sd = vdem[(vdem["iso3"] == iso) & (vdem["year"] == start_yr)]
        if len(sd):
            print(f"{iso} {name} took office {start_yr}: libdem={sd['v2x_libdem'].iloc[0]:.3f} | key event: {key_event}")


print("\n" + "="*80)
print("PATTERN_013 DEEP DIG COMPLETE")
print("="*80)
