"""Calibrate league-to-NBA translation factors per stat.

For each (source league, stat) combo, fit:
    NBA_rookie_per_36 = intercept + slope * pre_NBA_per_40

Source leagues:
  - ncaa (sample ~471 paired rookies)
  - g_league (sample ~100-150)
  - intl_pooled (Euroleague + ACB + LNB + NBL + BSL + OTE + others, ~60-80)

Output: data/parquet/translation_factors.parquet
        audit_runs/translation_factors_v1/{regression_diagnostics.csv, scatter_per_stat_per_league.png}

Calibration sample: NBA-rookie-year per-36 stats from historical_box_scores
filtered to ≥20 GP rookie season, paired with pre-NBA per-40 from join tables.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
SAVE_DIR = REPO / "audit_runs" / "translation_factors_v1"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# 12-stat target list (matches the v6.1 ship contract)
STATS = ["PTS", "REB", "AST", "STL", "BLK", "TOV",
         "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA"]
# Source-league columns are lowercase per40; target is uppercase per36
SRC_COL = {s: f"{s.lower()}_per40" for s in STATS}
SRC_COL["FG3M"] = "fg3m_per40"
SRC_COL["FG3A"] = "fg3a_per40"

MIN_ROOKIE_GP = 20  # Filter cup-of-coffee rookies


def load_nba_rookie_per36() -> pd.DataFrame:
    """Compute each player's NBA-rookie-year per-36 stats from box scores.

    Rookie season = earliest season in historical_box_scores per nba_api_id,
    with regular-season GP ≥ MIN_ROOKIE_GP.
    """
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx = bx[bx["season_type"] == "Regular Season"].copy()
    bx["minutes"] = pd.to_numeric(bx["minutes"], errors="coerce")
    bx = bx.dropna(subset=["minutes"])
    bx = bx[bx["minutes"] > 0]

    # First NBA season per player
    first = bx.groupby("nba_api_id")["season"].min().reset_index()
    first = first.rename(columns={"season": "rookie_season"})

    bx = bx.merge(first, on="nba_api_id")
    bx_rk = bx[bx["season"] == bx["rookie_season"]].copy()

    # Aggregate rookie season totals
    agg = bx_rk.groupby(["nba_api_id", "rookie_season"]).agg(
        gp=("game_id", "count"),
        minutes_total=("minutes", "sum"),
        PTS=("PTS", "sum"),
        REB=("REB", "sum"),
        AST=("AST", "sum"),
        STL=("STL", "sum"),
        BLK=("BLK", "sum"),
        TOV=("TOV", "sum"),
        FGM=("FGM", "sum"),
        FGA=("FGA", "sum"),
        FG3M=("FG3M", "sum"),
        FG3A=("FG3A", "sum"),
        FTM=("FTM", "sum"),
        FTA=("FTA", "sum"),
    ).reset_index()
    agg = agg[agg["gp"] >= MIN_ROOKIE_GP].copy()

    # Per-36 conversions
    factor = 36.0 / agg["minutes_total"]
    for s in STATS:
        agg[f"{s}_per36"] = agg[s] * factor
    return agg[["nba_api_id", "rookie_season", "gp", "minutes_total"] +
               [f"{s}_per36" for s in STATS]]


def load_ncaa_pairs(nba_rookie: pd.DataFrame) -> pd.DataFrame:
    """NCAA per-40 paired with NBA-rookie per-36.

    Derives missing per-40 columns (FG3M, FG3A, FTM, FTA) from per-game / mpg
    since the join only pre-computed per-40 for the 8 baseline stats.
    """
    nc = pd.read_parquet(PQ / "ncaa_to_nba_rookie_join.parquet")
    nc = nc.dropna(subset=["nba_api_id"])
    nc["nba_api_id"] = nc["nba_api_id"].astype(int)
    # Derive per-40 from per-game where missing
    for stat in ["FG3M", "FG3A", "FTM", "FTA"]:
        pg_col = f"{stat.lower()}_pg"
        p40_col = f"{stat.lower()}_per40"
        if p40_col not in nc.columns and pg_col in nc.columns and "mpg" in nc.columns:
            nc[p40_col] = pd.to_numeric(nc[pg_col], errors="coerce") * 40.0 / pd.to_numeric(nc["mpg"], errors="coerce")
    keep = ["nba_api_id"] + list(SRC_COL.values())
    keep = [c for c in keep if c in nc.columns]
    nc = nc[keep].rename(columns={SRC_COL[s]: f"src_{s}" for s in STATS if SRC_COL[s] in nc.columns})
    paired = nc.merge(nba_rookie, on="nba_api_id", how="inner")
    paired["league"] = "ncaa"
    return paired


def load_intl_pairs(nba_rookie: pd.DataFrame) -> pd.DataFrame:
    """Intl/G-League per-40 paired with NBA-rookie per-36.

    Uses last_pre_nba_season row per (player, league); the join already
    aggregates so each player has one row per pre-NBA league. We take the
    most-recent pre-NBA league as the calibration source.
    """
    it = pd.read_parquet(PQ / "international_to_nba_rookie_join.parquet")
    it = it.dropna(subset=["nba_api_id"])
    it["nba_api_id"] = it["nba_api_id"].astype(int)

    # Take the most-recent pre-NBA season per player (in case multiple league rows)
    it = it.sort_values(["nba_api_id", "last_pre_nba_season"], ascending=[True, False])
    it = it.drop_duplicates(subset=["nba_api_id"], keep="first")

    # FGM/FGA/FTM/FTA aren't in intl join; only PTS/REB/AST/STL/BLK/TOV/FG3M
    available = [s for s in STATS if SRC_COL[s] in it.columns]
    keep = ["nba_api_id", "league"] + [SRC_COL[s] for s in available]
    it = it[keep].rename(columns={SRC_COL[s]: f"src_{s}" for s in available})
    paired = it.merge(nba_rookie, on="nba_api_id", how="inner")
    return paired


def fit_one(df: pd.DataFrame, src_col: str, dst_col: str) -> dict | None:
    """Simple OLS: dst = a + b * src.  Returns coefficients + diagnostics."""
    sub = df[[src_col, dst_col]].dropna()
    if len(sub) < 10:
        return None
    x = sub[src_col].values.astype(float)
    y = sub[dst_col].values.astype(float)
    if x.std() < 1e-9:
        return None
    n = len(sub)
    b = np.cov(x, y, ddof=1)[0, 1] / x.var(ddof=1)
    a = y.mean() - b * x.mean()
    yhat = a + b * x
    ss_res = ((y - yhat) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {
        "n": n, "intercept": float(a), "slope": float(b), "r2": float(r2),
        "src_mean": float(x.mean()), "src_sd": float(x.std()),
        "dst_mean": float(y.mean()), "dst_sd": float(y.std()),
    }


def fit_league(paired: pd.DataFrame, league_label: str, available_stats: list[str]) -> pd.DataFrame:
    rows = []
    for s in available_stats:
        src = f"src_{s}"
        dst = f"{s}_per36"
        if src not in paired.columns or dst not in paired.columns:
            continue
        r = fit_one(paired, src, dst)
        if r is None:
            print(f"  {league_label}/{s}: insufficient data, skip")
            continue
        rows.append({"league": league_label, "stat": s, **r})
    return pd.DataFrame(rows)


def main():
    print("=" * 75)
    print("Translation factor calibration")
    print("=" * 75)
    print()

    print("Loading NBA-rookie per-36 from box scores ...")
    rookie = load_nba_rookie_per36()
    print(f"  {len(rookie)} NBA rookies with ≥{MIN_ROOKIE_GP} GP")
    print()

    print("Loading NCAA pairs ...")
    ncaa = load_ncaa_pairs(rookie)
    print(f"  {len(ncaa)} NCAA→NBA paired rookies")
    print()

    print("Loading intl/G-League pairs ...")
    intl = load_intl_pairs(rookie)
    print(f"  {len(intl)} intl/G-League→NBA paired rookies")
    print(f"  league counts: {intl['league'].value_counts().to_dict()}")
    print()

    # Split: g_league as its own bucket, everything else pooled as intl_pooled
    gl = intl[intl["league"] == "g_league"].copy()
    other = intl[intl["league"] != "g_league"].copy()
    other["league"] = "intl_pooled"
    print(f"  g_league pairs: {len(gl)}")
    print(f"  intl_pooled pairs: {len(other)}")
    print()

    available_ncaa = [s for s in STATS if f"src_{s}" in ncaa.columns]
    available_intl = [s for s in STATS if f"src_{s}" in gl.columns]
    print(f"NCAA available stats: {available_ncaa}")
    print(f"intl/g-league available stats: {available_intl}")
    print()

    print("=" * 75)
    print("Fits per league × stat")
    print("=" * 75)
    coefs = []
    for label, df, available in [
        ("ncaa", ncaa, available_ncaa),
        ("g_league", gl, available_intl),
        ("intl_pooled", other, available_intl),
    ]:
        sub = fit_league(df, label, available)
        if not sub.empty:
            print(f"\n--- {label} (n_pairs available varies per stat) ---")
            print(sub[["stat", "n", "intercept", "slope", "r2",
                      "src_mean", "src_sd", "dst_mean", "dst_sd"]].to_string(
                index=False, float_format=lambda x: f"{x:8.3f}"))
        coefs.append(sub)

    out = pd.concat(coefs, ignore_index=True)
    out.to_parquet(PQ / "translation_factors.parquet", index=False)
    out.to_csv(SAVE_DIR / "translation_factors.csv", index=False)
    print()
    print(f"Saved {len(out)} rows -> {PQ}/translation_factors.parquet")
    print(f"             and -> {SAVE_DIR}/translation_factors.csv")

    # Population-anchor sanity check (rough expected ratios)
    print()
    print("=" * 75)
    print("Sanity check: implied ratios at mean source")
    print("=" * 75)
    for _, row in out.iterrows():
        ratio = row["slope"] * row["src_mean"] + row["intercept"]
        ratio /= row["src_mean"] if row["src_mean"] > 0 else 1.0
        print(f"  {row['league']:<13} {row['stat']:<5} "
              f"slope={row['slope']:.3f}  R²={row['r2']:.3f}  "
              f"implied translation @ src_mean: {ratio:.3f}")

    metadata = {
        "calibration_date": pd.Timestamp.utcnow().isoformat(),
        "min_rookie_gp": MIN_ROOKIE_GP,
        "stats": STATS,
        "leagues": ["ncaa", "g_league", "intl_pooled"],
        "n_nba_rookies": len(rookie),
        "n_ncaa_pairs": len(ncaa),
        "n_g_league_pairs": len(gl),
        "n_intl_pooled_pairs": len(other),
        "model_form": "y = intercept + slope * x  (per-36 NBA rookie ~ per-40 source)",
    }
    with open(SAVE_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nMetadata -> {SAVE_DIR}/metadata.json")


if __name__ == "__main__":
    main()
