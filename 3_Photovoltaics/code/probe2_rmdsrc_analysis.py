"""
Probe 2 (23_PREREG_v1.0_FleetPLR_PVCZ) — §14.6 through §14.11
RMD-SRC moment-flow -> trajectory classification -> H1-H5 + falsifier verdicts.

Consumes:
  data/processed/probe2_plr_results.csv     (scalar PLR per system, §14.5)
  data/processed/probe2_cohort_p0.csv       (locked ℙ₀ assignment, §14.3)
  data/processed/monthly_pi/sys*_monthly_pi.csv  (monthly PI trajectories)

Emits verdict table to stdout + data/processed/probe2_verdicts.json.
All hypothesis gates are the LOCKED §8 gates; no post-hoc gate tuning.
"""
import json, glob
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data/processed"
T_ORDER = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]
VIABLE = ["T3:H3", "T4:H3", "T5:H2", "T5:H3", "T5:H4"]


def load():
    clean = PROC / "probe2_plr_results_clean.csv"
    src = clean if clean.exists() else (PROC / "probe2_plr_results.csv")
    r = pd.read_csv(src)
    r = r[r["status"] == "ok"].copy()
    c = pd.read_csv(PROC / "probe2_cohort_p0.csv")
    df = r.merge(c, on="system_id", how="left")
    # PLR sanity: drop |PLR|>10%/yr as meter-artifact (pre-declared physical bound)
    df = df[df["plr_pct_yr"].abs() <= 10].copy()
    return df


def eta_sq_partial(df, factor, covars):
    """Type-II partial eta^2 for `factor` controlling `covars`, on plr_pct_yr."""
    terms = [f"C({factor})"] + [f"C({c})" for c in covars]
    formula = "plr_pct_yr ~ " + " + ".join(terms)
    sub = df.dropna(subset=["plr_pct_yr", factor] + covars)
    # require each level of factor to have >=2 obs
    vc = sub[factor].value_counts()
    sub = sub[sub[factor].isin(vc[vc >= 2].index)]
    if sub[factor].nunique() < 2:
        return None
    model = smf.ols(formula, data=sub).fit()
    aov = sm.stats.anova_lm(model, typ=2)
    key = f"C({factor})"
    if key not in aov.index:
        return None
    ss_eff = aov.loc[key, "sum_sq"]
    ss_res = aov.loc["Residual", "sum_sq"]
    eta = ss_eff / (ss_eff + ss_res)
    p = aov.loc[key, "PR(>F)"]
    return {"eta2_partial": float(eta), "p": float(p), "n": int(len(sub)),
            "levels": int(sub[factor].nunique())}


def cell_moment_flow(cell_ids, monthly_dir):
    """RMD-SRC moment-flow on ELAPSED-TIME-aligned, start-normalized trajectories.

    Each system's monthly PI is normalized by its own first-6-month mean (relative PI,
    ~1.0 at start) and re-indexed to elapsed months since its own start. The cell
    moment-flow is then μ(τ)=mean relative-PI across systems at elapsed-month τ, and
    σ²(τ)=cross-system variance. slope_mu = average degradation drift; slope_var =
    convergence(<0)/divergence(>0). This separates within-system degradation from
    fleet-composition level differences (the calendar-mean confound)."""
    series = []
    for sid in cell_ids:
        f = monthly_dir / f"sys{sid}_monthly_pi.csv"
        if not f.exists():
            continue
        m = pd.read_csv(f, index_col=0, parse_dates=True).sort_index()
        s = m["pi_mean"].dropna()
        if len(s) < 12:
            continue
        base = s.iloc[:6].mean()
        if not np.isfinite(base) or base <= 0:
            continue
        rel = (s / base).reset_index(drop=True)  # elapsed-month index 0,1,2,...
        series.append(rel.rename(sid))
    if len(series) < 5:
        return None
    panel = pd.concat(series, axis=1)
    cnt = panel.count(axis=1)
    mask = cnt >= 5
    mu = panel.mean(axis=1)[mask]
    var = panel.var(axis=1)[mask]
    if len(mu) < 12:
        return None
    tau = np.asarray(mu.index) / 12.0  # elapsed years
    b_mu, _, r_mu, p_mu, _ = stats.linregress(tau, mu.values)
    b_var, _, r_var, p_var, _ = stats.linregress(tau, var.values)
    return {"n_sys": int(panel.shape[1]), "n_months": int(len(mu)),
            "slope_mu_per_yr": float(b_mu), "r2_mu": float(r_mu**2), "p_mu": float(p_mu),
            "slope_var_per_yr": float(b_var), "p_var": float(p_var),
            "mu_level": float(mu.mean())}


