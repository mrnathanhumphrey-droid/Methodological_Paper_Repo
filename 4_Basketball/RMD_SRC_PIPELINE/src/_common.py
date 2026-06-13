"""
RMD-SRC NBA pipeline — shared discipline guards.

All step scripts import `verify_sha_lock()` at entry. The guard reads
RMD_SRC_PIPELINE/SHA_LOCK.txt and refuses to proceed if the recorded
pre-reg commit does not match the file's current content-hash in the
working tree. This enforces the pre-registration commit-SHA discipline
mechanically: if anyone amends the locked pre-reg without re-locking,
the pipeline halts.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(r"D:/NBA Projections")
PIPE_ROOT = REPO_ROOT / "RMD_SRC_PIPELINE"
SHA_LOCK = PIPE_ROOT / "SHA_LOCK.txt"
PRE_REG = PIPE_ROOT / "PRE_REG_NBA_RMD_SRC_FULL_LOCKED.md"
RESULTS = PIPE_ROOT / "results"

# Locked partition axes (paper-canon, NBA-specific, §2.2 of pre-reg).
POSITION_BUCKETS = ("Center", "Forward", "Guard")

# Inclusive Test 1 classifier — metadata strings -> position bucket.
# Empty / unknown -> Guard (the catch-all per §2.2).
POSITION_MAP = {
    "Center":         "Center",
    "Center-Forward": "Center",
    "Forward-Center": "Center",
    "Forward":        "Forward",
    "Forward-Guard":  "Forward",
    "Guard-Forward":  "Forward",
    "Guard":          "Guard",
}

# Years-pro buckets (matches v6.1 LOCKED classifier).
YEARS_PRO_BUCKETS = ("Rookie", "Soph_Early", "Mid", "Deep_vet")
def years_pro_bucket(years_pro: int) -> str:
    if years_pro <= 1:
        return "Rookie"
    if years_pro <= 5:
        return "Soph_Early"
    if years_pro <= 12:
        return "Mid"
    return "Deep_vet"

# Role-cohort buckets.
# v1.0 (usage-tier): pre-reg §2.2.
ROLE_COHORT_BUCKETS_USG = ("High_usage", "Mid_usage", "Low_usage")
ROOKIE_ROLE_DEFAULT_USG = "Mid_usage"

def role_cohort_bucket_usg(usg_pct: float | None) -> str:
    if usg_pct is None:
        return ROOKIE_ROLE_DEFAULT_USG
    if usg_pct >= 25.0:
        return "High_usage"
    if usg_pct >= 15.0:
        return "Mid_usage"
    return "Low_usage"

# v1.1 amendment (MPG-tier): amendment §2.2.
ROLE_COHORT_BUCKETS_MPG = ("Starter", "Rotation", "Bench")

def role_cohort_bucket_mpg(mean_mpg: float) -> str:
    # No defaulting: mean MPG is well-defined for every qualifying player.
    if mean_mpg >= 28.0:
        return "Starter"
    if mean_mpg >= 18.0:
        return "Rotation"
    return "Bench"

# Back-compat alias for any code still importing the v1.0-only name.
ROLE_COHORT_BUCKETS = ROLE_COHORT_BUCKETS_USG
ROOKIE_ROLE_DEFAULT = ROOKIE_ROLE_DEFAULT_USG
role_cohort_bucket = role_cohort_bucket_usg

# Time axis — locked seasons.
TRAIN_SEASONS = ("2019-20", "2020-21", "2021-22", "2022-23", "2023-24")
HOLDOUT_SEASONS = ("2024-25", "2025-26")
ALL_SEASONS = TRAIN_SEASONS + HOLDOUT_SEASONS

# Observable column names → label used downstream.
OBSERVABLES = ("PTS_per36", "REB_per36", "AST_per36", "BLK_per36")

# Qualification.
MIN_GAMES_PER_SEASON = 20
MIN_MPG_PER_SEASON = 10.0

# Sparse-cell collapse rule.
SPARSE_TOTAL_FLOOR = 50          # < 50 player-seasons over all 7 seasons -> collapse
SPARSE_PER_SEASON_FLOOR = 5      # any single season with < 5 -> collapse


def season_start_year(s: str) -> int:
    """'2019-20' -> 2019."""
    return int(s.split("-")[0])


def ctg_season_for_nba(nba_season: str) -> int:
    """NBA '2019-20' -> CTG int season 2020 (the season's end-year)."""
    return season_start_year(nba_season) + 1


def _verify_one_locked_doc(step_name: str, doc_rel_path: str,
                            recorded_sha: str) -> None:
    """Verify (a) the recorded SHA matches the latest commit on the doc path,
    and (b) the doc has no uncommitted edits in the working tree."""
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "log", "-1", "--format=%H", "--",
         doc_rel_path],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit(f"[{step_name}] git log failed for {doc_rel_path}: "
                  f"{out.stderr.strip()}")
    head_sha = out.stdout.strip()
    if head_sha != recorded_sha:
        sys.exit(
            f"[{step_name}] SHA mismatch on {doc_rel_path}.\n"
            f"  SHA_LOCK.txt records: {recorded_sha}\n"
            f"  Latest commit on path: {head_sha}\n"
            f"  Locked doc has been amended without re-locking. Halting."
        )
    diff = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--quiet", "HEAD", "--",
         doc_rel_path], capture_output=True,
    )
    if diff.returncode != 0:
        sys.exit(
            f"[{step_name}] Locked doc {doc_rel_path} has uncommitted edits "
            "in working tree. Either revert or write a new lock."
        )


