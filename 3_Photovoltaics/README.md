# Solar

Research substrate for a future solar-panel performance + reliability lab.

**Scope (per user direction 2026-05-27):** scoping document for "exactly what we would need" to operate a lab that can move the solar-panel field forward across three axes:

1. **Degradation** — why panels lose output over years; module-level vs system-level decomposition
2. **Field reliability** — real-world failure mode distribution and what predicts which mode fires when
3. **Siting / yield** — geographic + meteorological drivers of actual yield vs nameplate

Goal of the work in this folder: identify the gaps where a lab CAN move the field, the instruments + data + partnerships needed to address them, and the specific experiments that produce evidence not already in NREL / Fraunhofer / SETO publications.

This is a research-program scoping log, not a paper. The literature/ folder holds decision memos (numbered, dated) that accumulate the actual scoping work.

## Structure

- `literature/` — numbered Markdown decision memos (00_, 01_, ...). Like Battery/literature.
- `code/` — analysis scripts when we start pulling field data
- `data/` — raw + processed data; raw is gitignored

## Current state

- `literature/00_LANDSCAPE_v0.md` — DEMOTED. LLM-written hypothesis pool, every numeric claim is NEEDS-VERIFICATION.
- `literature/01_METAPREREG_v1.0_evidence_discipline.md` — **load-bearing**. Locks evidence rules, primary-source admission list, anti-LLM provisions, knowledge state labels. All downstream work obeys this.
- `literature/02_CLAIMS_LEDGER.md` — every claim from 00 catalogued with verification status. Empty verification log; awaiting first pass.

## Discipline

Per `01_METAPREREG`: LLM outputs (Claude, etc.) are NEVER primary sources in this substrate. LLM-written content inherits NEEDS-VERIFICATION on every numeric / factual claim until an operator-driven verification pass against a primary source completes. This was set up in response to the v0 landscape doc being confident-sounding text without citations.
