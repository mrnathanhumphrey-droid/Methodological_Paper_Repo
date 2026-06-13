# 06 — Siting / Yield Research Landscape v0

> **🔴 SUPERSEDED FOR HEADLINE CITATIONS — see `02_CLAIMS_LEDGER.md` + verification memos `07_`, `10_`, `11_`, `16_`.**
>
> **Corrections established by verification passes v1+v2 (2026-05-27):**
> - **ERR-3 (CLM-014):** v0 said "soiling losses arid: 3-7%/yr if uncleaned (Ilse 2019)." Correct (verified verbatim via local Ilse 2019 PDF): Ilse's 3-4% is the **global aggregate** 2018 solar production loss; 4-7% is the **projected global** 2023 loss. NOT an arid-regions-only annual rate. Regional cuts need separate attribution (Sayyah 2014 / Costa 2018 / Maghami 2016 / Figgis Qatar papers). Verification memo `11_`.
> - **NSRDB vintage notes (Sengupta 2018):** 4 km / 30-min are the 2018-paper PSM v3 figures. Current NSRDB suite (post-2018) includes Himawari-8 at 2 km / 10-min, and Meteosat IODC for India added later. Cite Sengupta 2018 for the original paper; cite NREL Developer API docs + Buster et al. 2022 for current capability. Verification memo `07_`.
> - **POA modeling stack (CLM-013) VERIFIED:** Holmgren et al. 2018 JOSS pvlib paper + direct source-code verification of all transposition models in `pvlib/irradiance.py` v0.15.1 (2026-04-21). Cite both Holmgren 2018 (foundational) + Anderson et al. 2023 JOSS update (current state). Verification memo `10_`.
> - **Climate-stratified PLR (NEW from Jordan 2022, also relevant to siting/yield):** Jordan et al. 2022 PV Fleet paper establishes p<0.001 temperature-PLR correlation in Al-BSF c-Si ground-mounted fleet — T3 cool -0.48 → T5 hot -0.88 %/yr. Uses **Karin et al. 2019 PV-specific climate zones** (Arrhenius-weighted equivalent rack temperature × specific-humidity bins), **explicitly rejecting Köppen-Geiger** as "agriculture-focused." Substrate should adopt Karin zones for any climate-axis work. Verification memo `16_`.
> - **NREL DuraMAT Data Hub** hosts the public Fleet Degradation Insights dataset (DOI 10.21948/1842958). Operator-pullable; aggregate PLR + non-attributable system metadata.
>
> All other v0 claims remain NEEDS-VERIFICATION until processed through meta-pre-reg §3.

> **STATUS:** NEEDS-VERIFICATION per `01_METAPREREG_v1.0` §8. LLM-surfaced citation
> leads from subagent run 2026-05-27. UNVERIFIED-LEAD tags mark items with
> explicit lower confidence.

# Solar Siting + Yield Research Inventory

---

## 1. Research clusters

### NREL Solar Resource Assessment + Forecasting (Golden, CO)
Lead authors: Manajit Sengupta, Yu Xie, Aron Habte, Andrew Mills. Outputs: NSRDB v3/v4, PSM3, FARMS radiative transfer.
- Sengupta et al., "The National Solar Radiation Data Base (NSRDB)," *Renewable & Sustainable Energy Reviews*, 2018 — DOI: 10.1016/j.rser.2018.03.003 (canonical pre-2020).
- Yu Xie et al., "FARMS-NIT: A fast all-sky radiation model for narrowband irradiance on tilted surfaces," *Solar Energy*, 2020 — DOI: 10.1016/j.solener.2020.03.013 UNVERIFIED-LEAD (volume/page).
- Habte et al., NSRDB v4 update — UNVERIFIED-LEAD (likely NREL/TP-5D00-) check NREL publications database.

