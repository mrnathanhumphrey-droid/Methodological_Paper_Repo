"""Pre-check v3 — within-player residual with usage-proxy dose predictor.

Pointed swap from v2: replace `log(po_min+1)` with `po_usg_proxy` as the
Tier A dose predictor. Tests the mechanism that PLAYOFF LOAD (carrying
offensive responsibility) — not just minutes — drives the next-season
lift.

usage proxy:
  po_usg_proxy = (po_FGA + 0.44 * po_FTA + po_TOV) * 36 / po_min

Per-36 offensive-load events (shot attempts + FT trips + turnovers).
Same numerator as formal NBA USG% but un-team-normalized — fine for
within-cohort ranking and far simpler to compute.

Single cohort tonight (22-23 → 23-24 paired). Override criterion:
SNR ≥ 3 across BOTH confirmed cohorts triggers backward-extension.
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


def welch_snr(t: np.ndarray, c: np.ndarray) -> tuple[float, float]:
    if len(t) < 5 or len(c) < 5:
        return float("nan"), float("nan")
    eff = t.mean() - c.mean()
    se = np.sqrt(t.var(ddof=1) / len(t) + c.var(ddof=1) / len(c))
    return eff, eff / se if se > 0 else float("nan")


def pearson_snr(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Pearson r and its t-style SNR (r / SE(r))."""
    if len(x) < 6 or x.std() == 0 or y.std() == 0:
        return float("nan"), float("nan")
    r = float(np.corrcoef(x, y)[0, 1])
    n = len(x)
    se = np.sqrt((1 - r * r) / (n - 2))
    return r, r / se if se > 0 else float("nan")


def load_residuals(stat: str, ts: str) -> pd.DataFrame | None:
    audit = find_v4_audit(stat, ts)
    if audit is None:
        return None
    df = pd.read_csv(audit / "per_player_projections.csv")
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    df = df.dropna(subset=["error"])
    return df[["nba_api_id", "error"]].rename(columns={"error": f"err_{ts}"})


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
        po_fga=("fga", "sum"),
        po_fta=("fta", "sum"),
        po_tov=("tov", "sum"),
    ).reset_index()
    # Usage-rate proxy: per-36 offensive-load events
    po_simple["po_usg_proxy"] = np.where(
        po_simple["po_min"] > 0,
        (po_simple["po_fga"] + 0.44 * po_simple["po_fta"] + po_simple["po_tov"])
            * 36.0 / po_simple["po_min"],
        np.nan,
    )

    print("=" * 78)
    print("Within-player lift = err_2023-24 − err_2022-23")
    print("Predictor: 22-23 playoff usage-proxy (Tier A, mechanism-pointed)")
    print("=" * 78)

    rows = []
    for stat in STATS:
        baseline = load_residuals(stat, "2022-23")
        post = load_residuals(stat, "2023-24")
        if baseline is None or post is None:
            continue
        paired = baseline.merge(post, on="nba_api_id", how="inner")
        paired["lift"] = paired["err_2023-24"] - paired["err_2022-23"]

        yp = years_pro_for_season(meta, "2023-24")
        yp_lookup = dict(zip(meta["nba_api_id"], yp))
        paired["years_pro"] = paired["nba_api_id"].map(yp_lookup)

        po_2223 = po_simple[po_simple["season"] == "2022-23"]
        paired = paired.merge(
            po_2223[["nba_api_id", "po_gp", "po_min", "po_usg_proxy"]],
            on="nba_api_id", how="left",
        )
        paired["po_gp"] = paired["po_gp"].fillna(0)
        paired["po_usg_proxy"] = paired["po_usg_proxy"].fillna(0.0)
        paired["had_po"] = paired["po_gp"] > 0

        for label, lo, hi in [("[0,6]", 0, 6), ("[0,3]", 0, 3)]:
            cohort = paired[paired["years_pro"].between(lo, hi)].copy()
            if len(cohort) < 10:
                continue

            # Binary
            t = cohort.loc[cohort["had_po"], "lift"].values
            c = cohort.loc[~cohort["had_po"], "lift"].values
            bin_eff, bin_snr = welch_snr(t, c)

            # Usage-proxy dose, on the FULL cohort (zero-usage for non-playoff)
            r_full, snr_full = pearson_snr(cohort["po_usg_proxy"].values,
                                            cohort["lift"].values)

            # Usage-proxy dose, on TREATED ONLY (does usage explain lift among
            # players who DID make playoffs?)
            treated = cohort[cohort["had_po"]]
            r_treated, snr_treated = (float("nan"), float("nan"))
            if len(treated) >= 6:
                r_treated, snr_treated = pearson_snr(
                    treated["po_usg_proxy"].values, treated["lift"].values,
                )

            rows.append({
                "stat": stat,
                "cohort": label,
                "n": len(cohort),
                "n_treated": int(cohort["had_po"].sum()),
                "binary_eff": round(bin_eff, 3) if not np.isnan(bin_eff) else None,
                "binary_snr": round(bin_snr, 3) if not np.isnan(bin_snr) else None,
                "usg_r_full": round(r_full, 3) if not np.isnan(r_full) else None,
                "usg_snr_full": round(snr_full, 3) if not np.isnan(snr_full) else None,
                "usg_r_treated": round(r_treated, 3) if not np.isnan(r_treated) else None,
                "usg_snr_treated": round(snr_treated, 3) if not np.isnan(snr_treated) else None,
            })

    out = pd.DataFrame(rows)
    print()
    print(out.to_string(index=False))

    # Compare vs prior binary-only result for the [0,6] cohort
    print()
    print("=" * 78)
    print("Mechanism read — binary vs usage-proxy on [0,6] (n=103)")
    print("=" * 78)
    print(f"{'stat':<5} {'bin_snr':>8} {'usg_snr_full':>14} {'usg_snr_treated':>17} {'sharpened?':>12}")
    for stat in STATS:
        sub = out[(out["stat"] == stat) & (out["cohort"] == "[0,6]")]
        if sub.empty:
            continue
        b = sub.iloc[0]["binary_snr"]
        uf = sub.iloc[0]["usg_snr_full"]
        ut = sub.iloc[0]["usg_snr_treated"]
        sharper = (uf is not None and b is not None
                    and abs(uf) > abs(b)) and "yes" or "no"
        b_s = f"{b:.2f}" if b is not None else "—"
        uf_s = f"{uf:.2f}" if uf is not None else "—"
        ut_s = f"{ut:.2f}" if ut is not None else "—"
        print(f"{stat:<5} {b_s:>8} {uf_s:>14} {ut_s:>17} {sharper:>12}")


if __name__ == "__main__":
    main()
