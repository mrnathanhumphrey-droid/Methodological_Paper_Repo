# AST Projections — Install + Integration

**Producer:** [`scripts/produce_ast_projections.py`](produce_ast_projections.py)
**Scheduler:** `NBA_AST_Projections_Daily` — fires 10:15 ET daily
**Validation backtest:** [`runs/run_player_props_rolling_clean/`](../runs/run_player_props_rolling_clean/) (56.7% WR / +3.95% ROI on n=7,717)
**Post-mortem:** [`D:/nba_ev/docs/POSTMORTEM_2026_05_26.md`](file:///D:/nba_ev/docs/POSTMORTEM_2026_05_26.md)

## What gets produced

`D:/NBA Projections/audit_runs/{date}/ast_projections.parquet`

Per row:
| field | type | meaning |
|---|---|---|
| `nba_api_id` | int | NBA Stats player ID |
| `game_date` | str | YYYY-MM-DD (ET) |
| `player_name` | str | display |
| `proj_ast` | float | **forward-clean AST projection** = `prior_ast_per_game × (expected_mpg / prior_mpg)` |
| `prior_ast_per_game` | float | Bayesian-shrunk prior-season RS AST/game (k=30) |
| `prior_mpg` | float | prior-season RS MPG (baseline for ratio) |
| `s2d_mpg` | float | this-season MPG through yesterday (NaN if <5 prior games) |
| `expected_mpg` | float | `s2d_mpg` if available else `prior_mpg` |
| `n_prior_games` | int | sample size on prior-season rate |
| `mpg_source` | str | `s2d` or `prior_mpg_fallback` |

Sidecar JSON: `ast_projections_metadata.json` with build provenance.

## Recommended consumption pattern (nba_ev side)

```python
from pathlib import Path
import pandas as pd

def load_ast_projections(date: str) -> pd.DataFrame | None:
    p = Path(f"D:/NBA Projections/audit_runs/{date}/ast_projections.parquet")
    return pd.read_parquet(p) if p.exists() else None

# Per-bet evaluation:
proj_df = load_ast_projections(date)
proj_map = dict(zip(proj_df["nba_api_id"], proj_df["proj_ast"]))

for player_id, line in todays_ast_lines:
    proj = proj_map.get(player_id)
    if proj is None:  # rookie, off-night, or no prior season
        continue
    edge = proj - line
    if edge >= 1.0:
        bet = "OVER"
    elif edge <= -1.0:
        bet = "UNDER"
    else:
        bet = None  # skip
```

**Edge threshold = 1.0 assists** is the validated minimum. Higher thresholds (e.g., 1.85+) showed 59.5% WR / +8.7% ROI in backtest but cut sample size ~75%. Reasonable production stance: bet at edge ≥ 1.0, size larger on edge ≥ 1.85.

## Why this works (mechanism)

- AST is the lowest-liquidity major prop market at DK → looser closing lines than PTS
- AST varies most with MPG (a 5-min swing moves projected AST more proportionally than projected PTS, because non-AST minutes still produce points but distinctly AST-credited possessions are minutes-dependent)
- Our prior-season-shrunk rate + season-to-date MPG forecast catches both:
  - Season-mean reversion (Vegas overweights recent form)
  - Minutes-driven volume changes (rotation shifts that haven't propagated to line)

## Caveats + monitoring

1. **Cross-book check pending.** Backtest is DK-only. FanDuel + Caesars replication would harden the claim.
2. **CLV check pending.** We haven't tested whether the edge persists at close (vs at our 23:00 UTC snapshot). If lines tighten by tipoff, deployed edge could erode.
3. **Live tracking:** maintain a clean ledger of every AST bet placed. After ~200 bets, compare actual WR to backtested 56.7%. If live runs >2pp below backtest, flag for re-investigation (could be selection bias we haven't caught).
4. **Edge erosion:** AST market liquidity may tighten over time as books mature. Re-validate quarterly.
5. **Rookies + late signings** with no prior-season data get no projection (mpg_source absent from output). Live system should skip those bets.

## Producer guarantees

- Forward-clean: no current-date or future-date info used in projection
- Idempotent: safe to re-run for same date (overwrites)
- Atomic writes (parquet temp+rename)
- No-op if active cohort empty (off-day, off-season)

## Schedule + monitoring

```powershell
# Check status
Get-ScheduledTask -TaskName "NBA_AST_Projections_Daily" | Get-ScheduledTaskInfo

# Manual fire
& "D:\NBA Projections\cli\NBA_AST_Projections.bat"

# Tail log
Get-Content "D:\NBA Projections\logs\ast_projections.log" -Tail 30
```

Daily output directory:
```
D:/NBA Projections/audit_runs/2026-05-27/
├── ast_projections.parquet
└── ast_projections_metadata.json
```
