"""
v2.0 GEO_F4 re-slice — six-arm package fire.

Locked-by-commit at PRE_REG v2.0 (file `prereg/PRE_REG_v2.0_GEO_F4_reslice.md`).
All bars and falsifiers fixed in the pre-reg; this script reads them as given.

Outputs: results/v2_geo_f4_reslice/{arm_a, arm_b, arm_c, arm_d, arm_e, arm_f, verdict}.json
"""
from __future__ import annotations
import json
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
import tensorly as tl
from tensorly.decomposition import parafac
from pathlib import Path
from scipy.stats import pearsonr
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, str(Path(__file__).parent))

DERIVED = Path(r"D:\Migration\data\derived")
RESULTS = Path(r"D:\Migration\results")
OUT = RESULTS / "v2_geo_f4_reslice"
OUT.mkdir(parents=True, exist_ok=True)

# Locked window definitions (from v1.0 prereg + v2.0 ARM D)
TRAIN = list(range(2012, 2018))           # 2012..2017
HOLDOUT_FULL = list(range(2018, 2022))    # 2018..2021
HOLDOUT_PRE_COVID = [2018, 2019]
MIN_PTS_FULL = 4
MIN_PTS_PRE_COVID = 2  # relaxed per v2.0 pre-reg ARM D

# Locked Step-2 classifier thresholds (do not change)
TH_MU = 0.02
TH_VAR = 0.05

# ARM C top-N (locked)
TOPN = {"state": 100, "division": 15}

# ARM F threshold scaling (diagnostic only)
TH_SCALES = [0.5, 1.0, 2.0]

# ARM E bootstrap draws (locked)
N_BOOT = 1000
RNG = np.random.default_rng(20260531)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fit_slope(years, vals):
    """OLS slope of vals on years; return (slope, slope_se). NaN if <2 pts."""
    if len(years) < 2 or len(vals) < 2:
        return np.nan, np.nan
    X = sm.add_constant(np.asarray(years, dtype=float))
    y = np.asarray(vals, dtype=float)
    fit = sm.OLS(y, X).fit()
    return float(fit.params[1]), float(fit.bse[1])


def classify_v1(r_mu, r_var, th_mu=TH_MU, th_var=TH_VAR):
    """Original Step-2 classifier (locked)."""
    if np.isnan(r_var) or np.isnan(r_mu):
        return "Undef"
    if r_var < -th_var:
        return "Concentrating"
    if r_var > th_var:
        return "Diffusing"
    if abs(r_mu) < th_mu:
        return "Stationary"
    return "Fragmenting"


def slope_sign_3way(slope, se, k=1.5):
    """3-way sign classification with SE band. Returns -1, 0, +1."""
    if np.isnan(slope) or np.isnan(se) or se == 0:
        return 0
    if slope > k * se:
        return 1
    if slope < -k * se:
        return -1
    return 0


def cells_3x3_adjacent(c1, c2):
    """Two 3x3 cells (each a tuple of -1/0/+1) are same or 1-cell-adjacent."""
    dx, dy = c1[0] - c2[0], c1[1] - c2[1]
    # same cell -> dx=dy=0; adjacent -> exactly one of |dx|, |dy| is 1, other 0
    return (abs(dx) + abs(dy)) <= 1


