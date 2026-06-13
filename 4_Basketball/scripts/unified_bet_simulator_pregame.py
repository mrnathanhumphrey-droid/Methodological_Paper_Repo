"""Unified bet simulator — PRE-GAME USG version (forward-clean, no look-ahead).

Same strategies as unified_bet_simulator.py but USG is computed from each
player's SEASON-TO-DATE box scores BEFORE the current game. This removes
the selection bias of using post-game USG (which is endogenous to the
outcome being bet).

For players with <5 prior games in the season: fall back to prior-season
USG. For pure rookies with no prior NBA games: skip.

The quartile breaks are computed once on the pooled s2d USG distribution
across the full sample.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

PROPS_DIR = Path("D:/sports_lines/data/odds_api/player_props")
BOX_PATH = Path("D:/NBA Projections/data/parquet/historical_box_scores.parquet")
META_PATH = Path("D:/NBA Projections/data/parquet/player_metadata_enriched.parquet")
V4_RESID = Path("D:/NBA Projections/runs/run_nba_game_totals_22_26/v4_pace_adjusted/game_residuals.csv")
OUT_DIR = Path("D:/NBA Projections/runs/run_unified_bet_sim_pregame")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BET_UNIT = 100
BREAKEVEN = 110 / 210
MIN_PRIOR_GAMES_FOR_S2D_USG = 5


def parse_min(m):
    if pd.isna(m): return 0.0
    if isinstance(m, (int, float)): return float(m)
    try:
        parts = str(m).split(":")
        return float(parts[0]) + (float(parts[1]) / 60 if len(parts) > 1 else 0)
    except (ValueError, TypeError):
        return 0.0


def american_payout(price):
    if price > 0: return price / 100
    return 100 / -price


def load_box() -> pd.DataFrame:
    cols = ["nba_api_id", "game_id", "game_date", "team_abbr", "season",
            "season_type", "minutes",
            "FGA", "FTA", "TOV", "PTS", "REB", "AST"]
    box = pd.read_parquet(BOX_PATH, columns=cols)
    box = box[pd.notna(box["nba_api_id"])].copy()
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    box["game_date"] = pd.to_datetime(box["game_date"])
    box["min_played"] = box["minutes"].apply(parse_min)
    return box


def compute_per_game_usg(box: pd.DataFrame) -> pd.DataFrame:
    """USG per (player, game) for every game in box (including DNPs as NaN)."""
    team_per_game = box.groupby(["game_id", "team_abbr"]).agg(
        team_min=("min_played", "sum"),
        team_fga=("FGA", "sum"),
        team_fta=("FTA", "sum"),
        team_tov=("TOV", "sum"),
    ).reset_index()
    box = box.merge(team_per_game, on=["game_id", "team_abbr"], how="left")
    denom = box["min_played"] * (box["team_fga"] + 0.44 * box["team_fta"] + box["team_tov"])
    numer = (box["FGA"] + 0.44 * box["FTA"] + box["TOV"]) * (box["team_min"] / 5.0)
    box["USG"] = np.where(denom > 0, numer / denom, np.nan)
    return box


def add_pregame_usg(box_with_usg: pd.DataFrame) -> pd.DataFrame:
    """For each (player, game) row, compute season-to-date USG using only
    PRIOR games in this season. Forward-clean."""
    rs = box_with_usg[box_with_usg["min_played"] >= 5].copy()  # min sample to count
    rs = rs.sort_values(["nba_api_id", "season", "game_date"])
    # Cumulative USG over prior games this season (excluding current)
    grp = rs.groupby(["nba_api_id", "season"])
    rs["usg_cumsum"] = grp["USG"].cumsum() - rs["USG"]
    rs["usg_n_prior"] = grp.cumcount()
    rs["s2d_usg"] = np.where(
        rs["usg_n_prior"] >= MIN_PRIOR_GAMES_FOR_S2D_USG,
        rs["usg_cumsum"] / rs["usg_n_prior"],
        np.nan,
    )
    # Fallback: prior-season USG
    # Per (player, season), full-season mean USG
    season_avg = rs.groupby(["nba_api_id", "season"])["USG"].mean().reset_index()
    season_avg.columns = ["nba_api_id", "season", "season_usg_mean"]
    next_season = {"2017-18": "2018-19", "2018-19": "2019-20",
                   "2019-20": "2020-21", "2020-21": "2021-22",
                   "2021-22": "2022-23", "2022-23": "2023-24",
                   "2023-24": "2024-25", "2024-25": "2025-26"}
    season_avg["target_season"] = season_avg["season"].map(next_season)
    season_avg = season_avg.dropna(subset=["target_season"])
    prior_lookup = {(int(r["nba_api_id"]), r["target_season"]): r["season_usg_mean"]
                    for _, r in season_avg.iterrows()}

    def fallback(row):
        if not np.isnan(row["s2d_usg"]):
            return row["s2d_usg"]
        return prior_lookup.get((int(row["nba_api_id"]), row["season"]), np.nan)

    rs["pregame_usg"] = rs.apply(fallback, axis=1)
    return rs


def load_props() -> pd.DataFrame:
    files = sorted(PROPS_DIR.glob("*draftkings*.parquet"))
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df["commence_dt_utc"] = pd.to_datetime(df["commence_time"], utc=True)
    df["game_date"] = df["commence_dt_utc"].dt.tz_convert("US/Eastern").dt.date
    df["game_date"] = pd.to_datetime(df["game_date"])
    return df


def match_player(props: pd.DataFrame) -> pd.DataFrame:
    import unicodedata
    def _norm(name):
        if not isinstance(name, str): return ""
        s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
        for suf in [" jr.", " jr", " sr.", " sr", " ii", " iii", " iv"]:
            if s.endswith(suf): s = s[:-len(suf)]
        return "".join(c for c in s if c.isalnum() or c.isspace()).strip()

    meta = pd.read_parquet(META_PATH)
    meta = meta[pd.notna(meta["nba_api_id"])].copy()
    meta["nba_api_id"] = meta["nba_api_id"].astype(int)
    for nm_col in ("name", "player_name", "full_name", "display_name"):
        if nm_col in meta.columns:
            meta["name_norm"] = meta[nm_col].apply(_norm)
            break
    name_to_pid = dict(zip(meta["name_norm"], meta["nba_api_id"]))
    props["name_norm"] = props["player_name"].apply(_norm)
    props["nba_api_id"] = props["name_norm"].map(name_to_pid)
    return props.dropna(subset=["nba_api_id"]).copy()


def pair_market(props, market):
    m = props[props["market"] == market]
    if m.empty: return pd.DataFrame()
    over = m[m["side"] == "Over"][[
        "game_date", "nba_api_id", "player_name", "line", "juice_american"
    ]].rename(columns={"line": "line_over", "juice_american": "juice_over"})
    under = m[m["side"] == "Under"][[
        "game_date", "nba_api_id", "line", "juice_american"
    ]].rename(columns={"line": "line_under", "juice_american": "juice_under"})
    return over.merge(under, on=["game_date", "nba_api_id"], how="inner")


def resolve_bet(line, actual, side, juice):
    if pd.isna(actual) or pd.isna(line):
        return None, 0
    if actual == line: return 0, 0
    over = actual > line
    won = (side == "over" and over) or (side == "under" and not over)
    if won: return 1, BET_UNIT * american_payout(juice)
    return -1, -BET_UNIT


def main():
    print("=" * 70)
    print("Unified bet simulator — PRE-GAME USG (forward-clean)")
    print("=" * 70)

    print("\n[1/6] Loading props...")
    props = load_props()
    props = props[props["book"] == "draftkings"]
    print(f"  {len(props):,} props, {props['game_date'].min().date()} → "
          f"{props['game_date'].max().date()}")

    print("\n[2/6] Loading box + computing per-game USG...")
    box = load_box()
    box = compute_per_game_usg(box)
    print(f"  {len(box):,} box rows  ({box['USG'].notna().sum():,} with USG)")

    print("\n[3/6] Computing pre-game (s2d) USG per player-game...")
    box_pregame = add_pregame_usg(box)
    n_s2d = (box_pregame["pregame_usg"].notna() &
              (box_pregame["usg_n_prior"] >= MIN_PRIOR_GAMES_FOR_S2D_USG)).sum()
    n_fallback = (box_pregame["pregame_usg"].notna() &
                   (box_pregame["usg_n_prior"] < MIN_PRIOR_GAMES_FOR_S2D_USG)).sum()
    n_none = box_pregame["pregame_usg"].isna().sum()
    print(f"  s2d: {n_s2d:,}  prior-season fallback: {n_fallback:,}  none: {n_none:,}")

    print("\n[4/6] Matching props → nba_api_id + pre-game USG...")
    props_m = match_player(props)
    print(f"  {len(props_m):,} matched")

    # Join props with pre-game USG (by player + date)
    usg_join = box_pregame[["nba_api_id", "game_date", "PTS", "REB", "AST",
                              "pregame_usg", "USG"]].rename(columns={"USG": "actual_usg"})
    usg_join["game_date"] = pd.to_datetime(usg_join["game_date"])

    market_pairs = {}
    market_actual = {
        "player_points_assists": ("PTS", "AST"),
        "player_points_rebounds_assists": ("PTS", "REB", "AST"),
        "player_points_rebounds": ("PTS", "REB"),
    }
    for market in market_actual.keys():
        paired = pair_market(props_m, market)
        if paired.empty: continue
        paired = paired.merge(usg_join, on=["nba_api_id", "game_date"], how="inner")
        comp = market_actual[market]
        paired["actual"] = paired[list(comp)].sum(axis=1)
        # Filter: must have pre-game USG
        paired = paired.dropna(subset=["pregame_usg"])
        market_pairs[market] = paired
        print(f"  {market}: {len(paired):,} with pre-game USG")

    # Quartile breaks from pre-game USG across pooled sample (PA market as canonical)
    pa = market_pairs.get("player_points_assists")
    if pa is None or pa.empty:
        raise SystemExit("no PA market data")
    usg_breaks = pd.qcut(pa["pregame_usg"], 4, retbins=True, duplicates="drop")[1]
    print(f"\n  PRE-GAME USG quartile breaks: {[round(b, 3) for b in usg_breaks]}")

    def usg_q(usg):
        if pd.isna(usg): return None
        for i in range(1, len(usg_breaks)):
            if usg <= usg_breaks[i]:
                return i
        return len(usg_breaks) - 1

    print("\n[5/6] Resolving bets...")
    ledger_rows = []
    for market_name, market_label in [
        ("player_points_assists", "PA"),
        ("player_points_rebounds_assists", "PRA"),
        ("player_points_rebounds", "PR"),
    ]:
        df = market_pairs.get(market_name)
        if df is None or df.empty: continue
        df = df.copy()
        df["q"] = df["pregame_usg"].apply(usg_q)

        for q, side in [(1, "under"), (4, "over")]:
            sub = df[df["q"] == q]
            for _, r in sub.iterrows():
                line = r["line_under"] if side == "under" else r["line_over"]
                juice = r["juice_under"] if side == "under" else r["juice_over"]
                result, pnl = resolve_bet(line, r["actual"], side, juice)
                if result is None: continue
                ledger_rows.append({
                    "strategy": f"{market_label}_Q{q}_{side.upper()}",
                    "game_date": r["game_date"],
                    "player_name": r["player_name"],
                    "nba_api_id": int(r["nba_api_id"]),
                    "market": market_name, "side": side,
                    "line": line, "juice": juice,
                    "actual": r["actual"],
                    "pregame_usg": r["pregame_usg"],
                    "actual_usg": r["actual_usg"],
                    "result": result, "pnl": pnl,
                })

    # V4 PRIMARY
    if V4_RESID.exists():
        v4 = pd.read_csv(V4_RESID)
        v4["game_date"] = pd.to_datetime(v4["game_date"])
        prop_dates = set(pa["game_date"].dt.date.tolist())
        v4_in = v4[v4["game_date"].dt.date.isin(prop_dates)]
        for _, r in v4_in.iterrows():
            spread_abs = abs(r["close_spread_home"])
            edge = r["edge_total_v4"]
            if spread_abs <= 3 and abs(edge) >= 12 and edge > 0:
                juice = -110
                result, pnl = resolve_bet(r["close_total"], r["actual_total"],
                                           "over", juice)
                if result is None: continue
                ledger_rows.append({
                    "strategy": "V4_PRIMARY_pickem_bigEdge_OVER",
                    "game_date": r["game_date"], "player_name": "",
                    "nba_api_id": 0, "market": "game_total", "side": "over",
                    "line": r["close_total"], "juice": juice,
                    "actual": r["actual_total"],
                    "pregame_usg": np.nan, "actual_usg": np.nan,
                    "result": result, "pnl": pnl,
                })

    ledger = pd.DataFrame(ledger_rows)
    if ledger.empty:
        print("no bets generated")
        return
    ledger.to_csv(OUT_DIR / "bet_ledger.csv", index=False)

    print(f"\n[6/6] Total bets: {len(ledger):,}")
    print(f"\n  ── Per strategy ──")
    summary_rows = []
    for strat, g in ledger.groupby("strategy"):
        n = len(g)
        nw = int((g["result"] == 1).sum())
        nl = int((g["result"] == -1).sum())
        nd = nw + nl
        if nd == 0: continue
        wr = nw / nd
        pnl = g["pnl"].sum()
        roi = pnl / (n * BET_UNIT)
        p_val = stats.binomtest(nw, nd, p=BREAKEVEN, alternative="greater").pvalue
        summary_rows.append({
            "strategy": strat, "n": n, "wins": nw, "losses": nl,
            "WR": round(wr, 4), "ROI": round(roi, 4),
            "PnL": round(pnl, 2), "p_value": round(p_val, 4),
        })
        print(f"  {strat:<40} n={n:>5}  WR={wr*100:>5.1f}%  "
              f"ROI={roi*100:>+6.2f}%  PnL=${pnl:>+9,.2f}  p={p_val:.4f}")

    pd.DataFrame(summary_rows).to_csv(OUT_DIR / "strategy_summary.csv", index=False)

    total_n = len(ledger)
    total_wins = int((ledger["result"] == 1).sum())
    total_losses = int((ledger["result"] == -1).sum())
    total_pnl = ledger["pnl"].sum()
    total_risk = total_n * BET_UNIT
    total_wr = total_wins / (total_wins + total_losses) if (total_wins + total_losses) > 0 else 0
    total_roi = total_pnl / total_risk
    p_total = stats.binomtest(total_wins, total_wins + total_losses,
                               p=BREAKEVEN, alternative="greater").pvalue

    print(f"\n  ── FULL SUITE AGGREGATE (PRE-GAME USG, no look-ahead) ──")
    print(f"  Bets:        {total_n:,}")
    print(f"  W/L:         {total_wins} / {total_losses}")
    print(f"  WR:          {total_wr*100:.2f}%  (breakeven {BREAKEVEN*100:.2f}%)")
    print(f"  PnL:         ${total_pnl:+,.2f}  on ${total_risk:,.0f} risked")
    print(f"  ROI:         {total_roi*100:+.2f}%")
    print(f"  Binomial p:  {p_total:.4f}")

    pd.DataFrame([{
        "scope": "FULL_SUITE_AGGREGATE_PREGAME_USG",
        "n": total_n, "wins": total_wins, "losses": total_losses,
        "WR": round(total_wr, 4), "ROI": round(total_roi, 4),
        "PnL": round(total_pnl, 2), "p_value": round(p_total, 4),
    }]).to_csv(OUT_DIR / "aggregate_summary.csv", index=False)


if __name__ == "__main__":
    main()
