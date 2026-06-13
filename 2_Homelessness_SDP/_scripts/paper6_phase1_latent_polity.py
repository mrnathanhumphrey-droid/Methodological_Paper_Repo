"""
Paper 6 — Latent-covariate test, ROUND 2 (state-fragility / Polity).

WDI-only latent test (round 1) rejected the demographic-exposure hypothesis
(WDI covariates only absorbed +1.28 of the +12.64 typology lift).

Round 2 tests state-fragility / democratic-institutions hypothesis using
Polity5 polity2 (−10 autocracy to +10 democracy) as the country-level proxy.
Also adds Polity 'durable' (years since last regime change) as a second
fragility-axis covariate.

Models:
  M0 baseline
  M1 baseline + polity2 + durable
  M2 baseline + combined typology (headline)
  M3 baseline + polity covariates + combined typology
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az

sys.stdout.reconfigure(encoding="utf-8")
print("=" * 80)
print("PAPER 6 LATENT TEST — POLITY (state-fragility / democratic institutions)")
print("=" * 80)

# --- Panel construction (matches headline) ---
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

# Typology (matches headline)
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


def assign_class(row):
    if row["channel"] == "Conflict":
        return f"Conflict_{conflict_type.get(row['country'], 'other')}"
    return f"Disaster_{disaster_regime.get(row['country'], 'other')}"


panel["class"] = panel.apply(assign_class, axis=1)
panel = panel[~panel["class"].str.endswith("_other")].copy()

# --- Polity5 covariates ---
print("\n--- Loading Polity5 covariates ---")
poli = pd.read_excel("D:/IDP/data/polity5/p5v2018.xls")
# Special codes for missing: -66, -77, -88 → NaN
for col in ["polity2", "durable"]:
    poli[col] = pd.to_numeric(poli[col], errors="coerce")
    poli.loc[poli[col].isin([-66, -77, -88]), col] = np.nan
# Average polity2 + durable per country across 2008-2020
poli_recent = poli[poli["year"].between(2008, 2020)]
poli_country = (
    poli_recent.groupby("scode", as_index=False)
    .agg(polity2=("polity2", "mean"), durable=("durable", "mean"))
)
print(f"  polity2 country coverage: {poli_country['polity2'].notna().sum()} countries")
# scode in Polity ~ ISO3 (e.g., AFG, COD, USA)

# Map onto panel
poli_map_p2 = dict(zip(poli_country["scode"], poli_country["polity2"]))
poli_map_dur = dict(zip(poli_country["scode"], poli_country["durable"]))
panel["polity2"] = panel["country"].map(poli_map_p2)
panel["durable"] = panel["country"].map(poli_map_dur)

before = len(panel)
panel = panel.dropna(subset=["polity2", "durable"])
print(f"  dropped {before - len(panel)} rows for missing Polity (n={len(panel)} remaining)")
# Standardize
for col in ["polity2", "durable"]:
    panel[col] = (panel[col] - panel[col].mean()) / panel[col].std()

panel["log_disp"] = np.log1p(panel["displacement"])
country_idx, _ = pd.factorize(panel["country"])
year_idx, _ = pd.factorize(panel["year"])
channel_idx, _ = pd.factorize(panel["channel"])
class_idx, _ = pd.factorize(panel["class"])
n_countries = panel["country"].nunique()
n_years = panel["year"].nunique()
n_channels = panel["channel"].nunique()
n_classes = panel["class"].nunique()
n_obs = len(panel)
y = panel["log_disp"].values
xp = panel["polity2"].values
xd = panel["durable"].values
print(f"  n_obs={n_obs} n_countries={n_countries} n_classes={n_classes}")


def fit_model(name, with_cov=False, with_class=False):
    print(f"\n--- {name} ---")
    with pm.Model() as m:
        alpha = pm.Normal("alpha", 0, 5)
        sigma_country = pm.HalfNormal("sigma_country", 2)
        sigma_year = pm.HalfNormal("sigma_year", 2)
        sigma_channel = pm.HalfNormal("sigma_channel", 2)
        sigma_y = pm.HalfNormal("sigma_y", 2)
        z_country = pm.Normal("z_country", 0, 1, shape=n_countries)
        z_year = pm.Normal("z_year", 0, 1, shape=n_years)
        z_channel = pm.Normal("z_channel", 0, 1, shape=n_channels)
        beta_country = z_country * sigma_country
        beta_year = z_year * sigma_year
        beta_channel = z_channel * sigma_channel
        mu = alpha + beta_country[country_idx] + beta_year[year_idx] + beta_channel[channel_idx]
        if with_cov:
            b_p = pm.Normal("b_polity2", 0, 2)
            b_d = pm.Normal("b_durable", 0, 2)
            mu = mu + b_p * xp + b_d * xd
        if with_class:
            sigma_class = pm.HalfNormal("sigma_class", 2)
            z_class = pm.Normal("z_class", 0, 1, shape=n_classes)
            beta_class = z_class * sigma_class
            mu = mu + beta_class[class_idx]
        pm.Normal("obs", mu=mu, sigma=sigma_y, observed=y)
        idata = pm.sample(
            1000, tune=1000, chains=2, cores=1,
            target_accept=0.92, progressbar=True,
            idata_kwargs={"log_likelihood": True},
        )
    return idata


m0 = fit_model("M0 baseline", with_cov=False, with_class=False)
m1 = fit_model("M1 baseline + Polity covariates", with_cov=True, with_class=False)
m2 = fit_model("M2 baseline + typology", with_cov=False, with_class=True)
m3 = fit_model("M3 baseline + Polity + typology", with_cov=True, with_class=True)

print("\n" + "=" * 80)
print("LOO-CV — does Polity (state-fragility) absorb the typology lift?")
print("=" * 80)

results = {}
for name, idata in [("baseline", m0), ("polity_only", m1), ("typology_only", m2), ("polity_plus_typology", m3)]:
    loo = az.loo(idata)
    results[name] = {"elpd": float(loo.elpd), "se": float(loo.se)}
    print(f"  {name:>22s}: elpd_loo = {loo.elpd:+.2f} +/- {loo.se:.2f}")

compare = az.compare({n: i for n, i in [("baseline", m0), ("polity_only", m1), ("typology_only", m2), ("polity_plus_typology", m3)]})
print("\nModel comparison:")
print(compare)

base = results["baseline"]["elpd"]
print("\nDelta-LOO vs baseline:")
for name in ["polity_only", "typology_only", "polity_plus_typology"]:
    d = results[name]["elpd"] - base
    print(f"  {name:>25s}: {d:+.2f}")

d_pol_only = results["polity_only"]["elpd"] - results["baseline"]["elpd"]
d_typ_only = results["typology_only"]["elpd"] - results["baseline"]["elpd"]
d_both = results["polity_plus_typology"]["elpd"] - results["baseline"]["elpd"]
d_typ_given_pol = results["polity_plus_typology"]["elpd"] - results["polity_only"]["elpd"]
d_pol_given_typ = results["polity_plus_typology"]["elpd"] - results["typology_only"]["elpd"]

print("\nMarginal contributions:")
print(f"  Polity alone (vs baseline):              {d_pol_only:+.2f}")
print(f"  Typology alone (vs baseline):            {d_typ_only:+.2f}")
print(f"  Both (vs baseline):                      {d_both:+.2f}")
print(f"  Typology AFTER Polity (incremental):     {d_typ_given_pol:+.2f}")
print(f"  Polity AFTER typology (incremental):     {d_pol_given_typ:+.2f}")

if d_pol_only >= 0.7 * d_typ_only:
    print("\n[Interp] Polity absorbs >=70% of typology's lift -> state-fragility latent SUPPORTED.")
elif d_typ_given_pol >= 5:
    print("\n[Interp] Typology adds Delta-LOO>=5 even after Polity -> typology carries content beyond state-fragility.")
else:
    print("\n[Interp] Mixed; both partially overlapping.")

out = {
    "loo_results": results,
    "marginal": {
        "polity_only_vs_baseline": d_pol_only,
        "typology_only_vs_baseline": d_typ_only,
        "both_vs_baseline": d_both,
        "typology_given_polity": d_typ_given_pol,
        "polity_given_typology": d_pol_given_typ,
    },
    "n_obs": n_obs,
    "n_countries": n_countries,
    "n_classes": n_classes,
    "compare_table": compare.to_dict() if hasattr(compare, "to_dict") else str(compare),
}
Path("D:/IDP/analysis/paper6_phase1_latent_polity_2026_05_27.json").write_text(
    json.dumps(out, indent=2), encoding="utf-8"
)
print("\nSaved: D:/IDP/analysis/paper6_phase1_latent_polity_2026_05_27.json")
