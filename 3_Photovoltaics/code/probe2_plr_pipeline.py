"""
Probe 2 (23_PREREG_v1.0_FleetPLR_PVCZ) — §14.4 + §14.5
Per-system PLR via PVDAQ daily AC energy / pvlib-PVWatts expected energy
(NSRDB irradiance + temperature), then rdtools YoY degradation.

OUTCOME-COMPUTING STAGE. ℙ₀ already locked (probe2_cohort_p0.csv).

Normalization choice (logged per pre-reg §4 x_3 + §15 #6):
  measured: PVDAQ ac_energy_inv_*_daily_sum (kWh/day)
  expected: pvlib PVWatts DC model driven by NSRDB v4 GOES CONUS hourly
            GHI/DNI/DHI/Temp/Wind, transposed to POA (Hay-Davies),
            cell temp via pvlib SAPM thermal (open-rack default),
            gamma_pdc = -0.0047/°C (PVWatts c-Si default), Pdc0 = dc_capacity_kW.
  performance index PI(d) = E_meas(d) / E_model(d)
  PLR = rdtools.degradation.degradation_year_on_year(PI_daily) + bootstrap CI.

NSRDB cached per (lat2,lon2,year) grid cell under data/raw/nsrdb/.
"""
import os, re, io, time, json
from pathlib import Path
import numpy as np
import pandas as pd
import requests

import pvlib
from pvlib import location, irradiance, temperature, pvsystem
from rdtools import degradation_year_on_year

ROOT = Path(__file__).resolve().parent.parent  # Solar/
NSRDB_DIR = ROOT / "data/raw/nsrdb"
NSRDB_DIR.mkdir(parents=True, exist_ok=True)
PVDAQ_CACHE = ROOT / "data/raw/pvdaq_daily"
PVDAQ_CACHE.mkdir(parents=True, exist_ok=True)
MONTHLY_PI_DIR = ROOT / "data/processed/monthly_pi"
MONTHLY_PI_DIR.mkdir(parents=True, exist_ok=True)

S3 = "https://oedi-data-lake.s3.amazonaws.com"
NSRDB_EP = "https://developer.nrel.gov/api/nsrdb/v2/solar/nsrdb-GOES-conus-v4-0-0-download.csv"

# --- credentials from gitignored Solar/.env ---
def _load_env():
    env = {}
    p = ROOT / ".env"
    for line in p.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env
ENV = _load_env()
API_KEY = ENV["NREL_API_KEY"]
API_EMAIL = ENV["NREL_API_EMAIL"]

WINDOW_START = 2018          # NSRDB v4 GOES CONUS coverage begins 2018 (uniform fleet window)
WINDOW_END = 2023            # NSRDB v4 coverage ends 2023
GAMMA_PDC = -0.0047          # PVWatts c-Si default (1/°C)
TEMP_MODEL = temperature.TEMPERATURE_MODEL_PARAMETERS["sapm"]["open_rack_glass_polymer"]


# ---------------- PVDAQ daily energy ----------------
def list_pvdaq_csv_keys(sid):
    keys, token = [], None
    while True:
        url = f"{S3}/?list-type=2&prefix=pvdaq/csv/pvdata/system_id={sid}/&max-keys=1000"
        if token:
            url += f"&continuation-token={requests.utils.quote(token, safe='')}"
        xml = requests.get(url, timeout=60).text
        keys += [k for k in re.findall(r"<Key>(.*?)</Key>", xml) if k.endswith(".csv")]
        m = re.search(r"<NextContinuationToken>(.*?)</NextContinuationToken>", xml)
        if "<IsTruncated>true</IsTruncated>" in xml and m:
            token = m.group(1)
        else:
            break
    return keys


def get_daily_energy(sid):
    """Return daily AC energy Series (kWh/day), tz-naive DatetimeIndex. Cached."""
    cache = PVDAQ_CACHE / f"sys{sid}_daily_energy.csv"
    if cache.exists():
        s = pd.read_csv(cache, index_col=0, parse_dates=True).iloc[:, 0]
        s.index = pd.to_datetime(s.index)
        return s
    keys = [k for k in list_pvdaq_csv_keys(sid) if "_ac_" in k]
    frames = []
    for k in keys:
        try:
            df = pd.read_csv(f"{S3}/{k}")
        except Exception:
            continue
        ecols = [c for c in df.columns if re.match(r"ac_energy_inv_\d+_daily_sum", c)]
        if not ecols:
            continue
        idx = pd.to_datetime(df.iloc[:, 0], errors="coerce")
        e = df[ecols].sum(axis=1)  # sum inverters
        frames.append(pd.Series(e.values, index=idx))
    if not frames:
        return None
    s = pd.concat(frames).sort_index()
    s = s[~s.index.duplicated(keep="first")]
    s = s[s.index.notna()]
    s.name = "ac_energy_kwh"
    s.to_csv(cache)
    return s


# ---------------- NSRDB irradiance ----------------
def nsrdb_cell(lat, lon):
    return round(lat, 2), round(lon, 2)  # ~2 km grid dedupe


def pull_nsrdb_year(lat, lon, year, max_retry=4):
    clat, clon = nsrdb_cell(lat, lon)
    cache = NSRDB_DIR / f"{clat}_{clon}_{year}.csv"
    if cache.exists():
        return cache
    url = (f"{NSRDB_EP}?wkt=POINT({clon}%20{clat})&names={year}&interval=60&utc=false"
           f"&leap_day=true&email={API_EMAIL}&api_key={API_KEY}"
           f"&attributes=ghi,dni,dhi,air_temperature,wind_speed")
    for attempt in range(max_retry):
        r = requests.get(url, timeout=120)
        if r.status_code == 200 and r.text.startswith("Source"):
            cache.write_text(r.text)
            time.sleep(0.6)  # throttle < 2/s
            return cache
        if r.status_code in (429, 503):
            time.sleep(5 * (attempt + 1))
            continue
        # 400 = year out of NSRDB coverage; record empty sentinel
        if r.status_code == 400:
            return None
        time.sleep(2)
    return None


