"""Expanded class candidate test: 8 classes x 8 stats = 64 noise-floor tests.

New classes added beyond the original 3:
  - years_pro             (rookie / 1-3 / 4-7 / 8-12 / 13+)
  - career_mpg_tier       (star >=30 / starter 25-30 / rotation 18-25 / bench <18)
  - draft_pick_tier       (top5 / lottery 6-14 / late_first 15-30 / second / undrafted)
  - chronic_severity_bucket (none / low / med / high based on weighted_severity_3y)
  - years_with_team       (1 / 2-3 / 4-6 / 7+ tenure on 22-23 team)

Then run per-stat LOO ablation including all surviving (SNR>=1.5) combinations.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
from ablation_harness import load_baseline, per_stat_mae

REPO = Path(".")
PQ = REPO / "data" / "parquet"

STATS_WITH_ACTUAL = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FTA", "FTM"]


def parse_min(x):
    if pd.isna(x): return np.nan
    s = str(x)
    if ":" in s:
        try:
            a, b = s.split(":")
            return float(a) + float(b) / 60.0
        except Exception:
            return np.nan
    try:
        return float(s)
    except Exception:
        return np.nan


def years_with_team_map():
    """For each player, count consecutive seasons on their 22-23 team."""
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    # Per (player, season) take dominant team (most games)
    pts = box.groupby(["nba_api_id", "season"])["team_abbr"].agg(
        lambda x: x.value_counts().idxmax()).reset_index()
    out = {}
    for pid, grp in pts.groupby("nba_api_id"):
        grp = grp.sort_values("season")
        if "2022-23" not in grp["season"].values:
            continue
        team_22 = grp.loc[grp["season"] == "2022-23", "team_abbr"].iloc[0]
        # Walk back from 22-23
        years = 1
        seasons = sorted(grp["season"].unique(), reverse=True)
        for s in seasons:
            if s == "2022-23":
                continue
            if s > "2022-23":
                continue
            row_team = grp.loc[grp["season"] == s, "team_abbr"].iloc[0]
            if row_team == team_22:
                years += 1
            else:
                break
        out[int(pid)] = years
    return out


def attach_features(base):
    df = base.copy()
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    df = df.merge(meta[["nba_api_id", "position", "birth_date", "draft_year"]],
                  on="nba_api_id", how="left")
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
    df["age_2023"] = (pd.Timestamp("2023-10-24") - df["birth_date"]).dt.days / 365.25
    df["age_bucket"] = pd.cut(df["age_2023"],
                               bins=[0, 24, 27, 30, 33, 50],
                               labels=["<=24", "25-26", "27-29", "30-32", "33+"]).astype(str)

    # years pro = 2023 - draft_year (rookie if draft_year == 2023)
    df["years_pro"] = 2023 - df["draft_year"]
    df["years_pro_bucket"] = pd.cut(df["years_pro"],
                                      bins=[-1, 0, 3, 7, 12, 30],
                                      labels=["rookie", "1-3", "4-7", "8-12", "13+"]).astype(str)

    # career mpg tier from current projection (proxy for role)
    df["career_mpg_tier"] = pd.cut(df["MPG_proj"],
                                    bins=[0, 18, 25, 30, 50],
                                    labels=["bench", "rotation", "starter", "star"]).astype(str)

    # draft pick tier
    draft = pd.read_parquet(PQ / "nba_draft_data.parquet")
    pick_map = dict(zip(draft["nba_api_id"].dropna().astype(int),
                         draft.dropna(subset=["nba_api_id"])["draft_pick"]))
    df["draft_pick"] = df["nba_api_id"].astype(int).map(pick_map)
    def pick_bucket(p):
        if pd.isna(p):
            return "undrafted"
        p = int(p)
        if p <= 5: return "top5"
        if p <= 14: return "lottery"
        if p <= 30: return "late_first"
        return "second"
    df["draft_pick_tier"] = df["draft_pick"].apply(pick_bucket)

    # Chronic severity bucket
    chronic_path = PQ / "chronic_injury_features_path1.parquet"
    if chronic_path.exists():
        chronic = pd.read_parquet(chronic_path)
        chronic = chronic[chronic["target_year"] == 2024].copy()
        sev_map = dict(zip(chronic["nba_api_id"].astype(int),
                            chronic["weighted_severity_3y"]))
        df["chronic_severity"] = df["nba_api_id"].astype(int).map(sev_map).fillna(0)
        def sev_bucket(s):
            if s == 0: return "none"
            if s <= 3: return "low"
            if s <= 8: return "med"
            return "high"
        df["chronic_bucket"] = df["chronic_severity"].apply(sev_bucket)
    else:
        df["chronic_bucket"] = "none"

    # offseason traded
    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    traded = set(tx[(tx["transaction_type"] == "trade") &
                    (tx["event_date"] >= "2023-04-15") &
                    (tx["event_date"] <= "2023-10-24") &
                    (tx["nba_api_id"].notna())]["nba_api_id"].astype(int))
    df["offseason_traded"] = df["nba_api_id"].astype(int).isin(traded)

    # years with team
    ywt_map = years_with_team_map()
    df["years_with_team"] = df["nba_api_id"].astype(int).map(ywt_map).fillna(0)
    df["years_with_team_bucket"] = pd.cut(df["years_with_team"],
                                            bins=[-1, 1, 3, 6, 30],
                                            labels=["1", "2-3", "4-6", "7+"]).astype(str)

    # Per-stat residuals
    for stat in STATS_WITH_ACTUAL:
        proj = f"{stat}_proj"
        actual = f"{stat}_actual"
        if proj in df.columns and actual in df.columns:
            df[f"{stat}_residual"] = df[actual] - df[proj]
    return df


def noise_floor(df, class_col, stat):
    res_col = f"{stat}_residual"
    if res_col not in df.columns:
        return None
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


def loo_class_means(df, class_col, residual_col):
    sub = df.dropna(subset=[class_col, residual_col]).copy()
    out = {}
    for cls, idx in sub.groupby(class_col, observed=True).groups.items():
        idx = list(idx)
        for i in idx:
            others = [j for j in idx if j != i]
            mean = sub.loc[others, residual_col].mean() if others else 0.0
            out[i] = mean
    return out


def apply_per_stat_offsets(base, offsets):
    out = base.copy()
    for stat, pid_to_delta in offsets.items():
        col = f"{stat}_proj"
        if col not in out.columns:
            continue
        out[col] = out.apply(
            lambda r: r[col] + pid_to_delta.get(int(r["nba_api_id"]), 0.0)
            if pd.notna(r[col]) else r[col],
            axis=1
        )
    return out


def main():
    base = load_baseline()
    df = attach_features(base)
    print(f"Cohort: {len(df)}")

    classes = ["position", "age_bucket", "offseason_traded",
               "years_pro_bucket", "career_mpg_tier", "draft_pick_tier",
               "chronic_bucket", "years_with_team_bucket"]

    # =================== STAGE 1: SNR matrix ===================
    print("\n" + "=" * 92)
    print("PER-STAT SNR MATRIX (8 classes x 8 stats)")
    print("=" * 92)
    rows = []
    for stat in STATS_WITH_ACTUAL:
        for c in classes:
            r = noise_floor(df, c, stat)
            if r is None:
                continue
            rows.append({"stat": stat, "class": c, "snr": r["snr"],
                          "verdict": ("REAL" if r["snr"] >= 1.5
                                       else "marginal" if r["snr"] >= 1.05
                                       else "noise")})
    snr_df = pd.DataFrame(rows)
    pivot = snr_df.pivot(index="class", columns="stat", values="snr")
    print(pivot.applymap(lambda x: f"{x:.2f}" if not pd.isna(x) else "  ").to_string())

    # Surviving combos
    surviving = snr_df[snr_df["snr"] >= 1.5].sort_values(
        ["stat", "snr"], ascending=[True, False])
    print(f"\n--- Surviving (stat, class) combinations at SNR>=1.5 (count: {len(surviving)}) ---")
    print(surviving[["stat", "class", "snr"]].to_string(index=False))

    # =================== STAGE 2: build offsets and ablate ===================
    print("\n" + "=" * 92)
    print("EXPANDED PER-STAT OFFSET ABLATION (LOO, SNR>=1.5)")
    print("=" * 92)
    base_mae = per_stat_mae(base)

    surviving_per_stat = {}
    for stat in STATS_WITH_ACTUAL:
        cols = surviving[surviving["stat"] == stat]["class"].tolist()
        surviving_per_stat[stat] = cols

    offsets = {}
    for stat in STATS_WITH_ACTUAL:
        if not surviving_per_stat[stat]:
            continue
        res_col = f"{stat}_residual"
        sub = df.dropna(subset=[res_col]).copy()
        loo_per_class = {}
        for c in surviving_per_stat[stat]:
            loo_per_class[c] = loo_class_means(sub, c, res_col)
        per_stat = {}
        for idx, row in sub.iterrows():
            pid = int(row["nba_api_id"])
            d = sum(loo_per_class[c].get(idx, 0.0) for c in surviving_per_stat[stat])
            per_stat[pid] = d
        offsets[stat] = per_stat

    print("\nSurviving classes per stat:")
    for s, cs in surviving_per_stat.items():
        print(f"  {s}: {cs}")

    shocked = apply_per_stat_offsets(base, offsets)
    new_mae = per_stat_mae(shocked)
    rows = []
    for stat in STATS_WITH_ACTUAL:
        b = base_mae.get(stat, np.nan)
        a = new_mae.get(stat, np.nan)
        if np.isnan(b) or np.isnan(a):
            continue
        rows.append({"stat": stat, "base": b, "abl": a, "delta": a - b,
                      "pct": 100 * (a - b) / b if b > 0 else np.nan})
    out = pd.DataFrame(rows)
    out["base"] = out["base"].apply(lambda x: f"{x:.4f}")
    out["abl"] = out["abl"].apply(lambda x: f"{x:.4f}")
    out["delta"] = out["delta"].apply(lambda x: f"{x:+.4f}")
    out["pct"] = out["pct"].apply(lambda x: f"{x:+.2f}%")
    print("\n" + out.to_string(index=False))
    pcts = [100 * (new_mae[s] - base_mae[s]) / base_mae[s]
            for s in STATS_WITH_ACTUAL if s in new_mae and base_mae.get(s, 0) > 0]
    print(f"\n  Composite avg pct (8 stats): {np.mean(pcts):+.2f}%")

    # =================== STAGE 3: Compare to original 3-class result ===================
    print("\n--- Reference: original 3-class result was composite -1.34% ---")

    # Save matrix
    snr_df.to_parquet(PQ / "per_stat_class_snr_matrix.parquet", index=False)
    print(f"\nSaved SNR matrix -> {PQ / 'per_stat_class_snr_matrix.parquet'}")


if __name__ == "__main__":
    main()
