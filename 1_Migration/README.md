# RMD-SRC US Internal Migration Study

Substrate falsification target for RMD-SRC (Humphrey 2026 working draft). Pre-registration v1.0 locked 2026-05-27; v1.1–v1.9 amendments + extensions fired by 2026-05-28. Consolidated + confirmed verdict 2026-05-29.

**Headline:** RMD-SRC **partially holds** for migration. The *static* decomposition layer (demographic species + opportunity-moment pull taxonomy + gravity + latent corridors) works and transfers across periods. The *dynamic* regime-classification layer fails (F2 + GEO_F4 fire). Migration is **opportunity-clearing, not conservation-law decomposition** — and the displacement push that we tried to recover from migration flows is **structurally invisible by construction** (the truly displaced exit the ACS mover sample), making this study the **observable-PULL half** of a two-substrate displacement system whose **observable-PUSH half** is the SDP/homelessness study (see *Cross-substrate seam* below).

## Environment

Python 3.12.10 in venv at `D:\Migration\.venv`. Pinned deps in `requirements.lock.txt`; loose constraints in `requirements.txt`.

```powershell
& D:\Migration\.venv\Scripts\Activate.ps1
# or invoke directly:
& D:\Migration\.venv\Scripts\python.exe <script>
```

## Data

- **IRS SOI county-to-county migration** (open): `data/raw/irs_soi/`, 24 files, ~115 MB, 2011–2012 through 2022–2023 inflow + outflow. Provenance in `MANIFEST.tsv` with SHA256 per file.
- **IPUMS USA ACS 2012–2023** (gated): pulled via `IPUMS_API_KEY` env var; see `docs/IPUMS_EXTRACT_SPEC.md` and `src/submit_ipums_extract.py`.
- **IPUMS-CPS ASEC 2016–2024** (gated): extract #3 carries WHYMOVE × MIGRATE1 × OFFPOV × METFIPS × ASECWT for 122k movers (collection=cps; MIGRATE1D is ACS-only).

## The object and method

P₀ = age × income × family × education (48 cross-product cells). Sparse cells (<500 events/year) deterministically collapsed → **K = 38 species**. Unit: individual ACS cross-PUMA migrant 2012–2021, PERWT-weighted, on 2010-vintage PUMAs. **n = 994,235 events** (within-PUMA moves and immigration excluded; only MIGRATE1D ∈ {24,31,32}).

Two aggregations:
- **Demographic arm**: species × observable × year moment trajectories of μ, σ² for `log_distance`, `log_dest_density`, `opp_deficit`. T = 10 annual bins → 1,140 trajectories (38 × 3 × 10). Train 2012–2017 / holdout 2018–2021 (v1.1 windows).
- **Geographic arm**: MIGPUMA → MIGPUMA corridor flows; Poisson gravity (mass + distance) baseline; latent-corridor tensor factorization.

## Pre-regs and verdicts

| Pre-reg | Topic | Verdict |
|---|---|---|
| **v1.0** locked 2026-05-27 | Structural commitments (F1=80% / F2=50% / F3=30% / F4 κ≥0.4); six migration-specific operationalizations (PUMA, 2012–2023 annual, cross-product P₀, PCA opportunity index, etc.) | Substrate frame locked |
| **v1.1, v1.2, v1.4, v1.5** amendments | Train/holdout window correction (→ 2012–17 / 2018–21); P₀ K=38 (sparse-cell merge); etc. | Locked |
| **v1.7 — flow taxonomy** | Two-pull-moment taxonomy (4 flows) + 5th push (desperation) split; **held-out signature gate ≥0.80** | **PULL TAXONOMY PASSES (r=0.90 reproduced); DESPERATION push NULL** |
| **v1.8 — net-livability field (StageA)** | Origin economic/food-access fields beyond gravity | **NULL** (`field_real_and_singular = false`; gravity ate everything) |
| **v1.9 — food-apartheid push** | HOLC redline over-emission, racial F1/F2/F3 | **APARTHEID hypothesis FALSIFIED, racially INVERTED** (β_White > β_Black); finding = generic place-decline, not racial-mobility gap |

## Findings (top to bottom)

