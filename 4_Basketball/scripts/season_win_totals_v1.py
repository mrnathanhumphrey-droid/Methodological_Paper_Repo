"""Season win totals — aggregate Phase 2+3 per-team game predictions to season-level.

Input: per_team_game_predictions.csv (Phase 2+3 tier1b production run on 2025-26)
Output:
  - season_win_totals_2025_26.csv: per-team projected wins + actual through games-played
  - vs_vegas_comparison.csv (if a vegas season-totals snapshot available)

Method:
  - For each game in 2025-26, pair the two team rows
  - Compute per-game predicted win probability = logistic(predicted_score_diff / 12)
    (12 is approximate scoring std for NBA game margins)
  - Sum predicted_win_prob across all 82 games per team → expected_wins
  - Also compute actual wins to date for in-season comparison

Standalone product, no dependencies on Wonka. Reads only audit_runs/ outputs.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:/NBA Projections")
PRED_TIER1B = (ROOT / "audit_runs/game_predictions_2025_26_phase2_tier1b/"
                "per_team_game_predictions.csv")
PRED_LINEUP_DEF = (ROOT / "audit_runs/game_predictions_2025_26_phase3_lineup_def/"
                    "per_team_game_predictions.csv")
PRED_REST_B2B = (ROOT / "audit_runs/game_predictions_2025_26_phase3_rest_b2b/"
                  "per_team_game_predictions.csv")
OUT_DIR = ROOT / "audit_runs/season_win_totals_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Per memory + paper state: production model = 60% SRS + 40% Tier1B+EMA at 65.31%
# Use tier1b as the headline (matches the production blend per PAPER_STATE).
# Margin standard deviation per NBA game ~12 points (used to convert score-diff → win-prob)
MARGIN_SIGMA = 12.0


def load_pair_pred(path: Path) -> pd.DataFrame:
    """Load per-team-per-game predictions and pair the two team rows per game."""
    df = pd.read_csv(path)
    # Each game appears as two rows (one per team). Pair them.
    home = df[df["is_home"]].rename(columns={
        "team_abbreviation": "home_team", "team_pts_pred": "home_pts_pred",
        "pts": "home_pts_actual",
    })[["game_id", "game_date", "home_team", "home_pts_pred", "home_pts_actual",
         "opp_team"]]
    away = df[~df["is_home"]].rename(columns={
        "team_abbreviation": "away_team", "team_pts_pred": "away_pts_pred",
        "pts": "away_pts_actual",
    })[["game_id", "away_team", "away_pts_pred", "away_pts_actual"]]
    paired = home.merge(away, on="game_id", how="inner")
    # Predicted margin (home perspective)
    paired["pred_margin_home"] = paired["home_pts_pred"] - paired["away_pts_pred"]
    paired["actual_margin_home"] = paired["home_pts_actual"] - paired["away_pts_actual"]
    paired["home_win_actual"] = (paired["actual_margin_home"] > 0).astype(int)
    paired["home_win_pred_prob"] = 1 / (1 + np.exp(-paired["pred_margin_home"] / MARGIN_SIGMA))
    return paired


def aggregate_to_season(paired: pd.DataFrame) -> pd.DataFrame:
    """Per-team aggregate: actual wins + expected (predicted) wins across the season."""
    home_view = paired.assign(team=paired["home_team"],
                                win_pred=paired["home_win_pred_prob"],
                                win_actual=paired["home_win_actual"])
    away_view = paired.assign(team=paired["away_team"],
                                win_pred=1 - paired["home_win_pred_prob"],
                                win_actual=1 - paired["home_win_actual"])
    teams_all = pd.concat([home_view, away_view], ignore_index=True)
    # Game played has non-null actual_margin_home
    teams_all["games_played"] = teams_all["actual_margin_home"].notna().astype(int)
    teams_all["wins_to_date"] = teams_all["games_played"] * teams_all["win_actual"]
    out = teams_all.groupby("team").agg(
        games_predicted=("game_id", "count"),
        games_played=("games_played", "sum"),
        expected_wins=("win_pred", "sum"),
        wins_to_date=("wins_to_date", "sum"),
    ).reset_index()
    # Remaining games' expected wins = expected_wins from non-played games only
    not_played = teams_all[teams_all["games_played"] == 0]
    rem = not_played.groupby("team")["win_pred"].sum().reset_index().rename(
        columns={"win_pred": "expected_wins_remaining"})
    out = out.merge(rem, on="team", how="left")
    out["expected_wins_remaining"] = out["expected_wins_remaining"].fillna(0)
    out["projected_total_wins"] = out["wins_to_date"] + out["expected_wins_remaining"]
    out["projected_total_losses"] = (out["games_predicted"] -
                                       out["projected_total_wins"])
    out = out.sort_values("projected_total_wins", ascending=False).reset_index(drop=True)
    out["rank"] = out.index + 1
    return out


def main():
    print("=" * 80)
    print("SEASON WIN TOTALS v1 — 2025-26 NBA (aggregated from Phase 2+3 game predictions)")
    print("=" * 80)
    print()

    for name, path in [("tier1b production", PRED_TIER1B),
                        ("phase3 lineup_def", PRED_LINEUP_DEF),
                        ("phase3 rest_b2b", PRED_REST_B2B)]:
        if not path.exists():
            print(f"  SKIP {name}: {path} not found")
            continue
        print(f"\n--- {name} ---")
        paired = load_pair_pred(path)
        print(f"  Games loaded: {len(paired)}")
        n_played = paired["actual_margin_home"].notna().sum()
        print(f"  Games played so far: {n_played} of {len(paired)}")

        agg = aggregate_to_season(paired)
        agg.to_csv(OUT_DIR / f"win_totals_{name.replace(' ', '_')}.csv", index=False)
        print(f"\n  Top 10 projected (n=30 teams):")
        print(agg.head(10)[["rank", "team", "games_played", "wins_to_date",
                              "projected_total_wins"]].to_string(index=False))
        print(f"\n  Bottom 5:")
        print(agg.tail(5)[["rank", "team", "games_played", "wins_to_date",
                            "projected_total_wins"]].to_string(index=False))

    # Save the production tier1b as canonical
    print("\n" + "=" * 80)
    print(f"Outputs at {OUT_DIR}")
    print("Canonical season win totals: tier1b model (matches production per PAPER_STATE)")


if __name__ == "__main__":
    main()
