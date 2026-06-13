"""
Paper 8 - PRE_REG_036: SPEI meteorological-drought ENSO test (P8-F).

Re-runs PRE_REG_034 Set A against SPEI meteorological drought severity instead
of GIDD drought-DISPLACEMENT counts. SPEI is contemporaneous with rainfall (no
reporting lag) and dense (monthly 1950-2024 ~75 yr, vs ~4 displacement years),
so it can properly test whether Horn drought clusters in La Nina years.

Set A: ETH+SOM SPEI-drought years >=60% La Nina (predicted; 034 displacement gave 50%).
Set B: BRA-Amazon SPEI-drought El-Nino-aligned (La Nina <30%, < Horn share).
Set C: Horn SPEI La-Nina share exceeds displacement-based 50% by >=15pp -> 034 was instrument artifact.

Refuses to run on a truncated NetCDF (checks dims/eof first).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

SPEI12 = Path("D:/IDP/data/spei/SPEI_12.nc")
SPEI03 = Path("D:/IDP/data/spei/SPEI_03.nc")
ONI = Path("D:/IDP/data/oni.txt")
OUT = Path("D:/IDP/analysis/paper8_prereg036_spei_enso_2026_05_28.json")

# country bounding boxes (lat_min, lat_max, lon_min, lon_max) in -180..180
BBOX = {
    "ETH": (3.0, 15.0, 33.0, 48.0),
    "SOM": (-2.0, 12.0, 41.0, 51.0),
    "BRA": (-12.0, 5.0, -73.0, -50.0),  # Amazon basin
}
DROUGHT_THRESHOLDS = [-0.8, -1.0, -1.5]
PRIMARY_THR = -1.0


def load_oni_ond():
    df = pd.read_csv(ONI, sep=r"\s+")
    ond = df[df["SEAS"] == "OND"][["YR", "ANOM"]].rename(columns={"YR": "year", "ANOM": "oni"})

    def phase(o):
        if o <= -0.5:
            return "LaNina"
        if o >= 0.5:
            return "ElNino"
        return "neutral"

    ond["phase"] = ond["oni"].apply(phase)
    return ond.set_index("year")


def open_spei(path: Path):
    """Open SPEI NetCDF defensively; raise with a clear message if truncated."""
    import xarray as xr
    last = None
    for eng in ("h5netcdf", "netcdf4", None):
        try:
            ds = xr.open_dataset(path, engine=eng) if eng else xr.open_dataset(path)
            return ds
        except Exception as e:  # noqa
            last = e
    raise RuntimeError(f"cannot open {path.name}: {type(last).__name__}: {str(last)[:160]}")


def detect_coords(ds):
    names = {n.lower(): n for n in list(ds.coords) + list(ds.dims)}
    lat = names.get("lat") or names.get("latitude") or names.get("y")
    lon = names.get("lon") or names.get("longitude") or names.get("x")
    time = names.get("time") or names.get("t")
    # spei variable
    var = None
    for v in ds.data_vars:
        if "spei" in v.lower():
            var = v
            break
    if var is None:
        var = list(ds.data_vars)[0]
    return lat, lon, time, var


def area_mean_december(ds, lat, lon, timec, var, bbox):
    """Mean SPEI over bbox for the December value of each year."""
    latmin, latmax, lonmin, lonmax = bbox
    da = ds[var]
    # handle 0..360 lon convention
    lon_vals = ds[lon].values
    if float(np.nanmax(lon_vals)) > 180.0:
        lo = lonmin % 360
        hi = lonmax % 360
        if lo <= hi:
            sub = da.where((ds[lon] >= lo) & (ds[lon] <= hi), drop=True)
        else:  # wraps
            sub = da.where((ds[lon] >= lo) | (ds[lon] <= hi), drop=True)
    else:
        sub = da.where((ds[lon] >= lonmin) & (ds[lon] <= lonmax), drop=True)
    # latitude may be ascending or descending
    sub = sub.where((ds[lat] >= latmin) & (ds[lat] <= latmax), drop=True)
    # area mean over space
    spatial_dims = [d for d in sub.dims if d != timec]
    ts = sub.mean(dim=spatial_dims, skipna=True)
    df = ts.to_dataframe(name="spei").reset_index()
    df["year"] = pd.to_datetime(df[timec]).dt.year
    df["month"] = pd.to_datetime(df[timec]).dt.month
    dec = df[df["month"] == 12][["year", "spei"]].set_index("year")["spei"]
    return dec.dropna()


def contingency(drought_years, oni, label):
    phases = {y: oni.loc[y, "phase"] if y in oni.index else "?" for y in drought_years}
    n = len(drought_years)
    nl = sum(1 for p in phases.values() if p == "LaNina")
    ne = sum(1 for p in phases.values() if p == "ElNino")
    nn = sum(1 for p in phases.values() if p == "neutral")
    pct_l = round(100 * nl / n, 1) if n else None
    pct_e = round(100 * ne / n, 1) if n else None
    print(f"  {label}: n={n} drought-years  LaNina={nl}({pct_l}%) ElNino={ne}({pct_e}%) neutral={nn}")
    return {"n": n, "n_lanina": nl, "n_elnino": ne, "n_neutral": nn,
            "pct_lanina": pct_l, "pct_elnino": pct_e, "years": list(map(int, drought_years))}


def run_window(spei_by_country, oni, yr_lo, yr_hi, thr, results_key, out):
    print("\n" + "=" * 76)
    print(f"WINDOW {yr_lo}-{yr_hi}  |  SPEI drought threshold <= {thr}")
    print("=" * 76)
    years_range = [y for y in range(yr_lo, yr_hi + 1)]
    base_l = sum(1 for y in years_range if (y in oni.index and oni.loc[y, "phase"] == "LaNina"))
    base_pct = round(100 * base_l / len(years_range), 1)
    print(f"  baseline La Nina rate {yr_lo}-{yr_hi}: {base_l}/{len(years_range)} = {base_pct}%")

    horn_years = []
    per_country = {}
    for iso in ["ETH", "SOM", "BRA"]:
        s = spei_by_country[iso]
        s = s[(s.index >= yr_lo) & (s.index <= yr_hi)]
        dyears = sorted(s[s <= thr].index.tolist())
        per_country[iso] = contingency(dyears, oni, iso)
        if iso in ("ETH", "SOM"):
            horn_years.extend(dyears)

    horn_years = sorted(set(horn_years))
    print("  --- combined ---")
    horn = contingency(horn_years, oni, "HORN(ETH+SOM)")
    bra = per_country["BRA"]

    out[results_key] = {
        "baseline_lanina_pct": base_pct, "per_country": per_country,
        "horn": horn, "bra": bra,
    }
    return base_pct, horn, bra


def main():
    if not SPEI12.exists():
        print("SPEI_12.nc not present yet — abort."); return
    # integrity gate
    try:
        ds = open_spei(SPEI12)
    except RuntimeError as e:
        print(f"INTEGRITY FAIL: {e}")
        print("File is truncated / not fully downloaded. Aborting before analysis.")
        return
    lat, lon, timec, var = detect_coords(ds)
    print(f"SPEI_12 opened: var={var} lat={lat} lon={lon} time={timec}")
    print(f"  dims={dict(ds.dims)}  time=[{str(ds[timec].min().values)[:10]}..{str(ds[timec].max().values)[:10]}]")

    oni = load_oni_ond()
    spei_by_country = {iso: area_mean_december(ds, lat, lon, timec, var, BBOX[iso]) for iso in BBOX}
    for iso, s in spei_by_country.items():
        print(f"  {iso}: {len(s)} annual SPEI_12-Dec values [{s.index.min()}..{s.index.max()}], "
              f"min={s.min():.2f} median={s.median():.2f}")

    out = {"instrument": "SPEI_12 Dec annual", "bbox": BBOX, "primary_thr": PRIMARY_THR}

    # primary window + threshold
    base_full, horn_full, bra_full = run_window(spei_by_country, oni, 1950, 2024, PRIMARY_THR, "full_thr10", out)
    # 034-comparable window
    run_window(spei_by_country, oni, 2008, 2024, PRIMARY_THR, "w2008_thr10", out)
    # sensitivity sweep (full window)
    for thr in DROUGHT_THRESHOLDS:
        if thr == PRIMARY_THR:
            continue
        run_window(spei_by_country, oni, 1950, 2024, thr, f"full_thr{str(thr).replace('.','').replace('-','m')}", out)

    # ---- verdicts on primary (full window, thr -1.0) ----
    print("\n" + "=" * 76)
    print("VERDICTS (primary: 1950-2024, SPEI<=-1.0)")
    print("=" * 76)
    horn_pct = horn_full["pct_lanina"]
    bra_pct = bra_full["pct_lanina"]
    enrich = round(horn_pct - base_full, 1) if horn_pct is not None else None
    setA = horn_pct is not None and horn_pct >= 60 and enrich is not None and enrich >= 15
    setB = (bra_pct is not None and bra_pct < 30 and bra_full["pct_elnino"] is not None
            and bra_full["pct_elnino"] > bra_pct and (horn_pct is None or bra_pct < horn_pct))
    disp_034 = 50.0  # PRE_REG_034 Set A Horn displacement La Nina share
    setC = horn_pct is not None and (horn_pct - disp_034) >= 15
    print(f"  Set A (Horn SPEI-drought >=60% La Nina & enrich>=15pp): {horn_pct}% (enrich {enrich}pp vs {base_full}%) -> {'SUPPORTED' if setA else 'NOT SUPPORTED (F1)'}")
    print(f"  Set B (BRA El-Nino-aligned, La Nina<30% & < Horn): BRA {bra_pct}% La Nina / {bra_full['pct_elnino']}% El Nino -> {'SUPPORTED' if setB else 'NOT'}")
    print(f"  Set C (Horn SPEI exceeds displacement 50% by >=15pp -> 034 artifact): {horn_pct}% vs 50% -> {'CONFIRMED artifact' if setC else 'NOT (034 failure was real, F2)'}")

    out["verdicts"] = {
        "horn_lanina_pct": horn_pct, "bra_lanina_pct": bra_pct, "baseline": base_full,
        "enrichment_pp": enrich, "setA_supported": bool(setA),
        "setB_supported": bool(setB), "setC_artifact_confirmed": bool(setC),
        "displacement_034_pct": disp_034,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\nSaved: {OUT}")
    ds.close()


if __name__ == "__main__":
    main()
