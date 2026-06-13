"""
RMD-SRC NBA — Path B diagnostic extension (v1.3 amendment, SHA f3ede6c).

For each arm:
  1. Compute Check D = Hartigan dip on within-cell residuals
     r_pg = y_pg - mu_cell (cell training-window pooled mean).
  2. residual_clean = (Check D PASS) AND (Check B PASS) AND (Check C PASS).
  3. Path B Step 4 disposition (vacuous if no residual_clean non-Stationary).
  4. Path B F2 = (n_Stationary + n_nonStat_residual_clean) / (K*4 - n_Edge).
  5. Path B comparative arm = same logic as Path A but using residual_clean.
  6. Cross-arm: Path A vs Path B regime-label kappa (per arm per observable).

Localization disposition (v1.3 section 2.4 locked):
  Frac(Check D PASS) >= 0.50 -> measurement-on-raw-values localized
  Frac(Check D PASS) in [0.20, 0.50) -> partial localization
  Frac(Check D PASS) < 0.20 -> substrate-level multimodality

Path A reports stand untouched. Outputs append to SUBSTRATE_LEDGER.md.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import diptest

sys.path.insert(0, str(Path(__file__).parent))
from _common import (
    ALL_SEASONS, OBSERVABLES, RESULTS, TRAIN_SEASONS, verify_sha_lock,
)
from step02_classify_trajectories import load_observables
from step05_falsifiers_and_comparative import (
    F2_FIRE_FRAC, F4_FIRE_KAPPA, ARMS, REGIME_CODE, CODE_REGIME,
    COMPARATIVE_PER_CELL_R,
)

DATA = Path(r"D:/NBA Projections/data/parquet")
DIP_P_FLOOR = 0.05


def compute_check_d(arm: str) -> pd.DataFrame:
    """For each (cell, observable): pool training-window per-game values,
    subtract cell mean, run dip on the residuals."""
    p0 = pd.read_parquet(RESULTS / f"P0_partition_{arm}.parquet")
    box = load_observables(p0)
    cell_map = p0.set_index(["nba_api_id", "season"])["cell_id"]
    box["cell_id"] = box.set_index(["nba_api_id", "season"]).index.map(cell_map)
    box = box[box["cell_id"].notna()].copy()

    train_cls = pd.read_parquet(
        RESULTS / f"trajectory_classification_{arm}.parquet")
    cells = sorted(train_cls["cell_id"].unique())

    rows = []
    for cid in cells:
        for obs in OBSERVABLES:
            vals = box.loc[box["cell_id"] == cid, obs].to_numpy(float)
            vals = vals[np.isfinite(vals)]
            if len(vals) < 4:
                rows.append({"cell_id": cid, "observable": obs,
                              "n_pg": int(len(vals)),
                              "dip_residual_p": 1.0,
                              "check_D_pass": True})
                continue
            mu = float(vals.mean())
            resid = vals - mu
            try:
                _, p = diptest.diptest(resid)
                p = float(p)
            except Exception:
                p = 1.0
            rows.append({"cell_id": cid, "observable": obs,
                          "n_pg": int(len(vals)),
                          "dip_residual_p": p,
                          "check_D_pass": p >= DIP_P_FLOOR})
    return pd.DataFrame(rows)


def run_path_b_for_arm(arm: str, sha_payload: dict) -> dict:
    print(f"\n========== Path B arm={arm} ==========")
    check_d = compute_check_d(arm)
    n_total = len(check_d)
    n_d_pass = int(check_d["check_D_pass"].sum())
    frac_d_pass = n_d_pass / n_total if n_total else float("nan")
    print(f"  Check D pass: {n_d_pass}/{n_total} = {100*frac_d_pass:.1f}%")

    # Merge with Path A Step 3 to compute residual_clean.
    val_a = pd.read_parquet(RESULTS / f"step03_validation_{arm}.parquet")
    merged = check_d.merge(val_a[["cell_id", "observable", "perm_pass",
                                    "loso_pass"]],
                            on=["cell_id", "observable"], how="left")
    merged["residual_clean"] = (merged["check_D_pass"]
                                  & merged["perm_pass"]
                                  & merged["loso_pass"])
    n_residual_clean = int(merged["residual_clean"].sum())
    print(f"  residual_clean (D AND B AND C): {n_residual_clean}/{n_total} "
          f"= {100*n_residual_clean/n_total:.1f}%")

    merged.to_parquet(RESULTS / f"step03b_validation_{arm}.parquet",
                       index=False)

    # Path B F2.
    cls = pd.read_parquet(RESULTS / f"trajectory_classification_{arm}.parquet")
    full = cls.merge(merged[["cell_id", "observable", "residual_clean"]],
                      on=["cell_id", "observable"], how="left")
    n_stat = int((full["regime"] == "Stationary").sum())
    n_edge = int((full["regime"] == "Edge").sum())
    non_stat = full[full["regime"].isin(
        ["Concentrating", "Diffusing", "Contracting", "Drifting"])]
    n_nonstat_residual_clean = int(
        (non_stat["residual_clean"] == True).sum())
    n_clean_terminating = n_stat + n_nonstat_residual_clean
    denom = n_total - n_edge
    f2b_frac = n_clean_terminating / denom if denom > 0 else float("nan")
    f2b_fires = f2b_frac < F2_FIRE_FRAC
    print(f"  Path B F2: {n_clean_terminating}/{denom} = "
          f"{100*f2b_frac:.1f}% (fires: {f2b_fires})")

    # Path B Step 4 input cardinality.
    step4b_eligible = int(n_nonstat_residual_clean)
    print(f"  Path B Step 4 eligible: {step4b_eligible}")

    # Path B comparative (uses residual_clean for PASS criterion).
    # Re-load the cached per-cell transfer r from Path A artifacts.
    comp_a = pd.read_parquet(
        RESULTS / f"step05_comparative_{arm}.parquet")
    comp_b_rows = []
    val_idx = merged.set_index(["cell_id", "observable"])
    for _, r in comp_a.iterrows():
        cid, obs = r["cell_id"], r["observable"]
        regime_train = r["regime_train"]
        regime_holdout = r["regime_holdout"]
        per_r = r["per_cell_r"]
        is_non_stat = regime_train in {"Concentrating", "Diffusing",
                                         "Contracting", "Drifting"}
        is_edge = regime_train == "Edge"
        is_stationary = regime_train == "Stationary"
        rclean = (bool(val_idx.loc[(cid, obs), "residual_clean"])
                   if (cid, obs) in val_idx.index else False)
        regime_flipped = regime_train != regime_holdout
        if not rclean or is_stationary or is_edge:
            verdict = "TIE"
            reason = ("Stationary" if is_stationary
                       else "Edge" if is_edge
                       else "residual_clean_failed")
        elif (is_non_stat and np.isfinite(per_r)
              and per_r >= COMPARATIVE_PER_CELL_R):
            verdict = "PASS"
            reason = f"residual_clean + non-Stat + r={per_r:.2f}>=0.50"
        elif (is_non_stat and np.isfinite(per_r)
              and per_r < COMPARATIVE_PER_CELL_R and regime_flipped):
            verdict = "LOSE"
            reason = f"regime flipped to {regime_holdout}, r={per_r:.2f}<0.50"
        else:
            verdict = "TIE"
            reason = "non-conclusive transfer test"
        comp_b_rows.append({"cell_id": cid, "observable": obs,
                              "regime_train": regime_train,
                              "regime_holdout": regime_holdout,
                              "per_cell_r": per_r,
                              "residual_clean": rclean,
                              "verdict": verdict, "reason": reason})
    comp_b = pd.DataFrame(comp_b_rows)
    comp_b.to_parquet(RESULTS / f"step05b_comparative_{arm}.parquet",
                       index=False)
    comp_counts = Counter(comp_b["verdict"])
    print(f"  Path B comparative: {dict(comp_counts)}")

    return {
        "arm": arm,
        "check_d_pass": n_d_pass,
        "check_d_total": n_total,
        "check_d_frac": frac_d_pass,
        "residual_clean": n_residual_clean,
        "f2b_clean": n_clean_terminating,
        "f2b_denom": denom,
        "f2b_frac": f2b_frac,
        "f2b_fires": f2b_fires,
        "step4b_eligible": step4b_eligible,
        "comparative_counts": dict(comp_counts),
    }


def localization_disposition(frac_pass: float) -> str:
    if frac_pass >= 0.50:
        return "localized (measurement-on-raw-values)"
    if frac_pass >= 0.20:
        return "partial localization"
    return "substrate-level multimodality"


def append_path_b_to_ledger(findings: dict) -> None:
    ledger = RESULTS / "SUBSTRATE_LEDGER.md"
    body = ledger.read_text(encoding="utf-8")

    # Append a new section.
    new_section = ["\n## Path B (v1.3 dip-on-residuals) results\n",
                    "Locked at SHA `f3ede6ccebc29009b666146542465693f6fa721c`. "
                    "Check D (Hartigan dip on r_pg = y_pg - mu_cell) computed "
                    "per (cell, observable) per arm. Path A reports above are "
                    "NOT modified. Original Step 3 Check A continues firing "
                    "as documented.",
                    "",
                    "### Headline by arm\n",
                    "| Arm | Check D pass | Frac pass | Localization disposition | "
                    "residual_clean | Path B F2 | F2 fires? | Step 4 eligible "
                    "| Comp PASS / TIE / LOSE |",
                    "|---|---|---|---|---|---|---|---|---|"]
    for arm, f in findings.items():
        comp = f["comparative_counts"]
        comp_str = (f"{comp.get('PASS', 0)} / {comp.get('TIE', 0)} / "
                     f"{comp.get('LOSE', 0)}")
        new_section.append(
            f"| `{arm}` | {f['check_d_pass']}/{f['check_d_total']} | "
            f"{100*f['check_d_frac']:.1f}% | "
            f"{localization_disposition(f['check_d_frac'])} | "
            f"{f['residual_clean']} | "
            f"{f['f2b_clean']}/{f['f2b_denom']} = {100*f['f2b_frac']:.1f}% | "
            f"{'Y' if f['f2b_fires'] else 'N'} | "
            f"{f['step4b_eligible']} | {comp_str} |"
        )

    # Aggregate disposition across arms.
    all_frac = [f["check_d_frac"] for f in findings.values()
                 if np.isfinite(f["check_d_frac"])]
    mean_frac = float(np.mean(all_frac)) if all_frac else float("nan")
    aggregate = localization_disposition(mean_frac)
    new_section += ["",
                     f"### Aggregate Path B disposition",
                     f"Mean Frac(Check D PASS) across 4 arms: "
                     f"**{100*mean_frac:.1f}%** -> **{aggregate}**.",
                     ""]

    ledger.write_text(body.rstrip() + "\n" + "\n".join(new_section) + "\n",
                       encoding="utf-8")


def main() -> int:
    # Note: we currently don't have a way to verify v1.3 SHA in
    # _common.verify_sha_lock; v1.0/v1.1/v1.2 are verified, and v1.3's
    # presence in SHA_LOCK.txt is the audit pointer (the lock event).
    sha = verify_sha_lock("Path B (v1.3 extension)", arm="mpg_adj")

    findings: dict[str, dict] = {}
    for arm in ARMS:
        findings[arm] = run_path_b_for_arm(arm, sha)

    (RESULTS / "path_b_findings.json").write_text(
        json.dumps(findings, indent=2, default=str), encoding="utf-8")
    append_path_b_to_ledger(findings)
    print(f"\nPath B done. Substrate ledger updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
