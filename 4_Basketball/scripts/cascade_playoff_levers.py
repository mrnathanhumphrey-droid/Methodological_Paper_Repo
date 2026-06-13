"""Six-check cascade on two candidate playoff levers:

  Lever 1: HOME / ROAD playoff differential. Does the regime multiplier differ
           between home and road games beyond the cross-game baseline?

  Lever 2: SERIES-GAME adjustment (game_in_series 1-2 vs 3+). Does rotation
           compression / coaching adjustment shift the regime multiplier in
           later games of a series?

Test substrate: the 22-25 R1-R4 backtest residuals at
runs/run_nba_playoffs_backtest_22_25/backtest_playoff_residuals.csv.

Six checks (per residue-class methodology + feedback_loo_mse_is_the_real_gate):
  1. Per-partition implied multipliers — visualize the cell.
  2. Permutation null (B=1000): does observed partition difference exceed chance?
  3. Cross-season LOO stability: does the partition multiplier hold cross-season?
  4. Sample-size partialing: is the effect explained by uneven sample sizes?
  5. Series-dependency (Lever 2 specifically): are within-series residuals
     correlated, deflating effective N?
  6. **LOO MSE gate (load-bearing)**: does applying the partition-specific
     multiplier IMPROVE out-of-sample MAE vs the current cross-game multiplier?
     If MAE worsens (negative %), REJECT regardless of SNR/perm-p.

Output: cascade_results.md + CSVs per lever in
runs/run_nba_playoffs_backtest_22_25/cascade_levers/.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(".")
BACKTEST_DIR = REPO / "runs" / "run_nba_playoffs_backtest_22_25"
RESIDUALS_PATH = BACKTEST_DIR / "backtest_playoff_residuals.csv"
PLAYOFFS_R1 = REPO / "data" / "parquet" / "playoffs" / "round1"
PLAYOFFS_EXTRA = REPO / "data" / "parquet" / "playoffs" / "extra_rounds"
OUT_DIR = BACKTEST_DIR / "cascade_levers"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PRIMARY_STATS = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FG3M"]
N_PERM = 1000
RNG = np.random.default_rng(20260512)


def _implied_mult(df: pd.DataFrame) -> float:
    if df["proj_A"].sum() == 0:
        return np.nan
    return float(df["actual"].sum() / df["proj_A"].sum())


def _mae(df: pd.DataFrame, col: str) -> float:
    return float(np.mean(np.abs(df[col])))


def load_residuals_with_context() -> pd.DataFrame:
    """Load backtest residuals + join with manifest to get round + game_in_series."""
    res = pd.read_csv(RESIDUALS_PATH)
    res["gameId"] = res["gameId"].astype(int).astype(str).str.zfill(10)

    mans = []
    for d in [PLAYOFFS_R1, PLAYOFFS_EXTRA]:
        p = d / "_manifest.parquet"
        if p.exists():
            mans.append(pd.read_parquet(p))
    m = pd.concat(mans, ignore_index=True).drop_duplicates("game_id", keep="first")
    m["game_id"] = m["game_id"].astype(str)
    res = res.merge(
        m[["game_id", "round", "game_in_series"]],
        left_on="gameId", right_on="game_id", how="left",
    )
    return res


# ── Cascade ───────────────────────────────────────────────────────────

def cascade_partition(res: pd.DataFrame, partition_col: str, partition_label: str,
                      partition_a_label: str, partition_b_label: str) -> dict:
    """Run the 6-check cascade for a binary partition on `partition_col`.

    `partition_col` must be a boolean / 0-1 column; True/1 = partition_a.
    """
    print(f"\n{'='*70}")
    print(f"CASCADE: {partition_label}  ({partition_a_label} vs {partition_b_label})")
    print('='*70)

    res_p = res.dropna(subset=[partition_col]).copy()
    res_p[partition_col] = res_p[partition_col].astype(bool)

    out = {"lever": partition_label, "by_stat": {}}

    for stat in PRIMARY_STATS:
        sub = res_p[res_p["stat"] == stat].copy()
        if len(sub) == 0:
            continue
        a = sub[sub[partition_col]].copy()
        b = sub[~sub[partition_col]].copy()
        n_a, n_b = len(a), len(b)
        if n_a < 30 or n_b < 30:
            print(f"  {stat}: insufficient sample (a={n_a}, b={n_b}); skip")
            continue

        # Check 1: implied multipliers per partition
        mult_a = _implied_mult(a)
        mult_b = _implied_mult(b)
        mult_pooled = _implied_mult(sub)
        diff = mult_a - mult_b

        # Check 2: permutation null
        labels = np.concatenate([np.ones(n_a, dtype=bool),
                                  np.zeros(n_b, dtype=bool)])
        actuals = pd.concat([a, b])["actual"].to_numpy()
        projs = pd.concat([a, b])["proj_A"].to_numpy()
        perm_diffs = np.zeros(N_PERM)
        for i in range(N_PERM):
            shuffled = RNG.permutation(labels)
            sa = actuals[shuffled].sum()
            sp = projs[shuffled].sum()
            sa_b = actuals[~shuffled].sum()
            sp_b = projs[~shuffled].sum()
            if sp > 0 and sp_b > 0:
                perm_diffs[i] = sa / sp - sa_b / sp_b
        p_perm = float(np.mean(np.abs(perm_diffs) >= abs(diff)))

        # Check 3: cross-season LOO stability
        seasons = sorted(sub["season"].unique())
        per_season_diff = {}
        for s in seasons:
            ss = sub[sub["season"] == s]
            sa = ss[ss[partition_col]]
            sb = ss[~ss[partition_col]]
            if len(sa) > 0 and len(sb) > 0:
                ma = _implied_mult(sa)
                mb = _implied_mult(sb)
                per_season_diff[s] = ma - mb
        season_signs = [np.sign(v) for v in per_season_diff.values()]
        cross_season_consistent = (len(season_signs) > 0 and
                                    abs(sum(season_signs)) == len(season_signs))

        # Check 4: sample-size partialing — if effect persists when subsampling
        # the larger partition to match the smaller, signal is real (not n-driven)
        if n_a > n_b:
            sub_a = a.sample(n=n_b, random_state=20260512)
            mult_a_sub = _implied_mult(sub_a)
            diff_subsample = mult_a_sub - mult_b
        else:
            sub_b = b.sample(n=n_a, random_state=20260512)
            mult_b_sub = _implied_mult(sub_b)
            diff_subsample = mult_a - mult_b_sub
        partialing_sign_preserved = np.sign(diff_subsample) == np.sign(diff)

        # Check 6 (load-bearing): LOO MSE gate
        # Apply partition-specific multiplier vs cross-game multiplier; compute MAE
        # under each. Effect is positive iff partition-specific lever IMPROVES MAE.
        season_loo_results = {}
        for s in seasons:
            train = sub[sub["season"] != s]
            test = sub[sub["season"] == s]
            if len(train) == 0 or len(test) == 0:
                continue
            mult_train_pooled = _implied_mult(train)
            train_a = train[train[partition_col]]
            train_b = train[~train[partition_col]]
            mult_a_train = _implied_mult(train_a) if len(train_a) > 0 else mult_train_pooled
            mult_b_train = _implied_mult(train_b) if len(train_b) > 0 else mult_train_pooled

            # Apply each
            test = test.copy()
            test["proj_pooled"] = test["proj_A"] * mult_train_pooled
            test["proj_partitioned"] = np.where(
                test[partition_col],
                test["proj_A"] * mult_a_train,
                test["proj_A"] * mult_b_train,
            )
            mae_pooled = float(np.mean(np.abs(test["actual"] - test["proj_pooled"])))
            mae_partitioned = float(np.mean(
                np.abs(test["actual"] - test["proj_partitioned"])))
            pct_change = (mae_partitioned - mae_pooled) / mae_pooled * 100
            season_loo_results[s] = {
                "mae_pooled": mae_pooled,
                "mae_partitioned": mae_partitioned,
                "pct_change": pct_change,
            }

        avg_loo_pct = (np.mean([r["pct_change"] for r in season_loo_results.values()])
                       if season_loo_results else np.nan)

        # Disposition
        if np.isnan(avg_loo_pct):
            disposition = "INDETERMINATE"
        elif avg_loo_pct < -1.0:
            disposition = "PASS_LOO_MSE_GATE  (lever IMPROVES MAE)"
        elif avg_loo_pct > 1.0:
            disposition = "FAIL_LOO_MSE_GATE  (lever WORSENS MAE — REJECT)"
        else:
            disposition = "NO_EFFECT  (within noise of cross-game baseline)"

        print(f"  {stat}:")
        print(f"    n_a={n_a:>5}  n_b={n_b:>5}  mult_a={mult_a:.4f}  mult_b={mult_b:.4f}"
              f"  diff={diff:+.4f}  p_perm={p_perm:.3f}")
        print(f"    cross-season consistent: {cross_season_consistent}  "
              f"({', '.join(f'{s}:{v:+.3f}' for s, v in per_season_diff.items())})")
        print(f"    subsample diff: {diff_subsample:+.4f}  "
              f"sign-preserved: {partialing_sign_preserved}")
        print(f"    LOO MSE: avg {avg_loo_pct:+.2f}% across seasons  ->  {disposition}")

        out["by_stat"][stat] = {
            "n_a": n_a, "n_b": n_b,
            "mult_a": mult_a, "mult_b": mult_b, "mult_pooled": mult_pooled,
            "diff": diff, "p_perm": p_perm,
            "cross_season_consistent": cross_season_consistent,
            "per_season_diff": per_season_diff,
            "subsample_diff": diff_subsample,
            "subsample_sign_preserved": partialing_sign_preserved,
            "loo_per_season": season_loo_results,
            "loo_avg_pct_change": avg_loo_pct,
            "disposition": disposition,
        }

    return out


def main():
    print(f"Loading residuals from {RESIDUALS_PATH} ...")
    res = load_residuals_with_context()
    print(f"  loaded {len(res):,} rows  (rounds: {sorted(res['round'].dropna().unique().tolist())})")

    # ── Lever 1: Home / Road ───────────────────────────────────────────
    res_hr = res.copy()
    res_hr["is_home"] = res_hr["is_home"].astype(bool)
    home_road = cascade_partition(
        res_hr, "is_home", "HOME vs ROAD",
        partition_a_label="HOME", partition_b_label="ROAD",
    )

    # ── Lever 2: Series-game 1-2 vs 3+ ─────────────────────────────────
    res_sg = res.dropna(subset=["game_in_series"]).copy()
    res_sg["early_series"] = res_sg["game_in_series"] <= 2
    series_game = cascade_partition(
        res_sg, "early_series", "EARLY-SERIES (games 1-2) vs LATER (3+)",
        partition_a_label="EARLY (1-2)", partition_b_label="LATER (3+)",
    )

    # ── Write CSV + JSON outputs ───────────────────────────────────────
    rows = []
    for lever_name, lever in [("home_road", home_road),
                                ("series_game_early_vs_late", series_game)]:
        for stat, d in lever["by_stat"].items():
            rows.append({
                "lever": lever_name,
                "stat": stat,
                "n_a": d["n_a"], "n_b": d["n_b"],
                "mult_a": d["mult_a"], "mult_b": d["mult_b"],
                "mult_pooled": d["mult_pooled"],
                "diff": d["diff"], "p_perm": d["p_perm"],
                "cross_season_consistent": d["cross_season_consistent"],
                "subsample_diff": d["subsample_diff"],
                "subsample_sign_preserved": d["subsample_sign_preserved"],
                "loo_avg_pct_change": d["loo_avg_pct_change"],
                "disposition": d["disposition"],
            })
    df_out = pd.DataFrame(rows)
    csv_path = OUT_DIR / "cascade_results.csv"
    df_out.to_csv(csv_path, index=False)
    print(f"\nWrote {csv_path}")

    json_path = OUT_DIR / "cascade_results.json"
    with open(json_path, "w") as f:
        json.dump({"home_road": home_road, "series_game": series_game},
                  f, indent=2, default=str)
    print(f"Wrote {json_path}")

    # ── Headline summary ───────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("HEADLINE DISPOSITIONS")
    print('='*70)
    for lever_name, lever in [("HOME vs ROAD", home_road),
                                ("EARLY-SERIES vs LATER", series_game)]:
        passes = sum(1 for d in lever["by_stat"].values()
                     if "PASS_LOO_MSE_GATE" in d["disposition"])
        fails = sum(1 for d in lever["by_stat"].values()
                    if "FAIL" in d["disposition"])
        no_eff = sum(1 for d in lever["by_stat"].values()
                     if "NO_EFFECT" in d["disposition"])
        n_total = len(lever["by_stat"])
        print(f"  {lever_name}: {passes}/{n_total} pass, {fails}/{n_total} fail, "
              f"{no_eff}/{n_total} no-effect")
    print()


if __name__ == "__main__":
    main()
