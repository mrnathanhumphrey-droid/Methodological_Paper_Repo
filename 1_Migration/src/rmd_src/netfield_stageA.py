"""
Seam arc, Stage A (PRE_REG v1.8) — does ONE net-livability field organize flows?

Field (locked):  N(place,year) = med_hhinc - 12*med_rent   (realizable income
net of rent, dollars).  Tests whether between-MIGPUMA corridor flows align with
the gradient dN = N(dest)-N(orig) better than with its components (dINC, dRENT)
entered separately.

Models (Poisson GLM, log link, exposure offset = window years, origin-clustered SE):
  M0 gravity:    a + b*log(mass_o) + c*log(mass_d) + g*log(dist)
  M1 field:      M0 + bN*dN
  M2 components: M0 + bI*dINC + bR*dRENT
  M3 secondary:  M0 + bMU*dMU      (prior opportunity-index gradient)

Falsifiers: FIELD_F1 (signal), FIELD_F2 (one field not two), FIELD_F3 (held-out
parsimony).  Read-only.  Output: results/netfield_stageA.json
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
TRAIN = list(range(2012, 2018))   # 2012-2017 (6 yr)
HOLD = list(range(2018, 2022))    # 2018-2021 (4 yr)
MIN_CELL = 50


def haversine(lo1, la1, lo2, la2):
    R = 6371.0088
    lo1, la1, lo2, la2 = map(np.radians, [lo1, la1, lo2, la2])
    a = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def poisson_ll(y, mu):
    mu = np.clip(np.asarray(mu, float), 1e-9, None)
    y = np.asarray(y, float)
    return float(np.sum(y * np.log(mu) - mu - gammaln(y + 1)))


def place_field(years):
    """Window-mean N, INC, RENT, MU per (statefip,migpuma)."""
    soc = pd.read_parquet(DERIVED / "migpuma_socioecon_2010.parquet")
    soc = soc[soc.year.isin(years)].dropna(subset=["med_hhinc", "med_rent"]).copy()
    soc["N"] = soc.med_hhinc - 12.0 * soc.med_rent
    soc["RENT"] = 12.0 * soc.med_rent
    f = (soc.groupby(["statefip", "migpuma"])
         .agg(N=("N", "mean"), INC=("med_hhinc", "mean"), RENT=("RENT", "mean"))
         .reset_index())
    opp = pd.read_parquet(DERIVED / "migpuma_opportunity_2010.parquet")
    opp = opp[opp.year.isin(years)]
    mu = (opp.groupby(["statefip", "migpuma"]).opportunity_index.mean()
          .reset_index().rename(columns={"opportunity_index": "MU"}))
    return f.merge(mu, on=["statefip", "migpuma"], how="left")


def place_mass(years):
    pop = pd.read_parquet(DERIVED / "migpuma_population_2010.parquet")
    pop = pop[pop.year.isin(years)]
    return (pop.groupby(["statefip", "migpuma"]).population.mean()
            .reset_index().rename(columns={"population": "mass"}))


def corridor_flows(ev, years):
    e = ev[ev.YEAR.isin(years) & ~ev.missing_geo].copy()
    od = (e.groupby(["orig_state", "orig_migpuma", "dest_state", "dest_migpuma"])
          .PERWT.sum().reset_index().rename(columns={"PERWT": "flow"}))
    # between-MIGPUMA only
    od = od[~((od.orig_state == od.dest_state) & (od.orig_migpuma == od.dest_migpuma))]
    return od


def build_design(years, geo, n_years):
    f = place_field(years)
    mass = place_mass(years)
    ev = pd.read_parquet(DERIVED / "event_observables.parquet")
    od = corridor_flows(ev, years)

    o = f.add_prefix("o_").rename(columns={"o_statefip": "orig_state", "o_migpuma": "orig_migpuma"})
    d = f.add_prefix("d_").rename(columns={"d_statefip": "dest_state", "d_migpuma": "dest_migpuma"})
    od = od.merge(o, on=["orig_state", "orig_migpuma"], how="inner")
    od = od.merge(d, on=["dest_state", "dest_migpuma"], how="inner")
    mo = mass.rename(columns={"statefip": "orig_state", "migpuma": "orig_migpuma", "mass": "mass_o"})
    md = mass.rename(columns={"statefip": "dest_state", "migpuma": "dest_migpuma", "mass": "mass_d"})
    od = od.merge(mo, on=["orig_state", "orig_migpuma"], how="inner")
    od = od.merge(md, on=["dest_state", "dest_migpuma"], how="inner")

    g = geo.set_index(["statefip", "migpuma"])[["lon", "lat"]]
    od = od.join(g.rename(columns={"lon": "o_lon", "lat": "o_lat"}), on=["orig_state", "orig_migpuma"])
    od = od.join(g.rename(columns={"lon": "d_lon", "lat": "d_lat"}), on=["dest_state", "dest_migpuma"])
    od = od.dropna(subset=["o_lon", "d_lon", "mass_o", "mass_d"])
    od["dist"] = haversine(od.o_lon, od.o_lat, od.d_lon, od.d_lat).clip(lower=1)

    od = od[od.flow >= MIN_CELL].copy()
    # gradients, in $10k
    od["dN"] = (od.d_N - od.o_N) / 1e4
    od["dINC"] = (od.d_INC - od.o_INC) / 1e4
    od["dRENT"] = (od.d_RENT - od.o_RENT) / 1e4
    od["dMU"] = od.d_MU - od.o_MU
    od["log_mass_o"] = np.log(od.mass_o)
    od["log_mass_d"] = np.log(od.mass_d)
    od["log_dist"] = np.log(od.dist)
    od["offset"] = np.log(n_years)
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
    eta = X @ res.params + od.offset.to_numpy(float)
    mu = np.exp(eta)
    ll = poisson_ll(od.flow, mu)
    ll0 = poisson_ll(od.flow, np.full(len(od), od.flow.mean()))
    return 1 - ll / ll0


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    geo = pd.read_parquet(DERIVED / "migpuma_geometry_2010.parquet")

    # field descriptives (Stage B setup): fraction of MIGPUMA-years with N<0
    soc = pd.read_parquet(DERIVED / "migpuma_socioecon_2010.parquet").dropna(subset=["med_hhinc", "med_rent"])
    soc_N = soc.med_hhinc - 12.0 * soc.med_rent
    print(f"N (income net of annual rent) over MIGPUMA-years: median ${soc_N.median():,.0f}  "
          f"min ${soc_N.min():,.0f}  max ${soc_N.max():,.0f}")
    print(f"  fraction with N<0 (subsistence-negative): {100*(soc_N<0).mean():.2f}%  "
          f"(n={int((soc_N<0).sum())} of {len(soc_N)})\n")

    tr = build_design(TRAIN, geo, len(TRAIN))
    ho = build_design(HOLD, geo, len(HOLD))
    print(f"train corridors (flow>=50, between-MIGPUMA): {len(tr):,}   holdout: {len(ho):,}")
    print(f"dN range train [{tr.dN.min():.1f}, {tr.dN.max():.1f}] ($10k)\n")

    specs = {"M0": [], "M1_field": ["dN"], "M2_components": ["dINC", "dRENT"],
             "M3_dMU": ["dMU"]}
    out = {"n_train": int(len(tr)), "n_holdout": int(len(ho)),
           "N_frac_negative_pct": float(100 * (soc_N < 0).mean()), "models": {}}
    fits = {}
    for name, extra in specs.items():
        res, cols = fit(tr, extra)
        r2_tr = mcfadden(res, tr, cols)
        r2_ho = mcfadden(res, ho, cols)
        fits[name] = (res, cols)
        params = dict(zip(["const", "log_mass_o", "log_mass_d", "log_dist"] + extra, res.params))
        pvals = dict(zip(["const", "log_mass_o", "log_mass_d", "log_dist"] + extra, res.pvalues))
        out["models"][name] = {"r2_train": float(r2_tr), "r2_holdout": float(r2_ho),
                               "params": {k: float(v) for k, v in params.items()},
                               "pvalues": {k: float(v) for k, v in pvals.items()}}
        print(f"=== {name} ===  pseudo-R2 train {r2_tr:.4f}  holdout {r2_ho:.4f}")
        for k in extra:
            print(f"    {k:8s} beta={params[k]:+.4f}  p={pvals[k]:.2e}")

    # ---- falsifiers ----
    print("\n--- FALSIFIERS ---")
    m1_tr, _ = fits["M1_field"]
    bN_tr = out["models"]["M1_field"]["params"]["dN"]
    pN_tr = out["models"]["M1_field"]["pvalues"]["dN"]
    res_ho, cols_ho = fit(ho, ["dN"])
    bN_ho = float(res_ho.params[-1]); pN_ho = float(res_ho.pvalues[-1])
    f1_ok = (pN_tr < 0.01 and bN_tr > 0 and pN_ho < 0.01 and bN_ho > 0)
    print(f"FIELD_F1 (signal): train bN={bN_tr:+.4f} p={pN_tr:.1e} | holdout bN={bN_ho:+.4f} p={pN_ho:.1e}"
          f"  -> {'fires-correctly (field carries signal)' if f1_ok else 'FALSIFIED'}")

    bI = out["models"]["M2_components"]["params"]["dINC"]
    bR = out["models"]["M2_components"]["params"]["dRENT"]
    ratio = abs(bI) / abs(bR) if bR != 0 else np.inf
    f2_fires = not (bI > 0 and bR < 0 and 0.5 <= ratio <= 2.0)
    print(f"FIELD_F2 (one field): bINC={bI:+.4f} bRENT={bR:+.4f} ratio|I|/|R|={ratio:.2f}"
          f"  -> {'FIRES (two forces)' if f2_fires else 'does not fire (dollar-for-dollar holds)'}")

    r2ho_m1 = out["models"]["M1_field"]["r2_holdout"]
    r2ho_m2 = out["models"]["M2_components"]["r2_holdout"]
    f3_fires = (r2ho_m2 - r2ho_m1) > 0.01
    print(f"FIELD_F3 (held-out parsimony): M1 holdout R2={r2ho_m1:.4f}  M2={r2ho_m2:.4f}  "
          f"diff={r2ho_m2-r2ho_m1:+.4f}  -> {'FIRES (field lossy)' if f3_fires else 'does not fire (parsimony holds)'}")

    field_real = f1_ok and (not f2_fires) and (not f3_fires)
    print(f"\nVERDICT: net-livability field is {'REAL & SINGULAR -> Stage B licensed' if field_real else 'NOT confirmed as singular (see clauses)'}")
    out["falsifiers"] = {"F1_signal_ok": bool(f1_ok), "F2_two_forces_fires": bool(f2_fires),
                         "F3_lossy_fires": bool(f3_fires), "field_real_and_singular": bool(field_real),
                         "bN_train": bN_tr, "bN_holdout": bN_ho,
                         "bINC": bI, "bRENT": bR, "ratio_I_over_R": float(ratio)}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "netfield_stageA.json").write_text(json.dumps(out, indent=2))
    print(f"\nwritten: {RESULTS / 'netfield_stageA.json'}")


if __name__ == "__main__":
    main()
