# Mechanical data engineering: build CoC x covariate panel for 2024.
# NO regression/mediation/bootstrap. All values come from downloaded/read files only.
import os, re, json, urllib.request
import pandas as pd
import numpy as np

PAPER7 = 'D:/IDP/data/paper7'
OUT_CSV = 'D:/IDP/analysis/paper7_metro_coc_panel_2024.csv'
OUT_JSON = 'D:/IDP/analysis/paper7_metro_coc_panel_coverage.json'

failed_sources = []

# ----------------------------------------------------------------------------
# 0. Census API key
# ----------------------------------------------------------------------------
key = None
with open('D:/IDP/.env') as f:
    for line in f:
        if line.strip().startswith('CENSUS_API_KEY='):
            key = line.strip().split('=', 1)[1].strip().strip('"').strip("'")
assert key, 'no census key'

# ----------------------------------------------------------------------------
# 1. County ACS 2024 (5-year, full county coverage; ACS1 2024 covers only ~861)
# ----------------------------------------------------------------------------
ACS_DATASET = 'acs/acs5'
ACS_YEAR = 2024
url = (f'https://api.census.gov/data/{ACS_YEAR}/{ACS_DATASET}?get=NAME,'
       'B25064_001E,B19013_001E,B01003_001E&for=county:*&key=' + key)
with urllib.request.urlopen(url, timeout=180) as r:
    raw = json.loads(r.read().decode())
acs = pd.DataFrame(raw[1:], columns=raw[0])
for c in ['B25064_001E', 'B19013_001E', 'B01003_001E']:
    acs[c] = pd.to_numeric(acs[c], errors='coerce')
# Census uses negative sentinels (e.g. -666666666) for suppressed/NA
for c in ['B25064_001E', 'B19013_001E', 'B01003_001E']:
    acs.loc[acs[c] < 0, c] = np.nan
acs['county_fips'] = acs['state'].str.zfill(2) + acs['county'].str.zfill(3)
acs = acs.rename(columns={'B25064_001E': 'rent', 'B19013_001E': 'income',
                          'B01003_001E': 'cty_pop'})
acs = acs[['county_fips', 'NAME', 'rent', 'income', 'cty_pop']]
print('ACS5 2024 counties:', len(acs))
print('  rent non-null:', acs.rent.notna().sum(),
      ' income non-null:', acs.income.notna().sum(),
      ' pop non-null:', acs.cty_pop.notna().sum())

# ----------------------------------------------------------------------------
# 2. Crosswalk county -> CoC, aggregate rent & income (pop-weighted LEVELS)
# ----------------------------------------------------------------------------
cw = pd.read_csv(f'{PAPER7}/coc_crosswalk/county_coc_match.csv', encoding='latin-1')
cw = cw[['county_fips', 'coc_number', 'coc_name', 'pct_cnty_pop_coc']].copy()
# drop rows with no county_fips OR no coc_number (cannot be aggregated)
n_cw_pre = len(cw)
cw = cw.dropna(subset=['county_fips', 'coc_number']).copy()
print('crosswalk rows dropped (NaN county_fips/coc_number):', n_cw_pre - len(cw))
# float 1001.0 -> '01001'
cw['county_fips'] = cw['county_fips'].astype(float).round().astype(int).astype(str).str.zfill(5)

m = cw.merge(acs[['county_fips', 'rent', 'income', 'cty_pop']], on='county_fips', how='left')
# aggregation weight = county_pop * (pct of county pop inside this CoC)
m['w'] = m['cty_pop'] * (m['pct_cnty_pop_coc'] / 100.0)


def wmean(g, valcol):
    sub = g.dropna(subset=[valcol, 'w'])
    sub = sub[sub['w'] > 0]
    if sub.empty or sub['w'].sum() == 0:
        return np.nan
    return np.average(sub[valcol], weights=sub['w'])


agg = m.groupby('coc_number').apply(
    lambda g: pd.Series({'rent_coc': wmean(g, 'rent'),
                         'income_coc': wmean(g, 'income')}),
    include_groups=False).reset_index()
