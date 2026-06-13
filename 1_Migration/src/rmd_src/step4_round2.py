"""
RMD-SRC Step 4 — decomposition ROUND 2 (recurse on round-1 leaves).

Confirms (or refutes) the round-1 plateau before locking RMD_F2. Operates on
the P1 partition (round-1 leaf_id). 4a (un-collapse) is inapplicable to
sub-cells, so attempts 4b (time-phase) -> 4c (GMM mixture) per not-clean leaf,
in order. Same residual-cleanness definition and n>=50/yr floor as round 1.

Output: data/derived/P2_partition_round2.parquet ; appends to decomp_tree log.
"""
from __future__ import annotations
import sys
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).parent))
from step4_decomposition import (resid_tests, cell_cleanness, min_year_count,
                                 OBSERVABLES, MIN_YR, DERIVED, RESULTS, TRAIN_YEARS)
from step3_response_validation import attach_density


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ev = pd.read_parquet(DERIVED / "event_observables.parquet")
    ev = ev[~ev.missing_geo & ~ev.missing_opp]
    ev = ev[ev.YEAR.isin(TRAIN_YEARS)].copy()
    ev = attach_density(ev)
    ev = ev[ev.tot_stock.notna() & np.isfinite(ev.rho_s) & np.isfinite(ev.rho_x)].copy()

    p1 = pd.read_parquet(DERIVED / "P1_partition_round1.parquet")[
        ["YEAR", "SERIAL", "PERNUM", "leaf_id"]]
    ev = ev.merge(p1, on=["YEAR", "SERIAL", "PERNUM"], how="left")
    ev["leaf2"] = ev.leaf_id

    log = []
    for lid, d in ev.groupby("leaf_id"):
        parent_cn = cell_cleanness(d)
        if parent_cn >= 1.0 or len(d) < 2 * MIN_YR:
            log.append(dict(parent=lid, strategy="none", parent_cn=parent_cn,
                            child_cn=parent_cn, decision="leaf-clean-or-too-small"))
            continue
        locked = None
        # 4b
        early = d[d.YEAR <= 2015]; late = d[d.YEAR >= 2016]
        if min_year_count(early) >= MIN_YR and min_year_count(late) >= MIN_YR:
            cn = float(np.mean([cell_cleanness(early), cell_cleanness(late)]))
            dec = "locked" if cn > parent_cn else "rejected"
            log.append(dict(parent=lid, strategy="4b", parent_cn=parent_cn, child_cn=cn, decision=dec))
            if cn > parent_cn:
                ev.loc[early.index, "leaf2"] = f"{lid}.b0"
                ev.loc[late.index, "leaf2"] = f"{lid}.b1"
                locked = "4b"
        # 4c
        if locked is None:
            dips = {o: resid_tests(d, o)[1]["dip"] for o in OBSERVABLES}
            dips = {o: v for o, v in dips.items() if np.isfinite(v)}
            so = min(dips, key=dips.get) if dips else "log_distance"
            dd = d[np.isfinite(d[so])].rename(columns={so: "y"})
            f = "y ~ rho_s + rho_x" if so == "opp_deficit" else "y ~ opp_deficit + rho_s + rho_x"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m = smf.ols(f, data=dd).fit()
            lab = GaussianMixture(2, random_state=0).fit_predict(m.resid.to_numpy().reshape(-1, 1))
            dd = dd.assign(_l=lab)
            g0 = d.loc[dd.index[dd._l == 0]]; g1 = d.loc[dd.index[dd._l == 1]]
            if min_year_count(g0) >= MIN_YR and min_year_count(g1) >= MIN_YR:
                cn = float(np.mean([cell_cleanness(g0), cell_cleanness(g1)]))
                dec = "locked" if cn > parent_cn else "rejected"
                log.append(dict(parent=lid, strategy="4c", parent_cn=parent_cn, child_cn=cn, decision=dec))
                if cn > parent_cn:
                    ev.loc[g0.index, "leaf2"] = f"{lid}.c0"
                    ev.loc[g1.index, "leaf2"] = f"{lid}.c1"
                    locked = "4c"
            else:
                log.append(dict(parent=lid, strategy="4c", parent_cn=parent_cn,
                                child_cn=np.nan, decision="resolution-limited"))
        if locked is None:
            log.append(dict(parent=lid, strategy="none", parent_cn=parent_cn,
                            child_cn=parent_cn, decision="failure-terminated"))

    logdf = pd.DataFrame(log)
    ev[["YEAR", "SERIAL", "PERNUM", "cell_id", "leaf_id", "leaf2"]].to_parquet(
        DERIVED / "P2_partition_round2.parquet", index=False)

    locked = logdf[logdf.decision == "locked"]
    print(f"round-2: P1 leaves {ev.leaf_id.nunique()} -> P2 leaves {ev.leaf2.nunique()}")
    print(f"locked splits this round: {len(locked)}  ({locked.strategy.value_counts().to_dict() if len(locked) else 'none'})")

    rows = []
    for lid, g in ev.groupby("leaf2"):
        for o in OBSERVABLES:
            cl, det = resid_tests(g, o)
            rows.append((o, cl))
    nc = pd.DataFrame(rows, columns=["observable", "clean"])
    nclean = int(nc.clean.sum())
    print(f"\nround-2 leaf cleanness: {nclean}/{len(nc)} = {100*nclean/len(nc):.1f}%  "
          f"(round-1 was 7.1%)")
    print("clean by observable:")
    print(nc.groupby('observable').clean.agg(['sum', 'count']).to_string())
    print(f"\nP2 -> {DERIVED / 'P2_partition_round2.parquet'}")


if __name__ == "__main__":
    main()
