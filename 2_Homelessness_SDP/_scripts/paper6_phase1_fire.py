"""
Paper 6 Phase 1 — fire PRE_REG_022 residue-class Stan/PyMC model.
Fit baseline (no typology) vs residue-class (Papers 2 + 4 typology) hierarchical models.
LOO-CV comparison via arviz.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import pymc as pm
import arviz as az

sys.stdout.reconfigure(encoding="utf-8")

print("=" * 80)
print("PAPER 6 PHASE 1 — Residue-class Stan/PyMC fit (PRE_REG_022)")
print("=" * 80)

# ============================================================================
# Build country-year-hazard panel
# ============================================================================
print("\n[1/5] Building country-year-hazard panel...")

GIDD_DIS = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx")
GIDD_CONF = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Conflict_Violence_Disasters.xlsx")

d = pd.read_excel(GIDD_DIS)
d.columns = [c.strip() for c in d.columns]
d["idp"] = pd.to_numeric(d["Disaster Internal Displacements"], errors="coerce")
d = d[d["Year"].between(2008, 2024)].dropna(subset=["idp", "ISO3", "Year", "Hazard Type"])
d_panel = d.groupby(["ISO3", "Year", "Hazard Type"])["idp"].sum().reset_index()
d_panel.columns = ["country", "year", "channel", "displacement"]

c = pd.read_excel(GIDD_CONF)
c.columns = [col.strip() for col in c.columns]
c["idp"] = pd.to_numeric(c["Conflict Internal Displacements"], errors="coerce")
c = c[c["Year"].between(2008, 2024)].dropna(subset=["idp", "ISO3", "Year"])
c_panel = c.groupby(["ISO3", "Year"])["idp"].sum().reset_index()
c_panel.columns = ["country", "year", "displacement"]
c_panel["channel"] = "Conflict"

panel = pd.concat([d_panel, c_panel], ignore_index=True)
panel = panel[panel["displacement"] > 0]
# Keep only main channels
main_channels = ["Flood", "Storm", "Earthquake", "Drought", "Conflict"]
panel = panel[panel["channel"].isin(main_channels)]
print(f"  Panel rows: {len(panel)}")
print(f"  Countries: {panel['country'].nunique()}")
print(f"  Channels: {panel['channel'].unique()}")

# ============================================================================
# Class assignments (Papers 2 + 4)
# ============================================================================
print("\n[2/5] Applying Papers 2 + 4 class assignments...")

# Paper 2 disaster regimes
disaster_regime = {
    "PAK": "R1", "THA": "R1",
    "IND": "R2",
    "MOZ": "R3", "VNM": "R3",
    "USA": "R3a", "CUB": "R3a", "DOM": "R3a", "FJI": "R3a", "VUT": "R3a", "PRI": "R3a",
    "PHL": "R3b",
    "BRA": "R4a", "IDN": "R4a", "PER": "R4a", "IRN": "R4a", "AFG": "R4a",
    "BGD": "R4b", "JPN": "R4b", "MMR": "R4b",
    "MEX": "R4c", "CHN": "R4c", "GRC": "R4c",
    "HTI": "R6", "NPL": "R6", "TUR": "R6", "CHL": "R6", "ECU": "R6", "ITA": "R6",
}

# Paper 4 conflict types
conflict_type = {
    "ETH": "A", "UKR": "A", "RUS": "A", "ISR": "A", "PAK": "A", "EGY": "A",
    "COD": "B", "MOZ": "B", "HTI": "B",
    "MLI": "C", "LBN": "C", "SSD": "C", "COL": "C", "IRN": "C",
    "MEX": "D", "BRA": "D", "ECU": "D",
    "AFG": "E", "YEM": "E", "NGA": "E", "SDN": "E", "BFA": "E", "SYR": "E", "SOM": "E",
    "MMR": "E", "AZE": "E", "IRQ": "E", "CMR": "E", "CAF": "E", "IND": "E", "PHL": "E",
    "TCD": "E", "KEN": "E", "LBY": "E",
}

def assign_class(row):
    if row["channel"] == "Conflict":
        return f"Conflict_{conflict_type.get(row['country'], 'other')}"
    else:
        regime = disaster_regime.get(row["country"], "other")
        return f"Disaster_{regime}"

panel["class"] = panel.apply(assign_class, axis=1)

# Filter to country-year-channel rows with assigned classes
panel_classified = panel[~panel["class"].str.endswith("_other")].copy()
print(f"  Classified rows: {len(panel_classified)}")
print(f"  Unique classes: {panel_classified['class'].nunique()}")
print(f"  Class counts:")
for cls, count in panel_classified["class"].value_counts().items():
    print(f"    {cls}: {count}")

# ============================================================================
# Prepare data for PyMC
# ============================================================================
print("\n[3/5] Preparing PyMC tensors...")

panel_classified["log_disp"] = np.log1p(panel_classified["displacement"])
# Country / year / channel / class indices
country_idx, countries = pd.factorize(panel_classified["country"])
year_idx, years = pd.factorize(panel_classified["year"])
channel_idx, channels = pd.factorize(panel_classified["channel"])
class_idx, classes = pd.factorize(panel_classified["class"])
n_countries = len(countries)
n_years = len(years)
n_channels = len(channels)
n_classes = len(classes)
n_obs = len(panel_classified)
print(f"  n_countries={n_countries}, n_years={n_years}, n_channels={n_channels}, n_classes={n_classes}, n_obs={n_obs}")

y = panel_classified["log_disp"].values

# ============================================================================
# Baseline model: country + year + channel random effects only
# ============================================================================
print("\n[4/5] Fitting BASELINE model (no typology)...")

with pm.Model() as baseline_model:
    # Hyperpriors
    alpha = pm.Normal("alpha", 0, 5)
    sigma_country = pm.HalfNormal("sigma_country", 2)
    sigma_year = pm.HalfNormal("sigma_year", 2)
    sigma_channel = pm.HalfNormal("sigma_channel", 2)
    sigma_y = pm.HalfNormal("sigma_y", 2)

    # Non-centered random effects
    z_country = pm.Normal("z_country", 0, 1, shape=n_countries)
    z_year = pm.Normal("z_year", 0, 1, shape=n_years)
    z_channel = pm.Normal("z_channel", 0, 1, shape=n_channels)
    beta_country = pm.Deterministic("beta_country", z_country * sigma_country)
    beta_year = pm.Deterministic("beta_year", z_year * sigma_year)
    beta_channel = pm.Deterministic("beta_channel", z_channel * sigma_channel)

    mu = alpha + beta_country[country_idx] + beta_year[year_idx] + beta_channel[channel_idx]
    obs = pm.Normal("obs", mu=mu, sigma=sigma_y, observed=y)

    print("  Sampling baseline (cores=1 for Windows reliability)...")
    idata_baseline = pm.sample(
        1000,
        tune=1000,
        chains=2,
        cores=1,
        target_accept=0.9,
        progressbar=True,
        idata_kwargs={"log_likelihood": True},
    )

print("  Baseline sample summary:")
print(az.summary(idata_baseline, var_names=["alpha", "sigma_country", "sigma_year", "sigma_channel", "sigma_y"]))

# ============================================================================
# Residue-class model: same + class effect
# ============================================================================
print("\n[5/5] Fitting RESIDUE-CLASS model (Papers 2 + 4 typology)...")

with pm.Model() as rc_model:
    alpha = pm.Normal("alpha", 0, 5)
    sigma_country = pm.HalfNormal("sigma_country", 2)
    sigma_year = pm.HalfNormal("sigma_year", 2)
    sigma_channel = pm.HalfNormal("sigma_channel", 2)
    sigma_class = pm.HalfNormal("sigma_class", 2)
    sigma_y = pm.HalfNormal("sigma_y", 2)

    z_country = pm.Normal("z_country", 0, 1, shape=n_countries)
    z_year = pm.Normal("z_year", 0, 1, shape=n_years)
    z_channel = pm.Normal("z_channel", 0, 1, shape=n_channels)
    z_class = pm.Normal("z_class", 0, 1, shape=n_classes)
    beta_country = pm.Deterministic("beta_country", z_country * sigma_country)
    beta_year = pm.Deterministic("beta_year", z_year * sigma_year)
    beta_channel = pm.Deterministic("beta_channel", z_channel * sigma_channel)
    beta_class = pm.Deterministic("beta_class", z_class * sigma_class)

    mu = (alpha + beta_country[country_idx] + beta_year[year_idx]
          + beta_channel[channel_idx] + beta_class[class_idx])
    obs = pm.Normal("obs", mu=mu, sigma=sigma_y, observed=y)

    print("  Sampling residue-class (cores=1 for Windows reliability)...")
    idata_rc = pm.sample(
        1000,
        tune=1000,
        chains=2,
        cores=1,
        target_accept=0.9,
        progressbar=True,
        idata_kwargs={"log_likelihood": True},
    )

print("  Residue-class sample summary:")
print(az.summary(idata_rc, var_names=["alpha", "sigma_country", "sigma_year",
                                       "sigma_channel", "sigma_class", "sigma_y"]))

# ============================================================================
# LOO-CV comparison
# ============================================================================
print("\n" + "=" * 80)
print("LOO-CV COMPARISON (PRE_REG_022 H1)")
print("=" * 80)

loo_baseline = az.loo(idata_baseline)
loo_rc = az.loo(idata_rc)
print(f"\nBaseline LOO-CV elpd_loo: {loo_baseline.elpd:.2f} ± {loo_baseline.se:.2f}")
print(f"Residue-class LOO-CV elpd_loo: {loo_rc.elpd:.2f} ± {loo_rc.se:.2f}")

# Compare
compare = az.compare({"baseline": idata_baseline, "residue_class": idata_rc})
print("\nModel comparison (LOO-CV):")
print(compare)

delta_loo = loo_rc.elpd - loo_baseline.elpd
print(f"\nΔLOO (residue_class - baseline) = {delta_loo:.2f}")
print(f"  Predicted: ≥ 5 (PRE_REG_022 H1)")
print(f"  Status: {'SUPPORTED' if delta_loo >= 5 else 'NOT MET' if delta_loo >= 0 else 'WALKED BACK'}")

# F1 check
print(f"\nF1 (ΔLOO < 5): {'FIRED' if delta_loo < 5 else 'NOT FIRED'}")

# ============================================================================
# Save
# ============================================================================
import json
results = {
    "baseline_elpd_loo": float(loo_baseline.elpd),
    "baseline_se": float(loo_baseline.se),
    "residue_class_elpd_loo": float(loo_rc.elpd),
    "residue_class_se": float(loo_rc.se),
    "delta_loo": float(delta_loo),
    "n_obs": int(n_obs),
    "n_countries": int(n_countries),
    "n_classes": int(n_classes),
    "h1_threshold": 5,
    "h1_supported": bool(delta_loo >= 5),
    "compare_table": compare.to_dict() if hasattr(compare, "to_dict") else str(compare),
}
Path("D:/IDP/analysis/paper6_phase1_loo_results_2026_05_27.json").write_text(
    json.dumps(results, indent=2), encoding="utf-8"
)
print(f"\nResults saved: D:/IDP/analysis/paper6_phase1_loo_results_2026_05_27.json")
