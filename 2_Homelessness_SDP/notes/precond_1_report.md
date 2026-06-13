# Pre-cond 1 Report — Country Sample Availability

**Run at:** 2026-05-17 19:58:45

**Locked check:** Each country has >= 5 years of DTM data with >= 50 admin-2 units present per year.

**Overall verdict:** **PHASE0_STUB**


## Per-country results

| Country | Panel present | Years meeting threshold | Verdict |
|---|---|---|---|
| colombia | False | None | PHASE0_STUB |
| sudan | False | None | PHASE0_STUB |
| drc | False | None | PHASE0_STUB |
| yemen | False | None | PHASE0_STUB |

## Failure handling (locked walk-back §7)

- Any country FAIL: drop from primary panel; rerun with remaining 3 countries OR pivot to Stage-B-only for the failing country.

- PHASE0_STUB results indicate Phase 0 lock-time scaffold; Phase 2 re-runs after DTM panels build.

