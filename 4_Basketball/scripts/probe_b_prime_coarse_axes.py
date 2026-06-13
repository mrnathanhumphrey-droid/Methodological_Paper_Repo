"""Probe B' — coarser-axis follow-up to Probe B.

Tests whether residue-class structure beyond v6.3-A is detectable when the
context space is reduced from 648 -> 72 configs (drops pace_tier and role to
keep more obs per cell).

Axes (4 of original 6):
  opp_class (4) x record_tier (3) x season_phase (3) x home_away (2) = 72

Same clustering + bootstrap protocol as Probe B. Reuses the bug-fixed tagging
logic from probe_b_contextual_a_final.py.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")
from pathlib import Path
import json
import time
import warnings

import numpy as np
import pandas as pd

from probe_b_contextual_a_final import (
    build_opp_def_rating_quartile, build_pace_tercile, build_role_stability,
    build_24_25_winpct, build_opp_record_tier_lookup, build_season_phase,
    aggregate_configs, build_distance_matrix, cluster_validity,
    cohort_bootstrap, find_top_pairs, T_GRID, K_VALUES, MIN_CONFIG_OBS, STATS,
)

warnings.filterwarnings("ignore", category=RuntimeWarning)

REPO = Path(".")
PQ = REPO / "data" / "parquet"
RESID_CSV = REPO / "audit_runs" / "v6_3_A_baseline_2025_26" / "v6_3_A_residuals.csv"
OUT_DIR = REPO / "audit_runs" / "probe_b_prime_coarse"
OUT_DIR.mkdir(parents=True, exist_ok=True)

N_BOOTSTRAP = 500


def main():
    print("[load] v6.3-A residuals")
    rdf = pd.read_csv(RESID_CSV, parse_dates=["game_date"])

    print("[load] historical box scores")
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx["game_date"] = pd.to_datetime(bx["game_date"])
    bx["nba_api_id"] = bx["nba_api_id"].astype(int)
    bx["game_id"] = bx["game_id"].astype(str).str.lstrip("0").astype(int)
    bx_25_26 = bx[(bx["season"] == "2025-26") &
                    (bx["season_type"] == "Regular Season")].copy()
    bx_25_26["minutes"] = pd.to_numeric(bx_25_26["minutes"], errors="coerce")

    print("[build] context lookups (4 of 6 axes)")
    opp_class_map = build_opp_def_rating_quartile(bx)
    rank_24_25_winpct = build_24_25_winpct(bx)
    opp_record_tier = build_opp_record_tier_lookup(bx_25_26, rank_24_25_winpct)

    # team_game_n for season_phase
    tg = (bx_25_26.groupby(["team_abbr", "game_id", "game_date"])
                  .size().reset_index(name="_n"))
    tg = tg.sort_values(["team_abbr", "game_date"]).reset_index(drop=True)
    tg["team_game_n"] = tg.groupby("team_abbr").cumcount() + 1
    team_game_n_map = dict(zip(zip(tg["team_abbr"], tg["game_id"]),
                                tg["team_game_n"]))

    # is_home lookup
    is_home_map = dict(zip(zip(bx_25_26["nba_api_id"], bx_25_26["game_id"]),
                            bx_25_26["is_home"]))

    season_phase_fn = build_season_phase(None, None, team_total_games=82)

    print("[tag] residuals (coarse — 4 axes)")
    rdf["opp_class"] = rdf["opp_abbr"].map(opp_class_map).fillna("mid")
    rdf["is_home"] = rdf.apply(
        lambda r: is_home_map.get((int(r["nba_api_id"]), r["game_id"]), False),
        axis=1)
    rdf["home_away"] = rdf["is_home"].map({True: "home", False: "away"})
    rdf["record_tier"] = rdf.apply(
        lambda r: opp_record_tier.get((r["opp_abbr"], r["game_date"]), "mid"),
        axis=1)
    rdf["team_game_n_self"] = rdf.apply(
        lambda r: team_game_n_map.get((r["team_abbr"], r["game_id"]), np.nan),
        axis=1)
    rdf["season_phase"] = rdf.apply(
        lambda r: season_phase_fn(r["game_date"], r["team_game_n_self"]),
        axis=1)

    rdf["config"] = (rdf["opp_class"] + "_" + rdf["record_tier"] + "_" +
                       rdf["season_phase"] + "_" + rdf["home_away"])

    print(f"  unique configs in data: {rdf['config'].nunique()} (of 72 possible)")

    cohorts = []
    for cohort_v in ["rookie", "soph", "vet"]:
        for pos_v in ["Center", "Forward", "Guard"]:
            cohorts.append((cohort_v, pos_v))

    print("\n[analyze] per-cohort × stat (72-config space)")
    all_results = []
    all_top_pairs = []
    for cohort_v, pos_v in cohorts:
        sub = rdf[(rdf["cohort"] == cohort_v) & (rdf["pos_class"] == pos_v)]
        if len(sub) < 100:
            print(f"\n[skip] {cohort_v}_{pos_v}: n={len(sub)} < 100")
            for stat in STATS:
                all_results.append({
                    "cohort": f"{cohort_v}_{pos_v}", "stat": stat,
                    "n_obs": len(sub), "n_configs_retained": 0,
                    "verdict": "insufficient_n", "k_star": None,
                    "silhouette_obs": None, "p_value": None,
                })
            continue
        for stat in STATS:
            print(f"\n[run] {cohort_v}_{pos_v} / {stat}")
            t0 = time.time()
            result = analyze_cohort_local(sub, f"{cohort_v}_{pos_v}", stat)
            elapsed = time.time() - t0
            print(f"  done in {elapsed:.1f}s, verdict: {result['verdict']}")
            top = find_top_pairs(result, sub, stat)
            for pair in top:
                pair["cohort"] = f"{cohort_v}_{pos_v}"
                pair["stat"] = stat
                all_top_pairs.append(pair)
            all_results.append(result)

    print("\n[save] outputs")
    verdict_rows = []
    for r in all_results:
        verdict_rows.append({
            "cohort": r["cohort"], "stat": r["stat"], "n_obs": r["n_obs"],
            "n_configs_retained": r["n_configs_retained"],
            "k_star": r["k_star"], "silhouette_obs": r["silhouette_obs"],
            "p_value": r["p_value"], "verdict": r["verdict"],
        })
    pd.DataFrame(verdict_rows).to_csv(
        OUT_DIR / "result_verdicts.csv", index=False)

    assign_rows = []
    for r in all_results:
        if r.get("labels_at_kstar"):
            for cfg, lbl in zip(r["configs"], r["labels_at_kstar"]):
                assign_rows.append({"cohort": r["cohort"], "stat": r["stat"],
                                     "config": cfg, "cluster": int(lbl)})
    pd.DataFrame(assign_rows).to_csv(
        OUT_DIR / "result_per_cohort.csv", index=False)

    boot_rows = []
    for r in all_results:
        if r.get("null_distribution"):
            for entry in r["null_distribution"]:
                entry["cohort"] = r["cohort"]
                entry["stat"] = r["stat"]
                boot_rows.append(entry)
    pd.DataFrame(boot_rows).to_csv(
        OUT_DIR / "result_bootstrap.csv", index=False)

    pd.DataFrame(all_top_pairs).to_csv(
        OUT_DIR / "result_top_pairs.csv", index=False)

    summary = {"results": [{k: v for k, v in r.items()
                              if k not in ("null_distribution", "all_validity",
                                            "labels_at_kstar", "configs")}
                             for r in all_results]}
    with open(OUT_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\nDONE. Outputs at {OUT_DIR}")


def analyze_cohort_local(df_cohort, cohort_label, stat, n_boot=N_BOOTSTRAP):
    from probe_b_contextual_a_final import (
        aggregate_configs, build_distance_matrix, cluster_validity,
        cohort_bootstrap, MIN_CONFIG_OBS,
    )
    from scipy.cluster.hierarchy import linkage, fcluster
    from scipy.spatial.distance import squareform

    n_obs = len(df_cohort)
    print(f"  [{cohort_label} / {stat}] n_obs={n_obs}")
    configs, moms, cfs, ns = aggregate_configs(df_cohort, stat)
    n_configs = len(configs)
    print(f"    configs retained (>={MIN_CONFIG_OBS} obs): {n_configs} of 72 possible")
    if n_configs < 8:
        return {
            "cohort": cohort_label, "stat": stat, "n_obs": n_obs,
            "n_configs_retained": n_configs,
            "verdict": "insufficient_configs",
            "k_star": None, "silhouette_obs": None, "p_value": None,
            "configs": configs, "labels_at_kstar": [],
        }
    d, d_mom, d_phi = build_distance_matrix(moms, cfs)
    val = cluster_validity(d, ns)
    if not val:
        return {
            "cohort": cohort_label, "stat": stat, "n_obs": n_obs,
            "n_configs_retained": n_configs,
            "verdict": "clustering_failed",
            "k_star": None, "silhouette_obs": None, "p_value": None,
            "configs": configs, "labels_at_kstar": [],
        }
    k_star = max(val.keys(), key=lambda k: val[k]["silhouette"])
    sil_obs = val[k_star]["silhouette"]
    print(f"    k*={k_star}, silhouette={sil_obs:.4f}")

    print(f"    bootstrap n_boot={n_boot}")
    t0 = time.time()
    null_df = cohort_bootstrap(df_cohort, stat, n_boot=n_boot, n_workers=8)
    print(f"    bootstrap took {time.time()-t0:.1f}s")
    null_at_kstar = null_df[null_df["k"] == k_star]["silhouette_null"].dropna().values
    if len(null_at_kstar) == 0:
        p = np.nan
    else:
        p = (null_at_kstar >= sil_obs).mean()

    if k_star is not None and 4 <= k_star <= 16 and p < 0.05:
        verdict = "structure_detected"
    elif k_star is None or k_star > 30 or (p is not None and p >= 0.05):
        if n_obs < 1000:
            verdict = "no_structure_underpowered"
        else:
            verdict = "no_structure"
    else:
        verdict = "ambiguous"

    np.fill_diagonal(d, 0)
    cond = squareform(d, checks=False)
    Z = linkage(cond, method="average")
    labels_at_kstar = fcluster(Z, t=k_star, criterion="maxclust")

    return {
        "cohort": cohort_label, "stat": stat, "n_obs": n_obs,
        "n_configs_retained": n_configs,
        "verdict": verdict,
        "k_star": k_star, "silhouette_obs": sil_obs, "p_value": float(p),
        "configs": configs, "labels_at_kstar": labels_at_kstar.tolist(),
        "all_validity": val,
        "null_distribution": null_df.to_dict(orient="records"),
    }


if __name__ == "__main__":
    main()
