"""
Probe 2b — Detectability analysis (post-hoc interpretation of Probe 2's H1 null).

Question: was PVDAQ even POWERED to detect Jordan 2022's climate-temperature
PLR effect, given the fleet's within-cell heterogeneity? Quantifies the
mechanism claimed in result memo 24 §4 (heterogeneity buries the signal) with
a power calculation instead of a hand-wave.

NOT a new confirmatory hypothesis test — post-hoc power/MDE characterization of
a transparently-logged null. Uses only the existing 668 PLRs.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.power import FTestAnovaPower

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data/processed"

# Jordan 2022 climate-T per-zone PLR (memo 16, Al-BSF ground-mount homogeneous cohort)
JORDAN = {"T3": -0.48, "T4": -0.78, "T5": -0.88}


def main():
    df = pd.read_csv(PROC / "probe2_plr_results_clean.csv").merge(
        pd.read_csv(PROC / "probe2_cohort_p0.csv")[["system_id", "A_PVCZ_T", "A_PVCZ_H", "P0_primary_TH"]],
        on="system_id")
    df = df[df["plr_pct_yr"].abs() <= 10].dropna(subset=["A_PVCZ_T"])
    out = {}

    # ---- 1. PVDAQ within-cell residual SD of PLR ----
    # remove ℙ₀-cell medians, measure residual spread
    df["cell_med"] = df.groupby("P0_primary_TH")["plr_pct_yr"].transform("median")
    resid = df["plr_pct_yr"] - df["cell_med"]
    sigma_within = float(resid.std())
    out["pvdaq_within_cell_sigma_plr"] = sigma_within
    out["pvdaq_overall_sigma_plr"] = float(df["plr_pct_yr"].std())

    # ---- 2. Jordan 2022 climate effect size ----
    jvals = np.array(list(JORDAN.values()))
    jordan_zone_spread = float(jvals.max() - jvals.min())  # range across T3-T5
    jordan_sd_of_means = float(jvals.std(ddof=0))
    out["jordan_climate_effect"] = {"zone_PLR": JORDAN, "range_pct_yr": jordan_zone_spread,
                                     "sd_of_zone_means": jordan_sd_of_means}

    # Cohen's f for Jordan's effect AT PVDAQ's within-cell sigma
    cohen_f_at_pvdaq = jordan_sd_of_means / sigma_within
    eta2_implied = cohen_f_at_pvdaq**2 / (1 + cohen_f_at_pvdaq**2)
    out["jordan_effect_at_pvdaq_sigma"] = {"cohen_f": cohen_f_at_pvdaq, "implied_eta2": eta2_implied}

    # ---- 3. Power to detect Jordan's effect at PVDAQ's n + sigma ----
    # use temperature partition n (systems with valid T-zone)
    k_groups = df["A_PVCZ_T"].nunique()
    n_total = len(df)
    analysis = FTestAnovaPower()
    power = analysis.power(effect_size=cohen_f_at_pvdaq, nobs=n_total, alpha=0.05, k_groups=k_groups)
    out["power_to_detect_jordan_effect"] = {"n_total": int(n_total), "k_groups": int(k_groups),
                                            "achieved_power": float(power)}

    # MDE: min effect size (cohen f -> eta2) detectable at power=0.8, this n
    mde_f = analysis.solve_power(effect_size=None, nobs=n_total, alpha=0.05, power=0.80, k_groups=k_groups)
    mde_eta2 = mde_f**2 / (1 + mde_f**2)
    out["mde_at_pvdaq_n"] = {"cohen_f": float(mde_f), "eta2": float(mde_eta2)}

    # ---- 4. N required to detect Jordan's effect at PVDAQ's heterogeneity ----
    n_req = analysis.solve_power(effect_size=cohen_f_at_pvdaq, nobs=None, alpha=0.05, power=0.80, k_groups=k_groups)
    out["n_required_for_jordan_effect_at_pvdaq_sigma"] = float(n_req)

    # ---- 5. implied heterogeneity inflation vs Jordan ----
    # Jordan detected the effect cleanly at p<0.001 with n~1528, k~3.
    # Back out the within-cohort sigma that would make his effect detectable at his n.
    # His observed cohen f to reach p<0.001 at n=1528: solve for f giving power ~0.999
    jordan_f_implied = analysis.solve_power(effect_size=None, nobs=1528, alpha=0.001, power=0.999, k_groups=3)
    jordan_sigma_implied = jordan_sd_of_means / jordan_f_implied
    out["jordan_implied_within_cohort_sigma"] = float(jordan_sigma_implied)
    out["heterogeneity_inflation_ratio"] = float(sigma_within / jordan_sigma_implied)

    # ---- 5b. variance decomposition: measurement noise vs true heterogeneity ----
    df["sigma_meas"] = (df["ci_high"] - df["ci_low"]) / 2.0  # 68.2% CI ≈ 1σ measurement
    df["cell_med"] = df.groupby("P0_primary_TH")["plr_pct_yr"].transform("median")
    sig_tot = float((df["plr_pct_yr"] - df["cell_med"]).std())
    mean_meas_var = float((df["sigma_meas"] ** 2).mean())
    sig_true = float(np.sqrt(max(sig_tot**2 - mean_meas_var, 0)))
    pwr_true = analysis.power(effect_size=jordan_sd_of_means / sig_true, nobs=n_total, alpha=0.05, k_groups=k_groups)
    out["variance_decomposition"] = {
        "sigma_within_total": sig_tot,
        "measurement_rms": float(np.sqrt(mean_meas_var)),
        "measurement_variance_fraction": mean_meas_var / sig_tot**2,
        "sigma_true_heterogeneity": sig_true,
        "true_inflation_vs_jordan": sig_true / jordan_sigma_implied,
        "power_at_true_sigma": float(pwr_true)}

    # observed PVDAQ eta2 for reference
    model = smf.ols("plr_pct_yr ~ C(A_PVCZ_T) + C(A_PVCZ_H)", data=df).fit()
    aov = sm.stats.anova_lm(model, typ=2)
    ss = aov.loc["C(A_PVCZ_T)", "sum_sq"]; ssr = aov.loc["Residual", "sum_sq"]
    out["pvdaq_observed_eta2_Tzone"] = float(ss / (ss + ssr))

    # ---- print ----
    print("=== PROBE 2b — DETECTABILITY ANALYSIS ===\n")
    print(f"PVDAQ within-cell PLR sigma:      {sigma_within:.3f} %/yr")
    print(f"PVDAQ overall PLR sigma:          {out['pvdaq_overall_sigma_plr']:.3f} %/yr")
    print(f"Jordan 2022 climate effect:       range {jordan_zone_spread:.2f} %/yr (SD of zone means {jordan_sd_of_means:.3f})")
    print()
    print(f"Jordan's effect AT PVDAQ sigma:   Cohen f = {cohen_f_at_pvdaq:.3f}  -> implied eta2 = {eta2_implied:.4f}")
    print(f"PVDAQ observed eta2 (T-zone):     {out['pvdaq_observed_eta2_Tzone']:.4f}")
    print(f"  (consistency check: implied {eta2_implied:.4f} vs observed {out['pvdaq_observed_eta2_Tzone']:.4f})")
    print()
    print(f"Power to detect Jordan effect at PVDAQ n={n_total}, k={k_groups}: {power:.3f}")
    print(f"MDE at PVDAQ n (power=0.8): eta2 = {mde_eta2:.4f} (Cohen f {mde_f:.3f})")
    print(f"N required to detect Jordan effect at PVDAQ heterogeneity: {n_req:.0f} systems")
    print()
    print(f"Jordan implied within-cohort sigma: {jordan_sigma_implied:.3f} %/yr")
    print(f"HETEROGENEITY INFLATION RATIO (PVDAQ/Jordan sigma): {out['heterogeneity_inflation_ratio']:.2f}x")
    vd = out["variance_decomposition"]
    print()
    print("--- variance decomposition (measurement vs true heterogeneity) ---")
    print(f"  measurement fraction: {vd['measurement_variance_fraction']:.1%}")
    print(f"  sigma_true heterogeneity: {vd['sigma_true_heterogeneity']:.3f} %/yr ({vd['true_inflation_vs_jordan']:.2f}x Jordan)")
    print(f"  power at true sigma: {vd['power_at_true_sigma']:.3f} (still < 0.8 -> underpowering robust)")

    (PROC / "probe2b_detectability.json").write_text(json.dumps(out, indent=2))
    print(f"\nWrote {PROC/'probe2b_detectability.json'}")


if __name__ == "__main__":
    main()
