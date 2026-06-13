"""RMD-SRC v3.4 -- OLS mixed-effects with Pop random intercept.

Per LOCKED PRE_REG_v3.4_amendment.md.
Single structural change vs v3.2: OLS-MixedLM with Population random intercept
replaces Huber RLM. Otherwise identical (AD gates, joint-GMM 4c).
"""
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")
import hashlib, datetime, os
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

ROOT = Path(r"D:/Phenotype_Research")
DERIVED = ROOT / "data/orchids/gymnadenia/derived"
RESULTS = ROOT / "results"
PREREG = ROOT / "prereg"
WC = RESULTS / "within_cell"

PART = DERIVED / "P0_partition_v20.parquet"
SCORES = DERIVED / "observable_scores_v11.parquet"
ENV_PC1 = RESULTS / "step2_env_PC1.parquet"

OBS = [f"x{i+1}" for i in range(7)]
R2F, AD_ALPHA = 0.30, 0.01
PREDF, MIN_N_SUBCELL = 0.5, 20


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1<<16), b""): h.update(c)
    return h.hexdigest()


def ad_test(x):
    x = np.asarray(x); x = x[~np.isnan(x)]
    if len(x) < 8: return float("nan"), False, len(x)
    try:
        r = stats.anderson(x, dist="norm")
        return float(r.statistic), bool(r.statistic < r.critical_values[4]), len(x)
    except: return float("nan"), False, len(x)


def evaluate_subset(idx, df_j, j, regime, beta_g_sign, env_pop, global_clean):
    sub = df_j.loc[idx]; n = len(sub)
    if n < 8: return {"n": n, "cell_clean": False, "fail_reason": "n<8"}
    mu = float(sub[j].mean())
    sd = float(sub[j].std(ddof=1)) if n > 1 else None
    ym = float(sub["yhat"].mean()); err = mu - ym
    err_r = abs(err)/sd if sd else float("nan")
    ad_stat, ad_pass, _ = ad_test(sub["resid"].to_numpy())
    pred_ok = err_r < PREDF
    if regime == "Insufficient_T": reg_ok = True
    elif regime == "Gradient-tracking":
        reg_ok = (beta_g_sign == int(np.sign(env_pop)))
    else: reg_ok = True
    cc = global_clean and ad_pass and pred_ok and reg_ok
    reasons = [g for g, ok in [("global", global_clean), ("AD", ad_pass),
                                ("pred", pred_ok), ("regime", reg_ok)] if not ok]
    return {"n": n, "cell_mu": mu, "cell_sd": sd, "yhat_mean": ym,
            "mu_err": err, "mu_err_rel_sd": err_r, "ad_stat_cell": ad_stat,
            "ad_pass_cell": ad_pass, "global_clean": global_clean,
            "pred_clean": pred_ok, "regime_consistent": reg_ok, "cell_clean": cc,
            "fail_reason": "/".join(reasons) or "clean"}


