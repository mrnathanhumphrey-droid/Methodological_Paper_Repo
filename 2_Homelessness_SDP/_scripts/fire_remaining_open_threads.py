"""Fire remaining STILL OPEN threads on PATTERN_013.

A. PRE_REG_008: party-state vs personalist axis — speed test
B. Speed-variation decomposition (single-event vs incremental)
C. IND federal counter-pressure check (sub-national V-Dem if available)
D. Coordinated-resistance-within-one-electoral-cycle operationalization
E. Sub-indicator recovery symmetry test (POL+BRA quantitative)
"""
import pathlib
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
from scipy.stats import mannwhitneyu, spearmanr

ROOT = pathlib.Path("D:/IDP")
DATA = ROOT / "data"

vdem = pd.read_csv(DATA / "vdem" / "vdem_vdem.csv", low_memory=False)
print(f"V-Dem cols: {sum('libdem' in c or 'party' in c.lower() or 'pscohes' in c.lower() for c in vdem.columns)} party/libdem cols found")

# Bukelization corpus with classification (locked in PRE_REG_008)
corpus = [
    ("SLV", 2019, 2024, "personalist"),
    ("HUN", 2010, 2020, "party_state"),
    ("TUR", 2007, 2017, "personalist"),
    ("VEN", 1997, 2007, "party_state"),  # PSUV proto
    ("POL", 2010, 2020, "party_state"),
    ("TUN", 2012, 2022, "personalist"),
    ("BLR", 1992, 2002, "personalist"),
    ("IND", 2002, 2024, "party_state"),  # slow-burn 22y
    ("USA", 2017, 2024, "personalist"),  # short window, partial
    ("SRB", 2010, 2024, "personalist"),  # slow-burn 14y
    ("BGD", 2009, 2024, "party_state"),  # AL party-state
    ("NIC", 2007, 2020, "personalist"),  # Ortega/Murillo
]


def hdr(letter, title):
    print("\n" + "="*80)
    print(f"DIG {letter}: {title}")
    print("="*80)


# ============================================================
# A. Speed by classification (Mann-Whitney U test)
# ============================================================
hdr("A", "PRE_REG_008 first fit: speed by party-state vs personalist")

speeds = []
for iso, y1, y2, cls in corpus:
    s = vdem[(vdem["country_text_id"] == iso) & (vdem["year"] == y1)]
    e = vdem[(vdem["country_text_id"] == iso) & (vdem["year"] == y2)]
    if not (len(s) and len(e)):
        continue
    sv = s["v2x_libdem"].iloc[0]
    ev = e["v2x_libdem"].iloc[0]
    rate = (ev - sv) / (y2 - y1)
    speeds.append((iso, cls, sv, ev, rate, y2-y1))

print(f"\n{'iso':5s} {'class':>14s} {'start':>7s} {'end':>7s} {'rate':>10s} {'years':>6s}")
for iso, cls, sv, ev, rate, yrs in speeds:
    print(f"{iso:5s} {cls:>14s} {sv:>7.3f} {ev:>7.3f} {rate:>+10.4f} {yrs:>6d}")

personalist_rates = [r for iso, cls, sv, ev, r, yrs in speeds if cls == "personalist"]
party_state_rates = [r for iso, cls, sv, ev, r, yrs in speeds if cls == "party_state"]

print(f"\nPersonalist cases (n={len(personalist_rates)}): mean rate = {np.mean(personalist_rates):+.4f}, median = {np.median(personalist_rates):+.4f}")
print(f"Party-state cases (n={len(party_state_rates)}): mean rate = {np.mean(party_state_rates):+.4f}, median = {np.median(party_state_rates):+.4f}")

if len(personalist_rates) > 1 and len(party_state_rates) > 1:
    u, p = mannwhitneyu(personalist_rates, party_state_rates, alternative='less')
    print(f"\nMann-Whitney U test (personalist < party_state rate? i.e. personalist more negative): U={u:.1f}, p={p:.4f}")
    # Note: more negative rate = faster collapse


# ============================================================
# B. Speed-variation pattern: rate vs window length
# ============================================================
hdr("B", "Speed variation across window length")
print("\nDoes a SHORTER window correlate with FASTER absolute rate? (single-event hypothesis)")
print(f"{'iso':5s} {'window':>6s} {'rate':>10s} {'|rate|':>8s}")
ratios = []
for iso, cls, sv, ev, r, yrs in speeds:
    ratios.append((yrs, abs(r)))
    print(f"{iso:5s} {yrs:>6d} {r:>+10.4f} {abs(r):>8.4f}")

if len(ratios) >= 5:
    rho, p = spearmanr([r[0] for r in ratios], [r[1] for r in ratios])
    print(f"\nSpearman ρ(window_length, |rate|) = {rho:.3f} (p={p:.4f})")
    print("Predicted: negative correlation (shorter window = faster rate)")


# ============================================================
# C. IND federal-counter-pressure test
# ============================================================
hdr("C", "IND federal counter-pressure: party-state at national level, varied at state level")

# Use V-Dem sub-indicators: regional government / sub-national variation
ind_cols = [c for c in vdem.columns if 'reg' in c.lower() and 'lib' in c.lower()] + \
           [c for c in vdem.columns if c in ['v2elsuffrage','v2elffelr','v2psnatpar','v2ddlexrf']]
print(f"\nV-Dem sub-national candidate cols: {ind_cols}")

