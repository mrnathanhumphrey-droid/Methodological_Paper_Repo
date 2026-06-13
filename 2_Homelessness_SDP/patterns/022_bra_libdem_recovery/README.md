# Pattern 022 — Brazil libdem RECOVERY (Bolsonaro → Lula transition)

- **ID:** PATTERN_022
- **Status:** noted (single case; counter-example to collapse-only framing)
- **Type:** mechanism candidate (recovery dynamics)
- **Discovered:** 2026-05-25 via PRE_REG_002 holdout scoring
- **Severity / interest:** high — first RECOVERY case in the corpus

## One line
Brazil's V-Dem libdem went **0.608 (2018) → 0.534 (2020) → 0.540 (2022) → 0.712 (2024)** — a Δ of **+0.104** over 6 years. After 4 years of Bolsonaro-era decline, Lula's 2023 return produced a measurable libdem recovery.

## Numbers (BRA V-Dem libdem)

| Year | libdem | Note |
|---|---|---|
| 2014 | 0.752 | pre-Dilma-impeachment |
| 2016 | ~0.65 | Dilma impeached |
| 2018 | 0.608 | Bolsonaro elected (October) |
| 2020 | 0.534 | mid-Bolsonaro low |
| 2022 | 0.540 | Lula elected (October) |
| 2024 | **0.712** | first 2 years of Lula |

Recovery shape: rapid 2022 → 2024 jump (+0.172) after Lula assumed office Jan 2023.

## Why it stands out
- **First measurable libdem recovery in the corpus.** Every other case we've studied is collapse (BFA/MLI/NER/CAF/HTI/SLV/AFG/MMR/COL-stable/PAK-stable). BRA is the only **bounce-back**.
- **PATTERN_011 (range+trigger) has no recovery mechanism in it** — it only models collapse direction. Recovery may need a parallel "range+restoration-trigger" sub-mechanism with different triggers (election turnover, institutional reform, executive-rollback).
- **Mechanism: democratic election + transparent institutional rollback** — Lula reversed many Bolsonaro-era executive orders, restored Brazilian institutions (Ibama, FUNAI, university councils), reinstated transparency rules. The recovery is institutional, not via libdem's underlying indicators changing magically.

## Implications
- **PATTERN_011 needs a "Recovery" companion pattern** — what conditions enable libdem recovery?
- **PRE_REG_002 (range+trigger collapse) doesn't predict recovery and isn't falsified by it** (the pre-reg is asymmetric — about collapse only)
- **Asymmetric corpus**: 9 collapse cases vs 1 recovery case is a sample-size imbalance. May reflect (a) genuine asymmetry of political dynamics (it's easier to collapse than to recover) or (b) corpus selection bias (we sample fragility countries).
- **Note for methodology paper**: must mention that the framework's collapse-focused mechanism is asymmetric and a recovery analog is methodologically needed.

## Open questions
- Are there other libdem recovery cases in V-Dem that we haven't surfaced (because they're not in our 28-country corpus)? Specifically check: ZMB (Zambia post-2021 Hichilema), SLE (Sierra Leone), TUN (Tunisia pre-2021), MWI (Malawi 2020 election re-do)
- Is BRA recovery stable, or does it depend on continued Lula-coalition success? (Bolsonaro returns 2026 → potential re-collapse — see PRE_REG_005 watching this)
- Does the recovery generalize: do all "free + fair" elections that turn over incumbents produce libdem recovery? Or is it conditional on specific institutional-restoration acts?

## Related
- [[PATTERN_011]] range+trigger collapse — this is the recovery counter-pattern
- [[PRE_REG_002]] range+trigger collapse pre-reg — asymmetric (collapse-only); recovery is a methodological gap
- [[PRE_REG_005]] Bukelization — BRA is a forward-watch case (if Bolsonaro returns 2026, could re-collapse)
- [[PATTERN_013]] Bukelization — BRA was BORDERLINE Bukelization 2018-2022; the recovery shows civilian-authoritarian consolidation is NOT necessarily one-way

## Data sources
- `D:/IDP/analysis/prereg_holdout_stratified_panel_2026_05_21.parquet` rows iso3=BRA
- V-Dem v15 libdem 2014-2024
