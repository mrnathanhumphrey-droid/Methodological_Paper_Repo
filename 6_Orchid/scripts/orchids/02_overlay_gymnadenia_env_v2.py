"""
v2 env overlay for the 8 Gymnadenia odoratissima populations.

Upgrades over v1:
  - 2.5m WorldClim BIO (~4.5 km) replaces 10m (~18 km)
  - 5m WorldClim elev (~9 km) replaces 10m
  - 12-month tavg/tmin/tmax/prec (48 monthly clims)
  - Ecoregion attribution via point-in-polygon over Dinerstein 2017
  - SoilGrids 2.0 (10 props x 6 depths) with CRS reprojection (ESRI:54052 IGH)

Output:
  D:/Phenotype_Research/data/orchids/gymnadenia/derived/gymnadenia_pop_env_v2.csv
"""

from pathlib import Path
import csv
import rasterio
from rasterio.warp import transform as rio_transform
import geopandas as gpd
from shapely.geometry import Point

ROOT = Path(r"D:/Phenotype_Research")
BIO_DIR = ROOT / "data/climate/wc2.1_2.5m_bio"
TAVG_DIR = ROOT / "data/climate/wc2.1_10m_tavg"
TMIN_DIR = ROOT / "data/climate/wc2.1_10m_tmin"
TMAX_DIR = ROOT / "data/climate/wc2.1_10m_tmax"
PREC_DIR = ROOT / "data/climate/wc2.1_10m_prec"
ELEV_TIF = ROOT / "data/elevation/wc2.1_5m_elev/wc2.1_5m_elev.tif"
SOIL_DIR = ROOT / "data/soil"
ECO_SHP = ROOT / "data/ecoregions/Ecoregions2017/Ecoregions2017.shp"
OUT_CSV = ROOT / "data/orchids/gymnadenia/derived/gymnadenia_pop_env_v2.csv"


def dms(d, m, s):
    return d + m / 60.0 + s / 3600.0


POPULATIONS = [
    ("lowland",  "Doettingen",  "D",  dms(47, 34, 30), dms(8, 16, 25),  500),
    ("lowland",  "Remigen",     "R",  dms(47, 31, 45), dms(8,  9, 45),  600),
    ("lowland",  "Linn",        "L",  dms(47, 28, 35), dms(8,  7,  0),  500),
    ("lowland",  "Rossweid",    "RW", dms(47, 18, 45), dms(8, 30, 40),  650),
    ("mountain", "Schatzalp",   "S",  dms(46, 48, 20), dms(9, 49, 30), 1800),
    ("mountain", "Muenstertal", "M",  dms(46, 37, 50), dms(10,19,  5), 1800),
    ("mountain", "Albulapass",  "A",  dms(46, 34, 55), dms(9, 48, 50), 2250),
    ("mountain", "Corviglia",   "C",  dms(46, 30, 20), dms(9, 49, 55), 2200),
]


def sample_raster(tif, points):
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    with rasterio.open(tif) as src:
        if src.crs.to_string() != "EPSG:4326":
            xs, ys = rio_transform("EPSG:4326", src.crs, lons, lats)
        else:
            xs, ys = lons, lats
        nodata = src.nodatavals[0] if src.nodatavals else None
        vals = list(src.sample(list(zip(xs, ys))))
    out = []
    for v in vals:
        x = float(v[0])
        if nodata is not None and x == nodata:
            out.append(None)
        else:
            out.append(x)
    return out


def pixel_indices(tif, points):
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    with rasterio.open(tif) as src:
        if src.crs.to_string() != "EPSG:4326":
            xs, ys = rio_transform("EPSG:4326", src.crs, lons, lats)
        else:
            xs, ys = lons, lats
        return [src.index(x, y) for x, y in zip(xs, ys)]


