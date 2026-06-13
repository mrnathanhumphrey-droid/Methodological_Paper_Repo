"""
Find sPlotOpen vegetation plots within a radius of each Gymnadenia population,
then rank co-occurring species per population's neighborhood.

Two products:
  1. plot_neighborhood_50km.csv -- one row per (pop, plot) within 50 km
  2. species_neighborhood_50km.csv -- per (pop, species) frequency + mean relative cover

Uses haversine on lat/lon. sPlotOpen header has Latitude/Longitude per plot;
DT has (PlotObservationID, Species, Relative_cover).
"""

from pathlib import Path
import math
import pandas as pd

ROOT = Path(r"D:/Phenotype_Research")
SPLOT = ROOT / "data/occurrences/sPlotOpen"
HEADER = SPLOT / "sPlotOpen_header(3).txt"
DT = SPLOT / "sPlotOpen_DT(2).txt"
ENV_CSV = ROOT / "data/orchids/gymnadenia/derived/gymnadenia_pop_env_v2.csv"
OUT_PLOTS = ROOT / "data/orchids/gymnadenia/derived/splot_neighborhood_50km.csv"
OUT_SPECIES = ROOT / "data/orchids/gymnadenia/derived/splot_species_neighborhood_50km.csv"

RADIUS_KM = 50.0


def haversine_vec(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1r, lat2r = pd.to_numeric(lat1) * math.pi / 180, pd.to_numeric(lat2) * math.pi / 180
    dlat = lat2r - lat1r
    dlon = (pd.to_numeric(lon2) - pd.to_numeric(lon1)) * math.pi / 180
    a = (dlat / 2).apply(math.sin) ** 2 + lat1r.apply(math.cos) * lat2r.apply(math.cos) * (dlon / 2).apply(math.sin) ** 2
    return 2 * R * a.apply(lambda x: math.asin(math.sqrt(x)))


def main():
    env = pd.read_csv(ENV_CSV)[["region", "population", "code", "lat_dd", "lon_dd"]]
    print(f"pops: {len(env)}")

    print("Loading sPlotOpen header...")
    hdr = pd.read_csv(HEADER, sep="\t", low_memory=False)
    hdr = hdr[["PlotObservationID", "Country", "Biome", "Latitude", "Longitude",
               "Elevation", "Releve_area", "is_forest", "Naturalness",
               "Grassland", "Wetland"]].copy()
    # pre-filter to a CH-area bbox to keep things light: lat 45.5-48, lon 5-11
    hdr = hdr.dropna(subset=["Latitude", "Longitude"])
    bbox = hdr[(hdr["Latitude"].between(45.5, 48.0))
               & (hdr["Longitude"].between(5.0, 11.5))].copy()
    print(f"  plots in CH bbox: {len(bbox)}/{len(hdr)}")

    rows = []
    for _, p in env.iterrows():
        d = haversine_vec(pd.Series([p["lat_dd"]] * len(bbox)),
                          pd.Series([p["lon_dd"]] * len(bbox)),
                          bbox["Latitude"].reset_index(drop=True),
                          bbox["Longitude"].reset_index(drop=True))
        d.index = bbox.index
        near = bbox.assign(dist_km=d.values)
        near = near[near["dist_km"] <= RADIUS_KM].copy()
        near["pop_code"] = p["code"]
        near["pop_name"] = p["population"]
        near["pop_region"] = p["region"]
        rows.append(near)
        print(f"  {p['code']:3s} {p['population']:14s}  plots within {RADIUS_KM:.0f}km: {len(near)}")

    all_near = pd.concat(rows, ignore_index=True)
    all_near.to_csv(OUT_PLOTS, index=False)
    print(f"\nWrote {OUT_PLOTS}  ({len(all_near)} rows)")

    if len(all_near) == 0:
        print("No plots in any pop neighborhood; skipping species join.")
        return

    print("\nLoading sPlotOpen DT (species x plot)... slow")
    dt = pd.read_csv(DT, sep="\t",
                     usecols=["PlotObservationID", "Species", "Relative_cover"],
                     encoding="latin-1", low_memory=False)
    print(f"  DT rows: {len(dt)}")

    # restrict DT to our neighborhood plots
    nbr_ids = all_near["PlotObservationID"].unique()
    dt_nbr = dt[dt["PlotObservationID"].isin(nbr_ids)]
    print(f"  DT rows in neighborhood plots: {len(dt_nbr)}")

    # join in pop code
    plot_to_pops = all_near[["PlotObservationID", "pop_code", "pop_name", "pop_region"]]
    sp = dt_nbr.merge(plot_to_pops, on="PlotObservationID")

    # per (pop, species): frequency (n plots) + mean Relative_cover + sum cover
    agg = (sp.groupby(["pop_code", "pop_region", "Species"])
             .agg(n_plots=("PlotObservationID", "nunique"),
                  mean_rel_cover=("Relative_cover", "mean"),
                  sum_rel_cover=("Relative_cover", "sum"))
             .reset_index())
    agg = agg.sort_values(["pop_code", "n_plots"], ascending=[True, False])
    agg.to_csv(OUT_SPECIES, index=False)
    print(f"\nWrote {OUT_SPECIES}  ({len(agg)} rows)")

    print("\n=== TOP 10 SPECIES IN EACH POP NEIGHBORHOOD ===")
    for code in agg["pop_code"].unique():
        sub = agg[agg["pop_code"] == code].head(10)
        print(f"\n--- {code} ({sub.iloc[0]['pop_region']}) ---")
        for _, r in sub.iterrows():
            print(f"  {r['Species']:35s}  n_plots={r['n_plots']:3d}  mean_cov={r['mean_rel_cover']:.3f}")


if __name__ == "__main__":
    main()
