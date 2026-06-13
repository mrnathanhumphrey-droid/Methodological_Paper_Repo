"""Cohort-overlap diagnostic: does the 22-23 vs 23-24 class-top-flip persist
on the SAME player set?

Steps:
  1. Load 22-23 PTS audit cohort (199 players from v4-lite audit)
  2. Load 23-24 v6 ship cohort (195 players)
  3. Find intersection (~150-180 players we have residuals for in both seasons)
  4. Re-run noise-floor on PTS_residual for both seasons restricted to overlap
  5. Compare top classes

If the flip persists on the same players: real season effect (different roster
moves had different downstream PTS effects). Forward validation is genuinely
hard.

If the flip disappears: the apparent flip was cohort composition (different
players in each season's filter). Apples-to-apples forward (option a) is more
likely to pass.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")

from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
AUDIT_2223 = REPO / "audit_runs" / "20260428T235309Z" / "skill_backtest_PTS_phase4_v4_quadratic_tq_gya_2019-20-2020-21-2021-22__2022-23" / "per_player_projections.csv"
SHIP_2324 = REPO / "audit_runs" / "unified_ship_v6" / "per_player_projections_2023-24.csv"


def attach_class_features(df, target_year):
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    df = df.merge(meta[["nba_api_id", "position", "birth_date", "draft_year"]],
                  on="nba_api_id", how="left")
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
    season_start = pd.Timestamp(f"{target_year}-10-24")
    df["age"] = (season_start - df["birth_date"]).dt.days / 365.25
    df["age_bucket"] = pd.cut(df["age"], bins=[0, 24, 27, 30, 33, 50],
                                labels=["<=24", "25-26", "27-29", "30-32", "33+"]).astype(str)
    df["years_pro"] = target_year - df["draft_year"]
    df["years_pro_bucket"] = pd.cut(df["years_pro"], bins=[-1, 0, 3, 7, 12, 30],
                                      labels=["rookie", "1-3", "4-7", "8-12", "13+"]).astype(str)
    draft = pd.read_parquet(PQ / "nba_draft_data.parquet")
    pick_map = dict(zip(draft["nba_api_id"].dropna().astype(int),
                         draft.dropna(subset=["nba_api_id"])["draft_pick"]))
    df["draft_pick"] = df["nba_api_id"].astype(int).map(pick_map)
    def pick_bucket(p):
        if pd.isna(p): return "undrafted"
        p = int(p)
        if p <= 5: return "top5"
        if p <= 14: return "lottery"
        if p <= 30: return "late_first"
        return "second"
    df["draft_pick_tier"] = df["draft_pick"].apply(pick_bucket)
    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    traded = set(tx[(tx["transaction_type"] == "trade") &
                    (tx["event_date"] >= pd.Timestamp(f"{target_year}-04-15")) &
                    (tx["event_date"] <= pd.Timestamp(f"{target_year}-10-24")) &
                    (tx["nba_api_id"].notna())]["nba_api_id"].astype(int))
    df["offseason_traded"] = df["nba_api_id"].astype(int).isin(traded)
    return df


def noise_floor(df, class_col, res_col):
    sub = df.dropna(subset=[class_col, res_col]).copy()
    grouped = sub.groupby(class_col, observed=True)[res_col].agg(
        ["mean", "count"]).reset_index()
    grouped = grouped[grouped["count"] >= 2]
    if len(grouped) < 2:
        return None
    sd_obs = grouped["mean"].std(ddof=1)
    overall_var = sub[res_col].var(ddof=1)
    n_per_class = grouped["count"].mean()
    se_samp = np.sqrt(overall_var / n_per_class)
    snr = sd_obs / se_samp if se_samp > 0 else np.nan
    return {"snr": snr, "n_classes": len(grouped),
            "class_means": dict(zip(grouped[class_col], grouped["mean"]))}


def main():
    # Load 22-23 audit
    a22 = pd.read_csv(AUDIT_2223)
    a22["nba_api_id"] = a22["nba_api_id"].astype(int)
    a22 = a22.dropna(subset=["actual", "proj_mean"]).copy()
    a22["PTS_residual"] = a22["actual"] - a22["proj_mean"]
    a22 = a22[["nba_api_id", "actual", "proj_mean", "PTS_residual"]].rename(
        columns={"actual": "PTS_actual_2223", "proj_mean": "PTS_proj_2223",
                  "PTS_residual": "PTS_residual_2223"})

    # Load 23-24 ship
    s24 = pd.read_csv(SHIP_2324)
    s24["nba_api_id"] = s24["nba_api_id"].astype(int)
    s24 = s24.dropna(subset=["PTS_actual"]).copy()
    s24["PTS_residual"] = s24["PTS_actual"] - s24["PTS_proj"]
    s24 = s24[["nba_api_id", "PTS_actual", "PTS_proj", "PTS_residual"]].rename(
        columns={"PTS_actual": "PTS_actual_2324", "PTS_proj": "PTS_proj_2324",
                  "PTS_residual": "PTS_residual_2324"})

    print(f"22-23 PTS audit:    {len(a22)} players")
    print(f"23-24 v6 ship:      {len(s24)} players")
    overlap = a22.merge(s24, on="nba_api_id", how="inner")
    print(f"Overlap:            {len(overlap)} players (in both seasons' eligibility)")

    # Players in 22-23 only
    only22 = set(a22["nba_api_id"]) - set(s24["nba_api_id"])
    only24 = set(s24["nba_api_id"]) - set(a22["nba_api_id"])
    print(f"22-23 only:         {len(only22)}  (graduated/retired/dropped <200 min)")
    print(f"23-24 only:         {len(only24)}  (rookies/promoted/added >=200 min)")

    # Attach class features as of EACH season
    print("\nAttaching class features (each season's correct class membership)...")
    df_22 = attach_class_features(overlap[["nba_api_id"]].copy(),
                                    target_year=2022)
    df_22["PTS_residual"] = overlap["PTS_residual_2223"]

    df_24 = attach_class_features(overlap[["nba_api_id"]].copy(),
                                    target_year=2023)
    df_24["PTS_residual"] = overlap["PTS_residual_2324"]

    print(f"\n--- 22-23 residual stats on overlap ({len(df_22)}) ---")
    print(f"  mean: {df_22['PTS_residual'].mean():+.4f}  SD: {df_22['PTS_residual'].std(ddof=1):.4f}")
    print(f"\n--- 23-24 residual stats on overlap ({len(df_24)}) ---")
    print(f"  mean: {df_24['PTS_residual'].mean():+.4f}  SD: {df_24['PTS_residual'].std(ddof=1):.4f}")

    # Run noise-floor on overlap for both seasons
    classes = ["position", "age_bucket", "offseason_traded",
               "years_pro_bucket", "draft_pick_tier"]
    print("\n" + "=" * 84)
    print("NOISE-FLOOR ON OVERLAP COHORT (apples-to-apples player set)")
    print("=" * 84)
    print(f"{'class':<22}  {'22-23 SNR':>10}  {'23-24 SNR':>10}  flip?")
    print("-" * 60)
    flip_results = []
    for c in classes:
        r22 = noise_floor(df_22, c, "PTS_residual")
        r24 = noise_floor(df_24, c, "PTS_residual")
        s22 = r22["snr"] if r22 else np.nan
        s24v = r24["snr"] if r24 else np.nan
        v22 = "REAL" if s22 >= 1.5 else ("marg" if s22 >= 1.05 else "noise")
        v24 = "REAL" if s24v >= 1.5 else ("marg" if s24v >= 1.05 else "noise")
        flip = "YES" if (v22 == "REAL") != (v24 == "REAL") else "no"
        flip_results.append((c, s22, s24v, v22, v24, flip))
        print(f"{c:<22}  {s22:>10.2f}  {s24v:>10.2f}  {v22:<5}/{v24:<5}  {flip}")

    # Compare class means for any class that's REAL in either season
    print("\n" + "=" * 84)
    print("CLASS-LEVEL DETAIL: per-class mean residual, both seasons (overlap)")
    print("=" * 84)
    for c in classes:
        r22 = noise_floor(df_22, c, "PTS_residual")
        r24 = noise_floor(df_24, c, "PTS_residual")
        if r22 is None or r24 is None:
            continue
        print(f"\n--- {c} ---")
        all_keys = sorted(set(r22["class_means"].keys()) | set(r24["class_means"].keys()),
                            key=lambda x: str(x))
        for k in all_keys:
            m22 = r22["class_means"].get(k, np.nan)
            m24 = r24["class_means"].get(k, np.nan)
            sign_match = "agree" if (not np.isnan(m22) and not np.isnan(m24)
                                       and np.sign(m22) == np.sign(m24)) else "DIVERGE"
            print(f"  {str(k):<14}  22-23={m22:+.3f}  23-24={m24:+.3f}  {sign_match}")

    # Headline check: did the offseason_traded class effect's SIGN replicate?
    print("\n" + "=" * 84)
    print("HEADLINE: does offseason_traded × PTS effect replicate on overlap?")
    print("=" * 84)
    r22 = noise_floor(df_22, "offseason_traded", "PTS_residual")
    r24 = noise_floor(df_24, "offseason_traded", "PTS_residual")
    if r22 and r24:
        traded_22 = r22["class_means"].get(True, np.nan)
        traded_24 = r24["class_means"].get(True, np.nan)
        not_traded_22 = r22["class_means"].get(False, np.nan)
        not_traded_24 = r24["class_means"].get(False, np.nan)
        diff_22 = traded_22 - not_traded_22 if not np.isnan(traded_22) else np.nan
        diff_24 = traded_24 - not_traded_24 if not np.isnan(traded_24) else np.nan
        print(f"\n  Traded mean residual:     22-23={traded_22:+.3f}  23-24={traded_24:+.3f}")
        print(f"  Not-traded mean residual: 22-23={not_traded_22:+.3f}  23-24={not_traded_24:+.3f}")
        print(f"  (Traded - NotTraded):     22-23={diff_22:+.3f}  23-24={diff_24:+.3f}")
        if not np.isnan(diff_22) and not np.isnan(diff_24):
            if np.sign(diff_22) == np.sign(diff_24):
                print(f"  -> SIGN AGREES across seasons: real structural effect (magnitude varies)")
            else:
                print(f"  -> SIGN DIVERGES: trade-class signal does NOT replicate on overlap.")
                print(f"     22-23 traded players were under/correctly projected on PTS;")
                print(f"     23-24 traded players were over-projected. Different mechanism.")

    # Also check position
    print("\n  Position effect on overlap:")
    r22 = noise_floor(df_22, "position", "PTS_residual")
    r24 = noise_floor(df_24, "position", "PTS_residual")
    if r22 and r24:
        for pos in ["Center", "Forward", "Guard"]:
            m22 = r22["class_means"].get(pos, np.nan)
            m24 = r24["class_means"].get(pos, np.nan)
            sign = "agree" if (not np.isnan(m22) and not np.isnan(m24) and
                                np.sign(m22) == np.sign(m24)) else "DIVERGE"
            print(f"    {pos:<8}  22-23={m22:+.3f}  23-24={m24:+.3f}  {sign}")


if __name__ == "__main__":
    main()
