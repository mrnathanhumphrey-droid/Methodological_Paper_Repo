"""
Geographic arm — Stage 4: CP/PARAFAC tensor decomposition of the gravity-residual
species-cube (PRE_REG v1.6), division resolution (power-gated; state cube too sparse).

Residual cube R[orig(9), dest(9), species(38)] = observed window-sum flow minus
gravity-expected (E_ij * species national share), diagonal masked to 0.
CP decompose rank k=3 -> latent corridor-sorting factors.

GEO_F2 (factor stability): refit CP on 2012-2014 vs 2015-2017 residual cubes;
factor congruence (Tucker congruence) below floor -> factors not replicable ->
gravity dimension resists structured decomposition (fires).

Outputs: results/geo_tensor_factors.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import tensorly as tl
from tensorly.decomposition import parafac

sys.path.insert(0, str(Path(__file__).parent))
from geo_stage1_cube_gravity import DIVISION, unit_mass_centroid, haversine

DERIVED = Path(r"D:\Migration\data\derived")
RESULTS = Path(r"D:\Migration\results")
RANK = 3
DIV_NAMES = {1: "NewEng", 2: "MidAtl", 3: "ENCentral", 4: "WNCentral", 5: "SAtl",
             6: "ESCentral", 7: "WSCentral", 8: "Mountain", 9: "Pacific"}


def gravity_E(cube_window):
    mass = unit_mass_centroid("division").set_index("unit")
    od = cube_window.groupby(["orig", "dest"]).flow.sum().reset_index()
    od = od[od.orig != od.dest].copy()
    od = od.join(mass[["mass", "lon", "lat"]].rename(columns=lambda c: f"o_{c}"), on="orig")
    od = od.join(mass[["mass", "lon", "lat"]].rename(columns=lambda c: f"d_{c}"), on="dest")
    od = od.dropna(subset=["o_mass", "d_mass"])
    od["dist"] = haversine(od.o_lon, od.o_lat, od.d_lon, od.d_lat).clip(lower=1)
    X = sm.add_constant(np.column_stack([np.log(od.o_mass), np.log(od.d_mass), np.log(od.dist)]))
    fit = sm.GLM(od.flow, X, family=sm.families.Poisson()).fit()
    od["E"] = fit.predict(X)
    return {(r.orig, r.dest): r.E for r in od.itertuples()}


def build_residual_cube(cube_window):
    units = sorted(set(cube_window.orig) | set(cube_window.dest))
    species = sorted(cube_window.species.unique())
    ui = {u: k for k, u in enumerate(units)}
    si = {s: k for k, s in enumerate(species)}
    E = gravity_E(cube_window)
    tot = cube_window.flow.sum()
    p_s = (cube_window.groupby("species").flow.sum() / tot).to_dict()
    R = np.zeros((len(units), len(units), len(species)))
    O = cube_window.groupby(["orig", "dest", "species"]).flow.sum()
    for (i, j, s), o in O.items():
        if i == j:
            continue
        e = E.get((i, j))
        if e is None:
            continue
        R[ui[i], uj if (uj := ui[j]) is not None else 0, si[s]] = o - e * p_s.get(s, 0)
    return R, units, species


def cp(R, rank):
    R = np.nan_to_num(R)
    w, factors = parafac(tl.tensor(R), rank=rank, n_iter_max=500, random_state=0)
    return factors  # [orig(U x r), dest(U x r), species(S x r)]


def congruence(A, B):
    """Max mean Tucker congruence across matched components (greedy)."""
    A = A / (np.linalg.norm(A, axis=0, keepdims=True) + 1e-12)
    B = B / (np.linalg.norm(B, axis=0, keepdims=True) + 1e-12)
    C = np.abs(A.T @ B)
    used = set(); vals = []
    for i in range(C.shape[0]):
        j = int(np.argmax([C[i, j] if j not in used else -1 for j in range(C.shape[1])]))
        used.add(j); vals.append(float(C[i, j]))
    return float(np.mean(vals))


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    cube = pd.read_parquet(DERIVED / "geo_cube_divisions.parquet")

    R, units, species = build_residual_cube(cube)
    factors = cp(R, RANK)
    of, df, sf = factors

    print(f"=== CP/PARAFAC rank-{RANK} on division gravity-residual cube (9x9x{len(species)}) ===")
    out = {"rank": RANK, "units": [int(u) for u in units], "components": []}
    for k in range(RANK):
        o_top = sorted(zip(units, of[:, k]), key=lambda x: -abs(x[1]))[:3]
        d_top = sorted(zip(units, df[:, k]), key=lambda x: -abs(x[1]))[:3]
        s_top = sorted(zip(species, sf[:, k]), key=lambda x: -abs(x[1]))[:4]
        print(f"\ncomponent {k+1}:")
        print("  origins :", ", ".join(f"{DIV_NAMES[u]}({v:+.2f})" for u, v in o_top))
        print("  dests   :", ", ".join(f"{DIV_NAMES[u]}({v:+.2f})" for u, v in d_top))
        print("  species :", ", ".join(f"{s}({v:+.2f})" for s, v in s_top))
        out["components"].append(dict(
            origins=[(DIV_NAMES[u], float(v)) for u, v in o_top],
            dests=[(DIV_NAMES[u], float(v)) for u, v in d_top],
            species=[(s, float(v)) for s, v in s_top]))

    # GEO_F2: split-half stability
    early = cube[cube.year <= 2014]; late = cube[cube.year >= 2015]
    Re, _, _ = build_residual_cube(early); Rl, _, _ = build_residual_cube(late)
    fe = cp(Re, RANK); fl = cp(Rl, RANK)
    cong = np.mean([congruence(fe[m], fl[m]) for m in range(3)])
    out["geo_f2_split_half_congruence"] = float(cong)
    fires = cong < 0.5
    print(f"\n--- GEO_F2 (factor stability) ---")
    print(f"split-half (2012-14 vs 2015-17) mean Tucker congruence: {cong:.3f}")
    print(f"GEO_F2 (congruence<0.5 -> factors not replicable): "
          f"{'FIRES' if fires else 'does not fire (factors replicate -> stable structure)'}")

    (RESULTS / "geo_tensor_factors.json").write_text(json.dumps(out, indent=2))
    print(f"\nwritten: results/geo_tensor_factors.json")


if __name__ == "__main__":
    main()
