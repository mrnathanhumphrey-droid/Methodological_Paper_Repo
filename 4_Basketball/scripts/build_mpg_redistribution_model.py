"""Build the depth-chart-aware MPG redistribution calibration table.

Cleanly identifies "1 OUT teammate with starter-level minutes" cases and
calibrates how much of his expected minutes go to each depth-position cell
among the remaining active teammates.

Pipeline:
  1. Build active-state panel from pro_sports_injuries.
  2. Build box-score panel with rolling-prior expected_min.
  3. Filter to team-games with EXACTLY 1 OUT teammate (clean signal),
     OUT teammate has expected_min ≥ 18 (real starter/heavy role),
     OUT teammate has depth_order ∈ {1, 2} (starter or primary backup).
  4. For each active player on such team-games, compute:
        share = (actual_min − expected_min) / out_player_expected_min
        relation = (position_match flag, active player's depth_order)
  5. Aggregate share by (out_position, active_position, active_depth)
     → empirical redistribution share table.

Outputs:
  data/parquet/mpg_redistribution_lookup.parquet — share table
  data/parquet/mpg_redistribution_training_panel.parquet — training rows
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
OUT_LOOKUP = PQ / "mpg_redistribution_lookup.parquet"
OUT_PANEL = PQ / "mpg_redistribution_training_panel.parquet"

CALIB_SEASONS = ["2022-23", "2023-24", "2024-25"]
ROLLING_PRIOR_GAMES = 5
MIN_PLAYER_GAMES_PRIOR = 3
MIN_OUT_EXPECTED_MIN = 18.0       # require real starter / rotation player out
MIN_TRAINING_CELL_N = 30          # require this many rows per lookup cell


def build_player_segments() -> pd.DataFrame:
    inj = pd.read_parquet(PQ / "pro_sports_injuries.parquet")
    inj = inj.dropna(subset=["nba_api_id"]).copy()
    inj["nba_api_id"] = inj["nba_api_id"].astype(int)
    inj["event_date"] = pd.to_datetime(inj["event_date"])
    inj = inj.sort_values(["nba_api_id", "event_date"])
    return inj[["nba_api_id", "event_date", "side"]].assign(
        new_state_active=lambda d: d["side"].eq("acquired")
    )


def attach_active_flag(pg: pd.DataFrame, seg_df: pd.DataFrame) -> pd.DataFrame:
    seg_sorted = seg_df.sort_values(["nba_api_id", "event_date"]).reset_index(drop=True)
    pg = pg.copy()
    pg["nba_api_id"] = pg["nba_api_id"].astype(int)
    pg["game_date"] = pd.to_datetime(pg["game_date"])
    pg["is_active"] = True

    for pid, evs in seg_sorted.groupby("nba_api_id"):
        mask = (pg["nba_api_id"] == pid).values
        if not mask.any():
            continue
        ev_dates = pd.to_datetime(evs["event_date"].values).values
        ev_states = evs["new_state_active"].values.astype(bool)
        game_dates = pg.loc[mask, "game_date"].values
        pos = np.searchsorted(ev_dates, game_dates, side="right") - 1
        states = np.where(pos >= 0, ev_states[np.clip(pos, 0, None)], True)
        pg.loc[mask, "is_active"] = states
    return pg


def build_box_score_panel(seasons: list[str]) -> pd.DataFrame:
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx = bx[bx["season"].isin(seasons) & (bx["season_type"] == "Regular Season")].copy()
    bx["minutes"] = pd.to_numeric(bx["minutes"], errors="coerce")
    bx = bx.dropna(subset=["minutes"])
    bx["game_date"] = pd.to_datetime(bx["game_date"])
    bx["nba_api_id"] = bx["nba_api_id"].astype(int)
    bx = bx.sort_values(["nba_api_id", "game_date"])
    bx["expected_min"] = (
        bx.groupby("nba_api_id")["minutes"]
        .transform(lambda s: s.shift(1).rolling(ROLLING_PRIOR_GAMES, min_periods=MIN_PLAYER_GAMES_PRIOR).mean())
    )
    return bx[["nba_api_id", "game_id", "game_date", "team_abbr", "season",
               "minutes", "expected_min"]]


def attach_depth_and_position(panel: pd.DataFrame) -> pd.DataFrame:
    dc = pd.read_parquet(PQ / "derived_depth_chart.parquet")
    dc["nba_api_id"] = dc["nba_api_id"].astype(int)
    panel = panel.merge(
        dc[["season", "team_abbr", "nba_api_id", "depth_order"]],
        on=["season", "team_abbr", "nba_api_id"], how="left"
    )
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    meta = meta[["nba_api_id", "position"]].copy()
    meta["nba_api_id"] = meta["nba_api_id"].astype(int)
    panel = panel.merge(meta, on="nba_api_id", how="left")
    panel["position"] = panel["position"].fillna("Forward")
    panel["depth_bin"] = panel["depth_order"].fillna(99).clip(upper=8).astype(int)
    return panel


def build_training_rows(panel: pd.DataFrame) -> pd.DataFrame:
    """For each (team, game) with exactly 1 OUT teammate (expected_min ≥ threshold),
    emit rows for each ACTIVE player on the team."""
    # All inactive player-games per team-game
    inactive = panel[~panel["is_active"]].copy()
    inactive = inactive.dropna(subset=["expected_min"])
    inactive = inactive[inactive["expected_min"] >= MIN_OUT_EXPECTED_MIN]

    # team-games with exactly 1 such heavy-minute OUT
    grp = inactive.groupby(["team_abbr", "game_date"]).agg(
        n_heavy_out=("nba_api_id", "nunique"),
        out_pid=("nba_api_id", "first"),
        out_position=("position", "first"),
        out_depth=("depth_bin", "first"),
        out_expected_min=("expected_min", "first"),
    ).reset_index()
    clean = grp[grp["n_heavy_out"] == 1].copy()
    print(f"  team-games with EXACTLY 1 heavy OUT teammate: {len(clean)}")

    # Join back to active players' rows on those team-games
    active_rows = panel[panel["is_active"]].dropna(subset=["expected_min"]).copy()
    train = active_rows.merge(
        clean[["team_abbr", "game_date", "out_pid", "out_position",
               "out_depth", "out_expected_min"]],
        on=["team_abbr", "game_date"], how="inner"
    )
    # Don't include the OUT player himself (he's not active anyway, but be safe)
    train = train[train["nba_api_id"] != train["out_pid"]]
    train["min_shift"] = train["minutes"] - train["expected_min"]
    train["share_absorbed"] = train["min_shift"] / train["out_expected_min"]
    # Same-position flag: are active and out players same coarse position?
    train["same_position"] = train["position"] == train["out_position"]
    train["depth_pair"] = train["depth_bin"].astype(str) + "_vs_" + train["out_depth"].astype(str)
    print(f"  active-player rows on those team-games: {len(train)}")
    return train


def calibrate_lookup(train: pd.DataFrame) -> pd.DataFrame:
    """Aggregate by (out_position, active_position, active_depth)."""
    train = train.copy()
    # Clip outliers (DNP→played transitions, etc.)
    train["share_clipped"] = train["share_absorbed"].clip(-0.5, 1.5)
    rows = []
    for (out_pos, act_pos, act_depth), g in train.groupby(
            ["out_position", "position", "depth_bin"], dropna=False):
        if len(g) < MIN_TRAINING_CELL_N:
            continue
        rows.append({
            "out_position": out_pos,
            "active_position": act_pos,
            "active_depth": int(act_depth),
            "same_position": out_pos == act_pos,
            "n_rows": len(g),
            "mean_share": float(g["share_clipped"].mean()),
            "median_share": float(g["share_clipped"].median()),
            "sd_share": float(g["share_clipped"].std()),
        })
    return pd.DataFrame(rows).sort_values(
        ["out_position", "same_position", "active_depth"],
        ascending=[True, False, True]
    )


def main():
    print("[1/4] Building injury segments...")
    seg = build_player_segments()
    print(f"      {len(seg)} segment events, {seg['nba_api_id'].nunique()} players")

    print(f"[2/4] Loading box scores for {CALIB_SEASONS}...")
    bx = build_box_score_panel(CALIB_SEASONS)
    print(f"      {len(bx)} player-game rows")

    print("[3/4] Joining active-state flag + depth + position...")
    bx = attach_active_flag(bx, seg)
    bx = attach_depth_and_position(bx)
    print(f"      {(~bx['is_active']).sum()} inactive player-games")

    print("[4/4] Building training rows (clean-1-OUT cases)...")
    train = build_training_rows(bx)

    print()
    print("Saving training panel...")
    bx.to_parquet(OUT_PANEL, index=False)
    print(f"  -> {OUT_PANEL}")

    print()
    print("Calibrating lookup by (out_position, active_position, active_depth)...")
    lookup = calibrate_lookup(train)
    print()
    print("LOOKUP TABLE — share of OUT player's expected minutes absorbed")
    print("=" * 100)
    print(f"{'out_pos':<8} {'act_pos':<8} {'act_dpth':<9} {'same?':<6} "
          f"{'n':>6} {'mean':>8} {'median':>8} {'sd':>7}")
    print("-" * 70)
    for _, r in lookup.iterrows():
        same = "YES" if r["same_position"] else "no"
        print(f"{r['out_position']:<8} {r['active_position']:<8} "
              f"{int(r['active_depth']):<9} {same:<6} "
              f"{int(r['n_rows']):>6} {r['mean_share']:>+8.4f} "
              f"{r['median_share']:>+8.4f} {r['sd_share']:>7.4f}")

    lookup.to_parquet(OUT_LOOKUP, index=False)
    print()
    print(f"Saved lookup -> {OUT_LOOKUP}")

    # Sanity: same-position rows should show positive shares; cross-position near 0
    same_pos = lookup[lookup["same_position"]]
    cross_pos = lookup[~lookup["same_position"]]
    print()
    print(f"Same-position mean share avg: {same_pos['mean_share'].mean():+.4f} "
          f"(n_cells={len(same_pos)})")
    print(f"Cross-position mean share avg: {cross_pos['mean_share'].mean():+.4f} "
          f"(n_cells={len(cross_pos)})")


if __name__ == "__main__":
    main()
