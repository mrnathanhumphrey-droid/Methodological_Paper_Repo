"""v6.3-A baseline: in-season conjugate per-player update on PTS/REB/AST.

Methodology:
  - Architecture HELD CONSTANT vs v6.1 LOCKED (Stan posterior + cohort widening
    hybrid v3 + LOCKED offsets all unchanged at the prior).
  - In-season information channel: NB2/Gamma-Poisson conjugate update of each
    player's per-game rate using their actual 25-26 games 1-30.
  - Stats: PTS/REB/AST only (Test 1 confirmed coupling at position cells).
  - No de-shrinkage, no contextual variables.

Conjugate update:
    posterior_rate = (K_prior * mu_prior + sum_y_30) / (K_prior + 30)
  where K_prior is an effective prior sample size derived from career NBA GP
  capped at 50. Vets get higher K (less moved by 30 games), rookies get lower K.

Rookie handling:
  - Real-NBA-ID lookup via name match for synthetic 9990xxx IDs in v6.1 ship.
  - Rookies with >=10 games in 1-30: conjugate update.
  - Rookies with <10 games or unmatched: keep v6.1 hybrid v3 prior unchanged.

Tanking tag (TABLE 3):
  - Build rolling per-team standings + losing-streak series over 25-26.
  - For each game date D and opponent T:
      if T has <30 GP as of D:    use 24-25 final standings rank
      else:                       use rolling-30-day current-season rank as of D
  - Classify each opponent at each game:
      competitive:        rank in [1, 16] AND not on a 5+ losing streak
      tanking_affected:   rank in [23, 30] OR currently on a 10+ losing streak
      mid:                else
  - Each games-31-82 player-game gets the OPPONENT's classification at that date.

Outputs:
  audit_runs/v6_3_A_baseline_2025_26/
    v6_3_A_baseline_summary.md
    v6_3_A_per_player_projections.csv
    v6_3_A_residuals.csv  (input to Probe B)
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from pathlib import Path
import json

import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
OUT_DIR = REPO / "audit_runs" / "v6_3_A_baseline_2025_26"
OUT_DIR.mkdir(parents=True, exist_ok=True)

V6_1_SHIP_CSV = REPO / "audit_runs" / "unified_ship_v6_1_2025_26" / "per_player_projections_2025-26.csv"
ROOKIE_SUP = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "rookie_metadata_supplement.parquet"

STATS = ["PTS", "REB", "AST"]
GAME_30_CUTOFF = 30  # team_game_n cutoff for train/eval split


# ────────────────────────────────────────────────────────────────────────
# Load core data
# ────────────────────────────────────────────────────────────────────────

def load_core():
    print("[load] historical_box_scores.parquet")
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx = bx[bx["season_type"] == "Regular Season"].copy()
    bx["game_date"] = pd.to_datetime(bx["game_date"])
    bx["nba_api_id"] = bx["nba_api_id"].astype(int)
    bx["minutes"] = pd.to_numeric(bx["minutes"], errors="coerce")
    return bx


def attach_team_game_n(bx_25_26):
    """For each player-game in 25-26, attach team_game_n and opponent_abbr."""
    # Build per-team game ordering
    tg = (bx_25_26.groupby(["team_abbr", "game_id", "game_date"])
                  .size().reset_index(name="_n"))
    tg = tg.sort_values(["team_abbr", "game_date"]).reset_index(drop=True)
    tg["team_game_n"] = tg.groupby("team_abbr").cumcount() + 1

    # Opponent abbr from matchup ("LAL @ DEN" or "LAL vs. DEN")
    df = bx_25_26.merge(tg[["team_abbr", "game_id", "team_game_n"]],
                        on=["team_abbr", "game_id"], how="left")
    df["opp_abbr"] = df["matchup"].str.extract(r"(?:vs\.\s+|@\s+)([A-Z]{3})")
    return df, tg


# ────────────────────────────────────────────────────────────────────────
# Standings (24-25 final + 25-26 rolling)
# ────────────────────────────────────────────────────────────────────────

def standings_24_25_final(bx):
    sub = bx[bx["season"] == "2024-25"].copy()
    tg = sub.groupby(["team_abbr", "game_id"])["win"].first().reset_index()
    s = tg.groupby("team_abbr")["win"].agg(["sum", "count"]).reset_index()
    s.columns = ["team", "W", "GP"]
    s["L"] = s["GP"] - s["W"]
    s["win_pct"] = s["W"] / s["GP"]
    s = s.sort_values("win_pct", ascending=False).reset_index(drop=True)
    s["rank_24_25"] = s.index + 1
    return s[["team", "rank_24_25", "win_pct", "W", "L"]]


def build_rolling_25_26(bx_25_26):
    """For each (team, game_date), compute team_game_n, current rank (rolling-30
    by GP-as-of-now), and current losing streak length.
    """
    tg = (bx_25_26.groupby(["team_abbr", "game_id", "game_date"])
                  .agg(win=("win", "first")).reset_index())
    tg = tg.sort_values(["team_abbr", "game_date"]).reset_index(drop=True)
    tg["team_game_n"] = tg.groupby("team_abbr").cumcount() + 1

    # Cumulative wins and losses up to and including this game
    tg["cum_W"] = tg.groupby("team_abbr")["win"].cumsum()
    tg["cum_L"] = tg["team_game_n"] - tg["cum_W"]

    # Losing streak: count consecutive losses ending at this game
    def streak_length(s):
        out = []
        cur = 0
        for v in s.values:
            if v == 0:
                cur += 1
            else:
                cur = 0
            out.append(cur)
        return pd.Series(out, index=s.index)
    tg["losing_streak"] = (tg.groupby("team_abbr")["win"]
                              .transform(lambda s: streak_length(s)))

    # Rolling-30-game win pct (over the prior 30 games as of this game)
    def rolling_30_winpct(s):
        # window of 30 prior games inclusive of current
        return s.rolling(30, min_periods=1).mean()
    tg["rolling30_winpct"] = (tg.groupby("team_abbr")["win"]
                                 .transform(lambda s: rolling_30_winpct(s)))
    return tg


def opponent_classify(opp_abbr, game_date, opp_team_game_n, opp_streak,
                      opp_rolling30_winpct, rank_24_25_lookup,
                      rank_rolling_lookup):
    """Return 'competitive' | 'mid' | 'tanking_affected' for opponent at game date."""
    if opp_team_game_n is None or pd.isna(opp_team_game_n):
        return "mid"
    # Standings rank source
    if opp_team_game_n < 30:
        rank = rank_24_25_lookup.get(opp_abbr, 16)  # default to mid if missing
    else:
        # rank by rolling30 win pct as of this date
        rank = rank_rolling_lookup.get((opp_abbr, opp_team_game_n), 16)
    streak = int(opp_streak) if not pd.isna(opp_streak) else 0
    if rank >= 23 or streak >= 10:
        return "tanking_affected"
    if rank <= 16 and streak < 5:
        return "competitive"
    return "mid"


def build_rolling_rank_lookup(rolling_25_26):
    """For each (team_abbr, team_game_n), compute the team's rank by rolling30
    win pct as of that team's nth game, ranking against all teams' rolling30
    at their most recent game on or before that game date.
    """
    rolling = rolling_25_26.sort_values(["team_abbr", "team_game_n"]).copy()
    teams = rolling["team_abbr"].unique().tolist()
    out = {}
    # For each game date, get every team's most-recent rolling30 win pct.
    # For efficiency: iterate game dates in order, maintain latest win pct per team.
    rolling = rolling.sort_values("game_date")
    latest_pct = {}
    latest_team_game_n = {}
    for _, r in rolling.iterrows():
        latest_pct[r["team_abbr"]] = r["rolling30_winpct"]
        latest_team_game_n[r["team_abbr"]] = r["team_game_n"]
        # Snapshot: rank everyone with at least one game played so far
        snap = sorted(latest_pct.items(), key=lambda kv: -kv[1])
        ranks = {team: i + 1 for i, (team, _) in enumerate(snap)}
        out[(r["team_abbr"], r["team_game_n"])] = ranks.get(r["team_abbr"], 16)
    return out


# ────────────────────────────────────────────────────────────────────────
# Rookie ID mapping (synthetic 9990xxx -> real NBA ID via name)
# ────────────────────────────────────────────────────────────────────────

def map_rookie_ids(ship, bx_25_26):
    """Return dict synthetic_id -> real_nba_id by matching player name."""
    if not ROOKIE_SUP.exists():
        return {}
    sup = pd.read_parquet(ROOKIE_SUP)
    sup_ids = set(sup["nba_api_id"].astype(int).tolist())
    rookie_rows = ship[ship["nba_api_id"].astype(int).isin(sup_ids)].copy()
    rookie_rows["nba_api_id_int"] = rookie_rows["nba_api_id"].astype(int)
    # Names from supplement
    name_lookup = dict(zip(sup["nba_api_id"].astype(int), sup["name"]))

    # Real-id name lookup from box score data + metadata
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    real_name_to_id = {}
    for _, r in meta.iterrows():
        nm = (r["name"] or "").strip().lower()
        if nm:
            real_name_to_id[nm] = int(r["nba_api_id"])

    mapping = {}
    for synth_id in rookie_rows["nba_api_id_int"]:
        synth_id_int = int(synth_id)
        nm = (name_lookup.get(synth_id_int, "") or "").strip().lower()
        if nm and nm in real_name_to_id:
            mapping[synth_id_int] = real_name_to_id[nm]
    return mapping


# ────────────────────────────────────────────────────────────────────────
# Build prior K_player from career NBA train data
# ────────────────────────────────────────────────────────────────────────

def k_prior_per_player(bx, ship_ids):
    """Effective prior sample size = career_NBA_GP_in_train (capped 50).
    Sophs/rookies with little train data get small K; vets get K=50.
    """
    train = bx[(bx["season"].isin(["2019-20", "2020-21", "2021-22",
                                    "2022-23", "2023-24", "2024-25"])) &
                (bx["minutes"] > 0)].copy()
    gp = train.groupby("nba_api_id").size().reset_index(name="career_gp")
    gp["K_prior"] = gp["career_gp"].clip(upper=50.0).astype(float)
    k_lookup = dict(zip(gp["nba_api_id"].astype(int), gp["K_prior"]))
    # For ship players with no train history (rookies/intl), default K=8
    out = {}
    for pid in ship_ids:
        out[int(pid)] = float(k_lookup.get(int(pid), 8.0))
    return out


# ────────────────────────────────────────────────────────────────────────
# Cohort tags
# ────────────────────────────────────────────────────────────────────────

def build_cohort_tags(ship):
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    mc = ["nba_api_id", "draft_year", "debut_year", "position"]
    if ROOKIE_SUP.exists():
        sup = pd.read_parquet(ROOKIE_SUP)
        meta = pd.concat([meta[mc], sup[mc]], ignore_index=True)
    df = ship[["nba_api_id"]].copy()
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    meta["nba_api_id"] = meta["nba_api_id"].astype(int)
    df = df.merge(meta[mc], on="nba_api_id", how="left")
    df["years_pro"] = df["debut_year"].where(df["debut_year"].notna(),
                                              df["draft_year"] + 1)
    df["years_pro"] = 2025 - df["years_pro"]
    df["ypb"] = pd.cut(df["years_pro"], bins=[-1, 0, 3, 7, 12, 30],
                       labels=["rookie", "1-3", "4-7", "8-12", "13+"]).astype(str)

    def cohort_class(y):
        if y == "rookie": return "rookie"
        if y == "1-3":    return "soph"
        return "vet"

    def position_class(p):
        if pd.isna(p) or not p or str(p).strip() == "": return "Forward"
        primary = str(p).split("-")[0].strip().lower()
        if primary == "center": return "Center"
        if primary == "guard": return "Guard"
        return "Forward"

    df["cohort"] = df["ypb"].apply(cohort_class)
    df["pos_class"] = df["position"].apply(position_class)
    return df[["nba_api_id", "cohort", "pos_class", "ypb", "position",
               "years_pro"]]


# ────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────

def main():
    bx = load_core()
    bx_25_26 = bx[bx["season"] == "2025-26"].copy()
    bx_25_26_played = bx_25_26[bx_25_26["minutes"] > 0].copy()
    print(f"  25-26 RS player-games (any minutes): {len(bx_25_26)}")
    print(f"  25-26 RS player-games (min>0):       {len(bx_25_26_played)}")

    bx_with_n, team_games = attach_team_game_n(bx_25_26)
    bx_played_with_n, _ = attach_team_game_n(bx_25_26_played)

    # ── Load v6.1 LOCKED ship ───────────────────────────────────────────
    print("[load] v6.1 LOCKED ship")
    ship = pd.read_csv(V6_1_SHIP_CSV)
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    print(f"  ship rows: {len(ship)}")

    # ── Cohort tags ─────────────────────────────────────────────────────
    print("[build] cohort tags")
    cohort = build_cohort_tags(ship)
    ship = ship.merge(cohort, on="nba_api_id", how="left")

    # ── Rookie ID mapping ───────────────────────────────────────────────
    print("[map] synthetic rookie IDs -> real IDs")
    rookie_map = map_rookie_ids(ship, bx_25_26_played)
    print(f"  matched: {len(rookie_map)} synthetic rookies")

    # Add a "real_id_for_lookup" column. For non-rookies, identical to nba_api_id.
    ship["real_id"] = ship["nba_api_id"].map(
        lambda x: rookie_map.get(int(x), int(x))).astype(int)

    # ── K_prior per player ──────────────────────────────────────────────
    print("[build] K_prior per player")
    k_lookup = k_prior_per_player(bx, ship["real_id"].tolist())

    # ── Per-player actual aggregates over games 1-30 and 31-82 ──────────
    print("[aggregate] player x games 1-30 and 31-82 actuals")
    bx_played_with_n["nba_api_id"] = bx_played_with_n["nba_api_id"].astype(int)
    bx_played_with_n["train_slice"] = (bx_played_with_n["team_game_n"]
                                        <= GAME_30_CUTOFF)

    train_actuals = (bx_played_with_n[bx_played_with_n["train_slice"]]
                     .groupby("nba_api_id").agg(
                         gp_train=("game_id", "nunique"),
                         **{f"{s}_sum": (s, "sum") for s in STATS})
                     .reset_index())
    train_actuals.columns = ["real_id", "gp_train"] + [f"{s}_sum_30" for s in STATS]
    for s in STATS:
        train_actuals[f"{s}_pg_train"] = (train_actuals[f"{s}_sum_30"]
                                           / train_actuals["gp_train"])

    eval_actuals = (bx_played_with_n[~bx_played_with_n["train_slice"]]
                    .groupby("nba_api_id").agg(
                        gp_eval=("game_id", "nunique"),
                        **{f"{s}_sum_eval": (s, "sum") for s in STATS})
                    .reset_index())
    eval_actuals.columns = ["real_id", "gp_eval"] + [f"{s}_pg_eval_sum" for s in STATS]
    for s in STATS:
        eval_actuals[f"{s}_pg_eval"] = (eval_actuals[f"{s}_pg_eval_sum"]
                                         / eval_actuals["gp_eval"])
    eval_actuals = eval_actuals[["real_id", "gp_eval"] + [f"{s}_pg_eval" for s in STATS]]

    # Merge into ship
    ship = ship.merge(train_actuals[["real_id", "gp_train"]
                                      + [f"{s}_pg_train" for s in STATS]
                                      + [f"{s}_sum_30" for s in STATS]],
                      on="real_id", how="left")
    ship = ship.merge(eval_actuals, on="real_id", how="left")
    ship["gp_train"] = ship["gp_train"].fillna(0).astype(int)
    ship["gp_eval"] = ship["gp_eval"].fillna(0).astype(int)
    ship["K_prior"] = ship["real_id"].map(lambda x: k_lookup.get(int(x), 8.0))

    # ── Conjugate posterior update ──────────────────────────────────────
    print("[compute] conjugate posterior update")
    for s in STATS:
        prior_col = f"{s}_per_game"
        ship[f"{s}_v6_1_proj"] = ship[prior_col]
        # Conjugate update only when player has gp_train > 0
        # AND they qualify (vet/soph: any games; rookie: gp_train >= 10)
        is_rookie = ship["cohort"] == "rookie"
        rookie_qualifies = is_rookie & (ship["gp_train"] >= 10)
        non_rookie_qualifies = (~is_rookie) & (ship["gp_train"] > 0)
        qualifies = rookie_qualifies | non_rookie_qualifies
        ship["v6_3_A_qualifies"] = qualifies

        K = ship["K_prior"]
        n = ship["gp_train"].astype(float)
        sum_y = ship[f"{s}_sum_30"].fillna(0)
        mu_prior = ship[prior_col]
        v63a = (K * mu_prior + sum_y) / (K + n.replace(0, 1))
        # Where doesn't qualify, fall back to v6.1 prior
        ship[f"{s}_v6_3_A_proj"] = np.where(qualifies, v63a, mu_prior)

    # ── Filter to players with eval data ────────────────────────────────
    eval_set = ship[ship["gp_eval"] > 0].copy()
    print(f"  eval set (players w/ 31-82 actuals): {len(eval_set)} of {len(ship)}")

    # ── Standings + rolling tags ────────────────────────────────────────
    print("[build] standings + rolling lookup")
    s_2425 = standings_24_25_final(bx)
    rank_24_25 = dict(zip(s_2425["team"], s_2425["rank_24_25"]))
    rolling = build_rolling_25_26(bx_25_26)
    rolling_rank = build_rolling_rank_lookup(rolling)

    # Streak lookup: (team, team_game_n) -> losing_streak
    streak_lookup = dict(zip(zip(rolling["team_abbr"], rolling["team_game_n"]),
                             rolling["losing_streak"]))
    opp_team_game_n_lookup = dict(zip(zip(rolling["team_abbr"],
                                          rolling["game_date"]),
                                       rolling["team_game_n"]))

    # ── Per-game residuals (eval slice) with opponent tag ──────────────
    print("[build] per-game residuals with opponent tag")
    eval_pg = bx_played_with_n[~bx_played_with_n["train_slice"]].copy()
    eval_pg["nba_api_id"] = eval_pg["nba_api_id"].astype(int)

    # Attach opponent's team_game_n at game date
    rolling_pos = rolling[["team_abbr", "game_date", "team_game_n",
                            "losing_streak"]]
    rolling_pos = rolling_pos.rename(
        columns={"team_abbr": "opp_abbr",
                 "team_game_n": "opp_game_n",
                 "losing_streak": "opp_streak"})
    eval_pg = eval_pg.merge(rolling_pos, on=["opp_abbr", "game_date"],
                              how="left")

    # Classify
    def classify_row(r):
        opp_n = r["opp_game_n"]
        opp = r["opp_abbr"]
        if pd.isna(opp_n) or pd.isna(opp):
            return "mid"
        opp_n = int(opp_n)
        if opp_n < 30:
            rank = rank_24_25.get(opp, 16)
        else:
            rank = rolling_rank.get((opp, opp_n), 16)
        streak = int(r["opp_streak"]) if not pd.isna(r["opp_streak"]) else 0
        if rank >= 23 or streak >= 10:
            return "tanking_affected"
        if rank <= 16 and streak < 5:
            return "competitive"
        return "mid"

    eval_pg["opp_class"] = eval_pg.apply(classify_row, axis=1)
    print(f"  per-game eval rows: {len(eval_pg)}")
    print(f"  opp_class distribution: ")
    print(eval_pg["opp_class"].value_counts().to_string())

    # Attach v6.1 and v6.3-A projections per player
    proj_cols = ["nba_api_id"] + [f"{s}_v6_1_proj" for s in STATS] + \
                 [f"{s}_v6_3_A_proj" for s in STATS] + \
                 ["cohort", "pos_class", "v6_3_A_qualifies", "real_id"]
    # ship's nba_api_id may be synthetic; need to use real_id for join with box
    # scores. So reverse-map: real_id -> ship row.
    ship_proj = ship[proj_cols].copy()
    # Use real_id as join key on the boxscore side
    eval_pg = eval_pg.merge(ship_proj, left_on="nba_api_id", right_on="real_id",
                              how="inner", suffixes=("", "_ship"))
    print(f"  per-game eval rows joined to projections: {len(eval_pg)}")

    # Per-game residuals
    for s in STATS:
        eval_pg[f"{s}_resid_v6_1"] = eval_pg[s] - eval_pg[f"{s}_v6_1_proj"]
        eval_pg[f"{s}_resid_v6_3_A"] = eval_pg[s] - eval_pg[f"{s}_v6_3_A_proj"]

    # ── TABLE 1: Overall ────────────────────────────────────────────────
    print("\n=== TABLE 1: Overall improvement (per-player MAE on 31-82 means) ===")
    summary_t1 = []
    for s in STATS:
        # Per-player MAE comparison
        pg_eval_col = f"{s}_pg_eval"
        v61_col = f"{s}_v6_1_proj"
        v63_col = f"{s}_v6_3_A_proj"
        valid = eval_set.dropna(subset=[pg_eval_col, v61_col, v63_col])
        n = len(valid)
        v61_mae = (valid[pg_eval_col] - valid[v61_col]).abs().mean()
        v63_mae = (valid[pg_eval_col] - valid[v63_col]).abs().mean()
        v61_bias = (valid[pg_eval_col] - valid[v61_col]).mean()
        v63_bias = (valid[pg_eval_col] - valid[v63_col]).mean()
        d_mae = v63_mae - v61_mae
        d_pct = (d_mae / v61_mae) * 100 if v61_mae else 0
        summary_t1.append({
            "stat": s, "n": n,
            "v6_1_MAE": v61_mae, "v6_3_A_MAE": v63_mae,
            "delta_MAE": d_mae, "delta_pct": d_pct,
            "v6_1_bias": v61_bias, "v6_3_A_bias": v63_bias,
        })
    t1 = pd.DataFrame(summary_t1)
    print(t1.to_string(index=False))

    # ── TABLE 2: Cohort × Position ──────────────────────────────────────
    print("\n=== TABLE 2: Cohort x Position breakdown ===")
    cells = []
    for cohort_v in ["rookie", "soph", "vet"]:
        for pos_v in ["Center", "Forward", "Guard"]:
            sub = eval_set[(eval_set["cohort"] == cohort_v) &
                            (eval_set["pos_class"] == pos_v)]
            n = len(sub)
            row = {"cohort": cohort_v, "pos_class": pos_v, "n": n}
            for s in STATS:
                if n == 0:
                    row[f"{s}_v6_1_MAE"] = np.nan
                    row[f"{s}_v6_3_A_MAE"] = np.nan
                    row[f"{s}_dMAE"] = np.nan
                    continue
                v61 = (sub[f"{s}_pg_eval"] - sub[f"{s}_v6_1_proj"]).abs().mean()
                v63 = (sub[f"{s}_pg_eval"] - sub[f"{s}_v6_3_A_proj"]).abs().mean()
                row[f"{s}_v6_1_MAE"] = v61
                row[f"{s}_v6_3_A_MAE"] = v63
                row[f"{s}_dMAE"] = v63 - v61
            cells.append(row)
    t2 = pd.DataFrame(cells)
    print(t2.to_string(index=False))

    # ── TABLE 3: Tanking-context (per-player-game) ──────────────────────
    print("\n=== TABLE 3: Tanking-context (per-player-game level) ===")
    cells_t3 = []
    for cls in ["competitive", "mid", "tanking_affected"]:
        sub = eval_pg[eval_pg["opp_class"] == cls]
        n = len(sub)
        row = {"opp_class": cls, "n": n}
        for s in STATS:
            if n == 0:
                continue
            v61 = sub[f"{s}_resid_v6_1"].abs().mean()
            v63 = sub[f"{s}_resid_v6_3_A"].abs().mean()
            row[f"{s}_v6_1_MAE"] = v61
            row[f"{s}_v6_3_A_MAE"] = v63
            row[f"{s}_dMAE"] = v63 - v61
            row[f"{s}_d_pct"] = (v63 - v61) / v61 * 100 if v61 else 0
        cells_t3.append(row)
    t3 = pd.DataFrame(cells_t3)
    print(t3.to_string(index=False))

    # ── Save outputs ────────────────────────────────────────────────────
    print("\n[save] outputs")
    # Per-player projections
    out_proj_cols = ["nba_api_id", "real_id", "name", "cohort", "pos_class",
                     "ypb", "gp_train", "gp_eval",
                     "K_prior", "v6_3_A_qualifies"]
    for s in STATS:
        out_proj_cols += [f"{s}_v6_1_proj", f"{s}_v6_3_A_proj",
                          f"{s}_pg_train", f"{s}_pg_eval"]
    proj_out = ship[out_proj_cols].copy()
    proj_path = OUT_DIR / "v6_3_A_per_player_projections.csv"
    proj_out.to_csv(proj_path, index=False)
    print(f"  wrote {proj_path}")

    # Residuals (Probe B input)
    resid_cols = ["nba_api_id", "name", "game_id", "game_date", "team_abbr",
                   "opp_abbr", "team_game_n", "opp_game_n", "opp_streak",
                   "opp_class", "minutes", "cohort", "pos_class",
                   "v6_3_A_qualifies"]
    for s in STATS:
        resid_cols += [s, f"{s}_v6_1_proj", f"{s}_v6_3_A_proj",
                        f"{s}_resid_v6_1", f"{s}_resid_v6_3_A"]
    eval_pg_named = eval_pg.merge(
        ship[["nba_api_id", "name"]].rename(columns={"nba_api_id": "real_id"}),
        on="real_id", how="left")
    keep = [c for c in resid_cols if c in eval_pg_named.columns]
    resid_path = OUT_DIR / "v6_3_A_residuals.csv"
    eval_pg_named[keep].to_csv(resid_path, index=False)
    print(f"  wrote {resid_path}")

    # Save tables for the markdown
    summary = {
        "table_1_overall": summary_t1,
        "table_2_cohort": cells,
        "table_3_tanking": cells_t3,
        "n_train_player_games": int(len(bx_played_with_n[bx_played_with_n["train_slice"]])),
        "n_eval_player_games": int(len(eval_pg)),
        "n_eval_players": int(len(eval_set)),
        "n_rookies_mapped": len(rookie_map),
        "rookie_qualified_count": int(((eval_set["cohort"] == "rookie") &
                                          (eval_set["v6_3_A_qualifies"])).sum()),
        "rookie_unqualified_count": int(((eval_set["cohort"] == "rookie") &
                                            (~eval_set["v6_3_A_qualifies"])).sum()),
    }
    with open(OUT_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"  wrote {OUT_DIR / 'summary.json'}")
    print(f"\nDONE.")


if __name__ == "__main__":
    main()
