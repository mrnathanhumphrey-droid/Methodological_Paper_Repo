"""
RMD-SRC NBA — Step 5/6 + falsifiers + comparatives, SPATIAL re-axis arms.

Locked under spatial pre-reg cd40b46. Runs F1-F4 + Step5 transfer + the
vs-v6.1 comparative for off_feast & def_feast, ADDS the §9.2 vs-position
comparative (delta F2 / delta F4 kappa / delta dip-pass against the locked
usg position arm), and adjudicates the three timestamped predictions P1/P2/P3.

Reuses the locked step05 computation functions verbatim (holdout_step2,
compute_F4, build_signature_matrices, compute_step5_transfer,
comparative_per_cell) so the Step-5 logic is byte-identical to v1.0; only
(a) F1 uses `region` instead of pos_bucket, (b) the continuous role metric is
prior_usg (spatial role-cohort = usage-tier), (c) outputs go to a SEPARATE
spatial ledger (the committed position SUBSTRATE_LEDGER.md is NOT touched).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, str(Path(__file__).parent))
from _common import OBSERVABLES, RESULTS, TRAIN_SEASONS
import step05_falsifiers_and_comparative as s5
from step02_classify_trajectories import load_observables

DATA = Path(r"D:/NBA Projections/data/parquet")
SPATIAL_ARMS = ("off_feast", "def_feast")
POSITION_BASELINE = "usg"

F1_FIRE_R2 = s5.F1_FIRE_R2
F2_FIRE_FRAC = s5.F2_FIRE_FRAC
F4_FIRE_KAPPA = s5.F4_FIRE_KAPPA
STEP5_TRANSFER_R = s5.STEP5_TRANSFER_R

# Spatial arms use usage-tier role-cohort -> continuous metric is prior_usg.
s5._continuous_role_metric = (
    lambda arm, p0: p0.set_index(["nba_api_id", "season"])["prior_usg"])


def compute_F1_region(arm: str) -> dict[str, float]:
    """F1 additive-model R^2 using the SPATIAL partition variable `region`
    (+ yp + rc + season) instead of pos_bucket."""
    p0 = pd.read_parquet(RESULTS / f"P0_partition_{arm}.parquet")
    p0 = p0[p0["cell_id"] != "Profile-Sparse"]
    box = load_observables(p0)
    cmap = p0.set_index(["nba_api_id", "season"])[["region", "yp_bucket", "rc_bucket"]]
    keys = list(zip(box["nba_api_id"].astype(int), box["season"].astype(str)))
    box[["region", "yp", "rc"]] = pd.DataFrame(
        [cmap.loc[k].tolist() if k in cmap.index else [None, None, None]
         for k in keys], index=box.index, columns=["region", "yp", "rc"])
    box = box.dropna(subset=["region", "yp", "rc"]).copy()
    enc = OneHotEncoder(sparse_output=False, drop="first")
    X = enc.fit_transform(box[["region", "yp", "rc", "season"]])
    out = {}
    for obs in OBSERVABLES:
        y = box[obs].to_numpy(float)
        m = np.isfinite(y)
        out[obs] = (float(LinearRegression().fit(X[m], y[m]).score(X[m], y[m]))
                    if m.sum() >= 100 else float("nan"))
    return out


def compute_F2(arm: str) -> dict:
    cls = pd.read_parquet(RESULTS / f"trajectory_classification_{arm}.parquet")
    val = pd.read_parquet(RESULTS / f"step03_validation_{arm}.parquet")
    m = cls.merge(val[["cell_id", "observable", "clean"]],
                  on=["cell_id", "observable"], how="left")
    n_edge = (m["regime"] == "Edge").sum()
    n_stat = (m["regime"] == "Stationary").sum()
    n_clean_ns = ((m["regime"].isin(["Concentrating", "Diffusing",
                                      "Contracting", "Drifting"]))
                  & (m["clean"] == True)).sum()
    clean = int(n_stat + n_clean_ns)
    denom = int(len(m) - n_edge)
    frac = clean / denom if denom else float("nan")
    return {"clean_frac": frac, "n_clean": clean, "n_denom": denom,
            "fires": frac < F2_FIRE_FRAC}


def dip_pass_frac(arm: str) -> float:
    v = pd.read_parquet(RESULTS / f"step03_validation_{arm}.parquet")
    return float(v["dip_pass"].mean())


def run_arm(arm: str, f1_fn) -> dict:
    print(f"\n========== {arm} ==========")
    f1 = f1_fn(arm)
    ho = s5.holdout_step2(arm)
    ho.to_parquet(RESULTS / f"holdout_step2_{arm}.parquet", index=False)
    f4 = s5.compute_F4(arm, ho)
    S_tr, S_ho = s5.build_signature_matrices(arm, ho)
    S_tr.to_parquet(RESULTS / f"signature_train_{arm}.parquet", index=False)
    S_ho.to_parquet(RESULTS / f"signature_holdout_{arm}.parquet", index=False)
    col_r, per_cell_r = s5.compute_step5_transfer(S_tr, S_ho)
    f2 = compute_F2(arm)
    comp = s5.comparative_per_cell(arm, per_cell_r)
    comp.to_parquet(RESULTS / f"step05_comparative_{arm}.parquet", index=False)
    f4_kaps = [v["kappa"] for v in f4.values() if np.isfinite(v["kappa"])]
    rec = {
        "arm": arm, "K": int(pd.read_parquet(
            RESULTS / f"trajectory_classification_{arm}.parquet")["cell_id"].nunique()),
        "F1": {o: {"R2": r, "fires": (r >= F1_FIRE_R2) if np.isfinite(r) else None}
               for o, r in f1.items()},
        "F2": f2,
        "F4": f4, "F4_mean_kappa": float(np.mean(f4_kaps)) if f4_kaps else float("nan"),
        "F4_any_clears_040": any(np.isfinite(v["kappa"]) and v["kappa"] >= 0.40
                                 for v in f4.values()),
        "step5_mean_r": float(np.nanmean(list(col_r.values()))),
        "step5_col_r": col_r,
        "dip_pass_frac": dip_pass_frac(arm),
        "comparative_v61": dict(Counter(comp["verdict"])),
    }
    print(f"  F1 R2: { {o: round(v['R2'],3) for o,v in rec['F1'].items()} }")
    print(f"  F2 clean: {f2['n_clean']}/{f2['n_denom']} = {100*f2['clean_frac']:.1f}%  fires={f2['fires']}")
    print(f"  F4 kappa: { {o: round(v['kappa'],3) for o,v in f4.items()} }  mean={rec['F4_mean_kappa']:+.3f}")
    print(f"  F4 any obs >= 0.40: {rec['F4_any_clears_040']}")
    print(f"  Step5 mean r: {rec['step5_mean_r']:+.3f}")
    print(f"  Comparative vs v6.1: {rec['comparative_v61']}")
    return rec


def main() -> int:
    txt = (RESULTS.parent / "SHA_LOCK.txt").read_text(encoding="utf-8")
    if "## spatial re-axis" not in txt or "cd40b46" not in txt:
        sys.exit("[Step 5 spatial] lock SHA not found.")
    print("[Step 5 spatial] discipline gate OK — cd40b46")

    recs = {a: run_arm(a, compute_F1_region) for a in SPATIAL_ARMS}
    # position baseline recomputed on identical data (F1 uses pos_bucket).
    recs[POSITION_BASELINE] = run_arm(POSITION_BASELINE, s5.compute_F1)

    # ---- §9.2 vs-position comparative (delta vs usg) ----
    base = recs[POSITION_BASELINE]
    vs_pos = {}
    for a in SPATIAL_ARMS:
        d = {
            "delta_F2_clean_frac": recs[a]["F2"]["clean_frac"] - base["F2"]["clean_frac"],
            "delta_F4_mean_kappa": recs[a]["F4_mean_kappa"] - base["F4_mean_kappa"],
            "delta_dip_pass": recs[a]["dip_pass_frac"] - base["dip_pass_frac"],
            "spatial_F4_any_clears_040": recs[a]["F4_any_clears_040"],
            "position_F4_any_clears_040": base["F4_any_clears_040"],
        }
        if d["delta_F4_mean_kappa"] > 0 and recs[a]["F4_any_clears_040"]:
            d["disposition"] = "spatial-dominant"
        elif abs(d["delta_F4_mean_kappa"]) < 0.05 and abs(d["delta_F2_clean_frac"]) < 0.05:
            d["disposition"] = "parity"
        else:
            d["disposition"] = ("spatial-dominant" if d["delta_F4_mean_kappa"] > 0
                                else "position-dominant")
        vs_pos[a] = d
        (RESULTS / f"comparative_vs_position_{a}.json").write_text(
            json.dumps(d, indent=2, default=str), encoding="utf-8")

    # ---- cross-arm kappa: off_feast vs def_feast ----
    s5.ARMS = SPATIAL_ARMS  # restrict cross-arm to the two spatial arms
    xk = s5.cross_arm_kappa(SPATIAL_ARMS)

    # ---- P1 / P2 / P3 verdicts ----
    p1 = recs["off_feast"]["F4_any_clears_040"]
    # P2: BLK transfer + RimProtector tightening in def_feast
    def_blk_k = recs["def_feast"]["F4"]["BLK_per36"]["kappa"]
    cls_def = pd.read_parquet(RESULTS / "trajectory_classification_def_feast.parquet")
    rim_blk = cls_def[(cls_def.observable == "BLK_per36")
                      & (cls_def.cell_id.str.startswith("RimProtector"))]
    rim_tightening = (rim_blk["regime"].isin(["Concentrating", "Contracting"])).any()
    p2 = bool(rim_tightening)
    # P3: off cleaner than def on F2-clean AND mean-F4-kappa
    p3 = (recs["off_feast"]["F2"]["clean_frac"] > recs["def_feast"]["F2"]["clean_frac"]
          and recs["off_feast"]["F4_mean_kappa"] > recs["def_feast"]["F4_mean_kappa"])
    verdicts = {
        "P1_court_region_transfers": {"prediction": "off_feast F4 kappa>=0.40 on >=1 obs (position failed ~0)",
                                      "calibration": 0.60,
                                      "off_feast_F4_per_obs": {o: v["kappa"] for o, v in recs["off_feast"]["F4"].items()},
                                      "position_usg_F4_mean": base["F4_mean_kappa"],
                                      "HIT": bool(p1)},
        "P2_BLK_relocates_to_rim": {"prediction": "BLK x RimProtector tightens (Concentrating/Contracting) + transfers",
                                    "calibration": 0.55,
                                    "rim_blk_regimes": rim_blk[["cell_id", "regime"]].to_dict("records"),
                                    "def_BLK_F4_kappa": def_blk_k,
                                    "HIT_tightening": bool(p2)},
        "P3_offense_clean_defense_coupled": {"prediction": "off_feast beats def_feast on F2-clean AND mean-F4-kappa",
                                             "calibration": 0.65,
                                             "off_F2": recs["off_feast"]["F2"]["clean_frac"],
                                             "def_F2": recs["def_feast"]["F2"]["clean_frac"],
                                             "off_F4_mean": recs["off_feast"]["F4_mean_kappa"],
                                             "def_F4_mean": recs["def_feast"]["F4_mean_kappa"],
                                             "HIT": bool(p3)},
    }

    for a in SPATIAL_ARMS:
        (RESULTS / f"step05_falsifiers_{a}.json").write_text(
            json.dumps(recs[a], indent=2, default=str), encoding="utf-8")
    (RESULTS / "spatial_vs_position_comparative.json").write_text(
        json.dumps(vs_pos, indent=2, default=str), encoding="utf-8")
    (RESULTS / "spatial_predictions_verdict.json").write_text(
        json.dumps(verdicts, indent=2, default=str), encoding="utf-8")

    write_spatial_ledger(recs, vs_pos, xk, verdicts)
    print("\n===== PREDICTION VERDICTS =====")
    print(f"  P1 (court-region transfers, F4>=0.40): {'HIT' if p1 else 'MISS'}")
    print(f"  P2 (BLK tightens in RimProtector):     {'HIT' if p2 else 'MISS'}")
    print(f"  P3 (offense clean / defense coupled):  {'HIT' if p3 else 'MISS'}")
    print(f"\nSpatial ledger: {RESULTS / 'SUBSTRATE_LEDGER_SPATIAL.md'}")
    return 0


def write_spatial_ledger(recs, vs_pos, xk, verdicts) -> None:
    L = ["# NBA RMD-SRC SPATIAL re-axis — Substrate Ledger\n",
         "Locked under spatial pre-reg SHA `cd40b46`. Does NOT modify the "
         "position-arm `SUBSTRATE_LEDGER.md`.\n",
         "## Headline by arm",
         "| Arm | K | F1 fires? | F2 clean | F2 fires? | F4 mean κ | F4 any≥0.40? | Step5 mean r | Comp vs v6.1 (P/T/L) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for a in ("off_feast", "def_feast", "usg"):
        r = recs[a]
        f1f = any(v.get("fires") for v in r["F1"].values())
        c = r["comparative_v61"]
        L.append(f"| `{a}` | {r['K']} | {'Y' if f1f else 'N'} | "
                 f"{r['F2']['n_clean']}/{r['F2']['n_denom']} = {100*r['F2']['clean_frac']:.1f}% | "
                 f"{'Y' if r['F2']['fires'] else 'N'} | {r['F4_mean_kappa']:+.3f} | "
                 f"{'Y' if r['F4_any_clears_040'] else 'N'} | {r['step5_mean_r']:+.3f} | "
                 f"{c.get('PASS',0)}/{c.get('TIE',0)}/{c.get('LOSE',0)} |")
    L += ["", "## F4 detail — Cohen κ per (arm, observable)",
          "| Arm | PTS | REB | AST | BLK |", "|---|---|---|---|---|"]
    for a in ("off_feast", "def_feast", "usg"):
        row = [a] + [f"{recs[a]['F4'][o]['kappa']:+.3f}" if np.isfinite(recs[a]['F4'][o]['kappa']) else "n/a"
                     for o in OBSERVABLES]
        L.append("| `" + row[0] + "` | " + " | ".join(row[1:]) + " |")
    L += ["", "## §9.2 — spatial vs position (usg) comparative",
          "| Arm | ΔF2-clean | ΔF4-mean-κ | Δdip-pass | disposition |",
          "|---|---|---|---|---|"]
    for a in SPATIAL_ARMS:
        d = vs_pos[a]
        L.append(f"| `{a}` | {d['delta_F2_clean_frac']:+.3f} | {d['delta_F4_mean_kappa']:+.3f} | "
                 f"{d['delta_dip_pass']:+.3f} | {d['disposition']} |")
    L += ["", "## Cross-arm regime κ (off_feast vs def_feast), per observable", ""]
    for o in OBSERVABLES:
        k = xk[o].get("off_feast__def_feast", float("nan"))
        L.append(f"- {o}: κ = {k:+.3f}" if np.isfinite(k) else f"- {o}: n/a")
    L += ["", "## Prediction verdicts (timestamped 2026-06-10)"]
    for k, v in verdicts.items():
        hit = v.get("HIT", v.get("HIT_tightening"))
        L.append(f"- **{k}** (cal {v['calibration']}): **{'HIT' if hit else 'MISS'}** — {v['prediction']}")
    (RESULTS / "SUBSTRATE_LEDGER_SPATIAL.md").write_text("\n".join(L) + "\n",
                                                         encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
