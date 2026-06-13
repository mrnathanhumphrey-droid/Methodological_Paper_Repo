"""
Robustness battery for the spatial re-axis null (exploratory, post-hoc — NOT
pre-registered; clearly labeled as such in RESULTS_SPATIAL.md).

1. BLK/REB variance-RATIO relocation (the load-bearing cross-sectional test):
   the original BLK x Center coupling was a variance ratio [1.64, 2.01]. Does
   that ratio relocate to the def_feast RimProtector cell? Levene group-vs-rest
   per stat, by def-region vs by position, pooled + per-season.
2. Bootstrap 95% CI on F4 kappa per (arm, observable) — is the no-transfer
   null robust or a point-estimate fluke? (pre-reg §8 asks for bootstrap CI.)
3. Bootstrap 95% CI on the off-vs-def F2-clean difference (P3's surviving half).
4. Holdout 2-point fragility: count Insufficient_data holdout cells.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
import numpy as np, pandas as pd
from scipy.stats import levene
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, str(Path(__file__).parent))
from _common import ALL_SEASONS, HOLDOUT_SEASONS, OBSERVABLES, RESULTS
from step05_falsifiers_and_comparative import REGIME_CODE

DATA = Path(r"D:/NBA Projections/data/parquet")
RNG = np.random.RandomState(20260610)


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


def variance_ratio(values: np.ndarray, mask_group: np.ndarray) -> dict:
    """Var(group)/Var(rest) + Levene p, group vs complement."""
    grp = values[mask_group]; rest = values[~mask_group]
    grp = grp[np.isfinite(grp)]; rest = rest[np.isfinite(rest)]
    if len(grp) < 5 or len(rest) < 5:
        return {"ratio": float("nan"), "p_levene": float("nan"),
                "n_group": int(len(grp)), "var_group": float("nan")}
    vg, vr = grp.var(ddof=1), rest.var(ddof=1)
    try:
        _, p = levene(grp, rest, center="median")
    except Exception:
        p = float("nan")
    return {"ratio": float(vg / vr) if vr > 0 else float("nan"),
            "p_levene": float(p), "n_group": int(len(grp)),
            "var_group": float(vg)}


def relocation_test() -> dict:
    rates = player_season_rates()
    pdef = pd.read_parquet(RESULTS / "P0_partition_def_feast.parquet")
    pdef = pdef[pdef.cell_id != "Profile-Sparse"]
    df = rates.merge(pdef[["nba_api_id", "season", "region", "pos_bucket"]],
                     on=["nba_api_id", "season"], how="inner")
    out = {"pooled": {}, "by_season": {}}
    for stat in ["BLK_per36", "REB_per36"]:
        vals = df[stat].to_numpy(float)
        out["pooled"][stat] = {
            "by_region": {r: variance_ratio(vals, (df.region == r).to_numpy())
                          for r in ["RimProtector", "Hybrid", "Perimeter"]},
            "by_position": {p: variance_ratio(vals, (df.pos_bucket == p).to_numpy())
                            for p in ["Center", "Forward", "Guard"]},
        }
    # per-season ratio for RimProtector vs Center (BLK) — stability
    for stat in ["BLK_per36"]:
        out["by_season"][stat] = {}
        for ssn in ALL_SEASONS:
            d = df[df.season == ssn]; v = d[stat].to_numpy(float)
            out["by_season"][stat][ssn] = {
                "RimProtector": variance_ratio(v, (d.region == "RimProtector").to_numpy()),
                "Center": variance_ratio(v, (d.pos_bucket == "Center").to_numpy()),
            }
    return out


def f4_bootstrap(arm: str, B: int = 2000) -> dict:
    train = pd.read_parquet(RESULTS / f"trajectory_classification_{arm}.parquet")
    hold = pd.read_parquet(RESULTS / f"holdout_step2_{arm}.parquet")
    m = train.merge(hold, on=["cell_id", "observable"], how="inner")
    out = {}
    for obs in OBSERVABLES:
        sub = m[m.observable == obs]
        a = np.array([REGIME_CODE.get(r, 6) for r in sub.regime])
        b = np.array([REGIME_CODE.get(r, 6) for r in sub.regime_holdout])
        n = len(a)
        if n < 3:
            out[obs] = {"kappa": float("nan"), "ci": [None, None], "n": n}; continue
        boots = []
        for _ in range(B):
            idx = RNG.randint(0, n, n)
            try:
                if len(set(a[idx]) | set(b[idx])) > 1:
                    boots.append(cohen_kappa_score(a[idx], b[idx]))
            except Exception:
                pass
        try:
            k = float(cohen_kappa_score(a, b))
        except Exception:
            k = float("nan")
        ci = ([float(np.nanpercentile(boots, 2.5)),
               float(np.nanpercentile(boots, 97.5))] if boots else [None, None])
        out[obs] = {"kappa": k, "ci": ci, "n": n,
                    "straddles_zero": bool(ci[0] is not None and ci[0] <= 0 <= ci[1])}
    return out


def f2_diff_bootstrap(B: int = 2000) -> dict:
    def clean_flags(arm):
        cls = pd.read_parquet(RESULTS / f"trajectory_classification_{arm}.parquet")
        val = pd.read_parquet(RESULTS / f"step03_validation_{arm}.parquet")
        m = cls.merge(val[["cell_id", "observable", "clean"]],
                      on=["cell_id", "observable"], how="left")
        m = m[m.regime != "Edge"]  # Edge excluded from F2 denom
        m["terminates"] = ((m.regime == "Stationary")
                           | (m.regime.isin(["Concentrating", "Diffusing",
                                             "Contracting", "Drifting"]) & (m.clean == True)))
        return m["terminates"].to_numpy()
    off = clean_flags("off_feast"); dfn = clean_flags("def_feast")
    diff = off.mean() - dfn.mean()
    boots = []
    for _ in range(B):
        bo = off[RNG.randint(0, len(off), len(off))].mean()
        bd = dfn[RNG.randint(0, len(dfn), len(dfn))].mean()
        boots.append(bo - bd)
    return {"off_F2": float(off.mean()), "def_F2": float(dfn.mean()),
            "diff": float(diff),
            "ci": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
            "diff_excludes_zero": bool(np.percentile(boots, 2.5) > 0
                                       or np.percentile(boots, 97.5) < 0)}


def holdout_fragility() -> dict:
    out = {}
    for arm in ["off_feast", "def_feast", "usg"]:
        h = pd.read_parquet(RESULTS / f"holdout_step2_{arm}.parquet")
        out[arm] = {"n_cells_obs": int(len(h)),
                    "n_insufficient": int((h.regime_holdout == "Insufficient_data").sum())}
    return out


def main() -> int:
    print("Computing robustness battery...")
    res = {
        "relocation_variance_ratio": relocation_test(),
        "f4_bootstrap_ci": {a: f4_bootstrap(a) for a in ["off_feast", "def_feast", "usg"]},
        "f2_offense_vs_defense_diff": f2_diff_bootstrap(),
        "holdout_2pt_fragility": holdout_fragility(),
    }
    (RESULTS / "robustness_spatial.json").write_text(
        json.dumps(res, indent=2, default=str), encoding="utf-8")

    # console headline
    rel = res["relocation_variance_ratio"]["pooled"]["BLK_per36"]
    print("\n=== BLK variance-ratio relocation (pooled) ===")
    for r, d in rel["by_region"].items():
        print(f"  region {r:13s}: ratio={d['ratio']:.3f}  n={d['n_group']:4d}  p_levene={d['p_levene']:.1e}")
    for p, d in rel["by_position"].items():
        print(f"  pos    {p:13s}: ratio={d['ratio']:.3f}  n={d['n_group']:4d}  p_levene={d['p_levene']:.1e}")
    print("\n=== F4 bootstrap CI (BLK) ===")
    for a in ["off_feast", "def_feast", "usg"]:
        b = res["f4_bootstrap_ci"][a]["BLK_per36"]
        print(f"  {a:10s} κ={b['kappa']:+.3f} CI=[{b['ci'][0]:+.3f},{b['ci'][1]:+.3f}] straddles0={b['straddles_zero']}")
    fd = res["f2_offense_vs_defense_diff"]
    print(f"\n=== F2 off-def diff: {fd['diff']:+.3f} CI=[{fd['ci'][0]:+.3f},{fd['ci'][1]:+.3f}] excludes0={fd['diff_excludes_zero']}")
    print(f"\n-> robustness_spatial.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
