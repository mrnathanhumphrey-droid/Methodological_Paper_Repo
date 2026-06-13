"""Fire I + J + K + L: UN DESA emigration retest, POL reverse drain check, 2x2 typology, durability monitoring."""
import pathlib
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
from scipy.stats import spearmanr, pearsonr

ROOT = pathlib.Path("D:/IDP")
DATA = ROOT / "data"

vdem = pd.read_csv(DATA / "vdem" / "vdem_vdem.csv", low_memory=False)

# UN DESA emigration stock (by origin)
desa = pd.read_excel(DATA / "un_desa_migration" / "undesa_2024_origin.xlsx",
                     sheet_name="Table 1", skiprows=10)
desa = desa.rename(columns={"Region, development group, country or area": "country"})


def get_desa_stock(country_substr, year):
    """Return emigrant stock for a country in given year (1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024)."""
    m = desa[desa["country"].astype(str).str.contains(country_substr, regex=False, na=False, case=False)]
    if not len(m) or year not in m.columns:
        return None
    return m[year].iloc[0]


# Country mapping
COUNTRY_DESA_KEY = {
    "SLV": "El Salvador",
    "HUN": "Hungary",
    "TUR": "Türkiye",
    "VEN": "Venezuela",
    "POL": "Poland",
    "TUN": "Tunisia",
    "BLR": "Belarus",
    "IND": "India",
    "USA": "United States",
    "SRB": "Serbia",
    "BGD": "Bangladesh",
    "BRA": "Brazil",
    "NIC": "Nicaragua",
}


def hdr(t, n=""):
    print("\n" + "="*80)
    print(f"{n}: {t}")
    print("="*80)


# Population for normalization
wdi = pd.read_csv(DATA / "wb_wdi" / "extracted" / "WDICSV.csv", low_memory=False)
pop = wdi[wdi["Indicator Code"] == "SP.POP.TOTL"].copy()
year_cols = [c for c in pop.columns if c.isdigit()]
pop_long = pop.melt(id_vars=["Country Code"], value_vars=year_cols, var_name="year", value_name="population")
pop_long["year"] = pop_long["year"].astype(int)
pop_long = pop_long.rename(columns={"Country Code": "iso3"}).dropna(subset=["population"])


# ============================================================
# I. UN DESA emigration retest of PRE_REG_007 (v2 reframe)
# ============================================================
hdr("UN DESA emigration retest — does emigration LEAD or LAG libdem decline?", "I")

cases = [
    ("SLV", "El Salvador", 2019, 2024),
    ("HUN", "Hungary", 2010, 2024),
    ("TUR", "Türkiye", 2003, 2024),
    ("VEN", "Venezuela", 1999, 2024),
    ("POL", "Poland", 2015, 2024),
    ("TUN", "Tunisia", 2019, 2024),
    ("BLR", "Belarus", 1994, 2024),
    ("IND", "India", 2014, 2024),
    ("USA", "United States", 2017, 2024),
    ("SRB", "Serbia", 2012, 2024),
    ("BGD", "Bangladesh", 2009, 2024),
    ("BRA", "Brazil", 2018, 2022),
]

print(f"\n{'iso':4s} {'window':>9s} {'libdem_Δ':>9s} {'emig_start':>12s} {'emig_end':>12s} {'emig_Δ':>11s} {'pop_avg':>14s} {'emig_pct':>10s}")
results = []
for iso, name, y1, y2 in cases:
    s = vdem[(vdem["country_text_id"] == iso) & (vdem["year"] == y1)]
    e = vdem[(vdem["country_text_id"] == iso) & (vdem["year"] == y2)]
    if not (len(s) and len(e)):
        continue
    sv = s["v2x_libdem"].iloc[0]
    ev = e["v2x_libdem"].iloc[0]
    libdem_delta = ev - sv

    # Closest DESA years
    desa_years = [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024]
    y1_desa = min(desa_years, key=lambda y: abs(y - y1))
    y2_desa = min(desa_years, key=lambda y: abs(y - y2))
    emig_s = get_desa_stock(name, y1_desa)
    emig_e = get_desa_stock(name, y2_desa)
    if emig_s is None or emig_e is None:
        continue
    emig_delta = emig_e - emig_s

    pop_w = pop_long[(pop_long["iso3"] == iso) & (pop_long["year"] >= y1) & (pop_long["year"] <= y2)]
    pop_avg = pop_w["population"].mean() if len(pop_w) else None
    emig_pct = (emig_delta / pop_avg * 100) if pop_avg else None

    print(f"{iso:4s} {y1}-{y2:>4d} {libdem_delta:>+9.3f} {int(emig_s):>12,} {int(emig_e):>12,} {int(emig_delta):>+11,} {int(pop_avg) if pop_avg else 'NA':>14} {emig_pct:>9.2f}%")
    results.append((iso, libdem_delta, emig_pct, emig_delta, pop_avg))


