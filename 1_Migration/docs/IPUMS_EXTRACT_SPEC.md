# IPUMS USA Extract Specification — RMD-SRC Migration v1.0

Implements PRE_REG v1.0 §2.1 (data source), §2.2 (PUMA geography), §2.3 (2012–2023 window), §2.4 (ℙ₀ demographic species), and the PUMA-level aggregates needed to build §2.5 observables (opportunity index, density).

Extract name suggestion: `usa_rmdsrc_v1`

## Samples (12)

ACS 1-year samples — one per time bin t = 2012 … 2023:

`us2012a, us2013a, us2014a, us2015a, us2016a, us2017a, us2018a, us2019a, us2020a, us2021a, us2022a, us2023a`

Note: 2020 ACS 1-year was an experimental release due to COVID — keep it; PRE_REG §2.3 explicitly treats 2020–2023 as an adversarial holdout window.

## Variables

### Identifiers / weighting (required)
- `YEAR` — survey year
- `SAMPLE` — IPUMS sample code
- `SERIAL`, `PERNUM` — household / person id
- `PERWT` — person weight
- `HHWT` — household weight
- `GQ` — group quarters (used to filter institutionalized population out)

### Geography (required for §2.2 PUMA-to-PUMA migration)
- `STATEFIP` — current state FIPS
- `PUMA` — current PUMA (2012+ uses 2010-vintage PUMAs)
- `MIGRATE1` / `MIGRATE1D` — 1-year migration status
- `MIGPLAC1` — state of residence 1 year ago
- `MIGPUMA1` — PUMA of residence 1 year ago

### Demographics for ℙ₀ (§2.4 Option A cross-product)
- `AGE` — single year, bin to {18–29, 30–44, 45–59, 60+}
- `MARST` — marital status (for family-structure construction)
- `NCHILD` — number of own children in household (for family-structure construction)
- `EDUC` + `EDUCD` — education attainment (bin to BA+ / less-than-BA via EDUCD ≥ 101)
- `HHINCOME` — household income (for tertile bins by year)

### PUMA-level aggregates for §2.5 opportunity index (computed downstream)
These are person-level variables; PUMA-year aggregates are built in the derived stage:
- `INCTOT` — total personal income (aggregate to PUMA-year median household income, but HHINCOME already gives this for the household-head record)
- `EMPSTAT` + `EMPSTATD` — employment status (PUMA-year EMP/POP ratio for ages 25–54)
- `OWNERSHP` — owned/rented
- `RENTGRS` — gross rent (PUMA-year median rent for affordability index)
- `VALUEH` — house value (sanity check on ownership cost; not in PCA per §2.5)
- `LABFORCE` — labor force participation (subset filter for EMP/POP)

### Auxiliary (kept for falsifier audits, not in primary pipeline)
- `SEX`
- `RACE`, `HISPAN` — for v1.1 sensitivity slices if needed (NOT used in ℙ₀ v1.0)
- `CITIZEN` — for exclusion of recent immigrants from "internal migration" event definition per §2.7

## Case selection

Apply at extract time to keep size manageable:
- `AGE ≥ 18` (PRE_REG §2.4 uses age bins starting at 18)
- `GQ` in {1, 2, 5} (households + non-inst group quarters; drop institutionalized)

Do NOT case-select on MIGRATE1 at the extract — we need non-movers as the denominator for cell-population baselines.

## Output format
- Format: Fixed-width or CSV; CSV preferred for direct parquet conversion
- Structure: Rectangular (one row per person)
- Compression: gzip if available

## Estimated size
~3M persons/year × 12 years × ~25 variables ≈ 36M rows, 3–5 GB compressed.

---

## How to submit

### Path A: IPUMS API (preferred, fully automated)

1. Register at https://account.ipums.org/registration if you don't have an account
2. Generate API key at https://account.ipums.org/api_keys
3. Set environment variable (PowerShell): `$env:IPUMS_API_KEY = "<your-key>"`
4. Run: `python D:\Migration\src\submit_ipums_extract.py`

The submit script handles spec → API → poll-until-ready → download to `D:\Migration\data\raw\ipums\`.

### Path B: Manual web extract

1. Log in at https://usa.ipums.org/usa-action/menu
2. Select the 12 samples listed above
3. Add the variables listed above
4. Set case selections per the section above
5. Submit and wait for email notification (typically 5–30 min)
6. Download the .dat.gz or .csv.gz to `D:\Migration\data\raw\ipums\`

Either path works. Path A is faster on iteration.

## Citation
IPUMS USA: Steven Ruggles et al. IPUMS USA: Version 15.0. Minneapolis, MN: IPUMS, 2024. https://doi.org/10.18128/D010.V15.0
