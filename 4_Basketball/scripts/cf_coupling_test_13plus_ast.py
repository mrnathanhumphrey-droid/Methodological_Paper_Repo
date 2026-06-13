"""Characteristic-function coupling test on the 13+ AST class.

Test 1 (moment-2 coupling) found PTS×Center/REB×Center/BLK×Center coupled
but AST×13+ flat (variance ratio 1.05, p=0.64). Hypothesis: AST×13+ may
couple at higher Fourier modes (skewness, kurtosis, tails) that moment-2
truncation hides.

Method:
  S_13plus  = AST residuals from 13+ years_pro players (n≈33)
  S_under13 = AST residuals from <13 (n≈403 in matched 25-26 cohort)
  Bootstrap: 100 random n=33 samples from S_under13 → noise band

Compute:
  - Moments 1-6 for each set (with bootstrap p-values for moments 3-6)
  - Empirical characteristic function phi_S(t) on t ∈ [-5, 5] step 0.05
  - |phi_13plus(t) - phi_under13(t)| compared to bootstrap matched-N noise
  - Plot saved to audit_runs/cf_coupling_13plus_ast/cf_diff.png

Decision:
  - Higher modes differ AND moments 3+ differ at p<0.05 → structural
    coupling at higher modes (Test 1 missed it via moment-2 truncation)
  - All within noise → 13+ is genuinely process-only class
  - Mixed → partial coupling, identify dominant mode

If structural coupling holds, this becomes Rule 7 of the protocol:
"Test coupling at the characteristic-function level, not just moment level."
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
import os
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats as sstats

from models.skill.data_prep import _primary_position_class

REPO = Path(".")
PQ = REPO / "data" / "parquet"
OUT_DIR = REPO / "audit_runs" / "cf_coupling_13plus_ast"
OUT_DIR.mkdir(parents=True, exist_ok=True)

N_BOOTSTRAP = 100
T_GRID = np.arange(-5.0, 5.0 + 1e-9, 0.05)


def load_ast_residuals():
    """Returns (residual_13plus, residual_under13) AST residual arrays
    from v6.1 ship vs 25-26 actuals."""
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx = bx[(bx["season"] == "2025-26") & (bx["season_type"] == "Regular Season")].copy()
    bx["minutes"] = pd.to_numeric(bx["minutes"], errors="coerce")
    bx = bx.dropna(subset=["minutes"])
    bx = bx[bx["minutes"] > 0]
    actuals = bx.groupby("nba_api_id").agg(AST_a=("AST", "mean")).reset_index()
    actuals["nba_api_id"] = actuals["nba_api_id"].astype(int)

    # Use v6.1 (NOT v6.2 deshrunk) for clean comparison with Test 1
    ship = pd.read_csv("audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv")
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    ship = ship.drop(columns=[c for c in ship.columns if c.endswith("_actual")])
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    mc = ["nba_api_id", "draft_year", "debut_year", "position"]
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
    real["AST_resid"] = real["AST_a"] - real["AST_per_game"]

    s_13plus = real.loc[real["ypb"] == "13+", "AST_resid"].dropna().values
    s_under13 = real.loc[real["ypb"] != "13+", "AST_resid"].dropna().values
    return s_13plus, s_under13


def empirical_cf(arr, t_grid):
    """phi_S(t) = (1/|S|) sum_r exp(i*t*r). Returns complex array."""
    arr = arr.astype(float)
    out = np.zeros(len(t_grid), dtype=np.complex128)
    for k, t in enumerate(t_grid):
        out[k] = np.exp(1j * t * arr).mean()
    return out


def moments(arr, k=6):
    """Returns first k moments E[X^j] for j=1..k."""
    arr = arr.astype(float)
    return np.array([float((arr ** j).mean()) for j in range(1, k + 1)])


def central_moments(arr, k=6):
    """Returns mean, plus central moments of order 2..k.
    Output: [E[X], E[(X-mean)^2], ..., E[(X-mean)^k]]"""
    arr = arr.astype(float)
    m = arr.mean()
    out = [float(m)]
    for j in range(2, k + 1):
        out.append(float(((arr - m) ** j).mean()))
    return np.array(out)


def main():
    s13, sun = load_ast_residuals()
    n13 = len(s13)
    nun = len(sun)
    print(f"n_13plus  = {n13}")
    print(f"n_under13 = {nun}")
    print(f"mean(13+)  = {s13.mean():+.4f}")
    print(f"mean(<13)  = {sun.mean():+.4f}")
    print(f"sd(13+)    = {s13.std():.4f}")
    print(f"sd(<13)    = {sun.std():.4f}")
    print()

    # === MOMENT TABLE WITH BOOTSTRAP P-VALUES ===
    print("=" * 76)
    print("CENTRAL MOMENTS (M1=mean, M2=variance, M3=skew-like, etc.)")
    print("=" * 76)
    cm13 = central_moments(s13, k=6)
    cm_un = central_moments(sun, k=6)
    # Bootstrap matched-N moments from <13
    rng = np.random.default_rng(20260505)
    boot_cms = np.zeros((N_BOOTSTRAP, 6))
    for i in range(N_BOOTSTRAP):
        sample = rng.choice(sun, size=n13, replace=False)
        boot_cms[i] = central_moments(sample, k=6)
    # For each moment: p = fraction of bootstraps where |sample - <13_full| >= |13+ - <13_full|
    obs_diff = np.abs(cm13 - cm_un)
    boot_diff = np.abs(boot_cms - cm_un[None, :])  # (B, 6)
    p_vals = (boot_diff >= obs_diff[None, :]).mean(axis=0)
    print(f'{"order":<6} {"M_13plus":>10} {"M_under13":>11} {"obs_diff":>10} {"boot_p":>9}')
    print("-" * 76)
    for j in range(6):
        order = j + 1
        label = f'M{order}'
        if order == 1:
            label += ' (mean)'
        elif order == 2:
            label += ' (var)'
        elif order == 3:
            label += ' (skew)'
        elif order == 4:
            label += ' (kurt)'
        s13_str = ('{:+.5f}').format(cm13[j])
        sun_str = ('{:+.5f}').format(cm_un[j])
        diff_str = ('{:.5f}').format(obs_diff[j])
        p_str = ('{:.3f}').format(p_vals[j])
        flag = ' *' if p_vals[j] < 0.05 else ''
        print(f'{label:<10} {s13_str:>10} {sun_str:>11} {diff_str:>10} {p_str:>9}{flag}')
    print()

    # === CHARACTERISTIC FUNCTION ===
    print("=" * 76)
    print("EMPIRICAL CHARACTERISTIC FUNCTION on t ∈ [-5, 5] step 0.05 (201 points)")
    print("=" * 76)
    phi_13 = empirical_cf(s13, T_GRID)
    phi_un = empirical_cf(sun, T_GRID)
    obs_cf_diff = np.abs(phi_13 - phi_un)

    # Bootstrap CF differences
    boot_cf_diffs = np.zeros((N_BOOTSTRAP, len(T_GRID)))
    for i in range(N_BOOTSTRAP):
        sample = rng.choice(sun, size=n13, replace=False)
        phi_sample = empirical_cf(sample, T_GRID)
        boot_cf_diffs[i] = np.abs(phi_sample - phi_un)

    # Bootstrap noise envelope
    boot_p95 = np.quantile(boot_cf_diffs, 0.95, axis=0)
    boot_p99 = np.quantile(boot_cf_diffs, 0.99, axis=0)
    # p-value at each t: fraction of bootstraps producing diff >= observed
    p_vals_t = (boot_cf_diffs >= obs_cf_diff[None, :]).mean(axis=0)

    # Find regions of significance
    sig_mask = p_vals_t < 0.05
    print(f"Modes with p<0.05: {sig_mask.sum()} of {len(T_GRID)} grid points")
    print()
    # Aggregate by t-band
    bands = [(-5, -3, "tail/high-mode"), (-3, -1, "medium"), (-1, 1, "low (M1+M2)"),
             (1, 3, "medium"), (3, 5, "tail/high-mode")]
    print(f'{"band":<25} {"|t|_low":>8} {"|t|_high":>9} {"n_pts":>6} {"n_sig":>6} {"frac_sig":>10} {"max_diff":>10} {"max_p95_envelope":>18}')
    print("-" * 76)
    for lo, hi, label in bands:
        mask = (T_GRID >= lo) & (T_GRID <= hi)
        n_total = mask.sum()
        n_sig = (sig_mask & mask).sum()
        max_diff = obs_cf_diff[mask].max() if n_total > 0 else 0
        max_p95 = boot_p95[mask].max() if n_total > 0 else 0
        ratio = n_sig / n_total if n_total > 0 else 0
        print(f'{label:<25} {lo:>8.1f} {hi:>9.1f} {n_total:>6} {n_sig:>6} {ratio:>10.1%} {max_diff:>10.4f} {max_p95:>18.4f}')

    # Find peak diff t value
    peak_idx = np.argmax(obs_cf_diff)
    peak_t = T_GRID[peak_idx]
    peak_diff = obs_cf_diff[peak_idx]
    peak_p = p_vals_t[peak_idx]
    print()
    print(f'Peak |Δphi(t)|: t* = {peak_t:+.2f}, |Δphi(t*)| = {peak_diff:.5f}, bootstrap p = {peak_p:.3f}')

    # === VERDICT ===
    print()
    print("=" * 76)
    print("VERDICT")
    print("=" * 76)
    higher_mode_p = p_vals[2:6]  # M3-M6
    higher_mode_sig = (higher_mode_p < 0.05).sum()
    cf_higher_mode_sig = (sig_mask & ((T_GRID < -1) | (T_GRID > 1))).sum()
    cf_higher_mode_total = ((T_GRID < -1) | (T_GRID > 1)).sum()
    cf_higher_mode_frac = cf_higher_mode_sig / cf_higher_mode_total if cf_higher_mode_total else 0

    print(f"Higher-moment significance (M3-M6): {higher_mode_sig}/4 moments at p<0.05")
    print(f"CF higher-mode significance (|t|>1): {cf_higher_mode_frac:.1%} of grid points at p<0.05")
    print()
    if higher_mode_sig >= 2 and cf_higher_mode_frac > 0.20:
        print("VERDICT: STRUCTURAL COUPLING AT HIGHER FOURIER MODES")
        print("        AST×13+ couples beyond M2. Test 1 missed it via moment-2 truncation.")
        print("        Identify dominant differing mode below.")
    elif higher_mode_sig == 0 and cf_higher_mode_frac < 0.10:
        print("VERDICT: PROCESS-ONLY CLASS (NOT STRUCTURALLY COUPLED)")
        print("        AST×13+ shows no coupling beyond the moment-1 mean shift.")
        print("        Career stage genuinely behaves differently from position-driven classes.")
    else:
        print("VERDICT: MIXED — partial higher-mode coupling")
        print(f"        {higher_mode_sig}/4 higher moments differ; {cf_higher_mode_frac:.1%} of CF tail modes differ.")

    # === PLOT ===
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(T_GRID, obs_cf_diff, "b-", lw=2, label=f"|Δφ(t)| (13+ vs <13, n_13+={n13})")
        ax.fill_between(T_GRID, 0, boot_p95, color="gray", alpha=0.3,
                         label="bootstrap 95% noise envelope (matched n=33 from <13)")
        ax.fill_between(T_GRID, 0, boot_p99, color="gray", alpha=0.15,
                         label="bootstrap 99% noise envelope")
        ax.set_xlabel("t (Fourier mode)")
        ax.set_ylabel("|φ_13+(t) - φ_<13(t)|")
        ax.set_title("Characteristic-function coupling test: AST × 13+ vs <13")
        ax.axvspan(-1, 1, alpha=0.1, color="green", label="moment-2 region (|t|<1)")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plot_path = OUT_DIR / "cf_diff.png"
        plt.savefig(plot_path, dpi=120)
        print(f"\nPlot saved: {plot_path}")
    except Exception as e:
        print(f"Plot skipped: {e}")

    # Save summary
    summary = {
        "n_13plus": int(n13), "n_under13": int(nun),
        "central_moments_13plus": cm13.tolist(),
        "central_moments_under13": cm_un.tolist(),
        "moment_p_values": p_vals.tolist(),
        "cf_grid": T_GRID.tolist(),
        "cf_diff_obs": obs_cf_diff.tolist(),
        "cf_p_values_t": p_vals_t.tolist(),
        "cf_p95_envelope": boot_p95.tolist(),
        "peak_t": float(peak_t), "peak_diff": float(peak_diff), "peak_p": float(peak_p),
        "n_bootstrap": N_BOOTSTRAP,
    }
    with open(OUT_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary -> {OUT_DIR}/summary.json")


if __name__ == "__main__":
    main()
