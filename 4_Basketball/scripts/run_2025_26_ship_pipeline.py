"""End-to-end orchestrator for the 25-26 forward ship.

Run this AFTER cli.run_v4lite_overnight (forward-mode 25-26) has completed.
Walks the v1 -> v2 -> v3 -> v4 -> v5 -> v6 -> v6.1-offsets -> Wonka chain.

Each step is a separate subprocess so failures are isolated and log lines
are clean.

Usage:
    python scripts/run_2025_26_ship_pipeline.py
    python scripts/run_2025_26_ship_pipeline.py --skip-existing  # don't redo completed steps
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(".").resolve()

STEPS = [
    # (label, module, output_artifact_to_check_for_skip)
    ("v0 cohort widening", "scripts.cohort_widening_2025_26",
     "audit_runs/cohort_widening_v0_2025_26/per_player_projections.csv"),
    ("v1 unified", "scratch._unified_projection_ship_2025_26",
     "audit_runs/unified_ship_v1_2025_26/per_player_projections_2025-26.csv"),
    ("v2 mpg-blend", "scratch._unified_ship_v2_2025_26",
     "audit_runs/unified_ship_v2_2025_26/per_player_projections_2025-26.csv"),
    ("v3 3pct blend", "scratch._ship_v3_career_3pct_blend_2025_26",
     "audit_runs/unified_ship_v3_2025_26/per_player_projections_2025-26.csv"),
    ("v4 3pa blend", "scratch._ship_v4_career_3pa_blend_2025_26",
     "audit_runs/unified_ship_v4_2025_26/per_player_projections_2025-26.csv"),
    ("v5 PTS-authoritative", "scratch._ship_v5_pts_authoritative_2025_26",
     "audit_runs/unified_ship_v5_2025_26/per_player_projections_2025-26.csv"),
    ("v6 full consistency", "scratch._ship_v6_full_consistency_2025_26",
     "audit_runs/unified_ship_v6_2025_26/per_player_projections_2025-26.csv"),
    ("v6.1 LOCKED offsets", "scripts.apply_v6_1_locked_offsets_2025_26",
     "audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv"),
    ("v6.2 de-shrinkage", "scripts.apply_deshrinkage_2025_26",
     "audit_runs/unified_ship_v6_2_deshrunk_2025_26/per_player_projections_2025-26.csv"),
    ("Wonka writer (v1.1 rookie-aware)", "scripts.write_wonka_csv_2025_26_v11",
     None),  # destination is outside repo, always run
]


def run_step(label: str, module: str, log) -> bool:
    log(f"==> {label}  ({module})")
    t0 = time.time()
    proc = subprocess.run(
        [sys.executable, "-m", module],
        cwd=str(REPO),
        capture_output=False,  # let it stream
    )
    elapsed = time.time() - t0
    if proc.returncode != 0:
        log(f"  FAILED (exit {proc.returncode}, {elapsed:.1f}s)")
        return False
    log(f"  OK ({elapsed:.1f}s)")
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--skip-existing", action="store_true",
                   help="Skip steps whose output artifact already exists.")
    args = p.parse_args()

    def log(s):
        print(s, flush=True)

    log(f"25-26 ship pipeline @ {REPO}")
    log("=" * 70)

    for label, module, artifact in STEPS:
        if args.skip_existing and artifact and (REPO / artifact).exists():
            log(f"SKIP {label} — artifact exists: {artifact}")
            continue
        ok = run_step(label, module, log)
        if not ok:
            log("Halting pipeline due to failure.")
            return 1

    log("=" * 70)
    log("Pipeline complete.")
    log("Wonka CSV: D:/Wonka Resolve/audit/data/parsed/nba_projections_projections.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
