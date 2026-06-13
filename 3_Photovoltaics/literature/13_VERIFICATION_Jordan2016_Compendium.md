# 13 — Verification: Jordan et al. 2016 Compendium of PV Degradation Rates

**Verification date:** 2026-05-27
**Verifier:** subagent + operator endorsement pending
**Target citation:** Jordan, D.C., Kurtz, S.R., VanSant, K., Newmiller, J., 2016. "Compendium of photovoltaic degradation rates." *Progress in Photovoltaics: Research and Applications*, 24(7), 978-989. DOI: 10.1002/pip.2744.
**Purpose:** Close ERR-2 from `12_VERIFICATION_PASS_v1_summary.md`. v0 attributed the c-Si mean 0.8-0.9%/yr figure to Jordan-Kurtz 2013; pass v1 found it actually originates in this 2016 Compendium.

## Retrieval status

- `https://doi.org/10.1002/pip.2744` resolves to Wiley Online Library — **HTTP 402 paywalled**.
- `https://www.osti.gov/biblio/1259256` (DOE OSTI primary record) — **abstract + metadata retrieved**.
- `https://www.osti.gov/pages/biblio/1400540` (OSTI post-print record) — **abstract + metadata retrieved**.
- NREL `docs.nrel.gov/docs/fy16osti/65040.pdf` — 404, not the right report number.
- Local PDF: **not yet pulled** (operator may have a copy in Downloads to drop into `data/raw/papers/`).

**Net status:** abstract + metadata confirmed from two independent DOE OSTI records; full PDF body NOT obtained this pass. Abstract carries the key headline numbers we need.

## Citation header verdict — CONFIRMED

| Field | Our citation | Verified | Verdict |
|---|---|---|---|
| Authors (order) | Jordan, Kurtz, VanSant, Newmiller | Same 4, same order | CONFIRMED |
| Year | 2016 | 2016 | CONFIRMED |
| Title | "Compendium of photovoltaic degradation rates" | Confirmed (Wiley strips subtitle vs OSTI) | CONFIRMED |
| Journal | Progress in Photovoltaics | Same | CONFIRMED |
| Volume / issue / pages | 24(7), 978-989 | Same | CONFIRMED |
| DOI | 10.1002/pip.2744 | Resolves | CONFIRMED |

## Per-claim verdicts (all from OSTI abstract)

- **C1 — Median c-Si degradation rate: VERIFIED 0.5-0.6 %/yr.** Abstract: "median degradation for x-Si technologies in the 0.5-0.6%/year range."
- **C2 — Mean c-Si degradation rate: VERIFIED 0.8-0.9 %/yr.** Abstract: "mean in the 0.8-0.9%/year range." **This is the figure v0 mis-attributed to Jordan-Kurtz 2013. ERR-2 CLOSED — re-attribute to Jordan, Kurtz, VanSant, Newmiller 2016, pip.2744.**
- **C3 — Total degradation rates analyzed: VERIFIED >11,000.** "More than 11 000 degradation rates" from "almost 200 studies."
- **C4 — Countries in sample: VERIFIED 40.** "From 40 different countries."
- **C5 — Cell technology breakdown: VERIFIED (qualitative).** Abstract names: x-Si median 0.5-0.6 / mean 0.8-0.9 %/yr; HIT and microcrystalline-Si ~1 %/yr; CIGS several low-degradation studies; CdTe higher degradation reported. Per-technology numerical CIs not in abstract — need PDF body.
- **C6 — Distribution shape: PARTIAL.** Abstract states "majority of these modules exhibit a fairly linear decline" with some non-linearities in worst-performing units. Abstract does NOT explicitly say "log-normal."
- **C7 — Manufacturer warranty comparison: NOT-CONFIRMED-FROM-ABSTRACT.** No warranty-curve language in either OSTI abstract.
- **C8 — Climate stratification: VERIFIED (simplified Köppen-Geiger).** Categories: Moderate, Desert, Hot and Humid, Snow. Abstract: "Hotter climates and mounting configurations that lead to sustained higher temperatures may lead to higher degradation in **some, but not all, products**."

## Datasets + supplementary

- 2016 Compendium itself does NOT release a public machine-readable dataset (no supplementary CSV).
- **Public dataset release follows in the 2022 follow-up:** "Photovoltaic Fleet Degradation Data, Version 2022.02.22," NREL, DOI **10.21948/1842958**, at DuraMAT Data Hub + OSTI 1842958.

## Critical follow-up: 2022 fleet update (supersedes 2016 for "current median")

- **Jordan, Anderson, Perry, Muller, Deceglie, White, Deline, 2022. "Photovoltaic fleet degradation insights." *Prog. Photovolt.*, DOI 10.1002/pip.3566.**
- Headline numbers per search summary: 7.2 GW across 1700 sites / 19,000 inverters (~6-7% of US fleet); overall PLR **-0.75 %/yr**.
- **Climate-stratified field PLR**: **cool climates median -0.48 %/yr; hot climates -0.88 %/yr**.
- This is the canonical modern citation for "median field PV degradation."
- **Verify in a separate pass** — currently NEEDS-VERIFICATION on its own claims; only OSTI/abstract level here.

## Notes for v0 corrections

1. **ERR-2 closed.** Mean c-Si **0.8-0.9 %/yr** + median **0.5-0.6 %/yr** + **>11,000 rates / ~200 studies / 40 countries** all originate in **Jordan, Kurtz, VanSant, Newmiller 2016 (pip.2744)**, NOT Jordan-Kurtz 2013.
2. **Climate stratification framing:** simplified Köppen-Geiger (Moderate / Desert / Hot and Humid / Snow) — use this exact 4-category framing when citing.
3. **2022 fleet supersedes 2016 for modern claims:** When citing "median field c-Si degradation today," use Jordan 2022 (pip.3566) at -0.75%/yr overall; cite 2016 Compendium as historical literature-aggregation reference.
4. **CLM-002 ledger update:** re-attribute to pip.2744. Done in pass v2 ledger edit.

## Open follow-ups

- F1: Retrieve full PDF body (operator may have access via Wiley institutional login; OSTI may have full preprint)
- F2: Verify Jordan 2022 fleet paper (pip.3566) in its own pass
- F3: Pull NREL PV Fleet 2022 dataset (DOI 10.21948/1842958) — this is the actual machine-readable dataset

## Sources

- OSTI 1259256: https://www.osti.gov/biblio/1259256
- OSTI 1400540: https://www.osti.gov/pages/biblio/1400540
- Wiley (paywalled): https://onlinelibrary.wiley.com/doi/10.1002/pip.2744
- Follow-up 2022 paper: https://onlinelibrary.wiley.com/doi/10.1002/pip.3566
- 2022 NREL fleet dataset: https://www.osti.gov/biblio/1842958
- PV Lifetime Project at Sandia PVPMC

## Ledger impact (applies on operator endorsement)

- **CLM-002** mean c-Si 0.8-0.9%/yr: VERIFIED, citation Jordan et al. 2016 (pip.2744). ERR-2 CLOSED.
- New entry: **CLM-c-Si-MEDIAN**: median c-Si 0.5-0.6%/yr from same paper.
- New entry: **CLM-COMPENDIUM-N**: 11,000+ degradation rates, ~200 studies, 40 countries.
- New entry: **CLM-CLIMATE-DEGRADE-2016**: Hotter climates correlate with higher degradation "in some but not all products" — partial-correlation finding (note: this is the source for v0's "climate-specific aging" general claim, but the actual finding is product-conditional).
