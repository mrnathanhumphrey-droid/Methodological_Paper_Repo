"""CF coupling test sweep across all 13+ career-stage cells.

Extends cf_coupling_test_13plus_ast.py to PTS, REB, AST, BLK × 13+.

If all four cells are process-only (no higher-mode coupling), the c_final
hypothesis (career stage as structural identifier) is decisively falsified.
If even one cell shows higher-mode coupling, the asymmetry conclusion is
weakened and the framework needs additional articulation.

Output:
  - Per-cell moment table with bootstrap p-values
  - Per-cell CF analysis on t ∈ [-5, 5] step 0.05
  - Plot per cell saved to audit_runs/cf_coupling_13plus_sweep/
  - Consolidated verdict
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
import json
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
OUT_DIR = REPO / "audit_runs" / "cf_coupling_13plus_sweep"
OUT_DIR.mkdir(parents=True, exist_ok=True)

N_BOOTSTRAP = 100
T_GRID = np.arange(-5.0, 5.0 + 1e-9, 0.05)
RNG_SEED = 20260505


def load_residuals_for_stat(stat: str):
    """Returns (S_13plus, S_under13) residual arrays for a given stat."""
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx = bx[(bx["season"] == "2025-26") & (bx["season_type"] == "Regular Season")].copy()
    bx["minutes"] = pd.to_numeric(bx["minutes"], errors="coerce")
    bx = bx.dropna(subset=["minutes"])
    bx = bx[bx["minutes"] > 0]
    actuals = bx.groupby("nba_api_id").agg(**{f"{stat}_a": (stat, "mean")}).reset_index()
    actuals["nba_api_id"] = actuals["nba_api_id"].astype(int)

    ship = pd.read_csv("audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv")
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    ship = ship.drop(columns=[c for c in ship.columns if c.endswith("_actual")])

    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    mc = ["nba_api_id", "draft_year", "debut_year"]
    sup = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "rookie_metadata_supplement.parquet"
    if sup.exists():
        sp = pd.read_parquet(sup)
        meta = pd.concat([meta[mc], sp[mc]], ignore_index=True)
    ship = ship.merge(meta[mc], on="nba_api_id", how="left")
    ship["years_pro"] = ship["debut_year"].where(ship["debut_year"].notna(), ship["draft_year"] + 1)
    ship["years_pro"] = 2025 - ship["years_pro"]
    ship["ypb"] = pd.cut(ship["years_pro"], bins=[-1, 0, 3, 7, 12, 30],
                         labels=["rookie", "1-3", "4-7", "8-12", "13+"]).astype(str)

    real = ship[ship["nba_api_id"] < 9990000].merge(actuals, on="nba_api_id", how="inner")
    pg_col = f"{stat}_per_game"
    real[f"{stat}_resid"] = real[f"{stat}_a"] - real[pg_col]
    s13 = real.loc[real["ypb"] == "13+", f"{stat}_resid"].dropna().values
    sun = real.loc[real["ypb"] != "13+", f"{stat}_resid"].dropna().values
    return s13, sun


def empirical_cf(arr, t_grid):
    arr = arr.astype(float)
    out = np.zeros(len(t_grid), dtype=np.complex128)
    for k, t in enumerate(t_grid):
        out[k] = np.exp(1j * t * arr).mean()
    return out


def central_moments(arr, k=6):
    arr = arr.astype(float)
    m = arr.mean()
    out = [float(m)]
    for j in range(2, k + 1):
        out.append(float(((arr - m) ** j).mean()))
    return np.array(out)


def run_cell(stat: str, rng):
    s13, sun = load_residuals_for_stat(stat)
    n13 = len(s13)
    nun = len(sun)
    cm13 = central_moments(s13, k=6)
    cm_un = central_moments(sun, k=6)

    boot_cms = np.zeros((N_BOOTSTRAP, 6))
    boot_cf_diffs = np.zeros((N_BOOTSTRAP, len(T_GRID)))
    phi_un = empirical_cf(sun, T_GRID)
    phi_13 = empirical_cf(s13, T_GRID)
    obs_cf_diff = np.abs(phi_13 - phi_un)
    for i in range(N_BOOTSTRAP):
        sample = rng.choice(sun, size=n13, replace=False)
        boot_cms[i] = central_moments(sample, k=6)
        boot_cf_diffs[i] = np.abs(empirical_cf(sample, T_GRID) - phi_un)
    obs_diff_moments = np.abs(cm13 - cm_un)
    boot_diff_moments = np.abs(boot_cms - cm_un[None, :])
    p_moments = (boot_diff_moments >= obs_diff_moments[None, :]).mean(axis=0)
    p_cf = (boot_cf_diffs >= obs_cf_diff[None, :]).mean(axis=0)

    sig_higher_moments = int(((p_moments[2:6] < 0.05)).sum())
    sig_cf_higher_modes = int(((p_cf < 0.05) & ((T_GRID < -1) | (T_GRID > 1))).sum())
    sig_cf_total = ((T_GRID < -1) | (T_GRID > 1)).sum()
    cf_higher_frac = sig_cf_higher_modes / sig_cf_total if sig_cf_total else 0
    peak_idx = int(np.argmax(obs_cf_diff))
    peak_t = float(T_GRID[peak_idx])
    peak_diff = float(obs_cf_diff[peak_idx])
    peak_p = float(p_cf[peak_idx])

    if sig_higher_moments >= 2 and cf_higher_frac > 0.20:
        verdict = "STRUCTURAL_COUPLING_HIGHER_MODES"
    elif sig_higher_moments == 0 and cf_higher_frac < 0.10:
        verdict = "PROCESS_ONLY"
    else:
        verdict = "MIXED"

    # Plot
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        boot_p95 = np.quantile(boot_cf_diffs, 0.95, axis=0)
        boot_p99 = np.quantile(boot_cf_diffs, 0.99, axis=0)
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(T_GRID, obs_cf_diff, "b-", lw=2,
                label=f"|Δφ(t)| (13+ vs <13, n_13+={n13})")
        ax.fill_between(T_GRID, 0, boot_p95, color="gray", alpha=0.3, label="bootstrap 95%")
        ax.fill_between(T_GRID, 0, boot_p99, color="gray", alpha=0.15, label="bootstrap 99%")
        ax.axvspan(-1, 1, alpha=0.1, color="green", label="moment-2 region")
        ax.set_title(f"CF coupling test: {stat} × 13+   (verdict: {verdict})")
        ax.set_xlabel("t (Fourier mode)")
        ax.set_ylabel("|φ_13+(t) − φ_<13(t)|")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(OUT_DIR / f"cf_diff_{stat}.png", dpi=120)
        plt.close()
    except Exception as e:
        print(f"  Plot failed for {stat}: {e}")

    return {
        "stat": stat, "n_13plus": int(n13), "n_under13": int(nun),
        "cm_13plus": cm13.tolist(), "cm_under13": cm_un.tolist(),
        "p_moments": p_moments.tolist(),
        "sig_higher_moments_count": sig_higher_moments,
        "cf_higher_mode_frac_sig": float(cf_higher_frac),
        "peak_t": peak_t, "peak_diff": peak_diff, "peak_p": peak_p,
        "verdict": verdict,
    }


def main():
    rng = np.random.default_rng(RNG_SEED)
    results = {}
    for stat in ["PTS", "REB", "AST", "BLK"]:
        print(f"=== {stat} × 13+ ===")
        r = run_cell(stat, rng)
        results[stat] = r
        print(f'  n_13+={r["n_13plus"]}, n_<13={r["n_under13"]}')
        print(f'  M1={r["cm_13plus"][0]:+.4f} vs <13: {r["cm_under13"][0]:+.4f}  (M1 p={r["p_moments"][0]:.3f})')
        print(f'  M2={r["cm_13plus"][1]:+.4f} vs <13: {r["cm_under13"][1]:+.4f}  (M2 p={r["p_moments"][1]:.3f})')
        print(f'  M3={r["cm_13plus"][2]:+.4f} vs <13: {r["cm_under13"][2]:+.4f}  (M3 p={r["p_moments"][2]:.3f})')
        print(f'  M4={r["cm_13plus"][3]:+.4f} vs <13: {r["cm_under13"][3]:+.4f}  (M4 p={r["p_moments"][3]:.3f})')
        print(f'  Higher-moment signif (M3-M6): {r["sig_higher_moments_count"]}/4 at p<0.05')
        print(f'  CF higher-mode frac signif (|t|>1): {r["cf_higher_mode_frac_sig"]:.1%}')
        print(f'  Peak |Δφ| at t={r["peak_t"]:+.2f} (p={r["peak_p"]:.3f})')
        print(f'  → VERDICT: {r["verdict"]}')
        print()

    print("=" * 76)
    print("SWEEP SUMMARY — 13+ career-stage cells")
    print("=" * 76)
    print(f'{"stat":<6} {"n":>4} {"M3 p":>7} {"M4 p":>7} {"CF >|t|=1 frac":>14} {"verdict":>32}')
    print("-" * 76)
    for stat in ["PTS", "REB", "AST", "BLK"]:
        r = results[stat]
        print(f'{stat:<6} {r["n_13plus"]:>4} {r["p_moments"][2]:>7.3f} {r["p_moments"][3]:>7.3f} '
              f'{r["cf_higher_mode_frac_sig"]:>14.1%} {r["verdict"]:>32}')

    n_process_only = sum(1 for r in results.values() if r["verdict"] == "PROCESS_ONLY")
    n_coupled = sum(1 for r in results.values() if r["verdict"] == "STRUCTURAL_COUPLING_HIGHER_MODES")
    n_mixed = sum(1 for r in results.values() if r["verdict"] == "MIXED")
    print()
    print(f"  process-only: {n_process_only}/4")
    print(f"  coupled:      {n_coupled}/4")
    print(f"  mixed:        {n_mixed}/4")
    print()
    if n_process_only == 4:
        print("CONSOLIDATED VERDICT: c_final HYPOTHESIS FALSIFIED across all 4 career-stage cells.")
        print("                     Career stage is genuinely process-only at multiple stats.")
        print("                     Test 1's binary structural-vs-process distinction holds.")
        print("                     No Rule 7 added to protocol.")
    elif n_coupled >= 1:
        print("CONSOLIDATED VERDICT: c_final hypothesis PARTIALLY supported.")
        print("                     At least one career-stage cell shows higher-mode coupling.")
        print("                     The asymmetry vs position is more nuanced than Test 1 suggested.")
    else:
        print("CONSOLIDATED VERDICT: MIXED. Some cells process-only, some at the edge.")

    with open(OUT_DIR / "summary.json", "w") as f:
        json.dump({"sweep_results": results,
                   "n_process_only": n_process_only,
                   "n_coupled": n_coupled,
                   "n_mixed": n_mixed,
                   "n_bootstrap": N_BOOTSTRAP, "rng_seed": RNG_SEED}, f, indent=2)
    print(f'\nSaved: {OUT_DIR}/summary.json')


if __name__ == "__main__":
    main()