### 1. Static decomposition WORKS — pull taxonomy CONFIRMED
Four-flow opportunity taxonomy from two moments (μ stability, σ aspiration):

| flow | def | young | kids | dest density |
|---|---|---|---|---|
| DREAMER | hi-σ, lo-μ | 42.7% | 27.0% | 991 |
| STABILITY | hi-μ, lo-σ | 40.2% | 31.6% | 356 |
| BOTH | up both | 44.0% | 27.6% | 984 |
| CLEARING | down both | 39.0% | 28.7% | 381 |

Separation is sharp on *where* (destination density ~3×) and modest on *who* (4–5pp demographic shifts) — **opportunity generates the flow; demographics select within it**.

**Held-out transfer (train 2012–17 vs holdout 2018–21):** PASSES the ≥0.80 gate. **Reproducible r = 0.90** (independently recomputed in `D:/IDP/_scripts/CLTR_confirm_migration_heldout.py` from `results/flow_taxonomy.parquet × data/derived/P0_partition.parquet`; 4-pull-flow × 4-demographic-feature signature, Pearson). **The prose figure r = 0.999 (RESULTS_migration_substrate.md L78, L95) does NOT reproduce and is not committed in code — use 0.90 for publication.**

### 2. The push side is STRUCTURALLY INVISIBLE — three independent NULLs

- **Desperation 5th flow (v1.7).** Split CLEARING quadrant by origin rent-burden top-tercile. Demographically NULL (low-income Δ ≈ −1.2, wrong direction). *Reason:* ACS observes movers *post*-move (RENTGRS = destination), so the individual push is structurally invisible; only the area-median origin rent-burden was proxiable, which tags "left an expensive metro," not "was displaced." (The −1.2 figure is prose-only / no backing JSON — but the null is robust and replicated by the seam tests on the SDP side.)
- **Net-livability field (v1.8).** Origin economic + food-access fields fail to predict corridor flows beyond gravity. `results/netfield_stageA.json`.
- **Food-apartheid push (v1.9).** β_NH-White **+0.737 (p=8.2e-6)**, β_Black **+0.130 (p=0.48)**, β_Hispanic **+0.452 (p=0.049)**. F1 fires (signal exists). **F2 FAILS — racially inverted** (β_Black − β_White = −0.607, z=−2.46). F3 transfer holds. Apartheid hypothesis falsified; the result is **generic place-decline** in HOLC-redlined areas with the highest-power (most visible) group being NH-White. `results/v19_foodpush.json`, `v19_foodpush_ext.json`.

### 3. Geographic arm — statics hold, dynamic regimes do NOT transfer

- Poisson gravity baseline pseudo-R² ≈ **0.63 / 0.74**. `results/geo_gravity_baseline.json`.
- Latent corridors (tensor factorization) replicate split-half at **Tucker ≈ 0.95**. `results/geo_tensor_factors.json`.
- **GEO_F1, GEO_F2: do not fire** (statics replicate). **GEO_F3 fires** at division (small-n fragility). **GEO_F4 FIRES HARD** both division and state (κ = −0.06 / +0.015, near chance). `results/geo_falsifiers_summary.json`. **Corridor dynamic regimes do not transfer 2012–17 → 2018–21.**

### 4. Push/pull bridge — WHYMOVE microdata (D:/IDP collaboration)

