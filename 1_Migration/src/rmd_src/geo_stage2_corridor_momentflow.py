"""
Geographic arm — Stage 2: corridor RMD-SRC moment-flow (PRE_REG v1.6, observable A).

Per between-corridor (i!=j), species-decomposed gravity-residual:
  E_ij(t)   = gravity-expected flow (gravity refit per year on between-unit flows)
  p_s(t)    = national share of species s among movers in year t
  r_ij,s(t) = log((O_ij,s(t)+eps)/(E_ij(t)*p_s(t)+eps))
  mu_ij(t)  = mean over species ; var_ij(t) = variance over species
Then classify each corridor's (mu,var) trajectory over training years (2012-2017)
via the v1.4 Step-2 rule (Stationary/Concentrating/Diffusing/Fragmenting;
gradient-tracking N/A for corridors).

Outputs: results/geo_corridor_trajectories.parquet, results/geo_corridor_regimes.parquet
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).parent))
from geo_stage1_cube_gravity import DIVISION, unit_mass_centroid, haversine

DERIVED = Path(r"D:\Migration\data\derived")
RESULTS = Path(r"D:\Migration\results")
WINDOW = list(range(2012, 2022))
TRAIN = list(range(2012, 2018))
EPS = 1.0
MIN_SPECIES = 10


def gravity_expected_by_year(cube, mass):
    """Refit gravity per year on between-unit O-D totals; return dict (i,j,year)->E."""
    m = mass.set_index("unit")
    E = {}
    for yr, cy in cube.groupby("year"):
        od = cy.groupby(["orig", "dest"]).flow.sum().reset_index()
        od = od[od.orig != od.dest].copy()
        od = od.join(m[["mass", "lon", "lat"]].rename(columns=lambda c: f"o_{c}"), on="orig")
        od = od.join(m[["mass", "lon", "lat"]].rename(columns=lambda c: f"d_{c}"), on="dest")
        od = od.dropna(subset=["o_mass", "d_mass"])
        od["dist"] = haversine(od.o_lon, od.o_lat, od.d_lon, od.d_lat).clip(lower=1)
        X = sm.add_constant(np.column_stack([np.log(od.o_mass), np.log(od.d_mass), np.log(od.dist)]))
        fit = sm.GLM(od.flow, X, family=sm.families.Poisson()).fit()
        od["E"] = fit.predict(X)
        for r in od.itertuples():
            E[(r.orig, r.dest, int(yr))] = float(r.E)
    return E


def classify(r_mu, r_var):
    if r_var < -0.05:
        return "Concentrating"
    if r_var > 0.05:
        return "Diffusing"
    if abs(r_mu) < 0.02:
        return "Stationary"
    return "Fragmenting"


def run(level):
    cube = pd.read_parquet(DERIVED / f"geo_cube_{level}s.parquet")
    mass = unit_mass_centroid(level)
    E = gravity_expected_by_year(cube, mass)
    # national species share per year
    tot_y = cube.groupby("year").flow.sum()
    ps = cube.groupby(["species", "year"]).flow.sum() / tot_y
    ps = ps.to_dict()

    rows = []
    btw = cube[cube.orig != cube.dest]
    for (i, j), g in btw.groupby(["orig", "dest"]):
        for t in WINDOW:
            e = E.get((i, j, t))
            if e is None or e <= 0:
                continue
            gy = g[g.year == t]
            if len(gy) < MIN_SPECIES:
                continue
            r = np.log((gy.flow.to_numpy() + EPS) /
                       (e * np.array([ps.get((s, t), np.nan) for s in gy.species]) + EPS))
            r = r[np.isfinite(r)]
            if len(r) < MIN_SPECIES:
                continue
            rows.append((i, j, t, float(np.mean(r)), float(np.var(r)), len(r)))
    traj = pd.DataFrame(rows, columns=["orig", "dest", "year", "mu", "var", "n_species"])
    traj.to_parquet(RESULTS / f"geo_corridor_trajectories_{level}.parquet", index=False)

    # classify corridors with full TRAIN coverage
    out = []
    for (i, j), g in traj.groupby(["orig", "dest"]):
        gt = g[g.year.isin(TRAIN)].sort_values("year")
        if gt.year.nunique() < len(TRAIN):
            continue
        yrs = gt.year.to_numpy(float)
        mu_dot = float(np.polyfit(yrs, gt.mu, 1)[0]); mu_bar = gt.mu.mean()
        var_dot = float(np.polyfit(yrs, gt["var"], 1)[0]); var_bar = gt["var"].mean()
        r_mu = mu_dot / mu_bar if abs(mu_bar) > 1e-9 else np.inf
        r_var = var_dot / var_bar if abs(var_bar) > 1e-9 else np.inf
        out.append((i, j, mu_bar, var_bar, r_mu, r_var, classify(r_mu, r_var)))
    reg = pd.DataFrame(out, columns=["orig", "dest", "mu_bar", "var_bar",
                                     "r_mu", "r_var", "regime"])
    reg.to_parquet(RESULTS / f"geo_corridor_regimes_{level}.parquet", index=False)
    return traj, reg


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    for level in ["division", "state"]:
        traj, reg = run(level)
        print(f"\n=== {level.upper()} corridors (between-unit, gravity-residual moment-flow) ===")
        print(f"corridor-years with >= {MIN_SPECIES} species: {len(traj):,}")
        print(f"corridors with full 2012-2017 trajectory (classified): {len(reg)}")
        if len(reg):
            print("regime distribution:")
            print(reg.regime.value_counts().to_string())
            print(f"mean over/under-gravity (mu_bar): {reg.mu_bar.mean():+.3f}  "
                  f"(>0 = beats gravity); species-selectivity (var_bar) median {reg.var_bar.median():.3f}")
            top = reg.reindex(reg.mu_bar.abs().sort_values(ascending=False).index).head(5)
            print("most extreme corridors by |mu_bar|:")
            print(top[["orig", "dest", "mu_bar", "var_bar", "regime"]].to_string(index=False))
    print(f"\nwritten: results/geo_corridor_{{trajectories,regimes}}_*.parquet")


if __name__ == "__main__":
    main()
