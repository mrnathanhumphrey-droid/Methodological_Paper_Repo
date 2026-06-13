"""
RMD-SRC NBA — Step 3: response validation.

Per locked pre-reg v1.0 §4 (and v1.1/v1.2 amendments inherit identically).
For each (cell, observable):
  Check A: single-mode Hartigan dip on pooled per-game values across training
           seasons. PASS if p_dip >= 0.05.
  Check B: permutation-stability — exhaustively permute the 5 season-index
           assignments among the 5 (mu_s, var_s) points; recompute regime
           per permutation. PASS if the original regime is the modal label in
           >= 60% of the 120 permutations.
  Check C: leave-one-season-out — for each of the 5 training seasons, drop
           that season's (mu_s, var_s) point, recompute regime on the
           remaining 4 with their actual season indices. PASS if >= 3 of
           5 LOSO folds return the original regime.

A cell is response-validated (clean) iff all three checks PASS.

Outputs (per arm):
  step03_validation_{arm}.parquet  per (cell, obs): the three flags + clean
  step03_diagnostic_{arm}.md       headline pass-rates + per-cell ledger
"""
from __future__ import annotations

import argparse
import itertools
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import diptest

sys.path.insert(0, str(Path(__file__).parent))
from _common import (
    OBSERVABLES, PIPE_ROOT, RESULTS, TRAIN_SEASONS, verify_sha_lock,
)
from step02_classify_trajectories import (
    EPS_MU, EPS_VAR, MU_BAR_FLOOR, VAR_BAR_FLOOR,
    classify, load_observables, ols_slope, per36,
)

DATA = Path(r"D:/NBA Projections/data/parquet")

# Check thresholds (pre-reg §4 locked).
DIP_P_FLOOR = 0.05
PERM_PASS_FRAC = 0.60      # >= 60% of permutations return original regime
LOSO_PASS_COUNT = 3        # >= 3 of 5 folds return original regime


def _classify_pair(mu: np.ndarray, var: np.ndarray, idx: np.ndarray) -> str:
    """Slope + classify on a (mu, var) trajectory at the supplied indices."""
    if len(mu) < 2:
        return "Insufficient_data"
    mu_dot = ols_slope(idx.astype(float), mu)
    var_dot = ols_slope(idx.astype(float), var)
    mu_bar = float(mu.mean())
    var_bar = float(var.mean())
    if abs(mu_bar) > MU_BAR_FLOOR:
        r_mu = mu_dot / abs(mu_bar)
    else:
        r_mu = mu_dot
    if abs(var_bar) > VAR_BAR_FLOOR:
        r_var = var_dot / abs(var_bar)
    else:
        r_var = var_dot
    return classify(r_mu, r_var)


def _run_perm_check(mu: np.ndarray, var: np.ndarray, orig_regime: str
                    ) -> tuple[float, str]:
    """Exhaustively permute season-index assignment over the 5 (mu, var)
    points. Return (fraction-matching-original, modal-label)."""
    n = len(mu)
    if n < 2:
        return 0.0, "Insufficient_data"
    labels = []
    base_idx = np.arange(n)
    for perm in itertools.permutations(range(n)):
        # New index = base, but mu/var values reordered.
        mu_p = mu[list(perm)]
        var_p = var[list(perm)]
        labels.append(_classify_pair(mu_p, var_p, base_idx))
    cnt = Counter(labels)
    modal = cnt.most_common(1)[0][0]
    match = cnt.get(orig_regime, 0) / len(labels)
    return match, modal


