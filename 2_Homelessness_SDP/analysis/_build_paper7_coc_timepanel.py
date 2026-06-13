# Mechanical data engineering: build CoC x year panel (2012-2024) of
# homelessness + median rent + median HH income for a within-CoC gentrification
# test. NO regression/mediation/bootstrap. All numeric values come strictly from
# downloaded/read files (Census API + HUD PIT xlsb + crosswalk CSVs). Nothing
# from memory; failed sources are left missing and logged.
import json
import re
import time
import urllib.request
import urllib.error

import numpy as np
import pandas as pd

PAPER7 = 'D:/IDP/data/paper7'
OUT_PANEL = 'D:/IDP/analysis/paper7_coc_timepanel_2012_2024.csv'
OUT_LONGDIFF = 'D:/IDP/analysis/paper7_coc_longdiff_2012_2024.csv'
OUT_COV = 'D:/IDP/analysis/paper7_coc_timepanel_coverage.json'

PIT_PATH = f'{PAPER7}/hud_pit/2007-2024-PIT-Counts-by-CoC.xlsb'
CW_PATH = f'{PAPER7}/coc_crosswalk/county_coc_match.csv'
POP_PATH = f'{PAPER7}/coc_crosswalk/coc_population.csv'

UA = 'Mozilla/5.0 (research; IDP Paper 7 CoC timepanel)'
ACS_VARS = 'NAME,B25064_001E,B19013_001E,B01003_001E'
# ACS 1-yr exists 2012-2024 EXCEPT 2020 (Census did not release standard 1-yr).
PANEL_YEARS = [y for y in range(2012, 2025) if y != 2020]

failed_sources = []


# ---------------------------------------------------------------------------
# Census key
# ---------------------------------------------------------------------------
def load_key():
    for line in open('D:/IDP/.env'):
        if line.strip().startswith('CENSUS_API_KEY='):
            return line.strip().split('=', 1)[1].strip().strip('"').strip("'")
    raise SystemExit('CENSUS_API_KEY not in D:/IDP/.env')


KEY = load_key()


def fetch_acs_county(year, dataset):
    """Return county-level df (county_fips, rent, income, cty_pop) or None on fail.
    Census negative sentinels (-666666666 etc.) -> NaN. Values straight from API."""
    url = (f'https://api.census.gov/data/{year}/{dataset}?get={ACS_VARS}'
           f'&for=county:*&key={KEY}')
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = json.loads(r.read().decode())
    except Exception as e:  # noqa: BLE001 -- log + leave missing
        failed_sources.append(f'{dataset} {year}: {type(e).__name__} {e}')
        print(f'[acs] {year} {dataset} FAILED: {e}')
        return None
    df = pd.DataFrame(raw[1:], columns=raw[0])
    for c in ['B25064_001E', 'B19013_001E', 'B01003_001E']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
        df.loc[df[c] < 0, c] = np.nan
    df['county_fips'] = df['state'].str.zfill(2) + df['county'].str.zfill(3)
    df = df.rename(columns={'B25064_001E': 'rent', 'B19013_001E': 'income',
                            'B01003_001E': 'cty_pop'})
    return df[['county_fips', 'rent', 'income', 'cty_pop']]


# ---------------------------------------------------------------------------
# Crosswalk (county -> CoC, with within-county weight share)
# ---------------------------------------------------------------------------
cw = pd.read_csv(CW_PATH, encoding='latin-1')
cw = cw[['county_fips', 'coc_number', 'coc_name', 'pct_cnty_pop_coc']].copy()
cw = cw.dropna(subset=['county_fips', 'coc_number']).copy()
cw['county_fips'] = (cw['county_fips'].astype(float).round().astype(int)
                     .astype(str).str.zfill(5))
print('crosswalk rows:', len(cw), 'CoCs:', cw['coc_number'].nunique())

# CoC population (denominator for per-10k rates)
pop = pd.read_csv(POP_PATH, encoding='latin-1')[['coc_number', 'total_population']].copy()


def wmean(g, valcol):
    """Population-weighted mean of valcol; weight = county_pop * pct_in_coc/100."""
    sub = g.dropna(subset=[valcol, 'w'])
    sub = sub[sub['w'] > 0]
    if sub.empty or sub['w'].sum() == 0:
        return np.nan
    return np.average(sub[valcol], weights=sub['w'])


def aggregate_to_coc(acs):
    """county ACS -> CoC pop-weighted rent_coc / income_coc."""
    m = cw.merge(acs[['county_fips', 'rent', 'income', 'cty_pop']],
                 on='county_fips', how='left')
    m['w'] = m['cty_pop'] * (m['pct_cnty_pop_coc'] / 100.0)
    agg = m.groupby('coc_number').apply(
        lambda g: pd.Series({'rent_coc': wmean(g, 'rent'),
                             'income_coc': wmean(g, 'income')}),
        include_groups=False).reset_index()
    return agg


