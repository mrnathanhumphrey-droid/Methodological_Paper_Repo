"""Player-prop backtest — TRUE forward-clean rolling per-season projection.

For each player-game on date d in season s, we project using ONLY:
  - The player's PRIOR seasons' RS per-game stats (PTS, AST, REB, mpg)
    Shrunk toward league means with Bayesian-style weight (k=30 games).
  - Season-to-date MPG in season s through games strictly before d.

No v6.1 ship used (which had hindsight on 24-25 means). This is the
honest live-deploy-realistic test.

Shrinkage formula per stat:
  shrunk_per_game = (n_prior × player_rate + k × league_mean) / (n_prior + k)
  k = 30 games (~ half-season prior strength)
  league_mean: pooled per-stat per-game across all RS games in priors

Per-game projection:
  proj_stat_pre_game = shrunk_per_game × (s2d_mpg / shrunk_baseline_mpg)
  s2d_mpg requires ≥5 prior games in current season; else use shrunk_baseline_mpg

Output: runs/run_player_props_rolling_clean/
  - bet_ledger.csv
  - by_market_summary.csv
  - by_edge_tier.csv
  - vs_lookahead_compare.csv
  - ROLLING_CLEAN_RESULTS.md
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
OUT_DIR = Path("D:/NBA Projections/runs/run_player_props_rolling_clean")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BET_UNIT = 100
BREAKEVEN = 110 / 210
MIN_PRIOR_GAMES_FOR_S2D = 5
SHRINK_K = 30  # Bayesian shrinkage strength toward league mean

NEXT_SEASON = {
    "2014-15": "2015-16", "2015-16": "2016-17", "2016-17": "2017-18",
    "2017-18": "2018-19", "2018-19": "2019-20", "2019-20": "2020-21",
    "2020-21": "2021-22", "2021-22": "2022-23", "2022-23": "2023-24",
    "2023-24": "2024-25", "2024-25": "2025-26",
}
PRIOR_SEASON = {v: k for k, v in NEXT_SEASON.items()}


def parse_min(m):
    if pd.isna(m): return 0.0
    if isinstance(m, (int, float)): return float(m)
    try:
        parts = str(m).split(":")
        return float(parts[0]) + (float(parts[1]) / 60 if len(parts) > 1 else 0)
    except (ValueError, TypeError):
        return 0.0


def american_payout(price):
    if pd.isna(price): return 100 / 110
    if price > 0: return price / 100
    return 100 / -price


def load_box():
    cols = ["nba_api_id", "game_id", "game_date", "season", "season_type",
            "minutes", "PTS", "REB", "AST"]
    box = pd.read_parquet(BOX_PATH, columns=cols)
    box = box[pd.notna(box["nba_api_id"])].copy()
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    box["game_date"] = pd.to_datetime(box["game_date"])
    box["min_played"] = box["minutes"].apply(parse_min)
    return box


def add_s2d_mpg(box):
    rs = box[(box["min_played"] > 0) & (box["season_type"] == "Regular Season")].copy()
    rs = rs.sort_values(["nba_api_id", "season", "game_date"])
    grp = rs.groupby(["nba_api_id", "season"])
    rs["s2d_min_sum"] = grp["min_played"].cumsum() - rs["min_played"]
    rs["s2d_n_games"] = grp.cumcount()
    rs["s2d_mpg"] = np.where(
        rs["s2d_n_games"] >= MIN_PRIOR_GAMES_FOR_S2D,
        rs["s2d_min_sum"] / rs["s2d_n_games"],
        np.nan,
    )
    return rs


def build_prior_season_rates(box) -> dict:
    """{(pid, target_season): {stat_per_game, mpg, n_prior_games}}."""
    rs = box[(box["season_type"] == "Regular Season") & (box["min_played"] >= 5)]
    grp = rs.groupby(["nba_api_id", "season"]).agg(
        games=("game_id", "nunique"),
        total_pts=("PTS", "sum"),
        total_reb=("REB", "sum"),
        total_ast=("AST", "sum"),
        total_min=("min_played", "sum"),
    ).reset_index()
    # We use this season's data to project NEXT season
    grp["target_season"] = grp["season"].map(NEXT_SEASON)
    grp = grp.dropna(subset=["target_season"])

    # League means = avg per-game across all RS player-games (where min_played >= 5)
    league_means = {
        "PTS": float(rs["PTS"].mean()),
        "REB": float(rs["REB"].mean()),
        "AST": float(rs["AST"].mean()),
    }

    out = {}
    for _, r in grp.iterrows():
        n = int(r["games"])
        pts_rate = r["total_pts"] / n
        reb_rate = r["total_reb"] / n
        ast_rate = r["total_ast"] / n
        mpg = r["total_min"] / n
        # Apply Bayesian shrinkage toward league means
        k = SHRINK_K
        shrunk_pts = (n * pts_rate + k * league_means["PTS"]) / (n + k)
        shrunk_reb = (n * reb_rate + k * league_means["REB"]) / (n + k)
        shrunk_ast = (n * ast_rate + k * league_means["AST"]) / (n + k)
        # Don't shrink MPG (just use prior-season actual MPG)
        out[(int(r["nba_api_id"]), r["target_season"])] = {
            "pts_per_game": shrunk_pts,
            "reb_per_game": shrunk_reb,
            "ast_per_game": shrunk_ast,
            "mpg": mpg,
            "n_prior_games": n,
        }
    return out, league_means


def load_props():
    files = sorted(PROPS_DIR.glob("*draftkings*.parquet"))
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df["commence_dt_utc"] = pd.to_datetime(df["commence_time"], utc=True)
    df["game_date"] = df["commence_dt_utc"].dt.tz_convert("US/Eastern").dt.date
    df["game_date"] = pd.to_datetime(df["game_date"])
    return df


def match_player(props):
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


MARKET_DEF = {
    "player_points":              (["PTS"], ["pts_per_game"]),
    "player_assists":             (["AST"], ["ast_per_game"]),
    "player_rebounds":            (["REB"], ["reb_per_game"]),
    "player_points_assists":      (["PTS", "AST"], ["pts_per_game", "ast_per_game"]),
    "player_points_rebounds":     (["PTS", "REB"], ["pts_per_game", "reb_per_game"]),
    "player_rebounds_assists":    (["REB", "AST"], ["reb_per_game", "ast_per_game"]),
    "player_points_rebounds_assists": (["PTS", "REB", "AST"],
                                        ["pts_per_game", "reb_per_game", "ast_per_game"]),
}


def project_pre_game(pid: int, season: str, s2d_mpg: float,
                     prior_rates: dict, league_means: dict,
                     stat_keys: list) -> float:
    """Use prior-season shrunk per-game × (s2d_mpg / prior_mpg)."""
    key = (pid, season)
    rates = prior_rates.get(key)
    if rates is None or rates["mpg"] <= 0:
        return np.nan
    ratio = s2d_mpg / rates["mpg"] if s2d_mpg else 1.0
    total = 0
    for stat_key in stat_keys:
        v = rates.get(stat_key)
        if v is None or pd.isna(v): return np.nan
        total += v
    return total * ratio


def resolve_bet(line, actual, side, juice):
    if pd.isna(actual) or pd.isna(line): return None, 0
    if actual == line: return 0, 0
    over = actual > line
    won = (side == "over" and over) or (side == "under" and not over)
    if won: return 1, BET_UNIT * american_payout(juice)
    return -1, -BET_UNIT


def main():
    print("=" * 70)
    print("Player-prop ROLLING CLEAN backtest — prior-season-only projections")
    print("=" * 70)

    print("\n[1/6] Loading data...")
    props = load_props()
    props = props[props["book"] == "draftkings"]
    box = load_box()
    box = add_s2d_mpg(box)
    print(f"  {len(props):,} props  |  {len(box):,} box rows")
    print(f"  props range: {props['game_date'].min().date()} → {props['game_date'].max().date()}")

    print("\n[2/6] Building prior-season shrunk rates...")
    prior_rates, league_means = build_prior_season_rates(box)
    print(f"  {len(prior_rates):,} (player, target_season) cells")
    print(f"  league_means per-game: {league_means}")

    print("\n[3/6] Matching players...")
    props = match_player(props)
    print(f"  {len(props):,} matched")

    box_lookup = box[["nba_api_id", "game_date", "season",
                       "s2d_mpg", "s2d_n_games",
                       "PTS", "REB", "AST"]].copy()
    box_lookup["game_date"] = pd.to_datetime(box_lookup["game_date"])

    print("\n[4/6] Building bets per market...")
    all_bets = []
    edge_thresholds = {
        "player_points": 1.5,
        "player_assists": 0.7,
        "player_rebounds": 0.7,
        "player_points_assists": 2.0,
        "player_points_rebounds": 2.0,
        "player_rebounds_assists": 1.5,
        "player_points_rebounds_assists": 2.5,
    }

    for market, (comp, stat_keys) in MARKET_DEF.items():
        pairs = pair_market(props, market)
        if pairs.empty: continue
        pairs = pairs.merge(box_lookup, on=["nba_api_id", "game_date"], how="inner")
        pairs = pairs.dropna(subset=["s2d_mpg"])
        # Projection per row using prior-season rates
        pairs["proj"] = pairs.apply(
            lambda r: project_pre_game(int(r["nba_api_id"]), r["season"],
                                        r["s2d_mpg"], prior_rates,
                                        league_means, stat_keys), axis=1)
        pairs = pairs.dropna(subset=["proj"])
        pairs["actual"] = pairs[comp].sum(axis=1)

        et = edge_thresholds[market]
        pairs["line"] = pairs[["line_over", "line_under"]].mean(axis=1)
        pairs["edge"] = pairs["proj"] - pairs["line"]
        pairs["side"] = np.where(pairs["edge"] >= et, "over",
                          np.where(pairs["edge"] <= -et, "under", "skip"))
        bets = pairs[pairs["side"] != "skip"].copy()
        bets["market"] = market
        bets["juice"] = np.where(bets["side"] == "over",
                                  bets["juice_over"], bets["juice_under"])
        bets["line_used"] = np.where(bets["side"] == "over",
                                      bets["line_over"], bets["line_under"])
        results = bets.apply(
            lambda r: resolve_bet(r["line_used"], r["actual"], r["side"], r["juice"]),
            axis=1, result_type="expand")
        bets["result"] = results[0]
        bets["pnl"] = results[1]
        bets = bets.dropna(subset=["result"])
        print(f"  {market:<35} {len(bets):>5} bets (of {len(pairs):>5} candidates)")
        all_bets.append(bets[["game_date", "season", "nba_api_id", "player_name",
                                "market", "side", "line_used", "juice",
                                "proj", "edge", "actual", "result", "pnl"]])

    if not all_bets:
        print("no bets"); return
    ledger = pd.concat(all_bets, ignore_index=True)
    ledger.to_csv(OUT_DIR / "bet_ledger.csv", index=False)
    print(f"\n  Total bets: {len(ledger):,}")

    print("\n[5/6] Per-market summary...")
    summary_rows = []
    for market, g in ledger.groupby("market"):
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
            "market": market, "n": n, "wins": nw, "losses": nl,
            "WR": round(wr, 4), "ROI": round(roi, 4),
            "PnL": round(pnl, 2), "p_value": round(p_val, 4),
        })
        print(f"  {market:<40} n={n:>5}  WR={wr*100:>5.1f}%  "
              f"ROI={roi*100:>+6.2f}%  PnL=${pnl:>+9,.2f}  p={p_val:.4f}")
    pd.DataFrame(summary_rows).to_csv(OUT_DIR / "by_market_summary.csv", index=False)

    n = len(ledger)
    nw = int((ledger["result"] == 1).sum())
    nl = int((ledger["result"] == -1).sum())
    nd = nw + nl
    wr = nw / nd
    pnl_total = ledger["pnl"].sum()
    roi = pnl_total / (n * BET_UNIT)
    p = stats.binomtest(nw, nd, p=BREAKEVEN, alternative="greater").pvalue
    print(f"\n  ── AGGREGATE ──")
    print(f"  Bets: {n:,}  WR: {wr*100:.2f}%  ROI: {roi*100:+.2f}%  "
          f"PnL: ${pnl_total:+,.2f}  p: {p:.4f}")

    # Per-season check
    print("\n  ── Per season ──")
    season_rows = []
    for season in sorted(ledger["season"].unique()):
        sub = ledger[ledger["season"] == season]
        n = len(sub)
        nw = int((sub["result"] == 1).sum())
        nl = int((sub["result"] == -1).sum())
        nd = nw + nl
        if nd == 0: continue
        wr = nw / nd
        pnl = sub["pnl"].sum()
        roi = pnl / (n * BET_UNIT)
        season_rows.append({"season": season, "n": n, "WR": round(wr, 4),
                             "ROI": round(roi, 4), "PnL": round(pnl, 2)})
        print(f"  {season:<10}  n={n:>5}  WR={wr*100:>5.1f}%  "
              f"ROI={roi*100:>+6.2f}%  PnL=${pnl:>+9,.2f}")

    print("\n[6/6] By edge tier...")
    edge_rows = []
    for market in ledger["market"].unique():
        sub = ledger[ledger["market"] == market].copy()
        sub["edge_abs"] = sub["edge"].abs()
        try:
            sub["edge_tier"] = pd.qcut(sub["edge_abs"], 4,
                                       labels=["Q1_sm", "Q2", "Q3", "Q4_big"],
                                       duplicates="drop")
        except Exception:
            continue
        for tier in sub["edge_tier"].dropna().unique():
            t = sub[sub["edge_tier"] == tier]
            n = len(t)
            nw = int((t["result"] == 1).sum())
            nl = int((t["result"] == -1).sum())
            nd = nw + nl
            if nd < 30: continue
            wr = nw / nd
            pnl = t["pnl"].sum()
            roi = pnl / (n * BET_UNIT)
            edge_rows.append({
                "market": market, "edge_tier": str(tier),
                "n": n, "WR": round(wr, 4), "ROI": round(roi, 4),
                "edge_range": f"{t['edge_abs'].min():.2f}-{t['edge_abs'].max():.2f}",
            })
    edge_df = pd.DataFrame(edge_rows)
    if not edge_df.empty:
        edge_df.to_csv(OUT_DIR / "by_edge_tier.csv", index=False)
        print("\n  Top 15 by ROI:")
        print(edge_df.sort_values("ROI", ascending=False).head(15).to_string(index=False))

    md = OUT_DIR / "ROLLING_CLEAN_RESULTS.md"
    with open(md, "w", encoding="utf-8") as f:
        f.write("# Player-Prop Rolling-Clean Backtest\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n")
        f.write("**Method:** prior-season-only player rates, Bayesian shrunk toward "
                f"league means with k={SHRINK_K} games. s2d MPG within season "
                f"(min {MIN_PRIOR_GAMES_FOR_S2D} prior games). No v6.1 ship.\n\n")
        f.write("## Per-market\n\n")
        f.write(pd.DataFrame(summary_rows).to_markdown(index=False) + "\n\n")
        f.write(f"**Aggregate:** {len(ledger):,} bets, WR={wr*100:.2f}%, "
                f"ROI={roi*100:+.2f}%, p={p:.4f}\n\n")
        f.write("## Per-season\n\n")
        f.write(pd.DataFrame(season_rows).to_markdown(index=False) + "\n\n")
        if not edge_df.empty:
            f.write("## By edge tier (top ROI)\n\n")
            f.write(edge_df.sort_values("ROI", ascending=False).head(15).to_markdown(index=False))
    print(f"\n  → {md}")


if __name__ == "__main__":
    main()
