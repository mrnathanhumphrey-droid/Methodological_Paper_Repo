"""RMD-SRC v2.0 Steps 1-5 -- full pipeline under K=8 partition (Region × Pop).

Per LOCKED PRE_REG_v2.0_RMD_SRC_gymnadenia.md.
Inherits rotation W_v11 + scores_v11 + env_PC1 from v1.
"""
from pathlib import Path
import hashlib, datetime
from itertools import combinations
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.mixture import GaussianMixture
from sklearn.metrics import cohen_kappa_score
import diptest

ROOT = Path(r"D:/Phenotype_Research")
DERIVED = ROOT / "data/orchids/gymnadenia/derived"
RESULTS = ROOT / "results"
PREREG = ROOT / "prereg"

PART = DERIVED / "P0_partition_v20.parquet"
SCORES = DERIVED / "observable_scores_v11.parquet"
ENV_PC1 = RESULTS / "step2_env_PC1.parquet"

OBS = [f"x{i+1}" for i in range(7)]
R2F, SHAPF, PREDF = 0.30, 0.01, 0.5
MIN_N = 50

# §3.3 T=2 cutoffs
STAT_MU, STAT_VAR = 0.05, 0.10
GRAD_MU = 0.05
CONC_VAR, DIFF_VAR = -0.15, 0.15
FRAG_DIP = 0.05


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1<<16), b""): h.update(c)
    return h.hexdigest()


def classify(d_mu_rel, d_var_rel, dip_p, grad_sign_ok, grad_mag_ok):
    if dip_p < FRAG_DIP: return "Fragmenting"
    if d_var_rel < CONC_VAR: return "Concentrating"
    if d_var_rel > DIFF_VAR: return "Diffusing"
    if grad_sign_ok and grad_mag_ok: return "Gradient-tracking"
    if abs(d_mu_rel) < STAT_MU and abs(d_var_rel) < STAT_VAR: return "Stationary"
    return "Fragmenting"


def cleanness_of_subset(idx, df_j, j, regime, beta_g_sign, env_pop, global_clean):
    sub = df_j.loc[idx]
    n = len(sub)
    if n < 3: return {"n": n, "cell_clean": False, "fail_reason": "n<3"}
    mu = float(sub[j].mean())
    sd = float(sub[j].std(ddof=1)) if n > 1 else None
    ym = float(sub["yhat"].mean())
    err = mu - ym
    err_r = abs(err) / sd if sd else float("nan")
    try: sh = stats.shapiro(sub["resid"]).pvalue if n <= 5000 else np.nan
    except: sh = np.nan
    win = sh > SHAPF if not np.isnan(sh) else False
    pred = err_r < PREDF
    if regime == "Insufficient_T": reg = True
    elif regime == "Gradient-tracking": reg = (beta_g_sign == int(np.sign(env_pop)))
    else: reg = True
    cc = global_clean and win and pred and reg
    fr = "/".join(g for g, ok in [("global", global_clean), ("within", win),
                                   ("pred", pred), ("regime", reg)] if not ok) or "clean"
    return {"n": n, "cell_mu": mu, "cell_sd": sd, "yhat_mean": ym,
            "mu_err": err, "mu_err_rel_sd": err_r, "shapiro_p_cell": sh,
            "global_clean": global_clean, "within_cell_clean": win,
            "pred_clean": pred, "regime_consistent": reg, "cell_clean": cc,
            "fail_reason": fr}


def best_gmm(x, max_k=3):
    x = np.asarray(x).reshape(-1, 1)
    best_k, best_bic = 1, np.inf
    best_labels = np.zeros(len(x), dtype=int)
    for k in range(1, max_k + 1):
        if len(x) < k * MIN_N: break
        try:
            g = GaussianMixture(n_components=k, random_state=0,
                                covariance_type="full", n_init=3, reg_covar=1e-4).fit(x)
            bic = g.bic(x); lab = g.predict(x)
            if (np.bincount(lab, minlength=k) < MIN_N).any(): continue
            if bic < best_bic: best_bic, best_k, best_labels = bic, k, lab
        except: continue
    return best_k, best_labels


