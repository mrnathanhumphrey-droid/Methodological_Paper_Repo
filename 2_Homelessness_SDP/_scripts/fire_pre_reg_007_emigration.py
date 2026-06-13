"""Fire PRE_REG_007: Emigration-Backsliding Feedback Loop.

H1: emigration ↔ libdem decline feedback loop
H2: within-country lagged correlation
H3: cross-country emigration % vs libdem Δ
"""
import pathlib
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
from scipy.stats import spearmanr, pearsonr

ROOT = pathlib.Path("D:/IDP")
DATA = ROOT / "data"

# Load V-Dem
vdem = pd.read_csv(DATA / "vdem" / "vdem_vdem.csv", low_memory=False)
vdem = vdem[["country_text_id", "year", "v2x_libdem"]].rename(columns={"country_text_id": "iso3"})

# Load UNHCR RDF
rdf = pd.read_csv(DATA / "unhcr_rdf" / "extracted" / "population.csv", low_memory=False, encoding="utf-8")
# Use Country of origin (ISO) for emigration FROM that country
rdf = rdf.rename(columns={"Country of origin (ISO)": "iso3_origin", "Year": "year"})
# Total emigration = refugees + asylum-seekers OUT (regardless of destination)
rdf["Refugees under UNHCR's mandate"] = pd.to_numeric(rdf["Refugees under UNHCR's mandate"], errors="coerce").fillna(0)
rdf["Asylum-seekers"] = pd.to_numeric(rdf["Asylum-seekers"], errors="coerce").fillna(0)
rdf["emig_total"] = rdf["Refugees under UNHCR's mandate"] + rdf["Asylum-seekers"]
emig = rdf.groupby(["iso3_origin", "year"])["emig_total"].sum().reset_index().rename(columns={"iso3_origin": "iso3"})

# Population from WB WDI for percentage-of-population
wdi = pd.read_csv(DATA / "wb_wdi" / "extracted" / "WDICSV.csv", low_memory=False)
pop = wdi[wdi["Indicator Code"] == "SP.POP.TOTL"].copy()
year_cols = [c for c in pop.columns if c.isdigit()]
pop_long = pop.melt(id_vars=["Country Code"], value_vars=year_cols, var_name="year", value_name="population")
pop_long["year"] = pop_long["year"].astype(int)
pop_long = pop_long.rename(columns={"Country Code": "iso3"})
pop_long = pop_long.dropna(subset=["population"])

# Define Bukelization cases + consolidation windows
cases = {
    "SLV": ("Bukele", 2019, 2024),
    "HUN": ("Orbán", 2010, 2024),
    "TUR": ("Erdoğan", 2003, 2024),
    "VEN": ("Chávez/Maduro", 1999, 2024),
    "POL": ("PiS", 2015, 2023),
    "TUN": ("Saied", 2019, 2024),
    "BLR": ("Lukashenko", 1994, 2024),
    "IND": ("Modi", 2014, 2024),
    "USA": ("Trump (combined)", 2017, 2024),
    "SRB": ("Vučić", 2012, 2024),
}

def hdr(t):
    print("\n" + "="*80)
    print(t)
    print("="*80)


hdr("CROSS-COUNTRY ANALYSIS (PRE_REG_007 Prediction A)")
print()
print(f"{'iso':4s} {'window':>12s} {'libdem_start':>13s} {'libdem_end':>11s} {'delta':>8s} {'emig_total':>12s} {'pop_avg':>14s} {'emig_pct':>10s}")

results = []
for iso, (label, y1, y2) in cases.items():
    # libdem
    s = vdem[(vdem["iso3"] == iso) & (vdem["year"] == y1)]
    e = vdem[(vdem["iso3"] == iso) & (vdem["year"] == y2)]
    if not (len(s) and len(e)):
        continue
    sv, ev = s["v2x_libdem"].iloc[0], e["v2x_libdem"].iloc[0]
    libdem_delta = ev - sv

    # Cumulative emigration during window (using END-state stock as proxy — refugees+asylum-seekers from this country in 2024 vs 2010)
    emig_start = emig[(emig["iso3"] == iso) & (emig["year"] == y1)]["emig_total"].sum()
    emig_end = emig[(emig["iso3"] == iso) & (emig["year"] == y2)]["emig_total"].sum()
    emig_added = emig_end - emig_start

    # Population (avg of window)
    pop_window = pop_long[(pop_long["iso3"] == iso) & (pop_long["year"] >= y1) & (pop_long["year"] <= y2)]
    pop_avg = pop_window["population"].mean() if len(pop_window) else None

    emig_pct = (emig_added / pop_avg * 100) if pop_avg else None
    print(f"{iso:4s} {y1}-{y2:>4d}  {sv:>13.3f} {ev:>11.3f} {libdem_delta:>+8.3f} {int(emig_added):>12,} {int(pop_avg) if pop_avg else 'NA':>14} {emig_pct:>9.2f}%" if pop_avg else f"{iso:4s} {y1}-{y2}  (no pop data)")
    results.append((iso, libdem_delta, emig_pct, emig_added, pop_avg))


