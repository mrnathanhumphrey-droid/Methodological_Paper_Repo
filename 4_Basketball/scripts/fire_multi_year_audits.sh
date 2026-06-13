#!/usr/bin/env bash
# Multi-year v4-lite tq_g audit campaign.
#
# Fires v4-lite tq_g fits for missing (stat, test_season) combinations.
# Sequential by default (safe for CPU contention with concurrent regens).
# Idempotent: skips combinations whose audit dir already exists.
#
# When fetcher delivers older box scores (14-15 to 18-19), add those years
# to TEST_SEASONS list and re-run; existing audits will be skipped.
#
# Each fit: 2 chains, 400 warmup, 400 sampling. ~30-60 min wall under contention.
#
# Total possible: 6 stats x 6 seasons = 36 audits.
# Already exist: 23-24 (full), 22-23 (PTS only initially, 5 more in flight via bbcczit4w).
# Need: 19-20, 20-21, 21-22, 24-25 each x 6 stats = 24 fits if box scores cover those.
#
# After all complete:
#   python scripts/cross_season_full_validation.py
#   python scripts/hierarchical_multi_year_stan.py  (when ready)

set -e
cd "D:/NBA Projections"

STATS=(PTS REB AST STL BLK TOV)
TEST_SEASONS=(2019-20 2020-21 2021-22 2024-25)
LOG_DIR="logs/multi_year_audits"
mkdir -p "$LOG_DIR"

# Train sets per test season (3 prior seasons each for new tests, more for recent)
# Updated 2026-05-01 after 14-15 to 18-19 box-score backfill landed.
declare -A TRAIN_FOR
TRAIN_FOR[2019-20]="2016-17 2017-18 2018-19"
TRAIN_FOR[2020-21]="2017-18 2018-19 2019-20"
TRAIN_FOR[2021-22]="2018-19 2019-20 2020-21"
TRAIN_FOR[2022-23]="2019-20 2020-21 2021-22"
TRAIN_FOR[2023-24]="2019-20 2020-21 2021-22 2022-23"
TRAIN_FOR[2024-25]="2019-20 2020-21 2021-22 2022-23 2023-24"

# Train_tag (used in audit dir name) is "-".join(train seasons)
make_train_tag() {
    echo "$1" | tr ' ' '-'
}

count_total=0
count_existing=0
count_missing=0
count_fired=0
count_failed=0

# First pass: report what's needed
echo "=== Multi-year v4-lite tq_g audit matrix ==="
echo
printf "%-7s | " "stat"
for ts in "${TEST_SEASONS[@]}"; do
    printf "%-9s " "$ts"
done
echo
echo "$(printf '%.0s-' {1..60})"

for stat in "${STATS[@]}"; do
    printf "%-7s | " "$stat"
    for ts in "${TEST_SEASONS[@]}"; do
        train="${TRAIN_FOR[$ts]}"
        if [ -z "$train" ]; then
            printf "%-9s " "no-train"
            continue
        fi
        train_tag=$(make_train_tag "$train")
        pattern="audit_runs/*/skill_backtest_${stat}_phase4_v4_quadratic_tq_g_${train_tag}__${ts}"
        existing=$(ls -d $pattern 2>/dev/null | head -1)
        count_total=$((count_total+1))
        if [ -n "$existing" ]; then
            printf "%-9s " "✓"
            count_existing=$((count_existing+1))
        else
            printf "%-9s " "MISSING"
            count_missing=$((count_missing+1))
        fi
    done
    echo
done
echo
echo "Total: $count_total cells. Existing: $count_existing. Missing: $count_missing."
echo

# Confirm before firing
if [ "${1:-}" != "--fire" ]; then
    echo "Dry run mode. To fire missing fits: bash $0 --fire"
    exit 0
fi

echo "Firing missing fits sequentially..."
echo

for ts in "${TEST_SEASONS[@]}"; do
    train="${TRAIN_FOR[$ts]}"
    if [ -z "$train" ]; then
        echo "SKIP $ts — no train data (waiting on fetcher for older box scores)"
        continue
    fi
    train_tag=$(make_train_tag "$train")

    for stat in "${STATS[@]}"; do
        pattern="audit_runs/*/skill_backtest_${stat}_phase4_v4_quadratic_tq_g_${train_tag}__${ts}"
        existing=$(ls -d $pattern 2>/dev/null | head -1)
        if [ -n "$existing" ]; then
            echo "[$(date '+%H:%M:%S')] SKIP $stat/$ts — exists at $existing"
            continue
        fi

        log_file="$LOG_DIR/${stat}_${ts}_$(date '+%Y%m%d_%H%M%S').log"
        echo "[$(date '+%H:%M:%S')] FIRING $stat / $ts (log: $log_file)"

        python -u -m cli.backtest_skill_volume \
            --stat "$stat" \
            --quadratic-age --team-quality --gravity \
            --train $train \
            --test "$ts" \
            --max-players 200 \
            --chains 2 \
            --iter-warmup 400 \
            --iter-sampling 400 \
            > "$log_file" 2>&1

        if [ $? -eq 0 ]; then
            echo "[$(date '+%H:%M:%S')] DONE $stat / $ts"
            count_fired=$((count_fired+1))
        else
            echo "[$(date '+%H:%M:%S')] FAILED $stat / $ts — see $log_file"
            count_failed=$((count_failed+1))
        fi
    done
done

echo
echo "=== Campaign complete ==="
echo "Fired: $count_fired. Failed: $count_failed."
echo
echo "Next: python scripts/cross_season_full_validation.py"