def per_corridor_period_slopes(traj_df, years):
    """Return df indexed by (orig, dest) with mu_dot, var_dot, mu_dot_se, var_dot_se, n_pts."""
    rows = []
    for (i, j), g in traj_df.groupby(["orig", "dest"]):
        gw = g[g["year"].isin(years)]
        if len(gw) < 2:
            continue
        rmu, smu = fit_slope(gw["year"].values, gw["mu"].values)
        rvar, svar = fit_slope(gw["year"].values, gw["var"].values)
        rows.append({
            "orig": i, "dest": j, "n_pts": len(gw),
            "mu_dot": rmu, "var_dot": rvar,
            "mu_dot_se": smu, "var_dot_se": svar,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# ARM A — continuous-coordinate transfer on raw corridors
# ---------------------------------------------------------------------------

def arm_a(traj_df, holdout_years, min_pts_holdout):
    train_s = per_corridor_period_slopes(traj_df, TRAIN)
    hold_s  = per_corridor_period_slopes(traj_df, holdout_years)
    train_s = train_s[train_s["n_pts"] >= MIN_PTS_FULL]
    hold_s  = hold_s[hold_s["n_pts"] >= min_pts_holdout]
    merged = train_s.merge(hold_s, on=["orig", "dest"], suffixes=("_train", "_hold"))
    if len(merged) < 5:
        return {"n": int(len(merged)), "result": "insufficient_n"}
    r_mu, p_mu = pearsonr(merged["mu_dot_train"], merged["mu_dot_hold"])
    r_var, p_var = pearsonr(merged["var_dot_train"], merged["var_dot_hold"])
    # Bonferroni at 2 tests: pass each at p < 0.025
    pass_mu  = (r_mu >= 0.40) and (p_mu < 0.025)
    pass_var = (r_var >= 0.40) and (p_var < 0.025)
    return {
        "n_corridors": int(len(merged)),
        "r_mu_dot": float(r_mu), "p_mu_dot": float(p_mu),
        "r_var_dot": float(r_var), "p_var_dot": float(p_var),
        "pass_mu": bool(pass_mu),
        "pass_var": bool(pass_var),
        "pass_both": bool(pass_mu and pass_var),
    }


# ---------------------------------------------------------------------------
# ARM B — latent-factor continuous coords (division only)
#
# Re-fit static PARAFAC on the training-window residual cube to recover
# full orig+dest+species loadings; then weight per-year corridor (mu, var)
# trajectories by the (orig, dest) factor loading product to get a per-factor
# annual (mu_k(t), var_k(t)) trajectory.
# ---------------------------------------------------------------------------

def _haversine(lon1, lat1, lon2, lat2):
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = p2 - p1
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp/2)**2 + np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2*R*np.arcsin(np.sqrt(a))


def _build_div_static_factors(rank=3):
    """Re-fit static PARAFAC on division cube, full window 2012-2017 residual.
    Returns (A, B, C, units, species) where A:(9,r) orig, B:(9,r) dest, C:(38,r) species.
    """
    sys.path.insert(0, str(Path(__file__).parent))
    from geo_stage1_cube_gravity import DIVISION, unit_mass_centroid
    cube = pd.read_parquet(DERIVED / "geo_cube_divisions.parquet")
    cube = cube[cube["year"].isin(TRAIN)].copy()
    mass = unit_mass_centroid("division").set_index("unit")
    od = cube.groupby(["orig", "dest"]).flow.sum().reset_index()
    od = od[od.orig != od.dest].copy()
    od = od.join(mass[["mass","lon","lat"]].rename(columns=lambda c: f"o_{c}"), on="orig")
    od = od.join(mass[["mass","lon","lat"]].rename(columns=lambda c: f"d_{c}"), on="dest")
    od = od.dropna(subset=["o_mass","d_mass"])
    od["dist"] = _haversine(od.o_lon, od.o_lat, od.d_lon, od.d_lat).clip(lower=1)
    X = sm.add_constant(np.column_stack([np.log(od.o_mass), np.log(od.d_mass), np.log(od.dist)]))
    fit = sm.GLM(od.flow, X, family=sm.families.Poisson()).fit()
    od["E"] = fit.predict(X)
    E = {(r.orig, r.dest): r.E for r in od.itertuples()}
    tot = cube.flow.sum()
    p_s = (cube.groupby("species").flow.sum() / tot).to_dict()
    units = sorted(set(cube.orig) | set(cube.dest))
    species = sorted(cube.species.unique())
    ui = {u: k for k, u in enumerate(units)}
    si = {s: k for k, s in enumerate(species)}
    R = np.zeros((len(units), len(units), len(species)))
    O = cube.groupby(["orig","dest","species"]).flow.sum()
    for (i, j, s), o in O.items():
        if i == j:  continue
        e = E.get((i, j))
        if e is None: continue
        R[ui[i], ui[j], si[s]] = o - e * p_s.get(s, 0)
    R = np.nan_to_num(R)
    _, factors = parafac(tl.tensor(R), rank=rank, n_iter_max=500, random_state=0)
    A, B, C = factors  # (orig x r), (dest x r), (species x r)
    return np.asarray(A), np.asarray(B), np.asarray(C), units, species


def arm_b(traj_df, holdout_years, A, B, units):
    """Per latent factor k: weighted (mu, var) trajectory across years using
    w_ij,k = A[i,k] * B[j,k]. Then slope per period and 3x3-cell classification.
    """
    rank = A.shape[1]
    ui = {u: k for k, u in enumerate(units)}
    years_all = sorted(traj_df["year"].unique())

    out_factors = []
    for k in range(rank):
        # Compute per-year weighted mu_k(t), var_k(t)
        rows = []
        for t in years_all:
            gt = traj_df[traj_df["year"] == t]
            if len(gt) == 0: continue
            w = []
            mu_vals, var_vals = [], []
            for r in gt.itertuples():
                i = ui.get(r.orig); j = ui.get(r.dest)
                if i is None or j is None: continue
                wij = A[i, k] * B[j, k]
                if not np.isfinite(wij) or wij == 0: continue
                w.append(wij)
                mu_vals.append(r.mu)
                var_vals.append(r.var)
            if not w: continue
            w = np.asarray(w); mu_vals = np.asarray(mu_vals); var_vals = np.asarray(var_vals)
            W = w.sum()
            if W == 0: continue
            mu_k = float((w * mu_vals).sum() / W)
            var_k = float((w * var_vals).sum() / W)
            rows.append({"year": t, "mu_k": mu_k, "var_k": var_k})
        df = pd.DataFrame(rows)

        train_df = df[df["year"].isin(TRAIN)]
        hold_df  = df[df["year"].isin(holdout_years)]

        r_mu_tr, se_mu_tr = fit_slope(train_df["year"].values, train_df["mu_k"].values)
        r_var_tr, se_var_tr = fit_slope(train_df["year"].values, train_df["var_k"].values)
        r_mu_ho, se_mu_ho = fit_slope(hold_df["year"].values, hold_df["mu_k"].values)
        r_var_ho, se_var_ho = fit_slope(hold_df["year"].values, hold_df["var_k"].values)

        cell_tr = (slope_sign_3way(r_mu_tr, se_mu_tr), slope_sign_3way(r_var_tr, se_var_tr))
        cell_ho = (slope_sign_3way(r_mu_ho, se_mu_ho), slope_sign_3way(r_var_ho, se_var_ho))
        same_or_adj = cells_3x3_adjacent(cell_tr, cell_ho)
        out_factors.append({
            "factor_k": k,
            "n_train": int(len(train_df)), "n_hold": int(len(hold_df)),
            "r_mu_train": r_mu_tr, "se_mu_train": se_mu_tr,
            "r_var_train": r_var_tr, "se_var_train": se_var_tr,
            "r_mu_hold": r_mu_ho, "se_mu_hold": se_mu_ho,
            "r_var_hold": r_var_ho, "se_var_hold": se_var_ho,
            "cell_train": list(cell_tr),
            "cell_hold": list(cell_ho),
            "same_or_adj": bool(same_or_adj),
        })
    pass_count = sum(f["same_or_adj"] for f in out_factors)
    return {"per_factor": out_factors, "pass_count": int(pass_count),
            "pass_all_3": bool(pass_count == 3)}


# ---------------------------------------------------------------------------
# ARM C — top-N corridor original-classifier kappa
# ---------------------------------------------------------------------------

def arm_c(traj_df, cube_df, holdout_years, min_pts_holdout, top_n):
    """
    Top-N corridors by total panel volume. Re-run original classifier (locked
    thresholds) on train vs holdout per-corridor labels; Cohen's kappa.
    """
    # Total volume per corridor
    vol = cube_df[cube_df["orig"] != cube_df["dest"]].groupby(["orig", "dest"])["flow"].sum().reset_index()
    vol = vol.rename(columns={"flow": "vol"}).sort_values("vol", ascending=False).head(top_n)
    keep = set(zip(vol["orig"], vol["dest"]))
    sub = traj_df[traj_df.apply(lambda r: (r["orig"], r["dest"]) in keep, axis=1)]

    tr = per_corridor_period_slopes(sub, TRAIN)
    ho = per_corridor_period_slopes(sub, holdout_years)
    tr = tr[tr["n_pts"] >= MIN_PTS_FULL]
    ho = ho[ho["n_pts"] >= min_pts_holdout]
    merged = tr.merge(ho, on=["orig", "dest"], suffixes=("_train", "_hold"))
    if len(merged) < 5:
        return {"n": int(len(merged)), "result": "insufficient_n"}
    train_labels = [classify_v1(r.mu_dot_train, r.var_dot_train) for r in merged.itertuples()]
    hold_labels  = [classify_v1(r.mu_dot_hold,  r.var_dot_hold)  for r in merged.itertuples()]
    kappa = float(cohen_kappa_score(train_labels, hold_labels))
    return {"n_corridors": int(len(merged)), "kappa": kappa,
            "pass_kappa_ge_0p40": bool(kappa >= 0.40),
            "label_dist_train": pd.Series(train_labels).value_counts().to_dict(),
            "label_dist_hold":  pd.Series(hold_labels).value_counts().to_dict()}


# ---------------------------------------------------------------------------
# ARM E — bootstrap original kappa (full-corridor, full-holdout, locked thresh)
# ---------------------------------------------------------------------------

def arm_e(traj_df, holdout_years, n_boot=N_BOOT):
    tr = per_corridor_period_slopes(traj_df, TRAIN)
    ho = per_corridor_period_slopes(traj_df, holdout_years)
    tr = tr[tr["n_pts"] >= MIN_PTS_FULL]
    ho = ho[ho["n_pts"] >= MIN_PTS_FULL]
    merged = tr.merge(ho, on=["orig", "dest"], suffixes=("_train", "_hold"))
    if len(merged) < 5:
        return {"result": "insufficient_n"}
    train_labels = [classify_v1(r.mu_dot_train, r.var_dot_train) for r in merged.itertuples()]
    hold_labels  = [classify_v1(r.mu_dot_hold,  r.var_dot_hold)  for r in merged.itertuples()]
    kappa_obs = float(cohen_kappa_score(train_labels, hold_labels))
    N = len(merged)
    kappas = []
    train_labels = np.array(train_labels)
    hold_labels = np.array(hold_labels)
    for _ in range(n_boot):
        idx = RNG.integers(0, N, size=N)
        if len(set(train_labels[idx])) < 2 or len(set(hold_labels[idx])) < 2:
            kappas.append(0.0); continue
        kappas.append(float(cohen_kappa_score(train_labels[idx], hold_labels[idx])))
    kappas = np.array(kappas)
    ci_lo, ci_hi = float(np.percentile(kappas, 2.5)), float(np.percentile(kappas, 97.5))
    return {"kappa_observed": kappa_obs, "kappa_mean_bootstrap": float(kappas.mean()),
            "kappa_ci_95": [ci_lo, ci_hi],
            "frac_kappa_ge_0p40": float((kappas >= 0.40).mean()),
            "n_corridors": int(N), "n_boot": int(n_boot)}


# ---------------------------------------------------------------------------
# ARM F — threshold sensitivity (diagnostic)
# ---------------------------------------------------------------------------

def arm_f(traj_df, holdout_years):
    tr = per_corridor_period_slopes(traj_df, TRAIN)
    ho = per_corridor_period_slopes(traj_df, holdout_years)
    tr = tr[tr["n_pts"] >= MIN_PTS_FULL]
    ho = ho[ho["n_pts"] >= MIN_PTS_FULL]
    merged = tr.merge(ho, on=["orig", "dest"], suffixes=("_train", "_hold"))
    out = []
    for s in TH_SCALES:
        thmu = TH_MU * s; thvar = TH_VAR * s
        train_labels = [classify_v1(r.mu_dot_train, r.var_dot_train, thmu, thvar) for r in merged.itertuples()]
        hold_labels  = [classify_v1(r.mu_dot_hold,  r.var_dot_hold,  thmu, thvar) for r in merged.itertuples()]
        kappa = float(cohen_kappa_score(train_labels, hold_labels))
        out.append({"threshold_scale": s, "th_mu": thmu, "th_var": thvar, "kappa": kappa})
    return {"per_scale": out, "n_corridors": int(len(merged))}


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("PRE_REG v2.0 — GEO_F4 re-slice, 6-ARM package fire")
    print("=" * 70)

    # Static PARAFAC factors for ARM B (division only, training-window residual cube)
    print("\n[ARM B prep] Re-fitting static PARAFAC at division, rank=3 ...")
    A_div, B_div, _, units_div, _ = _build_div_static_factors(rank=3)
    print(f"  A: {A_div.shape}, B: {B_div.shape}, units: {units_div}")

    verdict = {"prereg": "v2.0", "locked_commit": "2d7f321"}

    for res in ["division", "state"]:
        traj = pd.read_parquet(RESULTS / f"geo_corridor_trajectories_{res}.parquet")
        cube = pd.read_parquet(DERIVED / f"geo_cube_{res}s.parquet")
        print(f"\n=== Resolution: {res} ===")
        print(f"  trajectories: {len(traj)} corridor-years; unique corridors: {traj.groupby(['orig','dest']).ngroups}")

        block = {}

        # ARM A
        print("  ARM A (continuous coords) ...")
        block["arm_a_full"] = arm_a(traj, HOLDOUT_FULL, MIN_PTS_FULL)
        # ARM D variant: pre-COVID holdout
        print("  ARM D-A (continuous coords, pre-COVID holdout) ...")
        block["arm_d_a_precovid"] = arm_a(traj, HOLDOUT_PRE_COVID, MIN_PTS_PRE_COVID)

        # ARM B (division only)
        if res == "division":
            print("  ARM B (latent-factor coords) ...")
            block["arm_b_full"] = arm_b(traj, HOLDOUT_FULL, A_div, B_div, units_div)
            print("  ARM D-B (latent, pre-COVID holdout) ...")
            block["arm_d_b_precovid"] = arm_b(traj, HOLDOUT_PRE_COVID, A_div, B_div, units_div)

        # ARM C
        print(f"  ARM C (top-{TOPN[res]} kappa) ...")
        block["arm_c_full"] = arm_c(traj, cube, HOLDOUT_FULL, MIN_PTS_FULL, TOPN[res])
        print(f"  ARM D-C (top-{TOPN[res]} kappa, pre-COVID holdout) ...")
        block["arm_d_c_precovid"] = arm_c(traj, cube, HOLDOUT_PRE_COVID, MIN_PTS_PRE_COVID, TOPN[res])

        # ARM E (bootstrap of original kappa, full population, full holdout)
        print(f"  ARM E (bootstrap original kappa, {N_BOOT} draws) ...")
        block["arm_e_bootstrap"] = arm_e(traj, HOLDOUT_FULL)

        # ARM F (threshold sensitivity, full population, full holdout)
        print("  ARM F (threshold sensitivity) ...")
        block["arm_f_threshold"] = arm_f(traj, HOLDOUT_FULL)

        verdict[res] = block

    # Verdict matrix
    print("\n" + "=" * 70)
    print("PACKAGE VERDICT")
    print("=" * 70)
    for res in ["division", "state"]:
        b = verdict[res]
        print(f"\n--- {res} ---")
        a = b["arm_a_full"]
        if "pass_both" in a:
            print(f"  ARM A:  r_mu_dot={a['r_mu_dot']:+.3f} (p={a['p_mu_dot']:.4f}), "
                  f"r_var_dot={a['r_var_dot']:+.3f} (p={a['p_var_dot']:.4f}), "
                  f"pass_both={a['pass_both']}, n={a['n_corridors']}")
        if res == "division" and "arm_b_full" in b:
            bb = b["arm_b_full"]
            print(f"  ARM B:  pass_count={bb['pass_count']}/3, pass_all_3={bb['pass_all_3']}")
        c = b["arm_c_full"]
        if "kappa" in c:
            print(f"  ARM C:  kappa={c['kappa']:+.3f}, pass>=0.40={c['pass_kappa_ge_0p40']}, n={c['n_corridors']}")
        e = b["arm_e_bootstrap"]
        if "kappa_observed" in e:
            print(f"  ARM E:  kappa_obs={e['kappa_observed']:+.3f}, "
                  f"bootstrap 95% CI=[{e['kappa_ci_95'][0]:+.3f}, {e['kappa_ci_95'][1]:+.3f}], "
                  f"P(kappa>=0.40)={e['frac_kappa_ge_0p40']:.3f}")
        f = b["arm_f_threshold"]
        print(f"  ARM F:  kappas at scale ×0.5 / ×1.0 / ×2.0: " + "  ".join(
            f"{p['threshold_scale']:.1f}->{p['kappa']:+.3f}" for p in f["per_scale"]))
        # ARM D summary
        da = b["arm_d_a_precovid"]
        if "pass_both" in da:
            print(f"  ARM D-A pre-COVID: r_mu={da['r_mu_dot']:+.3f} r_var={da['r_var_dot']:+.3f} "
                  f"pass_both={da['pass_both']} (n={da['n_corridors']})")
        if res == "division" and "arm_d_b_precovid" in b:
            dbb = b["arm_d_b_precovid"]
            print(f"  ARM D-B pre-COVID: pass_count={dbb['pass_count']}/3")
        dc = b["arm_d_c_precovid"]
        if "kappa" in dc:
            print(f"  ARM D-C pre-COVID: kappa={dc['kappa']:+.3f} pass={dc['pass_kappa_ge_0p40']} n={dc['n_corridors']}")

    out_path = OUT / "v2_results.json"
    out_path.write_text(json.dumps(verdict, indent=2, default=str))
    print(f"\nWritten -> {out_path}")


if __name__ == "__main__":
    main()
