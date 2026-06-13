"""
Paper 5 — PRE_REG_031 (recovery velocity / half-life) + PRE_REG_032 (recovery
ceiling), Phases 2+3. Runs on the 6 recovery-from-backsliding cases.

Per case: detect trough (argmin libdem in window) + baseline (max libdem in
lookback before trough), then track per-tier recovery.

Tiers (mirror-order from PRE_REG_012):
  horizontal (recovers first): v2juhcind, v2x_jucon, v2x_horacc
  diagonal   (middle):         v2x_diagacc, v2csprtcpt, v2mecenefm
  vertical   (recovers last):  v2xel_frefair, v2psoppaut, v2x_veracc

PRE_REG_031: recovery_fraction(t) = (val(t)-trough)/(baseline-trough), per
tier (mean of sub-indicators). half-life = years from trough to fraction>=0.5;
right-censored if never reached. Predicted: horizontal HL < diagonal < vertical.

PRE_REG_032: ceiling ratio = val(latest)/val(baseline) per tier. Predicted:
horizontal >=0.90; vertical <0.90 (plateaus below). Overshoot if >1.0.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

VDEM = Path("D:/IDP/data/vdem/vdem_vdem.csv")
OUT = Path("D:/IDP/analysis/paper5_recovery_velocity_ceiling_2026_05_28.json")

# Restrict each tier to 0-1 BOUNDED V-Dem indices (v2x_*) so recovery fractions
# are well-conditioned and tiers are scale-comparable. Latent-scale indices
# (v2juhcind/v2csprtcpt/v2psoppaut/v2mecenefm, ~-4..+4) excluded to avoid the
# near-zero-denominator + scale-mixing pathology that produced exploding ratios.
TIERS = {
    "horizontal": ["v2x_jucon", "v2x_horacc"],
    "diagonal": ["v2x_diagacc"],
    "vertical": ["v2xel_frefair", "v2x_veracc"],
}
MIN_DECLINE = 0.03  # exclude a sub-indicator if |baseline-trough| < this (didn't meaningfully decline)
ALL_IND = [c for cols in TIERS.values() for c in cols]

# case -> (iso, baseline_lookback_start, recovery_end). Trough auto-detected.
# Lookback windows scoped to the SPECIFIC backsliding episode (matching the
# case windows established in PRE_REG_012), so trough auto-detection lands on
# the right episode rather than an earlier unrelated dip (e.g., KOR Park 2016,
# LKA civil-war-end 2009).
CASES = {
    "POL_Tusk": ("POL", 2014, 2025),      # PiS 2015-2023
    "BRA_Lula": ("BRA", 2014, 2025),      # Bolsonaro 2019-2022
    "KOR_Yoon": ("KOR", 2021, 2025),      # Yoon 2022-2024
    "BGD_Yunus": ("BGD", 2014, 2025),     # Hasina late-stage -> Yunus 2024
    "LKA_Sirisena": ("LKA", 2010, 2018),  # Rajapaksa 2010-2014 -> Sirisena 2015-2018
    "ZMB_Hichilema": ("ZMB", 2011, 2025), # Lungu -> Hichilema 2021
}


def main():
    usecols = ["country_text_id", "year", "v2x_libdem"] + ALL_IND
    v = pd.read_csv(VDEM, usecols=usecols, low_memory=False)

    results = {}
    for case, (iso, lb_start, rec_end) in CASES.items():
        sub = v[(v["country_text_id"] == iso) & (v["year"].between(lb_start, rec_end))].sort_values("year")
        if sub.empty:
            results[case] = {"error": "no data"}
            continue
        # trough = argmin libdem; baseline = max libdem strictly before trough
        trough_year = int(sub.loc[sub["v2x_libdem"].idxmin(), "year"])
        pre = sub[sub["year"] < trough_year]
        if pre.empty:
            baseline_year = trough_year
        else:
            baseline_year = int(pre.loc[pre["v2x_libdem"].idxmax(), "year"])

        def val(year, col):
            r = sub[sub["year"] == year]
            return float(r[col].values[0]) if len(r) and not r[col].isna().all() else np.nan

        case_out = {
            "iso": iso, "baseline_year": baseline_year, "trough_year": trough_year,
            "latest_year": int(sub["year"].max()),
            "libdem_baseline": val(baseline_year, "v2x_libdem"),
            "libdem_trough": val(trough_year, "v2x_libdem"),
            "libdem_latest": val(int(sub["year"].max()), "v2x_libdem"),
            "tiers": {},
        }
        latest_year = int(sub["year"].max())
        for tier, inds in TIERS.items():
            # per-tier mean recovery fraction trajectory + ceiling
            half_life = None
            frac_by_year = {}
            for _, rr in sub[sub["year"] >= trough_year].iterrows():
                yr = int(rr["year"])
                fracs = []
                for col in inds:
                    b = val(baseline_year, col); t = val(trough_year, col); x = rr[col]
                    if pd.isna(b) or pd.isna(t) or pd.isna(x) or abs(b - t) < MIN_DECLINE:
                        continue
                    fracs.append((x - t) / (b - t))
                if fracs:
                    frac_by_year[yr] = float(np.mean(fracs))
            # half-life = first year frac>=0.5, in years from trough
            for yr in sorted(frac_by_year):
                if frac_by_year[yr] >= 0.5:
                    half_life = yr - trough_year
                    break
            # ceiling ratio = latest tier value / baseline tier value (mean across inds)
            ceil_ratios = []
            for col in inds:
                b = val(baseline_year, col); x = val(latest_year, col)
                if not pd.isna(b) and not pd.isna(x) and b != 0:
                    ceil_ratios.append(x / b)
            case_out["tiers"][tier] = {
                "half_life_years": half_life,  # None = right-censored
                "ceiling_ratio": float(np.mean(ceil_ratios)) if ceil_ratios else None,
                "latest_recovery_fraction": frac_by_year.get(latest_year),
            }
        results[case] = case_out

    # ---------- PRE_REG_031 velocity verdicts ----------
    print("=" * 90)
    print("PRE_REG_031 — Recovery velocity / half-life by tier (years from trough to 50% recovery)")
    print("=" * 90)
    print(f"{'case':<16}{'base':<6}{'trough':<8}{'H_hl':<8}{'D_hl':<8}{'V_hl':<8}")
    hl_ordered = 0; vert_censored = 0; n = 0
    for case, r in results.items():
        if "tiers" not in r:
            continue
        n += 1
        H = r["tiers"]["horizontal"]["half_life_years"]
        D = r["tiers"]["diagonal"]["half_life_years"]
        V = r["tiers"]["vertical"]["half_life_years"]
        def fmt(x): return "cens" if x is None else f"{x}"
        print(f"{case:<16}{r['baseline_year']:<6}{r['trough_year']:<8}{fmt(H):<8}{fmt(D):<8}{fmt(V):<8}")
        # ordering: horizontal recovers no-slower than vertical (treat censored as +inf)
        Hv = np.inf if H is None else H
        Vv = np.inf if V is None else V
        if Hv <= Vv:
            hl_ordered += 1
        if V is None:
            vert_censored += 1
    print(f"\nPRED A (horizontal HL <= vertical HL in >=5 of {n}): {hl_ordered}/{n} -> {'SUPPORTED' if hl_ordered>=5 else 'CHECK'}")
    print(f"PRED B (vertical right-censored in >=3 of {n}): {vert_censored}/{n} -> {'SUPPORTED' if vert_censored>=3 else 'CHECK'}")

    # ---------- PRE_REG_032 ceiling verdicts ----------
    print("\n" + "=" * 90)
    print("PRE_REG_032 — Recovery ceiling (latest / baseline, per tier)")
    print("=" * 90)
    # AMENDMENT 2026-05-28 (diagnostic-driven): ceiling measured as latest
    # recovery FRACTION (latest-trough)/(baseline-trough), not latest/baseline
    # ratio. Trigger: ratio explodes/goes negative when V-Dem baseline values
    # are near zero (LKA H -2.45, BGD D -0.03). Recovery-fraction is bounded
    # and interpretable: 1.0=full recovery, >1.0=overshoot, <1.0=plateau below.
    print("(ceiling = latest recovery fraction; 1.0=baseline, >1.0=overshoot, <1.0=below)")
    print(f"{'case':<16}{'H_ceil':<9}{'D_ceil':<9}{'V_ceil':<9}")
    horiz_ge90 = 0; vert_lt90 = 0; overshoot = 0; nc = 0
    for case, r in results.items():
        if "tiers" not in r:
            continue
        nc += 1
        H = r["tiers"]["horizontal"]["latest_recovery_fraction"]
        D = r["tiers"]["diagonal"]["latest_recovery_fraction"]
        V = r["tiers"]["vertical"]["latest_recovery_fraction"]
        def f2(x): return "n/a" if x is None else f"{x:.2f}"
        print(f"{case:<16}{f2(H):<9}{f2(D):<9}{f2(V):<9}")
        if H is not None and H >= 0.90: horiz_ge90 += 1
        if V is not None and V < 0.90: vert_lt90 += 1
        if H is not None and H > 1.0: overshoot += 1
    print(f"\nPRED A1 (horizontal ceiling >=0.90 in >=5 of {nc}): {horiz_ge90}/{nc}")
    print(f"PRED A2 (vertical ceiling <0.90 in >=4 of {nc}): {vert_lt90}/{nc}")
    print(f"PRED B (horizontal overshoot >1.0 in >=2 of {nc}): {overshoot}/{nc}")

    out = {
        "cases": results,
        "prereg031": {
            "n": n, "horizontal_le_vertical_HL": hl_ordered, "vertical_censored": vert_censored,
            "predA_supported": bool(hl_ordered >= 5), "predB_supported": bool(vert_censored >= 3),
        },
        "prereg032": {
            "n": nc, "horizontal_ge90": horiz_ge90, "vertical_lt90": vert_lt90, "overshoot": overshoot,
            "predA1_supported": bool(horiz_ge90 >= 5), "predA2_supported": bool(vert_lt90 >= 4),
            "predB_supported": bool(overshoot >= 2),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
