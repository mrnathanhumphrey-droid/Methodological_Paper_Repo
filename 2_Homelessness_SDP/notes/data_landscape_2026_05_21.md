# IDP Substrate — Data Landscape Recon (2026-05-21)

Subagent reconnaissance for the broad IDP data sweep. Pivot from narrow conflict→displacement framing (substrate 9 v1, paused at `75ca36a`) to global multi-source exploratory pull, then thread-following, then pre-reg on whatever threads emerge.

## Scope locked
- Geographic: global (~190 countries)
- Temporal: 1998+
- Cost: free + account-walled (Chrome handoffs)
- Methodology framing: its own thing. Mentioned in methodology corpus, uses the framework, but not formally substrate 9 of Paper 6.

## Top-line
- 32 sources surveyed across 6 tiers
- 31 fetchable endpoints in `_scripts/_landscape_targets.json`
- 8 require Chrome handoff: EM-DAT, IDMC API key, ACAPS API key, Copernicus CDS, DHS per-country, MICS per-country, GTD (likely denied), HOT Export

## Verification status

WebFetch was denied for most live probes during recon. URLs are from search-result snippets + existing project fetcher patterns + indexed docs pages. Endpoints used by existing IDP fetchers (UCDP, HDX HAPI v2 IDPs, GDELT) are verified working from the local infrastructure. The "UNVERIFIED" tag on individual JSON entries means HEAD/GET dry-run needed before bulk pull.

## Tier 1 — IDP / displacement core

### IDMC GIDD (Global Internal Displacement Database)
- Country-year IDP stocks + flows (conflict + disaster); IDU event-level updates
- API: `https://helix-tools-api.idmcdb.org/external-api/gidd/...?client_id=KEY`
- HDX mirror (no auth): `https://data.humdata.org/dataset/idmc-internal-displacement-global-database`
- Docs: https://www.internal-displacement.org/database/api-documentation/
- Format: JSON/GeoJSON/CSV; <50 MB GIDD bulk, <500 MB IDU
- Coverage: 2008+ (GIDD), 2016+ (IDU); ~200 countries
- Throttle: 2 s (Cloudflare)
- Cache: `D:/IDP/data/idmc_gidd/`
- Notes: HDX mirror is cleanest first pull

### UNHCR Refugee Data Finder + IDP
- Refugees, asylum-seekers, IDPs of concern, stateless; country origin × country asylum × year
- API docs: https://api.unhcr.org/docs/refugee-statistics.html
- Base: `https://api.unhcr.org/population/v1/population/?yearFrom=1990&yearTo=2024&coo_all=true&coa_all=true&download=true`
- ODP per-country: https://data.unhcr.org/en/country/{ISO3} (often JS-rendered → Chrome for subsets)
- Format: JSON, CSV via `&download=true`; <100 MB
- Coverage: 1951+ refugees, 1993+ IDPs; global
- Throttle: 1-2 s
- Cache: `D:/IDP/data/unhcr_rdf/`

### IOM DTM via HDX HAPI v2
- Admin-2 IDP / mobility figures by reporting round
- `https://hapi.humdata.org/api/v2/affected-people/idps?location_code={ISO3}&admin_level=2&output_format=json&offset={N}`
- Country-list: `/api/v2/metadata/location`
- Auth: base64-encoded `email:project` app identifier (already wired in `fetch_dtm_hdx.py`)
- Format: JSON paged (1000/page); ~50-200 MB across all countries
- Coverage: ~2018+, ~70 countries
- Throttle: 1.5 s
- Cache: `D:/IDP/data/dtm/{country}/`
- Notes: existing fetcher does 4 countries; global expansion = loop the location list

### HDX HAPI v2 — other endpoints
- IPC food security, baseline population, humanitarian needs, refugee returns
- `/v2/food-security-nutrition-poverty/food-security`
- `/v2/food-security-nutrition-poverty/food-prices-market-monitor`
- `/v2/geography-infrastructure/baseline-population`
- `/v2/affected-people/refugees-persons-of-concern`
- `/v2/coordination-context/humanitarian-needs`
- Auth: same app identifier; high ROI on existing wiring
- Throttle: 1.5 s
- Cache: `D:/IDP/data/hdx_hapi/{endpoint_slug}/`

