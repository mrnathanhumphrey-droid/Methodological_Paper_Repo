"""Unified bet simulator — runs full projection suite as if it were the live
betting system across all available historical data.

Strategies bundled:
  S1. PA Q1 UNDER + Q4 OVER  (deployed edge, +17/-16pp validated)
  S2. PRA Q1 UNDER + Q4 OVER (deployed, replicates PA)
  S3. PR Q1 UNDER + Q4 OVER  (deployed, replicates PA)
  S4. V4 PRIMARY: pickem (≤3) + |edge_v4| ≥ 12 + OVER side

Each player-game flows through PA/PRA/PR strategies independently if
priced. Game-total strategy fires once per game.

Bet sizing: flat $100 per bet, -110 vig (or actual juice if priced).

Outputs at D:/NBA Projections/runs/run_unified_bet_sim/:
  - bet_ledger.csv (every bet placed + outcome + PnL)
  - strategy_summary.csv (WR/ROI/PnL by strategy)
  - aggregate_summary.csv (combined view)
  - UNIFIED_RESULTS.md
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
V4_RESID = Path("D:/NBA Projections/runs/run_nba_game_totals_22_26/v4_pace_adjusted/game_residuals.csv")
OUT_DIR = Path("D:/NBA Projections/runs/run_unified_bet_sim")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BET_UNIT = 100
BREAKEVEN = 110 / 210


def american_to_prob(price: float) -> float:
    """Vig-stripped implied probability from a single side."""
    if price > 0:
        return 100 / (price + 100)
    return -price / (-price + 100)


def american_payout(price: float) -> float:
    """Net profit per $1 bet."""
    if price > 0:
        return price / 100
    return 100 / -price


def vig_stripped(price_over: float, price_under: float, side: str) -> float:
    """Strip vig proportionally; return implied probability for `side`."""
    p_o = american_to_prob(price_over)
    p_u = american_to_prob(price_under)
    total = p_o + p_u
    if total == 0: return 0.5
    if side == "over":
        return p_o / total
    return p_u / total


def load_props() -> pd.DataFrame:
    files = sorted(PROPS_DIR.glob("*draftkings*.parquet"))
    if not files:
        raise FileNotFoundError(f"no draftkings files in {PROPS_DIR}")
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    df["commence_dt_utc"] = pd.to_datetime(df["commence_time"], utc=True)
    df["game_date"] = df["commence_dt_utc"].dt.tz_convert("US/Eastern").dt.date
    df["game_date"] = pd.to_datetime(df["game_date"])
    return df


def parse_min(m):
    if pd.isna(m): return 0.0
    if isinstance(m, (int, float)): return float(m)
    try:
        parts = str(m).split(":")
        return float(parts[0]) + (float(parts[1]) / 60 if len(parts) > 1 else 0)
    except (ValueError, TypeError):
        return 0.0


def load_box_for_usg() -> pd.DataFrame:
    """Per (player, game) box stats sufficient to compute USG."""
    cols = ["nba_api_id", "game_id", "game_date", "team_abbr", "minutes",
            "FGA", "FTA", "TOV", "PTS", "REB", "AST"]
    box = pd.read_parquet(BOX_PATH, columns=cols)
    box = box[pd.notna(box["nba_api_id"])].copy()
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    box["game_date"] = pd.to_datetime(box["game_date"])
    box["min_played"] = box["minutes"].apply(parse_min)
    box = box[box["min_played"] >= 10]  # filter DNPs / garbage
    return box


def compute_usg(box: pd.DataFrame) -> pd.DataFrame:
    """Add USG% per player-game. Standard formula."""
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


def match_player_to_box(props: pd.DataFrame, box: pd.DataFrame) -> pd.DataFrame:
    """Match prop rows to box-score rows via name + game_date.

    Build a name → nba_api_id map from box. Normalize names lightly.
    """
    import unicodedata
    def _norm(name):
        if not isinstance(name, str): return ""
        s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
        for suf in [" jr.", " jr", " sr.", " sr", " ii", " iii", " iv"]:
            if s.endswith(suf): s = s[:-len(suf)]
        return "".join(c for c in s if c.isalnum() or c.isspace()).strip()

    # Build name → set of (pid, game_date) cells
    box["name_norm"] = (box["nba_api_id"].astype(str))  # placeholder
    # We'll join on player_name + game_date
    # First get a stable name from box — need to pull names; box-score doesn't have name col
    # So use a separate metadata source
    META_PATH = Path("D:/NBA Projections/data/parquet/player_metadata_enriched.parquet")
    if META_PATH.exists():
        meta = pd.read_parquet(META_PATH)
        meta = meta[pd.notna(meta["nba_api_id"])].copy()
        meta["nba_api_id"] = meta["nba_api_id"].astype(int)
        # name column candidates
        for nm_col in ("name", "player_name", "full_name", "display_name"):
            if nm_col in meta.columns:
                meta["name_norm"] = meta[nm_col].apply(_norm)
                break
        else:
            raise SystemExit("no name column found in player_metadata_enriched")
        name_to_pid = dict(zip(meta["name_norm"], meta["nba_api_id"]))
    else:
        raise SystemExit("player_metadata_enriched.parquet not found")

    props["name_norm"] = props["player_name"].apply(_norm)
    props["nba_api_id"] = props["name_norm"].map(name_to_pid)
    matched = props.dropna(subset=["nba_api_id"]).copy()
    matched["nba_api_id"] = matched["nba_api_id"].astype(int)
    return matched


def pair_market_sides(props: pd.DataFrame, market: str) -> pd.DataFrame:
    """One row per (player, game_date, market) with over+under sides paired."""
    m = props[props["market"] == market]
    if m.empty:
        return pd.DataFrame()
    over = m[m["side"] == "Over"][[
        "game_date", "nba_api_id", "player_name", "line", "juice_american"
    ]].rename(columns={"line": "line_over", "juice_american": "juice_over"})
    under = m[m["side"] == "Under"][[
        "game_date", "nba_api_id", "line", "juice_american"
    ]].rename(columns={"line": "line_under", "juice_american": "juice_under"})
    joined = over.merge(under, on=["game_date", "nba_api_id"], how="inner")
    return joined


def resolve_bet(line: float, actual: float, side: str,
                juice: float) -> tuple[int, float]:
    """Returns (result_code, pnl).  1=win, -1=loss, 0=push."""
    if actual == line:
        return 0, 0.0
    over = actual > line
    won = (side == "over" and over) or (side == "under" and not over)
    if won:
        return 1, BET_UNIT * american_payout(juice)
    return -1, -BET_UNIT


def main():
    print("=" * 70)
    print("Unified bet simulator — projection suite as live betting system")
    print("=" * 70)

    print("\n[1/5] Loading props (DK only)...")
    props = load_props()
    props = props[props["book"] == "draftkings"]
    print(f"  {len(props):,} prop rows, "
          f"{props['game_date'].min().date()} → {props['game_date'].max().date()}")

    print("\n[2/5] Loading box scores + computing USG...")
    box = load_box_for_usg()
    box = compute_usg(box)
    print(f"  {len(box):,} player-game rows (min ≥ 10)")

    print("\n[3/5] Matching props ↔ box via player metadata...")
    props_matched = match_player_to_box(props, box)
    print(f"  {len(props_matched):,} prop rows matched to nba_api_id")

    # ── Pair sides for each market we care about ─────────────────────
    print("\n[4/5] Building per-market over+under pairings + resolving outcomes...")
    market_actual = {
        "player_points": "PTS",
        "player_assists": "AST",
        "player_points_assists": ("PTS", "AST"),
        "player_points_rebounds": ("PTS", "REB"),
        "player_rebounds_assists": ("REB", "AST"),
        "player_points_rebounds_assists": ("PTS", "REB", "AST"),
    }

    # Subset box to (pid, date) → actual stat columns for lookup
    box_lookup = box[["nba_api_id", "game_date", "PTS", "REB", "AST", "USG"]].copy()
    box_lookup["game_date"] = pd.to_datetime(box_lookup["game_date"])

    market_pairs = {}
    for market in market_actual.keys():
        paired = pair_market_sides(props_matched, market)
        if paired.empty:
            continue
        paired = paired.merge(box_lookup, on=["nba_api_id", "game_date"],
                              how="inner")
        # Compute actual stat
        comp = market_actual[market]
        if isinstance(comp, tuple):
            paired["actual"] = paired[list(comp)].sum(axis=1)
        else:
            paired["actual"] = paired[comp]
        market_pairs[market] = paired
        print(f"  {market}: {len(paired):,} paired player-games")

    # ── USG quartile assignment (pooled over full sample) ───────────
    # Use PA market as the canonical USG-stratification source
    pa = market_pairs.get("player_points_assists")
    if pa is None or pa.empty:
        raise SystemExit("no PA market data — cannot run")
    usg_breaks = pd.qcut(pa["USG"], 4, retbins=True, duplicates="drop")[1]
    print(f"  USG quartile breaks: {[round(b, 3) for b in usg_breaks]}")

    def usg_q(usg):
        for i in range(1, len(usg_breaks)):
            if usg <= usg_breaks[i]:
                return i
        return len(usg_breaks) - 1

    # ── Apply strategies + resolve ────────────────────────────────────
    print("\n[5/5] Applying strategies + resolving...")
    ledger_rows = []
    for market_name, market_label, q1_side, q4_side in [
        ("player_points_assists", "PA", "under", "over"),
        ("player_points_rebounds_assists", "PRA", "under", "over"),
        ("player_points_rebounds", "PR", "under", "over"),
    ]:
        df = market_pairs.get(market_name)
        if df is None or df.empty:
            print(f"  {market_label}: no data, skip")
            continue
        df = df.dropna(subset=["USG"]).copy()
        df["q"] = df["USG"].apply(usg_q)

        # Q1 strategy: bet `q1_side`
        q1 = df[df["q"] == 1].copy()
        for _, r in q1.iterrows():
            line = r["line_under"] if q1_side == "under" else r["line_over"]
            juice = r["juice_under"] if q1_side == "under" else r["juice_over"]
            result, pnl = resolve_bet(line, r["actual"], q1_side, juice)
            ledger_rows.append({
                "strategy": f"{market_label}_Q1_{q1_side.upper()}",
                "game_date": r["game_date"], "player_name": r["player_name"],
                "nba_api_id": int(r["nba_api_id"]),
                "market": market_name, "side": q1_side,
                "line": line, "juice": juice,
                "actual": r["actual"], "USG": r["USG"],
                "result": result, "pnl": pnl,
            })

        # Q4 strategy: bet `q4_side`
        q4 = df[df["q"] == 4].copy()
        for _, r in q4.iterrows():
            line = r["line_under"] if q4_side == "under" else r["line_over"]
            juice = r["juice_under"] if q4_side == "under" else r["juice_over"]
            result, pnl = resolve_bet(line, r["actual"], q4_side, juice)
            ledger_rows.append({
                "strategy": f"{market_label}_Q4_{q4_side.upper()}",
                "game_date": r["game_date"], "player_name": r["player_name"],
                "nba_api_id": int(r["nba_api_id"]),
                "market": market_name, "side": q4_side,
                "line": line, "juice": juice,
                "actual": r["actual"], "USG": r["USG"],
                "result": result, "pnl": pnl,
            })

    # ── V4 game-totals PRIMARY ────────────────────────────────────────
    if V4_RESID.exists():
        v4 = pd.read_csv(V4_RESID)
        v4["game_date"] = pd.to_datetime(v4["game_date"])
        # Match the dates we have prop data for
        prop_dates = set(pa["game_date"].dt.date.tolist())
        v4_in = v4[v4["game_date"].dt.date.isin(prop_dates)].copy()
        # Apply PRIMARY rule on V4 edges
        for _, r in v4_in.iterrows():
            spread_abs = abs(r["close_spread_home"])
            edge = r["edge_total_v4"]
            if spread_abs <= 3 and abs(edge) >= 12 and edge > 0:
                # Bet OVER, vig assumed -110 (lines parquet didn't carry juice)
                juice = -110
                if r["actual_total"] == r["close_total"]:
                    result, pnl = 0, 0
                else:
                    over = r["actual_total"] > r["close_total"]
                    result = 1 if over else -1
                    pnl = BET_UNIT * american_payout(juice) if over else -BET_UNIT
                ledger_rows.append({
                    "strategy": "V4_PRIMARY_pickem_bigEdge_OVER",
                    "game_date": r["game_date"],
                    "player_name": "",
                    "nba_api_id": 0,
                    "market": "game_total",
                    "side": "over",
                    "line": r["close_total"],
                    "juice": juice,
                    "actual": r["actual_total"],
                    "USG": np.nan,
                    "result": result, "pnl": pnl,
                })

    # ── Aggregate ─────────────────────────────────────────────────────
    ledger = pd.DataFrame(ledger_rows)
    if ledger.empty:
        print("  no bets generated; exiting")
        return
    ledger.to_csv(OUT_DIR / "bet_ledger.csv", index=False)

    print(f"\n  Total bets: {len(ledger):,}")
    print(f"\n  ── Per strategy ──")
    summary_rows = []
    for strat, g in ledger.groupby("strategy"):
        n = len(g)
        nw = int((g["result"] == 1).sum())
        nl = int((g["result"] == -1).sum())
        nd = nw + nl
        if nd == 0:
            continue
        wr = nw / nd
        pnl = g["pnl"].sum()
        roi = pnl / (n * BET_UNIT)
        p_val = stats.binomtest(nw, nd, p=BREAKEVEN,
                                alternative="greater").pvalue
        summary_rows.append({
            "strategy": strat, "n": n, "wins": nw, "losses": nl,
            "WR": round(wr, 4), "ROI": round(roi, 4),
            "PnL": round(pnl, 2), "p_value": round(p_val, 4),
        })
        print(f"  {strat:<40} n={n:>5}  WR={wr*100:>5.1f}%  "
              f"ROI={roi*100:>+6.2f}%  PnL=${pnl:>+9,.2f}  p={p_val:.4f}")

    pd.DataFrame(summary_rows).to_csv(OUT_DIR / "strategy_summary.csv", index=False)

    # ── Aggregate (full suite) ────────────────────────────────────────
    total_n = len(ledger)
    total_wins = int((ledger["result"] == 1).sum())
    total_losses = int((ledger["result"] == -1).sum())
    total_pnl = ledger["pnl"].sum()
    total_risk = total_n * BET_UNIT
    total_wr = total_wins / (total_wins + total_losses) if (total_wins + total_losses) > 0 else 0
    total_roi = total_pnl / total_risk
    p_total = stats.binomtest(total_wins, total_wins + total_losses,
                               p=BREAKEVEN, alternative="greater").pvalue

    print(f"\n  ── FULL SUITE AGGREGATE ──")
    print(f"  Bets:        {total_n:,}")
    print(f"  W/L:         {total_wins} / {total_losses}")
    print(f"  WR:          {total_wr*100:.2f}%  (breakeven {BREAKEVEN*100:.2f}%)")
    print(f"  PnL:         ${total_pnl:+,.2f}  on ${total_risk:,.0f} risked")
    print(f"  ROI:         {total_roi*100:+.2f}%")
    print(f"  Binomial p:  {p_total:.4f}")

    pd.DataFrame([{
        "scope": "FULL_SUITE_AGGREGATE",
        "n": total_n, "wins": total_wins, "losses": total_losses,
        "WR": round(total_wr, 4), "ROI": round(total_roi, 4),
        "PnL": round(total_pnl, 2), "p_value": round(p_total, 4),
    }]).to_csv(OUT_DIR / "aggregate_summary.csv", index=False)

    # Equity curve
    ledger_sorted = ledger.sort_values("game_date").reset_index(drop=True)
    ledger_sorted["cum_pnl"] = ledger_sorted["pnl"].cumsum()
    ledger_sorted["cum_max"] = ledger_sorted["cum_pnl"].cummax()
    ledger_sorted["drawdown"] = ledger_sorted["cum_pnl"] - ledger_sorted["cum_max"]
    max_dd = float(ledger_sorted["drawdown"].min())
    peak = float(ledger_sorted["cum_pnl"].max())
    ledger_sorted.to_csv(OUT_DIR / "bet_ledger_chrono.csv", index=False)
    print(f"\n  Peak PnL:    ${peak:+,.2f}")
    print(f"  Max DD:      ${max_dd:+,.2f}")

    md = OUT_DIR / "UNIFIED_RESULTS.md"
    with open(md, "w", encoding="utf-8") as f:
        f.write("# Unified Bet Simulator — Full Projection Suite vs Vegas\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n")
        f.write("## Strategies bundled\n\n")
        f.write("- **PA Q1 UNDER** + **PA Q4 OVER** (deployed combo edge)\n")
        f.write("- **PRA Q1 UNDER** + **PRA Q4 OVER** (deployed)\n")
        f.write("- **PR Q1 UNDER** + **PR Q4 OVER** (deployed)\n")
        f.write("- **V4 PRIMARY**: pickem ≤3 + |edge| ≥ 12 + OVER game total\n\n")
        f.write("## Per-strategy results\n\n")
        f.write(pd.DataFrame(summary_rows).to_markdown(index=False) + "\n\n")
        f.write("## Full-suite aggregate\n\n")
        f.write(f"- Bets: **{total_n:,}**\n")
        f.write(f"- Wins / Losses: **{total_wins} / {total_losses}**\n")
        f.write(f"- WR: **{total_wr*100:.2f}%** (breakeven {BREAKEVEN*100:.2f}%)\n")
        f.write(f"- ROI: **{total_roi*100:+.2f}%**\n")
        f.write(f"- PnL: **${total_pnl:+,.2f}** on ${total_risk:,.0f} risked\n")
        f.write(f"- Binomial p (WR > BE, one-sided): **{p_total:.4f}**\n")
        f.write(f"- Peak PnL: ${peak:+,.2f}  |  Max drawdown: ${max_dd:+,.2f}\n")
    print(f"\n  → {md}")


if __name__ == "__main__":
    main()
