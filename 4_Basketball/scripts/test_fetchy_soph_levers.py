"""Test three fetchy-proposed soph levers on historical rookie→soph transitions.

Lever 1: Coach-continuity — does same-HC year-1→year-2 reduce soph drift?
Lever 2: Within-season MPG/USG instability → soph mean shift (positive)?
Lever 3: Pre-NBA over-performance gap → signed soph mean shift?

Pooling: all rookie→soph pairs 14-15→15-16 through 23-24→24-25.
Cohort filter: ≥20 GP rookie season AND ≥20 GP soph season (paired sample).

Reports per lever: SNR (Welch-style), Pearson r, n. Per-season sign replication
where applicable.
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from pathlib import Path
import pandas as pd
import numpy as np

REPO = Path(".")
PQ = REPO / "data" / "parquet"

STATS_SHARE = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA"]


def load_box_scores() -> pd.DataFrame:
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx = bx[bx["season_type"] == "Regular Season"].copy()
    bx["minutes"] = pd.to_numeric(bx["minutes"], errors="coerce")
    bx = bx.dropna(subset=["minutes"])
    bx = bx[bx["minutes"] > 0]
    bx["game_date"] = pd.to_datetime(bx["game_date"])
    bx["nba_api_id"] = bx["nba_api_id"].astype(int)
    return bx


def per_game_per_36(df_player_season):
    g = df_player_season.groupby(["nba_api_id", "season"]).agg(
        gp=("game_id", "count"), mins=("minutes", "sum"),
        PTS=("PTS", "sum"), REB=("REB", "sum"), AST=("AST", "sum"),
        STL=("STL", "sum"), BLK=("BLK", "sum"), TOV=("TOV", "sum"),
        FGM=("FGM", "sum"), FGA=("FGA", "sum"),
        FG3M=("FG3M", "sum"), FG3A=("FG3A", "sum"),
        FTM=("FTM", "sum"), FTA=("FTA", "sum"),
    ).reset_index()
    g["mpg"] = g["mins"] / g["gp"]
    f = 36.0 / g["mins"]
    for s in STATS_SHARE:
        g[f"{s}_p36"] = g[s] * f
        g[f"{s}_pg"] = g[s] / g["gp"]
    g["usg_p36"] = (g["FGA"] + 0.44 * g["FTA"] + g["TOV"]) * f
    return g


def primary_team(bx, season_filter):
    sub = bx[bx["season"] == season_filter].copy()
    if len(sub) == 0:
        return pd.DataFrame(columns=["nba_api_id", "primary_team"])
    return (sub.groupby("nba_api_id")["team_abbr"]
            .agg(lambda s: s.value_counts().index[0])
            .reset_index()
            .rename(columns={"team_abbr": "primary_team"}))


def build_rookie_year2_pairs(bx, min_gp=20):
    """Return paired (rookie_season, soph_season) per-player frame across all
    rookie classes 14-15 through 23-24 (where year-2 data exists in box scores)."""
    first = bx.groupby("nba_api_id")["season"].min().reset_index().rename(
        columns={"season": "rookie_season"})
    season_order = sorted(bx["season"].unique())
    season_to_idx = {s: i for i, s in enumerate(season_order)}
    first["rookie_idx"] = first["rookie_season"].map(season_to_idx)
    first = first[first["rookie_idx"] < len(season_order) - 1].copy()  # has year-2 possible
    first["soph_season"] = first["rookie_idx"].apply(lambda i: season_order[i + 1])

    full_per36 = per_game_per_36(bx)

    rk = first.merge(full_per36, left_on=["nba_api_id", "rookie_season"],
                     right_on=["nba_api_id", "season"], how="inner")
    rk = rk.add_suffix("_y1").rename(columns={"nba_api_id_y1": "nba_api_id",
                                                "rookie_season_y1": "rookie_season",
                                                "soph_season_y1": "soph_season"})
    sp = full_per36.copy()
    sp = sp.add_suffix("_y2").rename(columns={"nba_api_id_y2": "nba_api_id",
                                                "season_y2": "soph_season"})
    pair = rk.merge(sp, on=["nba_api_id", "soph_season"], how="inner")
    pair = pair[(pair["gp_y1"] >= min_gp) & (pair["gp_y2"] >= min_gp)].copy()
    return pair


# === LEVER 1: COACH CONTINUITY ===

def add_coach_continuity(pair, bx):
    cts = pd.read_parquet(PQ / "coach_team_season.parquet")
    cts = cts[["team_abbr", "season", "head_coach_name", "mid_season_change"]].copy()

    # Each rookie's primary team y1 and y2
    primary_y1 = (bx.groupby(["nba_api_id", "season"])["team_abbr"]
                  .agg(lambda s: s.value_counts().index[0])
                  .reset_index()
                  .rename(columns={"team_abbr": "team_y1", "season": "rookie_season"}))
    primary_y2 = primary_y1.rename(columns={"team_y1": "team_y2", "rookie_season": "soph_season"})

    pair = pair.merge(primary_y1, on=["nba_api_id", "rookie_season"], how="left")
    pair = pair.merge(primary_y2, on=["nba_api_id", "soph_season"], how="left")
    pair = pair.merge(
        cts.rename(columns={"team_abbr": "team_y1", "season": "rookie_season",
                            "head_coach_name": "hc_y1",
                            "mid_season_change": "midchg_y1"}),
        on=["team_y1", "rookie_season"], how="left",
    )
    pair = pair.merge(
        cts.rename(columns={"team_abbr": "team_y2", "season": "soph_season",
                            "head_coach_name": "hc_y2",
                            "mid_season_change": "midchg_y2"}),
        on=["team_y2", "soph_season"], how="left",
    )
    pair["same_hc"] = (pair["hc_y1"] == pair["hc_y2"]) & pair["hc_y1"].notna() & pair["hc_y2"].notna()
    pair["same_team"] = (pair["team_y1"] == pair["team_y2"])
    return pair


def report_lever1(pair):
    print("=" * 78)
    print("LEVER 1 — Coach continuity tightens drift?")
    print("=" * 78)
    sub = pair.dropna(subset=["hc_y1", "hc_y2"]).copy()
    print(f"  Pairs with HC-resolved both years: {len(sub)}")
    print(f"    same_hc=True: {int(sub['same_hc'].sum())}, False: {int((~sub['same_hc']).sum())}")
    print(f"    same_team=True: {int(sub['same_team'].sum())}, False: {int((~sub['same_team']).sum())}")
    print()
    print(f"  {'stat':<6} {'|Δ| same_hc':>13} {'|Δ| diff_hc':>13} {'ratio':>8} {'SNR(welch)':>12}")
    print("  " + "-" * 60)
    for stat in ["PTS", "REB", "AST", "FGA", "FG3A"]:
        col = f"{stat}_pg"
        sub2 = sub.dropna(subset=[f"{col}_y1", f"{col}_y2"])
        sub2 = sub2.assign(delta=(sub2[f"{col}_y2"] - sub2[f"{col}_y1"]).abs())
        a = sub2.loc[sub2["same_hc"], "delta"].values
        b = sub2.loc[~sub2["same_hc"], "delta"].values
        if len(a) < 5 or len(b) < 5: continue
        diff = a.mean() - b.mean()
        se = np.sqrt(a.var(ddof=1)/len(a) + b.var(ddof=1)/len(b))
        snr = diff / se if se > 0 else float("nan")
        ratio = a.mean() / b.mean() if b.mean() > 0 else float("nan")
        print(f"  {stat:<6} {a.mean():>13.3f} {b.mean():>13.3f} {ratio:>8.3f} {snr:>+12.3f}")

    # Also: does same_hc reduce SIGNED drift volatility on MPG?
    sub2 = sub.dropna(subset=["mpg_y1", "mpg_y2"])
    sub2 = sub2.assign(d_mpg=sub2["mpg_y2"] - sub2["mpg_y1"])
    a = sub2.loc[sub2["same_hc"], "d_mpg"].values
    b = sub2.loc[~sub2["same_hc"], "d_mpg"].values
    print()
    print(f"  Signed Δmpg sd: same_hc={a.std():.2f} (n={len(a)})  diff_hc={b.std():.2f} (n={len(b)})")
    print(f"    ratio (sd same / sd diff): {a.std()/b.std():.3f}  ← <1 = same-HC tightens drift")


# === LEVER 2: WITHIN-SEASON MPG/USG INSTABILITY ===

def add_instability_features(pair, bx):
    """Per rookie compute rolling-10 stdev/mean of MPG and per-36 USG, on
    games where the rookie played 10+ minutes."""
    rk_games = []
    for (pid, season), grp in bx.groupby(["nba_api_id", "season"]):
        if season not in set(pair["rookie_season"]):
            continue
        if pid not in set(pair["nba_api_id"].unique()):
            continue
        gp = grp.sort_values("game_date").copy()
        gp = gp[gp["minutes"] >= 10]
        if len(gp) < 10:
            continue
        m = gp["minutes"].astype(float)
        usg = (gp["FGA"] + 0.44 * gp["FTA"] + gp["TOV"]) * 36.0 / m
        roll_m = m.rolling(10).mean().dropna()
        roll_u = usg.rolling(10).mean().dropna()
        if len(roll_m) < 3 or m.mean() == 0:
            continue
        rk_games.append({
            "nba_api_id": pid, "rookie_season": season,
            "mpg_stability": roll_m.std() / roll_m.mean(),
            "usg_stability": roll_u.std() / roll_u.mean() if roll_u.mean() > 0 else float("nan"),
        })
    inst = pd.DataFrame(rk_games)
    return pair.merge(inst, on=["nba_api_id", "rookie_season"], how="left")


def report_lever2(pair):
    print("=" * 78)
    print("LEVER 2 — Within-season instability drives positive soph shift?")
    print("=" * 78)
    sub = pair.dropna(subset=["mpg_stability", "usg_stability"]).copy()
    print(f"  Pairs with instability features: {len(sub)}")
    print()
    # Quintile by mpg_stability
    sub["mpg_inst_q"] = pd.qcut(sub["mpg_stability"], 5, labels=False, duplicates="drop")
    print(f"  Quintile-mean stat shift (year2 − year1, per-game):")
    print(f"  {'q (mpg_inst)':<14} {'n':>5} {'ΔPTS':>8} {'ΔAST':>8} {'ΔMPG':>8} {'ΔUSG36':>9}")
    for q in sorted(sub["mpg_inst_q"].dropna().unique()):
        ss = sub[sub["mpg_inst_q"] == q]
        d_pts = (ss["PTS_pg_y2"] - ss["PTS_pg_y1"]).mean()
        d_ast = (ss["AST_pg_y2"] - ss["AST_pg_y1"]).mean()
        d_mpg = (ss["mpg_y2"] - ss["mpg_y1"]).mean()
        d_usg = (ss["usg_p36_y2"] - ss["usg_p36_y1"]).mean()
        print(f"  q={int(q)+1}/5         {len(ss):>5} {d_pts:>+8.3f} {d_ast:>+8.3f} {d_mpg:>+8.3f} {d_usg:>+9.3f}")

    # Direct correlation
    print()
    print(f"  Pearson r (instability vs soph leap):")
    for feat in ["mpg_stability", "usg_stability"]:
        for stat in ["PTS_pg", "AST_pg", "mpg", "usg_p36"]:
            d = sub[f"{stat}_y2"] - sub[f"{stat}_y1"]
            ss = sub[[feat]].assign(leap=d).dropna()
            if len(ss) < 30: continue
            r = np.corrcoef(ss[feat], ss["leap"])[0, 1]
            print(f"    {feat:<16} ↔ Δ{stat:<10}  r={r:+.3f}  (n={len(ss)})")


# === LEVER 3: PRE-NBA OVER-PERFORMANCE GAP ===

def add_pre_nba_gap(pair):
    pre = pd.read_parquet(PQ / "rookie_career_prior.parquet")
    pre = pre[pre["has_stats"] == True].copy()
    pre = pre.dropna(subset=["nba_api_id"])
    pre["nba_api_id"] = pre["nba_api_id"].astype(int)
    # Take most-recent pre-NBA row per player
    pre = pre.sort_values(["nba_api_id", "last_pre_nba_season"], ascending=[True, False])
    pre = pre.drop_duplicates(subset=["nba_api_id"], keep="first")
    cols = {"pts_per40": "pre_PTS_p40", "reb_per40": "pre_REB_p40", "ast_per40": "pre_AST_p40",
            "stl_per40": "pre_STL_p40", "blk_per40": "pre_BLK_p40",
            "tov_per40": "pre_TOV_p40", "fg3m_per40": "pre_FG3M_p40"}
    pre = pre[["nba_api_id"] + list(cols.keys())].rename(columns=cols)
    return pair.merge(pre, on="nba_api_id", how="left")


def report_lever3(pair):
    print("=" * 78)
    print("LEVER 3 — Pre-NBA over-performance gap drives signed soph shift?")
    print("=" * 78)
    pairs_with_pre = pair.dropna(subset=["pre_PTS_p40"]).copy()
    print(f"  Pairs with pre-NBA prior: {len(pairs_with_pre)}")
    print()
    # gap = pre_per40 − rookie_per40 (note: rookie p36 ≠ p40 scale, so we
    # convert rookie p36 → p40 via *(40/36) for fair comparison)
    print(f"  {'stat':<6} {'r(gap, leap)':>14} {'r(gap, sgn_leap)':>18} {'n':>5}")
    print("  " + "-" * 50)
    for stat in ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FG3M"]:
        pre_col = f"pre_{stat}_p40"
        rk_p36_col = f"{stat}_p36_y1"
        sp_p36_col = f"{stat}_p36_y2"
        ss = pairs_with_pre.dropna(subset=[pre_col, rk_p36_col, sp_p36_col])
        if len(ss) < 30: continue
        rk_p40 = ss[rk_p36_col] * (40.0 / 36.0)
        sp_p40 = ss[sp_p36_col] * (40.0 / 36.0)
        gap = ss[pre_col] - rk_p40  # +ve = pre-NBA over-produced rookie
        leap = sp_p40 - rk_p40       # signed
        if gap.std() == 0 or leap.std() == 0: continue
        r = np.corrcoef(gap, leap)[0, 1]
        # Also: just signed soph shift (year2 − year1)
        r_sgn = np.corrcoef(gap, sp_p40 - rk_p40)[0, 1]
        print(f"  {stat:<6} {r:>+14.3f} {r_sgn:>+18.3f} {len(ss):>5}")
    print()
    # Tertile split — does positive gap predict positive leap?
    pairs_with_pre["pts_gap"] = (pairs_with_pre["pre_PTS_p40"]
                                  - pairs_with_pre["PTS_p36_y1"] * (40 / 36))
    pairs_with_pre["pts_leap"] = (pairs_with_pre["PTS_p36_y2"] - pairs_with_pre["PTS_p36_y1"]) * (40 / 36)
    pairs_with_pre["gap_tertile"] = pd.qcut(pairs_with_pre["pts_gap"], 3, labels=["under","mid","over"], duplicates="drop")
    print(f"  PTS leap by gap tertile:")
    print(f"  {'tertile':<10} {'n':>5} {'mean_gap':>10} {'mean_leap':>11}")
    for t in ["under", "mid", "over"]:
        ss = pairs_with_pre[pairs_with_pre["gap_tertile"] == t]
        if len(ss) == 0: continue
        print(f"  {t:<10} {len(ss):>5} {ss['pts_gap'].mean():>+10.3f} {ss['pts_leap'].mean():>+11.3f}")


def main():
    print("=" * 78)
    print("Fetchy soph levers — historical rookie→soph transition tests")
    print("=" * 78)
    print()
    bx = load_box_scores()
    pair = build_rookie_year2_pairs(bx, min_gp=20)
    print(f"Total rookie→soph paired observations: {len(pair)}")
    print(f"  rookie season distribution:")
    print(pair["rookie_season"].value_counts().sort_index().to_string())
    print()

    pair = add_coach_continuity(pair, bx)
    pair = add_instability_features(pair, bx)
    pair = add_pre_nba_gap(pair)
    print()
    report_lever1(pair)
    print()
    report_lever2(pair)
    print()
    report_lever3(pair)


if __name__ == "__main__":
    main()
