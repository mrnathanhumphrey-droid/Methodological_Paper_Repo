"""
EXPLORATORY (post-hoc). 12-season (2013-14..2024-25) MORPH of the creation-WHERE
modulation. Self-contained on shot_locations_player + player_tracking_passing
(no box scores / P0 needed pre-2019). Region from shot-zone plurality
(Rim=ra / Paint / Perimeter=mid+corners+ab3, locked off_feast rule);
AST_per36 from passing (ast*36/min, gp>=20 & mpg>=10). Per season: variance
ratio Var(AST_per36|region)/Var(rest) -> watch the creator-big (Paint) emerge
and the rim->finisher (Rim) harden across the decade.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
import numpy as np, pandas as pd
from scipy.stats import levene
sys.path.insert(0, str(Path(__file__).parent))
from _common import RESULTS
DATA = Path(r"D:/NBA Projections/data/parquet")
SEASONS = ["2013-14", "2014-15", "2015-16", "2016-17", "2017-18", "2018-19",
           "2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]
ZF = ["ra_fga", "paint_fga", "mid_fga", "lc3_fga", "rc3_fga", "ab3_fga"]


def vr(y, mask):
    g = y[mask]; r = y[~mask]
    g = g[np.isfinite(g)]; r = r[np.isfinite(r)]
    if len(g) < 5 or len(r) < 5: return float("nan"), int(len(g)), float("nan")
    vg, vrr = g.var(ddof=1), r.var(ddof=1)
    try: _, p = levene(g, r, center="median")
    except Exception: p = float("nan")
    return (round(float(vg/vrr), 3) if vrr > 0 else float("nan")), int(len(g)), float(p)


def season_row(season: str) -> dict:
    sl = pd.read_parquet(DATA / "shot_locations_player.parquet")
    sl = sl[sl.season == season]
    g = sl.groupby("nba_api_id", as_index=False)[ZF].sum()
    g["tot"] = g[ZF].sum(axis=1); g = g[g.tot >= 50]
    g["perim"] = g[["mid_fga", "lc3_fga", "rc3_fga", "ab3_fga"]].sum(axis=1)
    trio = g[["ra_fga", "paint_fga", "perim"]].rename(columns={"ra_fga": "Rim", "paint_fga": "Paint", "perim": "Perimeter"})
    g["region"] = trio.idxmax(axis=1)

    pas = pd.read_parquet(DATA / "player_tracking_passing.parquet")
    pas = pas[(pas.season == season) & (pas.season_type == "Regular Season")]
    pas = pas.groupby("nba_api_id", as_index=False).agg(gp=("gp", "max"), min=("min", "sum"), ast=("ast", "sum"))
    pas = pas[(pas.gp >= 20) & (pas["min"] / pas.gp >= 10)]
    pas["AST_per36"] = pas.ast * 36.0 / pas["min"]

    m = g[["nba_api_id", "region"]].merge(pas[["nba_api_id", "AST_per36"]], on="nba_api_id", how="inner")
    y = m.AST_per36.to_numpy(float)
    out = {"season": season, "n": len(m)}
    for reg in ["Rim", "Paint", "Perimeter"]:
        ratio, n, p = vr(y, (m.region == reg).to_numpy())
        out[reg] = {"ratio": ratio, "n": n, "p": p}
    return out


def main() -> int:
    rows = [season_row(s) for s in SEASONS]
    out = {"per_season": rows}
    (RESULTS / "explore_where_morph_12season.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")

    print("=== 12-season MORPH of creation-WHERE modulation (AST_per36 variance ratio) ===")
    print(f"{'season':10s} {'n':>4s} | {'Rim (finisher)':>20s} | {'Paint (creator-big)':>22s} | {'Perimeter':>16s}")
    for r in rows:
        def fmt(d): return f"{d['ratio']:.2f} (n{d['n']})" if np.isfinite(d['ratio']) else f"n/a (n{d['n']})"
        print(f"{r['season']:10s} {r['n']:4d} | {fmt(r['Rim']):>20s} | {fmt(r['Paint']):>22s} | {fmt(r['Perimeter']):>16s}")

    def series(reg): return [r[reg]["ratio"] for r in rows if np.isfinite(r[reg]["ratio"])]
    for reg in ["Rim", "Paint", "Perimeter"]:
        s = [r[reg]["ratio"] for r in rows]
        valid = [(i, v) for i, v in enumerate(s) if np.isfinite(v)]
        if len(valid) >= 3:
            xs, ys = zip(*valid)
            sl = float(np.polyfit(xs, ys, 1)[0])
            print(f"\n  {reg:10s} trend slope: {sl:+.3f}/season   "
                  f"first->last valid: {valid[0][1]:.2f} -> {valid[-1][1]:.2f}")
    # Paint n growth (creator-big emergence)
    print(f"\n  Paint bucket n by season: {[r['Paint']['n'] for r in rows]}")
    print("\n-> explore_where_morph_12season.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
