"""Write 25-26 v6.1 LOCKED ship to Wonka's audit-CSV contract — v1.1 rookie-aware.

Adds 9 rookie-aware columns to the v1.0 schema:
  - projection_method  (stan_v6.1_full / cohort_regression / draft_pick_log / pre_nba_translation)
  - years_in_league    (0 = rookie, 1 = soph, ...)
  - draft_year, draft_pick, draft_round
  - pre_nba_league     (Wonka enum: NCAA_D1 / G_LEAGUE / OTHER_INTL / ...)
  - pre_nba_team       (school or club name)
  - cohort_size_n      (number of historical comps backing the projection; rookies = 452)
  - auction_value_seed (model-derived $ via Z-score over replacement; rookies/sophs only)

Z-score auction-seed: closed-form 9-cat formula with league-format defaults
(12 teams, $200/team, 13-player roster). Counting cats z-scored on
per-season totals (per-game × GP), TOV inverted. Ratio cats use
impact = (player_pct - league_pct) × attempts. $_player = floor + budget
proportional to z_over_replacement.

Reads:    audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv
          audit_runs/cohort_widening_v0_2025_26/per_player_projections.csv  (for __cohort)
          audit_runs/cohort_widening_v0_2025_26/metadata.json               (for cohort_size_n)
          audit_runs/cohort_widening_v0_2025_26/rookie_metadata_supplement.parquet
          data/parquet/{player_metadata_enriched, nba_draft_data,
                        rookie_career_prior, historical_box_scores}.parquet

Writes:   D:/Wonka Resolve/audit/data/parsed/nba_projections_projections.csv
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"

SHIP_V61 = REPO / "audit_runs" / "unified_ship_v6_1_2025_26" / "per_player_projections_2025-26.csv"
COHORT_DIR = REPO / "audit_runs" / "cohort_widening_v0_2025_26"
WONKA_OUT = Path("D:/Wonka Resolve/audit/data/parsed/nba_projections_projections.csv")
WONKA_OUT_DRYRUN = Path("audit_runs/wonka_v11_dryrun/nba_projections_projections.csv")

CONTRACT_VERSION = "1.1"
SOURCE_NAME = "nba_projections"
MODE = "production"
TARGET_SEASON = "2025-26"
TARGET_SEASON_START_YEAR = 2025
TRAIN_TAG = "2019-20-2020-21-2021-22-2022-23-2023-24-2024-25"
PRIOR_SEASON = "2024-25"

# League-format defaults for auction-seed (Wonka overrides via LeagueConfig)
LEAGUE_TEAMS = 12
BUDGET_PER_TEAM = 200
ROSTER_SIZE = 13
REPLACEMENT_RANK = LEAGUE_TEAMS * ROSTER_SIZE  # 156
TOTAL_BUDGET = LEAGUE_TEAMS * BUDGET_PER_TEAM  # $2400
DOLLAR_FLOOR = 1.0
ROOKIE_ID_BASE = 9990000

WONKA_FIELDS = [
    "source", "player_name", "team", "position", "nba_api_id",
    "games_proj", "minutes_proj",
    # 12-cat block
    "PTS_proj", "PTS_stddev_per_game",
    "REB_proj", "REB_stddev_per_game",
    "AST_proj", "AST_stddev_per_game",
    "STL_proj", "STL_stddev_per_game",
    "BLK_proj", "BLK_stddev_per_game",
    "TOV_proj", "TOV_stddev_per_game",
    "FGM_proj", "FGM_stddev_per_game",
    "FGA_proj", "FGA_stddev_per_game",
    "FG_pct_proj",
    "FTM_proj", "FTM_stddev_per_game",
    "FTA_proj", "FTA_stddev_per_game",
    "FT_pct_proj",
    "3PM_proj", "3PM_stddev_per_game",
    "3PA_proj", "3PA_stddev_per_game",
    "3P_pct_proj",
    # v1.1 rookie-aware columns
    "projection_method",
    "years_in_league",
    "draft_year", "draft_pick", "draft_round",
    "pre_nba_league", "pre_nba_team",
    "cohort_size_n",
    "auction_value_seed",
    # v1.2 (2026-06-04): resolve_value — model-derived $ for ALL players
    # (auction_value_seed is gated to non-stan rows for legacy reasons).
    # Same Z-score-over-replacement formula; emit for everyone so Wonka
    # Resolve can compute Pure/Resolve Value without anchoring on Yahoo $.
    "resolve_value",
]

SHIP_TO_WONKA = {
    "PTS_per_game": "PTS_proj", "PTS_per_game_sd": "PTS_stddev_per_game",
    "REB_per_game": "REB_proj", "REB_per_game_sd": "REB_stddev_per_game",
    "AST_per_game": "AST_proj", "AST_per_game_sd": "AST_stddev_per_game",
    "STL_per_game": "STL_proj", "STL_per_game_sd": "STL_stddev_per_game",
    "BLK_per_game": "BLK_proj", "BLK_per_game_sd": "BLK_stddev_per_game",
    "TOV_per_game": "TOV_proj", "TOV_per_game_sd": "TOV_stddev_per_game",
    "FGM_per_game": "FGM_proj", "FGM_per_game_sd": "FGM_stddev_per_game",
    "FGA_per_game": "FGA_proj", "FGA_per_game_sd": "FGA_stddev_per_game",
    "FTM_per_game": "FTM_proj", "FTM_per_game_sd": "FTM_stddev_per_game",
    "FTA_per_game": "FTA_proj", "FTA_per_game_sd": "FTA_stddev_per_game",
    "FG3M_per_game": "3PM_proj", "FG3M_per_game_sd": "3PM_stddev_per_game",
    "FG3A_per_game": "3PA_proj", "FG3A_per_game_sd": "3PA_stddev_per_game",
}

# rookie_career_prior pre_nba_league raw values -> Wonka enum
PRE_NBA_LEAGUE_MAP = {
    "ncaa_d1": "NCAA_D1",
    "g_league": "G_LEAGUE",
    "lnb_france": "LNB_PRO_A",
    "acb_spain": "ACB",
    "nbl_australia": "NBL",
    "bsl_israel": "OTHER_INTL",
    # nba_draft_data pre_nba_team_type fallback
    "ncaa": "NCAA_D1",
    "non_ncaa": "OTHER_INTL",
    "international": "OTHER_INTL",
}


def build_cohort_lookups():
    """Return dicts:
       pid -> projection_method
       pid -> cohort_size_n
       pid -> __cohort  (raw cohort label for diagnostics)
    """
    pm_lookup: dict[int, str] = {}
    csn_lookup: dict[int, int] = {}
    cohort_lookup: dict[int, str] = {}

    cw_csv = COHORT_DIR / "per_player_projections.csv"
    if not cw_csv.exists():
        print(f"  WARN: cohort widening output missing at {cw_csv}")
        return pm_lookup, csn_lookup, cohort_lookup

    cw = pd.read_csv(cw_csv)
    cw["nba_api_id"] = cw["nba_api_id"].astype(int)

    md_path = COHORT_DIR / "metadata.json"
    md = {}
    if md_path.exists():
        with open(md_path) as f:
            md = json.load(f)
    coefs = md.get("rookie_pick_regression_coefs", {})
    rookie_n = int(next(iter(coefs.values())).get("n", 0)) if coefs else 0
    soph_n = int(md.get("n_sophs_or_unfit_vets", 0))

    # Determine which 2025 rookies had NCAA path used. Heuristic: any rookie
    # whose name appears in ncaa_player_seasons 2024-25 is "pre_nba_translation".
    # Otherwise "draft_pick_log".
    ncaa_p = PQ / "ncaa_player_seasons.parquet"
    ncaa_2025_names = set()
    if ncaa_p.exists():
        ncaa = pd.read_parquet(ncaa_p)
        if "ncaa_season" in ncaa.columns and "draft_year" in ncaa.columns:
            sub = ncaa[(ncaa["ncaa_season"] == "2024-25") &
                       (ncaa["draft_year"] == 2025)]
            ncaa_2025_names = set(sub["player_name_raw"].dropna().tolist())

    for _, r in cw.iterrows():
        pid = int(r["nba_api_id"])
        cohort = r.get("__cohort", "")
        cohort_lookup[pid] = cohort
        if cohort == "soph_or_unfit_vet":
            pm_lookup[pid] = "cohort_regression"
            # Soph cohort_size_n: leave blank (current-season cohort, not historical comps)
        elif cohort == "rookie_2025":
            name = r.get("name", "")
            if name in ncaa_2025_names:
                pm_lookup[pid] = "pre_nba_translation"
            else:
                pm_lookup[pid] = "draft_pick_log"
            if rookie_n:
                csn_lookup[pid] = rookie_n

    return pm_lookup, csn_lookup, cohort_lookup


def build_draft_lookups():
    """Return dicts: pid -> draft_year, pid -> draft_pick, pid -> draft_round,
       pid -> pre_nba_team, pid -> pre_nba_team_type."""
    draft = pd.read_parquet(PQ / "nba_draft_data.parquet")
    draft = draft.dropna(subset=["nba_api_id"])
    draft["nba_api_id"] = draft["nba_api_id"].astype(int)
    draft = draft.drop_duplicates(subset=["nba_api_id"], keep="first")

    dy = dict(zip(draft["nba_api_id"], draft["draft_year"]))
    dp = dict(zip(draft["nba_api_id"], draft["draft_pick"]))
    dr = dict(zip(draft["nba_api_id"], draft["draft_round"]))
    pt = dict(zip(draft["nba_api_id"], draft["pre_nba_team"]))
    pty = dict(zip(draft["nba_api_id"], draft["pre_nba_team_type"]))
    return dy, dp, dr, pt, pty


def build_rookie_supplement_lookups():
    """Synthetic-id rookies: pid -> draft_year/pick/team/etc."""
    sup_path = COHORT_DIR / "rookie_metadata_supplement.parquet"
    if not sup_path.exists():
        return {}, {}, {}, {}, {}
    sup = pd.read_parquet(sup_path)
    sup["nba_api_id"] = sup["nba_api_id"].astype(int)
    dy = dict(zip(sup["nba_api_id"], sup["draft_year"]))
    dp = dict(zip(sup["nba_api_id"], sup["draft_pick"]))
    dt = dict(zip(sup["nba_api_id"], sup["drafted_by_team"]))
    # draft_round derive: pick 1-30 -> round 1, pick 31-60 -> round 2 (modern era)
    dr = {pid: (1 if int(pk) <= 30 else 2) for pid, pk in zip(sup["nba_api_id"], sup["draft_pick"])}
    return dy, dp, dr, dt, sup


def build_pre_nba_league_lookups():
    """pid -> pre_nba_league (Wonka enum), pid -> pre_nba_team (string).

    Sources, in order of preference:
      1. rookie_career_prior.parquet (most informative — has actual league)
      2. nba_draft_data.pre_nba_team_type (ncaa/non_ncaa/international fallback)
    """
    league_lookup: dict[int, str] = {}
    team_lookup: dict[int, str] = {}

    rcp_path = PQ / "rookie_career_prior.parquet"
    if rcp_path.exists():
        rcp = pd.read_parquet(rcp_path)
        rcp = rcp.dropna(subset=["nba_api_id"])
        rcp["nba_api_id"] = rcp["nba_api_id"].astype(int)
        for _, r in rcp.iterrows():
            pid = int(r["nba_api_id"])
            raw = r.get("pre_nba_league")
            if pd.notna(raw):
                league_lookup[pid] = PRE_NBA_LEAGUE_MAP.get(str(raw).lower(), "OTHER_INTL")
            team = r.get("pre_nba_team")
            if pd.notna(team):
                team_lookup[pid] = str(team)
    return league_lookup, team_lookup


def compute_auction_seeds(df: pd.DataFrame, games_lookup: dict) -> dict[int, float]:
    """Z-score over replacement, closed-form. Returns pid -> $.

    Cats: PTS, REB, AST, STL, BLK, TOV (counting; TOV inverted)
          FG3M (counting)
          FG_pct, FT_pct, 3P_pct (ratio; impact-weighted by attempts)
    """
    work = df.copy()
    work["nba_api_id"] = work["nba_api_id"].astype(int)
    # Games for season-total scaling
    work["gp_used"] = work["nba_api_id"].map(games_lookup).fillna(70).astype(float)

    # Counting cats: total = per_game * GP
    counting = {
        "PTS": "PTS_per_game",
        "REB": "REB_per_game",
        "AST": "AST_per_game",
        "STL": "STL_per_game",
        "BLK": "BLK_per_game",
        "TOV": "TOV_per_game",  # inverted
        "FG3M": "FG3M_per_game",
    }
    z_cols = []
    for cat, col in counting.items():
        if col not in work.columns:
            continue
        total = pd.to_numeric(work[col], errors="coerce").fillna(0.0) * work["gp_used"]
        mean = total.mean()
        sd = total.std(ddof=1)
        if sd == 0 or pd.isna(sd):
            work[f"z_{cat}"] = 0.0
        else:
            z = (total - mean) / sd
            if cat == "TOV":
                z = -z  # higher TOV = worse
            work[f"z_{cat}"] = z
        z_cols.append(f"z_{cat}")

    # Ratio cats: impact = (player_pct - league_pct) × attempts_total
    ratios = [
        ("FG_pct", "FGM_per_game", "FGA_per_game"),
        ("FT_pct", "FTM_per_game", "FTA_per_game"),
        ("3P_pct", "FG3M_per_game", "FG3A_per_game"),
    ]
    for label, made_col, att_col in ratios:
        if made_col not in work.columns or att_col not in work.columns:
            continue
        made = pd.to_numeric(work[made_col], errors="coerce").fillna(0.0) * work["gp_used"]
        att = pd.to_numeric(work[att_col], errors="coerce").fillna(0.0) * work["gp_used"]
        league_pct = made.sum() / att.sum() if att.sum() > 0 else 0.0
        # Per-player pct, then impact
        with np.errstate(divide="ignore", invalid="ignore"):
            player_pct = np.where(att > 0, made / att, league_pct)
        impact = (player_pct - league_pct) * att
        impact_sd = impact.std(ddof=1)
        if impact_sd == 0 or pd.isna(impact_sd):
            work[f"z_{label}"] = 0.0
        else:
            work[f"z_{label}"] = impact / impact_sd
        z_cols.append(f"z_{label}")

    work["total_z"] = work[z_cols].sum(axis=1)
    # Replacement at rank N
    sorted_z = work["total_z"].sort_values(ascending=False).reset_index(drop=True)
    if len(sorted_z) > REPLACEMENT_RANK:
        replacement = sorted_z.iloc[REPLACEMENT_RANK - 1]  # rank N-th best
    else:
        replacement = sorted_z.iloc[-1]
    work["z_above_repl"] = (work["total_z"] - replacement).clip(lower=0.0)

    # Allocate budget proportional to z_above_repl among players above replacement
    pos_pool = work["z_above_repl"].sum()
    n_above = (work["z_above_repl"] > 0).sum()
    surplus = TOTAL_BUDGET - n_above * DOLLAR_FLOOR  # budget after $1 floor for above-replacement
    if pos_pool > 0 and surplus > 0:
        work["auction_seed"] = np.where(
            work["z_above_repl"] > 0,
            DOLLAR_FLOOR + surplus * (work["z_above_repl"] / pos_pool),
            DOLLAR_FLOOR,
        )
    else:
        work["auction_seed"] = DOLLAR_FLOOR

    return dict(zip(work["nba_api_id"], work["auction_seed"]))


def main(dryrun: bool = False):
    out_path = WONKA_OUT_DRYRUN if dryrun else WONKA_OUT
    print(f"Reading v6.1 ship: {SHIP_V61}")
    print(f"Output target: {out_path} {'(DRY-RUN)' if dryrun else '(PRODUCTION)'}")
    df = pd.read_csv(SHIP_V61)
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    print(f"  rows: {len(df)}")

    # Player metadata for team / position / name / debut_year
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    meta["nba_api_id"] = meta["nba_api_id"].astype(int)
    name_lookup = dict(zip(meta["nba_api_id"], meta["name"]))
    pos_lookup = dict(zip(meta["nba_api_id"], meta["position"].fillna("")))
    debut_lookup = dict(zip(meta["nba_api_id"], meta["debut_year"]))

    # Rookie supplement (synthetic IDs 9990001+)
    sup_dy, sup_dp, sup_dr, sup_dt, sup_df = build_rookie_supplement_lookups()
    if not sup_df.empty if isinstance(sup_df, pd.DataFrame) else False:
        for _, r in sup_df.iterrows():
            pid = int(r["nba_api_id"])
            name_lookup[pid] = r["name"]
            pos_lookup[pid] = r["position"]
            debut_lookup[pid] = int(r["debut_year"])

    # Draft data lookups (real nba_api_ids)
    draft_dy, draft_dp, draft_dr, draft_pt, draft_pty = build_draft_lookups()
    # Merge supplement values where missing for synthetic IDs
    for pid, v in sup_dy.items():
        draft_dy.setdefault(pid, v)
    for pid, v in sup_dp.items():
        draft_dp.setdefault(pid, v)
    for pid, v in sup_dr.items():
        draft_dr.setdefault(pid, v)

    # pre_nba_league / pre_nba_team — start with rookie_career_prior, fall back to draft data
    league_lookup, pre_team_lookup = build_pre_nba_league_lookups()
    # For 2025 rookies (synthetic ids) — derive from supplement: pre_nba_team_type via name->draft join
    raw_draft = pd.read_parquet(PQ / "nba_draft_data.parquet")
    raw_2025 = raw_draft[raw_draft["draft_year"] == 2025]
    name_to_pty = dict(zip(raw_2025["player_name_raw"], raw_2025["pre_nba_team_type"]))
    name_to_pre_team = dict(zip(raw_2025["player_name_raw"], raw_2025["pre_nba_team"]))
    if isinstance(sup_df, pd.DataFrame) and not sup_df.empty:
        for _, r in sup_df.iterrows():
            pid = int(r["nba_api_id"])
            nm = r["name"]
            if pid not in league_lookup:
                pty = name_to_pty.get(nm)
                if pd.notna(pty):
                    league_lookup[pid] = PRE_NBA_LEAGUE_MAP.get(str(pty).lower(), "OTHER_INTL")
            if pid not in pre_team_lookup:
                pt = name_to_pre_team.get(nm)
                if pd.notna(pt):
                    pre_team_lookup[pid] = str(pt)
    # Vets w/o rookie_career_prior entry — fall back to draft data pre_nba_team_type
    for pid, pty in draft_pty.items():
        if pid not in league_lookup and pd.notna(pty):
            league_lookup[pid] = PRE_NBA_LEAGUE_MAP.get(str(pty).lower(), "OTHER_INTL")
    for pid, pt in draft_pt.items():
        if pid not in pre_team_lookup and pd.notna(pt):
            pre_team_lookup[pid] = str(pt)

    # Cohort + projection_method + cohort_size_n
    pm_lookup, csn_lookup, cohort_lookup = build_cohort_lookups()
    # Anyone in v6.1 ship NOT in cohort widening = stan_v6.1_full vet
    ship_ids = set(df["nba_api_id"].tolist())
    for pid in ship_ids:
        if pid not in pm_lookup:
            pm_lookup[pid] = "stan_v6.1_full"

    # Team + 24-25 GP from box scores
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    sub = box[box["season"] == PRIOR_SEASON].copy()
    sub["minutes"] = pd.to_numeric(sub["minutes"], errors="coerce")
    sub = sub.dropna(subset=["minutes"])
    sub = sub[sub["minutes"] > 0]
    team_lookup = (sub.groupby("nba_api_id")["team_abbr"]
                   .agg(lambda s: s.value_counts().index[0])
                   .to_dict())
    team_lookup = {int(k): v for k, v in team_lookup.items()}
    games_lookup = sub.groupby("nba_api_id")["game_id"].count().to_dict()
    games_lookup = {int(k): int(v) for k, v in games_lookup.items()}

    # Rookies: team from drafted_by_team, GP placeholder = 70
    if isinstance(sup_df, pd.DataFrame) and not sup_df.empty:
        for _, r in sup_df.iterrows():
            pid = int(r["nba_api_id"])
            if pid not in team_lookup and pd.notna(r.get("drafted_by_team")):
                team_lookup[pid] = r["drafted_by_team"]
            if pid not in games_lookup:
                games_lookup[pid] = 70

    # Compute derived ratio cats
    if "FGA_per_game" in df.columns and "FGM_per_game" in df.columns:
        df["FG_pct_proj"] = (df["FGM_per_game"] /
                             df["FGA_per_game"].replace(0, pd.NA))
    if "FTA_per_game" in df.columns and "FTM_per_game" in df.columns:
        df["FT_pct_proj"] = (df["FTM_per_game"] /
                             df["FTA_per_game"].replace(0, pd.NA))
    if "FG3A_per_game" in df.columns and "FG3M_per_game" in df.columns:
        df["3P_pct_proj"] = (df["FG3M_per_game"] /
                             df["FG3A_per_game"].replace(0, pd.NA))

    # Auction seed (compute on full pool, emit only for non-stan rows)
    print("Computing auction-value seeds (Z-score over replacement, league defaults)...")
    auction_seeds = compute_auction_seeds(df, games_lookup)
    n_above = sum(1 for v in auction_seeds.values() if v > DOLLAR_FLOOR + 1e-6)
    print(f"  players above replacement: {n_above} / {len(auction_seeds)}")
    print(f"  budget allocation total: ${sum(auction_seeds.values()):.0f} (target ${TOTAL_BUDGET})")
    top5 = sorted(auction_seeds.items(), key=lambda kv: -kv[1])[:5]
    for pid, v in top5:
        print(f"    top: pid={pid} name={name_lookup.get(pid, '?'):<25} ${v:.1f}")

    # Write output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    n_rookie = 0
    n_soph = 0
    n_stan = 0
    with out_path.open("w", encoding="utf-8", newline="") as f:
        f.write(f"# contract_version={CONTRACT_VERSION} mode={MODE} "
                f"target_season={TARGET_SEASON} train_seasons={TRAIN_TAG} "
                f"source=v6.1_LOCKED_forward_rookie_aware "
                f"note=as_if_25-26_unplayed\n")
        writer = csv.DictWriter(f, fieldnames=WONKA_FIELDS)
        writer.writeheader()

        for _, r in df.iterrows():
            pid = int(r["nba_api_id"])
            row = {k: "" for k in WONKA_FIELDS}
            row["source"] = SOURCE_NAME
            row["player_name"] = name_lookup.get(pid, r.get("name", ""))
            row["team"] = team_lookup.get(pid, "")
            row["position"] = pos_lookup.get(pid, "")
            row["nba_api_id"] = str(pid)
            row["games_proj"] = f"{games_lookup.get(pid, 70):.1f}"
            row["minutes_proj"] = f"{float(r.get('mpg', 0.0)):.4f}"

            for ship_col, wonka_col in SHIP_TO_WONKA.items():
                if ship_col in df.columns and pd.notna(r[ship_col]):
                    row[wonka_col] = f"{float(r[ship_col]):.4f}"

            for pct_col in ("FG_pct_proj", "FT_pct_proj", "3P_pct_proj"):
                if pct_col in df.columns and pd.notna(r.get(pct_col)):
                    row[pct_col] = f"{float(r[pct_col]):.4f}"

            # v1.1 rookie-aware columns
            method = pm_lookup.get(pid, "stan_v6.1_full")
            row["projection_method"] = method
            if method == "stan_v6.1_full":
                n_stan += 1
            elif method == "cohort_regression":
                n_soph += 1
            else:
                n_rookie += 1

            # years_in_league: 25-26 - debut_year (2024 debut = 1 year done)
            debut = debut_lookup.get(pid)
            if pd.notna(debut):
                yil = max(0, TARGET_SEASON_START_YEAR - int(debut))
                row["years_in_league"] = str(yil)

            dy = draft_dy.get(pid)
            if pd.notna(dy):
                row["draft_year"] = str(int(dy))
            dp = draft_dp.get(pid)
            if pd.notna(dp):
                row["draft_pick"] = str(int(dp))
            dr = draft_dr.get(pid)
            if pd.notna(dr):
                row["draft_round"] = str(int(dr))

            pl = league_lookup.get(pid)
            if pl:
                row["pre_nba_league"] = pl
            pt = pre_team_lookup.get(pid)
            if pt:
                row["pre_nba_team"] = pt

            csn = csn_lookup.get(pid)
            if csn:
                row["cohort_size_n"] = str(int(csn))

            # auction_value_seed: emit only for non-stan rows (vets use Yahoo $)
            if method != "stan_v6.1_full":
                seed = auction_seeds.get(pid)
                if seed is not None:
                    row["auction_value_seed"] = f"{float(seed):.2f}"

            # resolve_value: emit for ALL players — model-derived $ no Yahoo
            # dependency. Wonka Resolve uses this for Pure/Resolve Value math.
            rv = auction_seeds.get(pid)
            if rv is not None:
                row["resolve_value"] = f"{float(rv):.2f}"

            writer.writerow(row)
            written += 1

    print(f"\nWrote {written} rows -> {out_path}")
    print(f"  projection_method breakdown: stan={n_stan}  cohort={n_soph}  rookie={n_rookie}")
    print(f"  contract_version={CONTRACT_VERSION}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dryrun", action="store_true", help="Write to test path, not production")
    args = p.parse_args()
    main(dryrun=args.dryrun)
