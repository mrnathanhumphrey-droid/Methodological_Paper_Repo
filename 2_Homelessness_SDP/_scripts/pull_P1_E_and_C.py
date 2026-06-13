"""Pull P1-E + P1-C: recovery-mechanism asymmetry + elections-bellwether.

P1-E: code which V-Dem sub-indicators recover FAST vs SLOW across recovery cases
P1-C: specifically test if v2elfrfair (elections-free-fair) is the LAST sub-indicator
       to recover across all recovery cases — the "elections-bellwether" hypothesis

Recovery cases identified so far:
- POL: PiS-era 2015-2023 → Tusk recovery 2023+
- BRA: Bolsonaro 2019-2022 → Lula recovery 2023+
- KOR: Yoon martial law Dec 2024 → impeachment + recovery 2025
- BGD: Hasina 2009-2024 → Yunus interim 2024+ (V-Dem 2024-2025 lag)
- Historical: Sri Lanka 2015-2019 (Sirisena reformist win, reversed 2019)
- Historical: South Korea 1987 (Constitutional amendment + transition)
- Historical: Indonesia post-1998 (Suharto → Constitutional Court 2003)

For each case + each sub-indicator, compute:
- Pre-collapse baseline (best year before consolidation)
- Trough year (worst year during consolidation)
- Recovery year (latest available)
- Recovery fraction = (recovery - trough) / (baseline - trough)
- Recovery speed = (recovery - trough) / years_since_trough
"""
import pathlib
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np

ROOT = pathlib.Path("D:/IDP")
DATA = ROOT / "data"

vdem = pd.read_csv(DATA / "vdem" / "vdem_vdem.csv", low_memory=False)

SUBIND = {
    "v2x_libdem": "libdem aggregate",
    "v2x_jucon": "judicial constraints",
    "v2x_freexp_altinf": "free expression + alt info",
    "v2elfrfair": "elections free + fair",
    "v2juhcind": "high court independence",
    "v2mecenefm": "media censorship (HIGHER = less censorship)",
    "v2cseeorgs": "civil society entry/exit",
    "v2psoppaut": "opposition party autonomy",
    "v2x_horacc": "horizontal accountability",
    "v2x_diagacc": "diagonal accountability",
    "v2x_veracc": "vertical accountability",
}

# Recovery cases with their windows
CASES = [
    # (iso, label, baseline_year, trough_year, recovery_end_year)
    ("POL", "POL Tusk recovery", 2012, 2022, 2025),
    ("BRA", "BRA Lula recovery", 2014, 2019, 2025),
    ("KOR", "KOR Yoon-impeachment recovery", 2018, 2023, 2025),
    ("BGD", "BGD Hasina-Yunus transition", 2008, 2024, 2025),  # very recent; expect lag
    ("LKA", "Sri Lanka Sirisena 2015", 2005, 2014, 2018),  # reformist phase only
    ("KOR_hist", "KOR 1987 transition (historical)", 1986, 1987, 1992),  # baseline=trough year approach
    ("IDN", "Indonesia 1998 transition", 1996, 1998, 2005),
]


def get_val(iso_actual, year, col):
    """Get V-Dem value for country-year-indicator."""
    sub = vdem[(vdem["country_text_id"] == iso_actual) & (vdem["year"] == year)]
    if not len(sub):
        return None
    v = sub[col].iloc[0] if col in vdem.columns else None
    return v if pd.notna(v) else None


def hdr(t):
    print("\n" + "="*80)
    print(t)
    print("="*80)


# Build the recovery asymmetry table
hdr("P1-E: Recovery-Mechanism Asymmetry — sub-indicator recovery fractions per case")

# Resolve historical aliases
ISO_MAP = {
    "POL": "POL", "BRA": "BRA", "KOR": "KOR", "BGD": "BGD",
    "LKA": "LKA", "KOR_hist": "KOR", "IDN": "IDN"
}

results = {}  # {case_label: {col: (baseline, trough, recovery, frac, speed)}}
for iso_key, label, y_base, y_trough, y_rec in CASES:
    iso = ISO_MAP[iso_key]
    results[label] = {}
    for col, name in SUBIND.items():
        baseline = get_val(iso, y_base, col)
        trough = get_val(iso, y_trough, col)
        recovery = get_val(iso, y_rec, col)
        if None in (baseline, trough, recovery):
            results[label][col] = None
            continue
        # Sign of decline: for v2mecenefm higher=less censorship, so decline means index dropped
        # All V-Dem indices: lower = worse for democracy (except v2mecenefm is also lower=worse actually in V-Dem v15)
        # Recovery direction is always "back toward baseline"
        # If baseline > trough, recovery should increase toward baseline
        if baseline > trough:
            frac = (recovery - trough) / (baseline - trough) if (baseline - trough) > 0 else None
        else:
            # baseline < trough means we're using wrong direction; flag
            frac = None
        years_since_trough = y_rec - y_trough
        speed = (recovery - trough) / years_since_trough if years_since_trough > 0 else None
        results[label][col] = (baseline, trough, recovery, frac, speed)


