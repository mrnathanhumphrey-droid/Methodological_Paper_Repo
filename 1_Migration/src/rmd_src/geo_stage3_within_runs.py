"""
Geographic arm — Stage 3: within-mini-country demographic runs (PRE_REG v1.6).

For each mini-country (division, then state), fit the demographic response
function on the unit's IN-migration events and extract the network coefficient
beta_s (same-species destination density) per observable. Compares the sorting
signature across mini-countries: are some agglomerating (boson, beta_s>0) and
others dispersing (fermion, beta_s<0)? -> "mini-countries with different physics".

Tractable proxy for "full Steps 0-3 per unit": the demographic arm's load-bearing
output is the beta_s sorting signature; we compute it per unit (pooled across
species, the partition is shared) rather than re-deriving ℙ0 within each unit.

Output: results/geo_within_signatures_{division,state}.parquet
"""
from __future__ import annotations
import sys
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).parent))
from geo_stage1_cube_gravity import DIVISION
from step3_response_validation import attach_density

DERIVED = Path(r"D:\Migration\data\derived")
RESULTS = Path(r"D:\Migration\results")
TRAIN = list(range(2013, 2018))
OBSERVABLES = ["log_distance", "log_dest_density", "opp_deficit"]
MIN_UNIT_EVENTS = 500


def fit_unit(d, obs):
    dd = d[np.isfinite(d[obs])].rename(columns={obs: "y"})
    if len(dd) < MIN_UNIT_EVENTS or dd.y.nunique() < 5:
        return None
    f = "y ~ rho_s + rho_x" if obs == "opp_deficit" else "y ~ opp_deficit + rho_s + rho_x"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            m = smf.ols(f, data=dd).fit(cov_type="cluster", cov_kwds={"groups": dd.orig_cluster})
        except Exception:
            return None
    b = float(m.params.get("rho_s", np.nan)); t = float(m.tvalues.get("rho_s", np.nan))
    return dict(beta_s=b, t_s=t, sig=abs(t) > 2.0, r2=float(m.rsquared), n=len(dd))


def run(level, ev):
    col = "dest_div" if level == "division" else "dest_state"
    rows = []
    for unit, d in ev.groupby(col):
        for obs in OBSERVABLES:
            r = fit_unit(d, obs)
            if r is None:
                continue
            sign = "boson(+)" if (r["sig"] and r["beta_s"] > 0) else \
                   "fermion(-)" if (r["sig"] and r["beta_s"] < 0) else "null"
            rows.append((unit, obs, r["beta_s"], r["t_s"], r["sig"], sign, r["r2"], r["n"]))
    sig = pd.DataFrame(rows, columns=["unit", "observable", "beta_s", "t_s",
                                      "sig", "sorting", "r2", "n"])
    sig.to_parquet(RESULTS / f"geo_within_signatures_{level}.parquet", index=False)
    return sig


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ev = pd.read_parquet(DERIVED / "event_observables.parquet")
    ev = ev[~ev.missing_geo & ~ev.missing_opp]
    ev = ev[ev.YEAR.isin(TRAIN)].copy()
    ev = attach_density(ev)
    ev = ev[ev.tot_stock.notna() & np.isfinite(ev.rho_s) & np.isfinite(ev.rho_x)].copy()
    ev = ev[ev.dest_state.isin(DIVISION)].copy()
    ev["dest_div"] = ev.dest_state.map(DIVISION)

    for level in ["division", "state"]:
        sig = run(level, ev)
        print(f"\n=== {level.upper()} within-unit sorting signatures ===")
        print(f"units with >=1 fitted observable: {sig.unit.nunique()}")
        print("sorting x observable:")
        print(pd.crosstab(sig.observable, sig.sorting).to_string())
        # unit-level dominant sorting (across the behavioral observables, distance+density)
        beh = sig[sig.observable != "opp_deficit"]
        dom = beh.groupby("unit").sorting.agg(lambda s: s.value_counts().idxmax())
        print(f"\nunit dominant sorting (distance+density): "
              f"{dom.value_counts().to_dict()}")
        # heterogeneity test: do units differ?
        het = beh.groupby("unit").beta_s.mean()
        print(f"across-unit beta_s spread: mean {het.mean():+.3f}, sd {het.std():.3f}, "
              f"range [{het.min():+.3f}, {het.max():+.3f}]")
    print(f"\nwritten: results/geo_within_signatures_*.parquet")


if __name__ == "__main__":
    main()