print('CoCs in crosswalk:', m['coc_number'].nunique())
print('  rent_coc non-null:', agg.rent_coc.notna().sum(),
      ' income_coc non-null:', agg.income_coc.notna().sum())

# ----------------------------------------------------------------------------
# 3. CoC homelessness from PIT 2024 + coc_population
# ----------------------------------------------------------------------------
pit = pd.read_excel(f'{PAPER7}/hud_pit/2007-2024-PIT-Counts-by-CoC.xlsb',
                    sheet_name='2024', engine='pyxlsb')
keep = pit[pit['CoC Number'].astype(str).str.match(r'^[A-Z]{2}-\d')].copy()
pit_cols = ['CoC Number', 'CoC Name', 'Overall Homeless',
            'Unsheltered Homeless', 'Overall Homeless People in Families']
keep = keep[pit_cols].copy()
keep = keep.rename(columns={'CoC Number': 'coc_number', 'CoC Name': 'coc_name_pit',
                            'Overall Homeless': 'overall_homeless',
                            'Unsheltered Homeless': 'unsheltered_homeless',
                            'Overall Homeless People in Families': 'family_homeless'})
for c in ['overall_homeless', 'unsheltered_homeless', 'family_homeless']:
    keep[c] = pd.to_numeric(keep[c], errors='coerce')
print('PIT 2024 CoC rows kept:', len(keep))

pop = pd.read_csv(f'{PAPER7}/coc_crosswalk/coc_population.csv', encoding='latin-1')
pop = pop[['coc_number', 'total_population']].copy()

hl = keep.merge(pop, on='coc_number', how='left')
hl['homeless_per_10k'] = hl['overall_homeless'] / hl['total_population'] * 1e4
hl['unsheltered_per_10k'] = hl['unsheltered_homeless'] / hl['total_population'] * 1e4
print('  homeless rows w/ population:', hl.total_population.notna().sum())
print('  homeless_per_10k non-null:', hl.homeless_per_10k.notna().sum())

# ----------------------------------------------------------------------------
# 4. SUPPLY measures
# ----------------------------------------------------------------------------
# 4pre. CBSA delineation: CBSA code/title <-> county FIPS
deln = pd.read_excel(f'{PAPER7}/cbsa_delineation/list1_2023.xlsx', header=2)
deln = deln[['CBSA Code', 'CBSA Title', 'FIPS State Code', 'FIPS County Code']].copy()
deln = deln.dropna(subset=['CBSA Code', 'FIPS State Code', 'FIPS County Code'])
deln['county_fips'] = (deln['FIPS State Code'].astype(float).round().astype(int).astype(str).str.zfill(2)
                       + deln['FIPS County Code'].astype(float).round().astype(int).astype(str).str.zfill(3))
deln['cbsa_code'] = deln['CBSA Code'].astype(float).round().astype(int)
print('CBSA delineation: rows', len(deln), 'CBSAs', deln.cbsa_code.nunique(),
      'counties', deln.county_fips.nunique())

# ---- 4a. Saiz elasticity -> CBSA (name match) -> county -> CoC -------------
saiz = pd.read_stata(f'{PAPER7}/saiz_elasticity/saiz_elasticity.dta')


def core_name(s):
    """Reduce a metro name to (first principal city, state) for matching.
    Handles Saiz '(MSA)/(PMSA)/(NECMA)' tags and modern CBSA titles."""
    s = str(s)
    s = re.sub(r'\s*\((?:P?MSA|NECMA|MD|CMSA)\)\s*$', '', s)  # strip Saiz tag
    s = s.strip()
    if ',' not in s:
        return None
    place, st = s.rsplit(',', 1)
    st = st.strip()
    # state may be 'TX' or 'MA-NH'; take first 2-letter token
    st = st.split('-')[0].strip()[:2].upper()
    # first principal city = first token before '-' or '/'
    city = re.split(r'[-/]', place)[0].strip().lower()
    city = re.sub(r'[^a-z ]', '', city)
    return (city, st)


