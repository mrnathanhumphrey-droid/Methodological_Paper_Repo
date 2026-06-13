"""
Geographic arm — Stage 5: GEO_F3 + GEO_F4 falsifiers + consolidated GEO_F1-F4.

GEO_F3 (within-vs-between consistency): per unit, does the within-unit sorting
(Stage 3, density beta_s sign) contradict the unit's between-corridor regime
(Stage 2, dominant regime of corridors where the unit is destination)?
Concentrating~agglomeration, Diffusing~dispersion; boson~agglomeration,
fermion~dispersion. Fire if contradictory on >=30% of units.

GEO_F4 (predictive transfer): corridor regimes fit on training 2012-2017 should
predict the 2018-2021 holdout. Cohen's kappa (+ accuracy sanity) between training
and holdout regime labels. kappa>=0.4 -> transfers (does not fire).

Output: results/geo_falsifiers_summary.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, str(Path(__file__).parent))
from geo_stage2_corridor_momentflow import classify

RESULTS = Path(r"D:\Migration\results")
TRAIN = list(range(2012, 2018))
HOLD = list(range(2018, 2022))


def reclassify(traj, years):
    out = {}
    for (i, j), g in traj.groupby(["orig", "dest"]):
        gt = g[g.year.isin(years)].sort_values("year")
        if gt.year.nunique() < len(years):
            continue
        yrs = gt.year.to_numpy(float)
        mu_dot = float(np.polyfit(yrs, gt.mu, 1)[0]); mu_bar = gt.mu.mean()
        var_dot = float(np.polyfit(yrs, gt["var"], 1)[0]); var_bar = gt["var"].mean()
        r_mu = mu_dot / mu_bar if abs(mu_bar) > 1e-9 else np.inf
        r_var = var_dot / var_bar if abs(var_bar) > 1e-9 else np.inf
        out[(i, j)] = classify(r_mu, r_var)
    return out


def geo_f4(level):
    traj = pd.read_parquet(RESULTS / f"geo_corridor_trajectories_{level}.parquet")
    tr = reclassify(traj, TRAIN); ho = reclassify(traj, HOLD)
    common = sorted(set(tr) & set(ho))
    if len(common) < 5:
        return dict(level=level, n=len(common), kappa=None, accuracy=None)
    a = [tr[c] for c in common]; b = [ho[c] for c in common]
    kappa = float(cohen_kappa_score(a, b))
    acc = float(np.mean([x == y for x, y in zip(a, b)]))
    return dict(level=level, n_corridors=len(common), kappa=kappa, accuracy=acc,
                fires=kappa < 0.4)


def geo_f3(level):
    reg = pd.read_parquet(RESULTS / f"geo_corridor_regimes_{level}.parquet")
    sig = pd.read_parquet(RESULTS / f"geo_within_signatures_{level}.parquet")
    # between: dominant regime among corridors where unit is destination
    btw_mech = {}
    for u, g in reg.groupby("dest"):
        dom = g.regime.value_counts().idxmax()
        btw_mech[u] = "agg" if dom == "Concentrating" else "disp" if dom == "Diffusing" else "neutral"
    # within: density beta_s sorting sign
    den = sig[sig.observable == "log_dest_density"].set_index("unit")
    win_mech = {}
    for u, r in den.iterrows():
        win_mech[u] = "agg" if r.sorting == "boson(+)" else "disp" if r.sorting == "fermion(-)" else "neutral"
    units = sorted(set(btw_mech) & set(win_mech))
    contra = 0; comparable = 0
    for u in units:
        b, w = btw_mech[u], win_mech[u]
        if b == "neutral" or w == "neutral":
            continue
        comparable += 1
        if b != w:
            contra += 1
    rate = contra / comparable if comparable else 0.0
    return dict(level=level, units_comparable=comparable, contradictions=contra,
                contra_rate=rate, fires=rate >= 0.30)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    grav = json.loads((RESULTS / "geo_gravity_baseline.json").read_text())
    tens = json.loads((RESULTS / "geo_tensor_factors.json").read_text())

    summary = {"GEO_F1": {}, "GEO_F2": {}, "GEO_F3": {}, "GEO_F4": {}}
    print("=== GEO falsifier summary ===\n")

    # F1 (from Stage 1)
    print("GEO_F1 (gravity-only, pseudo-R2>=0.80):")
    for lvl in ["division", "state"]:
        r2 = grav[lvl]["gravity"]["mcfadden_pseudo_r2"]
        fires = r2 >= 0.80
        summary["GEO_F1"][lvl] = dict(pseudo_r2=r2, fires=fires)
        print(f"  {lvl}: pseudo-R2={r2:.3f} -> {'FIRES' if fires else 'does not fire'}")

    # F2 (from Stage 4, divisions)
    cong = tens["geo_f2_split_half_congruence"]
    summary["GEO_F2"] = dict(division_congruence=cong, fires=cong < 0.5)
    print(f"\nGEO_F2 (tensor factor stability, congruence<0.5):")
    print(f"  division: congruence={cong:.3f} -> {'FIRES' if cong<0.5 else 'does not fire'}")

    # F3
    print(f"\nGEO_F3 (within-vs-between contradiction>=30%):")
    for lvl in ["division", "state"]:
        f3 = geo_f3(lvl); summary["GEO_F3"][lvl] = f3
        print(f"  {lvl}: {f3['contradictions']}/{f3['units_comparable']} = "
              f"{100*f3['contra_rate']:.0f}% -> {'FIRES' if f3['fires'] else 'does not fire'}")

    # F4
    print(f"\nGEO_F4 (holdout transfer, kappa<0.4):")
    for lvl in ["division", "state"]:
        f4 = geo_f4(lvl); summary["GEO_F4"][lvl] = f4
        if f4.get("kappa") is None:
            print(f"  {lvl}: insufficient corridors")
        else:
            print(f"  {lvl}: kappa={f4['kappa']:.3f}, acc={f4['accuracy']:.2f}, "
                  f"n={f4['n_corridors']} -> {'FIRES' if f4['fires'] else 'does not fire'}")

    (RESULTS / "geo_falsifiers_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nwritten: results/geo_falsifiers_summary.json")


if __name__ == "__main__":
    main()
