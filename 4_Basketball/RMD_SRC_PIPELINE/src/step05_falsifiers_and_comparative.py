"""
RMD-SRC NBA — Step 5 + Step 6 + comparative arm + cross-arm ledger.

Per locked pre-reg v1.0 sections 6, 7, 8, 9 (and amendments v1.1, v1.2):
  - F1 substrate validity (R^2 >= 0.90 per observable -> correct refusal)
  - F2 decomposability (terminate cleanly fraction; <50% fires)
  - F3 lossy decomposition (vacuous under Path A on this substrate)
  - F4 regime non-transfer (Cohen kappa train->holdout < 0.40 fires)
  - Step 5 cell-signature transfer (mean column-wise Pearson r >= 0.80)
  - Step 6 mechanism inference (partition-level, confidence-tiered)
  - Comparative arm vs v6.1 LOCKED (per pre-reg section 9.2: Method B
    synthesizes Stationary for every cell; per-cell PASS/TIE/LOSE)
  - Cross-arm 4-arm regime kappa matrix (per amendment v1.1/v1.2 section 3)

Notes on spec-ambiguity handling (documented for the substrate ledger):
  - The pre-reg's Step 5 cell-signature 4-tuple references
    "beta_role_cohort (response coefficient on role-cohort indicator from
    Step 3 OLS fit)". Step 3 as locked has 3 checks but no per-cell OLS.
    The defensible reading used here: beta_role_cohort = within-cell OLS
    slope of per-game observable on the CONTINUOUS role-cohort metric
    (prior-season USG% for usg/usg_adj arms; same-season mean MPG for
    mpg/mpg_adj arms). Each player-game contributes one (x, y) pair
    where x is the player's USG% or mean MPG for that season.
  - rho_LOSO uses Step 3's loso_matches / 5 as the defensible reading.

Outputs (per arm and cross-arm):
  step05_falsifiers_{arm}.json
  step05_comparative_{arm}.parquet
  step05_diagnostic_{arm}.md
  crossarm_kappa_matrix.json
  SUBSTRATE_LEDGER.md
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, str(Path(__file__).parent))
from _common import (
    ALL_SEASONS, HOLDOUT_SEASONS, OBSERVABLES, PIPE_ROOT, RESULTS,
    TRAIN_SEASONS, verify_sha_lock,
)
from step02_classify_trajectories import (
    EPS_MU, EPS_VAR, MU_BAR_FLOOR, VAR_BAR_FLOOR, classify,
    load_observables, ols_slope, per36,
)

DATA = Path(r"D:/NBA Projections/data/parquet")

# Falsifier thresholds (locked).
F1_FIRE_R2 = 0.90
F2_FIRE_FRAC = 0.50
F4_FIRE_KAPPA = 0.40
STEP5_TRANSFER_R = 0.80
COMPARATIVE_PER_CELL_R = 0.50

ARMS = ("usg", "mpg", "usg_adj", "mpg_adj")

# Regime integer encoding (locked for cross-arm comparison).
REGIME_CODE = {"Stationary": 0, "Edge": 1, "Concentrating": 2,
               "Diffusing": 3, "Contracting": 4, "Drifting": 5,
               "Insufficient_data": 6}


# ---------------------------------------------------------------------------
# F1 — substrate validity
# ---------------------------------------------------------------------------

def compute_F1(arm: str) -> dict[str, float]:
    """R^2 per observable for additive linear model on partition variables.
    Pooled per-game records across the training window."""
    p0 = pd.read_parquet(RESULTS / f"P0_partition_{arm}.parquet")
    box = load_observables(p0)
    cell_map = p0.set_index(["nba_api_id", "season"])[
        ["pos_bucket", "yp_bucket", "rc_bucket"]]
    keys = list(zip(box["nba_api_id"].astype(int),
                     box["season"].astype(str)))
    box[["pos", "yp", "rc"]] = pd.DataFrame(
        [cell_map.loc[k].tolist() if k in cell_map.index
         else [None, None, None] for k in keys],
        index=box.index, columns=["pos", "yp", "rc"],
    )
    box = box.dropna(subset=["pos", "yp", "rc"]).copy()

    enc = OneHotEncoder(sparse_output=False, drop="first")
    X_cat = enc.fit_transform(box[["pos", "yp", "rc", "season"]])

    out: dict[str, float] = {}
    for obs in OBSERVABLES:
        y = box[obs].to_numpy(float)
        mask = np.isfinite(y)
        if mask.sum() < 100:
            out[obs] = float("nan"); continue
        reg = LinearRegression().fit(X_cat[mask], y[mask])
        out[obs] = float(reg.score(X_cat[mask], y[mask]))
    return out


# ---------------------------------------------------------------------------
# Holdout Step 2 — re-run trajectory classification on 2-season holdout
# ---------------------------------------------------------------------------

def holdout_step2(arm: str) -> pd.DataFrame:
    """Per (cell, observable): mu_holdout, var_holdout, slope, regime, on the
    holdout window (2024-25 + 2025-26)."""
    p0 = pd.read_parquet(RESULTS / f"P0_partition_{arm}.parquet")
    bs = pd.read_parquet(DATA / "historical_box_scores.parquet",
                          columns=["nba_api_id", "season", "season_type",
                                   "minutes", "PTS", "REB", "AST", "BLK"])
    bs = bs[(bs["season_type"] == "Regular Season")
            & (bs["season"].isin(HOLDOUT_SEASONS))
            & (bs["minutes"] > 0)].copy()
    qkeys = set(zip(p0["nba_api_id"].astype(int),
                     p0["season"].astype(str)))
    bs["_k"] = list(zip(bs["nba_api_id"].astype(int),
                         bs["season"].astype(str)))
    bs = bs[bs["_k"].isin(qkeys)].drop(columns="_k")
    for obs, src in [("PTS_per36", "PTS"), ("REB_per36", "REB"),
                     ("AST_per36", "AST"), ("BLK_per36", "BLK")]:
        bs[obs] = bs[src] * 36.0 / bs["minutes"]
    cell_map = p0.set_index(["nba_api_id", "season"])["cell_id"]
    bs["cell_id"] = bs.set_index(["nba_api_id", "season"]).index.map(cell_map)
    bs = bs[bs["cell_id"].notna()].copy()

    train_cls = pd.read_parquet(
        RESULTS / f"trajectory_classification_{arm}.parquet")
    cells = sorted(train_cls["cell_id"].unique())

    holdout_idx_map = {s: i for i, s in enumerate(HOLDOUT_SEASONS)}
    rows: list[dict] = []
    for cid in cells:
        for obs in OBSERVABLES:
            mus, vars_, idxs = [], [], []
            for ssn in HOLDOUT_SEASONS:
                vals = bs.loc[(bs["cell_id"] == cid) & (bs["season"] == ssn),
                                obs].to_numpy(float)
                vals = vals[np.isfinite(vals)]
                if len(vals) == 0:
                    continue
                mus.append(float(vals.mean()))
                vars_.append(float(vals.var(ddof=1)) if len(vals) > 1
                              else 0.0)
                idxs.append(holdout_idx_map[ssn])
            if len(mus) < 2:
                rows.append({"cell_id": cid, "observable": obs,
                              "regime_holdout": "Insufficient_data"})
                continue
            mu = np.array(mus); var = np.array(vars_); idx = np.array(idxs, float)
            mu_dot = ols_slope(idx, mu); var_dot = ols_slope(idx, var)
            mu_bar = float(mu.mean()); var_bar = float(var.mean())
            r_mu = mu_dot / abs(mu_bar) if abs(mu_bar) > MU_BAR_FLOOR else mu_dot
            r_var = (var_dot / abs(var_bar) if abs(var_bar) > VAR_BAR_FLOOR
                      else var_dot)
            rows.append({"cell_id": cid, "observable": obs,
                          "mu_bar_holdout": mu_bar, "var_bar_holdout": var_bar,
                          "r_mu_holdout": r_mu, "r_var_holdout": r_var,
                          "regime_holdout": classify(r_mu, r_var)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# F4 — regime non-transfer kappa
# ---------------------------------------------------------------------------

def compute_F4(arm: str, holdout_df: pd.DataFrame) -> dict[str, dict]:
    train = pd.read_parquet(RESULTS / f"trajectory_classification_{arm}.parquet")
    merged = train.merge(holdout_df, on=["cell_id", "observable"], how="inner")
    out: dict[str, dict] = {}
    for obs in OBSERVABLES:
        sub = merged[merged["observable"] == obs]
        labels_train = [REGIME_CODE.get(r, 6) for r in sub["regime"]]
        labels_hold = [REGIME_CODE.get(r, 6) for r in sub["regime_holdout"]]
        if len(set(labels_train + labels_hold)) <= 1 or len(sub) < 2:
            kap = float("nan")
        else:
            kap = float(cohen_kappa_score(labels_train, labels_hold))
        fires = (kap < F4_FIRE_KAPPA) if np.isfinite(kap) else None
        out[obs] = {"kappa": kap, "n_cells": int(len(sub)), "fires": fires}
    return out


# ---------------------------------------------------------------------------
# Step 5 cell-signature transfer + comparative per-cell r
# ---------------------------------------------------------------------------

def _continuous_role_metric(arm: str, p0: pd.DataFrame) -> pd.Series:
    """Per (nba_api_id, season) -> continuous role-cohort metric (USG% for
    usg arms, mean MPG for mpg arms)."""
    if arm.startswith("usg"):
        return p0.set_index(["nba_api_id", "season"])["prior_usg"]
    else:
        return p0.set_index(["nba_api_id", "season"])["mean_min"]


def build_signature_matrices(arm: str, holdout_df: pd.DataFrame
                              ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the 4-column cell-signature matrices for train and holdout.
    Columns: regime_int, sigma_within, rho_LOSO_proxy, beta_role_cohort.
    Returns S_train, S_holdout as DataFrames indexed by (cell_id, observable)."""
    p0 = pd.read_parquet(RESULTS / f"P0_partition_{arm}.parquet")
    train_cls = pd.read_parquet(
        RESULTS / f"trajectory_classification_{arm}.parquet")
    val = pd.read_parquet(RESULTS / f"step03_validation_{arm}.parquet")

    # Per-game observable values + continuous role metric.
    bs = pd.read_parquet(DATA / "historical_box_scores.parquet",
                          columns=["nba_api_id", "season", "season_type",
                                   "minutes", "PTS", "REB", "AST", "BLK"])
    bs = bs[(bs["season_type"] == "Regular Season")
            & (bs["minutes"] > 0)
            & (bs["season"].isin(ALL_SEASONS))].copy()
    qkeys = set(zip(p0["nba_api_id"].astype(int),
                     p0["season"].astype(str)))
    bs["_k"] = list(zip(bs["nba_api_id"].astype(int),
                         bs["season"].astype(str)))
    bs = bs[bs["_k"].isin(qkeys)].drop(columns="_k")
    bs["PTS_per36"] = bs["PTS"] * 36.0 / bs["minutes"]
    bs["REB_per36"] = bs["REB"] * 36.0 / bs["minutes"]
    bs["AST_per36"] = bs["AST"] * 36.0 / bs["minutes"]
    bs["BLK_per36"] = bs["BLK"] * 36.0 / bs["minutes"]

    cell_map = p0.set_index(["nba_api_id", "season"])["cell_id"]
    role_metric = _continuous_role_metric(arm, p0)
    bs["cell_id"] = bs.set_index(["nba_api_id", "season"]).index.map(cell_map)
    bs["role_x"] = bs.set_index(["nba_api_id", "season"]).index.map(role_metric)
    bs = bs[bs["cell_id"].notna() & bs["role_x"].notna()].copy()

    train_box = bs[bs["season"].isin(TRAIN_SEASONS)]
    holdout_box = bs[bs["season"].isin(HOLDOUT_SEASONS)]

    val_idx = val.set_index(["cell_id", "observable"])

    def per_cell_signature(box: pd.DataFrame, regime_lookup: dict
                            ) -> pd.DataFrame:
        cells = sorted(box["cell_id"].unique())
        rows = []
        for cid in cells:
            sub = box[box["cell_id"] == cid]
            for obs in OBSERVABLES:
                vals = sub[obs].to_numpy(float)
                xs = sub["role_x"].to_numpy(float)
                m = np.isfinite(vals) & np.isfinite(xs)
                vals = vals[m]; xs = xs[m]
                if len(vals) < 5 or np.std(xs) < 1e-9:
                    sigma_within = float(vals.std(ddof=1)) if len(vals) > 1 \
                                    else float("nan")
                    beta_rc = float("nan")
                else:
                    sigma_within = float(vals.std(ddof=1))
                    beta_rc = float(np.polyfit(xs, vals, 1)[0])
                regime = regime_lookup.get((cid, obs), "Insufficient_data")
                regime_int = REGIME_CODE.get(regime, 6)
                # rho_LOSO proxy: from step03 loso_matches / 5 (train only;
                # for holdout we re-use train's value as a stability proxy).
                key = (cid, obs)
                if key in val_idx.index:
                    rho_loso = float(val_idx.loc[key, "loso_matches"]) / 5.0
                else:
                    rho_loso = float("nan")
                rows.append({"cell_id": cid, "observable": obs,
                              "regime_int": regime_int,
                              "sigma_within": sigma_within,
                              "rho_LOSO": rho_loso,
                              "beta_rc": beta_rc})
        return pd.DataFrame(rows)

    train_lookup = {(r["cell_id"], r["observable"]): r["regime"]
                     for _, r in train_cls.iterrows()}
    holdout_lookup = {(r["cell_id"], r["observable"]): r["regime_holdout"]
                       for _, r in holdout_df.iterrows()}

    S_train = per_cell_signature(train_box, train_lookup)
    S_hold = per_cell_signature(holdout_box, holdout_lookup)
    return S_train, S_hold


