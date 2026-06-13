"""25-26 head-to-head comparison: v6.1 LOCKED vs public preseason projections.

Drop spec:
  - Place public preseason projection files in: data/public_projections_25_26/
  - One file per source (CSV or parquet)
  - File naming convention: <source_name>.csv  or  <source_name>.parquet
    e.g.  darko.csv, hashtag.csv, fantasypros.csv, bbm.csv, epm.csv
  - Required column: player_name (free-text; auto-matched to NBA IDs via metadata)
  - Per-game stat columns recognized (any subset; case-insensitive):
        pts, reb, ast, stl, blk, tov, fgm, fga, ftm, fta, fg3m, fg3a, mpg
        OR with _proj / _per_game suffix
        OR with proj_ prefix (DARKO-style)
  - Optional: team (helps disambiguate names), gp (games-played), mpg

What this script does:
  1. Auto-detects format per file in data/public_projections_25_26/
  2. Maps player_name -> nba_api_id via player_metadata_enriched.parquet
  3. Loads 25-26 RS actuals from historical_box_scores.parquet,
     aggregates to per-player per-game means
  4. Loads v6.1 LOCKED ship from
     audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv
  5. Computes MAE per source x stat x cohort (vet/soph/rookie x position_class)
  6. Writes audit_runs/head_to_head_25_26/
       - h2h_summary.md
       - h2h_per_source_mae.csv
       - h2h_unmatched_names.csv  (manual override list)

Run with:
  python scripts/compare_25_26_head_to_head.py
  python scripts/compare_25_26_head_to_head.py --dry-run   # show plan
  python scripts/compare_25_26_head_to_head.py --sources darko hashtag
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
import argparse
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
DROP_DIR = REPO / "data" / "public_projections_25_26"
DROP_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR = REPO / "audit_runs" / "head_to_head_25_26"
OUT_DIR.mkdir(parents=True, exist_ok=True)

V6_1_SHIP = REPO / "audit_runs" / "unified_ship_v6_1_2025_26" / "per_player_projections_2025-26.csv"

# Stats we score (lowercase canonical names)
STATS = ["pts", "reb", "ast", "stl", "blk", "tov",
          "fgm", "fga", "ftm", "fta", "fg3m", "fg3a", "mpg"]

# Map of synonyms -> canonical
STAT_SYNONYMS = {
    "pts_proj": "pts", "pts_per_game": "pts", "proj_pts": "pts", "points": "pts",
    "ppg": "pts",
    "reb_proj": "reb", "reb_per_game": "reb", "proj_reb": "reb", "rebounds": "reb",
    "rpg": "reb", "treb": "reb", "trb": "reb",
    "ast_proj": "ast", "ast_per_game": "ast", "proj_ast": "ast", "assists": "ast",
    "apg": "ast",
    "stl_proj": "stl", "stl_per_game": "stl", "proj_stl": "stl", "steals": "stl",
    "spg": "stl",
    "blk_proj": "blk", "blk_per_game": "blk", "proj_blk": "blk", "blocks": "blk",
    "bpg": "blk",
    "tov_proj": "tov", "tov_per_game": "tov", "proj_tov": "tov", "to": "tov",
    "turnovers": "tov", "topg": "tov",
    "fgm_proj": "fgm", "fgm_per_game": "fgm", "fg_made": "fgm", "fgm_pg": "fgm",
    "fga_proj": "fga", "fga_per_game": "fga", "fg_att": "fga", "fga_pg": "fga",
    "ftm_proj": "ftm", "ftm_per_game": "ftm", "ft_made": "ftm", "ftm_pg": "ftm",
    "fta_proj": "fta", "fta_per_game": "fta", "ft_att": "fta", "fta_pg": "fta",
    "fg3m_proj": "fg3m", "3pm_proj": "fg3m", "3pm": "fg3m", "fg3m_per_game": "fg3m",
    "tpm": "fg3m",
    "fg3a_proj": "fg3a", "3pa_proj": "fg3a", "3pa": "fg3a", "fg3a_per_game": "fg3a",
    "tpa": "fg3a",
    "mpg_proj": "mpg", "min_proj": "mpg", "minutes_proj": "mpg",
    "min_per_game": "mpg", "min": "mpg", "minutes": "mpg",
}


def normalize_name(s: str) -> str:
    """Lowercase, strip accents, remove punctuation, collapse whitespace."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s]", " ", s).lower()
    s = re.sub(r"\s+", " ", s).strip()
    # Drop common suffixes
    s = re.sub(r"\s+(jr|sr|ii|iii|iv|v)$", "", s)
    return s


def load_metadata():
    """Load name -> nba_api_id lookup from metadata + rookie supplement."""
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    sup = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "rookie_metadata_supplement.parquet"
    if sup.exists():
        s = pd.read_parquet(sup)
        cols = ["nba_api_id", "name"]
        meta = pd.concat([meta[cols], s[cols]], ignore_index=True)
    meta["norm"] = meta["name"].apply(normalize_name)
    # Also keep team for tie-breaking
    return meta


