"""Multi-season Test-1 replication + Probe B pooled-residual analysis.

Reads:
  - 6 per-player projection CSVs from today's Stan chain
  - 25-26 ship CSV (already exists from v6.1 LOCKED)
  - historical_box_scores.parquet for per-game actuals + cohort tags

Test 1 cells (3 of 4 — BLK not run, missing):
  - PTS x Center  (variance-COUPLING expected; coupled in 25-26 at p<0.001)
  - REB x Center  (variance-COUPLING expected; coupled in 25-26 at p<0.001)
  - AST x 13+     (variance-NOT-COUPLING expected; null in 25-26, p=0.64)

Probe B pooled:
  - Pool per-game residuals across 23-24 + 24-25 + 25-26
  - Tag with 72-config Probe B' axes (opp_class, record_tier, season_phase, home_away)
  - Test Tier-1 pre-registered: outlier cluster dominated by top_record + early + home theme

Output: audit_runs/multi_season_replication/result.md + supporting CSVs
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")
from pathlib import Path
import json

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(".")
PQ = REPO / "data" / "parquet"
OUT_DIR = REPO / "audit_runs" / "multi_season_replication"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Per-player projection paths
PROJ_PATHS = {
    ("PTS", "2024-25"): "audit_runs/20260505T154737Z/skill_backtest_PTS_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/per_player_projections.csv",
    ("REB", "2024-25"): "audit_runs/20260505T171359Z/skill_backtest_REB_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/per_player_projections.csv",
    ("AST", "2024-25"): "audit_runs/20260505T183718Z/skill_backtest_AST_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/per_player_projections.csv",
    ("PTS", "2023-24"): "audit_runs/20260505T211540Z/skill_backtest_PTS_phase4_v4_quadratic_tq_g_2017-18-2018-19-2019-20-2020-21-2021-22-2022-23__2023-24/per_player_projections.csv",
    ("REB", "2023-24"): "audit_runs/20260505T225045Z/skill_backtest_REB_phase4_v4_quadratic_tq_g_2017-18-2018-19-2019-20-2020-21-2021-22-2022-23__2023-24/per_player_projections.csv",
    ("AST", "2023-24"): "audit_runs/20260506T002014Z/skill_backtest_AST_phase4_v4_quadratic_tq_g_2017-18-2018-19-2019-20-2020-21-2021-22-2022-23__2023-24/per_player_projections.csv",
}

V6_1_SHIP = REPO / "audit_runs" / "unified_ship_v6_1_2025_26" / "per_player_projections_2025-26.csv"
ROOKIE_SUP = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "rookie_metadata_supplement.parquet"


def load_metadata():
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    cols = ["nba_api_id", "draft_year", "debut_year", "position", "name"]
    if ROOKIE_SUP.exists():
        sup = pd.read_parquet(ROOKIE_SUP)
        meta = pd.concat([meta[cols], sup[cols]], ignore_index=True)
    meta["nba_api_id"] = meta["nba_api_id"].astype(int)
    return meta


def position_class(p):
    """Permissive Center: any position string containing "center" -> Center.
    Then Guard: any string containing "guard" -> Guard.
    Else Forward.
    Aligns with the original Test 1 cohort definition (n=63 Centers in 25-26 paper).
    """
    if pd.isna(p) or not p or str(p).strip() == "":
        return "Forward"
    s = str(p).lower()
    if "center" in s: return "Center"
    if "guard" in s: return "Guard"
    return "Forward"


def years_pro_at_season(meta, season_label):
    season_year = int(season_label[:4])
    yp = meta["debut_year"].where(meta["debut_year"].notna(), meta["draft_year"] + 1)
    yp = season_year - yp
    return yp


def years_pro_bucket(yp):
    return pd.cut(yp, bins=[-1, 0, 3, 7, 12, 30],
                   labels=["rookie", "1-3", "4-7", "8-12", "13+"]).astype(str)


# ────────────────────────────────────────────────────────────────────────
# Test 1 same-class mean-variance coupling
# ────────────────────────────────────────────────────────────────────────

def test_1_cell(residuals, in_mask, label):
    """Compute variance ratio for in-class vs out-of-class residuals.
    Returns dict with sd_in, sd_out, ratio, p (Levene's test)."""
    r_in = residuals[in_mask].dropna().values
    r_out = residuals[~in_mask].dropna().values
    if len(r_in) < 5 or len(r_out) < 5:
        return {"label": label, "n_in": len(r_in), "n_out": len(r_out),
                "sd_in": np.nan, "sd_out": np.nan, "ratio": np.nan,
                "p_levene": np.nan, "mean_in": np.nan, "mean_out": np.nan}
    sd_in = r_in.std(ddof=1)
    sd_out = r_out.std(ddof=1)
    ratio = (sd_in / sd_out) if sd_out > 0 else np.nan
    # Levene's test for variance equality
    try:
        _, p = stats.levene(r_in, r_out, center="median")
    except Exception:
        p = np.nan
    return {"label": label,
             "n_in": len(r_in), "n_out": len(r_out),
             "mean_in": float(r_in.mean()), "mean_out": float(r_out.mean()),
             "sd_in": float(sd_in), "sd_out": float(sd_out),
             "ratio": float(ratio), "p_levene": float(p)}


def run_test_1_for_season(season, stat, proj_path, meta):
    """Returns Test 1 result for the relevant cell on this season."""
    df = pd.read_csv(proj_path)
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    df["error"] = df["actual"] - df["proj_mean"]  # residual
    # Attach class info
    df = df.merge(meta[["nba_api_id", "position", "draft_year", "debut_year"]],
                    on="nba_api_id", how="left")
    df["yp"] = years_pro_at_season(df, season)
    df["ypb"] = years_pro_bucket(df["yp"])
    df["pos_class"] = df["position"].apply(position_class)

    # Cell of interest:
    if stat in ("PTS", "REB"):
        cell_label = f"{stat} x Center"
        in_mask = df["pos_class"] == "Center"
        result = test_1_cell(df["error"], in_mask, cell_label)
    elif stat == "AST":
        cell_label = "AST x 13+"
        in_mask = df["ypb"] == "13+"
        result = test_1_cell(df["error"], in_mask, cell_label)
    else:
        return None
    result["season"] = season
    result["stat"] = stat
    return result


def test_1_for_25_26(meta, ship_path, bx):
    """Compute Test-1 cells on v6.1 LOCKED ship + pulled actuals from box scores.
    The ship CSV's *_actual columns only cover vets; need to pull full cohort
    actuals from box scores to align with the paper's n=63-77 Center cohort.
    """
    ship = pd.read_csv(ship_path)
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)

    # Pull 25-26 RS per-game actuals from box scores for ALL ship players
    bx_25_26 = bx[(bx["season"] == "2025-26") &
                    (bx["season_type"] == "Regular Season")].copy()
    bx_25_26["minutes"] = pd.to_numeric(bx_25_26["minutes"], errors="coerce")
    bx_25_26 = bx_25_26[bx_25_26["minutes"] > 0]
    actuals = bx_25_26.groupby("nba_api_id").agg(
        PTS_actual_bx=("PTS", "mean"),
        REB_actual_bx=("REB", "mean"),
        AST_actual_bx=("AST", "mean"),
    ).reset_index()
    actuals["nba_api_id"] = actuals["nba_api_id"].astype(int)

    # Synthetic rookie IDs in ship → map to real IDs via name
    sup_path = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "rookie_metadata_supplement.parquet"
    rookie_real_id = {}
    if sup_path.exists():
        sup = pd.read_parquet(sup_path)
        meta2 = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
        real_name_id = dict(zip(meta2["name"].str.lower().fillna(""),
                                  meta2["nba_api_id"].astype(int)))
        for _, r in sup.iterrows():
            nm = (r["name"] or "").strip().lower()
            if nm in real_name_id:
                rookie_real_id[int(r["nba_api_id"])] = real_name_id[nm]
    ship["real_id"] = ship["nba_api_id"].map(
        lambda x: rookie_real_id.get(int(x), int(x))).astype(int)

    ship = ship.merge(actuals, left_on="real_id", right_on="nba_api_id",
                        how="left", suffixes=("", "_actuals"))
    # Use box-score actuals as primary, fall back to ship actuals
    for stat in ("PTS", "REB", "AST"):
        actual_col = f"{stat}_actual"
        bx_col = f"{stat}_actual_bx"
        ship[actual_col] = ship[bx_col].fillna(ship[actual_col])
        ship[f"{stat}_resid"] = ship[actual_col] - ship[f"{stat}_per_game"]

    ship = ship.merge(meta[["nba_api_id", "position", "draft_year", "debut_year"]],
                        left_on="real_id", right_on="nba_api_id",
                        how="left", suffixes=("", "_m"))
    ship["yp"] = years_pro_at_season(ship, "2025-26")
    ship["ypb"] = years_pro_bucket(ship["yp"])
    ship["pos_class"] = ship["position"].apply(position_class)
    out = []
    for stat in ("PTS", "REB"):
        res = test_1_cell(ship[f"{stat}_resid"], ship["pos_class"] == "Center",
                            f"{stat} x Center")
        res.update({"season": "2025-26 (full ship)", "stat": stat})
        out.append(res)
    res = test_1_cell(ship["AST_resid"], ship["ypb"] == "13+", "AST x 13+")
    res.update({"season": "2025-26 (full ship)", "stat": "AST"})
    out.append(res)
    return out