def load_nsrdb(cache_path):
    df = pd.read_csv(cache_path, skiprows=2)
    idx = pd.to_datetime(df[["Year", "Month", "Day", "Hour", "Minute"]])
    out = pd.DataFrame({
        "ghi": df["GHI"].values, "dni": df["DNI"].values, "dhi": df["DHI"].values,
        "temp_air": df["Temperature"].values, "wind_speed": df["Wind Speed"].values,
    }, index=idx)
    return out


# ---------------- expected energy model ----------------
def model_expected_daily(weather, lat, lon, tilt, az, pdc0):
    loc = location.Location(lat, lon)
    sp = loc.get_solarposition(weather.index)
    dni_extra = irradiance.get_extra_radiation(weather.index)
    poa = irradiance.get_total_irradiance(
        surface_tilt=tilt, surface_azimuth=az,
        solar_zenith=sp["apparent_zenith"], solar_azimuth=sp["azimuth"],
        dni=weather["dni"], ghi=weather["ghi"], dhi=weather["dhi"],
        dni_extra=dni_extra, model="haydavies",
    )
    poa_global = poa["poa_global"].fillna(0).clip(lower=0)
    tcell = temperature.sapm_cell(poa_global, weather["temp_air"], weather["wind_speed"],
                                  TEMP_MODEL["a"], TEMP_MODEL["b"], TEMP_MODEL["deltaT"])
    # PVWatts DC (kW); pdc0 in kW
    p_dc = pvsystem.pvwatts_dc(poa_global, tcell, pdc0, GAMMA_PDC)  # kW
    # hourly -> daily energy (kWh); interval is 60 min so kW*1h = kWh
    daily = p_dc.resample("D").sum()
    daily.index = daily.index.tz_localize(None) if daily.index.tz else daily.index
    return daily


# ---------------- PLR per system ----------------
def compute_plr(sid, lat, lon, tilt, az, pdc0):
    E = get_daily_energy(sid)
    if E is None or len(E) < 365 * 2:
        return {"system_id": sid, "status": "no_energy_or_short"}
    # uniform fleet observation window = NSRDB v4 coverage (2018-2023)
    E = E[(E.index.year >= WINDOW_START) & (E.index.year <= WINDOW_END)]
    if len(E) < 365 * 2:
        return {"system_id": sid, "status": "short_in_window", "n_days": int(len(E))}
    years = sorted(set(E.index.year))
    wx = []
    for y in years:
        cp = pull_nsrdb_year(lat, lon, y)
        if cp is not None:
            wx.append(load_nsrdb(cp))
    if not wx:
        return {"system_id": sid, "status": "no_nsrdb"}
    weather = pd.concat(wx).sort_index()
    weather = weather[~weather.index.duplicated(keep="first")]
    Emod = model_expected_daily(weather, lat, lon, tilt, az, pdc0)
    # align measured & modeled on date
    df = pd.DataFrame({"meas": E, "mod": Emod}).dropna()
    df = df[(df["mod"] > 0.1 * df["mod"].median())]  # drop near-zero model days (deep winter/no-sun artifact)
    pi = (df["meas"] / df["mod"])
    # sanity clip on PI (remove physically impossible spikes from meter resets)
    pi = pi[(pi > 0.2) & (pi < 1.8)]
    if len(pi) < 365 * 2:
        return {"system_id": sid, "status": "insufficient_aligned_days", "n_days": int(len(pi))}
    pi.name = "pi"
    # persist monthly PI trajectory (for RMD-SRC moment-flow + H2 regime classification)
    monthly = pd.DataFrame({
        "pi_mean": pi.resample("MS").mean(),
        "pi_std": pi.resample("MS").std(),
        "n": pi.resample("MS").count(),
    })
    monthly = monthly[monthly["n"] >= 5]  # require >=5 valid days/month
    monthly.to_csv(MONTHLY_PI_DIR / f"sys{sid}_monthly_pi.csv")
    try:
        rd, ci, info = degradation_year_on_year(pi, recenter=True, confidence_level=68.2)
    except Exception as e:
        return {"system_id": sid, "status": f"rdtools_err:{e}"}
    return {
        "system_id": sid, "status": "ok",
        "plr_pct_yr": float(rd), "ci_low": float(ci[0]), "ci_high": float(ci[1]),
        "n_days": int(len(pi)), "n_years": len(years),
        "pi_median": float(pi.median()),
        "first": str(pi.index.min().date()), "last": str(pi.index.max().date()),
    }


if __name__ == "__main__":
    import sys
    idx = pd.read_csv(ROOT / "data/raw/datasets/PVDAQ_systems_20250729.csv").iloc[:, :26]
    idx = idx.set_index("system_id")
    sid = int(sys.argv[1]) if len(sys.argv) > 1 else 10001
    row = idx.loc[sid]
    tilt = row["tilt"] if pd.notna(row["tilt"]) else min(abs(row["latitude"]), 30)
    az = row["azimuth"] if (pd.notna(row["azimuth"]) and row["azimuth"] >= 0) else 180
    res = compute_plr(sid, float(row["latitude"]), float(row["longitude"]),
                      float(tilt), float(az), float(row["dc_capacity_kW"]))
    print(json.dumps(res, indent=2))
