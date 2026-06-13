"""2025-26 international stats scrape for the 4 unmatched 2026 draft prospects.

Targets:
  - Sergio De Larrea (Valencia / Joventut, Spanish ACB)
  - Jack Kayil (German BBL or French LNB)
  - Karim Lopez (NZ Breakers, Australian NBL)
  - Luigi Suigo (Italian Lega A)

Source: RealGM (https://basketball.realgm.com) — public, free, no auth, broad
international coverage. URL flow:
  1. https://basketball.realgm.com/search?q=<NAME>   (search results JSON-ish)
  2. https://basketball.realgm.com/player/<Slug>/Summary/<ID>  (player page HTML)

Parses 2025-26 row from the international stats table.

Output:
    data/parquet/draft_2026_intl_supplement.parquet  (one row per matched prospect)
"""
from __future__ import annotations
import sys, time, urllib.request, urllib.parse, re
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NBA-Research/1.0"
OUT = Path("D:/NBA Projections/data/parquet/draft_2026_intl_supplement.parquet")

TARGETS = [
    ("Sergio De Larrea", "PG"),
    ("Jack Kayil", "PG"),
    ("Karim Lopez", "PF"),
    ("Luigi Suigo", "C"),
]


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"__ERR__ {e}"


def search_realgm(name: str) -> str | None:
    """Hit RealGM search; return first /player/.../Summary/<id> URL."""
    q = urllib.parse.quote(name)
    url = f"https://basketball.realgm.com/search?q={q}"
    html = fetch(url)
    if html.startswith("__ERR__"):
        return None
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if "/player/" in h and "/Summary/" in h:
            text = a.get_text(strip=True)
            if name.split()[-1].lower() in text.lower():
                return f"https://basketball.realgm.com{h}"
    return None


def parse_player_2025_26(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    for tbl in tables:
        caption = tbl.find("caption")
        head = " ".join([(caption.get_text(strip=True) if caption else "")] + [th.get_text(strip=True) for th in tbl.find_all("th")[:15]])
        if not any(k in head for k in ["International", "EuroLeague", "Euroleague", "Per Game"]):
            continue
        for tr in tbl.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if not cells:
                continue
            season_cell = cells[0]
            if season_cell.startswith("25-26") or "2025-26" in season_cell or season_cell.startswith("25/26"):
                return {"season_raw": season_cell, "row": cells, "table_head": head[:120]}
    return None


def fallback_player_page(name: str) -> str | None:
    slug = name.replace(" ", "-")
    for nid in range(2_000_000, 2_300_000, 50_000):
        url = f"https://basketball.realgm.com/player/{slug}/Summary/{nid}"
        html = fetch(url)
        if html.startswith("__ERR__"):
            continue
        if "Player Not Found" not in html and slug.replace("-", " ").lower() in html.lower():
            return url
        time.sleep(0.3)
    return None


def main():
    print("=== 2025-26 intl scrape via RealGM ===")
    out_rows = []
    for name, pos in TARGETS:
        print(f"\n--- {name} ({pos}) ---")
        url = search_realgm(name)
        if not url:
            print(f"  search miss; trying fallback ID scan...")
            url = fallback_player_page(name)
        if not url:
            out_rows.append({"player_name": name, "position": pos, "status": "SEARCH_MISS", "url": None})
            continue
        print(f"  page: {url}")
        time.sleep(1.0)
        html = fetch(url)
        if html.startswith("__ERR__"):
            out_rows.append({"player_name": name, "position": pos, "status": "FETCH_ERR", "url": url})
            continue
        parsed = parse_player_2025_26(html)
        if parsed is None:
            out_rows.append({"player_name": name, "position": pos, "status": "NO_2025_26_ROW", "url": url})
            continue
        out_rows.append({
            "player_name": name, "position": pos, "status": "OK",
            "url": url, "season_raw": parsed.get("season_raw"),
            "row_cells": "|".join(parsed.get("row", [])[:25]),
            "table_head": parsed.get("table_head"),
        })
        print(f"  ✓ found 2025-26 row: {parsed.get('row')[:10]}")

    sup = pd.DataFrame(out_rows)
    sup.to_parquet(OUT, index=False)
    sup.to_csv(OUT.with_suffix(".csv"), index=False)
    print(f"\nwrote: {OUT}")
    print(sup[["player_name", "position", "status", "url"]].to_string(index=False))


if __name__ == "__main__":
    main()
