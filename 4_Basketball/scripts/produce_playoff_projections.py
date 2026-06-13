"""Drop playoff_projections.parquet at audit_runs/{date}/ for nba_ev consumption.

Contract per D:/sports_lines/live/playoff_baseline.py + recommend.py:
  Path:  D:/NBA Projections/audit_runs/{date}/playoff_projections.parquet
  Lookup key (in recommend.py):  (int(nba_api_id), str(game_date), stat)
  Required fields:
    - nba_api_id           (int)
    - game_date            (string YYYY-MM-DD)
    - stat                 (one of PTS, REB, AST, BLK, STL, TOV, FG3M, PRA, PR, PA, RA)
    - projected_mean       (float, post-playoff-multiplier)
    - projected_sd         (float, post-playoff-multiplier)
    - model_rmse           (float, defaults 0.0)
    - n_playoff_games_prior (int, defaults 0)

How projections are produced:
  1. Load v6.1 LOCKED 25-26 ship: per-game season-rate projections.
  2. Apply per-stat playoff multiplier from
     runs/run_nba_playoffs_backtest_22_25/playoff_regime_multipliers.json
     (LOO-fit on 22-23, 23-24, 24-25 full-playoff seasons; cross-season stable).
  3. Replicate per-player rows with the bet date as game_date.

Active player cohort: players who appear in the 25-26 R1 traditional table
(played at least 1 minute in 25-26 playoff R1) AND are present in the v6.1 ship.

Usage:
  python scripts/produce_playoff_projections.py                   # today (ET)
  python scripts/produce_playoff_projections.py --date 2026-05-12
  python scripts/produce_playoff_projections.py --date 2026-05-12 --dry-run

Note on `n_playoff_games_prior`: set to count of 25-26 playoff games the player
appeared in PRIOR to bet_date. nba_ev/recommend.py uses this only for its
diagnostic readout; the projection source is the bayesian baseline.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import argparse
import json
from datetime import date as dt_date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(".")
SHIP_PATH = REPO / "audit_runs" / "unified_ship_v6_1_2025_26" / "per_player_projections_2025-26.csv"
MULT_PATH = REPO / "runs" / "run_nba_playoffs_backtest_22_25" / "playoff_regime_multipliers.json"
PLAYOFFS_R1 = REPO / "data" / "parquet" / "playoffs" / "round1"
PLAYOFFS_EXTRA = REPO / "data" / "parquet" / "playoffs" / "extra_rounds"
AUDIT_BASE = REPO / "audit_runs"
PDF_STATUS_PATH = Path("D:/sports_lines/data/nba_injury_status.parquet")
PLAYOFF_DEPTH_CHART_PATH = Path("D:/sports_lines/data/playoff_depth_chart.parquet")
META_PATH = REPO / "data" / "parquet" / "player_metadata_enriched.parquet"

# Module-level cache for the persistent InjuryStatusLookup. Loaded lazily on
# first fallback use — initialization reads pro_sports_injuries (~23K events)
# + depth chart, taking ~1-2s. One producer run amortizes the cost across
# (today, tomorrow) date emits.
_INJ_LOOKUP_CACHE = None

# Position-aware MPG redistribution constants — calibrated 2026-05-10 in
# D:/sports_lines/calibration_check_v7.py. Same-position teammate-out
# MPG redistributes more heavily than other-position.
SAME_POS_REDIST = 0.30
OTHER_POS_REDIST = 0.10

# Sanity caps to prevent the persistent injury-events source from inflating
# projections via stale OUT flags. The persistent source uses event-log +
# return-horizon-from-severity, which can carry forward an "out_for_season"
# tag from October even after a player actually returned. These caps bound
# the damage to physically plausible values.
INJURY_UPLIFT_MAX_MIN = 10.0   # max minutes one player can absorb from outs
ADJUSTED_MPG_MAX = 44.0        # max plausible playoff MPG (heavy load + OT)

PRIMARY_STATS = ["PTS", "REB", "AST", "BLK", "STL", "TOV", "FG3M"]
DERIVED_STATS = {
    "PRA": ["PTS", "REB", "AST"],
    "PR":  ["PTS", "REB"],
    "PA":  ["PTS", "AST"],
    "RA":  ["REB", "AST"],
}
ALL_STATS = PRIMARY_STATS + list(DERIVED_STATS.keys())


def _today_et() -> str:
    now = datetime.now(timezone.utc)
    et_offset = timedelta(hours=-4) if 3 <= now.month <= 10 else timedelta(hours=-5)
    return (now + et_offset).date().isoformat()


def load_multipliers() -> dict:
    with open(MULT_PATH) as f:
        m = json.load(f)
    return m["multipliers"]


def _parse_min(m):
    """Parse 'MM:SS' or numeric minutes into float."""
    if pd.isna(m) or m == "" or m is None:
        return 0.0
    if isinstance(m, (int, float)):
        return float(m)
    try:
        parts = str(m).split(":")
        return float(parts[0]) + (float(parts[1]) / 60.0 if len(parts) > 1 else 0.0)
    except (ValueError, TypeError):
        return 0.0


def load_active_cohort_2526() -> pd.DataFrame:
    """Players who appeared in 25-26 R1 (or extra_rounds when those land).

    Returns columns:
      nba_api_id, name, n_playoff_games_25_26, r1_mpg_2526
    """
    frames = []
    for src in [PLAYOFFS_R1, PLAYOFFS_EXTRA]:
        for fn in ["traditional_t0.parquet", "traditional_t1.parquet"]:
            p = src / fn
            if p.exists():
                df_full = pd.read_parquet(p)
                wanted = [c for c in
                          ["personId", "season", "gameId", "minutes",
                           "firstName", "familyName"]
                          if c in df_full.columns]
                frames.append(df_full[wanted])
    if not frames:
        return pd.DataFrame(columns=["nba_api_id", "name",
                                      "n_playoff_games_25_26", "r1_mpg_2526"])
    df = pd.concat(frames, ignore_index=True)
    df = df[df["season"] == "2025-26"].copy()
    df = df.dropna(subset=["personId"])
    df["personId"] = df["personId"].astype(int)
    df["min_played"] = df["minutes"].apply(_parse_min)
    df = df[df["min_played"] > 0]
    grouped = df.groupby("personId").agg(
        name=("firstName", lambda s: f"{s.iloc[0]} {df.loc[s.index, 'familyName'].iloc[0]}"),
        n_playoff_games_25_26=("gameId", "nunique"),
        r1_mpg_2526=("min_played", "mean"),
    ).reset_index().rename(columns={"personId": "nba_api_id"})
    return grouped


def load_player_team_lookup() -> dict:
    """Map nba_api_id -> most-recent team tricode from 25-26 playoff games."""
    frames = []
    for src in [PLAYOFFS_R1, PLAYOFFS_EXTRA]:
        for fn in ["traditional_t0.parquet", "traditional_t1.parquet"]:
            p = src / fn
            if not p.exists():
                continue
            df_full = pd.read_parquet(p)
            need = [c for c in ["personId", "season", "gameId",
                                 "teamTricode", "teamId"] if c in df_full.columns]
            sub = df_full[need]
            sub = sub[sub["season"] == "2025-26"]
            frames.append(sub)
    if not frames:
        return {}
    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["personId"])
    df["personId"] = df["personId"].astype(int)
    # Most recent team per player (gameId sorts approximately by recency)
    df = df.sort_values("gameId").drop_duplicates("personId", keep="last")
    return dict(zip(df["personId"].astype(int), df["teamTricode"].astype(str)))


def load_player_position_lookup() -> dict:
    """Map nba_api_id -> primary position class (G/F/C) for E2 same-pos check."""
    if not META_PATH.exists():
        return {}
    meta = pd.read_parquet(META_PATH)
    out = {}
    for _, r in meta.iterrows():
        pos = r.get("position")
        if not isinstance(pos, str) or not pos:
            continue
        first = pos.split("-")[0].strip().upper()
        if first.startswith("G"):
            cls = "G"
        elif first.startswith("C"):
            cls = "C"
        elif first.startswith("F"):
            cls = "F"
        else:
            continue
        try:
            out[int(r["nba_api_id"])] = cls
        except (ValueError, TypeError):
            continue
    return out


def _load_inj_lookup_persistent():
    """Lazy load + cache InjuryStatusLookup with playoff depth chart.

    Source: D:/NBA Projections/data/parquet/pro_sports_injuries_with_derived_severity.parquet
            (event log with derived return horizons; computes 'is player X out
             on date Y' from severity + games_missed)
    Depth chart: D:/sports_lines/data/playoff_depth_chart.parquet (playoff-tuned)

    This source persists across dates — unlike the PDF parquet which is
    point-in-time per report — so a player tagged OUT 5 days ago with a
    medium_term severity stays OUT on today's lookup until the return horizon
    elapses. Used as fallback when PDF source has no entries for target date.
    """
    global _INJ_LOOKUP_CACHE
    if _INJ_LOOKUP_CACHE is not None:
        return _INJ_LOOKUP_CACHE
    try:
        import sys
        sys.path.insert(0, "D:/sports_lines")
        from injury_status import InjuryStatusLookup
        depth_path = str(PLAYOFF_DEPTH_CHART_PATH) if PLAYOFF_DEPTH_CHART_PATH.exists() else None
        if depth_path:
            _INJ_LOOKUP_CACHE = InjuryStatusLookup(depth_chart_path=depth_path)
        else:
            _INJ_LOOKUP_CACHE = InjuryStatusLookup()
    except Exception as e:
        print(f"[warn] InjuryStatusLookup load failed: {e}; secondary source disabled")
        _INJ_LOOKUP_CACHE = False  # sentinel — don't re-attempt
    return _INJ_LOOKUP_CACHE


def load_tonight_outs(date_iso: str, position_lookup: dict,
                      player_mpg: dict,
                      player_team_lookup: dict | None = None,
                      season: str | None = None) -> tuple[dict, str]:
    """For target date, return ({team_tricode: [(pid, position, MPG), ...]}, source).

    Sources tried in order:
      1. PDF (D:/sports_lines/data/nba_injury_status.parquet) — best when fresh,
         has team_abbr + status directly; point-in-time per report.
      2. Persistent injury events (InjuryStatusLookup with playoff depth chart) —
         event-log + return-horizon; survives stale PDF gaps; requires team
         lookup since the source doesn't tag team by date.

    Returns ({}, "none") if neither source produces OUT entries.
    """
    # ── Primary: PDF status ────────────────────────────────────────────
    pdf_outs = _load_outs_from_pdf(date_iso, position_lookup, player_mpg)
    if pdf_outs:
        return pdf_outs, "pdf"

    # ── Fallback: persistent injury events ─────────────────────────────
    if not player_team_lookup:
        return {}, "none"
    inj = _load_inj_lookup_persistent()
    if not inj:
        return {}, "none"
    if season is None:
        # Derive season from date_iso: NBA season label
        from datetime import datetime
        d = datetime.fromisoformat(date_iso).date()
        y = d.year
        season = f"{y}-{str(y + 1)[-2:]}" if d.month >= 8 else f"{y - 1}-{str(y)[-2:]}"

    # Recency filter — drops stale event-log flags (Oct preseason out_for_season
    # tags that linger because return events were missed). Only count OUT if
    # most recent injury event for player is within RECENCY_DAYS of date_iso.
    RECENCY_DAYS = 45
    target_date = pd.Timestamp(date_iso)
    def _is_recent_out(pid: int) -> bool:
        events = inj.events_by_player.get(int(pid))
        if events is None or events.empty:
            return False
        prior = events[events["event_date"] <= target_date]
        if prior.empty:
            return False
        most_recent = prior.iloc[-1]["event_date"]
        return (target_date - most_recent).days <= RECENCY_DAYS

    teams = sorted(set(player_team_lookup.values()))
    out_by_team: dict[str, list[tuple]] = {}
    n_filtered_stale = 0
    for team in teams:
        if not team:
            continue
        try:
            outs = inj.team_high_mpg_outs(team, date_iso, season, top_n=5)
        except Exception:
            outs = []
        for pid, _rs_mpg in outs:
            if not _is_recent_out(pid):
                n_filtered_stale += 1
                continue
            pos = position_lookup.get(pid, "F")
            mpg = float(player_mpg.get(pid, _rs_mpg or 0.0))
            if mpg <= 0:
                continue
            out_by_team.setdefault(team, []).append((pid, pos, mpg))
    if n_filtered_stale > 0:
        print(f"  [recency-filter] dropped {n_filtered_stale} stale OUT flags "
              f"(events older than {RECENCY_DAYS} days)")
    if out_by_team:
        return out_by_team, "injury_events"
    return {}, "none"


def _load_outs_from_pdf(date_iso: str, position_lookup: dict,
                        player_mpg: dict) -> dict:
    """Primary source: PDF injury status parquet, point-in-time per report."""
    if not PDF_STATUS_PATH.exists():
        return {}
    inj = pd.read_parquet(PDF_STATUS_PATH)
    today_status = inj[(inj["report_date"].astype(str) == date_iso) &
                       (inj["status"].isin(["Out", "Not With Team"]))]
    if today_status.empty:
        return {}

    import unicodedata
    def _norm(name):
        if not isinstance(name, str):
            return ""
        s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
        for suf in [" jr.", " jr", " sr.", " sr", " ii", " iii", " iv"]:
            if s.endswith(suf):
                s = s[: -len(suf)]
        return "".join(c for c in s if c.isalnum() or c.isspace()).strip()
    if not META_PATH.exists():
        return {}
    meta = pd.read_parquet(META_PATH)
    name_to_pid = {}
    for _, r in meta.iterrows():
        nm = r.get("name") or r.get("player_name") or r.get("full_name")
        if isinstance(nm, str) and pd.notna(r["nba_api_id"]):
            name_to_pid[_norm(nm)] = int(r["nba_api_id"])

    out_by_team: dict[str, list[tuple]] = {}
    for _, r in today_status.iterrows():
        nm = _norm(r["player_first_last"])
        pid = name_to_pid.get(nm)
        if pid is None:
            continue
        team = str(r["team_abbr"]).upper()
        pos = position_lookup.get(pid, "F")
        mpg = float(player_mpg.get(pid, 0.0))
        if mpg <= 0:
            continue
        out_by_team.setdefault(team, []).append((pid, pos, mpg))
    return out_by_team


def compute_injury_uplift(player_pos: str, team_outs: list[tuple],
                          exclude_pid: int | None = None) -> tuple[float, float, float]:
    """Position-aware MPG uplift for one player given team's OUT teammates.

    Returns (uplift_min, same_pos_out_mpg, other_pos_out_mpg).
    """
    same = 0.0
    other = 0.0
    for pid, pos, mpg in team_outs:
        if exclude_pid is not None and pid == exclude_pid:
            continue
        if player_pos and pos == player_pos:
            same += mpg
        else:
            other += mpg
    uplift = same * SAME_POS_REDIST + other * OTHER_POS_REDIST
    return uplift, same, other


def build_per_stat_rmse() -> dict:
    """Per-stat RMSE from the 22-25 full-playoff backtest A_adj residuals."""
    res_path = REPO / "runs" / "run_nba_playoffs_backtest_22_25" / "backtest_playoff_residuals.csv"
    res = pd.read_csv(res_path, usecols=["stat", "residual_A_adj"])
    out = {}
    for stat in res["stat"].unique():
        sub = res[res["stat"] == stat]
        if len(sub) > 0:
            out[stat] = float(np.sqrt(np.mean(sub["residual_A_adj"] ** 2)))
    return out


def build_projections(date_iso: str, apply_injury_adjustment: bool = True) -> pd.DataFrame:
    multipliers = load_multipliers()
    rmse_table = build_per_stat_rmse()
    ship = pd.read_csv(SHIP_PATH)
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    cohort = load_active_cohort_2526()

    if cohort.empty:
        print("[WARN] no active 25-26 playoff cohort found; returning empty df")
        return pd.DataFrame()

    # Merge cohort with ship — only players in BOTH (active + has v6.1 projection)
    merged = cohort.merge(ship, on="nba_api_id", how="inner", suffixes=("", "_ship"))
    print(f"  active cohort with v6.1 projection: {len(merged)} players")

    # Injury-aware MPG redistribution prep
    team_lookup = load_player_team_lookup() if apply_injury_adjustment else {}
    position_lookup = load_player_position_lookup() if apply_injury_adjustment else {}
    player_po_mpg = dict(zip(merged["nba_api_id"].astype(int),
                              merged["r1_mpg_2526"].astype(float)))
    if apply_injury_adjustment:
        out_by_team, injury_source = load_tonight_outs(
            date_iso, position_lookup, player_po_mpg,
            player_team_lookup=team_lookup,
        )
        n_outs = sum(len(v) for v in out_by_team.values())
        n_teams = len(out_by_team)
        if n_outs > 0:
            print(f"  injury-aware: {n_outs} OUT players across {n_teams} teams "
                  f"for {date_iso}  (source={injury_source})")
        else:
            print(f"  injury-aware: no OUT entries for {date_iso} "
                  f"(both PDF + persistent-events sources empty)")
    else:
        out_by_team = {}
        injury_source = "disabled"

    rows = []
    for _, p in merged.iterrows():
        pid = int(p["nba_api_id"])
        nm = p.get("name") if pd.notna(p.get("name")) else p.get("name_ship", "")

        # Per-player MPG ratio: playoff MPG / RS MPG, used to scale per-game
        # projections that v6.1 produced using RS MPG. Captures playoff rotation
        # changes (starters up, bench down, DNP'd guys -> ~0).
        rs_mpg = float(p["mpg"]) if pd.notna(p.get("mpg")) and float(p["mpg"]) > 0 else None
        po_mpg = float(p["r1_mpg_2526"]) if pd.notna(p.get("r1_mpg_2526")) else None
        n_po_games = int(p["n_playoff_games_25_26"]) if pd.notna(p.get("n_playoff_games_25_26")) else 0
        if rs_mpg is None:
            mpg_ratio = 1.0
            mpg_used = "rs_only"
        elif po_mpg is None or n_po_games == 0:
            mpg_ratio = 1.0
            mpg_used = "rs_fallback_no_playoff_games"
            po_mpg = rs_mpg
        else:
            mpg_ratio = po_mpg / rs_mpg
            mpg_used = "playoff_actual" if n_po_games >= 3 else "playoff_actual_small_n"

        # Injury-aware uplift: if player's team has OUT teammates tonight,
        # bump player's expected MPG via position-aware redistribution.
        injury_uplift = 0.0
        same_pos_out_mpg = 0.0
        other_pos_out_mpg = 0.0
        player_is_out = False
        if apply_injury_adjustment and pid in team_lookup:
            player_team = team_lookup[pid]
            player_pos = position_lookup.get(pid, "F")
            team_outs = out_by_team.get(player_team, [])
            # If this player themselves is on the OUT list, project to 0
            if any(o_pid == pid for o_pid, _, _ in team_outs):
                player_is_out = True
            else:
                injury_uplift, same_pos_out_mpg, other_pos_out_mpg = compute_injury_uplift(
                    player_pos, team_outs, exclude_pid=pid,
                )
                # Sanity caps — persistent injury source can over-flag via
                # stale return horizons; bound the damage.
                if injury_uplift > INJURY_UPLIFT_MAX_MIN:
                    injury_uplift = INJURY_UPLIFT_MAX_MIN
                if injury_uplift > 0:
                    new_po_mpg = po_mpg + injury_uplift
                    if new_po_mpg > ADJUSTED_MPG_MAX:
                        new_po_mpg = ADJUSTED_MPG_MAX
                        injury_uplift = new_po_mpg - po_mpg
                    mpg_ratio = new_po_mpg / rs_mpg if rs_mpg else 1.0
                    mpg_used = "injury_adjusted"
                    po_mpg = new_po_mpg
        if player_is_out:
            # Player listed OUT tonight — project to 0 across all stats
            mpg_ratio = 0.0
            mpg_used = "out_tonight"
            po_mpg = 0.0

        per_stat_proj = {}
        per_stat_sd = {}
        for stat in PRIMARY_STATS:
            base_col = f"{stat}_per_game"
            sd_col = f"{stat}_per_game_sd"
            if base_col not in p.index or pd.isna(p[base_col]):
                continue
            base = float(p[base_col])
            base_sd = float(p[sd_col]) if pd.notna(p.get(sd_col)) else 0.0
            mult = multipliers.get(stat, 1.0)
            # Per-min playoff multiplier × playoff-MPG / RS-MPG × v6.1 per-game
            # = per_min × playoff_MPG × playoff_per_min_mult.
            # SD scales with sqrt of mpg_ratio (Poisson-like) × multiplier.
            mean = base * mpg_ratio * mult
            sd = base_sd * float(np.sqrt(mpg_ratio)) * mult
            per_stat_proj[stat] = mean
            per_stat_sd[stat] = sd
            rows.append({
                "nba_api_id": pid,
                "name": nm,
                "game_date": date_iso,
                "stat": stat,
                "projected_mean": mean,
                "projected_sd": sd,
                "model_rmse": rmse_table.get(stat, 0.0),
                "n_playoff_games_prior": n_po_games,
                # min_avg field: nba_ev's E2 layer wants this for the
                # teammate-out uplift ratio. Currently recommend.py hard-codes
                # None for the projection branch (line 110); this populated
                # field is forward-compatible once that's patched.
                "min_avg": po_mpg,
                "rs_mpg": rs_mpg,
                "playoff_mpg": po_mpg,
                "mpg_ratio": mpg_ratio,
                "mpg_source": mpg_used,
                "injury_uplift_min": injury_uplift,
                "same_pos_out_mpg": same_pos_out_mpg,
                "other_pos_out_mpg": other_pos_out_mpg,
                "player_team": team_lookup.get(pid, ""),
                "player_pos": position_lookup.get(pid, ""),
            })

        for derived, components in DERIVED_STATS.items():
            if not all(c in per_stat_proj for c in components):
                continue
            mean = sum(per_stat_proj[c] for c in components)
            sd = float(np.sqrt(sum(per_stat_sd[c] ** 2 for c in components)))
            mult = multipliers.get(derived, 1.0)
            base_sum = sum(float(p[f"{c}_per_game"]) for c in components
                           if pd.notna(p.get(f"{c}_per_game")))
            base_sd_sum = float(np.sqrt(sum(
                float(p[f"{c}_per_game_sd"]) ** 2 for c in components
                if pd.notna(p.get(f"{c}_per_game_sd"))
            )))
            # For derived stats use the derived-stat multiplier on the base
            # component sum (which still needs per-player MPG scaling).
            mean_via_derived_mult = (base_sum * mpg_ratio * mult
                                      if mult != 1.0 else mean)
            sd_via_derived_mult = (base_sd_sum * float(np.sqrt(mpg_ratio)) * mult
                                    if mult != 1.0 else sd)
            rows.append({
                "nba_api_id": pid,
                "name": nm,
                "game_date": date_iso,
                "stat": derived,
                "projected_mean": mean_via_derived_mult,
                "projected_sd": sd_via_derived_mult,
                "model_rmse": rmse_table.get(derived, 0.0),
                "n_playoff_games_prior": n_po_games,
                "min_avg": po_mpg,
                "rs_mpg": rs_mpg,
                "playoff_mpg": po_mpg,
                "mpg_ratio": mpg_ratio,
                "mpg_source": mpg_used,
                "injury_uplift_min": injury_uplift,
                "same_pos_out_mpg": same_pos_out_mpg,
                "other_pos_out_mpg": other_pos_out_mpg,
                "player_team": team_lookup.get(pid, ""),
                "player_pos": position_lookup.get(pid, ""),
            })

    df = pd.DataFrame(rows)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=_today_et(),
                    help="bet date in ISO YYYY-MM-DD (default: today ET)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print summary, do not write")
    args = ap.parse_args()

    date_iso = args.date
    print(f"Producing playoff_projections for {date_iso}")
    print(f"  v6.1 ship:  {SHIP_PATH}")
    print(f"  multipliers: {MULT_PATH}")

    df = build_projections(date_iso)
    if df.empty:
        print("  no rows produced; exiting")
        return

    print(f"  {len(df)} rows ({df['nba_api_id'].nunique()} players × "
          f"{df['stat'].nunique()} stats)")
    print(f"  per-stat row counts: {df.groupby('stat').size().to_dict()}")

    if args.dry_run:
        print("\nFirst 5 rows:")
        print(df.head().to_string())
        print(f"\n[dry-run] not writing")
        return

    out_dir = AUDIT_BASE / date_iso
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "playoff_projections.parquet"
    df.to_parquet(out_path, index=False)
    print(f"  -> {out_path}")

    # Also drop a JSON sidecar with metadata for traceability
    sidecar = {
        "produced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bet_date": date_iso,
        "n_rows": int(len(df)),
        "n_players": int(df["nba_api_id"].nunique()),
        "stats": sorted(df["stat"].unique().tolist()),
        "ship_source": str(SHIP_PATH).replace("\\", "/"),
        "multipliers_source": str(MULT_PATH).replace("\\", "/"),
        "multipliers_applied": load_multipliers(),
        "rmse_source": "runs/run_nba_playoffs_backtest_22_25/backtest_playoff_residuals.csv",
        "schema_doc": "D:/sports_lines/live/playoff_baseline.py + recommend.py",
        "notes": [
            "projected_mean = v6.1_per_game * (playoff_MPG_adjusted / RS_MPG) * per-minute_playoff_multiplier.",
            "projected_sd   = v6.1_per_game_sd * sqrt(playoff_MPG_adjusted / RS_MPG) * per-minute_playoff_multiplier (Poisson-like sd scaling).",
            "playoff_MPG = cumulative average across 25-26 playoff games to date (R1 + extra_rounds).",
            "playoff_MPG_adjusted = playoff_MPG + injury_uplift_min, where uplift = same_pos_out_mpg * 0.30 + other_pos_out_mpg * 0.10 (calibrated 2026-05-10 in D:/sports_lines/calibration_check_v7.py).",
            "OUT players on date_iso (PDF status = 'Out' or 'Not With Team') project to mpg=0 across all stats (mpg_source='out_tonight').",
            "Players on teams with OUT teammates get their MPG bumped via position-aware redistribution (mpg_source='injury_adjusted').",
            "Players on teams with no OUT teammates use cumulative playoff MPG directly (mpg_source='playoff_actual').",
            "If PDF status parquet has no entries for date_iso (stale or off-day), injury adjustment is silently skipped — producer falls back to playoff_actual MPG for all players.",
            "Per-minute playoff multiplier derived from 22-25 R1-R4 backtest's playoff_mult_loo. Cross-season + cross-round stable (per-stat range < 0.05 for primary stats).",
            "Active cohort = players with >=1 minute in 25-26 playoff games + present in v6.1 ship.",
            "n_playoff_games_prior = count of 25-26 playoff games the player has appeared in.",
            "min_avg field populated with playoff_MPG_adjusted for forward-compat with E2 teammate-out uplift; current recommend.py line 110 hard-codes None for the projection branch — field is dead-letter until that patch lands.",
            "Re-run daily via cli/playoff_daily_refresh.py at 10am ET; ad-hoc --date <YYYY-MM-DD> override available. recommend.py picks up the per-date file automatically.",
        ],
    }
    with open(out_dir / "playoff_projections_metadata.json", "w") as f:
        json.dump(sidecar, f, indent=2, default=str)
    print(f"  -> {out_dir / 'playoff_projections_metadata.json'}")


if __name__ == "__main__":
    main()
