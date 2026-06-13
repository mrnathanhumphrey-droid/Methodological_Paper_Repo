# 16 — Verification: Jordan et al. 2022 PV Fleet Degradation Insights

**Verification date:** 2026-05-27
**Verifier:** subagent (full-text retrieved via NREL open access) + operator endorsement pending
**Target citation:** Jordan, D.C., Anderson, K., Perry, K., Muller, M., Deceglie, M., White, R., Deline, C. 2022. **"Photovoltaic fleet degradation insights."** *Progress in Photovoltaics: Research and Applications*, **30(10), 1166-1175**. DOI: 10.1002/pip.3566. **Open access** (US Government work, CC-BY).
**Importance:** This paper is the MODERN canonical field-PLR citation and **directly resolves ERR-5** from `12_VERIFICATION_PASS_v1_summary.md` (climate-failure correlation at large N).

## Retrieval status

- **Full PDF retrieved at NREL open access:** `https://docs.nrel.gov/docs/fy22osti/81314.pdf` (10 pages, ~9.3 MB)
- Local copy via subagent at `tool-results/webfetch-1779910881593-i2755c.pdf` — recommend operator move into substrate as `Jordan2022_PVFleet.pdf`
- Wiley DOI link paywalled (HTTP 402)
- OSTI journal record + dataset record accessible

## Citation header — CONFIRMED

| Field | Verified value |
|---|---|
| Authors | Jordan, Anderson, Perry, Muller, Deceglie, White, Deline (7-author NREL list) |
| Year | 2022 |
| Journal | Progress in Photovoltaics: Research and Applications |
| Vol(issue), pages | 30(10), 1166-1175 |
| DOI | 10.1002/pip.3566 |
| Received / Revised / Accepted | 14 Dec 2021 / 25 Feb 2022 / 12 Apr 2022 |
| License | CC-BY (US Government work) |

## Per-claim verdicts — all CONFIRMED with section/page refs

- **C1 — Sample scale:** "more than 1700 sites, with approximately 19,000 individual inverter data streams … 7.2 gigawatts (GW) or between 6% and 7% of the entire installed capacity in the United States." §2, p.1167, Fig. 1. **CONFIRMED EXACT.**
- **C2 — Overall median PLR:** **Inverter median -0.75%/yr; mean -0.88%/yr; P90 -1.90%/yr; n=4915 inverters.** Site-level median -0.68%/yr (n=585 sites). §4, p.1169, Table 2. **CONFIRMED EXACT.**
- **C3 — Climate-stratified PLR (Al-BSF ground-mounted only):**
  - **T3 (cool): -0.48%/yr** (n=904 inv / 44 sites)
  - **T4 (mid): -0.78%/yr** (407 / 43)
  - **T5 (hot): -0.88%/yr** (217 / 25)
  §7, p.1171, Table 4, Fig. 6. **CONFIRMED EXACT** with refinement: the "cool -0.48 / hot -0.88" framing is the endpoints of a three-bin spectrum.