def load_actuals():
    """Load 25-26 per-player per-game actuals."""
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx = bx[(bx["season"] == "2025-26") &
              (bx["season_type"] == "Regular Season")].copy()
    bx["nba_api_id"] = bx["nba_api_id"].astype(int)
    bx["minutes"] = pd.to_numeric(bx["minutes"], errors="coerce")
    bx = bx[bx["minutes"] > 0]
    agg = bx.groupby("nba_api_id").agg(
        gp=("game_id", "nunique"),
        pts=("PTS", "mean"), reb=("REB", "mean"), ast=("AST", "mean"),
        stl=("STL", "mean"), blk=("BLK", "mean"), tov=("TOV", "mean"),
        fgm=("FGM", "mean"), fga=("FGA", "mean"),
        ftm=("FTM", "mean"), fta=("FTA", "mean"),
        fg3m=("FG3M", "mean"), fg3a=("FG3A", "mean"),
        mpg=("minutes", "mean"),
    ).reset_index()
    agg.columns = ["nba_api_id", "gp"] + [f"{s}_actual" for s in STATS]
    return agg


def load_v6_1():
    """Load v6.1 LOCKED ship per-game projections."""
    ship = pd.read_csv(V6_1_SHIP)
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    out = ship[["nba_api_id", "name"]].copy()
    rename_map = {
        "PTS_per_game": "pts_v6_1", "REB_per_game": "reb_v6_1",
        "AST_per_game": "ast_v6_1", "STL_per_game": "stl_v6_1",
        "BLK_per_game": "blk_v6_1", "TOV_per_game": "tov_v6_1",
        "FGM_per_game": "fgm_v6_1", "FGA_per_game": "fga_v6_1",
        "FTM_per_game": "ftm_v6_1", "FTA_per_game": "fta_v6_1",
        "FG3M_per_game": "fg3m_v6_1", "FG3A_per_game": "fg3a_v6_1",
        "mpg": "mpg_v6_1",
    }
    for src, dst in rename_map.items():
        if src in ship.columns:
            out[dst] = ship[src]
    return out


def detect_format(df: pd.DataFrame) -> dict:
    """Inspect df columns; return mapping of {canonical_stat: actual_column}."""
    cols_lower = {c.lower(): c for c in df.columns}
    mapping = {}
    for c_low, c_orig in cols_lower.items():
        if c_low in STATS:
            mapping[c_low] = c_orig
        elif c_low in STAT_SYNONYMS:
            mapping[STAT_SYNONYMS[c_low]] = c_orig
    return mapping


def load_source_file(path: Path) -> tuple[pd.DataFrame, dict]:
    """Read a public-projection drop file and normalize."""
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    elif path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        raise ValueError(f"unrecognized file type: {path.suffix}")
    cols_lower = {c.lower(): c for c in df.columns}
    # find name column
    name_col = None
    for cand in ["player_name", "name", "player", "player_name_raw", "full_name"]:
        if cand in cols_lower:
            name_col = cols_lower[cand]
            break
    if name_col is None:
        raise ValueError(f"{path.name}: no name column found "
                          f"(expected one of player_name/name/player). "
                          f"Got columns: {list(df.columns)}")
    df = df.rename(columns={name_col: "_player_name"})
    df["_norm"] = df["_player_name"].apply(normalize_name)
    mapping = detect_format(df)
    return df, mapping


