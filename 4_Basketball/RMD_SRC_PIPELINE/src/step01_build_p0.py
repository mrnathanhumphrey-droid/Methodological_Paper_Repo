"""
RMD-SRC NBA — Step 0/1: build the P0 partition.

Supports two arms (locked separately):
  --arm usg  (v1.0 pre-reg, SHA recorded in SHA_LOCK.txt; role-cohort by
              prior-season USG%, thresholds 25.0 / 15.0)
  --arm mpg  (v1.1 amendment; role-cohort by same-season mean MPG,
              thresholds 28.0 / 18.0)

Per locked docs §2.2 in each, construct per-(player, season) cell
assignments over:

    P0 = position (3) x years_pro_bucket (4) x role_cohort (3)

with qualification gates (>= 20 games AND >= 10 MPG per season) and the
sparse-cell collapse rule (< 50 player-seasons total OR < 5 in any single
season -> merge with nearest neighbor, preferring role-cohort first,
then years-pro, then position).

Inspects ONLY partition-level metadata (games, MPG, position, years_pro,
prior-season USG% for usg arm). Does NOT touch per-game observable
distributions, which are the Step 2 quantity under the pre-reg.

Outputs (under RMD_SRC_PIPELINE/results/) suffixed by arm:
  P0_partition_{arm}.parquet
  P0_collapse_map_{arm}.json
  P0_diagnostic_{arm}.md
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
    ALL_SEASONS, MIN_GAMES_PER_SEASON, MIN_MPG_PER_SEASON, OBSERVABLES,
    PIPE_ROOT, POSITION_BUCKETS, POSITION_MAP, RESULTS,
    ROLE_COHORT_BUCKETS_USG, ROLE_COHORT_BUCKETS_MPG,
    ROOKIE_ROLE_DEFAULT_USG, SPARSE_PER_SEASON_FLOOR, SPARSE_TOTAL_FLOOR,
    YEARS_PRO_BUCKETS, ctg_season_for_nba, role_cohort_bucket_usg,
    role_cohort_bucket_mpg, season_start_year, verify_sha_lock,
    years_pro_bucket,
)

DATA = Path(r"D:/NBA Projections/data/parquet")


# ---------------------------------------------------------------------------
# Loaders (arm-agnostic)
# ---------------------------------------------------------------------------

def load_qualifying_player_seasons() -> pd.DataFrame:
    """Per (nba_api_id, season): games, mean_minutes_per_game, qualifying flag."""
    bs = pd.read_parquet(DATA / "historical_box_scores.parquet",
                          columns=["nba_api_id", "season", "season_type", "minutes"])
    bs = bs[(bs["season"].isin(ALL_SEASONS))
            & (bs["season_type"] == "Regular Season")]
    agg = (bs.groupby(["nba_api_id", "season"], observed=True)
             .agg(games=("minutes", "size"), mean_min=("minutes", "mean"))
             .reset_index())
    agg["qualified"] = ((agg["games"] >= MIN_GAMES_PER_SEASON)
                        & (agg["mean_min"] >= MIN_MPG_PER_SEASON))
    return agg


def load_metadata() -> pd.DataFrame:
    m = pd.read_parquet(DATA / "player_metadata_enriched.parquet",
                         columns=["nba_api_id", "name", "position", "debut_year"])
    m["pos_bucket"] = m["position"].map(POSITION_MAP).fillna("Guard")
    m["pos_string_missing"] = (m["position"].isna()
                                | (m["position"].astype(str).str.strip() == ""))
    return m[["nba_api_id", "name", "pos_bucket", "debut_year",
              "pos_string_missing"]]


def load_ctg_usage_by_name() -> pd.DataFrame:
    """CTG USG% (converted fraction -> percent) per (name_key, ctg_season).
    Only loaded for the --arm usg run."""
    c = pd.read_parquet(DATA / "ctg_players.parquet",
                         columns=["name", "season", "usage", "mpg",
                                  "games_played"])
    c = c.dropna(subset=["name", "usage", "season"])
    c["nkey"] = c["name"].str.lower().str.strip()
    c["w"] = (c["mpg"].fillna(20.0) * c["games_played"].fillna(40.0)).clip(lower=1.0)
    grp = c.groupby(["nkey", "season"], observed=True)
    weighted = grp.apply(lambda g: np.average(g["usage"], weights=g["w"]),
                         include_groups=False).reset_index(name="usg")
    weighted["season"] = weighted["season"].astype(int)
    # CTG `usage` is 0-1 fraction; pre-reg threshold is in USG-percent.
    weighted["usg"] = weighted["usg"] * 100.0
    return weighted


# ---------------------------------------------------------------------------
# Bucketing — arm-conditional
# ---------------------------------------------------------------------------

def build_records_usg(quals: pd.DataFrame, meta: pd.DataFrame,
                       ctg: pd.DataFrame) -> pd.DataFrame:
    """v1.0 usage-tier arm: prior-season USG% -> role-cohort."""
    df = quals[quals["qualified"]].merge(meta, on="nba_api_id", how="left")

    df["debut_year"] = df["debut_year"].fillna(0).astype(int)
    df["season_start"] = df["season"].map(season_start_year)
    df["years_pro"] = df["season_start"] - df["debut_year"]
    df.loc[df["debut_year"] == 0, "years_pro"] = -1
    df["yp_bucket"] = df["years_pro"].apply(
        lambda y: years_pro_bucket(int(y)) if y >= 0 else None)

    df["nkey"] = df["name"].str.lower().str.strip()
    df["prior_ctg_season"] = df["season_start"]  # = end-year of prior NBA season
    df = df.merge(
        ctg.rename(columns={"season": "prior_ctg_season", "usg": "prior_usg"}),
        on=["nkey", "prior_ctg_season"], how="left",
    )
    df["usg_fallback_to_default"] = df["prior_usg"].isna()
    df["rc_bucket"] = df["prior_usg"].apply(
        lambda u: ROOKIE_ROLE_DEFAULT_USG if pd.isna(u)
                  else role_cohort_bucket_usg(float(u)))

    df.attrs["dropped_no_debut"] = int((df["yp_bucket"].isna()).sum())
    df = df[df["yp_bucket"].notna() & df["pos_bucket"].notna()].copy()

    df["cell_id"] = (df["pos_bucket"] + "|" + df["yp_bucket"]
                     + "|" + df["rc_bucket"])
    return df


def build_records_mpg(quals: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """v1.1 MPG-tier arm: same-season mean MPG -> role-cohort."""
    df = quals[quals["qualified"]].merge(meta, on="nba_api_id", how="left")

    df["debut_year"] = df["debut_year"].fillna(0).astype(int)
    df["season_start"] = df["season"].map(season_start_year)
    df["years_pro"] = df["season_start"] - df["debut_year"]
    df.loc[df["debut_year"] == 0, "years_pro"] = -1
    df["yp_bucket"] = df["years_pro"].apply(
        lambda y: years_pro_bucket(int(y)) if y >= 0 else None)

    df["rc_bucket"] = df["mean_min"].apply(
        lambda m: role_cohort_bucket_mpg(float(m)))

    # Columns the usg-arm has that mpg-arm does not; fill with NaN so
    # downstream code can rely on a stable schema if it inspects them.
    df["prior_usg"] = np.nan
    df["usg_fallback_to_default"] = False

    df.attrs["dropped_no_debut"] = int((df["yp_bucket"].isna()).sum())
    df = df[df["yp_bucket"].notna() & df["pos_bucket"].notna()].copy()

    df["cell_id"] = (df["pos_bucket"] + "|" + df["yp_bucket"]
                     + "|" + df["rc_bucket"])
    return df


# ---------------------------------------------------------------------------
# Sparse-cell collapse (arm-aware via the role-cohort adjacency map)
# ---------------------------------------------------------------------------

POS_ADJ = {"Center": ["Forward"], "Forward": ["Center", "Guard"],
           "Guard": ["Forward"],
           # Positionless: amendment v1.2 §2.6 — NO position-axis adjacency.
           # Sparse Positionless cells can only collapse along role-cohort or
           # years-pro (handled by cell_neighbors via the RC/YP loops).
           "Positionless": []}
YP_ADJ = {"Rookie": ["Soph_Early"], "Soph_Early": ["Rookie", "Mid"],
          "Mid": ["Soph_Early", "Deep_vet"], "Deep_vet": ["Mid"]}
RC_ADJ_USG = {"High_usage": ["Mid_usage"],
              "Mid_usage": ["High_usage", "Low_usage"],
              "Low_usage": ["Mid_usage"]}
RC_ADJ_MPG = {"Starter": ["Rotation"], "Rotation": ["Starter", "Bench"],
              "Bench": ["Rotation"]}


def cell_neighbors(cid: str, rc_adj: dict[str, list[str]]) -> list[str]:
    """Per §2.2: prefer role-cohort axis, then years-pro, then position."""
    pos, yp, rc = cid.split("|")
    out: list[str] = []
    for nrc in rc_adj[rc]:
        out.append(f"{pos}|{yp}|{nrc}")
    for nyp in YP_ADJ[yp]:
        out.append(f"{pos}|{nyp}|{rc}")
    for npos in POS_ADJ[pos]:
        out.append(f"{npos}|{yp}|{rc}")
    return out


def per_season_counts(df: pd.DataFrame, cell_col: str) -> pd.DataFrame:
    return (df.groupby([cell_col, "season"], observed=True)
              .size().unstack(fill_value=0).reindex(columns=ALL_SEASONS,
                                                    fill_value=0))


def is_sparse(row: pd.Series) -> bool:
    return bool((row.sum() < SPARSE_TOTAL_FLOOR)
                or (row.min() < SPARSE_PER_SEASON_FLOOR))


def collapse_sparse_cells(df: pd.DataFrame, rc_adj: dict[str, list[str]]
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
        for nbr in cell_neighbors(target, rc_adj):
            if nbr in sc.index and nbr != target:
                cur.loc[cur["cell_id"] == target, "cell_id"] = nbr
                axis = ("role_cohort"
                        if nbr.split("|")[0:2] == target.split("|")[0:2]
                        else "years_pro"
                        if nbr.split("|")[0] == target.split("|")[0]
                        else "position")
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
# Main
# ---------------------------------------------------------------------------

def load_adjudication_override() -> dict[int, str]:
    """Load v1.2 adjudication verdicts; return {nba_api_id: adjudicated_bucket}.
    Bucket can be Center/Forward/Guard/Positionless."""
    import json as _json
    path = RESULTS / "position_adjudication_v12.json"
    if not path.exists():
        sys.exit("Override map missing: position_adjudication_v12.json. "
                  "Run the v1.2 adjudication workflow first.")
    payload = _json.loads(path.read_text(encoding="utf-8"))
    return {int(v["nba_api_id"]): v["adjudicated_bucket"]
            for v in payload["verdicts"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["usg", "mpg", "usg_adj", "mpg_adj"],
                     required=True,
                     help="usg=v1.0, mpg=v1.1, usg_adj/mpg_adj=v1.2 (adjudicated).")
    args = ap.parse_args()
    arm = args.arm
    base_arm = "usg" if arm.startswith("usg") else "mpg"
    is_adj = arm.endswith("_adj")

    sha_payload = verify_sha_lock(f"Step 0/1 build_p0 [arm={arm}]", arm=arm)

    print(f"\n--- Loading inputs (arm={arm}) ---")
    quals = load_qualifying_player_seasons()
    print(f"  qualifying-aggregate rows: {len(quals):,}  "
          f"(across {len(ALL_SEASONS)} seasons)")
    print(f"  qualified (>= {MIN_GAMES_PER_SEASON} games AND "
          f">= {MIN_MPG_PER_SEASON} MPG): {int(quals['qualified'].sum()):,}")

    meta = load_metadata()

    if base_arm == "usg":
        ctg = load_ctg_usage_by_name()
        print(f"  metadata rows: {len(meta):,}")
        print(f"  CTG name-season USG records: {len(ctg):,}  "
              f"(seasons {ctg['season'].min()}-{ctg['season'].max()})")
        df = build_records_usg(quals, meta, ctg)
        rc_adj = RC_ADJ_USG
        print(f"\n--- Bucketing (usage-tier base) ---")
    else:
        df = build_records_mpg(quals, meta)
        rc_adj = RC_ADJ_MPG
        print(f"\n--- Bucketing (MPG-tier base) ---")

    # ---- v1.2 adjudication override (only for usg_adj / mpg_adj) ----
    if is_adj:
        overrides = load_adjudication_override()
        df["_pre_adj_pos_bucket"] = df["pos_bucket"]
        df["pos_bucket"] = df["nba_api_id"].apply(
            lambda i: overrides.get(int(i)) if int(i) in overrides
                       else None)
        # Players NOT in the override map keep their base-arm pos_bucket.
        df["pos_bucket"] = df["pos_bucket"].fillna(df["_pre_adj_pos_bucket"])
        n_overridden = int((df["pos_bucket"] != df["_pre_adj_pos_bucket"]).sum())
        n_targets_in_data = int(df["nba_api_id"].isin(overrides).sum())
        print(f"\n--- v1.2 override application ({arm}) ---")
        print(f"  override map size: {len(overrides)} players")
        print(f"  player-seasons covered by overrides: {n_targets_in_data}")
        print(f"  player-seasons actually changed bucket: {n_overridden}")
        # Recompute cell_id with potentially-new pos_bucket.
        df["cell_id"] = (df["pos_bucket"] + "|" + df["yp_bucket"]
                         + "|" + df["rc_bucket"])
        df = df.drop(columns="_pre_adj_pos_bucket")

    print(f"\nqualifying player-seasons: {len(df):,}")
    if base_arm == "usg":
        n_default = int(df['usg_fallback_to_default'].sum())
        print(f"  rookie default {ROOKIE_ROLE_DEFAULT_USG} applied: "
              f"{n_default:,} ({100*n_default/max(1,len(df)):.1f}%)")
    else:
        rc_counts = df['rc_bucket'].value_counts().to_dict()
        print(f"  role-cohort raw distribution: {rc_counts}")

    raw_counts = per_season_counts(df, "cell_id")
    print(f"\n--- Raw 36-cell counts ---")
    print(f"  raw cells materialised: {raw_counts.shape[0]} / 36 possible")

    print(f"\n--- Applying sparse-cell collapse ---")
    df_p, merge_log = collapse_sparse_cells(df, rc_adj)
    final_counts = per_season_counts(df_p, "cell_id")
    K = final_counts.shape[0]
    print(f"  merges applied: {len(merge_log)}")
    print(f"  final K (after collapse): {K}")

    print(f"\n--- Writing artifacts (arm={arm}) ---")
    RESULTS.mkdir(parents=True, exist_ok=True)
    out_cols = ["nba_api_id", "season", "games", "mean_min", "name",
                "pos_bucket", "yp_bucket", "rc_bucket", "years_pro",
                "prior_usg", "usg_fallback_to_default", "cell_id"]
    pq_path = RESULTS / f"P0_partition_{arm}.parquet"
    df_p[out_cols].to_parquet(pq_path, index=False)
    print(f"  -> {pq_path.name}")

    counts_dict = {cid: {"total": int(final_counts.loc[cid].sum()),
                          "per_season": {s: int(final_counts.loc[cid, s])
                                          for s in ALL_SEASONS},
                          "min_per_season": int(final_counts.loc[cid].min())}
                    for cid in final_counts.index}
    collapse_map = {
        "arm": arm,
        "locked_sha_v1_0": sha_payload["v1.0"],
        "locked_sha_v1_1": sha_payload["v1.1"],
        "K_raw_materialized": int(raw_counts.shape[0]),
        "K_final": K,
        "qualifying_player_seasons": int(len(df_p)),
        "merge_log": merge_log,
        "final_cells": counts_dict,
    }
    cm_path = RESULTS / f"P0_collapse_map_{arm}.json"
    cm_path.write_text(json.dumps(collapse_map, indent=2), encoding="utf-8")
    print(f"  -> {cm_path.name}")

    # Markdown diagnostic.
    lines = [f"# Step 0/1 — P0 partition diagnostic (arm = {arm})\n",
              f"Locked SHA v1.0: `{sha_payload['v1.0']}`",
              (f"Locked SHA v1.1: `{sha_payload['v1.1']}`"
               if sha_payload['v1.1'] else "(v1.1 amendment not in scope)"),
              "",
              f"K_raw materialized = {raw_counts.shape[0]} / 36 possible",
              f"K_final after collapse = **{K}**",
              f"Qualifying player-seasons: {len(df_p):,}",
              f"Merges applied: {len(merge_log)}",
              "",
              "## Final cells (post-collapse), by season",
              "",
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
    lines += ["", "## Merge log (sparse-cell collapse)", "",
              "| target | into_neighbor | axis | total | min/season |",
              "|---|---|---|---|---|"]
    for m in merge_log:
        lines.append(
            f"| `{m['merged_target']}` | `{m['into_neighbor']}` | "
            f"{m['axis']} | {m['target_total']} | "
            f"{m['target_min_per_season']} |"
        )
    diag = "\n".join(lines) + "\n"
    (RESULTS / f"P0_diagnostic_{arm}.md").write_text(diag, encoding="utf-8")
    print(f"  -> P0_diagnostic_{arm}.md")

    print(f"\nStep 0/1 ({arm}) complete. K_final = {K}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