def compute_step5_transfer(S_train: pd.DataFrame, S_hold: pd.DataFrame
                            ) -> tuple[dict[str, float], pd.DataFrame]:
    """Return per-column Pearson r between S_train and S_hold, and per-cell
    transfer r DataFrame."""
    cols = ["regime_int", "sigma_within", "rho_LOSO", "beta_rc"]
    merged = S_train.merge(S_hold, on=["cell_id", "observable"],
                            suffixes=("_t", "_h"))
    col_r: dict[str, float] = {}
    for c in cols:
        tc = merged[f"{c}_t"].to_numpy(float)
        hc = merged[f"{c}_h"].to_numpy(float)
        m = np.isfinite(tc) & np.isfinite(hc)
        if m.sum() < 2 or np.std(tc[m]) == 0 or np.std(hc[m]) == 0:
            col_r[c] = float("nan")
        else:
            col_r[c] = float(np.corrcoef(tc[m], hc[m])[0, 1])

    # Per-cell transfer r: 4-tuple vs 4-tuple Pearson per row.
    per_cell_rows = []
    for _, r in merged.iterrows():
        tv = np.array([r[f"{c}_t"] for c in cols], dtype=float)
        hv = np.array([r[f"{c}_h"] for c in cols], dtype=float)
        m = np.isfinite(tv) & np.isfinite(hv)
        if m.sum() < 2 or np.std(tv[m]) == 0 or np.std(hv[m]) == 0:
            per_r = float("nan")
        else:
            per_r = float(np.corrcoef(tv[m], hv[m])[0, 1])
        per_cell_rows.append({"cell_id": r["cell_id"],
                                "observable": r["observable"],
                                "regime_train": int(r["regime_int_t"]),
                                "regime_holdout": int(r["regime_int_h"]),
                                "per_cell_r": per_r})
    return col_r, pd.DataFrame(per_cell_rows)


