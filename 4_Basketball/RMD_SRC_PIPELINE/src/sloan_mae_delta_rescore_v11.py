"""Sloan Test 2 v1.1 — bug-corrected v6.1 LOCKED re-scoring under adjudicated bucketing.

Per amendment SHA <v1.1 lock SHA>. Corrected formula per Stan model + production
projection code (`hierarchical_aging_quadratic_v4.stan` + `models/skill/backtest.py:780-822`).

The position-conditional shift at predict time is ONLY the quadratic position term:
    factor = exp( -gamma_pos[adj_idx] * (age - peak_age_pos[adj_idx])^2
                  + gamma_pos[meta_idx] * (age - peak_age_pos[meta_idx])^2 )

The linear `age_tilt_player[p] * (age - age_center)` term does NOT enter the delta
because age_tilt_player[p] is a FITTED per-player posterior parameter that absorbs
the position information at fit time. At predict time, switching position does NOT
change age_tilt_player[p].

Outputs to D:/NBA Projections/RMD_SRC_PIPELINE/results/sloan_mae_delta/v1_1_corrected/.
v1.0 artifacts at results/sloan_mae_delta/ are PRESERVED in-place at commit 189b61c.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as scistats

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path("D:/NBA Projections")
RESULTS_V11 = ROOT / "RMD_SRC_PIPELINE" / "results" / "sloan_mae_delta" / "v1_1_corrected"
RESULTS_V11.mkdir(parents=True, exist_ok=True)

V6_RAW_2526 = ROOT / "audit_runs/unified_ship_v6_2025_26/per_player_projections_2025-26.csv"
META_PATH = ROOT / "data/parquet/player_metadata_enriched.parquet"
ADJ_PATH = ROOT / "RMD_SRC_PIPELINE/results/position_adjudication_v12.json"

# v6.1 LOCKED apply_offsets parameters (READ-ONLY, unchanged from v1.0)
PTS_CENTER_ADDITIVE = -0.587

# Stan posterior summaries per stat (Phase 4 v4 quadratic, train through 23-24, holdout 24-25).
# READ-ONLY; same input as v1.0.
POSTERIOR_SUMMARY = {
    "REB": ROOT / "audit_runs/20260505T171359Z/skill_backtest_REB_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/posterior_summary.csv",
    "PTS": ROOT / "audit_runs/20260505T154737Z/skill_backtest_PTS_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/posterior_summary.csv",
    "BLK": ROOT / "audit_runs/20260506T140025Z/skill_backtest_BLK_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/posterior_summary.csv",
}

POS_TO_STAN_IDX = {"Guard": 1, "Forward": 2, "Center": 3}


def primary_position_class(pos):
    if not isinstance(pos, str):
        return "Forward"
    first = pos.split("-")[0].strip()
    return first


def load_adjudication():
    with open(ADJ_PATH, encoding="utf-8") as f:
        adj_data = json.load(f)
    return {int(v["nba_api_id"]): {
        "metadata_bucket": v["metadata_bucket_v1"],
        "adjudicated_bucket": v["adjudicated_bucket"],
    } for v in adj_data["verdicts"]}


def load_position_aging(stat):
    """Load only the position-conditional QUADRATIC parameters (gamma_pos and peak_age_pos)
    that enter the predict-time position-switch delta. The linear beta_age_pos and per-player
    age_tilt_player_z are NOT loaded because they do not contribute to the delta."""
    summary_path = POSTERIOR_SUMMARY.get(stat)
    if summary_path is None or not summary_path.exists():
        return None
    df = pd.read_csv(summary_path)
    out = {"peak_age_pos": {}, "gamma_pos": {}}
    for idx in (1, 2, 3):
        for param in ("peak_age_pos", "gamma_pos"):
            row = df[df["param"] == f"{param}[{idx}]"]
            if len(row) == 0:
                out[param][idx] = None
            else:
                out[param][idx] = float(row.iloc[0]["mean"])
    return out


def position_quadratic_term(pos_idx, age, posterior):
    """The position-conditional quadratic term from the Stan model:
        -gamma_pos[k] * (age - peak_age_pos[k])^2
    Per `hierarchical_aging_quadratic_v4.stan:127` and `backtest.py:788`."""
    if posterior is None or posterior["gamma_pos"].get(pos_idx) is None:
        return 0.0
    peak = posterior["peak_age_pos"][pos_idx]
    gamma = posterior["gamma_pos"][pos_idx]
    delta = age - peak
    return -gamma * (delta ** 2)


def position_switch_factor(meta_bucket, adj_bucket, age, posterior):
    """exp(quadratic_term_adj - quadratic_term_meta) at the given age."""
    if meta_bucket == adj_bucket or posterior is None:
        return 1.0
    meta_idx = POS_TO_STAN_IDX.get(meta_bucket)
    adj_idx = POS_TO_STAN_IDX.get(adj_bucket)
    if meta_idx is None or adj_idx is None:
        return 1.0
    q_meta = position_quadratic_term(meta_idx, age, posterior)
    q_adj = position_quadratic_term(adj_idx, age, posterior)
    return float(np.exp(q_adj - q_meta))


def apply_offsets_pts(base_rate, bucket):
    """PTS Center additive offset per `apply_v6_1_locked_offsets_2025_26.py:6`."""
    return base_rate + (PTS_CENTER_ADDITIVE if bucket == "Center" else 0)


def main():
    adj = load_adjudication()
    flip_ids = {pid for pid, b in adj.items()
                if b["metadata_bucket"] == "Forward" and b["adjudicated_bucket"] == "Center"}
    non_flip_ids = {pid for pid, b in adj.items()
                    if b["metadata_bucket"] == b["adjudicated_bucket"]}
    print(f"v1.2 adjudication: {len(adj)} players")
    print(f"  Cohort A (F->C flip): {len(flip_ids)}")
    print(f"  Cohort C (non-flip): {len(non_flip_ids)}")

    meta = pd.read_parquet(META_PATH)[["nba_api_id", "name", "position", "birth_date"]]
    meta["pos_class"] = meta["position"].apply(primary_position_class)
    meta["birth_year"] = pd.to_datetime(meta["birth_date"], errors="coerce").dt.year
    meta["age_2025"] = 2025 - meta["birth_year"]

    v6 = pd.read_csv(V6_RAW_2526)
    v6["nba_api_id"] = v6["nba_api_id"].astype(int)
    df = v6.merge(meta[["nba_api_id", "pos_class", "age_2025"]], on="nba_api_id", how="left")
    df["pos_class"] = df["pos_class"].fillna("Forward")
    df["age_2025"] = df["age_2025"].fillna(28).astype(float)

    pos_full = {"G": "Guard", "F": "Forward", "C": "Center",
                "Guard": "Guard", "Forward": "Forward", "Center": "Center"}
    df["metadata_bucket"] = df["pos_class"].map(pos_full).fillna("Forward")
    df["adjudicated_bucket"] = df.apply(
        lambda r: adj.get(int(r["nba_api_id"]), {}).get("adjudicated_bucket", r["metadata_bucket"]),
        axis=1,
    )
    df["is_adjudicated"] = df["nba_api_id"].isin(adj.keys())
    df["is_flip"] = df["nba_api_id"].isin(flip_ids)
    df["is_non_flip_adj"] = df["nba_api_id"].isin(non_flip_ids)

    print(f"\n25-26 ship intersections: adjudicated={df['is_adjudicated'].sum()}, "
          f"flip={df['is_flip'].sum()}, non-flip-adj={df['is_non_flip_adj'].sum()}")

    posteriors = {s: load_position_aging(s) for s in ("PTS", "REB", "BLK")}
    for s, p in posteriors.items():
        if p is not None:
            print(f"  {s} gamma_pos: " + ", ".join(f"[{k}]={v:.6f}" for k, v in p["gamma_pos"].items()))
            print(f"  {s} peak_age_pos: " + ", ".join(f"[{k}]={v:.3f}" for k, v in p["peak_age_pos"].items()))

    STATS = ["PTS", "REB", "AST", "BLK"]
    out_rows = []
    for _, row in df.iterrows():
        pid = int(row["nba_api_id"])
        name = row["name"]
        age = float(row["age_2025"])
        meta_b = row["metadata_bucket"]
        adj_b = row["adjudicated_bucket"]
        for stat in STATS:
            col_pg = f"{stat}_per_game"
            col_actual = f"{stat}_actual"
            if col_pg not in row or pd.isna(row[col_pg]):
                continue
            base = float(row[col_pg])  # Stan posterior mean (already conditional on metadata-position aging curve)
            actual = float(row[col_actual]) if not pd.isna(row[col_actual]) else None

            # Strip apply_offsets from base (only PTS Center additive is position-conditional)
            # v6 raw is BEFORE apply_offsets, so base is the pure Stan rate.

            # mu_metadata: apply offsets under metadata bucket
            if stat == "PTS":
                mu_meta = apply_offsets_pts(base, meta_b)
            else:
                mu_meta = base

            # mu_adjudicated: apply quadratic position-switch factor, then offsets under adj bucket
            posterior = posteriors.get(stat)
            factor = position_switch_factor(meta_b, adj_b, age, posterior)
            base_adj_rate = base * factor
            if stat == "PTS":
                mu_adj = apply_offsets_pts(base_adj_rate, adj_b)
            else:
                mu_adj = base_adj_rate

            out_rows.append({
                "nba_api_id": pid,
                "name": name,
                "age_2025": age,
                "metadata_bucket": meta_b,
                "adjudicated_bucket": adj_b,
                "is_adjudicated": bool(row["is_adjudicated"]),
                "is_flip": bool(row["is_flip"]),
                "is_non_flip_adj": bool(row["is_non_flip_adj"]),
                "stat": stat,
                "stan_factor": factor,
                "mu_metadata": mu_meta,
                "mu_adjudicated": mu_adj,
                "delta_mu": mu_adj - mu_meta,
                "actual": actual,
                "ae_metadata": abs(actual - mu_meta) if actual is not None else None,
                "ae_adjudicated": abs(actual - mu_adj) if actual is not None else None,
                "delta_ae": (abs(actual - mu_meta) - abs(actual - mu_adj)) if actual is not None else None,
            })

    proj_df = pd.DataFrame(out_rows)
    proj_df.to_parquet(RESULTS_V11 / "per_player_projections_25-26.parquet", index=False)
    print(f"\nWrote {RESULTS_V11 / 'per_player_projections_25-26.parquet'} ({len(proj_df)} rows)")

    # Pipeline integrity check (§3.5)
    print("\n=== Pipeline integrity check (v1.1) ===")
    cohort_c = proj_df[proj_df["is_non_flip_adj"]]
    integrity_rows = []
    for stat in STATS:
        s = cohort_c[cohort_c["stat"] == stat]
        max_abs_delta = s["delta_mu"].abs().max() if len(s) > 0 else 0
        n = len(s)
        passed = max_abs_delta < 1e-6
        print(f"  Cohort C {stat}: n={n}, max |delta_mu|={max_abs_delta:.2e}, "
              f"{'PASS' if passed else 'FAIL'}")
        integrity_rows.append({"stat": stat, "n": n, "max_abs_delta": float(max_abs_delta), "pass": bool(passed)})

    with open(RESULTS_V11 / "pipeline_integrity_check.md", "w", encoding="utf-8") as f:
        f.write("# Pipeline integrity check (v1.1 corrected)\n\n")
        f.write("Per amendment v1.1 §3.5: Cohort C (non-flip) must show |delta_mu| < 1e-6.\n\n")
        f.write("| Stat | n | max |delta_mu| | Status |\n|---|---|---|---|\n")
        for r in integrity_rows:
            f.write(f"| {r['stat']} | {r['n']} | {r['max_abs_delta']:.2e} | "
                    f"{'PASS' if r['pass'] else 'FAIL'} |\n")

    # MAE statistics (same cells as v1.0)
    SEASON = "25-26"
    cell_results = []
    rng = np.random.default_rng(20260602)
    B = 1000

    print("\n=== MAE delta statistics (v1.1) ===")
    for cohort_name, mask in [
        ("A_flip", proj_df["is_flip"]),
        ("B_all_230", proj_df["is_adjudicated"]),
        ("C_non_flip", proj_df["is_non_flip_adj"]),
    ]:
        sub = proj_df[mask & proj_df["ae_metadata"].notna()]
        for stat in STATS:
            cell = sub[sub["stat"] == stat]
            n = len(cell)
            if n < 8:
                cell_results.append({"cohort": cohort_name, "season": SEASON, "stat": stat,
                                     "n": n, "disposition": "INCONCLUSIVE_POWER_LIMITED"})
                continue
            ae_meta = cell["ae_metadata"].values
            ae_adj = cell["ae_adjudicated"].values
            mae_meta = float(ae_meta.mean())
            mae_adj = float(ae_adj.mean())
            delta = mae_meta - mae_adj
            boot_deltas = np.zeros(B)
            for b in range(B):
                idx = rng.integers(0, n, size=n)
                boot_deltas[b] = ae_meta[idx].mean() - ae_adj[idx].mean()
            ci_lo, ci_hi = float(np.percentile(boot_deltas, 2.5)), float(np.percentile(boot_deltas, 97.5))
            paired = ae_meta - ae_adj
            if np.all(paired == 0):
                w_p = 1.0
            else:
                try:
                    _, w_p = scistats.wilcoxon(paired, zero_method="wilcox", alternative="two-sided")
                except Exception:
                    w_p = float("nan")
            cell_results.append({"cohort": cohort_name, "season": SEASON, "stat": stat,
                                 "n": n, "mae_metadata": mae_meta, "mae_adjudicated": mae_adj,
                                 "delta": delta, "ci95_lo": ci_lo, "ci95_hi": ci_hi,
                                 "wilcoxon_p": float(w_p),
                                 "pct_improvement": 100.0 * delta / mae_meta if mae_meta > 0 else float("nan")})
            print(f"  {cohort_name} {stat} n={n}: MAE meta={mae_meta:.3f}, adj={mae_adj:.3f}, "
                  f"delta={delta:+.4f} ({100.0 * delta / mae_meta:+.1f}%) "
                  f"CI95=[{ci_lo:+.4f}, {ci_hi:+.4f}] wilcoxon_p={w_p:.4f}")

    cell_df = pd.DataFrame(cell_results)
    cell_df.to_csv(RESULTS_V11 / "cohort_aggregate_mae_25-26.csv", index=False)
    print(f"\nWrote {RESULTS_V11 / 'cohort_aggregate_mae_25-26.csv'}")

    # Named-player tables (v1.1)
    LABEL_PRIORITY = [
        "Anthony Davis", "Giannis Antetokounmpo", "Kevin Love", "Mason Plumlee",
        "Kristaps Porziņģis", "Kelly Olynyk", "Dwight Powell", "Taj Gibson",
    ]
    named = proj_df[proj_df["name"].isin(LABEL_PRIORITY) & proj_df["is_flip"]]
    if len(named) > 0:
        named.to_csv(RESULTS_V11 / "named_player_table_25-26.csv", index=False)
        print(f"\nNamed-player table (v1.1): {len(named)} rows")
        print(named[["name", "stat", "stan_factor", "mu_metadata", "mu_adjudicated", "actual",
                     "ae_metadata", "ae_adjudicated", "delta_ae"]].to_string())


if __name__ == "__main__":
    main()
