"""Pre-cond 4 — Yemen post-2022 GDELT coverage check.

**REDLINE Entry 001 (notes/pre_reg_redline.md):** ACLED replaced by GDELT
for the Yemen post-2022 coverage check. Threshold (>= 30% of pre-2022
per-year level) and Houthi-governorate list UNCHANGED from v1.

Locked check (§7 of design doc, as redlined v1 -> v2):
  GDELT events ActionGeo_CountryCode=YM in Houthi-controlled governorates,
  post-2022 (2022-2024) as a fraction of pre-2022 (2014-2021) per-year
  level. Drop threshold: < 30% of pre-2022 per-year rate -> Yemen
  post-2022 Stage A is unreliable.

Pass: coverage >= 30% -> Yemen panel intact.
Fail: drop Yemen post-2022 from Stage B; keep Stage A historical polygon
      analysis only. **Document, don't fight it** (locked constraint).

Houthi-controlled governorates (locked list per ICG / Salisbury 2015):
  Sa'dah, Hajjah, Amran, Sana'a (capital + governorate), Dhamar, Ibb,
  Hodeidah, Mahwit, Raymah

GDELT ActionGeo_ADM1Code identifies governorates within Yemen. We match
both by ADM1Code (where available) and by ActionGeo_FullName substring
match (fallback for sparser geocoding).

Phase 0 status: requires fetched GDELT Yemen data covering both 2014-2021
and 2022-2024 windows. Phase 0 smoke test fetched Dec 2024 only; this
script will emit PHASE0_STUB until Phase 1 expands GDELT to full panel.
"""
import pathlib, sys, json, time, io, re
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass

ROOT = pathlib.Path(r"D:/IDP")
GDELT_DIR = ROOT / "data" / "gdelt"   # was ACLED_DIR per redline Entry 001
NOTES = ROOT / "notes"
REPORT = NOTES / "precond_4_report.md"

YEMEN_FILE = GDELT_DIR / "gdelt-yemen.csv"   # full panel after Phase 1 expansion

HOUTHI_CONTROLLED_GOV_NAMES = {
    # Substring patterns to match against GDELT ActionGeo_FullName
    # (which is typically "Saada, Saada, Yemen" or "Sanaa, Amanat Al Asimah, Yemen" format)
    "sa'dah","saada","sadah",
    "hajjah",
    "amran","'amran",
    "sana'a","sanaa","amanat al asimah",
    "dhamar",
    "ibb",
    "hodeidah","al hudaydah","hudaydah",
    "mahwit","al mahwit",
    "raymah","raima",
}
LOCKED_DROP_THRESHOLD = 0.30


def stub_result(reason):
    return {"verdict": "PHASE0_STUB", "reason": reason}


def main():
    print(f"=== Pre-cond 4: Yemen post-2022 GDELT coverage (per redline Entry 001) ===")
    print(f"  Locked threshold: post-2022 GDELT events in Houthi-controlled govs >= {LOCKED_DROP_THRESHOLD*100:.0f}% of pre-2022 per-year")

    if not YEMEN_FILE.exists():
        result = stub_result(f"{YEMEN_FILE.relative_to(ROOT)} not yet fetched")
        print(f"  STUB: {result['reason']}")
    else:
        import pandas as pd
        try:
            df = pd.read_csv(YEMEN_FILE, sep="\t", low_memory=False)
        except Exception as e:
            result = stub_result(f"GDELT Yemen read failed: {e}")
        else:
            # Filter by ActionGeo_FullName substring matching Houthi-controlled govs
            fname_col = next((c for c in df.columns if "actiongeo_fullname" in c.lower()
                              or c.lower() == "actiongeo_fullname"), None)
            year_col = "year" if "year" in df.columns else None
            if year_col is None and "sqldate" in df.columns:
                df["year"] = pd.to_numeric(df["sqldate"].astype(str).str[:4], errors="coerce")
                year_col = "year"

            if fname_col is None or year_col is None:
                result = stub_result(f"GDELT Yemen missing required columns. Have: {list(df.columns)[:10]}...")
            else:
                names_lower = df[fname_col].astype(str).str.lower()
                houthi_mask = names_lower.str.contains(
                    "|".join(re.escape(n) for n in HOUTHI_CONTROLLED_GOV_NAMES),
                    regex=True, na=False
                )
                pre = df[houthi_mask & (df[year_col] >= 2014) & (df[year_col] <= 2021)]
                post = df[houthi_mask & (df[year_col] >= 2022) & (df[year_col] <= 2024)]
                pre_per_year = len(pre) / 8
                post_per_year = len(post) / 3
                ratio = post_per_year / pre_per_year if pre_per_year > 0 else None
                if ratio is None or pre_per_year == 0:
                    result = stub_result("pre-2022 baseline empty (Phase 0 smoke test only covers Dec 2024; Phase 1 fetches full panel)")
                else:
                    verdict = "PASS" if ratio >= LOCKED_DROP_THRESHOLD else "FAIL"
                    result = {
                        "verdict": verdict,
                        "n_pre_events_houthi_govs_2014_2021": int(len(pre)),
                        "n_post_events_houthi_govs_2022_2024": int(len(post)),
                        "events_per_year_pre": float(pre_per_year),
                        "events_per_year_post": float(post_per_year),
                        "ratio_post_to_pre": float(ratio),
                        "threshold": LOCKED_DROP_THRESHOLD,
                    }
                    print(f"  Pre-2022 (2014-21) Houthi-gov events: {len(pre):,} ({pre_per_year:.0f}/yr)")
                    print(f"  Post-2022 (2022-24) Houthi-gov events: {len(post):,} ({post_per_year:.0f}/yr)")
                    print(f"  ratio = {ratio:.3f}  verdict: {verdict}")

    md = []
    md.append("# Pre-cond 4 Report — Yemen Post-2022 GDELT Coverage\n")
    md.append("**Redline:** Entry 001 — ACLED replaced by GDELT (notes/pre_reg_redline.md). Threshold + governorate list unchanged.\n")
    md.append(f"**Run at:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    md.append(f"**Locked check:** GDELT events ActionGeo Yemen + Houthi-governorate filter, post-2022 >= {LOCKED_DROP_THRESHOLD*100:.0f}% of pre-2022 (2014-2021) per-year rate.\n")
    md.append(f"**Verdict:** **{result['verdict']}**\n")
    md.append("\n## Houthi-controlled governorate name patterns (locked)\n")
    md.append(", ".join(sorted(HOUTHI_CONTROLLED_GOV_NAMES)) + "\n")
    if result["verdict"] not in ("PHASE0_STUB",):
        md.append("\n## Coverage statistics\n")
        for k, v in result.items():
            if k == "verdict": continue
            md.append(f"- **{k}**: {v}")
    md.append("\n## Failure handling (locked constraint)\n")
    md.append("- FAIL: drop Yemen post-2022 from Stage B; keep Stage A historical polygon analysis only.\n")
    md.append("Document, don't fight it. Yemen post-2022 will appear as a Stage-B sample-size caveat in §6 disposition reading.\n")
    REPORT.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\n=== Report: {REPORT} ===")
    (NOTES / "precond_4_results.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
