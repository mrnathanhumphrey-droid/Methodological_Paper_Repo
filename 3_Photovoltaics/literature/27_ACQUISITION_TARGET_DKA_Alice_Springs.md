# 27 — Data Acquisition Target: DKA Solar Centre (Alice Springs)

**Status:** TARGET IDENTIFIED, automated pull BLOCKED → operator-pull required.
**Date:** 2026-05-28
**Purpose:** Unblock the probe PVDAQ structurally could not support (Probe 2/2b): a **technology-controlled degradation comparison at a single arid site** — vary cell technology, hold climate fixed (the inverse of Probe 2's failed vary-climate-hold-technology).

---

## 1. Why DKA is the right source

| Property | DKA Alice Springs | Why it matters |
|---|---|---|
| Site | Single site, Alice Springs NT (arid, hot) | Holds climate fixed → isolates technology effect. Also = the **arid (H1)** regime PVDAQ entirely lacked (Probe 3 §3). |
| Technologies | 40+ installations: mono-Si, poly-Si, HIT/SHJ, CdTe, CIGS, a-Si, CPV | Direct technology-controlled comparison — the design Probe 2b proved you need (σ_within ≤ ~1 %/yr via homogeneity). |
| On-site weather | Global/POA irradiance, module temp, ambient, wind, humidity (Class A from 2019) | **Measured POA → clean PI** (no NSRDB-modeling noise; the 32% measurement floor that killed Probe 3 soiling). |
| Record length | 15+ years (2008–present) | Long degradation baselines; some arrays from 2008–2010. |
| License | Open-access, free for research | No confidentiality gate (unlike DuraMAT). |

This unblocks **Probe 4 (technology-controlled degradation)** AND a **real soiling probe** (arid + measured POA — both things PVDAQ lacked).

---

## 2. Automated-pull BLOCKED (2026-05-28 attempts)

DKA download portal (`dkasolarcentre.com.au/download?location=alice-springs`) is a JavaScript/Craft-CMS app with an **async server-side CSV export** ("downloads may take a few minutes"). Attempted and failed:
- WebFetch of download page → exceeds 10 MB content limit (13.6 MB JS app).
- `notes-on-the-data` page → no documented API/endpoint/parameters.
- GitHub catalog (Charlie5DH/Solar-Power-Datasets) + Kaggle/Zenodo mirror search → no clean mirror found.
- GraphQL / `/api` / `/graphql` POST probes → 404 (not exposed).
- System list + sourceIds load dynamically (not in static HTML), so no endpoint reconstruction.

Only programmatic path would be a headless browser (not available in this environment). Bulk datasets also available by emailing `info@dkasolarcentre.com.au`.

→ **Operator-pull** (the established pattern in this substrate — cf. paper PDFs, NSRDB key).

---

## 3. Operator-pull instructions (what to download)

At `https://dkasolarcentre.com.au/download?location=alice-springs`:

**Systems:** the longest-running arrays spanning the main technologies. Prioritize 2008–2010-vintage systems (longest degradation record), aiming for ≥3 per technology where available:
- mono-Si (e.g. Trina, SunPower)
- poly-Si / multi-Si (e.g. Kyocera, BP Solar)
- HIT / SHJ (Sanyo/Panasonic)
- CdTe (Calyxo / First Solar)
- thin-film a-Si / CIGS if present

**Date range:** full history (earliest available → present).

**Interval:** **Daily** if offered (smallest, sufficient for degradation/PLR). Else hourly. (5-min native is fine but large.)

**Fields (per system):** Active Power (or Active Energy), Global Horizontal Radiation AND/OR tilted/POA irradiance, Module Temperature, Ambient Temperature, Wind Speed.

**Also grab:** the system metadata table (technology, rating kW, # panels, install date, tilt/azimuth per array) — visible on the portal or the array pages.

**Drop location:** `D:/Renewables/Solar/data/raw/dka/` (gitignored under `Solar/data/*`). One CSV per system is ideal; filenames containing the technology + array name help.

---

## 4. Probe this unblocks (Probe 4 — sketch, NOT yet pre-registered)

**Question:** At a single arid site (climate fixed), do cell technologies degrade at different rates, and does RMD-SRC partition the per-technology PLR trajectories cleanly?

**ℙ₀:** cell-technology × array-vintage × (tilt/azimuth). Single site → no climate axis (that's the point — it's the control).

**Observable:** measured-POA-normalized performance index → rdtools YoY PLR + bootstrap, per array.

**Hypotheses (draft):** technology explains PLR variance (η² test); HIT/SHJ + CdTe vs c-Si ordering per literature; thin-film higher year-1 then stabilize. Soiling sub-probe now feasible (arid + measured POA).

**Why it complements Probe 2:** Probe 2 varied climate at ~fixed (unknown) technology and found heterogeneity buried the signal. Probe 4 varies technology at fixed climate with measured POA → σ_within should be ~1 %/yr (Probe 2b's homogeneity target), making effects detectable at DKA's modest N.

---

## 4b. DKA Alice Springs system catalog (operator-provided 2026-05-28) + Probe 4 selection

Full active-system list (each ~200–300 MB CSV, 5-min interval + on-site weather, full history). **Files are 5-min native — no daily option; aggregate to daily in processing.**

**★ CORE technology-controlled set (FIXED mount, 2008–2011 vintage — isolates technology, holds mounting+vintage):**

| # | Brand | kW | Technology | Mount | Year |
|---|---|---|---|---|---|
| 10 | SunPower | 5.8 | mono-Si | Fixed | 2009 |
| 12 | BP Solar | 5.1 | mono-Si | Fixed | 2008 |
| 13 | Trina | 5.3 | mono-Si | Fixed | 2009 |
| 18 | SunPower | 5.2 | mono-Si | Fixed | 2011 |
| 19 | Sungrid | 5.0 | mono-Si | Fixed | 2010 |
| 3 | BP Solar | 5.0 | poly-Si | Fixed (roof) | 2008 |
| 11 | BP Solar | 5.0 | poly-Si | Fixed | 2008 |
| 14 | Kyocera | 5.4 | poly-Si | Fixed | 2008 |
| 20 | Sungrid | 5.0 | poly-Si | Fixed | 2010 |
| 21 | Evergreen | 4.9 | poly-Si | Fixed | 2010 |
| 7 | First Solar | 7.0 | CdTe | Fixed | 2008 |
| 23 | Calyxo | 5.4 | CdTe | Fixed | 2010 |
| 8 | Kaneka | 6.0 | a-Si | Fixed | 2008 |
| 17 | Sanyo | 6.3 | HIT | Fixed | 2010 |

→ mono-Si ×5, poly-Si ×5 (powered contrast), CdTe ×2, a-Si ×1, HIT ×1. ~3.8 GB.

**Secondary (sub-studies, optional):**
- **Orientation control:** 16A/16B/16C/16D — *same* BP poly-Si 2008 at North/Flat/East/West → vary azimuth/tilt, hold tech+vintage. Clean orientation-effect test.
- **CIGS:** 9A Solibro 2017 (newer); discontinued CIGS (Solco 2009, Hanergy 2010) if long-record CIGS wanted.
- **CPV:** 22 SolFocus 16.8kW dual-track 2010 (exotic; separate handling).
- **Tracking confound study:** 1A/1B/2 (dual-track mono-Si) vs fixed mono-Si → mounting effect.
- **Vintage/poly replication:** 24–37 (2012–2017 poly-Si fixed) for poly-Si vintage + newer-cohort comparison.

**Skip:** #0 (aggregate of all sites — not per-system).

**Probe 4 ℙ₀ (revised with real catalog):** cell-technology {mono-Si, poly-Si, CdTe, a-Si, HIT} × mount {Fixed} × vintage-band {2008-09, 2010-11}. Single site (Alice Springs) = climate fixed. mono/poly have n≥5 → the two-class contrast is the powered headline; thin-film/HIT are directional.

## 5. REQUIRED citation + attribution (DKA use terms)

DKA Solar Centre data is open-access but carries a **mandatory citation requirement**. Any substrate result memo, pre-reg, or publication using DKA data **MUST** include:

**General citation:**
> Desert Knowledge Australia Centre. dd/mm/yyyy. Download Data. Alice Springs. http://dkasolarcentre.com.au/download, date accessed: dd/mm/yyyy.

**Specific (per-array) citation:**
> Desert Knowledge Australia Centre. dd/mm/yyyy. Download Data: Array ## Brand Name. Alice Springs. http://dkasolarcentre.com.au/download, date accessed: dd/mm/yyyy.

(Fill `dd/mm/yyyy` with the data-publication date shown on the portal and the access date; list each Array ## + Brand actually used in the specific form.)

**Courtesy notification:** DKA requests being notified of R&D outputs using their data — email `info@dkasolarcentre.com.au` with any publication/initiative.

**Substrate rule:** Probe 4's pre-reg and result memos must carry the citation block above with the actual array list + access date recorded at pull time. Treat this as a hard requirement (same standing as the meta-pre-reg primary-source discipline) — log the array IDs + access date in `data/raw/dka/` alongside the CSVs so the specific citations are reproducible.

---

**END — acquisition target. Resume: operator pulls DKA CSVs → `data/raw/dka/` → pre-reg + build Probe 4. Citation block (§5) is MANDATORY in all DKA-derived outputs.**