### Sandia PV Performance Modeling Collaborative (PVPMC) (Albuquerque, NM)
Lead authors: Joshua Stein, Clifford Hansen, Bruce King, Daniel Riley. Hosts PVPMC workshop, maintains Sandia Array Performance Model + pvlib lineage.
- Holmgren, Hansen, Mikofski, "pvlib python: a python package for modeling solar energy systems," *JOSS*, 2018 — DOI: 10.21105/joss.00884 (canonical).
- Deline et al., "Assessment of bifacial PV system performance modeling with bifacial_radiance and bifacialvf," IEEE PVSC — UNVERIFIED-LEAD.
- Anderson + Mikofski, "Slope-aware backtracking for single-axis trackers," NREL/TP-5K00-76626, 2020 — verify report ID.

### SAM development team (NREL)
Lead: Paul Gilman, Nicholas DiOrio, Janine Freeman.
- Freeman et al., "Validation of multiple tools for flat plate photovoltaic modeling against measured data," NREL/TP-6A20-61722 — pre-2020 but canonical; check for post-2020 update.

### Soiling research clusters
- NREL/Sandia/DLR/Fraunhofer ISE soiling consortium. Key author: Leonardo Micheli (Universidad de Jaén, Spain → moved; verify affiliation).
- Micheli et al., "Mapping photovoltaic soiling using spatial interpolation techniques," *Renewable Energy*, 2021 — DOI: 10.1016/j.renene.2020.12.046 UNVERIFIED-LEAD.
- Ilse et al. (Fraunhofer CSP), "Techno-economic assessment of soiling losses and mitigation strategies for solar power generation," *Joule*, 2019 — DOI: 10.1016/j.joule.2019.08.019 (canonical, pre-2020 boundary).

### PVsyst SA (Satigny, Switzerland)
Closed-source commercial; André Mermoud + Bruno Wittmer. Outputs: validation white papers on their site; no peer-reviewed stream. UNVERIFIED-LEAD on post-2020 peer outputs.

### Bifacial / tracking research
- NREL (Chris Deline, Silvana Ayala Pelaez), Sandia (Joshua Stein), and CFV Labs.
- Ayala Pelaez et al., "Comparison of bifacial solar irradiance model predictions with field validation," *IEEE J. Photovoltaics*, 2019 — DOI: 10.1109/JPHOTOV.2018.2877000 (pre-2020 canonical).
- Stein et al., "Bifacial PV system performance: separating fact from fiction," NREL/TP-5K00-74090 — UNVERIFIED-LEAD report ID.

### Sky-imager + short-horizon forecasting
- UC San Diego (Jan Kleissl group); now distributed across NREL, IBM Research, DTU.
- Kleissl et al. canonical 2013 book; post-2020 papers UNVERIFIED-LEAD.
- Nouri et al. (DLR), "Sky imager-based forecast of solar irradiance using machine learning," *Atmosphere*, 2022 — UNVERIFIED-LEAD DOI.

---

## 2. Established findings

| Quantity | Range | Canonical source | Notes |
|---|---|---|---|
| Module temperature coefficient (Pmax, c-Si) | −0.35 to −0.45 %/°C | IEC 61853 series; manufacturer datasheets | tight consensus |
| Module temperature coefficient (CdTe) | −0.25 to −0.30 %/°C | First Solar tech briefs; verify | thinner-film advantage well established |
| Soiling losses, arid (MENA, US SW) | 0.1–1.0 %/day accumulation; 3–7 %/yr if uncleaned | Ilse 2019 *Joule*; Micheli 2021 | high site variance |
| Soiling losses, temperate | 0.5–3 %/yr | Micheli/Smestad reviews — UNVERIFIED-LEAD specific paper | sparse data |
| Bifacial gain (utility, optimized albedo) | 5–15 % | Deline/Ayala Pelaez NREL; Stein Sandia | albedo & ground cover dominant |
| Bifacial gain (rooftop, low albedo) | 2–6 % | UNVERIFIED-LEAD | thinner literature |
| Single-axis tracker gain vs fixed-tilt | 15–25 % at low-latitude desert | NREL SAM validation; Bolinger LBNL utility-scale report | varies with DNI fraction |
| Spectral mismatch correction (annual, c-Si) | ±1–3 % | Lee/Panchula SPECTRAL papers — UNVERIFIED-LEAD | small but non-negligible for finance |
| LID (light-induced degradation, c-Si) | 1–3 % first hours | IEC 61215; legacy literature | PERC may differ |
| Long-term degradation rate (c-Si median) | 0.5–0.8 %/yr | Jordan & Kurtz, NREL meta-analysis | DOI: 10.1002/pip.1182 (pre-2020 canonical); Jordan 2022 update UNVERIFIED-LEAD |
| GHI-to-POA transposition error | 2–8 % RMS by model | Lave/Stein, Gueymard reviews | Perez vs Hay-Davies disagreement persists |