def main():
    p0 = pd.read_parquet(PART)
    scores = pd.read_parquet(SCORES)
    env = pd.read_parquet(ENV_PC1)
    env_by_pop = dict(zip(env["population"], env["env_PC1"]))

    df = (p0.merge(scores, on="PlantID")
            .merge(env[["population","env_PC1"]],
                   left_on="Population", right_on="population")
            .drop(columns=["population"]))
    df["y2011"] = (df["Year"]==2011).astype(int)

    # ============================================
    # STEP 3 v3.4 — MixedLM per observable
    # ============================================
    print("=== STEP 3 v3.4 — Pop random-intercept LMM ===\n")
    resp_rows = []
    re_estimates = []
    fits_cache = {}

    for j in OBS:
        try:
            mdl = smf.mixedlm(f"{j} ~ env_PC1 + y2011", df, groups=df["Population"])
            res = mdl.fit(reml=True, method="lbfgs")
            fits_cache[j] = res
            yhat = res.fittedvalues  # includes random effects
            resid = df[j] - yhat
            # conditional R² = 1 - SSE/SST on full fit
            sse = np.sum(resid**2); sst = np.sum((df[j] - df[j].mean())**2)
            condR2 = 1 - sse/sst if sst > 0 else float("nan")
            ad_stat, ad_pass, _ = ad_test(resid.to_numpy())
            beta_g = res.fe_params["env_PC1"]
            beta_g_sign = int(np.sign(beta_g))
            beta_g_se = res.bse_fe["env_PC1"]
            beta_g_t = beta_g / beta_g_se if beta_g_se > 0 else float("nan")
            beta_y = res.fe_params["y2011"]
            sigma_pop = float(np.sqrt(res.cov_re.iloc[0, 0]))
            sigma_resid = float(np.sqrt(res.scale))
            icc = sigma_pop**2 / (sigma_pop**2 + sigma_resid**2)
            global_clean = (condR2 >= R2F) and ad_pass
            resp_rows.append({
                "observable": j, "n": int(res.nobs),
                "cond_R2": condR2, "ad_stat": ad_stat, "ad_pass_global": ad_pass,
                "beta_g": float(beta_g), "beta_g_se": float(beta_g_se),
                "beta_g_t": float(beta_g_t), "beta_g_sign": beta_g_sign,
                "beta_y": float(beta_y),
                "sigma_pop": sigma_pop, "sigma_resid": sigma_resid, "ICC": icc,
                "global_clean": global_clean,
            })
            # extract random intercepts per pop
            re_dict = res.random_effects
            for pop, vec in re_dict.items():
                re_estimates.append({"observable": j, "population": pop,
                                     "u_pop": float(vec.iloc[0])})
        except Exception as e:
            print(f"  {j}: ERROR {e}")
            resp_rows.append({"observable": j, "n": 0,
                              "cond_R2": float("nan"),
                              "ad_pass_global": False, "global_clean": False})

    resp = pd.DataFrame(resp_rows)
    re_df = pd.DataFrame(re_estimates)
    resp.to_parquet(RESULTS / "step3_response_function_v34.parquet", index=False)
    re_df.to_parquet(RESULTS / "step_random_intercepts_v34.parquet", index=False)

    print(resp[["observable","cond_R2","ad_stat","ad_pass_global","beta_g","beta_g_t",
                "sigma_pop","sigma_resid","ICC","global_clean"]].round(3).to_string(index=False))

    ad_pass_count = int(resp["ad_pass_global"].sum())
    n_sig_pop_var = int((resp["sigma_pop"] >= 0.30).sum())
    n_id_g = int((resp["beta_g_t"].abs() > 2).sum())
    print(f"\n  H_v3.4A — σ_pop ≥ 0.30 on {n_sig_pop_var}/7 observables (target ≥ 4)")
    print(f"  H_v3.4D — β_g identifiable (|t| > 2) on {n_id_g}/7 observables (target ≥ 4)")

    # H_v3.4C: extreme random intercepts
    print(f"\n  H_v3.4C — random intercepts per pop per observable:")
    pivot_re = re_df.pivot(index="population", columns="observable", values="u_pop")
    print(pivot_re.round(3).to_string())
    print(f"\n  largest |u_pop| per observable:")
    for j in pivot_re.columns:
        col = pivot_re[j].abs().sort_values(ascending=False)
        top = col.head(3)
        print(f"    {j}: " + ", ".join(f"{p}={pivot_re.loc[p, j]:+.2f}" for p in top.index))

    # ============================
    # Cell cleanness
    # ============================
    print("\n=== Cell cleanness ===")
    cells = []
    converged_obs = list(fits_cache.keys())
    print(f"  Converged LMM observables: {converged_obs}")
    print(f"  Failed-LMM observables (singular cov): {[j for j in OBS if j not in converged_obs]}")
    for j in converged_obs:
        res = fits_cache[j]
        global_clean = bool(resp[resp["observable"]==j]["global_clean"].iloc[0])
        bg_sign_val = resp[resp["observable"]==j]["beta_g_sign"].iloc[0]
        if pd.isna(bg_sign_val):
            continue
        beta_g_sign = int(bg_sign_val)
        yhat = res.fittedvalues
        resid = df[j] - yhat
        sub_df = df.assign(yhat=yhat, resid=resid)
        for cell, cell_rows in sub_df.groupby("P0_cell"):
            pop = cell_rows["Population"].iloc[0]
            env_p = env_by_pop[pop]
            c = evaluate_subset(cell_rows.index, sub_df, j, "Insufficient_T",
                                beta_g_sign, env_p, global_clean)
            cells.append({**c, "P0_cell": cell, "observable": j, "population": pop,
                          "region": cell_rows["Region"].iloc[0],
                          "n_cell": int(c["n"])})
    cells_df = pd.DataFrame(cells)
    cells_df.to_parquet(RESULTS / "step3_cell_cleanness_v34.parquet", index=False)
    n0 = len(cells_df); n0_clean = int(cells_df["cell_clean"].sum())
    print(f"  pre-decomp clean: {n0_clean}/{n0} = {100*n0_clean/n0:.1f}%")

    # Step 4 with joint-GMM 4c (v3.2 style)
    print("\n=== Step 4 — 4b year + 4c joint-GMM subcell ===")
    wc_summary = pd.read_parquet(WC / "summary.parquet").set_index("cell")
    cell_labels = {}
    for cell in wc_summary.index:
        if int(wc_summary.loc[cell, "best_k_gmm_7d"]) > 1:
            f = WC / f"{cell}_gmm_labels.parquet"
            if os.path.exists(f):
                cell_labels[cell] = pd.read_parquet(f)

    leaves = []
    for _, l in cells_df[cells_df["cell_clean"]].iterrows():
        leaves.append({**l.to_dict(), "decomp_path": "carry-through"})

    for _, r in cells_df[~cells_df["cell_clean"]].iterrows():
        cell_id, j, pop = r["P0_cell"], r["observable"], r["population"]
        if j not in fits_cache: continue
        res = fits_cache[j]
        global_clean = bool(resp[resp["observable"]==j]["global_clean"].iloc[0])
        beta_g_sign = int(resp[resp["observable"]==j]["beta_g_sign"].iloc[0])
        env_p = env_by_pop[pop]
        yhat = res.fittedvalues
        resid = df[j] - yhat
        sub = df.assign(yhat=yhat, resid=resid)
        cell_rows = sub[sub["P0_cell"]==cell_id]
        recovered = False
        # 4b
        years = sorted(cell_rows["Year"].unique())
        if len(years) >= 2:
            cr = {}
            for y in years:
                idx = cell_rows[cell_rows["Year"]==y].index
                if len(idx) >= MIN_N_SUBCELL:
                    cr[y] = evaluate_subset(idx, sub, j, "Insufficient_T",
                                            beta_g_sign, env_p, global_clean)
            if any(c.get("cell_clean") for c in cr.values()):
                for y, c in cr.items():
                    leaves.append({**c, "P0_cell": f"{cell_id}/4b={y}",
                                   "observable": j, "population": pop,
                                   "region": r["region"], "decomp_path": "4b-year"})
                recovered = True
        if recovered: continue
        # 4c joint GMM
        if cell_id in cell_labels:
            lab_df = cell_labels[cell_id]
            merged = cell_rows.merge(lab_df, on="PlantID", how="left")
            cr = {}
            for cl in sorted(lab_df["gmm_cluster"].unique()):
                pids = merged[merged["gmm_cluster"]==cl]["PlantID"].tolist()
                cl_idx = sub[sub["PlantID"].isin(pids)].index
                if len(cl_idx) >= MIN_N_SUBCELL:
                    cr[cl] = evaluate_subset(cl_idx, sub, j, "Insufficient_T",
                                              beta_g_sign, env_p, global_clean)
            if any(c.get("cell_clean") for c in cr.values()):
                for cl, c in cr.items():
                    leaves.append({**c, "P0_cell": f"{cell_id}/4c-joint=cl{cl}",
                                   "observable": j, "population": pop,
                                   "region": r["region"], "decomp_path": "4c-joint-GMM"})
                continue
        leaves.append({**r.to_dict(), "decomp_path": "4abc_exhausted"})

    leaf_df = pd.DataFrame(leaves)
    leaf_df.to_parquet(RESULTS / "step4_leaves_v34.parquet", index=False)
    n_leaves = len(leaf_df); n_cl = int(leaf_df["cell_clean"].sum())

    print(f"\n=== RESULTS v3.4 ===")
    print(f"  pre-decomp clean:  {n0_clean}/{n0} = {100*n0_clean/n0:.1f}%")
    print(f"  post-decomp clean: {n_cl}/{n_leaves} = {100*n_cl/n_leaves:.1f}% of leaves")
    print(f"  recovered/orig:    {n_cl}/{n0} = {100*n_cl/n0:.1f}%")
    print(f"\n  vs v3.2 (19.6%): {'✓ IMPROVED' if (n_cl/n0)>0.196 else '✗ no improvement'}")
    print(f"  H_v3.4B post-decomp ≥ 25%: {'✓' if (n_cl/n0)>=0.25 else '✗'} ({100*n_cl/n0:.1f}%)")

    print("\n  leaves by decomp_path × clean:")
    print(leaf_df.groupby(["decomp_path","cell_clean"]).size().unstack(fill_value=0).to_string())
    print("\n  leaves by population × clean:")
    print(leaf_df.groupby(["population","cell_clean"]).size().unstack(fill_value=0).to_string())

    # Falsifiers
    F1 = (n0_clean / n0) >= 0.80
    F2 = (n_cl / n0) < 0.50
    print(f"\n=== FALSIFIERS v3.4 ===")
    print(f"  F1: {100*n0_clean/n0:.1f}%  {'FIRES' if F1 else 'silent'}")
    print(f"  F2: {100*n_cl/n0:.1f}%  {'FIRES' if F2 else 'silent'}")

    fals = pd.DataFrame([
        {"falsifier":"F1","value":n0_clean/n0,"threshold":0.80,"fires":F1},
        {"falsifier":"F2","value":n_cl/n0,"threshold":0.50,"fires":F2},
    ])
    fals.to_parquet(RESULTS / "step_falsifier_report_v34.parquet", index=False)

    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (PREREG / "v34_log.txt").write_text(
        f"# RMD-SRC Gymnadenia v3.4 — Pop random-intercept LMM\n"
        f"# Generated: {ts}\n"
        f"step3_response_function_v34.parquet sha = {sha(RESULTS/'step3_response_function_v34.parquet')}\n"
        f"step3_cell_cleanness_v34.parquet sha    = {sha(RESULTS/'step3_cell_cleanness_v34.parquet')}\n"
        f"step4_leaves_v34.parquet sha            = {sha(RESULTS/'step4_leaves_v34.parquet')}\n"
        f"step_random_intercepts_v34.parquet sha  = {sha(RESULTS/'step_random_intercepts_v34.parquet')}\n\n"
        f"H_v3.4A σ_pop ≥ 0.30 on  {n_sig_pop_var}/7 (target ≥ 4)\n"
        f"H_v3.4B post-decomp ≥ 25%: {100*n_cl/n0:.1f}%\n"
        f"H_v3.4D β_g identifiable: {n_id_g}/7 (target ≥ 4)\n\n"
        f"F1 fires: {F1}\nF2 fires: {F2}\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
