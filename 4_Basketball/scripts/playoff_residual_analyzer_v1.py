"""Playoff Residual Analyzer v1 — 5 Tier-1 hypotheses per PRE_REGISTRATION_NBA_PLAYOFFS_25_26.md.

DEVIATION FROM PRE-REG (logged here, not a methodology change):
  - Pre-reg specifies dual baseline (A = v6.1 re-scoring, B = cohort-mean).
  - v1 runs Baseline B only. Baseline A requires running v6.1 inference on
    playoff covariates which is a heavier separate build (deferred to v2 of analyzer).
  - Per pre-reg §2.5, a finding is robust only if BOTH baselines agree on disposition.
    v1 reports Baseline B dispositions as PRELIMINARY pending Baseline A.

Outputs:
  - per-prediction verdict JSON (PERSISTS/WEAKENS/REGIME-SHIFT/FALSIFIED per
    pre-reg §3 decision rules)
  - per-cell variance ratio + bootstrap 95% CI + Levene's + permutation null
  - per-player residuals for audit
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:/NBA Projections")
PLAYOFFS = ROOT / "data/parquet/playoffs"
PLAYER_META = ROOT / "data/parquet/player_metadata.parquet"
OUT_DIR = ROOT / "audit_runs/playoff_residual_pre_reg_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BOOT_N = 1000
PERM_N = 1000
REG_SEASON_BLK_RANGE = (1.26, 2.03)  # per pre-reg §3 H1


def load_playoff_player_games() -> pd.DataFrame:
    """Combine traditional_t0 (per-player-per-game) across round1 + extra_rounds."""
    parts = []
    for sub in ("round1", "extra_rounds"):
        p = PLAYOFFS / sub / "traditional_t0.parquet"
        if p.exists():
            df = pd.read_parquet(p)
            df["playoff_round"] = sub
            parts.append(df)
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)


def normalize_minutes(min_str):
    """Convert 'MM:SS' string or numeric minutes to float."""
    if pd.isna(min_str):
        return np.nan
    if isinstance(min_str, (int, float)):
        return float(min_str)
    s = str(min_str)
    if ":" in s:
        try:
            mm, ss = s.split(":")
            return float(mm) + float(ss) / 60
        except Exception:
            return np.nan
    try:
        return float(s)
    except Exception:
        return np.nan


def variance_ratio_test(group_a: np.ndarray, group_b: np.ndarray, label_a: str,
                          label_b: str, boot_n: int = BOOT_N, perm_n: int = PERM_N,
                          seed: int = 2026) -> dict:
    """Variance ratio σ_a / σ_b + bootstrap CI + Levene's + permutation null."""
    rng = np.random.default_rng(seed)
    n_a, n_b = len(group_a), len(group_b)
    if n_a < 3 or n_b < 3:
        return {"verdict": "INSUFFICIENT", "n_a": n_a, "n_b": n_b}
    sigma_a = float(np.std(group_a, ddof=1))
    sigma_b = float(np.std(group_b, ddof=1))
    ratio = sigma_a / max(sigma_b, 1e-12)
    boot_ratios = []
    for _ in range(boot_n):
        ba = rng.choice(group_a, size=n_a, replace=True)
        bb = rng.choice(group_b, size=n_b, replace=True)
        bra = np.std(ba, ddof=1) / max(np.std(bb, ddof=1), 1e-12)
        boot_ratios.append(bra)
    ci_lo, ci_hi = float(np.quantile(boot_ratios, 0.025)), float(np.quantile(boot_ratios, 0.975))
    lev_stat, lev_p = stats.levene(group_a, group_b, center="median")
    combined = np.concatenate([group_a, group_b])
    perm_ratios = []
    for _ in range(perm_n):
        rng.shuffle(combined)
        pa, pb = combined[:n_a], combined[n_a:]
        pr = np.std(pa, ddof=1) / max(np.std(pb, ddof=1), 1e-12)
        perm_ratios.append(pr)
    p_perm = float(np.mean(np.abs(np.array(perm_ratios) - 1) >=
                              abs(ratio - 1)))
    return {
        "label_a": label_a, "label_b": label_b,
        "n_a": int(n_a), "n_b": int(n_b),
        "sigma_a": sigma_a, "sigma_b": sigma_b,
        "variance_ratio_a_over_b": float(ratio),
        "bootstrap_95ci": [ci_lo, ci_hi],
        "levene_stat": float(lev_stat), "levene_p": float(lev_p),
        "permutation_p_two_sided": p_perm,
    }