### EM-DAT (CRED disaster database)
- Global disaster events 1900+; deaths / affected / displaced / damage
- Login at https://public.emdat.be/ → form-driven XLSX export. No direct bulk URL.
- Auth: **free account; Chrome handoff**
- Format: XLSX ~50 MB; coverage 1900+, global
- Cache: `D:/IDP/data/emdat/`
- Notes: aggregated HDX mirrors lag the live DB

### ReliefWeb API
- Curated humanitarian reports + disaster taxonomy from 4000+ sources
- `https://api.reliefweb.int/v2/disasters?appname=IDP-Research&limit=1000`
- Collections: reports, disasters, countries, jobs, sources
- Docs: https://apidoc.reliefweb.int/
- Auth: none; `appname` query param required
- Format: JSON (HAL-paginated); disasters <10 MB, reports millions
- Coverage: 1996+, global
- Throttle: 1-2 s
- Cache: `D:/IDP/data/reliefweb/`

### IPC / FEWS NET food insecurity
- Sub-national IPC acute food insecurity phase + population
- IPC API hub: https://www.ipcinfo.org/ipc-country-analysis/api/ (key on request)
- FEWS NET FDW: https://fdw.fews.net/api/
- Shapefiles on HDX e.g. `https://data.humdata.org/dataset/{country}_current_situation_fewsnet_ipc_shapefile_for_{year}`
- Format: GeoJSON/vector tiles (IPC); shapefile (FEWS NET via HDX)
- Coverage: 2009+ (FEWS NET); 30+ countries (IPC)
- Throttle: 2 s
- Cache: `D:/IDP/data/ipc_fewsnet/`
- Notes: HAPI's `/food-security` endpoint already harmonizes IPC

### FTS (UN Financial Tracking Service)
- Humanitarian funding flows by appeal/country/year
- Docs: https://fts.unocha.org/content/fts-public-api
- v2: https://api.hpc.tools/docs/v2/
- Example: `https://api.hpc.tools/v2/public/fts/flow?countryISO3=YEM&year=2023`
- Auth: none
- Format: JSON/XML
- Coverage: 2000+, global
- Throttle: 1-2 s
- Cache: `D:/IDP/data/fts/`
- Notes: funding = response signal; pairs with displacement need

### ACAPS country analytics
- INFORM Severity Index, humanitarian access score, crisis briefs
- API: `https://api.acaps.org/api/v1/inform-severity-index/?date=Mar2024`
- HDX mirror: https://data.humdata.org/organization/acaps
- Auth: **free subscription token (Chrome handoff)**; HDX mirror open
- Format: CSV
- Coverage: ~2017+, global
- Throttle: 2 s
- Cache: `D:/IDP/data/acaps/`

### REACH Initiative Resource Centre
- Multi-Sector Needs Assessments (MSNAs), per-crisis microdata
- HDX org: https://data.humdata.org/organization/reach-initiative (60+ datasets)
- Auth: none on HDX
- Format: XLSX/CSV/shapefile
- Coverage: 2014+, ~30 crisis countries
- Throttle: 2 s
- Cache: `D:/IDP/data/reach/`
- Skip if breadth>depth not wanted

## Tier 2 — climate / environment drivers

### ERA5 / Copernicus CDS
- Hourly + monthly atmospheric reanalysis (temp, precip, soil moisture, wind)
- API: `https://cds.climate.copernicus.eu/api/v2/`
- Dataset: `reanalysis-era5-single-levels-monthly-means`
- Setup: https://cds.climate.copernicus.eu/how-to-api
- Auth: **account + per-dataset ToU click-through → `.cdsapirc` token (Chrome handoff)**
- Format: NetCDF/GRIB; **>50 GB global monthly 1940+; subset spatially**
- Coverage: 1940+, global, 0.25° resolution
- Throttle: queue-based, jobs run minutes to hours
- Cache: `D:/IDP/data/era5/`

### NASA EONET
- Curated natural-hazard events (wildfires, storms, floods, EQ, volcanoes)
- `https://eonet.gsfc.nasa.gov/api/v3/events`, `/categories`, `/sources`
- Auth: none
- Format: JSON/GeoJSON; <50 MB
- Coverage: ~2015+, global
- Throttle: 1-2 s
- Cache: `D:/IDP/data/eonet/`

