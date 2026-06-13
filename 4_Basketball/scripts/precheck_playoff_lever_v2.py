"""Pre-check v2: tighter cohort + within-player residual variant.

Variant 1 (tightened cohort):
  Same as v1 but years_pro in [0, 3] — rookies through 4th year only.
  Strips peak-window 5th/6th-year players that diluted the prior pass.

Variant 2 (within-player residual):
  DV = residual_in_season_N - residual_in_season_{N-1}  (paired by player).
  Predictor: prior-season (= season N-1) playoff exposure.
  Tests whether playoff exposure CAUSED a lift over the player's own
  baseline, stripping team-quality / starter-status / cohort-of-peers
  confounds that contaminate the between-player comparison.

  Only 23-24 cohort qualifies: needs paired (22-23 residual, 23-24 residual)
  per player. 21-22 audit doesn't exist; 24-25 has no pre-peak coverage.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")
from pathlib import Path

import numpy as np
import pandas as pd

from precheck_playoff_lever import (
    find_v4_audit, prior_season, years_pro_for_season,
)

REPO = Path(".")
PQ = REPO / "data" / "parquet"

STATS = ["PTS", "REB", "AST", "STL", "BLK", "TOV"]
SNR_GATE = 1.5


def welch_snr(treated: np.ndarray, control: np.ndarray) -> tuple[float, float]:
    if len(treated) < 5 or len(control) < 5:
        return float("nan"), float("nan")
    eff = treated.mean() - control.mean()
    se = np.sqrt(treated.var(ddof=1) / len(treated)
                  + control.var(ddof=1) / len(control))
    return eff, eff / se if se > 0 else float("nan")


def load_residuals(stat: str, test_season: str) -> pd.DataFrame | None:
    audit = find_v4_audit(stat, test_season)
    if audit is None:
        return None
    df = pd.read_csv(audit / "per_player_projections.csv")
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    df = df.dropna(subset=["error"])
    return df[["nba_api_id", "error"]].rename(columns={"error": f"err_{test_season}"})


def main():
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    meta["nba_api_id"] = meta["nba_api_id"].astype(int)

    po = pd.read_parquet(PQ / "player_career_season_totals_po.parquet")
    po = po[po["league_id"] == "00"].copy()
    po = po.rename(columns={"player_id": "nba_api_id", "season_id": "season"})
    po["nba_api_id"] = po["nba_api_id"].astype(int)
    po_simple = po.groupby(["nba_api_id", "season"]).agg(
        po_gp=("gp", "sum"),
        po_min=("min", "sum"),
    ).reset_index()

    # ─── Variant 1: tighter cohort ──────────────────────────────────
    print("=" * 75)
    print("VARIANT 1 — tightened cohort (years_pro ∈ [0, 3])")
    print("=" * 75)
    rows = []
    for stat in STATS:
        for ts in ["2022-23", "2023-24"]:  # 24-25 has no pre-peak
            df = load_residuals(stat, ts)
            if df is None:
                continue
            df = df.rename(columns={f"err_{ts}": "error"})
            yp_lookup = dict(zip(meta["nba_api_id"],
                                  years_pro_for_season(meta, ts)))
            df["years_pro"] = df["nba_api_id"].map(yp_lookup)
            cohort = df[df["years_pro"].between(0, 3)].copy()
            if len(cohort) < 15:
                continue
            ps = prior_season(ts)
            po_prior = po_simple[po_simple["season"] == ps]
            cohort = cohort.merge(po_prior[["nba_api_id", "po_gp", "po_min"]],
                                   on="nba_api_id", how="left")
            cohort["po_gp"] = cohort["po_gp"].fillna(0)
            cohort["po_min"] = cohort["po_min"].fillna(0)
            cohort["had_po"] = cohort["po_gp"] > 0

            t = cohort.loc[cohort["had_po"], "error"].values
            c = cohort.loc[~cohort["had_po"], "error"].values
            eff, snr = welch_snr(t, c)
            rows.append({
                "stat": stat, "test_season": ts, "n": len(cohort),
                "n_treated": int(cohort["had_po"].sum()),
                "n_control": int((~cohort["had_po"]).sum()),
                "binary_effect": round(eff, 4) if not np.isnan(eff) else None,
                "binary_snr": round(snr, 3) if not np.isnan(snr) else None,
            })

    out1 = pd.DataFrame(rows)
    print(out1.to_string(index=False))
    print()
    print("Cross-season per stat:")
    for stat in STATS:
        sub = out1[out1["stat"] == stat]
        if len(sub) < 2:
            continue
        signs = "".join("+" if x and x > 0 else ("-" if x and x < 0 else "0")
                          for x in sub["binary_effect"].fillna(0))
        snr_pass = sum(1 for s in sub["binary_snr"]
                        if s is not None and abs(s) >= SNR_GATE)
        verdict = ("PASS" if snr_pass >= 2 and len(set(signs.replace("0", ""))) == 1
                    else "fail")
        print(f"  {stat:<5} signs={signs:<4} snr_pass={snr_pass}/{len(sub)}  "
              f"effects={list(sub['binary_effect'])}  -> {verdict}")

    # ─── Variant 2: within-player residual ───────────────────────────
    print()
    print("=" * 75)
    print("VARIANT 2 — within-player residual (lift = err_23-24 − err_22-23)")
    print("=" * 75)
    rows = []
    for stat in STATS:
        baseline = load_residuals(stat, "2022-23")
        post = load_residuals(stat, "2023-24")
        if baseline is None or post is None:
            continue
        paired = baseline.merge(post, on="nba_api_id", how="inner")
        paired["lift"] = paired["err_2023-24"] - paired["err_2022-23"]
        # Cohort gate at the POST season (23-24)
        yp_lookup = dict(zip(meta["nba_api_id"],
                              years_pro_for_season(meta, "2023-24")))
        paired["years_pro_at_post"] = paired["nba_api_id"].map(yp_lookup)
        for cohort_label, lo, hi in [("[0,6]", 0, 6), ("[0,3]", 0, 3)]:
            cohort = paired[paired["years_pro_at_post"].between(lo, hi)].copy()
            if len(cohort) < 10:
                continue
            # Predictor: 22-23 playoff exposure (the playoffs BETWEEN the two
            # residual measurements)
            po_2223 = po_simple[po_simple["season"] == "2022-23"]
            cohort = cohort.merge(po_2223[["nba_api_id", "po_gp", "po_min"]],
                                   on="nba_api_id", how="left")
            cohort["po_gp"] = cohort["po_gp"].fillna(0)
            cohort["had_po"] = cohort["po_gp"] > 0
            t = cohort.loc[cohort["had_po"], "lift"].values
            c = cohort.loc[~cohort["had_po"], "lift"].values
            eff, snr = welch_snr(t, c)
            rows.append({
                "stat": stat, "cohort": cohort_label, "n_paired": len(cohort),
                "n_treated": int(cohort["had_po"].sum()),
                "n_control": int((~cohort["had_po"]).sum()),
                "lift_effect_treated_minus_control": round(eff, 4)
                    if not np.isnan(eff) else None,
                "snr": round(snr, 3) if not np.isnan(snr) else None,
            })

    out2 = pd.DataFrame(rows)
    print(out2.to_string(index=False))

    print("\nVerdict per cohort tightness:")
    for ch in ["[0,6]", "[0,3]"]:
        sub = out2[out2["cohort"] == ch]
        if sub.empty:
            continue
        n_pass = sum(1 for s in sub["snr"] if s is not None and abs(s) >= SNR_GATE)
        signs = "".join("+" if (e or 0) > 0 else ("-" if (e or 0) < 0 else "0")
                          for e in sub["lift_effect_treated_minus_control"])
        print(f"  cohort {ch:<6} {n_pass}/{len(sub)} stats SNR≥{SNR_GATE}  signs={signs}")


if __name__ == "__main__":
    main()
