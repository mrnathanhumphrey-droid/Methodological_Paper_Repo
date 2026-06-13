"""
EXPLORATORY (post-hoc, 2024-25 — passing tracking covers it). THE test of the
reframe: creation is a RELATIONAL event (an edge in the passing graph), not a
terminal event with a court-location. So partition playmaking by NETWORK ROLE
(Hub / Connector / Terminal), not by court-region.

Prediction: the network-role cut OWNS AST variance (high ratio, like rim-zone
owned BLK) and BEATS both the position label (Guard) and the failed court-
region cut (off_feast). If so: terminal events partition on space, relational
events partition on the network.

Network roles from the `passing` tracking file:
  Hub       = top tercile of potential_ast/g (the creation engine; ball routes
              through you, you generate looks).
  Connector = non-hub with secondary_ast/g >= median (relay / hockey-assist).
  Terminal  = non-hub, below (receive-and-finish).

Outcome = AST_per36 over the 2024-25 qualifying universe (NO assist floor — the
full low-to-high range must be present to measure the coupling). Compared to
position bucket and off_feast court-region.
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


def main() -> int:
    # qualifying universe + position + AST_per36 (2024-25)
    p0 = pd.read_parquet(RESULTS / "P0_partition_usg.parquet")
    p0 = p0[p0.season == S][["nba_api_id", "name", "pos_bucket"]]
    box = pd.read_parquet(DATA / "historical_box_scores.parquet",
                          columns=["nba_api_id", "season", "season_type", "minutes", "AST"])
    box = box[(box.season == S) & (box.season_type == "Regular Season") & (box.minutes > 0)]
    bg = box.groupby("nba_api_id", as_index=False).agg(gp=("minutes", "size"), mins=("minutes", "sum"), AST=("AST", "sum"))
    bg["AST_per36"] = bg.AST * 36.0 / bg.mins
    m = p0.merge(bg, on="nba_api_id", how="inner")

    # passing graph signatures
    pas = pd.read_parquet(DATA / "player_tracking_passing.parquet")
    pas = pas[pas.season == S]
    keep = ["nba_api_id", "passes_made", "passes_received", "secondary_ast",
            "potential_ast", "ast_pts_created", "ast_to_pass_pct"]
    keep = [c for c in keep if c in pas.columns]
    pas = pas.groupby("nba_api_id", as_index=False)[keep[1:]].sum() if "gp" not in pas.columns \
          else pas.groupby("nba_api_id", as_index=False).agg({**{c: "sum" for c in keep[1:]}})
    m = m.merge(pas, on="nba_api_id", how="left")
    m = m[m.potential_ast.notna() & m.passes_received.notna()].copy()

    # per-game normalize (tracking are season totals here)
    for c in ["passes_made", "passes_received", "secondary_ast", "potential_ast"]:
        m[c + "_pg"] = m[c] / m.gp
    m["out_in"] = m.passes_made / m.passes_received.clip(lower=1)

    # ---- network role ----
    hub_cut = m.potential_ast_pg.quantile(2/3)
    m["network_role"] = np.where(m.potential_ast_pg >= hub_cut, "Hub", "TBD")
    non = m[m.network_role == "TBD"]
    sec_med = non.secondary_ast_pg.median()
    m.loc[(m.network_role == "TBD") & (m.secondary_ast_pg >= sec_med), "network_role"] = "Connector"
    m.loc[m.network_role == "TBD", "network_role"] = "Terminal"

    # off_feast court-region (the failed spatial cut) for 2024-25
    poff = pd.read_parquet(RESULTS / "P0_partition_off_feast.parquet")
    poff = poff[(poff.season == S) & (poff.cell_id != "Profile-Sparse")][["nba_api_id", "region"]]
    m = m.merge(poff, on="nba_api_id", how="left")

    print(f"n = {len(m)} (2024-25 qualifying, with passing)")
    print("network_role:", m.network_role.value_counts().to_dict())
    print("\nTop 12 Hubs by potential_ast/g (face-validity check):")
    print(m.sort_values("potential_ast_pg", ascending=False)
            .head(12)[["name", "potential_ast_pg", "AST_per36", "pos_bucket", "network_role"]]
            .to_string(index=False))

    y = m.AST_per36.to_numpy(float)
    r_net = {role: vratio(y, (m.network_role == role).to_numpy()) for role in ["Hub", "Connector", "Terminal"]}
    r_pos = {p: vratio(y, (m.pos_bucket == p).to_numpy()) for p in ["Guard", "Forward", "Center"]}
    r_reg = {reg: vratio(y, (m.region == reg).to_numpy()) for reg in m.region.dropna().unique()}
    b_net, b_pos, b_reg = best(r_net), best(r_pos), best(r_reg)

    out = {"n": len(m), "hub_cut_potential_ast_pg": round(float(hub_cut), 2),
           "network_role": {k: v for k, v in r_net.items()},
           "position": r_pos, "court_region_off_feast": r_reg,
           "best_network": b_net, "best_position": b_pos, "best_court_region": b_reg,
           "network_beats_position": bool(b_net[1] > b_pos[1]),
           "network_beats_court_region": bool(b_net[1] > b_reg[1])}
    (RESULTS / "explore_creation_network.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")

    print("\n=== AST_per36 variance ratio: which axis OWNS the coupling? ===")
    print(f"  NETWORK ROLE   best: {b_net[0]:10s} ratio={b_net[1]}   all={ {k: v['ratio'] for k,v in r_net.items()} }")
    print(f"  POSITION       best: {b_pos[0]:10s} ratio={b_pos[1]}   all={ {k: v['ratio'] for k,v in r_pos.items()} }")
    print(f"  COURT-REGION   best: {b_reg[0]:10s} ratio={b_reg[1]}   all={ {k: v['ratio'] for k,v in r_reg.items()} }")
    print(f"\n  network beats position?     {out['network_beats_position']}")
    print(f"  network beats court-region? {out['network_beats_court_region']}")
    print("\n-> explore_creation_network.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
