"""
Paper 6 Phase 1 — typology ABLATION.
Compare 4 models:
  M0 baseline (no typology)
  M1 + disaster regimes only (Paper 2)
  M2 + conflict types only (Paper 4)
  M3 + both (combined residue-class, the headline)

LOO-CV pairwise to attribute the +13.66 ΔLOO between the two typologies.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az

sys.stdout.reconfigure(encoding="utf-8")
print("=" * 80)
print("PAPER 6 ABLATION — disaster-only vs conflict-only vs combined")
print("=" * 80)

# ============================================================================
# Reuse the panel-construction + class-assignment from paper6_phase1_fire.py
# ============================================================================
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
main_channels = ["Flood", "Storm", "Earthquake", "Drought", "Conflict"]
panel = panel[panel["channel"].isin(main_channels)]

# Exact same assignments as paper6_phase1_fire.py (DO NOT REORDER)
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
conflict_type = {
    "ETH": "A", "UKR": "A", "RUS": "A", "ISR": "A", "PAK": "A", "EGY": "A",
    "COD": "B", "MOZ": "B", "HTI": "B",
    "MLI": "C", "LBN": "C", "SSD": "C", "COL": "C", "IRN": "C",
    "MEX": "D", "BRA": "D", "ECU": "D",
    "AFG": "E", "YEM": "E", "NGA": "E", "SDN": "E", "BFA": "E", "SYR": "E", "SOM": "E",
    "MMR": "E", "AZE": "E", "IRQ": "E", "CMR": "E", "CAF": "E", "IND": "E", "PHL": "E",
    "TCD": "E", "KEN": "E", "LBY": "E",
}


def assign_class_combined(row):
    if row["channel"] == "Conflict":
        return f"Conflict_{conflict_type[row['country']]}" if row["country"] in conflict_type else None
    return f"Disaster_{disaster_regime[row['country']]}" if row["country"] in disaster_regime else None


def assign_class_disaster_only(row):
    if row["channel"] == "Conflict":
        return None
    return f"Disaster_{disaster_regime[row['country']]}" if row["country"] in disaster_regime else None


def assign_class_conflict_only(row):
    if row["channel"] == "Conflict":
        return f"Conflict_{conflict_type[row['country']]}" if row["country"] in conflict_type else None
    return None


panel["class_combined"] = panel.apply(assign_class_combined, axis=1)
panel["class_disaster"] = panel.apply(assign_class_disaster_only, axis=1)
panel["class_conflict"] = panel.apply(assign_class_conflict_only, axis=1)

# Filter to combined-classified rows (same n=1239 as headline)
df = panel[panel["class_combined"].notna()].copy()
df["log_disp"] = np.log1p(df["displacement"])  # log(1+x) — matches headline fit

country_idx, _ = pd.factorize(df["country"])
year_idx, _ = pd.factorize(df["year"])
channel_idx, _ = pd.factorize(df["channel"])

# For ablation models, we need to handle the "unclassified" case:
# - Disaster-only: replace conflict rows with a single "Conflict_NA" sentinel class
# - Conflict-only: replace disaster rows with a single "Disaster_NA" sentinel class
df["class_d_only"] = df["class_disaster"].fillna("Conflict_NA")
df["class_c_only"] = df["class_conflict"].fillna("Disaster_NA")

class_combined_idx, class_combined_labels = pd.factorize(df["class_combined"])
class_d_idx, class_d_labels = pd.factorize(df["class_d_only"])
class_c_idx, class_c_labels = pd.factorize(df["class_c_only"])

n_countries = df["country"].nunique()
n_years = df["year"].nunique()
n_channels = df["channel"].nunique()
n_class_combined = len(class_combined_labels)
n_class_d = len(class_d_labels)
n_class_c = len(class_c_labels)
n_obs = len(df)
y = df["log_disp"].values

print(f"\nPanel: n_obs={n_obs}, countries={n_countries}, years={n_years}, channels={n_channels}")
print(f"Class counts: combined={n_class_combined}, disaster-only={n_class_d}, conflict-only={n_class_c}")


def fit_model(name, with_class=False, class_idx=None, n_classes=None):
    """Hierarchical fit. with_class=False is the baseline; True adds one class effect."""
    print(f"\n--- Fitting {name} ---")
    with pm.Model() as m:
        alpha = pm.Normal("alpha", 0, 5)
        sigma_country = pm.HalfNormal("sigma_country", 2)
        sigma_year = pm.HalfNormal("sigma_year", 2)
        sigma_channel = pm.HalfNormal("sigma_channel", 2)
        sigma_y = pm.HalfNormal("sigma_y", 2)
        z_country = pm.Normal("z_country", 0, 1, shape=n_countries)
        z_year = pm.Normal("z_year", 0, 1, shape=n_years)
        z_channel = pm.Normal("z_channel", 0, 1, shape=n_channels)
        beta_country = pm.Deterministic("beta_country", z_country * sigma_country)
        beta_year = pm.Deterministic("beta_year", z_year * sigma_year)
        beta_channel = pm.Deterministic("beta_channel", z_channel * sigma_channel)
        mu = alpha + beta_country[country_idx] + beta_year[year_idx] + beta_channel[channel_idx]
        if with_class:
            sigma_class = pm.HalfNormal("sigma_class", 2)
            z_class = pm.Normal("z_class", 0, 1, shape=n_classes)
            beta_class = pm.Deterministic("beta_class", z_class * sigma_class)
            mu = mu + beta_class[class_idx]
        pm.Normal("obs", mu=mu, sigma=sigma_y, observed=y)
        idata = pm.sample(
            1000, tune=1000, chains=2, cores=1,
            target_accept=0.92, progressbar=True,
            idata_kwargs={"log_likelihood": True},
        )
    return idata


m0 = fit_model("M0 baseline", with_class=False)
m1 = fit_model("M1 + disaster only", with_class=True, class_idx=class_d_idx, n_classes=n_class_d)
m2 = fit_model("M2 + conflict only", with_class=True, class_idx=class_c_idx, n_classes=n_class_c)
m3 = fit_model("M3 + both", with_class=True, class_idx=class_combined_idx, n_classes=n_class_combined)

print("\n" + "=" * 80)
print("LOO-CV ABLATION")
print("=" * 80)

loo_results = {}
for name, idata in [("baseline", m0), ("disaster_only", m1), ("conflict_only", m2), ("both", m3)]:
    loo = az.loo(idata)
    loo_results[name] = {"elpd": float(loo.elpd), "se": float(loo.se)}
    print(f"{name:>15s}: elpd_loo = {loo.elpd:+.2f} ± {loo.se:.2f}")

compare = az.compare({"baseline": m0, "disaster_only": m1, "conflict_only": m2, "both": m3})
print("\nModel comparison:")
print(compare)

base = loo_results["baseline"]["elpd"]
print("\nΔLOO vs baseline:")
for name in ["disaster_only", "conflict_only", "both"]:
    d = loo_results[name]["elpd"] - base
    print(f"  {name:>15s}: {d:+.2f}")

results = {
    "loo_results": loo_results,
    "delta_loo_vs_baseline": {
        name: loo_results[name]["elpd"] - base
        for name in ["disaster_only", "conflict_only", "both"]
    },
    "n_obs": n_obs,
    "n_class_disaster_only": n_class_d,
    "n_class_conflict_only": n_class_c,
    "n_class_combined": n_class_combined,
    "compare_table": compare.to_dict() if hasattr(compare, "to_dict") else str(compare),
}
Path("D:/IDP/analysis/paper6_phase1_ablation_2026_05_27.json").write_text(
    json.dumps(results, indent=2), encoding="utf-8"
)
print("\nSaved: D:/IDP/analysis/paper6_phase1_ablation_2026_05_27.json")
