"""Signal-Source: per Y1 outcome stat, which inputs actually carry predictive signal.

For each of (pts, reb, ast, stl, blk, fg3m, tov) NBA Y1 per-36:
  Run univariate regressions vs each candidate input across 5 input families:
    1. PRE-NBA STATS   (ncaa_*_per40, intl_*_per40, gp, mpg, fg%, ft%)
    2. COMBINE         (height, wingspan, reach, vert, agility, sprint, weight)
    3. DRAFT           (draft_pick, draft_round, draft_year)
    4. POSITION/PHYSICAL (height_with_shoes, weight, wingspan/reach delta)
    5. EXPECTED ROLE   (mpg in pre-NBA, position bucket)

Report per-stat top-5 predictors with slope + R². The "what predicts what" map.

Output:
    data/parquet/rookie_signal_source.parquet   (long-format)
    docs/ROOKIE_DECOMP_SIGNAL_SOURCE.md
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

PQ = Path("D:/NBA Projections/data/parquet")
DOCS = Path("D:/NBA Projections/docs")
OUT_PQ = PQ / "rookie_signal_source.parquet"
OUT_DOC = DOCS / "ROOKIE_DECOMP_SIGNAL_SOURCE.md"
MIN_GP_Y1 = 25
MIN_N = 30

TARGETS = [
    ("pts_per36", "nba_y1_pts_per36"),
    ("reb_per36", "nba_y1_reb_per36"),
    ("ast_per36", "nba_y1_ast_per36"),
    ("stl_per36", "nba_y1_stl_per36"),
    ("blk_per36", "nba_y1_blk_per36"),
    ("fg3m_per36", "nba_y1_fg3m_per36"),
    ("tov_per36", "nba_y1_tov_per36"),
    ("mpg", "nba_y1_mpg"),
]

INPUT_FAMILIES = {
    "PRE_NBA": [
        "ncaa_pts_per40", "ncaa_reb_per40", "ncaa_ast_per40",
        "ncaa_stl_per40", "ncaa_blk_per40", "ncaa_tov_per40",
        "ncaa_fg_pct", "ncaa_fg3_pct", "ncaa_ft_pct",
        "ncaa_gp", "ncaa_mpg",
        "intl_pts_per40", "intl_reb_per40", "intl_ast_per40",
        "intl_stl_per40", "intl_blk_per40", "intl_fg3m_per40",
        "intl_fg_pct", "intl_fg3_pct", "intl_ft_pct",
        "intl_gp", "intl_mpg",
    ],
    "COMBINE": [
        "combine_height_with_shoes_inches", "combine_height_no_shoes_inches",
        "combine_weight_lbs", "combine_wingspan_inches",
        "combine_standing_reach_inches", "combine_body_fat_pct",
        "combine_hand_length_inches", "combine_hand_width_inches",
        "combine_standing_vertical_inches", "combine_max_vertical_inches",
        "combine_lane_agility_seconds", "combine_modified_lane_agility_seconds",
        "combine_three_quarter_sprint_seconds", "combine_bench_press_reps",
    ],
    "DRAFT": ["draft_pick", "draft_round", "draft_year"],
}


def fit_one(x, y):
    mask = pd.notna(x) & pd.notna(y) & ~np.isinf(x) & ~np.isinf(y)
    x, y = x[mask].values, y[mask].values
    n = len(x)
    if n < MIN_N or x.std() == 0:
        return dict(n=n, slope=np.nan, intercept=np.nan, r2=np.nan, corr=np.nan)
    A = np.vstack([x, np.ones_like(x)]).T
    slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
    yhat = slope * x + intercept
    ss_res = ((y - yhat) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
    corr = float(np.corrcoef(x, y)[0, 1])
    return dict(n=int(n), slope=float(slope), intercept=float(intercept),
                  r2=float(r2), corr=corr)


def main():
    m = pd.read_parquet(PQ / "rookies_master.parquet")
    m = m[m["has_nba_y1"] & (m["nba_y1_gp"] >= MIN_GP_Y1)].copy()
    print(f"  master Y1 >= {MIN_GP_Y1} GP: {len(m):,}")

    rows = []
    for target_lbl, target_col in TARGETS:
        if target_col not in m.columns:
            continue
        for family, inputs in INPUT_FAMILIES.items():
            for inp in inputs:
                if inp not in m.columns:
                    continue
                x = pd.to_numeric(m[inp], errors="coerce")
                y = pd.to_numeric(m[target_col], errors="coerce")
                r = fit_one(x, y)
                r.update(dict(target=target_lbl, family=family, input=inp))
                rows.append(r)
    out = pd.DataFrame(rows)
    out.to_parquet(OUT_PQ, index=False)
    print(f"wrote: {OUT_PQ}")

    lines = ["# Rookie Decomp — Signal Source Cascade",
                 "",
                 f"Window: 2014-24 draft years, Y1 GP >= {MIN_GP_Y1}.",
                 "Univariate regressions of each candidate input vs each Y1 NBA outcome per-36 stat.",
                 "",
                 "## Per-target top 5 predictors (by |corr|)",
                 ""]
    for target_lbl, _ in TARGETS:
        sub = out[out["target"] == target_lbl].copy()
        sub["abs_corr"] = sub["corr"].abs()
        sub = sub.dropna(subset=["corr"]).sort_values("abs_corr", ascending=False).head(8)
        lines.append(f"### NBA Y1 {target_lbl}")
        lines.append("")
        lines.append("| Family | Input | n | Corr | R² | Slope |")
        lines.append("|---|---|---:|---:|---:|---:|")
        for _, r in sub.iterrows():
            lines.append(f"| {r['family']} | {r['input']} | {r['n']} | {r['corr']:+.3f} | {r['r2']:+.3f} | {r['slope']:+.4f} |")
        lines.append("")

    OUT_DOC.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote: {OUT_DOC}")

    print("\n=== TOP PREDICTORS PER TARGET (|corr|) ===")
    for target_lbl, _ in TARGETS:
        sub = out[out["target"] == target_lbl].copy()
        sub["abs_corr"] = sub["corr"].abs()
        sub = sub.dropna(subset=["corr"]).sort_values("abs_corr", ascending=False).head(5)
        print(f"\n  {target_lbl}:")
        print(sub[["family", "input", "n", "corr", "r2"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