print()
valid = [(i, ld, ep) for i, ld, ep, _, _ in results if ep is not None and pd.notna(ep)]
isos = [r[0] for r in valid]
ld = [r[1] for r in valid]
ep = [r[2] for r in valid]
r_p, p_p = pearsonr(ld, ep)
r_s, p_s = spearmanr(ld, ep)
print(f"UN DESA cross-country (n={len(valid)}):")
print(f"  Pearson r(libdem_Δ, emig_pct) = {r_p:.3f} (p={p_p:.4f})")
print(f"  Spearman ρ = {r_s:.3f} (p={p_s:.4f})")
print(f"  Expected: negative (more emigration → more libdem decline)")

# VEN-removed
no_ven = [(i, l, e) for i, l, e in zip(isos, ld, ep) if i != "VEN"]
if len(no_ven) >= 3:
    r_p2, p_p2 = pearsonr([r[1] for r in no_ven], [r[2] for r in no_ven])
    print(f"\nVEN-removed (n={len(no_ven)}): Pearson r = {r_p2:.3f} (p={p_p2:.4f})")


# VEN deep-chronology: stock at every year vs libdem
hdr("VEN UN DESA stock vs V-Dem libdem — pre-vs-post crisis chronology", "I.b")
ven_stocks = {}
for y in [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024]:
    v = get_desa_stock("Venezuela", y)
    ven_stocks[y] = int(v) if v else None
ven_lib = vdem[(vdem["country_text_id"] == "VEN") & (vdem["year"].isin([1990,1995,2000,2005,2010,2015,2020,2024]))].sort_values("year")
print(f"\n{'year':>5} {'libdem':>7} {'emig_stock':>12} {'libdem chunk':>25}")
prev_lib = None
prev_emig = None
for y in [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024]:
    v = ven_lib[ven_lib["year"] == y]
    lib = v["v2x_libdem"].iloc[0] if len(v) else None
    emig = ven_stocks[y]
    if prev_lib is not None and prev_emig is not None:
        lib_change = (lib - prev_lib) if lib else None
        emig_pct_change = ((emig - prev_emig) / prev_emig * 100) if prev_emig else None
        print(f"{y:>5} {lib:>7.3f} {emig:>12,}   libdem Δ from prev 5y: {lib_change:+.3f}, emig stock chg: {emig_pct_change:+.0f}%")
    else:
        lib_str = f"{lib:.3f}" if lib else "NA"
        print(f"{y:>5} {lib_str:>7} {emig:>12,}")
    prev_lib = lib
    prev_emig = emig


# ============================================================
# J. POL reverse brain drain
# ============================================================
hdr("POL: pre-PiS vs PiS-era vs post-PiS emigration stock", "J")
pol_stocks = {y: get_desa_stock("Poland", y) for y in [1990, 2000, 2010, 2015, 2020, 2024]}
print(f"POL emigration stock (UN DESA, by origin):")
for y, v in pol_stocks.items():
    print(f"   {y}: {int(v):,}")
print(f"\nPre-PiS 2010-2015 growth: {pol_stocks[2015]-pol_stocks[2010]:+,} ({(pol_stocks[2015]-pol_stocks[2010])/5:+,.0f}/yr)")
print(f"PiS-era 2015-2020 growth: {pol_stocks[2020]-pol_stocks[2015]:+,} ({(pol_stocks[2020]-pol_stocks[2015])/5:+,.0f}/yr)")
print(f"Tusk-recovery 2020-2024 growth: {pol_stocks[2024]-pol_stocks[2020]:+,} ({(pol_stocks[2024]-pol_stocks[2020])/4:+,.0f}/yr)")
print("\nNote: UN DESA migrant stock counts cumulative POLES LIVING ABROAD. If reverse brain drain happens 2023+, the 2024 stock should grow SLOWER than 2015-2020 (or even shrink).")


# ============================================================
# K. 2x2 typology (speed x institutional vehicle)
# ============================================================
hdr("2x2 typology — speed × institutional vehicle", "K")
# Classify each case on 2 axes:
# Axis 1: speed (single-event-driven vs incremental-legalistic)
# Axis 2: institutional vehicle (party-state vs personalist)