# Print per-case table
for case_label, cols in results.items():
    print(f"\n--- {case_label} ---")
    print(f"{'subindicator':40s} {'base':>7} {'trough':>7} {'recov':>7} {'frac_rec':>10} {'Δ/yr':>9}")
    for col, name in SUBIND.items():
        if cols.get(col) is None:
            print(f"{name[:40]:40s}   (insufficient data or no decline)")
            continue
        b, t, r, f, s = cols[col]
        f_str = f"{f:>9.2%}" if f is not None else "    NA   "
        s_str = f"{s:>+9.4f}" if s is not None else "   NA   "
        print(f"{name[:40]:40s} {b:>7.3f} {t:>7.3f} {r:>7.3f}  {f_str} {s_str}")


# Cross-case aggregation: median recovery fraction per sub-indicator
hdr("Cross-case aggregation: median recovery fraction by sub-indicator")
print("\n(Higher fraction = faster/more complete recovery; 1.0 = fully back to baseline; 0 = no recovery; negative = continued decline)")
print()
aggregate = {col: [] for col in SUBIND}
for case_label, cols in results.items():
    for col in SUBIND:
        if cols.get(col) is not None:
            _, _, _, frac, _ = cols[col]
            if frac is not None:
                aggregate[col].append((case_label, frac))

print(f"{'subindicator':40s} {'n_cases':>8s} {'median_frac':>12s} {'min':>7s} {'max':>7s}  {'case-by-case'}")
ranked = []
for col, name in SUBIND.items():
    vals = aggregate[col]
    if not vals:
        continue
    fracs = [v[1] for v in vals]
    med = np.median(fracs)
    mn = min(fracs)
    mx = max(fracs)
    detail = ", ".join([f"{cl[:8]}={f:.2f}" for cl, f in vals])
    ranked.append((col, name, len(vals), med, mn, mx, detail))

# Sort by median recovery fraction (descending — best-recovering first)
ranked.sort(key=lambda x: x[3], reverse=True)
for col, name, n, med, mn, mx, detail in ranked:
    print(f"{name[:40]:40s} {n:>8d} {med:>11.2%} {mn:>+7.2f} {mx:>+7.2f}  {detail[:80]}")


# P1-C explicitly: is elections-free-fair (v2elfrfair) consistently the LAST to recover?
hdr("P1-C: Elections-free-fair as RECOVERY BELLWETHER hypothesis")

print("\nFor each case, compare v2elfrfair recovery fraction vs other sub-indicators:")
print()
print(f"{'case':35s} {'el_ff_frac':>12s} {'other_avg':>12s} {'el_ff rank':>15s}")
for case_label, cols in results.items():
    el_ff = cols.get("v2elfrfair")
    if el_ff is None:
        continue
    _, _, _, el_ff_frac, _ = el_ff
    if el_ff_frac is None:
        continue
    other_fracs = []
    for col in SUBIND:
        if col == "v2elfrfair" or col == "v2x_libdem":
            continue
        c = cols.get(col)
        if c is not None and c[3] is not None:
            other_fracs.append((col, c[3]))
    if not other_fracs:
        continue
    other_avg = np.mean([f for _, f in other_fracs])
    # Where does v2elfrfair rank among all sub-indicators?
    all_subs = [(col, cols[col][3]) for col in SUBIND if cols.get(col) is not None and cols[col][3] is not None and col != "v2x_libdem"]
    all_subs.sort(key=lambda x: x[1], reverse=True)  # descending
    rank = next((i+1 for i, (col, _) in enumerate(all_subs) if col == "v2elfrfair"), None)
    n_total = len(all_subs)
    print(f"{case_label[:35]:35s} {el_ff_frac:>11.2%} {other_avg:>11.2%} rank {rank}/{n_total} {'LAST' if rank == n_total else ''}")


# Visualize: WHICH sub-indicators recover first vs last across all cases
hdr("Recovery-order summary across cases")
print()
print("Sub-indicators sorted by median recovery fraction (FAST → SLOW):")
for i, (col, name, n, med, mn, mx, _) in enumerate(ranked):
    rank_marker = "★ FAST RECOVERY" if i < 3 else ("⚠ SLOW RECOVERY" if i >= len(ranked) - 3 else "")
    print(f"  {i+1}. {name[:50]:50s} median = {med:>6.2%}  (n={n})  {rank_marker}")


print("\n" + "="*80)
print("P1-E + P1-C COMPLETE")
print("="*80)