def main():
    pts = [(lat, lon) for _, _, _, lat, lon, _ in POPULATIONS]

    # --- BIO @ 2.5m ---
    print("Sampling 19 BIO @ 2.5m ...")
    bio_cols = [f"bio_{i}" for i in range(1, 20)]
    bio_vals = {f"bio_{i}": sample_raster(BIO_DIR / f"wc2.1_2.5m_bio_{i}.tif", pts)
                for i in range(1, 20)}

    # --- elev @ 5m ---
    print("Sampling elev @ 5m ...")
    elev_vals = sample_raster(ELEV_TIF, pts)

    # --- monthly clims @ 10m ---
    print("Sampling monthly tavg/tmin/tmax/prec @ 10m ...")
    monthly_cols = []
    monthly_vals = {}
    for prefix, d in (("tavg", TAVG_DIR), ("tmin", TMIN_DIR),
                      ("tmax", TMAX_DIR), ("prec", PREC_DIR)):
        for m in range(1, 13):
            mm = f"{m:02d}"
            tif = d / f"wc2.1_10m_{prefix}_{mm}.tif"
            key = f"{prefix}_{mm}"
            monthly_cols.append(key)
            monthly_vals[key] = sample_raster(tif, pts)

    # --- soil ---
    print("Sampling 60 SoilGrids rasters @ 5km ...")
    soil_props = ["bdod", "cec", "cfvo", "clay", "nitrogen",
                  "ocd", "phh2o", "sand", "silt", "soc"]
    soil_depths = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]
    soil_cols = []
    soil_vals = {}
    for p in soil_props:
        for d in soil_depths:
            tif = SOIL_DIR / f"{p}_{d}_mean_5000.tif"
            key = f"{p}_{d}"
            soil_cols.append(key)
            try:
                soil_vals[key] = sample_raster(tif, pts)
            except Exception as e:
                print(f"  WARN {tif.name}: {e}")
                soil_vals[key] = [None] * len(pts)

    # --- ecoregion ---
    print("Ecoregion point-in-polygon ...")
    eco = gpd.read_file(ECO_SHP)
    eco_attrs = ["ECO_NAME", "BIOME_NAME", "REALM", "NNH_NAME"]
    pop_geoms = gpd.GeoDataFrame(
        {"i": list(range(len(pts)))},
        geometry=[Point(lon, lat) for lat, lon in pts],
        crs="EPSG:4326",
    )
    eco = eco.to_crs("EPSG:4326")
    joined = gpd.sjoin(pop_geoms, eco[["geometry"] + eco_attrs],
                       how="left", predicate="within")
    joined = joined.sort_values("i")
    eco_lookup = {row.i: tuple(getattr(row, a) for a in eco_attrs)
                  for row in joined.itertuples()}

    # --- distinctness diagnostics ---
    print("\n=== PIXEL DISTINCTNESS ===")
    for label, tif in [("BIO 2.5m", BIO_DIR / "wc2.1_2.5m_bio_1.tif"),
                       ("elev 5m", ELEV_TIF),
                       ("soil 5km", SOIL_DIR / "phh2o_0-5cm_mean_5000.tif")]:
        idx = pixel_indices(tif, pts)
        seen = {}
        for (_, _, code, _, _, _), i in zip(POPULATIONS, idx):
            seen.setdefault(i, []).append(code)
        n_unique = len(seen)
        print(f"  {label}: {n_unique}/8 unique")
        for i, codes in seen.items():
            if len(codes) > 1:
                print(f"    COLLISION  {i}  -> {codes}")

    # --- write csv ---
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = ["region", "population", "code", "lat_dd", "lon_dd",
              "altitude_paper_m", "elev_wc5m"] + eco_attrs + bio_cols + monthly_cols + soil_cols
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for i, (region, name, code, lat, lon, alt) in enumerate(POPULATIONS):
            row = [region, name, code, round(lat, 6), round(lon, 6),
                   alt, elev_vals[i]] + list(eco_lookup[i])
            row += [bio_vals[c][i] for c in bio_cols]
            row += [monthly_vals[c][i] for c in monthly_cols]
            row += [soil_vals[c][i] for c in soil_cols]
            w.writerow(row)
    print(f"\nWrote {OUT_CSV}")
    print(f"  8 rows x {len(fields)} cols")


if __name__ == "__main__":
    main()