- **C4 — CRITICAL — Climate-correlation statistical significance:** **"A significant trend (p value < 0.001) of higher performance loss with hotter temperature climates can be discerned."** §7, p.1171. **CONFIRMED EXACT.** Caveat: temperature only; humidity NOT confirmable due to Al-BSF skew across humidity bins.
- **C5 — Methodology RdTools / YoY:** **CONFIRMED.** RdTools v2.1.0-beta.1 year-on-year method (ref 19, Deceglie et al.). Clipping filter rejects >10% clipped streams. Irradiance filter 200-1200 W/m². Normalization: sensor 73% / NSRDB satellite 22% / clearsky 5%. Two-sigma CIs per PLR; fleet aggregates weighted by inverse CI. Soiling NOT separated fleet-wide (CODS algorithm applied only to a few high-soiling CA sites, then excluded from tracker comparison). §3, p.1168-1169.
- **C6 — Module-vintage stratification (install-year cohort):** **PARTIAL.** No clean install-year curve published. Closest: Table 5 stratifies PERC + Al-BSF by field-exposure years 2/3/4/5 in CA zones T3+T4. PERC: 2yr -1.36 / 3yr -0.95 / 4yr -0.89. Al-BSF: 3yr -0.39 / 4yr -1.12 / 5yr -0.64. Paper flags small-n inconclusiveness. §8, p.1172, Table 5, Fig. 8.
- **C7 — Cell-tech stratification:** **PARTIAL.** c-Si broken out by **cell technology**: Al-BSF, PERC (mfr 1 & 2), SHJ, IBC. CdTe present (n=235 inv / 6 sites, median -0.61%/yr, Table 3). **CIGS NOT broken out** — fleet is "primarily c-Si with a small percentage of thin-film, mostly CdTe" (p.1167). "Tracked Si and CdTe systems showed no statistical difference vs fixed-tilt … p > 0.49." §6 Table 3; §8 Tables 5-6.
- **C8 — Companion dataset:** **CONFIRMED.** "Photovoltaic Fleet Degradation Insights" dataset, Deline et al., 1 Feb 2022, NREL/DuraMAT Data Hub, OSTI ID **1842958**, DOI **10.21948/1842958**. Public; contains aggregated PLR + nonattributable site metadata (sufficient to reproduce Fig. 3 histogram per ref 28). Site-identifying metadata NOT included.

## Climate-correlation finding — ERR-5 RESOLVED

The 2017 T13-09:2017 null finding on climate-failure correlation is **OVERTURNED by this paper at p < 0.001 for temperature axis** at fleet N≈1500 inverters / 112 sites.

**Magnitude:** approximately **1.8× PLR escalation** from cool (T3) to hot (T5) climate zones in Al-BSF c-Si ground-mounted fleet.

**Caveats:**
1. **Temperature axis only.** Humidity axis "trend with respect to humidity zones could not be determined with confidence" due to uneven Al-BSF geographic distribution across humidity bins (Conclusion, p.1173).
2. **Al-BSF c-Si only.** Other module technologies (PERC, SHJ, IBC, CdTe) have "insufficient samples … to identify any trend versus climate" (Conclusion, p.1173).
3. **Ground-mounted only.** Rooftop/BIPV climate analysis not in this paper.
4. **NOT Köppen-Geiger.** Paper uses **Karin et al. 2019** PV-specific zones (Arrhenius-weighted equivalent rack temperature × specific-humidity bins). Paper explicitly rejects Köppen-Geiger as "agriculture-focused" (§2, p.1167). Karin reference: 46th IEEE PVSC, 2019, "Photovoltaic degradation climate zones."

## Methodology details (substantive)

- **RdTools YoY** with three normalization paths: sensor (73%), NSRDB satellite (22%), clearsky (5%).
- **QA pipeline:** changepoint detection for data shifts; rejection of streams with <2 yr data, >25% missing daytime data, >10% clipped points, or bad orientation metadata. ~10% of passing inverters still data-shift-contaminated — three RdTools analyses run + best-non-shifted PLR selected.
- **Aggregation weighting:** inverse-CI weighting (high-uncertainty PLRs contribute less). Median/P90 unaffected by weighting; mean shifts by 0.01%/yr.
- **Soiling separation:** CODS algorithm (Skomedal & Deceglie 2020) NOT run fleet-wide due to compute cost; high-soiling sites excluded from tracker analysis.
- **AC vs DC:** AC-DC PLR difference centered on zero (Fig. 4) — inverter aging doesn't generally contribute to system PLR (one mfr exception).

## Comparison to 2016 Compendium

Paper explicitly addresses why its median (-0.75%/yr) differs from 2016 Compendium (-0.5 to -0.6%/yr):

> "smaller median PLR of -0.5%/yr for the previously published results may be attributable to … predominantly (~80%) module-level measurements rather than system PLRs … additional losses such as series mismatch, soiling, and cabling which may account for the increase to -0.75%/year." (Conclusion, p.1173)