**Source disagreement zones:**
- Bifacial gain magnitude: NREL field studies tend toward 6–10 %; manufacturer claims 10–20 %.
- Cell-temperature models: Faiman vs King vs NOCT differ 2–5 °C on hot sunny days, propagating ~1–3 % yield disagreement.
- Albedo: PVsyst defaults (0.20) vs measured (0.15–0.40 site-dependent) is a known finance-vs-physics gap.

---

## 3. Open research questions (white-space)

1. **Sub-hourly forecasting under partly-cloudy / cumulus regimes.** Sky-imager + NWP fusion has not converged; sub-15-min RMSE remains 15–30 % of clear-sky GHI.
2. **Bifacial yield under realistic non-ideal ground (vegetation, gravel patches, dust, snow patches).** bifacial_radiance assumes uniform albedo; field validation suggests 2–4 % systematic error on heterogeneous ground.
3. **Rooftop / BIPV thermal modeling under constrained airflow.** Faiman/SAPM derived from open-rack data; rooftop with low standoff can run 10–15 °C hotter than predicted. No widely-validated rooftop-specific model.
4. **Hail damage probability vs module design (glass thickness, tempered vs heat-strengthened, cell technology).** Severe-hail underwriting is currently actuarial, not physics. NREL/Sandia hail testing initiative (Moriarty, Burnham) is active — UNVERIFIED-LEAD recent papers.
5. **Soiling characterization in humid/temperate regions** including biological soiling (pollen, algae, bird droppings). Current literature is desert-biased.
6. **Snow soiling losses + sliding behavior** on bifacial trackers. Marion/Ryberg NREL pre-2020 canonical; tracker-specific snow shedding underspecified.
7. **Module-level mismatch under partial shading** with module-level power electronics (MLPE) — combinatorial validation gap.
8. **Spectral effects under wildfire smoke / aerosol-loaded skies.** 2020–2023 western-US events showed 10–30 % anomalous yield deviations not captured by current spectral models. UNVERIFIED-LEAD on peer-reviewed papers; Smith et al. 2023 candidate.
9. **Long-term degradation of newer cell architectures** (TOPCon, HJT, perovskite tandem) — field data <5 yrs; Jordan 2022 update is the leading edge.

---

## 4. Datasets / public data resources

| Dataset | Coverage | Resolution | Access | Notes |
|---|---|---|---|---|
| NSRDB v3/v4 | CONUS, Americas, India, parts of Asia/Africa | 4 km spatial, 30-min temporal, 1998–~2022 | free via NREL HSDS / API key | citation: NSRDB DOI 10.7799/1183814 UNVERIFIED-LEAD exact DOI |
| SURFRAD | 7 US sites | 1-min, ground-truth GHI/DNI/DHI | free, NOAA GMD | ground-truth gold standard CONUS |
| BSRN (Baseline Surface Radiation Network) | ~70 global sites | 1-min | free registration, WRMC Bremen | global ground truth |
| ERA5 reanalysis | global | ~31 km, hourly, 1940–present | free Copernicus CDS | bias-corrected against ground stations for solar work |
| Solcast | global | 1–5 km, 5-min | commercial, free tier limited | proprietary satellite-derived |
| NREL PVDAQ | ~100 US sites field yield | 1–15 min, multi-year | free via OEDI | DC/AC/met data, ground truth for model validation |
| DOE OEDI | aggregator | varies | free | hosts PVDAQ + others |
| PV GIS (EU JRC) | Europe, Africa, Asia | ~5 km, hourly | free | European canonical |
| CAMS Radiation Service | global | hourly, 4 km | free registration Copernicus | aerosol-aware |
| Sandia Regional Test Centers | 5 US sites | high-cadence module data | restricted/by-request | calibrated reference modules |

