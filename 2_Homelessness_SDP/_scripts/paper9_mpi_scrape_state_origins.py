"""
Paper 9 Phase 1 - Scrape MPI per-state unauthorized-immigrant origin estimates.

MPI state profile pages at /data/unauthorized-immigrant-population/state/XX contain
a "Top Countries of Birth" table giving the top 5 origins by unauthorized population
estimate, plus regional aggregates. We need state x origin estimates for the
cross-walk's "Undocumented" track.

Limitation: only top-5 origins per state; smaller P9 origins (e.g., Eritrea,
Myanmar, DRC) may not appear in a given state's table -> they get NaN, treated
as below MPI's per-state reporting threshold.
"""
from __future__ import annotations
import sys, time, urllib.request, re
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")

OUT_DIR = Path("D:/IDP/data/paper9/mpi")
RAW_DIR = OUT_DIR / "state_pages"
RAW_DIR.mkdir(parents=True, exist_ok=True)

STATE_ABBR = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","DC","FL","GA","HI","ID","IL","IN",
    "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH",
    "NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT",
    "VT","VA","WA","WV","WI","WY",
]
STATE_ABBR_TO_NAME = {
    "AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California",
    "CO":"Colorado","CT":"Connecticut","DE":"Delaware","DC":"District of Columbia",
    "FL":"Florida","GA":"Georgia","HI":"Hawaii","ID":"Idaho","IL":"Illinois",
    "IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana",
    "ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota",
    "MS":"Mississippi","MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada",
    "NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico","NY":"New York",
    "NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma","OR":"Oregon",
    "PA":"Pennsylvania","RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota",
    "TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia",
    "WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming",
}
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def fetch_state(abbr: str) -> str | None:
    fp = RAW_DIR / f"mpi_state_{abbr}.html"
    if fp.exists() and fp.stat().st_size > 5000:
        return fp.read_text(encoding="utf-8", errors="ignore")
    url = f"https://www.migrationpolicy.org/data/unauthorized-immigrant-population/state/{abbr}"
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        fp.write_bytes(data)
        time.sleep(0.4)
        return data.decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  {abbr}: FAIL {type(e).__name__} {str(e)[:80]}")
        return None


def parse_state_origins(html: str, state_name: str) -> pd.DataFrame:
    """Extract Top Countries of Birth section from the state profile HTML."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    # Find the topcountries subheading row, then read sibling rows until next subheading
    sub = soup.find("tr", id="topcountries")
    if not sub:
        return pd.DataFrame(rows)
    # walk subsequent <tr> until we hit another datasheet-subheading
    cur = sub.find_next_sibling("tr")
    while cur is not None:
        cls = cur.get("class", []) or []
        if "datasheet-subheading" in cls:
            break
        cells = cur.find_all("td")
        if len(cells) >= 3:
            origin = cells[0].get_text(strip=True)
            estimate_s = cells[1].get_text(strip=True).replace(",", "").replace(" ", "")
            pct_s = cells[2].get_text(strip=True).replace("%", "")
            try:
                est = int(estimate_s) if estimate_s.isdigit() else None
            except Exception:
                est = None
            try:
                pct = float(pct_s)
            except Exception:
                pct = None
            if origin and est is not None:
                rows.append({"state": state_name, "origin_raw": origin,
                             "mpi_undoc_est": est, "pct_of_state": pct})
        cur = cur.find_next_sibling("tr")
    return pd.DataFrame(rows)


# Canonicalize MPI origin labels to P9 canonical names
MPI_ORIGIN_CANON = {
    "Mexico": "Mexico",
    "Guatemala": "Guatemala",
    "Honduras": "Honduras",
    "El Salvador": "El Salvador",
    "Venezuela": "Venezuela",
    "Cuba": "Cuba",
    "Haiti": "Haiti",
    "Ecuador": "Ecuador",
    "Colombia": "Colombia",
    "Dominican Republic": "Dominican Republic",
    "Brazil": "Brazil",
    "China": "China",
    "India": "India",
    "Philippines": "Philippines",
    "Nicaragua": "Nicaragua",
    "Ukraine": "Ukraine",
    "Afghanistan": "Afghanistan",
    "Syria": "Syria",
    "Iraq": "Iraq",
    "Myanmar": "Myanmar", "Burma": "Myanmar",
    "Dem. Rep. Congo": "DRC", "DR Congo": "DRC", "Democratic Republic of the Congo": "DRC",
    "Eritrea": "Eritrea",
    "Somalia": "Somalia",
    "Sudan": "Sudan",
}


def main():
    print(f"Scraping {len(STATE_ABBR)} states from MPI...")
    all_rows = []
    failed = []
    for abbr in STATE_ABBR:
        html = fetch_state(abbr)
        if html is None:
            failed.append(abbr); continue
        state_name = STATE_ABBR_TO_NAME[abbr]
        df = parse_state_origins(html, state_name)
        print(f"  {abbr} ({state_name}): {len(df)} origin rows")
        all_rows.append(df)

    if failed:
        print(f"\nFailed states: {failed}")

    full = pd.concat(all_rows, ignore_index=True)
    full["origin"] = full["origin_raw"].map(MPI_ORIGIN_CANON).fillna(full["origin_raw"])
    print(f"\nTotal state-origin rows: {len(full):,}")
    print(f"Unique origins seen: {full['origin'].nunique()}")
    print(f"Top origins by total estimate:")
    print(full.groupby("origin")["mpi_undoc_est"].sum().sort_values(ascending=False).head(20).to_string())

    out = OUT_DIR / "mpi_2023_unauthorized_state_origin_top5.csv"
    full.to_csv(out, index=False)
    print(f"\nSaved {len(full):,} rows -> {out}")

    # P9-origin pivot
    P9 = ["Ukraine","Venezuela","Cuba","Honduras","El Salvador","Guatemala","Haiti",
          "Afghanistan","Syria","Iraq","Myanmar","DRC","Eritrea","Somalia","Sudan"]
    p9 = full[full["origin"].isin(P9)]
    pv = p9.pivot_table(index="state", columns="origin", values="mpi_undoc_est",
                        aggfunc="sum", fill_value=0)
    print(f"\nP9-origin state coverage: {len(pv)} states with at-least-one P9-origin row")
    print(f"P9 origins observed at state-level: {sorted(p9['origin'].unique())}")
    print(f"P9 origins NEVER in any state top-5: {sorted(set(P9) - set(p9['origin'].unique()))}")
    pv["P9_total"] = pv.sum(axis=1)
    cols_present = [c for c in P9 if c in pv.columns]
    print(f"\nTop 15 states by P9-origin undocumented total:")
    print(pv.sort_values("P9_total", ascending=False).head(15)[cols_present + ["P9_total"]].to_string())


if __name__ == "__main__":
    main()
