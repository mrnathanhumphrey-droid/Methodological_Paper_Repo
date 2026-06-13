"""RMD-SRC v3.1 -- Huber + Corviglia chemotype dummy.

Per LOCKED PRE_REG_v3.1_amendment.md.
Single change vs v3.0: add Corv_monomorph dummy from locked GMM labels.
"""
from pathlib import Path
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
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
WC = RESULTS / "within_cell"

PART = DERIVED / "P0_partition_v20.parquet"
SCORES = DERIVED / "observable_scores_v11.parquet"
ENV_PC1 = RESULTS / "step2_env_PC1.parquet"
REGIMES = RESULTS / "step2_regimes_v20.parquet"
CORV_LABELS = WC / "M_Corv_gmm_labels.parquet"

OBS = [f"x{i+1}" for i in range(7)]
R2F, AD_ALPHA = 0.30, 0.01
PREDF, MIN_N = 0.5, 50


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
    except Exception:
        return float("nan"), False, len(x)


def pseudo_r2(y, yhat):
    sse = np.sum((y - yhat)**2); sst = np.sum((y - np.mean(y))**2)
    return 1 - sse/sst if sst > 0 else float("nan")


def cleanness_of_subset(idx, df_j, j, regime, beta_g_sign, env_pop, global_clean):
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
    corv_labels = pd.read_parquet(CORV_LABELS)
    env_by_pop = dict(zip(env["population"], env["env_PC1"]))

    # build the Corv_monomorph dummy: 1 if (plant in Corviglia AND gmm_cluster==1)
    # cluster 1 is the smaller monoterpene-rich cluster per within-cell-noise analysis
    print(f"Corviglia GMM cluster sizes from locked labels:")
    print(corv_labels["gmm_cluster"].value_counts().to_string())
    # Identify which cluster is monoterpene-rich -- it had +β-pinene +Limonene loadings
    # per the cluster_traits parquet. Cluster 1 in M_Corv_gmm_cluster_traits had higher
    # monoterpene z-scores. Lock by direct read.
    corv_traits = pd.read_parquet(WC / "M_Corv_gmm_cluster_traits.parquet")
    # confirm: cluster with higher betaPinene_ngPerL_z is the morph
    mono_idx = corv_traits["betaPinene_ngPerL_z"].idxmax()
    print(f"  monomorph cluster index = {mono_idx} (β-pinene z-mean={corv_traits.loc[mono_idx,'betaPinene_ngPerL_z']:+.2f})")
    corv_morph_ids = corv_labels[corv_labels["gmm_cluster"]==mono_idx]["PlantID"].tolist()
    print(f"  Corv_monomorph plants: {len(corv_morph_ids)}")

    df = (p0.merge(scores, on="PlantID")
            .merge(env[["population","env_PC1"]],
                   left_on="Population", right_on="population")
            .drop(columns=["population"]))
    df["y2011"] = (df["Year"]==2011).astype(int)
    df["Corv_mono"] = df["PlantID"].isin(corv_morph_ids).astype(int)
    n_morph = df["Corv_mono"].sum()
    print(f"  total Corv_monomorph plants in modeling table: {n_morph}\n")

    # =====================================
    # STEP 3 v3.1 -- Huber + Corv_mono dummy
    # =====================================
    print("=== STEP 3 v3.1 — Huber + Corv_monomorph dummy ===\n")
    X = sm.add_constant(df[["env_PC1","y2011","Corv_mono"]])
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
        beta_g = rlm.params["env_PC1"]; beta_g_sign = int(np.sign(beta_g))
        beta_m = rlm.params["Corv_mono"]; beta_m_p = rlm.pvalues["Corv_mono"]
        global_clean = (pR2 >= R2F) and ad_pass
        resp_rows.append({
            "observable": j, "n": int(rlm.nobs),
            "pseudo_R2": pR2, "ad_stat": ad_stat, "ad_pass_global": ad_pass,
            "beta_const": rlm.params["const"],
            "beta_g": beta_g, "beta_g_sign": beta_g_sign,
            "beta_g_p": rlm.pvalues["env_PC1"],
            "beta_y": rlm.params["y2011"], "beta_y_p": rlm.pvalues["y2011"],
            "beta_m": beta_m, "beta_m_se": rlm.bse["Corv_mono"],
            "beta_m_p": beta_m_p,
            "global_clean": global_clean,
        })
        df_j = df.assign(yhat=yhat, resid=resid)
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
    resp.to_parquet(RESULTS / "step3_response_function_v31.parquet", index=False)
    cells.to_parquet(RESULTS / "step3_cell_cleanness_v31.parquet", index=False)

    print(resp[["observable","pseudo_R2","ad_stat","ad_pass_global",
                "beta_g","beta_g_p","beta_m","beta_m_p","global_clean"]].round(4).to_string(index=False))

    n_global = int(resp["global_clean"].sum())
    print(f"\nH_v3.1A — β_m significance (target ≥ 3 of 7 at p<0.01):")
    sig_m = (resp["beta_m_p"] < 0.01).sum()
    print(f"  β_m significant @ p<0.01 on {sig_m}/7 observables")
    print(f"  per-obs β_m: " + ", ".join(f"{r.observable}: β={r.beta_m:+.3f} p={r.beta_m_p:.4f}" for r in resp.itertuples()))

    n0 = len(cells); n0_clean = int(cells["cell_clean"].sum())
    print(f"\npre-decomp clean: {n0_clean}/{n0} = {100*n0_clean/n0:.1f}% (v3.0 was 12.5%)")

    # H_v3.1B Corviglia check
    corv = cells[cells["population"]=="Corviglia"]
    corv_clean = int(corv["cell_clean"].sum())
    print(f"\nH_v3.1B — Corviglia cleanness rose from 0/7 to {corv_clean}/7")
    print(corv[["P0_cell","observable","regime","n","cell_clean","fail_reason"]].to_string(index=False))

    # ==========================
    # STEP 4 decomp (v3.0 form)
    # ==========================
    print("\n=== STEP 4 — decomp with v3.1 cleanness ===")
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

        # 4a no split; 4b year; 4c GMM
        years = sorted(df_j["Year"].unique())
        recovered = False
        if len(years) >= 2:
            cr = {}
            for y in years:
                idx = df_j[df_j["Year"]==y].index
                if len(idx) < MIN_N:
                    cr[y] = {"n": len(idx), "cell_clean": False, "fail_reason": "resolution_min_n"}
                else:
                    cr[y] = cleanness_of_subset(idx, df_j, j, regime, beta_g_sign, env_p, global_clean)
            ac = any(c.get("cell_clean") for c in cr.values())
            if ac:
                for y, c in cr.items():
                    leaves.append({**c, "P0_cell": f"{cell_id}/4b={y}", "observable": j,
                                   "population": pop, "region": r["region"],
                                   "regime": regime, "decomp_path": "4b-year"})
                recovered = True
        if recovered: continue

        best_k, labels = best_gmm(df_j[j].to_numpy())
        if best_k == 1:
            leaves.append({**r.to_dict(), "decomp_path": "4abc_exhausted"})
            continue
        cr = {}
        for k in range(best_k):
            idx = df_j.index[labels==k]
            cr[k] = cleanness_of_subset(idx, df_j, j, regime, beta_g_sign, env_p, global_clean)
        ac = any(c.get("cell_clean") for c in cr.values())
        if ac:
            for k, c in cr.items():
                leaves.append({**c, "P0_cell": f"{cell_id}/4c=k{k}", "observable": j,
                               "population": pop, "region": r["region"],
                               "regime": regime, "decomp_path": f"4c-k{best_k}"})
        else:
            leaves.append({**r.to_dict(), "decomp_path": "4abc_exhausted"})

    leaf_df = pd.DataFrame(leaves)
    leaf_df.to_parquet(RESULTS / "step4_leaves_v31.parquet", index=False)
    n_leaves = len(leaf_df); n_cl = int(leaf_df["cell_clean"].sum())
    print(f"  pre-decomp clean: {n0_clean}/{n0} = {100*n0_clean/n0:.1f}%")
    print(f"  post-decomp clean leaves: {n_cl}/{n_leaves} = {100*n_cl/n_leaves:.1f}%")
    print(f"  recovered / orig: {n_cl}/{n0} = {100*n_cl/n0:.1f}%")
    print(f"\nH_v3.1C — substrate-wide cleanness vs v3.0 (16.1%):")
    print(f"  v3.1 post-decomp clean: {100*n_cl/n0:.1f}%   {'IMPROVED' if (n_cl/n0)>0.161 else 'no change/worse'}")

    print("\n  leaves by pop × clean:")
    print(leaf_df.groupby(["population","cell_clean"]).size().unstack(fill_value=0).to_string())

    # ==========================
    # FALSIFIERS
    # ==========================
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

    region_map = regimes.drop_duplicates("population").set_index("population")["region"]
    pivot = regimes.pivot(index="population", columns="observable", values="regime")
    traj_pops = [p for p in pivot.index if (pivot.loc[p] != "Insufficient_T").all()]
    kr = []
    for region in ["lowland","mountain"]:
        pops = [p for p in traj_pops if region_map[p]==region]
        for a,b in combinations(pops, 2):
            va, vb = pivot.loc[a].tolist(), pivot.loc[b].tolist()
            kr.append({"region": region, "pop_a": a, "pop_b": b,
                       "kappa": cohen_kappa_score(va, vb)})
    kdf = pd.DataFrame(kr)
    avg_k = kdf["kappa"].mean() if len(kdf) else float("nan")
    F4 = avg_k < 0.40 if not np.isnan(avg_k) else None

    print(f"\n=== FALSIFIER REPORT v3.1 ===")
    print(f"  F1: {n0_clean}/{n0} = {100*n0_clean/n0:.1f}%  {'FIRES' if F1 else 'silent'}")
    print(f"  F2: {n_cl}/{n0} = {100*n_cl/n0:.1f}%  {'FIRES' if F2 else 'silent'}")
    print(f"  F3: {disagree}/{n_leaves} = {100*disagree/n_leaves:.1f}%  {'FIRES' if F3 else 'silent'}")
    print(f"  F4: κ = {avg_k:.3f}  {'FIRES' if F4 else 'silent'}")

    fals = pd.DataFrame([
        {"falsifier":"F1","value":n0_clean/n0,"threshold":0.80,"fires":F1},
        {"falsifier":"F2","value":n_cl/n0,"threshold":0.50,"fires":F2},
        {"falsifier":"F3","value":disagree/n_leaves,"threshold":0.30,"fires":F3},
        {"falsifier":"F4","value":avg_k,"threshold":0.40,"fires":F4},
    ])
    fals.to_parquet(RESULTS / "step_falsifier_report_v31.parquet", index=False)

    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log = PREREG / "v31_log.txt"
    log.write_text(
        f"# RMD-SRC Gymnadenia v3.1 — Huber + Corv_monomorph dummy\n"
        f"# Generated: {ts}\n"
        f"# Per PRE_REG_v3.1_amendment.md\n\n"
        f"step3_response_function_v31.parquet sha = {sha(RESULTS/'step3_response_function_v31.parquet')}\n"
        f"step3_cell_cleanness_v31.parquet sha    = {sha(RESULTS/'step3_cell_cleanness_v31.parquet')}\n"
        f"step4_leaves_v31.parquet sha            = {sha(RESULTS/'step4_leaves_v31.parquet')}\n\n"
        f"H_v3.1A β_m sig count (target ≥3): {sig_m}/7\n"
        f"H_v3.1B Corviglia clean (target ≥4): {corv_clean}/7\n"
        f"H_v3.1C substrate post-decomp: {100*n_cl/n0:.1f}% (vs v3.0 16.1%)\n\n"
        f"F1 fires: {F1}\nF2 fires: {F2}\nF3 fires: {F3}\nF4 fires: {F4}\n",
        encoding="utf-8")
    print(f"\nWrote {log}")


if __name__ == "__main__":
    main()