def classify_regime(mf):
    """Map moment-flow to one of the 5 RMD-SRC regimes (operationalization logged in result)."""
    if mf is None:
        return "INSUFFICIENT"
    smu, pvar, bvar, pmu, r2 = (mf["slope_mu_per_yr"], mf["p_var"], mf["slope_var_per_yr"],
                                mf["p_mu"], mf["r2_mu"])
    declining = (smu < -0.005) and (pmu < 0.05)
    var_shrink = (bvar < 0) and (pvar < 0.10)
    var_grow = (bvar > 0) and (pvar < 0.10)
    if not declining and abs(smu) < 0.005:
        return "Stationary"
    if r2 < 0.2 and not (var_shrink or var_grow):
        return "Fragmenting"
    if var_shrink:
        return "Concentrating"
    if var_grow:
        return "Diffusing"
    if declining:
        return "Gradient-tracking"
    return "Fragmenting"


def main():
    df = load()
    monthly_dir = PROC / "monthly_pi"
    out = {"n_systems_ok": int(len(df)), "hypotheses": {}, "falsifiers": {}, "cells": {}}

    # ---- cell census + moment-flow + regime ----
    cell_rows = []
    for th in sorted(df["P0_primary_TH"].dropna().unique()):
        ids = df.loc[df["P0_primary_TH"] == th, "system_id"].tolist()
        med = df.loc[df["P0_primary_TH"] == th, "plr_pct_yr"].median()
        mf = cell_moment_flow(ids, monthly_dir)
        regime = classify_regime(mf)
        cell_rows.append({"cell": th, "n": len(ids), "plr_median": round(float(med), 3),
                          "regime": regime, "mf": mf})
        out["cells"][th] = {"n": len(ids), "plr_median": float(med), "regime": regime, "moment_flow": mf}
    cells_df = pd.DataFrame(cell_rows)

    # ================= H1: T-zone dominates + monotone hotter->faster =================
    h1 = eta_sq_partial(df, "A_PVCZ_T", ["A_PVCZ_H"])
    # monotone test: median PLR by T-zone (more negative as hotter), Spearman vs T rank
    tmed = df.groupby("A_PVCZ_T")["plr_pct_yr"].median()
    tmed = tmed.reindex([t for t in T_ORDER if t in tmed.index])
    tranks = np.arange(len(tmed))
    mono_rho, mono_p = (stats.spearmanr(tranks, tmed.values) if len(tmed) >= 4 else (np.nan, np.nan))
    # CONFIRMED: eta2>0.20 AND monotone (negative rho i.e. hotter=more negative PLR) across>=4 zones at p<0.01
    h1_verdict = "INDETERMINATE"
    if h1:
        mono_ok = (len(tmed) >= 4) and (mono_rho < 0) and (mono_p < 0.01)
        if h1["eta2_partial"] > 0.20 and mono_ok:
            h1_verdict = "CONFIRMED"
        elif (0.08 <= h1["eta2_partial"] <= 0.20) or (mono_ok and h1["eta2_partial"] <= 0.20):
            h1_verdict = "PARTIAL"
        elif h1["eta2_partial"] < 0.08 and not mono_ok:
            h1_verdict = "REFUTED"
        else:
            h1_verdict = "PARTIAL"
    out["hypotheses"]["H1"] = {"verdict": h1_verdict, "eta2": h1, "T_zone_median_plr": tmed.round(3).to_dict(),
                               "monotone_rho": float(mono_rho), "monotone_p": float(mono_p)}

    # ================= H2: hot zones T5-T6 Gradient-tracking dominance =================
    hot = cells_df[cells_df["cell"].str.startswith(("T5", "T6", "T7", "T8"))]
    n_hot = len(hot)
    frac_gt = (hot["regime"] == "Gradient-tracking").mean() if n_hot else np.nan
    frac_frag = (hot["regime"] == "Fragmenting").mean() if n_hot else np.nan
    if n_hot == 0:
        h2_verdict = "INDETERMINATE"
    elif frac_gt >= 0.50:
        h2_verdict = "CONFIRMED"
    elif frac_gt >= 0.25:
        h2_verdict = "PARTIAL"
    else:
        h2_verdict = "REFUTED"
    out["hypotheses"]["H2"] = {"verdict": h2_verdict, "n_hot_cells": int(n_hot),
                               "frac_gradient_tracking": float(frac_gt) if n_hot else None,
                               "frac_fragmenting": float(frac_frag) if n_hot else None,
                               "hot_cell_regimes": hot.set_index("cell")["regime"].to_dict()}

    # ================= H3: roof vs ground PLR (mounting metadata) =================
    mnt = df[df["A_MOUNT"].isin(["roof", "ground"])]
    n_roof = (mnt["A_MOUNT"] == "roof").sum(); n_grd = (mnt["A_MOUNT"] == "ground").sum()
    if n_roof < 10 or n_grd < 10:
        h3_verdict = "INDETERMINATE"
        h3_info = {"reason": "mounting metadata too sparse", "n_roof": int(n_roof), "n_ground": int(n_grd)}
    else:
        roof_med = mnt.loc[mnt["A_MOUNT"] == "roof", "plr_pct_yr"].median()
        grd_med = mnt.loc[mnt["A_MOUNT"] == "ground", "plr_pct_yr"].median()
        u, p = stats.mannwhitneyu(mnt.loc[mnt["A_MOUNT"] == "roof", "plr_pct_yr"],
                                  mnt.loc[mnt["A_MOUNT"] == "ground", "plr_pct_yr"], alternative="less")
        delta = roof_med - grd_med
        h3_verdict = ("CONFIRMED" if (delta <= -0.15 and p < 0.05)
                      else "PARTIAL" if (delta <= -0.05 or p < 0.15) else "REFUTED")
        h3_info = {"roof_med": float(roof_med), "ground_med": float(grd_med), "delta": float(delta), "p": float(p)}
    out["hypotheses"]["H3"] = {"verdict": h3_verdict, **h3_info}

    # ================= H4: tracking null replication =================
    trk = df[df["A_TRACK"].isin(["fixed", "tracking"])]
    n_trk = (trk["A_TRACK"] == "tracking").sum()
    if n_trk < 10:
        h4_verdict = "INDETERMINATE"
        h4_info = {"reason": "tracking metadata too sparse", "n_tracking": int(n_trk)}
    else:
        f_med = trk.loc[trk["A_TRACK"] == "fixed", "plr_pct_yr"].median()
        t_med = trk.loc[trk["A_TRACK"] == "tracking", "plr_pct_yr"].median()
        u, p = stats.mannwhitneyu(trk.loc[trk["A_TRACK"] == "fixed", "plr_pct_yr"],
                                  trk.loc[trk["A_TRACK"] == "tracking", "plr_pct_yr"])
        dabs = abs(f_med - t_med)
        h4_verdict = ("CONFIRMED" if (p > 0.05 and dabs < 0.10)
                      else "REFUTED" if (p < 0.01 and dabs > 0.20) else "PARTIAL")
        h4_info = {"fixed_med": float(f_med), "tracking_med": float(t_med), "delta_abs": float(dabs), "p": float(p)}
    out["hypotheses"]["H4"] = {"verdict": h4_verdict, **h4_info}

    # ================= H5: humidity underpowered / indeterminate =================
    h5 = eta_sq_partial(df, "A_PVCZ_H", ["A_PVCZ_T"])
    hcounts = df["A_PVCZ_H"].value_counts()
    n_under = int((hcounts < 50).sum())
    if h5 is None:
        h5_verdict = "CONFIRMED"; h5_eta = None
    else:
        h5_eta = h5["eta2_partial"]
        if h5_eta < 0.05 or n_under >= 2:
            h5_verdict = "CONFIRMED"          # indeterminacy replicated (as predicted)
        elif h5_eta <= 0.12:
            h5_verdict = "PARTIAL"
        else:
            h5_verdict = "REFUTED"            # surprise: strong humidity signal
    out["hypotheses"]["H5"] = {"verdict": h5_verdict, "eta2": h5,
                               "n_H_zones_below_50": n_under, "H_zone_counts": hcounts.to_dict()}

    # ================= Falsifiers =================
    plr_med_all = df["plr_pct_yr"].median()
    ci_cross0 = ((df["ci_low"] < 0) & (df["ci_high"] > 0)).mean()
    out["falsifiers"]["F_Fleet_1_no_signal"] = {
        "fired": bool(abs(plr_med_all) < 0.1 or ci_cross0 > 0.70),
        "fleet_median_plr": float(plr_med_all), "frac_CI_cross_zero": float(ci_cross0)}
    out["falsifiers"]["F_Fleet_2_climate_null_vs_anchor"] = {
        "fired": bool(h1_verdict == "REFUTED")}
    # F_Fleet_3 inversion: hotter zones credibly LOWER PLR (positive spearman = hotter->less negative)
    out["falsifiers"]["F_Fleet_3_inversion"] = {
        "fired": bool((not np.isnan(mono_rho)) and mono_rho > 0 and mono_p < 0.01),
        "monotone_rho": float(mono_rho), "monotone_p": float(mono_p)}
    # RMD_F1 cleanliness: fraction of cells Stationary/Gradient-tracking cleanly (proxy)
    clean = cells_df["regime"].isin(["Gradient-tracking", "Stationary", "Concentrating"]).mean()
    out["falsifiers"]["RMD_F1_initial_cleanness"] = {"fired": bool(clean >= 0.80), "frac_clean": float(clean)}
    out["falsifiers"]["RMD_F2_decomp_convergence"] = {"note": "evaluated only if decomposition run"}

    # ---- print ----
    print(f"=== PROBE 2 RESULTS — Fleet PLR × PVCZ (n_ok={len(df)}) ===\n")
    print(f"Fleet median PLR: {plr_med_all:.3f} %/yr | frac CI crossing 0: {ci_cross0:.2f}\n")
    print("Cell census + moment-flow regime:")
    for _, row in cells_df.sort_values("cell").iterrows():
        mf = row["mf"]; smu = f"{mf['slope_mu_per_yr']:+.4f}/yr" if mf else "n/a"
        print(f"  {row['cell']:8s} n={row['n']:4d}  PLR_med={row['plr_median']:+.3f}  regime={row['regime']:16s} mu_slope={smu}")
    print(f"\nH1 T-zone median PLR (hotter→): {out['hypotheses']['H1']['T_zone_median_plr']}")
    print(f"   monotone rho={mono_rho:+.3f} p={mono_p:.4f}")
    print("\n--- VERDICTS ---")
    for h, v in out["hypotheses"].items():
        extra = ""
        if v.get("eta2"):
            extra = f" (η²={v['eta2']['eta2_partial']:.3f}, p={v['eta2']['p']:.4f})"
        print(f"  {h}: {v['verdict']}{extra}")
    print("\n--- FALSIFIERS ---")
    for f, v in out["falsifiers"].items():
        print(f"  {f}: {'FIRED' if v.get('fired') else 'not fired'}")

    (PROC / "probe2_verdicts.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {PROC/'probe2_verdicts.json'}")


if __name__ == "__main__":
    main()
