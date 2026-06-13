# Pattern 014 — UCDP-GED merge silently drops Syria + Yemen due to pycountry name mismatch

- **ID:** PATTERN_014
- **Status:** firmed (fix applied to build_regional_panel.py 2026-05-21)
- **Type:** data-quality-flag
- **Discovered:** 2026-05-21 via MENA panel build
- **Severity / interest:** high (silent data loss in MENA panel)

## One line
The `build_regional_panel.py` UCDP merge uses pycountry's official names (e.g., "Syrian Arab Republic") but UCDP-GED stores raw names ("Syria", "Yemen (North Yemen)"). MENA panel shows 0 war fatalities for SYR and YEM as a result; the real numbers are large.

## Numbers

Affected merges (zero-rows in current MENA panel where real data exists):
- SYR all periods: war_state_based, strife_non_state, one_sided shown as 0
- YEM all periods: war_state_based, strife_non_state, one_sided shown as 0

Other UCDP name oddities to verify:
- "Cambodia (Kampuchea)"
- "DR Congo (Zaire)"
- "Madagascar (Malagasy)"
- "Myanmar (Burma)"

## Why it stands out
This is a silent bug. The merge succeeds (left join, no row drop) but emits NaN for the conflict-stratification columns on SYR/YEM rows. Downstream analysis would not realize Syria's massive war fatalities (likely 150K+ for the civil war period through 2019) are not in the panel.

## Open questions
- Are there other countries silently dropped? (LBN was found via "Lebanon" which matches.)
- Should the name-mapping use a hand-curated dict for UCDP-specific naming?

## Companion fix discovered
Same kind of bug on the user-side: the user typed CAR as ISO3 for Central African Republic, but the canonical ISO3 is **CAF**. GIDD/UCDP/V-Dem all use CAF. The CAR-key request silently produced an empty result for CAF rows. Lesson: validate ISO3 codes against pycountry before building any panel. Auto-fix the panel script to either warn or auto-map common mistakes (CAR -> CAF, EAST_TIMOR -> TLS, etc.).

## Fix (UCDP names — applied)
Added explicit overrides in `build_regional_panel.py`:
```python
UCDP_NAME_OVERRIDES = {
    "Syria": "SYR",
    "Yemen (North Yemen)": "YEM",
    "Yemen": "YEM",
    "Cambodia (Kampuchea)": "KHM",
    "DR Congo (Zaire)": "COD",
    "Madagascar (Malagasy)": "MDG",
    "Myanmar (Burma)": "MMR",
    "Russia (Soviet Union)": "RUS",
    # ... etc
}
# Apply: name_to_iso.update(UCDP_NAME_OVERRIDES)
```

Then re-run MENA panel.

## Related
- All four cluster panels — check for similar misses

## Data sources
- `D:/IDP/data/ucdp/GEDEvent_v25_1.csv` country column values
- `pycountry` library v26.2.16
