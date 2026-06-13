"""
RMD-SRC Step 2 -- trajectory regime classification per (Pop, observable).

Per locked PRE_REG_v1.0_RMD_SRC_gymnadenia.md §3.3 (T=2 rules):
  Stationary       |Δμ/μ̄| < 0.05 AND |Δσ²/σ̄²| < 0.10
  Gradient-track   sign(Δμ) == sign(env_PC1 of pop) AND |Δμ/μ̄| > 0.05
  Concentrating    Δσ²/σ̄² < -0.15
  Diffusing        Δσ²/σ̄² > +0.15
  Fragmenting      Hartigan dip p < 0.05  OR  none of above

Interpretation note: the locked K=12 partition encodes Year inside the cell ID
(each P0_cell is one year). "Trajectory across t within cell" reads as
"trajectory at the (Region, Pop) projection of P0_cell". Pop is the trajectory
unit; Year is the t-bin. 5 of 8 pops span both years; 3 single-year pops
(Rossweid, Albulapass, Corviglia) get regime "Insufficient_T" per §3.7 fallback.

§2.6 env_PC1: PCA on the 8-pop x 10-covariate matrix, frozen, sign-corrected
so that high PC1 == mountain.

Output:
  results/step2_regimes.parquet
  results/step2_env_PC1.parquet      (the locked env rotation + scores)
"""

from pathlib import Path
import hashlib
import datetime
import numpy as np
import pandas as pd
from scipy import stats
import diptest

ROOT = Path(r"D:/Phenotype_Research")
RAW = ROOT / "data/orchids/gymnadenia/raw"
DERIVED = ROOT / "data/orchids/gymnadenia/derived"
RESULTS = ROOT / "results"
PREREG = ROOT / "prereg"

ENV_CSV = DERIVED / "gymnadenia_pop_env_v2.csv"
PARTITION_PARQUET = DERIVED / "P0_partition.parquet"
SCORES_PARQUET = DERIVED / "observable_scores_v11.parquet"
MOMENTS_PARQUET = RESULTS / "moment_trajectories.parquet"
ENV_PC1_PARQUET = RESULTS / "step2_env_PC1.parquet"
OUT_REGIMES = RESULTS / "step2_regimes.parquet"

ENV_COVARIATES = [
    "bio_1", "bio_6", "bio_12", "bio_15",
    "phh2o_0-5cm", "clay_0-5cm", "sand_0-5cm", "soc_0-5cm",
    "elev_wc5m", "altitude_paper_m",
]
OBS_COLS = [f"x{i+1}" for i in range(7)]

# §3.3 cutoffs
STAT_MU_REL = 0.05
STAT_VAR_REL = 0.10
GRAD_MU_REL = 0.05
CONC_VAR_REL = -0.15
DIFF_VAR_REL = 0.15
FRAG_DIP_P = 0.05


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def env_pc1():
    """Lock env-PC1 per §2.6: PCA on 8-pop x 10-covariate matrix, frozen,
    sign so high PC1 = mountain."""
    env = pd.read_csv(ENV_CSV)
    M = env[ENV_COVARIATES].apply(pd.to_numeric, errors="coerce")
    if M.isna().any().any():
        # Rossweid 5 of 6 0-5cm soil NA -- fall back to 5-15cm for missing
        # but per §2.6 we use 0-5cm specifically. Use column-mean imputation,
        # log it.
        n_na = M.isna().sum().sum()
        print(f"WARN: env covariate NA count {n_na}; column-mean imputed")
        M = M.fillna(M.mean())
    col_mean, col_sd = M.mean(0), M.std(0, ddof=1)
    Z = ((M - col_mean) / col_sd).to_numpy()
    U, S, Vt = np.linalg.svd(Z, full_matrices=False)
    scores = U[:, 0] * S[0]
    loadings = Vt[0]
    # Sign-correct: high PC1 should be mountain. Anchor: mountain populations
    # have higher elev. If loading on elev_wc5m is positive, sign is correct.
    elev_idx = ENV_COVARIATES.index("elev_wc5m")
    if loadings[elev_idx] < 0:
        scores = -scores
        loadings = -loadings
    out = env[["region", "population", "code"]].copy()
    out["env_PC1"] = scores
    var_expl = (S[0] ** 2) / (S ** 2).sum()
    print(f"env_PC1 explains {var_expl*100:.1f}% of env variance")
    print(out.to_string(index=False))
    out.to_parquet(ENV_PC1_PARQUET, index=False)
    print(f"  wrote {ENV_PC1_PARQUET}")
    return out


