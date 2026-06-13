# Data Sources — Phase 0 Provenance

Public sources for substrate-9 IDP study. All raw data files are gitignored
per `.gitignore`; SHA-256 hashes recorded in `manifest.json`.

## UCDP-GED (Uppsala Conflict Data Program — Georeferenced Event Dataset)

- **Homepage:** https://ucdp.uu.se/
- **Downloads:** https://ucdp.uu.se/downloads/
- **Coverage:** 1989-present, global, georeferenced violent events
- **Use:** Stage-B contemporary conflict shocks; one-sided-violence subset
  (type_of_violence=3) as substitute for EOSV when geocoding needed
- **Citation:** Sundberg, R., & Melander, E. (2013). Introducing the UCDP
  georeferenced event dataset. *Journal of Peace Research*, 50(4),
  523-532.

## ACLED (Armed Conflict Location & Event Data) — DROPPED per redline Entry 001

- **Status:** v1 spec dropped via `notes/pre_reg_redline.md` Entry 001
  (2026-05-17). Non-institutional PI access denied. ACLED replaced by
  GDELT for cross-source validation. Threshold + aggregation unchanged.
- **Homepage:** https://acleddata.com/ (retained for documentation)
- **API:** https://api.acleddata.com/acled/read (requires institutional
  registration + API key; non-institutional access gated)
- **Citation:** Raleigh, C., Linke, A., Hegre, H., & Karlsen, J. (2010).
  Introducing ACLED. *Journal of Peace Research*, 47(5), 651-660.

## GDELT 2.0 Event Database (replaces ACLED per redline Entry 001)

- **Homepage:** https://www.gdeltproject.org/
- **Daily event files:** http://data.gdeltproject.org/events/{YYYYMMDD}.export.CSV.zip
- **Documentation:** http://data.gdeltproject.org/documentation/GDELT-Data_Format_Codebook.pdf
- **Coverage:** April 2013-present, global, machine-coded news events with lat/long
- **Use:** Cross-source conflict event validation against UCDP-GED
  (pre-cond 2); Yemen post-2022 coverage check (pre-cond 4); robustness
  axis 1 substitution
- **License:** Creative Commons (no auth, no institutional requirement)
- **Citation:** Leetaru, K., & Schrodt, P. A. (2013). GDELT: Global Data
  on Events, Language, and Tone, 1979-2012. *ISA Annual Convention*.
- **FIPS country codes used:** Colombia=CO, Sudan=SU, DRC=CG, Yemen=YM
- **Quality caveat:** GDELT is machine-coded from news; false-positive
  rate higher than ACLED's human coding. Mitigated by admin-2 × year
  aggregation in pre-cond 2.

## IOM DTM (Displacement Tracking Matrix)

- **Homepage:** https://dtm.iom.int/
- **Per-country pages:**
  - Sudan: https://dtm.iom.int/sudan
  - DRC: https://dtm.iom.int/democratic-republic-congo
  - Yemen: https://dtm.iom.int/yemen
- **Colombia substitute:** Unidad para las Víctimas RUV
  (https://www.unidadvictimas.gov.co/) — DTM coverage of Colombia is
  minimal; RUV is the canonical Colombian IDP registry
- **Use:** Primary outcome — admin-2 × year IDP counts
- **Schema drift:** see `data/dtm/schema_rulebook.json` for the locked
  per-country harmonization rules

## GADM (Global Administrative Areas)

- **Homepage:** https://gadm.org/
- **Per-country downloads:** https://gadm.org/download_country.html
- **Direct URL pattern:** `https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_{ISO3}.gpkg`
- **Coverage:** Global admin-0 through admin-3 boundaries
- **Use:** Admin-2 polygons for spatial join with conflict events + DTM
  panels (level 2 = county/municipality/governorate equivalent)
- **License:** Free for academic + non-commercial use; license details
  at https://gadm.org/license.html

## EOSV (Ethnic One-Sided Violence)

- **Homepage:** https://www.pcr.uu.se/research/ucdp/datasets/eosv/
- **Coverage:** 1989-2013 (ENDS 2013 per locked constraint)
- **Use:** Sudan historical atrocity-count covariate, 2003-2010 window
  (within EOSV coverage); cross-country one-sided violence indicator
- **Citation:** Eck, K., & Hultman, L. (2007). One-sided violence
  against civilians in war: insights from new fatality data. *Journal of
  Peace Research*, 44(2), 233-246.

## Nunn-Puga Terrain Ruggedness Index

- **Homepage:** https://diegopuga.org/data/rugged/
- **Use:** Terrain ruggedness covariate per admin-2 (H_TERRAIN test)
- **Citation:** Nunn, N., & Puga, D. (2012). Ruggedness: The blessing of
  bad geography in Africa. *Review of Economics and Statistics*, 94(1),
  20-36.

## Africapolis / GHS-SMOD

- **Africapolis:** https://africapolis.org/ — African urban
  geography (Sudan, DRC; secondary for Yemen)
- **GHS-SMOD:** https://human-settlement.emergency.copernicus.eu/
  ghs_smod2023.php — global urban/rural classification
- **Use:** urban_rural binary covariate per admin-2

## CINEP (Centro de Investigación y Educación Popular, Colombia)

- **Homepage:** https://www.cinep.org.co/
- **Noche y Niebla database:** https://www.nocheyniebla.org/
- **Use:** Colombia historical violence archive (La Violencia 1948-2002,
  pre-FARC + early-FARC period) for `historical_atrocity_count`
  covariate per Colombian municipio

## Sudan Open Archive

- **Homepage:** https://www.sudanarchive.net/
- **Use:** Sudan colonial-era cartographic + administrative records for
  pre-1994 Fur dar polygon digitization

## International Crisis Group + Salisbury 2015

- **ICG:** https://www.crisisgroup.org/
- **Salisbury 2015:** Chatham House Research Paper, "Yemen and the
  Saudi-Iranian 'Cold War'"
- **Use:** Yemen Six Wars (2004-2010) timeline + maps for pre-2014
  Houthi conflict zone polygon

## Fetch dates

All fetches dated in `manifest.json` per file. Phase 0 lock fetches
executed at the initial commit; Phase 2 fetches dated separately.