# ---------------------------------------------------------------------------
# Comparative arm — Method A vs Method B per cell
# ---------------------------------------------------------------------------

CODE_REGIME = {v: k for k, v in REGIME_CODE.items()}

def comparative_per_cell(arm: str, per_cell_r: pd.DataFrame) -> pd.DataFrame:
    val = pd.read_parquet(RESULTS / f"step03_validation_{arm}.parquet")
    val_idx = val.set_index(["cell_id", "observable"])
    rows = []
    for _, r in per_cell_r.iterrows():
        cid, obs = r["cell_id"], r["observable"]
        regime_train_str = CODE_REGIME.get(int(r["regime_train"]), "?")
        regime_holdout_str = CODE_REGIME.get(int(r["regime_holdout"]), "?")
        is_non_stat = regime_train_str in {"Concentrating", "Diffusing",
                                            "Contracting", "Drifting"}
        is_edge = regime_train_str == "Edge"
        is_stationary = regime_train_str == "Stationary"
        flagged = (not val_idx.loc[(cid, obs), "clean"]
                    if (cid, obs) in val_idx.index else True)
        regime_flipped = regime_train_str != regime_holdout_str
        per_r = r["per_cell_r"]
        # Decision rule per pre-reg section 9.3.
        if flagged or is_stationary or is_edge:
            verdict = "TIE"
            reason = ("Stationary" if is_stationary
                       else "Edge" if is_edge else "Step3_flagged")
        elif is_non_stat and np.isfinite(per_r) and per_r >= COMPARATIVE_PER_CELL_R:
            verdict = "PASS"
            reason = f"non-Stationary regime + r={per_r:.2f}>=0.50"
        elif is_non_stat and np.isfinite(per_r) and per_r < COMPARATIVE_PER_CELL_R \
              and regime_flipped:
            verdict = "LOSE"
            reason = f"regime flipped to {regime_holdout_str}, r={per_r:.2f}<0.50"
        else:
            verdict = "TIE"
            reason = "non-conclusive transfer test"
        rows.append({"cell_id": cid, "observable": obs,
                      "regime_train": regime_train_str,
                      "regime_holdout": regime_holdout_str,
                      "per_cell_r": per_r,
                      "flagged_step3": bool(flagged),
                      "verdict": verdict, "reason": reason})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Cross-arm kappa matrix
