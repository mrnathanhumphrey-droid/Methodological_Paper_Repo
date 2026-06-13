"""Mine V3 bet ledger for structural patterns.

Inputs: bet_simulation/v3_mock_runner_bet_ledger_edge_t3.0_s2.0.csv (the
deployable model's hypothetical bets + outcomes).

Analyses:
  A. Side breakdown — OVER vs UNDER, HOME vs AWAY win rates
  B. Season stability — do signals repeat across 22-23, 23-24, 24-25?
  C. Compound stratifications — pickem AND low-total AND edge 5-8?
  D. Fade signals — strata where WE lose hardest (bet opposite?)
  E. Day-of-week, b2b, rest effects where derivable
  F. Bias direction — when we under-project, do we miss OVERs?

Outputs to runs/run_nba_game_totals_22_26/pattern_mining/:
  - side_breakdown.csv
  - season_stability.csv
  - compound_strata.csv
  - fade_candidates.csv
  - PATTERN_FINDINGS.md
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("D:/NBA Projections")
LEDGER = REPO / "runs" / "run_nba_game_totals_22_26" / "bet_simulation" / "v3_mock_runner_bet_ledger_edge_t3.0_s2.0.csv"
OUT_DIR = REPO / "runs" / "run_nba_game_totals_22_26" / "pattern_mining"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BREAKEVEN = 110 / 210  # 0.5238
BET_UNIT = 100
PAYOUT = 100 / 110  # 0.9091


def wr_ci(wins: int, n: int) -> tuple[float, float, float]:
    if n == 0: return (0, 0, 0)
    p = wins / n
    se = (p * (1 - p) / n) ** 0.5
    return p, max(0, p - 1.96 * se), min(1, p + 1.96 * se)


def roi(wins: int, n: int) -> float:
    if n == 0: return 0
    return (wins * BET_UNIT * PAYOUT - (n - wins) * BET_UNIT) / (n * BET_UNIT)


def summarize_bucket(df: pd.DataFrame, kind: str = "total",
                     min_n: int = 30) -> dict | None:
    bet_col = f"bet_{kind}"
    won_col = f"won_{kind}"
    placed = df[df[bet_col] == True]
    n = len(placed)
    if n < min_n: return None
    wins = int(placed[won_col].sum())
    p, lo, hi = wr_ci(wins, n)
    r = roi(wins, n)
    pp_be = (p - BREAKEVEN) * 100
    # Significance: is CI lower bound above breakeven?
    significant_win = lo > BREAKEVEN
    significant_lose = hi < BREAKEVEN
    return {
        "n": n,
        "wins": wins,
        "WR": round(p, 4),
        "CI_lo": round(lo, 4),
        "CI_hi": round(hi, 4),
        "pp_over_BE": round(pp_be, 2),
        "ROI": round(r, 4),
        "sig_win": significant_win,
        "sig_lose": significant_lose,
    }


def show_table(rows: list[dict], title: str):
    print(f"\n── {title} ──")
    if not rows:
        print("  (no rows)")
        return
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))


def main():
    df = pd.read_csv(LEDGER)
    df["game_date"] = pd.to_datetime(df["game_date"])
    df["dow"] = df["game_date"].dt.day_name()
    print(f"Loaded {len(df)} games from V3 ledger")
    print(f"Date range: {df['game_date'].min().date()} → {df['game_date'].max().date()}")
    print(f"Seasons: {sorted(df['season'].unique())}")

    # ──────────────────────────────────────────────────────────────────
    # A. Side breakdown
    # ──────────────────────────────────────────────────────────────────
    rows = []
    for season in [None] + sorted(df["season"].unique()):
        sub = df if season is None else df[df["season"] == season]
        # OVER bets
        over = sub[sub["side_total"] == "OVER"]
        under = sub[sub["side_total"] == "UNDER"]
        home = sub[sub["side_spread"] == "HOME"]
        away = sub[sub["side_spread"] == "AWAY"]
        lbl = "ALL" if season is None else season
        for side_name, side_df, kind in [
            ("OVER", over, "total"),
            ("UNDER", under, "total"),
            ("HOME (spread)", home, "spread"),
            ("AWAY (spread)", away, "spread"),
        ]:
            s = summarize_bucket(side_df, kind=kind, min_n=20)
            if s:
                rows.append({"label": lbl, "side": side_name, **s})

    side_df = pd.DataFrame(rows)
    side_df.to_csv(OUT_DIR / "side_breakdown.csv", index=False)
    print("\n=== A. SIDE BREAKDOWN ===")
    print(side_df.to_string(index=False))

    # ──────────────────────────────────────────────────────────────────
    # B. Season stability of key patterns
    # ──────────────────────────────────────────────────────────────────
    print("\n\n=== B. SEASON STABILITY OF KEY PATTERNS ===")
    # Pickem total bets, low-total bets, edge 5-8 bets — per season
    df["close_spread_abs"] = df["close_spread_home"].abs()
    df["edge_total_abs"] = (df["proj_total"] - df["close_total"]).abs()

    patterns = {
        "pickem (spread≤3)": df["close_spread_abs"] <= 3,
        "low total (≤215)": df["close_total"] <= 215,
        "high total (>235)": df["close_total"] > 235,
        "edge 3-5": (df["edge_total_abs"] >= 3) & (df["edge_total_abs"] < 5),
        "edge 5-8": (df["edge_total_abs"] >= 5) & (df["edge_total_abs"] < 8),
        "edge 8-12": (df["edge_total_abs"] >= 8) & (df["edge_total_abs"] < 12),
        "edge 12+": df["edge_total_abs"] >= 12,
        "long spread (>12)": df["close_spread_abs"] > 12,
        "med spread (7-12)": (df["close_spread_abs"] > 7) & (df["close_spread_abs"] <= 12),
    }
    stab_rows = []
    for pat_name, mask in patterns.items():
        for season in sorted(df["season"].unique()):
            sub = df[mask & (df["season"] == season)]
            s = summarize_bucket(sub, "total", min_n=30)
            if s:
                stab_rows.append({"pattern": pat_name, "season": season, **s})
    stab_df = pd.DataFrame(stab_rows)
    stab_df.to_csv(OUT_DIR / "season_stability.csv", index=False)
    # Pivot for legibility
    if not stab_df.empty:
        piv = stab_df.pivot_table(index="pattern", columns="season",
                                   values="ROI", aggfunc="first")
        print("\nROI by pattern × season:")
        print((piv * 100).round(2).to_string())
        piv_wr = stab_df.pivot_table(index="pattern", columns="season",
                                      values="WR", aggfunc="first")
        print("\nWR by pattern × season:")
        print((piv_wr * 100).round(1).to_string())

    # ──────────────────────────────────────────────────────────────────
    # C. Compound stratifications
    # ──────────────────────────────────────────────────────────────────
    print("\n\n=== C. COMPOUND STRATIFICATIONS ===")
    compound_rows = []
    pickem_mask = df["close_spread_abs"] <= 3
    low_mask = df["close_total"] <= 220
    high_mask = df["close_total"] > 230
    mid_edge_mask = (df["edge_total_abs"] >= 5) & (df["edge_total_abs"] < 12)
    big_edge_mask = df["edge_total_abs"] >= 12

    compounds = {
        "pickem ∧ low-total": pickem_mask & low_mask,
        "pickem ∧ high-total": pickem_mask & high_mask,
        "pickem ∧ mid-edge": pickem_mask & mid_edge_mask,
        "pickem ∧ big-edge": pickem_mask & big_edge_mask,
        "low-total ∧ mid-edge": low_mask & mid_edge_mask,
        "low-total ∧ big-edge": low_mask & big_edge_mask,
        "high-total ∧ mid-edge": high_mask & mid_edge_mask,
        "high-total ∧ big-edge": high_mask & big_edge_mask,
        "pickem ∧ low ∧ mid-edge": pickem_mask & low_mask & mid_edge_mask,
        "pickem ∧ low ∧ big-edge": pickem_mask & low_mask & big_edge_mask,
    }
    for name, mask in compounds.items():
        sub = df[mask]
        s = summarize_bucket(sub, "total", min_n=20)
        if s:
            compound_rows.append({"compound": name, **s})
    comp_df = pd.DataFrame(compound_rows)
    if not comp_df.empty:
        comp_df = comp_df.sort_values("ROI", ascending=False)
        comp_df.to_csv(OUT_DIR / "compound_strata.csv", index=False)
        print(comp_df.to_string(index=False))

    # ──────────────────────────────────────────────────────────────────
    # D. Fade signals — where we lose hardest
    # ──────────────────────────────────────────────────────────────────
    print("\n\n=== D. FADE CANDIDATES (worst-WR strata) ===")
    fade_rows = []
    # Run all single-condition strata + flag the worst
    all_conditions = {**patterns, **compounds}
    for name, mask in all_conditions.items():
        sub = df[mask]
        s = summarize_bucket(sub, "total", min_n=30)
        if s:
            fade_rows.append({"strata": name, **s})
    fade_df = pd.DataFrame(fade_rows).sort_values("WR")
    print("Worst 10 strata (smallest WR — candidates to FADE):")
    print(fade_df.head(10).to_string(index=False))
    fade_df.to_csv(OUT_DIR / "fade_candidates.csv", index=False)

    # ──────────────────────────────────────────────────────────────────
    # E. Day of week (b2b proxy)
    # ──────────────────────────────────────────────────────────────────
    print("\n\n=== E. DAY-OF-WEEK ===")
    dow_rows = []
    for dow in ["Monday", "Tuesday", "Wednesday", "Thursday",
                "Friday", "Saturday", "Sunday"]:
        sub = df[df["dow"] == dow]
        for kind in ["total", "spread"]:
            s = summarize_bucket(sub, kind=kind, min_n=50)
            if s:
                dow_rows.append({"dow": dow, "kind": kind, **s})
    dow_df = pd.DataFrame(dow_rows)
    if not dow_df.empty:
        print(dow_df.to_string(index=False))
        dow_df.to_csv(OUT_DIR / "dow_breakdown.csv", index=False)

    # ──────────────────────────────────────────────────────────────────
    # F. Bias direction → side correctness
    # ──────────────────────────────────────────────────────────────────
    print("\n\n=== F. BIAS DIRECTION VALIDATION ===")
    # When we under-project (proj < close), do actuals usually OVER (matching close)?
    # i.e., when we're biased low, the market is right and we should fade
    under_proj = df[df["proj_total"] < df["close_total"]]
    over_proj = df[df["proj_total"] > df["close_total"]]
    bias_rows = []
    for name, sub in [("we_under_proj (we bet UNDER)", under_proj),
                      ("we_over_proj (we bet OVER)", over_proj)]:
        actual_over_close = (sub["actual_total"] > sub["close_total"]).mean()
        bias_rows.append({
            "case": name,
            "n": len(sub),
            "actual_over_close_rate": round(actual_over_close, 4),
        })
    bias_df = pd.DataFrame(bias_rows)
    print(bias_df.to_string(index=False))

    # ──────────────────────────────────────────────────────────────────
    # Markdown writeup
    # ──────────────────────────────────────────────────────────────────
    md = OUT_DIR / "PATTERN_FINDINGS.md"
    with open(md, "w", encoding="utf-8") as f:
        f.write(f"# V3 Bet Pattern Mining\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n")
        f.write(f"**Source:** {LEDGER}  (V3 mock runner = deployable model)\n\n")
        f.write(f"**Total games:** {len(df)}  ({df['season'].nunique()} seasons)\n\n")
        f.write("## A. Side breakdown\n\n")
        f.write(side_df.to_markdown(index=False) + "\n\n")
        f.write("## B. Season stability\n\n")
        f.write(stab_df.to_markdown(index=False) + "\n\n")
        f.write("## C. Compound stratifications (sorted by ROI)\n\n")
        f.write(comp_df.to_markdown(index=False) + "\n\n")
        f.write("## D. Fade candidates\n\n")
        f.write(fade_df.head(15).to_markdown(index=False) + "\n\n")
        f.write("## E. Day-of-week\n\n")
        f.write(dow_df.to_markdown(index=False) + "\n\n")
        f.write("## F. Bias direction validation\n\n")
        f.write(bias_df.to_markdown(index=False) + "\n")
    print(f"\n  → {md}")


if __name__ == "__main__":
    main()