axis1_label = {
    "single_event": "Single dramatic event triggers consolidation",
    "incremental": "Incremental legalistic consolidation over years"
}
axis2_label = {
    "party_state": "Party-state fusion (party survives leader)",
    "personalist": "Personalist (leader-centric, succession fragile)"
}

typology = {
    "SLV": ("single_event", "personalist"),
    "HUN": ("incremental", "party_state"),
    "TUR": ("incremental", "personalist"),
    "VEN": ("incremental", "party_state"),
    "POL": ("incremental", "party_state"),
    "TUN": ("single_event", "personalist"),  # 2021 self-coup
    "BLR": ("incremental", "personalist"),
    "IND": ("incremental", "party_state"),  # very slow incremental
    "USA": ("single_event", "personalist"),  # Trump II = fast-pole single-event-driven
    "SRB": ("incremental", "personalist"),
    "BGD": ("incremental", "party_state"),
    "NIC": ("single_event", "personalist"),  # 2018 protest crackdown + 2021 election sham
}

print("\n2x2 Typology cells:")
print()
for s in ["single_event", "incremental"]:
    print(f"\n--- {s} ({axis1_label[s]}) ---")
    for p in ["party_state", "personalist"]:
        cells = [iso for iso, (sp, pp) in typology.items() if sp == s and pp == p]
        print(f"   {p}: {cells}")

# Predict durability by cell
print("\nPredicted durability ranking (best-to-worst recovery prospects):")
print("1. SINGLE-EVENT × PERSONALIST: post-leader-exit RECOVERY most likely (SLV, TUN, USA, NIC)")
print("2. INCREMENTAL × PERSONALIST: succession-crisis RECOVERY possible (TUR, BLR, SRB)")
print("3. INCREMENTAL × PARTY-STATE: STALLED-RECOVERY likely (HUN, POL, IND, BGD)")
print("4. SINGLE-EVENT × PARTY-STATE: rare config; could rebound or freeze (VEN late-stage)")


# ============================================================
# L. Durability monitoring setup
# ============================================================
hdr("Durability monitoring — locked predictions for forward 2026-2030", "L")
print("""
Forward-watch predictions LOCKED per case + cell:

CELL: single-event × personalist (best recovery prospect)
- SLV: predict if Bukele exits 2027/2029 → libdem rises ≥0.20 within 3y of exit
- TUN: predict Saied's coalition fragmentation → libdem rises ≥0.10 by 2028
- USA: predict if Trump exits 2029 → libdem rises ≥0.10 within 2y (caveat: GOP party-state fusion progress)
- NIC: Ortega aging → succession crisis → likely rapid trajectory either way

CELL: incremental × personalist (moderate recovery prospect)
- TUR: predict Erdoğan succession 2028 → if free election, libdem rises ≥0.15 by 2031
- BLR: Lukashenko aging → if Russia doesn't engineer continuation, libdem rises ≥0.10 by 2030
- SRB: Vučić 2027 election → competitive election triggers reform OR consolidation deepens

CELL: incremental × party-state (STALLED-RECOVERY expected)
- HUN: Orbán 2026 election loss scenario → predict libdem rises ≤0.10 in first 2y (Fidesz inst. resistance)
- POL: 2027 parliamentary election (Tusk hold?) → predict stalled per PRE_REG_006 at 0.55-0.65
- IND: continued slow-burn → libdem 0.22-0.28 by 2030 regardless of election outcomes
- BGD: Yunus transition → captured judiciary blocks reform → predict libdem 0.15-0.25 by 2028

CELL: single-event × party-state (rare; treat as outlier)
- VEN late-stage: Maduro continuation → libdem 0.05-0.10 floor

KEY HOLDOUT EVENTS TO WATCH:
- 2026 HUN parliamentary election
- 2026 BRA presidential election (Bolsonaro return scenario)
- 2027 POL parliamentary election
- 2028 USA presidential election
- 2028 TUR succession (Erdoğan term-limited unless constitutional workaround)
- 2026 V-Dem v16 release (covers 2025)
- 2027 V-Dem v17 release (covers 2026)

If 3+ of these predictions land correctly = STRONG SUPPORT for 2x2 typology
If 0-1 = WALK-BACK 2x2 typology
""")


print("\n" + "="*80)
print("I + J + K + L COMPLETE")
print("="*80)