def main():
    p0 = pd.read_parquet(PART)
    scores = pd.read_parquet(SCORES)
    env = pd.read_parquet(ENV_PC1)
    df = (p0.merge(scores, on="PlantID")
            .merge(env[["population","env_PC1"]], left_on="Population", right_on="population")
            .drop(columns=["population"]))
    df["y2011"] = (df["Year"]==2011).astype(int)

    # ==============================================================
    # STEP 1 — moments per (cell, observable, year)
    # ==============================================================
    print("=== STEP 1 — moments per (cell, observable, year) ===")
    m_rows = []
    for cell, sub_c in df.groupby("P0_cell"):
        region = sub_c["Region"].iloc[0]
        pop = sub_c["Population"].iloc[0]
        for j in OBS:
            for year in [2010, 2011]:
                sub_y = sub_c[sub_c["Year"]==year]
                n = len(sub_y)
                v = sub_y[j].dropna()
                m_rows.append({"P0_cell": cell, "region": region, "population": pop,
                               "observable": j, "year": year, "n": n,
                               "mu": float(v.mean()) if n else None,
                               "var": float(v.var(ddof=1)) if n > 1 else None})
    moments = pd.DataFrame(m_rows)
    moments.to_parquet(RESULTS / "moment_trajectories_v20.parquet", index=False)
    print(f"  {len(moments)} (cell, obs, year) rows; populated = {moments['n'].gt(0).sum()}")

    # ==============================================================
    # STEP 2 — regime classification per (cell, observable)
    # ==============================================================
    print("\n=== STEP 2 — regime classification ===")
    env_by_pop = dict(zip(env["population"], env["env_PC1"]))
    r_rows = []
    for cell, sub_c in df.groupby("P0_cell"):
        region = sub_c["Region"].iloc[0]
        pop = sub_c["Population"].iloc[0]
        env_p = env_by_pop[pop]
        env_sign = 1 if env_p > 0 else -1
        years_in_cell = sorted(sub_c["Year"].unique())
        for j in OBS:
            base = {"P0_cell": cell, "region": region, "population": pop,
                    "observable": j, "env_PC1": env_p, "n_years": len(years_in_cell)}
            if len(years_in_cell) < 2:
                base.update({"regime": "Insufficient_T", "rule_path": "single_year_cell"})
                r_rows.append(base); continue
            r10 = moments[(moments["P0_cell"]==cell) & (moments["observable"]==j)
                          & (moments["year"]==2010)].iloc[0]
            r11 = moments[(moments["P0_cell"]==cell) & (moments["observable"]==j)
                          & (moments["year"]==2011)].iloc[0]
            mu_bar = (r10["mu"] + r11["mu"]) / 2
            var_bar = (r10["var"] + r11["var"]) / 2
            d_mu = r11["mu"] - r10["mu"]
            d_var = r11["var"] - r10["var"]
            d_mu_r = d_mu / mu_bar if abs(mu_bar) > 1e-9 else float("nan")
            d_var_r = d_var / var_bar if abs(var_bar) > 1e-9 else float("nan")
            grad_sign_ok = (np.sign(d_mu) == env_sign)
            grad_mag_ok = abs(d_mu_r) > GRAD_MU if not np.isnan(d_mu_r) else False
            try:
                dip_p = diptest.diptest(sub_c[j].dropna().to_numpy())[1]
            except:
                dip_p = 1.0
            regime = classify(d_mu_r, d_var_r, dip_p, grad_sign_ok, grad_mag_ok)
            base.update({"regime": regime, "d_mu": d_mu, "d_var": d_var,
                         "d_mu_rel": d_mu_r, "d_var_rel": d_var_r,
                         "dip_p": dip_p, "rule_path": "T2_delta"})
            r_rows.append(base)
    regimes = pd.DataFrame(r_rows)
    regimes.to_parquet(RESULTS / "step2_regimes_v20.parquet", index=False)
    print(f"  {len(regimes)} (cell, obs) classifications")
    cnt = regimes.groupby(["region","regime"]).size().unstack(fill_value=0)
    print(cnt.to_string())
    pivot = regimes.pivot(index="P0_cell", columns="observable", values="regime")
    print("\n", pivot.to_string())

    # ==============================================================
    # STEP 3 — pooled response function per observable, v1.3 Option B
    # ==============================================================
    print("\n=== STEP 3 — response function (Option B: env_PC1 + y2011) ===")
    X = sm.add_constant(df[["env_PC1","y2011"]])
    resp_rows, cell_rows = [], []
    fits = {}
    for j in OBS:
        fit = sm.OLS(df[j], X, missing="drop").fit(
            cov_type="cluster", cov_kwds={"groups": df["Population"]})
        fits[j] = fit
        sh_p = stats.shapiro(fit.resid).pvalue
        beta_g = fit.params["env_PC1"]
        beta_g_sign = int(np.sign(beta_g))
        global_clean = (fit.rsquared >= R2F) and (sh_p > SHAPF)
        resp_rows.append({"observable": j, "n": int(fit.nobs), "R2": fit.rsquared,
                          "shapiro_p_pooled": sh_p,
                          "beta_g": beta_g, "beta_g_sign": beta_g_sign,
                          "beta_g_p": fit.pvalues["env_PC1"],
                          "beta_y": fit.params["y2011"], "beta_y_p": fit.pvalues["y2011"],
                          "global_clean": global_clean})

        df_j = df.assign(yhat=fit.fittedvalues, resid=fit.resid)
        for cell, sub in df_j.groupby("P0_cell"):
            pop = sub["Population"].iloc[0]
            reg_row = regimes[(regimes["P0_cell"]==cell) & (regimes["observable"]==j)]
            regime = reg_row["regime"].iloc[0] if len(reg_row) else "Unknown"
            env_p = env_by_pop[pop]
            c = cleanness_of_subset(sub.index, df_j, j, regime, beta_g_sign, env_p, global_clean)
            cell_rows.append({**c, "P0_cell": cell, "observable": j,
                              "population": pop, "region": sub["Region"].iloc[0],
                              "regime": regime, "n_cell": int(c["n"])})
    resp = pd.DataFrame(resp_rows)
    cells = pd.DataFrame(cell_rows)
    resp.to_parquet(RESULTS / "step3_response_function_v20.parquet", index=False)
    cells.to_parquet(RESULTS / "step3_cell_cleanness_v20.parquet", index=False)
    print(resp[["observable","R2","shapiro_p_pooled","beta_g","beta_g_p","global_clean"]].to_string(index=False))

    n0_clean = int(cells["cell_clean"].sum())
    n0_total = len(cells)
    print(f"\n  pre-decomp clean: {n0_clean}/{n0_total} = {100.0*n0_clean/n0_total:.1f}%")

    # ==============================================================
    # STEP 4 — decomp, now with 4b alive
    # ==============================================================
    print("\n=== STEP 4 — decomposition (4a → 4b → 4c, 4b ALIVE) ===")
    tree_rows = []; leaves = []
    not_clean = cells[~cells["cell_clean"]].copy()
    for _, l in cells[cells["cell_clean"]].iterrows():
        leaves.append({"leaf_id": f"{l['P0_cell']}/{l['observable']}",
                       "parent_P0_cell": l["P0_cell"], "observable": l["observable"],
                       "population": l["population"], "region": l["region"],
                       "regime": l["regime"], "n": int(l["n_cell"]),
                       "cell_clean": True, "fail_reason": "clean",
                       "decomp_path": "carry-through"})

    for _, r in not_clean.iterrows():
        cell_id = r["P0_cell"]
        j = r["observable"]
        pop = r["population"]
        regime = r["regime"]
        global_clean = bool(resp[resp["observable"]==j]["global_clean"].iloc[0])
        beta_g_sign = int(resp[resp["observable"]==j]["beta_g_sign"].iloc[0])
        env_p = env_by_pop[pop]
        fit = fits[j]
        df_j = df[df["P0_cell"]==cell_id].assign(
            yhat=fit.fittedvalues.loc[df["P0_cell"]==cell_id],
            resid=fit.resid.loc[df["P0_cell"]==cell_id])

        # 4a -- no valid pre-outcome categorical (Region, Pop are cell ID)
        tree_rows.append({"parent": cell_id, "observable": j, "strategy": "4a",
                          "split_variable": "", "children": "",
                          "decision": "rejected", "termination": "no_valid_categorical_split"})

        # 4b -- TIME-PHASE SPLIT BY YEAR (alive in v2.0)
        years_in_cell = sorted(df_j["Year"].unique())
        if len(years_in_cell) >= 2:
            child_results = {}
            for y in years_in_cell:
                idx = df_j[df_j["Year"]==y].index
                if len(idx) < MIN_N:
                    child_results[y] = {"n": len(idx), "cell_clean": False,
                                         "fail_reason": "resolution_min_n"}
                else:
                    child_results[y] = cleanness_of_subset(idx, df_j, j, regime,
                                                            beta_g_sign, env_p, global_clean)
            any_clean = any(c.get("cell_clean") for c in child_results.values())
            tree_rows.append({"parent": cell_id, "observable": j, "strategy": "4b",
                              "split_variable": "Year",
                              "children": "|".join(f"{y}:{c['n']}" for y,c in child_results.items()),
                              "decision": "locked" if any_clean else "rejected",
                              "termination": "" if any_clean else "no_4b_improvement"})
            if any_clean:
                for y, c in child_results.items():
                    leaves.append({"leaf_id": f"{cell_id}/{j}/4b={y}",
                                   "parent_P0_cell": cell_id, "observable": j,
                                   "population": pop, "region": r["region"],
                                   "regime": regime, "n": int(c["n"]),
                                   "cell_clean": bool(c.get("cell_clean", False)),
                                   "fail_reason": c.get("fail_reason", ""),
                                   "decomp_path": "4b-year-split"})
                continue
        else:
            tree_rows.append({"parent": cell_id, "observable": j, "strategy": "4b",
                              "split_variable": "Year", "children": "",
                              "decision": "rejected", "termination": "single_year_cell"})

        # 4c -- GMM on observable
        best_k, labels = best_gmm(df_j[j].to_numpy())
        if best_k == 1:
            tree_rows.append({"parent": cell_id, "observable": j, "strategy": "4c",
                              "split_variable": f"GMM_{j}", "children": "",
                              "decision": "rejected", "termination": "no_mixture_k=1"})
            leaves.append({"leaf_id": f"{cell_id}/{j}",
                           "parent_P0_cell": cell_id, "observable": j,
                           "population": pop, "region": r["region"],
                           "regime": regime, "n": int(len(df_j)),
                           "cell_clean": False, "fail_reason": "failure_no_strategy",
                           "decomp_path": "4abc_exhausted"})
            continue
        child_results = {}
        for k in range(best_k):
            idx = df_j.index[labels==k]
            child_results[k] = cleanness_of_subset(idx, df_j, j, regime,
                                                    beta_g_sign, env_p, global_clean)
        any_clean = any(c.get("cell_clean") for c in child_results.values())
        tree_rows.append({"parent": cell_id, "observable": j, "strategy": "4c",
                          "split_variable": f"GMM_{j}_k={best_k}",
                          "children": "|".join(f"k{k}:{c['n']}" for k,c in child_results.items()),
                          "decision": "locked" if any_clean else "rejected",
                          "termination": "" if any_clean else "no_4c_improvement"})
        if any_clean:
            for k, c in child_results.items():
                leaves.append({"leaf_id": f"{cell_id}/{j}/4c=k{k}",
                               "parent_P0_cell": cell_id, "observable": j,
                               "population": pop, "region": r["region"],
                               "regime": regime, "n": int(c["n"]),
                               "cell_clean": bool(c.get("cell_clean", False)),
                               "fail_reason": c.get("fail_reason", ""),
                               "decomp_path": f"4c-k{best_k}"})
        else:
            leaves.append({"leaf_id": f"{cell_id}/{j}",
                           "parent_P0_cell": cell_id, "observable": j,
                           "population": pop, "region": r["region"],
                           "regime": regime, "n": int(len(df_j)),
                           "cell_clean": False, "fail_reason": "failure_no_strategy",
                           "decomp_path": "4abc_exhausted"})

    tree = pd.DataFrame(tree_rows)
    leaf_df = pd.DataFrame(leaves)
    (RESULTS / "decomposition_logs_v20").mkdir(exist_ok=True)
    tree.to_parquet(RESULTS / "decomposition_logs_v20" / "decomp_tree.parquet", index=False)
    leaf_df.to_parquet(RESULTS / "step4_leaves_v20.parquet", index=False)
    print(f"  decomp attempts: {len(tree)}; leaves: {len(leaf_df)}")

    n_leaves = len(leaf_df)
    n_clean_leaves = int(leaf_df["cell_clean"].sum())
    n_orig = len(cells)
    n_orig_clean = int(cells["cell_clean"].sum())

    print(f"\n  pre-decomp clean leaves: {n_orig_clean}/{n_orig} = {100.0*n_orig_clean/n_orig:.1f}%")
    print(f"  post-decomp clean leaves: {n_clean_leaves}/{n_leaves} = {100.0*n_clean_leaves/n_leaves:.1f}%")
    print(f"  recovered / original     : {n_clean_leaves}/{n_orig} = {100.0*n_clean_leaves/n_orig:.1f}%")
    print("\n  leaves by decomp_path × clean:")
    print(leaf_df.groupby(["decomp_path","cell_clean"]).size().unstack(fill_value=0).to_string())
    print("\n  leaves by observable × clean:")
    print(leaf_df.groupby(["observable","cell_clean"]).size().unstack(fill_value=0).to_string())

    # ==============================================================
    # FALSIFIERS F1 / F2 / F3
    # ==============================================================
    F1 = (n_orig_clean / n_orig) >= 0.80
    F2 = (n_clean_leaves / n_orig) < 0.50
    # F3 -- regime vs response disagreement
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

    # ==============================================================
    # STEP 5 / F4 -- between-pop κ within region
    # ==============================================================
    print("\n=== STEP 5 / F4 -- between-pop κ within region ===")
    region_map = regimes.drop_duplicates("population").set_index("population")["region"]
    pivot_t = regimes.pivot(index="population", columns="observable", values="regime")
    traj_pops = [p for p in pivot_t.index if (pivot_t.loc[p] != "Insufficient_T").all()]
    print(f"  trajectory-classifiable pops (both years in cell): {traj_pops}")

    kr = []
    for region in ["lowland", "mountain"]:
        pops = [p for p in traj_pops if region_map[p] == region]
        for a, b in combinations(pops, 2):
            va, vb = pivot_t.loc[a].tolist(), pivot_t.loc[b].tolist()
            kr.append({"region": region, "pop_a": a, "pop_b": b,
                       "kappa": cohen_kappa_score(va, vb),
                       "raw_agree": sum(x==y for x,y in zip(va,vb))/len(va)})
    kdf = pd.DataFrame(kr)
    print(kdf.round(3).to_string(index=False))
    avg_k = kdf["kappa"].mean() if len(kdf) else float("nan")
    F4 = avg_k < 0.40 if not np.isnan(avg_k) else None
    print(f"  avg κ = {avg_k:.3f}")
    kdf.to_parquet(RESULTS / "step5_F4_pairs_v20.parquet", index=False)

    # ==============================================================
    # falsifier report
    # ==============================================================
    print("\n=== FALSIFIER REPORT (v2.0) ===")
    print(f"  F1 (pre-decomp >= 80% clean):      {n_orig_clean}/{n_orig} = "
          f"{100.0*n_orig_clean/n_orig:.1f}%  -- {'FIRES' if F1 else 'silent'}")
    print(f"  F2 (post-decomp < 50% clean):      {n_clean_leaves}/{n_orig} = "
          f"{100.0*n_clean_leaves/n_orig:.1f}%  -- {'FIRES' if F2 else 'silent'}")
    print(f"  F3 (regime vs response, >= 30%):   {disagree}/{n_leaves} = "
          f"{100.0*disagree/n_leaves:.1f}%  -- {'FIRES' if F3 else 'silent'}")
    print(f"  F4 (between-pop κ < 0.40):         κ = {avg_k:.3f}  -- "
          f"{'FIRES' if F4 else 'silent'}")

    fals = pd.DataFrame([
        {"falsifier":"F1","value":n_orig_clean/n_orig,"threshold":0.80,"fires":F1},
        {"falsifier":"F2","value":n_clean_leaves/n_orig,"threshold":0.50,"fires":F2},
        {"falsifier":"F3","value":disagree/n_leaves,"threshold":0.30,"fires":F3},
        {"falsifier":"F4","value":avg_k,"threshold":0.40,"fires":F4},
    ])
    fals.to_parquet(RESULTS / "step_falsifier_report_v20.parquet", index=False)

    # log
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log = PREREG / "v20_log.txt"
    log.write_text(
        f"# RMD-SRC Gymnadenia v2.0 -- full pipeline\n"
        f"# Generated: {ts}\n"
        f"# Per PRE_REG_v2.0 + inherited v1.1/v1.2/v1.3\n\n"
        f"P0_partition_v20.parquet sha           = {sha(PART)}\n"
        f"moment_trajectories_v20.parquet sha    = {sha(RESULTS/'moment_trajectories_v20.parquet')}\n"
        f"step2_regimes_v20.parquet sha          = {sha(RESULTS/'step2_regimes_v20.parquet')}\n"
        f"step3_response_function_v20.parquet sha= {sha(RESULTS/'step3_response_function_v20.parquet')}\n"
        f"step3_cell_cleanness_v20.parquet sha   = {sha(RESULTS/'step3_cell_cleanness_v20.parquet')}\n"
        f"step4_leaves_v20.parquet sha           = {sha(RESULTS/'step4_leaves_v20.parquet')}\n"
        f"step5_F4_pairs_v20.parquet sha         = {sha(RESULTS/'step5_F4_pairs_v20.parquet')}\n"
        f"step_falsifier_report_v20.parquet sha  = {sha(RESULTS/'step_falsifier_report_v20.parquet')}\n\n"
        f"K cells (v2.0)              = 8\n"
        f"original (cell, obs) total  = {n_orig}\n"
        f"pre-decomp clean             = {n_orig_clean} ({100.0*n_orig_clean/n_orig:.2f}%)\n"
        f"post-decomp clean (leaves)   = {n_clean_leaves} / {n_leaves}\n"
        f"recovered / orig             = {n_clean_leaves}/{n_orig} = {100.0*n_clean_leaves/n_orig:.2f}%\n\n"
        f"F1 fires (>= 80%)            = {F1}\n"
        f"F2 fires (< 50%)             = {F2}\n"
        f"F3 fires (>= 30%)            = {F3}\n"
        f"F4 fires (< 0.40)            = {F4}\n",
        encoding="utf-8")
    print(f"\nWrote {log}")


if __name__ == "__main__":
    main()
