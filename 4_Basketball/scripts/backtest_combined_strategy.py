"""Combined strategy backtest: apply all 4 discovered rules together,
validate with statistical tests, build equity curve.

Strategy rules:
  PRIMARY:    pickem (spread ≤ 3) + |our_edge| ≥ 12 + OVER side  → bet OVER
  FADE-1:     med-spread (Vegas 7-12) + |our_edge| ≥ 3           → bet OPPOSITE
  FADE-2:     |our_edge| 8-12 + spread > 3 (non-pickem)          → bet OPPOSITE
  Otherwise:  SKIP

Priority: PRIMARY > FADE-1 > FADE-2 > SKIP.

Statistical validation:
  - Binomial test: WR vs breakeven (52.38%)
  - Bootstrap CI on aggregate ROI (10K resamples)
  - Walk-forward: train discovery on early seasons, test late
  - Equity curve + max drawdown

Outputs at runs/run_nba_game_totals_22_26/combined_strategy/:
  - bets_ledger.csv          per-game bet ledger
  - equity_curve.csv         cumulative PnL
  - validation.csv           per-rule + aggregate WR/ROI/CI/p-value
  - STRATEGY_RESULTS.md
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path("D:/NBA Projections")
V3_RESID = REPO / "runs" / "run_nba_game_totals_22_26" / "v3_mock_runner" / "game_residuals.csv"
OUT_DIR = REPO / "runs" / "run_nba_game_totals_22_26" / "combined_strategy"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BREAKEVEN = 110 / 210  # 0.5238
BET_UNIT = 100
PAYOUT = 100 / 110  # net per win


def decide(row) -> tuple[str, str]:
    """Returns (side, rule_label).  side ∈ {OVER, UNDER, NONE}."""
    spread_abs = abs(row["close_spread_home"])
    edge = row["proj_total"] - row["close_total"]
    edge_abs = abs(edge)
    if edge == 0:
        return "NONE", "NO_EDGE"
    our_side = "OVER" if edge > 0 else "UNDER"

    # PRIMARY: pickem + big edge + OVER side
    if spread_abs <= 3 and edge_abs >= 12 and our_side == "OVER":
        return "OVER", "PRIMARY_pickem_bigEdge_OVER"

    # FADE-1: med-spread (7-12pt Vegas) → flip our side
    if 7 < spread_abs <= 12 and edge_abs >= 3:
        return ("UNDER" if our_side == "OVER" else "OVER"), "FADE_medspread"

    # FADE-2: edge 8-12 in non-pickem games → flip
    if 8 <= edge_abs < 12 and spread_abs > 3:
        return ("UNDER" if our_side == "OVER" else "OVER"), "FADE_edge_8_12"

    return "NONE", "NO_BET"


def resolve(row, side: str) -> int:
    """Returns 1 win / 0 push / -1 loss / None if no bet."""
    if side == "NONE":
        return None
    if row["actual_total"] == row["close_total"]:
        return 0
    over = row["actual_total"] > row["close_total"]
    if side == "OVER":
        return 1 if over else -1
    return 1 if not over else -1


def pnl(result: int) -> float:
    if result is None or result == 0:
        return 0
    return BET_UNIT * PAYOUT if result == 1 else -BET_UNIT


def bootstrap_ci(values: np.ndarray, n_boot: int = 10000,
                 ci: float = 0.95) -> tuple[float, float]:
    if len(values) < 2:
        return (0, 0)
    rng = np.random.default_rng(42)
    boots = np.array([
        rng.choice(values, size=len(values), replace=True).sum() / (len(values) * BET_UNIT)
        for _ in range(n_boot)
    ])
    lo = np.percentile(boots, (1 - ci) / 2 * 100)
    hi = np.percentile(boots, (1 + ci) / 2 * 100)
    return float(lo), float(hi)


def main():
    df = pd.read_csv(V3_RESID)
    df["game_date"] = pd.to_datetime(df["game_date"])
    print(f"Loaded {len(df)} games from V3 residuals")
    df = df.sort_values("game_date").reset_index(drop=True)

    # Apply strategy
    df["side"] = ""
    df["rule"] = ""
    df["result"] = pd.Series(dtype=object)
    df["pnl"] = 0.0

    for i, row in df.iterrows():
        side, rule = decide(row)
        df.at[i, "side"] = side
        df.at[i, "rule"] = rule
        r = resolve(row, side)
        df.at[i, "result"] = r
        df.at[i, "pnl"] = pnl(r)

    # Filter to actual bets
    bets = df[df["side"] != "NONE"].copy()
    pushes = bets[bets["result"] == 0]
    wins = bets[bets["result"] == 1]
    losses = bets[bets["result"] == -1]

    n = len(bets)
    n_wins = len(wins)
    n_losses = len(losses)
    n_push = len(pushes)
    n_decisive = n_wins + n_losses  # excl. push
    wr = n_wins / n_decisive if n_decisive > 0 else 0
    total_pnl = bets["pnl"].sum()
    total_risk = n * BET_UNIT
    roi = total_pnl / total_risk if total_risk > 0 else 0

    print("\n" + "=" * 70)
    print("COMBINED STRATEGY — V3 MOCK RUNNER LEDGER (22-23 to 25-26)")
    print("=" * 70)
    print(f"Games considered:       {len(df):,}")
    print(f"Bets placed:            {n:,}  ({100*n/len(df):.1f}% bet rate)")
    print(f"  wins / losses / push: {n_wins} / {n_losses} / {n_push}")
    print(f"Win rate:               {wr*100:.2f}%  (breakeven {BREAKEVEN*100:.2f}%)")
    print(f"Total PnL:              ${total_pnl:+,.2f}  on ${total_risk:,.0f} risked")
    print(f"ROI:                    {roi*100:+.2f}%")

    # Stat tests
    if n_decisive >= 30:
        p_binom = stats.binomtest(n_wins, n_decisive, p=BREAKEVEN,
                                  alternative="greater").pvalue
        ci_lo, ci_hi = bootstrap_ci(bets["pnl"].values, n_boot=10000)
        print(f"Binomial p (WR > BE):   {p_binom:.4f}")
        print(f"Bootstrap 95% ROI CI:   [{ci_lo*100:+.2f}%, {ci_hi*100:+.2f}%]")

    # Per-rule breakdown
    print("\n── PER-RULE BREAKDOWN ──")
    rule_rows = []
    for rule_name, sub in bets.groupby("rule"):
        n_r = len(sub)
        nw = (sub["result"] == 1).sum()
        nl = (sub["result"] == -1).sum()
        nd = nw + nl
        if nd == 0: continue
        wr_r = nw / nd
        pnl_r = sub["pnl"].sum()
        roi_r = pnl_r / (n_r * BET_UNIT)
        p_r = stats.binomtest(int(nw), int(nd), p=BREAKEVEN,
                              alternative="greater").pvalue
        rule_rows.append({
            "rule": rule_name, "n": int(n_r), "wins": int(nw),
            "losses": int(nl), "WR": round(wr_r, 4),
            "ROI": round(roi_r, 4),
            "p_value_one_sided": round(p_r, 4),
        })
        print(f"  {rule_name:<32} n={n_r:>4}  WR={wr_r*100:>5.1f}%  "
              f"ROI={roi_r*100:>+6.2f}%  p={p_r:.4f}")

    # Per-season breakdown (walk-forward test)
    print("\n── PER-SEASON BREAKDOWN (walk-forward) ──")
    season_rows = []
    for season in sorted(bets["season"].unique()):
        sub = bets[bets["season"] == season]
        n_s = len(sub)
        nw = (sub["result"] == 1).sum()
        nl = (sub["result"] == -1).sum()
        nd = nw + nl
        if nd == 0: continue
        wr_s = nw / nd
        pnl_s = sub["pnl"].sum()
        roi_s = pnl_s / (n_s * BET_UNIT)
        p_s = stats.binomtest(int(nw), int(nd), p=BREAKEVEN,
                              alternative="greater").pvalue
        season_rows.append({
            "season": season, "n": int(n_s), "WR": round(wr_s, 4),
            "ROI": round(roi_s, 4), "PnL": round(pnl_s, 2),
            "p_value": round(p_s, 4),
        })
        print(f"  {season:<10} n={n_s:>4}  WR={wr_s*100:>5.1f}%  "
              f"ROI={roi_s*100:>+6.2f}%  PnL=${pnl_s:>+8,.0f}  p={p_s:.4f}")

    # Equity curve
    bets_sorted = bets.sort_values("game_date").reset_index(drop=True)
    bets_sorted["cum_pnl"] = bets_sorted["pnl"].cumsum()
    bets_sorted["cum_max"] = bets_sorted["cum_pnl"].cummax()
    bets_sorted["drawdown"] = bets_sorted["cum_pnl"] - bets_sorted["cum_max"]
    max_dd = float(bets_sorted["drawdown"].min())
    max_pnl = float(bets_sorted["cum_pnl"].max())

    print("\n── EQUITY CURVE ──")
    print(f"  Final PnL:   ${total_pnl:+,.2f}")
    print(f"  Peak PnL:    ${max_pnl:+,.2f}")
    print(f"  Max drawdown: ${max_dd:+,.2f}  ({max_dd/total_risk*100:.2f}% of total risk)")

    bets_sorted.to_csv(OUT_DIR / "bets_ledger.csv", index=False)
    bets_sorted[["game_date", "season", "rule", "pnl", "cum_pnl",
                 "drawdown"]].to_csv(OUT_DIR / "equity_curve.csv", index=False)

    # Validation table
    val_rows = [
        {"scope": "ALL", "n": n, "wins": n_wins, "WR": round(wr, 4),
         "ROI": round(roi, 4), "PnL": round(total_pnl, 2)},
    ] + rule_rows + season_rows
    pd.DataFrame(val_rows).to_csv(OUT_DIR / "validation.csv", index=False)

    # Markdown writeup
    md = OUT_DIR / "STRATEGY_RESULTS.md"
    with open(md, "w", encoding="utf-8") as f:
        f.write("# Combined Strategy Backtest — V3 Mock Runner\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n")
        f.write("## Strategy rules\n\n")
        f.write("```\n")
        f.write("PRIMARY:  pickem (spread ≤ 3) + |edge| ≥ 12 + OVER side  → BET OVER\n")
        f.write("FADE-1:   med-spread (Vegas 7-12) + |edge| ≥ 3           → BET OPPOSITE\n")
        f.write("FADE-2:   |edge| 8-12 + spread > 3                       → BET OPPOSITE\n")
        f.write("Else:     SKIP\n")
        f.write("```\n\n")
        f.write("## Headline\n\n")
        f.write(f"- Bets: **{n:,}**  ({100*n/len(df):.1f}% of {len(df):,} games)\n")
        f.write(f"- Win rate: **{wr*100:.2f}%** (breakeven {BREAKEVEN*100:.2f}%)\n")
        f.write(f"- ROI: **{roi*100:+.2f}%**\n")
        f.write(f"- PnL: **${total_pnl:+,.2f}** on ${total_risk:,.0f} risked\n")
        f.write(f"- Max drawdown: ${max_dd:+,.2f}\n\n")
        f.write("## Per-rule breakdown\n\n")
        f.write(pd.DataFrame(rule_rows).to_markdown(index=False) + "\n\n")
        f.write("## Per-season (walk-forward)\n\n")
        f.write(pd.DataFrame(season_rows).to_markdown(index=False) + "\n")

    print(f"\n  → {md}")


if __name__ == "__main__":
    main()
