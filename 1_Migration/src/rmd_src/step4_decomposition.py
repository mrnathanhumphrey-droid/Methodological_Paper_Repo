"""
RMD-SRC Step 4 — decomposition, round 1 (PRE_REG §4, order 4a->4b->4c).

For each not-clean cell, attempt ONE strategy in the pre-registered order;
the first that yields cleaner children is locked. Every attempt is logged.

  4a categorical: un-collapse a merged species into its finer (age,income)
       raw members (only applies to v1.2-collapsed cells; n>=50/yr floor, §2.8).
       Singleton cells have no finer ℙ₀ categorical -> 4a inapplicable -> 4b.
  4b time-phase: split training 2013-2017 into {2013-2015, 2016-2017}.
  4c mixture: GMM(k=2) on residuals of the cell's most-multimodal observable;
       latent class defines two sub-cells.

Child cleanness = mean over the cell's observables of the residual-test pass
(R2>=0.05 AND Shapiro(n=300) p>0.01 AND residual dip p>=0.05; v1.5). Sign-
agreement is not re-derived (contradictions were 0/114 at parent level).
Density regressors rho_s/rho_x held at parent-species resolution.

This is ONE round (one level). Outputs ℙ1 + decomposition log.

Outputs:
  results/decomposition_logs/decomp_tree.parquet   (every attempt)
  data/derived/P1_partition_round1.parquet         (event -> leaf_id after round 1)
"""
from __future__ import annotations
import json
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import shapiro
from sklearn.mixture import GaussianMixture
import diptest

DERIVED = Path(r"D:\Migration\data\derived")
RESULTS = Path(r"D:\Migration\results")
LOGDIR = RESULTS / "decomposition_logs"
TRAIN_YEARS = list(range(2013, 2018))  # fit window (2012 dropped: no t-1 density)
OBSERVABLES = ["log_distance", "log_dest_density", "opp_deficit"]
RNG = np.random.default_rng(0)
MIN_YR = 50  # §2.8 estimation floor per (cell, year)


def resid_tests(d, obs):
    """Fit response fn for one observable on subset d; return (clean_bool, detail)."""
    dd = d[np.isfinite(d[obs])].rename(columns={obs: "y"})
    if dd.y.nunique() < 5 or len(dd) < MIN_YR:
        return False, dict(n=len(dd), r2=np.nan, sh=np.nan, dip=np.nan)
    formula = "y ~ rho_s + rho_x" if obs == "opp_deficit" else "y ~ opp_deficit + rho_s + rho_x"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            m = smf.ols(formula, data=dd).fit(cov_type="cluster",
                                              cov_kwds={"groups": dd.orig_cluster})
        except Exception:
            return False, dict(n=len(dd), r2=np.nan, sh=np.nan, dip=np.nan)
    resid = m.resid.to_numpy()
    samp = resid if len(resid) <= 300 else RNG.choice(resid, 300, replace=False)
    sh = float(shapiro(samp).pvalue) if len(samp) >= 3 else 0.0
    dip = float(diptest.diptest(resid)[1])
    r2 = float(m.rsquared)
    clean = (r2 >= 0.05) and (sh > 0.01) and (dip >= 0.05)
    return clean, dict(n=len(dd), r2=r2, sh=sh, dip=dip)


def cell_cleanness(d):
    """Fraction of observables whose response-fit residuals are clean."""
    if len(d) < MIN_YR:
        return 0.0
    return float(np.mean([resid_tests(d, o)[0] for o in OBSERVABLES]))


def min_year_count(d):
    if len(d) == 0:
        return 0
    return int(d.groupby("YEAR").size().min())


