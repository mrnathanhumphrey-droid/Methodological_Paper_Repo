"""
Paper 7 SDP probe: IDP->SDP bridge test.
Does the 2022->2024 US family-homelessness spike concentrate in documented
migrant-receiving CoCs, aligning ecologically with the 2022-24 international
displacement wave (Venezuela/Haiti)?

ECOLOGICAL / CORRELATIONAL ONLY. HUD CoC data carries NO origin tags.
Author: probe run 2026-05-28. Creates NEW files only.
"""
import json
import re
import numpy as np
import pandas as pd

PIT = "D:/IDP/data/paper7/hud_pit/2007-2024-PIT-Counts-by-CoC.xlsb"
UNHCR = "D:/IDP/data/unhcr_rdf/extracted/population.csv"
OUT = "D:/IDP/analysis/paper7_probe_migrant_bridge_2026_05_28.json"

FAM = "Overall Homeless People in Families"
CoC_RE = re.compile(r"^[A-Z]{2}-\d")

YEARS = list(range(2015, 2025))  # 2015..2024
BASE_YEARS = list(range(2015, 2022))  # 2015..2021 baseline

# Documented migrant-receiving CoCs (2022-24 busing / asylum-seeker destinations).
# Defined a priori from public reporting before reading the rank.
MIGRANT_COCS = {
    "NY-600": "New York City",
    "NY-500": "Rochester/Monroe County",
    "NY-507": "Schenectady City & County",
    "IL-510": "Chicago",
    "IL-511": "Cook County (suburban Chicago)",
    "CO-503": "Metropolitan Denver",
    "MA-500": "Boston",
    "MA-502": "Lynn/North Shore",
    "MA-503": "Cape Cod & Islands",
    "MA-504": "Springfield/Hampden County",
    "MA-505": "New Bedford/Bristol/Plymouth Counties",
    "MA-506": "Worcester City & County",
    "MA-507": "Pittsfield/Berkshire/Franklin/Hampshire",
    "MA-509": "Cambridge",
    "MA-511": "Quincy/Brockton/Weymouth/Plymouth",
    "MA-516": "Massachusetts Balance of State",
    "DC-500": "Washington DC",
    "TX-503": "Austin/Travis County",
    "TX-700": "Houston/Harris/Fort Bend/Montgomery",
    "TX-600": "Dallas City & County/Irving",
    "TX-601": "Fort Worth/Arlington/Tarrant County",
    "CA-600": "Los Angeles City & County",
    "CA-501": "San Francisco",
    "AZ-502": "Phoenix/Mesa/Maricopa County",
    "FL-600": "Miami-Dade County",
    "WA-500": "Seattle/King County",
    "NJ-500": "Atlantic City & County",
    "PA-500": "Philadelphia",
}

# ---- Build CoC x year family series ----
frames = {}
for y in YEARS:
    df = pd.read_excel(PIT, sheet_name=str(y), engine="pyxlsb")
    df = df[df["CoC Number"].astype(str).str.match(CoC_RE)].copy()
    s = pd.to_numeric(df[FAM], errors="coerce")
    sub = pd.DataFrame({
        "CoC Number": df["CoC Number"].astype(str).str.strip(),
        "CoC Name": df["CoC Name"].astype(str).str.strip(),
        str(y): s.values,
    })
    # collapse any dup CoC rows (shouldn't happen) by sum
    name_map = sub.groupby("CoC Number")["CoC Name"].first()
    val = sub.groupby("CoC Number")[str(y)].sum(min_count=1)
    frames[y] = pd.DataFrame({"CoC Name": name_map, str(y): val})

panel = None
for y in YEARS:
    f = frames[y]
    if panel is None:
        panel = f.copy()
    else:
        panel = panel.join(f[str(y)], how="outer")
        # keep first non-null name
        if "CoC Name" not in panel.columns:
            panel["CoC Name"] = f["CoC Name"]
panel = panel.reset_index().rename(columns={"index": "CoC Number"})