### SPEI (CSIC SPEIbase)
- Standardized Precipitation-Evapotranspiration Index, 1-48 month scales
- Page: https://spei.csic.es/database.html
- Repository: https://digital.csic.es/handle/10261/72264
- Format: NetCDF, 0.5° grid; ~500 MB-2 GB per timescale
- Coverage: 1901-2023, monthly
- Throttle: 2 s
- Cache: `D:/IDP/data/spei/`
- Notes: 1/6/12-month most useful

### CHIRPS (UCSB CHC)
- Rainfall 0.05° (~5 km), daily/pentad/dekad/monthly
- v2 monthly: `https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/netcdf/chirps-v2.0.monthly.nc`
- v3: `https://data.chc.ucsb.edu/products/CHIRPS-3.0/`
- Auth: none
- Format: NetCDF/GeoTIFF/BIL; monthly global ~5 GB; daily global >50 GB
- Coverage: 1981+, 60°N-60°S
- Throttle: 2 s
- Cache: `D:/IDP/data/chirps/`
- Notes: **v2 ends Dec 2026 — target v3**

## Tier 3 — conflict / violence

### UCDP-GED
- Event-level fatal violence 1989+, georeferenced
- `https://ucdp.uu.se/downloads/ged/ged251-csv.zip` (verified)
- Format: CSV ZIP, ~150 MB
- Coverage: 1989 - 2024-12-31 (v25.1), global
- Throttle: 2 s
- Cache: `D:/IDP/data/ucdp/`
- Notes: existing fetcher present; global panel = skip country filter

### GDELT 2.0
- Media-event extraction every 15 min + Global Knowledge Graph
- Master: `http://data.gdeltproject.org/gdeltv2/masterfilelist.txt`
- Per-15-min: `http://data.gdeltproject.org/gdeltv2/{YYYYMMDDHHMMSS}.export.CSV.zip`
- GKG (skip): `...gkg.csv.zip` — **2.5 TB/year**, default to events-only
- GDELT 1.0 events: `http://data.gdeltproject.org/events/index.html`
- Auth: none
- Throttle: 0.5-1 s
- Cache: `D:/IDP/data/gdelt/`

### GTD (START/UMD)
- Terrorist incidents 1970-2020, ~190k records
- https://www.start.umd.edu/gtd-download
- Auth: **registration; reportedly closed 2025**
- Format: XLSX ~105 MB; frozen 1970-2020
- Cache: `D:/IDP/data/gtd/`
- Skip if registration denied — UCDP-GED + GDELT substantially overlap

### ICEWS (Harvard Dataverse) — DISCONTINUED
- Coded socio-political events (CAMEO), 1995-2023
- Historic: `https://doi.org/10.7910/DVN/28075`
- API: `https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/28075`
- Weekly: `doi:10.7910/DVN/QI2T9A`
- **Successor POLECAT: `doi:10.7910/DVN/AJGVIT`**
- Format: TSV per file; historic ~10 GB
- Coverage: 1995-2023 frozen
- Throttle: 2 s
- Cache: `D:/IDP/data/icews/` and `D:/IDP/data/polecat/`

### V-Dem v15
- 531 democracy indicators + 245 indices, 202 countries, 1789-2024
- https://www.v-dem.net/data/the-v-dem-dataset/country-year-v-dem-fullothers-v15/
- GitHub releases: https://github.com/vdeminstitute/vdemdata/releases
- Format: CSV/R/Stata in ZIP; ~100 MB
- Coverage: 1789-2024
- Throttle: 1-2 s
- Cache: `D:/IDP/data/vdem/`

### Polity V (CSP)
- Regime authority -10 to +10, 1800-2018
- INSCR page: https://www.systemicpeace.org/inscrdata.html
- File pattern: `https://www.systemicpeace.org/inscr/p5v2018.xls`
- Format: XLS/SPSS; <10 MB
- Coverage: 1800-2018 frozen — use V-Dem for post-2018
- Cache: `D:/IDP/data/polity5/`

### Correlates of War (COW)
- NMC v6 (military capabilities), MID v5 (interstate disputes), wars
- https://correlatesofwar.org/data-sets/
- NMC: /national-material-capabilities/, MID: /mids/
- Format: CSV ZIPs; <50 MB total
- Coverage: 1816-2016 (NMC); 1816-2014 (MID)
- Cache: `D:/IDP/data/cow/`

