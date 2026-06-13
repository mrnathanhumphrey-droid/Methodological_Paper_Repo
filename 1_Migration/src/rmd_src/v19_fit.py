"""
PRE_REG v1.9 fit — race-stratified gravity + HOLC redline push, falsifiers F1-F3.
(FARA / FOODPUSH_F4 deferred: needs a clean 2010 tract->PUMA crosswalk.)

Per race group g, between-MIGPUMA corridors, HOLC-covered ORIGINS only, flow>=50,
offset=log(window years), origin-MIGPUMA-clustered SE:
  M0_g : a + b*log(mass_o^g) + c*log(mass_d^g) + d*log(dist)
  M1_g : M0_g + bR*redline_D_share(origin)        (CD share also fit, robustness)
beta_R>0 => redlined origins over-emit = the push.

Output: results/v19_foodpush.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.special import gammaln

DERIVED = Path(r"D:\Migration\data\derived")
RESULTS = Path(r"D:\Migration\results")
TRAIN = list(range(2012, 2018))
HOLD = list(range(2018, 2022))
MIN_FLOW = 50
GROUPS = ["NH_White", "NH_Black", "Hispanic", "NH_AsianPI", "NH_Other", "NH_AIAN"]


def haversine(lo1, la1, lo2, la2):
    R = 6371.0088
    lo1, la1, lo2, la2 = map(np.radians, [lo1, la1, lo2, la2])
    a = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def poisson_ll(y, mu):
    mu = np.clip(np.asarray(mu, float), 1e-9, None)
    y = np.asarray(y, float)
    return float(np.sum(y * np.log(mu) - mu - gammaln(y + 1)))


FLOWS = pd.read_parquet(DERIVED / "race_corridor_flows_2010.parquet")
POPR = pd.read_parquet(DERIVED / "migpuma_population_by_race_2010.parquet")
GEO = pd.read_parquet(DERIVED / "migpuma_geometry_2010.parquet")
HOLC = pd.read_parquet(DERIVED / "migpuma_holc_2010.parquet")
CENT = GEO.set_index(["statefip", "migpuma"])[["lon", "lat"]]


def build_design(years, race):
    f = FLOWS[(FLOWS.race_group == race) & (FLOWS.YEAR.isin(years))]
    od = (f.groupby(["orig_state", "orig_migpuma", "dest_state", "dest_migpuma"])
          .flow.sum().reset_index())
    pr = (POPR[(POPR.race_group == race) & (POPR.year.isin(years))]
          .groupby(["statefip", "migpuma"]).population.mean().reset_index())
    mo = pr.rename(columns={"statefip": "orig_state", "migpuma": "orig_migpuma", "population": "mass_o"})
    md = pr.rename(columns={"statefip": "dest_state", "migpuma": "dest_migpuma", "population": "mass_d"})
    od = od.merge(mo, on=["orig_state", "orig_migpuma"], how="inner")
    od = od.merge(md, on=["dest_state", "dest_migpuma"], how="inner")
    # HOLC redline at ORIGIN (inner -> restrict to HOLC-covered origins)
    h = HOLC.rename(columns={"statefip": "orig_state", "migpuma": "orig_migpuma"})
    od = od.merge(h[["orig_state", "orig_migpuma", "redline_D_share", "redline_CD_share"]],
                  on=["orig_state", "orig_migpuma"], how="inner")
    od = od.join(CENT.rename(columns={"lon": "o_lon", "lat": "o_lat"}), on=["orig_state", "orig_migpuma"])
    od = od.join(CENT.rename(columns={"lon": "d_lon", "lat": "d_lat"}), on=["dest_state", "dest_migpuma"])
    od = od.dropna(subset=["o_lon", "d_lon", "mass_o", "mass_d"])
    od = od[(od.mass_o > 0) & (od.mass_d > 0) & (od.flow >= MIN_FLOW)].copy()
    od["dist"] = haversine(od.o_lon, od.o_lat, od.d_lon, od.d_lat).clip(lower=1)
    od["log_mass_o"] = np.log(od.mass_o)
    od["log_mass_d"] = np.log(od.mass_d)
    od["log_dist"] = np.log(od.dist)
    od["offset"] = np.log(len(years))
    od["grp"] = od.orig_state * 1000 + od.orig_migpuma
    return od


def fit(od, extra):
    cols = ["log_mass_o", "log_mass_d", "log_dist"] + extra
    X = sm.add_constant(od[cols].to_numpy(float))
    m = sm.GLM(od.flow.to_numpy(float), X, family=sm.families.Poisson(),
               offset=od.offset.to_numpy(float))
    res = m.fit(cov_type="cluster", cov_kwds={"groups": od.grp.to_numpy()})
    return res, cols


def mcfadden(res, od, cols):
    X = sm.add_constant(od[cols].to_numpy(float))
    mu = np.exp(X @ res.params + od.offset.to_numpy(float))
    ll = poisson_ll(od.flow, mu)
    ll0 = poisson_ll(od.flow, np.full(len(od), od.flow.mean()))
    return 1 - ll / ll0


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    out = {"min_flow": MIN_FLOW, "holc_origins": int(len(HOLC)), "groups": {}}
    for g in GROUPS:
        tr = build_design(TRAIN, g)
        ho = build_design(HOLD, g)
        n_or = tr.grp.nunique() if len(tr) else 0
        rec = {"n_corridors_train": int(len(tr)), "n_corridors_holdout": int(len(ho)),
               "n_origins_train": int(n_or)}
        if len(tr) < 50 or tr.grp.nunique() < 10:
            rec["status"] = "POWER_GATED"
            out["groups"][g] = rec
            print(f"=== {g:11s} ===  n_train={len(tr):,}  origins={n_or}  -> POWER_GATED")
            continue
        for share, tag in [("redline_D_share", "D"), ("redline_CD_share", "CD")]:
            m0, c0 = fit(tr, [])
            m1, c1 = fit(tr, [share])
            bR = float(m1.params[-1]); pR = float(m1.pvalues[-1]); seR = float(m1.bse[-1])
            r2_0 = mcfadden(m0, tr, c0); r2_1 = mcfadden(m1, tr, c1)
            r2_0h = mcfadden(m0, ho, c0); r2_1h = mcfadden(m1, ho, c1)
            mh, ch = fit(ho, [share])
            bRh = float(mh.params[-1]); pRh = float(mh.pvalues[-1]); seRh = float(mh.bse[-1])
            rec[tag] = {"beta_train": bR, "p_train": pR, "se_train": seR,
                        "beta_holdout": bRh, "p_holdout": pRh, "se_holdout": seRh,
                        "r2_M0_train": r2_0, "r2_M1_train": r2_1,
                        "r2_M0_holdout": r2_0h, "r2_M1_holdout": r2_1h}
        rec["status"] = "FIT"
        out["groups"][g] = rec
        d = rec["D"]
        print(f"=== {g:11s} ===  n_train={len(tr):,}  origins={n_or}")
        print(f"    redline_D  beta_train={d['beta_train']:+.4f} (se {d['se_train']:.4f}, p={d['p_train']:.2e}) | "
              f"holdout={d['beta_holdout']:+.4f} (p={d['p_holdout']:.2e})")

    # ---- falsifiers ----
    fit_groups = {g: r for g, r in out["groups"].items() if r.get("status") == "FIT"}
    hp = max(fit_groups, key=lambda g: fit_groups[g]["n_corridors_train"]) if fit_groups else None
    fz = {}
    if hp:
        d = fit_groups[hp]["D"]
        f1 = (d["p_train"] < 0.01 and d["beta_train"] > 0 and d["p_holdout"] < 0.01 and d["beta_holdout"] > 0)
        fz["F1_highest_power_group"] = hp
        fz["F1_signal_fires_correctly"] = bool(f1)
    # F2 racial differential vs NH_White (independent-sample z on beta diff)
    f2 = {}
    if "NH_White" in fit_groups:
        bw = fit_groups["NH_White"]["D"]["beta_train"]; sw = fit_groups["NH_White"]["D"]["se_train"]
        for g in ["NH_Black", "Hispanic"]:
            if g in fit_groups:
                bg = fit_groups[g]["D"]["beta_train"]; sg = fit_groups[g]["D"]["se_train"]
                z = (bg - bw) / np.sqrt(sg ** 2 + sw ** 2)
                from scipy.stats import norm
                p = 2 * (1 - norm.cdf(abs(z)))
                f2[g] = {"beta": bg, "beta_white": bw, "diff": bg - bw, "z": float(z),
                         "p_diff": float(p), "minority_gt_white_sig": bool(bg > bw and p < 0.05)}
    fz["F2_apartheid_differential"] = f2
    # F3 transfer on highest-power group
    if hp:
        d = fit_groups[hp]["D"]
        same_sign = (np.sign(d["beta_train"]) == np.sign(d["beta_holdout"]))
        fz["F3_transfer_ok"] = bool(same_sign and d["p_holdout"] < 0.05)
    out["falsifiers"] = fz

    print("\n--- FALSIFIERS ---")
    print(f"F1 (signal, highest-power group = {fz.get('F1_highest_power_group')}): "
          f"{'fires-correctly' if fz.get('F1_signal_fires_correctly') else 'does NOT fire (no signal)'}")
    print("F2 (apartheid differential vs NH_White):")
    for g, v in f2.items():
        print(f"    {g:10s} beta={v['beta']:+.4f} vs White {v['beta_white']:+.4f}  diff={v['diff']:+.4f}  "
              f"z={v['z']:+.2f} p={v['p_diff']:.3f}  -> {'DIFFERENTIAL' if v['minority_gt_white_sig'] else 'no sig differential'}")
    print(f"F3 (holdout transfer, {fz.get('F1_highest_power_group')}): "
          f"{'ok' if fz.get('F3_transfer_ok') else 'fails'}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "v19_foodpush.json").write_text(json.dumps(out, indent=2))
    print(f"\nwritten: {RESULTS / 'v19_foodpush.json'}")


if __name__ == "__main__":
    main()