# ---- Spike z-score: 2024 value vs 2015-2021 baseline ----
ybcols = [str(y) for y in BASE_YEARS]
records = []
for _, r in panel.iterrows():
    coc = r["CoC Number"]
    name = r["CoC Name"]
    base = np.array([r.get(c, np.nan) for c in ybcols], dtype=float)
    base = base[~np.isnan(base)]
    v2021 = r.get("2021", np.nan)
    v2022 = r.get("2022", np.nan)
    v2023 = r.get("2023", np.nan)
    v2024 = r.get("2024", np.nan)
    if len(base) < 4 or np.isnan(v2024):
        continue
    mu = base.mean()
    sd = base.std(ddof=1)
    if sd == 0 or np.isnan(sd):
        sd = max(1.0, 0.05 * mu)  # guard flat baselines
    z = (v2024 - mu) / sd
    # spike magnitude 2022->2024 (per task) and absolute jump
    abs_jump_22_24 = (v2024 - v2022) if not np.isnan(v2022) else np.nan
    abs_jump_23_24 = (v2024 - v2023) if not np.isnan(v2023) else np.nan
    pct_22_24 = (v2024 / v2022 - 1.0) if (not np.isnan(v2022) and v2022 > 0) else np.nan
    records.append({
        "coc": coc, "name": name,
        "base_mean": round(mu, 1), "base_sd": round(sd, 1),
        "v2021": None if np.isnan(v2021) else int(v2021),
        "v2022": None if np.isnan(v2022) else int(v2022),
        "v2023": None if np.isnan(v2023) else int(v2023),
        "v2024": int(v2024),
        "z_2024": round(float(z), 2),
        "abs_jump_22_24": None if np.isnan(abs_jump_22_24) else int(abs_jump_22_24),
        "abs_jump_23_24": None if np.isnan(abs_jump_23_24) else int(abs_jump_23_24),
        "pct_22_24": None if np.isnan(pct_22_24) else round(float(pct_22_24), 3),
        "is_migrant_coc": coc in MIGRANT_COCS,
    })

res = pd.DataFrame(records)
res_by_z = res.sort_values("z_2024", ascending=False).reset_index(drop=True)
res_by_abs = res.sort_values("abs_jump_22_24", ascending=False).reset_index(drop=True)

# ---- Concentration test: are big spikes in migrant CoCs? ----
TOPN = 25
top_z = res_by_z.head(TOPN)
top_abs = res_by_abs.head(TOPN)
n_migrant_total = int(res["is_migrant_coc"].sum())
n_total = len(res)
top_z_migrant = int(top_z["is_migrant_coc"].sum())
top_abs_migrant = int(top_abs["is_migrant_coc"].sum())

# Hypergeometric-style expectation
exp_top_migrant = TOPN * n_migrant_total / n_total

# Share of national family-homelessness *increase* 2022->2024 captured by migrant CoCs
tot_jump = res["abs_jump_22_24"].dropna().sum()
mig_jump = res.loc[res["is_migrant_coc"], "abs_jump_22_24"].dropna().sum()
share_jump_migrant = float(mig_jump / tot_jump) if tot_jump else None

# ---- Timing: 2023->24 step vs gradual. Compare spike vs non-spike CoCs ----
# spike CoCs = top decile by z
spike_thresh = res["z_2024"].quantile(0.90)
res["is_spike"] = res["z_2024"] >= spike_thresh

def step_fraction(row):
    # fraction of the 2022->2024 jump that happened in 2023->2024 (the migrant-wave window)
    j = row["abs_jump_22_24"]
    s = row["abs_jump_23_24"]
    if j is None or s is None or j == 0:
        return np.nan
    return s / j

res["step_frac_23_24"] = res.apply(step_fraction, axis=1)
spike_step = res.loc[res["is_spike"], "step_frac_23_24"].dropna()
nonspike_step = res.loc[~res["is_spike"], "step_frac_23_24"].dropna()

# ---- UNHCR origin series: VEN / HTI -> USA cross-border ----
u = pd.read_csv(UNHCR)
for c in ["Refugees under UNHCR's mandate", "Asylum-seekers",
          "Other people in need of international protection"]:
    u[c] = pd.to_numeric(u[c], errors="coerce").fillna(0)

def origin_to_usa(iso):
    sub = u[(u["Country of origin (ISO)"] == iso) &
            (u["Country of asylum (ISO)"] == "USA") &
            (u["Year"].between(2014, 2024))].copy()
    g = sub.groupby("Year").agg(
        refugees=("Refugees under UNHCR's mandate", "sum"),
        asylum_seekers=("Asylum-seekers", "sum"),
        other_protection=("Other people in need of international protection", "sum"),
    ).reset_index()
    g["total_concern_usa"] = g["refugees"] + g["asylum_seekers"] + g["other_protection"]
    return g

ven_usa = origin_to_usa("VEN")
hti_usa = origin_to_usa("HTI")
# global displacement magnitude (all asylum countries) for VEN/HTI
def origin_global(iso):
    sub = u[(u["Country of origin (ISO)"] == iso) & (u["Year"].between(2014, 2024))]
    g = sub.groupby("Year").agg(
        refugees=("Refugees under UNHCR's mandate", "sum"),
        asylum_seekers=("Asylum-seekers", "sum"),
        other_protection=("Other people in need of international protection", "sum"),
    ).reset_index()
    g["total_displaced_global"] = g["refugees"] + g["asylum_seekers"] + g["other_protection"]
    return g

ven_glob = origin_global("VEN")
hti_glob = origin_global("HTI")

def to_yeardict(df, col):
    return {int(r["Year"]): int(r[col]) for _, r in df.iterrows()}

