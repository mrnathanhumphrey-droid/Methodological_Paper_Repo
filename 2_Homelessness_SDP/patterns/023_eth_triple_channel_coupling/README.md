# Pattern 023 — Ethiopia: triple-channel coupling, all 3 displacement channels correlated

- **ID:** PATTERN_023
- **Status:** candidate-hypothesis (unpredicted anomaly)
- **Type:** mechanism + anomaly
- **Discovered:** 2026-05-25 via deep PRE_REG_004 dig
- **Severity / interest:** **high — most extreme channel-coupling in entire corpus**

## One line
Ethiopia is the only country in the corpus where ALL THREE displacement channels (conflict / flood / drought) are simultaneously correlated at country-year level: ρ(CF)=0.691, ρ(CD)=0.830, ρ(FD)=0.582. This is a fundamental violation of PATTERN_001's 3-channel orthogonality.

## Numbers (ETH 2008-2024)

| Pair | Spearman ρ | Pre-locked threshold | Status |
|---|---|---|---|
| conflict ↔ flood | **0.691** | ≤0.5 | VIOLATED (CF) |
| conflict ↔ drought | **0.830** | ≤0.5 | VIOLATED (CD) — strongest in corpus |
| flood ↔ drought | **0.582** | ≤0.5 | VIOLATED (FD) — only country with this pair > 0.5 |

For context:
- BRA (PATTERN_021): CD=0.697 only
- SOM (pre-registered H3): CD=0.786 only
- Every other country in corpus: <0.5 on all pairs

## Why it stands out
- **Total channel-coupling case**: Ethiopia in 2008-2024 had simultaneous (a) Federal-TPLF war + Amhara/Oromia conflicts, (b) Rift Valley flooding, (c) Horn drought cycles. All three peaked or troughed in correlated years.
- **2020-2021 was a triple peak**: Tigray war opening + flooding + drought all hit simultaneously
- **Falsifies the 3-channel orthogonality assumption in ETH specifically** — but PATTERN_001 still holds for ~92% of corpus, so ETH is the most extreme exception
- **Mechanism candidate: ENSO + political destabilization coupling.** La Niña years drive both Horn drought AND Sahel insurgency expansion (climate-conflict feedback). Ethiopia sits at the intersection.

## Implications for the framework
- **PRE_REG_004 H3 needs ETH as a 5th pre-specified exception** alongside SOM/SDN/PHL/(BRA)
- **The orthogonality assumption is conditioned on "no single shock period dominates all channels"** — 2020-2024 hit Ethiopia with synchronized war + flood + drought, breaking the assumption
- **Possible new mechanism: synchronized-crisis coupling** — when a country experiences multi-channel shocks within the same 2-3 year window, the channels couple artificially through shared baseline pressure (state capacity collapse, refugee compounding, food-system collapse)

## Open questions
- Is the coupling driven by 2020-2024 alone, or does it hold over a longer window? Bootstrap test needed.
- What does ETH's coupling look like in 2008-2018 vs 2018-2024? (split test)
- Are there other "synchronized crisis" countries we haven't tested (SOM, SDN both have CD coupling but FD wasn't testable due to drought-data sparsity)?
- Cross-link to climate attribution: did the same La Niña/El Niño cycles drive both ETH drought and ETH war timing?

## Related
- [[PATTERN_001]] 3-channel orthogonality — most extreme violation
- [[PATTERN_021]] BRA conf-drought coupling — similar but only 1 pair
- [[PATTERN_012]] Tigray war (the conflict pressure)
- [[PATTERN_008]] Horn drought channel (the drought pressure)
- [[PRE_REG_004]] orthogonality pre-reg — this result is a 2nd unpredicted exception requiring H3 expansion

## Data sources
- GIDD conflict + flood + drought channels, ETH 2008-2024
- Spearman correlations from deep_dig_pre_regs.py output 2026-05-25
