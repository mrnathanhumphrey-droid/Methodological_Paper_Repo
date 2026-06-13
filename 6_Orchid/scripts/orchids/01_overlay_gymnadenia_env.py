"""
Overlay the 8 Gymnadenia odoratissima populations against:
  - WorldClim 2.1 BIO 1-19 (10 arcminute)
  - WorldClim 2.1 elevation (10 arcminute)
  - SoilGrids 2.0 (10 properties x 6 depths = 60 rasters, 5km)

Coordinates per S1 Table of Schiestl et al. 2016, PLOS ONE 0147975
(D:/Phenotype_Research/data/orchids/gymnadenia/raw/S1_TABLE_population_locations.pdf).
Original coords are DMS; converted to decimal degrees here.

Output:
  D:/Phenotype_Research/data/orchids/gymnadenia/derived/gymnadenia_pop_env.csv
"""

from pathlib import Path
import csv
import rasterio
from rasterio.warp import transform as rio_transform

ROOT = Path(r"D:/Phenotype_Research")
BIO_DIR = ROOT / "data/climate/wc2.1_10m_bio"
ELEV_TIF = ROOT / "data/elevation/wc2.1_10m_elev/wc2.1_10m_elev.tif"
SOIL_DIR = ROOT / "data/soil"
OUT_CSV = ROOT / "data/orchids/gymnadenia/derived/gymnadenia_pop_env.csv"


def dms(d, m, s):
    return d + m / 60.0 + s / 3600.0


POPULATIONS = [
    # (region, name, code, lat_DMS, lon_DMS, altitude_paper_m)
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
    """Return list of single-band float values at (lat, lon) points.

    Reprojects WGS84 lat/lon to the raster's native CRS before sampling.
    """
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
    """(row, col) of each (lat, lon) point in the raster's native CRS."""
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

    # --- BIO 1-19 ---
    bio_vars = [f"bio_{i}" for i in range(1, 20)]
    bio_vals = {}
    for i in range(1, 20):
        tif = BIO_DIR / f"wc2.1_10m_bio_{i}.tif"
        bio_vals[f"bio_{i}"] = sample_raster(tif, pts)

    # --- elev ---
    elev_vals = sample_raster(ELEV_TIF, pts)

    # --- soil (10 props x 6 depths) ---
    soil_props = ["bdod", "cec", "cfvo", "clay", "nitrogen",
                  "ocd", "phh2o", "sand", "silt", "soc"]
    soil_depths = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]
    soil_vals = {}
    soil_cols = []
    for p in soil_props:
        for d in soil_depths:
            tif = SOIL_DIR / f"{p}_{d}_mean_5000.tif"
            key = f"{p}_{d}"
            soil_cols.append(key)
            try:
                soil_vals[key] = sample_raster(tif, pts)
            except Exception as e:
                print(f"  WARN: {tif.name}: {e}")
                soil_vals[key] = [None] * len(pts)

    # --- pixel distinctness diagnostic ---
    print("\n=== PIXEL DISTINCTNESS (10m WorldClim grid) ===")
    bio1_idx = pixel_indices(BIO_DIR / "wc2.1_10m_bio_1.tif", pts)
    seen = {}
    for (region, name, code, lat, lon, _), idx in zip(POPULATIONS, bio1_idx):
        seen.setdefault(idx, []).append(f"{code}:{name}")
    n_unique = len(seen)
    print(f"  unique 10m BIO pixels for 8 pops: {n_unique}/8")
    for idx, names in seen.items():
        marker = "COLLISION" if len(names) > 1 else "ok       "
        print(f"  {marker}  pixel {idx}  -> {', '.join(names)}")

    soil_idx = pixel_indices(SOIL_DIR / "phh2o_0-5cm_mean_5000.tif", pts)
    seen_s = {}
    for (region, name, code, lat, lon, _), idx in zip(POPULATIONS, soil_idx):
        seen_s.setdefault(idx, []).append(f"{code}:{name}")
    print(f"  unique soil (5km) pixels for 8 pops: {len(seen_s)}/8")
    for idx, names in seen_s.items():
        marker = "COLLISION" if len(names) > 1 else "ok       "
        print(f"  {marker}  pixel {idx}  -> {', '.join(names)}")

    # --- write CSV ---
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = ["region", "population", "code", "lat_dd", "lon_dd",
              "altitude_paper_m", "elev_wc_m"] + bio_vars + soil_cols
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for i, (region, name, code, lat, lon, alt) in enumerate(POPULATIONS):
            row = [region, name, code, round(lat, 6), round(lon, 6), alt,
                   elev_vals[i]]
            row.extend(bio_vals[v][i] for v in bio_vars)
            row.extend(soil_vals[c][i] for c in soil_cols)
            w.writerow(row)
    print(f"\nWrote {OUT_CSV}")
    print(f"  8 rows x {len(fields)} cols")


if __name__ == "__main__":
    main()
