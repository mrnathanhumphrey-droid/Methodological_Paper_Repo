# Pre-cond 3 Report — Historical Polygon Coverage

**Run at:** 2026-05-17 22:31:55

**Locked check:** Each Stage-A polygon contains >= 5 admin-2 units.

**Overall verdict:** **PASS**


## Per-country results

| Country | Polygon file | N admin-2 inside | Verdict |
|---|---|---|---|
| colombia | historical_polygons\colombia_la_violencia_1948_1958\stage_a_polygon.geojson | 658 | PASS |
| sudan | historical_polygons\sudan_fur_dar_pre1994\stage_a_polygon.geojson | 21 | PASS |
| drc | historical_polygons\drc_kasai_1959_1965\stage_a_polygon.geojson | 59 | PASS |
| yemen | historical_polygons\yemen_six_wars_2004_2010\stage_a_polygon.geojson | 102 | PASS |

## Failure handling (locked walk-back §7)

- FAIL: aggregate polygon-internal admin-2s to a single binary indicator without within-polygon partial pooling. Document downgrade.

- PHASE0_STUB: polygon digitization not yet complete. Phase 0+ pacing: 1922 CDO + pre-1994 Fur dar are 2-3 day each per locked budget.

