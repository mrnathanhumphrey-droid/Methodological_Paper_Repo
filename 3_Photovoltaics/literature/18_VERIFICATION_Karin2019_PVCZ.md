# 18 — Verification: Karin et al. 2019 — Photovoltaic Degradation Climate Zones (PVCZ)

**Verification date:** 2026-05-27
**Verifier:** subagent + operator endorsement pending
**Target citation:** Karin, T., Jones, C.B., Jain, A. 2019. **"Photovoltaic Degradation Climate Zones."** Proceedings of the 46th IEEE Photovoltaic Specialists Conference (PVSC-46), Chicago IL, June 16-21, 2019. DOI: **10.1109/PVSC40753.2019.8980831**. Affiliations: Karin + Jain at LBNL; Jones at Sandia (inferred from PV reliability group).

## Why this paper matters

Jordan et al. 2022 PV Fleet paper uses Karin's PVCZ scheme as its climate axis (T3/T4/T5 in Al-BSF analysis). The substrate is adopting this framework — needs verification of methodology + zone definitions + open-source software access.

## Retrieval status

- **Citation header confirmed** via Semantic Scholar (DOI-keyed metadata).
- **IEEE Xplore HTML blocked** (HTTP 418 anti-bot).
- **Karin 2019 PDF retrieved locally** at `D:/Renewables/Solar/data/raw/papers/Karin2019_PVSC_ClimateZones.pdf` (5.2 MB), source: `github.com/toddkarin/pvcz` repo. PDF text-extraction failed in subagent session; needs local pdfplumber read for page-level threshold tables.
- **GitHub repo retrieved:** `github.com/toddkarin/pvcz` (MIT-licensed Python package + companion data).
- **Page range NOT confirmed** (IEEE Xplore blocked, PDF cover not extracted). Flag UNVERIFIED — local PDF read can close.

## Citation header — CONFIRMED (page range UNVERIFIED)

| Field | Verified value |
|---|---|
| Title | "Photovoltaic Degradation Climate Zones" (no subtitle) |
| Authors | Todd Karin (LBNL); C. Birk Jones (Sandia); Anubhav Jain (LBNL). 3-author list. |
| Year | 2019 |
| Conference | IEEE PVSC-46 (Chicago, June 16-21, 2019) |
| DOI | 10.1109/PVSC40753.2019.8980831 |
| Page range | UNVERIFIED |

## Per-claim verdicts

### C1 — PV-specific zones distinct from Köppen-Geiger — **CONFIRMED**

Verbatim from abstract: *"Most typically the Köppen-Geiger classification scheme is used... Köppen-Geiger uses temperature and rainfall to develop zones relevant for botany and lacks the ability to distinguish locations based on climate stressors more relevant to PV degradation."*

Paper introduces **PhotoVoltaic Climate Zones (PVCZ-2019 or PVCZ)**.

### C2 — Methodology: Arrhenius-weighted equivalent rack temperature + specific humidity — **CONFIRMED**

From `pvcz` package README + `main.py` source:
- `T_equiv_rack_1p1eV`: Arrhenius-weighted module equivalent temperature, open-rack polymer-back temperature model, **activation energy 1.1 eV default**, in °C.
- `specific_humidity_mean` (g/kg).
- `T_velocity_rack`: thermal cycling.
- `equiv_temp_in_C()` implements: `T_equiv = -Ea/kB/ln(mean(exp(-Ea/(kB·T))))` — standard Arrhenius reduction.

### C3 — Zone labels — **PARTIALLY REFUTED from my prior framing**

Prior framing (mine): "T3 cool / T4 mid / T5 hot — 5-zone scheme." **CORRECT scheme is much finer:**
- **Temperature: T1-T10 (10 bins)**
- **Humidity: H1-H5 (5 bins)**
- **Wind speed: W1-W5 (5 bins)**
- **Combined PVCZ: 0-49 (10×5 = 50 T×H zones)**, labeled `Tx:Hy` (e.g., `T5:H2`).

Jordan 2022 talked about T3/T4/T5 because **that's where California PERC systems landed**, not because the scheme stops at T5. Substrate framing must adopt the full T1-T10 × H1-H5 × W1-W5 taxonomy.

### C4 — Threshold numbers — **STILL UNVERIFIED**

The actual °C and g/kg cutoffs for T1...T10 + H1...H5 + W1...W5 zones are in:
- `PVCZ-2019_ver0p2_zones.npz` binary (in repo, needs Python load to inspect)
- Tables in the Karin 2019 PDF (text extraction failed in subagent session; need local pdfplumber read)

**Substrate adoption requires loading the .npz file OR reading the PDF tables locally.** Recommendation:

```python
# Local extraction (after pip install pvcz):
import pvcz
d = pvcz.load_pvcz()  # returns DataFrame with all stressors + zones
# or directly:
import numpy as np
zones = np.load('PVCZ-2019_ver0p2_zones.npz', allow_pickle=True)
print({k: zones[k] for k in zones.files})
```

### C5 — Geographic scope — **CONFIRMED (global, not US-only)**

Per `pvcz` README: data is calculated from **GLDAS** (Global Land Data Assimilation Service) at **0.25° resolution across the world**. CSV `PVCZ-2019_ver0p2_world_PV_climate_stressors_and_zones.csv` ships in the repo. CONUS mapping is a subset by lat/lon.

