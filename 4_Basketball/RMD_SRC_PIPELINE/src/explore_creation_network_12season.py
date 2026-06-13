"""
EXPLORATORY (post-hoc). TRUE multi-era (12-season, 2013-14..2024-25)
de-heliocentrization arc. Self-contained on player_tracking_passing.parquet
(ast/min/gp/potential_ast/secondary_ast) -> no box scores / position needed
pre-2019. Tests whether the network-Hub grip on AST variance peaks in the
heliocentric-iso era (2017-2019: Harden/Westbrook/Doncic) and declines into the
distributed-2020s.

Per season: inclusion gp>=20 & mpg>=10; AST_per36 = ast*36/min; Hub = top
tercile potential_ast/g; variance ratio Var(AST_per36|Hub)/Var(rest).
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


def hub_ratio(season: str) -> dict:
    d = pd.read_parquet(DATA / "player_tracking_passing.parquet")
    d = d[(d.season == season) & (d.season_type == "Regular Season")].copy()
    d = d.groupby("nba_api_id", as_index=False).agg(
        gp=("gp", "max"), min=("min", "sum"), ast=("ast", "sum"),
        potential_ast=("potential_ast", "sum"), secondary_ast=("secondary_ast", "sum"))
    d = d[(d.gp >= 20) & (d["min"] / d.gp >= 10)].copy()
    d["AST_per36"] = d.ast * 36.0 / d["min"]
    d["pot_pg"] = d.potential_ast / d.gp
    cut = d.pot_pg.quantile(2/3)
    d["is_hub"] = d.pot_pg >= cut
    y = d.AST_per36.to_numpy(float)
    hub = y[d.is_hub.to_numpy()]; rest = y[~d.is_hub.to_numpy()]
    vg, vr = hub.var(ddof=1), rest.var(ddof=1)
    _, p = levene(hub, rest, center="median")
    return {"season": season, "n": int(len(d)), "n_hub": int(d.is_hub.sum()),
            "hub_ratio": round(float(vg/vr), 3), "p": float(p),
            "mean_pot_ast_pg_hub": round(float(d[d.is_hub].pot_pg.mean()), 2)}


def main() -> int:
    rows = [hub_ratio(s) for s in SEASONS]
    series = [r["hub_ratio"] for r in rows]
    eras = {"early_pace_space_2013_2016": series[0:3],
            "heliocentric_iso_2016_2019": series[3:6],
            "distributed_2019_2025": series[6:12]}
    era_means = {k: round(float(np.mean(v)), 3) for k, v in eras.items()}
    slope = float(np.polyfit(range(len(series)), series, 1)[0])
    out = {"per_season": rows, "hub_ratio_series": series,
           "era_means": era_means, "trend_slope_per_season": round(slope, 3)}
    (RESULTS / "explore_creation_network_12season.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")

    print("=== 12-season Hub-grip on AST variance (de-heliocentrization arc) ===")
    print(f"{'season':10s} {'n':>4s} {'Hub ratio':>10s} {'p':>9s}  mean potAST/g (hubs)")
    for r in rows:
        print(f"{r['season']:10s} {r['n']:4d} {r['hub_ratio']:10.2f} {r['p']:9.1e}  {r['mean_pot_ast_pg_hub']}")
    print(f"\nEra means:")
    for k, v in era_means.items():
        print(f"  {k:32s} {v}")
    pk = max(rows, key=lambda r: r["hub_ratio"])
    print(f"\nPeak Hub-grip season: {pk['season']} (ratio {pk['hub_ratio']})")
    print(f"12-season trend slope: {slope:+.3f}/season")
    print("\n-> explore_creation_network_12season.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