def per_pop_year_moments():
    """Compute μ, σ² per (Pop, Year, observable) from per-plant scores -- this
    bypasses the K=12 cell collapse so Schatzalp 2010 is its own pop-year
    rather than merged into Muenstertal 2010 (the merge only matters for
    Step-5 min-cell-size and Step-3 cell-cleanness checks)."""
    part = pd.read_parquet(PARTITION_PARQUET)
    scores = pd.read_parquet(SCORES_PARQUET)
    df = part.merge(scores, on="PlantID", how="inner",
                    validate="one_to_one")
    rows = []
    for (region, pop, year), sub in df.groupby(["Region", "Population", "Year"]):
        for j in OBS_COLS:
            x = sub[j].dropna()
            n = len(x)
            rows.append({
                "region": region, "population": pop, "year": int(year),
                "observable": j,
                "n": n,
                "mu":  float(x.mean()) if n else None,
                "var": float(x.var(ddof=1)) if n > 1 else None,
            })
    return pd.DataFrame(rows), df


def classify(d_mu_rel, d_var_rel, dip_p, grad_sign_ok, grad_mag_ok):
    """Apply §3.3 T=2 rule. Returns regime label."""
    if dip_p < FRAG_DIP_P:
        return "Fragmenting"
    if d_var_rel < CONC_VAR_REL:
        return "Concentrating"
    if d_var_rel > DIFF_VAR_REL:
        return "Diffusing"
    if grad_sign_ok and grad_mag_ok:
        return "Gradient-tracking"
    if abs(d_mu_rel) < STAT_MU_REL and abs(d_var_rel) < STAT_VAR_REL:
        return "Stationary"
    return "Fragmenting"  # "none of above" fallback per spec


