"""Probe 14 — Monte Carlo cleaning ROI with stochastic rain + natural cleaning.

Generalizes Probe 13's deterministic ROI to include:
- Empirical day-of-year rain probability from DKA on-site weather
- Seasonal deposition (wet 0.173 %/day Oct-Mar; dry 0.128 %/day Apr-Sep, per Probe 5c)
- Saturating soiling model (deposition rate slows as soiling accumulates)
- Per-rain partial cleaning (calibrated to reproduce DKA observed 3.87 %/yr)
- Multiple operator-strategy classes (scheduled, opportunistic, threshold, mixed)

Calibration step: find rain-cleaning fraction f_rain such that net annual energy
loss matches DKA's 3.87 %/yr when running at ~3.5 operational cleanings/yr.
Then run all strategies against the calibrated rain process and compare costs.

Strategies:
1. Pure-scheduled: clean every T days, T in {60, 90, 120, 156, 180, 250, 365}
2. Pure-opportunistic: clean exactly K days after each rain >=1mm, K in {0,1,2,3,4,5,7}
3. Mixed: opportunistic with minimum-interval constraint (avoid back-to-back cleanings)
4. Soiling-threshold: clean when current soiling > X%, X in {5, 8, 10, 15}

For each strategy, run N=2000 simulated years and report cost distribution.

Honest framing: this is a substrate-grounded design exercise to compare
strategy CLASSES, not an exact prediction. Calibration pins one free parameter;
others (saturation level, exact deposition seasonality cutoff) are choices.
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
WEATHER = ROOT / "data/raw/dka/101-Site_DKA-WeatherStation.csv"
OUT = ROOT / "data/processed/probe14_monte_carlo_strategies.csv"
OUT_CALIB = ROOT / "data/processed/probe14_calibration.json"

# Inputs
YIELD_KWH_KW_DAY = 5.5
PRICE_USD_KWH = 0.10
CLEANING_COST_USD_KW = 10.0
SOIL_SAT = 0.25                   # saturation level: 25% loss max
RAIN_THR_MM = 1.0
N_SIMS = 2000
SEED = 20260601

# Seasonal deposition (per Probe 5c)
# Wet season Oct-Mar (months 10-12, 1-3): 0.173 %/day
# Dry season Apr-Sep (months 4-9): 0.128 %/day
DEPOSITION_WET_PCT_DAY = 0.173
DEPOSITION_DRY_PCT_DAY = 0.128


def load_rain_empirical():
    """Return per-DOY empirical rain probability based on full DKA weather history."""
    df = pd.read_csv(WEATHER, usecols=["timestamp", "Weather_Daily_Rainfall"],
                     engine="python", on_bad_lines="skip")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["Weather_Daily_Rainfall"] = pd.to_numeric(df["Weather_Daily_Rainfall"], errors="coerce")
    df = df.dropna().set_index("timestamp").sort_index()
    daily = df["Weather_Daily_Rainfall"].resample("D").max().fillna(0)
    is_rainy = (daily >= RAIN_THR_MM).astype(int)
    doy_prob = is_rainy.groupby(is_rainy.index.dayofyear).mean()
    # Make sure all 366 DOYs are covered; fill any missing with overall mean
    overall_p = float(is_rainy.mean())
    doy_prob = doy_prob.reindex(range(1, 367)).fillna(overall_p)
    return doy_prob.values, overall_p


def simulate_year(doy_rain_prob, strategy, rng, calibration):
    """Simulate one 365-day year. strategy is dict with keys:
       'kind': scheduled/opportunistic/threshold/mixed
       parameters per kind
    Returns dict with annual_energy_loss_pct, n_cleanings, n_rain_events."""
    f_rain = calibration["f_rain"]   # fractional soiling reduction per rain event
    soil = 0.0                        # current soiling loss fraction (0 = clean)
    energy_loss_total = 0.0
    n_cleanings = 0
    n_rain = 0
    days_since_clean = 999
    days_since_rain = 999
    cumulative_rain_dep_for_threshold = 0.0  # only for threshold strategies

    for day in range(1, 366):
        # Deposition (seasonal)
        month = ((day - 1) // 30) + 1
        if month in [10, 11, 12, 1, 2, 3]:
            r = DEPOSITION_WET_PCT_DAY / 100.0
        else:
            r = DEPOSITION_DRY_PCT_DAY / 100.0
        # Saturating: ds/dt = r * (1 - s/sat)
        soil = soil + r * (1.0 - min(soil / SOIL_SAT, 1.0))
        soil = min(soil, SOIL_SAT)

        # Energy lost today
        energy_loss_today = soil * YIELD_KWH_KW_DAY    # kWh lost per kW today
        energy_loss_total += energy_loss_today

        # Rain event?
        p_rain = doy_rain_prob[day - 1]
        if rng.random() < p_rain:
            n_rain += 1
            days_since_rain = 0
            # Partial cleaning by rain
            soil = soil * (1.0 - f_rain)
        else:
            days_since_rain += 1

        days_since_clean += 1

        # Operator cleaning decision (END of day, after deposition + rain)
        clean_today = False
        if strategy["kind"] == "scheduled":
            if days_since_clean >= strategy["T"]:
                clean_today = True
        elif strategy["kind"] == "opportunistic":
            if days_since_rain == strategy["lag"] and days_since_clean >= strategy.get("min_interval", 0):
                clean_today = True
        elif strategy["kind"] == "threshold":
            if soil >= strategy["threshold"] / 100.0:
                clean_today = True
        elif strategy["kind"] == "mixed_opp_min":
            if days_since_rain == strategy["lag"] and days_since_clean >= strategy["min_interval"]:
                clean_today = True
        elif strategy["kind"] == "none":
            pass

        if clean_today:
            soil = 0.0
            n_cleanings += 1
            days_since_clean = 0

    # Annual loss as fraction
    annual_energy_baseline = YIELD_KWH_KW_DAY * 365
    annual_loss_pct = energy_loss_total / annual_energy_baseline * 100
    return {
        "annual_loss_pct": annual_loss_pct,
        "n_cleanings": n_cleanings,
        "n_rain": n_rain,
        "energy_loss_kwh_kw": energy_loss_total,
    }


def run_strategy(doy_rain_prob, strategy, n_sims, rng, calibration):
    losses = []
    n_cs = []
    n_rs = []
    for _ in range(n_sims):
        r = simulate_year(doy_rain_prob, strategy, rng, calibration)
        losses.append(r["annual_loss_pct"])
        n_cs.append(r["n_cleanings"])
        n_rs.append(r["n_rain"])
    losses = np.array(losses)
    n_cs = np.array(n_cs)
    # Cost per kW per year
    cleaning_cost = n_cs * CLEANING_COST_USD_KW
    soiling_cost = (losses / 100.0) * YIELD_KWH_KW_DAY * 365 * PRICE_USD_KWH
    total = cleaning_cost + soiling_cost
    return {
        "loss_mean": float(losses.mean()), "loss_sd": float(losses.std()),
        "loss_p05": float(np.percentile(losses, 5)), "loss_p95": float(np.percentile(losses, 95)),
        "n_clean_mean": float(n_cs.mean()), "n_clean_sd": float(n_cs.std()),
        "n_rain_mean": float(np.mean(n_rs)),
        "cleaning_cost_mean": float(cleaning_cost.mean()),
        "soiling_cost_mean": float(soiling_cost.mean()),
        "total_cost_mean": float(total.mean()), "total_cost_sd": float(total.std()),
        "total_cost_p05": float(np.percentile(total, 5)),
        "total_cost_p95": float(np.percentile(total, 95)),
    }


def calibrate_f_rain(doy_rain_prob, target_loss_pct=3.87, target_n_clean=3.5, n_sims=500):
    """Find f_rain such that with ~3.5 scheduled cleanings/yr, mean annual loss = 3.87%."""
    # Use scheduled T=104 days (~3.5/yr) to match DKA observed regime
    # Test f_rain in [0.05, 0.95]; bisect on mean loss
    test_strategy = {"kind": "scheduled", "T": 104}
    rng = np.random.default_rng(SEED + 999)
    def loss_at(f):
        cal = {"f_rain": f}
        sub_rng = np.random.default_rng(SEED + 100)
        losses = []
        for _ in range(n_sims):
            r = simulate_year(doy_rain_prob, test_strategy, sub_rng, cal)
            losses.append(r["annual_loss_pct"])
        return float(np.mean(losses))
    lo, hi = 0.05, 0.95
    f_lo, f_hi = loss_at(lo), loss_at(hi)
    print(f"  calibration bracket: f=0.05 -> loss {f_lo:.2f}%, f=0.95 -> loss {f_hi:.2f}%")
    # Target is between them: f_lo > target (too little cleaning), f_hi < target (too much)
    if not (f_hi <= target_loss_pct <= f_lo):
        print(f"  WARNING: target {target_loss_pct}% not bracketed by f_rain in [{lo},{hi}]")
        # Pick boundary closest
        if abs(f_lo - target_loss_pct) < abs(f_hi - target_loss_pct):
            return lo, f_lo
        else:
            return hi, f_hi
    # Bisect
    for _ in range(20):
        mid = (lo + hi) / 2
        f_mid = loss_at(mid)
        if f_mid > target_loss_pct:
            lo = mid; f_lo = f_mid
        else:
            hi = mid; f_hi = f_mid
        if abs(f_mid - target_loss_pct) < 0.05:
            return mid, f_mid
    return (lo + hi) / 2, loss_at((lo + hi) / 2)


def main():
    print("=== PROBE 14: Monte Carlo cleaning ROI ===\n")
    print("Loading DKA empirical rain DOY probability...")
    doy_rain_prob, overall_p = load_rain_empirical()
    print(f"  overall rain probability: {overall_p:.3f} ({overall_p * 365:.0f} rainy days/yr)")
    print(f"  DOY distribution: min={doy_rain_prob.min():.3f}, max={doy_rain_prob.max():.3f}, mean={doy_rain_prob.mean():.3f}\n")

    print("Calibrating f_rain to reproduce DKA 3.87%/yr at ~3.5 operational/yr...")
    f_rain, achieved_loss = calibrate_f_rain(doy_rain_prob)
    print(f"  Calibrated f_rain = {f_rain:.3f} (each rain event removes {f_rain*100:.1f}% of current soiling)")
    print(f"  Achieved mean loss at T=104d schedule: {achieved_loss:.2f}% (target 3.87%)")
    calibration = {"f_rain": f_rain, "achieved_loss_pct": achieved_loss,
                   "target_loss_pct": 3.87, "target_n_clean_per_yr": 3.5}
    with open(OUT_CALIB, "w") as f:
        json.dump(calibration, f, indent=2)

    rng = np.random.default_rng(SEED)

    # Define strategies
    strategies = []
    # No cleaning at all (baseline)
    strategies.append(("NONE", {"kind": "none"}))
    # Pure-scheduled
    for T in [60, 90, 120, 156, 180, 250, 365]:
        strategies.append((f"sched_T={T}d", {"kind": "scheduled", "T": T}))
    # Pure-opportunistic (clean K days after each rain)
    for K in [0, 1, 2, 3, 4, 5, 7]:
        strategies.append((f"opp_lag={K}d", {"kind": "opportunistic", "lag": K}))
    # Mixed: opportunistic with minimum interval (lag=3, min_interval={30,60,90})
    for mi in [30, 60, 90]:
        strategies.append((f"opp_lag=3d_min={mi}d", {"kind": "mixed_opp_min", "lag": 3, "min_interval": mi}))
    # Soiling-threshold
    for thr in [3, 5, 8, 10, 15]:
        strategies.append((f"threshold={thr}%", {"kind": "threshold", "threshold": thr}))

    print(f"\nRunning {len(strategies)} strategies x {N_SIMS} simulated years...\n")
    print(f"{'strategy':<25s} {'loss%mean':>10s} {'loss%p05/p95':>14s} {'N_clean':>8s} {'TOTAL$/kW/yr':>15s} {'cost p05/p95':>15s}")
    rows = []
    for name, strat in strategies:
        r = run_strategy(doy_rain_prob, strat, N_SIMS, rng, calibration)
        rows.append({"strategy": name, **strat, **r})
        print(f"  {name:<23s} {r['loss_mean']:>8.2f}  [{r['loss_p05']:.2f}/{r['loss_p95']:.2f}] {r['n_clean_mean']:>7.2f} ${r['total_cost_mean']:>11.2f} [${r['total_cost_p05']:.0f}/${r['total_cost_p95']:.0f}]")

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    print(f"\nWrote {OUT.name}")

    # Verdict
    print("\n=== VERDICT ===")
    best = df.loc[df["total_cost_mean"].idxmin()]
    print(f"Lowest mean total cost: {best['strategy']} -> ${best['total_cost_mean']:.2f}/kW/yr "
          f"(cleaning ${best['cleaning_cost_mean']:.2f} + soiling ${best['soiling_cost_mean']:.2f}), "
          f"N_clean={best['n_clean_mean']:.2f}/yr")
    # Compare opportunistic lag=2,3,4 to scheduled near optimum
    print("\n=== KEY COMPARISON: opportunistic vs scheduled-near-optimum ===")
    for sname in ["sched_T=156d", "sched_T=180d", "opp_lag=2d", "opp_lag=3d", "opp_lag=4d",
                  "opp_lag=3d_min=30d", "opp_lag=3d_min=60d", "opp_lag=3d_min=90d",
                  "threshold=8%", "threshold=10%"]:
        r = df[df["strategy"] == sname]
        if len(r):
            r = r.iloc[0]
            print(f"  {sname:<25s} cost=${r['total_cost_mean']:>6.2f}/kW/yr (loss {r['loss_mean']:.2f}%, N={r['n_clean_mean']:.2f}/yr)")


if __name__ == "__main__":
    main()
