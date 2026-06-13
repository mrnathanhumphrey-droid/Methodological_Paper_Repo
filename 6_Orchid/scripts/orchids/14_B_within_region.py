"""POST-HOC EXPLORATORY -- within-region stratified RMD-SRC v2.0.

NOT pre-registered. Slices the substrate after the locked v2.0 pipeline ran.
Run on each region independently to test whether decomposition cleanness
patterns differ inside the lowland vs mountain block.

Per region:
  - subset plants (lowland 4 pops vs mountain 4 pops)
  - re-fit env-PC1 on within-region 4-pop env matrix (within-region gradient)
  - ℙ₀ = Pop (K=4 per region, time-invariant)
  - inherited rotation W_v11
  - run steps 1-5 within stratum, report falsifiers
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
ENV_CSV = DERIVED / "gymnadenia_pop_env_v2.csv"

OBS = [f"x{i+1}" for i in range(7)]
R2F, SHAPF, PREDF = 0.30, 0.01, 0.5
MIN_N = 50
STAT_MU, STAT_VAR = 0.05, 0.10
GRAD_MU = 0.05
CONC_VAR, DIFF_VAR = -0.15, 0.15
FRAG_DIP = 0.05

ENV_COVS = ["bio_1","bio_6","bio_12","bio_15",
            "phh2o_0-5cm","clay_0-5cm","sand_0-5cm","soc_0-5cm",
            "elev_wc5m","altitude_paper_m"]


def fit_env_pc1_in_region(env_region):
    M = env_region[ENV_COVS].apply(pd.to_numeric, errors="coerce")
    if M.isna().any().any():
        M = M.fillna(M.mean())
    mean, sd = M.mean(0), M.std(0, ddof=1).replace(0, 1)
    Z = ((M - mean) / sd).to_numpy()
    U, S, Vt = np.linalg.svd(Z, full_matrices=False)
    scores = U[:, 0] * S[0]
    elev_i = ENV_COVS.index("elev_wc5m")
    if Vt[0, elev_i] < 0:
        scores = -scores
    var_expl = (S[0]**2) / (S**2).sum()
    return dict(zip(env_region["population"], scores)), var_expl


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
    if n < 3:
        return {"n": n, "cell_clean": False, "fail_reason": "n<3"}
    mu = float(sub[j].mean())
    sd = float(sub[j].std(ddof=1)) if n > 1 else None
    ym = float(sub["yhat"].mean())
    err = mu - ym
    err_r = abs(err)/sd if sd else float("nan")
    try: sh = stats.shapiro(sub["resid"]).pvalue if n <= 5000 else np.nan
    except: sh = np.nan
    win = sh > SHAPF if not np.isnan(sh) else False
    pred = err_r < PREDF
    if regime == "Insufficient_T": reg = True
    elif regime == "Gradient-tracking":
        reg = (beta_g_sign == int(np.sign(env_pop)))
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
            lab = g.predict(x)
            if (np.bincount(lab, minlength=k) < MIN_N).any(): continue
            bic = g.bic(x)
            if bic < best_bic: best_bic, best_k, best_labels = bic, k, lab
        except: continue
    return best_k, best_labels


def run_stratum(region, plant_df, env_table):
    print(f"\n{'='*70}\nSTRATUM: {region}  (n_plants = {len(plant_df)})\n{'='*70}")
    env_pc1_map, var_expl = fit_env_pc1_in_region(env_table[env_table["region"]==region])
    print(f"  within-region env_PC1 explains {var_expl*100:.1f}% of {region} variance")
    for p, v in sorted(env_pc1_map.items(), key=lambda x: x[1]):
        print(f"    {p:15s}  env_PC1 = {v:+.3f}")

    df = plant_df.copy()
    df["env_PC1"] = df["Population"].map(env_pc1_map)
    df["y2011"] = (df["Year"]==2011).astype(int)

    # STEP 2 -- regime per (cell, observable)
    print(f"\n  Step 2 regime classifications:")
    r_rows = []
    for cell, sub_c in df.groupby("P0_cell"):
        pop = sub_c["Population"].iloc[0]
        env_p = env_pc1_map[pop]
        env_sign = 1 if env_p > 0 else -1
        years = sorted(sub_c["Year"].unique())
        for j in OBS:
            base = {"P0_cell": cell, "population": pop, "observable": j,
                    "env_PC1": env_p, "n_years": len(years)}
            if len(years) < 2:
                base["regime"] = "Insufficient_T"
                r_rows.append(base); continue
            m10 = sub_c[sub_c["Year"]==2010][j].dropna()
            m11 = sub_c[sub_c["Year"]==2011][j].dropna()
            mu_bar = (m10.mean() + m11.mean())/2
            var_bar = (m10.var(ddof=1) + m11.var(ddof=1))/2
            d_mu = m11.mean() - m10.mean()
            d_var = m11.var(ddof=1) - m10.var(ddof=1)
            d_mu_r = d_mu/mu_bar if abs(mu_bar) > 1e-9 else float("nan")
            d_var_r = d_var/var_bar if abs(var_bar) > 1e-9 else float("nan")
            grad_sign_ok = (np.sign(d_mu)==env_sign)
            grad_mag_ok = abs(d_mu_r) > GRAD_MU if not np.isnan(d_mu_r) else False
            try:
                dip_p = diptest.diptest(sub_c[j].dropna().to_numpy())[1]
            except: dip_p = 1.0
            base["regime"] = classify(d_mu_r, d_var_r, dip_p, grad_sign_ok, grad_mag_ok)
            r_rows.append(base)
    regimes = pd.DataFrame(r_rows)
    print(regimes.groupby("regime").size().to_string())

    # STEP 3 -- pooled response function within stratum
    print(f"\n  Step 3 response (env_PC1 + y2011, within {region}):")
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
                          "shapiro_p_pooled": sh_p, "beta_g": beta_g,
                          "beta_g_sign": beta_g_sign,
                          "beta_g_p": fit.pvalues["env_PC1"],
                          "beta_y": fit.params["y2011"],
                          "beta_y_p": fit.pvalues["y2011"],
                          "global_clean": global_clean})
        df_j = df.assign(yhat=fit.fittedvalues, resid=fit.resid)
        for cell, sub in df_j.groupby("P0_cell"):
            pop = sub["Population"].iloc[0]
            reg_row = regimes[(regimes["P0_cell"]==cell) & (regimes["observable"]==j)]
            regime = reg_row["regime"].iloc[0] if len(reg_row) else "Unknown"
            env_p = env_pc1_map[pop]
            c = cleanness_of_subset(sub.index, df_j, j, regime, beta_g_sign, env_p, global_clean)
            cell_rows.append({**c, "P0_cell": cell, "observable": j,
                              "population": pop, "regime": regime,
                              "n_cell": int(c["n"])})
    resp = pd.DataFrame(resp_rows)
    cells = pd.DataFrame(cell_rows)
    print(resp[["observable","R2","shapiro_p_pooled","beta_g","beta_g_p","global_clean"]].to_string(index=False))
    n0_clean = int(cells["cell_clean"].sum())
    n0 = len(cells)
    print(f"\n  pre-decomp clean: {n0_clean}/{n0} = {100.0*n0_clean/n0:.1f}%")

    # STEP 4 -- decomp
    print(f"\n  Step 4 decomp:")
    leaves = []
    for _, l in cells[cells["cell_clean"]].iterrows():
        leaves.append({**l.to_dict(), "decomp_path": "carry-through"})
    for _, r in cells[~cells["cell_clean"]].iterrows():
        cell_id = r["P0_cell"]; j = r["observable"]; pop = r["population"]
        regime = r["regime"]
        global_clean = bool(resp[resp["observable"]==j]["global_clean"].iloc[0])
        beta_g_sign = int(resp[resp["observable"]==j]["beta_g_sign"].iloc[0])
        env_p = env_pc1_map[pop]
        fit = fits[j]
        df_j = df[df["P0_cell"]==cell_id].assign(
            yhat=fit.fittedvalues.loc[df["P0_cell"]==cell_id],
            resid=fit.resid.loc[df["P0_cell"]==cell_id])
        # 4a: no valid split
        # 4b: year split
        years = sorted(df_j["Year"].unique())
        recovered = False
        if len(years) >= 2:
            child_results = {}
            for y in years:
                idx = df_j[df_j["Year"]==y].index
                if len(idx) < MIN_N:
                    child_results[y] = {"n": len(idx), "cell_clean": False}
                else:
                    child_results[y] = cleanness_of_subset(idx, df_j, j, regime,
                                                            beta_g_sign, env_p, global_clean)
            if any(c.get("cell_clean") for c in child_results.values()):
                for y, c in child_results.items():
                    leaves.append({**c, "P0_cell": f"{cell_id}/4b={y}",
                                   "observable": j, "population": pop,
                                   "regime": regime, "decomp_path": "4b-year"})
                recovered = True
        if recovered: continue
        # 4c
        best_k, labels = best_gmm(df_j[j].to_numpy())
        if best_k == 1:
            leaves.append({**r.to_dict(), "decomp_path": "4abc_exhausted"})
            continue
        child_results = {}
        for k in range(best_k):
            idx = df_j.index[labels==k]
            child_results[k] = cleanness_of_subset(idx, df_j, j, regime,
                                                    beta_g_sign, env_p, global_clean)
        if any(c.get("cell_clean") for c in child_results.values()):
            for k, c in child_results.items():
                leaves.append({**c, "P0_cell": f"{cell_id}/4c=k{k}",
                               "observable": j, "population": pop,
                               "regime": regime, "decomp_path": f"4c-k{best_k}"})
        else:
            leaves.append({**r.to_dict(), "decomp_path": "4abc_exhausted"})

    leaf_df = pd.DataFrame(leaves)
    n_leaves = len(leaf_df)
    n_clean_l = int(leaf_df["cell_clean"].sum())
    print(f"    post-decomp clean: {n_clean_l}/{n_leaves} = {100.0*n_clean_l/n_leaves:.1f}%")
    print(f"    recovered / orig:  {n_clean_l}/{n0} = {100.0*n_clean_l/n0:.1f}%")
    print(f"    leaves by decomp_path × clean:")
    print(leaf_df.groupby(["decomp_path","cell_clean"]).size().unstack(fill_value=0).to_string())

    # FALSIFIERS
    F1 = (n0_clean / n0) >= 0.80
    F2 = (n_clean_l / n0) < 0.50
    disagree = 0
    for _, l in leaf_df.iterrows():
        j = l["observable"]
        bsign = int(resp[resp["observable"]==j]["beta_g_sign"].iloc[0])
        bp = float(resp[resp["observable"]==j]["beta_g_p"].iloc[0])
        env_p = env_pc1_map[l["population"]]
        agree = True
        if l["regime"] == "Gradient-tracking":
            agree = (bsign == int(np.sign(env_p)))
        elif l["regime"] == "Stationary":
            agree = (bp > 0.05)
        if not agree: disagree += 1
    F3 = (disagree / n_leaves) >= 0.30
    # F4 within stratum
    pivot = regimes.pivot(index="population", columns="observable", values="regime")
    traj_pops = [p for p in pivot.index if (pivot.loc[p] != "Insufficient_T").all()]
    kr = []
    for a, b in combinations(traj_pops, 2):
        va, vb = pivot.loc[a].tolist(), pivot.loc[b].tolist()
        kr.append({"pop_a": a, "pop_b": b,
                   "kappa": cohen_kappa_score(va, vb),
                   "raw_agree": sum(x==y for x,y in zip(va,vb))/len(va)})
    kdf = pd.DataFrame(kr)
    avg_k = kdf["kappa"].mean() if len(kdf) else float("nan")
    F4 = avg_k < 0.40 if not np.isnan(avg_k) else None

    print(f"\n  === FALSIFIERS ({region}) ===")
    print(f"    F1 (>= 80%): {n0_clean}/{n0} = {100.0*n0_clean/n0:.1f}%  {'FIRES' if F1 else 'silent'}")
    print(f"    F2 (< 50%):  {n_clean_l}/{n0} = {100.0*n_clean_l/n0:.1f}%  {'FIRES' if F2 else 'silent'}")
    print(f"    F3 (>= 30%): {disagree}/{n_leaves} = {100.0*disagree/n_leaves:.1f}%  {'FIRES' if F3 else 'silent'}")
    print(f"    F4 (< 0.40): κ = {avg_k:.3f}  {'FIRES' if F4 else 'silent'}")
    if len(kdf):
        print(f"    F4 pairs:")
        print(kdf.round(3).to_string(index=False))

    return {"region": region, "n_plants": len(df),
            "var_expl_env_pc1": var_expl,
            "n_orig": n0, "n_orig_clean": n0_clean,
            "n_leaves": n_leaves, "n_clean_leaves": n_clean_l,
            "F1": F1, "F2": F2, "F3": F3, "F4": F4,
            "avg_kappa": avg_k, "n_disagree": disagree,
            "regimes": regimes, "cleanness": cells,
            "leaves": leaf_df, "f4_pairs": kdf, "response": resp}


def main():
    p0 = pd.read_parquet(PART)
    scores = pd.read_parquet(SCORES)
    env_csv = pd.read_csv(ENV_CSV)
    plants = p0.merge(scores, on="PlantID")

    summary = []
    for region in ["lowland", "mountain"]:
        sub = plants[plants["Region"]==region].copy()
        result = run_stratum(region, sub, env_csv)
        # save artifacts
        result["regimes"].to_parquet(RESULTS / f"step2_regimes_{region}.parquet", index=False)
        result["cleanness"].to_parquet(RESULTS / f"step3_cell_cleanness_{region}.parquet", index=False)
        result["leaves"].to_parquet(RESULTS / f"step4_leaves_{region}.parquet", index=False)
        result["response"].to_parquet(RESULTS / f"step3_response_function_{region}.parquet", index=False)
        if len(result["f4_pairs"]) > 0:
            result["f4_pairs"].to_parquet(RESULTS / f"step5_F4_pairs_{region}.parquet", index=False)
        summary.append({k: v for k, v in result.items()
                        if k in ["region","n_plants","var_expl_env_pc1","n_orig",
                                  "n_orig_clean","n_leaves","n_clean_leaves",
                                  "F1","F2","F3","F4","avg_kappa","n_disagree"]})

    sdf = pd.DataFrame(summary)
    sdf.to_parquet(RESULTS / "B_within_region_summary.parquet", index=False)

    print(f"\n{'='*70}\nSUMMARY ACROSS STRATA")
    print(f"{'='*70}")
    print(sdf.to_string(index=False))

    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log = PREREG / "B_within_region_log.txt"
    log.write_text(
        f"# POST-HOC EXPLORATORY -- within-region stratified RMD-SRC v2.0\n"
        f"# Generated: {ts}\n"
        f"# NOT pre-registered. Slices substrate after v2.0 full run.\n\n"
        f"{sdf.to_string(index=False)}\n",
        encoding="utf-8")
    print(f"\nWrote {log}")


if __name__ == "__main__":
    main()
