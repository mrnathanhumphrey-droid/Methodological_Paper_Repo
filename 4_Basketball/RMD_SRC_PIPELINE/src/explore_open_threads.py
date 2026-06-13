"""
EXPLORATORY (post-hoc, NOT pre-registered) — open-thread sensitivity analyses
on the completed spatial re-axis study (pre-reg cd40b46). Does NOT modify any
locked artifact or verdict. All results reported; no cherry-pick.

A. Full coupling-relocation map: for each observable, variance ratio
   Var(group)/Var(rest) by off-region, def-region, and position. Which
   court-region owns each stat's coupling, and does it beat the position cut?

B. Dynamic-null robustness: recompute F4 regime-transfer kappa under
   alternative temporal splits (locked 5/2, plus 3/4 and 4/3) to test whether
   kappa~0 is 2-season-holdout fragility or a real substrate property.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
import numpy as np, pandas as pd
from scipy.stats import levene
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, str(Path(__file__).parent))
from _common import ALL_SEASONS, OBSERVABLES, RESULTS
from step02_classify_trajectories import classify, ols_slope, MU_BAR_FLOOR, VAR_BAR_FLOOR
from step05_falsifiers_and_comparative import REGIME_CODE

DATA = Path(r"D:/NBA Projections/data/parquet")


def player_season_rates() -> pd.DataFrame:
    bs = pd.read_parquet(DATA / "historical_box_scores.parquet",
                         columns=["nba_api_id", "season", "season_type",
                                  "minutes", "PTS", "REB", "AST", "BLK"])
    bs = bs[(bs.season_type == "Regular Season") & (bs.season.isin(ALL_SEASONS))
            & (bs.minutes > 0)]
    g = bs.groupby(["nba_api_id", "season"], as_index=False).agg(
        mins=("minutes", "sum"), PTS=("PTS", "sum"), REB=("REB", "sum"),
        AST=("AST", "sum"), BLK=("BLK", "sum"))
    for s in ["PTS", "REB", "AST", "BLK"]:
        g[f"{s}_per36"] = g[s] * 36.0 / g["mins"]
    return g


def vratio(vals, mask):
    grp = vals[mask]; rest = vals[~mask]
    grp = grp[np.isfinite(grp)]; rest = rest[np.isfinite(rest)]
    if len(grp) < 5 or len(rest) < 5:
        return {"ratio": float("nan"), "p": float("nan"), "n": int(len(grp))}
    vg, vr = grp.var(ddof=1), rest.var(ddof=1)
    try: _, p = levene(grp, rest, center="median")
    except Exception: p = float("nan")
    return {"ratio": float(vg / vr) if vr > 0 else float("nan"),
            "p": float(p), "n": int(len(grp))}


def thread_A_relocation_map() -> dict:
    rates = player_season_rates()
    poff = pd.read_parquet(RESULTS / "P0_partition_off_feast.parquet")
    pdef = pd.read_parquet(RESULTS / "P0_partition_def_feast.parquet")
    poff = poff[poff.cell_id != "Profile-Sparse"][["nba_api_id", "season", "region", "pos_bucket"]].rename(columns={"region": "off_region"})
    pdef = pdef[pdef.cell_id != "Profile-Sparse"][["nba_api_id", "season", "region"]].rename(columns={"region": "def_region"})
    df = rates.merge(poff, on=["nba_api_id", "season"], how="inner").merge(
        pdef, on=["nba_api_id", "season"], how="left")
    OFF = ["Rim", "Paint", "Perimeter"]; DEF = ["RimProtector", "Hybrid", "Perimeter"]; POS = ["Center", "Forward", "Guard"]
    out = {}
    for obs in OBSERVABLES:
        v = df[obs].to_numpy(float)
        row = {
            "off_region": {r: vratio(v, (df.off_region == r).to_numpy()) for r in OFF},
            "def_region": {r: vratio(v, (df.def_region == r).to_numpy()) for r in DEF},
            "position":   {p: vratio(v, (df.pos_bucket == p).to_numpy()) for p in POS},
        }
        # best (max-ratio) group per cut
        def best(d):
            items = [(k, x["ratio"]) for k, x in d.items() if np.isfinite(x["ratio"])]
            return max(items, key=lambda t: t[1]) if items else (None, float("nan"))
        bo, bd, bp = best(row["off_region"]), best(row["def_region"]), best(row["position"])
        best_region = bo if bo[1] >= bd[1] else bd
        row["summary"] = {
            "best_off": bo, "best_def": bd, "best_pos": bp,
            "best_court_region": best_region,
            "region_beats_position": bool(best_region[1] > bp[1]),
        }
        out[obs] = row
    return out


def all_season_trajectories(arm: str) -> pd.DataFrame:
    """Per (cell, obs, season): mu, var over per-game per-36 — ALL 7 seasons."""
    p0 = pd.read_parquet(RESULTS / f"P0_partition_{arm}.parquet")
    p0 = p0[p0.cell_id != "Profile-Sparse"]
    bs = pd.read_parquet(DATA / "historical_box_scores.parquet",
                         columns=["nba_api_id", "season", "season_type",
                                  "minutes", "PTS", "REB", "AST", "BLK"])
    bs = bs[(bs.season_type == "Regular Season") & (bs.season.isin(ALL_SEASONS)) & (bs.minutes > 0)].copy()
    qk = set(zip(p0.nba_api_id.astype(int), p0.season.astype(str)))
    bs["_k"] = list(zip(bs.nba_api_id.astype(int), bs.season.astype(str)))
    bs = bs[bs._k.isin(qk)].drop(columns="_k")
    for o, s in [("PTS_per36", "PTS"), ("REB_per36", "REB"), ("AST_per36", "AST"), ("BLK_per36", "BLK")]:
        bs[o] = bs[s] * 36.0 / bs.minutes
    cmap = p0.set_index(["nba_api_id", "season"]).cell_id
    bs["cell_id"] = bs.set_index(["nba_api_id", "season"]).index.map(cmap)
    bs = bs[bs.cell_id.notna()]
    rows = []
    for obs in OBSERVABLES:
        for (cid, ssn), g in bs.groupby(["cell_id", "season"], observed=True):
            v = g[obs].to_numpy(float); v = v[np.isfinite(v)]
            if len(v) == 0: continue
            rows.append({"cell_id": cid, "observable": obs, "season": ssn,
                         "mu": v.mean(), "var": v.var(ddof=1) if len(v) > 1 else 0.0})
    return pd.DataFrame(rows)


def regime_on(seasons: list[str], traj_co: pd.DataFrame) -> str:
    g = traj_co[traj_co.season.isin(seasons)].sort_values("season")
    if len(g) < 2: return "Insufficient_data"
    idx = np.arange(len(g), dtype=float)
    mu = g.mu.to_numpy(float); var = g["var"].to_numpy(float)
    mu_dot, var_dot = ols_slope(idx, mu), ols_slope(idx, var)
    mb, vb = mu.mean(), var.mean()
    r_mu = mu_dot / abs(mb) if abs(mb) > MU_BAR_FLOOR else mu_dot
    r_var = var_dot / abs(vb) if abs(vb) > VAR_BAR_FLOOR else var_dot
    return classify(r_mu, r_var)


def thread_B_dynamic_robustness() -> dict:
    S = list(ALL_SEASONS)
    splits = {
        "locked_5_2":  (S[:5], S[5:]),
        "alt_3_4":     (S[:3], S[3:]),
        "alt_4_3":     (S[:4], S[4:]),
    }
    out = {}
    for arm in ["off_feast", "def_feast", "usg"]:
        traj = all_season_trajectories(arm)
        out[arm] = {}
        for sname, (tr, ho) in splits.items():
            per_obs = {}
            for obs in OBSERVABLES:
                sub = traj[traj.observable == obs]
                a, b = [], []
                for cid, g in sub.groupby("cell_id"):
                    rt = regime_on(tr, g); rh = regime_on(ho, g)
                    a.append(REGIME_CODE.get(rt, 6)); b.append(REGIME_CODE.get(rh, 6))
                if len(a) >= 3 and len(set(a) | set(b)) > 1:
                    try: k = float(cohen_kappa_score(a, b))
                    except Exception: k = float("nan")
                else: k = float("nan")
                per_obs[obs] = round(k, 3) if np.isfinite(k) else None
            kaps = [v for v in per_obs.values() if v is not None]
            out[arm][sname] = {"per_obs": per_obs,
                               "mean": round(float(np.mean(kaps)), 3) if kaps else None,
                               "train_n": len(tr), "hold_n": len(ho)}
    return out


def thread_C_mpg_robustness() -> dict:
    """Do the dynamic metrics (F2 Stationary-frac, F4 locked-split kappa)
    survive swapping usage-tier -> MPG-tier role-cohort? Cross-sectional
    relocation is role-cohort-invariant (marginal variance ratio), so only
    the dynamic layer can move. F2 numerator = Stationary count (dip over-
    fires -> no non-Stationary cell is clean, established)."""
    S = list(ALL_SEASONS); tr, ho = S[:5], S[5:]
    out = {}
    for arm in ["off_feast", "off_feast_mpg", "def_feast", "def_feast_mpg"]:
        traj = all_season_trajectories(arm)
        per_obs_f4 = {}; n_stat = 0; n_nonedge = 0
        for obs in OBSERVABLES:
            sub = traj[traj.observable == obs]
            a, b = [], []
            for cid, g in sub.groupby("cell_id"):
                rt = regime_on(tr, g); rh = regime_on(ho, g)
                a.append(REGIME_CODE.get(rt, 6)); b.append(REGIME_CODE.get(rh, 6))
                if rt != "Edge":
                    n_nonedge += 1
                    if rt == "Stationary": n_stat += 1
            k = (float(cohen_kappa_score(a, b))
                 if len(a) >= 3 and len(set(a) | set(b)) > 1 else float("nan"))
            per_obs_f4[obs] = round(k, 3) if np.isfinite(k) else None
        kaps = [v for v in per_obs_f4.values() if v is not None]
        out[arm] = {"K": int(traj.cell_id.nunique()),
                    "F4_per_obs": per_obs_f4,
                    "F4_mean": round(float(np.mean(kaps)), 3) if kaps else None,
                    "F4_any_clears_040": any(v is not None and v >= 0.40 for v in per_obs_f4.values()),
                    "F2_stationary_frac": round(n_stat / n_nonedge, 3) if n_nonedge else None}
    return out


def main() -> int:
    print("=== Thread A: coupling-relocation map ===")
    A = thread_A_relocation_map()
    for obs in OBSERVABLES:
        s = A[obs]["summary"]
        br, bp = s["best_court_region"], s["best_pos"]
        print(f"  {obs:10s}  best court-region: {br[0]:12s} ratio={br[1]:.3f}   "
              f"best position: {bp[0]:7s} ratio={bp[1]:.3f}   region_beats_pos={s['region_beats_position']}")
    print("\n=== Thread B: F4 robustness to temporal split (BLK + mean) ===")
    B = thread_B_dynamic_robustness()
    for arm in ["off_feast", "def_feast", "usg"]:
        for sn, d in B[arm].items():
            print(f"  {arm:10s} {sn:11s} ({d['train_n']}/{d['hold_n']}): BLK={d['per_obs']['BLK_per36']}  mean={d['mean']}")
    print("\n=== Thread C: mpg-tier role-cohort robustness (dynamic layer) ===")
    C = thread_C_mpg_robustness()
    for arm in ["off_feast", "off_feast_mpg", "def_feast", "def_feast_mpg"]:
        d = C[arm]
        print(f"  {arm:16s} K={d['K']:2d}  F4_mean={d['F4_mean']}  any>=0.40={d['F4_any_clears_040']}  "
              f"F2_stat={d['F2_stationary_frac']}  BLK_F4={d['F4_per_obs']['BLK_per36']}")
    (RESULTS / "explore_open_threads.json").write_text(
        json.dumps({"thread_A_relocation_map": A, "thread_B_dynamic_robustness": B,
                    "thread_C_mpg_robustness": C}, indent=2, default=str), encoding="utf-8")
    print(f"\n-> explore_open_threads.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
