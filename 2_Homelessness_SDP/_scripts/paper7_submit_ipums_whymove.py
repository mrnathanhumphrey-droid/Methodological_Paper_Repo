"""
Paper 7 Bridge-1 upgrade — submit IPUMS-CPS ASEC extract for WHYMOVE
(individual reason-for-move) crossed with poverty + move-distance + metro.

Mirrors D:/Migration/src/submit_ipums_extract.py (same ipumspy idioms / key).
collection='cps'. ASEC samples (cpsYYYY_03s) carry WHYMOVE + migration vars.

Key: IPUMS_API_KEY env var (Windows User var; load it before running).
Submits, polls, downloads to D:/IDP/data/paper7/ipums_cps/.
Idempotent-ish: records extract_id to extract_state.json.
"""
from __future__ import annotations
import json, os, sys, time
from datetime import datetime
from pathlib import Path

OUT_DIR = Path(r"D:/IDP/data/paper7/ipums_cps")
STATE = OUT_DIR / "extract_state.json"

# ASEC samples with WHYMOVE (March supplement). 2020 ASEC exists in CPS (unlike ACS 1yr).
SAMPLES = [f"cps{y}_03s" for y in range(2016, 2025)]

VARIABLES = [
    "YEAR", "SERIAL", "PERNUM", "ASECWT",
    "AGE", "SEX", "RACE", "HISPAN", "EDUC",
    "STATEFIP", "METAREA", "METFIPS", "COUNTY",
    "MIGRATE1", "WHYMOVE",
    "OFFPOV", "FAMINC",
]

def need_key():
    k = os.environ.get("IPUMS_API_KEY")
    if not k:
        print("ERROR: IPUMS_API_KEY not in process env. Run via PowerShell with:")
        print('  $env:IPUMS_API_KEY = [Environment]::GetEnvironmentVariable(\'IPUMS_API_KEY\',\'User\')')
        sys.exit(2)
    return k

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    key = need_key()
    from ipumspy import IpumsApiClient, MicrodataExtract
    client = IpumsApiClient(key)

    # try the full variable set; if the API rejects a var/sample, drop it and retry
    variables = list(VARIABLES)
    samples = list(SAMPLES)
    extract = None
    for attempt in range(6):
        try:
            extract = MicrodataExtract(
                collection="cps", samples=samples, variables=variables,
                description="Paper7 SDP Bridge-1: WHYMOVE x poverty x move-distance x metro",
                data_format="csv")
            client.submit_extract(extract)
            break
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            print(f"[attempt {attempt}] submit error: {msg[:300]}")
            # drop offending variable or sample mentioned in the error
            dropped = False
            import re as _re
            for v in list(variables):
                if _re.search(rf"\b{_re.escape(v)}\b", msg) and v not in ("YEAR",):
                    variables.remove(v); print(f"  dropped variable {v}"); dropped=True; break
            if not dropped:
                for s in list(samples):
                    if s in msg:
                        samples.remove(s); print(f"  dropped sample {s}"); dropped=True; break
            if not dropped:
                print("  unrecognized error; aborting."); raise
    if extract is None:
        print("could not build a valid extract"); sys.exit(4)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Submitted extract_id={extract.extract_id} samples={len(samples)} vars={len(variables)}")
    STATE.write_text(json.dumps({"extract_id": str(extract.extract_id), "collection": "cps",
                                 "submitted_at": ts, "samples": samples, "variables": variables}, indent=2))
    print("Polling...")
    while True:
        st = client.extract_status(extract)
        print(f"  [{datetime.now():%H:%M:%S}] status={st}")
        if st == "completed": break
        if st == "failed": print("FAILED server-side"); sys.exit(5)
        time.sleep(30)
    print("Downloading...")
    client.download_extract(extract, download_dir=OUT_DIR)
    print(f"Done. Files in {OUT_DIR}")

if __name__ == "__main__":
    main()
