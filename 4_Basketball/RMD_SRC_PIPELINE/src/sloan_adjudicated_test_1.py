"""
Sloan adjudicated Test 1 re-validation — analysis script.

Locked under SLOAN_PRE_REG_TEST_1_ADJUDICATED_v1.0_LOCKED.md (commit e52505f).
Cross-paper anchors:
  - RMD-SRC v1.2 amendment (adjudication artifact): commit 1bfdb4c
  - Adjudication verdicts SHA256: eb615269f09159e0d0ceaf071812b84750578d81a9a53b01dff5a1ac2ac9dcbd
  - v6.1 LOCKED residual artifacts: May 2026 audit-run CSVs (locked paths below)

Computes per-cell variance ratios on per-player residuals for three NBA cells
(23-24, 24-25, 25-26) x three observables (BLK, PTS, REB) under TWO bucketing
arms in parallel:
  - METADATA bucket (control, exactly replicates cross-league paper section 5.5)
  - ADJUDICATED bucket (load-bearing, v1.2 verdicts override metadata for 230
                       players)

Applies per-cell decision rules from pre-reg section 3 and emits the locked
artifact set under RMD_SRC_PIPELINE/results/sloan_adjudicated/.

Single fire per pre-reg section 7. No re-runs after seeing results.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from _common import PIPE_ROOT, RESULTS

REPO = Path(r"D:/NBA Projections")
PQ = REPO / "data" / "parquet"
SLOAN_OUT = RESULTS / "sloan_adjudicated"
SLOAN_OUT.mkdir(parents=True, exist_ok=True)

# Locked input artifacts.
ADJ_VERDICTS = RESULTS / "position_adjudication_v12.json"
SHIP_25_26 = REPO / "audit_runs" / "unified_ship_v6_1_2025_26" / \
              "per_player_projections_2025-26.csv"
ROOKIE_SUP = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / \
              "rookie_metadata_supplement.parquet"

# Per (stat, season) -> Stan backtest CSV (May 2026 canonical run).
STAN_BACKTEST = {
    ("BLK", "2023-24"): "audit_runs/20260506T150621Z/skill_backtest_BLK_phase4_v4_quadratic_tq_g_2017-18-2018-19-2019-20-2020-21-2021-22-2022-23__2023-24/per_player_projections.csv",
    ("BLK", "2024-25"): "audit_runs/20260506T140025Z/skill_backtest_BLK_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/per_player_projections.csv",
    ("PTS", "2023-24"): "audit_runs/20260505T211540Z/skill_backtest_PTS_phase4_v4_quadratic_tq_g_2017-18-2018-19-2019-20-2020-21-2021-22-2022-23__2023-24/per_player_projections.csv",
    ("PTS", "2024-25"): "audit_runs/20260505T154737Z/skill_backtest_PTS_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/per_player_projections.csv",
    ("REB", "2023-24"): "audit_runs/20260505T225045Z/skill_backtest_REB_phase4_v4_quadratic_tq_g_2017-18-2018-19-2019-20-2020-21-2021-22-2022-23__2023-24/per_player_projections.csv",
    ("REB", "2024-25"): "audit_runs/20260505T171359Z/skill_backtest_REB_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/per_player_projections.csv",
}

STATS = ("BLK", "PTS", "REB")
SEASONS = ("2023-24", "2024-25", "2025-26")

# Locked decision-rule reference bands (pre-reg section 3).
BLK_RANGE = (1.26, 2.03)
PTS_RANGE = (0.76, 1.02)
POWER_LIFT = 1.30
ALPHA = 0.05
BOOTSTRAP_B = 1000
SEED = 20260601


def position_class_metadata(p) -> str:
    """Inclusive Test 1 classifier matching cross-league paper section 2.5."""
    if pd.isna(p) or not p or str(p).strip() == "":
        return "Forward"  # catch-all per existing script default
    s = str(p).lower()
    if "center" in s:
        return "Center"
    if "guard" in s:
        return "Guard"
    return "Forward"


def load_meta_and_adj() -> tuple[pd.DataFrame, dict]:
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    if ROOKIE_SUP.exists():
        sup = pd.read_parquet(ROOKIE_SUP)
        cols = ["nba_api_id", "name", "position", "draft_year", "debut_year"]
        meta = pd.concat([meta[cols], sup[cols]], ignore_index=True)
    meta["nba_api_id"] = meta["nba_api_id"].astype(int)
    meta["pos_meta"] = meta["position"].apply(position_class_metadata)

    verdicts = json.loads(ADJ_VERDICTS.read_text(encoding="utf-8"))["verdicts"]
    adj_map = {int(v["nba_api_id"]): v["adjudicated_bucket"] for v in verdicts}
    return meta, adj_map


def load_25_26_residuals(stat: str, bx_2526: pd.DataFrame
                          ) -> pd.DataFrame:
    """Match the existing test_1_blk_center protocol: ship per-game projection
    minus box-score per-game actual."""
    ship = pd.read_csv(SHIP_25_26)
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    actuals = bx_2526.groupby("nba_api_id").agg(
        actual=(stat, "mean")).reset_index()

    rookie_real_id: dict[int, int] = {}
    if ROOKIE_SUP.exists():
        sup = pd.read_parquet(ROOKIE_SUP)
        meta_base = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
        real_name_id = dict(zip(meta_base["name"].str.lower().fillna(""),
                                  meta_base["nba_api_id"].astype(int)))
        for _, r in sup.iterrows():
            nm = (r["name"] or "").strip().lower()
            if nm in real_name_id:
                rookie_real_id[int(r["nba_api_id"])] = real_name_id[nm]

    ship["real_id"] = ship["nba_api_id"].map(
        lambda x: rookie_real_id.get(int(x), int(x))).astype(int)

    proj_col = f"{stat}_per_game"
    stale_actuals = [c for c in ship.columns if c.endswith("_actual")]
    ship = ship.drop(columns=stale_actuals, errors="ignore")
    df = ship.merge(actuals, left_on="real_id", right_on="nba_api_id",
                     how="left", suffixes=("", "_act"))
    df["resid"] = df["actual"] - df[proj_col]
    df["nba_api_id_for_meta"] = df["real_id"].astype(int)
    return df[["nba_api_id_for_meta", "resid"]].rename(
        columns={"nba_api_id_for_meta": "nba_api_id"})


def load_stan_backtest_residuals(stat: str, season: str) -> pd.DataFrame:
    path = REPO / STAN_BACKTEST[(stat, season)]
    df = pd.read_csv(path)
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    df["resid"] = df["actual"] - df["proj_mean"]
    return df[["nba_api_id", "resid"]]


def attach_buckets(df: pd.DataFrame, meta: pd.DataFrame,
                    adj_map: dict) -> pd.DataFrame:
    meta_lookup = meta.set_index("nba_api_id")["pos_meta"].to_dict()
    df = df.copy()
    df["pos_meta"] = df["nba_api_id"].map(meta_lookup).fillna("Forward")
    df["pos_adj"] = df["nba_api_id"].apply(
        lambda i: adj_map.get(int(i), meta_lookup.get(int(i), "Forward")))
    df["in_meta"] = df["pos_meta"] == "Center"
    df["in_adj"] = df["pos_adj"] == "Center"
    return df


def variance_ratio_with_ci(r_in: np.ndarray, r_out: np.ndarray,
                            B: int = BOOTSTRAP_B, seed: int = SEED
                            ) -> dict:
    if len(r_in) < 5 or len(r_out) < 5:
        return {"n_in": len(r_in), "n_out": len(r_out),
                 "sd_in": float("nan"), "sd_out": float("nan"),
                 "ratio": float("nan"),
                 "ci_lo": float("nan"), "ci_hi": float("nan"),
                 "p_levene": float("nan"), "p_bartlett": float("nan"),
                 "p_F": float("nan")}
    sd_in = float(np.std(r_in, ddof=1))
    sd_out = float(np.std(r_out, ddof=1))
    ratio = sd_in / sd_out if sd_out > 0 else float("nan")

    rng = np.random.default_rng(seed)
    boots = np.empty(B, dtype=float)
    for b in range(B):
        rin_b = rng.choice(r_in, size=len(r_in), replace=True)
        rout_b = rng.choice(r_out, size=len(r_out), replace=True)
        s_in = np.std(rin_b, ddof=1)
        s_out = np.std(rout_b, ddof=1)
        boots[b] = s_in / s_out if s_out > 0 else np.nan
    boots = boots[np.isfinite(boots)]
    ci_lo, ci_hi = (float(np.quantile(boots, 0.025)),
                     float(np.quantile(boots, 0.975))) if len(boots) > 0 \
                    else (float("nan"), float("nan"))

    try:
        _, p_lev = stats.levene(r_in, r_out, center="median")
        p_lev = float(p_lev)
    except Exception:
        p_lev = float("nan")
    try:
        _, p_bart = stats.bartlett(r_in, r_out)
        p_bart = float(p_bart)
    except Exception:
        p_bart = float("nan")
    try:
        F = (sd_in ** 2) / (sd_out ** 2) if sd_out > 0 else float("nan")
        cdf = stats.f.cdf(F, len(r_in) - 1, len(r_out) - 1)
        p_F = float(2 * min(cdf, 1 - cdf))
    except Exception:
        p_F = float("nan")

    return {"n_in": int(len(r_in)), "n_out": int(len(r_out)),
             "sd_in": sd_in, "sd_out": sd_out, "ratio": float(ratio),
             "ci_lo": ci_lo, "ci_hi": ci_hi,
             "p_levene": p_lev, "p_bartlett": p_bart, "p_F": p_F}


# ---------------------------------------------------------------------------
# Decision rules (pre-reg section 3, locked)
# ---------------------------------------------------------------------------

def overlaps(ci_lo: float, ci_hi: float, lo: float, hi: float) -> bool:
    """Does [ci_lo, ci_hi] overlap [lo, hi]?"""
    return not (ci_hi < lo or ci_lo > hi)


def brackets_one(ci_lo: float, ci_hi: float) -> bool:
    return ci_lo < 1.0 < ci_hi


def disposition_BLK(adj: dict, power_pass: bool) -> str:
    if not power_pass:
        return "INCONCLUSIVE (power-limited)"
    lo, hi = adj["ci_lo"], adj["ci_hi"]
    p = adj["p_levene"]
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return "INCONCLUSIVE (CI undefined)"
    if hi < 1.0:
        return "INVERTED"
    if brackets_one(lo, hi):
        return "REGIME-NULL"
    if overlaps(lo, hi, *BLK_RANGE) and p < ALPHA:
        return "PERSISTS"
    if overlaps(lo, hi, *BLK_RANGE) and p >= ALPHA:
        return "PERSISTS-DIRECTIONAL"
    if lo > 1.0 and hi < BLK_RANGE[0] and p < ALPHA:
        return "ATTENUATES"
    return "MIXED-or-EDGE"


def disposition_PTS(adj: dict, power_pass: bool) -> str:
    if not power_pass:
        return "INCONCLUSIVE (power-limited)"
    lo, hi = adj["ci_lo"], adj["ci_hi"]
    ratio = adj["ratio"]
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return "INCONCLUSIVE (CI undefined)"
    if lo > 1.0:
        return "INVERTED"
    if brackets_one(lo, hi):
        return "NULL"
    if overlaps(lo, hi, *PTS_RANGE) and ratio < 1.0:
        return "DIRECTIONAL-PERSISTS"
    return "MIXED-or-EDGE"


def disposition_REB(adj: dict, power_pass: bool) -> str:
    if not power_pass:
        return "INCONCLUSIVE (power-limited)"
    lo, hi = adj["ci_lo"], adj["ci_hi"]
    p = adj["p_levene"]
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return "INCONCLUSIVE (CI undefined)"
    if hi < 1.0:
        return "WALK-BACK FALSIFIED-INVERTED"
    if lo > 1.0 and p < ALPHA:
        return "WALK-BACK FALSIFIED"
    if brackets_one(lo, hi) and p >= ALPHA:
        return "WALK-BACK UPHELD"
    return "MIXED-or-EDGE"


DISPOSITION_FN = {"BLK": disposition_BLK, "PTS": disposition_PTS,
                  "REB": disposition_REB}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print(f"Sloan adjudicated Test 1 — single fire under pre-reg e52505f")
    print(f"Adjudication artifact SHA256 anchor: eb615269...")
    print()

    meta, adj_map = load_meta_and_adj()
    print(f"loaded metadata rows: {len(meta):,}")
    print(f"loaded adjudication verdicts: {len(adj_map)}")

    # 25-26 box scores (once).
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx_2526 = bx[(bx["season"] == "2025-26") &
                   (bx["season_type"] == "Regular Season")].copy()
    bx_2526["minutes"] = pd.to_numeric(bx_2526["minutes"], errors="coerce")
    bx_2526 = bx_2526[bx_2526["minutes"] > 0]
    bx_2526["nba_api_id"] = bx_2526["nba_api_id"].astype(int)

    rows: list[dict] = []
    for stat in STATS:
        for season in SEASONS:
            if season == "2025-26":
                df = load_25_26_residuals(stat, bx_2526)
            else:
                df = load_stan_backtest_residuals(stat, season)
            df = df[df["resid"].notna()].copy()
            df = attach_buckets(df, meta, adj_map)
            r_in_meta = df.loc[df["in_meta"], "resid"].to_numpy()
            r_out_meta = df.loc[~df["in_meta"], "resid"].to_numpy()
            r_in_adj = df.loc[df["in_adj"], "resid"].to_numpy()
            r_out_adj = df.loc[~df["in_adj"], "resid"].to_numpy()

            meta_stats = variance_ratio_with_ci(r_in_meta, r_out_meta)
            adj_stats = variance_ratio_with_ci(r_in_adj, r_out_adj)

            n_in_meta = meta_stats["n_in"]
            n_in_adj = adj_stats["n_in"]
            lift = n_in_adj / n_in_meta if n_in_meta else float("nan")
            power_pass = lift >= POWER_LIFT

            disp = DISPOSITION_FN[stat](adj_stats, power_pass)

            row = {"stat": stat, "season": season,
                    "n_in_meta": n_in_meta, "n_out_meta": meta_stats["n_out"],
                    "n_in_adj": n_in_adj, "n_out_adj": adj_stats["n_out"],
                    "lift": lift, "power_pass": power_pass,
                    "meta_ratio": meta_stats["ratio"],
                    "meta_ci_lo": meta_stats["ci_lo"],
                    "meta_ci_hi": meta_stats["ci_hi"],
                    "meta_p_levene": meta_stats["p_levene"],
                    "adj_ratio": adj_stats["ratio"],
                    "adj_ci_lo": adj_stats["ci_lo"],
                    "adj_ci_hi": adj_stats["ci_hi"],
                    "adj_p_levene": adj_stats["p_levene"],
                    "adj_p_bartlett": adj_stats["p_bartlett"],
                    "adj_p_F": adj_stats["p_F"],
                    "disposition": disp}
            rows.append(row)
            print(f"  {stat} {season}: n_meta={n_in_meta}, n_adj={n_in_adj}, "
                  f"lift={lift:.2f}, ratio_meta={meta_stats['ratio']:.3f}, "
                  f"ratio_adj={adj_stats['ratio']:.3f}, "
                  f"CI_adj=[{adj_stats['ci_lo']:.3f}, {adj_stats['ci_hi']:.3f}], "
                  f"p_levene_adj={adj_stats['p_levene']:.4f} -> {disp}")

    out = pd.DataFrame(rows)
    out.to_parquet(SLOAN_OUT / "per_cell_results.parquet", index=False)

    # Locked pre-reg artifacts.
    (SLOAN_OUT / "n_in_lift_table.parquet").write_bytes(
        out[["stat", "season", "n_in_meta", "n_in_adj", "lift",
              "power_pass"]].to_parquet(index=False))
    (SLOAN_OUT / "variance_ratios_metadata.parquet").write_bytes(
        out[["stat", "season", "n_in_meta", "n_out_meta", "meta_ratio",
              "meta_ci_lo", "meta_ci_hi", "meta_p_levene"]].to_parquet(
            index=False))
    (SLOAN_OUT / "variance_ratios_adjudicated.parquet").write_bytes(
        out[["stat", "season", "n_in_adj", "n_out_adj", "adj_ratio",
              "adj_ci_lo", "adj_ci_hi", "adj_p_levene", "adj_p_bartlett",
              "adj_p_F"]].to_parquet(index=False))

    dispositions = {f"{r['stat']}__{r['season']}": r["disposition"]
                     for _, r in out.iterrows()}
    (SLOAN_OUT / "dispositions.json").write_text(
        json.dumps(dispositions, indent=2), encoding="utf-8")

    write_aggregate_report(out)
    write_results_md(out)
    print(f"\nDone. Reports under {SLOAN_OUT.relative_to(PIPE_ROOT)}/")
    return 0


def aggregate_verdict_per_stat(rows_for_stat: pd.DataFrame) -> str:
    disps = rows_for_stat["disposition"].tolist()
    if all("PERSISTS" in d for d in disps):
        return "3/3 PERSISTS (or PERSISTS-DIRECTIONAL)"
    if rows_for_stat["stat"].iloc[0] == "REB":
        n_falsified = sum(1 for d in disps if "FALSIFIED" in d)
        n_upheld = sum(1 for d in disps if d == "WALK-BACK UPHELD")
        return f"{n_upheld}/3 UPHELD, {n_falsified}/3 FALSIFIED, " \
                f"{3-n_upheld-n_falsified}/3 OTHER"
    n_pers = sum(1 for d in disps if "PERSISTS" in d or "DIRECTIONAL" in d)
    n_null = sum(1 for d in disps if "NULL" in d)
    n_inv = sum(1 for d in disps if "INVERTED" in d)
    return f"{n_pers}/3 PERSISTS-direction, {n_null}/3 NULL, " \
            f"{n_inv}/3 INVERTED"


def write_aggregate_report(out: pd.DataFrame) -> None:
    lines = ["# Sloan adjudicated Test 1 — aggregate verdict\n",
              "Pre-reg lock: `SLOAN_PRE_REG_TEST_1_ADJUDICATED_v1.0_LOCKED.md` "
              "(commit `e52505f`)",
              "Adjudication artifact SHA256: "
              "`eb615269f09159e0d0ceaf071812b84750578d81a9a53b01dff5a1ac2ac9dcbd`",
              "",
              "## 3 x 3 disposition table",
              "",
              "| Hypothesis | 2023-24 | 2024-25 | 2025-26 | Aggregate |",
              "|---|---|---|---|---|"]
    for stat in STATS:
        sub = out[out["stat"] == stat]
        cells = " | ".join(sub.set_index("season").loc[s, "disposition"]
                            for s in SEASONS)
        agg = aggregate_verdict_per_stat(sub)
        lines.append(f"| {stat} x Center | {cells} | **{agg}** |")
    (SLOAN_OUT / "aggregate_verdict.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")


def write_results_md(out: pd.DataFrame) -> None:
    lines = ["# Sloan Adjudicated Test 1 — Results\n",
              "Single-fire analysis under pre-reg `e52505f`. Adjudication "
              "artifact SHA256 `eb615269...`. Cross-paper anchor: v1.2 "
              "amendment commit `1bfdb4c` on the RMD-SRC paper.",
              "",
              "## Per-cell results (3 seasons x 3 stats x 2 buckets)",
              "",
              "Columns: n_in (Center) / n_out (non-Center), variance ratio = "
              "sigma_Center / sigma_non-Center, bootstrap 95% CI on the ratio "
              "(B=1000 with seed 20260601 per spec), Levene's p (median-"
              "centered, load-bearing), Bartlett's p + p_F supplementary.",
              ""]

    for stat in STATS:
        lines.append(f"### {stat} x Center")
        lines.append("")
        lines.append("| Season | bucket | n_in | n_out | ratio | CI95 | p_levene | disposition |")
        lines.append("|---|---|---|---|---|---|---|---|")
        sub = out[out["stat"] == stat]
        for _, r in sub.iterrows():
            lines.append(
                f"| {r['season']} | metadata | {int(r['n_in_meta'])} | "
                f"{int(r['n_out_meta'])} | {r['meta_ratio']:.3f} | "
                f"[{r['meta_ci_lo']:.3f}, {r['meta_ci_hi']:.3f}] | "
                f"{r['meta_p_levene']:.4f} | (control) |"
            )
            lines.append(
                f"| {r['season']} | **adjudicated** | "
                f"{int(r['n_in_adj'])} | {int(r['n_out_adj'])} | "
                f"**{r['adj_ratio']:.3f}** | "
                f"[{r['adj_ci_lo']:.3f}, {r['adj_ci_hi']:.3f}] | "
                f"**{r['adj_p_levene']:.4f}** | **{r['disposition']}** |"
            )
        lines.append("")

    lines += ["## Power lift summary",
              "",
              "| Stat | Season | n_in_meta | n_in_adj | lift | gate (>=1.30) |",
              "|---|---|---|---|---|---|"]
    for _, r in out.iterrows():
        lines.append(
            f"| {r['stat']} | {r['season']} | {int(r['n_in_meta'])} | "
            f"{int(r['n_in_adj'])} | {r['lift']:.2f} | "
            f"{'PASS' if r['power_pass'] else 'FAIL'} |"
        )

    lines += ["", "## Aggregate verdict",
              "", "See [aggregate_verdict.md](aggregate_verdict.md) for the "
              "3 x 3 disposition table and aggregate per-hypothesis verdicts.",
              "", "## Paper integration",
              "",
              "Per the pre-reg section 4 published-narrative framework, the "
              "result drives a specific cross-league paper revision. The "
              "adjudicated arm is reported alongside the metadata arm in "
              "cross-league paper section 5.4 (NBA contribution to the 11/11 "
              "BLK x Center claim) and section 5.4.1 (REB walk-back). The "
              "metadata-bucket numbers above must replicate the existing "
              "section 5.5 / 5.4 numbers exactly; the adjudicated-bucket "
              "numbers are the new headline."]

    (SLOAN_OUT / "SLOAN_ADJUDICATED_RESULTS.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