# ---------------------------------------------------------------------------
# HUD PIT homelessness per year
# ---------------------------------------------------------------------------
COC_RE = re.compile(r'^[A-Z]{2}-\d')


def pit_year(year):
    """Return (coc_number, overall_homeless, unsheltered_homeless) for a year."""
    df = pd.read_excel(PIT_PATH, sheet_name=str(year), engine='pyxlsb')
    df = df[df['CoC Number'].astype(str).str.match(COC_RE)].copy()
    df = df[['CoC Number', 'Overall Homeless', 'Unsheltered Homeless']].copy()
    df = df.rename(columns={'CoC Number': 'coc_number',
                            'Overall Homeless': 'overall_homeless',
                            'Unsheltered Homeless': 'unsheltered_homeless'})
    for c in ['overall_homeless', 'unsheltered_homeless']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    # collapse any duplicate CoC rows within a sheet by sum (defensive)
    df = df.groupby('coc_number', as_index=False).sum(min_count=1)
    return df


# ===========================================================================
# 1+2+3. LONG PANEL: ACS1 county -> CoC + PIT homelessness, per year
# ===========================================================================
panel_rows = []
acs1_county_cov = {}
for y in PANEL_YEARS:
    acs = fetch_acs_county(y, 'acs/acs1')
    if acs is None:
        continue
    acs1_county_cov[y] = {
        'counties_returned': int(len(acs)),
        'rent_nonnull': int(acs['rent'].notna().sum()),
        'income_nonnull': int(acs['income'].notna().sum()),
        'pop_nonnull': int(acs['cty_pop'].notna().sum()),
    }
    agg = aggregate_to_coc(acs)
    try:
        pit = pit_year(y)
    except Exception as e:  # noqa: BLE001
        failed_sources.append(f'PIT {y}: {type(e).__name__} {e}')
        print(f'[pit] {y} FAILED: {e}')
        pit = pd.DataFrame(columns=['coc_number', 'overall_homeless',
                                    'unsheltered_homeless'])
    # union of CoCs in crosswalk-agg and PIT for this year
    base = pd.DataFrame({'coc_number': sorted(
        set(agg['coc_number']).union(set(pit['coc_number'])))})
    yr = (base.merge(agg, on='coc_number', how='left')
          .merge(pit, on='coc_number', how='left')
          .merge(pop, on='coc_number', how='left'))
    tp = yr['total_population'].replace(0, np.nan)
    yr['homeless_per_10k'] = yr['overall_homeless'] / tp * 1e4
    yr['unsheltered_per_10k'] = yr['unsheltered_homeless'] / tp * 1e4
    yr['year'] = y
    panel_rows.append(yr[['coc_number', 'year', 'rent_coc', 'income_coc',
                          'homeless_per_10k', 'unsheltered_per_10k',
                          'total_population']])
    n_full = int(yr.dropna(subset=['rent_coc', 'income_coc',
                                   'homeless_per_10k']).shape[0])
    print(f'[panel] {y}: CoCs={len(yr)} full(rent+inc+hl)={n_full}')

panel = pd.concat(panel_rows, ignore_index=True)
panel = panel.sort_values(['coc_number', 'year']).reset_index(drop=True)
panel.to_csv(OUT_PANEL, index=False)
print('\nLONG PANEL written:', OUT_PANEL, 'shape', panel.shape)

