"""RMD-SRC v3.0 Step 3-5 -- Huber robust regression + Anderson-Darling gate.

Per LOCKED PRE_REG_v3.0_RMD_SRC_gymnadenia.md.
Inherits Steps 0-2 from v2.0.
"""
from pathlib import Path
import hashlib, datetime
from itertools import combinations
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.mixture import GaussianMixture
from sklearn.metrics import cohen_kappa_score

ROOT = Path(r"D:/Phenotype_Research")
DERIVED = ROOT / "data/orchids/gymnadenia/derived"
RESULTS = ROOT / "results"
PREREG = ROOT / "prereg"

PART = DERIVED / "P0_partition_v20.parquet"
SCORES = DERIVED / "observable_scores_v11.parquet"
ENV_PC1 = RESULTS / "step2_env_PC1.parquet"
REGIMES = RESULTS / "step2_regimes_v20.parquet"

OBS = [f"x{i+1}" for i in range(7)]
R2F, AD_ALPHA = 0.30, 0.01
PREDF, MIN_N = 0.5, 50


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1<<16), b""): h.update(c)
    return h.hexdigest()


def ad_test(x):
    """Anderson-Darling normality. Returns (statistic, pass_at_0.01, n).
    AD pass at p > 0.01 if statistic < critical_value at 1% sig level.
    scipy returns critical values for sig levels [15, 10, 5, 2.5, 1] %.
    """
    x = np.asarray(x)
    x = x[~np.isnan(x)]
    if len(x) < 8:
        return float("nan"), False, len(x)
    try:
        r = stats.anderson(x, dist="norm")
        return float(r.statistic), bool(r.statistic < r.critical_values[4]), len(x)
    except Exception:
        return float("nan"), False, len(x)


def pseudo_r2(y, yhat):
    """1 - SSE / SST"""
    sse = np.sum((y - yhat)**2)
    sst = np.sum((y - np.mean(y))**2)
    return 1 - sse / sst if sst > 0 else float("nan")


def cleanness_of_subset(idx, df_j, j, regime, beta_g_sign, env_pop, global_clean):
    sub = df_j.loc[idx]
    n = len(sub)
    if n < 8:
        return {"n": n, "cell_clean": False, "fail_reason": "n<8"}
    mu = float(sub[j].mean())
    sd = float(sub[j].std(ddof=1)) if n > 1 else None
    ym = float(sub["yhat"].mean())
    err = mu - ym
    err_r = abs(err)/sd if sd else float("nan")
    ad_stat, ad_pass, n_ad = ad_test(sub["resid"].to_numpy())
    pred_ok = err_r < PREDF
    if regime == "Insufficient_T": reg_ok = True
    elif regime == "Gradient-tracking":
        reg_ok = (beta_g_sign == int(np.sign(env_pop)))
    else: reg_ok = True
    cc = global_clean and ad_pass and pred_ok and reg_ok
    reasons = [g for g, ok in [("global", global_clean), ("AD", ad_pass),
                                ("pred", pred_ok), ("regime", reg_ok)] if not ok]
    return {"n": n, "cell_mu": mu, "cell_sd": sd, "yhat_mean": ym,
            "mu_err": err, "mu_err_rel_sd": err_r,
            "ad_stat_cell": ad_stat, "ad_pass_cell": ad_pass,
            "global_clean": global_clean, "pred_clean": pred_ok,
            "regime_consistent": reg_ok, "cell_clean": cc,
            "fail_reason": "/".join(reasons) or "clean"}


def best_gmm(x, max_k=3):
    x = np.asarray(x).reshape(-1, 1)
    best_k, best_bic = 1, np.inf
    best_labels = np.zeros(len(x), dtype=int)
    for k in range(1, max_k+1):
        if len(x) < k*MIN_N: break
        try:
            g = GaussianMixture(n_components=k, random_state=0,
                                covariance_type="full", n_init=3, reg_covar=1e-4).fit(x)
            lab = g.predict(x)
            if (np.bincount(lab, minlength=k) < MIN_N).any(): continue
            bic = g.bic(x)
            if bic < best_bic: best_bic, best_k, best_labels = bic, k, lab
        except: continue
    return best_k, best_labels


