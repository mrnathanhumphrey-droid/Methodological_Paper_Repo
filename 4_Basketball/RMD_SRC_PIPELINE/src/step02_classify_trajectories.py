"""
RMD-SRC NBA — Step 2: moment-flow trajectories + 5-regime classification.

Per pre-reg v1.0 §3 (and v1.1 amendment §2.4: identical Step-2 protocol on
the MPG-tier partition).

For each (cell, observable) on the 5-season training window:
  1. Trajectory  = (mu_s, var_s) for s in TRAIN_SEASONS, computed over all
                   qualifying (player, game) per-36 values in cell x season.
  2. mu_dot, var_dot = OLS slopes of mu_s, var_s on season-index t in {0..4}.
  3. r_mu  = mu_dot / |mu_bar|   if |mu_bar|  > 0.01 else mu_dot (absolute)
     r_var = var_dot / |var_bar| if |var_bar| > 1e-6 else var_dot (absolute)
  4. Classify with the canonical 5-regime taxonomy at locked thresholds
     eps_mu = 0.02, eps_var = 0.05.
       |r_mu| <= eps AND |r_var| <= eps         -> Stationary
       r_mu  > +eps  AND r_var  < -eps          -> Concentrating
       r_mu  > +eps  AND r_var  > +eps          -> Diffusing
       r_mu  < -eps  AND r_var  < -eps          -> Contracting
       r_mu  < -eps  AND r_var  > +eps          -> Drifting
       (one slope inside, one outside)          -> Edge

Outputs (per arm):
  moment_trajectories_{arm}.parquet      cell x observable x season x (mu, var, n)
  trajectory_classification_{arm}.parquet  cell x observable x classifier-fields
  step02_diagnostic_{arm}.md             regime distribution

Per-game qualification: minutes > 0 (DNPs / GS=0-min appearances excluded).
Per-36 values: rate = stat * 36 / minutes.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _common import (
    OBSERVABLES, PIPE_ROOT, RESULTS, TRAIN_SEASONS, verify_sha_lock,
)

DATA = Path(r"D:/NBA Projections/data/parquet")

# Locked thresholds (pre-reg v1.0 §3.1).
EPS_MU = 0.02
EPS_VAR = 0.05

# Normalization fallback floors.
MU_BAR_FLOOR = 0.01     # if |mu_bar| <= this, use absolute slope
VAR_BAR_FLOOR = 1e-6    # if |var_bar| <= this, use absolute slope


def classify(r_mu: float, r_var: float) -> str:
    mu_in = abs(r_mu) <= EPS_MU
    var_in = abs(r_var) <= EPS_VAR
    if mu_in and var_in:
        return "Stationary"
    if not mu_in and not var_in:
        if r_mu > 0 and r_var < 0:
            return "Concentrating"
        if r_mu > 0 and r_var > 0:
            return "Diffusing"
        if r_mu < 0 and r_var < 0:
            return "Contracting"
        if r_mu < 0 and r_var > 0:
            return "Drifting"
    return "Edge"  # one slope inside, one outside


def per36(stat: pd.Series, minutes: pd.Series) -> pd.Series:
    """stat * 36 / minutes, with minutes > 0 enforced upstream."""
    return stat.astype(float) * 36.0 / minutes.astype(float)


def load_observables(p0: pd.DataFrame) -> pd.DataFrame:
    """Per-(player, game, season) box rows restricted to qualifying players
    (those in p0), with PTS/REB/AST/BLK per-36 columns appended.
    Per-game filter: minutes > 0."""
    bs = pd.read_parquet(DATA / "historical_box_scores.parquet",
                          columns=["nba_api_id", "season", "season_type",
                                   "minutes", "PTS", "REB", "AST", "BLK"])
    bs = bs[(bs["season_type"] == "Regular Season")
            & (bs["season"].isin(TRAIN_SEASONS))
            & (bs["minutes"] > 0)].copy()
    # Restrict to qualifying (player, season) pairs only.
    qual_keys = set(zip(p0["nba_api_id"].astype(int),
                         p0["season"].astype(str)))
    bs["_k"] = list(zip(bs["nba_api_id"].astype(int),
                         bs["season"].astype(str)))
    bs = bs[bs["_k"].isin(qual_keys)].drop(columns="_k")
    bs["PTS_per36"] = per36(bs["PTS"], bs["minutes"])
    bs["REB_per36"] = per36(bs["REB"], bs["minutes"])
    bs["AST_per36"] = per36(bs["AST"], bs["minutes"])
    bs["BLK_per36"] = per36(bs["BLK"], bs["minutes"])
    return bs


def compute_trajectories(box: pd.DataFrame, p0: pd.DataFrame) -> pd.DataFrame:
    """Long-form: cell_id x observable x season -> mu, var, n."""
    # Attach cell_id to per-game rows.
    cell_map = p0.set_index(["nba_api_id", "season"])["cell_id"]
    box["cell_id"] = box.set_index(["nba_api_id", "season"]).index.map(cell_map)
    box = box[box["cell_id"].notna()].copy()

    rows: list[dict] = []
    for obs in OBSERVABLES:
        for (cid, ssn), g in box.groupby(["cell_id", "season"], observed=True):
            vals = g[obs].to_numpy(dtype=float)
            vals = vals[np.isfinite(vals)]
            if len(vals) == 0:
                continue
            rows.append({
                "cell_id": cid, "observable": obs, "season": ssn,
                "mu": float(vals.mean()),
                "var": float(vals.var(ddof=1)) if len(vals) > 1 else 0.0,
                "n": int(len(vals)),
            })
    return pd.DataFrame(rows)


def ols_slope(years_idx: np.ndarray, y: np.ndarray) -> float:
    if len(y) < 2 or np.std(y) == 0:
        return 0.0
    return float(np.polyfit(years_idx, y, 1)[0])


def classify_trajectories(traj: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    train_idx = {s: i for i, s in enumerate(TRAIN_SEASONS)}
    for (cid, obs), g in traj.groupby(["cell_id", "observable"], observed=True):
        g = g[g["season"].isin(TRAIN_SEASONS)].sort_values("season")
        if len(g) < 3:
            # Need at least 3 points for a meaningful slope on the training window.
            rows.append({"cell_id": cid, "observable": obs,
                          "n_seasons": len(g), "regime": "Insufficient_data"})
            continue
        idx = np.array([train_idx[s] for s in g["season"]], dtype=float)
        mu = g["mu"].to_numpy(float)
        var = g["var"].to_numpy(float)
        mu_dot = ols_slope(idx, mu)
        var_dot = ols_slope(idx, var)
        mu_bar = float(mu.mean())
        var_bar = float(var.mean())

        if abs(mu_bar) > MU_BAR_FLOOR:
            r_mu = mu_dot / abs(mu_bar)
            mu_normalized = True
        else:
            r_mu = mu_dot
            mu_normalized = False
        if abs(var_bar) > VAR_BAR_FLOOR:
            r_var = var_dot / abs(var_bar)
            var_normalized = True
        else:
            r_var = var_dot
            var_normalized = False

        regime = classify(r_mu, r_var)
        rows.append({
            "cell_id": cid, "observable": obs, "n_seasons": int(len(g)),
            "mu_bar": mu_bar, "var_bar": var_bar,
            "mu_dot": mu_dot, "var_dot": var_dot,
            "r_mu": r_mu, "r_var": r_var,
            "mu_normalized": mu_normalized, "var_normalized": var_normalized,
            "regime": regime,
        })
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm",
                     choices=["usg", "mpg", "usg_adj", "mpg_adj",
                              "off_feast", "def_feast"],
                     required=True)
    args = ap.parse_args()
    arm = args.arm

    SPATIAL_ARMS = {"off_feast", "def_feast"}
    if arm in SPATIAL_ARMS:
        # Spatial re-axis discipline gate (pre-reg SHA cd40b46).
        txt = (RESULTS.parent / "SHA_LOCK.txt").read_text(encoding="utf-8")
        if "## spatial re-axis" not in txt or "cd40b46" not in txt:
            sys.exit("[Step 2] spatial re-axis lock SHA not found in SHA_LOCK.txt.")
        print(f"[Step 2 classify [arm={arm}]] spatial SHA-lock verified: cd40b46")
        sha = {"v1.0": "cd40b46", "v1.1": ""}
    else:
        sha = verify_sha_lock(f"Step 2 classify [arm={arm}]", arm=arm)

    p0_path = RESULTS / f"P0_partition_{arm}.parquet"
    if not p0_path.exists():
        sys.exit(f"[Step 2] Missing {p0_path.name}; run step01 --arm {arm} first.")
    p0 = pd.read_parquet(p0_path)
    # Profile-Sparse is a reported residual, not a cell — exclude from Step 2.
    p0 = p0[p0["cell_id"] != "Profile-Sparse"].copy()
    print(f"\n--- Loaded P0_partition_{arm}: "
          f"{len(p0):,} player-seasons, K={p0['cell_id'].nunique()}")

    print(f"--- Loading per-game observables (training window) ---")
    box = load_observables(p0)
    print(f"  per-game records (qual players, MIN>0, train seasons): {len(box):,}")

    print(f"--- Computing moment trajectories ---")
    traj = compute_trajectories(box, p0)
    print(f"  trajectory rows: {len(traj):,}")

    traj_path = RESULTS / f"moment_trajectories_{arm}.parquet"
    traj.to_parquet(traj_path, index=False)
    print(f"  -> {traj_path.name}")

    print(f"--- Classifying ---")
    cls = classify_trajectories(traj)
    cls_path = RESULTS / f"trajectory_classification_{arm}.parquet"
    cls.to_parquet(cls_path, index=False)
    print(f"  -> {cls_path.name}")

    # ----- diagnostic -----
    regime_counts = cls["regime"].value_counts().to_dict()
    by_obs = cls.groupby("observable")["regime"].value_counts().unstack(fill_value=0)

    lines = [f"# Step 2 — Trajectory classification (arm = {arm})\n",
              f"Locked SHA v1.0: `{sha['v1.0']}`",
              (f"Locked SHA v1.1: `{sha['v1.1']}`"
               if sha['v1.1'] else "(v1.1 amendment not in scope)"),
              "",
              f"Cells classified: {len(cls)}",
              f"Training window: {TRAIN_SEASONS[0]} -> {TRAIN_SEASONS[-1]} "
              f"({len(TRAIN_SEASONS)} seasons)",
              f"Thresholds: eps_mu = {EPS_MU}, eps_var = {EPS_VAR}",
              "",
              "## Regime distribution (overall)",
              "",
              "| Regime | Count |",
              "|---|---|"]
    for r, n in sorted(regime_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {r} | {n} |")

    lines += ["", "## Regime distribution by observable", ""]
    cols = sorted(set(by_obs.columns))
    lines.append("| Observable | " + " | ".join(cols) + " |")
    lines.append("|" + "---|" * (len(cols) + 1))
    for obs in OBSERVABLES:
        if obs not in by_obs.index:
            continue
        vals = " | ".join(str(int(by_obs.loc[obs].get(c, 0))) for c in cols)
        lines.append(f"| {obs} | {vals} |")

    # Flag fallback-to-absolute-slope cases.
    flagged = cls[(cls.get("mu_normalized") == False)
                   | (cls.get("var_normalized") == False)]
    lines += ["", f"## Normalization fallback (mu_bar < {MU_BAR_FLOOR} "
                  f"or var_bar < {VAR_BAR_FLOOR})",
              f"Cells using absolute slope: {len(flagged)}", ""]
    if len(flagged):
        lines.append("| cell_id | observable | mu_bar | var_bar | regime |")
        lines.append("|---|---|---|---|---|")
        for _, r in flagged.iterrows():
            lines.append(
                f"| `{r['cell_id']}` | {r['observable']} | "
                f"{r['mu_bar']:.4f} | {r['var_bar']:.4f} | {r['regime']} |"
            )

    # Per-cell regime list (full ledger).
    lines += ["", "## Per-cell regime ledger", "",
              "| cell_id | observable | r_mu | r_var | regime |",
              "|---|---|---|---|---|"]
    for _, r in cls.sort_values(["cell_id", "observable"]).iterrows():
        rmu = r.get("r_mu", float("nan"))
        rvar = r.get("r_var", float("nan"))
        lines.append(
            f"| `{r['cell_id']}` | {r['observable']} | "
            f"{rmu:+.4f} | {rvar:+.4f} | {r['regime']} |"
        )

    diag = "\n".join(lines) + "\n"
    (RESULTS / f"step02_diagnostic_{arm}.md").write_text(diag, encoding="utf-8")
    print(f"  -> step02_diagnostic_{arm}.md")

    print(f"\nStep 2 ({arm}) complete. "
          f"Regimes: {regime_counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
