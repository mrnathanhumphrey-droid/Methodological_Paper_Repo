# IDP Pattern Catalog

Living log of anomalies, contrasts, pooling patterns, and candidate mechanism stories surfaced as we stratify the IDP corpus.

## Naming convention

**"Bukelization" is our internal working shorthand.** In academic + public-facing writing, use established terms:

| Established academic term | Source | Use when |
|---|---|---|
| **third wave of autocratization** | Lührmann & Lindberg 2019, *Democratization* | Describing the broad temporal phenomenon |
| **autocratic legalism** | Scheppele 2018, *U. Chicago Law Review* | Describing the legal-civilian mechanism |
| **constitutional retrogression** | Ginsburg & Huq 2018, *How to Save a Constitutional Democracy* | Describing the structural shape |
| **executive aggrandizement** | Bermeo 2016, *Journal of Democracy* | Describing the leader-driven causal direction |
| **competitive authoritarianism** | Levitsky & Way 2010, 2025 | Describing the resulting regime form |

The folder slug `013_bukelization_libdem_no_coup/` is internal-navigation only. The pattern's writing-facing framing is the third-wave autocratization story.

## Quick navigation

- **[INDEX.md](INDEX.md)** — master table of all patterns with status + tier
- Each pattern lives in its own folder `NNN_<slug>/` with `README.md`, `digs/`, and `figures/` subfolders
- Cross-references between patterns use `[[PATTERN_NNN]]` syntax

## Table of Contents (25 patterns, by tier)

### Tier A — strongest, cross-cluster recurring (candidate-hypotheses)
- [001 — 3-channel displacement (conflict / flood / drought)](001_sahel_two_channel_displacement/README.md)
- [010 — Strife-dominant cross-cluster recurrence (MLI/SSD/HTI/CAF)](010_strife_dominant_recurs/README.md)
- [011 — Libdem range+trigger collapse model](011_libdem_dynamic_range_cluster_conditioned/README.md)
- [013 — Third-wave autocratization / executive-aggrandizement backsliding (FIRMED across SLV/HUN/TUR/VEN/POL/TUN/BLR; IND slow-burn; USA fast-pole; BRA failed)](013_bukelization_libdem_no_coup/README.md) ★★
- [017 — UKR pure-interstate-war boundary case](017_ukr_pure_state_war_anti_strife/README.md)
- [018 — Twin 2021 collapses (AFG Taliban + MMR coup)](018_dual_collapse_taliban_coup_2021/README.md)
- [019 — Disaster-displacement regime typology (6 regimes)](019_disaster_displacement_regime_typology/README.md)
- [020 — Regime 6 Earthquake-dominant (FIRMED across HTI/NPL/CHL/ECU/TUR/ITA)](020_hti_earthquake_dominant_regime/README.md) ★
- [023 — ETH triple-channel coupling (unpredicted)](023_eth_triple_channel_coupling/README.md)
- [024 — POL PiS-era Bukelization (unpredicted true positive)](024_pol_unpredicted_bukelization/README.md)
- [025 — Regime 3 sub-typology (bimodal-storm vs perpetual-storm)](025_regime3_subtypes_bimodal_vs_perpetual_storm/README.md)
- [026 — USA Trump II fast-pole (1-in-700 single-year LDI drop)](026_usa_fast_pole_2025/README.md) ★★ NEW
- [027 — Failed-backsliding archive (BRA/ISR/USA-I/KOR/PER null cases)](027_failed_backsliding_archive/README.md) NEW

### Tier B — single-cluster mechanisms
- [002 — Sahel libdem-coup lockstep (downstream of 011)](002_sahel_libdem_coup_lockstep/README.md)
- [009 — Earthquake as 4th displacement channel](009_earthquake_fourth_channel/README.md)

### Tier C — magnitude / anomaly observations
- [003 — BFA industrial-scale displacement (firmed-anomaly)](003_bfa_industrial_scale_displacement/README.md)
- [004 — NER 2024 monsoon flood (firmed-anomaly)](004_ner_2024_flood_exceeds_war/README.md)
- [012 — ETH/Tigray war fatality cluster (firmed; conflict-type meta-pattern)](012_tigray_largest_war_fatality_cluster/README.md)
- [015 — DRC 30M cumulative IDP corpus (firmed; predator-militia type)](015_cod_largest_cumulative_idp_corpus/README.md)
- [016 — PAK 2022 monster monsoon (firmed; uniquely bimodal-mega-flood)](016_pak_2022_flood_largest_single_disaster/README.md)

### Tier D — contrasts
- [005 — MLI strife EPICENTER + temporal diffusion (firmed)](005_mli_strife_ratio_outlier/README.md)
- [006 — BEN periphery spillover (firmed; active-spillover)](006_ben_periphery_spillover/README.md)
- [021 — BRA conf-drought coupling (unpredicted exception)](021_bra_drought_conflict_coupling_unpredicted/README.md)
- [022 — BRA libdem RECOVERY (first recovery case)](022_bra_libdem_recovery/README.md)

### Tier E — data quality
- [007 — Sahel drought-displacement gap (revised Sahel-specific)](007_drought_displacement_gap/README.md)
- [008 — Drought channel real globally](008_drought_channel_real_globally/README.md)
- [014 — UCDP pycountry name bug (firmed via fix)](014_ucdp_pycountry_name_bug/README.md)

## Pre-registrations

5 pre-regs locked; all stored in [../pre_regs/](../pre_regs/)
- **PRE_REG_001** — Strife-Signature Epicenter Diffusion (locked, awaiting TGO/CIV/GHA UCDP updates)
- **PRE_REG_002** — Range+Trigger Libdem Collapse (CONSISTENT after first fit)
- **PRE_REG_003** — Disaster-Displacement Regime Typology (SUPPORTED + extension to Regime 6)
- **PRE_REG_004** — 3-Channel Orthogonality (SUPPORTED 92%; ETH + BRA exceptions filed)
- **PRE_REG_005** — Bukelization Path (FIRMED with 5 cases at 10y window; POL unpredicted)

## When to log a pattern

Any time stratifying the data surfaces something that:
- **Sticks out** — outlier event, magnitude anomaly, lone trajectory
- **Pools** — multiple countries/years/sources converge
- **Contrasts** — one cell behaves opposite to its neighbors
- **Suggests mechanism** — candidate hypothesis worth pre-registering
- **Flags data quality** — gap, mismatch, suspicious column

Cheap to add. Cheap to discard.

## Status taxonomy

- `noted` — surfaced, not yet investigated
- `digging` — actively pulling on the thread
- `null` — investigated, doesn't replicate / artifact
- `candidate-hypothesis` — ready for pre-reg drafting
- `firmed` — pre-reg locked + result holds (or replicated across cases)
- `walked-back` — pre-reg locked + result didn't hold (still log it; honesty matters)
- `discarded` — no longer relevant

## Type taxonomy

- `anomaly` — single outlier event/cell
- `pooling` — multiple cells aligning
- `contrast` — cell behaving opposite to peers
- `mechanism-candidate` — structural story worth testing
- `data-quality-flag` — gap, encoding bug, misalignment

## Per-pattern folder template

```
NNN_<slug>/
├── README.md         ← main pattern doc (the file you'd read first)
├── digs/             ← subsequent dig notes as the thread evolves
│   └── YYYY_MM_DD_dig.md
└── figures/          ← charts, maps, plots
```

## ★ Star indicates pattern firmed across multiple cases (most-confirmed Tier A mechanisms)
