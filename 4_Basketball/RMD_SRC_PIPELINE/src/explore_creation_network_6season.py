"""
EXPLORATORY (post-hoc). 6-season (2019-20..2024-25) decomposition of the
creation-coupling: does the network-role (Hub) grip on AST variance hold across
seasons, and does the WHERE modulation (Rim->finisher / Paint->creator-big /
Perimeter->neutral) drift within the modern era? Hardens the single-season
2024-25 capstone (Hub 2.69) into a 6-season result + per-season drift.

Per season: build Hub/Connector/Terminal (within-season terciles), compute
AST_per36 variance ratio by network-role, position, and off_feast court-region.
Pooled = within-season role assignment, then variance ratio over all stacked
player-seasons.
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
SEASONS = ["2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]


def vratio(vals, mask):
    g = vals[mask]; r = vals[~mask]
    g = g[np.isfinite(g)]; r = r[np.isfinite(r)]
    if len(g) < 5 or len(r) < 5:
        return float("nan"), int(len(g))
    vg, vr = g.var(ddof=1), r.var(ddof=1)
    return (round(float(vg/vr), 3) if vr > 0 else float("nan")), int(len(g))


def build_season(season: str) -> pd.DataFrame:
    p0 = pd.read_parquet(RESULTS / "P0_partition_usg.parquet")
    p0 = p0[p0.season == season][["nba_api_id", "name", "pos_bucket"]]
    box = pd.read_parquet(DATA / "historical_box_scores.parquet",
                          columns=["nba_api_id", "season", "season_type", "minutes", "AST"])
    box = box[(box.season == season) & (box.season_type == "Regular Season") & (box.minutes > 0)]
    bg = box.groupby("nba_api_id", as_index=False).agg(gp=("minutes", "size"), mins=("minutes", "sum"), AST=("AST", "sum"))
    bg["AST_per36"] = bg.AST * 36.0 / bg.mins
    m = p0.merge(bg, on="nba_api_id", how="inner")

    pas = pd.read_parquet(DATA / "player_tracking_passing.parquet")
    pas = pas[pas.season == season]
    cols = [c for c in ["passes_made", "passes_received", "secondary_ast", "potential_ast"] if c in pas.columns]
    pas = pas.groupby("nba_api_id", as_index=False)[cols].sum()
    m = m.merge(pas, on="nba_api_id", how="left")
    m = m[m.potential_ast.notna()].copy()
    for c in cols: m[c + "_pg"] = m[c] / m.gp

    hub_cut = m.potential_ast_pg.quantile(2/3)
    m["network_role"] = np.where(m.potential_ast_pg >= hub_cut, "Hub", "TBD")
    non = m[m.network_role == "TBD"]
    sec_med = non.secondary_ast_pg.median()
    m.loc[(m.network_role == "TBD") & (m.secondary_ast_pg >= sec_med), "network_role"] = "Connector"
    m.loc[m.network_role == "TBD", "network_role"] = "Terminal"

    poff = pd.read_parquet(RESULTS / "P0_partition_off_feast.parquet")
    poff = poff[(poff.season == season) & (poff.cell_id != "Profile-Sparse")][["nba_api_id", "region"]]
    m = m.merge(poff, on="nba_api_id", how="left")
    m["season"] = season
    return m


def coupling(m: pd.DataFrame) -> dict:
    y = m.AST_per36.to_numpy(float)
    hub_r, hub_n = vratio(y, (m.network_role == "Hub").to_numpy())
    guard_r, guard_n = vratio(y, (m.pos_bucket == "Guard").to_numpy())
    reg = {}
    for r in ["Rim", "Paint", "Perimeter"]:
        rr, rn = vratio(y, (m.region == r).to_numpy())
        reg[r] = {"ratio": rr, "n": rn}
    return {"n": len(m), "Hub": {"ratio": hub_r, "n": hub_n},
            "Guard": {"ratio": guard_r, "n": guard_n}, "court_region": reg}


def main() -> int:
    per_season = {}
    frames = []
    for s in SEASONS:
        m = build_season(s)
        per_season[s] = coupling(m)
        frames.append(m)
    pooled = pd.concat(frames, ignore_index=True)
    pooled_c = coupling(pooled)

    out = {"per_season": per_season, "pooled": pooled_c}
    (RESULTS / "explore_creation_network_6season.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")

    print("=== Network-role (Hub) grip on AST variance, per season ===")
    print(f"{'season':10s} {'n':>4s} {'Hub':>7s} {'Guard':>7s} | court-region (Rim/Paint/Perim)")
    for s in SEASONS:
        c = per_season[s]
        rg = c["court_region"]
        print(f"{s:10s} {c['n']:4d} {c['Hub']['ratio']:7.2f} {c['Guard']['ratio']:7.2f} | "
              f"Rim {rg['Rim']['ratio']:.2f}(n{rg['Rim']['n']})  Paint {rg['Paint']['ratio']:.2f}(n{rg['Paint']['n']})  "
              f"Perim {rg['Perimeter']['ratio']:.2f}(n{rg['Perimeter']['n']})")
    print(f"\n=== POOLED (6 seasons, within-season role assignment) ===")
    rg = pooled_c["court_region"]
    print(f"  n={pooled_c['n']}  Hub={pooled_c['Hub']['ratio']} (n{pooled_c['Hub']['n']})  "
          f"Guard={pooled_c['Guard']['ratio']} (n{pooled_c['Guard']['n']})")
    print(f"  court-region: Rim {rg['Rim']['ratio']}(n{rg['Rim']['n']})  "
          f"Paint {rg['Paint']['ratio']}(n{rg['Paint']['n']})  Perim {rg['Perimeter']['ratio']}(n{rg['Perimeter']['n']})")

    hub_series = [per_season[s]["Hub"]["ratio"] for s in SEASONS]
    print(f"\n=== DRIFT ===")
    print(f"  Hub ratio by season: {[round(x,2) for x in hub_series]}")
    sl = np.polyfit(range(len(hub_series)), hub_series, 1)[0]
    print(f"  Hub trend slope: {sl:+.3f}/season ({'strengthening' if sl>0.05 else 'weakening' if sl<-0.05 else 'stable'})")
    print(f"  Hub > Guard every season? {all(per_season[s]['Hub']['ratio'] > per_season[s]['Guard']['ratio'] for s in SEASONS)}")
    print("\n-> explore_creation_network_6season.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