## Tier 4 — health / wellbeing

### DHS (Demographic and Health Surveys)
- Microdata + indicators on health/nutrition/fertility/mortality
- Indicator API: `https://api.dhsprogram.com/rest/dhs/data?indicatorIds=...&countryIds=...&perpage=5000`
- Microdata per-country: https://dhsprogram.com/data/dataset/{country}_{phase}.cfm
- Auth: **indicator API open; microdata requires per-country project request (24-48h, Chrome handoff)**
- Format: JSON (indicators); SAS/SPSS/Stata (microdata)
- Coverage: 1985+, 90+ countries
- Cache: `D:/IDP/data/dhs/`

### UNICEF MICS
- Household surveys, 124 countries, child wellbeing
- https://mics.unicef.org/surveys
- Mirror: https://microdata.worldbank.org/index.php/catalog/MICS
- Auth: **registration + 3-business-day review (Chrome handoff)**
- Format: SPSS/Stata
- Coverage: 1995+, 124 countries
- Cache: `D:/IDP/data/mics/`

### WHO GHO (Global Health Observatory)
- Life expectancy, child mortality, immunization, NCDs
- List: `https://ghoapi.azureedge.net/api/Indicator`
- Data: `https://ghoapi.azureedge.net/api/{IndicatorCode}`
- Auth: none
- Format: JSON; small per-indicator (<10 MB), full <2 GB
- Coverage: ~1990+, ~194 countries
- Throttle: 1 s
- Cache: `D:/IDP/data/who_gho/`
- Notes: **OData API deprecates end of 2025**

### WHO Health Emergency Dashboard
- Real-time outbreak events
- HDX mirror; Outbreak News: `https://www.who.int/api/news/diseaseoutbreaknews/sfhelp`
- Format: CSV (HDX); JSON (REST)
- Coverage: ~2019+, global
- Cache: `D:/IDP/data/who_emergencies/`

### WFP VAM / Hunger Monitoring (mVAM)
- Food security indicators (FCS, rCSI) from phone monitoring + market prices
- mVAM **POST** API: `http://vam.wfp.org/mvam_monitoring/api.aspx`
- DataViz UI: https://dataviz.vam.wfp.org/
- HungerMap: https://hungermap.wfp.org/
- Auth: none
- Format: XML/JSON (**POST-only**)
- Coverage: 2015+, ~40 countries
- Cache: `D:/IDP/data/wfp_vam/`
- Notes: **POST-only — needs separate wrapper**

## Tier 5 — economic context

### World Bank WDI
- ~1500 development indicators, 217 countries, 1960+
- API: `https://api.worldbank.org/v2/country/all/indicator/{INDICATOR}?format=json&per_page=20000`
- Bulk: `https://databank.worldbank.org/data/download/WDI_CSV.zip`
- Auth: none
- Format: JSON (API); CSV ZIP (bulk, ~250 MB)
- Throttle: 0.5-1 s
- Cache: `D:/IDP/data/wb_wdi/`

### IMF IFS
- Macro/financial stats; BoP; fiscal
- Dataflow list: `http://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow`
- CompactData: `.../CompactData/IFS/{freq}.{country}.{indicator}?startPeriod=1990`
- v3 portal: https://sdmxcentral.imf.org/
- Auth: none for v1
- Format: SDMX-JSON
- Coverage: 1948+
- Throttle: 1-2 s
- Cache: `D:/IDP/data/imf_ifs/`

### ILOSTAT
- Employment, wages, informality
- Bulk: `https://www.ilo.org/ilostat-files/WEB_bulk_download/indicator/{INDICATOR}.csv.gz`
- SDMX: `https://sdmx.ilo.org/rest/data/ILO,DF_{flow}/{key}`
- Auth: none
- Format: CSV.GZ (bulk)
- Coverage: 1947+, 190+ countries
- Throttle: 1 s
- Cache: `D:/IDP/data/ilostat/`

