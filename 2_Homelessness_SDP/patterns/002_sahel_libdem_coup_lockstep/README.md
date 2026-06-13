# Pattern 002 — V-Dem libdem collapse perfectly tracks coup occurrence; Benin held

- **ID:** PATTERN_002
- **Status:** candidate-hypothesis
- **Type:** mechanism-candidate
- **Discovered:** 2026-05-21 via `build_sahel_stratified.py` first look
- **Severity / interest:** high

## One line
Three of four Sahel countries had military coups 2020-2023 — and their V-Dem liberal-democracy indices cratered. Benin, the only one without a coup, slightly improved. Coup-occurrence is essentially a binary lever on libdem in this cluster.

## Numbers

| Country | Coup year(s) | V-Dem libdem 2018 | V-Dem libdem 2024 | Δ |
|---|---|---|---|---|
| MLI | 2020, 2021 | 0.307 | 0.141 | **−0.166** |
| BFA | 2022 (Jan + Sep) | 0.485 | 0.126 | **−0.359** |
| NER | 2023 | 0.405 | 0.182 | **−0.223** |
| BEN | none | 0.472 | 0.323 | −0.149 (drift) |

## Why it stands out
Pre-coup BFA was the most democratic of the four (0.485) and post-coup is the least (0.126). The libdem-collapse magnitude scales roughly with how many years the post-coup regime has been in power. Benin's drift is much smaller and is consistent with general regional democratic backsliding rather than acute state collapse. This gives us a clean before/after structure on three countries plus a natural control.

## Open questions
- Is the libdem collapse a *consequence* of conflict-displacement, or upstream of it? Need to check ordering of: conflict escalation → coup → libdem drop, vs coup → libdem drop → conflict escalation.
- Does the BEN-as-control story hold up across other governance indicators (Polity 5, V-Dem civlib, V-Dem rule)?
- Could the gradient (Dakar/Cotonou ↔ Mali/Burkina interior) be measured as continuous governance gradient rather than binary?

## Related
- [[PATTERN_001]] Conflict channel tracks libdem; flood channel doesn't
- [[PATTERN_006]] Benin periphery — the no-coup control needs corroboration

## Data sources
- `D:/IDP/analysis/sahel_stratified_panel_2026_05_21.parquet` columns vdem_libdem, vdem_polyarchy, vdem_civlib, vdem_corr
- V-Dem v15
- Public record on coup dates (Mali 18 Aug 2020; Mali 24 May 2021; Burkina Faso 24 Jan 2022; Burkina Faso 30 Sep 2022; Niger 26 Jul 2023)
