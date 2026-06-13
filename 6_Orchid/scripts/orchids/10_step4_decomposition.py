"""
RMD-SRC Step 4 -- decomposition for not-clean cells.

Per locked PRE_REG_v1.0 §1.4 + §3.5:
  Strictly 4a (categorical) -> 4b (time-phase) -> 4c (mixture).
  One strategy per not-clean node. No skipping, no reordering.
  Each attempt logged to results/decomposition_logs/decomp_tree.parquet.

Substrate notes (logged per §1.4 "no skipping" rule):
  4a: only M_Muen_2010 has within-cell pop variation (Schatzalp + Muenstertal
      collapse). All other cells encode (Region, Pop, Year) in their ID and
      have no pre-outcome categorical structure left to split on. For those
      cells, 4a attempt is logged as "no_valid_split" and execution proceeds
      to 4b per the spec ordering.
  4b: every cell is single-year by construction (Year is inside P0_cell ID).
      No within-cell t-bins exist. 4b attempt is logged as "single_year_cell"
      for every cell and execution proceeds to 4c.
  4c: Gaussian Mixture on plant x_j scores within (cell, observable),
      k=1..3 by BIC. If best_k=1: termination='no_mixture'. If best_k>1
      but any component below MIN_CELL_N=50: reject, fall back to lower k.

Output:
  results/decomposition_logs/decomp_tree.parquet
  results/step4_leaves.parquet     (final leaf inventory + cleanness)
  results/step4_falsifier_report.parquet
"""

from pathlib import Path
import hashlib
import datetime
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.mixture import GaussianMixture

ROOT = Path(r"D:/Phenotype_Research")
DERIVED = ROOT / "data/orchids/gymnadenia/derived"
RESULTS = ROOT / "results"
PREREG = ROOT / "prereg"

PARTITION_PARQUET = DERIVED / "P0_partition.parquet"
SCORES_PARQUET = DERIVED / "observable_scores_v11.parquet"
ENV_PC1_PARQUET = RESULTS / "step2_env_PC1.parquet"
REGIMES_PARQUET = RESULTS / "step2_regimes.parquet"
RESP_PARQUET = RESULTS / "step3_response_function.parquet"
CLEAN_PARQUET = RESULTS / "step3_cell_cleanness.parquet"

TREE_DIR = RESULTS / "decomposition_logs"
TREE_DIR.mkdir(parents=True, exist_ok=True)
TREE_PARQUET = TREE_DIR / "decomp_tree.parquet"
LEAVES_PARQUET = RESULTS / "step4_leaves.parquet"
FALSIFIER_PARQUET = RESULTS / "step4_falsifier_report.parquet"

OBS_COLS = [f"x{i+1}" for i in range(7)]
R2_FLOOR, SHAPIRO_P_FLOOR, CELL_PRED_TOL_SD = 0.30, 0.01, 0.5
MIN_CELL_N = 50
MAX_K_MIXTURE = 3


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def cleanness_of_subset(sub_idx, df_j, j, regime, beta_g_sign, env_pc1_pop,
                       global_clean):
    """Evaluate v1.3 §3.4 cleanness gates on a subset of plant rows."""
    sub = df_j.loc[sub_idx]
    n = len(sub)
    if n < 3:
        return {"n": n, "cell_clean": False, "fail_reason": "n<3"}
    cell_mu = float(sub[j].mean())
    cell_sd = float(sub[j].std(ddof=1)) if n > 1 else None
    yhat_mean = float(sub["yhat"].mean())
    mu_err = cell_mu - yhat_mean
    mu_err_rel = abs(mu_err) / cell_sd if cell_sd and cell_sd > 0 else float("nan")
    try:
        sh_cell = stats.shapiro(sub["resid"]).pvalue if n <= 5000 else np.nan
    except Exception:
        sh_cell = np.nan
    within_ok = sh_cell > SHAPIRO_P_FLOOR if not np.isnan(sh_cell) else False
    pred_ok = mu_err_rel < CELL_PRED_TOL_SD
    if regime == "Insufficient_T":
        reg_ok = True
    elif regime == "Gradient-tracking":
        reg_ok = (beta_g_sign == int(np.sign(env_pc1_pop)))
    else:
        reg_ok = True
    cc = global_clean and within_ok and pred_ok and reg_ok
    reasons = []
    if not global_clean: reasons.append("global")
    if not within_ok: reasons.append("within")
    if not pred_ok: reasons.append("pred")
    if not reg_ok: reasons.append("regime")
    return {"n": n, "cell_mu": cell_mu, "cell_sd": cell_sd,
            "yhat_mean": yhat_mean, "mu_err": mu_err,
            "mu_err_rel_sd": mu_err_rel, "shapiro_p_cell": sh_cell,
            "within_cell_clean": within_ok, "pred_clean": pred_ok,
            "regime_consistent": reg_ok, "cell_clean": cc,
            "fail_reason": "/".join(reasons) or "clean"}