def main():
    # --- prereqs ---
    p0_sha = sha256_file(PARTITION_PARQUET)
    locked = next(
        (l for l in (PREREG / "P0_hash.txt").read_text(encoding="utf-8").splitlines()
         if "P0_partition.parquet sha256" in l), "").split("=")[1].strip()
    assert p0_sha == locked, "P0 hash mismatch"
    print(f"P0 hash verified: {p0_sha[:16]}...\n")

    # --- env-PC1 ---
    print("=== §2.6 env-PC1 freeze ===")
    env_pc = env_pc1()
    env_pc1_by_pop = dict(zip(env_pc["population"], env_pc["env_PC1"]))

    # --- per-(pop, year, observable) moments ---
    print("\n=== per-(pop, year, observable) moments ===")
    py_moments, plant_df = per_pop_year_moments()

    # --- classify per (Pop, observable) ---
    print("\n=== regime classification (T=2 per §3.3) ===\n")
    rows = []
    pops_all = sorted(py_moments["population"].unique())
    for pop in pops_all:
        sub = py_moments[py_moments["population"] == pop]
        years = sorted(sub["year"].unique())
        region = sub["region"].iloc[0]
        env_p = env_pc1_by_pop[pop]
        env_sign = 1 if env_p > 0 else -1

        for j in OBS_COLS:
            row = {"population": pop, "region": region, "observable": j,
                   "n_years": len(years), "env_PC1": env_p}
            if len(years) < 2:
                row.update({"regime": "Insufficient_T",
                            "d_mu": None, "d_mu_rel": None,
                            "d_var": None, "d_var_rel": None,
                            "dip_p": None,
                            "mu_2010": None, "mu_2011": None,
                            "var_2010": None, "var_2011": None,
                            "n_2010": 0, "n_2011": 0,
                            "rule_path": "single_year_pop"})
                if 2010 in years:
                    r = sub[(sub["year"] == 2010) & (sub["observable"] == j)].iloc[0]
                    row["mu_2010"], row["var_2010"], row["n_2010"] = r["mu"], r["var"], int(r["n"])
                if 2011 in years:
                    r = sub[(sub["year"] == 2011) & (sub["observable"] == j)].iloc[0]
                    row["mu_2011"], row["var_2011"], row["n_2011"] = r["mu"], r["var"], int(r["n"])
                rows.append(row)
                continue

            r10 = sub[(sub["year"] == 2010) & (sub["observable"] == j)].iloc[0]
            r11 = sub[(sub["year"] == 2011) & (sub["observable"] == j)].iloc[0]
            mu_bar = (r10["mu"] + r11["mu"]) / 2
            var_bar = (r10["var"] + r11["var"]) / 2
            d_mu = r11["mu"] - r10["mu"]
            d_var = r11["var"] - r10["var"]
            d_mu_rel = d_mu / mu_bar if abs(mu_bar) > 1e-9 else float("nan")
            d_var_rel = d_var / var_bar if abs(var_bar) > 1e-9 else float("nan")

            grad_sign_ok = (np.sign(d_mu) == env_sign)
            grad_mag_ok = abs(d_mu_rel) > GRAD_MU_REL if not np.isnan(d_mu_rel) else False

            # dip test on pooled within-pop plant scores
            pop_plants = plant_df[plant_df["Population"] == pop][j].dropna()
            try:
                dip_stat, dip_p = diptest.diptest(pop_plants.to_numpy())
            except Exception:
                dip_p = 1.0

            regime = classify(d_mu_rel, d_var_rel, dip_p,
                              grad_sign_ok, grad_mag_ok)
            row.update({
                "regime": regime,
                "d_mu": d_mu, "d_mu_rel": d_mu_rel,
                "d_var": d_var, "d_var_rel": d_var_rel,
                "dip_p": dip_p,
                "mu_2010": r10["mu"], "mu_2011": r11["mu"],
                "var_2010": r10["var"], "var_2011": r11["var"],
                "n_2010": int(r10["n"]), "n_2011": int(r11["n"]),
                "rule_path": "T2_delta",
            })
            rows.append(row)

    regimes = pd.DataFrame(rows)
    regimes.to_parquet(OUT_REGIMES, index=False)
    print(f"Wrote {OUT_REGIMES}  ({len(regimes)} rows)\n")

    # --- summary ---
    print("=== regime counts ===")
    counts = regimes.groupby(["region", "regime"]).size().unstack(fill_value=0)
    print(counts.to_string())
    print(f"\ntotal cells classified: {len(regimes)}")
    print(f"  trajectory-classifiable (both years): "
          f"{(regimes['regime'] != 'Insufficient_T').sum()}")
    print(f"  Insufficient_T (single year): "
          f"{(regimes['regime'] == 'Insufficient_T').sum()}")

    print("\n=== regime per (pop, observable) ===")
    pivot = regimes.pivot(index="population", columns="observable",
                          values="regime")
    print(pivot.to_string())

    # --- hash log ---
    sha = sha256_file(OUT_REGIMES)
    sha_e = sha256_file(ENV_PC1_PARQUET)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log_lines = [
        "", "# RMD-SRC Gymnadenia Step 2 -- regime classification",
        f"# Generated: {ts}",
        f"# Per PRE_REG_v1.0 §3.3 T=2 rules, K=12 partition, v1.1 observables",
        "",
        f"step2_regimes.parquet sha256        = {sha}",
        f"step2_env_PC1.parquet sha256        = {sha_e}",
        f"rows                                 = {len(regimes)}",
        f"trajectory-classifiable rows         = {(regimes['regime'] != 'Insufficient_T').sum()}",
        f"Insufficient_T rows                  = {(regimes['regime'] == 'Insufficient_T').sum()}",
    ]
    log_path = PREREG / "step2_log.txt"
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"\nWrote {log_path}")


if __name__ == "__main__":
    main()
