"""PBP garbage-time vs clutch residual variance test (Tier-1 pre-registered).

Pre-registration: audit_runs/pbp_garbage_clutch_pre_reg/PRE_REGISTRATION.md
(filed 2026-05-07, signed off before this analysis ran).

Test: For each volume stat S in {PTS, REB, AST}, does
  σ(rate_state_garbage − r_bar) > σ(rate_state_clutch − r_bar)
hold across a cohort of players with ≥30 min in each state, ≥5 GP,
in the 2024-25 NBA regular season?

Approximation note (documented in pre-reg Section 4): on-court window per
player per game is [first_event_time, last_event_time] for events attributed
to that player, intersected with state durations. This overestimates court-time
for benched-mid-game players; the ≥30-min cohort filter and within-game
residual computation absorb most of the bias, but it is honest to flag.

Output: audit_runs/pbp_garbage_clutch/
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(r"D:/NBA Projections")
PBP_DIR = ROOT / "data" / "parquet" / "pbp"
OUT_BASE = ROOT / "audit_runs" / "pbp_garbage_clutch"
OUT_BASE.mkdir(parents=True, exist_ok=True)

import argparse
_p = argparse.ArgumentParser()
_p.add_argument("--season", default="2024-25")
_args = _p.parse_args()
TEST_SEASON = _args.season
PBP_FILE = PBP_DIR / f"pbp_{TEST_SEASON}.parquet"

CLOCK_RE = re.compile(r"PT(\d+)M([\d.]+)S")
AST_RE = re.compile(r"\(([A-Za-z\.\-' ]+?)\s+\d+\s+AST\)")
SUB_RE = re.compile(r"SUB:\s+([A-Za-z\.\-' ]+?)\s+FOR\s+([A-Za-z\.\-' ]+)")


def clock_secs_remaining(s):
    if pd.isna(s): return np.nan
    m = CLOCK_RE.match(str(s))
    if not m: return np.nan
    return int(m.group(1)) * 60 + float(m.group(2))


def parse_score(v):
    try: return int(v)
    except (ValueError, TypeError): return None


def to_abs_secs(period, secs_remaining):
    """Absolute seconds elapsed since game start."""
    if pd.isna(period) or pd.isna(secs_remaining): return np.nan
    if period <= 4:
        period_len = 720
        return (period - 1) * 720 + (period_len - secs_remaining)
    period_len = 300  # OT
    return 4 * 720 + (period - 5) * 300 + (period_len - secs_remaining)


def state_for(period, secs_remaining, abs_margin):
    if pd.isna(period) or pd.isna(secs_remaining) or pd.isna(abs_margin):
        return "neutral"
    if period >= 4 and secs_remaining < 300 and abs_margin <= 5:
        return "clutch"
    if secs_remaining < 300 and abs_margin > 20:
        return "garbage"
    return "neutral"


def build_name_lookup(df):
    """Return dict (game_id, team_tricode) -> {last_name: person_id}.
    Uses last token of player_name as the surname key."""
    sub = df[(df["person_id"].fillna(0) > 0) & (df["player_name"].astype(str).str.len() > 0)]
    # Use the last whitespace-separated token as 'surname' key
    sub = sub.copy()
    sub["surname"] = sub["player_name"].astype(str).str.split().str[-1]
    grp = sub.groupby(["game_id", "team_tricode", "surname"])["person_id"].first()
    out = {}
    for (gid, tri, sn), pid in grp.items():
        out.setdefault((gid, tri), {})[sn] = int(pid)
    return out


def resolve_player(name_str, game_id, team_tricode, lookup):
    if not name_str: return None
    candidate = name_str.strip()
    surname = candidate.split()[-1] if " " in candidate else candidate
    table = lookup.get((game_id, team_tricode), {})
    if surname in table: return table[surname]
    # Try matching the full given string as surname
    if candidate in table: return table[candidate]
    return None


def process_one_game(game_pbp, name_lookup):
    """Returns:
       - state_durations: dict[(person_id, state)] -> seconds of on-court state minutes
       - state_counts: dict[(person_id, state, stat)] -> count
       Approximation: on-court window for player p = [first_event_secs, last_event_secs]."""

    if len(game_pbp) == 0: return {}, {}, {}

    g = game_pbp.copy()
    g = g.sort_values(["period", "action_number"])
    g["secs_rem"] = g["clock"].apply(clock_secs_remaining)
    g["abs_secs"] = g.apply(lambda r: to_abs_secs(r["period"], r["secs_rem"]), axis=1)
    g["score_h"] = g["score_home"].apply(parse_score).ffill().fillna(0).astype(int)
    g["score_a"] = g["score_away"].apply(parse_score).ffill().fillna(0).astype(int)
    g["abs_margin"] = (g["score_h"] - g["score_a"]).abs()
    g["state"] = g.apply(
        lambda r: state_for(r["period"], r["secs_rem"], r["abs_margin"]), axis=1)

    game_id = g["game_id"].iloc[0]

    # Compute per-state durations across the whole game
    g_sorted = g.dropna(subset=["abs_secs"]).sort_values("abs_secs").reset_index(drop=True)
    if len(g_sorted) == 0: return {}, {}, {}

    state_intervals = []
    for i in range(len(g_sorted) - 1):
        t0 = g_sorted.loc[i, "abs_secs"]
        t1 = g_sorted.loc[i + 1, "abs_secs"]
        state_now = g_sorted.loc[i, "state"]
        if t1 > t0:
            state_intervals.append((t0, t1, state_now))

    # Per-player on-court window: first to last event with their person_id involved
    # Including: actor (person_id), assister (parsed from desc), and substitution-in
    player_first = {}
    player_last = {}

    def update_window(pid, t):
        if pid is None or pid == 0 or pd.isna(pid) or pd.isna(t): return
        pid = int(pid)
        if pid not in player_first: player_first[pid] = t
        player_first[pid] = min(player_first[pid], t)
        player_last[pid] = max(player_last.get(pid, t), t)

    state_counts = {}  # (pid, state, stat) -> count
    def add_count(pid, state, stat, val=1):
        if pid is None or pid == 0 or pd.isna(pid): return
        key = (int(pid), state, stat)
        state_counts[key] = state_counts.get(key, 0) + val

    for _, ev in g_sorted.iterrows():
        t = ev["abs_secs"]
        s = ev["state"]
        atype = ev["action_type"]
        pid = ev["person_id"]
        team = ev["team_tricode"]

        update_window(pid, t)

        if atype == "Made Shot":
            sv = ev.get("shot_value", 0)
            try: sv = int(sv) if pd.notna(sv) else 0
            except (ValueError, TypeError): sv = 0
            add_count(pid, s, "PTS", sv)
            # Assist
            m = AST_RE.search(str(ev.get("description", "")))
            if m:
                ast_pid = resolve_player(m.group(1), game_id, team, name_lookup)
                if ast_pid:
                    add_count(ast_pid, s, "AST", 1)
                    update_window(ast_pid, t)
        elif atype == "Free Throw":
            if str(ev.get("shot_result", "")) == "Made":
                add_count(pid, s, "PTS", 1)
        elif atype == "Rebound":
            add_count(pid, s, "REB", 1)
        elif atype == "Substitution":
            m = SUB_RE.search(str(ev.get("description", "")))
            if m:
                in_name, out_name = m.group(1), m.group(2)
                in_pid = resolve_player(in_name, game_id, team, name_lookup)
                if in_pid:
                    update_window(in_pid, t)
                update_window(pid, t)  # OUT player

    # Compute per-player per-state durations: intersect on-court window with state intervals
    state_durations = {}
    for pid in player_first:
        first = player_first[pid]
        last = player_last[pid]
        for t0, t1, s in state_intervals:
            overlap_start = max(t0, first)
            overlap_end = min(t1, last)
            if overlap_end > overlap_start:
                key = (pid, s)
                state_durations[key] = state_durations.get(key, 0) + (overlap_end - overlap_start)

    return state_durations, state_counts, {pid: (player_first[pid], player_last[pid])
                                             for pid in player_first}


def main():
    print(f"[load] {PBP_FILE}")
    df = pd.read_parquet(PBP_FILE)
    df = df[df["season_type"] == "Regular Season"].copy()
    df["game_id"] = df["game_id"].astype(str)
    print(f"  {len(df)} regular-season events, "
          f"{df['game_id'].nunique()} games, "
          f"{df['person_id'].nunique()} unique person_ids")

    print("[build] name lookup table")
    name_lookup = build_name_lookup(df)
    print(f"  {len(name_lookup)} (game, team) keys")

    print("[process] per-game state durations + stat counts")
    all_dur = []  # rows: pid, game_id, state, seconds
    all_counts = []  # rows: pid, game_id, state, stat, count
    n_games = df["game_id"].nunique()
    for i, (gid, gdf) in enumerate(df.groupby("game_id")):
        if i % 200 == 0:
            print(f"  [{i+1}/{n_games}] game_id={gid}")
        durations, counts, _ = process_one_game(gdf, name_lookup)
        for (pid, s), secs in durations.items():
            all_dur.append((pid, gid, s, secs))
        for (pid, s, stat), c in counts.items():
            all_counts.append((pid, gid, s, stat, c))

    dur_df = pd.DataFrame(all_dur, columns=["person_id", "game_id", "state", "seconds"])
    cnt_df = pd.DataFrame(all_counts, columns=["person_id", "game_id", "state", "stat", "count"])

    # Per-player season totals per state
    season_state_min = (dur_df.groupby(["person_id", "state"])["seconds"]
                        .sum().reset_index())
    season_state_min["minutes"] = season_state_min["seconds"] / 60.0
    season_pivot = season_state_min.pivot(
        index="person_id", columns="state", values="minutes").fillna(0)

    # Cohort filter: ≥30 min in clutch AND garbage
    season_pivot["games"] = (dur_df.groupby("person_id")["game_id"].nunique()
                              .reindex(season_pivot.index).fillna(0))
    cohort = season_pivot[
        (season_pivot.get("clutch", 0) >= 30)
        & (season_pivot.get("garbage", 0) >= 30)
        & (season_pivot["games"] >= 5)
    ].copy()
    print(f"\n[cohort] {len(cohort)} players pass ≥30 min clutch + ≥30 min garbage + ≥5 GP")

    OUT = OUT_BASE / TEST_SEASON
    OUT.mkdir(parents=True, exist_ok=True)
    cohort.to_csv(OUT / "cohort.csv")

    # Per-player baseline rate (per-minute, season pooled across all states)
    total_counts = cnt_df.groupby(["person_id", "stat"])["count"].sum().reset_index()
    total_minutes = (dur_df.groupby("person_id")["seconds"].sum() / 60.0).rename("total_min")

    # Per-game per-state rate residuals
    rows = []
    for stat in ["PTS", "REB", "AST"]:
        # Player baseline rate
        baseline = (total_counts[total_counts["stat"] == stat].set_index("person_id")["count"]
                    / total_minutes).rename("baseline_rate")

        # Per-game per-state aggregates
        cnt_state = cnt_df[cnt_df["stat"] == stat]
        merged = cnt_state.merge(dur_df, on=["person_id", "game_id", "state"], how="outer")
        merged["count"] = merged["count"].fillna(0)
        merged = merged[merged["seconds"] > 0].copy()
        merged["minutes"] = merged["seconds"] / 60.0
        merged = merged.merge(baseline, left_on="person_id", right_index=True, how="left")
        merged["rate"] = merged["count"] / merged["minutes"]
        merged["residual"] = merged["rate"] - merged["baseline_rate"]
        merged = merged[merged["person_id"].isin(cohort.index)].copy()

        merged["stat"] = stat
        rows.append(merged)

    resid_df = pd.concat(rows, ignore_index=True)
    resid_df.to_csv(OUT / "residuals_per_game.csv", index=False)

    # Tier-1 test per stat
    test_rows = []
    for stat in ["PTS", "REB", "AST"]:
        sub = resid_df[(resid_df["stat"] == stat)
                        & (resid_df["state"].isin(["clutch", "garbage"]))].copy()
        # Drop any rows with insufficient minutes per game-state (< 0.5 min)
        sub = sub[sub["minutes"] >= 0.5]
        clutch = sub.loc[sub["state"] == "clutch", "residual"].dropna().values
        garbage = sub.loc[sub["state"] == "garbage", "residual"].dropna().values
        if len(clutch) < 5 or len(garbage) < 5:
            test_rows.append({"stat": stat, "n_clutch": len(clutch), "n_garbage": len(garbage),
                                "ratio": np.nan, "p_levene": np.nan, "p_bartlett": np.nan, "p_F": np.nan,
                                "verdict": "insufficient n"})
            continue
        sd_clutch = float(np.std(clutch, ddof=1))
        sd_garbage = float(np.std(garbage, ddof=1))
        ratio = sd_garbage / sd_clutch if sd_clutch > 0 else np.nan
        try: _, p_lev = stats.levene(clutch, garbage, center="median")
        except Exception: p_lev = np.nan
        try: _, p_bart = stats.bartlett(clutch, garbage)
        except Exception: p_bart = np.nan
        # F-test two-sided
        var_c, var_g = clutch.var(ddof=1), garbage.var(ddof=1)
        if var_c > 0 and var_g > 0:
            F = var_g / var_c
            cdf = stats.f.cdf(F, len(garbage) - 1, len(clutch) - 1)
            p_F = 2 * min(cdf, 1 - cdf)
        else:
            p_F = np.nan
        confirmed = (p_lev < 0.05) and (ratio > 1.0)
        verdict = ("CONFIRM (ratio>1, p<0.05)" if confirmed
                    else f"NULL (ratio={ratio:.3f}, p={p_lev:.4f})")
        test_rows.append({"stat": stat, "n_clutch": len(clutch), "n_garbage": len(garbage),
                            "sd_clutch": sd_clutch, "sd_garbage": sd_garbage,
                            "ratio": ratio, "p_levene": p_lev, "p_bartlett": p_bart, "p_F": p_F,
                            "verdict": verdict})

    test_df = pd.DataFrame(test_rows)
    test_df.to_csv(OUT / "tier1_test_results.csv", index=False)

    print()
    print("=" * 100)
    print(f"PBP TIER-1 TEST — score-margin × possession-outcome lever ({TEST_SEASON})")
    print("=" * 100)
    print(test_df.to_string(index=False))
    print()
    n_confirm = sum(1 for r in test_rows if "CONFIRM" in r["verdict"])
    print(f"Aggregate verdict: {n_confirm}/3 stats confirm Tier-1 prediction")
    print(f"\n[save] {OUT}")


if __name__ == "__main__":
    main()