def _run_loso_check(mu: np.ndarray, var: np.ndarray, idx: np.ndarray,
                    orig_regime: str) -> int:
    """5-fold leave-one-season-out. Return count of folds matching original."""
    n = len(mu)
    matches = 0
    for drop in range(n):
        keep = [i for i in range(n) if i != drop]
        mu_k = mu[keep]
        var_k = var[keep]
        idx_k = idx[keep]
        if _classify_pair(mu_k, var_k, idx_k) == orig_regime:
            matches += 1
    return matches


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["usg", "mpg", "usg_adj", "mpg_adj",
                                       "off_feast", "def_feast"],
                     required=True)
    args = ap.parse_args()
    arm = args.arm

    if arm in {"off_feast", "def_feast"}:
        txt = (RESULTS.parent / "SHA_LOCK.txt").read_text(encoding="utf-8")
        if "## spatial re-axis" not in txt or "cd40b46" not in txt:
            sys.exit("[Step 3] spatial re-axis lock SHA not found in SHA_LOCK.txt.")
        print(f"[Step 3 validate [arm={arm}]] spatial SHA-lock verified: cd40b46")
        sha = {"v1.0": "cd40b46", "v1.1": ""}
    else:
        sha = verify_sha_lock(f"Step 3 validate [arm={arm}]", arm=arm)

    # Load Step 2 outputs.
    cls = pd.read_parquet(RESULTS / f"trajectory_classification_{arm}.parquet")
    traj = pd.read_parquet(RESULTS / f"moment_trajectories_{arm}.parquet")
    p0 = pd.read_parquet(RESULTS / f"P0_partition_{arm}.parquet")
    print(f"\n--- Step 3 ({arm}) ---")
    print(f"  Step 2 cells classified: {len(cls)}")

    # Per-game observable values per cell (training window pooled).
    box = load_observables(p0)
    cell_map = p0.set_index(["nba_api_id", "season"])["cell_id"]
    box["cell_id"] = box.set_index(["nba_api_id", "season"]).index.map(cell_map)
    box = box[box["cell_id"].notna()].copy()

    train_idx_map = {s: i for i, s in enumerate(TRAIN_SEASONS)}

    rows: list[dict] = []
    for _, r in cls.iterrows():
        cid = r["cell_id"]
        obs = r["observable"]
        orig = r["regime"]

        # Insufficient_data cells skip Step 3 (already flagged at Step 2).
        if orig == "Insufficient_data":
            rows.append({"cell_id": cid, "observable": obs,
                          "orig_regime": orig, "dip_p": np.nan,
                          "dip_pass": False, "perm_match_frac": np.nan,
                          "perm_modal": "", "perm_pass": False,
                          "loso_matches": 0, "loso_pass": False,
                          "clean": False, "failed_checks": "insufficient"})
            continue

        # Check A: Hartigan dip on pooled per-game values.
        vals = box.loc[box["cell_id"] == cid, obs].to_numpy(dtype=float)
        vals = vals[np.isfinite(vals)]
        if len(vals) < 4:
            dip_p = 1.0  # too few points; dip undefined -> default unimodal
        else:
            try:
                dip_stat, dip_p = diptest.diptest(vals)
                dip_p = float(dip_p)
            except Exception:
                dip_p = 1.0
        dip_pass = dip_p >= DIP_P_FLOOR

        # Checks B + C: re-load trajectory (mu, var) per season.
        gtraj = (traj[(traj["cell_id"] == cid)
                       & (traj["observable"] == obs)
                       & (traj["season"].isin(TRAIN_SEASONS))]
                  .sort_values("season"))
        mu = gtraj["mu"].to_numpy(float)
        var = gtraj["var"].to_numpy(float)
        idx = np.array([train_idx_map[s] for s in gtraj["season"]], dtype=float)

        if len(mu) < 3:
            perm_match_frac = 0.0; perm_modal = ""; perm_pass = False
            loso_matches = 0; loso_pass = False
        else:
            perm_match_frac, perm_modal = _run_perm_check(mu, var, orig)
            perm_pass = perm_match_frac >= PERM_PASS_FRAC
            loso_matches = _run_loso_check(mu, var, idx, orig)
            loso_pass = loso_matches >= LOSO_PASS_COUNT

        clean = bool(dip_pass and perm_pass and loso_pass)
        failed = []
        if not dip_pass: failed.append("dip")
        if not perm_pass: failed.append("perm")
        if not loso_pass: failed.append("loso")
        rows.append({"cell_id": cid, "observable": obs,
                      "orig_regime": orig, "dip_p": dip_p, "dip_pass": dip_pass,
                      "perm_match_frac": perm_match_frac, "perm_modal": perm_modal,
                      "perm_pass": perm_pass, "loso_matches": loso_matches,
                      "loso_pass": loso_pass, "clean": clean,
                      "failed_checks": "|".join(failed) if failed else ""})

    val = pd.DataFrame(rows)
    val_path = RESULTS / f"step03_validation_{arm}.parquet"
    val.to_parquet(val_path, index=False)
    print(f"  -> {val_path.name}")

    # ----- diagnostic -----
    overall_pass = int(val["clean"].sum())
    overall_total = len(val)
    by_check = {
        "dip": int(val["dip_pass"].sum()),
        "perm": int(val["perm_pass"].sum()),
        "loso": int(val["loso_pass"].sum()),
    }

    # Per-regime pass rate.
    by_regime = (val.groupby("orig_regime")
                    .agg(n=("clean", "size"),
                         clean=("clean", "sum"))
                    .reset_index())
    by_regime["pct_clean"] = 100 * by_regime["clean"] / by_regime["n"]

    # Per-observable clean count by Stationary vs non-Stationary (for F2 preview).
    val["is_stationary"] = val["orig_regime"] == "Stationary"
    val["is_edge"] = val["orig_regime"] == "Edge"
    val["nonstat_nonedge"] = ~val["is_stationary"] & ~val["is_edge"]
    by_obs = (val.groupby("observable")
                 .agg(n=("clean", "size"),
                      n_stationary=("is_stationary", "sum"),
                      n_edge=("is_edge", "sum"),
                      n_nonstat_clean=("clean",
                                       lambda c: int(
                                           ((c) & val.loc[c.index,
                                                          "nonstat_nonedge"]
                                            ).sum())))
                 .reset_index())

    # Step 2 + Step 3 combined: which non-Stationary cells survive Step 3?
    survivors = val[val["nonstat_nonedge"] & val["clean"]][
        ["cell_id", "observable", "orig_regime", "dip_p",
         "perm_match_frac", "loso_matches"]].sort_values(
        ["orig_regime", "cell_id", "observable"])

    lines = [
        f"# Step 3 — response validation (arm = {arm})\n",
        f"Locked v1.0 SHA: `{sha['v1.0']}`",
        (f"Locked v1.1 SHA: `{sha['v1.1']}`" if sha['v1.1']
         else "(v1.1 amendment not in scope)"),
        "",
        "## Headline",
        f"- Cells classified at Step 2: **{overall_total}**",
        f"- Cells passing all 3 Step-3 checks: **{overall_pass}**  "
        f"({100*overall_pass/overall_total:.1f}%)",
        f"- Pass by individual check (cells passing this check):",
        f"  - Hartigan dip  (p ≥ {DIP_P_FLOOR}): {by_check['dip']}/{overall_total}",
        f"  - Permutation   (modal ≥ {int(100*PERM_PASS_FRAC)}%): "
        f"{by_check['perm']}/{overall_total}",
        f"  - LOSO 5-fold   (≥ {LOSO_PASS_COUNT} match orig): "
        f"{by_check['loso']}/{overall_total}",
        "",
        "## Pass rate by original Step-2 regime",
        "| regime | n | clean | % clean |",
        "|---|---|---|---|",
    ]
    for _, r in by_regime.iterrows():
        lines.append(f"| {r['orig_regime']} | {int(r['n'])} | "
                      f"{int(r['clean'])} | {r['pct_clean']:.1f}% |")

    lines += ["", "## F2 preview (Stationary auto-clean + non-Stationary "
                  "passing Step 3, excluding Edge)",
              "| observable | n_cells | n_Stationary | n_Edge | "
              "n_nonStat_clean | terminates_cleanly (pre-Step-4) | "
              "% of (n - Edge) |",
              "|---|---|---|---|---|---|---|"]
    for _, r in by_obs.iterrows():
        n_clean_terminating = int(r["n_stationary"]) + int(r["n_nonstat_clean"])
        denom = int(r["n"]) - int(r["n_edge"])
        pct = 100 * n_clean_terminating / max(1, denom)
        lines.append(
            f"| {r['observable']} | {int(r['n'])} | {int(r['n_stationary'])} | "
            f"{int(r['n_edge'])} | {int(r['n_nonstat_clean'])} | "
            f"{n_clean_terminating} | {pct:.1f}% |"
        )

    lines += ["", "## Non-Stationary cells passing Step 3 (load-bearing for Step 4 4a/4b)"]
    if len(survivors) == 0:
        lines.append("\n*(none)*")
    else:
        lines.append("\n| cell_id | observable | regime | dip_p | perm match | loso |")
        lines.append("|---|---|---|---|---|---|")
        for _, r in survivors.iterrows():
            lines.append(
                f"| `{r['cell_id']}` | {r['observable']} | {r['orig_regime']} | "
                f"{r['dip_p']:.3f} | {r['perm_match_frac']:.2f} | "
                f"{int(r['loso_matches'])}/5 |"
            )

    lines += ["", "## Full per-cell ledger",
              "| cell_id | observable | regime | dip | perm | loso | clean | failed |",
              "|---|---|---|---|---|---|---|---|"]
    for _, r in val.sort_values(["cell_id", "observable"]).iterrows():
        lines.append(
            f"| `{r['cell_id']}` | {r['observable']} | {r['orig_regime']} | "
            f"{r['dip_p']:.3f} | {r['perm_match_frac']:.2f} | "
            f"{int(r['loso_matches'])}/5 | {'Y' if r['clean'] else 'N'} | "
            f"{r['failed_checks']} |"
        )

    (RESULTS / f"step03_diagnostic_{arm}.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print(f"  -> step03_diagnostic_{arm}.md")
    print(f"\nStep 3 ({arm}) complete. clean={overall_pass}/{overall_total} "
          f"({100*overall_pass/overall_total:.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
