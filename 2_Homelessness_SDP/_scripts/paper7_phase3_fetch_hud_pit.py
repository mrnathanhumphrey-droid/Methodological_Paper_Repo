"""
Paper 7 Phase 3 — fetch HUD PIT master workbook (2007-2024 by CoC).

Single keyless source: HUD USER portal .xlsb workbook. One sheet per year;
each sheet is CoC x sub-population (Overall / Chronically Homeless / Veterans /
Family / Youth / sheltered-unsheltered splits, columns vary by year).

We download the raw file only here (chain-of-custody). Parsing happens in
paper7_phase3_build_panel.py so the raw bytes are hashed once and never mutated.
"""
from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

URL = "https://www.huduser.gov/portal/sites/default/files/xls/2007-2024-PIT-Counts-by-CoC.xlsb"
OUT = Path(r"D:/IDP/data/paper7/hud_pit")
OUT.mkdir(parents=True, exist_ok=True)
DEST = OUT / "2007-2024-PIT-Counts-by-CoC.xlsb"

UA = "Mozilla/5.0 (research; IDP substrate-9 Paper 7; contact mr.nathanhumphrey@gmail.com)"


def main() -> None:
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    print(f"[hud_pit] GET {URL}")
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    DEST.write_bytes(data)
    sha = hashlib.sha256(data).hexdigest()
    print(f"[hud_pit] wrote {DEST} ({len(data)/1e6:.2f} MB)")
    print(f"[hud_pit] sha256={sha}")


if __name__ == "__main__":
    main()
