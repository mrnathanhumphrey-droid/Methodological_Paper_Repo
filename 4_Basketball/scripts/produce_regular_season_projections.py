"""Daily RS projection producer — Phase 2 (full architecture).

Implements Phase 1c v1.1 LOCKED shrinkage architecture with:
  - schedule-driven team-pair lookup (past + future dates uniformly)
  - depth-chart-aware active rotation (two-way + G-League filtered)
  - dual-source injury lookup (PDF point-in-time + persistent events fallback)
  - position-aware MPG redistribution when teammates OUT
  - rest_days / is_b2b derived from schedule + last completed game per team
  - v6.1 ship for base + season-to-date rolling_emp + Phase 1c shrinkage

Usage:
    python scripts/produce_regular_season_projections.py YYYY-MM-DD

Output: audit_runs/rs_projections_{date}/rs_projections.parquet
        audit_runs/rs_projections_{date}/rs_projections_metadata.json

Schema columns (per row = one (player × stat) per game):
  nba_api_id, name, team_abbr, opp_team_abbr, game_date, game_id, is_home,
  position, stat, stat_class, n_prior_games, bucket, projected_mean,
  projected_sd, model_rmse, used_shrinkage, mpg_used, projected_mpg,
  season_mpg, injury_uplift_min, player_is_out, rest_days, is_b2b,
  rotation_source, spec_version
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import unicodedata

from rs_daily_projector import RSDailyProjector, RAW_STATS, RATE_STATS, PASSTHROUGH_STATS

ROOT = Path("D:/NBA Projections")
BOX = ROOT / "data/parquet/historical_box_scores.parquet"
META = ROOT / "data/parquet/player_metadata.parquet"
SHIP = ROOT / "audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv"
SCHEDULE = ROOT / "data/parquet/schedule_2025_26.parquet"
DEPTH_CHART = ROOT / "data/parquet/depth_charts_rotowire.parquet"
ROSTERS = ROOT / "data/parquet/sportradar_rosters.parquet"
INJURY_PDF = Path("D:/sports_lines/data/nba_injury_status.parquet")

MIN_MINUTES = 1
DEPTH_ORDER_ROTATION_CUTOFF = 3
SAME_POS_REDIST = 0.30
OTHER_POS_REDIST = 0.10
INJURY_UPLIFT_MAX_MIN = 10.0
ADJUSTED_MPG_MAX = 44.0
RECENCY_DAYS = 45

POS_3_FROM_PG_SG_SF_PF_C = {"PG": "G", "SG": "G", "SF": "F", "PF": "F", "C": "C"}

_INJ_LOOKUP_CACHE = None


def _norm_name(name) -> str:
    if not isinstance(name, str):
        return ""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
    for suf in [" jr.", " jr", " sr.", " sr", " ii", " iii", " iv"]:
        if s.endswith(suf):
            s = s[: -len(suf)]
    return "".join(c for c in s if c.isalnum() or c.isspace()).strip()


def parse_opp(matchup: str, team_abbr: str) -> str:
    parts = matchup.split()
    if team_abbr == parts[0]:
        return parts[-1]
    return parts[0]


def build_name_to_pid(meta: pd.DataFrame) -> dict:
    out = {}
    for _, r in meta.iterrows():
        nm = r.get("name")
        if isinstance(nm, str) and pd.notna(r["nba_api_id"]):
            out[_norm_name(nm)] = int(r["nba_api_id"])
    return out


def load_active_rotation_from_depth_chart(depth_df: pd.DataFrame,
                                          name_to_pid: dict) -> dict:
    """Per team_abbr, return set of nba_api_ids in projected rotation
    (depth_order <= cutoff, NOT two-way)."""
    rot = depth_df[
        (depth_df["depth_order"] <= DEPTH_ORDER_ROTATION_CUTOFF)
        & (depth_df["two_way"] == False)
    ].copy()
    out: dict[str, set[int]] = {}
    n_unmatched = 0
    for _, r in rot.iterrows():
        team = str(r["team_abbr"]).upper()
        pid = name_to_pid.get(_norm_name(r["player_name"]))
        if pid is None:
            n_unmatched += 1
            continue
        out.setdefault(team, set()).add(pid)
    return out, n_unmatched


def load_outs_from_pdf(date_iso: str, position_lookup: dict,
                       player_mpg: dict, name_to_pid: dict) -> dict:
    """PDF point-in-time OUT lookup. Returns {team_abbr: [(pid, pos3, mpg), ...]}."""
    if not INJURY_PDF.exists():
        return {}
    inj = pd.read_parquet(INJURY_PDF)
    today = inj[(inj["report_date"].astype(str) == date_iso)
                & (inj["status"].isin(["Out", "Not With Team"]))]
    if today.empty:
        return {}
    out: dict[str, list] = {}
    for _, r in today.iterrows():
        pid = name_to_pid.get(_norm_name(r["player_first_last"]))
        if pid is None:
            continue
        team = str(r["team_abbr"]).upper()
        pos = position_lookup.get(pid, "F")
        mpg = float(player_mpg.get(pid, 0.0))
        if mpg <= 0:
            continue
        out.setdefault(team, []).append((pid, pos, mpg))
    return out


def load_outs_from_persistent_events(date_iso: str, season: str,
                                     team_lookup: dict,
                                     position_lookup: dict,
                                     player_mpg: dict) -> dict:
    """Fallback: persistent injury event log with return-horizon-from-severity."""
    global _INJ_LOOKUP_CACHE
    if _INJ_LOOKUP_CACHE is False:
        return {}
    if _INJ_LOOKUP_CACHE is None:
        try:
            sys.path.insert(0, "D:/sports_lines")
            from injury_status import InjuryStatusLookup
            _INJ_LOOKUP_CACHE = InjuryStatusLookup()
        except Exception as e:
            print(f"  [warn] persistent injury lookup unavailable: {e}")
            _INJ_LOOKUP_CACHE = False
            return {}
    inj = _INJ_LOOKUP_CACHE
    target = pd.Timestamp(date_iso)

    def _is_recent(pid: int) -> bool:
        events = inj.events_by_player.get(int(pid))
        if events is None or events.empty:
            return False
        prior = events[events["event_date"] <= target]
        if prior.empty:
            return False
        most_recent = prior.iloc[-1]["event_date"]
        return (target - most_recent).days <= RECENCY_DAYS

    teams = sorted(set(team_lookup.values()))
    out: dict[str, list] = {}
    n_stale = 0
    for team in teams:
        if not team:
            continue
        try:
            entries = inj.team_high_mpg_outs(team, date_iso, season, top_n=5)
        except Exception:
            entries = []
        for pid, _ in entries:
            if not _is_recent(pid):
                n_stale += 1
                continue
            pos = position_lookup.get(pid, "F")
            mpg = float(player_mpg.get(pid, 0.0))
            if mpg <= 0:
                continue
            out.setdefault(team, []).append((pid, pos, mpg))
    if n_stale:
        print(f"  [recency-filter] dropped {n_stale} stale OUT flags (>{RECENCY_DAYS} days)")
    return out


def compute_injury_uplift(player_pos3: str, team_outs: list, exclude_pid: int) -> tuple:
    same = other = 0.0
    for pid, pos, mpg in team_outs:
        if pid == exclude_pid:
            continue
        if player_pos3 and pos == player_pos3:
            same += mpg
        else:
            other += mpg
    uplift = min(same * SAME_POS_REDIST + other * OTHER_POS_REDIST, INJURY_UPLIFT_MAX_MIN)
    return uplift, same, other


def derive_season(date_iso: str) -> str:
    d = pd.Timestamp(date_iso).date()
    y = d.year
    return f"{y}-{str(y + 1)[-2:]}" if d.month >= 8 else f"{y - 1}-{str(y)[-2:]}"


def position_3tier_from_metadata(position_str) -> str | None:
    if not isinstance(position_str, str):
        return None
    s = position_str.strip().upper()
    if s.startswith("G") or s in ("PG", "SG"):
        return "G"
    if s.startswith("C"):
        return "C"
    if s.startswith("F") or s in ("SF", "PF"):
        return "F"
    return None


def compute_rest_b2b_from_schedule(schedule: pd.DataFrame, target_date) -> dict:
    """For each team, find last completed game prior to target_date. Returns
    {team_abbr: (rest_days, is_b2b)}."""
    target_pd = pd.Timestamp(target_date)
    out = {}
    rs = schedule[
        (schedule["season_type"] == "Regular Season")
        & (pd.to_datetime(schedule["game_date"]) < target_pd)
    ].copy()
    rs["game_date"] = pd.to_datetime(rs["game_date"])
    home = rs[["game_date", "home_team_abbr"]].rename(columns={"home_team_abbr": "team_abbr"})
    away = rs[["game_date", "away_team_abbr"]].rename(columns={"away_team_abbr": "team_abbr"})
    all_team_games = pd.concat([home, away], ignore_index=True)
    last = all_team_games.groupby("team_abbr")["game_date"].max().reset_index()
    for _, r in last.iterrows():
        days = (target_pd - r["game_date"]).days
        out[r["team_abbr"]] = (int(days), days == 1)
    return out


def determine_active_cohort(target_date, schedule: pd.DataFrame,
                            box: pd.DataFrame,
                            depth_rotation: dict,
                            ship_pids: set,
                            name_to_pid: dict) -> tuple[pd.DataFrame, str]:
    """For each scheduled team on target_date, determine projected active
    rotation. Past-date: use actual box-score appearances. Future-date:
    use depth-chart rotation + active roster.

    Returns (cohort_df, source_label).
    Columns: nba_api_id, name, team_abbr, opp_team_abbr, game_id, is_home, position
    """
    target_pd = pd.Timestamp(target_date)
    target_iso = target_pd.date().isoformat()

    box_today = box[
        (box["season_type"] == "Regular Season")
        & (pd.to_datetime(box["game_date"]).dt.date == target_pd.date())
    ]
    if len(box_today) > 0:
        meta = pd.read_parquet(META)[["nba_api_id", "name", "position"]]
        cohort = box_today[["nba_api_id", "game_id", "team_abbr", "matchup", "is_home"]].drop_duplicates()
        cohort = cohort.merge(meta, on="nba_api_id", how="left")
        cohort["opp_team_abbr"] = cohort.apply(lambda r: parse_opp(r["matchup"], r["team_abbr"]), axis=1)
        cohort = cohort[["nba_api_id", "name", "team_abbr", "opp_team_abbr",
                         "game_id", "is_home", "position"]]
        return cohort, "box_score_actuals"

    sched_today = schedule[
        (schedule["season_type"] == "Regular Season")
        & (pd.to_datetime(schedule["game_date"]).dt.date == target_pd.date())
    ].copy()
    if sched_today.empty:
        return pd.DataFrame(), "no_games"

    meta = pd.read_parquet(META)[["nba_api_id", "name", "position"]]
    rows = []
    for _, g in sched_today.iterrows():
        for team_abbr, opp_abbr, is_home in [
            (g["home_team_abbr"], g["away_team_abbr"], True),
            (g["away_team_abbr"], g["home_team_abbr"], False),
        ]:
            team_pids = depth_rotation.get(str(team_abbr).upper(), set())
            team_pids = team_pids & ship_pids
            for pid in team_pids:
                rows.append({
                    "nba_api_id": pid,
                    "team_abbr": team_abbr,
                    "opp_team_abbr": opp_abbr,
                    "game_id": g["game_id"],
                    "is_home": is_home,
                })
    cohort = pd.DataFrame(rows)
    if cohort.empty:
        return cohort, "depth_chart_no_match"
    cohort = cohort.merge(meta, on="nba_api_id", how="left")
    cohort = cohort[["nba_api_id", "name", "team_abbr", "opp_team_abbr",
                     "game_id", "is_home", "position"]]
    return cohort, "depth_chart"


def compute_rolling_emp_and_n_g(target_date, box: pd.DataFrame,
                                cohort_pids: list) -> pd.DataFrame:
    """For each player in cohort_pids, compute n_prior_games + rolling_emp
    per stat (including USG) from prior 25-26 RS games (causal, no look-ahead)."""
    target_pd = pd.Timestamp(target_date)
    prior = box[
        (box["season"] == "2025-26")
        & (box["season_type"] == "Regular Season")
        & (pd.to_datetime(box["game_date"]) < target_pd)
        & (box["minutes"] >= MIN_MINUTES)
        & (box["nba_api_id"].isin(cohort_pids))
    ].copy()
    counting_stats = list(RAW_STATS) + list(PASSTHROUGH_STATS)
    rolling_cols = counting_stats + ["USG"]
    if prior.empty:
        return pd.DataFrame({"nba_api_id": cohort_pids,
                             "n_prior_games": 0,
                             "season_mpg": np.nan,
                             **{f"rolling_emp_{s}": np.nan for s in rolling_cols}})

    team_tot = (
        prior.groupby(["game_id", "team_abbr"], observed=True)
             .agg(team_FGA=("FGA", "sum"), team_FTA=("FTA", "sum"),
                  team_TOV=("TOV", "sum"), team_MP=("minutes", "sum"))
             .reset_index()
    )
    prior = prior.merge(team_tot, on=["game_id", "team_abbr"], how="left")
    poss_player = prior["FGA"] + 0.44 * prior["FTA"] + prior["TOV"]
    poss_team = prior["team_FGA"] + 0.44 * prior["team_FTA"] + prior["team_TOV"]
    denom_usg = prior["minutes"] * poss_team
    num_usg = poss_player * (prior["team_MP"] / 5.0)
    prior["USG"] = 100.0 * num_usg / denom_usg.replace(0, np.nan)

    agg = (
        prior.groupby("nba_api_id", observed=True)
             .agg(n_prior_games=("PTS", "size"),
                  season_mpg=("minutes", "mean"),
                  **{f"rolling_emp_{s}": (s, "mean") for s in counting_stats},
                  rolling_emp_USG=("USG", "mean"))
             .reset_index()
    )
    missing_pids = set(cohort_pids) - set(agg["nba_api_id"].astype(int))
    if missing_pids:
        zeros = pd.DataFrame({"nba_api_id": list(missing_pids), "n_prior_games": 0,
                              "season_mpg": np.nan,
                              **{f"rolling_emp_{s}": np.nan for s in rolling_cols}})
        agg = pd.concat([agg, zeros], ignore_index=True)
    return agg


PRIOR_SEASON_MAP = {"2025-26": "2024-25", "2024-25": "2023-24",
                    "2023-24": "2022-23", "2022-23": "2021-22"}


def load_prior_season_usg_means(season: str) -> dict:
    """Per-player prior-season mean USG for 'v6.1 substitute' on USG.

    Reads player_season_means.parquet (with mean_USG column added by the
    Phase 1c v1.2 fire script). Returns {nba_api_id: mean_USG} for the
    prior season relative to target.
    """
    p = ROOT / "runs/run_nba_rs_phase_1c_22_25/player_season_means.parquet"
    if not p.exists():
        return {}
    df = pd.read_parquet(p)
    prior_season = PRIOR_SEASON_MAP.get(season)
    if prior_season is None or "mean_USG" not in df.columns:
        return {}
    sub = df[(df["season"] == prior_season) & df["mean_USG"].notna()]
    return dict(zip(sub["nba_api_id"].astype(int), sub["mean_USG"].astype(float)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("target_date", help="YYYY-MM-DD")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    target = pd.to_datetime(args.target_date).normalize()
    season = derive_season(args.target_date)

    print(f"=== RS daily projection for {target.date()} (season {season}) ===")

    box = pd.read_parquet(BOX)
    schedule = pd.read_parquet(SCHEDULE)
    meta = pd.read_parquet(META)
    ship = pd.read_csv(SHIP)
    ship_pids = set(int(x) for x in ship["nba_api_id"].dropna().astype(int))

    name_to_pid = build_name_to_pid(meta)
    depth_df = pd.read_parquet(DEPTH_CHART)
    depth_rotation, n_dc_unmatched = load_active_rotation_from_depth_chart(depth_df, name_to_pid)
    if n_dc_unmatched:
        print(f"  depth-chart name->pid unmatched: {n_dc_unmatched}")

    cohort, cohort_source = determine_active_cohort(
        target, schedule, box, depth_rotation, ship_pids, name_to_pid
    )
    if cohort.empty:
        print(f"  no active cohort for {target.date()} (source={cohort_source}). Exiting.")
        sys.exit(0)
    print(f"  cohort: {len(cohort):,} player-games  ({cohort['nba_api_id'].nunique()} unique players)  "
          f"source={cohort_source}")

    pos_lookup = {}
    for pid in cohort["nba_api_id"].unique():
        pos_str = cohort[cohort["nba_api_id"] == pid]["position"].iloc[0]
        p3 = position_3tier_from_metadata(pos_str)
        if p3:
            pos_lookup[int(pid)] = p3

    team_lookup = dict(zip(cohort["nba_api_id"].astype(int), cohort["team_abbr"]))

    rolling = compute_rolling_emp_and_n_g(target, box, cohort["nba_api_id"].astype(int).tolist())
    cohort = cohort.merge(rolling, on="nba_api_id", how="left")

    cohort = cohort.merge(
        ship.set_index("nba_api_id")[
            [f"{s}_per_game" for s in RAW_STATS + PASSTHROUGH_STATS]
            + [f"{s}_per_game_sd" for s in RAW_STATS + PASSTHROUGH_STATS]
            + ["mpg"]
        ],
        left_on="nba_api_id", right_index=True, how="left"
    ).rename(columns={"mpg": "ship_mpg"})

    usg_v61_lookup = load_prior_season_usg_means(season)
    cohort["USG_v61"] = cohort["nba_api_id"].astype(int).map(usg_v61_lookup)

    cohort["season_mpg"] = cohort["season_mpg"].fillna(cohort["ship_mpg"])

    player_mpg_universal = dict(zip(
        ship["nba_api_id"].astype(int), ship["mpg"].fillna(0.0).astype(float)
    ))
    pos_lookup_universal = {}
    meta_for_pos = meta[["nba_api_id", "position"]].copy()
    for _, r in meta_for_pos.iterrows():
        p3 = position_3tier_from_metadata(r["position"])
        if p3:
            pos_lookup_universal[int(r["nba_api_id"])] = p3
    for pid, p3 in pos_lookup.items():
        pos_lookup_universal[pid] = p3

    out_by_team = load_outs_from_pdf(args.target_date, pos_lookup_universal,
                                     player_mpg_universal, name_to_pid)
    injury_source = "pdf"
    if not out_by_team:
        out_by_team = load_outs_from_persistent_events(
            args.target_date, season, team_lookup, pos_lookup_universal,
            player_mpg_universal,
        )
        injury_source = "persistent_events" if out_by_team else "none"
    n_outs = sum(len(v) for v in out_by_team.values())
    print(f"  injury-aware: {n_outs} OUT players across {len(out_by_team)} teams  source={injury_source}")

    rest_b2b = compute_rest_b2b_from_schedule(schedule, target)

    projector = RSDailyProjector()

    out_rows = []
    n_player_is_out = 0
    n_injury_adjusted = 0
    for _, row in cohort.iterrows():
        pid = int(row["nba_api_id"])
        team = row["team_abbr"]
        if pd.isna(row.get("PTS_per_game")):
            continue
        n_g = int(row["n_prior_games"]) if pd.notna(row["n_prior_games"]) else 0

        team_outs = out_by_team.get(team, [])
        player_is_out = any(o_pid == pid for o_pid, _, _ in team_outs)

        season_mpg = float(row["season_mpg"]) if pd.notna(row.get("season_mpg")) else float("nan")
        projected_mpg = season_mpg
        injury_uplift = 0.0
        mpg_used = "season_avg"

        if player_is_out:
            projected_mpg = 0.0
            mpg_ratio = 0.0
            mpg_used = "out_today"
            n_player_is_out += 1
        else:
            player_pos3 = pos_lookup.get(pid, "F")
            if team_outs:
                injury_uplift, _, _ = compute_injury_uplift(player_pos3, team_outs, pid)
            if injury_uplift > 0 and not np.isnan(season_mpg) and season_mpg > 0:
                projected_mpg = min(season_mpg + injury_uplift, ADJUSTED_MPG_MAX)
                mpg_used = "injury_uplift"
                n_injury_adjusted += 1
            if season_mpg and not np.isnan(season_mpg) and season_mpg > 0:
                mpg_ratio = projected_mpg / season_mpg
            else:
                mpg_ratio = 1.0

        rd, is_b2b = rest_b2b.get(team, (None, None))

        for s in RAW_STATS:
            v61 = row[f"{s}_per_game"]
            sd = row[f"{s}_per_game_sd"]
            rolling_v = row.get(f"rolling_emp_{s}")
            if pd.isna(v61):
                continue
            res = projector.project_single(
                stat=s, n_g=n_g,
                rolling_emp=float(rolling_v) if pd.notna(rolling_v) else float("nan"),
                v61_per_game=float(v61),
                v61_sd=float(sd) if pd.notna(sd) else float("nan"),
            )
            mean = res["projected_mean"] * mpg_ratio
            sd_scaled = res["projected_sd"] * (float(np.sqrt(mpg_ratio)) if mpg_ratio > 0 else 0.0)
            out_rows.append({
                "nba_api_id": pid, "name": row.get("name"),
                "team_abbr": team, "opp_team_abbr": row["opp_team_abbr"],
                "game_date": target.date().isoformat(), "game_id": row["game_id"],
                "is_home": bool(row["is_home"]), "position": row.get("position"),
                "stat": s, "stat_class": "raw",
                "n_prior_games": n_g, "bucket": res["bucket"],
                "projected_mean": mean, "projected_sd": sd_scaled,
                "model_rmse": res["model_rmse"],
                "used_shrinkage": res["used_shrinkage"],
                "mpg_used": mpg_used, "projected_mpg": projected_mpg,
                "season_mpg": season_mpg,
                "injury_uplift_min": injury_uplift, "player_is_out": player_is_out,
                "rest_days": rd, "is_b2b": is_b2b,
                "rotation_source": cohort_source,
                "spec_version": projector.spec_version,
            })

        for s in RATE_STATS:
            v61 = row.get(f"{s}_v61")
            rolling_v = row.get(f"rolling_emp_{s}")
            if pd.isna(v61):
                continue
            res = projector.project_single(
                stat=s, n_g=n_g,
                rolling_emp=float(rolling_v) if pd.notna(rolling_v) else float("nan"),
                v61_per_game=float(v61),
                v61_sd=float("nan"),
            )
            mean = res["projected_mean"] if not player_is_out else 0.0
            out_rows.append({
                "nba_api_id": pid, "name": row.get("name"),
                "team_abbr": team, "opp_team_abbr": row["opp_team_abbr"],
                "game_date": target.date().isoformat(), "game_id": row["game_id"],
                "is_home": bool(row["is_home"]), "position": row.get("position"),
                "stat": s, "stat_class": "rate",
                "n_prior_games": n_g, "bucket": res["bucket"],
                "projected_mean": mean, "projected_sd": float("nan"),
                "model_rmse": res["model_rmse"],
                "used_shrinkage": res["used_shrinkage"],
                "mpg_used": "rate_no_scaling", "projected_mpg": projected_mpg,
                "season_mpg": season_mpg,
                "injury_uplift_min": injury_uplift, "player_is_out": player_is_out,
                "rest_days": rd, "is_b2b": is_b2b,
                "rotation_source": cohort_source,
                "spec_version": projector.spec_version,
            })

        for s in PASSTHROUGH_STATS:
            v61 = row[f"{s}_per_game"]
            sd = row[f"{s}_per_game_sd"]
            if pd.isna(v61):
                continue
            res = projector.project_passthrough(
                stat=s, v61_per_game=float(v61),
                v61_sd=float(sd) if pd.notna(sd) else float("nan"),
            )
            mean = res["projected_mean"] * mpg_ratio
            sd_scaled = res["projected_sd"] * (float(np.sqrt(mpg_ratio)) if mpg_ratio > 0 else 0.0)
            out_rows.append({
                "nba_api_id": pid, "name": row.get("name"),
                "team_abbr": team, "opp_team_abbr": row["opp_team_abbr"],
                "game_date": target.date().isoformat(), "game_id": row["game_id"],
                "is_home": bool(row["is_home"]), "position": row.get("position"),
                "stat": s, "stat_class": "ma_pair_passthrough",
                "n_prior_games": n_g, "bucket": res["bucket"],
                "projected_mean": mean, "projected_sd": sd_scaled,
                "model_rmse": float("nan"),
                "used_shrinkage": False,
                "mpg_used": mpg_used, "projected_mpg": projected_mpg,
                "season_mpg": season_mpg,
                "injury_uplift_min": injury_uplift, "player_is_out": player_is_out,
                "rest_days": rd, "is_b2b": is_b2b,
                "rotation_source": cohort_source,
                "spec_version": projector.spec_version,
            })

    out = pd.DataFrame(out_rows)
    out_dir = ROOT / f"audit_runs/rs_projections_{target.date().isoformat()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "rs_projections.parquet"

    print(f"  rows: {len(out):,}  players: {out['nba_api_id'].nunique()}  "
          f"shrinkage_rows: {out['used_shrinkage'].sum():,}  "
          f"OUT_players: {n_player_is_out}  injury_adjusted: {n_injury_adjusted}")

    if args.dry_run:
        print("\n[dry-run] not writing")
        return

    out.to_parquet(out_path, index=False)
    print(f"  -> {out_path}")

    meta_sidecar = {
        "produced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target_date": target.date().isoformat(),
        "season": season,
        "n_rows": int(len(out)),
        "n_players": int(out["nba_api_id"].nunique()),
        "rotation_source": cohort_source,
        "injury_source": injury_source,
        "n_outs": n_outs,
        "n_player_is_out": n_player_is_out,
        "n_injury_adjusted": n_injury_adjusted,
        "spec_version": projector.spec_version,
        "shrinkage_cells_loaded_from": str(projector.ship_cells),
    }
    with open(out_dir / "rs_projections_metadata.json", "w") as f:
        json.dump(meta_sidecar, f, indent=2, default=str)
    print(f"  -> {out_dir / 'rs_projections_metadata.json'}")


if __name__ == "__main__":
    main()
