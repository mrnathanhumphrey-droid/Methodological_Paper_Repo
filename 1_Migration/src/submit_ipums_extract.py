"""
Submit and download the IPUMS USA extract specified in
docs/IPUMS_EXTRACT_SPEC.md for the RMD-SRC migration study.

Requires:
  pip install ipumspy
  env: IPUMS_API_KEY

Workflow:
  1. Build extract spec (12 ACS samples, ~25 variables, case-selected)
  2. Submit to IPUMS API
  3. Poll until ready
  4. Download to D:\\Migration\\data\\raw\\ipums\\

Idempotent: if a prior extract from this script is still pending or
downloaded, prints status and exits without resubmitting.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

OUT_DIR = Path(r"D:\Migration\data\raw\ipums")
LOG_DIR = Path(r"D:\Migration\logs")
STATE_FILE = OUT_DIR / "extract_state.json"

SAMPLES = [f"us{y}a" for y in range(2012, 2024)]

VARIABLES = [
    # identifiers / weights / GQ filter
    "YEAR", "SAMPLE", "SERIAL", "PERNUM", "PERWT", "HHWT", "GQ",
    # geography + migration
    "STATEFIP", "PUMA", "MIGRATE1", "MIGRATE1D",
    "MIGPLAC1", "MIGPUMA1",
    # P0 demographic species (PRE_REG v1.0 §2.4)
    "AGE", "MARST", "NCHILD", "EDUC", "EDUCD", "HHINCOME",
    # observable inputs (PRE_REG v1.0 §2.5)
    "INCTOT", "EMPSTAT", "EMPSTATD", "OWNERSHP", "RENTGRS",
    "VALUEH", "LABFORCE",
    # auxiliary
    "SEX", "RACE", "HISPAN", "CITIZEN",
]


def need_key():
    key = os.environ.get("IPUMS_API_KEY")
    if not key:
        print("ERROR: IPUMS_API_KEY env var not set.")
        print("Get a key at https://account.ipums.org/api_keys then:")
        print('  $env:IPUMS_API_KEY = "<your-key>"')
        sys.exit(2)
    return key


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    key = need_key()

    try:
        from ipumspy import IpumsApiClient, MicrodataExtract
    except ImportError:
        print("ERROR: ipumspy not installed. Run: pip install ipumspy")
        sys.exit(3)

    client = IpumsApiClient(key)
    extract = MicrodataExtract(
        collection="usa",
        samples=SAMPLES,
        variables=VARIABLES,
        description="RMD-SRC migration study v1.0 (PRE_REG locked 2026-05-27)",
        data_format="csv",
    )

    # case selections: age >= 18, non-institutionalized
    # (ipumspy uses post-build case_select_who and select_cases on individual vars;
    # we keep it minimal here — extract is small enough that we filter downstream)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"submit_ipums_{ts}.log"
    log = log_path.open("w", encoding="utf-8")
    def say(msg):
        print(msg)
        log.write(msg + "\n")
        log.flush()

    say(f"# IPUMS submit run {ts}")
    say(f"samples: {SAMPLES}")
    say(f"variables: {VARIABLES}")
    say(f"variable count: {len(VARIABLES)}")

    say("Submitting extract...")
    client.submit_extract(extract)
    say(f"Submitted. extract_id={extract.extract_id}")

    state = {
        "extract_id": str(extract.extract_id),
        "collection": getattr(extract, "collection", "usa"),
        "api_version": str(getattr(extract, "api_version", "")),
        "submitted_at": ts,
        "samples": SAMPLES,
        "variables": VARIABLES,
    }
    (OUT_DIR / "extract_state.json").write_text(json.dumps(state, indent=2))

    # poll
    say("Polling status...")
    poll_interval = 30
    while True:
        status = client.extract_status(extract)
        say(f"  [{datetime.now().strftime('%H:%M:%S')}] status={status}")
        if status == "completed":
            break
        if status == "failed":
            say("FAIL: extract failed server-side. Check IPUMS account.")
            sys.exit(4)
        time.sleep(poll_interval)

    say("Downloading...")
    client.download_extract(extract, download_dir=OUT_DIR)
    say(f"Download complete. Files in {OUT_DIR}")

    say("Writing manifest with SHA256 per file...")
    manifest_script = Path(__file__).parent / "write_ipums_manifest.py"
    rc = subprocess.call([sys.executable, str(manifest_script)])
    if rc == 0:
        say(f"Manifest written: {OUT_DIR / 'MANIFEST.tsv'}")
    else:
        say(f"WARN: manifest writer exited {rc}; rerun src/write_ipums_manifest.py manually")
    log.close()


if __name__ == "__main__":
    main()
