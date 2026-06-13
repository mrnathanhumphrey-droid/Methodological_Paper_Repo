"""Two cheap follow-ups:
  1) F-test sensitivity on PTS x Center across 3 seasons
     (Levene's vs F-test for variance equality; settles paper p=0.024 vs 0.21)
  2) Probe B coarser axes (24 configs = opp_class x record_tier x home_away,
     dropping season_phase) on pooled 3-season residuals
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(".")
PQ = REPO / "data" / "parquet"
OUT_DIR = REPO / "audit_runs" / "followup_ftest_24config"
OUT_DIR.mkdir(parents=True, exist_ok=True)

POOLED_RESID = REPO / "audit_runs" / "multi_season_replication" / "pooled_residuals.csv"


# ────────────────────────────────────────────────────────────────────────
# Part 1: F-test sensitivity on PTS x Center
# ────────────────────────────────────────────────────────────────────────

def f_test_two_sided(arr_in, arr_out):
    """Two-sided F-test for variance equality.
    Returns ratio = var_in / var_out, F-stat, p-value (two-sided).
    """
    a = np.asarray(arr_in, dtype=float)
    b = np.asarray(arr_out, dtype=float)
    var_a = a.var(ddof=1)
    var_b = b.var(ddof=1)
    if var_b == 0 or var_a == 0:
        return np.nan, np.nan, np.nan
    F = var_a / var_b
    df_a = len(a) - 1
    df_b = len(b) - 1
    # two-sided p: 2*min(P(F<=f), P(F>=f))
    cdf = stats.f.cdf(F, df_a, df_b)
    p = 2 * min(cdf, 1 - cdf)
    return float(F), float(F), float(p)


def part_1_ftest():
    print("=" * 70)
    print("PART 1: F-test sensitivity on PTS x Center (3 seasons)")
    print("=" * 70)

    # Load residuals from each source as we did in multi_season_replication.py
    # 23-24, 24-25 from per-player projection CSVs;
    # 25-26 from v6.1 ship + box-score actuals (full ship cohort)
    rows = []

    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    sup_path = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "rookie_metadata_supplement.parquet"
    if sup_path.exists():
        sup = pd.read_parquet(sup_path)
        cols = ["nba_api_id", "name", "position", "draft_year", "debut_year"]
        meta = pd.concat([meta[cols], sup[cols]], ignore_index=True)
    meta["nba_api_id"] = meta["nba_api_id"].astype(int)

    def position_class(p):
        if pd.isna(p) or not p or str(p).strip() == "": return "Forward"
        s = str(p).lower()
        if "center" in s: return "Center"
        if "guard" in s: return "Guard"
        return "Forward"

    proj_paths = {
        "2023-24": "audit_runs/20260505T211540Z/skill_backtest_PTS_phase4_v4_quadratic_tq_g_2017-18-2018-19-2019-20-2020-21-2021-22-2022-23__2023-24/per_player_projections.csv",
        "2024-25": "audit_runs/20260505T154737Z/skill_backtest_PTS_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/per_player_projections.csv",
    }
    for season, path in proj_paths.items():
        df = pd.read_csv(path)
        df["nba_api_id"] = df["nba_api_id"].astype(int)
        df["error"] = df["actual"] - df["proj_mean"]
        df = df.merge(meta[["nba_api_id", "position"]], on="nba_api_id", how="left")
        df["pos_class"] = df["position"].apply(position_class)
        in_mask = df["pos_class"] == "Center"
        r_in = df.loc[in_mask, "error"].dropna().values
        r_out = df.loc[~in_mask, "error"].dropna().values
        # Levene's
        try:
            _, p_lev = stats.levene(r_in, r_out, center="median")
        except Exception:
            p_lev = np.nan
        F, _, p_F = f_test_two_sided(r_in, r_out)
        # Bartlett (sensitive to non-normality, sometimes used in older lit)
        try:
            _, p_bart = stats.bartlett(r_in, r_out)
        except Exception:
            p_bart = np.nan
        # Brown-Forsythe = Levene with center='median' (already the default)
        rows.append({
            "season": season, "test_set": "Stan vets only (n=200 cap)",
            "n_in": len(r_in), "n_out": len(r_out),
            "var_in": float(r_in.var(ddof=1)),
            "var_out": float(r_out.var(ddof=1)),
            "ratio_var": float(r_in.var(ddof=1) / r_out.var(ddof=1))
                if r_out.var(ddof=1) > 0 else np.nan,
            "ratio_sd": float(r_in.std(ddof=1) / r_out.std(ddof=1))
                if r_out.std(ddof=1) > 0 else np.nan,
            "p_levene": float(p_lev),
            "p_bartlett": float(p_bart),
            "p_F_two_sided": float(p_F),
        })

    # 25-26 from full ship + box-score actuals
    ship = pd.read_csv(REPO / "audit_runs" / "unified_ship_v6_1_2025_26"
                          / "per_player_projections_2025-26.csv")
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx_2526 = bx[(bx["season"] == "2025-26") &
                   (bx["season_type"] == "Regular Season")].copy()
    bx_2526["minutes"] = pd.to_numeric(bx_2526["minutes"], errors="coerce")
    bx_2526 = bx_2526[bx_2526["minutes"] > 0]
    bx_2526["nba_api_id"] = bx_2526["nba_api_id"].astype(int)
    actuals = bx_2526.groupby("nba_api_id").agg(PTS_actual=("PTS", "mean")).reset_index()

    # Map synthetic rookie IDs
    rookie_real_id = {}
    if sup_path.exists():
        sup = pd.read_parquet(sup_path)
        meta_base = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
        real_name_id = dict(zip(meta_base["name"].str.lower().fillna(""),
                                  meta_base["nba_api_id"].astype(int)))
        for _, r in sup.iterrows():
            nm = (r["name"] or "").strip().lower()
            if nm in real_name_id:
                rookie_real_id[int(r["nba_api_id"])] = real_name_id[nm]
    ship["real_id"] = ship["nba_api_id"].map(
        lambda x: rookie_real_id.get(int(x), int(x))).astype(int)
    # Drop stale ship actuals
    stale = [c for c in ship.columns if c.endswith("_actual")]
    ship = ship.drop(columns=stale)
    df = ship.merge(actuals, left_on="real_id", right_on="nba_api_id",
                      how="left", suffixes=("", "_act"))
    df["resid"] = df["PTS_actual"] - df["PTS_per_game"]
    df = df.merge(meta[["nba_api_id", "position"]], left_on="real_id",
                    right_on="nba_api_id", how="left", suffixes=("", "_m"))
    df["pos_class"] = df["position"].apply(position_class)
    in_mask = df["pos_class"] == "Center"
    r_in = df.loc[in_mask, "resid"].dropna().values
    r_out = df.loc[~in_mask, "resid"].dropna().values
    try:
        _, p_lev = stats.levene(r_in, r_out, center="median")
    except Exception:
        p_lev = np.nan
    F, _, p_F = f_test_two_sided(r_in, r_out)
    try:
        _, p_bart = stats.bartlett(r_in, r_out)
    except Exception:
        p_bart = np.nan
    rows.append({
        "season": "2025-26", "test_set": "Full ship (n=567)",
        "n_in": len(r_in), "n_out": len(r_out),
        "var_in": float(r_in.var(ddof=1)),
        "var_out": float(r_out.var(ddof=1)),
        "ratio_var": float(r_in.var(ddof=1) / r_out.var(ddof=1))
            if r_out.var(ddof=1) > 0 else np.nan,
        "ratio_sd": float(r_in.std(ddof=1) / r_out.std(ddof=1))
            if r_out.std(ddof=1) > 0 else np.nan,
        "p_levene": float(p_lev),
        "p_bartlett": float(p_bart),
        "p_F_two_sided": float(p_F),
    })

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    out.to_csv(OUT_DIR / "pts_center_ftest_sensitivity.csv", index=False)
    print(f"\n[save] {OUT_DIR / 'pts_center_ftest_sensitivity.csv'}")
    return out


# ────────────────────────────────────────────────────────────────────────
# Part 2: Probe B 24-config (opp_class x record_tier x home_away)
# ────────────────────────────────────────────────────────────────────────

def part_2_24config():
    print("\n" + "=" * 70)
    print("PART 2: Probe B 24-config (drop season_phase) on pooled 3-season")
    print("=" * 70)

    pooled = pd.read_csv(POOLED_RESID, parse_dates=["game_date"])
    print(f"  pooled rows: {len(pooled)}")
    # Build 24-config = opp_class x record_tier x home_away
    pooled["config"] = (pooled["opp_class"] + "_" +
                          pooled["record_tier"] + "_" +
                          pooled["home_away"])
    print(f"  unique configs: {pooled['config'].nunique()} (of 24 possible)")

    # Reuse Probe B helpers — need to rename for compatibility
    pooled_for_test = pooled.copy()
    for stat in ("PTS", "REB", "AST"):
        pooled_for_test[f"{stat}_resid_v6_3_A"] = pooled_for_test[f"{stat}_resid"]

    from probe_b_contextual_a_final import (
        aggregate_configs as agg_b, build_distance_matrix,
        cluster_validity, cohort_bootstrap,
    )
    from scipy.cluster.hierarchy import linkage, fcluster
    from scipy.spatial.distance import squareform

    cohorts = []
    for cohort_v in ("rookie", "soph", "vet"):
        for pos_v in ("Center", "Forward", "Guard"):
            cohorts.append((cohort_v, pos_v))

    rows = []
    for cohort_v, pos_v in cohorts:
        sub = pooled_for_test[(pooled_for_test["cohort"] == cohort_v) &
                                (pooled_for_test["pos_class"] == pos_v)]
        if len(sub) < 100:
            for stat in ("PTS", "REB", "AST"):
                rows.append({"cohort": f"{cohort_v}_{pos_v}", "stat": stat,
                              "n_obs": len(sub), "n_configs": 0,
                              "verdict": "insufficient_n"})
            continue
        for stat in ("PTS", "REB", "AST"):
            configs, moms, cfs, ns = agg_b(sub, stat)
            n_configs = len(configs)
            if n_configs < 8:
                rows.append({"cohort": f"{cohort_v}_{pos_v}", "stat": stat,
                              "n_obs": len(sub), "n_configs": n_configs,
                              "verdict": "insufficient_configs"})
                continue
            d, _, _ = build_distance_matrix(moms, cfs)
            val = cluster_validity(d, ns)
            if not val:
                rows.append({"cohort": f"{cohort_v}_{pos_v}", "stat": stat,
                              "n_obs": len(sub), "n_configs": n_configs,
                              "verdict": "clustering_failed"})
                continue
            k_star = max(val.keys(), key=lambda k: val[k]["silhouette"])
            sil = val[k_star]["silhouette"]
            null_df = cohort_bootstrap(sub, stat, n_boot=300, n_workers=8)
            null_at_kstar = null_df[null_df["k"] == k_star]["silhouette_null"].dropna().values
            p = (null_at_kstar >= sil).mean() if len(null_at_kstar) else np.nan
            np.fill_diagonal(d, 0)
            cond = squareform(d, checks=False)
            Z = linkage(cond, method="average")
            labels = fcluster(Z, t=k_star, criterion="maxclust")
            cfg_to_label = dict(zip(configs, labels))
            df_lbl = sub.copy()
            df_lbl["cluster"] = df_lbl["config"].map(cfg_to_label)
            cluster_sizes = df_lbl["cluster"].dropna().astype(int).value_counts().to_dict()
            outlier_cluster = min(cluster_sizes, key=cluster_sizes.get)
            outlier_configs = [c for c, lbl in cfg_to_label.items() if lbl == outlier_cluster]
            verdict = ("structure_detected"
                        if 4 <= k_star <= 16 and p < 0.05
                        else ("ambiguous"
                              if p is not None and p < 0.05
                              else "no_structure"))
            rows.append({
                "cohort": f"{cohort_v}_{pos_v}", "stat": stat,
                "n_obs": len(sub), "n_configs": n_configs,
                "k_star": int(k_star), "silhouette": float(sil),
                "p_value": float(p), "verdict": verdict,
                "outlier_cluster_size": len(outlier_configs),
                "outlier_configs": "; ".join(outlier_configs[:10]),
            })
            print(f"  {cohort_v}_{pos_v}/{stat}: n={len(sub)}, "
                  f"configs={n_configs}, k*={k_star}, "
                  f"sil={sil:.3f}, p={p:.3f}, verdict={verdict}, "
                  f"outlier=[{', '.join(outlier_configs[:3])}]")

    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "probe_b_24config_pooled.csv", index=False)
    print(f"\n[save] {OUT_DIR / 'probe_b_24config_pooled.csv'}")

    # Summary
    valid = out.dropna(subset=["p_value"])
    print()
    print(f"Total testable cells: {len(valid)} / 27")
    print(f"  p<0.05: {(valid['p_value'] < 0.05).sum()}")
    print(f"  p<0.05 AND k* in [4,16]: "
          f"{((valid['p_value'] < 0.05) & valid['k_star'].between(4, 16)).sum()}")
    bonf = 0.05 / max(1, len(valid))
    print(f"  Bonferroni-corrected (alpha={bonf:.4f}): "
          f"{(valid['p_value'] < bonf).sum()}")
    return out


def main():
    out1 = part_1_ftest()
    out2 = part_2_24config()
    print("\nDONE.")


if __name__ == "__main__":
    main()