def main():
    try:
        import sys as _s; _s.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ev = pd.read_parquet(DERIVED / "event_observables.parquet")
    ev = ev[~ev.missing_geo & ~ev.missing_opp]
    ev = ev[ev.YEAR.isin(TRAIN_YEARS)].copy()
    # attach rho_s/rho_x (same logic as step3)
    from step3_response_validation import attach_density
    ev = attach_density(ev)
    ev = ev[ev.tot_stock.notna() & np.isfinite(ev.rho_s) & np.isfinite(ev.rho_x)].copy()

    # age_bin / income_bin live in P0_partition, not event_observables -> join for 4a
    p0 = pd.read_parquet(DERIVED / "P0_partition.parquet")[
        ["YEAR", "SERIAL", "PERNUM", "age_bin", "income_bin"]]
    ev = ev.merge(p0, on=["YEAR", "SERIAL", "PERNUM"], how="left")

    defs = json.loads((DERIVED / "P0_cell_definitions.json").read_text(encoding="utf-8"))
    raw_members = {c["cell_id"]: c["raw_members"] for c in defs["cells"]}

    log = []
    ev["leaf_id"] = ev.cell_id  # default: no split
    cells = sorted(ev.cell_id.unique())

    for c in cells:
        d = ev[ev.cell_id == c]
        parent_cn = cell_cleanness(d)
        locked = None

        # ---- 4a: un-collapse (only if merged species, >1 raw member) ----
        n_raw = len(raw_members.get(c, [c]))
        if n_raw > 1:
            sub = {k: g for k, g in d.groupby(["age_bin", "income_bin"])}
            valid = {k: g for k, g in sub.items() if min_year_count(g) >= MIN_YR}
            if len(valid) >= 2:
                child_cn = float(np.mean([cell_cleanness(g) for g in valid.values()]))
                log.append(dict(parent=c, strategy="4a", split_var="age_bin x income_bin",
                                n_children=len(valid), parent_cn=parent_cn,
                                child_cn=child_cn, decision="locked" if child_cn > parent_cn else "rejected"))
                if child_cn > parent_cn:
                    for j, (k, g) in enumerate(valid.items()):
                        ev.loc[g.index, "leaf_id"] = f"{c}.a{j}"
                    locked = "4a"

        # ---- 4b: time-phase split ----
        if locked is None:
            early = d[d.YEAR <= 2015]; late = d[d.YEAR >= 2016]
            if min_year_count(early) >= MIN_YR and min_year_count(late) >= MIN_YR:
                child_cn = float(np.mean([cell_cleanness(early), cell_cleanness(late)]))
                log.append(dict(parent=c, strategy="4b", split_var="year<=2015|>=2016",
                                n_children=2, parent_cn=parent_cn, child_cn=child_cn,
                                decision="locked" if child_cn > parent_cn else "rejected"))
                if child_cn > parent_cn:
                    ev.loc[early.index, "leaf_id"] = f"{c}.b0"
                    ev.loc[late.index, "leaf_id"] = f"{c}.b1"
                    locked = "4b"

        # ---- 4c: GMM(k=2) mixture on residuals of most-multimodal observable ----
        if locked is None:
            dips = {o: resid_tests(d, o)[1]["dip"] for o in OBSERVABLES}
            dips = {o: v for o, v in dips.items() if np.isfinite(v)}
            split_obs = min(dips, key=dips.get) if dips else "log_distance"
            dd = d[np.isfinite(d[split_obs])].rename(columns={split_obs: "y"})
            formula = "y ~ rho_s + rho_x" if split_obs == "opp_deficit" else "y ~ opp_deficit + rho_s + rho_x"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m = smf.ols(formula, data=dd).fit()
            resid = m.resid.to_numpy().reshape(-1, 1)
            gm = GaussianMixture(n_components=2, random_state=0).fit(resid)
            lab = gm.predict(resid)
            dd = dd.assign(_lab=lab)
            g0 = d.loc[dd.index[dd._lab == 0]]; g1 = d.loc[dd.index[dd._lab == 1]]
            if min_year_count(g0) >= MIN_YR and min_year_count(g1) >= MIN_YR:
                child_cn = float(np.mean([cell_cleanness(g0), cell_cleanness(g1)]))
                log.append(dict(parent=c, strategy="4c", split_var=f"GMM2_resid({split_obs})",
                                n_children=2, parent_cn=parent_cn, child_cn=child_cn,
                                decision="locked" if child_cn > parent_cn else "rejected"))
                if child_cn > parent_cn:
                    ev.loc[g0.index, "leaf_id"] = f"{c}.c0"
                    ev.loc[g1.index, "leaf_id"] = f"{c}.c1"
                    locked = "4c"
            else:
                log.append(dict(parent=c, strategy="4c", split_var=f"GMM2_resid({split_obs})",
                                n_children=0, parent_cn=parent_cn, child_cn=np.nan,
                                decision="resolution-limited (child<50/yr)"))

        if locked is None:
            log.append(dict(parent=c, strategy="none", split_var="",
                            n_children=0, parent_cn=parent_cn, child_cn=parent_cn,
                            decision="incompletely-decomposed"))

    logdf = pd.DataFrame(log)
    LOGDIR.mkdir(parents=True, exist_ok=True)
    logdf.to_parquet(LOGDIR / "decomp_tree.parquet", index=False)
    ev[["YEAR", "SERIAL", "PERNUM", "cell_id", "leaf_id"]].to_parquet(
        DERIVED / "P1_partition_round1.parquet", index=False)

    # ---- report ----
    locked_rows = logdf[logdf.decision == "locked"]
    print(f"cells processed: {len(cells)}")
    print("strategy locked per cell:")
    print(locked_rows.strategy.value_counts().to_string() if len(locked_rows) else "  (none locked)")
    n_split = ev.cell_id.nunique()
    n_leaves = ev.leaf_id.nunique()
    print(f"\nP0 species: {n_split}  ->  P1 leaves after round 1: {n_leaves}")
    # new partition cleanness
    new_cn = []
    for lid, g in ev.groupby("leaf_id"):
        for o in OBSERVABLES:
            cl, det = resid_tests(g, o)
            new_cn.append((lid, o, cl, det["n"], det["r2"], det["sh"], det["dip"]))
    nc = pd.DataFrame(new_cn, columns=["leaf_id", "observable", "clean", "n", "r2", "sh", "dip"])
    nclean = int(nc.clean.sum())
    print(f"\nround-1 leaf cleanness: {nclean}/{len(nc)} = {100*nclean/len(nc):.1f}% "
          f"(was 1/114 = 0.9% pre-decomposition)")
    print(f"clean by observable:")
    print(nc.groupby('observable').clean.agg(['sum', 'count']).to_string())
    print(f"\nlog -> {LOGDIR / 'decomp_tree.parquet'}")
    print(f"ℙ1 -> {DERIVED / 'P1_partition_round1.parquet'}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    main()