def classify_position(pos_str) -> str:
    """Center if pos in {C, C-F, F-C, "Center"}; else non-Center. Per pre-reg §2.2.

    Handles both short codes (C, PG) and full-word codes (Center, Guard) since the
    metadata uses full words but the pre-reg specifies short-code semantics.
    """
    if pd.isna(pos_str) or not isinstance(pos_str, str):
        return "Unknown"
    s = pos_str.strip()
    s_upper = s.upper()
    if s_upper in {"C", "C-F", "F-C"} or s == "Center":
        return "Center"
    if s_upper in {"PG", "SG", "G", "SF", "PF", "F", "G-F", "F-G"} or s in {"Guard", "Forward"}:
        return "non-Center"
    return "Unknown"


def main():
    print("=" * 80)
    print("PLAYOFF RESIDUAL ANALYZER v1 — 5 Tier-1 hypotheses (Baseline B only)")
    print("=" * 80)
    print("DEVIATION: Baseline A (v6.1 re-scoring) deferred; v1 reports Baseline B only.")
    print()

    games = load_playoff_player_games()
    if games.empty:
        print("No playoff data found.")
        return
    print(f"Loaded {len(games)} player-game rows across playoff rounds")
    print(f"  Rounds: {games['playoff_round'].value_counts().to_dict()}")

    # Normalize minutes
    games["min"] = games["minutes"].apply(normalize_minutes)
    # Player inclusion: ≥3 playoff games + avg ≥10 min/game
    player_agg = games.groupby("personId").agg(
        g=("gameId", "nunique"),
        mpg=("min", "mean"),
    ).reset_index()
    eligible_players = player_agg[(player_agg["g"] >= 3) &
                                     (player_agg["mpg"] >= 10)]
    print(f"  Eligible players (≥3g, ≥10 mpg): {len(eligible_players)}")
    games_elig = games[games["personId"].isin(eligible_players["personId"])].copy()
    print(f"  Eligible player-game rows: {len(games_elig)}")

    # Join player metadata (position + years_pro)
    # Use enriched metadata for position + derive years_pro from debut_year
    meta_enriched_path = ROOT / "data/parquet/player_metadata_enriched.parquet"
    meta = pd.read_parquet(meta_enriched_path)
    print(f"  Player metadata (enriched): {len(meta)} rows")
    meta_keep = meta[["nba_api_id", "position", "debut_year"]].drop_duplicates("nba_api_id")
    meta_keep = meta_keep.rename(columns={"position": "meta_position"})
    games_elig = games_elig.merge(meta_keep, left_on="personId", right_on="nba_api_id",
                                     how="left")
    games_elig["pos_class"] = games_elig["meta_position"].apply(classify_position)
    # Derive years_pro for 2025-26 playoffs (season starts in 2025 → 2026)
    games_elig["years_pro"] = 2026 - pd.to_numeric(games_elig["debut_year"], errors="coerce")
    print(f"  Position classes: {games_elig['pos_class'].value_counts().to_dict()}")
    print(f"  Years_pro range: {games_elig['years_pro'].min()} to {games_elig['years_pro'].max()}")

    # Compute per-game per-minute rates for the variance ratio analysis
    for stat in ("BLK", "AST", "PTS", "REB"):
        # Stat column case from traditional box: blocks, assists, etc — let's check
        # Actually the cols include personId, firstName, etc. Real stat names depend.
        pass
    print(f"  Stat columns available: {[c for c in games_elig.columns if c.lower() in ('blocks','assists','points','reboundstotal','rebounds')]}")
    # Map traditional NBA columns
    rate_cols = {"BLK": "blocks", "AST": "assists", "PTS": "points",
                  "REB": "reboundsTotal"}
    for stat, col in rate_cols.items():
        if col in games_elig.columns:
            games_elig[f"{stat}_per_min"] = (pd.to_numeric(games_elig[col], errors="coerce") /
                                                 games_elig["min"].replace(0, np.nan))
        else:
            games_elig[f"{stat}_per_min"] = np.nan
            print(f"  WARNING: {stat} column '{col}' not in traditional_t0")

    # ---- Baseline B: cohort-mean residuals ----
    # For each (stat, pos_class) cell: r_bar_c = mean of stat/min across cell
    # residual = stat/min - r_bar_c
    print("\nComputing Baseline B (cohort-mean) residuals per stat × pos_class cell...")
    results = {}

    # Prediction 1: BLK × Center variance ratio (target 1.26-2.03)
    print("\n--- Prediction 1: BLK × Center variance ratio (vs regular-season [1.26, 2.03]) ---")
    cell_center = games_elig[games_elig["pos_class"] == "Center"].copy()
    cell_noncenter = games_elig[games_elig["pos_class"] == "non-Center"].copy()
    if len(cell_center) > 0:
        c_mean = cell_center["BLK_per_min"].mean()
        nc_mean = cell_noncenter["BLK_per_min"].mean()
        c_resid = (cell_center["BLK_per_min"] - c_mean).dropna()
        nc_resid = (cell_noncenter["BLK_per_min"] - nc_mean).dropna()
        h1 = variance_ratio_test(c_resid.values, nc_resid.values,
                                   "Center", "non-Center")
        # Decision rule
        if h1.get("verdict") == "INSUFFICIENT":
            h1["disposition"] = "INSUFFICIENT"
        else:
            ci_lo, ci_hi = h1["bootstrap_95ci"]
            lo, hi = REG_SEASON_BLK_RANGE
            if ci_lo <= hi and ci_hi >= lo:
                h1["disposition"] = "PERSISTS"
            elif ci_hi < lo and ci_lo > 1.0:
                h1["disposition"] = "WEAKENS"
            elif ci_lo > hi:
                h1["disposition"] = "PERSISTS — INTENSIFIES"
            elif ci_lo <= 1.0 <= ci_hi:
                h1["disposition"] = "REGIME-SHIFT (toward null)"
            elif ci_hi < 1.0:
                h1["disposition"] = "FALSIFIED (inversion)"
            else:
                h1["disposition"] = "INDETERMINATE"
        print(f"  ratio={h1.get('variance_ratio_a_over_b', np.nan):.3f} CI={h1.get('bootstrap_95ci', [])}")
        print(f"  Levene's p={h1.get('levene_p', np.nan):.3f} | disposition: {h1.get('disposition', 'na')}")
        results["H1_BLK_x_Center"] = h1

    # Prediction 2: AST × deep-vet (13+ years) null persistence
    print("\n--- Prediction 2: AST × deep-vet (13+) null persistence ---")
    deep_vet = games_elig[games_elig["years_pro"] >= 13]
    non_deep_vet = games_elig[(games_elig["years_pro"] < 13) & games_elig["years_pro"].notna()]
    fallback_used = False
    if len(deep_vet["personId"].unique()) < 10:
        deep_vet = games_elig[games_elig["years_pro"] >= 10]
        non_deep_vet = games_elig[(games_elig["years_pro"] < 10) & games_elig["years_pro"].notna()]
        fallback_used = True
        print(f"  Using 10+ fallback (13+ had insufficient n)")
    if len(deep_vet) > 0:
        d_mean = deep_vet["AST_per_min"].mean()
        nd_mean = non_deep_vet["AST_per_min"].mean()
        d_resid = (deep_vet["AST_per_min"] - d_mean).dropna()
        nd_resid = (non_deep_vet["AST_per_min"] - nd_mean).dropna()
        h2 = variance_ratio_test(d_resid.values, nd_resid.values,
                                   f"deep_vet_{'10+' if fallback_used else '13+'}",
                                   "non-deep-vet")
        h2["fallback_10plus_used"] = fallback_used
        if h2.get("verdict") == "INSUFFICIENT":
            h2["disposition"] = "INSUFFICIENT"
        else:
            ci_lo, ci_hi = h2["bootstrap_95ci"]
            lev_p = h2["levene_p"]
            if ci_lo <= 1.0 <= ci_hi and lev_p >= 0.05:
                h2["disposition"] = "PERSISTS (null replicates)"
            elif ci_lo <= 1.0 <= ci_hi and lev_p < 0.05:
                h2["disposition"] = "WEAKENS (Levene fire but ratio ambig)"
            else:
                h2["disposition"] = "REGIME-SHIFT or FALSIFIED"
        print(f"  ratio={h2.get('variance_ratio_a_over_b', np.nan):.3f} CI={h2.get('bootstrap_95ci', [])}")
        print(f"  Levene p={h2.get('levene_p', np.nan):.3f} | disposition: {h2.get('disposition', 'na')}")
        results["H2_AST_deep_vet"] = h2

    # Prediction 3: PTS × Center directional persistence (ratio < 1.0)
    print("\n--- Prediction 3: PTS × Center directional (ratio < 1.0) ---")
    if len(cell_center) > 0:
        c_mean = cell_center["PTS_per_min"].mean()
        nc_mean = cell_noncenter["PTS_per_min"].mean()
        c_resid = (cell_center["PTS_per_min"] - c_mean).dropna()
        nc_resid = (cell_noncenter["PTS_per_min"] - nc_mean).dropna()
        h3 = variance_ratio_test(c_resid.values, nc_resid.values,
                                   "Center", "non-Center")
        # Decision: ratio < 1.0 majority cell count — here single cell so check direction
        if h3.get("verdict") == "INSUFFICIENT":
            h3["disposition"] = "INSUFFICIENT"
        else:
            ratio = h3["variance_ratio_a_over_b"]
            ci_lo, ci_hi = h3["bootstrap_95ci"]
            if ci_hi < 1.0:
                h3["disposition"] = "PERSISTS (directional + significant)"
            elif ratio < 1.0:
                h3["disposition"] = "PERSISTS (directional, ratio < 1.0 even if CI overlaps 1.0)"
            elif ratio >= 1.0 and ci_lo > 1.0:
                h3["disposition"] = "FALSIFIED (inversion)"
            else:
                h3["disposition"] = "WEAKENS or REGIME-SHIFT"
        print(f"  ratio={h3.get('variance_ratio_a_over_b', np.nan):.3f} CI={h3.get('bootstrap_95ci', [])}")
        print(f"  disposition: {h3.get('disposition', 'na')}")
        results["H3_PTS_x_Center"] = h3

    # Prediction 4: REB × Center surgical walk-back (Baseline B only — surgical equivalent)
    print("\n--- Prediction 4: REB × Center surgical walk-back ---")
    if len(cell_center) > 0:
        c_mean = cell_center["REB_per_min"].mean()
        nc_mean = cell_noncenter["REB_per_min"].mean()
        c_resid = (cell_center["REB_per_min"] - c_mean).dropna()
        nc_resid = (cell_noncenter["REB_per_min"] - nc_mean).dropna()
        h4 = variance_ratio_test(c_resid.values, nc_resid.values,
                                   "Center", "non-Center")
        if h4.get("verdict") == "INSUFFICIENT":
            h4["disposition"] = "INSUFFICIENT"
        else:
            ratio = h4["variance_ratio_a_over_b"]
            ci_lo, ci_hi = h4["bootstrap_95ci"]
            # Baseline B = surgical; expected to couple (ratio > 1.0 CI excluding 1.0)
            if ci_lo > 1.0:
                h4["disposition"] = ("BASELINE B (surgical) couples — walk-back claim "
                                       "requires Baseline A to dissolve it; deferred")
            elif ci_lo <= 1.0 <= ci_hi:
                h4["disposition"] = "WEAKENS — surgical coupling weak"
            else:
                h4["disposition"] = "FALSIFIED — surgical doesn't couple either"
        print(f"  ratio={h4.get('variance_ratio_a_over_b', np.nan):.3f} CI={h4.get('bootstrap_95ci', [])}")
        print(f"  disposition: {h4.get('disposition', 'na')}")
        results["H4_REB_x_Center_surgical"] = h4

    # Prediction 5: PBP score-margin × possession variance ratio
    # Needs PBP data with clutch/garbage tagging — heavier. Skip in v1, log.
    print("\n--- Prediction 5: PBP score-margin × possession (clutch vs garbage) ---")
    print("  DEFERRED: requires PBP-level clutch/garbage tagging across all 25-26 playoff games.")
    print("  Not implemented in v1; flagged as not-tested.")
    results["H5_PBP_clutch_garbage"] = {"status": "DEFERRED",
                                           "reason": "PBP clutch/garbage tagging deferred to v2"}

    # Summary
    print("\n" + "=" * 80)
    print("V1 SUMMARY (Baseline B only, preliminary)")
    print("=" * 80)
    for k, v in results.items():
        disp = v.get("disposition") or v.get("status") or "na"
        print(f"  {k}: {disp}")

    summary = {
        "version": "v1",
        "deviation": ("Baseline A (v6.1 re-scoring) deferred; Baseline B only. "
                       "Per pre-reg §2.5 a finding is robust only if both baselines agree; "
                       "v1 dispositions are PRELIMINARY pending v2."),
        "n_eligible_players": int(len(eligible_players)),
        "n_eligible_player_games": int(len(games_elig)),
        "h1_h5": results,
    }
    with open(OUT_DIR / "results.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    games_elig.to_parquet(OUT_DIR / "eligible_player_games.parquet", index=False)
    print(f"\nWrote outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
