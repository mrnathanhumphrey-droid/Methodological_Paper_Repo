"""Hierarchical multi-year offset model runner (Desktop #6).

Gathers all v4-lite tq_g audits across (stat, season), prepares Stan data,
fits the hierarchical_multi_year_offsets.stan model, extracts cross-year-stable
class offsets with shrinkage.

Stan model details: see hierarchical_multi_year_offsets.stan.

Output: data/parquet/hierarchical_validated_offsets.parquet
        with shrunk offsets for each (stat, class, class_value).

Each entry includes:
  - mu_class (posterior mean of grand-mean offset)
  - tau_class (cross-year SD)
  - sigma_class (residual SD)
  - stability_fraction (1 = stable across years, 0 = year-specific noise)
  - shrunk_offset = mu_class * stability_fraction (this is what to ship)

Usage:
  # First do a dry-run to see what data is available:
  python scripts/hierarchical_multi_year_runner.py --dry-run

  # Then fit (CPU-heavy; ~30-90 min depending on N):
  python scripts/hierarchical_multi_year_runner.py --fit

Expected: needs >= 3 seasons of audits per stat for meaningful shrinkage.
With current 2 seasons (22-23 + 23-24 PTS), the prior dominates.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")

import argparse
from pathlib import Path
import re
import json
import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
STAN_FILE = REPO / "scripts" / "hierarchical_multi_year_offsets.stan"

STATS = ["PTS", "REB", "AST", "STL", "BLK", "TOV"]
CLASSES = ["position", "age_bucket", "years_pro_bucket", "draft_pick_tier",
            "offseason_traded", "new_coach_this_season", "mid_season_change"]


def find_audits(stat: str) -> dict:
    """Tiebreak: prefer audit with largest per_player_projections.csv size
    (avoids picking smoke-test runs over canonical fits)."""
    pattern = re.compile(
        rf"skill_backtest_{stat}_phase4_v4_quadratic_tq_g_.*__(\d{{4}}-\d{{2}})$"
    )
    found = {}  # ts -> (csv, size)
    for d in (REPO / "audit_runs").glob("*"):
        if not d.is_dir():
            continue
        for sub in d.glob(f"skill_backtest_{stat}_phase4_v4_quadratic_tq_g_*"):
            m = pattern.search(sub.name)
            if m:
                ts = m.group(1)
                csv = sub / "per_player_projections.csv"
                if csv.exists():
                    size = csv.stat().st_size
                    if ts not in found or size > found[ts][1]:
                        found[ts] = (csv, size)
    return {ts: csv for ts, (csv, _) in found.items()}


from _class_features import attach_class_features


def gather_data():
    """For each stat, collect (residual, class_idx, year_idx) tuples across all
    available season audits, fold all class types into a single class_idx
    space."""
    rows = []
    class_id_map = {}  # (stat, class_name, class_value) -> int
    next_class_id = 1

    for stat in STATS:
        audits = find_audits(stat)
        for season, audit_path in audits.items():
            target_year = int(season.split("-")[0])
            df = pd.read_csv(audit_path)
            df["nba_api_id"] = df["nba_api_id"].astype(int)
            df = df.dropna(subset=["actual", "proj_mean"]).copy()
            df["residual"] = df["actual"] - df["proj_mean"]
            df = attach_class_features(df, target_year)

            for cls in CLASSES:
                if cls not in df.columns:
                    continue
                for _, r in df.iterrows():
                    val = r[cls]
                    if val is None or (isinstance(val, float) and np.isnan(val)):
                        continue
                    key = (stat, cls, str(val))
                    if key not in class_id_map:
                        class_id_map[key] = next_class_id
                        next_class_id += 1
                    rows.append({
                        "stat": stat,
                        "class_name": cls,
                        "class_value": str(val),
                        "season": season,
                        "year_idx_raw": target_year,
                        "class_idx": class_id_map[key],
                        "residual": float(r["residual"]),
                        "nba_api_id": int(r["nba_api_id"]),
                    })
    df = pd.DataFrame(rows)
    if len(df) == 0:
        return df, class_id_map

    # Year index: 1-based contiguous
    years_sorted = sorted(df["year_idx_raw"].unique())
    year_map = {y: i + 1 for i, y in enumerate(years_sorted)}
    df["year_idx"] = df["year_idx_raw"].map(year_map)
    return df, class_id_map


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true",
                    help="Don't fit, just gather and report")
    p.add_argument("--fit", action="store_true", help="Run Stan fit")
    args = p.parse_args()

    print("Gathering data from all available audits...")
    df, class_id_map = gather_data()
    if len(df) == 0:
        print("  No audit data found.")
        return

    n_obs = len(df)
    n_classes = df["class_idx"].nunique()
    n_years = df["year_idx"].nunique()
    print(f"\n  Observations: {n_obs}")
    print(f"  Distinct (stat, class, value) combos: {n_classes}")
    print(f"  Years: {n_years}  ({sorted(df['year_idx_raw'].unique())})")
    print(f"  Stats covered: {sorted(df['stat'].unique())}")
    print()
    by_stat_year = df.groupby(["stat", "year_idx_raw"]).size().unstack(fill_value=0)
    print("Observations per (stat, year):")
    print(by_stat_year.to_string())

    if args.dry_run:
        return

    if not args.fit:
        print("\nUse --fit to actually run Stan (CPU-heavy). --dry-run to inspect data only.")
        return

    if n_years < 2:
        print("\nWARNING: only 1 year of data — hierarchical model has no shrinkage signal.")
        print("Need 2+ seasons of audits per stat. Re-run after multi-year campaign.")
        return

    # Run Stan fit
    print("\nRunning Stan fit...")
    try:
        import cmdstanpy
        from cmdstanpy import CmdStanModel
    except ImportError:
        print("cmdstanpy not installed. Install with: pip install cmdstanpy")
        return

    # Auto-detect cmdstan installation (mirrors models/skill/fit.py setup;
    # Windows env-var inheritance through bash subshells is unreliable).
    try:
        cmdstanpy.cmdstan_path()
    except (ValueError, FileNotFoundError):
        from pathlib import Path as _Path
        candidates = []
        try:
            candidates.append(_Path.home() / ".cmdstan")
        except (RuntimeError, OSError):
            pass
        candidates.append(_Path("C:/Users/Nate/.cmdstan"))
        for cdir in candidates:
            if not cdir.exists():
                continue
            for sub in sorted(cdir.iterdir(), reverse=True):
                if sub.is_dir() and sub.name.startswith("cmdstan-"):
                    cmdstanpy.set_cmdstan_path(str(sub).replace("\\", "/"))
                    print(f"  Auto-detected cmdstan at {sub}")
                    break
            else:
                continue
            break

    # Activate C++ toolchain (RTools40 on Windows). No-op when already on PATH.
    try:
        from cmdstanpy.utils import cxx_toolchain_path
        cxx_toolchain_path()
    except Exception as e:
        print(f"  cxx_toolchain_path activation skipped: {e}")

    model = CmdStanModel(stan_file=str(STAN_FILE))
    stan_data = {
        "N": n_obs,
        "n_classes": n_classes,
        "n_years": n_years,
        "class_idx": df["class_idx"].astype(int).tolist(),
        "year_idx": df["year_idx"].astype(int).tolist(),
        "residual": df["residual"].astype(float).tolist(),
    }

    fit = model.sample(data=stan_data, chains=2, parallel_chains=2,
                        iter_warmup=400, iter_sampling=400,
                        seed=42, adapt_delta=0.95, max_treedepth=12)
    print(f"Stan fit complete. Diagnostics:")
    print(fit.diagnose())

    summary = fit.summary()
    # Extract per-class posterior summaries
    inv_class_map = {v: k for k, v in class_id_map.items()}
    rows = []
    for cls_id in range(1, n_classes + 1):
        stat, cls_name, cls_val = inv_class_map[cls_id]
        mu_post = summary.loc[f"mu_class[{cls_id}]"]
        tau_post = summary.loc[f"tau_class[{cls_id}]"]
        sigma_post = summary.loc[f"sigma_class[{cls_id}]"]
        stab_post = summary.loc[f"stability_fraction[{cls_id}]"]
        rows.append({
            "stat": stat, "class": cls_name, "class_value": cls_val,
            "mu_mean": mu_post["Mean"],
            "mu_sd": mu_post["StdDev"],
            "mu_q05": mu_post["5%"], "mu_q95": mu_post["95%"],
            "tau_mean": tau_post["Mean"],
            "sigma_mean": sigma_post["Mean"],
            "stability_fraction": stab_post["Mean"],
            "shrunk_offset": mu_post["Mean"] * stab_post["Mean"],
        })

    out = pd.DataFrame(rows)
    out = out.sort_values(["stat", "stability_fraction"], ascending=[True, False])
    out.to_parquet(PQ / "hierarchical_validated_offsets.parquet", index=False)
    print(f"\nSaved -> {PQ / 'hierarchical_validated_offsets.parquet'}")
    print(f"\nTop-stability offsets per stat (these would ship):")
    for stat in sorted(out["stat"].unique()):
        ssub = out[out["stat"] == stat]
        ssub = ssub[(ssub["stability_fraction"] > 0.7) &
                     (ssub["mu_mean"].abs() > 0.1)]
        if len(ssub) > 0:
            print(f"\n  {stat}:")
            print(ssub[["class", "class_value", "mu_mean", "stability_fraction",
                          "shrunk_offset"]].to_string(index=False))


if __name__ == "__main__":
    main()