# Pearson + Spearman correlation
hdr("CROSS-COUNTRY CORRELATION (n=10 with USA + SRB included)")
valid = [(iso, ld, ep) for iso, ld, ep, _, _ in results if ep is not None and pd.notna(ep)]
isos = [r[0] for r in valid]
deltas = [r[1] for r in valid]
emig_pcts = [r[2] for r in valid]
print(f"\nn = {len(valid)}")
print(f"Countries: {isos}")
r_p, p_p = pearsonr(deltas, emig_pcts)
r_s, p_s = spearmanr(deltas, emig_pcts)
print(f"\nPearson r (libdem_delta, emig_pct) = {r_p:.3f}  (p={p_p:.4f})")
print(f"Spearman ρ (libdem_delta, emig_pct) = {r_s:.3f}  (p={p_s:.4f})")
print(f"\nExpected sign: NEGATIVE (more emigration → more libdem decline)")

# VEN-removed sensitivity
hdr("SENSITIVITY TEST — VEN removed")
no_ven = [(iso, ld, ep) for iso, ld, ep in zip(isos, deltas, emig_pcts) if iso != "VEN"]
isos_nv = [r[0] for r in no_ven]
deltas_nv = [r[1] for r in no_ven]
pcts_nv = [r[2] for r in no_ven]
r_p2, p_p2 = pearsonr(deltas_nv, pcts_nv)
r_s2, p_s2 = spearmanr(deltas_nv, pcts_nv)
print(f"\nn = {len(no_ven)} (VEN excluded)")
print(f"Pearson r = {r_p2:.3f}  (p={p_p2:.4f})")
print(f"Spearman ρ = {r_s2:.3f}  (p={p_s2:.4f})")


# Within-country year-by-year lagged correlation
hdr("WITHIN-COUNTRY LAGGED CORRELATION (PRE_REG_007 Prediction B)")
print("\nFor each case, test ρ(emig_t, libdem_decline_{t+1}) at annual level during consolidation window")
print(f"\n{'iso':4s} {'years':>5s} {'mean_emig_yoy':>15s} {'rho(emig_t, lib_dec_t+1)':>26s}")
for iso, (label, y1, y2) in cases.items():
    # Annual emigration
    e_annual = emig[(emig["iso3"] == iso) & (emig["year"] >= y1) & (emig["year"] <= y2)].sort_values("year")
    if len(e_annual) < 5:
        continue
    e_annual = e_annual.set_index("year")["emig_total"]
    # Annual libdem
    v_annual = vdem[(vdem["iso3"] == iso) & (vdem["year"] >= y1) & (vdem["year"] <= y2 + 1)].sort_values("year")
    if len(v_annual) < 5:
        continue
    v_annual = v_annual.set_index("year")["v2x_libdem"]
    libdem_decline = -v_annual.diff()  # positive value = libdem dropped
    # Align: emig_year_t with libdem_decline_year_{t+1}
    pairs = []
    for y in range(y1, y2):
        if y in e_annual.index and (y+1) in libdem_decline.index and not pd.isna(libdem_decline[y+1]):
            pairs.append((e_annual[y], libdem_decline[y+1]))
    if len(pairs) < 4:
        print(f"{iso:4s} {len(pairs):>5d}   (insufficient pairs)")
        continue
    e_vals = [p[0] for p in pairs]
    d_vals = [p[1] for p in pairs]
    rho, p = spearmanr(e_vals, d_vals)
    mean_yoy = np.mean(np.diff(e_vals)) if len(e_vals) > 1 else 0
    flag = " *** ≥+0.4" if rho >= 0.4 else ""
    print(f"{iso:4s} {len(pairs):>5d} {int(mean_yoy):>15,} {rho:>26.3f}{flag}")


# VEN deep dive (the anchor case)
hdr("VEN DEEP-DIVE (anchor case for cross-country correlation)")
ven_e = emig[(emig["iso3"] == "VEN") & (emig["year"] >= 1999)].sort_values("year")
ven_v = vdem[(vdem["iso3"] == "VEN") & (vdem["year"] >= 1999)].sort_values("year")
print(f"\n{'year':>5s} {'libdem':>7s} {'emig_stock':>12s}")
for y in range(1999, 2025):
    e_row = ven_e[ven_e["year"] == y]
    v_row = ven_v[ven_v["year"] == y]
    if len(e_row) and len(v_row):
        print(f"{y:>5d} {v_row['v2x_libdem'].iloc[0]:>7.3f} {int(e_row['emig_total'].iloc[0]):>12,}")


# POL reverse brain drain check
hdr("POL REVERSE BRAIN DRAIN CHECK (PRE_REG_007 Prediction C)")
pol_e = emig[(emig["iso3"] == "POL") & (emig["year"] >= 2015)].sort_values("year")
pol_v = vdem[(vdem["iso3"] == "POL") & (vdem["year"] >= 2015)].sort_values("year")
print(f"\n{'year':>5s} {'libdem':>7s} {'emig_stock':>12s}")
for y in range(2015, 2026):
    e_row = pol_e[pol_e["year"] == y]
    v_row = pol_v[pol_v["year"] == y]
    if len(e_row) and len(v_row):
        print(f"{y:>5d} {v_row['v2x_libdem'].iloc[0]:>7.3f} {int(e_row['emig_total'].iloc[0]):>12,}")


print("\n" + "="*80)
print("PRE_REG_007 FIT COMPLETE")
print("="*80)
