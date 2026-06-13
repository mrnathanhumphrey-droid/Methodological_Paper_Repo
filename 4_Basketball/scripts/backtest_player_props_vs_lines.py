"""Forward-clean test: does v6.1 × s2d MPG ratio beat Vegas player-prop lines?

For each player-game with a priced prop:
  - Look up v6.1 per-game projection for the stat (PTS, AST, REB)
  - Compute s2d MPG (season-to-date through PRIOR games only, forward-clean)
  - Pre-game projection: stat_proj = v6.1_per_game × (s2d_mpg / v6.1_mpg)
  - Compare to Vegas line
  - Bet if |proj - line| >= edge threshold

For combo markets (PA, PRA, PR): sum component projections.

Strategies tested across: PTS, AST, REB, PA, PRA, PR.

No USG quartiles, no post-game info. Live-deploy-realistic.

Outputs at runs/run_player_props_vs_lines/:
  - bet_ledger.csv
  - by_market_summary.csv
  - by_edge_tier.csv
  - PROPS_VS_LINES_RESULTS.md
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
SHIP_PATH = Path("D:/NBA Projections/audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv")
META_PATH = Path("D:/NBA Projections/data/parquet/player_metadata_enriched.parquet")
OUT_DIR = Path("D:/NBA Projections/runs/run_player_props_vs_lines")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BET_UNIT = 100
BREAKEVEN = 110 / 210
MIN_PRIOR_GAMES = 5


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
    """Per (player, game) s2d MPG using strictly prior games this season."""
    rs = box[box["min_played"] > 0].copy()
    rs = rs.sort_values(["nba_api_id", "season", "game_date"])
    grp = rs.groupby(["nba_api_id", "season"])
    rs["s2d_min_sum"] = grp["min_played"].cumsum() - rs["min_played"]
    rs["s2d_n_games"] = grp.cumcount()
    rs["s2d_mpg"] = np.where(
        rs["s2d_n_games"] >= MIN_PRIOR_GAMES,
        rs["s2d_min_sum"] / rs["s2d_n_games"],
        np.nan,
    )
    return rs


def load_ship():
    cols = ["nba_api_id", "PTS_per_game", "REB_per_game", "AST_per_game", "mpg"]
    ship = pd.read_csv(SHIP_PATH, usecols=cols)
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    return ship.set_index("nba_api_id").to_dict("index")


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


# Market → (component box-score stats, ship per_game keys)
MARKET_DEF = {
    "player_points":              (["PTS"], ["PTS_per_game"]),
    "player_assists":             (["AST"], ["AST_per_game"]),
    "player_rebounds":            (["REB"], ["REB_per_game"]),
    "player_points_assists":      (["PTS", "AST"], ["PTS_per_game", "AST_per_game"]),
    "player_points_rebounds":     (["PTS", "REB"], ["PTS_per_game", "REB_per_game"]),
    "player_rebounds_assists":    (["REB", "AST"], ["REB_per_game", "AST_per_game"]),
    "player_points_rebounds_assists": (["PTS", "REB", "AST"],
                                        ["PTS_per_game", "REB_per_game", "AST_per_game"]),
}


def project_pre_game(pid: int, s2d_mpg: float, ship_lookup: dict,
                     ship_keys: list) -> float:
    """Pre-game projection = sum(v6.1_per_game) × (s2d_mpg / v6.1_mpg).

    Returns NaN if any required ship value missing.
    """
    s = ship_lookup.get(pid)
    if s is None: return np.nan
    base_mpg = s.get("mpg")
    if base_mpg is None or base_mpg <= 0 or pd.isna(base_mpg): return np.nan
    ratio = s2d_mpg / base_mpg
    total = 0
    for k in ship_keys:
        v = s.get(k)
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
    print("Player-prop forward-clean backtest — v6.1 × s2d MPG vs lines")
    print("=" * 70)

    print("\n[1/5] Loading data...")
    props = load_props()
    props = props[props["book"] == "draftkings"]
    box = load_box()
    box = add_s2d_mpg(box)
    ship = load_ship()
    print(f"  {len(props):,} props  |  {len(box):,} box rows  |  {len(ship)} ship players")
    print(f"  props date range: {props['game_date'].min().date()} → {props['game_date'].max().date()}")

    print("\n[2/5] Matching players...")
    props = match_player(props)
    print(f"  {len(props):,} props with nba_api_id")

    # Box lookup: s2d MPG + actual stats
    box_lookup = box[["nba_api_id", "game_date", "s2d_mpg", "s2d_n_games",
                       "PTS", "REB", "AST"]].copy()
    box_lookup["game_date"] = pd.to_datetime(box_lookup["game_date"])

    print("\n[3/5] Building per-market bet candidates with projections...")
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

    for market, (comp, ship_keys) in MARKET_DEF.items():
        pairs = pair_market(props, market)
        if pairs.empty:
            continue
        pairs = pairs.merge(box_lookup, on=["nba_api_id", "game_date"], how="inner")
        # require s2d MPG (≥5 prior games)
        pairs = pairs.dropna(subset=["s2d_mpg"])
        # Compute projection per row
        pairs["proj"] = pairs.apply(
            lambda r: project_pre_game(int(r["nba_api_id"]), r["s2d_mpg"],
                                        ship, ship_keys), axis=1)
        pairs = pairs.dropna(subset=["proj"])
        # Actual stat sum
        pairs["actual"] = pairs[comp].sum(axis=1)

        edge_t = edge_thresholds.get(market, 1.5)
        # Use OVER line as reference (over+under usually same line; pick avg if differ)
        pairs["line"] = pairs[["line_over", "line_under"]].mean(axis=1)
        pairs["edge"] = pairs["proj"] - pairs["line"]
        pairs["side"] = np.where(pairs["edge"] >= edge_t, "over",
                          np.where(pairs["edge"] <= -edge_t, "under", "skip"))
        bets = pairs[pairs["side"] != "skip"].copy()
        bets["market"] = market

        # Resolve
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
        print(f"  {market:<35} {len(bets):>5} bets (of {len(pairs):>5} priced player-games)")
        all_bets.append(bets[["game_date", "nba_api_id", "player_name",
                                "market", "side", "line_used", "juice",
                                "proj", "edge", "actual", "result", "pnl"]])

    if not all_bets:
        print("no bets generated"); return
    ledger = pd.concat(all_bets, ignore_index=True)
    ledger.to_csv(OUT_DIR / "bet_ledger.csv", index=False)
    print(f"\n  Total bets across all markets: {len(ledger):,}")

    print("\n[4/5] Per-market summary...")
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

    # Aggregate
    n = len(ledger)
    nw = int((ledger["result"] == 1).sum())
    nl = int((ledger["result"] == -1).sum())
    nd = nw + nl
    wr = nw / nd
    pnl = ledger["pnl"].sum()
    roi = pnl / (n * BET_UNIT)
    p = stats.binomtest(nw, nd, p=BREAKEVEN, alternative="greater").pvalue
    print(f"\n  ── AGGREGATE (all markets) ──")
    print(f"  Bets: {n:,}  WR: {wr*100:.2f}%  ROI: {roi*100:+.2f}%  "
          f"PnL: ${pnl:+,.2f}  p: {p:.4f}")

    print("\n[5/5] By edge tier per market...")
    edge_rows = []
    for market in ledger["market"].unique():
        sub = ledger[ledger["market"] == market].copy()
        sub["edge_abs"] = sub["edge"].abs()
        # Adaptive bins
        try:
            sub["edge_tier"] = pd.qcut(sub["edge_abs"], 4,
                                       labels=["Q1_small", "Q2", "Q3", "Q4_big"],
                                       duplicates="drop")
        except Exception:
            continue
        for tier in sub["edge_tier"].dropna().unique():
            tsub = sub[sub["edge_tier"] == tier]
            n = len(tsub)
            nw = int((tsub["result"] == 1).sum())
            nl = int((tsub["result"] == -1).sum())
            nd = nw + nl
            if nd < 30: continue
            wr = nw / nd
            pnl = tsub["pnl"].sum()
            roi = pnl / (n * BET_UNIT)
            edge_rows.append({
                "market": market, "edge_tier": str(tier), "n": n,
                "WR": round(wr, 4), "ROI": round(roi, 4),
                "min_edge_abs": round(tsub["edge_abs"].min(), 2),
                "max_edge_abs": round(tsub["edge_abs"].max(), 2),
            })
    edge_df = pd.DataFrame(edge_rows)
    if not edge_df.empty:
        edge_df = edge_df.sort_values(["market", "edge_tier"])
        edge_df.to_csv(OUT_DIR / "by_edge_tier.csv", index=False)
        print("\n  By edge tier (top 20 ROI):")
        print(edge_df.sort_values("ROI", ascending=False).head(20).to_string(index=False))

    # Markdown
    md = OUT_DIR / "PROPS_VS_LINES_RESULTS.md"
    with open(md, "w", encoding="utf-8") as f:
        f.write("# Player-Prop Forward-Clean Backtest\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n")
        f.write("**Method:** for each priced player-game, compute pre-game projection as "
                "`v6.1_per_game × (s2d_MPG / v6.1_baseline_MPG)` where s2d_MPG uses ONLY "
                "prior games in season. Bet OVER if proj exceeds line by edge threshold, "
                "UNDER if below.\n\n")
        f.write("## Per-market\n\n")
        f.write(pd.DataFrame(summary_rows).to_markdown(index=False) + "\n\n")
        f.write(f"\n**Aggregate:** {len(ledger):,} bets, "
                f"WR={wr*100:.2f}%, ROI={roi*100:+.2f}%, p={p:.4f}\n\n")
        if not edge_df.empty:
            f.write("## By edge tier (top ROI rows)\n\n")
            f.write(edge_df.sort_values("ROI", ascending=False).head(20).to_markdown(index=False))
    print(f"\n  → {md}")


if __name__ == "__main__":
    main()