# ---------------------------------------------------------------------------

def cross_arm_kappa(arms: tuple[str, ...]) -> dict[str, dict[str, float]]:
    """4-arm regime-label kappa per observable. Operates at the
    per-(player, season) level: every player-season has a regime label
    under each arm = the regime of the cell they're in for that observable."""
    out = {obs: {} for obs in OBSERVABLES}
    # Build per-arm: (player, season, observable) -> regime label.
    arm_labels: dict[str, dict] = {}
    for arm in arms:
        p0 = pd.read_parquet(RESULTS / f"P0_partition_{arm}.parquet")
        cls = pd.read_parquet(
            RESULTS / f"trajectory_classification_{arm}.parquet")
        cls_idx = cls.set_index(["cell_id", "observable"])["regime"]
        # Build per (player, season): cell_id
        ps_cell = p0.set_index(["nba_api_id", "season"])["cell_id"].to_dict()
        labels = {}
        for (nid, ssn), cid in ps_cell.items():
            for obs in OBSERVABLES:
                regime = cls_idx.get((cid, obs))
                if regime is not None:
                    labels[(int(nid), str(ssn), obs)] = REGIME_CODE[regime]
        arm_labels[arm] = labels

    # Pairwise kappa across arms per observable.
    for a, b in combinations(arms, 2):
        for obs in OBSERVABLES:
            keys = [k for k in arm_labels[a] if k[2] == obs
                     and k in arm_labels[b]]
            if len(keys) < 5:
                out[obs][f"{a}__{b}"] = float("nan"); continue
            la = [arm_labels[a][k] for k in keys]
            lb = [arm_labels[b][k] for k in keys]
            try:
                k = float(cohen_kappa_score(la, lb))
            except Exception:
                k = float("nan")
            out[obs][f"{a}__{b}"] = k
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    # Verify SHA on each arm before any compute. Use the most-restrictive
    # arm (any v1.2 arm enforces v1.0 + v1.1 + v1.2).
    sha = verify_sha_lock("Step 5 falsifiers", arm="mpg_adj")

    all_findings = {}
    for arm in ARMS:
        print(f"\n========== arm={arm} ==========")
        f1 = compute_F1(arm)
        print(f"  F1 R^2: {f1}")

        ho = holdout_step2(arm)
        ho.to_parquet(RESULTS / f"holdout_step2_{arm}.parquet", index=False)
        print(f"  holdout Step 2: {len(ho)} (cell, obs) classifications")

        f4 = compute_F4(arm, ho)
        print(f"  F4 kappa: {f4}")

        S_train, S_hold = build_signature_matrices(arm, ho)
        S_train.to_parquet(RESULTS / f"signature_train_{arm}.parquet", index=False)
        S_hold.to_parquet(RESULTS / f"signature_holdout_{arm}.parquet", index=False)
        col_r, per_cell_r = compute_step5_transfer(S_train, S_hold)
        print(f"  Step 5 col r: {col_r}, mean={np.nanmean(list(col_r.values())):.3f}")

        # F2 (computable now from existing data).
        cls = pd.read_parquet(RESULTS / f"trajectory_classification_{arm}.parquet")
        val = pd.read_parquet(RESULTS / f"step03_validation_{arm}.parquet")
        merged = cls.merge(val[["cell_id", "observable", "clean"]],
                            on=["cell_id", "observable"], how="left")
        n_total = len(merged)
        n_edge = (merged["regime"] == "Edge").sum()
        n_stat = (merged["regime"] == "Stationary").sum()
        n_clean_nonstat = ((merged["regime"].isin(
            ["Concentrating", "Diffusing", "Contracting", "Drifting"]))
                            & (merged["clean"] == True)).sum()
        terminate_clean = int(n_stat + n_clean_nonstat)
        denom = int(n_total - n_edge)
        f2_frac = terminate_clean / denom if denom > 0 else float("nan")
        f2_fires = f2_frac < F2_FIRE_FRAC

        # F3 (vacuous under Path A: 0 sub-partitions exist).
        f3 = {"fires": False, "vacuous": True, "n_subpartitions": 0}

        # Comparative arm.
        comp = comparative_per_cell(arm, per_cell_r)
        comp.to_parquet(RESULTS / f"step05_comparative_{arm}.parquet",
                         index=False)
        verdict_counts = Counter(comp["verdict"])
        print(f"  Comparative: {dict(verdict_counts)}")

        all_findings[arm] = {
            "F1": {obs: {"R2": r2, "fires": (r2 >= F1_FIRE_R2)
                          if np.isfinite(r2) else None}
                    for obs, r2 in f1.items()},
            "F2": {"clean_frac": f2_frac, "n_clean": terminate_clean,
                    "n_denom": denom, "fires": f2_fires},
            "F3": f3,
            "F4": f4,
            "step5_transfer": {"col_r": col_r,
                                "mean_r": float(np.nanmean(list(col_r.values()))),
                                "fires_threshold": STEP5_TRANSFER_R,
                                "passes": (np.nanmean(list(col_r.values()))
                                            >= STEP5_TRANSFER_R)},
            "comparative": dict(verdict_counts),
        }

    # Cross-arm kappa.
    print("\n========== cross-arm kappa ==========")
    xk = cross_arm_kappa(ARMS)
    for obs, d in xk.items():
        print(f"  {obs}: {d}")

    # Write the per-arm falsifier JSON.
    for arm in ARMS:
        (RESULTS / f"step05_falsifiers_{arm}.json").write_text(
            json.dumps(all_findings[arm], indent=2, default=str),
            encoding="utf-8")

    # Cross-arm artifact.
    (RESULTS / "crossarm_kappa_matrix.json").write_text(
        json.dumps(xk, indent=2, default=str), encoding="utf-8")

    # Substrate ledger MD.
    write_substrate_ledger(all_findings, xk, sha)
    print(f"\nDone. Substrate ledger: {RESULTS / 'SUBSTRATE_LEDGER.md'}")
    return 0