def verify_sha_lock(step_name: str, arm: str = "usg") -> dict[str, str]:
    """Read SHA_LOCK.txt; verify the recorded SHA(s) match HEAD on their
    respective locked doc paths.
    - arm='usg' verifies only the v1.0 pre-reg SHA.
    - arm='mpg' verifies both the v1.0 pre-reg SHA AND the v1.1 amendment SHA.
    Returns {'v1.0': sha, 'v1.1': sha or ''} for audit logging.
    """
    if arm not in {"usg", "mpg", "usg_adj", "mpg_adj"}:
        sys.exit(f"[{step_name}] verify_sha_lock: unknown arm={arm!r}")
    if not SHA_LOCK.exists():
        sys.exit(f"[{step_name}] SHA_LOCK.txt missing. Lock the pre-reg first.")

    text = SHA_LOCK.read_text(encoding="utf-8")

    # Match both "Commit SHA:" entries (v1.0 first, v1.1 second if present).
    shas = re.findall(r"Commit SHA:\s*([0-9a-f]{40})", text)
    if not shas:
        sys.exit(f"[{step_name}] SHA_LOCK.txt malformed (no 40-char SHA).")
    v10_sha = shas[0]
    _verify_one_locked_doc(step_name,
        "RMD_SRC_PIPELINE/PRE_REG_NBA_RMD_SRC_FULL_LOCKED.md", v10_sha)

    v11_sha = ""
    if arm == "mpg":
        if len(shas) < 2:
            sys.exit(
                f"[{step_name}] arm=mpg requested but SHA_LOCK.txt records "
                "only one SHA. Lock the v1.1 amendment first."
            )
        v11_sha = shas[1]
        _verify_one_locked_doc(step_name,
            "RMD_SRC_PIPELINE/AMENDMENT_v1.1_MPG_TIER_PARALLEL_ARM_LOCKED.md",
            v11_sha)
        print(f"[{step_name}] SHA-lock verified: "
              f"v1.0={v10_sha[:7]}, v1.1={v11_sha[:7]}")
    else:
        print(f"[{step_name}] SHA-lock verified: v1.0={v10_sha[:7]}")
    return {"v1.0": v10_sha, "v1.1": v11_sha}


def write_artifact_with_hash(path: Path, payload_bytes: bytes) -> str:
    """Write bytes to `path` and return the SHA256 of the content. The hash
    is appended to results/MANIFEST.txt for audit."""
    RESULTS.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload_bytes)
    digest = hashlib.sha256(payload_bytes).hexdigest()
    manifest = RESULTS / "MANIFEST.txt"
    line = f"{digest}  {path.relative_to(PIPE_ROOT)}\n"
    with manifest.open("a", encoding="utf-8") as f:
        f.write(line)
    return digest
