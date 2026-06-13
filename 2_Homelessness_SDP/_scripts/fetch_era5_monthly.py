"""ERA5 monthly means fetch via Copernicus CDS.

Variables: 2m temperature, total precipitation, soil moisture, 10m wind components.
Years: 1998-2024 (matches substrate temporal scope).
Spatial: global, 0.25° native grid.
Format: NetCDF.

Queued at CDS — may take minutes to hours depending on load.
"""
import cdsapi
import pathlib
import time

OUT = pathlib.Path(r"D:/IDP/data/era5")
OUT.mkdir(parents=True, exist_ok=True)
TARGET = OUT / "era5_monthly_1998_2024.nc"

if TARGET.exists():
    print(f"[skip] {TARGET} exists ({TARGET.stat().st_size:,} bytes)")
    raise SystemExit(0)

print(f"[{time.strftime('%H:%M:%S')}] submitting ERA5 monthly request -> {TARGET}")
c = cdsapi.Client()
c.retrieve(
    "reanalysis-era5-single-levels-monthly-means",
    {
        "product_type": ["monthly_averaged_reanalysis"],
        "variable": [
            "2m_temperature",
            "total_precipitation",
            "volumetric_soil_water_layer_1",
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
        ],
        "year": [str(y) for y in range(1998, 2025)],
        "month": [f"{m:02d}" for m in range(1, 13)],
        "time": ["00:00"],
        "data_format": "netcdf",
        "download_format": "unarchived",
    },
    str(TARGET),
)
print(f"[{time.strftime('%H:%M:%S')}] complete: {TARGET} ({TARGET.stat().st_size:,} bytes)")

