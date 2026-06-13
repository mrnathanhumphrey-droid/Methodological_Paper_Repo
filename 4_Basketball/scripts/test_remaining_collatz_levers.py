"""De-shrinkage fit + R66 envelope + Plancherel symmetry + (q-3)/q closed-form tests.

Round 4 of the Collatz residual-class lens applied to NBA. Earlier tests:
  R76 leading-mode → PCA showed 62.9% variance on PC1 (role direction)
  R74 scale-normalize → BLK fully closes vet/soph gap; PTS partial
  Four-term decomp → cross-scale slope +1.55 on PTS (Galton shrinkage)

This script:
  - Fits the de-shrinkage regression per stat (saves coefs)
  - R66 envelope: residual decay rate as covariates added
  - Plancherel symmetry: cohort effects under involution
  - (q-3)/q closed-form: cohort offset vs log(scale) at coarse level
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from pathlib import Path
import json
import os
import numpy as np
import pandas as pd

from models.skill.data_prep import _primary_position_class

REPO = Path(".")
PQ = REPO / "data" / "parquet"


def load():
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx = bx[(bx["season"] == "2025-26") & (bx["season_type"] == "Regular Season")].copy()
    bx["minutes"] = pd.to_numeric(bx["minutes"], errors="coerce")
    bx = bx.dropna(subset=["minutes"])
    bx = bx[bx["minutes"] > 0]
    actuals = bx.groupby("nba_api_id").agg(
        PTS_a=("PTS", "mean"), REB_a=("REB", "mean"), AST_a=("AST", "mean"),
        STL_a=("STL", "mean"), BLK_a=("BLK", "mean"), TOV_a=("TOV", "mean"),
        FGM_a=("FGM", "mean"), FGA_a=("FGA", "mean"),
        FG3M_a=("FG3M", "mean"), FG3A_a=("FG3A", "mean"),
        FTM_a=("FTM", "mean"), FTA_a=("FTA", "mean"),
    ).reset_index()
    actuals["nba_api_id"] = actuals["nba_api_id"].astype(int)
    ship = pd.read_csv("audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv")
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    ship = ship.drop(columns=[c for c in ship.columns if c.endswith("_actual")])
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    mc = ["nba_api_id", "position", "draft_year", "debut_year"]
    sup = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "rookie_metadata_supplement.parquet"
    if sup.exists():
        sp = pd.read_parquet(sup)
        meta = pd.concat([meta[mc], sp[mc]], ignore_index=True)
    ship = ship.merge(meta[mc], on="nba_api_id", how="left")
    ship["pos_class"] = ship["position"].apply(_primary_position_class)
    ship["years_pro"] = ship["debut_year"].where(ship["debut_year"].notna(), ship["draft_year"] + 1)
    ship["years_pro"] = 2025 - ship["years_pro"]
    ship["ypb"] = pd.cut(ship["years_pro"], bins=[-1, 0, 3, 7, 12, 30],
                          labels=["rookie", "1-3", "4-7", "8-12", "13+"]).astype(str)
    real = ship[ship["nba_api_id"] < 9990000].merge(actuals, on="nba_api_id", how="inner")
    return real


def main():
    real = load()
    print(f"Sample: {len(real)}")
    print()

    STATS_BY_PROJ = {
        "PTS": "PTS_per_game", "REB": "REB_per_game", "AST": "AST_per_game",
        "STL": "STL_per_game", "BLK": "BLK_per_game", "TOV": "TOV_per_game",
        "FGM": "FGM_per_game", "FGA": "FGA_per_game",
        "FG3M": "3PM_per_game" if "3PM_per_game" in real.columns else "FG3M_per_game",
        "FG3A": "3PA_per_game" if "3PA_per_game" in real.columns else "FG3A_per_game",
        "FTM": "FTM_per_game", "FTA": "FTA_per_game",
    }

    # === DE-SHRINKAGE ===
    print("=" * 78)
    print("DE-SHRINKAGE: actual = α + γ · proj   (γ>1 means proj is shrunk to mean)")
    print("=" * 78)
    print(f'{"stat":<5} {"n":>4} {"alpha":>8} {"gamma":>7} {"raw_MAE":>9} {"corr_MAE":>10} {"Δ%":>7} {"R²":>7}')
    print("-" * 78)
    deshrinkage = {}
    for stat, proj_col in STATS_BY_PROJ.items():
        if proj_col not in real.columns:
            continue
        sub = real.dropna(subset=[proj_col, f"{stat}_a"])
        if len(sub) < 30:
            continue
        p = sub[proj_col].values.astype(float)
        a = sub[f"{stat}_a"].values.astype(float)
        if p.var(ddof=1) == 0:
            continue
        gamma = np.cov(p, a, ddof=1)[0, 1] / p.var(ddof=1)
        alpha = a.mean() - gamma * p.mean()
        pred_corr = alpha + gamma * p
        r2 = float(np.corrcoef(p, a)[0, 1] ** 2)
        mae_raw = float(np.abs(p - a).mean())
        mae_corr = float(np.abs(pred_corr - a).mean())
        delta = (mae_corr / mae_raw - 1.0) * 100
        alpha_str = ('{:+.3f}').format(alpha)
        delta_str = ('{:+.2f}').format(delta)
        print(f'{stat:<5} {len(sub):>4} {alpha_str:>8s} {gamma:>7.3f} {mae_raw:>9.3f} {mae_corr:>10.3f} {delta_str:>7s}% {r2:>7.3f}')
        deshrinkage[stat] = {"alpha": float(alpha), "gamma": float(gamma), "r2": r2,
                              "raw_mae": mae_raw, "corr_mae": mae_corr, "delta_pct": delta}

    out_path = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "deshrinkage_coefs.json"
    with open(out_path, "w") as f:
        json.dump(deshrinkage, f, indent=2)
    print()
    print(f"Saved coefs -> {out_path}")
    print()

    # === R66 envelope ===
    print("=" * 78)
    print("TEST R66: residual decay across covariate layers")
    print("=" * 78)
    print('  L=0 baseline-pooled, L=1 v6.1 per-stat, L=2 +pos, L=3 +ypb, L=4 +pos×ypb')
    print(f'{"layer":<26} {"stat":<5} {"|mean|":>9} {"·2^L":>9} {"sd":>9}')
    print("-" * 78)
    layers_str = ["baseline-pooled","v6.1 per-stat","+pos","+ypb","+pos×ypb interact"]
    for stat in ["PTS", "REB", "AST"]:
        proj_col = STATS_BY_PROJ[stat]
        sub = real.dropna(subset=[proj_col, f"{stat}_a"]).copy()
        a = sub[f"{stat}_a"].values
        p = sub[proj_col].values
        league = a.mean()
        resid_0 = a - league
        resid_1 = a - p
        sub["_d"] = a - p
        pos_means = sub.groupby("pos_class")["_d"].transform("mean").values
        resid_2 = sub["_d"].values - pos_means
        ypb_means = sub.groupby("ypb")["_d"].transform("mean").values
        resid_3 = resid_2 - ypb_means
        sub["_cell"] = sub["pos_class"].astype(str) + "|" + sub["ypb"].astype(str)
        cell_means = sub.groupby("_cell")["_d"].transform("mean").values
        resid_4 = sub["_d"].values - cell_means
        for L, r in enumerate([resid_0, resid_1, resid_2, resid_3, resid_4]):
            scale_L = 2 ** L
            print(f'L={L} ({layers_str[L]:<20}) {stat:<5} {abs(r.mean()):>9.4f} {abs(r.mean())*scale_L:>9.4f} {r.std():>9.4f}')
        print()

    # === Plancherel symmetry ===
    print("=" * 78)
    print("TEST Plancherel: cohort effects under involution (years_pro reflection)")
    print("=" * 78)
    print('  involution σ: rookie ↔ 13+, 1-3 ↔ 8-12, 4-7 fixed')
    print('  if effect is symmetric: residual(rookie) ≈ -residual(13+), etc.')
    print()
    print(f'{"ypb":<10} {"n":>4} {"PTS_resid":>10} {"REB_resid":>10} {"AST_resid":>10}')
    cohort_resids = {}
    for ypb_grp in ["rookie", "1-3", "4-7", "8-12", "13+"]:
        sub = real[real["ypb"] == ypb_grp]
        if len(sub) < 5:
            continue
        cohort_resids[ypb_grp] = {
            "PTS": (sub["PTS_a"] - sub["PTS_per_game"]).mean(),
            "REB": (sub["REB_a"] - sub["REB_per_game"]).mean(),
            "AST": (sub["AST_a"] - sub["AST_per_game"]).mean(),
            "n": len(sub),
        }
        c = cohort_resids[ypb_grp]
        ps = ('{:+.3f}').format(c["PTS"])
        rs = ('{:+.3f}').format(c["REB"])
        as_ = ('{:+.3f}').format(c["AST"])
        print(f'{ypb_grp:<10} {c["n"]:>4} {ps:>10} {rs:>10} {as_:>10}')

    # Symmetry score: correlate (rookie, 1-3) vs flipped (13+, 8-12)
    print()
    print("Involution check (under perfect symmetry these should match in magnitude/opposite sign):")
    pairs = [("rookie", "13+"), ("1-3", "8-12")]
    for stat in ["PTS", "REB", "AST"]:
        for a_grp, b_grp in pairs:
            if a_grp in cohort_resids and b_grp in cohort_resids:
                ra = cohort_resids[a_grp][stat]
                rb = cohort_resids[b_grp][stat]
                expected = -rb
                gap = abs(ra - expected)
                ras = ('{:+.3f}').format(ra)
                rbs = ('{:+.3f}').format(rb)
                exps = ('{:+.3f}').format(expected)
                print(f'  {stat} | {a_grp}={ras} vs (-{b_grp})={exps}  gap={gap:.3f}')

    # === (q-3)/q closed-form ===
    print()
    print("=" * 78)
    print("TEST (q-3)/q: cohort residual mean as closed form of cohort scale")
    print("=" * 78)
    print()
    print('  Cohort-level: residual_mean = α + β·log(cohort_scale)?')
    print()
    cohort_table = []
    for ypb_grp in ["rookie", "1-3", "4-7", "8-12", "13+"]:
        sub = real[real["ypb"] == ypb_grp]
        if len(sub) < 5:
            continue
        cohort_table.append({
            "ypb": ypb_grp,
            "n": len(sub),
            "mean_actual": sub["PTS_a"].mean(),
            "mean_proj": sub["PTS_per_game"].mean(),
            "mean_resid": (sub["PTS_a"] - sub["PTS_per_game"]).mean(),
            "log_scale": np.log(sub["PTS_a"].mean()),
        })
    ct = pd.DataFrame(cohort_table)
    print(ct.to_string(index=False))
    if len(ct) >= 3:
        log_scale = ct["log_scale"].values
        resid = ct["mean_resid"].values
        if log_scale.var(ddof=1) > 0:
            slope_cohort = np.cov(log_scale, resid, ddof=1)[0, 1] / log_scale.var(ddof=1)
            alpha_cohort = resid.mean() - slope_cohort * log_scale.mean()
            r2 = float(np.corrcoef(log_scale, resid)[0, 1] ** 2)
            print()
            print(f'  Cohort-level OLS: residual = {alpha_cohort:+.3f} + {slope_cohort:+.3f}·log(scale)   R²={r2:.3f}')
            print()
            # Compare to per-player slope (1.55 from earlier test)
            print(f'  Per-player PTS slope on log(actual): +1.55')
            print(f'  Cohort-level slope on log(scale):    {slope_cohort:+.3f}')
            print(f'  → If they match (Simpson-OK), the closed form is just a rescaling of the per-player effect.')


if __name__ == "__main__":
    main()
