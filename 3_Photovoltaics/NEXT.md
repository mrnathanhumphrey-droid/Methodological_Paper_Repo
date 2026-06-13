# Next Session — Pickup Pointer (Solar Substrate, pre-compact 2026-05-30)

**Repo HEAD target:** commit pending post-synthesis (will be the lock SHA) on `main` at github.com/mrnathanhumphrey-droid/Renewables.
**Last session ended:** Substrate synthesis (memo 30) written. **Operator direction:** "synth, prepare to compact. we do verification after compact."

---

## 0. POST-COMPACT FIRST PRIORITY — Verification of substrate-novel findings

Per operator direction, the next session runs **external-literature verification** of the substrate-novel findings before any further probes. Targets (memo 30 §4):

| # | Finding to verify | Source | Verification target |
|---|---|---|---|
| **V1** | Wet-season DEPOSITION rate > dry-season at Alice Springs ("muddy soiling") | memo 29 §6c, CLM-093 | Atacama / Sahara / Mojave / Saudi soiling lit on rain "cementation"; Ilse 2019 discussion; Figgis Qatar; DKA-specific Australian-soiling studies |
| **V2** | Multi-system synchrony separates natural from operational cleaning | memo 29 §6d, CLM-094/095 | NREL soiling-monitoring papers; rdtools multi-system docs; any prior synchrony decomposition in PV lit |
| **V3** | 2.0× σ_within inflation heterogeneous vs homogeneous (PVDAQ vs Jordan vs DKA) | memo 25 §4b CLM-078; memo 28 §2 CLM-083 | Jordan 2022 / Deceglie 2018 reported within-cohort SDs; cross-fleet variance-decomposition lit |
| **V4** | CdTe-low soiling (3.15% at M7) — n=1 directional | memo 29 §3 CLM-090 | First Solar / CdTe anti-soiling glass-coating literature |

**Pre-reg discipline:** these are VERIFIED-OWN (substrate-internal); external verification will mark them VERIFIED (anchor-supported) or PARTIAL or NOVEL-FRONTIER per meta-pre-reg §4 knowledge-state labels.

---

## 1. Substrate state at lock

| Layer | Status | Doc |
|---|---|---|
| Meta-pre-reg | LOCKED `fc32be4` | `01_METAPREREG_v1.0` |
| Claims ledger | LIVE 96 CLMs (001–096) | `02_CLAIMS_LEDGER.md` |
| Probe 1 TOPCon UVID pre-reg | LOCKED `fc32be4`, blocked on cohort ID | `19_PREREG_v1.0_TOPCon_UVID.md` |
| Probe 2 PVDAQ Fleet PLR pre-reg | LOCKED `165342b`, EXECUTED | `23_PREREG_v1.0_FleetPLR_PVCZ.md` |
| Probe 2 result | DONE | `24_RESULT_v1.0_FleetPLR_PVCZ_RMDSRC.md` |
| Probe 2b detectability | DONE | `25_RESULT_Probe2b_detectability.md` |
| Probe 3 PVDAQ soiling | FEASIBILITY-NULL | `26_RESULT_Probe3_soiling_feasibility_NULL.md` |
| DKA acquisition target | LIVE, operator-pulled 5.4 GB | `27_ACQUISITION_TARGET_DKA_Alice_Springs.md` |
| Probe 4 DKA tech-controlled PLR | DONE | `28_RESULT_Probe4_DKA_AliceSprings.md` |
| Probe 5 + 5b + 5c + 5d + 5e soiling | DONE (4 sub-probes in 1 memo) | `29_RESULT_Probe5_DKA_soiling.md` |
| **Substrate synthesis v1.0** | **DONE** | `30_SYNTHESIS_v1.0.md` |

## 2. End-state numbers (the substrate's main quantitative claims)