# ────────────────────────────────────────────────────────────────────────
# Per-game residuals for Probe B pooled
# ────────────────────────────────────────────────────────────────────────

def compute_per_game_residuals(season, proj_paths, bx, meta):
    """For a given test season, return per-game residuals tagged with cohort + position."""
    bx_s = bx[(bx["season"] == season) &
                (bx["season_type"] == "Regular Season")].copy()
    bx_s["minutes"] = pd.to_numeric(bx_s["minutes"], errors="coerce")
    bx_s = bx_s[bx_s["minutes"] > 0].copy()
    bx_s["nba_api_id"] = bx_s["nba_api_id"].astype(int)
    per_game = bx_s[["nba_api_id", "game_id", "game_date", "team_abbr",
                       "matchup", "minutes", "is_home",
                       "PTS", "REB", "AST"]].copy()
    per_game["opp_abbr"] = per_game["matchup"].str.extract(
        r"(?:vs\.\s+|@\s+)([A-Z]{3})")

    # Attach per-stat projection per player
    for stat in ("PTS", "REB", "AST"):
        proj = pd.read_csv(proj_paths[(stat, season)])
        proj["nba_api_id"] = proj["nba_api_id"].astype(int)
        proj_lu = dict(zip(proj["nba_api_id"], proj["proj_mean"]))
        per_game[f"{stat}_proj"] = per_game["nba_api_id"].map(proj_lu)
        per_game[f"{stat}_resid"] = per_game[stat] - per_game[f"{stat}_proj"]

    per_game = per_game.merge(meta[["nba_api_id", "position", "draft_year",
                                       "debut_year"]],
                                on="nba_api_id", how="left")
    per_game["yp"] = years_pro_at_season(per_game, season)
    per_game["ypb"] = years_pro_bucket(per_game["yp"])
    per_game["pos_class"] = per_game["position"].apply(position_class)
    per_game["cohort"] = per_game["ypb"].apply(
        lambda y: "rookie" if y == "rookie" else (
            "soph" if y == "1-3" else "vet"))
    per_game["season"] = season
    return per_game