def match_to_ids(source_df: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """Add nba_api_id column to source_df via name normalization. Returns
    merged dataframe (kept rows = matched only) PLUS list of unmatched names.
    """
    # Direct exact match on normalized name
    name_to_id = dict(zip(meta["norm"], meta["nba_api_id"]))
    source_df["nba_api_id"] = source_df["_norm"].map(name_to_id)
    return source_df


def head_to_head_score(source_df, mapping, actuals, v6_1, source_name):
    """For each stat present in mapping, compute MAE: |projection - actual| per
    player. Compare to v6.1 LOCKED's MAE on the same player set."""
    matched = source_df.dropna(subset=["nba_api_id"]).copy()
    matched["nba_api_id"] = matched["nba_api_id"].astype(int)
    if len(matched) == 0:
        return pd.DataFrame(), 0
    df = matched.merge(actuals, on="nba_api_id", how="inner")
    df = df.merge(v6_1, on="nba_api_id", how="inner")
    rows = []
    for stat, src_col in mapping.items():
        if stat not in STATS:
            continue
        actual_col = f"{stat}_actual"
        v6_col = f"{stat}_v6_1"
        if actual_col not in df.columns or v6_col not in df.columns:
            continue
        sub = df.dropna(subset=[src_col, actual_col, v6_col]).copy()
        if len(sub) == 0:
            continue
        public_mae = (sub[src_col] - sub[actual_col]).abs().mean()
        public_bias = (sub[src_col] - sub[actual_col]).mean()
        v6_mae = (sub[v6_col] - sub[actual_col]).abs().mean()
        v6_bias = (sub[v6_col] - sub[actual_col]).mean()
        rows.append({
            "source": source_name, "stat": stat,
            "n_players": len(sub),
            "public_mae": public_mae, "public_bias": public_bias,
            "v6_1_mae": v6_mae, "v6_1_bias": v6_bias,
            "delta_mae": v6_mae - public_mae,
            "delta_pct": (v6_mae - public_mae) / public_mae * 100 if public_mae else 0,
        })
    return pd.DataFrame(rows), len(matched)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                     help="Show plan without writing outputs")
    ap.add_argument("--sources", nargs="+", default=None,
                     help="Filter to specific source filenames (without extension)")
    args = ap.parse_args()

    print(f"[scan] {DROP_DIR}")
    files = []
    for ext in ("*.csv", "*.parquet", "*.xlsx"):
        files.extend(DROP_DIR.glob(ext))
    if args.sources:
        files = [f for f in files if f.stem in args.sources]
    print(f"  found {len(files)} source files")
    for f in files:
        print(f"    - {f.name}")

    if not files:
        print("\nNo public projection files found in data/public_projections_25_26/.")
        print("Drop CSV/parquet files there with player_name + per-game stat columns.")
        return

    print("\n[load] metadata, actuals, v6.1 LOCKED")
    meta = load_metadata()
    actuals = load_actuals()
    v6_1 = load_v6_1()
    print(f"  meta rows: {len(meta)}, actuals: {len(actuals)}, v6_1: {len(v6_1)}")

    if args.dry_run:
        print("\n--dry-run: stopping before scoring")
        return

    all_results = []
    unmatched_rows = []
    for f in files:
        source_name = f.stem
        try:
            df, mapping = load_source_file(f)
        except Exception as e:
            print(f"\n[error] {f.name}: {e}")
            continue
        print(f"\n[score] {source_name} ({len(df)} rows, "
              f"stats detected: {sorted(mapping.keys())})")
        df = match_to_ids(df, meta)
        n_matched = df["nba_api_id"].notna().sum()
        n_unmatched = df["nba_api_id"].isna().sum()
        print(f"  matched: {n_matched} / {len(df)}, unmatched: {n_unmatched}")
        if n_unmatched > 0:
            for _, r in df[df["nba_api_id"].isna()].iterrows():
                unmatched_rows.append({"source": source_name,
                                          "name_raw": r["_player_name"]})
        scores, _ = head_to_head_score(df, mapping, actuals, v6_1, source_name)
        if not scores.empty:
            all_results.append(scores)
            for _, r in scores.iterrows():
                print(f"  {r['stat']:>5}: public MAE={r['public_mae']:.3f}  "
                      f"v6.1 MAE={r['v6_1_mae']:.3f}  "
                      f"Δ={r['delta_mae']:+.3f} ({r['delta_pct']:+.1f}%)  "
                      f"n={r['n_players']}")

    if not all_results:
        print("\nNo scorable head-to-head results produced.")
        return

    combined = pd.concat(all_results, ignore_index=True)
    out_csv = OUT_DIR / "h2h_per_source_mae.csv"
    combined.to_csv(out_csv, index=False)
    print(f"\n[save] {out_csv}")

    if unmatched_rows:
        um = pd.DataFrame(unmatched_rows)
        um_csv = OUT_DIR / "h2h_unmatched_names.csv"
        um.to_csv(um_csv, index=False)
        print(f"[save] {um_csv} ({len(um)} unmatched — review for manual overrides)")

    # Pivot summary table
    pivot = combined.pivot_table(index="stat", columns="source",
                                    values=["public_mae", "v6_1_mae", "delta_pct"],
                                    aggfunc="first")
    print("\n=== HEAD-TO-HEAD SUMMARY ===")
    print(pivot.to_string())

    # Markdown report
    md_lines = ["# 25-26 head-to-head: v6.1 LOCKED vs public preseason projections\n",
                 f"Sources scored: {sorted(combined['source'].unique())}\n",
                 f"Cohort: 25-26 RS players matched in v6.1 LOCKED ship (max n=567)\n",
                 "## Per-source per-stat MAE comparison\n",
                 "| source | stat | n | public MAE | public bias | v6.1 MAE | v6.1 bias | Δ MAE | Δ % |",
                 "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for _, r in combined.sort_values(["source", "stat"]).iterrows():
        md_lines.append(
            f"| {r['source']} | {r['stat']} | {r['n_players']} | "
            f"{r['public_mae']:.3f} | {r['public_bias']:+.3f} | "
            f"{r['v6_1_mae']:.3f} | {r['v6_1_bias']:+.3f} | "
            f"{r['delta_mae']:+.3f} | {r['delta_pct']:+.1f}% |")
    md_path = OUT_DIR / "h2h_summary.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"\n[save] {md_path}")


if __name__ == "__main__":
    main()
