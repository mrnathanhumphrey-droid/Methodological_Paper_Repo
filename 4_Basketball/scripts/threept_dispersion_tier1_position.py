"""Tier-1 §7 conditional: position stratification on 2017-18 + 2018-19.

Authorized by pre-reg §7 ("Both replication seasons confirm Claim A"). Claim A
confirmed 2/2 in Tier-1 base run.

Pre-reg threshold per amendment 2026-05-19a: bootstrap 95% CI lower bound on
top(.390+) ÷ bottom(≤.300) median ratio ≥ 1.05 per position cell.

Center cell skipped if n_in_top_bucket < 15 in either replication season.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path("D:/NBA Projections")
BOX = ROOT / "data" / "parquet" / "historical_box_scores.parquet"
META = ROOT / "data" / "parquet" / "player_metadata.parquet"
OUT = ROOT / "audit_runs" / "threept_dispersion"

REPLICATION_SEASONS = ["2017-18", "2018-19"]
TOP_P = 0.390
BOT_P = 0.300
POSITION_LCI_THRESHOLD = 1.05
BOOT_N = 10_000
MIN_GAMES = 30
MIN_3PA = 30
MIN_MINUTES = 10
RNG = np.random.default_rng(2026)


def primary_position(pos: str) -> str:
    if pd.isna(pos):
        return "UNK"
    s = str(pos).strip().split("-")[0].strip()
    return {"Guard": "G", "Forward": "F", "Center": "C",
            "G": "G", "F": "F", "C": "C"}.get(s, "UNK")


def build_cohort(df: pd.DataFrame, season: str, meta: pd.DataFrame) -> pd.DataFrame:
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
    grp = grp.merge(meta[["nba_api_id", "pos"]], on="nba_api_id", how="left")
    grp["pos"] = grp["pos"].fillna("UNK")
    return grp.reset_index(drop=True)


def gradient_test(top: np.ndarray, bot: np.ndarray) -> dict:
    if len(top) < 5 or len(bot) < 5:
        return {"n_top": int(len(top)), "n_bot": int(len(bot)),
                "median_top": float("nan"), "median_bot": float("nan"),
                "ratio": float("nan"), "ci_lo": float("nan"), "ci_hi": float("nan"),
                "note": "insufficient_n"}
    boots = np.empty(BOOT_N)
    for i in range(BOOT_N):
        t = RNG.choice(top, size=len(top), replace=True)
        b = RNG.choice(bot, size=len(bot), replace=True)
        boots[i] = np.median(t) / np.median(b)
    lo, hi = np.quantile(boots, [0.025, 0.975])
    return {
        "n_top": int(len(top)),
        "n_bot": int(len(bot)),
        "median_top": float(np.median(top)),
        "median_bot": float(np.median(bot)),
        "ratio": float(np.median(top) / np.median(bot)),
        "ci_lo": float(lo),
        "ci_hi": float(hi),
    }


def main():
    df = pd.read_parquet(BOX)
    meta = pd.read_parquet(META)[["nba_api_id", "position"]].copy()
    meta["pos"] = meta["position"].map(primary_position)

    rows = []
    skip_log = []

    for season in REPLICATION_SEASONS:
        print(f"=" * 70)
        print(f"SEASON: {season}")
        print(f"=" * 70)
        cohort = build_cohort(df, season, meta)
        print(f"  total n: {len(cohort)}  position breakdown: "
              f"{cohort['pos'].value_counts().to_dict()}")

        for pos in ["G", "F", "C"]:
            sub = cohort[cohort["pos"] == pos]
            top = sub[sub["p"] >= TOP_P]["dispersion"].values
            bot = sub[sub["p"] <= BOT_P]["dispersion"].values

            if pos == "C" and (len(top) < 15):
                skip_log.append({"season": season, "pos": pos,
                                 "reason": f"C cell n_top={len(top)} < 15 (pre-reg §7)"})
                print(f"\n  {pos}: SKIP — n_top={len(top)} < 15")
                continue

            r = gradient_test(top, bot)
            r["season"] = season
            r["pos"] = pos
            r["threshold_lci"] = POSITION_LCI_THRESHOLD
            r["confirms"] = bool(r["ci_lo"] >= POSITION_LCI_THRESHOLD)
            rows.append(r)
            print(f"\n  {pos}: top n={r['n_top']} (med {r['median_top']:.3f})  "
                  f"bot n={r['n_bot']} (med {r['median_bot']:.3f})")
            print(f"     ratio={r['ratio']:.3f}  CI [{r['ci_lo']:.3f}, {r['ci_hi']:.3f}]  "
                  f"vs threshold {POSITION_LCI_THRESHOLD}  → "
                  f"{'CONFIRMS' if r['confirms'] else 'NULL'}")

        print()

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUT / "position_stratification.csv", index=False)
    if skip_log:
        pd.DataFrame(skip_log).to_csv(OUT / "position_stratification_skips.csv", index=False)

    print(f"=" * 70)
    print(f"POSITION STRATIFICATION VERDICT")
    print(f"=" * 70)
    for pos in ["G", "F", "C"]:
        cells = [r for r in rows if r["pos"] == pos]
        if not cells:
            print(f"  {pos}: all seasons skipped (insufficient n)")
            continue
        n_conf = sum(1 for r in cells if r["confirms"])
        n_tot = len(cells)
        print(f"  {pos}: {n_conf}/{n_tot} seasons confirm gradient ≥ {POSITION_LCI_THRESHOLD}")

    pooled_confirms = sum(1 for r in rows if r["confirms"])
    total_cells = len(rows)
    print(f"\n  pooled: {pooled_confirms}/{total_cells} (position × season) cells confirm")

    print(f"\nwrote: position_stratification.csv ({len(rows)} cells), "
          f"position_stratification_skips.csv ({len(skip_log)} skips)")


if __name__ == "__main__":
    main()
