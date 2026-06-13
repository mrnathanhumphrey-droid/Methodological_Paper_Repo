# Pattern 013 — Executive-aggrandizement backsliding (third-wave autocratization) — libdem collapse via civilian-legal channels

- **ID:** PATTERN_013
- **Status:** firmed (5+ cases confirmed; corpus now includes IND slow-burn + USA fast-pole + BRA failed)
- **Type:** mechanism (third-wave autocratization, post-Lührmann-Lindberg 2019)
- **Discovered:** 2026-05-21 via LatAm first-look (SLV as in-sample case)
- **Severity / interest:** high — most-confirmed Tier A mechanism in the substrate

## Naming
- **Public-facing / academic term**: "third wave of autocratization" (Lührmann & Lindberg 2019) / "autocratic legalism" (Scheppele 2018) / "executive aggrandizement" (Bermeo 2016) / "constitutional retrogression" (Ginsburg & Huq 2018)
- **Internal working shorthand**: "Bukelization" (after El Salvador's Bukele case where the pattern was first dug out in our corpus). Folder slug is internal-navigation only.

## One line
SLV V-Dem libdem 2018 → 2024: **0.428 → 0.090** (−0.338) — comparable to BFA's coup-driven collapse (−0.359) but with no military coup. Bukele's state-of-exception and mass detentions drove the libdem drop and the 467K acute conflict-displacement figure.

## Numbers

SLV libdem trajectory:
- 2018: 0.428
- 2020: 0.316
- 2024: **0.090**

SLV acute period:
- conflict-displaced: 467,000
- war_fatal: 0
- strife_fatal: 0
- one_sided_fatal: 97

(The high conflict-displacement with low fatalities suggests **detention-driven displacement** — people fleeing the state-of-exception arrest sweeps rather than war fatalities.)

## Why it stands out
Adds a non-coup civilian-led authoritarianism mechanism to the libdem-collapse story. Same outcome shape (libdem collapse + displacement increase) as the Sahel coup-countries via a completely different mechanism: elected civilian president consolidating power through executive emergency decrees + mass detentions, rather than military coup. This complicates [[PATTERN_002]] (libdem tracks coup) — the right framing might be "libdem tracks state-violence-against-civilians" with coup as one trigger and authoritarian consolidation as another.

The SLV case also matters because it's the "successful authoritarianism" version — Bukele has 90%+ approval ratings and is widely cited internationally as a model. If displacement-as-consequence-of-authoritarianism holds even in popular authoritarian regimes, that's a finding worth showing.

## Open questions
- What's the timing of SLV's detention-displacement vs the libdem decline? Concurrent or lagged?
- Are the SLV displaced going to internal regions or fleeing to neighboring countries (which would show up in UNHCR as cross-border)?
- Does HTI (libdem 0.257 → 0.101, similar collapse magnitude) operate through a third mechanism (state failure) distinct from both coup (Sahel) and consolidation (SLV)?

## Related
- [[PATTERN_002]] Original libdem-coup pattern; this adds the non-coup variant
- [[PATTERN_011]] Cluster-conditioned dynamic range; SLV is the LatAm parallel to Sahel coups

## Data sources
- `D:/IDP/analysis/latin_america_stratified_panel_2026_05_21.parquet`
- V-Dem v15 libdem indicator for SLV
- Public record on Bukele's March 2022 state of exception

---

## Dig 2026-05-25 — Bukelization replicates across 5 countries (sliding 10y windows)

Sliding 10-year windows tested for the Bukelization shape (start libdem ≥ 0.30, Δ ≤ −0.30, monotonic, no coup, no interstate war):

| Country | # fitting windows | Best window | Δ | Notes |
|---|---|---|---|---|
| **SLV** (in-sample) | 4 | 2014-2024 | −0.375 | Bukele state-of-exception 2022 |
| **HUN** | 4 | 2009-2019 | **−0.402** | Orbán post-2010 |
| **TUR** | 3 | 2007-2017 | **−0.360** | Erdoğan AKP consolidation |
| **VEN** | 8 | 1997-2007 | **−0.441** | Chávez consolidation (deepest window count) |
| **POL** | 6 | 2010-2020 | −0.377 | PiS 2015-2023 — UNPREDICTED, see [[PATTERN_024]] |

**Counter-examples (fit FAILS at 10y window):**
- **RUS** — Putin-era libdem decline DOES NOT fit Bukelization shape. RUS started lower and declined slower; different mechanism (KGB-state continuation, not populist consolidation)
- **IND** — On Bukelization trajectory but at 22-year scale (0.587 in 2002 → 0.281 in 2024 = Δ−0.306). Decline is monotonic 10 of 12 years 2014-2024 but doesn't satisfy 10y window criteria.
- **BRA** — Non-monotonic (Bolsonaro decline then Lula recovery)
- **USA** — Stable; no Bukelization signal

**Negative controls all pass:** USA, DEU, GBR, FRA, CAN, NLD, JPN show ZERO fitting Bukelization windows.

**Status updated:** candidate-hypothesis (1 case) → **candidate-hypothesis FIRMED (5 cross-continent cases)** + 7 negative controls + 4 falsified-candidate countries.

**Refined Bukelization mechanism:**
1. **Populist mandate**: leader wins free election with majoritarian/anti-establishment platform
2. **Institutional capture**: judicial + media + electoral institutions captured through legal-civilian means
3. **5-15 year window**: collapse plays out over decade, not single-event
4. **Recovery POSSIBLE**: POL 2023 (Tusk coalition) + BRA 2023 (Lula) show election turnover can reverse the trajectory — see [[PATTERN_022]]

**Cross-link strengthening:** This is now a robust mechanism that may be the single most important Tier A pattern in the substrate.

---

## Deep Extraction 2026-05-25 — see [digs/2026_05_25_deep_extraction.md](digs/2026_05_25_deep_extraction.md)

**7-headline summary from full extraction:**

1. **Sub-indicator generalization** — Bukelization holds across V-Dem's 6 sub-components. Magnitudes: elections-free-and-fair drops biggest (range −1.16 to −3.69); media censorship drops in 4 of 5; judicial constraints + high court independence + civil society all decline. **CHRONOLOGY (per literature, NOT our finding)**: courts captured FIRST → enables election law changes + media ownership transfers + civil society restrictions. Our magnitude data is downstream of court-first chronology, not the chronology itself.

2. **Recovery is symmetric** — POL 2023-2025 sub-indicators reverse the captures that fell during PiS: high court +1.69, media censorship +2.47, free expression +0.30. BRA 2023-2024 same. **Captures reversible by election turnover.**

3. **2 new unpredicted confirmations**: **TUN (Saied 2012-2022, Δ=−0.446 deepest signature)** + **BLR (early Lukashenko 1992-2004, Δ=−0.343)**. Corpus now **7 confirmed cases** across 4 continents / 4 decades.

4. **IND is slow-burn Bukelization** — fits at 18-24 year windows (Δ=−0.306 over 22y; rate −0.014/yr ≈ 4× slower than SLV). Federal counter-pressure likely explains the slower trajectory.

5. **Speed varies 2× across cases** — SLV fastest (−0.061/yr, single state-of-exception event), HUN slowest (−0.033/yr, incremental legalistic).

6. **Displacement NOT a necessary consequence** — only SLV's mass-detention model generates GIDD conflict-displacement. HUN/POL/VEN/TUR/TUN/BLR don't produce IDPs via consolidation. **Libdem mechanism separable from displacement mechanism**.

7. **No coup signature anywhere** — UCDP shows zero state-based fatality jumps tied to consolidation in any case (TUR's PKK conflict runs parallel but unrelated). Civilian-authoritarian mechanism confirmed.

**Corpus updated:** 7 confirmed Bukelization countries + 1 slow-burn (IND) + 2 recovery cases (POL, BRA).

This is the strongest empirical pattern in the IDP substrate.

---

## Literature synthesis 2026-05-25 — see [literature/SYNTHESIS.md](literature/SYNTHESIS.md)

3 parallel lit-fetch agents covered theory + case-empirics + consequences-and-recovery. Key takeaways:

- **Don't call it "Bukelization"** publicly. Established term is **"third wave of autocratization"** (Lührmann & Lindberg 2019). Mechanism term is **"autocratic legalism"** (Scheppele).
- **Recovery is the NORM**: V-Dem WP #147 finds 52% of episodes reverse (73% in last 30 years). Our POL+BRA recoveries are baseline-consistent.
- **Sub-indicator chronology**: Literature says **courts captured FIRST**, then enable elections + media + civil society changes. Our magnitude rankings (elections-free-fair drops biggest) are DOWNSTREAM consequences of court-first chronology. The two findings are consistent; writeup must distinguish.
- **Stalled-recovery configuration** (Carnegie 2025): captured Constitutional Court + opposition presidency = stalled. POL has both (Nawrocki PiS-backed won June 2025 presidency). Our +0.228 libdem 2yr signal may not be durable.
- **Mass emigration is a feedback loop** (Auer & Schaub 2024): liberal-leaning citizens self-select out, accelerating backsliding. New testable mechanism for our corpus.
- **Sato et al. 2022 V-Dem WP #133** already tested sub-indicator sequencing across 69 episodes. Must compare before claiming our sequencing finding is novel.
- **TUN is shape-fit but mechanism-divergent** ("breakdown by disengagement" not executive aggrandizement). Keep in corpus with caveat.
- **BLR is a "completed-consolidation" case**, not ongoing backsliding (literature treats as negative control).
- **New candidates surfaced**: SRB, BGD (recently reversed 2024), USA Trump II (V-Dem 2025 explicit), NIC, BRA Bolsonaro as the failed-backsliding null case.
