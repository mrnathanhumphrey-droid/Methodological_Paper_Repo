"""Out-of-sample test: simulate betting top N EV recommendations per night.

Uses D:/sports_lines/data/live_recommendations/*_recommendations.parquet —
the live system's output ranked by ev_per_dollar. Pure OOS: these files
were generated daily as system outputs, not used as inputs to any of our
projection models.

For each night during the test window:
  1. Sort recommendations by ev_per_dollar descending
  2. Take top N (default 15)
  3. Resolve outcome from historical_box_scores
  4. Compute PnL with actual juice priced

Sweep top-N across {5, 10, 15, 20, 25} to see how performance changes
with bet count per night.

Outputs at runs/run_top_n_ev_backtest/:
  - bet_ledger.csv (every simulated bet + outcome)
  - by_top_n_summary.csv
  - per_strategy_breakdown.csv
  - TOP_N_RESULTS.md
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RECS_DIR = Path("D:/sports_lines/data/live_recommendations")
BOX_PATH = Path("D:/NBA Projections/data/parquet/historical_box_scores.parquet")
OUT_DIR = Path("D:/NBA Projections/runs/run_top_n_ev_backtest")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BET_UNIT = 100
BREAKEVEN = 110 / 210


def american_payout(price):
    if pd.isna(price): return 100 / 110
    if price > 0: return price / 100
    return 100 / -price


def parse_min(m):
    if pd.isna(m): return 0.0
    if isinstance(m, (int, float)): return float(m)
    try:
        parts = str(m).split(":")
        return float(parts[0]) + (float(parts[1]) / 60 if len(parts) > 1 else 0)
    except (ValueError, TypeError):
        return 0.0


def load_recommendations() -> pd.DataFrame:
    """Pull all recommendations, take the OPEN snapshot per market (live deploy choice)."""
    files = sorted(RECS_DIR.glob("*_recommendations.parquet"))
    if not files:
        raise FileNotFoundError(f"no recommendation files in {RECS_DIR}")
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    # Keep one snapshot per (game_date, player, stat, side): prefer 'open' snapshot
    df = df[df["snapshot_type"] == "open"]
    df = df.drop_duplicates(
        subset=["game_date_et", "nba_api_id", "stat", "side"], keep="first")
    df["game_date"] = pd.to_datetime(df["game_date_et"])
    return df


def load_box_actuals() -> pd.DataFrame:
    """Pull box scores from historical + playoff staging tables."""
    cols = ["nba_api_id", "game_id", "game_date", "season", "season_type",
            "minutes", "PTS", "REB", "AST", "FG3M"]
    frames = []
    try:
        box = pd.read_parquet(BOX_PATH, columns=cols)
        frames.append(box)
    except Exception as e:
        print(f"  WARN historical box: {e}")

    # Playoff staging tables — match game_date via schedule + playoff manifests
    PLAYOFFS_R1 = Path("D:/NBA Projections/data/parquet/playoffs/round1")
    PLAYOFFS_EXTRA = Path("D:/NBA Projections/data/parquet/playoffs/extra_rounds")
    sched_lookup = {}
    # Base lookup from main schedule
    schedule = pd.read_parquet("D:/NBA Projections/data/parquet/schedule.parquet")
    schedule.columns = [c.lower() for c in schedule.columns]
    gid_col = "game_id" if "game_id" in schedule.columns else "gameid"
    date_col = "game_date" if "game_date" in schedule.columns else "gamedate"
    sched_lookup.update(dict(zip(schedule[gid_col].astype(str),
                                   pd.to_datetime(schedule[date_col]))))
    # Augment with 25-26 playoff dates from nba_api cache
    pdate_cache = Path("D:/NBA Projections/data/parquet/playoffs/_gameid_to_date_25_26.parquet")
    if pdate_cache.exists():
        pd_df = pd.read_parquet(pdate_cache)
        sched_lookup.update(dict(zip(pd_df["game_id"].astype(str),
                                       pd.to_datetime(pd_df["game_date"]))))
    # Also augment with R1 manifest (has dates back to 2010)
    r1_man = Path("D:/NBA Projections/data/parquet/playoffs/round1/_manifest.parquet")
    if r1_man.exists():
        m = pd.read_parquet(r1_man)
        sched_lookup.update(dict(zip(m["game_id"].astype(str),
                                       pd.to_datetime(m["game_date"]))))

    for src in [PLAYOFFS_R1, PLAYOFFS_EXTRA]:
        for fn in ["traditional_t0.parquet", "traditional_t1.parquet"]:
            p = src / fn
            if not p.exists(): continue
            df = pd.read_parquet(p)
            if "personId" not in df.columns: continue
            df = df.dropna(subset=["personId"])
            df["nba_api_id"] = df["personId"].astype(int)
            # Map gameId → game_date via schedule
            df["game_date"] = df["gameId"].astype(str).map(sched_lookup)
            stat_map = {"points": "PTS", "reboundsTotal": "REB",
                         "assists": "AST", "threePointersMade": "FG3M"}
            for src_col, dest_col in stat_map.items():
                if src_col in df.columns:
                    df[dest_col] = df[src_col]
            keep = [c for c in cols if c in df.columns]
            # Dedupe column names in case of repeat (defensive)
            df_sub = df[keep].loc[:, ~df[keep].columns.duplicated()]
            frames.append(df_sub)

    if not frames:
        return pd.DataFrame()
    box = pd.concat(frames, ignore_index=True)
    box = box[pd.notna(box["nba_api_id"])].copy()
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    box["game_date"] = pd.to_datetime(box["game_date"])
    box["min_played"] = box["minutes"].apply(parse_min)
    return box


# stat → list of box-score columns to sum for actual
STAT_COMP = {
    "PTS": ["PTS"],
    "REB": ["REB"],
    "AST": ["AST"],
    "FG3M": ["FG3M"],
    "PA": ["PTS", "AST"],
    "PR": ["PTS", "REB"],
    "RA": ["REB", "AST"],
    "PRA": ["PTS", "REB", "AST"],
}


def resolve_outcome(rec_row, actual_map) -> tuple | None:
    """Returns (result, pnl) where result ∈ {1, 0, -1}, pnl in $ at flat $100."""
    pid = int(rec_row["nba_api_id"])
    d = pd.Timestamp(rec_row["game_date_et"])
    stat = rec_row["stat"]
    if stat not in STAT_COMP:
        return None
    comp = STAT_COMP[stat]
    actuals = actual_map.get((pid, d.date()))
    if actuals is None:
        return None
    # Filter out DNPs (0 min played = player didn't play, bet was a push or loss)
    if actuals.get("min_played", 0) < 1:
        # Player didn't play. Treat as loss (DK voids; conservative)
        # In practice DK voids these — model as 0 PnL (no win, no loss).
        return (0, 0.0)
    actual = sum(actuals.get(c, 0) for c in comp)
    line = rec_row["line"]
    side = rec_row["side"]
    juice = rec_row["juice_american"]
    if actual == line:
        return (0, 0.0)  # push
    over = actual > line
    won = (side == "over" and over) or (side == "under" and not over)
    if won:
        return (1, BET_UNIT * american_payout(juice))
    return (-1, -BET_UNIT)


def main():
    print("=" * 70)
    print("Top-N EV nightly simulator — OOS playoff window")
    print("=" * 70)

    print("\n[1/4] Loading data...")
    recs = load_recommendations()
    box = load_box_actuals()
    print(f"  recs: {len(recs):,}  ({recs['game_date_et'].nunique()} dates)")
    print(f"  box rows: {len(box):,}")
    print(f"  date range: {recs['game_date_et'].min()} → {recs['game_date_et'].max()}")

    # Build (pid, date) → {stat actuals} lookup
    print("\n[2/4] Indexing actuals...")
    actual_map = {}
    for _, r in box.iterrows():
        actual_map[(int(r["nba_api_id"]), r["game_date"].date())] = {
            "PTS": r["PTS"], "REB": r["REB"], "AST": r["AST"],
            "FG3M": r["FG3M"], "min_played": r["min_played"],
        }

    print("\n[3/4] Resolving every recommendation...")
    resolved_rows = []
    for _, r in recs.iterrows():
        result = resolve_outcome(r, actual_map)
        if result is None:
            continue
        resolved_rows.append({
            "game_date": r["game_date_et"],
            "nba_api_id": int(r["nba_api_id"]),
            "player_name": r["player_name"],
            "event_name": r["event_name"],
            "stat": r["stat"], "side": r["side"],
            "line": r["line"], "juice": r["juice_american"],
            "your_prob": r["your_prob"],
            "implied_prob": r["implied_prob_over"],
            "edge": r["edge"],
            "ev_per_dollar": r["ev_per_dollar"],
            "kelly_capped": r["kelly_fraction_capped"],
            "baseline_source": r["baseline_source"],
            "result": result[0],
            "pnl": result[1],
        })

    resolved = pd.DataFrame(resolved_rows)
    print(f"  resolved {len(resolved)} of {len(recs)} recs "
          f"({100*len(resolved)/len(recs):.1f}%)")
    if not len(resolved):
        return
    resolved.to_csv(OUT_DIR / "all_recs_resolved.csv", index=False)

    # Per-date stats
    n_dates = resolved["game_date"].nunique()
    print(f"\n  Per date: avg {len(resolved)/n_dates:.0f} resolved recs/night")

    # ── Top-N sweep ─────────────────────────────────────────────────────
    print("\n[4/4] Sweeping top-N per night...")
    sweep_rows = []
    per_n_ledgers = {}
    for N in [5, 10, 15, 20, 25, 50]:
        nightly = []
        for d, grp in resolved.groupby("game_date"):
            top = grp.sort_values("ev_per_dollar", ascending=False).head(N)
            nightly.append(top)
        topn = pd.concat(nightly, ignore_index=True) if nightly else pd.DataFrame()
        per_n_ledgers[N] = topn

        n = len(topn)
        nw = int((topn["result"] == 1).sum())
        nl = int((topn["result"] == -1).sum())
        nd = nw + nl
        wr = nw / nd if nd > 0 else 0
        pnl = topn["pnl"].sum()
        roi = pnl / (n * BET_UNIT) if n > 0 else 0
        p_val = (stats.binomtest(nw, nd, p=BREAKEVEN, alternative="greater").pvalue
                 if nd > 0 else 1.0)
        sweep_rows.append({
            "top_N": N, "n_bets": n, "wins": nw, "losses": nl,
            "WR": round(wr, 4), "ROI": round(roi, 4),
            "PnL": round(pnl, 2), "p_value": round(p_val, 4),
        })
        print(f"  top {N:>2}/night: n={n:>4}  WR={wr*100:>5.1f}%  "
              f"ROI={roi*100:>+6.2f}%  PnL=${pnl:>+9,.2f}  p={p_val:.4f}")

    sweep_df = pd.DataFrame(sweep_rows)
    sweep_df.to_csv(OUT_DIR / "by_top_n_summary.csv", index=False)
    # Save top-15 ledger as primary
    if 15 in per_n_ledgers:
        per_n_ledgers[15].to_csv(OUT_DIR / "top_15_ledger.csv", index=False)

    # ── Per-strategy (by stat) on top-15 ─────────────────────────────────
    print("\n── Top-15 per stat ──")
    top15 = per_n_ledgers.get(15, pd.DataFrame())
    per_stat_rows = []
    if not top15.empty:
        for stat, g in top15.groupby("stat"):
            n = len(g)
            nw = int((g["result"] == 1).sum())
            nl = int((g["result"] == -1).sum())
            nd = nw + nl
            if nd == 0: continue
            wr = nw / nd
            pnl = g["pnl"].sum()
            roi = pnl / (n * BET_UNIT)
            per_stat_rows.append({
                "stat": stat, "n": n, "wins": nw, "losses": nl,
                "WR": round(wr, 4), "ROI": round(roi, 4),
                "PnL": round(pnl, 2),
            })
            print(f"  {stat:<6} n={n:>3}  WR={wr*100:>5.1f}%  "
                  f"ROI={roi*100:>+6.2f}%  PnL=${pnl:>+8,.2f}")
        pd.DataFrame(per_stat_rows).to_csv(OUT_DIR / "top_15_per_stat.csv", index=False)

    # ── Per-baseline-source on top-15 ────────────────────────────────────
    print("\n── Top-15 per baseline_source ──")
    if not top15.empty:
        for src, g in top15.groupby("baseline_source"):
            n = len(g)
            nw = int((g["result"] == 1).sum())
            nl = int((g["result"] == -1).sum())
            nd = nw + nl
            if nd == 0: continue
            wr = nw / nd
            pnl = g["pnl"].sum()
            roi = pnl / (n * BET_UNIT)
            print(f"  {src:<25} n={n:>3}  WR={wr*100:>5.1f}%  "
                  f"ROI={roi*100:>+6.2f}%  PnL=${pnl:>+8,.2f}")

    # ── Kelly-sized version of top-15 ───────────────────────────────────
    print("\n── Top-15 sized by kelly_capped (Kelly sizing, not flat) ──")
    if not top15.empty:
        # PnL when bet size = kelly_capped (already a fraction, multiply by some bankroll)
        BANKROLL = 1000  # nominal
        sized = top15.copy()
        sized["bet_size"] = sized["kelly_capped"] * BANKROLL
        sized["pnl_kelly"] = np.where(
            sized["result"] == 1,
            sized["bet_size"] * sized["juice"].apply(american_payout),
            np.where(sized["result"] == -1, -sized["bet_size"], 0)
        )
        kelly_total = sized["pnl_kelly"].sum()
        kelly_risk = sized["bet_size"].sum()
        kelly_roi = kelly_total / kelly_risk if kelly_risk > 0 else 0
        print(f"  Total Kelly bets sized: {len(sized)}")
        print(f"  Total risked: ${kelly_risk:,.2f} (vs ${len(sized)*100:,} at flat $100)")
        print(f"  PnL: ${kelly_total:+,.2f}")
        print(f"  ROI on risked: {kelly_roi*100:+.2f}%")

    # ── Per-night equity curve on top-15 flat ─────────────────────────
    print("\n── Per-night PnL (top-15 flat $100) ──")
    if not top15.empty:
        nightly_pnl = top15.groupby("game_date")["pnl"].agg(["sum", "count"]).reset_index()
        nightly_pnl.columns = ["game_date", "pnl_night", "n_bets"]
        nightly_pnl["cum_pnl"] = nightly_pnl["pnl_night"].cumsum()
        nightly_pnl.to_csv(OUT_DIR / "nightly_pnl.csv", index=False)
        for _, r in nightly_pnl.iterrows():
            print(f"  {r['game_date']}  n={int(r['n_bets']):>2}  "
                  f"PnL=${r['pnl_night']:>+8.2f}  cum=${r['cum_pnl']:>+9.2f}")

    # Markdown writeup
    md = OUT_DIR / "TOP_N_RESULTS.md"
    with open(md, "w", encoding="utf-8") as f:
        f.write("# Top-N EV Nightly OOS Backtest\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n")
        f.write(f"**Source:** D:/sports_lines/data/live_recommendations/ (OOS — system outputs, not training input)\n\n")
        f.write(f"**Window:** {resolved['game_date'].min()} → {resolved['game_date'].max()}  ({n_dates} dates)\n\n")
        f.write(f"**Resolved recs:** {len(resolved):,} of {len(recs):,} ({100*len(resolved)/len(recs):.1f}%)\n\n")
        f.write("## Top-N sweep\n\n")
        f.write(sweep_df.to_markdown(index=False) + "\n\n")
        if per_stat_rows:
            f.write("## Top-15 by stat\n\n")
            f.write(pd.DataFrame(per_stat_rows).to_markdown(index=False) + "\n")
    print(f"\n  → {md}")


if __name__ == "__main__":
    main()