def main():
    p0 = pd.read_parquet(PART)
    scores = pd.read_parquet(SCORES)
    env = pd.read_parquet(ENV_PC1)
    regimes = pd.read_parquet(REGIMES)
    df = (p0.merge(scores, on="PlantID")
            .merge(env[["population","env_PC1"]],
                   left_on="Population", right_on="population")
            .drop(columns=["population"]))
    df["y2011"] = (df["Year"]==2011).astype(int)
    env_by_pop = dict(zip(env["population"], env["env_PC1"]))

    # ============================================================
    # STEP 3 v3.0 -- Huber RLM per observable
    # ============================================================
    print("=== STEP 3 v3.0 — Huber RLM per observable ===\n")
    X = sm.add_constant(df[["env_PC1","y2011"]])
    resp_rows, cell_rows = [], []
    fits = {}

    for j in OBS:
        y = df[j]
        rlm = sm.RLM(y, X, M=sm.robust.norms.HuberT()).fit()
        fits[j] = rlm
        yhat = rlm.fittedvalues
        resid = y - yhat
        pR2 = pseudo_r2(y.to_numpy(), yhat)
        ad_stat, ad_pass, _ = ad_test(resid.to_numpy())
        # Also report Shapiro for comparison with v2
        try: sh_p = stats.shapiro(resid).pvalue
        except: sh_p = float("nan")
        beta_g = rlm.params["env_PC1"]
        beta_g_p = rlm.pvalues["env_PC1"]
        beta_g_sign = int(np.sign(beta_g))
        global_clean = (pR2 >= R2F) and ad_pass

        resp_rows.append({
            "observable": j, "n": int(rlm.nobs),
            "pseudo_R2": pR2, "ad_stat": ad_stat, "ad_pass_global": ad_pass,
            "shapiro_p_for_compare": sh_p,
            "beta_const": rlm.params["const"],
            "beta_g": beta_g, "beta_g_sign": beta_g_sign,
            "beta_g_se": rlm.bse["env_PC1"], "beta_g_p": beta_g_p,
            "beta_y": rlm.params["y2011"], "beta_y_se": rlm.bse["y2011"],
            "beta_y_p": rlm.pvalues["y2011"],
            "global_clean": global_clean,
        })

        df_j = df.assign(yhat=yhat, resid=resid)
        for cell, sub in df_j.groupby("P0_cell"):
            pop = sub["Population"].iloc[0]
            reg_row = regimes[(regimes["P0_cell"]==cell) & (regimes["observable"]==j)]
            regime = reg_row["regime"].iloc[0] if len(reg_row) else "Unknown"
            env_p = env_by_pop[pop]
            c = cleanness_of_subset(sub.index, df_j, j, regime,
                                    beta_g_sign, env_p, global_clean)
            cell_rows.append({**c, "P0_cell": cell, "observable": j,
                              "population": pop, "region": sub["Region"].iloc[0],
                              "regime": regime, "n_cell": int(c["n"])})

    resp = pd.DataFrame(resp_rows)
    cells = pd.DataFrame(cell_rows)
    resp.to_parquet(RESULTS / "step3_response_function_v30.parquet", index=False)
    cells.to_parquet(RESULTS / "step3_cell_cleanness_v30.parquet", index=False)

    print(resp[["observable","pseudo_R2","ad_stat","ad_pass_global",
                "shapiro_p_for_compare","beta_g","beta_g_p","beta_y_p","global_clean"]].round(4).to_string(index=False))

    n_global_clean = int(resp["global_clean"].sum())
    print(f"\nH1 — global AD pass count: {n_global_clean}/7  (v2.0 was 1/7)")

    n0_clean = int(cells["cell_clean"].sum())
    n0 = len(cells)
    print(f"\npre-decomp cell-clean: {n0_clean}/{n0} = {100*n0_clean/n0:.1f}%")

    # ============================================================
    # STEP 4 decomp (inherited from v2.0 structure, v3.0 cleanness)
    # ============================================================
    print("\n=== STEP 4 — decomp with v3.0 cleanness ===")
    tree_rows, leaves = [], []
    for _, l in cells[cells["cell_clean"]].iterrows():
        leaves.append({**l.to_dict(), "decomp_path": "carry-through"})

    for _, r in cells[~cells["cell_clean"]].iterrows():
        cell_id, j, pop, regime = r["P0_cell"], r["observable"], r["population"], r["regime"]
        global_clean = bool(resp[resp["observable"]==j]["global_clean"].iloc[0])
        beta_g_sign = int(resp[resp["observable"]==j]["beta_g_sign"].iloc[0])
        env_p = env_by_pop[pop]
        fit = fits[j]
        df_j = df[df["P0_cell"]==cell_id].assign(
            yhat=fit.fittedvalues.loc[df["P0_cell"]==cell_id],
            resid=df[df["P0_cell"]==cell_id][j] - fit.fittedvalues.loc[df["P0_cell"]==cell_id])

        # 4a -- no categorical
        tree_rows.append({"parent": cell_id, "observable": j, "strategy": "4a",
                          "decision": "rejected", "termination": "no_valid_categorical_split"})

        # 4b -- year split
        years = sorted(df_j["Year"].unique())
        recovered = False
        if len(years) >= 2:
            child_results = {}
            for y in years:
                idx = df_j[df_j["Year"]==y].index
                if len(idx) < MIN_N:
                    child_results[y] = {"n": len(idx), "cell_clean": False,
                                         "fail_reason": "resolution_min_n"}
                else:
                    child_results[y] = cleanness_of_subset(idx, df_j, j, regime,
                                                            beta_g_sign, env_p, global_clean)
            ac = any(c.get("cell_clean") for c in child_results.values())
            tree_rows.append({"parent": cell_id, "observable": j, "strategy": "4b",
                              "decision": "locked" if ac else "rejected",
                              "termination": "" if ac else "no_4b_improvement"})
            if ac:
                for y, c in child_results.items():
                    leaves.append({**c, "P0_cell": f"{cell_id}/4b={y}",
                                   "observable": j, "population": pop,
                                   "region": r["region"], "regime": regime,
                                   "decomp_path": "4b-year"})
                recovered = True
        if recovered: continue

        # 4c -- GMM on x_j
        best_k, labels = best_gmm(df_j[j].to_numpy())
        if best_k == 1:
            tree_rows.append({"parent": cell_id, "observable": j, "strategy": "4c",
                              "decision": "rejected", "termination": "no_mixture"})
            leaves.append({**r.to_dict(), "decomp_path": "4abc_exhausted"})
            continue
        child_results = {}
        for k in range(best_k):
            idx = df_j.index[labels==k]
            child_results[k] = cleanness_of_subset(idx, df_j, j, regime,
                                                    beta_g_sign, env_p, global_clean)
        ac = any(c.get("cell_clean") for c in child_results.values())
        tree_rows.append({"parent": cell_id, "observable": j, "strategy": "4c",
                          "decision": "locked" if ac else "rejected",
                          "termination": "" if ac else "no_4c_improvement"})
        if ac:
            for k, c in child_results.items():
                leaves.append({**c, "P0_cell": f"{cell_id}/4c=k{k}",
                               "observable": j, "population": pop,
                               "region": r["region"], "regime": regime,
                               "decomp_path": f"4c-k{best_k}"})
        else:
            leaves.append({**r.to_dict(), "decomp_path": "4abc_exhausted"})

    tree = pd.DataFrame(tree_rows)
    leaf_df = pd.DataFrame(leaves)
    (RESULTS / "decomposition_logs_v30").mkdir(exist_ok=True)
    tree.to_parquet(RESULTS / "decomposition_logs_v30" / "decomp_tree.parquet", index=False)
    leaf_df.to_parquet(RESULTS / "step4_leaves_v30.parquet", index=False)

    n_leaves = len(leaf_df)
    n_cl = int(leaf_df["cell_clean"].sum())
    print(f"  decomp attempts: {len(tree)}; leaves: {n_leaves}")
    print(f"  pre-decomp clean / total: {n0_clean}/{n0} = {100*n0_clean/n0:.1f}%")
    print(f"  post-decomp clean / leaves: {n_cl}/{n_leaves} = {100*n_cl/n_leaves:.1f}%")
    print(f"  recovered / orig: {n_cl}/{n0} = {100*n_cl/n0:.1f}%")
    print("\n  leaves by decomp_path × clean:")
    print(leaf_df.groupby(["decomp_path","cell_clean"]).size().unstack(fill_value=0).to_string())
    print("\n  leaves by observable × clean:")
    print(leaf_df.groupby(["observable","cell_clean"]).size().unstack(fill_value=0).to_string())
    print("\n  leaves by population × clean:")
    print(leaf_df.groupby(["population","cell_clean"]).size().unstack(fill_value=0).to_string())

    # ============================================================
    # FALSIFIERS
    # ============================================================
    F1 = (n0_clean / n0) >= 0.80
    F2 = (n_cl / n0) < 0.50
    disagree = 0
    for _, l in leaf_df.iterrows():
        j = l["observable"]
        bsign = int(resp[resp["observable"]==j]["beta_g_sign"].iloc[0])
        bp = float(resp[resp["observable"]==j]["beta_g_p"].iloc[0])
        env_p = env_by_pop[l["population"]]
        agree = True
        if l["regime"] == "Gradient-tracking":
            agree = (bsign == int(np.sign(env_p)))
        elif l["regime"] == "Stationary":
            agree = (bp > 0.05)
        if not agree: disagree += 1
    F3 = (disagree / n_leaves) >= 0.30

    # F4 inherited from v2 regime classifications
    region_map = regimes.drop_duplicates("population").set_index("population")["region"]
    pivot = regimes.pivot(index="population", columns="observable", values="regime")
    traj_pops = [p for p in pivot.index if (pivot.loc[p] != "Insufficient_T").all()]
    kr = []
    for region in ["lowland","mountain"]:
        pops = [p for p in traj_pops if region_map[p]==region]
        for a,b in combinations(pops, 2):
            va, vb = pivot.loc[a].tolist(), pivot.loc[b].tolist()
            kr.append({"region": region, "pop_a": a, "pop_b": b,
                       "kappa": cohen_kappa_score(va, vb),
                       "raw_agree": sum(x==y for x,y in zip(va,vb))/len(va)})
    kdf = pd.DataFrame(kr)
    avg_k = kdf["kappa"].mean() if len(kdf) else float("nan")
    F4 = avg_k < 0.40 if not np.isnan(avg_k) else None

    print("\n=== FALSIFIER REPORT v3.0 ===")
    print(f"  F1 (>= 80% pre-decomp clean): {n0_clean}/{n0} = {100*n0_clean/n0:.1f}%  {'FIRES' if F1 else 'silent'}")
    print(f"  F2 (< 50% post-decomp clean): {n_cl}/{n0} = {100*n_cl/n0:.1f}%  {'FIRES' if F2 else 'silent'}")
    print(f"  F3 (>= 30% regime-vs-response disagree): {disagree}/{n_leaves} = {100*disagree/n_leaves:.1f}%  {'FIRES' if F3 else 'silent'}")
    print(f"  F4 (< 0.40 avg κ): {avg_k:.3f}  {'FIRES' if F4 else 'silent'}")

    fals = pd.DataFrame([
        {"falsifier":"F1","value":n0_clean/n0,"threshold":0.80,"fires":F1},
        {"falsifier":"F2","value":n_cl/n0,"threshold":0.50,"fires":F2},
        {"falsifier":"F3","value":disagree/n_leaves,"threshold":0.30,"fires":F3},
        {"falsifier":"F4","value":avg_k,"threshold":0.40,"fires":F4},
    ])
    fals.to_parquet(RESULTS / "step_falsifier_report_v30.parquet", index=False)

    # ============================================================
    # H3 -- Corviglia chemotype isolation check
    # ============================================================
    print("\n=== H3 — Corviglia chemotype check ===")
    corv = leaf_df[leaf_df["population"]=="Corviglia"]
    mono_obs = ["x1","x4","x5"]  # monoterpene-related per rotation loading
    print(corv[["P0_cell","observable","regime","n","cell_clean","fail_reason"]].to_string(index=False))
    corv_mono_failed = corv[(corv["observable"].isin(mono_obs)) & (~corv["cell_clean"])]
    corv_mono_ok = corv[(corv["observable"].isin(mono_obs)) & (corv["cell_clean"])]
    print(f"\n  Corviglia mono-obs failing: {len(corv_mono_failed)}/3 ({list(corv_mono_failed['observable'])})")
    print(f"  Corviglia mono-obs clean:   {len(corv_mono_ok)}/3 ({list(corv_mono_ok['observable'])})")

    # log
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log = PREREG / "v30_log.txt"
    log.write_text(
        f"# RMD-SRC Gymnadenia v3.0 — Huber + Anderson-Darling pipeline\n"
        f"# Generated: {ts}\n"
        f"# Per PRE_REG_v3.0\n\n"
        f"step3_response_function_v30.parquet sha     = {sha(RESULTS/'step3_response_function_v30.parquet')}\n"
        f"step3_cell_cleanness_v30.parquet sha        = {sha(RESULTS/'step3_cell_cleanness_v30.parquet')}\n"
        f"step4_leaves_v30.parquet sha                = {sha(RESULTS/'step4_leaves_v30.parquet')}\n"
        f"step_falsifier_report_v30.parquet sha       = {sha(RESULTS/'step_falsifier_report_v30.parquet')}\n\n"
        f"H1 global AD pass count (>= 4 to confirm): {n_global_clean}/7\n"
        f"H2 post-decomp clean (>= 50% to silence F2): {100*n_cl/n0:.1f}%\n"
        f"H3 Corviglia mono-obs failed: {len(corv_mono_failed)}/3\n\n"
        f"F1 fires (>= 80%):  {F1}\n"
        f"F2 fires (< 50%):   {F2}\n"
        f"F3 fires (>= 30%):  {F3}\n"
        f"F4 fires (< 0.40):  {F4}\n",
        encoding="utf-8")
    print(f"\nWrote {log}")


if __name__ == "__main__":
    main()