def best_gmm(x, max_k):
    """Fit GMM with k=1..max_k, return (best_k, labels) by BIC; respect MIN_CELL_N."""
    x = np.asarray(x).reshape(-1, 1)
    best_k = 1
    best_bic = np.inf
    best_labels = np.zeros(len(x), dtype=int)
    for k in range(1, max_k + 1):
        if len(x) < k * MIN_CELL_N:
            break
        try:
            gmm = GaussianMixture(n_components=k, random_state=0,
                                  covariance_type="full",
                                  n_init=3, reg_covar=1e-4)
            gmm.fit(x)
            bic = gmm.bic(x)
            labels = gmm.predict(x)
            # respect MIN_CELL_N on every component
            counts = np.bincount(labels, minlength=k)
            if (counts < MIN_CELL_N).any():
                continue
            if bic < best_bic:
                best_bic, best_k, best_labels = bic, k, labels
        except Exception:
            continue
    return best_k, best_labels


def main():
    # --- load + verify ---
    p0_sha = sha256_file(PARTITION_PARQUET)
    locked = next((l for l in (PREREG/"P0_hash.txt").read_text(encoding="utf-8").splitlines()
                   if "P0_partition.parquet sha256" in l), "").split("=")[1].strip()
    assert p0_sha == locked
    print(f"P0 hash verified: {p0_sha[:16]}...")

    part = pd.read_parquet(PARTITION_PARQUET)
    scores = pd.read_parquet(SCORES_PARQUET)
    env = pd.read_parquet(ENV_PC1_PARQUET)
    regimes = pd.read_parquet(REGIMES_PARQUET)
    resp = pd.read_parquet(RESP_PARQUET).set_index("observable")
    parent_clean = pd.read_parquet(CLEAN_PARQUET)

    df = (part.merge(scores, on="PlantID")
              .merge(env[["population","env_PC1"]],
                     left_on="Population", right_on="population")
              .drop(columns=["population"]))
    df["y2011"] = (df["Year"]==2011).astype(int)

    # rebuild fits (yhat + resid per observable) -- same as v1.3 Step 3
    X = sm.add_constant(df[["env_PC1","y2011"]])
    fits = {}
    for j in OBS_COLS:
        fit = sm.OLS(df[j], X).fit()
        fits[j] = fit.fittedvalues
        df = df.assign(**{f"resid_{j}": df[j] - fit.fittedvalues})

    # --- decomposition loop ---
    tree_rows = []
    leaves = []   # final leaves: (leaf_id, P0_cell parent, observable, plant_idx_set, cleanness dict)
    not_clean = parent_clean[~parent_clean["cell_clean"]].copy()
    clean_passthrough = parent_clean[parent_clean["cell_clean"]].copy()

    # carry-through clean cells straight to leaves
    for _, r in clean_passthrough.iterrows():
        leaves.append({
            "leaf_id": f"{r['P0_cell']}/{r['observable']}",
            "parent_P0_cell": r["P0_cell"], "observable": r["observable"],
            "population": r["population"], "region": r["region"],
            "year": r["year"], "regime": r["regime"],
            "n": int(r["n_cell"]), "cell_clean": True,
            "fail_reason": "clean", "decomp_path": "carry-through",
        })

    print(f"\nStarting decomp on {len(not_clean)} not-clean (cell, obs) pairs")

    for _, r in not_clean.iterrows():
        cell_id = r["P0_cell"]
        j = r["observable"]
        pop = r["population"]
        regime = r["regime"]
        global_clean = bool(resp.loc[j, "global_clean"])
        beta_g_sign = int(resp.loc[j, "beta_g_sign"])
        env_pc1_pop = float(env[env["population"]==pop]["env_PC1"].iloc[0])

        df_j = df[df["P0_cell"]==cell_id].assign(
            yhat=fits[j].loc[df["P0_cell"]==cell_id],
            resid=df[df["P0_cell"]==cell_id][f"resid_{j}"],
        ).copy()

        # ---- 4a categorical ----
        unique_pops_in_cell = df_j["Population"].unique()
        if len(unique_pops_in_cell) > 1:
            split_var = "Population"
            children = {}
            for cp in unique_pops_in_cell:
                children[cp] = df_j[df_j["Population"]==cp].index
            child_results = {}
            for cp, idx in children.items():
                if len(idx) < MIN_CELL_N:
                    child_results[cp] = {"n": len(idx), "cell_clean": False,
                                          "fail_reason": "resolution_min_n"}
                else:
                    child_results[cp] = cleanness_of_subset(
                        idx, df_j, j, regime, beta_g_sign, env_pc1_pop,
                        global_clean)
            any_clean = any(c.get("cell_clean") for c in child_results.values())
            tree_rows.append({
                "parent": cell_id, "observable": j, "strategy": "4a",
                "split_variable": split_var,
                "children": "|".join(f"{cp}:{c['n']}" for cp,c in child_results.items()),
                "parent_clean": False,
                "child_clean_mean": np.mean([c.get("cell_clean", False)
                                              for c in child_results.values()]),
                "decision": "locked" if any_clean else "rejected",
                "termination": "" if any_clean else "no_4a_improvement",
            })
            if any_clean:
                for cp, c in child_results.items():
                    leaves.append({
                        "leaf_id": f"{cell_id}/{j}/4a={cp}",
                        "parent_P0_cell": cell_id, "observable": j,
                        "population": cp, "region": r["region"],
                        "year": r["year"], "regime": regime,
                        "n": int(c["n"]), "cell_clean": bool(c.get("cell_clean", False)),
                        "fail_reason": c.get("fail_reason", ""),
                        "decomp_path": "4a-split",
                    })
                continue
        else:
            tree_rows.append({
                "parent": cell_id, "observable": j, "strategy": "4a",
                "split_variable": "", "children": "",
                "parent_clean": False, "child_clean_mean": np.nan,
                "decision": "rejected",
                "termination": "no_valid_categorical_split",
            })

        # ---- 4b time-phase ----
        tree_rows.append({
            "parent": cell_id, "observable": j, "strategy": "4b",
            "split_variable": "Year", "children": "",
            "parent_clean": False, "child_clean_mean": np.nan,
            "decision": "rejected", "termination": "single_year_cell",
        })

        # ---- 4c mixture (GMM on observable x_j within cell) ----
        x_vals = df_j[j].to_numpy()
        best_k, labels = best_gmm(x_vals, MAX_K_MIXTURE)
        if best_k == 1:
            tree_rows.append({
                "parent": cell_id, "observable": j, "strategy": "4c",
                "split_variable": f"GMM_{j}", "children": "",
                "parent_clean": False, "child_clean_mean": np.nan,
                "decision": "rejected", "termination": "no_mixture_k=1",
            })
            leaves.append({
                "leaf_id": f"{cell_id}/{j}",
                "parent_P0_cell": cell_id, "observable": j,
                "population": pop, "region": r["region"],
                "year": r["year"], "regime": regime,
                "n": int(len(df_j)), "cell_clean": False,
                "fail_reason": "failure_no_strategy",
                "decomp_path": "4abc_exhausted",
            })
            continue
        # k>1: split
        child_results = {}
        sub_idx_lists = []
        for ki in range(best_k):
            sub_idx = df_j.index[labels==ki]
            sub_idx_lists.append((ki, sub_idx))
            child_results[ki] = cleanness_of_subset(
                sub_idx, df_j, j, regime, beta_g_sign, env_pc1_pop,
                global_clean)
        any_clean = any(c.get("cell_clean") for c in child_results.values())
        tree_rows.append({
            "parent": cell_id, "observable": j, "strategy": "4c",
            "split_variable": f"GMM_{j}_k={best_k}",
            "children": "|".join(f"k{ki}:{c['n']}" for ki,c in child_results.items()),
            "parent_clean": False,
            "child_clean_mean": np.mean([c.get("cell_clean", False)
                                          for c in child_results.values()]),
            "decision": "locked" if any_clean else "rejected",
            "termination": "" if any_clean else "no_4c_improvement",
        })
        if any_clean:
            for ki, c in child_results.items():
                leaves.append({
                    "leaf_id": f"{cell_id}/{j}/4c=k{ki}",
                    "parent_P0_cell": cell_id, "observable": j,
                    "population": pop, "region": r["region"],
                    "year": r["year"], "regime": regime,
                    "n": int(c["n"]), "cell_clean": bool(c.get("cell_clean", False)),
                    "fail_reason": c.get("fail_reason", ""),
                    "decomp_path": f"4c-k{best_k}",
                })
        else:
            # split rejected; cell remains as a failure leaf
            leaves.append({
                "leaf_id": f"{cell_id}/{j}",
                "parent_P0_cell": cell_id, "observable": j,
                "population": pop, "region": r["region"],
                "year": r["year"], "regime": regime,
                "n": int(len(df_j)), "cell_clean": False,
                "fail_reason": "failure_no_strategy",
                "decomp_path": "4abc_exhausted",
            })

    # --- finalize ---
    tree = pd.DataFrame(tree_rows)
    leaf_df = pd.DataFrame(leaves)
    tree.to_parquet(TREE_PARQUET, index=False)
    leaf_df.to_parquet(LEAVES_PARQUET, index=False)
    print(f"\nWrote {TREE_PARQUET} ({len(tree)} attempts)")
    print(f"Wrote {LEAVES_PARQUET} ({len(leaf_df)} leaves)")

    # --- tally ---
    n_leaves = len(leaf_df)
    n_clean_leaves = int(leaf_df["cell_clean"].sum())
    pct_clean = 100.0 * n_clean_leaves / n_leaves
    n_orig_clean = int(parent_clean["cell_clean"].sum())
    n_orig = len(parent_clean)
    pct_orig_clean_postdecomp = 100.0 * n_clean_leaves / n_orig

    print(f"\n=== STEP 4 FINAL TALLY ===")
    print(f"  pre-decomp clean:        {n_orig_clean}/{n_orig} = {100.0*n_orig_clean/n_orig:.1f}%")
    print(f"  post-decomp clean leaves: {n_clean_leaves}/{n_leaves} = {pct_clean:.1f}% of {n_leaves} leaves")
    print(f"  recovered / original:     {n_clean_leaves}/{n_orig} = {pct_orig_clean_postdecomp:.1f}%")

    print(f"\nleaves by region x clean:")
    print(leaf_df.groupby(["region","cell_clean"]).size().unstack(fill_value=0).to_string())
    print(f"\nleaves by observable x clean:")
    print(leaf_df.groupby(["observable","cell_clean"]).size().unstack(fill_value=0).to_string())
    print(f"\nleaves by decomp_path x clean:")
    print(leaf_df.groupby(["decomp_path","cell_clean"]).size().unstack(fill_value=0).to_string())

    # --- falsifier accounting ---
    F1_threshold = 0.80   # of original 84 cells
    F2_threshold = 0.50   # of original 84 cells
    F3_threshold = 0.30   # of leaves -- regime vs response disagreement

    F1_fires = (n_orig_clean / n_orig) >= F1_threshold
    F2_fires = (n_clean_leaves / n_orig) < F2_threshold

    # F3: regime vs response disagreement on clean leaves
    # rule: Gradient-tracking leaves must have β_g sign matching env_PC1 sign;
    #       Stationary leaves should have weak β_g (per spec — no observable response);
    #       C/D/F/Insufficient_T: no specific direction expected.
    disagreement = 0
    leaf_eval = []
    for _, l in leaf_df.iterrows():
        j = l["observable"]
        beta_g_sign = int(resp.loc[j, "beta_g_sign"])
        beta_g_p = float(resp.loc[j, "beta_g_p"])
        pop = l["population"]
        env_pc1 = float(env[env["population"]==pop]["env_PC1"].iloc[0])
        agree = True
        if l["regime"] == "Gradient-tracking":
            agree = (beta_g_sign == int(np.sign(env_pc1)))
        elif l["regime"] == "Stationary":
            agree = (beta_g_p > 0.05)   # no significant β_g
        # else: no direction expectation
        if not agree:
            disagreement += 1
        leaf_eval.append({"leaf_id": l["leaf_id"], "regime": l["regime"],
                          "observable": j, "agree": agree})
    pct_disagree = 100.0 * disagreement / n_leaves
    F3_fires = (disagreement / n_leaves) >= F3_threshold

    print(f"\n=== FALSIFIER REPORT ===")
    print(f"  F1 (substrate doesn't need RMD): "
          f"{n_orig_clean}/{n_orig} = {100.0*n_orig_clean/n_orig:.1f}%  "
          f"-- {'FIRES' if F1_fires else 'silent'} (threshold ≥ 80%)")
    print(f"  F2 (decomposition-resistant): "
          f"{n_clean_leaves}/{n_orig} clean post-decomp = {pct_orig_clean_postdecomp:.1f}%  "
          f"-- {'FIRES' if F2_fires else 'silent'} (threshold < 50%)")
    print(f"  F3 (regime vs response disagreement): "
          f"{disagreement}/{n_leaves} leaves = {pct_disagree:.1f}%  "
          f"-- {'FIRES' if F3_fires else 'silent'} (threshold ≥ 30%)")
    print(f"  F4 (holdout instability): NOT YET COMPUTED -- requires Step 4 v1.0 §3.7 protocol")

    fals = pd.DataFrame([
        {"falsifier": "F1", "value": n_orig_clean/n_orig,
         "threshold_op": ">=", "threshold": 0.80, "fires": F1_fires},
        {"falsifier": "F2", "value": n_clean_leaves/n_orig,
         "threshold_op": "<",  "threshold": 0.50, "fires": F2_fires},
        {"falsifier": "F3", "value": disagreement/n_leaves,
         "threshold_op": ">=", "threshold": 0.30, "fires": F3_fires},
    ])
    fals.to_parquet(FALSIFIER_PARQUET, index=False)

    # --- log ---
    sha_t = sha256_file(TREE_PARQUET)
    sha_l = sha256_file(LEAVES_PARQUET)
    sha_f = sha256_file(FALSIFIER_PARQUET)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log = PREREG / "step4_log.txt"
    log.write_text(
        f"# RMD-SRC Gymnadenia Step 4 -- decomposition + F1/F2/F3 falsifiers\n"
        f"# Generated: {ts}\n"
        f"# Per PRE_REG v1.0 §1.4 + §3.5 + v1.3 cleanness gates\n\n"
        f"decomp_tree.parquet sha            = {sha_t}\n"
        f"step4_leaves.parquet sha           = {sha_l}\n"
        f"step4_falsifier_report.parquet sha = {sha_f}\n\n"
        f"decomp attempts logged              = {len(tree)}\n"
        f"final leaves                        = {n_leaves}\n"
        f"clean leaves                        = {n_clean_leaves}\n"
        f"original cells                      = {n_orig}\n"
        f"post-decomp clean / original        = {n_clean_leaves}/{n_orig} ({pct_orig_clean_postdecomp:.2f}%)\n\n"
        f"F1 fires (>= 80% original clean): {F1_fires}\n"
        f"F2 fires (< 50% original clean post-decomp): {F2_fires}\n"
        f"F3 fires (>= 30% leaves disagree): {F3_fires}\n",
        encoding="utf-8",
    )
    print(f"\nWrote {log}")


if __name__ == "__main__":
    main()
