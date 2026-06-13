"""
v1.2 adjudication prep: build the 230-player profile payload that the
agent fleet consumes.

Per locked amendment v1.2 (SHA 1bfdb4c) §2.1:
  - Scope = exactly 230 players: 196 with multi-bucket Yahoo eligibility
    AND 34 with single-bucket Yahoo that disagrees with metadata.

Output (under RMD_SRC_PIPELINE/results/):
  adjudication_profiles_v12.json   list of 230 profile dicts
    Each: {nba_api_id, name, metadata_position, metadata_bucket_v1,
           yahoo_eligible_positions, yahoo_primary_position,
           height_inches, debut_year, last_seen_season,
           career_avg_REB_per36, career_avg_AST_per36,
           career_avg_BLK_per36, career_avg_FG3M_per36}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _common import POSITION_MAP, RESULTS, TRAIN_SEASONS, ALL_SEASONS, verify_sha_lock

DATA = Path(r"D:/NBA Projections/data/parquet")


def parse_ye(x):
    if x is None or pd.isna(x):
        return None
    s = str(x).strip()
    if s == "" or s == "None":
        return None
    return tuple(sorted(p.strip() for p in s.split(",") if p.strip()))


# Yahoo label -> v1.0 inclusive Test 1 position bucket.
LBL2B = {"C": "Center", "PF": "Forward", "SF": "Forward",
         "PG": "Guard", "SG": "Guard", "G": "Guard"}


def implied_buckets(ye_tuple) -> set:
    if ye_tuple is None:
        return set()
    return {LBL2B[l] for l in ye_tuple if l in LBL2B}


def main() -> int:
    sha = verify_sha_lock("adjudicate_v12_prep", arm="usg_adj")
    print(f"v1.0 SHA: {sha['v1.0']}")
    print(f"v1.1 SHA must exist (not checked here but enforced downstream)")
    print(f"v1.2 SHA: 1bfdb4c (recorded by SHA_LOCK.txt)")

    print("\n--- Loading metadata + qualifying union ---")
    m = pd.read_parquet(DATA / "player_metadata_enriched.parquet")
    p0u = pd.read_parquet(RESULTS / "P0_partition_usg.parquet")
    qual_ids = set(p0u["nba_api_id"].astype(int))
    mq = m[m["nba_api_id"].isin(qual_ids)].copy()
    print(f"  qualifying-union players: {len(mq)}")

    mq["ye"] = mq["yahoo_eligible_positions"].apply(parse_ye)
    mq["buckets"] = mq["ye"].apply(implied_buckets)
    mq["n_buckets"] = mq["buckets"].apply(len)
    mq["pos_bucket"] = mq["position"].map(POSITION_MAP).fillna("Guard")

    # Multi-bucket targets (Yahoo implies >= 2 of {Center, Forward, Guard}).
    multi = mq[mq["n_buckets"] >= 2].copy()
    # Single-bucket Yahoo disagrees with metadata.
    single = mq[mq["n_buckets"] == 1].copy()
    single["ye_single"] = single["buckets"].apply(lambda s: list(s)[0])
    disagree = single[single["ye_single"] != single["pos_bucket"]].copy()

    print(f"  multi-bucket Yahoo targets: {len(multi)}")
    print(f"  single-bucket Yahoo disagreements: {len(disagree)}")

    targets = pd.concat([multi, disagree], ignore_index=True)
    print(f"  total adjudication targets: {len(targets)}")

    # ----- Per-player career averages in the 2019-26 window -----
    print("\n--- Computing career per-36 averages for target players ---")
    bs = pd.read_parquet(DATA / "historical_box_scores.parquet",
                          columns=["nba_api_id", "season", "season_type",
                                   "minutes", "PTS", "REB", "AST", "BLK",
                                   "FG3M"])
    bs = bs[(bs["season"].isin(ALL_SEASONS))
            & (bs["season_type"] == "Regular Season")
            & (bs["minutes"] > 0)
            & (bs["nba_api_id"].isin(targets["nba_api_id"]))].copy()
    bs["REB36"] = bs["REB"] * 36.0 / bs["minutes"]
    bs["AST36"] = bs["AST"] * 36.0 / bs["minutes"]
    bs["BLK36"] = bs["BLK"] * 36.0 / bs["minutes"]
    bs["FG3M36"] = bs["FG3M"] * 36.0 / bs["minutes"]
    career = (bs.groupby("nba_api_id")
                .agg(REB36=("REB36", "mean"), AST36=("AST36", "mean"),
                     BLK36=("BLK36", "mean"), FG3M36=("FG3M36", "mean"))
                .reset_index())

    targets = targets.merge(career, on="nba_api_id", how="left")
    n_no_career = int(targets["REB36"].isna().sum())
    print(f"  players with computed career averages: "
          f"{len(targets) - n_no_career} / {len(targets)}")

    # ----- Build profile JSON -----
    def last_seen(row):
        ls = row["last_seen_season"]
        if isinstance(ls, str): return ls
        if hasattr(ls, "tolist"):
            arr = ls.tolist()
            return arr[-1] if arr else None
        return None

    def ye_for_prompt(t):
        return ",".join(t) if t else ""

    profiles = []
    for _, r in targets.iterrows():
        profiles.append({
            "nba_api_id": int(r["nba_api_id"]),
            "name": str(r["name"]),
            "metadata_position": str(r["position"])
                                  if pd.notna(r["position"]) else "",
            "metadata_bucket_v1": str(r["pos_bucket"]),
            "yahoo_eligible_positions": ye_for_prompt(r["ye"]),
            "yahoo_primary_position": (str(r["yahoo_primary_position"])
                                        if pd.notna(r["yahoo_primary_position"])
                                        else ""),
            "height_inches": (int(r["height_inches"])
                               if pd.notna(r["height_inches"]) else None),
            "debut_year": (int(r["debut_year"])
                            if pd.notna(r["debut_year"]) else None),
            "last_seen_season": last_seen(r),
            "career_avg_REB_per36": (round(float(r["REB36"]), 2)
                                      if pd.notna(r["REB36"]) else None),
            "career_avg_AST_per36": (round(float(r["AST36"]), 2)
                                      if pd.notna(r["AST36"]) else None),
            "career_avg_BLK_per36": (round(float(r["BLK36"]), 2)
                                      if pd.notna(r["BLK36"]) else None),
            "career_avg_FG3M_per36": (round(float(r["FG3M36"]), 2)
                                       if pd.notna(r["FG3M36"]) else None),
        })

    # Stable ordering (by nba_api_id) for reproducibility.
    profiles.sort(key=lambda p: p["nba_api_id"])

    out_path = RESULTS / "adjudication_profiles_v12.json"
    out_path.write_text(json.dumps(profiles, indent=2, ensure_ascii=False),
                         encoding="utf-8")
    print(f"\n  -> {out_path.name}")
    print(f"  profile count: {len(profiles)}")

    # Sanity preview.
    print("\n--- First 5 profiles (sanity) ---")
    for p in profiles[:5]:
        print(f"  {p['name']:<25} | bucket_v1={p['metadata_bucket_v1']:<8} | "
              f"yahoo={p['yahoo_eligible_positions']:<14} | "
              f"H={p['height_inches']} | REB/36={p['career_avg_REB_per36']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