### C6 — Open-source reproducibility — **CONFIRMED**

- Package: `pvcz` on PyPI + GitHub (`github.com/toddkarin/pvcz`)
- License: MIT
- Install: `pip install pvcz`
- Author: Todd Karin
- README points to PDF for full methodology
- Interoperates with pvlib but not in pvlib core

### C7 — Köppen-Geiger benchmarking — **CONFIRMED (conceptual)**

Paper motivation IS the K-G critique. Dataset retains `KG_zone` column for side-by-side comparison. Quantitative head-to-head benchmark within the paper itself: UNVERIFIED (need local PDF read).

### C8 — PV-system validation — **NOT IN THIS PAPER**

Abstract describes zone construction from GLDAS climate reanalysis (NOT a PV-system fleet). **Validation of zones against measured degradation is in Jordan et al. 2022 downstream**, not in Karin 2019 itself. Cite both as a pair when claiming the zones are field-validated.

## Software / data availability summary

| Resource | URL | Notes |
|---|---|---|
| Code (Python) | github.com/toddkarin/pvcz | MIT, pip-installable, `pip install pvcz` |
| Global PVCZ CSV | In-repo: `pvcz/PVCZ-2019_ver0p2_world_PV_climate_stressors_and_zones.csv` | 0.25° GLDAS grid |
| Zone thresholds (.npz) | In-repo: `pvcz/PVCZ-2019_ver0p2_zones.npz` | Binary; needs Python load |
| Methodology PDF | In-repo: `Karin2019 - Photovoltaic Degradation Climate Zones - PVSC.pdf` | 5.2 MB, also at `D:/Renewables/Solar/data/raw/papers/Karin2019_PVSC_ClimateZones.pdf` |

## Adoption / citation count

- **Semantic Scholar citation count: 19** (`influentialCitationCount: 0`) — modest, niche-but-foundational conference paper.
- **Adopted by Jordan et al. 2022 PIP** (DOI 10.1002/pip.3566) for California PERC fleet climate stratification.
- **No evidence of IEC / IEA-PVPS / NREL standards-body normative codification.** De-facto research convention propagated through LBNL/NREL/Sandia reliability community via Jordan 2022 and downstream.

## Notes for substrate landscape revision

1. **Update substrate's climate-axis framing** from "5-zone PVCZ" to **"T1-T10 × H1-H5 × W1-W5"** combined-zone scheme. Jordan 2022's California analysis is a subset.
2. **Zone-threshold numbers (literal °C and g/kg) are NOT yet in this memo.** Before substrate publishes any zone boundary table, do a local extraction (load .npz or read PDF tables).
3. **Activation energy default 1.1 eV** is a load-bearing methodological choice (typical for module-level Arrhenius; some literature uses 0.7-0.9 eV for adhesion/encapsulant). Substrate should disclose which E_a it adopts if it deviates.
4. **Validation pairing:** when substrate claims the zones are field-validated, cite both Karin 2019 (zone construction) AND Jordan 2022 (fleet PLR validation) — Karin 2019 alone does NOT validate against measured degradation; that lives downstream.
5. **Software:** install `pvcz` Python package for local zone lookup; it interoperates cleanly with pvlib.

## Ledger impact (applies on operator endorsement)

New ledger entries:

- **CLM-PVCZ-SCHEME:** Karin 2019 PVCZ is T1-T10 (Arrhenius-weighted equivalent rack temperature) × H1-H5 (specific humidity) × W1-W5 (wind), combined `Tx:Hy` 50-zone scheme. VERIFIED via pvcz package README + Semantic Scholar abstract.
- **CLM-PVCZ-ACTIVATION:** Default activation energy E_a = 1.1 eV for module-level Arrhenius reduction. VERIFIED via pvcz package `main.py`.
- **CLM-PVCZ-DATA:** Global PVCZ at 0.25° GLDAS resolution; shipped as CSV in `pvcz` repo. VERIFIED.
- **CLM-PVCZ-OSS:** `pvcz` Python package MIT-licensed, pip-installable. VERIFIED.
- **CLM-PVCZ-VALIDATION:** Karin 2019 does NOT validate zones against measured PV degradation; validation in Jordan 2022. VERIFIED (negative claim).
- **CLM-PVCZ-CITATIONS:** Modest citation count (~19) as of 2026-05-27. Not standards-body codified. VERIFIED via Semantic Scholar.

## Open follow-ups

- F1: **Read Karin 2019 PDF tables locally** via pdfplumber to extract T1-T10 + H1-H5 + W1-W5 threshold numbers verbatim.
- F2: **Load `PVCZ-2019_ver0p2_zones.npz` locally** (after `pip install pvcz`) to dump thresholds programmatically.
- F3: Verify IEEE Xplore page range for citation header completeness.

## Sources

- Semantic Scholar: https://www.semanticscholar.org/paper/Photovoltaic-Degradation-Climate-Zones-Karin-Jones/8e825b35a56cdd2588e72f58e5c74d15f10dd4c3
- IEEE Xplore (paywalled): https://ieeexplore.ieee.org/document/8980831/
- GitHub: https://github.com/toddkarin/pvcz
- PyPI: https://pypi.org/project/pvcz/
- Local PDF: `D:/Renewables/Solar/data/raw/papers/Karin2019_PVSC_ClimateZones.pdf`
