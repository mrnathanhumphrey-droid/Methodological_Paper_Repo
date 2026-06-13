"""RMD-SRC v3.3 -- raw 26-compound observables, Huber + AD + joint-GMM 4c."""
from pathlib import Path
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import hashlib, datetime, os
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy import stats

ROOT = Path(r"D:/Phenotype_Research")
DERIVED = ROOT / "data/orchids/gymnadenia/derived"
RAW = ROOT / "data/orchids/gymnadenia/raw"
RESULTS = ROOT / "results"
PREREG = ROOT / "prereg"
WC = RESULTS / "within_cell"

PART = DERIVED / "P0_partition_v20.parquet"
ENV_PC1 = RESULTS / "step2_env_PC1.parquet"

R2F, AD_ALPHA = 0.30, 0.01
PREDF, MIN_N_SUBCELL = 0.5, 20

MORPH = ["PlantHeight_cm","InflorescenceLength_cm","NrFlowers"]
SCENT = ["Z3Hexen1Ol_ngPerL","Styrene_ngPerL","Heptanal_ngPerL","alphaPinene_ngPerL",
         "Benzaldehyde_ngPerL","Sabinene_ngPerL","betaPinene_ngPerL",
         "6Methyl5Hepten2One_ngPerL","Z3HexenylAcetate_ngPerL","HexylAcetate_ngPerL",
         "Limonene_ngPerL","BenzylAlcohol_ngPerL","Phenylacetaldehyde_ngPerL",
         "PhenylethylAlcohol_ngPerL","BenzylAcetate_ngPerL",
         "1Phenyl12Propanedione_ngPerL","Phenylethylacetate_ngPerL",
         "1Phenyl23Butanedione_ngPerL","Eugenol_ngPerL","MethylEugenol_ngPerL",
         "GeranylAcetone_ngPerL","Benzylbenzoate_ngPerL"]
COL = "ColourCode"
TRAITS = MORPH + SCENT + [COL]


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


