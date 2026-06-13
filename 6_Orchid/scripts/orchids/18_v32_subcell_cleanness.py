"""RMD-SRC v3.2 -- subcell cleanness using locked joint 7-D GMM labels.

Per LOCKED PRE_REG_v3.2_amendment.md.
Inherits Huber fit from v3.0 unchanged. Only Step 4 decomp logic changes.
"""
from pathlib import Path
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import hashlib, datetime, os
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy import stats

ROOT = Path(r"D:/Phenotype_Research")
DERIVED = ROOT / "data/orchids/gymnadenia/derived"
RESULTS = ROOT / "results"
PREREG = ROOT / "prereg"
WC = RESULTS / "within_cell"

PART = DERIVED / "P0_partition_v20.parquet"
SCORES = DERIVED / "observable_scores_v11.parquet"
ENV_PC1 = RESULTS / "step2_env_PC1.parquet"
REGIMES = RESULTS / "step2_regimes_v20.parquet"
RESP_V30 = RESULTS / "step3_response_function_v30.parquet"
WC_SUMMARY = WC / "summary.parquet"

OBS = [f"x{i+1}" for i in range(7)]
R2F = 0.30
PREDF = 0.5
MIN_N_SUBCELL = 20    # softer than original 50 since these are sub-decomp


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
    regimes = pd.read_parquet(REGIMES)
    resp_v30 = pd.read_parquet(RESP_V30).set_index("observable")
    wc_summary = pd.read_parquet(WC_SUMMARY).set_index("cell")
    env_by_pop = dict(zip(env["population"], env["env_PC1"]))

    df = (p0.merge(scores, on="PlantID")
            .merge(env[["population","env_PC1"]],
                   left_on="Population", right_on="population")
            .drop(columns=["population"]))
    df["y2011"] = (df["Year"]==2011).astype(int)

    # Re-fit v3.0 Huber to get same residuals
    X = sm.add_constant(df[["env_PC1","y2011"]])
    fits = {}
    for j in OBS:
        fits[j] = sm.RLM(df[j], X, M=sm.robust.norms.HuberT()).fit()

    # Load locked GMM labels per cell (where best_k > 1)
    cell_labels = {}
    for cell in wc_summary.index:
        k = int(wc_summary.loc[cell, "best_k_gmm_7d"])
        if k > 1:
            f = WC / f"{cell}_gmm_labels.parquet"
            if os.path.exists(f):
                lab = pd.read_parquet(f)
                cell_labels[cell] = (k, lab)
    print(f"Cells with locked joint-7D GMM splits (k > 1):")
    for cell, (k, lab) in cell_labels.items():
        sizes = lab.groupby("gmm_cluster").size().to_dict()
        print(f"  {cell}  k={k}  sizes={sizes}")

    # ============ Step 4 v3.2 ============
    print("\n=== STEP 4 v3.2 — subcell cleanness on joint GMM clusters ===")
    leaves = []
    n_orig_total = 0; n_orig_clean = 0

    for cell in p0["P0_cell"].unique():
        cell_rows = df[df["P0_cell"]==cell]
        pop = cell_rows["Population"].iloc[0]
        region = cell_rows["Region"].iloc[0]
        env_p = env_by_pop[pop]

        for j in OBS:
            n_orig_total += 1
            reg_row = regimes[(regimes["P0_cell"]==cell) & (regimes["observable"]==j)]
            regime = reg_row["regime"].iloc[0] if len(reg_row) else "Unknown"
            global_clean = bool(resp_v30.loc[j, "global_clean"])
            beta_g_sign = int(resp_v30.loc[j, "beta_g_sign"])
            fit = fits[j]
            df_j = cell_rows.assign(yhat=fit.fittedvalues.loc[cell_rows.index],
                                     resid=cell_rows[j] - fit.fittedvalues.loc[cell_rows.index])
            parent_eval = evaluate_subset(cell_rows.index, df_j, j, regime,
                                          beta_g_sign, env_p, global_clean)
            if parent_eval["cell_clean"]:
                n_orig_clean += 1
                leaves.append({**parent_eval, "P0_cell": cell, "observable": j,
                               "population": pop, "region": region, "regime": regime,
                               "decomp_path": "carry-through"})
                continue

            # Try 4b year split if applicable
            recovered = False
            years = sorted(cell_rows["Year"].unique())
            if len(years) >= 2:
                children = []
                for y in years:
                    yidx = cell_rows[cell_rows["Year"]==y].index
                    if len(yidx) < MIN_N_SUBCELL: continue
                    children.append((f"4b={y}", yidx))
                yr_results = {tag: evaluate_subset(idx, df_j, j, regime, beta_g_sign,
                                                    env_p, global_clean)
                              for tag, idx in children}
                if any(r.get("cell_clean") for r in yr_results.values()):
                    for tag, c in yr_results.items():
                        leaves.append({**c, "P0_cell": f"{cell}/{tag}", "observable": j,
                                       "population": pop, "region": region, "regime": regime,
                                       "decomp_path": "4b-year"})
                    recovered = True
            if recovered: continue

            # Try v3.2 4c: locked joint-7D GMM split
            if cell in cell_labels:
                k, lab_df = cell_labels[cell]
                cell_with_lab = cell_rows.merge(lab_df, on="PlantID", how="left")
                children_cl = []
                for cl in sorted(lab_df["gmm_cluster"].unique()):
                    cl_idx = cell_with_lab[cell_with_lab["gmm_cluster"]==cl].index.tolist()
                    # map back to df_j index
                    pids = cell_with_lab[cell_with_lab["gmm_cluster"]==cl]["PlantID"].tolist()
                    cl_idx_in_df_j = df_j[df_j["PlantID"].isin(pids)].index
                    if len(cl_idx_in_df_j) < MIN_N_SUBCELL: continue
                    children_cl.append((cl, cl_idx_in_df_j))
                if children_cl:
                    cl_results = {f"4c-joint=cl{cl}": evaluate_subset(idx, df_j, j, regime,
                                                                       beta_g_sign, env_p,
                                                                       global_clean)
                                  for cl, idx in children_cl}
                    if any(r.get("cell_clean") for r in cl_results.values()):
                        for tag, c in cl_results.items():
                            leaves.append({**c, "P0_cell": f"{cell}/{tag}", "observable": j,
                                           "population": pop, "region": region,
                                           "regime": regime,
                                           "decomp_path": "4c-joint-GMM"})
                        continue
            # exhausted
            leaves.append({**parent_eval, "P0_cell": cell, "observable": j,
                           "population": pop, "region": region, "regime": regime,
                           "decomp_path": "4abc_exhausted"})

    leaf_df = pd.DataFrame(leaves)
    leaf_df.to_parquet(RESULTS / "step4_leaves_v32.parquet", index=False)
    n_leaves = len(leaf_df); n_cl = int(leaf_df["cell_clean"].sum())

    print(f"\n=== RESULTS v3.2 ===")
    print(f"  original cells:                {n_orig_total}")
    print(f"  pre-decomp clean (parent):      {n_orig_clean} = {100*n_orig_clean/n_orig_total:.1f}%")
    print(f"  post-decomp leaves total:       {n_leaves}")
    print(f"  post-decomp clean:              {n_cl} = {100*n_cl/n_leaves:.1f}% of leaves")
    print(f"  recovered / orig:               {n_cl}/{n_orig_total} = {100*n_cl/n_orig_total:.1f}%")
    print(f"\n  vs v3.0 (16.1%) → {('IMPROVED' if (n_cl/n_orig_total)>0.161 else 'no change/worse')}")

    print("\n  leaves by decomp_path × clean:")
    print(leaf_df.groupby(["decomp_path","cell_clean"]).size().unstack(fill_value=0).to_string())
    print("\n  leaves by population × clean:")
    print(leaf_df.groupby(["population","cell_clean"]).size().unstack(fill_value=0).to_string())

    # Corviglia
    print("\n=== H_v3.2B Corviglia subcell results ===")
    corv = leaf_df[leaf_df["population"]=="Corviglia"]
    print(corv[["P0_cell","observable","regime","n","cell_clean","fail_reason"]].to_string(index=False))

    # H_v3.2C
    print("\n=== H_v3.2C L_Ross + M_Muen subcells ===")
    for pop in ["Rossweid","Muenstertal"]:
        sub = leaf_df[leaf_df["population"]==pop]
        cleans = sub["cell_clean"].sum()
        print(f"  {pop}: {cleans} clean / {len(sub)} leaves")

    # Falsifiers
    F1 = (n_orig_clean / n_orig_total) >= 0.80
    F2 = (n_cl / n_orig_total) < 0.50
    print(f"\n=== FALSIFIERS v3.2 ===")
    print(f"  F1: {n_orig_clean}/{n_orig_total} = {100*n_orig_clean/n_orig_total:.1f}%  {'FIRES' if F1 else 'silent'}")
    print(f"  F2: {n_cl}/{n_orig_total} = {100*n_cl/n_orig_total:.1f}%  {'FIRES' if F2 else 'silent'}")

    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log = PREREG / "v32_log.txt"
    log.write_text(
        f"# RMD-SRC Gymnadenia v3.2 — subcell cleanness via locked joint-7D GMM\n"
        f"# Generated: {ts}\nstep4_leaves_v32.parquet sha = {sha(RESULTS/'step4_leaves_v32.parquet')}\n\n"
        f"original cells:        {n_orig_total}\n"
        f"pre-decomp clean:      {n_orig_clean} ({100*n_orig_clean/n_orig_total:.1f}%)\n"
        f"post-decomp clean:     {n_cl} ({100*n_cl/n_orig_total:.1f}%)\n"
        f"vs v3.0 (16.1%):       {'IMPROVED' if (n_cl/n_orig_total)>0.161 else 'no improvement'}\n\n"
        f"F1 fires: {F1}\nF2 fires: {F2}\n",
        encoding="utf-8")
    print(f"\nWrote {log}")


if __name__ == "__main__":
    main()
