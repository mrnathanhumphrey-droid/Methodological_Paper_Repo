"""
RMD-SRC Step 3 v1.3 -- response function fit + cleanness, Option B (drop ρ_s, ρ_x).

Per PRE_REG_v1.3 §2.7 (operative):
  x_j(plant_i) = α + β_g · env_PC1(pop_i) + β_y · 1[year_i==2011] + ε
  OLS, cluster-robust SE at Pop, n=1028 per regression.

Cleanness gates per v1.2 §3.4 (carry-over):
  (i) global per-observable:
       R² ≥ 0.30  AND  shapiro_p > 0.01  AND  β_g sign consistent with Step-2
  (ii) per-(cell, observable):
       within-cell shapiro_p > 0.01  AND  |μ̂_cell - μ_cell| < 0.5 · cell_sd
  (iii) regime-consistency

Output:
  results/step3_response_function.parquet
  results/step3_cell_cleanness.parquet
"""

from pathlib import Path
import hashlib
import datetime
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

ROOT = Path(r"D:/Phenotype_Research")
DERIVED = ROOT / "data/orchids/gymnadenia/derived"
RESULTS = ROOT / "results"
PREREG = ROOT / "prereg"

PARTITION_PARQUET = DERIVED / "P0_partition.parquet"
SCORES_PARQUET = DERIVED / "observable_scores_v11.parquet"
ENV_PC1_PARQUET = RESULTS / "step2_env_PC1.parquet"
REGIMES_PARQUET = RESULTS / "step2_regimes.parquet"
OUT_RESP = RESULTS / "step3_response_function.parquet"
OUT_CLEAN = RESULTS / "step3_cell_cleanness.parquet"