# ===========================================================================
# 4. LONG-DIFFERENCE TABLE: ACS5 endpoints 2012 (2008-12) & 2024 (2020-24)
#    full county coverage -> CoC; homelessness 2012 & 2024.
# ===========================================================================
acs5_2012 = fetch_acs_county(2012, 'acs/acs5')
acs5_2024 = fetch_acs_county(2024, 'acs/acs5')
acs5_cov = {}
ld = None
if acs5_2012 is not None and acs5_2024 is not None:
    acs5_cov = {
        2012: {'counties_returned': int(len(acs5_2012)),
               'rent_nonnull': int(acs5_2012['rent'].notna().sum()),
               'income_nonnull': int(acs5_2012['income'].notna().sum())},
        2024: {'counties_returned': int(len(acs5_2024)),
               'rent_nonnull': int(acs5_2024['rent'].notna().sum()),
               'income_nonnull': int(acs5_2024['income'].notna().sum())},
    }
    agg12 = aggregate_to_coc(acs5_2012).rename(
        columns={'rent_coc': 'rent_2012', 'income_coc': 'income_2012'})
    agg24 = aggregate_to_coc(acs5_2024).rename(
        columns={'rent_coc': 'rent_2024', 'income_coc': 'income_2024'})

    pit12 = pit_year(2012).merge(pop, on='coc_number', how='left')
    pit24 = pit_year(2024).merge(pop, on='coc_number', how='left')
    pit12['homeless_per_10k_2012'] = (pit12['overall_homeless']
                                      / pit12['total_population'].replace(0, np.nan) * 1e4)
    pit24['homeless_per_10k_2024'] = (pit24['overall_homeless']
                                      / pit24['total_population'].replace(0, np.nan) * 1e4)

    base = pd.DataFrame({'coc_number': sorted(
        set(agg12['coc_number']).union(agg24['coc_number'])
        .union(pit12['coc_number']).union(pit24['coc_number']))})
    ld = (base
          .merge(agg12, on='coc_number', how='left')
          .merge(agg24, on='coc_number', how='left')
          .merge(pit12[['coc_number', 'homeless_per_10k_2012']],
                 on='coc_number', how='left')
          .merge(pit24[['coc_number', 'homeless_per_10k_2024']],
                 on='coc_number', how='left'))
    ld['d_rent'] = ld['rent_2024'] - ld['rent_2012']
    ld['d_income'] = ld['income_2024'] - ld['income_2012']
    ld['d_homeless'] = ld['homeless_per_10k_2024'] - ld['homeless_per_10k_2012']
    ld = ld[['coc_number', 'rent_2012', 'rent_2024', 'income_2012', 'income_2024',
             'homeless_per_10k_2012', 'homeless_per_10k_2024',
             'd_rent', 'd_income', 'd_homeless']].sort_values('coc_number')
    ld.to_csv(OUT_LONGDIFF, index=False)
    print('LONG-DIFF written:', OUT_LONGDIFF, 'shape', ld.shape)
else:
    print('LONG-DIFF SKIPPED: an ACS5 endpoint failed')

# ===========================================================================
# Coverage report
# ===========================================================================
# n CoCs with >=6 years of rent + income + homeless
full = panel.dropna(subset=['rent_coc', 'income_coc', 'homeless_per_10k'])
yrs_per_coc = full.groupby('coc_number')['year'].nunique()
n_ge6 = int((yrs_per_coc >= 6).sum())

per_year_full = (panel.dropna(subset=['rent_coc', 'income_coc', 'homeless_per_10k'])
                 .groupby('year')['coc_number'].nunique().to_dict())
per_year_total = panel.groupby('year')['coc_number'].nunique().to_dict()

ld_n = 0
ld_full = 0
if ld is not None:
    ld_n = int(len(ld))
    ld_full = int(ld.dropna(subset=['d_rent', 'd_income', 'd_homeless']).shape[0])

cov = {
    'panel_years': PANEL_YEARS,
    'panel_acs_dataset': 'acs/acs1 (median rent B25064, median HH income B19013, '
                         'pop B01003); counties >=65k pop only',
    'longdiff_acs_dataset': 'acs/acs5 endpoints 2012 (2008-2012) & 2024 (2020-2024); '
                            'full county coverage',
    'note_2020': '2020 dropped from long panel (ACS 1-yr not released by Census).',
    'n_coc_per_year_total': {int(k): int(v) for k, v in per_year_total.items()},
    'n_coc_per_year_full_rent_income_homeless':
        {int(k): int(v) for k, v in per_year_full.items()},
    'n_coc_with_ge6_years_full': n_ge6,
    'longdiff_n_coc': ld_n,
    'longdiff_n_coc_full_d_rent_income_homeless': ld_full,
    'acs1_county_coverage_by_year': acs1_county_cov,
    'acs5_endpoint_coverage': {str(k): v for k, v in acs5_cov.items()},
    'failed_sources': failed_sources,
}
with open(OUT_COV, 'w') as f:
    json.dump(cov, f, indent=2)
print('COVERAGE written:', OUT_COV)
print(json.dumps(cov, indent=2))

# ---- sanity sample CoCs ----------------------------------------------------
print('\nSAMPLE (long-diff endpoints):')
for c in ['NY-600', 'CA-600', 'IL-510']:
    if ld is not None:
        r = ld[ld['coc_number'] == c]
        if r.empty:
            print(c, 'NOT IN LONG-DIFF')
        else:
            d = r.to_dict('records')[0]
            print(f"{c}: rent {d['rent_2012']:.0f}->{d['rent_2024']:.0f} | "
                  f"hl/10k {d['homeless_per_10k_2012']:.2f}->{d['homeless_per_10k_2024']:.2f}")
print('\nSAMPLE (long-panel rows for NY-600):')
print(panel[panel['coc_number'] == 'NY-600'].to_string(index=False))
