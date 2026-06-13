"""Step 3 diagnostic — query-only inspection of cleanness, multicollinearity,
and x2 structure. Writes no parquets / no logs.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

ROOT = Path(r"D:/Phenotype_Research")
D = ROOT / "data/orchids/gymnadenia/derived"
R = ROOT / "results"

part = pd.read_parquet(D / "P0_partition.parquet")
scores = pd.read_parquet(D / "observable_scores_v11.parquet")
W = pd.read_parquet(D / "observable_rotation_W_v11.parquet")
env = pd.read_parquet(R / "step2_env_PC1.parquet")
regimes = pd.read_parquet(R / "step2_regimes.parquet")
resp = pd.read_parquet(R / "step3_response_function.parquet")
cells = pd.read_parquet(R / "step3_cell_cleanness.parquet")
sp = pd.read_csv(D / "splot_species_neighborhood_50km.csv")
nbr = pd.read_csv(D / "splot_neighborhood_50km.csv")

# rebuild predictor table to recompute things
pop_code_to_name = {"D":"Doettingen","R":"Remigen","L":"Linn","RW":"Rossweid",
                    "S":"Schatzalp","M":"Muenstertal","A":"Albulapass","C":"Corviglia"}
pop_name_to_code = {v:k for k,v in pop_code_to_name.items()}
n_plots_per_pop = nbr.groupby("pop_name")["PlotObservationID"].nunique()
gym = sp[sp["Species"]=="Gymnadenia odoratissima"].groupby("pop_code")["n_plots"].sum()
rho_s = {p: int(gym.get(pop_name_to_code[p],0))/n for p,n in n_plots_per_pop.items()}
pic = sp[sp["Species"]=="Picea abies"].set_index("pop_code")["mean_rel_cover"]
rho_x = {pop_code_to_name[k]: float(v) for k,v in pic.items()}
env["rho_s"] = env["population"].map(rho_s)
env["rho_x"] = env["population"].map(rho_x)

df = (part.merge(scores, on="PlantID")
          .merge(env[["population","env_PC1","rho_s","rho_x"]],
                 left_on="Population", right_on="population"))
df["y2011"] = (df["Year"]==2011).astype(int)


# ============================================================
print("=== A. POP-LEVEL PREDICTOR TABLE ===")
pred_pop = (df.groupby("Population")[["env_PC1","rho_s","rho_x"]]
              .first().sort_values("env_PC1"))
print(pred_pop.round(4).to_string())

print("\n=== B. POP-LEVEL CORRELATIONS (n=8 pops) ===")
print(pred_pop.corr().round(3).to_string())

print("\n=== C. PLANT-LEVEL CORRELATIONS (n=1028; predictors are pop-constant) ===")
plant_pred = df[["env_PC1","rho_s","rho_x","y2011"]]
print(plant_pred.corr().round(3).to_string())

print("\n=== D. VIF (plant-level) ===")
def vif(X):
    out = {}
    for c in X.columns:
        y = X[c]
        Xother = sm.add_constant(X.drop(columns=[c]))
        r2 = sm.OLS(y, Xother).fit().rsquared
        out[c] = 1.0/(1.0-r2) if r2 < 0.9999 else float('inf')
    return out
for c,v in vif(plant_pred).items():
    print(f"  {c:8s}  VIF = {v:.2f}")


# ============================================================
print("\n=== E. x2 ROTATION LOADINGS (top 10 by |W|) ===")
w2 = W["x2"].sort_values(key=lambda s: s.abs(), ascending=False).head(10)
print(w2.round(3).to_string())
print("\n--- bottom 5 ---")
w2_b = W["x2"].sort_values(key=lambda s: s.abs(), ascending=True).head(5)
print(w2_b.round(3).to_string())


# ============================================================
print("\n=== F. RE-FIT x2 DROPPING DENSITY TERMS (β_g sign flip check) ===")
def fitone(y, X, groups):
    X_ = sm.add_constant(X)
    f = sm.OLS(y, X_, missing="drop").fit(cov_type="cluster",
                                          cov_kwds={"groups": groups})
    return f
configs = [
    ("env_PC1 + rho_s + rho_x + y2011 (v1.2 §3.4)", ["env_PC1","rho_s","rho_x","y2011"]),
    ("env_PC1 + y2011 (drop densities)",            ["env_PC1","y2011"]),
    ("env_PC1 alone",                                ["env_PC1"]),
    ("rho_s + y2011",                                ["rho_s","y2011"]),
    ("rho_x + y2011",                                ["rho_x","y2011"]),
]
for label, cols in configs:
    f = fitone(df["x2"], df[cols], df["Population"])
    bg = f.params.get("env_PC1", float('nan'))
    bs = f.params.get("rho_s", float('nan'))
    bx = f.params.get("rho_x", float('nan'))
    print(f"  {label:50s}  R²={f.rsquared:.3f}  "
          f"β_env={bg:+.3f}  β_s={bs:+.3f}  β_x={bx:+.3f}  shapiro={stats.shapiro(f.resid).pvalue:.3e}")


# ============================================================
print("\n=== G. THE 5 CLEAN CELLS (all x2) ===")
clean5 = cells[cells["cell_clean"]].copy()
print(clean5[["P0_cell","population","region","year","regime","n_cell",
              "cell_mu","cell_sd","yhat_mean","mu_err","mu_err_rel_sd",
              "shapiro_p_cell"]].round(3).to_string(index=False))

print("\n=== H. x2 CELL-LEVEL GATE BREAKDOWN (which gate kills each cell) ===")
c2 = cells[cells["observable"]=="x2"].copy()
c2["fail_reasons"] = c2.apply(lambda r:
    "/".join(g for g,ok in [
        ("global", r["global_clean"]),
        ("within", r["within_cell_clean"]),
        ("pred",   r["pred_clean"]),
        ("regime", r["regime_consistent"]),
    ] if not ok) or "clean",
    axis=1)
print(c2[["P0_cell","regime","n_cell","cell_mu","yhat_mean","mu_err_rel_sd",
          "shapiro_p_cell","fail_reasons"]].round(3).to_string(index=False))


# ============================================================
print("\n=== I. WHY EACH OBSERVABLE FAILS GLOBALLY (R² + shapiro_p + which gate) ===")
# For each observable, count how many cells fail each gate
gate_cols = ["global_clean","within_cell_clean","pred_clean","regime_consistent"]
diag = (cells.groupby("observable")
              [gate_cols].apply(lambda d: (d == False).sum()))
# add R² + shapiro
m = resp.set_index("observable")[["R2","shapiro_p_pooled","global_clean"]]
diag = diag.join(m).round(3)
print(diag.to_string())

print("\n=== J. PER-OBS CELL STATS: within-cell Shapiro fail rate + median pred error ===")
agg = (cells.groupby("observable")
              .agg(median_pred_err_sd=("mu_err_rel_sd","median"),
                   median_within_shapiro=("shapiro_p_cell","median"),
                   pct_within_shapiro_fail=("within_cell_clean",
                                            lambda s: 100.0*(~s).mean()),
                   pct_pred_fail=("pred_clean",
                                  lambda s: 100.0*(~s).mean())))
print(agg.round(3).to_string())


# ============================================================
print("\n=== K. STEP 1 POOLED REGION MEANS vs STEP 3 PREDICTED REGION MEANS for x2 ===")
df2 = df.assign(yhat_x2=sm.OLS(df["x2"], sm.add_constant(df[["env_PC1","rho_s","rho_x","y2011"]])).fit().fittedvalues)
print(df2.groupby("Region")[["x2","yhat_x2"]].mean().round(3).to_string())
print()
print("=== L. STEP 1 POOLED POP MEANS for x2 ===")
print(df.groupby("Population")["x2"].agg(["mean","std","count"]).round(3).to_string())
