"""Fetch GADM admin-2 polygons for the 4 study countries.

GADM provides per-country boundary files at multiple levels (0/1/2/3).
We pull level-2 (county / municipality / governorate equivalent).

URL pattern: https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_{ISO3}.gpkg
(GADM 4.1; GeoPackage format).

Output: data/gadm/gadm41_{country}.gpkg + manifest entries.
"""
import pathlib, sys, hashlib, json, urllib.request, urllib.error, time, io
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass

ROOT = pathlib.Path(r"D:/IDP")
OUT_DIR = ROOT / "data" / "gadm"
MANIFEST = ROOT / "manifest.json"

COUNTRIES = {
    "Colombia": "COL",
    "Sudan":    "SDN",
    "DRC":      "COD",
    "Yemen":    "YEM",
}

GADM_URL_TEMPLATE = "https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_{iso3}.gpkg"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def update_manifest(entry):
    manifest = {}
    if MANIFEST.exists():
        try: manifest = json.loads(MANIFEST.read_text())
        except: manifest = {}
    manifest.setdefault("files", []).append(entry)
    manifest["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    MANIFEST.write_text(json.dumps(manifest, indent=2))


def fetch_url(url, dest, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "IDP-Study/0.1"})
            with urllib.request.urlopen(req, timeout=300) as resp:
                with open(dest, "wb") as f:
                    f.write(resp.read())
            return True
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"  attempt {attempt+1}/{retries} failed: {type(e).__name__}: {e}")
            time.sleep(5 * (attempt + 1))
    return False


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== GADM 4.1 admin-2 polygon fetch (4 countries) ===")
    for country, iso3 in COUNTRIES.items():
        url = GADM_URL_TEMPLATE.format(iso3=iso3)
        out_path = OUT_DIR / f"gadm41_{country.lower()}.gpkg"
        if out_path.exists():
            print(f"  [cache] {out_path.name} already present, skipping")
            continue
        print(f"  fetching {country} ({iso3}) from {url}")
        ok = fetch_url(url, out_path)
        if not ok:
            print(f"  FAIL: GADM fetch failed for {country}. Try manual download from https://gadm.org/download_country.html")
            continue
        update_manifest({
            "source": f"GADM 4.1: {country} (level 0-3)",
            "url": url,
            "filename": str(out_path.relative_to(ROOT)),
            "sha256": sha256(out_path),
            "size_bytes": out_path.stat().st_size,
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        # Quick layer check
        try:
            import geopandas as gpd, fiona
            layers = fiona.listlayers(out_path)
            print(f"  {country}: layers = {layers}")
            # Admin-2 typically layer ADM_ADM_2
            adm2_layer = [l for l in layers if "ADM_2" in l.upper() or "_2" in l] or layers
            if adm2_layer:
                g = gpd.read_file(out_path, layer=adm2_layer[0])
                print(f"  {country} admin-2 layer rows: {len(g):,}")
        except Exception as e:
            print(f"  WARN: couldn't inspect {out_path}: {e}")
    print(f"\n=== GADM fetch complete. Files in {OUT_DIR} ===")


if __name__ == "__main__":
    main()