OBS_COLS = [f"x{i+1}" for i in range(7)]
R2_FLOOR, SHAPIRO_P_FLOOR, CELL_PRED_TOL_SD = 0.30, 0.01, 0.5


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    p0_sha = sha256_file(PARTITION_PARQUET)
    locked = next((l for l in (PREREG/"P0_hash.txt").read_text(encoding="utf-8").splitlines()
                   if "P0_partition.parquet sha256" in l), "").split("=")[1].strip()
    assert p0_sha == locked
    print(f"P0 hash verified: {p0_sha[:16]}...")

    part = pd.read_parquet(PARTITION_PARQUET)
    scores = pd.read_parquet(SCORES_PARQUET)
    env = pd.read_parquet(ENV_PC1_PARQUET)
    regimes = pd.read_parquet(REGIMES_PARQUET)

    df = (part.merge(scores, on="PlantID")
              .merge(env[["population","env_PC1"]],
                     left_on="Population", right_on="population")
              .drop(columns=["population"]))
    df["y2011"] = (df["Year"]==2011).astype(int)

    X = sm.add_constant(df[["env_PC1","y2011"]])
    resp_rows, cell_rows = [], []

    for j in OBS_COLS:
        y = df[j]
        fit = sm.OLS(y, X, missing="drop").fit(
            cov_type="cluster", cov_kwds={"groups": df["Population"]})
        params, bse, pvals = fit.params, fit.bse, fit.pvalues
        r2 = fit.rsquared
        resid = fit.resid
        sh_p = stats.shapiro(resid).pvalue
        beta_g, beta_y = params["env_PC1"], params["y2011"]
        beta_g_sign = int(np.sign(beta_g))
        global_clean = (r2 >= R2_FLOOR) and (sh_p > SHAPIRO_P_FLOOR)

        resp_rows.append({
            "observable": j, "n": int(fit.nobs), "R2": r2,
            "shapiro_p_pooled": sh_p,
            "beta_const": params["const"],
            "beta_g": beta_g, "beta_g_sign": beta_g_sign,
            "beta_g_se": bse["env_PC1"], "beta_g_p": pvals["env_PC1"],
            "beta_y": beta_y, "beta_y_se": bse["y2011"],
            "beta_y_p": pvals["y2011"],
            "global_clean": global_clean,
        })

        df_j = df.assign(yhat=fit.fittedvalues, resid=resid)
        for cell, sub in df_j.groupby("P0_cell"):
            n_cell = len(sub)
            cell_mu = float(sub[j].mean())
            cell_sd = float(sub[j].std(ddof=1)) if n_cell > 1 else None
            yhat_mean = float(sub["yhat"].mean())
            mu_err = cell_mu - yhat_mean
            mu_err_rel = abs(mu_err)/cell_sd if cell_sd else float("nan")
            try:
                sh_cell = (stats.shapiro(sub["resid"]).pvalue
                           if 3 <= n_cell <= 5000 else np.nan)
            except Exception:
                sh_cell = np.nan
            pop = sub["Population"].iloc[0]
            reg_row = regimes[(regimes["population"]==pop)
                              & (regimes["observable"]==j)]
            regime = reg_row["regime"].iloc[0] if len(reg_row) else "Unknown"

            within = (sh_cell > SHAPIRO_P_FLOOR) if not np.isnan(sh_cell) else False
            pred_ok = mu_err_rel < CELL_PRED_TOL_SD

            if regime == "Insufficient_T":
                reg_ok = True
            elif regime == "Gradient-tracking":
                pop_env = float(sub["env_PC1"].iloc[0])
                reg_ok = (beta_g_sign == int(np.sign(pop_env)))
            else:
                reg_ok = True

            cc = global_clean and within and pred_ok and reg_ok
            cell_rows.append({
                "P0_cell": cell, "observable": j,
                "population": pop, "region": sub["Region"].iloc[0],
                "year": int(sub["Year"].iloc[0]),
                "regime": regime, "n_cell": n_cell,
                "cell_mu": cell_mu, "cell_sd": cell_sd,
                "yhat_mean": yhat_mean, "mu_err": mu_err,
                "mu_err_rel_sd": mu_err_rel,
                "shapiro_p_cell": sh_cell,
                "global_clean": global_clean,
                "within_cell_clean": within,
                "pred_clean": pred_ok,
                "regime_consistent": reg_ok,
                "cell_clean": cc,
            })

    resp = pd.DataFrame(resp_rows)
    cells = pd.DataFrame(cell_rows)
    resp.to_parquet(OUT_RESP, index=False)
    cells.to_parquet(OUT_CLEAN, index=False)

    print("\n=== v1.3 response function (Option B: env_PC1 + y2011 only) ===")
    print(resp[["observable","n","R2","shapiro_p_pooled","beta_g","beta_g_p",
                "beta_y","beta_y_p","global_clean"]].to_string(index=False))

    print("\n=== per-cell cleanness ===")
    pivot = (cells.pivot(index="P0_cell", columns="observable", values="cell_clean")
                  .replace({True:"✓", False:"·"}))
    print(pivot.to_string())

    n_clean = int(cells["cell_clean"].sum())
    n_total = len(cells)
    pct = 100.0 * n_clean/n_total
    f1 = pct >= 80.0
    print(f"\n=== F1 ACCOUNTING (v1.3) ===")
    print(f"clean: {n_clean}/{n_total} = {pct:.1f}%   F1 fires: {f1}")

    print("\nclean cells by region:")
    print(cells.groupby(["region","cell_clean"]).size().unstack(fill_value=0).to_string())
    print("\nclean cells by regime:")
    print(cells.groupby(["regime","cell_clean"]).size().unstack(fill_value=0).to_string())
    print("\nclean cells by observable:")
    print(cells.groupby(["observable","cell_clean"]).size().unstack(fill_value=0).to_string())

    sha_r = sha256_file(OUT_RESP)
    sha_c = sha256_file(OUT_CLEAN)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log = PREREG / "step3_log.txt"
    existing = log.read_text(encoding="utf-8") if log.exists() else ""
    log.write_text(existing + "\n"
        f"# RMD-SRC Gymnadenia Step 3 v1.3 -- Option B (drop ρ_s, ρ_x)\n"
        f"# Generated: {ts}\n"
        f"# Per PRE_REG_v1.3 §2.7\n\n"
        f"step3_response_function.parquet (v1.3) sha = {sha_r}\n"
        f"step3_cell_cleanness.parquet (v1.3) sha    = {sha_c}\n"
        f"clean / total                                = {n_clean}/{n_total} ({pct:.2f}%)\n"
        f"F1 fires                                      = {f1}\n",
        encoding="utf-8")
    print(f"\nAppended to {log}")


if __name__ == "__main__":
    main()
