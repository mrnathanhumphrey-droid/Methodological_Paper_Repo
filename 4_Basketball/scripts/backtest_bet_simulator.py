"""Bet simulator: convert game residuals into hypothetical bets, resolve, hunt
for structural mispricing.

For each game:
  - Total bet: if abs(proj_total - close_total) >= EDGE_THRESHOLD_TOTAL,
    bet OVER (if proj > close) or UNDER (if proj < close).
  - Spread bet: same logic on proj_margin_home vs close_margin_home_implied.

Win/loss:
  - Total: actual_total > close_total → OVER wins.
  - Spread: actual_margin_home > close_margin_home_implied → HOME covers.

ROI assumes flat -110 vigorish (bet $110 to win $100, 52.38% breakeven).

Inputs: game_residuals.csv from v1 (perfect-foresight) AND v2 (live-formula).
Outputs: per-bet ledger, win-rate by edge tier, structural stratifications.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("D:/NBA Projections")
V1_RESID = REPO / "runs" / "run_nba_game_totals_22_26" / "game_residuals.csv"
V2_RESID = REPO / "runs" / "run_nba_game_totals_22_26" / "v2_live_formula" / "game_residuals.csv"
V3_RESID = REPO / "runs" / "run_nba_game_totals_22_26" / "v3_mock_runner" / "game_residuals.csv"
OUT_DIR = REPO / "runs" / "run_nba_game_totals_22_26" / "bet_simulation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIG_PRICE = -110  # standard juice
BREAKEVEN_RATE = 110 / 210  # 0.5238
BET_UNIT = 100  # $100 to win $90.91


def american_to_payout(price: int) -> float:
    """Net profit on $1 wagered."""
    if price > 0:
        return price / 100
    return 100 / -price


PAYOUT_PER_UNIT = american_to_payout(VIG_PRICE)  # 0.9091 net per $1


def simulate_total_bets(df: pd.DataFrame, edge: float) -> pd.DataFrame:
    """For each game, place a TOTAL bet if |proj - close| >= edge.
    Numpy-vectorized to avoid pandas boolean-index assignment gotchas."""
    skew = (df["proj_total"] - df["close_total"]).to_numpy()
    actual_over = (df["actual_total"] > df["close_total"]).to_numpy()
    push = (df["actual_total"] == df["close_total"]).to_numpy()

    side = np.where(skew >= edge, "OVER",
            np.where(skew <= -edge, "UNDER", "NO_BET"))
    bet = side != "NO_BET"
    won = np.where(side == "OVER", actual_over,
            np.where(side == "UNDER", ~actual_over, False))

    pnl = np.zeros(len(df))
    pnl[bet & won & ~push] = BET_UNIT * PAYOUT_PER_UNIT
    pnl[bet & ~won & ~push] = -BET_UNIT
    return pd.DataFrame({
        "side_total": side,
        "edge_total": skew,
        "won_total": won,
        "pnl_total": pnl,
        "bet_total": bet,
    })


def simulate_spread_bets(df: pd.DataFrame, edge: float) -> pd.DataFrame:
    """For each game, place a SPREAD bet if |proj_margin - close_margin| >= edge."""
    skew = (df["proj_margin_home"] - df["close_margin_home_implied"]).to_numpy()
    home_covers = (df["actual_margin_home"] > df["close_margin_home_implied"]).to_numpy()
    push = (df["actual_margin_home"] == df["close_margin_home_implied"]).to_numpy()

    side = np.where(skew >= edge, "HOME",
            np.where(skew <= -edge, "AWAY", "NO_BET"))
    bet = side != "NO_BET"
    won = np.where(side == "HOME", home_covers,
            np.where(side == "AWAY", ~home_covers, False))

    pnl = np.zeros(len(df))
    pnl[bet & won & ~push] = BET_UNIT * PAYOUT_PER_UNIT
    pnl[bet & ~won & ~push] = -BET_UNIT
    return pd.DataFrame({
        "side_spread": side,
        "edge_spread": skew,
        "won_spread": won,
        "pnl_spread": pnl,
        "bet_spread": bet,
    })


def summarize_bets(bets: pd.DataFrame, label: str, kind: str) -> dict:
    """kind: 'total' or 'spread'."""
    bet_col = f"bet_{kind}"
    won_col = f"won_{kind}"
    pnl_col = f"pnl_{kind}"
    placed = bets[bets[bet_col]]
    n = len(placed)
    if n == 0:
        return {"label": label, "kind": kind, "n_bets": 0}
    wr = float(placed[won_col].mean())
    roi = float(placed[pnl_col].sum() / (n * BET_UNIT))
    pnl = float(placed[pnl_col].sum())
    # Confidence: 95% binomial CI on win rate
    p = wr
    se = (p * (1 - p) / n) ** 0.5
    ci_lo = max(0, p - 1.96 * se)
    ci_hi = min(1, p + 1.96 * se)
    # Edge over breakeven (52.38%)
    edge_over_be = (wr - BREAKEVEN_RATE) * 100
    return {
        "label": label, "kind": kind, "n_bets": n,
        "win_rate": wr, "ci_lo": ci_lo, "ci_hi": ci_hi,
        "edge_over_breakeven_pp": edge_over_be,
        "roi": roi, "pnl_$": pnl,
    }


def run_simulation(df: pd.DataFrame, version: str,
                   edge_total: float = 3.0,
                   edge_spread: float = 2.0) -> dict:
    print(f"\n{'='*70}")
    print(f"BET SIMULATION — {version} (edge_total={edge_total}, edge_spread={edge_spread})")
    print(f"{'='*70}")

    tot_bets = simulate_total_bets(df, edge_total)
    spr_bets = simulate_spread_bets(df, edge_spread)
    ledger = pd.concat([df.reset_index(drop=True),
                         tot_bets.reset_index(drop=True),
                         spr_bets.reset_index(drop=True)], axis=1)
    ledger.to_csv(OUT_DIR / f"{version}_bet_ledger_edge_t{edge_total}_s{edge_spread}.csv",
                   index=False)

    rows = []
    # Overall
    rows.append(summarize_bets(ledger, "ALL", "total"))
    rows.append(summarize_bets(ledger, "ALL", "spread"))
    # By season
    for season in sorted(ledger["season"].dropna().unique()):
        sub = ledger[ledger["season"] == season]
        rows.append(summarize_bets(sub, season, "total"))
        rows.append(summarize_bets(sub, season, "spread"))

    # Edge tier stratifications (for totals)
    ledger["edge_total_abs"] = ledger["edge_total"].abs()
    edge_bins = [edge_total, 5, 8, 12, 100]
    edge_labels = [f"{edge_bins[i]}-{edge_bins[i+1]}" for i in range(len(edge_bins)-1)]
    ledger["edge_total_tier"] = pd.cut(ledger["edge_total_abs"], bins=edge_bins,
                                        labels=edge_labels, right=False)
    for tier in edge_labels:
        sub = ledger[ledger["edge_total_tier"] == tier]
        rows.append(summarize_bets(sub, f"edge_t_{tier}", "total"))

    ledger["edge_spread_abs"] = ledger["edge_spread"].abs()
    edge_bins_s = [edge_spread, 4, 6, 10, 100]
    edge_labels_s = [f"{edge_bins_s[i]}-{edge_bins_s[i+1]}" for i in range(len(edge_bins_s)-1)]
    ledger["edge_spread_tier"] = pd.cut(ledger["edge_spread_abs"], bins=edge_bins_s,
                                         labels=edge_labels_s, right=False)
    for tier in edge_labels_s:
        sub = ledger[ledger["edge_spread_tier"] == tier]
        rows.append(summarize_bets(sub, f"edge_s_{tier}", "spread"))

    # Spread-tier stratifications (close vs blowout)
    if "close_spread_home" in ledger.columns:
        ledger["spread_size"] = pd.cut(ledger["close_spread_home"].abs(),
                                        bins=[-0.01, 3, 7, 12, 100],
                                        labels=["pickem", "short", "med", "long"])
        for tier in ["pickem", "short", "med", "long"]:
            sub = ledger[ledger["spread_size"] == tier]
            rows.append(summarize_bets(sub, f"spread_size_{tier}", "total"))
            rows.append(summarize_bets(sub, f"spread_size_{tier}", "spread"))

    # Total-tier stratifications (high-scoring vs low-scoring environments)
    if "close_total" in ledger.columns:
        ledger["total_tier"] = pd.cut(ledger["close_total"],
                                       bins=[150, 215, 225, 235, 290],
                                       labels=["low", "mid_lo", "mid_hi", "high"])
        for tier in ["low", "mid_lo", "mid_hi", "high"]:
            sub = ledger[ledger["total_tier"] == tier]
            rows.append(summarize_bets(sub, f"total_tier_{tier}", "total"))

    sm = pd.DataFrame(rows)
    sm.to_csv(OUT_DIR / f"{version}_summary_edge_t{edge_total}_s{edge_spread}.csv",
               index=False)

    # ── Print headline ────────────────────────────────────────────────
    def show(rows_subset, header):
        print(f"\n{header}")
        print(f"  {'label':<22} {'kind':<7} {'n':>4} {'WR':>6} {'CI95':>14}  "
              f"{'pp_over_BE':>10} {'ROI%':>7}")
        for r in rows_subset:
            if r["n_bets"] == 0:
                continue
            print(f"  {r['label']:<22} {r['kind']:<7} {r['n_bets']:>4} "
                  f"{r['win_rate']*100:>5.1f}% "
                  f"[{r['ci_lo']*100:>4.1f}-{r['ci_hi']*100:>4.1f}]  "
                  f"{r['edge_over_breakeven_pp']:>+9.2f}  "
                  f"{r['roi']*100:>+6.2f}%")

    show([r for r in rows if r["label"] == "ALL"], "── Overall ──")
    show([r for r in rows if r["label"] in [
        "2022-23", "2023-24", "2024-25", "2025-26"
    ]], "── By season ──")
    show([r for r in rows if r["label"].startswith("edge_")],
         "── By edge tier ──")
    show([r for r in rows if r["label"].startswith("spread_size")],
         "── By Vegas spread size ──")
    show([r for r in rows if r["label"].startswith("total_tier")],
         "── By Vegas total tier ──")

    return {"ledger": ledger, "summary": sm, "n_total_bets": int(tot_bets["bet_total"].sum()),
            "n_spread_bets": int(spr_bets["bet_spread"].sum())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edge-total", type=float, default=3.0,
                    help="min |proj - close| in points to place a TOTAL bet")
    ap.add_argument("--edge-spread", type=float, default=2.0,
                    help="min |proj_margin - close_margin| in points to place a SPREAD bet")
    ap.add_argument("--version", choices=["v1", "v2", "v3", "all"], default="all")
    args = ap.parse_args()

    print(f"Vig: {VIG_PRICE} → breakeven {BREAKEVEN_RATE*100:.2f}% win rate")
    print(f"Bet unit: ${BET_UNIT}  net payout per win: ${BET_UNIT * PAYOUT_PER_UNIT:.2f}")

    if args.version in ("v1", "all"):
        if V1_RESID.exists():
            v1 = pd.read_csv(V1_RESID)
            run_simulation(v1, "v1_static_mpg",
                           edge_total=args.edge_total, edge_spread=args.edge_spread)
        else:
            print(f"  WARN: {V1_RESID} not found; skipping v1")
    if args.version in ("v2", "all"):
        if V2_RESID.exists():
            v2 = pd.read_csv(V2_RESID)
            run_simulation(v2, "v2_live_formula",
                           edge_total=args.edge_total, edge_spread=args.edge_spread)
        else:
            print(f"  WARN: {V2_RESID} not found; skipping v2")
    if args.version in ("v3", "all"):
        if V3_RESID.exists():
            v3 = pd.read_csv(V3_RESID)
            run_simulation(v3, "v3_mock_runner",
                           edge_total=args.edge_total, edge_spread=args.edge_spread)
        else:
            print(f"  WARN: {V3_RESID} not found; skipping v3")


if __name__ == "__main__":
    main()
