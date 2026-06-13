"""Final batch — WB WDI extract + V-Dem RData->CSV + WHO GHO priority + IDMC IDU all countries."""
import json
import pathlib
import time
import urllib.request
import zipfile
import io

ROOT = pathlib.Path("D:/IDP/data")

# === 1. Extract WB WDI bulk ===
print("=== 1. WB WDI extract ===")
wdi_zip = ROOT / "wb_wdi" / "WDI_CSV.zip"
wdi_out = ROOT / "wb_wdi" / "extracted"
wdi_out.mkdir(parents=True, exist_ok=True)
if wdi_zip.exists() and not (wdi_out / "WDICSV.csv").exists():
    with zipfile.ZipFile(wdi_zip) as z:
        z.extractall(wdi_out)
        print(f"  extracted {len(z.namelist())} files: {z.namelist()[:5]}")
for f in sorted(wdi_out.iterdir()):
    print(f"  {f.name}: {f.stat().st_size:,} bytes")

# === 2. V-Dem RData -> CSV ===
print("\n=== 2. V-Dem RData -> CSV ===")
try:
    import pyreadr
    vdem_rdata = ROOT / "vdem" / "vdemdata_repo" / "data" / "vdem.RData"
    if vdem_rdata.exists():
        out = pyreadr.read_r(str(vdem_rdata))
        for key, df in out.items():
            target = ROOT / "vdem" / f"vdem_{key}.csv"
            df.to_csv(target, index=False)
            print(f"  vdem.{key}: {df.shape[0]:,} rows × {df.shape[1]} cols -> {target.name}")
    codebook_rdata = ROOT / "vdem" / "vdemdata_repo" / "data" / "codebook.RData"
    if codebook_rdata.exists():
        out = pyreadr.read_r(str(codebook_rdata))
        for key, df in out.items():
            target = ROOT / "vdem" / f"codebook_{key}.csv"
            df.to_csv(target, index=False)
            print(f"  codebook.{key}: {df.shape[0]:,} rows × {df.shape[1]} cols -> {target.name}")
    vparty_rdata = ROOT / "vdem" / "vdemdata_repo" / "data" / "vparty.RData"
    if vparty_rdata.exists():
        out = pyreadr.read_r(str(vparty_rdata))
        for key, df in out.items():
            target = ROOT / "vdem" / f"vparty_{key}.csv"
            df.to_csv(target, index=False)
            print(f"  vparty.{key}: {df.shape[0]:,} rows × {df.shape[1]} cols -> {target.name}")
except Exception as e:
    print(f"  FAIL: {type(e).__name__}: {e}")

# === 3. WHO GHO priority indicators (displacement-adjacent ~40) ===
print("\n=== 3. WHO GHO priority indicators ===")
priority = [
    # Mortality
    "MDG_0000000001",  # Maternal mortality ratio
    "MDG_0000000007",  # Neonatal mortality
    "WHOSIS_000002",   # Life expectancy at birth
    "WHOSIS_000007",   # Adult mortality rate
    "WHOSIS_000015",   # Healthy life expectancy
    # Child health
    "MDG_0000000006",  # Under-5 mortality
    "MDG_0000000026",  # Children stunted
    "MDG_0000000028",  # Children wasted
    "MDG_0000000029",  # Children underweight
    "WSH_HYGIENE_SAFELY_MANAGED",  # Sanitation
    "WSH_WATER_SAFELY_MANAGED",
    # Immunization
    "WHS4_543",  # DTP3
    "WHS4_117",  # Measles
    "WHS4_544",  # BCG
    # Maternal/reproductive
    "MDG_0000000025",  # Adolescent birth rate
    "RHR_ANC4",  # Antenatal care 4+ visits
    "MDG_0000000003",  # Births by skilled attendant
    # Disease burden
    "MDG_0000000017",  # Malaria incidence
    "MDG_0000000018",  # Malaria mortality
    "MDG_0000000020",  # TB incidence
    "MDG_0000000023",  # HIV new infections
    "WHS3_50",  # Cholera reported cases
    # Mental health / NCD
    "NCD_BMI_30A",  # Obesity adults
    "NCD_BMI_18A",  # Underweight adults
    "SDGSUICIDE",  # Suicide mortality
    # Nutrition
    "NUTRITION_ANT_HAZ_NE2",
    "NUTRITION_ANT_WHZ_NE2",
    # Health system
    "HWF_0001",  # Medical doctors per 10k
    "HWF_0006",  # Nursing personnel per 10k
    # Universal health coverage
    "UHC_INDEX_REPORTED",
]
out = ROOT / "who_gho" / "indicators"
out.mkdir(parents=True, exist_ok=True)
ok = 0
for code in priority:
    target = out / f"{code}.json"
    if target.exists() and target.stat().st_size > 500:
        ok += 1
        continue
    try:
        req = urllib.request.Request(f"https://ghoapi.azureedge.net/api/{code}", headers={"User-Agent": "IDP-Study/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            target.write_bytes(resp.read())
        sz = target.stat().st_size
        if sz > 500:
            ok += 1
            print(f"  {code}: {sz:,}")
        else:
            print(f"  {code}: too small ({sz})")
    except Exception as e:
        print(f"  {code}: FAIL {type(e).__name__}")
    time.sleep(0.4)
print(f"  WHO GHO total: {ok}/{len(priority)}")

# === 4. IDMC IDU all-country expansion ===
print("\n=== 4. IDMC IDU all countries ===")
search = ROOT / "idmc_gidd" / "hdx_search_idmc.json"
out = ROOT / "idmc_gidd" / "idu"
out.mkdir(parents=True, exist_ok=True)
fews = json.load(open(search))
results = fews["result"]["results"]
new = 0
for r in results:
    name = r.get("name", "")
    if "idu-events" not in name and "idu_events" not in name:
        continue
    iso3 = name.split("-")[0][:3].lower()
    for res in r.get("resources", []):
        url = res.get("url", "")
        if url.endswith(".csv"):
            fname = f"{iso3}_{name.split('-')[0]}.csv"
            target = out / fname
            if target.exists() and target.stat().st_size > 1000:
                break
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "IDP-Study/1.0"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    target.write_bytes(resp.read())
                sz = target.stat().st_size
                if sz > 1000:
                    new += 1
                    print(f"  {fname}: {sz:,}")
            except Exception as e:
                print(f"  {fname}: FAIL {type(e).__name__}")
            time.sleep(0.4)
            break
print(f"  IDMC IDU new countries: {new}")

print(f"\n=== complete @ {time.strftime('%H:%M:%S')} ===")
