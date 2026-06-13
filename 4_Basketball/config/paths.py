"""Filesystem paths for the NBA Projections project.

All disk locations are centralised here so the rest of the code never hard-codes
absolute paths. Override via env vars where useful.
"""
from __future__ import annotations

import os
from pathlib import Path


# Project root resolved from this file's location (two levels up: config/paths.py)
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]


# nba_api responses cached here. Parquet for tabular endpoints, JSON for single-shot
# metadata. TTL-keyed by filename suffix (see ingestion/cache.py).
NBA_CACHE_DIR: Path = Path(os.environ.get("NBA_PROJ_CACHE_DIR", PROJECT_ROOT / ".nba_cache"))


# Long-term parquet store of cleaned, schema-validated historical data.
# Distinct from NBA_CACHE_DIR (raw responses). Validation runs between the two.
DATA_PARQUET_DIR: Path = PROJECT_ROOT / "data" / "parquet"


# Where the embedded-audit harness writes its run outputs.
AUDIT_RUNS_DIR: Path = PROJECT_ROOT / "audit_runs"


# College / international source data — populated in Phase 1, consumed in Phase 5
# (rookie model). Stored separately because schema and lifecycle differ from
# nba_api cached data.
COLLEGE_DATA_DIR: Path = PROJECT_ROOT / "data" / "college"


# Wonka Resolve audit folder — used as external validation harness per
# audit_agent_spec.md and the project memory entry. Read-only from this project.
WONKA_AUDIT_DIR: Path = Path(os.environ.get("WONKA_AUDIT_DIR", "D:/Wonka Resolve/audit"))
WONKA_AUDIT_PARSED_DIR: Path = WONKA_AUDIT_DIR / "data" / "parsed"


# Output artifacts (Phase 7). Created by the formatters; cleared by `make clean`.
OUTPUT_DIR: Path = PROJECT_ROOT / "output"


DARKO_RAW_DIR: Path = PROJECT_ROOT / "data" / "raw" / "darko"
DEBUG_DIR: Path = PROJECT_ROOT / "data" / "debug"


# Cleaning the Glass — subscriber data + persisted auth state
CTG_RAW_DIR: Path = PROJECT_ROOT / "data" / "raw" / "ctg"
CTG_AUTH_STATE_PATH: Path = CTG_RAW_DIR / "auth_state.json"


# Yahoo Fantasy — OAuth tokens persisted here after one-time browser authorize.
# OAuth credentials (client_id / client_secret) live in env vars; loaded from
# Wonka's .env as a fallback when this project's .env is absent.
YAHOO_AUTH_DIR: Path = PROJECT_ROOT / "data" / "raw" / "yahoo"
YAHOO_TOKENS_PATH: Path = YAHOO_AUTH_DIR / "tokens.json"


def ensure_dirs() -> None:
    """Create all expected directories if missing. Idempotent. Safe to call at
    every CLI entrypoint."""
    for d in (NBA_CACHE_DIR, DATA_PARQUET_DIR, AUDIT_RUNS_DIR,
              COLLEGE_DATA_DIR, OUTPUT_DIR, DARKO_RAW_DIR, DEBUG_DIR,
              CTG_RAW_DIR, YAHOO_AUTH_DIR):
        d.mkdir(parents=True, exist_ok=True)