def pseudo_r2(y, yhat):
    sse = np.sum((y - yhat)**2); sst = np.sum((y - np.mean(y))**2)
    return 1 - sse/sst if sst > 0 else float("nan")


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
    env = pd.read_parquet(ENV_PC1)
    env_by_pop = dict(zip(env["population"], env["env_PC1"]))

    # build raw trait matrix
    df_raw = pd.read_excel(RAW / "Data__SelectionAnalysis.xlsx", sheet_name="SelectionAnalysis")
    morph = df_raw[MORPH].apply(pd.to_numeric, errors="coerce")
    scent = df_raw[SCENT].apply(pd.to_numeric, errors="coerce")
    scent_log = np.log1p(scent.clip(lower=0))
    colour = pd.to_numeric(df_raw[COL], errors="coerce")
    Z = pd.concat([df_raw[["PlantID"]], morph, scent_log, colour.rename(COL)], axis=1)
    # global z (drop colour-NA rows for the standardization fit set)
    fit_set = Z.dropna()
    means = fit_set[TRAITS].mean()
    sds = fit_set[TRAITS].std(ddof=1)
    for t in TRAITS:
        Z[t] = (Z[t] - means[t]) / sds[t]
    Z = Z.merge(p0, on="PlantID").merge(env[["population","env_PC1"]],
                                          left_on="Population", right_on="population")
    Z["y2011"] = (Z["Year"]==2011).astype(int)
    print(f"modeling table: {Z.shape}")

    # ============== Step 3 v3.3 ==============
    print("\n=== STEP 3 v3.3 — 26 raw compound Huber fits ===")
    X = sm.add_constant(Z[["env_PC1","y2011"]])
    resp_rows = []
    fits = {}
    for j in TRAITS:
        sub = Z[Z[j].notna()]
        Xj = sm.add_constant(sub[["env_PC1","y2011"]])
        try:
            rlm = sm.RLM(sub[j], Xj, M=sm.robust.norms.HuberT()).fit()
            fits[j] = (rlm, sub.index)
            yhat = rlm.fittedvalues
            resid = sub[j] - yhat
            pR2 = pseudo_r2(sub[j].to_numpy(), yhat)
            ad_stat, ad_pass, _ = ad_test(resid.to_numpy())
            beta_g = rlm.params["env_PC1"]
            global_clean = (pR2 >= R2F) and ad_pass
            resp_rows.append({"observable": j, "n": int(rlm.nobs),
                              "pseudo_R2": pR2, "ad_stat": ad_stat,
                              "ad_pass_global": ad_pass,
                              "beta_g": beta_g, "beta_g_sign": int(np.sign(beta_g)),
                              "beta_g_p": rlm.pvalues["env_PC1"],
                              "beta_y": rlm.params["y2011"],
                              "beta_y_p": rlm.pvalues["y2011"],
                              "global_clean": global_clean})
        except Exception as e:
            resp_rows.append({"observable": j, "n": 0, "ad_pass_global": False,
                              "global_clean": False, "error": str(e)})
    resp = pd.DataFrame(resp_rows)
    resp.to_parquet(RESULTS / "step3_response_function_v33.parquet", index=False)

    # AD pass tally
    ad_pass_count = int(resp["ad_pass_global"].sum())
    print(f"\n  H_v3.3A — AD-pass observables: {ad_pass_count}/26 (v3.2 had 2/7 = 28.6%; threshold ≥ 8)")
    pass_obs = resp[resp["ad_pass_global"]]["observable"].tolist()
    fail_obs = resp[~resp["ad_pass_global"]]["observable"].tolist()
    print(f"  AD-pass: {pass_obs}")
    print(f"  AD-fail (top 5 by AD stat): "
          f"{resp.nlargest(5, 'ad_stat')['observable'].tolist()}")
    print()
    # show top failers' AD stats
    top_fail = resp.nlargest(5, "ad_stat")[["observable","ad_stat","pseudo_R2","beta_g","beta_g_p"]]
    print(top_fail.round(3).to_string(index=False))

    # ============== Cell cleanness ==============
    print("\n=== Step 4 cleanness across (cell × 26 obs) ===")
    cells = []
    for j in TRAITS:
        rlm_pair = fits.get(j)
        if rlm_pair is None: continue
        rlm, sub_idx = rlm_pair
        global_clean = bool(resp[resp["observable"]==j]["global_clean"].iloc[0])
        beta_g_sign = int(resp[resp["observable"]==j]["beta_g_sign"].iloc[0])
        sub = Z.loc[sub_idx].copy()
        sub["yhat"] = rlm.fittedvalues
        sub["resid"] = sub[j] - rlm.fittedvalues
        for cell, cell_rows in sub.groupby("P0_cell"):
            pop = cell_rows["Population"].iloc[0]
            env_p = env_by_pop[pop]
            c = evaluate_subset(cell_rows.index, sub, j, "Insufficient_T",
                                beta_g_sign, env_p, global_clean)
            cells.append({**c, "P0_cell": cell, "observable": j, "population": pop,
                          "region": cell_rows["Region"].iloc[0],
                          "n_cell": int(c["n"])})
    cells_df = pd.DataFrame(cells)
    cells_df.to_parquet(RESULTS / "step3_cell_cleanness_v33.parquet", index=False)
    n0 = len(cells_df); n0_clean = int(cells_df["cell_clean"].sum())
    print(f"  pre-decomp cleanness: {n0_clean}/{n0} = {100*n0_clean/n0:.1f}%")

    # ============ 4c-joint-GMM subcell evaluation =============
    print("\n=== Step 4c joint-7D-GMM subcell evaluation ===")
    wc_summary = pd.read_parquet(WC / "summary.parquet").set_index("cell")
    cell_labels = {}
    for cell in wc_summary.index:
        k = int(wc_summary.loc[cell, "best_k_gmm_7d"])
        if k > 1:
            f = WC / f"{cell}_gmm_labels.parquet"
            if os.path.exists(f):
                cell_labels[cell] = pd.read_parquet(f)

    leaves = []
    for _, l in cells_df[cells_df["cell_clean"]].iterrows():
        leaves.append({**l.to_dict(), "decomp_path": "carry-through"})
    for _, r in cells_df[~cells_df["cell_clean"]].iterrows():
        cell_id, j = r["P0_cell"], r["observable"]
        rlm, sub_idx = fits[j]
        global_clean = bool(resp[resp["observable"]==j]["global_clean"].iloc[0])
        beta_g_sign = int(resp[resp["observable"]==j]["beta_g_sign"].iloc[0])
        pop = r["population"]; env_p = env_by_pop[pop]
        sub = Z.loc[sub_idx].assign(yhat=rlm.fittedvalues,
                                       resid=Z.loc[sub_idx, j] - rlm.fittedvalues)
        cell_rows = sub[sub["P0_cell"]==cell_id]
        recovered = False
        # 4b year
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
            cell_merged = cell_rows.merge(lab_df, on="PlantID", how="left")
            cr = {}
            for cl in sorted(lab_df["gmm_cluster"].unique()):
                pids = cell_merged[cell_merged["gmm_cluster"]==cl]["PlantID"].tolist()
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
    leaf_df.to_parquet(RESULTS / "step4_leaves_v33.parquet", index=False)
    n_leaves = len(leaf_df); n_cl = int(leaf_df["cell_clean"].sum())
    print(f"\n=== RESULTS v3.3 ===")
    print(f"  K × d = 8 × 26 = {n0} original cells")
    print(f"  pre-decomp clean:       {n0_clean}/{n0} = {100*n0_clean/n0:.1f}%")
    print(f"  post-decomp clean:      {n_cl}/{n_leaves} = {100*n_cl/n_leaves:.1f}% of leaves")
    print(f"  recovered / original:   {n_cl}/{n0} = {100*n_cl/n0:.1f}%")
    print(f"\nH_v3.3A AD pass count (≥ 8): {ad_pass_count}/26  {'✓' if ad_pass_count >= 8 else '✗'}")
    print(f"H_v3.3B post-decomp ≥ 25%:    {100*n_cl/n0:.1f}%  {'✓' if (n_cl/n0)>=0.25 else '✗'}")

    print(f"\n  leaves by decomp_path × clean:")
    print(leaf_df.groupby(["decomp_path","cell_clean"]).size().unstack(fill_value=0).to_string())
    print(f"\n  leaves by population × clean:")
    print(leaf_df.groupby(["population","cell_clean"]).size().unstack(fill_value=0).to_string())

    # H_v3.3C: top AD-failers
    print(f"\nH_v3.3C — top 5 heaviest-tailed compounds (highest AD stat):")
    top5 = resp.nlargest(5, "ad_stat")[["observable","ad_stat","pseudo_R2"]]
    print(top5.round(3).to_string(index=False))

    # Falsifiers
    F1 = (n0_clean / n0) >= 0.80
    F2 = (n_cl / n0) < 0.50
    print(f"\n=== FALSIFIERS v3.3 ===")
    print(f"  F1: {n0_clean}/{n0} = {100*n0_clean/n0:.1f}%  {'FIRES' if F1 else 'silent'}")
    print(f"  F2: {n_cl}/{n0} = {100*n_cl/n0:.1f}%  {'FIRES' if F2 else 'silent'}")
    fals = pd.DataFrame([
        {"falsifier":"F1","value":n0_clean/n0,"threshold":0.80,"fires":F1},
        {"falsifier":"F2","value":n_cl/n0,"threshold":0.50,"fires":F2},
    ])
    fals.to_parquet(RESULTS / "step_falsifier_report_v33.parquet", index=False)

    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (PREREG / "v33_log.txt").write_text(
        f"# RMD-SRC Gymnadenia v3.3 — 26 raw compounds, Huber + AD + joint GMM\n"
        f"# Generated: {ts}\n"
        f"AD pass: {ad_pass_count}/26\n"
        f"pre-decomp clean:  {n0_clean}/{n0} = {100*n0_clean/n0:.1f}%\n"
        f"post-decomp clean: {n_cl}/{n0} = {100*n_cl/n0:.1f}%\n"
        f"F1 fires: {F1}\nF2 fires: {F2}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