The IPUMS-CPS WHYMOVE bridge (extract #3, 122k movers, ASEC 2016–2024) recovered a small *visible-completed* push sliver: affordability-push share is **poverty-concentrated AND intensifies with distance** — interstate **8.0% (below-pov) vs 4.8% (above) = 1.68×**, intercity 1.33×, local 1.42×. **2021 ratio = 0.93** (eviction moratorium suppressed the push exactly when eviction was blocked). Confirms a real push exists at the edges (5–9% of intercity moves, poverty-tilted), but it is dominated by pull (job/family/aspiration) and only captures *completed* moves — the invisible tail (deprivation-push that exits the sample) persists.

## Consolidated verdict — RMD-SRC partially holds

- ✅ **Static decomposition works** — demographic species, pull taxonomy (transfer r = 0.90), gravity (R² 0.63/0.74), latent corridors (Tucker 0.95).
- ❌ **Dynamic regime-classification fails** — F2 (geography is decomposition-resistant under demographic partition) + GEO_F4 (corridor regimes don't transfer).
- **Mechanism reading:** migration is an opportunity-clearing flow network. Opportunity is the generative field (endogenous, vacancy-chain-coupled); demographics are the selection/gearing; the field is read by people through its moments (μ = stability, σ = aspiration). Decomposition is the wrong mathematics for what is in part a *conservation law*, which is precisely why the static layer holds while the dynamic/decomposition layer breaks.

## Cross-substrate seam (the unified frame)

Migration is the **observable-pull half** of a two-substrate displacement system; the SDP/homelessness study (`D:/IDP/papers/PAPER_7_SDP_FRAMEWORK/`) is the **observable-push half**. The cascade:

```
PRESSURE (wages → rent)
  GATE 1 mobility:
    pull           → in-migration              [visible, completes]
    push·cost      → out-migration             [visible; small completed sliver, poverty-tilted with distance — WHYMOVE]
    push·deprivation → TRAPPED                 [INVISIBLE TO MIGRATION — exits the sample]
  GATE 2 rent floor (of the trapped):
    soft floor → stays housed-but-poor         [food insecurity rides POVERTY here, parallel axis]
    hard floor → HOMELESSNESS                  [the rent-precarity terminus]
  GATE 3 shelter policy:
    RTS mandate → sheltered (terminal)
    escapes     → STREET                       [the residual of the whole cascade]
  GATE 4 (street only):
    climate GATE (national) × supply MAGNITUDE (West-Coast-regional)
```

Migration sees Gate-1 escapers. Homelessness sees the deprivation-residual that fails Gate 1 and falls through Gates 2–4. The conservation/bifurcation seam test (`D:/IDP/analysis/paper7_conservation_seam_2026_05_28.json`) confirms: rent drives both out-migration (+0.41) and homelessness (+0.75), but income does *not* route the split (P2b: income → out-migration −0.13, p=0.17), because aggregate out-migration is pull-dominated and cannot isolate the displacement sub-flow. **The seam is un-instrumentable from the migration side.**

## Publication watch-outs (corrections before citing)

1. **Use r = 0.90, not r = 0.999** for the v1.7 held-out transfer. The 0.999 in `docs/RESULTS_migration_substrate.md` L78, L95 does not reproduce; the reproducible 0.90 is in `D:/IDP/_scripts/CLTR_confirm_migration_heldout.py` + `D:/IDP/analysis/CLTR_migration_heldout_confirm_2026_05_29.json`.
2. **Relabel v1.9.** "Redline → racial-mobility gap" is wrong; the F2 result is **racially inverted (β_White highest)** — finding is **generic place-decline in HOLC-redlined areas**, not racial-targeting.
3. **Desperation Δ = −1.2** lives only in prose (no JSON). It's a NULL so low stakes, but flag it if cited.
4. The **species counts (38), event count (994,235), "48 boson / 41 fermion," and 0.9%-clean rate** also live in prose `docs/RESULTS_migration_substrate.md` without a backing JSON. Either commit a Step-3 results JSON or cite cautiously.

## Layout

```
data/{raw,derived,external}
src/rmd_src/         # Step 1-6 algorithm components + pre-reg fire scripts
prereg/              # v1.0 lock + v1.1–v1.9 amendments + P0 hash record
results/             # flow_taxonomy.parquet, gravity baselines, tensor factors, falsifier summaries, v1.9 food-push
docs/                # RESULTS_migration_substrate.md, extract specs
notebooks/           # exploration
figures/             # moment-flow trajectories
logs/                # per-run logs
```

## Cross-reference

- Confirmation ledger (publication-readiness): `D:/IDP/papers/PAPER_7_SDP_FRAMEWORK/digs/CLTR_2026_05_29_CONFIRMATION_LEDGER.md`
- SDP / homelessness substrate: `D:/IDP/papers/PAPER_7_SDP_FRAMEWORK/README.md`
- Reproducible recompute of v1.7 held-out transfer: `D:/IDP/_scripts/CLTR_confirm_migration_heldout.py`