---

## 5. Modeling stack + instrumentation state (2024–2026)

### Open-source
- **pvlib-python** v0.10/0.11 era (verify current). Active dev: Holmgren, Mikofski, Anderson, Hansen, Ayala Pelaez. Includes IEC 61853 module model, multiple transposition models, SAPM/CEC/PVWatts DC models, single-axis tracker w/ backtracking + slope-aware, bifacial via bifacial_radiance bridge. GitHub: pvlib/pvlib-python.
- **bifacial_radiance** (NREL, Deline + Ayala Pelaez). Ray-traced rear-side irradiance via Radiance. Active.
- **rdtools** (NREL/SunPower) — degradation + soiling analysis from field data. DOI for canonical paper: 10.1109/JPHOTOV.2018.2840140 (Jordan et al.) — UNVERIFIED-LEAD.
- **PVMismatch** (SunPower OSS) — cell-level shading mismatch.

### Free closed-source
- **SAM (System Advisor Model)**, NREL. v2024.x. Detailed-Photovoltaic + PVWatts paths. Used widely in finance + research. Free, source available.

### Commercial
- **PVsyst** — utility-scale standard for bankable yield reports. v7.x. Closed-source; validation white papers self-published.
- **PlantPredict** (formerly First Solar, now Terabase) — utility-scale.
- **Helioscope** (Folsom Labs / Aurora) — rooftop/C&I.
- **PVCase / RatedPower** — siting + layout integrated tools, growing 2023–2026.

### Sky-imager / short-horizon
- TSI (Total Sky Imager), Yankee Environmental — legacy.
- ASI-16 (Schreder/CSPS) and custom DSLR + fisheye networks at NREL, DLR, UCSD.
- DLR all-sky imager network (10+ sites) — Nouri et al. publications.
- Open-source: pysolar-imager, skymage UNVERIFIED-LEAD whether maintained.

### Soiling station design trends
- **DustIQ** (Kipp & Zonen / OTT HydroMet) — optical soiling ratio.
- **Mars Soiling Sensor** (Atonometrics) — dual-module reference vs soiled.
- Trends: lower-cost networked deployments (Micheli + others advocating regional soiling maps); pairing with PM2.5 / PM10 from EPA/co-located met.

### Instrumentation reference
- IEC 61724-1 Class A monitoring stations: pyranometer (secondary standard, Kipp CMP10/11 or Hukseflux SR25), DNI via pyrheliometer (CHP1) on tracker, met (T, RH, wind, BP), back-of-module T. Reference cells (IEC 60904-2) increasingly used alongside thermopile for spectral-aware reference.

---

## Notes on verification burden

High-confidence (canonical, widely cited): pvlib-JOSS DOI, Jordan-Kurtz degradation, NSRDB Sengupta 2018, Ilse 2019 *Joule*. **Verify before citing in pre-reg.**

UNVERIFIED-LEAD items needing user check: all post-2022 DOIs above (knowledge-cutoff drift), NREL report IDs, Micheli affiliation, Jordan 2022 degradation update, wildfire-smoke spectral papers, recent sky-imager benchmarks. Several venues (PVsyst, commercial soiling sensors) publish on company sites not indexed in Crossref — check vendor white papers directly.

**White-space candidates** for a new lab, ranked by tractability × novelty: (1) humid/temperate soiling characterization with networked low-cost sensors, (2) rooftop/BIPV thermal modeling with constrained airflow, (3) bifacial under heterogeneous ground, (4) wildfire-smoke spectral effects. Hail and sub-hourly forecasting are crowded with NREL/Sandia incumbents.
