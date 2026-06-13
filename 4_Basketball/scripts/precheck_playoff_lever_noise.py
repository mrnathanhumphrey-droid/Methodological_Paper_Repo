"""Noise tests on the within-player PTS lift signal.

Three tests:
  1. Permutation null: shuffle had_po 10k times, get null SNR distribution.
     p = fraction of |perm SNR| >= |observed SNR|.
  2. LOO MSE — binary offset: for each held-out player, fit offset from the
     other N-1, apply, accumulate squared error. Compare total MSE to the
     "no offset" baseline. If MSE_offset < MSE_baseline, real signal.
  3. LOO MSE — usage-proxy slope: same but with linear slope on continuous
     usage-proxy.

Cohort: paired (22-23, 23-24) pre-peak, years_pro [0,6], n=103.
DV: lift = err_2023-24 − err_2022-23 (per-36 PTS).
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")
from pathlib import Path

import numpy as np
import pandas as pd

from precheck_playoff_lever import find_v4_audit, years_pro_for_season

REPO = Path(".")
PQ = REPO / "data" / "parquet"

RNG = np.random.default_rng(20260503)
N_PERM = 10_000


def welch_snr(t, c):
    if len(t) < 5 or len(c) < 5:
        return float("nan")
    se = np.sqrt(t.var(ddof=1) / len(t) + c.var(ddof=1) / len(c))
    if se == 0:
        return float("nan")
    return (t.mean() - c.mean()) / se


def load_residuals(stat, ts):
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
    po_simple["po_usg_proxy"] = np.where(
        po_simple["po_min"] > 0,
        (po_simple["po_fga"] + 0.44 * po_simple["po_fta"] + po_simple["po_tov"])
            * 36.0 / po_simple["po_min"],
        np.nan,
    )

    baseline = load_residuals("PTS", "2022-23")
    post = load_residuals("PTS", "2023-24")
    paired = baseline.merge(post, on="nba_api_id", how="inner")
    paired["lift"] = paired["err_2023-24"] - paired["err_2022-23"]

    yp_lookup = dict(zip(meta["nba_api_id"],
                          years_pro_for_season(meta, "2023-24")))
    paired["years_pro"] = paired["nba_api_id"].map(yp_lookup)
    cohort = paired[paired["years_pro"].between(0, 6)].copy()

    po_2223 = po_simple[po_simple["season"] == "2022-23"]
    cohort = cohort.merge(
        po_2223[["nba_api_id", "po_usg_proxy", "po_gp"]],
        on="nba_api_id", how="left",
    )
    cohort["po_usg_proxy"] = cohort["po_usg_proxy"].fillna(0.0)
    cohort["po_gp"] = cohort["po_gp"].fillna(0)
    cohort["had_po"] = cohort["po_gp"] > 0

    lift = cohort["lift"].values
    had = cohort["had_po"].values
    usg = cohort["po_usg_proxy"].values
    n = len(cohort)

    print(f"Cohort: PTS pre-peak [0,6] paired (22-23, 23-24), n={n}")
    print(f"  treated (had_po): {int(had.sum())}, control: {int((~had).sum())}")
    print()

    # ─── Test 1: Permutation null ──────────────────────────────────────
    obs_snr = welch_snr(lift[had], lift[~had])
    obs_eff = lift[had].mean() - lift[~had].mean()
    perm_snrs = np.empty(N_PERM)
    for i in range(N_PERM):
        shuffled = RNG.permutation(had)
        perm_snrs[i] = welch_snr(lift[shuffled], lift[~shuffled])
    perm_snrs = perm_snrs[~np.isnan(perm_snrs)]
    p_two_sided = (np.abs(perm_snrs) >= abs(obs_snr)).mean()
    p_one_sided = (perm_snrs >= obs_snr).mean()
    print("=" * 72)
    print("TEST 1 — permutation null (10k shuffles)")
    print("=" * 72)
    print(f"  Observed effect: {obs_eff:+.3f} PTS/36   SNR: {obs_snr:+.3f}")
    print(f"  Null SNR mean: {perm_snrs.mean():+.3f}   sd: {perm_snrs.std():.3f}")
    print(f"  Null SNR 95% range: [{np.quantile(perm_snrs, 0.025):+.3f}, "
          f"{np.quantile(perm_snrs, 0.975):+.3f}]")
    print(f"  Two-sided p = {p_two_sided:.4f}   one-sided p = {p_one_sided:.4f}")
    verdict_perm = "REAL signal" if p_two_sided < 0.05 else "could be noise"
    print(f"  -> {verdict_perm}")

    # ─── Test 2: LOO MSE — binary offset ────────────────────────────────
    print()
    print("=" * 72)
    print("TEST 2 — LOO MSE: does the binary offset reduce held-out MSE?")
    print("=" * 72)
    sse_baseline = float((lift ** 2).sum())  # offset = 0 baseline
    sse_offset = 0.0
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        train_lift = lift[mask]
        train_had = had[mask]
        if train_had.sum() < 5 or (~train_had).sum() < 5:
            offset = 0.0
        else:
            offset = train_lift[train_had].mean() - train_lift[~train_had].mean()
        pred = offset if had[i] else 0.0
        sse_offset += (lift[i] - pred) ** 2
    rmse_baseline = np.sqrt(sse_baseline / n)
    rmse_offset = np.sqrt(sse_offset / n)
    delta_pct = (1 - sse_offset / sse_baseline) * 100
    print(f"  RMSE baseline (no offset): {rmse_baseline:.4f}")
    print(f"  RMSE w/ binary offset (LOO): {rmse_offset:.4f}")
    print(f"  MSE delta: {delta_pct:+.2f}%   (positive = offset HELPS)")
    verdict_bin = "lever helps" if delta_pct > 0 else "lever hurts / wash"
    print(f"  -> {verdict_bin}")

    # ─── Test 3: LOO MSE — usage-proxy linear slope ────────────────────
    print()
    print("=" * 72)
    print("TEST 3 — LOO MSE: does usage-proxy slope reduce held-out MSE?")
    print("=" * 72)
    sse_slope = 0.0
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        x = usg[mask]
        y = lift[mask]
        if x.std() == 0:
            a, b = 0.0, 0.0
        else:
            b = np.cov(x, y, ddof=1)[0, 1] / x.var(ddof=1)
            a = y.mean() - b * x.mean()
        pred = a + b * usg[i]
        sse_slope += (lift[i] - pred) ** 2
    rmse_slope = np.sqrt(sse_slope / n)
    delta_pct_slope = (1 - sse_slope / sse_baseline) * 100
    print(f"  RMSE baseline: {rmse_baseline:.4f}")
    print(f"  RMSE w/ usage slope (LOO): {rmse_slope:.4f}")
    print(f"  MSE delta: {delta_pct_slope:+.2f}%")
    verdict_slope = "slope helps" if delta_pct_slope > 0 else "slope hurts / wash"
    print(f"  -> {verdict_slope}")

    print()
    print("=" * 72)
    print("INTEGRATED VERDICT")
    print("=" * 72)
    print(f"  Permutation p (two-sided): {p_two_sided:.4f}")
    print(f"  LOO MSE delta — binary:    {delta_pct:+.2f}%")
    print(f"  LOO MSE delta — usage:     {delta_pct_slope:+.2f}%")
    if p_two_sided < 0.05 and delta_pct > 0:
        print("  → Signal is statistically real AND reduces MSE. Lever stays alive.")
    elif p_two_sided < 0.05 and delta_pct <= 0:
        print("  → Signal real but doesn't reduce MSE — bias-variance tradeoff fails.")
    else:
        print("  → Signal could be noise. Lever weakens.")


if __name__ == "__main__":
    main()
