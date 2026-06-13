"""
Paper 6 — Latent-covariate test.

Hypothesis from ablation finding: the +14.22 combined-typology ΔLOO might be a
projection of a latent country-level signal (state-fragility / institutional
capacity / demographic exposure). Test by adding WDI country-level covariates
and comparing ΔLOO with and without typology.

Models:
  M0 baseline (no typology, no covariates)
  M1 baseline + WDI covariates (log_pop, log_gdp_pc, urban_share)
  M2 baseline + combined typology (headline)
  M3 baseline + WDI covariates + combined typology
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
print("PAPER 6 LATENT-COVARIATE TEST")
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

# --- WDI covariates (country-level, mid-panel year 2015) ---
print("\n--- Loading WDI covariates ---")
wdi = pd.read_csv("D:/IDP/data/wb_wdi/extracted/WDICSV.csv", low_memory=False)
def wdi_lookup(code, year="2015"):
    rows = wdi[wdi["Indicator Code"] == code]
    out = rows[["Country Code", year]].rename(columns={"Country Code": "country", year: "value"})
    return dict(zip(out["country"], pd.to_numeric(out["value"], errors="coerce")))

pop_map = wdi_lookup("SP.POP.TOTL", "2015")
gdp_map = wdi_lookup("NY.GDP.PCAP.KD", "2015")
urb_map = wdi_lookup("SP.URB.TOTL.IN.ZS", "2015")

panel["log_pop"] = panel["country"].map(pop_map).apply(np.log)
panel["log_gdp"] = panel["country"].map(gdp_map).apply(np.log)
panel["urban_share"] = panel["country"].map(urb_map)

before = len(panel)
panel = panel.dropna(subset=["log_pop", "log_gdp", "urban_share"])
print(f"  dropped {before - len(panel)} rows for missing WDI; n={len(panel)}")
# Standardize covariates
for col in ["log_pop", "log_gdp", "urban_share"]:
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
xpop = panel["log_pop"].values
xgdp = panel["log_gdp"].values
xurb = panel["urban_share"].values
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
            b_pop = pm.Normal("b_pop", 0, 2)
            b_gdp = pm.Normal("b_gdp", 0, 2)
            b_urb = pm.Normal("b_urb", 0, 2)
            mu = mu + b_pop * xpop + b_gdp * xgdp + b_urb * xurb
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
m1 = fit_model("M1 baseline + WDI covariates", with_cov=True, with_class=False)
m2 = fit_model("M2 baseline + typology", with_cov=False, with_class=True)
m3 = fit_model("M3 baseline + WDI covariates + typology", with_cov=True, with_class=True)

print("\n" + "=" * 80)
print("LOO-CV — does WDI covariate absorb the typology lift?")
print("=" * 80)

results = {}
for name, idata in [("baseline", m0), ("covariates_only", m1), ("typology_only", m2), ("covariates_plus_typology", m3)]:
    loo = az.loo(idata)
    results[name] = {"elpd": float(loo.elpd), "se": float(loo.se)}
    print(f"  {name:>25s}: elpd_loo = {loo.elpd:+.2f} ± {loo.se:.2f}")

compare = az.compare({n: i for n, i in [("baseline", m0), ("covariates_only", m1), ("typology_only", m2), ("covariates_plus_typology", m3)]})
print("\nModel comparison:")
print(compare)

base = results["baseline"]["elpd"]
print("\nΔLOO vs baseline:")
for name in ["covariates_only", "typology_only", "covariates_plus_typology"]:
    d = results[name]["elpd"] - base
    print(f"  {name:>30s}: {d:+.2f}")

# Marginal contributions
d_cov_only = results["covariates_only"]["elpd"] - results["baseline"]["elpd"]
d_typ_only = results["typology_only"]["elpd"] - results["baseline"]["elpd"]
d_both = results["covariates_plus_typology"]["elpd"] - results["baseline"]["elpd"]
d_typ_given_cov = results["covariates_plus_typology"]["elpd"] - results["covariates_only"]["elpd"]
d_cov_given_typ = results["covariates_plus_typology"]["elpd"] - results["typology_only"]["elpd"]

print("\nMarginal contributions:")
print(f"  Covariates alone (vs baseline):        {d_cov_only:+.2f}")
print(f"  Typology alone (vs baseline):          {d_typ_only:+.2f}")
print(f"  Both (vs baseline):                    {d_both:+.2f}")
print(f"  Typology AFTER covariates (incremental): {d_typ_given_cov:+.2f}")
print(f"  Covariates AFTER typology (incremental): {d_cov_given_typ:+.2f}")

if d_cov_only >= 0.7 * d_typ_only:
    print(f"\n[Interpretation] WDI covariates absorb ≥70% of typology's lift → latent-signal hypothesis SUPPORTED.")
elif d_typ_given_cov >= 5:
    print(f"\n[Interpretation] Typology adds ΔLOO≥5 even after covariates → typology carries additional content beyond WDI latent.")
else:
    print(f"\n[Interpretation] Mixed; both partially overlapping.")

out = {
    "loo_results": results,
    "marginal": {
        "covariates_only_vs_baseline": d_cov_only,
        "typology_only_vs_baseline": d_typ_only,
        "both_vs_baseline": d_both,
        "typology_given_covariates": d_typ_given_cov,
        "covariates_given_typology": d_cov_given_typ,
    },
    "n_obs": n_obs,
    "n_countries": n_countries,
    "compare_table": compare.to_dict() if hasattr(compare, "to_dict") else str(compare),
}
Path("D:/IDP/analysis/paper6_phase1_latent_test_2026_05_27.json").write_text(
    json.dumps(out, indent=2), encoding="utf-8"
)
print("\nSaved: D:/IDP/analysis/paper6_phase1_latent_test_2026_05_27.json")
