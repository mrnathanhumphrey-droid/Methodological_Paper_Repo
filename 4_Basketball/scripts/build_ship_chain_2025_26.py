"""Build _2025_26 variants of the v6.1 ship chain.

Reads each scratch/_ship_v*.py and the v1/v2 unified scripts, applies
mechanical substitutions, writes _2025_26.py copies. Originals are not
modified.

Substitutions:
  - "2023-24" -> "2025-26"        (TEST_SEASON references)
  - "2022-23" -> "2024-25"        (PRIOR_SEASON references)
  - TARGET_YEAR = 2023 -> 2025
  - PRIOR_SEASON = "..." -> "2024-25" (defensive double-set)
  - audit_runs/unified_ship_vN/  -> audit_runs/unified_ship_vN_2025_26/
  - TRAIN_SEASONS list extended by 2023-24 + 2024-25
  - mpg_career_weighted/mpg_prior_2023-24.csv -> graceful skip in v2

After-build behavior:
  - v1 (_unified_projection_ship_2025_26.py): reads v4-lite audits filtered
    by latest mtime (auto-picks 25-26 fits since they're newest). Falls back
    naturally for shot_zone/fta_direct/ftm_compose since those alt-models
    don't exist for 25-26.
  - v2: patched to fall back to mpg_naive when career-weighted prior is
    missing.
  - v3..v6: chain operates as before, just with 25-26 paths.

Usage:
    python scripts/build_ship_chain_2025_26.py
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import re

REPO = Path(".").resolve()
SCRATCH = REPO / "scratch"

SHIP_FILES = [
    "_unified_projection_ship.py",   # v1
    "_unified_ship_v2.py",           # v2
    "_ship_v3_career_3pct_blend.py", # v3
    "_ship_v4_career_3pa_blend.py",  # v4
    "_ship_v5_pts_authoritative.py", # v5
    "_ship_v6_full_consistency.py",  # v6
]


def substitute(content: str, fname: str) -> str:
    out = content

    # 1. Season string substitutions (do TEST first, then PRIOR — order matters
    # because "2023-24" is BOTH a test season for the 23-24 ship AND a train
    # season for our 25-26 ship; we want the test→test mapping).
    out = out.replace('"2023-24"', '"2025-26"')
    out = out.replace("'2023-24'", "'2025-26'")
    out = out.replace("_2023-24.csv", "_2025-26.csv")
    out = out.replace("validation_2023-24.csv", "validation_2025-26.csv")
    out = out.replace("mpg_prior_2023-24.csv", "mpg_prior_2025-26.csv")

    out = out.replace('"2022-23"', '"2024-25"')
    out = out.replace("'2022-23'", "'2024-25'")

    # 2. Target year integer
    out = out.replace("TARGET_YEAR = 2023", "TARGET_YEAR = 2025")

    # 3. Train seasons list — append 2023-24 + 2024-25 to existing list
    #    Match: ["2019-20", "2020-21", "2021-22", "2022-23"]  (post-substitution this
    #    has already become ["2019-20", "2020-21", "2021-22", "2024-25"] due to step 1
    #    so we need to be careful — actually wait, step 1 only changes "2022-23" inside
    #    DOUBLE quotes that ALSO have 2022-23, but the TRAIN_SEASONS list IS such a
    #    thing. So after step 1: ["2019-20", "2020-21", "2021-22", "2024-25"]. We want
    #    ["2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25"].
    #    Easier: pre-empt step 1 effects on TRAIN_SEASONS by replacing the whole list.
    out = re.sub(
        r'TRAIN_SEASONS\s*=\s*\[\s*"2019-20"\s*,\s*"2020-21"\s*,\s*"2021-22"\s*,\s*"2024-25"\s*\]',
        'TRAIN_SEASONS = ["2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]',
        out,
    )

    # 4. Audit dir paths — read paths from upstream and SAVE_DIR. Use 2025_26
    #    suffix (underscore for valid Python ident-friendly dir name).
    for vN in ("unified_ship_v1", "unified_ship_v2", "unified_ship_v3",
                "unified_ship_v4", "unified_ship_v5", "unified_ship_v6"):
        out = out.replace(f'"{vN}"', f'"{vN}_2025_26"')
        out = out.replace(f'/{vN}/', f'/{vN}_2025_26/')
        out = out.replace(f'\\{vN}\\', f'\\{vN}_2025_26\\')

    # 5. v2-specific patch — graceful fallback for missing mpg_career_weighted prior.
    if fname == "_unified_ship_v2.py":
        # Replace the unconditional read with try/except.
        out = out.replace(
            'prior = pd.read_csv("audit_runs/mpg_career_weighted/mpg_prior_2025-26.csv")\n'
            '    prior["nba_api_id"] = prior["nba_api_id"].astype(int)\n\n'
            '    df = v1.merge(prior[["nba_api_id", "mpg_prior_adj"]], on="nba_api_id", how="left")',
            'try:\n'
            '        prior = pd.read_csv("audit_runs/mpg_career_weighted/mpg_prior_2025-26.csv")\n'
            '        prior["nba_api_id"] = prior["nba_api_id"].astype(int)\n'
            '        df = v1.merge(prior[["nba_api_id", "mpg_prior_adj"]], on="nba_api_id", how="left")\n'
            '    except FileNotFoundError:\n'
            '        print("v2: mpg_prior_2025-26.csv not found — falling back to mpg_naive (no career-weighted blend)")\n'
            '        df = v1.copy()\n'
            '        df["mpg_prior_adj"] = df["mpg_naive"]'
        )

    # 6. v1-specific patch — _v4_audit picks latest by mtime, but old 23-24 audits
    #    might still be the chosen audit if they're somehow more recent. Make it
    #    filter by test_season suffix in dir name.
    if fname == "_unified_projection_ship.py":
        # Patch the audit-finder to filter by test_season suffix.
        out = out.replace(
            'if f"_{stat}_phase4_v4" not in sub.name: continue',
            'if f"_{stat}_phase4_v4" not in sub.name: continue\n'
            '            if not sub.name.endswith(f"__{TEST_SEASON}"): continue'
        )

    return out


def main():
    for fname in SHIP_FILES:
        src = SCRATCH / fname
        if not src.exists():
            print(f"  SKIP missing: {src}")
            continue
        dst = SCRATCH / fname.replace(".py", "_2025_26.py")
        original = src.read_text(encoding="utf-8")
        modified = substitute(original, fname)
        dst.write_text(modified, encoding="utf-8")
        size = len(modified.splitlines())
        print(f"  WROTE {dst.name}  ({size} lines)")
    print("\nDone. Run order:")
    for f in SHIP_FILES:
        v = f.replace(".py", "_2025_26.py")
        print(f"  python -m scratch.{v.replace('.py', '')}")


if __name__ == "__main__":
    main()