saiz['key'] = saiz['msaname'].apply(core_name)
deln_titles = deln[['cbsa_code', 'CBSA Title']].drop_duplicates()
deln_titles['key'] = deln_titles['CBSA Title'].apply(core_name)
# build lookup key->cbsa_code (if multiple, keep first deterministically by code)
key2cbsa = (deln_titles.dropna(subset=['key'])
            .sort_values('cbsa_code')
            .drop_duplicates('key')
            .set_index('key')['cbsa_code'].to_dict())

saiz['cbsa_code'] = saiz['key'].map(key2cbsa)
n_saiz = len(saiz)
n_saiz_matched = saiz['cbsa_code'].notna().sum()
saiz_match_rate = n_saiz_matched / n_saiz
print(f'Saiz MSAs matched to CBSA: {n_saiz_matched}/{n_saiz} = {saiz_match_rate:.3f}')

# CBSA -> county (delineation) -> attach Saiz elasticity by cbsa_code
saiz_m = saiz.dropna(subset=['cbsa_code'])[['cbsa_code', 'elasticity']].copy()
saiz_m['cbsa_code'] = saiz_m['cbsa_code'].astype(int)
# if a cbsa got >1 saiz row (shouldn't normally) average
saiz_m = saiz_m.groupby('cbsa_code', as_index=False)['elasticity'].mean()
cnty_saiz = deln[['county_fips', 'cbsa_code']].merge(saiz_m, on='cbsa_code', how='inner')
cnty_saiz = cnty_saiz.drop_duplicates('county_fips')[['county_fips', 'elasticity']]
print('  counties with a Saiz elasticity:', len(cnty_saiz))

# county Saiz -> CoC (pop-weighted by county_pop * pct_cnty_pop_coc)
ms = cw.merge(cnty_saiz, on='county_fips', how='left').merge(
    acs[['county_fips', 'cty_pop']], on='county_fips', how='left')
ms['w'] = ms['cty_pop'] * (ms['pct_cnty_pop_coc'] / 100.0)
saiz_coc = ms.groupby('coc_number').apply(
    lambda g: pd.Series({'saiz_elasticity': wmean(g, 'elasticity')}),
    include_groups=False).reset_index()
print('  CoCs with saiz_elasticity:', saiz_coc.saiz_elasticity.notna().sum())

# ---- 4b. WRLURI -> county -> CoC (weight_full-weighted) --------------------
wz = pd.read_stata(f'{PAPER7}/wharton_zoning/WHARTON-LAND-REGULATION-DATA_01_15_2020.dta')
wz = wz[['statecode_str', 'countycode18', 'WRLURI18', 'weight_full']].copy()
wzv = wz.dropna(subset=['WRLURI18', 'countycode18', 'statecode_str']).copy()
wzv['county_fips'] = (wzv['statecode_str'].astype(str).str.zfill(2)
                      + wzv['countycode18'].astype(float).round().astype(int).astype(str).str.zfill(3))


def wrluri_cty(g):
    sub = g.dropna(subset=['WRLURI18', 'weight_full'])
    sub = sub[sub['weight_full'] > 0]
    if sub.empty:
        return np.nan
    return np.average(sub['WRLURI18'], weights=sub['weight_full'])


cnty_wrluri = (wzv.groupby('county_fips')
               .apply(wrluri_cty, include_groups=False)
               .reset_index(name='wrluri_cty'))
print('WRLURI counties:', len(cnty_wrluri))

# county WRLURI -> CoC (pop-weighted by county_pop * pct_cnty_pop_coc)
mw = cw.merge(cnty_wrluri, on='county_fips', how='left').merge(
    acs[['county_fips', 'cty_pop']], on='county_fips', how='left')
mw['w'] = mw['cty_pop'] * (mw['pct_cnty_pop_coc'] / 100.0)
wrluri_coc = mw.groupby('coc_number').apply(
    lambda g: pd.Series({'wrluri_coc': wmean(g, 'wrluri_cty')}),
    include_groups=False).reset_index()
