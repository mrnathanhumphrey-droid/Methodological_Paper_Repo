"""Sloan Test 2 — v6.1 LOCKED re-scoring under adjudicated position bucketing.

Per pre-reg SHA 49fd54b (`SLOAN_PRE_REG_TEST_2_MAE_DELTA_v1.0_LOCKED.md`).

Re-scoring procedure per §2.2:
- Reads v6 raw Stan output (`audit_runs/unified_ship_v6_2025_26/per_player_projections_2025-26.csv`).
- Applies offsets and variance multipliers per `apply_v6_1_locked_offsets_2025_26.py`
  conventions under both metadata and adjudicated buckets.
- Includes Stan-level aging-curve delta: for the 46 F->C flip players, the
  position-specific aging curve parameters (peak_age_pos, beta_age_pos,
  gamma_pos) shift the age-tilt at the player's age. Extracted from the
  matching backtest posterior_summary.csv (one per stat, READ-ONLY).
- Pipeline integrity check (§3.4): Cohort C (184 non-flip adjudicated
  players) must show |Delta_mu| < 1e-6 in all cells.

Outputs to D:/NBA Projections/RMD_SRC_PIPELINE/results/sloan_mae_delta/.
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
RESULTS.mkdir(parents=True, exist_ok=True)

# Inputs (all read-only)
V6_RAW_2526 = ROOT / "audit_runs/unified_ship_v6_2025_26/per_player_projections_2025-26.csv"
V61_LOCKED_2526 = ROOT / "audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv"
META_PATH = ROOT / "data/parquet/player_metadata_enriched.parquet"
ADJ_PATH = ROOT / "RMD_SRC_PIPELINE/results/position_adjudication_v12.json"

# v6.1 LOCKED parameters (per apply_v6_1_locked_offsets_2025_26.py, READ-ONLY)
PTS_CENTER_ADDITIVE = -0.587
AST_VET_MULT = 0.9278  # not position-conditional, identical under both buckets
REB_GUARD_VAR_MULT = 0.723
AST_FWD_VAR_MULT = 0.819
BLK_GUARD_VAR_MULT = 0.662

# Stan posterior_summary paths per stat (Phase 4 v4 quadratic, train through 23-24, holdout 24-25)
# These are the v6.1 LOCKED fits; their mu_position / aging-curve params are the
# canonical position-conditional parameters.
POSTERIOR_SUMMARY = {
    "REB": ROOT / "audit_runs/20260505T171359Z/skill_backtest_REB_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/posterior_summary.csv",
    "PTS": ROOT / "audit_runs/20260505T154737Z/skill_backtest_PTS_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/posterior_summary.csv",
    "BLK": ROOT / "audit_runs/20260506T140025Z/skill_backtest_BLK_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/posterior_summary.csv",
    # AST — locate next
}

# Stan position index convention per `_primary_position_class`:
# 1 = Guard, 2 = Forward, 3 = Center (inferred from mu_position[3] being highest log-rate for REB)
POS_TO_STAN_IDX = {"Guard": 1, "Forward": 2, "Center": 3}


def primary_position_class(pos: str) -> str:
    """Replicates models.skill.data_prep._primary_position_class behavior:
    first token of hyphenated position string -> G/F/C abbreviation -> full name."""
    if not isinstance(pos, str):
        return "Forward"  # default
    first = pos.split("-")[0].strip()
    return first  # e.g., "Forward", "Center", "Guard"


def load_adjudication():
    with open(ADJ_PATH, encoding="utf-8") as f:
        adj = json.load(f)
    by_id = {}
    for v in adj["verdicts"]:
        by_id[int(v["nba_api_id"])] = {
            "metadata_bucket": v["metadata_bucket_v1"],
            "adjudicated_bucket": v["adjudicated_bucket"],
        }
    return by_id


def load_position_aging(stat: str) -> dict:
    """Returns dict with mu_position, peak_age_pos, beta_age_pos, gamma_pos per
    position index (1, 2, 3). Used for Stan-level aging-curve delta."""
    summary_path = POSTERIOR_SUMMARY.get(stat)
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


def age_tilt(pos_idx: int, age: float, posterior: dict) -> float:
    """Per Stan model `age_tilt_player[p] = beta_age_pos[k] * (age - peak_age_pos[k]) +
                                              gamma_pos[k] * (age - peak_age_pos[k])^2`
    where k = position index. Returns the log-rate aging shift."""
    if posterior is None or posterior["beta_age_pos"].get(pos_idx) is None:
        return 0.0
    peak = posterior["peak_age_pos"][pos_idx]
    beta = posterior["beta_age_pos"][pos_idx]
    gamma = posterior["gamma_pos"][pos_idx]
    delta = age - peak
    return beta * delta + gamma * (delta ** 2)


def stan_aging_delta_factor(metadata_bucket: str, adjudicated_bucket: str,
                              age: float, posterior: dict) -> float:
    """Returns the multiplicative factor on the predicted rate from switching
    position from metadata to adjudicated, capturing the Stan aging-curve shift."""
    if metadata_bucket == adjudicated_bucket or posterior is None:
        return 1.0
    meta_idx = POS_TO_STAN_IDX.get(metadata_bucket)
    adj_idx = POS_TO_STAN_IDX.get(adjudicated_bucket)
    if meta_idx is None or adj_idx is None:
        return 1.0
    aging_meta = age_tilt(meta_idx, age, posterior)
    aging_adj = age_tilt(adj_idx, age, posterior)
    return float(np.exp(aging_adj - aging_meta))


def main():
    # Load inputs
    print("Loading inputs...")
    adj = load_adjudication()
    print(f"  v1.2 adjudication: {len(adj)} players")

    flip_ids = {pid for pid, b in adj.items()
                if b["metadata_bucket"] == "Forward" and b["adjudicated_bucket"] == "Center"}
    non_flip_ids = {pid for pid, b in adj.items()
                    if b["metadata_bucket"] == b["adjudicated_bucket"]}
    print(f"  Cohort A (F->C flips): {len(flip_ids)}")
    print(f"  Cohort C (non-flip): {len(non_flip_ids)}")

    meta = pd.read_parquet(META_PATH)[["nba_api_id", "name", "position", "birth_date"]]
    meta["pos_class"] = meta["position"].apply(primary_position_class)

    # Compute age at start of season (2025 for 25-26)
    meta["birth_year"] = pd.to_datetime(meta["birth_date"], errors="coerce").dt.year
    TARGET_SEASON_START_YEAR = 2025
    meta["age_2025"] = TARGET_SEASON_START_YEAR - meta["birth_year"]

    v6_raw = pd.read_csv(V6_RAW_2526)
    v6_raw["nba_api_id"] = v6_raw["nba_api_id"].astype(int)
    print(f"  v6 raw 25-26 ship: {len(v6_raw)} players")

    df = v6_raw.merge(meta[["nba_api_id", "pos_class", "age_2025"]],
                       on="nba_api_id", how="left")
    df["pos_class"] = df["pos_class"].fillna("Forward")
    df["age_2025"] = df["age_2025"].fillna(28).astype(float)

    # Map metadata pos_class -> bucket (Guard / Forward / Center) and lookup adjudication
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

    print(f"\nCohort intersections with 25-26 ship:")
    print(f"  Adjudicated: {df['is_adjudicated'].sum()}/230")
    print(f"  Flip (Cohort A): {df['is_flip'].sum()}/{len(flip_ids)}")
    print(f"  Non-flip (Cohort C): {df['is_non_flip_adj'].sum()}/{len(non_flip_ids)}")

    # Load posterior summaries per stat
    posteriors = {s: load_position_aging(s) for s in ("PTS", "REB", "BLK")}
    for s, p in posteriors.items():
        if p is None:
            print(f"  [warn] posterior summary missing for {s}; aging-curve delta will be 1.0")
        else:
            print(f"  {s} mu_position: " + ", ".join(f"[{k}]={v:.3f}" for k, v in p["mu_position"].items()))

    # Compute predictions under metadata bucket (= v6.1 LOCKED baseline)
    # and under adjudicated bucket.
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
            base = float(row[col_pg])  # v6 raw Stan output per-game
            actual = float(row[col_actual]) if not pd.isna(row[col_actual]) else None

            # mu_metadata (matches v6.1 LOCKED)
            mu_meta = base
            if stat == "PTS" and meta_b == "Center":
                mu_meta += PTS_CENTER_ADDITIVE

            # mu_adjudicated: same base, but offsets and aging-curve under adjudicated bucket.
            mu_adj = base
            if stat == "PTS" and adj_b == "Center":
                mu_adj += PTS_CENTER_ADDITIVE
            # Stan aging-curve multiplicative delta (applies to underlying rate)
            posterior = posteriors.get(stat)
            if posterior is not None and meta_b != adj_b:
                factor = stan_aging_delta_factor(meta_b, adj_b, age, posterior)
                # apply to the underlying rate (PTS additive comes AFTER aging)
                if stat == "PTS":
                    rate_meta = mu_meta - (PTS_CENTER_ADDITIVE if meta_b == "Center" else 0)
                    rate_adj = rate_meta * factor
                    mu_adj = rate_adj + (PTS_CENTER_ADDITIVE if adj_b == "Center" else 0)
                else:
                    mu_adj = base * factor

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
                "mu_metadata": mu_meta,
                "mu_adjudicated": mu_adj,
                "delta_mu": mu_adj - mu_meta,
                "actual": actual,
                "ae_metadata": abs(actual - mu_meta) if actual is not None else None,
                "ae_adjudicated": abs(actual - mu_adj) if actual is not None else None,
                "delta_ae": (abs(actual - mu_meta) - abs(actual - mu_adj)) if actual is not None else None,
            })

    proj_df = pd.DataFrame(out_rows)
    proj_df.to_parquet(RESULTS / "per_player_projections_25-26.parquet", index=False)
    print(f"\nWrote {RESULTS / 'per_player_projections_25-26.parquet'} ({len(proj_df)} rows)")

    # Pipeline integrity check (§3.4): Cohort C delta_mu should be ~0
    print("\n=== Pipeline integrity check (Cohort C non-flip should have delta_mu == 0) ===")
    cohort_c = proj_df[proj_df["is_non_flip_adj"]]
    for stat in STATS:
        s = cohort_c[cohort_c["stat"] == stat]
        max_abs_delta = s["delta_mu"].abs().max()
        n = len(s)
        passed = max_abs_delta < 1e-6
        print(f"  Cohort C {stat}: n={n}, max |delta_mu| = {max_abs_delta:.2e}, "
              f"{'PASS' if passed else 'FAIL'}")
    # Write integrity check file
    with open(RESULTS / "pipeline_integrity_check.md", "w", encoding="utf-8") as f:
        f.write("# Pipeline integrity check (Cohort C)\n\n")
        f.write("Per pre-reg §3.4: Cohort C (184 non-flip adjudicated players) "
                "must show |delta_mu| < 1e-6 for all cells.\n\n")
        f.write("| Stat | n | max |delta_mu| | Status |\n|---|---|---|---|\n")
        for stat in STATS:
            s = cohort_c[cohort_c["stat"] == stat]
            max_abs = s["delta_mu"].abs().max()
            f.write(f"| {stat} | {len(s)} | {max_abs:.2e} | {'PASS' if max_abs < 1e-6 else 'FAIL'} |\n")

    # Per-cell MAE statistics: Cohort A (Flip) and Cohort B (all 230 adjudicated)
    print("\n=== MAE delta statistics ===")
    SEASON = "25-26"
    cell_results = []
    rng = np.random.default_rng(20260602)
    B = 1000

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
            # Cluster bootstrap on player (one row per player per stat-cell, so resample rows)
            boot_deltas = np.zeros(B)
            for b in range(B):
                idx = rng.integers(0, n, size=n)
                boot_deltas[b] = ae_meta[idx].mean() - ae_adj[idx].mean()
            ci_lo, ci_hi = float(np.percentile(boot_deltas, 2.5)), float(np.percentile(boot_deltas, 97.5))
            # Paired Wilcoxon on (ae_meta - ae_adj)
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
    cell_df.to_csv(RESULTS / "cohort_aggregate_mae_25-26.csv", index=False)
    print(f"\nWrote {RESULTS / 'cohort_aggregate_mae_25-26.csv'}")

    # Named-player tables
    LABEL_PRIORITY = [
        "Anthony Davis", "Giannis Antetokounmpo", "Kevin Love", "Mason Plumlee",
        "Kristaps Porziņģis", "Kelly Olynyk", "Dwight Powell", "Taj Gibson",
    ]
    named = proj_df[proj_df["name"].isin(LABEL_PRIORITY) & proj_df["is_flip"]]
    if len(named) > 0:
        named.to_csv(RESULTS / "named_player_table_25-26.csv", index=False)
        print(f"\nNamed-player table: {len(named)} rows")
        print(named[["name", "stat", "mu_metadata", "mu_adjudicated", "actual", "ae_metadata", "ae_adjudicated", "delta_ae"]].to_string())


if __name__ == "__main__":
    main()
