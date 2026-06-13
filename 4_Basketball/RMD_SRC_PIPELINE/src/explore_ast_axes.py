"""
EXPLORATORY (post-hoc, single-season 2024-25 — tracking data only covers it).
AST coupling: WHERE you create (#1 playmaking-origin) vs HOW you create
(#2 creation-role / on-ball play-style) vs position label (#3). Plus the
dependency question: is HOW dependent on WHERE? (are #1 and #2 separable axes,
or is on-ball-hub-ness just a consequence of court origin?)

Outcome = AST_per36 (2024-25 player-season). Partitions:
  #1 origin region: plurality of assist origin among
     {drive, paint_touch, post_touch, elbow_touch, perimeter-residual}
  #2 creation-role tier: terciles of avg_drib_per_touch (on-ball intensity)
  #3 position bucket (Guard/Forward/Center)
Variance ratio = Var(AST|group)/Var(AST|rest) + Levene p (marginal +
conditional on the other axis). Dependency = eta^2 of avg_drib_per_touch
across origin regions + crosstab.
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
S = "2024-25"


def vratio(vals, mask):
    g = vals[mask]; r = vals[~mask]
    g = g[np.isfinite(g)]; r = r[np.isfinite(r)]
    if len(g) < 5 or len(r) < 5:
        return {"ratio": float("nan"), "p": float("nan"), "n": int(len(g))}
    vg, vr = g.var(ddof=1), r.var(ddof=1)
    try: _, p = levene(g, r, center="median")
    except Exception: p = float("nan")
    return {"ratio": round(float(vg/vr), 3) if vr > 0 else float("nan"),
            "p": float(p), "n": int(len(g))}


def best(d):
    items = [(k, v["ratio"]) for k, v in d.items() if np.isfinite(v["ratio"])]
    return max(items, key=lambda t: t[1]) if items else (None, float("nan"))


def load_touch_ast(f, col):
    d = pd.read_parquet(DATA / f"{f}.parquet"); d = d[d.season == S]
    return d.groupby("nba_api_id", as_index=False).agg(**{col: (col, "sum"), f"{col}_gp": ("gp", "max")})


def main() -> int:
    # outcome
    box = pd.read_parquet(DATA / "historical_box_scores.parquet",
                          columns=["nba_api_id", "season", "season_type", "minutes", "AST"])
    box = box[(box.season == S) & (box.season_type == "Regular Season") & (box.minutes > 0)]
    bg = box.groupby("nba_api_id", as_index=False).agg(gp=("minutes", "size"), mins=("minutes", "sum"), AST=("AST", "sum"))
    bg["AST_per36"] = bg.AST * 36.0 / bg.mins
    bg["ast_pg"] = bg.AST / bg.gp

    # assist origins
    dr = load_touch_ast("player_tracking_drives", "drive_ast")
    pt = load_touch_ast("player_tracking_painttouch", "paint_touch_ast")
    po = load_touch_ast("player_tracking_posttouch", "post_touch_ast")
    el = load_touch_ast("player_tracking_elbowtouch", "elbow_touch_ast")
    m = bg.merge(dr, on="nba_api_id", how="left").merge(pt, on="nba_api_id", how="left") \
          .merge(po, on="nba_api_id", how="left").merge(el, on="nba_api_id", how="left")
    O = ["drive_ast", "paint_touch_ast", "post_touch_ast", "elbow_touch_ast"]
    for c in O: m[c] = m[c].fillna(0.0)
    # unit detection: are touch-ast totals or per-game? compare sum-of-origins to ast_pg.
    raw_sum = m[O].sum(axis=1)
    is_totals = (raw_sum / m.gp).median() < (raw_sum.median() / 3)  # heuristic
    if raw_sum.median() > m.ast_pg.median() * 3:  # origins look like season totals
        for c in O: m[c] = m[c] / m.gp
        unit_note = "touch-ast were season totals -> converted to per-game"
    else:
        unit_note = "touch-ast already per-game"
    # The 4 tracked touch-types capture only a MINORITY of total assists (PnR
    # passes, handoffs, transition are untracked), so a total-AST residual
    # swamps everyone. Build the WHERE axis over the TRACKABLE creation contexts
    # only: among {Drive, Paint, Post, Elbow}, which dominates your assists.
    SIMP = O
    tot = m[SIMP].sum(axis=1).replace(0, np.nan)
    NAME = {"drive_ast": "Drive", "paint_touch_ast": "Paint",
            "post_touch_ast": "Post", "elbow_touch_ast": "Elbow"}
    for c in SIMP: m[c + "_sh"] = m[c] / tot
    # require enough tracked-assist volume to have a stable origin profile
    m = m[(m.ast_pg >= 2.0) & tot.notna() & (m[O].sum(axis=1) >= 0.5)].copy()
    m["origin_region"] = m[[c + "_sh" for c in SIMP]].idxmax(axis=1).str.replace("_sh", "", regex=False).map(NAME)

    # creation-role (#2): avg_drib_per_touch terciles
    poss = pd.read_parquet(DATA / "player_tracking_possessions.parquet")
    poss = poss[poss.season == S][["nba_api_id", "avg_sec_per_touch", "avg_drib_per_touch", "touches", "front_ct_touches"]]
    m = m.merge(poss, on="nba_api_id", how="left")
    m = m[m.avg_drib_per_touch.notna()].copy()
    q1, q2 = m.avg_drib_per_touch.quantile([1/3, 2/3]).values
    m["role_tier"] = np.where(m.avg_drib_per_touch >= q2, "OnBallHub",
                       np.where(m.avg_drib_per_touch >= q1, "Mid", "OffBall"))

    # position
    p0 = pd.read_parquet(RESULTS / "P0_partition_usg.parquet")
    posmap = p0.groupby("nba_api_id").pos_bucket.agg(lambda s: s.value_counts().index[0])
    m["pos_bucket"] = m.nba_api_id.map(posmap)

    print(f"n (ast_pg>=2, w/ origin+role): {len(m)}   [{unit_note}]")
    print("origin_region:", m.origin_region.value_counts().to_dict())
    print("role_tier:", m.role_tier.value_counts().to_dict())

    y = m.AST_per36.to_numpy(float)
    # ---- marginal variance ratios ----
    r1 = {reg: vratio(y, (m.origin_region == reg).to_numpy()) for reg in m.origin_region.unique()}
    r2 = {t: vratio(y, (m.role_tier == t).to_numpy()) for t in ["OnBallHub", "Mid", "OffBall"]}
    r3 = {p: vratio(y, (m.pos_bucket == p).to_numpy()) for p in ["Guard", "Forward", "Center"]}
    b1, b2, b3 = best(r1), best(r2), best(r3)

    # ---- dependency: is HOW dependent on WHERE? eta^2 of drib_per_touch across origin regions ----
    grand = m.avg_drib_per_touch.mean()
    ss_tot = ((m.avg_drib_per_touch - grand) ** 2).sum()
    ss_between = sum(len(g) * (g.avg_drib_per_touch.mean() - grand) ** 2
                     for _, g in m.groupby("origin_region"))
    eta2 = float(ss_between / ss_tot) if ss_tot > 0 else float("nan")
    drib_by_origin = {reg: round(float(g.avg_drib_per_touch.mean()), 2)
                      for reg, g in m.groupby("origin_region")}
    crosstab = pd.crosstab(m.origin_region, m.role_tier)

    # ---- conditional: does the winning axis survive controlling for the other? ----
    # #2 (role) within the dominant origin region; #1 (origin) within dominant role tier
    cond = {}
    dom_origin = b1[0]; dom_role = b2[0]
    sub_o = m[m.origin_region == dom_origin]
    if len(sub_o) >= 15:
        yo = sub_o.AST_per36.to_numpy(float)
        cond["role_within_" + str(dom_origin)] = {
            t: vratio(yo, (sub_o.role_tier == t).to_numpy()) for t in ["OnBallHub", "Mid", "OffBall"]}
    sub_r = m[m.role_tier == dom_role]
    if len(sub_r) >= 15:
        yr = sub_r.AST_per36.to_numpy(float)
        cond["origin_within_" + str(dom_role)] = {
            reg: vratio(yr, (sub_r.origin_region == reg).to_numpy()) for reg in sub_r.origin_region.unique()}

    out = {"unit_note": unit_note, "n": len(m),
           "marginal": {"origin_region": r1, "role_tier": r2, "position": r3,
                        "best_origin": b1, "best_role": b2, "best_position": b3},
           "dependency_how_on_where": {"eta2_drib_per_touch_across_origin": round(eta2, 3),
                                        "mean_drib_per_touch_by_origin": drib_by_origin,
                                        "crosstab_origin_x_role": crosstab.to_dict()},
           "conditional": cond}
    (RESULTS / "explore_ast_axes.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")

    print("\n=== MARGINAL AST variance ratio (which axis owns the coupling) ===")
    print(f"  #1 WHERE  best origin-region: {b1[0]:10s} ratio={b1[1]}   all={ {k:v['ratio'] for k,v in r1.items()} }")
    print(f"  #2 HOW    best role-tier:     {b2[0]:10s} ratio={b2[1]}   all={ {k:v['ratio'] for k,v in r2.items()} }")
    print(f"  #3 POS    best position:      {b3[0]:10s} ratio={b3[1]}   all={ {k:v['ratio'] for k,v in r3.items()} }")
    print(f"\n=== DEPENDENCY: is HOW dependent on WHERE? ===")
    print(f"  eta^2(avg_drib_per_touch ~ origin_region) = {eta2:.3f}  (0=orthogonal, 1=fully determined by location)")
    print(f"  mean dribbles/touch by origin: {drib_by_origin}")
    print(f"  crosstab origin x role:\n{crosstab.to_string()}")
    print(f"\n=== CONDITIONAL (does winner survive controlling for the other) ===")
    for k, d in cond.items():
        print(f"  {k}: { {kk: vv['ratio'] for kk, vv in d.items()} }")
    print("\n-> explore_ast_axes.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
