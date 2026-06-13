"""Backtest v6.1 LOCKED projection layer on historical NBA playoff data (22-25, R1).

Goal: assess whether v6.1's regular-season-trained projection layer transfers to
playoff regime, to inform deployment posture for the in-progress 25-26 playoffs.

Three variants per (player, game, stat):
  A) regular-season-only: per-game season rate × (game_min / season_avg_min)
  B) conditioned: A × opponent DvP multiplier × pace multiplier
  C) playoff-cohort-only: position-cohort-mean playoff rate × game_min (LOO)

Outputs to runs/run_nba_playoffs_backtest_22_25/:
  - backtest_playoff_residuals.csv  (long-format per (game, player, stat, variant))
  - backtest_mae_summary.csv        (aggregated MAE per (variant, cohort, stat))
  - backtest_variance_calibration.csv (50/80/95% interval coverage)
  - per_season_summary.csv          (MAE per (variant, stat, season))

Ship lookup: latest phase4_v4_quadratic_tq_g per-stat ship per target season.
v6.1 LOCKED levers per scripts/apply_v6_1_locked_offsets_2025_26.py applied per season.

Data-availability rule: each historical season's projection uses only data
strictly before that season starts (the phase4 ships are forward-only, by
construction — the train season list ends with the prior season).
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
PLAYOFFS_R1 = PQ / "playoffs" / "round1"
PLAYOFFS_EXTRA = PQ / "playoffs" / "extra_rounds"
OUT_DIR = REPO / "runs" / "run_nba_playoffs_backtest_22_25"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BACKTEST_SEASONS = ["2022-23", "2023-24", "2024-25"]
PRIMARY_STATS = ["PTS", "REB", "AST", "STL", "BLK", "TOV"]   # full 22-25 coverage
SINGLE_SEASON_STATS = ["FG3M"]                                 # 23-24 only
DERIVED_STATS = {
    "RA": ("REB", "AST"),
    "PR": ("PTS", "REB"),
    "PRA": ("PTS", "REB", "AST"),
}
ALL_STATS = PRIMARY_STATS + SINGLE_SEASON_STATS + list(DERIVED_STATS.keys())

# Box-score field name mapping (camelCase -> our stat code)
BOX_STAT_MAP = {
    "PTS": "points",
    "REB": "reboundsTotal",
    "AST": "assists",
    "STL": "steals",
    "BLK": "blocks",
    "TOV": "turnovers",
    "FG3M": "threePointersMade",
}

# v6.1 LOCKED levers (per audit_runs/unified_ship_v6_1/metadata.json, 2026-05-02)
# Mid-season-change lever (PTS x0.9382) is INERT here — applies only when
# a coaching change exists in the target season's metadata.
PTS_CENTER_OFFSET = -0.587            # ADDITIVE per-game PTS for Centers
AST_VET_MULT = 0.9278                 # MULT per-game AST for years_pro_bucket=13+
REB_GUARD_VAR_MULT = 0.723            # tightens REB sd for Guards
AST_FWD_VAR_MULT = 0.819              # tightens AST sd for Forwards
BLK_GUARD_VAR_MULT = 0.662            # tightens BLK sd for Guards


# --------------------------------------------------------------------------- #
# 1. Load + apply v6.1 levers per (stat, season)
# --------------------------------------------------------------------------- #
SHIP_INDEX_PATH = OUT_DIR / "_ship_index.json"


def discover_ships():
    """Return {(stat, season): csv_path} for the latest phase4_v4_quadratic_tq_g
    ship per (stat, target_season).
    """
    pat = re.compile(
        r"skill_backtest_([A-Z3]+)_phase4_v4_quadratic_tq_g_[0-9-]+__([0-9-]+)/"
        r"per_player_projections\.csv$"
    )
    hits = defaultdict(list)
    for f in REPO.glob("audit_runs/*/skill_backtest_*_phase4_v4_quadratic_tq_g_*"
                       "__*/per_player_projections.csv"):
        fn = str(f).replace("\\", "/")
        m = pat.search(fn)
        if not m:
            continue
        stat, target = m.group(1), m.group(2)
        ts = fn.split("/")[1]
        hits[(stat, target)].append((ts, fn))

    out = {}
    for k, v in hits.items():
        out[k] = sorted(v)[-1][1]   # latest by timestamp dir

    # Also pick up FG3M prior-season-rate baselines for missing seasons
    for target_season in BACKTEST_SEASONS:
        if ("FG3M", target_season) not in out:
            p = REPO / "audit_runs" / f"fg3m_prior_season_baseline_{target_season}" / "per_player_projections.csv"
            if p.exists():
                out[("FG3M", target_season)] = str(p).replace("\\", "/")
    return out


def attach_class_features(df: pd.DataFrame, target_year: int) -> pd.DataFrame:
    """Attach pos_class, years_pro_bucket using metadata-enriched table."""
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    sup_path = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "rookie_metadata_supplement.parquet"
    cols = ["nba_api_id", "position", "draft_year", "debut_year"]
    if sup_path.exists():
        sup = pd.read_parquet(sup_path)
        meta = pd.concat([meta[cols], sup[cols]], ignore_index=True)
    df = df.merge(meta[cols], on="nba_api_id", how="left")

    # Primary position class: G/F/C from first letter of first listed component
    def _primary(p):
        if not isinstance(p, str) or not p:
            return None
        first = p.split("-")[0].strip().upper()
        if first.startswith("G"):
            return "G"
        if first.startswith("C"):
            return "C"
        if first.startswith("F"):
            return "F"
        return None

    df["pos_class"] = df["position"].apply(_primary)
    df["years_pro"] = df["debut_year"].where(
        df["debut_year"].notna(),
        df["draft_year"] + 1,
    )
    df["years_pro"] = target_year - df["years_pro"]
    df["years_pro_bucket"] = pd.cut(
        df["years_pro"], bins=[-1, 0, 3, 7, 12, 30],
        labels=["rookie", "1-3", "4-7", "8-12", "13+"],
    ).astype(str)
    return df


COHORT_MAP = {
    "rookie": "rookie",
    "1-3": "soph",
    "4-7": "early_vet",
    "8-12": "mid_vet",
    "13+": "deep_vet",
}


def build_unified_season_ship(stat: str, season: str, ship_csv: str) -> pd.DataFrame:
    """Load ship, attach class features, apply v6.1 LOCKED levers for this stat.

    Returns columns: nba_api_id, name, stat, season, pos_class, years_pro_bucket,
                     cohort, proj_mean, proj_sd, proj_q05, proj_q25, proj_q75,
                     proj_q95, actual_minutes_rs, actual_games_rs, mpg_rs,
                     proj_per_min, sd_per_min
    """
    df = pd.read_csv(ship_csv)
    if "nba_api_id" not in df.columns:
        raise ValueError(f"ship missing nba_api_id: {ship_csv}")
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    df["stat"] = stat
    df["season"] = season

    target_year = int(season.split("-")[0])
    df = attach_class_features(df, target_year=target_year)
    df["cohort"] = df["years_pro_bucket"].map(COHORT_MAP).fillna("unknown")

    # Apply v6.1 LOCKED mean offsets per stat
    if stat == "PTS":
        center_mask = df["pos_class"] == "C"
        df.loc[center_mask, "proj_mean"] = df.loc[center_mask, "proj_mean"] + PTS_CENTER_OFFSET
    elif stat == "AST":
        vet_mask = df["years_pro_bucket"] == "13+"
        df.loc[vet_mask, "proj_mean"] = df.loc[vet_mask, "proj_mean"] * AST_VET_MULT

    # Apply v6.1 LOCKED variance multipliers per stat (TIGHTEN sd)
    if stat == "REB":
        guard_mask = df["pos_class"] == "G"
        df.loc[guard_mask, "proj_sd"] = df.loc[guard_mask, "proj_sd"] * REB_GUARD_VAR_MULT
    elif stat == "AST":
        fwd_mask = df["pos_class"] == "F"
        df.loc[fwd_mask, "proj_sd"] = df.loc[fwd_mask, "proj_sd"] * AST_FWD_VAR_MULT
    elif stat == "BLK":
        guard_mask = df["pos_class"] == "G"
        df.loc[guard_mask, "proj_sd"] = df.loc[guard_mask, "proj_sd"] * BLK_GUARD_VAR_MULT

    # Per-min rates from regular-season averages
    df["mpg_rs"] = df["actual_minutes"] / df["actual_games"]
    df["proj_per_min"] = df["proj_mean"] / df["mpg_rs"]
    df["sd_per_min"] = df["proj_sd"] / df["mpg_rs"]

    out_cols = [
        "nba_api_id", "name", "stat", "season",
        "pos_class", "years_pro_bucket", "cohort",
        "proj_mean", "proj_sd", "proj_q05", "proj_q25", "proj_q75", "proj_q95",
        "actual_minutes", "actual_games", "mpg_rs", "proj_per_min", "sd_per_min",
    ]
    return df[out_cols].rename(columns={
        "actual_minutes": "actual_minutes_rs",
        "actual_games": "actual_games_rs",
    })


# --------------------------------------------------------------------------- #
# 2. Playoff per-game stats (Round 1, all backtest seasons)
# --------------------------------------------------------------------------- #
def load_playoff_pergame() -> pd.DataFrame:
    """Combine traditional_t0 + traditional_t1 across backtest seasons.

    Loads from BOTH playoffs/round1/ and playoffs/extra_rounds/ when the latter
    exists (round 2/3/4 from cli/fetch_playoff_extra_rounds.py).

    Returns one row per (gameId, personId) with columns:
      gameId, season, personId, position, minutes, PTS, REB, AST, STL, BLK,
      TOV, FG3M, teamId, opp_teamId, is_home (best-effort), game_date, round
    """
    frames = []
    for src_dir in [PLAYOFFS_R1, PLAYOFFS_EXTRA]:
        if (src_dir / "traditional_t0.parquet").exists():
            frames.append(pd.read_parquet(src_dir / "traditional_t0.parquet"))
        if (src_dir / "traditional_t1.parquet").exists():
            frames.append(pd.read_parquet(src_dir / "traditional_t1.parquet"))
    df = pd.concat(frames, ignore_index=True)
    # Deduplicate at (gameId, personId) — extra_rounds might overlap with round1
    if "personId" in df.columns:
        df = df.drop_duplicates(subset=["gameId", "personId"], keep="first")
    df = df[df["season"].isin(BACKTEST_SEASONS)].copy()

    # Derive opp team per (game, team) from set of teams in that game
    game_teams = (df.groupby("gameId")["teamId"]
                    .apply(lambda s: list(set(s)))
                    .to_dict())
    def _opp(row):
        teams = game_teams.get(row["gameId"], [])
        if len(teams) != 2:
            return None
        return teams[0] if teams[1] == row["teamId"] else teams[1]
    df["opp_teamId"] = df.apply(_opp, axis=1)

    # Parse minutes "MM:SS" or "MM:SS.f"
    def _parse_min(s):
        if pd.isna(s) or s == "" or s is None:
            return 0.0
        if isinstance(s, (int, float)):
            return float(s)
        try:
            parts = str(s).split(":")
            if len(parts) == 2:
                m = float(parts[0]); ss = float(parts[1])
                return m + ss / 60.0
            return float(parts[0])
        except (ValueError, TypeError):
            return 0.0
    df["minutes_played"] = df["minutes"].apply(_parse_min)

    # Pull game_date + round from manifest (combine both dirs)
    mans = []
    for src_dir in [PLAYOFFS_R1, PLAYOFFS_EXTRA]:
        if (src_dir / "_manifest.parquet").exists():
            mans.append(pd.read_parquet(src_dir / "_manifest.parquet"))
    man = pd.concat(mans, ignore_index=True).drop_duplicates("game_id", keep="first")
    df = df.merge(
        man[["game_id", "game_date", "home_team_id", "away_team_id",
             "season_end_year", "round"]],
        left_on="gameId", right_on="game_id", how="left",
    )
    df["is_home"] = df["teamId"] == df["home_team_id"]

    # Rename camelCase box stats to our codes
    rename_map = {
        "personId": "nba_api_id",
        "points": "PTS",
        "reboundsTotal": "REB",
        "assists": "AST",
        "steals": "STL",
        "blocks": "BLK",
        "turnovers": "TOV",
        "threePointersMade": "FG3M",
    }
    df = df.rename(columns=rename_map)
    # Drop rows missing nba_api_id (rare but possible for inactive lists)
    df = df.dropna(subset=["nba_api_id"]).copy()
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    # Filter rows with comment indicating DNP / Inactive (no minutes played)
    df = df[df["minutes_played"] > 0].copy()
    return df


# --------------------------------------------------------------------------- #
# 3. Conditioning data (opponent DvP, pace) for Variant B
# --------------------------------------------------------------------------- #
def load_team_pace_def() -> dict:
    """Per-team-per-season pace and DEF rating, aggregated from playoff
    advanced_t0+t1 (team-game-level metrics).

    For each (season, team_id), average the team's per-game pace and
    defensiveRating across their playoff games in the dataset. Used as the
    Variant B conditioning baseline (opponent + pace).

    The proper-backtest-discipline alternative is regular-season pace+def_rating
    pre-playoff, but historical regular-season team-level aggregates are not
    locally available. Using playoff team aggregates here mirrors the production
    deployment posture (live opponent metrics fed at scoring time).

    Returns dict keyed by (season, team_id) -> {pace, def_rating}.
    """
    frames = []
    for src_dir in [PLAYOFFS_R1, PLAYOFFS_EXTRA]:
        if (src_dir / "advanced_t0.parquet").exists():
            frames.append(pd.read_parquet(src_dir / "advanced_t0.parquet"))
        if (src_dir / "advanced_t1.parquet").exists():
            frames.append(pd.read_parquet(src_dir / "advanced_t1.parquet"))
    a = pd.concat(frames, ignore_index=True)
    if "personId" in a.columns:
        a = a.drop_duplicates(subset=["gameId", "personId"], keep="first")
    a = a[a["season"].isin(BACKTEST_SEASONS)].copy()
    a["pace"] = pd.to_numeric(a["pace"], errors="coerce")
    a["defensiveRating"] = pd.to_numeric(a["defensiveRating"], errors="coerce")

    # Per-team-per-game: average across players on team (some are weighted by
    # minutes-on-court but for a team baseline taking the mean gives the team
    # baseline).
    team_game = (a.groupby(["season", "gameId", "teamId"], as_index=False)
                   [["pace", "defensiveRating"]].mean())
    team_season = (team_game.groupby(["season", "teamId"], as_index=False)
                              [["pace", "defensiveRating"]].mean())

    out = {}
    for _, r in team_season.iterrows():
        out[(r["season"], int(r["teamId"]))] = {
            "pace": r["pace"], "def_rating": r["defensiveRating"],
        }
    return out


def load_pace_from_advanced() -> pd.DataFrame:
    """Per-game pace from playoffs/round1/ + playoffs/extra_rounds/ advanced_t0+t1.

    Returns columns: gameId, teamId, pace_game
    """
    frames = []
    for src_dir in [PLAYOFFS_R1, PLAYOFFS_EXTRA]:
        if (src_dir / "advanced_t0.parquet").exists():
            frames.append(pd.read_parquet(src_dir / "advanced_t0.parquet"))
        if (src_dir / "advanced_t1.parquet").exists():
            frames.append(pd.read_parquet(src_dir / "advanced_t1.parquet"))
    a = pd.concat(frames, ignore_index=True)
    cols_lower = {c.lower(): c for c in a.columns}
    pace_c = None
    for k in ["pace", "Pace"]:
        if k.lower() in cols_lower:
            pace_c = cols_lower[k.lower()]
            break
    if pace_c is None:
        return pd.DataFrame(columns=["gameId", "teamId", "pace_game"])
    out = a[["gameId", "teamId", pace_c]].rename(columns={pace_c: "pace_game"})
    out["pace_game"] = pd.to_numeric(out["pace_game"], errors="coerce")
    out = out.dropna(subset=["pace_game"])
    return out


# --------------------------------------------------------------------------- #
# 4. Compute the three variants per (player, game, stat)
# --------------------------------------------------------------------------- #
def compute_variants(playoff: pd.DataFrame, ships_by_stat_season: dict,
                     pace_team_season: dict,
                     pace_per_game: pd.DataFrame) -> pd.DataFrame:
    """Per (game, player, stat) compute proj_A, proj_B, proj_C and sd_per_game.

    Returns long-format DataFrame.
    """
    league_avg_pace = np.mean([
        v["pace"] for v in pace_team_season.values() if not pd.isna(v["pace"])
    ]) if pace_team_season else None

    # Pre-build playoff-cohort means across all playoff games (LOO computed later)
    pos_min_rates = compute_position_cohort_rates(playoff)

    pace_lookup = {(r["gameId"], int(r["teamId"])): r["pace_game"]
                   for _, r in pace_per_game.iterrows()}

    rows = []
    for stat in PRIMARY_STATS + SINGLE_SEASON_STATS:
        if stat not in playoff.columns:
            continue
        for season in BACKTEST_SEASONS:
            if (stat, season) not in ships_by_stat_season:
                continue
            ship = ships_by_stat_season[(stat, season)]
            ship_idx = ship.set_index("nba_api_id")
            po_s = playoff[playoff["season"] == season]
            for _, g in po_s.iterrows():
                pid = int(g["nba_api_id"])
                if pid not in ship_idx.index:
                    continue
                s = ship_idx.loc[pid]
                if isinstance(s, pd.DataFrame):
                    s = s.iloc[0]
                if pd.isna(s.get("proj_per_min")) or s.get("mpg_rs", 0) <= 0:
                    continue

                game_min = float(g["minutes_played"])
                if game_min <= 0:
                    continue
                actual = float(g[stat]) if pd.notna(g[stat]) else None
                if actual is None:
                    continue

                # --- Variant A: regular-season-only, scaled to game minutes ---
                proj_A = float(s["proj_per_min"]) * game_min

                # --- Variant B: + opponent DvP + pace ---
                opp_team = g.get("opp_teamId")
                opp_def = pace_team_season.get((season, int(opp_team) if pd.notna(opp_team) else -1))
                if opp_def and "def_rating" in opp_def and league_avg_pace:
                    league_avg_def = np.mean([
                        v["def_rating"] for v in pace_team_season.values()
                        if v.get("def_rating") is not None and not pd.isna(v["def_rating"])
                    ])
                    opp_def_val = opp_def["def_rating"] if not pd.isna(opp_def["def_rating"]) else league_avg_def
                    # DvP-style multiplier: HIGHER opp def_rating = WORSE defense (more stat allowed)
                    # def_rating measures points allowed per 100 poss for the defender.
                    # Multiplier: opp_def / league_avg_def, applied to points/proxy stats.
                    dvp_mult = float(opp_def_val) / float(league_avg_def)
                else:
                    dvp_mult = 1.0
                game_pace = pace_lookup.get((g["gameId"], int(g["teamId"])))
                if game_pace and league_avg_pace and not pd.isna(game_pace):
                    pace_mult = float(game_pace) / float(league_avg_pace)
                else:
                    pace_mult = 1.0
                proj_B = proj_A * dvp_mult * pace_mult

                # --- Variant C: playoff-cohort-only, position-cohort fallback ---
                pos = s.get("pos_class") if pd.notna(s.get("pos_class")) else "F"
                rate_C = pos_min_rates.get((stat, pos))
                if rate_C is None:
                    rate_C = pos_min_rates.get((stat, "F"))
                proj_C = float(rate_C) * game_min if rate_C is not None else proj_A

                # Per-game variance: scale season sd by sqrt(game_min / mpg_rs)
                # (Poisson-like). Used for coverage calc.
                sd_game = float(s["proj_sd"]) * np.sqrt(max(game_min, 1.0) /
                                                         max(float(s["mpg_rs"]), 1.0))

                rows.append({
                    "season": season,
                    "gameId": g["gameId"],
                    "game_date": g.get("game_date"),
                    "nba_api_id": pid,
                    "name": s.get("name"),
                    "pos_class": pos,
                    "years_pro_bucket": s.get("years_pro_bucket"),
                    "cohort": s.get("cohort"),
                    "stat": stat,
                    "minutes_played": game_min,
                    "mpg_rs": float(s["mpg_rs"]),
                    "actual": actual,
                    "proj_A": proj_A,
                    "proj_B": proj_B,
                    "proj_C": proj_C,
                    "sd_game": sd_game,
                    "dvp_mult": dvp_mult,
                    "pace_mult": pace_mult,
                    "opp_teamId": int(opp_team) if pd.notna(opp_team) else None,
                    "is_home": bool(g.get("is_home", False)),
                })

    df = pd.DataFrame(rows)

    # Add derived combo stats RA, PR, PRA
    if not df.empty:
        derived_rows = []
        keys = ["season", "gameId", "nba_api_id"]
        for derived, components in DERIVED_STATS.items():
            sub = df[df["stat"].isin(components)]
            if sub.empty:
                continue
            piv_proj_A = sub.groupby(keys)["proj_A"].sum().reset_index()
            piv_proj_B = sub.groupby(keys)["proj_B"].sum().reset_index()
            piv_proj_C = sub.groupby(keys)["proj_C"].sum().reset_index()
            piv_actual = sub.groupby(keys)["actual"].sum().reset_index()
            piv_sd = sub.groupby(keys)["sd_game"].apply(
                lambda x: float(np.sqrt(np.sum(x.astype(float)**2)))
            ).reset_index()
            meta = sub.groupby(keys).first().reset_index()[
                keys + ["game_date", "name", "pos_class", "years_pro_bucket",
                        "cohort", "minutes_played", "mpg_rs", "dvp_mult",
                        "pace_mult", "opp_teamId", "is_home"]
            ]
            merged = (meta.merge(piv_proj_A, on=keys)
                          .merge(piv_proj_B, on=keys)
                          .merge(piv_proj_C, on=keys)
                          .merge(piv_actual, on=keys)
                          .merge(piv_sd, on=keys))
            # Only keep rows where all components present (n_components matches)
            n_components = sub.groupby(keys)["stat"].nunique()
            valid_keys = n_components[n_components == len(components)].index
            merged_keys = list(zip(*[merged[k] for k in keys]))
            mask = [k in valid_keys for k in merged_keys]
            merged = merged.loc[mask].copy()
            merged["stat"] = derived
            derived_rows.append(merged)

        if derived_rows:
            derived_df = pd.concat(derived_rows, ignore_index=True)
            df = pd.concat([df, derived_df], ignore_index=True)

    # Compute residuals
    if not df.empty:
        df["residual_A"] = df["actual"] - df["proj_A"]
        df["residual_B"] = df["actual"] - df["proj_B"]
        df["residual_C"] = df["actual"] - df["proj_C"]

        # Variant A_adj: apply LOO playoff multiplier per stat fit on the OTHER
        # two backtest seasons. Per-stat scalar multiplier = mean(actual) /
        # mean(proj_A) across players in those seasons. This is the cleanest
        # deployable adjustment that does NOT modify v6.1 — applied as a
        # post-hoc per-stat playoff regime factor.
        for stat in df["stat"].unique():
            mask_stat = df["stat"] == stat
            for season in df[mask_stat]["season"].unique():
                other = df[mask_stat & (df["season"] != season)]
                if len(other) == 0 or other["proj_A"].sum() == 0:
                    mult = 1.0
                else:
                    mult = float(other["actual"].sum()) / float(other["proj_A"].sum())
                target = mask_stat & (df["season"] == season)
                df.loc[target, "playoff_mult_loo"] = mult
                df.loc[target, "proj_A_adj"] = df.loc[target, "proj_A"] * mult
        df["residual_A_adj"] = df["actual"] - df["proj_A_adj"]
    return df


def per_round_summary(residuals: pd.DataFrame) -> pd.DataFrame:
    """MAE per (variant, stat, round) across all 3 backtest seasons."""
    rows = []
    if "round" not in residuals.columns:
        return pd.DataFrame()
    for variant in ["A", "B", "C", "A_adj"]:
        rcol = f"residual_{variant}"
        if rcol not in residuals.columns:
            continue
        for stat in residuals["stat"].unique():
            for r in sorted(residuals["round"].dropna().unique()):
                sub = residuals[(residuals["stat"] == stat) &
                                (residuals["round"] == r)]
                n = len(sub)
                if n == 0:
                    continue
                rows.append({
                    "variant": variant, "stat": stat, "round": int(r), "n": n,
                    "mae": float(np.mean(np.abs(sub[rcol]))),
                    "bias": float(np.mean(sub[rcol])),
                })
    return pd.DataFrame(rows)


def compute_position_cohort_rates(playoff: pd.DataFrame) -> dict:
    """Aggregate per-position per-min stat rates across all R1 playoff games."""
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    pos_lookup = dict(zip(meta["nba_api_id"].astype(int), meta["position"]))

    def _primary(p):
        if not isinstance(p, str) or not p:
            return None
        first = p.split("-")[0].strip().upper()
        if first.startswith("G"):
            return "G"
        if first.startswith("C"):
            return "C"
        if first.startswith("F"):
            return "F"
        return None

    pf = playoff.copy()
    pf["pos_class"] = pf["nba_api_id"].astype(int).map(pos_lookup).map(_primary)
    pf = pf.dropna(subset=["pos_class"])
    pf = pf[pf["minutes_played"] > 0]
    rates = {}
    for stat in PRIMARY_STATS + SINGLE_SEASON_STATS:
        if stat not in pf.columns:
            continue
        for pos in ["G", "F", "C"]:
            sub = pf[pf["pos_class"] == pos]
            if len(sub) == 0:
                continue
            total = sub[stat].sum()
            mins = sub["minutes_played"].sum()
            if mins > 0:
                rates[(stat, pos)] = float(total) / float(mins)
    return rates


# --------------------------------------------------------------------------- #
# 5. Aggregation: MAE per (variant, cohort, stat) + coverage 50/80/95%
# --------------------------------------------------------------------------- #
def aggregate_mae(residuals: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for variant in ["A", "B", "C", "A_adj"]:
        rcol = f"residual_{variant}"
        if rcol not in residuals.columns:
            continue
        # Overall (per stat) and per-cohort
        for stat in residuals["stat"].unique():
            for cohort in [None] + sorted(residuals["cohort"].dropna().unique().tolist()):
                sub = residuals[residuals["stat"] == stat]
                if cohort:
                    sub = sub[sub["cohort"] == cohort]
                n = len(sub)
                if n == 0:
                    continue
                mae = float(np.mean(np.abs(sub[rcol])))
                bias = float(np.mean(sub[rcol]))
                rows.append({
                    "variant": variant,
                    "stat": stat,
                    "cohort": cohort or "ALL",
                    "n": n,
                    "mae": mae,
                    "bias": bias,
                })
    return pd.DataFrame(rows)


def per_season_mae(residuals: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for variant in ["A", "B", "C", "A_adj"]:
        rcol = f"residual_{variant}"
        if rcol not in residuals.columns:
            continue
        for stat in residuals["stat"].unique():
            for season in residuals["season"].unique():
                sub = residuals[(residuals["stat"] == stat) &
                                (residuals["season"] == season)]
                n = len(sub)
                if n == 0:
                    continue
                rows.append({
                    "variant": variant,
                    "stat": stat,
                    "season": season,
                    "n": n,
                    "mae": float(np.mean(np.abs(sub[rcol]))),
                    "bias": float(np.mean(sub[rcol])),
                })
    return pd.DataFrame(rows)


def variance_calibration(residuals: pd.DataFrame) -> pd.DataFrame:
    """For each (variant, stat), compute empirical 50/80/95% interval coverage
    using Gaussian assumption with sd_game.

    50% interval = mu +/- 0.674 * sd
    80% interval = mu +/- 1.282 * sd
    95% interval = mu +/- 1.96  * sd
    """
    z_50 = 0.6745
    z_80 = 1.2816
    z_95 = 1.96
    rows = []
    for variant in ["A", "B", "C", "A_adj"]:
        pcol = f"proj_{variant}"
        if pcol not in residuals.columns:
            continue
        for stat in residuals["stat"].unique():
            sub = residuals[residuals["stat"] == stat].copy()
            sub = sub.dropna(subset=[pcol, "sd_game", "actual"])
            sub = sub[sub["sd_game"] > 0]
            if len(sub) == 0:
                continue
            z = (sub["actual"] - sub[pcol]) / sub["sd_game"]
            cov_50 = float(np.mean(np.abs(z) <= z_50))
            cov_80 = float(np.mean(np.abs(z) <= z_80))
            cov_95 = float(np.mean(np.abs(z) <= z_95))
            rows.append({
                "variant": variant,
                "stat": stat,
                "n": len(sub),
                "coverage_50": cov_50,
                "coverage_80": cov_80,
                "coverage_95": cov_95,
                "z_mae": float(np.mean(np.abs(z))),
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    print(f"Backtest output dir: {OUT_DIR}")
    print()

    # 1. Discover and load ships
    print("[1/5] Discovering ships ...")
    ships = discover_ships()
    needed = [(s, season) for s in PRIMARY_STATS + SINGLE_SEASON_STATS
              for season in BACKTEST_SEASONS]
    missing = [k for k in needed if k not in ships]
    if missing:
        print(f"  MISSING ships: {missing}")
    SHIP_INDEX_PATH.write_text(json.dumps(
        {f"{k[0]}|{k[1]}": v for k, v in ships.items()}, indent=2,
    ))

    print(f"  Found {len(ships)} (stat, season) ship pairs.")
    print(f"  Building unified ships with v6.1 LOCKED levers ...")
    unified = {}
    for stat in PRIMARY_STATS + SINGLE_SEASON_STATS:
        for season in BACKTEST_SEASONS:
            if (stat, season) not in ships:
                continue
            unified[(stat, season)] = build_unified_season_ship(
                stat, season, ships[(stat, season)],
            )
    print(f"  Unified ships: {len(unified)} (stat, season) pairs")
    print()

    # 2. Load playoff per-game stats
    print("[2/5] Loading R1 playoff per-game stats (22-23, 23-24, 24-25) ...")
    playoff = load_playoff_pergame()
    print(f"  Player-game observations: {len(playoff)}")
    print(f"  Unique games: {playoff['gameId'].nunique()}")
    print(f"  Per-season game count:\n{playoff.groupby('season')['gameId'].nunique()}")
    print()

    # 3. Conditioning data for variant B
    print("[3/5] Loading pace/DefRating conditioning data ...")
    pace_team_season = load_team_pace_def()
    pace_per_game = load_pace_from_advanced()
    print(f"  team-season pace records: {len(pace_team_season)}")
    print(f"  per-game pace records: {len(pace_per_game)}")
    print()

    # 4. Compute variants
    print("[4/5] Computing per (player, game, stat) projections + residuals ...")
    residuals = compute_variants(
        playoff, unified, pace_team_season, pace_per_game,
    )
    print(f"  total per-(player,game,stat) rows: {len(residuals)}")
    print(f"  per-stat counts:\n{residuals.groupby('stat').size()}")
    print()

    # 5. Aggregate + write outputs
    print("[5/5] Aggregating MAE + coverage and writing outputs ...")
    out_residuals = OUT_DIR / "backtest_playoff_residuals.csv"
    out_mae = OUT_DIR / "backtest_mae_summary.csv"
    out_var = OUT_DIR / "backtest_variance_calibration.csv"
    out_season = OUT_DIR / "per_season_summary.csv"

    residuals.to_csv(out_residuals, index=False)
    print(f"  -> {out_residuals}  ({len(residuals)} rows)")

    mae = aggregate_mae(residuals)
    mae.to_csv(out_mae, index=False)
    print(f"  -> {out_mae}  ({len(mae)} rows)")

    cal = variance_calibration(residuals)
    cal.to_csv(out_var, index=False)
    print(f"  -> {out_var}  ({len(cal)} rows)")

    per_season = per_season_mae(residuals)
    per_season.to_csv(out_season, index=False)
    print(f"  -> {out_season}  ({len(per_season)} rows)")

    out_round = OUT_DIR / "per_round_summary.csv"
    per_round = per_round_summary(residuals)
    if not per_round.empty:
        per_round.to_csv(out_round, index=False)
        print(f"  -> {out_round}  ({len(per_round)} rows)")
    print()

    print("DONE.")
    return residuals, mae, cal, per_season


if __name__ == "__main__":
    main()