# ---- Assemble JSON ----
out = {
    "probe": "paper7_idp_to_sdp_migrant_bridge",
    "date": "2026-05-28",
    "framing": ("ECOLOGICAL / CORRELATIONAL ONLY. HUD CoC family-homelessness "
                "carries NO origin/nationality tags. UNHCR origin series shows "
                "international-wave timing only. No origin->destination causal "
                "claim is made or supported."),
    "metric": FAM,
    "baseline_years": BASE_YEARS,
    "spike_metric": "z = (2024 family value - mean(2015-2021)) / sd(2015-2021)",
    "n_cocs_analyzed": n_total,
    "n_migrant_cocs_present": n_migrant_total,
    "migrant_coc_list": MIGRANT_COCS,
    "top25_by_z": res_by_z.head(25).to_dict(orient="records"),
    "top25_by_abs_jump_22_24": res_by_abs.head(25).to_dict(orient="records"),
    "migrant_cocs_detail": res[res["is_migrant_coc"]].sort_values(
        "z_2024", ascending=False).to_dict(orient="records"),
    "concentration": {
        "topN": TOPN,
        "n_migrant_in_top25_by_z": top_z_migrant,
        "n_migrant_in_top25_by_abs": top_abs_migrant,
        "expected_migrant_in_top25_if_random": round(exp_top_migrant, 2),
        "enrichment_factor_z": round(top_z_migrant / exp_top_migrant, 2) if exp_top_migrant else None,
        "national_total_family_increase_22_24": int(tot_jump),
        "migrant_coc_family_increase_22_24": int(mig_jump),
        "share_of_national_increase_in_migrant_cocs": round(share_jump_migrant, 3) if share_jump_migrant else None,
    },
    "timing": {
        "spike_def": "top decile by 2024 z-score",
        "spike_z_threshold": round(float(spike_thresh), 2),
        "n_spike_cocs": int(res["is_spike"].sum()),
        "median_step_frac_23_24_spike": round(float(spike_step.median()), 3) if len(spike_step) else None,
        "median_step_frac_23_24_nonspike": round(float(nonspike_step.median()), 3) if len(nonspike_step) else None,
        "interpretation_note": ("step_frac_23_24 = (2024-2023)/(2024-2022). "
                                "Near 1.0 => the jump is a 2023->2024 STEP (migrant-wave window); "
                                "near 0.5 => evenly spread 2022->2024 (gradual)."),
    },
    "origin_series_unhcr": {
        "source": "UNHCR RDF population.csv (origin->asylum stock by year)",
        "VEN_to_USA_total_concern": to_yeardict(ven_usa, "total_concern_usa"),
        "VEN_to_USA_asylum_seekers": to_yeardict(ven_usa, "asylum_seekers"),
        "HTI_to_USA_total_concern": to_yeardict(hti_usa, "total_concern_usa"),
        "HTI_to_USA_asylum_seekers": to_yeardict(hti_usa, "asylum_seekers"),
        "VEN_global_total_displaced": to_yeardict(ven_glob, "total_displaced_global"),
        "HTI_global_total_displaced": to_yeardict(hti_glob, "total_displaced_global"),
        "note": ("VEN global displacement ramped 2016-2019, plateaued ~7M+. "
                 "US-destination asylum-seeker stock and southern-border "
                 "encounters surged 2022-2024 (busing to NYC/Chicago/Denver). "
                 "Domestic family spike timing is compared to this ecologically."),
    },
}

with open(OUT, "w") as f:
    json.dump(out, f, indent=2)

# ---- console summary ----
print("=== CONCENTRATION ===")
print(f"CoCs analyzed: {n_total}; migrant CoCs present: {n_migrant_total}")
print(f"Top25 by z: {top_z_migrant} migrant (expected if random ~{exp_top_migrant:.1f}) "
      f"enrichment {top_z_migrant/exp_top_migrant:.1f}x")
print(f"Top25 by abs jump: {top_abs_migrant} migrant")
print(f"National family increase 2022->2024: {int(tot_jump):,}; "
      f"migrant CoCs captured: {int(mig_jump):,} ({share_jump_migrant*100:.0f}%)")
print("\n=== TOP 15 BY Z ===")
for _, r in res_by_z.head(15).iterrows():
    flag = "  <MIGRANT" if r["is_migrant_coc"] else ""
    print(f"{r['coc']:8s} z={r['z_2024']:6.1f}  2022={r['v2022']} 2023={r['v2023']} 2024={r['v2024']}  {r['name'][:40]}{flag}")
print("\n=== TIMING ===")
print(f"spike step_frac med {out['timing']['median_step_frac_23_24_spike']} "
      f"vs nonspike {out['timing']['median_step_frac_23_24_nonspike']}")
print("\n=== VEN->USA total concern ===", to_yeardict(ven_usa, "total_concern_usa"))
print("=== HTI->USA total concern ===", to_yeardict(hti_usa, "total_concern_usa"))
print("=== VEN global displaced ===", to_yeardict(ven_glob, "total_displaced_global"))
print("\nWrote", OUT)