print('  CoCs with wrluri_coc:', wrluri_coc.wrluri_coc.notna().sum())

# ----------------------------------------------------------------------------
# 5. MERGE into one CoC-level table
# ----------------------------------------------------------------------------
# Base universe = union of CoCs appearing in crosswalk + PIT
base = pd.DataFrame({'coc_number': sorted(
    set(cw['coc_number']).union(set(hl['coc_number'])))})
# coc_name: prefer crosswalk name, fall back to PIT name
cw_names = cw[['coc_number', 'coc_name']].drop_duplicates('coc_number')
panel = (base.merge(cw_names, on='coc_number', how='left')
         .merge(hl[['coc_number', 'coc_name_pit', 'total_population',
                    'overall_homeless', 'unsheltered_homeless', 'family_homeless',
                    'homeless_per_10k', 'unsheltered_per_10k']],
                on='coc_number', how='left')
         .merge(agg, on='coc_number', how='left')
         .merge(saiz_coc, on='coc_number', how='left')
         .merge(wrluri_coc, on='coc_number', how='left'))
panel['coc_name'] = panel['coc_name'].fillna(panel['coc_name_pit'])
panel = panel.drop(columns=['coc_name_pit'])

cols = ['coc_number', 'coc_name', 'total_population',
        'overall_homeless', 'unsheltered_homeless', 'family_homeless',
        'homeless_per_10k', 'unsheltered_per_10k',
        'rent_coc', 'income_coc', 'saiz_elasticity', 'wrluri_coc']
panel = panel[cols].sort_values('coc_number').reset_index(drop=True)
panel.to_csv(OUT_CSV, index=False)
print('\nPANEL written:', OUT_CSV, 'shape', panel.shape)

# ----------------------------------------------------------------------------
# Coverage report
# ----------------------------------------------------------------------------
def nn(c):
    return int(panel[c].notna().sum())


full_core = panel.dropna(subset=['homeless_per_10k', 'rent_coc', 'income_coc'])
full_any_supply = full_core[full_core['saiz_elasticity'].notna()
                            | full_core['wrluri_coc'].notna()]

cov = {
    'acs_dataset_used': f'{ACS_YEAR} {ACS_DATASET}',
    'acs_note': 'ACS5 2024 used (full county coverage 3222); ACS1 2024 covers only ~861 counties so would gut Balance-of-State CoC coverage.',
    'n_coc_total': int(len(panel)),
    'n_with_total_population': nn('total_population'),
    'n_with_overall_homeless': nn('overall_homeless'),
    'n_with_homeless_per_10k': nn('homeless_per_10k'),
    'n_with_unsheltered_per_10k': nn('unsheltered_per_10k'),
    'n_with_family_homeless': nn('family_homeless'),
    'n_with_rent_coc': nn('rent_coc'),
    'n_with_income_coc': nn('income_coc'),
    'n_with_saiz_elasticity': nn('saiz_elasticity'),
    'n_with_wrluri_coc': nn('wrluri_coc'),
    'saiz_match_rate': round(float(saiz_match_rate), 4),
    'saiz_matched_count': int(n_saiz_matched),
    'saiz_total_count': int(n_saiz),
    'n_full_core_homeless_rent_income': int(len(full_core)),
    'n_full_coverage_core_plus_any_supply': int(len(full_any_supply)),
    'n_full_coverage_with_saiz': int(full_core['saiz_elasticity'].notna().sum()),
    'n_full_coverage_with_wrluri': int(full_core['wrluri_coc'].notna().sum()),
    'failed_sources': failed_sources,
}
with open(OUT_JSON, 'w') as f:
    json.dump(cov, f, indent=2)
print('COVERAGE written:', OUT_JSON)
print(json.dumps(cov, indent=2))

# sanity-check sample CoCs
print('\nSAMPLE CoCs:')
for c in ['NY-600', 'CA-600', 'IL-510']:
    row = panel[panel['coc_number'] == c]
    if row.empty:
        print(c, 'NOT IN PANEL')
    else:
        print(row.to_dict('records')[0])
