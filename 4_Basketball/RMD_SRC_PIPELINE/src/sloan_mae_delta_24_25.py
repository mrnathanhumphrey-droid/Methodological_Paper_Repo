"""Sloan Test 2 — 24-25 backtest extension.

24-25 backtest projections are per-stat CSVs (one per PTS / REB / AST / BLK)
with columns proj_mean / proj_sd / actual / abs_error. Stan-vet cohort.

Reads from per-stat backtest paths matching v6.1 LOCKED training spec
(through 23-24 train, 24-25 holdout).

Per pre-reg SHA 49fd54b §2.1: 24-25 cell uses Stan vet pool 200-player cap.

Output: appends rows to existing per_player_projections + cohort aggregate
CSVs with season='24-25'.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as scistats

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path("D:/NBA Projections")
RESULTS = ROOT / "RMD_SRC_PIPELINE" / "results" / "sloan_mae_delta"
ADJ_PATH = ROOT / "RMD_SRC_PIPELINE/results/position_adjudication_v12.json"
META_PATH = ROOT / "data/parquet/player_metadata_enriched.parquet"

PTS_CENTER_ADDITIVE = -0.587

BACKTEST_24_25 = {
    "PTS": ROOT / "audit_runs/20260505T154737Z/skill_backtest_PTS_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/per_player_projections.csv",
    "REB": ROOT / "audit_runs/20260505T171359Z/skill_backtest_REB_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/per_player_projections.csv",
    "BLK": ROOT / "audit_runs/20260506T140025Z/skill_backtest_BLK_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/per_player_projections.csv",
}

POSTERIOR_24_25 = {
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


def load_position_aging(stat):
    summary_path = POSTERIOR_24_25.get(stat)
    if summary_path is None or not summary_path.exists():
        return None
    df = pd.read_csv(summary_path)
    out = {"mu_position": {}, "peak_age_pos": {}, "beta_age_pos": {}, "gamma_pos": {}}
    for idx in (1, 2, 3):
        for param in ("mu_position", "peak_age_pos", "beta_age_pos", "gamma_pos"):
            row = df[df["param"] == f"{param}[{idx}]"]
            if len(row) == 0:
                out[param][idx] = None
            else:
                out[param][idx] = float(row.iloc[0]["mean"])
    return out


def age_tilt(pos_idx, age, posterior):
    if posterior is None or posterior["beta_age_pos"].get(pos_idx) is None:
        return 0.0
    peak = posterior["peak_age_pos"][pos_idx]
    beta = posterior["beta_age_pos"][pos_idx]
    gamma = posterior["gamma_pos"][pos_idx]
    delta = age - peak
    return beta * delta + gamma * (delta ** 2)


def main():
    with open(ADJ_PATH, encoding="utf-8") as f:
        adj_data = json.load(f)
    adj = {int(v["nba_api_id"]): v for v in adj_data["verdicts"]}
    flip_ids = {pid for pid, v in adj.items()
                if v["metadata_bucket_v1"] == "Forward" and v["adjudicated_bucket"] == "Center"}
    non_flip_ids = {pid for pid, v in adj.items()
                    if v["metadata_bucket_v1"] == v["adjudicated_bucket"]}
    print(f"Cohort A flip: {len(flip_ids)}, Cohort C non-flip: {len(non_flip_ids)}")

    meta = pd.read_parquet(META_PATH)[["nba_api_id", "name", "position", "birth_date"]]
    meta["pos_class"] = meta["position"].apply(primary_position_class)
    meta["birth_year"] = pd.to_datetime(meta["birth_date"], errors="coerce").dt.year
    meta["age_2024"] = 2024 - meta["birth_year"]

    pos_full = {"G": "Guard", "F": "Forward", "C": "Center",
                "Guard": "Guard", "Forward": "Forward", "Center": "Center"}

    out_rows = []
    posteriors = {s: load_position_aging(s) for s in ("PTS", "REB", "BLK")}

    for stat, backtest_path in BACKTEST_24_25.items():
        if not backtest_path.exists():
            print(f"  [warn] backtest missing for {stat}: {backtest_path}")
            continue
        bt = pd.read_csv(backtest_path)
        bt["nba_api_id"] = bt["nba_api_id"].astype(int)
        bt = bt.merge(meta[["nba_api_id", "pos_class", "age_2024"]], on="nba_api_id", how="left")
        bt["pos_class"] = bt["pos_class"].fillna("Forward")
        bt["age_2024"] = bt["age_2024"].fillna(28).astype(float)
        bt["metadata_bucket"] = bt["pos_class"].map(pos_full).fillna("Forward")
        bt["adjudicated_bucket"] = bt["nba_api_id"].apply(
            lambda pid: adj.get(int(pid), {}).get("adjudicated_bucket")
        )
        bt["adjudicated_bucket"] = bt["adjudicated_bucket"].fillna(bt["metadata_bucket"])
        bt["is_adjudicated"] = bt["nba_api_id"].isin(adj.keys())
        bt["is_flip"] = bt["nba_api_id"].isin(flip_ids)
        bt["is_non_flip_adj"] = bt["nba_api_id"].isin(non_flip_ids)

        posterior = posteriors.get(stat)
        for _, row in bt.iterrows():
            pid = int(row["nba_api_id"])
            base = float(row["proj_mean"])  # backtest's projected mean (v6.1 LOCKED apply_offsets already applied for Center if metadata=Center)
            actual = float(row["actual"]) if not pd.isna(row["actual"]) else None
            age = float(row["age_2024"])
            meta_b = row["metadata_bucket"]
            adj_b = row["adjudicated_bucket"]

            # Backtest CSV is the raw Stan output BEFORE apply_offsets (Phase 4 per-stat backtest
            # output is the model's posterior predictive mean). The PTS additive offset is NOT
            # applied in these per-stat backtests; they're the unmodified Stan output.
            mu_meta = base
            mu_adj = base

            # Apply PTS additive under each bucket
            if stat == "PTS":
                if meta_b == "Center":
                    mu_meta += PTS_CENTER_ADDITIVE
                if adj_b == "Center":
                    mu_adj += PTS_CENTER_ADDITIVE

            # Stan aging-curve delta for flip players
            if posterior is not None and meta_b != adj_b:
                meta_idx = POS_TO_STAN_IDX.get(meta_b)
                adj_idx = POS_TO_STAN_IDX.get(adj_b)
                if meta_idx is not None and adj_idx is not None:
                    aging_meta = age_tilt(meta_idx, age, posterior)
                    aging_adj = age_tilt(adj_idx, age, posterior)
                    factor = float(np.exp(aging_adj - aging_meta))
                    if stat == "PTS":
                        rate_meta = mu_meta - (PTS_CENTER_ADDITIVE if meta_b == "Center" else 0)
                        rate_adj = rate_meta * factor
                        mu_adj = rate_adj + (PTS_CENTER_ADDITIVE if adj_b == "Center" else 0)
                    else:
                        mu_adj = base * factor

            out_rows.append({
                "nba_api_id": pid,
                "name": row["name"],
                "age_2024": age,
                "metadata_bucket": meta_b,
                "adjudicated_bucket": adj_b,
                "is_adjudicated": bool(row["is_adjudicated"]),
                "is_flip": bool(row["is_flip"]),
                "is_non_flip_adj": bool(row["is_non_flip_adj"]),
                "stat": stat,
                "mu_metadata": mu_meta,
                "mu_adjudicated": mu_adj,
                "delta_mu": mu_adj - mu_meta,
                "actual": actual,
                "ae_metadata": abs(actual - mu_meta) if actual is not None else None,
                "ae_adjudicated": abs(actual - mu_adj) if actual is not None else None,
                "delta_ae": (abs(actual - mu_meta) - abs(actual - mu_adj)) if actual is not None else None,
            })

    proj_df = pd.DataFrame(out_rows)
    proj_df.to_parquet(RESULTS / "per_player_projections_24-25.parquet", index=False)
    print(f"\nWrote {RESULTS / 'per_player_projections_24-25.parquet'} ({len(proj_df)} rows)")

    # Pipeline integrity check
    print("\n=== Pipeline integrity check (24-25) ===")
    cohort_c = proj_df[proj_df["is_non_flip_adj"]]
    for stat in ("PTS", "REB", "BLK"):
        s = cohort_c[cohort_c["stat"] == stat]
        max_abs_delta = s["delta_mu"].abs().max()
        n = len(s)
        passed = max_abs_delta < 1e-6
        print(f"  Cohort C {stat}: n={n}, max |delta_mu| = {max_abs_delta:.2e}, {'PASS' if passed else 'FAIL'}")

    # MAE statistics
    SEASON = "24-25"
    cell_results = []
    rng = np.random.default_rng(20260602)
    B = 1000
    STATS = ["PTS", "REB", "BLK"]  # AST not in backtest

    print("\n=== MAE delta statistics (24-25) ===")
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
                cell_results.append({
                    "cohort": cohort_name, "season": SEASON, "stat": stat,
                    "n": n, "disposition": "INCONCLUSIVE_POWER_LIMITED",
                })
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
            cell_results.append({
                "cohort": cohort_name, "season": SEASON, "stat": stat,
                "n": n, "mae_metadata": mae_meta, "mae_adjudicated": mae_adj,
                "delta": delta, "ci95_lo": ci_lo, "ci95_hi": ci_hi,
                "wilcoxon_p": float(w_p),
                "pct_improvement": 100.0 * delta / mae_meta if mae_meta > 0 else float("nan"),
            })
            print(f"  {cohort_name} {stat} n={n}: MAE meta={mae_meta:.3f}, adj={mae_adj:.3f}, "
                  f"delta={delta:+.4f} ({100.0 * delta / mae_meta:+.1f}%) "
                  f"CI95=[{ci_lo:+.4f}, {ci_hi:+.4f}] wilcoxon_p={w_p:.4f}")

    cell_df = pd.DataFrame(cell_results)
    cell_df.to_csv(RESULTS / "cohort_aggregate_mae_24-25.csv", index=False)
    print(f"\nWrote {RESULTS / 'cohort_aggregate_mae_24-25.csv'}")


if __name__ == "__main__":
    main()
