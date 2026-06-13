"""V4 backtest — V3 + pace-adjustment for spread-driven scoring inflation.

V3 mechanism finding: actual total exceeds projected total by an amount that
grows linearly with |Vegas spread|. Inferred mechanism = pace inflation in
high-spread games (faster tempo + less defense in blowout-prone matchups).

V4 fix: after computing V3's team-rescaled projected total, add a
pace-correction term proportional to |close_spread_home|. Slope calibrated
on 22-23 + 23-24 (training), then tested out-of-sample on 24-25 + 25-26.

This is a true train/test split to guard against overfitting.

Outputs at runs/run_nba_game_totals_22_26/v4_pace_adjusted/:
  - calibration.json
  - game_residuals.csv (V4 residuals)
  - combined_strategy_v4.csv
  - V4_RESULTS.md
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path("D:/NBA Projections")
V3_RESID = REPO / "runs" / "run_nba_game_totals_22_26" / "v3_mock_runner" / "game_residuals.csv"
OUT_DIR = REPO / "runs" / "run_nba_game_totals_22_26" / "v4_pace_adjusted"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_SEASONS = ["2022-23", "2023-24"]
TEST_SEASONS = ["2024-25", "2025-26"]

BREAKEVEN = 110 / 210
BET_UNIT = 100
PAYOUT = 100 / 110


def decide_strategy(row, edge_col="edge_total") -> tuple[str, str]:
    """Combined strategy applied to V4 residuals."""
    spread_abs = abs(row["close_spread_home"])
    edge = row[edge_col]
    edge_abs = abs(edge)
    if edge == 0: return "NONE", "NO_EDGE"
    our_side = "OVER" if edge > 0 else "UNDER"

    if spread_abs <= 3 and edge_abs >= 12 and our_side == "OVER":
        return "OVER", "PRIMARY"
    if 7 < spread_abs <= 12 and edge_abs >= 3:
        return ("UNDER" if our_side == "OVER" else "OVER"), "FADE_medspread"
    if 8 <= edge_abs < 12 and spread_abs > 3:
        return ("UNDER" if our_side == "OVER" else "OVER"), "FADE_edge_8_12"
    return "NONE", "NO_BET"


def pnl_of(side: str, row) -> tuple[int, float]:
    """Returns (result_code, pnl).  result ∈ {1, 0, -1, None}."""
    if side == "NONE": return None, 0.0
    if row["actual_total"] == row["close_total"]: return 0, 0.0
    over = row["actual_total"] > row["close_total"]
    won = (side == "OVER" and over) or (side == "UNDER" and not over)
    return (1 if won else -1), (BET_UNIT * PAYOUT if won else -BET_UNIT)


def summarize_bets(df_bets: pd.DataFrame, label: str) -> dict:
    n = len(df_bets)
    nw = int((df_bets["result"] == 1).sum())
    nl = int((df_bets["result"] == -1).sum())
    nd = nw + nl
    if nd == 0:
        return {"label": label, "n": 0}
    wr = nw / nd
    pnl_total = df_bets["pnl"].sum()
    roi = pnl_total / (n * BET_UNIT)
    p = stats.binomtest(nw, nd, p=BREAKEVEN, alternative="greater").pvalue
    return {
        "label": label, "n": n, "wins": nw, "losses": nl,
        "WR": round(wr, 4), "ROI": round(roi, 4),
        "PnL": round(pnl_total, 2), "p_value": round(p, 4),
    }


def main():
    df = pd.read_csv(V3_RESID)
    df["game_date"] = pd.to_datetime(df["game_date"])
    df["close_spread_abs"] = df["close_spread_home"].abs()
    print(f"Loaded {len(df)} V3 games")

    # ── 1. Calibrate pace slope on training seasons ────────────────────
    train = df[df["season"].isin(TRAIN_SEASONS)].copy()
    # bias = actual - proj. Fit bias ~ spread_abs (linear, no intercept ideal)
    # Use OLS with intercept to capture residual bias.
    X = train["close_spread_abs"].values
    y = (train["actual_total"] - train["proj_total"]).values
    slope, intercept = np.polyfit(X, y, 1)
    print(f"\n[CALIBRATION on {TRAIN_SEASONS}]")
    print(f"  bias = {intercept:.4f} + {slope:.4f} * spread_abs")
    print(f"  R²: {np.corrcoef(X, y)[0,1]**2:.4f}")

    # ── 2. Apply correction to all games ────────────────────────────────
    df["proj_total_v4"] = df["proj_total"] + intercept + slope * df["close_spread_abs"]
    df["edge_total_v4"] = df["proj_total_v4"] - df["close_total"]
    df["resid_total_v4"] = df["actual_total"] - df["proj_total_v4"]

    # ── 3. Bias check: train + test seasons ─────────────────────────────
    print("\n[BIAS BY SPREAD TIER — V4]")
    df["spread_tier"] = pd.cut(df["close_spread_abs"],
                                bins=[-0.01, 3, 7, 12, 100],
                                labels=["pickem", "short", "med", "long"])
    print(f"  {'tier':<7} {'season':<10} {'n':>5} {'v3_bias':>8} {'v4_bias':>8}")
    for tier in ["pickem", "short", "med", "long"]:
        for season in sorted(df["season"].unique()):
            sub = df[(df["spread_tier"] == tier) & (df["season"] == season)]
            if len(sub) < 30: continue
            v3b = (sub["actual_total"] - sub["proj_total"]).mean()
            v4b = (sub["actual_total"] - sub["proj_total_v4"]).mean()
            print(f"  {tier:<7} {season:<10} {len(sub):>5} "
                  f"{v3b:>+8.2f} {v4b:>+8.2f}")

    # ── 4. Aggregate V4 bias + MAE ──────────────────────────────────────
    print("\n[V4 vs V3 — totals]")
    for label, sub in [("ALL", df), ("TRAIN", df[df["season"].isin(TRAIN_SEASONS)]),
                       ("TEST", df[df["season"].isin(TEST_SEASONS)])]:
        n = len(sub)
        v3_bias = (sub["actual_total"] - sub["proj_total"]).mean()
        v4_bias = (sub["actual_total"] - sub["proj_total_v4"]).mean()
        v3_mae = (sub["actual_total"] - sub["proj_total"]).abs().mean()
        v4_mae = (sub["actual_total"] - sub["proj_total_v4"]).abs().mean()
        vegas_mae = (sub["actual_total"] - sub["close_total"]).abs().mean()
        print(f"  {label:<6} n={n:>5}  "
              f"v3_bias={v3_bias:>+6.2f} → v4_bias={v4_bias:>+6.2f}  "
              f"v3_mae={v3_mae:.2f} → v4_mae={v4_mae:.2f}  vegas={vegas_mae:.2f}")

    # ── 5. Apply combined strategy on V4 edges ──────────────────────────
    print("\n[V4 + COMBINED STRATEGY]")
    df["v4_side"] = ""
    df["v4_rule"] = ""
    df["result"] = pd.Series(dtype=object)
    df["pnl"] = 0.0
    for i, row in df.iterrows():
        side, rule = decide_strategy(row, edge_col="edge_total_v4")
        df.at[i, "v4_side"] = side
        df.at[i, "v4_rule"] = rule
        r, p = pnl_of(side, row)
        df.at[i, "result"] = r
        df.at[i, "pnl"] = p

    bets = df[df["v4_side"] != "NONE"].copy()
    print(f"  Total bets: {len(bets):,}  ({100*len(bets)/len(df):.1f}% of games)")

    # Overall + train/test split
    rows = [summarize_bets(bets, "ALL")]
    rows.append(summarize_bets(bets[bets["season"].isin(TRAIN_SEASONS)], "TRAIN_seasons"))
    rows.append(summarize_bets(bets[bets["season"].isin(TEST_SEASONS)], "TEST_seasons"))

    # Per-rule
    for rule_name in ["PRIMARY", "FADE_medspread", "FADE_edge_8_12"]:
        rows.append(summarize_bets(bets[bets["v4_rule"] == rule_name], f"rule_{rule_name}"))

    # Per-season
    for season in sorted(df["season"].unique()):
        rows.append(summarize_bets(bets[bets["season"] == season], season))

    sm = pd.DataFrame(rows)
    print(sm.to_string(index=False))
    sm.to_csv(OUT_DIR / "combined_strategy_v4.csv", index=False)

    # ── 6. Write artifacts ──────────────────────────────────────────────
    calib = {
        "train_seasons": TRAIN_SEASONS,
        "test_seasons": TEST_SEASONS,
        "intercept": float(intercept),
        "slope_per_spread_pt": float(slope),
        "formula": "proj_total_v4 = proj_total_v3 + "
                   f"{intercept:.4f} + {slope:.4f} * |close_spread_home|",
        "r_squared_train": float(np.corrcoef(X, y)[0, 1] ** 2),
    }
    with open(OUT_DIR / "calibration.json", "w") as f:
        json.dump(calib, f, indent=2)

    df_to_save = df[[
        "game_id", "game_date", "season", "home_team_abbr", "away_team_abbr",
        "home_proj_pts", "away_proj_pts", "proj_total", "proj_total_v4",
        "actual_total", "close_total", "close_spread_home", "edge_total_v4",
        "resid_total_v4", "v4_side", "v4_rule", "result", "pnl",
    ]].copy()
    df_to_save.to_csv(OUT_DIR / "game_residuals.csv", index=False)

    md = OUT_DIR / "V4_RESULTS.md"
    with open(md, "w", encoding="utf-8") as f:
        f.write("# V4 Pace-Adjusted Backtest\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n")
        f.write("## Calibration (TRAIN seasons: 22-23, 23-24)\n\n")
        f.write(f"`proj_total_v4 = proj_total_v3 + {intercept:.4f} + {slope:.4f} × |spread|`\n\n")
        f.write(f"R² on training: {calib['r_squared_train']:.4f}\n\n")
        f.write("## Combined strategy (V4 edges, same 4 rules)\n\n")
        f.write(sm.to_markdown(index=False) + "\n")
    print(f"\n  → {md}")


if __name__ == "__main__":
    main()