- **Fleet PLR magnitudes (3 independent replications):** Jordan 2022 −0.75 / PVDAQ Probe 2 −0.79 / DKA Probe 4 −0.91 %/yr
- **Heterogeneity inflation:** PVDAQ σ_within = **2.0× Jordan**; DKA fixed-mount σ = **0.23 %/yr = 1/8 PVDAQ**
- **Climate-T partition on PVDAQ:** η²=0.019 (refuted-by-underpower, power 0.49 at n=668, would need ~1938)
- **DKA fixed-mount tech ordering:** HIT −0.80 ≤ mono-Si −0.91 ≤ CdTe −0.96 < poly-Si −1.14 %/yr
- **DKA soiling:** median 3.87 %/yr (fixed-mount 3.62) → matches Ilse 2019 global aggregate at the canonical arid site
- **Wet > dry deposition (substrate-novel surprise):** 11/13 systems, ratio 0.74×, p=0.998 opposite-direction
- **Multi-system synchrony:** 4.78× random; K=8 peak rain-aligned 25% (1.65×); K=13 NOT rain-aligned (~3.5 manual cleanings/yr at DKA)
- **Soiling temporal drift:** NULL across 12 years (regime stable, baseline durable)

## 3. Reusable infrastructure

- `code/probe2_plr_pipeline.py` — PVDAQ daily-energy + NSRDB v4 + PVWatts + rdtools YoY
- `code/probe2b_detectability.py` — power-analysis on existing PLR results
- `code/probe4_dka_run.py` — DKA per-array loader + self-normalizing PLR
- `code/probe5_dka_soiling.py` — rdtools SRR on DKA daily PR
- `code/probe5b_rain_validation.py` — rain-event coincidence test
- `code/probe5c_seasonal_soiling.py` — seasonal interval classification
- `code/probe5d_soiling_synchrony.py` — pairwise Jaccard + K-threshold consensus
- `code/probe5e_temporal_drift.py` — per-system + pooled year-vs-rate regression

## 4. Data inventory

- `data/raw/dka/` — operator-pulled DKA CSVs (~5.4 GB, 16 files, gitignored). 12 distinct M-array numbers: M1, M2, M3, M4, M5, M6, M7, M11, M15, M16, M17, M19.
- `data/raw/pvdaq_daily/`, `data/raw/nsrdb/` — caches from Probe 2 (gitignored)
- `data/raw/datasets/PVDAQ_systems_20250729.csv` — committed (small)
- `data/processed/` — small whitelisted result artifacts (probe2/2b/4/5/5b/5c/5d/5e/*.csv|json)
- `Solar/.env` — NREL API key (gitignored)

## 5. Blockers carried forward

- **Probe 1 TOPCon UVID** still blocked on cell-architecture cohort identification (PVDAQ S3 per-system JSON or manufacturer outreach)
- **DuraMAT direct** still network-blocked + confidentiality-gated
- **DKA missing catalog #s** for fuller per-tech replication: 8, 10, 12, 13, 14, 18, 20, 21, 23 (low priority — substrate has enough findings)

## 6. Operational protocol on resume

1. **Open `30_SYNTHESIS_v1.0.md` first** — consolidated map of where the substrate is.
2. **Read `02_CLAIMS_LEDGER.md`** CLM-093/094/095/078/083/090 — substrate-novel claims targeted for verification.
3. **For each of V1–V4 (§0 above):** WebSearch / WebFetch external lit; if anchor found, update CLM status from VERIFIED-OWN → VERIFIED (anchor-supported) or PARTIAL or REFUTED with attribution. Write per-verification memo if substantial.
4. **No new probes** until verification round 1 completes (operator direction).
5. **After verification:** report which substrate-novel findings hold under external triangulation; which need refinement; which are NOVEL-FRONTIER (publishable methodology).

## 7. Discipline patterns established this session (carry forward)

1. **Meta-pre-reg locked before any content writing** (carried from prior session)
2. **LLM outputs disallowed as primary evidence** (carried)
3. **Verification memo per anchor + per substrate-novel finding** (carried + extended this session)
4. **Pre-reg LOCK-SHA convention** (commit with placeholder → fill SHA → commit)
5. **FEASIBILITY-NULL is a result type** — stop probes that the data can't support (3 cases this session)
6. **Substrate-novel findings explicitly flagged for external verification** (new this session — memo 30 §4)
7. **Per-phase tracker data is unreliable per-system** — use phase-combined files (Probes 4/5 carried)
8. **In Solar substrate, talk to user in PLAIN language** — no PV jargon when they're operating ([[feedback_plain_language_solar_domain]])

---

**Lock anchor:** commit hash captured at synthesis commit (HEAD post-commit). Pre-compact lock established.
