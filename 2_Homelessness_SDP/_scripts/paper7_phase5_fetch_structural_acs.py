"""
PRE_REG_029 — fetch ACS structural covariates, state x year (2007-2024, 1-yr; 2020 gap).

- B25004_001E .. : vacancy status (we use rental vacancy rate proxy)
- B25064_001E    : median gross rent
- B19013_001E    : median household income
- B17001_001E/_002E : poverty universe / below poverty -> poverty rate
- B25003_001/_003 : tenure (renter share) for rent-to-income context

Rental vacancy rate = for-rent vacant units / (renter-occupied + for-rent vacant).
  B25004_002E = for rent ; B25002/B25003 give occupied tenure.
We pull B25003 (tenure) + B25004 (vacancy by status) to compute rental vacancy.
"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

OUT = Path(r"D:/IDP/data/paper7/acs_structural")
OUT.mkdir(parents=True, exist_ok=True)
UA = "Mozilla/5.0 (research; IDP Paper 7 PRE_REG_029)"

VARS = [
    "NAME",
    "B25064_001E",          # median gross rent
    "B19013_001E",          # median household income
    "B17001_001E", "B17001_002E",   # poverty universe / below
    "B25003_001E", "B25003_003E",   # tenure total / renter-occupied
    "B25004_001E", "B25004_002E",   # vacant total / vacant-for-rent
]
YEARS = [y for y in range(2007, 2025) if y != 2020]


def load_key() -> str:
    for line in (Path(r"D:/IDP/.env")).read_text().splitlines():
        if line.startswith("CENSUS_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no key")


def main() -> None:
    key = load_key()
    rows = []
    for y in YEARS:
        url = (f"https://api.census.gov/data/{y}/acs/acs1?get={','.join(VARS)}"
               f"&for=state:*&key={key}")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                payload = json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            print(f"[acs-struct] {y} FAILED: {e}")
            continue
        h, *data = payload
        i = {c: j for j, c in enumerate(h)}

        def g(rec, v):
            try:
                return float(rec[i[v]]) if rec[i[v]] not in (None, "") else None
            except (KeyError, ValueError):
                return None

        for rec in data:
            pov_u = g(rec, "B17001_001E")
            pov_b = g(rec, "B17001_002E")
            ten_t = g(rec, "B25003_001E")
            ten_r = g(rec, "B25003_003E")
            vac_t = g(rec, "B25004_001E")
            vac_r = g(rec, "B25004_002E")
            rental_vac = (vac_r / (ten_r + vac_r)
                          if (ten_r and vac_r is not None) else None)
            rows.append({
                "year": y,
                "state_name": rec[i["NAME"]],
                "state_fips": rec[i["state"]],
                "median_gross_rent": g(rec, "B25064_001E"),
                "median_hh_income": g(rec, "B19013_001E"),
                "poverty_rate": (pov_b / pov_u if (pov_u and pov_b is not None) else None),
                "renter_share": (ten_r / ten_t if (ten_t and ten_r is not None) else None),
                "rental_vacancy_rate": rental_vac,
            })
        print(f"[acs-struct] {y}: {len(data)} states")
        time.sleep(0.25)
    out = OUT / "acs_structural_state_year.json"
    out.write_text(json.dumps(rows, indent=2))
    print(f"[acs-struct] wrote {out} ({len(rows)} state-years)")


if __name__ == "__main__":
    main()
