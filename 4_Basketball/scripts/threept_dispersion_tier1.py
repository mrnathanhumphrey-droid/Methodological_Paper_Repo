"""Tier-1 pre-registered test: 3PM over-dispersion + 3P% gradient.

Pre-reg locked at audit_runs/threept_dispersion_pre_reg/PRE_REGISTRATION.md
Amended 2026-05-19a (Claim B threshold 1.30 → lower CI bound ≥ 1.15).

Replication seasons: 2017-18 + 2018-19 (untouched by exploratory probe).
Inclusion: Regular Season, ≥30 qual games (min ≥10), ≥30 3PA/season.
Statistic: dispersion = var_game(3PM) / (mean_3PA × p × (1-p)).
Claim A: one-sided Wilcoxon signed-rank vs median ≤ 1.25, α=0.05.
Claim B: bootstrap 95% CI lower bound on top(.390+)÷bottom(≤.300) median ratio ≥ 1.15.

Aggregate verdict per §5.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path("D:/NBA Projections")
BOX = ROOT / "data" / "parquet" / "historical_box_scores.parquet"
OUT = ROOT / "audit_runs" / "threept_dispersion"
OUT.mkdir(parents=True, exist_ok=True)

REPLICATION_SEASONS = ["2017-18", "2018-19"]
CLAIM_A_THRESHOLD = 1.25
CLAIM_B_LCI_THRESHOLD = 1.15
TOP_P = 0.390
BOT_P = 0.300
BOOT_N = 10_000
MIN_GAMES = 30
MIN_3PA = 30
MIN_MINUTES = 10
RNG = np.random.default_rng(2026)


def build_cohort(df: pd.DataFrame, season: str) -> pd.DataFrame:
    sub = df[(df["season"] == season) & (df["season_type"] == "Regular Season")].copy()
    sub["FG3M"] = pd.to_numeric(sub["FG3M"], errors="coerce")
    sub["FG3A"] = pd.to_numeric(sub["FG3A"], errors="coerce")
    sub["minutes"] = pd.to_numeric(sub["minutes"], errors="coerce")
    sub = sub.dropna(subset=["FG3M", "FG3A", "minutes"])
    sub = sub[sub["minutes"] >= MIN_MINUTES]

    grp = sub.groupby("nba_api_id").agg(
        n_games=("FG3M", "size"),
        var_3pm=("FG3M", "var"),
        mean_3pa=("FG3A", "mean"),
        sum_3pm=("FG3M", "sum"),
        sum_3pa=("FG3A", "sum"),
    ).reset_index()
    grp["season"] = season

    grp = grp[(grp["n_games"] >= MIN_GAMES) & (grp["sum_3pa"] >= MIN_3PA)]
    grp["p"] = grp["sum_3pm"] / grp["sum_3pa"]
    grp["binom_var"] = grp["mean_3pa"] * grp["p"] * (1 - grp["p"])
    grp["dispersion"] = grp["var_3pm"] / grp["binom_var"]
    grp = grp.replace([np.inf, -np.inf], np.nan).dropna(subset=["dispersion"])
    return grp.reset_index(drop=True)


def claim_a_test(disp: np.ndarray, threshold: float) -> dict:
    """One-sided Wilcoxon signed-rank: H0 median ≤ threshold, H1 median > threshold."""
    diffs = disp - threshold
    diffs_nz = diffs[diffs != 0]
    # one-sided "greater" — testing whether (disp - threshold) is stochastically > 0
    res = stats.wilcoxon(diffs_nz, alternative="greater", zero_method="wilcox")
    return {
        "n": int(len(disp)),
        "n_nonzero": int(len(diffs_nz)),
        "median": float(np.median(disp)),
        "iqr_lo": float(np.quantile(disp, 0.25)),
        "iqr_hi": float(np.quantile(disp, 0.75)),
        "wilcoxon_stat": float(res.statistic),
        "p_value": float(res.pvalue),
        "threshold": threshold,
        "confirms": bool(res.pvalue < 0.05 and np.median(disp) > threshold),
    }


def claim_b_test(top: np.ndarray, bot: np.ndarray, lci_threshold: float,
                  n_boot: int = BOOT_N) -> dict:
    if len(top) < 5 or len(bot) < 5:
        return {"n_top": int(len(top)), "n_bot": int(len(bot)),
                "median_top": float("nan"), "median_bot": float("nan"),
                "ratio": float("nan"), "ci_lo": float("nan"), "ci_hi": float("nan"),
                "lci_threshold": lci_threshold, "confirms": False,
                "note": "insufficient_n"}
    boots = np.empty(n_boot)
    for i in range(n_boot):
        t = RNG.choice(top, size=len(top), replace=True)
        b = RNG.choice(bot, size=len(bot), replace=True)
        boots[i] = np.median(t) / np.median(b)
    lo, hi = np.quantile(boots, [0.025, 0.975])
    point = float(np.median(top) / np.median(bot))
    return {
        "n_top": int(len(top)),
        "n_bot": int(len(bot)),
        "median_top": float(np.median(top)),
        "median_bot": float(np.median(bot)),
        "ratio": point,
        "ci_lo": float(lo),
        "ci_hi": float(hi),
        "lci_threshold": lci_threshold,
        "confirms": bool(lo >= lci_threshold),
    }


def per_season_disposition(a_res: dict, b_res: dict) -> str:
    if a_res["confirms"] and b_res["confirms"]:
        return "CONFIRMED"
    if a_res["confirms"] or b_res["confirms"]:
        return "PARTIAL"
    return "NULL"


def main():
    print(f"Loading box scores from {BOX}...")
    df = pd.read_parquet(BOX)
    seasons_present = sorted(df["season"].dropna().unique())
    print(f"  seasons in box scores: {seasons_present[:3]} ... {seasons_present[-3:]}")
    for s in REPLICATION_SEASONS:
        if s not in seasons_present:
            print(f"  ERROR: replication season {s} NOT in box scores")
            sys.exit(1)
    print()

    claim_a_rows = []
    claim_b_rows = []
    per_season_verdict = {}

    for season in REPLICATION_SEASONS:
        print(f"=" * 70)
        print(f"SEASON: {season}")
        print(f"=" * 70)
        cohort = build_cohort(df, season)
        cohort.to_csv(OUT / f"cohort_{season.replace('-','_')}.csv", index=False)
        print(f"  cohort n: {len(cohort):,}")
        print(f"  median 3PA/g: {cohort['mean_3pa'].median():.2f}  "
              f"median 3P%: {cohort['p'].median():.3f}  "
              f"median games: {cohort['n_games'].median():.0f}")

        # Claim A
        a = claim_a_test(cohort["dispersion"].values, CLAIM_A_THRESHOLD)
        a["season"] = season
        claim_a_rows.append(a)
        print(f"\n  CLAIM A — over-dispersion median > {CLAIM_A_THRESHOLD}")
        print(f"    median = {a['median']:.3f}  IQR [{a['iqr_lo']:.3f}, {a['iqr_hi']:.3f}]  n={a['n']}")
        print(f"    Wilcoxon one-sided p = {a['p_value']:.4g}")
        print(f"    → {'CONFIRMS' if a['confirms'] else 'NULL'}")

        # Claim B
        top = cohort[cohort["p"] >= TOP_P]["dispersion"].values
        bot = cohort[cohort["p"] <= BOT_P]["dispersion"].values
        b = claim_b_test(top, bot, CLAIM_B_LCI_THRESHOLD)
        b["season"] = season
        claim_b_rows.append(b)
        print(f"\n  CLAIM B — 3P% gradient lower CI ≥ {CLAIM_B_LCI_THRESHOLD}")
        print(f"    top (≥.390) n={b['n_top']}  median={b['median_top']:.3f}")
        print(f"    bot (≤.300) n={b['n_bot']}  median={b['median_bot']:.3f}")
        print(f"    ratio = {b['ratio']:.3f}  CI [{b['ci_lo']:.3f}, {b['ci_hi']:.3f}]")
        print(f"    → {'CONFIRMS' if b['confirms'] else 'NULL'}")

        verdict = per_season_disposition(a, b)
        per_season_verdict[season] = verdict
        print(f"\n  SEASON VERDICT: {verdict}")
        print()

    pd.DataFrame(claim_a_rows).to_csv(OUT / "claim_a_test.csv", index=False)
    pd.DataFrame(claim_b_rows).to_csv(OUT / "claim_b_test.csv", index=False)

    # Aggregate
    print(f"=" * 70)
    print(f"AGGREGATE VERDICT (per pre-reg §5)")
    print(f"=" * 70)
    confirmed = sum(1 for v in per_season_verdict.values() if v == "CONFIRMED")
    partial = sum(1 for v in per_season_verdict.values() if v == "PARTIAL")
    a_only = sum(1 for r in claim_a_rows if r["confirms"])
    b_only = sum(1 for r in claim_b_rows if r["confirms"])
    for s, v in per_season_verdict.items():
        print(f"  {s}: {v}")

    if confirmed == 2:
        agg = "STRUCTURAL FINDING — both claims confirm both seasons; supports paper extension + cross-league Tier-2"
    elif a_only == 2 and b_only < 2:
        agg = "PARTIAL — Claim A (over-dispersion) replicates 2/2; Claim B (3P% gradient) does not"
    elif a_only < 2:
        agg = "NULL — Claim A fails to replicate; the 1.83 exploratory ratio does not generalize"
    else:
        agg = f"MIXED — Claim A confirms {a_only}/2; Claim B confirms {b_only}/2"
    print(f"\n  AGGREGATE: {agg}")

    # Summary markdown
    summary_lines = [
        "# 3PM Dispersion Tier-1 Result Summary",
        "",
        f"**Pre-reg:** `audit_runs/threept_dispersion_pre_reg/PRE_REGISTRATION.md`",
        f"**Replication seasons:** {', '.join(REPLICATION_SEASONS)} (untouched by exploratory probe)",
        f"**Run date:** 2026-05-19",
        "",
        "## Per-season",
        "",
        "| Season | n cohort | Claim A median | Claim A p | A | Claim B ratio | Claim B CI | B | Verdict |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for a, b in zip(claim_a_rows, claim_b_rows):
        s = a["season"]
        v = per_season_verdict[s]
        summary_lines.append(
            f"| {s} | {a['n']} | {a['median']:.3f} | {a['p_value']:.3g} | "
            f"{'✓' if a['confirms'] else '✗'} | "
            f"{b['ratio']:.3f} | [{b['ci_lo']:.3f}, {b['ci_hi']:.3f}] | "
            f"{'✓' if b['confirms'] else '✗'} | **{v}** |"
        )
    summary_lines += ["", f"## Aggregate", "", agg, ""]

    (OUT / "summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"\nartifacts written to: {OUT}")
    for p in sorted(OUT.glob("*")):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