# Just plot IND year-by-year polyarchy and libdem
ind = vdem[(vdem["country_text_id"] == "IND") & (vdem["year"] >= 1998)].sort_values("year")
print(f"\nIND polyarchy vs libdem 1998-2024:")
print(f"{'year':>4s} {'libdem':>7s} {'polyarchy':>10s} {'jucon':>7s} {'partyaut':>9s}")
for _, r in ind.iterrows():
    y = int(r['year'])
    lib = r.get('v2x_libdem', None)
    pol = r.get('v2x_polyarchy', None)
    juc = r.get('v2x_jucon', None)
    psoppaut = r.get('v2psoppaut', None)
    if pd.notna(lib):
        print(f"{y:>4d} {lib:>7.3f} {pol if pd.notna(pol) else 'NA':>10}", end=' ')
        print(f"{juc if pd.notna(juc) else 'NA':>7}", end=' ')
        print(f"{psoppaut if pd.notna(psoppaut) else 'NA':>9}")


# ============================================================
# D. POL+BRA sub-indicator recovery symmetry — quantitative
# ============================================================
hdr("D", "POL+BRA recovery symmetry — magnitude correlation test")

subind_cols = ['v2x_jucon', 'v2x_freexp_altinf', 'v2elfrfair', 'v2juhcind', 'v2mecenefm', 'v2cseeorgs']

def get_deltas(iso, y_consol_start, y_consol_end, y_rec_start, y_rec_end):
    """Returns (consolidation_deltas, recovery_deltas) per sub-indicator."""
    s_cs = vdem[(vdem["country_text_id"] == iso) & (vdem["year"] == y_consol_start)]
    e_cs = vdem[(vdem["country_text_id"] == iso) & (vdem["year"] == y_consol_end)]
    s_rec = vdem[(vdem["country_text_id"] == iso) & (vdem["year"] == y_rec_start)]
    e_rec = vdem[(vdem["country_text_id"] == iso) & (vdem["year"] == y_rec_end)]
    if not all([len(s_cs), len(e_cs), len(s_rec), len(e_rec)]):
        return None
    cd = []
    rd = []
    for col in subind_cols:
        if col in vdem.columns:
            cd.append(e_cs[col].iloc[0] - s_cs[col].iloc[0])
            rd.append(e_rec[col].iloc[0] - s_rec[col].iloc[0])
    return cd, rd

pol = get_deltas("POL", 2010, 2020, 2022, 2024)
bra = get_deltas("BRA", 2018, 2022, 2022, 2024)

print("\nPOL consolidation 2010-2020 deltas vs recovery 2022-2024 deltas (signs should be opposite):")
if pol:
    cd, rd = pol
    print(f"{'subind':30s} {'consol Δ':>10s} {'recov Δ':>10s} {'symmetric?':>11s}")
    for col, c, r in zip(subind_cols, cd, rd):
        sym = "YES" if (c < 0 and r > 0) or (c > 0 and r < 0) else "no"
        print(f"{col:30s} {c:>+10.3f} {r:>+10.3f} {sym:>11s}")
    rho, p = spearmanr(cd, [-x for x in rd])  # negative recovery should correlate positively with consolidation deltas
    print(f"\nSpearman ρ(consol_delta, -recovery_delta) for POL = {rho:.3f} (p={p:.4f})")
    print("Higher ρ = stronger symmetry — same sub-indicators reverse direction by similar magnitudes")

print()
if bra:
    cd, rd = bra
    print(f"BRA consolidation 2018-2022 deltas vs recovery 2022-2024 deltas:")
    print(f"{'subind':30s} {'consol Δ':>10s} {'recov Δ':>10s} {'symmetric?':>11s}")
    for col, c, r in zip(subind_cols, cd, rd):
        sym = "YES" if (c < 0 and r > 0) or (c > 0 and r < 0) else "no"
        print(f"{col:30s} {c:>+10.3f} {r:>+10.3f} {sym:>11s}")
    rho, p = spearmanr(cd, [-x for x in rd])
    print(f"\nSpearman ρ(consol_delta, -recovery_delta) for BRA = {rho:.3f} (p={p:.4f})")


# ============================================================
# E. Coordinated-resistance proxy — opposition cohesion
# ============================================================
hdr("E", "Coordinated resistance proxy — V-Dem opposition autonomy + party cohesion")

# Use v2psoppaut (opposition party autonomy) and v2pscohesv (party cohesion)
print(f"\n{'iso':5s} {'window':>9s} {'oppaut_start':>13s} {'oppaut_end':>11s} {'oppaut_Δ':>9s}")
for iso, y1, y2, cls in corpus:
    s = vdem[(vdem["country_text_id"] == iso) & (vdem["year"] == y1)]
    e = vdem[(vdem["country_text_id"] == iso) & (vdem["year"] == y2)]
    if not (len(s) and len(e)):
        continue
    if 'v2psoppaut' in vdem.columns:
        sv = s['v2psoppaut'].iloc[0]
        ev = e['v2psoppaut'].iloc[0]
        if pd.notna(sv) and pd.notna(ev):
            print(f"{iso:5s} {y1}-{y2:>4d} {sv:>13.3f} {ev:>11.3f} {ev-sv:>+9.3f}")


print("\n" + "="*80)
print("REMAINING OPEN THREADS FIT COMPLETE")
print("="*80)