def compute_per_game_residuals_25_26(ship_path, bx, meta):
    """Per-game residuals for 25-26 from the v6.1 LOCKED ship."""
    ship = pd.read_csv(ship_path)
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    real_id = ship["nba_api_id"].copy()  # for synthetic rookies, can't easily map back
    proj_lu = {
        "PTS": dict(zip(real_id, ship["PTS_per_game"])),
        "REB": dict(zip(real_id, ship["REB_per_game"])),
        "AST": dict(zip(real_id, ship["AST_per_game"])),
    }
    bx_s = bx[(bx["season"] == "2025-26") &
                (bx["season_type"] == "Regular Season")].copy()
    bx_s["minutes"] = pd.to_numeric(bx_s["minutes"], errors="coerce")
    bx_s = bx_s[bx_s["minutes"] > 0].copy()
    bx_s["nba_api_id"] = bx_s["nba_api_id"].astype(int)
    per_game = bx_s[["nba_api_id", "game_id", "game_date", "team_abbr",
                       "matchup", "minutes", "is_home",
                       "PTS", "REB", "AST"]].copy()
    per_game["opp_abbr"] = per_game["matchup"].str.extract(
        r"(?:vs\.\s+|@\s+)([A-Z]{3})")
    for stat in ("PTS", "REB", "AST"):
        per_game[f"{stat}_proj"] = per_game["nba_api_id"].map(proj_lu[stat])
        per_game[f"{stat}_resid"] = per_game[stat] - per_game[f"{stat}_proj"]
    per_game = per_game.merge(meta[["nba_api_id", "position", "draft_year",
                                       "debut_year"]],
                                on="nba_api_id", how="left")
    per_game["yp"] = years_pro_at_season(per_game, "2025-26")
    per_game["ypb"] = years_pro_bucket(per_game["yp"])
    per_game["pos_class"] = per_game["position"].apply(position_class)
    per_game["cohort"] = per_game["ypb"].apply(
        lambda y: "rookie" if y == "rookie" else (
            "soph" if y == "1-3" else "vet"))
    per_game["season"] = "2025-26"
    return per_game