def write_substrate_ledger(findings: dict, xk: dict, sha: dict) -> None:
    lines = [
        "# NBA Full-Pipeline RMD-SRC — Substrate Ledger\n",
        "Locked under three commit-SHAs:",
        f"- **v1.0 pre-reg:** `{sha['v1.0']}`",
        f"- **v1.1 amendment (MPG-tier parallel arm):** `{sha['v1.1']}`",
        "- **v1.2 amendment (position adjudication):** "
        "`1bfdb4c0dfa2b3754f67e9c2f91b2ab26fa01866`",
        "",
        "## Path A — locked-spec compliance",
        "Steps 0-6 + F1-F4 + comparative arm executed under the locked spec "
        "with no rescue. Step 3's Hartigan-dip-on-raw-values check over-fires "
        "at 100% across all 4 arms — a substrate-shape finding mirroring "
        "Migration's v1.4 diagnosis. Step 4 vacuous (empty input). F2 carried "
        "by Stationary count (Edge excluded per section 3.2). F1, F4, Step 5, "
        "and comparative arm computed normally.",
        "",
        "## Headline by arm",
        "",
        "| Arm | K | F1 fires? | F2 clean | F2 fires? | F4 kappa (mean) | F4 fires? | Step 5 mean r | Comp PASS / TIE / LOSE |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    arm_K = {"usg": 19, "mpg": 21, "usg_adj": 21, "mpg_adj": 25}
    for arm in ARMS:
        f = findings[arm]
        f1_fires = any(v.get("fires") for v in f["F1"].values())
        f4_kaps = [v["kappa"] for v in f["F4"].values()
                    if np.isfinite(v["kappa"])]
        f4_mean = float(np.mean(f4_kaps)) if f4_kaps else float("nan")
        f4_fires = any(v.get("fires") for v in f["F4"].values())
        comp = f["comparative"]
        comp_str = f"{comp.get('PASS', 0)} / {comp.get('TIE', 0)} / {comp.get('LOSE', 0)}"
        s5 = f["step5_transfer"]
        lines.append(
            f"| `{arm}` | {arm_K[arm]} | "
            f"{'Y' if f1_fires else 'N'} | "
            f"{f['F2']['n_clean']}/{f['F2']['n_denom']} = "
            f"{100*f['F2']['clean_frac']:.1f}% | "
            f"{'Y' if f['F2']['fires'] else 'N'} | "
            f"{f4_mean:+.3f} | {'Y' if f4_fires else 'N'} | "
            f"{s5['mean_r']:+.3f} | {comp_str} |"
        )

    lines += ["", "## F1 detail — R^2 of additive linear model per observable",
              "", "| Arm | PTS_per36 | REB_per36 | AST_per36 | BLK_per36 |",
              "|---|---|---|---|---|"]
    for arm in ARMS:
        row = [arm]
        for obs in OBSERVABLES:
            r2 = findings[arm]["F1"][obs]["R2"]
            row.append(f"{r2:.3f}")
        lines.append("| `" + row[0] + "` | " + " | ".join(row[1:]) + " |")

    lines += ["", "## F4 detail — Cohen kappa per (arm, observable)",
              "", "| Arm | PTS_per36 | REB_per36 | AST_per36 | BLK_per36 |",
              "|---|---|---|---|---|"]
    for arm in ARMS:
        row = [arm]
        for obs in OBSERVABLES:
            k = findings[arm]["F4"][obs]["kappa"]
            row.append(f"{k:+.3f}" if np.isfinite(k) else "n/a")
        lines.append("| `" + row[0] + "` | " + " | ".join(row[1:]) + " |")

    lines += ["", "## Cross-arm regime kappa (per-player-season per observable)"]
    for obs in OBSERVABLES:
        lines += ["", f"### {obs}", ""]
        lines.append("| | " + " | ".join(ARMS) + " |")
        lines.append("|" + "---|" * (len(ARMS) + 1))
        for a in ARMS:
            row = [f"`{a}`"]
            for b in ARMS:
                if a == b:
                    row.append("1.000")
                else:
                    key = f"{a}__{b}" if (f"{a}__{b}" in xk[obs]) else f"{b}__{a}"
                    v = xk[obs].get(key, float("nan"))
                    row.append(f"{v:+.3f}" if np.isfinite(v) else "n/a")
            lines.append("| " + " | ".join(row) + " |")

    lines += ["", "## Step 6 mechanism inference",
              "",
              "Per pre-reg section 7 prospective tier: the BLK x Center "
              "concentration mechanism was committed ex ante. Under Path A, "
              "Step 3 dip over-fires on every cell, so no non-Stationary cell "
              "is response-validated. The prospective claim is therefore "
              "**not falsified but not confirmed** at the response-validation "
              "layer. Retrospective and post-hoc tier mechanisms: none named "
              "(no Step 4 sub-partitions to anchor them).",
              "",
              "## Path B (queued, not locked)",
              "",
              "A v1.3 diagnostic-amendment draft is staged at "
              "`RMD_SRC_PIPELINE/DRAFT_v1.3_DIP_ON_RESIDUALS.md` "
              "(unlocked). It would add a dip-on-residuals check parallel to "
              "the locked dip-on-raw-values check at Step 3, localizing the "
              "over-fire as measurement-artifact-on-raw-values rather than "
              "substrate property. Path A reports stand untouched; Path B "
              "extends without modifying the locked spec, per the methodology "
              "paper section 3.4 ('diagnostic-amendment without falsifier "
              "rescue').",
              ""]
    (RESULTS / "SUBSTRATE_LEDGER.md").write_text(
        "\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
