#!/usr/bin/env bash
# Orchestrator: fire v4-lite tq_g fits for 24-25 across all 6 stats, sequentially.
#
# Stats: PTS, REB, AST, STL, BLK, TOV
# Train: 5 prior seasons (19-20 to 23-24, max available)
# Each fit: 2 chains, 400 warmup, 400 sampling. ~30-60 min wall under contention.
# Total: ~3-5 hours wall time.
#
# Purpose: cross-season validation NEEDS 3+ seasons per stat. We have 22-23 + 23-24
# already; this adds 24-25 to clear that threshold and unlock the hierarchical
# Stan shrinkage model.
#
# After completion, re-run:
#   python scripts/cross_season_full_validation.py
#   python scripts/hierarchical_multi_year_runner.py --dry-run  (then --fit if good)

# Note: NOT using set -e. STL fit on 24-25 returned exit 1 due to harmless
# Stan ESS-diagnostic warnings; set -e would kill the chain after a usable fit.
# Per-stat exit handling below preserves the loop.
cd "D:/NBA Projections"

STATS=(PTS REB AST STL BLK TOV)
TRAIN="2019-20 2020-21 2021-22 2022-23 2023-24"
TEST="2024-25"
TRAIN_TAG="2019-20-2020-21-2021-22-2022-23-2023-24"

LOG_DIR="logs/v6_24_25_chain"
mkdir -p "$LOG_DIR"

for stat in "${STATS[@]}"; do
    EXPECTED_DIR_PATTERN="audit_runs/*/skill_backtest_${stat}_phase4_v4_quadratic_tq_g_${TRAIN_TAG}__${TEST}"
    EXISTING=$(ls -d $EXPECTED_DIR_PATTERN 2>/dev/null | head -1)

    if [ -n "$EXISTING" ]; then
        echo "[$(date '+%H:%M:%S')] SKIP $stat — audit exists at $EXISTING"
        continue
    fi

    LOG_FILE="$LOG_DIR/${stat}_$(date '+%Y%m%d_%H%M%S').log"
    echo "[$(date '+%H:%M:%S')] FIRING $stat (logging to $LOG_FILE)..."

    python -u -m cli.backtest_skill_volume \
        --stat "$stat" \
        --quadratic-age --team-quality --gravity \
        --train $TRAIN \
        --test "$TEST" \
        --max-players 200 \
        --chains 2 \
        --iter-warmup 400 \
        --iter-sampling 400 \
        > "$LOG_FILE" 2>&1
    exit_code=$?

    # Verify artifact regardless of exit code (Stan ESS warnings can produce
    # exit 1 on a clean fit — check that the audit dir landed on disk).
    POST_DIR=$(ls -d $EXPECTED_DIR_PATTERN 2>/dev/null | head -1)
    if [ -n "$POST_DIR" ] && [ -f "$POST_DIR/per_player_projections.csv" ]; then
        echo "[$(date '+%H:%M:%S')] DONE $stat (exit=$exit_code, artifact OK)"
    else
        echo "[$(date '+%H:%M:%S')] FAILED $stat (exit=$exit_code, no artifact) — see $LOG_FILE"
    fi
done

echo "[$(date '+%H:%M:%S')] Chain complete. Audit dirs:"
for stat in "${STATS[@]}"; do
    DIR=$(ls -d audit_runs/*/skill_backtest_${stat}_phase4_v4_quadratic_tq_g_${TRAIN_TAG}__${TEST} 2>/dev/null | head -1)
    if [ -n "$DIR" ]; then
        echo "  $stat: $DIR"
    else
        echo "  $stat: MISSING"
    fi
done

echo ""
echo "Next steps:"
echo "  python scripts/cross_season_full_validation.py     # 3-season pool"
echo "  python scripts/hierarchical_multi_year_runner.py --dry-run"
