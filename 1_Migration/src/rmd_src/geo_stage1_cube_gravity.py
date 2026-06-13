"""
Geographic arm (PRE_REG v1.6) — Stage 1: flow 4-cube + gravity baseline + coverage.

Builds the full 4-cube T[origin, dest, species, year] flows at TWO resolutions
(census divisions, states), fits the gravity baseline on between-unit flows,
and reports the n>=50 moment-coverage map. CHECK-IN before moment-flow.

Outputs:
  data/derived/geo_cube_divisions.parquet   (orig_div, dest_div, species, year, flow)
  data/derived/geo_cube_states.parquet      (orig_st,  dest_st,  species, year, flow)
  results/geo_gravity_baseline.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

DERIVED = Path(r"D:\Migration\data\derived")
RESULTS = Path(r"D:\Migration\results")
WINDOW = list(range(2012, 2022))  # full geographic-arm window 2012-2021
MIN_CELL = 50

# state FIPS -> Census division (1-9); 50 states + DC(11)
DIVISION = {
    1: 6, 2: 9, 4: 8, 5: 7, 6: 9, 8: 8, 9: 1, 10: 5, 11: 5, 12: 5, 13: 5,
    15: 9, 16: 8, 17: 3, 18: 3, 19: 4, 20: 4, 21: 6, 22: 7, 23: 1, 24: 5,
    25: 1, 26: 3, 27: 4, 28: 6, 29: 4, 30: 8, 31: 4, 32: 8, 33: 1, 34: 2,
    35: 8, 36: 2, 37: 5, 38: 4, 39: 3, 40: 7, 41: 9, 42: 2, 44: 1, 45: 5,
    46: 4, 47: 6, 48: 7, 49: 8, 50: 1, 51: 5, 53: 9, 54: 5, 55: 3, 56: 8,
}


def unit_mass_centroid(level):
    """Aggregate MIGPUMA population + centroid to division/state level."""
    pop = pd.read_parquet(DERIVED / "migpuma_population_2010.parquet")
    geo = pd.read_parquet(DERIVED / "migpuma_geometry_2010.parquet")
    g = pop.merge(geo[["statefip", "migpuma", "lon", "lat"]],
                  on=["statefip", "migpuma"], how="left")
    g = g[g.statefip.isin(DIVISION)].copy()
    g["unit"] = g.statefip.map(DIVISION) if level == "division" else g.statefip
    # mean annual population per unit; pop-weighted centroid
    mass = g.groupby("unit").apply(
        lambda d: pd.Series({
            "mass": d.groupby("year").population.sum().mean(),
            "lon": np.average(d.lon, weights=d.population),
            "lat": np.average(d.lat, weights=d.population),
        }), include_groups=False).reset_index()
    return mass


def haversine(lo1, la1, lo2, la2):
    R = 6371.0088
    lo1, la1, lo2, la2 = map(np.radians, [lo1, la1, lo2, la2])
    a = np.sin((la2-la1)/2)**2 + np.cos(la1)*np.cos(la2)*np.sin((lo2-lo1)/2)**2
    return 2*R*np.arcsin(np.sqrt(a))


def build(level, ev):
    col = "div" if level == "division" else "st"
    cube = (ev.groupby([f"orig_{col}", f"dest_{col}", "cell_id", "YEAR"]).PERWT.sum()
            .reset_index().rename(columns={f"orig_{col}": "orig", f"dest_{col}": "dest",
                                           "cell_id": "species", "YEAR": "year",
                                           "PERWT": "flow"}))
    cube.to_parquet(DERIVED / f"geo_cube_{level}s.parquet", index=False)

    n_units = len(set(cube.orig) | set(cube.dest))
    n_cells_full = n_units * n_units * ev.cell_id.nunique() * len(WINDOW)
    moment_cells = int((cube.groupby(["orig", "dest", "species"])
                        .filter(lambda d: d.year.nunique() == len(WINDOW))
                        .groupby(["orig", "dest", "species"]).flow.count().ge(1).sum()))
    # n>=50 coverage on the (orig,dest,species) corridor-species over the window
    cs = cube.groupby(["orig", "dest", "species"]).flow.sum()
    cov_cs = int((cs >= MIN_CELL).sum())
    od = cube.groupby(["orig", "dest"]).flow.sum()
    cov_od = int((od >= MIN_CELL).sum())
    return cube, mass_gravity(level, cube), dict(
        level=level, n_units=n_units, cube_cells_full=int(n_cells_full),
        corridor_species_total=int(len(cs)), corridor_species_ge50=cov_cs,
        OD_pairs_total=int(len(od)), OD_pairs_ge50=cov_od)


def mass_gravity(level, cube):
    mass = unit_mass_centroid(level)
    od = cube.groupby(["orig", "dest"]).flow.sum().reset_index()
    od = od[od.orig != od.dest].copy()  # between-unit only (gravity)
    m = mass.set_index("unit")
    od = od.join(m[["mass", "lon", "lat"]].rename(columns=lambda c: f"o_{c}"), on="orig")
    od = od.join(m[["mass", "lon", "lat"]].rename(columns=lambda c: f"d_{c}"), on="dest")
    od = od.dropna(subset=["o_mass", "d_mass"])
    od["dist"] = haversine(od.o_lon, od.o_lat, od.d_lon, od.d_lat).clip(lower=1)
    X = np.column_stack([np.log(od.o_mass), np.log(od.d_mass), np.log(od.dist)])
    X = sm.add_constant(X)
    model = sm.GLM(od.flow, X, family=sm.families.Poisson()).fit()
    null = sm.GLM(od.flow, np.ones((len(od), 1)), family=sm.families.Poisson()).fit()
    mcfadden = 1 - model.llf / null.llf
    return dict(level=level, n_OD_between=int(len(od)),
                coef_const=float(model.params[0]), coef_log_mass_o=float(model.params[1]),
                coef_log_mass_d=float(model.params[2]), gamma_log_dist=float(model.params[3]),
                mcfadden_pseudo_r2=float(mcfadden))


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ev = pd.read_parquet(DERIVED / "event_observables.parquet")
    ev = ev[~ev.missing_geo].copy()
    ev = ev[ev.YEAR.isin(WINDOW)]
    ev = ev[ev.orig_state.isin(DIVISION) & ev.dest_state.isin(DIVISION)].copy()
    ev["orig_st"] = ev.orig_state; ev["dest_st"] = ev.dest_state
    ev["orig_div"] = ev.orig_state.map(DIVISION); ev["dest_div"] = ev.dest_state.map(DIVISION)
    print(f"events in geo window/scope: {len(ev):,}")

    report = {}
    for level in ["division", "state"]:
        cube, grav, cov = build(level, ev)
        report[level] = {"coverage": cov, "gravity": grav}
        print(f"\n=== {level.upper()}S ===")
        print(f"units: {cov['n_units']}  full 4-cube cells: {cov['cube_cells_full']:,}")
        print(f"O-D pairs: {cov['OD_pairs_total']}  (>=50 flow: {cov['OD_pairs_ge50']})")
        print(f"corridor x species: {cov['corridor_species_total']:,}  "
              f"(>=50 flow, moment-eligible: {cov['corridor_species_ge50']:,})")
        print(f"GRAVITY (between-unit): pseudo-R2={grav['mcfadden_pseudo_r2']:.3f}  "
              f"gamma_dist={grav['gamma_log_dist']:.3f}  "
              f"mass_o={grav['coef_log_mass_o']:.2f} mass_d={grav['coef_log_mass_d']:.2f}")
        print(f"GEO_F1 (gravity pseudo-R2>=0.80 -> 'just gravity'): "
              f"{'FIRES' if grav['mcfadden_pseudo_r2']>=0.80 else 'does not fire (residual structure exists)'}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "geo_gravity_baseline.json").write_text(json.dumps(report, indent=2))
    print(f"\ncubes -> data/derived/geo_cube_*.parquet ; gravity -> results/geo_gravity_baseline.json")


if __name__ == "__main__":
    main()