### UNDP HDR
- HDI, GDI, IHDI, MPI for 193 countries
- API: https://hdrdata.org/ (key)
- Annex XLSX: `https://hdr.undp.org/sites/default/files/2023-24_HDR/HDR23-24_Statistical_Annex_HDI_Table.xlsx`
- Auth: API key (free); XLSX open
- Format: XLSX/JSON
- Coverage: 1990+, 193 countries
- Cache: `D:/IDP/data/undp_hdr/`

## Tier 6 — geographic / population baseline

### WorldPop
- Gridded population 100 m + 1 km, annual
- REST: https://www.worldpop.org/rest/data
- Hub: https://hub.worldpop.org/project/list
- HDX mirror: https://data.humdata.org/dataset/worldpop-population-counts-for-world
- STAC: https://stac.worldpop.org/
- Auth: none
- Format: GeoTIFF; **per-country per-year ~500 MB (100m); global per-year >50 GB**
- Coverage: 2000+ (1 km), 2015-2030 (100 m)
- Throttle: 2 s
- Cache: `D:/IDP/data/worldpop/`

### Meta HRSL
- 30 m gridded population
- AWS bucket: `https://dataforgood-fb-data.s3.amazonaws.com/hrsl-cogs/{country}/...`
- HDX: `https://data.humdata.org/dataset/highresolutionpopulationdensitymaps-{ISO3}`
- Auth: none
- Format: Cloud-Optimized GeoTIFF; per-country 100 MB-2 GB
- Coverage: snapshot ~2020 (not annual)
- Throttle: 1 s
- Cache: `D:/IDP/data/hrsl/`

### OSM / HOT Export
- Roads, buildings, POIs
- Geofabrik: `https://download.geofabrik.de/{region}/{country}-latest.osm.pbf`
- HOT Export: https://export.hotosm.org/ + Raw Data API
- Auth: OSM login for HOT; none for Geofabrik
- Format: PBF/Shapefile/GeoJSON; per-country 100 MB-5 GB
- Throttle: 2-3 s
- Cache: `D:/IDP/data/osm/`

### Natural Earth
- Public-domain boundary vectors 1:10m / 50m / 110m
- Admin 0: `https://www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_countries.zip`
- Admin 1: `https://www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_1_states_provinces.zip`
- Auth: none
- Format: Shapefile ZIP; <100 MB
- Cache: `D:/IDP/data/natural_earth/`

## Blockers / deprecation watch

- **ICEWS** discontinued April 2023 → POLECAT successor
- **GTD** likely closed for new registrations as of 2025
- **WHO GHO OData API** deprecates end of 2025
- **CHIRPS v2** ends Dec 2026 → v3
- **Polity V** frozen at 2018 → V-Dem for post-2018
- **WFP mVAM** POST-only (separate wrapper)
- **GDELT 2.0 GKG** = 2.5 TB/year (use events-only)
- **WorldPop 100m global** per-year >50 GB (default to 1 km)

## Account / Chrome handoff checklist

| Source | Action |
|---|---|
| EM-DAT | Register at public.emdat.be → export full DB XLSX |
| IDMC direct API | Request `client_id` via web form |
| ACAPS API | Subscribe at api.acaps.org for token |
| Copernicus CDS (ERA5) | Register, accept ToU, copy token to `~/.cdsapirc` |
| DHS Program | (defer) Register research project + per-country requests |
| MICS / UNICEF | Register + per-country requests (top-20 IDP-affected first) |
| GTD | Register at START/UMD (likely denied as of 2025) |
| HOT Export | OSM login if going beyond Geofabrik |

## Recommended first-wave parallel pulls (anonymous, fetchable today)

1. UCDP-GED v25.1 (single ZIP)
2. IDMC GIDD via HDX CKAN package_show
3. UNHCR Refugee Data Finder
4. World Bank WDI bulk CSV ZIP
5. UNDP HDR statistical annex XLSX
6. V-Dem v15 Full+Others (unverified filename)
7. ReliefWeb disasters
8. NASA EONET events
9. Natural Earth admin 0 + 1
10. HDX HAPI v2 baseline-population + food-security + humanitarian-needs (existing auth)
11. COW NMC v6 + MID v5 (landing pages first)
12. SPEI 1/6/12-month NetCDF (unverified filenames)
13. CHIRPS v3 monthly global (unverified filename)
14. GDELT 2.0 master filelist
15. ICEWS historic + POLECAT metadata
