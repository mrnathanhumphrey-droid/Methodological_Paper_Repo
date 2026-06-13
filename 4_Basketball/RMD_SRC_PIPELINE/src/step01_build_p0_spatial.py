"""
RMD-SRC NBA — Step 0/1 SPATIAL re-axis: build the P0 partition.

Locked under PRE_REG_NBA_RMD_SRC_SPATIAL_LOCKED.md (SHA cd40b46, recorded in
SHA_LOCK.txt `## spatial re-axis`). Swaps the PRIMARY partition axis from
position to court-region-of-feast, holding years-pro x role-cohort (usage-tier)
verbatim from v1.0 by sourcing them from P0_partition_usg.parquet — so the
qualifying universe and the two secondary axes are byte-identical to v1.0 and
ONLY the primary axis changes.

Two arms:
  --arm off_feast  Rim / Paint / Perimeter by shot-location plurality
                   (shot_locations_player zones; Interior = Rim u Paint).
  --arm def_feast  RimProtector / Hybrid / Perimeter by within-season tercile
                   of rim-defense share = d_fga(lt6) / d_fga(overall).

Profile floors (locked §2.1): offense >= 50 total zone FGA; defense >= 3.0
defensive contests per game. Sub-floor (or no spatial profile) -> Profile-Sparse
residual bucket, reported and EXCLUDED from the cell partition. Traded players
summed across team rows before shares (dedup).

Inspects ONLY partition-side variables (shot-location shares, defensive-contest
distribution) + the v1.0 partition metadata. Does NOT touch PTS/REB/AST/BLK
moment-flow (the Step 2 quantity).

Outputs (under RMD_SRC_PIPELINE/results/) suffixed by arm:
  P0_partition_{arm}.parquet
  P0_collapse_map_{arm}.json
  P0_diagnostic_{arm}.md
  P0_position_overlap_{arm}.parquet   (region x v1.0 pos_bucket confusion)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _common import (
    ALL_SEASONS, SPARSE_PER_SEASON_FLOOR, SPARSE_TOTAL_FLOOR, RESULTS,
)

DATA = Path(r"D:/NBA Projections/data/parquet")

OFF_FGA = ["ra_fga", "paint_fga", "mid_fga", "lc3_fga", "rc3_fga", "ab3_fga"]
OFF_FLOOR_FGA = 50.0
DEF_FLOOR_CONTESTS_PG = 3.0

# ---- locked discipline gate ------------------------------------------------
SPATIAL_LOCK_SHA = "cd40b46"


def verify_spatial_lock() -> None:
    txt = (RESULTS.parent / "SHA_LOCK.txt").read_text(encoding="utf-8")
    if "## spatial re-axis" not in txt or SPATIAL_LOCK_SHA not in txt:
        sys.exit("DISCIPLINE GATE: spatial re-axis lock SHA not found in "
                 "SHA_LOCK.txt. No compute before lock.")
    print(f"  discipline gate OK — spatial lock SHA {SPATIAL_LOCK_SHA} present.")


# ---- region adjacency (linear), swapped in for POS_ADJ ---------------------
REGION_ADJ = {
    "off_feast": {"Rim": ["Paint"], "Paint": ["Rim", "Perimeter"],
                  "Perimeter": ["Paint"]},
    "def_feast": {"RimProtector": ["Hybrid"],
                  "Hybrid": ["RimProtector", "Perimeter"],
                  "Perimeter": ["Hybrid"]},
}
YP_ADJ = {"Rookie": ["Soph_Early"], "Soph_Early": ["Rookie", "Mid"],
          "Mid": ["Soph_Early", "Deep_vet"], "Deep_vet": ["Mid"]}
RC_ADJ_USG = {"High_usage": ["Mid_usage"],
              "Mid_usage": ["High_usage", "Low_usage"],
              "Low_usage": ["Mid_usage"]}
RC_ADJ_MPG = {"Starter": ["Rotation"], "Rotation": ["Starter", "Bench"],
              "Bench": ["Rotation"]}


def cell_neighbors(cid: str, region_adj: dict, rc_adj: dict) -> list[str]:
    """Per §2.2.3: prefer role-cohort axis, then years-pro, then region."""
    reg, yp, rc = cid.split("|")
    out: list[str] = []
    for nrc in rc_adj[rc]:
        out.append(f"{reg}|{yp}|{nrc}")
    for nyp in YP_ADJ[yp]:
        out.append(f"{reg}|{nyp}|{rc}")
    for nreg in region_adj.get(reg, []):
        out.append(f"{nreg}|{yp}|{rc}")
    return out


def per_season_counts(df: pd.DataFrame, cell_col: str) -> pd.DataFrame:
    return (df.groupby([cell_col, "season"], observed=True)
              .size().unstack(fill_value=0)
              .reindex(columns=ALL_SEASONS, fill_value=0))


def is_sparse(row: pd.Series) -> bool:
    return bool((row.sum() < SPARSE_TOTAL_FLOOR)
                or (row.min() < SPARSE_PER_SEASON_FLOOR))


def collapse_sparse_cells(df: pd.DataFrame, region_adj: dict, rc_adj: dict
                          ) -> tuple[pd.DataFrame, list[dict]]:
    cur = df.copy()
    merge_log: list[dict] = []
    while True:
        sc = per_season_counts(cur, "cell_id")
        sparse_cells = [cid for cid in sc.index if is_sparse(sc.loc[cid])]
        if not sparse_cells:
            break
        sparse_cells.sort(key=lambda c: (int(sc.loc[c].sum()),
                                          int(sc.loc[c].min()), c))
        target = sparse_cells[0]
        merged = False
        for nbr in cell_neighbors(target, region_adj, rc_adj):
            if nbr in sc.index and nbr != target:
                cur.loc[cur["cell_id"] == target, "cell_id"] = nbr
                axis = ("role_cohort"
                        if nbr.split("|")[0:2] == target.split("|")[0:2]
                        else "years_pro"
                        if nbr.split("|")[0] == target.split("|")[0]
                        else "region")
                merge_log.append({
                    "merged_target": target, "into_neighbor": nbr, "axis": axis,
                    "target_total": int(sc.loc[target].sum()),
                    "target_min_per_season": int(sc.loc[target].min()),
                })
                merged = True
                break
        if not merged:
            merge_log.append({"merged_target": target, "into_neighbor": None,
                              "axis": None,
                              "target_total": int(sc.loc[target].sum()),
                              "target_min_per_season": int(sc.loc[target].min()),
                              "note": "no_adjacent_neighbor_alive"})
            break
    return cur, merge_log


# ---------------------------------------------------------------------------
# Region assignment
# ---------------------------------------------------------------------------

def assign_off_feast() -> pd.DataFrame:
    """(nba_api_id, season) -> Rim/Paint/Perimeter or Profile-Sparse."""
    df = pd.read_parquet(DATA / "shot_locations_player.parquet")
    df = df[df["season"].isin(ALL_SEASONS)].copy()
    # dedup traded players: sum zone fga across team rows
    g = df.groupby(["nba_api_id", "season"], as_index=False)[OFF_FGA].sum()
    g["tot"] = g[OFF_FGA].sum(axis=1)
    g["ra_sh"] = g["ra_fga"] / g["tot"]
    g["paint_sh"] = g["paint_fga"] / g["tot"]
    g["perim_sh"] = (g[["mid_fga", "lc3_fga", "rc3_fga", "ab3_fga"]].sum(axis=1)
                     / g["tot"])
    def pick(r):
        if r["tot"] < OFF_FLOOR_FGA:
            return "Profile-Sparse"
        trio = {"Rim": r["ra_sh"], "Paint": r["paint_sh"],
                "Perimeter": r["perim_sh"]}
        return max(trio, key=trio.get)
    g["region"] = g.apply(pick, axis=1)
    return g[["nba_api_id", "season", "region"]]


def assign_def_feast() -> pd.DataFrame:
    """(nba_api_id, season) -> RimProtector/Hybrid/Perimeter or Profile-Sparse."""
    lt6 = pd.read_parquet(DATA / "player_def_zone_lt6.parquet")
    ov = pd.read_parquet(DATA / "player_def_zone_overall.parquet")
    lt6 = lt6[lt6["season"].isin(ALL_SEASONS)]
    ov = ov[ov["season"].isin(ALL_SEASONS)]
    # dedup traded players: sum across team rows
    lt6g = (lt6.groupby(["nba_api_id", "season"], as_index=False)["d_fga"].sum()
              .rename(columns={"d_fga": "lt6"}))
    ovg = (ov.groupby(["nba_api_id", "season"], as_index=False)
             .agg(ovr=("d_fga", "sum"), gp=("gp", "sum")))
    m = lt6g.merge(ovg, on=["nba_api_id", "season"], how="inner")
    m["contests_pg"] = m["ovr"] / m["gp"].clip(lower=1)
    m["rim_share"] = m["lt6"] / m["ovr"].clip(lower=1e-9)
    out = []
    for season, grp in m.groupby("season"):
        elig = grp[grp["contests_pg"] >= DEF_FLOOR_CONTESTS_PG].copy()
        # within-season terciles of rim_share among eligible
        if len(elig) >= 3:
            q1, q2 = elig["rim_share"].quantile([1/3, 2/3]).values
        else:
            q1 = q2 = elig["rim_share"].median() if len(elig) else 0.0
        def pick(r):
            if r["contests_pg"] < DEF_FLOOR_CONTESTS_PG:
                return "Profile-Sparse"
            if r["rim_share"] >= q2:
                return "RimProtector"
            if r["rim_share"] >= q1:
                return "Hybrid"
            return "Perimeter"
        grp = grp.copy()
        grp["region"] = grp.apply(pick, axis=1)
        out.append(grp[["nba_api_id", "season", "region"]])
    return pd.concat(out, ignore_index=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["off_feast", "def_feast"], required=True)
    ap.add_argument("--base", choices=["usg", "mpg"], default="usg",
                    help="secondary-axis source: usg (locked, v1.0 usage-tier) "
                         "or mpg (EXPLORATORY robustness, v1.1 MPG-tier role-cohort)")
    args = ap.parse_args()
    arm = args.arm
    base_name = args.base
    region_adj = REGION_ADJ[arm]
    rc_adj = RC_ADJ_USG if base_name == "usg" else RC_ADJ_MPG
    # output suffix: locked usg arms keep plain name; mpg arms are suffixed.
    out_arm = arm if base_name == "usg" else f"{arm}_{base_name}"

    print(f"\n--- Step 0/1 SPATIAL (arm={out_arm}, base={base_name}) ---")
    verify_spatial_lock()

    base = pd.read_parquet(RESULTS / f"P0_partition_{base_name}.parquet")
    print(f"  base universe (P0_partition_{base_name}): {len(base):,} player-seasons, "
          f"{base['season'].nunique()} seasons")

    # spatial region
    reg = assign_off_feast() if arm == "off_feast" else assign_def_feast()
    df = base.merge(reg, on=["nba_api_id", "season"], how="left")
    df["region"] = df["region"].fillna("Profile-Sparse")

    n_total = len(df)
    n_sparse = int((df["region"] == "Profile-Sparse").sum())
    print(f"  region assigned. Profile-Sparse (no/under-floor profile): "
          f"{n_sparse:,} / {n_total:,} ({100*n_sparse/n_total:.1f}%)")
    print(f"  region distribution (in-partition):")
    print(df[df.region != "Profile-Sparse"]["region"].value_counts().to_string())

    # position-overlap diagnostic (region x v1.0 pos_bucket) BEFORE dropping sparse
    overlap = (pd.crosstab(df["region"], df["pos_bucket"])
                 .reset_index())
    overlap.to_parquet(RESULTS / f"P0_position_overlap_{out_arm}.parquet", index=False)
    print(f"\n  region x position(v1.0) confusion:")
    print(pd.crosstab(df["region"], df["pos_bucket"]).to_string())

    # Profile-Sparse excluded from the cell partition (reported separately)
    sparse_df = df[df["region"] == "Profile-Sparse"].copy()
    part = df[df["region"] != "Profile-Sparse"].copy()
    part["cell_id"] = part["region"] + "|" + part["yp_bucket"] + "|" + part["rc_bucket"]

    raw_counts = per_season_counts(part, "cell_id")
    print(f"\n  raw cells materialised: {raw_counts.shape[0]} / 36 possible")

    part_p, merge_log = collapse_sparse_cells(part, region_adj, rc_adj)
    final_counts = per_season_counts(part_p, "cell_id")
    K = final_counts.shape[0]
    print(f"  merges applied: {len(merge_log)}   final K = {K}")

    # ---- write artifacts ----
    RESULTS.mkdir(parents=True, exist_ok=True)
    out_cols = ["nba_api_id", "season", "games", "mean_min", "name",
                "region", "pos_bucket", "yp_bucket", "rc_bucket", "years_pro",
                "prior_usg", "usg_fallback_to_default", "cell_id"]
    # mark sparse rows with cell_id = Profile-Sparse, keep them in the parquet
    sparse_df["cell_id"] = "Profile-Sparse"
    full = pd.concat([part_p[out_cols], sparse_df.reindex(columns=out_cols)],
                     ignore_index=True)
    full.to_parquet(RESULTS / f"P0_partition_{out_arm}.parquet", index=False)
    print(f"  -> P0_partition_{out_arm}.parquet ({len(full):,} rows incl "
          f"{len(sparse_df):,} Profile-Sparse)")

    counts_dict = {cid: {"total": int(final_counts.loc[cid].sum()),
                          "per_season": {s: int(final_counts.loc[cid, s])
                                          for s in ALL_SEASONS},
                          "min_per_season": int(final_counts.loc[cid].min())}
                    for cid in final_counts.index}
    collapse_map = {
        "arm": out_arm, "base": base_name, "axis": "court-region-of-feast",
        "locked_sha_spatial": SPATIAL_LOCK_SHA,
        "K_raw_materialized": int(raw_counts.shape[0]),
        "K_final": K,
        "qualifying_player_seasons_in_partition": int(len(part_p)),
        "profile_sparse_excluded": int(len(sparse_df)),
        "merge_log": merge_log,
        "final_cells": counts_dict,
    }
    (RESULTS / f"P0_collapse_map_{out_arm}.json").write_text(
        json.dumps(collapse_map, indent=2), encoding="utf-8")
    print(f"  -> P0_collapse_map_{out_arm}.json")

    # diagnostic md
    lines = [f"# Step 0/1 SPATIAL — P0 partition diagnostic (arm = {out_arm})\n",
             f"Axis: court-region-of-feast. Locked SHA: `{SPATIAL_LOCK_SHA}`\n",
             f"K_raw materialized = {raw_counts.shape[0]} / 36",
             f"K_final after collapse = **{K}**",
             f"Player-seasons in partition: {len(part_p):,}",
             f"Profile-Sparse excluded: {len(sparse_df):,}",
             f"Merges applied: {len(merge_log)}", "",
             "## region x v1.0 position confusion", "",
             "| region | " + " | ".join(sorted(df.pos_bucket.unique())) + " |",
             "|" + "---|" * (df.pos_bucket.nunique() + 1)]
    ct = pd.crosstab(df["region"], df["pos_bucket"])
    for reg_name, row in ct.iterrows():
        lines.append(f"| {reg_name} | "
                     + " | ".join(str(int(row[c])) for c in sorted(df.pos_bucket.unique()))
                     + " |")
    lines += ["", "## Final cells (post-collapse), by season", "",
              "| cell_id | " + " | ".join(ALL_SEASONS) + " | TOTAL | MIN/season |",
              "|" + "---|" * (len(ALL_SEASONS) + 3)]
    tbl = final_counts.copy()
    tbl["TOTAL"] = tbl.sum(axis=1)
    tbl["MIN_SEASON"] = tbl[list(ALL_SEASONS)].min(axis=1)
    tbl = tbl.sort_values("TOTAL", ascending=False)
    for cid, row in tbl.iterrows():
        cells = " | ".join(str(int(row[s])) for s in ALL_SEASONS)
        lines.append(f"| `{cid}` | {cells} | {int(row['TOTAL'])} | "
                     f"{int(row['MIN_SEASON'])} |")
    lines += ["", "## Merge log", "",
              "| target | into | axis | total | min/season |",
              "|---|---|---|---|---|"]
    for mlog in merge_log:
        lines.append(f"| `{mlog['merged_target']}` | `{mlog['into_neighbor']}` "
                     f"| {mlog['axis']} | {mlog['target_total']} | "
                     f"{mlog['target_min_per_season']} |")
    (RESULTS / f"P0_diagnostic_{out_arm}.md").write_text("\n".join(lines) + "\n",
                                                          encoding="utf-8")
    print(f"  -> P0_diagnostic_{out_arm}.md")
    print(f"\nStep 0/1 SPATIAL ({out_arm}) complete. K_final = {K}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
