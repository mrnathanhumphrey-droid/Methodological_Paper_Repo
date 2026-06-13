"""Probe 3 feasibility — can rdtools SRR extract a credible soiling signal from PVDAQ daily PI?
Recomputes daily PI + daily POA insolation from cache for a few systems, runs soiling_srr,
reports soiling ratio + CI + insufficient-data flags. Diagnostic only; no pre-reg yet."""
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
from probe2_plr_pipeline import (get_daily_energy, load_nsrdb, pull_nsrdb_year, nsrdb_cell,
                                 model_expected_daily, WINDOW_START, WINDOW_END)
from pvlib import location, irradiance, temperature
import rdtools.soiling as rsoil

def daily_poa_insolation(weather, lat, lon, tilt, az):
    loc = location.Location(lat, lon)
    sp = loc.get_solarposition(weather.index)
    dni_extra = irradiance.get_extra_radiation(weather.index)
    poa = irradiance.get_total_irradiance(tilt, az, sp["apparent_zenith"], sp["azimuth"],
        dni=weather["dni"], ghi=weather["ghi"], dhi=weather["dhi"], dni_extra=dni_extra, model="haydavies")
    pg = poa["poa_global"].fillna(0).clip(lower=0)
    ins = (pg / 1000.0).resample("D").sum()  # kWh/m2/day (hourly)
    ins.index = ins.index.tz_localize(None) if ins.index.tz else ins.index
    return ins

def feas(sid, lat, lon, tilt, az, pdc0):
    E = get_daily_energy(sid)
    if E is None: return {"sid": sid, "status": "no_energy"}
    E = E[(E.index.year >= WINDOW_START) & (E.index.year <= WINDOW_END)]
    years = sorted(set(E.index.year))
    wx = [load_nsrdb(p) for y in years if (p := pull_nsrdb_year(lat, lon, y)) is not None]
    if not wx: return {"sid": sid, "status": "no_nsrdb"}
    weather = pd.concat(wx).sort_index(); weather = weather[~weather.index.duplicated()]
    Emod = model_expected_daily(weather, lat, lon, tilt, az, pdc0)
    ins = daily_poa_insolation(weather, lat, lon, tilt, az)
    df = pd.DataFrame({"meas": E, "mod": Emod, "ins": ins}).dropna()
    df = df[df["mod"] > 0.1 * df["mod"].median()]
    pi = (df["meas"] / df["mod"]); m = (pi > 0.2) & (pi < 1.8)
    pi, insol = pi[m], df["ins"][m]
    pi = pi / pi.quantile(0.98)  # normalize to ~1 at clean baseline (soiling_srr wants PI near 1)
    if len(pi) < 365 * 2: return {"sid": sid, "status": "short", "n": int(len(pi))}
    pi.index = pd.to_datetime(pi.index); insol.index = pd.to_datetime(insol.index)
    pi = pi.asfreq("D"); insol = insol.reindex(pi.index)
    try:
        sr, sr_ci, info = rsoil.soiling_srr(pi, insol, reps=200)
    except Exception as e:
        return {"sid": sid, "status": f"srr_err:{type(e).__name__}:{str(e)[:80]}", "n": int(len(pi))}
    return {"sid": sid, "status": "ok", "n": int(pi.notna().sum()),
            "soiling_ratio": float(sr), "sr_ci_low": float(sr_ci[0]), "sr_ci_high": float(sr_ci[1]),
            "soiling_loss_pct": float((1 - sr) * 100)}

if __name__ == "__main__":
    idx = pd.read_csv(ROOT / "data/raw/datasets/PVDAQ_systems_20250729.csv").iloc[:, :26].set_index("system_id")
    tests = {"H2_semiarid": [10068, 10112, 10196], "H3_moderate": [10000, 10001, 10003]}
    for grp, sids in tests.items():
        print(f"=== {grp} ===")
        for sid in sids:
            r = idx.loc[sid]
            tilt = r["tilt"] if pd.notna(r["tilt"]) else min(abs(r["latitude"]), 30)
            az = r["azimuth"] if (pd.notna(r["azimuth"]) and r["azimuth"] >= 0) else 180
            res = feas(sid, float(r["latitude"]), float(r["longitude"]), float(tilt), float(az), float(r["dc_capacity_kW"]))
            if res["status"] == "ok":
                print(f"  sys{sid}: soiling_loss={res['soiling_loss_pct']:.2f}% "
                      f"(SR={res['soiling_ratio']:.4f} CI[{res['sr_ci_low']:.4f},{res['sr_ci_high']:.4f}]) n={res['n']}")
            else:
                print(f"  sys{sid}: {res['status']}")
