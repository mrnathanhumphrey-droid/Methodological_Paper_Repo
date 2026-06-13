"""Apply Galton de-shrinkage stretch to the v6.1 ship.

For each stat: corrected = α + γ × proj  (γ < 1 across all stats)

Coefs fit on 25-26 actuals (in-sample for the demonstration; multi-season
backtest pending). NOTE: the empirical γ values are saved at
audit_runs/cohort_widening_v0_2025_26/deshrinkage_coefs.json from the
test_remaining_collatz_levers.py run.

Reads:    audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv
Writes:   audit_runs/unified_ship_v6_2_deshrunk_2025_26/per_player_projections_2025-26.csv

Shifts {stat}_per_game by α + γ × proj. Leaves {stat}_per_game_sd untouched
(de-shrinkage is a mean correction, not a variance one — that's the variance
miscalibration finding, parked separately).
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
import json
from pathlib import Path
import pandas as pd

REPO = Path(".")
SHIP_V61 = REPO / "audit_runs" / "unified_ship_v6_1_2025_26" / "per_player_projections_2025-26.csv"
COEFS = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "deshrinkage_coefs.json"
OUT_DIR = REPO / "audit_runs" / "unified_ship_v6_2_deshrunk_2025_26"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "per_player_projections_2025-26.csv"

# Map stat to per-game column in v6.1 ship (FG3M/FG3A use "3PM"/"3PA" alias post-v5)
STAT_TO_COL = {
    "PTS": "PTS_per_game", "REB": "REB_per_game", "AST": "AST_per_game",
    "STL": "STL_per_game", "BLK": "BLK_per_game", "TOV": "TOV_per_game",
    "FGM": "FGM_per_game", "FGA": "FGA_per_game",
    "FG3M": "FG3M_per_game", "FG3A": "FG3A_per_game",
    "FTM": "FTM_per_game", "FTA": "FTA_per_game",
}


def main():
    print(f"Reading: {SHIP_V61}")
    df = pd.read_csv(SHIP_V61)
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    print(f"  rows: {len(df)}")

    if not COEFS.exists():
        raise FileNotFoundError(f"De-shrinkage coefs not found at {COEFS}. "
                                 "Run test_remaining_collatz_levers.py first.")
    with open(COEFS) as f:
        coefs = json.load(f)

    print(f"De-shrinkage coefs loaded: {list(coefs.keys())}")
    n_applied = 0
    delta_log = {}
    for stat, col in STAT_TO_COL.items():
        if stat not in coefs or col not in df.columns:
            continue
        c = coefs[stat]
        # Skip stats where the fit had positive Δ (i.e., correction made it worse)
        if c.get("delta_pct", 0) >= 0:
            print(f"  SKIP {stat}: delta_pct={c['delta_pct']:+.2f}% (no improvement)")
            continue
        before = df[col].copy()
        df[col] = c["alpha"] + c["gamma"] * df[col]
        n_applied += 1
        delta_log[stat] = {
            "alpha": c["alpha"], "gamma": c["gamma"],
            "mean_before": float(before.mean()),
            "mean_after": float(df[col].mean()),
            "shift": float(df[col].mean() - before.mean()),
            "expected_mae_delta_pct": c["delta_pct"],
        }
        print(f"  applied {stat}: α={c['alpha']:+.3f}, γ={c['gamma']:.3f}  "
              f"(mean shift: {df[col].mean() - before.mean():+.3f})")

    df.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {OUT_CSV} ({len(df)} rows, {n_applied} stats de-shrunk)")

    metadata = {
        "version": "v6.2_deshrunk_2025_26",
        "source_ship": str(SHIP_V61).replace("\\", "/"),
        "applied_stats": list(delta_log.keys()),
        "applied_log": delta_log,
        "method": "actual = alpha + gamma * proj (Galton de-shrinkage), per-stat OLS fit",
        "calibration_basis": "25-26 actuals (in-sample for demo; cross-season validation pending)",
        "note": "Galton/Tukey shrinkage correction. v6.1 hierarchical posterior shrinks rates "
                 "too aggressively toward the league mean; γ < 1 across all stats reverses this.",
    }
    with open(OUT_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata -> {OUT_DIR}/metadata.json")


if __name__ == "__main__":
    main()
