"""
Generate the Resolve Lottery 2026 post-mortem doc from actual draft results.

Usage:
    1. Fill in D:/NBA Projections/data/draft_2026_actual_results.csv with the actual draft
       (pick number → player name). Picks 1-60.
    2. Run: python lottery_2026_postmortem.py
    3. Output: D:/NBA Projections/docs/RESOLVE_LOTTERY_2026_POSTMORTEM.md

Discipline: the LOCKED predictions are baked in below. Do NOT edit them.
"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import date

# ===== LOCKED PRE-REGISTRATION (do not edit) =====
LOCK_DATE = "2026-06-07"

RESOLVE_TOP14 = [
    (1, "Cameron Boozer"),
    (2, "Joshua Jefferson"),
    (3, "AJ Dybantsa"),
    (4, "Nate Ament"),
    (5, "Amari Allen"),
    (6, "Caleb Wilson"),
    (7, "Aday Mara"),
    (8, "Labaron Philon Jr."),
    (9, "Ebuka Okorie"),
    (10, "Hannes Steinbach"),
    (11, "Darryn Peterson"),
    (12, "Jack Kayil"),
    (13, "Tyler Tanner"),
    (14, "Christian Anderson"),
]

HIGH_CALLS = [
    ("Aday Mara", 7, "late-1st / undrafted"),
    ("Caleb Wilson", 6, "mid-1st (15-25)"),
    ("Hannes Steinbach", 10, "2nd round"),
    ("Ebuka Okorie", 9, "late-2nd / undrafted"),
    ("Amari Allen", 5, "mid-1st"),
]

LOW_CALLS = [
    ("Koa Peat", "outside top-14 (v3 #49)", "top-5"),
    ("Baba Miller", "#25 (v3 #53)", "top-15"),
    ("Karim Lopez", "outside lottery", "mid-1st"),
]

TOP3_LOCK = ["Cameron Boozer", "Joshua Jefferson", "AJ Dybantsa"]


def fuzzy_pick(actual_df, name):
    """Find a player's actual pick number by fuzzy name match."""
    if actual_df is None or actual_df.empty:
        return None
    name_lower = name.lower().replace(".", "").replace(",", "").strip()
    for _, r in actual_df.iterrows():
        if pd.isna(r.get("player_name", "")):
            continue
        actual_name = str(r["player_name"]).lower().replace(".", "").replace(",", "").strip()
        # exact or last-name match
        if name_lower in actual_name or actual_name in name_lower:
            return int(r["pick"])
        # last name only
        last = name_lower.split()[-1]
        if last in actual_name:
            return int(r["pick"])
    return None


def verdict_high_call(actual_pick, resolve_pick, public_band):
    """HIGH call = we said higher than public. Hit if actual >= resolve OR actual <= 14 when public said 2nd round."""
    if actual_pick is None:
        return "UNDRAFTED" + (" — HIT (public expected 2nd/UDFA)" if "undrafted" in public_band.lower() else " — MISS")
    if actual_pick <= 14:
        return f"actual #{actual_pick} (LOTTERY) — **HIT**"
    if "2nd round" in public_band.lower() and actual_pick <= 30:
        return f"actual #{actual_pick} (1st round) — **HIT**"
    if "undrafted" in public_band.lower() and actual_pick <= 30:
        return f"actual #{actual_pick} (1st round) — **HIT**"
    if "15-25" in public_band:
        return f"actual #{actual_pick} — {'HIT' if actual_pick < 15 else 'MISS'}"
    return f"actual #{actual_pick} — MISS"


