"""Cheap pre-check: does prior-season playoff exposure predict v4-lite raw
residuals for pre-peak players?

If signal SNR >= 1.5 with sign-replication across 22-23 / 23-24 / 24-25,
the playoff lever is real and worth committing v6.1 re-validation to. If
not, drop it.

Tests two predictor representations:
  - binary: had_playoff_GP > 0 in prior season
  - dose: prior-season playoff total minutes (continuous, z-scored within cohort)

Cohort gate: years_pro in [0, 6] (rough pre-peak proxy; refines later).
DV: residual = actual_per_36 - proj_per_36 (column 'error' in audit CSVs).

Output: per-stat × per-season summary table + cross-season aggregate.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(".")
AUDIT_ROOT = REPO / "audit_runs"
PQ = REPO / "data" / "parquet"

STATS = ["PTS", "REB", "AST", "STL", "BLK", "TOV"]
TEST_SEASONS = ["2022-23", "2023-24", "2024-25"]
COHORT_YEARS_PRO = (0, 6)  # inclusive both ends
SNR_GATE = 1.5


def find_v4_audit(stat: str, test_season: str, min_rows: int = 100) -> Path | None:
    """Find the latest v4-lite (NOT v4-lite-gya) audit for (stat, test_season).
    Filters out smoke runs (< min_rows) and the gya variant.
    """
    cands = []
    for run in AUDIT_ROOT.iterdir():
        if not run.is_dir():
            continue
        for sub in run.iterdir():
            if not sub.is_dir():
                continue
            # Require exactly _phase4_v4_quadratic_tq_g_ (not gya / pos5 / etc.)
            if "_phase4_v4_quadratic_tq_g_" not in sub.name:
                continue
            parts = sub.name.split("_phase4_v4_")
            stat_in_dir = parts[0].split("_")[-1]
            test_in_dir = parts[1].split("__")[-1]
            if stat_in_dir != stat or test_in_dir != test_season:
                continue
            proj = sub / "per_player_projections.csv"
            if not proj.exists():
                continue
            try:
                n = sum(1 for _ in proj.open(encoding="utf-8")) - 1
            except OSError:
                continue
            if n < min_rows:
                continue
            cands.append((sub.stat().st_mtime, sub))
    return sorted(cands)[-1][1] if cands else None


def prior_season(test_season: str) -> str:
    parts = test_season.split("-")
    s = int(parts[0])
    e = int(parts[1])
    return f"{s - 1}-{(e - 1) % 100:02d}"


def years_pro_for_season(meta: pd.DataFrame, season: str) -> pd.Series:
    """Years of NBA experience as of `season` start (Oct of season's first year)."""
    start_year = int(season.split("-")[0])
    debut = meta["debut_year"].fillna(meta["draft_year"] + 1)
    yp = start_year - debut
    return yp


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
        po_pts=("pts", "sum"),
    ).reset_index()

    # Welch-style 2-sample t / SNR for treated vs control means
    def welch_snr(treated: np.ndarray, control: np.ndarray) -> tuple[float, float]:
        if len(treated) < 5 or len(control) < 5:
            return float("nan"), float("nan")
        mt = treated.mean()
        mc = control.mean()
        st = treated.std(ddof=1)
        sc = control.std(ddof=1)
        eff = mt - mc
        se = np.sqrt(st**2 / len(treated) + sc**2 / len(control))
        snr = eff / se if se > 0 else float("nan")
        return eff, snr

    rows: list[dict] = []
    for stat in STATS:
        for test_season in TEST_SEASONS:
            audit = find_v4_audit(stat, test_season)
            if audit is None:
                continue
            df = pd.read_csv(audit / "per_player_projections.csv")
            df["nba_api_id"] = df["nba_api_id"].astype(int)
            # Residual = error column (already actual - proj_mean)
            df = df.dropna(subset=["error"])

            # Attach years_pro AT TEST SEASON START
            yp_lookup = dict(zip(meta["nba_api_id"],
                                  years_pro_for_season(meta, test_season)))
            df["years_pro"] = df["nba_api_id"].map(yp_lookup)
            cohort = df[df["years_pro"].between(COHORT_YEARS_PRO[0],
                                                  COHORT_YEARS_PRO[1])].copy()
            if len(cohort) < 20:
                continue

            # Attach PRIOR-season playoff exposure
            ps = prior_season(test_season)
            po_prior = po_simple[po_simple["season"] == ps]
            cohort = cohort.merge(po_prior[["nba_api_id", "po_gp", "po_min"]],
                                   on="nba_api_id", how="left")
            cohort["po_gp"] = cohort["po_gp"].fillna(0)
            cohort["po_min"] = cohort["po_min"].fillna(0)
            cohort["had_po"] = cohort["po_gp"] > 0

            treated = cohort.loc[cohort["had_po"], "error"].values
            control = cohort.loc[~cohort["had_po"], "error"].values

            eff, snr = welch_snr(treated, control)

            # Dose-response slope (linear) on log(po_min + 1) to compress heavy tails
            if cohort["po_min"].sum() > 0:
                x = np.log1p(cohort["po_min"].values)
                y = cohort["error"].values
                if x.std() > 0:
                    # Pearson r, then SNR via Fisher z-style
                    r = np.corrcoef(x, y)[0, 1]
                    n = len(cohort)
                    # SE of correlation: 1/sqrt(n-3) for Fisher z; for r itself ~sqrt((1-r^2)/(n-2))
                    se_r = np.sqrt((1 - r**2) / (n - 2)) if n > 3 else float("nan")
                    snr_dose = r / se_r if se_r and se_r > 0 else float("nan")
                else:
                    r, snr_dose = float("nan"), float("nan")
            else:
                r, snr_dose = float("nan"), float("nan")

            rows.append({
                "stat": stat,
                "test_season": test_season,
                "n_cohort": len(cohort),
                "n_treated": int((cohort["had_po"]).sum()),
                "n_control": int((~cohort["had_po"]).sum()),
                "binary_effect": round(eff, 4) if not np.isnan(eff) else None,
                "binary_snr": round(snr, 3) if not np.isnan(snr) else None,
                "dose_pearson_r": round(r, 3) if not np.isnan(r) else None,
                "dose_snr": round(snr_dose, 3) if not np.isnan(snr_dose) else None,
            })

    out = pd.DataFrame(rows)
    print("\n=== Per (stat, test_season) — pre-peak cohort, prior-season playoff exposure ===\n")
    print(out.to_string(index=False))

    # Cross-season aggregate per stat: sign-replication + magnitude check
    print("\n=== Cross-season aggregate per stat ===\n")
    print(f"{'stat':<5} {'binary_signs':<14} {'binary_pass':<12} {'dose_signs':<12} {'dose_pass':<10}")
    print("-" * 60)
    for stat in STATS:
        sub = out[out["stat"] == stat]
        if len(sub) < 2:
            continue
        b_signs = "".join("+" if x and x > 0 else ("-" if x and x < 0 else "0")
                            for x in sub["binary_effect"].fillna(0))
        b_snr_pass = sum(1 for s in sub["binary_snr"]
                          if s is not None and abs(s) >= SNR_GATE)
        d_signs = "".join("+" if x and x > 0 else ("-" if x and x < 0 else "0")
                            for x in sub["dose_pearson_r"].fillna(0))
        d_snr_pass = sum(1 for s in sub["dose_snr"]
                          if s is not None and abs(s) >= SNR_GATE)
        b_pass = "YES" if b_snr_pass >= 2 and len(set(b_signs.replace("0", ""))) == 1 else "no"
        d_pass = "YES" if d_snr_pass >= 2 and len(set(d_signs.replace("0", ""))) == 1 else "no"
        print(f"{stat:<5} {b_signs:<14} {b_pass:<12} {d_signs:<12} {d_pass:<10}")

    print("\nGate: ≥2/3 seasons SNR ≥ 1.5 AND consistent sign across non-zero seasons.")
    print(f"Cohort def: years_pro ∈ [{COHORT_YEARS_PRO[0]}, {COHORT_YEARS_PRO[1]}]\n")


if __name__ == "__main__":
    main()