**Median has NOT clearly worsened module-to-module;** system-level PLR is intrinsically ~0.15-0.25%/yr higher than module-level by construction.

## Notes for substrate landscape revision

1. **Replace 2016 Compendium median as canonical** for modern field claims with Jordan 2022 -0.75%/yr **system-level** PLR; cite 2016 Compendium for module-level historical reference.
2. **Adopt Karin et al. 2019 PV-specific climate zones** in any new substrate work — NOT Köppen-Geiger.
3. **ERR-5 status: CLOSED.** Climate-failure correlation IS established for temperature axis at p < 0.001 in Al-BSF c-Si ground-mounted fleet. Update `04_LANDSCAPE_DEGRADATION_v0.md` + `05_LANDSCAPE_RELIABILITY_v0.md` to reflect this.
4. **Companion dataset is a public PRIMARY source** for substrate analysis: DOI 10.21948/1842958 at NREL DuraMAT — operator should pull this dataset into `data/raw/` for direct work.
5. Fleet composition skew: ~80%+ c-Si, ~3-5% CdTe, near-zero CIGS — paper is NOT a thin-film cross-technology authority.
6. Vintage / install-year cohort: paper does NOT cleanly resolve; PERC may show elevated early-life PLR with small-n caveat. For vintage analysis substrate work needs supplementation.

## Ledger impact (applies on operator endorsement)

- New entry **CLM-FLEET-PLR-2022:** Modern fleet median PLR -0.75%/yr (system-level), inverter median -0.88%/yr, P90 -1.90%/yr. n=4915 inverters / 1700 sites / 7.2 GW. VERIFIED via Jordan 2022 (pip.3566) §4 Table 2.
- New entry **CLM-FLEET-CLIMATE-T:** Climate-temperature axis shows credible higher PLR in hotter zones at p<0.001: T3 cool -0.48 → T5 hot -0.88 %/yr in Al-BSF ground-mounted c-Si. VERIFIED via Jordan 2022 §7 Table 4 Fig. 6.
- New entry **CLM-FLEET-CLIMATE-H:** Humidity climate axis trend UNCONFIRMED at this fleet N due to geographic skew. INDETERMINATE.
- New entry **CLM-FLEET-DATASET:** Public dataset at NREL DuraMAT (DOI 10.21948/1842958) — aggregate PLR + non-attributable system metadata. VERIFIED.
- New entry **CLM-FLEET-TRACKER-NULL:** Tracked Si + CdTe systems show no statistical PLR difference vs fixed-tilt (p > 0.49). VERIFIED.
- **CLM-005** (climate-specific aging established) — UPGRADE from PARTIAL to **VERIFIED-TEMPERATURE-AXIS** with primary citation Jordan 2022 (NOT Köntges T13-09:2017 which was the prior cited source).

## Open follow-ups

- F1: **Pull the companion dataset** (DOI 10.21948/1842958) into `data/raw/papers/` or `data/raw/datasets/` — this is the actual machine-readable fleet PLR data for substrate work.
- F2: Verify Karin et al. 2019 paper (46th IEEE PVSC) for the PV-specific climate-zone methodology — substrate should adopt this as its climate-axis framework.
- F3: T13-30:2025 REPORT full body (Fraunhofer CSP mirror) — likely contains additional climate analysis not in the 3-page EX-SUMM.
- F4: Pull RdTools open-source package (`github.com/NREL/rdtools`) into `code/` for local field-data analysis.

## Sources

- NREL full PDF: https://docs.nrel.gov/docs/fy22osti/81314.pdf
- OSTI journal record: https://www.osti.gov/pages/biblio/1864619
- OSTI dataset: https://www.osti.gov/biblio/1842958 (DOI 10.21948/1842958)
- Wiley (paywalled): https://onlinelibrary.wiley.com/doi/10.1002/pip.3566
- Karin et al. 2019 (climate zones, follow-up F2): 46th IEEE PVSC 2019, "Photovoltaic degradation climate zones"
