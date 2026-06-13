"""LOO MSE deployment gate for cross-season-validated offsets.

For each (stat, class, value) in data/parquet/cross_season_validated_offsets.parquet:
  For each season s in the lever's available pool:
    Train: derive the class-mean residual from the OTHER seasons
    Test:  apply that learned offset to s's audit per_player_projections
    Score: MAE_baseline (no offset) vs MAE_post (with offset) on s

Aggregate: mean MAE delta across LOO folds.
Verdict per memory feedback_loo_mse_is_the_real_gate.md:
  - delta < -1.0%  → DEPLOY (real improvement)
  - delta within ±1% → HOLD (no signal beyond noise)
  - delta > +1.0%  → REJECT (lever hurts)

Outputs:
  data/parquet/loo_mse_offset_verdicts_2526.parquet
  stdout summary table
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")

from pathlib import Path
import re
import numpy as np
import pandas as pd

from _class_features import attach_class_features

REPO = Path(".")
PQ = REPO / "data" / "parquet"
OUT_PATH = PQ / "loo_mse_offset_verdicts_2526.parquet"


def find_audits_for_stat(stat: str) -> dict[str, Path]:
    """Return {test_season: per_player_projections.csv path}.

    Tiebreak: largest file (canonical fits over smoke runs).
    """
    pattern = re.compile(
        rf"skill_backtest_{stat}_phase4_v4_quadratic_tq_g_.*__(\d{{4}}-\d{{2}})$"
    )
    found: dict[str, tuple[Path, int]] = {}
    for d in (REPO / "audit_runs").glob("*"):
        if not d.is_dir():
            continue
        for sub in d.glob(f"skill_backtest_{stat}_phase4_v4_quadratic_tq_g_*"):
            m = pattern.search(sub.name)
            if m:
                ts = m.group(1)
                csv = sub / "per_player_projections.csv"
                if csv.exists():
                    sz = csv.stat().st_size
                    if ts not in found or sz > found[ts][1]:
                        found[ts] = (csv, sz)
    return {ts: csv for ts, (csv, _) in found.items()}


def load_audit_with_features(stat: str, season: str, csv: Path) -> pd.DataFrame:
    """Load one season's audit, attach class features keyed to that season's start year."""
    df = pd.read_csv(csv)
    df = df.dropna(subset=["actual", "proj_mean"]).copy()
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    df["residual"] = df["actual"] - df["proj_mean"]
    target_year = int(season.split("-")[0])
    return attach_class_features(df, target_year)


def compute_class_mean_offset(audits: dict[str, pd.DataFrame],
                              class_col: str,
                              class_val: str,
                              train_seasons: list[str]) -> float:
    """Compute class-mean residual across the union of train seasons."""
    pieces = []
    for s in train_seasons:
        d = audits[s]
        sub = d[d[class_col].astype(str) == str(class_val)]
        if len(sub):
            pieces.append(sub["residual"])
    if not pieces:
        return 0.0
    all_resid = pd.concat(pieces)
    return float(all_resid.mean())


def loo_mae_delta(stat: str,
                  class_col: str,
                  class_val: str,
                  audits: dict[str, pd.DataFrame]) -> dict:
    """For each season s in audits, derive offset from the other seasons,
    apply to s, compute MAE before/after. Return summary."""
    seasons = sorted(audits.keys())
    fold_records = []
    for s in seasons:
        train = [t for t in seasons if t != s]
        if not train:
            continue
        offset = compute_class_mean_offset(audits, class_col, class_val, train)
        test = audits[s].copy()
        mask = test[class_col].astype(str) == str(class_val)
        # Baseline: actual - proj_mean
        # Post-offset: actual - (proj_mean + offset)  i.e., new_resid = resid - offset on the class
        baseline_resid = test["residual"].values.copy()
        post_resid = baseline_resid.copy()
        post_resid[mask.values] -= offset
        mae_base = float(np.mean(np.abs(baseline_resid)))
        mae_post = float(np.mean(np.abs(post_resid)))
        n_class = int(mask.sum())
        n_total = len(test)
        fold_records.append({
            "season": s,
            "train_seasons": "|".join(train),
            "n_total": n_total,
            "n_class": n_class,
            "offset_learned": offset,
            "mae_baseline": mae_base,
            "mae_post": mae_post,
            "mae_delta": mae_post - mae_base,
            "mae_delta_pct": (mae_post - mae_base) / mae_base * 100.0,
        })
    if not fold_records:
        return {"folds": [], "verdict": "NO_FOLDS"}
    fold_df = pd.DataFrame(fold_records)
    mean_delta_pct = float(fold_df["mae_delta_pct"].mean())
    mean_abs_delta = float(fold_df["mae_delta"].mean())
    if mean_delta_pct < -1.0:
        verdict = "DEPLOY"
    elif mean_delta_pct > 1.0:
        verdict = "REJECT"
    else:
        verdict = "HOLD"
    return {
        "folds": fold_records,
        "mean_delta": mean_abs_delta,
        "mean_delta_pct": mean_delta_pct,
        "n_folds": len(fold_records),
        "verdict": verdict,
    }


def main():
    print("=" * 90)
    print("LOO MSE deployment gate — cross-season-validated offsets including 25-26")
    print("=" * 90)

    offsets = pd.read_parquet(PQ / "cross_season_validated_offsets.parquet")
    print(f"\nValidated offset candidates: {len(offsets)}")
    print(offsets[["stat", "class", "class_value", "n_seasons", "cross_season_mean"]].to_string(index=False))
    print()

    # Cache audits per stat
    print("Loading audits + attaching class features...")
    audit_cache: dict[str, dict[str, pd.DataFrame]] = {}
    for stat in offsets["stat"].unique():
        paths = find_audits_for_stat(stat)
        per_season = {}
        for s, p in paths.items():
            try:
                per_season[s] = load_audit_with_features(stat, s, p)
            except Exception as e:
                print(f"  {stat}/{s}: skip ({type(e).__name__}: {e})")
        audit_cache[stat] = per_season
        print(f"  {stat}: {sorted(per_season.keys())}")

    results = []
    print()
    print("=" * 90)
    print("LOO MSE per candidate lever")
    print("=" * 90)
    hdr = f"{'stat':<5} {'class':<22} {'value':<14} {'n_fold':>6} {'mean_delta':>12} {'pct':>8} {'verdict':<8}"
    print(hdr)
    print("-" * 90)
    for _, row in offsets.iterrows():
        stat = row["stat"]
        cls = row["class"]
        val = row["class_value"]
        a = audit_cache.get(stat, {})
        out = loo_mae_delta(stat, cls, val, a)
        v = out.get("verdict", "NO_FOLDS")
        if v == "NO_FOLDS":
            print(f"  {stat:<5} {cls:<22} {str(val):<14} {0:>6} {'NA':>12} {'NA':>8} {v:<8}")
            results.append({
                "stat": stat, "class": cls, "class_value": val,
                "n_folds": 0, "mean_delta": float("nan"),
                "mean_delta_pct": float("nan"), "verdict": v,
                "validated_offset": row["cross_season_mean"],
            })
            continue
        print(f"  {stat:<5} {cls:<22} {str(val):<14} {out['n_folds']:>6} "
              f"{out['mean_delta']:>+12.5f} {out['mean_delta_pct']:>+7.2f}% {v:<8}")
        results.append({
            "stat": stat, "class": cls, "class_value": val,
            "n_folds": out["n_folds"],
            "mean_delta": out["mean_delta"],
            "mean_delta_pct": out["mean_delta_pct"],
            "verdict": v,
            "validated_offset": row["cross_season_mean"],
        })

    print()
    out_df = pd.DataFrame(results)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(OUT_PATH, index=False)
    print(f"Saved verdict table -> {OUT_PATH}")

    print()
    print("=" * 90)
    print("SUMMARY")
    print("=" * 90)
    counts = out_df["verdict"].value_counts().to_dict()
    print(f"  DEPLOY:    {counts.get('DEPLOY', 0)}")
    print(f"  HOLD:      {counts.get('HOLD', 0)}")
    print(f"  REJECT:    {counts.get('REJECT', 0)}")
    print(f"  NO_FOLDS:  {counts.get('NO_FOLDS', 0)}")

    deploy = out_df[out_df["verdict"] == "DEPLOY"].sort_values("mean_delta_pct")
    if len(deploy):
        print()
        print("DEPLOY candidates (most improvement first):")
        print(deploy[["stat", "class", "class_value", "mean_delta_pct", "validated_offset"]].to_string(index=False))


if __name__ == "__main__":
    main()
