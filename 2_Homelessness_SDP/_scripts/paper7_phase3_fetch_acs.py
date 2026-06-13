"""
Paper 7 Phase 3 — fetch ACS renter cost-burden by state x year.

Table B25070 (gross rent as % of household income), ACS 1-year, all states.
Cost-burdened share = (30-34.9 + 35-39.9 + 40-49.9 + 50+) / (total - not_computed).
Severe share = (50+) / (total - not_computed).

ACS 1-year exists 2007-2024 except 2020 (Census did not release standard 1-yr
2020 due to COVID collection disruption). We pull every available year and log
2020 as a known gap (handled downstream by interpolation flag, not silently).

Key is read from D:/IDP/.env (gitignored). Never printed.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

OUT = Path(r"D:/IDP/data/paper7/acs_cost_burden")
OUT.mkdir(parents=True, exist_ok=True)

# B25070: 001 total; 007 30-34.9; 008 35-39.9; 009 40-49.9; 010 50+; 011 not computed
VARS = ["NAME", "B25070_001E", "B25070_007E", "B25070_008E",
        "B25070_009E", "B25070_010E", "B25070_011E"]
YEARS = [y for y in range(2007, 2025) if y != 2020]  # 2020 1-yr not released
UA = "Mozilla/5.0 (research; IDP Paper 7)"


def load_key() -> str:
    env = Path(r"D:/IDP/.env")
    for line in env.read_text().splitlines():
        if line.startswith("CENSUS_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("CENSUS_API_KEY not in D:/IDP/.env")


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
        except Exception as e:  # noqa: BLE001 — log and continue, gap is informative
            print(f"[acs] {y} FAILED: {e}")
            continue
        header, *data = payload
        idx = {h: i for i, h in enumerate(header)}
        for rec in data:
            total = float(rec[idx["B25070_001E"]] or 0)
            notc = float(rec[idx["B25070_011E"]] or 0)
            denom = total - notc
            burdened = sum(float(rec[idx[v]] or 0) for v in
                           ["B25070_007E", "B25070_008E", "B25070_009E", "B25070_010E"])
            severe = float(rec[idx["B25070_010E"]] or 0)
            rows.append({
                "year": y,
                "state_name": rec[idx["NAME"]],
                "state_fips": rec[idx["state"]],
                "renter_hh_total": total,
                "renter_hh_computed": denom,
                "cost_burdened_30plus": burdened,
                "severe_burdened_50plus": severe,
                "cb_share": burdened / denom if denom else None,
                "severe_share": severe / denom if denom else None,
            })
        print(f"[acs] {y}: {len(data)} states")
        time.sleep(0.3)
    out = OUT / "acs_b25070_cost_burden_state_year.json"
    out.write_text(json.dumps(rows, indent=2))
    print(f"[acs] wrote {out} ({len(rows)} state-years; 2020 gap logged)")


if __name__ == "__main__":
    main()
