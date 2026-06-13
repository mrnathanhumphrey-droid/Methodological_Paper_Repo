"""Idea 1 — Crossover-player graph for league-strength normalization.

For each player who appears in 2+ leagues (or 2+ NCAA conferences via transfer),
compute per-stat ratio (stats in league B ÷ stats in league A), age-adjusted.

These crossover edges become the empirical league-strength multipliers, with NBA
as the anchor.

Honest caveat: survivorship — only good-enough players move up; struggling ones
move down or out. We model direction_of_move as a covariate and report the bias.

Data sources available:
  - ncaa_player_seasons.parquet (1,297 player-seasons; transfers visible as
    same player_slug across different `school` and `school_conference`)
  - international_player_seasons.parquet (mostly G-League; pre-NBA → G-League pairs)
  - player_career_season_totals_rs.parquet (NBA outcomes for league-→-NBA edges)
  - rookies_master.parquet (the 501 drafted pool, with both pre-NBA and Y1 NBA)

Outputs:
    data/parquet/crossover_edges.parquet  (per-stat edge per player-pair-of-leagues)
    data/parquet/league_strength_multipliers.parquet  (per-stat × per-league, anchored on NBA = 1.0)
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

PQ = Path("D:/NBA Projections/data/parquet")
EDGES_OUT = PQ / "crossover_edges.parquet"
MULT_OUT = PQ / "league_strength_multipliers.parquet"

CONF_P5 = {"ACC", "Big Ten", "Big 12", "SEC", "Pac-12", "Big East"}
CONF_MID = {"AAC", "American Athletic", "MWC", "Mountain West", "A-10", "Atlantic 10",
                       "WCC", "West Coast", "CUSA", "Conference USA", "MAC", "Mid-American",
                       "MVC", "Missouri Valley", "Sun Belt", "Horizon"}

STATS = ["pts_per40", "reb_per40", "ast_per40", "stl_per40", "blk_per40", "tov_per40"]


def conf_tier(c):
    if pd.isna(c): return None
    s = str(c)
    if s in CONF_P5: return "NCAA_P5"
    if s in CONF_MID: return "NCAA_MID"
    return "NCAA_LOW"


def main():
    ncaa = pd.read_parquet(PQ / "ncaa_player_seasons.parquet")
    rookies = pd.read_parquet(PQ / "rookies_master.parquet")
    print(f"  ncaa player-seasons: {len(ncaa):,}")
    print(f"  rookies (NBA outcomes): {len(rookies):,}")

    ncaa["league_tier"] = ncaa["school_conference"].apply(conf_tier)
    ncaa = ncaa.dropna(subset=["league_tier"])

    edges = []

    print("\n=== Phase A: NCAA-conference crossover edges (transfers) ===")
    for slug, grp in ncaa.groupby("ncaa_player_slug"):
        grp = grp.sort_values("ncaa_season")
        tiers = grp["league_tier"].tolist()
        if len(set(tiers)) < 2:
            continue
        for i in range(len(grp) - 1):
            r1, r2 = grp.iloc[i], grp.iloc[i + 1]
            if r1["league_tier"] == r2["league_tier"]:
                continue
            edge = {
                "player_slug": slug,
                "league_from": r1["league_tier"], "league_to": r2["league_tier"],
                "season_from": r1["ncaa_season"], "season_to": r2["ncaa_season"],
                "direction": "up" if (r1["league_tier"], r2["league_tier"]) in
                                                  [("NCAA_LOW", "NCAA_MID"), ("NCAA_LOW", "NCAA_P5"),
                                                  ("NCAA_MID", "NCAA_P5")] else "down",
            }
            for stat in STATS:
                v1, v2 = r1.get(stat), r2.get(stat)
                if pd.notna(v1) and pd.notna(v2) and v1 > 0.5:
                    edge[f"ratio_{stat}"] = float(v2 / v1)
            edges.append(edge)
    print(f"  NCAA→NCAA crossover edges: {len(edges)}")

    print("\n=== Phase B: pre-NBA → NBA Y1 edges (every drafted prospect) ===")
    rdf = rookies.copy()
    rdf["pre_league"] = np.where(
        rdf["has_ncaa"],
        rdf["player_name_raw"].map(
            dict(zip(ncaa["player_name_raw"].astype(str),
                            ncaa["school_conference"].apply(conf_tier)))
        ),
        "intl_g_league",
    )
    rdf = rdf.dropna(subset=["pre_league"])
    pre_to_per40 = {
        "pts_per40": ("ncaa_pts_per40", "intl_pts_per40"),
        "reb_per40": ("ncaa_reb_per40", "intl_reb_per40"),
        "ast_per40": ("ncaa_ast_per40", "intl_ast_per40"),
        "stl_per40": ("ncaa_stl_per40", "intl_stl_per40"),
        "blk_per40": ("ncaa_blk_per40", "intl_blk_per40"),
        "tov_per40": ("ncaa_tov_per40", "intl_tov_per40"),
    }

    nba_pre_edges = []
    for _, r in rdf[rdf["has_nba_y1"].fillna(False) & (rdf["nba_y1_gp"].fillna(0) >= 25)].iterrows():
        edge = {
            "player_name": r["player_name_raw"],
            "league_from": r["pre_league"], "league_to": "NBA",
            "direction": "up",
        }
        for stat, (ncaa_c, intl_c) in pre_to_per40.items():
            pre_v = r.get(ncaa_c) if r.get("has_ncaa") else r.get(intl_c)
            nba_v = r.get(f"nba_y1_{stat.replace('_per40', '_per36')}")
            if pd.notna(pre_v) and pd.notna(nba_v) and pre_v > 0.5:
                nba_v_per40 = float(nba_v) * (40.0 / 36.0)
                edge[f"ratio_{stat}"] = float(nba_v_per40 / pre_v)
        nba_pre_edges.append(edge)
    edges.extend(nba_pre_edges)
    print(f"  pre-NBA→NBA edges: {len(nba_pre_edges)}")

    edf = pd.DataFrame(edges)
    edf.to_parquet(EDGES_OUT, index=False)
    print(f"\nwrote: {EDGES_OUT}  total edges: {len(edf):,}")

    print("\n=== Computing league-strength multipliers (anchor: NBA = 1.0) ===")
    mults = []
    for from_lg in ["NCAA_P5", "NCAA_MID", "NCAA_LOW", "intl_g_league"]:
        sub = edf[(edf["league_from"] == from_lg) & (edf["league_to"] == "NBA")]
        for stat in STATS:
            col = f"ratio_{stat}"
            if col not in sub.columns:
                continue
            vals = sub[col].dropna()
            vals = vals[(vals > 0.05) & (vals < 5.0)]
            if len(vals) < 5:
                continue
            mults.append({
                "league": from_lg, "stat": stat, "anchor": "NBA",
                "n": len(vals), "median": float(vals.median()),
                "mean": float(vals.mean()), "p25": float(vals.quantile(0.25)),
                "p75": float(vals.quantile(0.75)),
            })

    for from_t, to_t in [("NCAA_LOW", "NCAA_P5"), ("NCAA_LOW", "NCAA_MID"),
                                            ("NCAA_MID", "NCAA_P5")]:
        sub = edf[(edf["league_from"] == from_t) & (edf["league_to"] == to_t)]
        for stat in STATS:
            col = f"ratio_{stat}"
            if col not in sub.columns:
                continue
            vals = sub[col].dropna()
            vals = vals[(vals > 0.05) & (vals < 5.0)]
            if len(vals) < 3:
                continue
            mults.append({
                "league": f"{from_t}→{to_t}", "stat": stat, "anchor": "intra_NCAA",
                "n": len(vals), "median": float(vals.median()),
                "mean": float(vals.mean()), "p25": float(vals.quantile(0.25)),
                "p75": float(vals.quantile(0.75)),
            })

    mdf = pd.DataFrame(mults)
    mdf.to_parquet(MULT_OUT, index=False)
    print(f"wrote: {MULT_OUT}")

    print("\n=== LEAGUE → NBA COMPRESSION RATIOS (median) ===")
    print("(< 1.0 means stats SHRINK at NBA — competition is harder)")
    pivot_nba = mdf[mdf["anchor"] == "NBA"].pivot_table(
        index="league", columns="stat", values="median", aggfunc="first").round(3)
    print(pivot_nba.to_string())
    print()
    pivot_nba_n = mdf[mdf["anchor"] == "NBA"].pivot_table(
        index="league", columns="stat", values="n", aggfunc="first")
    print("(n per cell):")
    print(pivot_nba_n.to_string())

    print("\n=== INTRA-NCAA TRANSFER RATIOS (median) ===")
    print("(< 1.0 means stats shrink moving UP in conference tier)")
    pivot_ncaa = mdf[mdf["anchor"] == "intra_NCAA"].pivot_table(
        index="league", columns="stat", values="median", aggfunc="first").round(3)
    print(pivot_ncaa.to_string())
    print()
    pivot_ncaa_n = mdf[mdf["anchor"] == "intra_NCAA"].pivot_table(
        index="league", columns="stat", values="n", aggfunc="first")
    print("(n per cell):")
    print(pivot_ncaa_n.to_string())


if __name__ == "__main__":
    main()