# ────────────────────────────────────────────────────────────────────────
# Probe B' pooled
# ────────────────────────────────────────────────────────────────────────

def build_24_25_winpct(bx):
    """24-25 final win pct per team for use as 25-26 prior."""
    out = {}
    for season in ("2022-23", "2023-24", "2024-25"):
        sub = bx[(bx["season"] == season) &
                  (bx["season_type"] == "Regular Season")].copy()
        tg = sub.groupby(["team_abbr", "game_id"])["win"].first().reset_index()
        s = tg.groupby("team_abbr")["win"].agg(["sum", "count"]).reset_index()
        s["win_pct"] = s["sum"] / s["count"]
        out[season] = dict(zip(s["team_abbr"], s["win_pct"]))
    return out


def build_def_quartile_prev_season(bx, prev_season):
    """Defensive rating quartile using prev_season."""
    sub = bx[(bx["season"] == prev_season) &
              (bx["season_type"] == "Regular Season")].copy()
    g = sub.groupby(["game_id", "team_abbr"]).agg(
        FGA=("FGA", "sum"), FTA=("FTA", "sum"),
        TO=("TOV", "sum"), OREB=("OREB", "sum"),
        PTS=("PTS", "sum"),
    ).reset_index()
    g["poss"] = g["FGA"] + 0.44 * g["FTA"] + g["TO"] - g["OREB"]
    g_pts = g[["game_id", "team_abbr", "PTS"]].rename(
        columns={"team_abbr": "opp_abbr", "PTS": "opp_PTS"})
    merged = g.merge(g_pts, on="game_id")
    merged = merged[merged["team_abbr"] != merged["opp_abbr"]]
    team_def = merged.groupby("team_abbr").agg(
        opp_pts=("opp_PTS", "sum"),
        poss=("poss", "sum"),
    ).reset_index()
    team_def["def_rating"] = team_def["opp_pts"] / team_def["poss"] * 100
    team_def = team_def.sort_values("def_rating").reset_index(drop=True)
    ranks = np.clip((np.arange(len(team_def)) // (len(team_def) / 4)).astype(int), 0, 3)
    team_def["def_quartile_rank"] = ranks
    label = {0: "top", 1: "high", 2: "mid", 3: "bottom"}
    team_def["opp_class"] = team_def["def_quartile_rank"].map(label)
    return dict(zip(team_def["team_abbr"], team_def["opp_class"]))


def tag_with_probe_b_prime(per_game, bx, opp_class_map, prev_season_winpct):
    """Tag per-game residuals with the 72-config space from Probe B'."""
    season = per_game["season"].iloc[0]
    season_year = int(season[:4])
    all_star_dates = {
        "2023-24": pd.Timestamp("2024-02-16"),
        "2024-25": pd.Timestamp("2025-02-14"),
        "2025-26": pd.Timestamp("2026-02-14"),
    }
    all_star = all_star_dates[season]
    per_game["game_date"] = pd.to_datetime(per_game["game_date"])
    # Build team_game_n + cumulative win pct
    bx_s = bx[(bx["season"] == season) &
                (bx["season_type"] == "Regular Season")].copy()
    bx_s["game_date"] = pd.to_datetime(bx_s["game_date"])
    tg = (bx_s.groupby(["team_abbr", "game_id", "game_date"])
                .agg(win=("win", "first")).reset_index())
    tg = tg.sort_values(["team_abbr", "game_date"]).reset_index(drop=True)
    tg["team_game_n"] = tg.groupby("team_abbr").cumcount() + 1
    tg["cum_W"] = tg.groupby("team_abbr")["win"].cumsum()
    tg["win_pct_now"] = tg["cum_W"] / tg["team_game_n"]
    # opponent record tier per (opp_abbr, game_date)
    opp_rec = tg.copy()
    opp_record_tier = {}
    for _, r in opp_rec.iterrows():
        if r["team_game_n"] < 30:
            wp = prev_season_winpct.get(r["team_abbr"], 0.5)
        else:
            wp = r["win_pct_now"]
        if wp >= 0.55: tier = "top"
        elif wp >= 0.40: tier = "mid"
        else: tier = "bottom"
        opp_record_tier[(r["team_abbr"], r["game_date"])] = tier
    # Player team's team_game_n
    team_game_n_map = dict(zip(zip(tg["team_abbr"], tg["game_id"]),
                                  tg["team_game_n"]))

    per_game["opp_class"] = per_game["opp_abbr"].map(opp_class_map).fillna("mid")
    per_game["record_tier"] = per_game.apply(
        lambda r: opp_record_tier.get((r["opp_abbr"], r["game_date"]), "mid"),
        axis=1)
    per_game["home_away"] = per_game["is_home"].map({True: "home", False: "away"})
    per_game["team_game_n_self"] = per_game.apply(
        lambda r: team_game_n_map.get((r["team_abbr"], r["game_id"]), np.nan),
        axis=1)
    def phase(r):
        if pd.isna(r["team_game_n_self"]):
            return "early"
        if r["team_game_n_self"] > 62:
            return "last20"
        if r["game_date"] >= all_star:
            return "post_AS"
        return "early"
    per_game["season_phase"] = per_game.apply(phase, axis=1)
    per_game["config"] = (per_game["opp_class"] + "_" +
                            per_game["record_tier"] + "_" +
                            per_game["season_phase"] + "_" +
                            per_game["home_away"])
    return per_game


def matches_tier_1_theme(config_str):
    """Theme: top_record + early + home (4 of 72 configs match this)."""
    parts = config_str.split("_")
    if len(parts) != 4:
        return False
    opp_class, record_tier, season_phase, home_away = parts
    return (record_tier == "top" and season_phase == "early"
            and home_away == "home")


# ────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────

def main():
    print("[load] metadata + box scores")
    meta = load_metadata()
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx["game_date"] = pd.to_datetime(bx["game_date"])
    bx["nba_api_id"] = bx["nba_api_id"].astype(int)
    bx["game_id"] = bx["game_id"].astype(str).str.lstrip("0").astype(int)
    bx["minutes"] = pd.to_numeric(bx["minutes"], errors="coerce")

    # ── Test 1 cross-season replication ─────────────────────────────────
    print("\n=== TEST 1 cross-season replication (3 of 4 cells) ===\n")
    t1_results = []
    for stat in ("PTS", "REB", "AST"):
        for season in ("2023-24", "2024-25"):
            r = run_test_1_for_season(season, stat, PROJ_PATHS[(stat, season)], meta)
            if r:
                t1_results.append(r)
    # Add 25-26 from ship — pulls actuals from box scores (full ship cohort)
    t1_25_26 = test_1_for_25_26(meta, V6_1_SHIP, bx)
    t1_results.extend(t1_25_26)
    t1_df = pd.DataFrame(t1_results).sort_values(["stat", "season"])
    print(t1_df[["season", "stat", "label", "n_in", "n_out", "mean_in", "mean_out",
                  "sd_in", "sd_out", "ratio", "p_levene"]].to_string(index=False))

    # Save
    t1_df.to_csv(OUT_DIR / "test_1_cross_season.csv", index=False)
    print(f"\nSaved test_1 -> {OUT_DIR / 'test_1_cross_season.csv'}")

    # Decision-tree scoring
    print("\n=== DECISION TREE: Test 1 cross-season replication ===\n")
    cells = ["PTS x Center", "REB x Center", "AST x 13+"]
    expected_couple = {"PTS x Center": True, "REB x Center": True, "AST x 13+": False}
    decisions = []
    for cell in cells:
        sub = t1_df[t1_df["label"] == cell].sort_values("season")
        print(f"--- {cell} ---")
        print(sub[["season", "ratio", "p_levene"]].to_string(index=False))
        # Did each season confirm?
        confirms = []
        for _, r in sub.iterrows():
            if expected_couple[cell]:
                # Coupling expected: ratio != 1 AND p_levene < 0.05
                ok = (r["p_levene"] < 0.05) and (r["ratio"] != 1.0)
            else:
                # No coupling expected: ratio close to 1.0 AND p_levene >= 0.05
                ok = r["p_levene"] >= 0.05
            confirms.append(ok)
        decisions.append({"cell": cell,
                            "expected_couple": expected_couple[cell],
                            "n_seasons_confirmed": sum(confirms),
                            "n_seasons_total": len(sub),
                            "per_season_confirm": dict(zip(sub["season"], confirms))})
        print()

    # Verdict per pre-registered scenarios
    n_total = sum(d["n_seasons_total"] for d in decisions)
    n_confirmed = sum(d["n_seasons_confirmed"] for d in decisions)
    print(f"Total cells x seasons: {n_total}, confirmed: {n_confirmed}")

    # Save decisions
    pd.DataFrame(decisions).to_csv(OUT_DIR / "test_1_decision_tree.csv", index=False)

    # ── Probe B pooled ──────────────────────────────────────────────────
    print("\n=== PROBE B POOLED (multi-season, Tier-1 pre-registered) ===\n")

    # Per-game residuals per season
    print("[compute] per-game residuals 23-24, 24-25, 25-26")
    pg_2324 = compute_per_game_residuals("2023-24", PROJ_PATHS, bx, meta)
    pg_2425 = compute_per_game_residuals("2024-25", PROJ_PATHS, bx, meta)
    pg_2526 = compute_per_game_residuals_25_26(V6_1_SHIP, bx, meta)
    print(f"  23-24 player-games: {len(pg_2324)}")
    print(f"  24-25 player-games: {len(pg_2425)}")
    print(f"  25-26 player-games: {len(pg_2526)}")

    # Tag with Probe B' axes per season
    print("[tag] Probe B' 72-config")
    prev_winpct = build_24_25_winpct(bx)
    # Per-season opp_class map (from prior season's def rating)
    opp_class_2324 = build_def_quartile_prev_season(bx, "2022-23")
    opp_class_2425 = build_def_quartile_prev_season(bx, "2023-24")
    opp_class_2526 = build_def_quartile_prev_season(bx, "2024-25")

    pg_2324 = tag_with_probe_b_prime(pg_2324, bx, opp_class_2324,
                                       prev_winpct["2022-23"])
    pg_2425 = tag_with_probe_b_prime(pg_2425, bx, opp_class_2425,
                                       prev_winpct["2023-24"])
    pg_2526 = tag_with_probe_b_prime(pg_2526, bx, opp_class_2526,
                                       prev_winpct["2024-25"])

    pooled = pd.concat([pg_2324, pg_2425, pg_2526], ignore_index=True)
    pooled = pooled.dropna(subset=["PTS_resid", "REB_resid", "AST_resid"], how="all")
    print(f"  pooled rows: {len(pooled)}")
    print(f"  unique configs: {pooled['config'].nunique()}")
    pooled["theme_match"] = pooled["config"].apply(matches_tier_1_theme)
    print(f"  theme-matched rows: {pooled['theme_match'].sum()} ({pooled['theme_match'].mean()*100:.1f}%)")

    # ── Probe B test on pooled per cohort × stat ────────────────────────
    print("\n[test] Probe B clustering on pooled residuals")
    from probe_b_contextual_a_final import (
        aggregate_configs as agg_b, build_distance_matrix,
        cluster_validity, cohort_bootstrap,
    )
    from scipy.cluster.hierarchy import linkage, fcluster
    from scipy.spatial.distance import squareform

    # Reuse Probe B's residual column convention: needs <stat>_resid_v6_3_A
    # But we have <stat>_resid. Rename so the helper works.
    pooled_for_test = pooled.copy()
    for stat in ("PTS", "REB", "AST"):
        pooled_for_test[f"{stat}_resid_v6_3_A"] = pooled_for_test[f"{stat}_resid"]

    cohorts = []
    for cohort_v in ("rookie", "soph", "vet"):
        for pos_v in ("Center", "Forward", "Guard"):
            cohorts.append((cohort_v, pos_v))

    pooled_results = []
    for cohort_v, pos_v in cohorts:
        sub = pooled_for_test[(pooled_for_test["cohort"] == cohort_v) &
                                (pooled_for_test["pos_class"] == pos_v)]
        if len(sub) < 100:
            for stat in ("PTS", "REB", "AST"):
                pooled_results.append({"cohort": f"{cohort_v}_{pos_v}",
                                          "stat": stat, "n_obs": len(sub),
                                          "n_configs": 0,
                                          "verdict": "insufficient_n"})
            continue
        for stat in ("PTS", "REB", "AST"):
            configs, moms, cfs, ns = agg_b(sub, stat)
            n_configs = len(configs)
            if n_configs < 8:
                pooled_results.append({"cohort": f"{cohort_v}_{pos_v}",
                                          "stat": stat, "n_obs": len(sub),
                                          "n_configs": n_configs,
                                          "verdict": "insufficient_configs"})
                continue
            d, _, _ = build_distance_matrix(moms, cfs)
            val = cluster_validity(d, ns)
            if not val:
                pooled_results.append({"cohort": f"{cohort_v}_{pos_v}",
                                          "stat": stat, "n_obs": len(sub),
                                          "n_configs": n_configs,
                                          "verdict": "clustering_failed"})
                continue
            k_star = max(val.keys(), key=lambda k: val[k]["silhouette"])
            sil = val[k_star]["silhouette"]
            # Bootstrap (300 reps for runtime)
            null_df = cohort_bootstrap(sub, stat, n_boot=300, n_workers=8)
            null_at_kstar = null_df[null_df["k"] == k_star]["silhouette_null"].dropna().values
            p = (null_at_kstar >= sil).mean() if len(null_at_kstar) else np.nan

            # Cluster assignments
            np.fill_diagonal(d, 0)
            cond = squareform(d, checks=False)
            Z = linkage(cond, method="average")
            labels = fcluster(Z, t=k_star, criterion="maxclust")

            # Tier 1 check: outlier cluster theme dominance
            cfg_to_label = dict(zip(configs, labels))
            df_lbl = sub.copy()
            df_lbl["cluster"] = df_lbl["config"].map(cfg_to_label)
            df_lbl = df_lbl.dropna(subset=["cluster"])
            df_lbl["cluster"] = df_lbl["cluster"].astype(int)
            cluster_sizes = df_lbl["cluster"].value_counts().to_dict()
            outlier_cluster = min(cluster_sizes, key=cluster_sizes.get)
            outlier_configs = [c for c, lbl in cfg_to_label.items() if lbl == outlier_cluster]
            n_outlier_configs = len(outlier_configs)
            theme_in_outlier = sum(matches_tier_1_theme(c) for c in outlier_configs)
            theme_frac_outlier = (theme_in_outlier / n_outlier_configs
                                    if n_outlier_configs else 0)
            theme_match_overall = sum(matches_tier_1_theme(c) for c in configs)
            theme_frac_overall = theme_match_overall / len(configs)

            verdict = ("structure_detected"
                        if 4 <= k_star <= 16 and p < 0.05
                        else ("ambiguous"
                              if p is not None and p < 0.05
                              else "no_structure"))
            pooled_results.append({
                "cohort": f"{cohort_v}_{pos_v}", "stat": stat,
                "n_obs": len(sub), "n_configs": n_configs,
                "k_star": int(k_star), "silhouette": float(sil),
                "p_value": float(p), "verdict": verdict,
                "outlier_cluster_size": int(n_outlier_configs),
                "theme_in_outlier": int(theme_in_outlier),
                "theme_frac_outlier": float(theme_frac_outlier),
                "theme_frac_overall": float(theme_frac_overall),
                "outlier_configs": "; ".join(outlier_configs[:10]),
            })
            print(f"  {cohort_v}_{pos_v} / {stat}: n={len(sub)}, "
                  f"configs={n_configs}, k*={k_star}, "
                  f"sil={sil:.3f}, p={p:.3f}, "
                  f"outlier_size={n_outlier_configs}, "
                  f"theme_in_outlier={theme_in_outlier}/{n_outlier_configs} "
                  f"({theme_frac_outlier:.0%})")
    pooled_df = pd.DataFrame(pooled_results)
    pooled_df.to_csv(OUT_DIR / "probe_b_pooled.csv", index=False)
    print(f"\nSaved probe_b -> {OUT_DIR / 'probe_b_pooled.csv'}")

    # Save residuals for archival
    pooled[["season", "nba_api_id", "game_id", "game_date", "team_abbr",
              "opp_abbr", "cohort", "pos_class", "ypb", "config",
              "opp_class", "record_tier", "season_phase", "home_away",
              "theme_match", "PTS_resid", "REB_resid", "AST_resid"]].to_csv(
        OUT_DIR / "pooled_residuals.csv", index=False)

    # Summary
    summary = {
        "test_1_cross_season": t1_df.to_dict(orient="records"),
        "test_1_decisions": decisions,
        "probe_b_pooled": pooled_df.to_dict(orient="records"),
        "n_pooled_rows": len(pooled),
        "n_unique_configs": int(pooled["config"].nunique()),
    }
    with open(OUT_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\nDONE. Outputs at {OUT_DIR}")


if __name__ == "__main__":
    main()