def verdict_low_call(actual_pick, resolve_band, public_band):
    """LOW call = we said lower than public."""
    if actual_pick is None:
        return "UNDRAFTED — **HIT** (public expected 1st round)"
    if "outside top-14" in resolve_band.lower() and actual_pick > 14:
        return f"actual #{actual_pick} — **HIT**"
    if "outside lottery" in resolve_band.lower() and actual_pick > 14:
        return f"actual #{actual_pick} — **HIT**"
    if "top-15" in public_band.lower() and actual_pick > 15:
        return f"actual #{actual_pick} — **HIT**"
    if "top-5" in public_band.lower() and actual_pick > 5:
        return f"actual #{actual_pick} — **HIT**"
    return f"actual #{actual_pick} — MISS"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="D:/NBA Projections/data/draft_2026_actual_results.csv",
                    help="CSV with actual draft results (pick, player_name)")
    ap.add_argument("--template", default="D:/NBA Projections/docs/RESOLVE_LOTTERY_2026_POSTMORTEM_TEMPLATE.md",
                    help="Template markdown file")
    ap.add_argument("--out", default="D:/NBA Projections/docs/RESOLVE_LOTTERY_2026_POSTMORTEM.md",
                    help="Output markdown")
    ap.add_argument("--draft-date", default=None, help="Draft date YYYY-MM-DD")
    args = ap.parse_args()

    actual_df = None
    if Path(args.results).exists():
        actual_df = pd.read_csv(args.results)
        actual_df = actual_df.dropna(subset=["player_name"])
        actual_df["player_name"] = actual_df["player_name"].astype(str).str.strip()
    else:
        print(f"[postmortem] No actual results yet at {args.results}.")
        print("[postmortem] Generating template with placeholders for visual inspection.")
        actual_df = pd.DataFrame(columns=["pick", "player_name", "team"])

    # Rank-delta table for lottery
    rank_delta_rows = []
    deltas = []
    exact = 0; within2 = 0; within5 = 0
    for resolve_pick, name in RESOLVE_TOP14:
        actual = fuzzy_pick(actual_df, name)
        if actual is None:
            row = f"| {resolve_pick} | UNDRAFTED | — | {name} | MISS (UDFA) |"
        else:
            d = actual - resolve_pick
            deltas.append(abs(d))
            if d == 0: exact += 1
            if abs(d) <= 2: within2 += 1
            if abs(d) <= 5: within5 += 1
            result = "EXACT" if d == 0 else (f"+{d}" if d > 0 else str(d))
            row = f"| {resolve_pick} | {actual} | {result} | {name} | |"
        rank_delta_rows.append(row)
    rank_delta_table = "\n".join(rank_delta_rows)

    # HIGH calls
    high_hits = 0
    high_rows = []
    for name, resolve_pick, public in HIGH_CALLS:
        actual = fuzzy_pick(actual_df, name)
        verdict = verdict_high_call(actual, resolve_pick, public) if actual is not None or "undrafted" in public else (
            "UNDRAFTED — HIT" if "undrafted" in public.lower() else "UNDRAFTED — MISS")
        if "HIT" in verdict:
            high_hits += 1
        high_rows.append(f"| {name} | #{resolve_pick} | {public} | {actual if actual is not None else 'UNDRAFTED'} | {verdict} |")

    # LOW calls
    low_hits = 0
    low_rows = []
    for name, resolve_band, public in LOW_CALLS:
        actual = fuzzy_pick(actual_df, name)
        verdict = verdict_low_call(actual, resolve_band, public)
        if "HIT" in verdict:
            low_hits += 1
        low_rows.append(f"| {name} | {resolve_band} | {public} | {actual if actual is not None else 'UNDRAFTED'} | {verdict} |")

    # Top-3 lock
    pick1 = actual_df[actual_df["pick"] == 1]["player_name"].iloc[0] if not actual_df.empty and (actual_df["pick"] == 1).any() else "?"
    top3_actual = []
    for p in [1, 2, 3]:
        match = actual_df[actual_df["pick"] == p]
        if not match.empty:
            top3_actual.append(str(match.iloc[0]["player_name"]))
        else:
            top3_actual.append(f"pick-{p}-unknown")
    top3_lock_hit = any(p == pick1 for p in TOP3_LOCK)
    top3_verdict = "**HIT** — one of our locked top-3 took #1" if top3_lock_hit else "MISS"
    top3_status = "HIT" if top3_lock_hit else "MISS"

    overall_bold = ((high_hits + low_hits + (1 if top3_lock_hit else 0))
                    / (len(HIGH_CALLS) + len(LOW_CALLS) + 1)) if actual_df is not None and not actual_df.empty else 0
    overall_bold_pct = f"{overall_bold*100:.0f}%" if overall_bold > 0 else "{{N/A — input not filled}}"

    mean_abs = f"{np.mean(deltas):.2f}" if deltas else "{{N/A}}"
    median_abs = f"{np.median(deltas):.1f}" if deltas else "{{N/A}}"

    # Read template and substitute
    template = Path(args.template).read_text(encoding="utf-8")

    substitutions = {
        "{{draft_date}}": args.draft_date or "{{TBD}}",
        "{{scoring_date}}": str(date.today()) if not actual_df.empty else "{{TBD — fill once draft happens}}",
        "{{days_locked}}": "{{TBD}}",
        "{{tldr_summary}}": "{{Auto-summary will be filled once actual results are in.}}",
        "{{rank_delta_table}}": rank_delta_table,
        "{{mean_abs_delta_lottery}}": mean_abs,
        "{{median_abs_delta}}": median_abs,
        "{{exact_match_count}}": str(exact),
        "{{within_2_count}}": str(within2),
        "{{within_5_count}}": str(within5),
        "{{mara_actual}}": str(fuzzy_pick(actual_df, "Aday Mara") or "UNDRAFTED"),
        "{{wilson_actual}}": str(fuzzy_pick(actual_df, "Caleb Wilson") or "UNDRAFTED"),
        "{{steinbach_actual}}": str(fuzzy_pick(actual_df, "Hannes Steinbach") or "UNDRAFTED"),
        "{{okorie_actual}}": str(fuzzy_pick(actual_df, "Ebuka Okorie") or "UNDRAFTED"),
        "{{allen_actual}}": str(fuzzy_pick(actual_df, "Amari Allen") or "UNDRAFTED"),
        "{{mara_verdict}}": verdict_high_call(fuzzy_pick(actual_df, "Aday Mara"), 7, "late-1st / undrafted"),
        "{{wilson_verdict}}": verdict_high_call(fuzzy_pick(actual_df, "Caleb Wilson"), 6, "mid-1st (15-25)"),
        "{{steinbach_verdict}}": verdict_high_call(fuzzy_pick(actual_df, "Hannes Steinbach"), 10, "2nd round"),
        "{{okorie_verdict}}": verdict_high_call(fuzzy_pick(actual_df, "Ebuka Okorie"), 9, "late-2nd / undrafted"),
        "{{allen_verdict}}": verdict_high_call(fuzzy_pick(actual_df, "Amari Allen"), 5, "mid-1st"),
        "{{peat_actual}}": str(fuzzy_pick(actual_df, "Koa Peat") or "UNDRAFTED"),
        "{{miller_actual}}": str(fuzzy_pick(actual_df, "Baba Miller") or "UNDRAFTED"),
        "{{lopez_actual}}": str(fuzzy_pick(actual_df, "Karim Lopez") or "UNDRAFTED"),
        "{{peat_verdict}}": verdict_low_call(fuzzy_pick(actual_df, "Koa Peat"), "outside top-14", "top-5"),
        "{{miller_verdict}}": verdict_low_call(fuzzy_pick(actual_df, "Baba Miller"), "#25", "top-15"),
        "{{lopez_verdict}}": verdict_low_call(fuzzy_pick(actual_df, "Karim Lopez"), "outside lottery", "mid-1st"),
        "{{pick1_player}}": pick1,
        "{{actual_top3}}": ", ".join(top3_actual),
        "{{top3_lock_verdict}}": top3_verdict,
        "{{high_call_hits}}": str(high_hits),
        "{{low_call_hits}}": str(low_hits),
        "{{top3_lock_status}}": top3_status,
        "{{overall_bold_pct}}": overall_bold_pct,
        "{{resolve_mean_abs}}": "{{TBD per-method analysis}}",
        "{{resolve_best}}": "{{TBD}}",
        "{{resolve_worst}}": "{{TBD}}",
        "{{v3_mean_abs}}": "{{TBD}}",
        "{{v3_best}}": "{{TBD}}",
        "{{v3_worst}}": "{{TBD}}",
        "{{hand_mean_abs}}": "{{TBD}}",
        "{{hand_best}}": "{{TBD}}",
        "{{hand_worst}}": "{{TBD}}",
        "{{advanced_mean_abs}}": "{{TBD}}",
        "{{advanced_best}}": "{{TBD}}",
        "{{advanced_worst}}": "{{TBD}}",
        "{{method_takeaway}}": "{{TBD}}",
        "{{honest_losses_section}}": "{{TBD — write after seeing the results}}",
        "{{intl_eval}}": "{{TBD}}",
        "{{advanced_unconditioned_eval}}": "{{TBD}}",
        "{{def_metrics_eval}}": "{{TBD}}",
        "{{lock_for_2027}}": "{{TBD — articulate after sufficient retrospective}}",
    }

    out = template
    for k, v in substitutions.items():
        out = out.replace(k, str(v))
    Path(args.out).write_text(out, encoding="utf-8")
    print(f"WROTE {args.out}")
    if not actual_df.empty:
        print(f"\nSummary:")
        print(f"  Lottery exact matches: {exact}/14")
        print(f"  Within 2 picks:        {within2}/14")
        print(f"  Within 5 picks:        {within5}/14")
        print(f"  Mean absolute delta:   {mean_abs}")
        print(f"  HIGH-call hits:        {high_hits}/{len(HIGH_CALLS)}")
        print(f"  LOW-call hits:         {low_hits}/{len(LOW_CALLS)}")
        print(f"  Top-3 lock:            {top3_status}")
        print(f"  Overall bold-call:     {overall_bold_pct}")


if __name__ == "__main__":
    main()
