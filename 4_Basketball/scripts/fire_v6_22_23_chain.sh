#!/usr/bin/env bash
# Orchestrator: fire v4-lite tq_g fits for 22-23 across 5 stats, sequentially.
#
# Stats: REB, AST, STL, BLK, TOV  (PTS already done in audit_runs/20260501T222551Z/)
# Each fit: 2 chains, 400 warmup, 400 sampling. ~30-60 min wall under contention.
# Total: 2.5-5 hours wall time.
#
# After completion, run scripts/forward_validation_full_per_stat.py to derive
# cross-season-validated offsets for v6.1.x updates.
#
# Skip individual stats by removing them from the STATS list.
# Each stat is gated by checking if its audit dir already exists for this train/test combo.

set -e
cd "D:/NBA Projections"

STATS=(REB AST STL BLK TOV)
TRAIN="2019-20 2020-21 2021-22"
TEST="2022-23"
TRAIN_TAG="2019-20-2020-21-2021-22"

LOG_DIR="logs/v6_22_23_chain"
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

    if [ $? -eq 0 ]; then
        echo "[$(date '+%H:%M:%S')] DONE $stat"
    else
        echo "[$(date '+%H:%M:%S')] FAILED $stat — see $LOG_FILE"
        # Don't bail entirely — continue to next stat
    fi
done

echo "[$(date '+%H:%M:%S')] Chain complete. Audit dirs:"
for stat in "${STATS[@]}" PTS; do
    DIR=$(ls -d audit_runs/*/skill_backtest_${stat}_phase4_v4_quadratic_tq_g_${TRAIN_TAG}__${TEST} 2>/dev/null | head -1)
    if [ -n "$DIR" ]; then
        echo "  $stat: $DIR"
    else
        echo "  $stat: MISSING"
    fi
done

echo ""
echo "Next step: python scripts/forward_validation_full_per_stat.py"
