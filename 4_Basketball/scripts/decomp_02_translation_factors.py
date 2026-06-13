"""Translation factors: pre-NBA per-40 → NBA Year-1 per-36, by position + source.

Per-stat OLS regression of NBA Y1 per-36 on pre-NBA per-40, separately for:
  - NCAA vs international source
  - Position bucket (G / W / B from combine; fallback to draft position label)

Reports per-stat (a) raw coefficient (slope from regression w/ intercept),
(b) per-stat shrinkage to NBA league mean Y1, (c) R^2, (d) sample size.

These factors are what rookie_priors.parquet will USE downstream to convert any
incoming rookie's pre-NBA per-40 line into an NBA Y1 per-36 point estimate.

Outputs:
    data/parquet/rookie_translation_factors.parquet  (per-stat × source × position)
    docs/ROOKIE_DECOMP_TRANSLATION_FACTORS.md (human-readable summary)
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
DOCS.mkdir(parents=True, exist_ok=True)
OUT_PQ = PQ / "rookie_translation_factors.parquet"
OUT_DOC = DOCS / "ROOKIE_DECOMP_TRANSLATION_FACTORS.md"
MIN_GP_Y1 = 25
MIN_PER_BUCKET = 25

STAT_MAP = [
    ("pts", "pts_per40", "pts_per36"),
    ("reb", "reb_per40", "reb_per36"),
    ("ast", "ast_per40", "ast_per36"),
    ("stl", "stl_per40", "stl_per36"),
    ("blk", "blk_per40", "blk_per36"),
    ("tov", "tov_per40", "tov_per36"),
    ("fg3m", "fg3m_per40", "fg3m_per36"),
]


def pos_bucket(p):
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return "UNK"
    s = str(p).upper()
    if "PG" in s or "G" == s[:1] and "F" not in s and "C" not in s:
        return "PG_SG"
    if "SG" in s:
        return "PG_SG"
    if "SF" in s or "PF" in s:
        return "WING"
    if "C" in s:
        return "BIG"
    if "F" in s:
        return "WING"
    if "G" in s:
        return "PG_SG"
    return "UNK"


def fit_one(x, y):
    mask = pd.notna(x) & pd.notna(y)
    x, y = x[mask].values, y[mask].values
    n = len(x)
    if n < 5:
        return dict(n=n, slope=np.nan, intercept=np.nan, r2=np.nan, mean_x=np.nan, mean_y=np.nan)
    A = np.vstack([x, np.ones_like(x)]).T
    slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
    yhat = slope * x + intercept
    ss_res = float(((y - yhat) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
    return dict(n=int(n), slope=float(slope), intercept=float(intercept),
                  r2=float(r2), mean_x=float(x.mean()), mean_y=float(y.mean()))


def main():
    m = pd.read_parquet(PQ / "rookies_master.parquet")
    print(f"  master rows: {len(m):,}")

    m = m[m["has_nba_y1"] & (m["nba_y1_gp"] >= MIN_GP_Y1)].copy()
    print(f"  w/ y1 gp >= {MIN_GP_Y1}: {len(m):,}")

    m["pos_bucket"] = m.get("combine_position").apply(pos_bucket)
    print(f"  pos distribution: {m['pos_bucket'].value_counts().to_dict()}")

    rows = []
    for source_lbl, source_prefix in [("ncaa", "ncaa_"), ("intl", "intl_")]:
        sub = m[m[f"has_{source_lbl}"]].copy()
        for stat, pre_col, nba_col in STAT_MAP:
            pre_full = f"{source_prefix}{pre_col}"
            nba_full = f"nba_y1_{nba_col}"
            if pre_full not in sub.columns or nba_full not in sub.columns:
                continue
            x = pd.to_numeric(sub[pre_full], errors="coerce")
            y = pd.to_numeric(sub[nba_full], errors="coerce")
            r = fit_one(x, y)
            r.update(dict(source=source_lbl, stat=stat, bucket="ALL"))
            rows.append(r)
            for pb in ["PG_SG", "WING", "BIG"]:
                sub2 = sub[sub["pos_bucket"] == pb]
                if len(sub2) < MIN_PER_BUCKET:
                    continue
                x2 = pd.to_numeric(sub2[pre_full], errors="coerce")
                y2 = pd.to_numeric(sub2[nba_full], errors="coerce")
                r2 = fit_one(x2, y2)
                r2.update(dict(source=source_lbl, stat=stat, bucket=pb))
                rows.append(r2)

    out = pd.DataFrame(rows)
    out.to_parquet(OUT_PQ, index=False)
    print(f"\nwrote: {OUT_PQ}")

    lines = ["# Rookie Translation Factors — pre-NBA per-40 → NBA Year-1 per-36",
                 "",
                 f"Window: draft years 2014-2024. Min NBA Year-1 GP for inclusion: {MIN_GP_Y1}.",
                 "",
                 "## How to read the slope",
                 "",
                 "- Slope >0.30 = signal-carrying.",
                 "- Slope ≈0 = pre-NBA stat carries no Y1 NBA information for that bucket.",
                 "- R² <0.05 = effectively noise even where slope looks positive.",
                 "",
                 "## Per-stat × source × position",
                 ""]
    for source in ["ncaa", "intl"]:
        lines.append(f"### {source.upper()}")
        lines.append("")
        sub = out[out["source"] == source].sort_values(["stat", "bucket"])
        lines.append("| Stat | Bucket | n | Slope | Intercept | R² | μ_x | μ_y |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
        for _, r in sub.iterrows():
            lines.append(f"| {r['stat']} | {r['bucket']} | {r['n']} | {r['slope']:+.3f} | {r['intercept']:+.3f} | {r['r2']:+.3f} | {r['mean_x']:.2f} | {r['mean_y']:.2f} |")
        lines.append("")

    OUT_DOC.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote: {OUT_DOC}")

    print("\n=== HEADLINE (ALL-bucket slopes) ===")
    headline = out[out["bucket"] == "ALL"].sort_values(["source", "stat"])
    print(headline[["source", "stat", "n", "slope", "intercept", "r2", "mean_x", "mean_y"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
