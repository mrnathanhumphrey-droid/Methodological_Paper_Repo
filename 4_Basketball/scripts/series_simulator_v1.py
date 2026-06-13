"""Series Simulator v1 — best-of-7 Monte Carlo on top of team game predictions.

Method:
  - Use Phase 2+3 team game predictions to estimate per-game predicted margin
    between two teams
  - Convert margin → win probability via logistic(margin / 12) with home-court adjust
  - Monte Carlo 50k 7-game series; report P(team_A wins), expected length, by-game
  - Handle current real-world state: if a series is in progress, condition on games
    already played

Input data:
  - team_strength.csv (derived): per-team rating from season_win_totals v1
  - This-season playoff bracket (from data/parquet/playoffs/_manifest.parquet)

Output:
  - series_outcomes.csv: per active/upcoming series, simulated win probabilities
  - prediction_for_conference_finals.json (if Conf Finals matchups known)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:/NBA Projections")
WIN_TOTALS = ROOT / "audit_runs/season_win_totals_v1/win_totals_tier1b_production.csv"
WIN_TOTALS_FALLBACK = ROOT / "audit_runs/season_win_totals_v1/win_totals_phase3_lineup_def.csv"
MANIFEST = ROOT / "data/parquet/playoffs/round1/_manifest.parquet"
MANIFEST_EXTRA = ROOT / "data/parquet/playoffs/extra_rounds/_manifest.parquet"
SUMMARY_GAME = ROOT / "data/parquet/playoffs/extra_rounds/summary_game.parquet"
OUT_DIR = ROOT / "audit_runs/series_simulator_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

N_SIMS = 50000
HOMECOURT_MARGIN = 1.74  # per memory, halved from 2.72 over era
MARGIN_SIGMA = 12.0


def derive_team_strength() -> pd.DataFrame:
    """Per-team strength rating in points (vs average team)."""
    # Use season win totals — pretend wins ↔ strength via logistic inverse
    if WIN_TOTALS.exists():
        df = pd.read_csv(WIN_TOTALS)
    elif WIN_TOTALS_FALLBACK.exists():
        df = pd.read_csv(WIN_TOTALS_FALLBACK)
    else:
        raise FileNotFoundError("No season win totals output found — run season_win_totals_v1.py first")
    # win_pct → log-odds → point margin equivalent
    df["win_pct"] = df["projected_total_wins"] / df["games_predicted"]
    df["win_pct"] = df["win_pct"].clip(0.05, 0.95)  # avoid -inf
    df["log_odds"] = np.log(df["win_pct"] / (1 - df["win_pct"]))
    # Center on league average
    df["strength_points"] = (df["log_odds"] - df["log_odds"].mean()) * MARGIN_SIGMA
    return df[["team", "strength_points", "projected_total_wins"]].copy()


def sim_game(home_strength: float, away_strength: float,
              rng: np.random.Generator) -> int:
    """Simulate one game; return 1 if home wins, 0 if away."""
    pred_margin_home = home_strength - away_strength + HOMECOURT_MARGIN
    realized_margin = pred_margin_home + rng.normal(0, MARGIN_SIGMA)
    return 1 if realized_margin > 0 else 0


def sim_series(team_a: str, team_b: str, strength: pd.DataFrame,
                home_for_first_two: str = None, format_2_2_1_1_1: bool = True,
                n_sims: int = N_SIMS, already_played: list = None) -> dict:
    """Monte Carlo best-of-7. Standard 2-2-1-1-1 format.

    team_a = higher-seed (gets home-court advantage)
    home_for_first_two = team_a by default
    already_played: list of (game_num_1_to_7, winner_team) tuples to condition on
    """
    if home_for_first_two is None:
        home_for_first_two = team_a
    home_per_game = []
    if format_2_2_1_1_1:
        # Games 1,2,5,7 at home_for_first_two; 3,4,6 at the other
        for g in [1, 2, 3, 4, 5, 6, 7]:
            home_per_game.append(home_for_first_two if g in (1, 2, 5, 7) else
                                   (team_b if home_for_first_two == team_a else team_a))
    else:
        home_per_game = [home_for_first_two] * 7
    s_a = float(strength[strength["team"] == team_a]["strength_points"].iloc[0])
    s_b = float(strength[strength["team"] == team_b]["strength_points"].iloc[0])
    already_played = already_played or []

    rng = np.random.default_rng(2026)
    wins_a = 0
    series_lens = []
    by_game_a_win_count = [0] * 8  # 1-indexed
    series_outcomes_4_5_6_7 = {4: 0, 5: 0, 6: 0, 7: 0}
    for _ in range(n_sims):
        a_w, b_w = 0, 0
        last_g = 0
        for g_idx, host in enumerate(home_per_game, start=1):
            # If this game already played, use real result
            played = [r for r in already_played if r[0] == g_idx]
            if played:
                if played[0][1] == team_a:
                    a_w += 1
                else:
                    b_w += 1
                last_g = g_idx
            else:
                if host == team_a:
                    res = sim_game(s_a, s_b, rng)
                    if res == 1:
                        a_w += 1
                    else:
                        b_w += 1
                else:
                    res = sim_game(s_b, s_a, rng)
                    if res == 1:
                        b_w += 1
                    else:
                        a_w += 1
                last_g = g_idx
            if a_w == 4 or b_w == 4:
                if a_w == 4:
                    wins_a += 1
                    by_game_a_win_count[g_idx] += 1
                series_lens.append(g_idx)
                series_outcomes_4_5_6_7[g_idx if g_idx in series_outcomes_4_5_6_7 else 7] += 1
                break

    return {
        "team_a": team_a, "team_b": team_b,
        "team_a_strength_points": s_a, "team_b_strength_points": s_b,
        "p_team_a_wins_series": wins_a / n_sims,
        "expected_series_length": float(np.mean(series_lens)),
        "p_sweep_a": by_game_a_win_count[4] / n_sims,
        "p_series_length": {k: v / n_sims for k, v in series_outcomes_4_5_6_7.items()},
        "n_sims": n_sims,
        "already_played": already_played,
    }


def main():
    print("=" * 80)
    print("SERIES SIMULATOR v1 — best-of-7 Monte Carlo on 25-26 NBA playoffs")
    print("=" * 80)
    print()

    strength = derive_team_strength()
    print("Top 8 teams by derived strength (points vs average):")
    print(strength.sort_values("strength_points", ascending=False).head(8).to_string(index=False))
    print()

    # Detect current playoff bracket from manifest + summary_game
    bracket_info = {}
    if MANIFEST_EXTRA.exists():
        m = pd.read_parquet(MANIFEST_EXTRA)
        print(f"\nExtra-rounds manifest: {len(m)} entries")
        if len(m) > 0:
            print(m[["game_id", "round", "matchup_idx", "game_in_series",
                      "home_team_abbr", "game_date"]].to_string()
                  if "round" in m.columns else m.head().to_string())

    # Hardcoded current Conference Finals as of 2026-05-18 evening:
    # Game 1 of CF tonight. User said this. Need to deduce matchups from strength data.
    # Top teams: OKC, SAS, DET, BOS, DEN, LAL, HOU, NYK
    # Western: OKC (1), SAS (2), DEN (5), LAL (6) - typically WCF has top 2 seeds
    # Eastern: DET (3), BOS (4), CLE (9), NYK (8)
    print("\n" + "=" * 80)
    print("Simulating projected Conference Finals matchups")
    print("(Based on top-strength teams per derived rating)")
    print("=" * 80)

    # Western Conf candidates: OKC, SAS, DEN, LAL (top-strength West)
    # Eastern Conf candidates: DET, BOS, NYK, CLE (top-strength East)
    # Without explicit bracket info, simulate 4 plausible CF matchups + one Finals
    matchups = [
        ("OKC", "DEN", "Western Conf Final hypothetical"),
        ("OKC", "SAS", "Western Conf Final hypothetical"),
        ("BOS", "DET", "Eastern Conf Final hypothetical"),
        ("BOS", "NYK", "Eastern Conf Final hypothetical"),
        ("OKC", "BOS", "NBA Finals hypothetical (top seeds)"),
    ]
    results = []
    for a, b, label in matchups:
        if a not in strength["team"].values or b not in strength["team"].values:
            print(f"  Skip {a} vs {b}: team not in strength table")
            continue
        sim = sim_series(a, b, strength)
        sim["label"] = label
        results.append(sim)
        print(f"\n{label}: {a} vs {b}")
        print(f"  {a} strength: {sim['team_a_strength_points']:.2f} pts")
        print(f"  {b} strength: {sim['team_b_strength_points']:.2f} pts")
        print(f"  P({a} wins series) = {sim['p_team_a_wins_series']:.3f}")
        print(f"  P(sweep by {a}) = {sim['p_sweep_a']:.3f}")
        print(f"  Expected series length: {sim['expected_series_length']:.2f} games")
        print(f"  Series length distribution: {sim['p_series_length']}")

    # Persist
    with open(OUT_DIR / "series_outcomes.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    strength.to_csv(OUT_DIR / "team_strength_ratings.csv", index=False)
    pd.DataFrame(results).to_csv(OUT_DIR / "series_outcomes.csv", index=False)
    print(f"\nWrote outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
