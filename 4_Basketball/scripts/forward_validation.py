"""Forward validation: derive class offsets from 22-23 residuals, apply to 23-24.

Requires:
  audit_runs/unified_ship_v6_2022-23/per_player_projections_2022-23.csv
  audit_runs/unified_ship_v6/per_player_projections_2023-24.csv  (already exists)
  data/parquet/historical_box_scores.parquet (already has 22-23 + 23-24)

If 22-23 ship CSV doesn't exist yet, prints a clear message and exits.
See docs/forward_validation_spec_v6_22_23.md for build instructions.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")

from pathlib import Path
import numpy as np
import pandas as pd

from ablation_harness import per_stat_mae

REPO = Path(".")
PQ = REPO / "data" / "parquet"
SHIP_2223 = REPO / "audit_runs" / "unified_ship_v6_2022-23" / "per_player_projections_2022-23.csv"
SHIP_2324 = REPO / "audit_runs" / "unified_ship_v6" / "per_player_projections_2023-24.csv"

STATS_WITH_ACTUAL = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FTA", "FTM"]


def attach_features_for_season(df, season_label, target_year):
    """season_label like '2022-23'; target_year like 2022 (for offseason cutoffs)."""
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
    df["career_mpg_tier"] = pd.cut(df.get("MPG_proj", df.get("mpg")),
                                     bins=[0, 18, 25, 30, 50],
                                     labels=["bench", "rotation", "starter", "star"]).astype(str)
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

    # Offseason traded relative to TARGET season (e.g., for 22-23 target: Apr-Oct 2022)
    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    tx_window_start = pd.Timestamp(f"{target_year}-04-15")
    tx_window_end = pd.Timestamp(f"{target_year}-10-24")
    traded = set(tx[(tx["transaction_type"] == "trade") &
                    (tx["event_date"] >= tx_window_start) &
                    (tx["event_date"] <= tx_window_end) &
                    (tx["nba_api_id"].notna())]["nba_api_id"].astype(int))
    df["offseason_traded"] = df["nba_api_id"].astype(int).isin(traded)
    return df


def attach_actual_residuals(df, season_label):
    """Add {stat}_residual and mpg_actual columns based on box-score actuals."""
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["minutes"] = pd.to_numeric(box["minutes"], errors="coerce")
    box = box.dropna(subset=["minutes"])
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    s = box[box["season"] == season_label]
    actual = s.groupby("nba_api_id").agg(
        gp=("game_id", "nunique"),
        total_min=("minutes", "sum"),
        PTS_a=("PTS", "sum"), REB_a=("REB", "sum"), AST_a=("AST", "sum"),
        STL_a=("STL", "sum"), BLK_a=("BLK", "sum"), TOV_a=("TOV", "sum"),
        FTA_a=("FTA", "sum"), FTM_a=("FTM", "sum"),
    ).reset_index()
    for stat in STATS_WITH_ACTUAL:
        actual[f"{stat}_actual"] = actual[f"{stat}_a"] / actual["gp"]
    actual["mpg_actual"] = actual["total_min"] / actual["gp"]
    actual = actual[["nba_api_id", "mpg_actual"] +
                     [f"{s}_actual" for s in STATS_WITH_ACTUAL] + ["gp"]]
    df = df.merge(actual, on="nba_api_id", how="left", suffixes=("", "_box"))
    # If df already has _actual columns from CSV, prefer the box-derived for clean math
    for stat in STATS_WITH_ACTUAL:
        if f"{stat}_actual_box" in df.columns:
            df[f"{stat}_actual"] = df[f"{stat}_actual_box"]
            df = df.drop(columns=[f"{stat}_actual_box"])
        proj = f"{stat}_proj"
        if proj in df.columns:
            df[f"{stat}_residual"] = df[f"{stat}_actual"] - df[proj]
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
    return {"snr": snr, "class_means": dict(zip(grouped[class_col], grouped["mean"]))}


def derive_offsets_from_22_23(df_2223):
    """For each stat, find top-1 class at SNR>=1.5; return dict[stat -> dict[class_value -> offset]]."""
    classes = ["position", "age_bucket", "offseason_traded",
               "years_pro_bucket", "career_mpg_tier", "draft_pick_tier"]
    offset_table = {}
    used_classes = {}
    for stat in STATS_WITH_ACTUAL:
        candidates = []
        for c in classes:
            r = noise_floor(df_2223, c, stat)
            if r is not None and r["snr"] >= 1.5:
                candidates.append((c, r["snr"], r["class_means"]))
        if not candidates:
            continue
        candidates.sort(key=lambda x: -x[1])
        cls, snr, means = candidates[0]
        offset_table[stat] = means
        used_classes[stat] = cls
        print(f"  {stat:<5} -> {cls:<22} (SNR={snr:.2f})  offsets: " +
              ", ".join(f"{k}={v:+.2f}" for k, v in means.items()))
    return offset_table, used_classes


def apply_external_offsets_to_2324(df_2324_with_features, offset_table, used_classes):
    """For each player in 2324 cohort, look up their class value, apply offset to {stat}_proj."""
    out = df_2324_with_features.copy()
    for stat, class_means in offset_table.items():
        cls_col = used_classes[stat]
        proj_col = f"{stat}_proj"
        if proj_col not in out.columns:
            continue
        out[proj_col] = out.apply(
            lambda r: r[proj_col] + class_means.get(r[cls_col], 0.0)
            if pd.notna(r[proj_col]) else r[proj_col],
            axis=1
        )
    return out


def main():
    if not SHIP_2223.exists():
        print("=" * 70)
        print("MISSING: 22-23 v6 ship CSV")
        print(f"Expected at: {SHIP_2223}")
        print("=" * 70)
        print()
        print("Build it first per docs/forward_validation_spec_v6_22_23.md")
        print("(Requires firing v4-lite NB2 Stan fit retargeted to 2021-22 prior + ")
        print("v3/v4/v5/v6 wrappers. NOT TO BE FIRED WITHOUT EXPLICIT CONFIRMATION.)")
        sys.exit(1)

    print("Loading 22-23 ship + actuals...")
    df_2223 = pd.read_csv(SHIP_2223)
    df_2223["nba_api_id"] = df_2223["nba_api_id"].astype(int)
    df_2223 = attach_features_for_season(df_2223, "2022-23", target_year=2022)
    df_2223 = attach_actual_residuals(df_2223, "2022-23")
    df_2223 = df_2223.dropna(subset=["PTS_residual"])
    print(f"  22-23 cohort with actuals: {len(df_2223)}")

    print("\nDeriving offsets from 22-23 (top-1 class per stat, SNR>=1.5)...")
    offset_table, used_classes = derive_offsets_from_22_23(df_2223)
    if not offset_table:
        print("\n  No (stat, class) survived SNR>=1.5 in 22-23. Forward validation rejects.")
        return

    print("\nLoading 23-24 ship + actuals...")
    df_2324 = pd.read_csv(SHIP_2324)
    df_2324["nba_api_id"] = df_2324["nba_api_id"].astype(int)
    df_2324 = attach_features_for_season(df_2324, "2023-24", target_year=2023)
    df_2324 = attach_actual_residuals(df_2324, "2023-24")
    df_2324 = df_2324.dropna(subset=["PTS_residual"])
    print(f"  23-24 cohort with actuals: {len(df_2324)}")

    print("\nApplying 22-23-derived offsets to 23-24 projections...")
    df_2324_corrected = apply_external_offsets_to_2324(
        df_2324, offset_table, used_classes)

    base_mae = per_stat_mae(df_2324)
    new_mae = per_stat_mae(df_2324_corrected)

    print("\n" + "=" * 70)
    print("FORWARD VALIDATION: offsets from 22-23 -> 23-24 MAE")
    print("=" * 70)
    rows = []
    for stat in STATS_WITH_ACTUAL:
        b = base_mae.get(stat, np.nan)
        a = new_mae.get(stat, np.nan)
        delta = a - b if not (np.isnan(b) or np.isnan(a)) else np.nan
        pct = 100 * delta / b if b > 0 else np.nan
        rows.append({"stat": stat, "class_used": used_classes.get(stat, "—"),
                      "base": b, "abl": a, "pct": pct})
    out = pd.DataFrame(rows)
    out["base"] = out["base"].apply(lambda x: f"{x:.4f}")
    out["abl"] = out["abl"].apply(lambda x: f"{x:.4f}")
    out["pct"] = out["pct"].apply(lambda x: f"{x:+.2f}%" if not pd.isna(x) else "")
    print(out.to_string(index=False))
    pcts = [100 * (new_mae[s] - base_mae[s]) / base_mae[s]
            for s in STATS_WITH_ACTUAL if s in new_mae and base_mae.get(s, 0) > 0]
    comp = np.mean(pcts)
    print(f"\n  Composite avg pct: {comp:+.2f}%")

    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    if comp < -1.0:
        print(f"  STRONG forward generalization (composite {comp:+.2f}%). Ship v6.1.")
    elif comp < -0.3:
        print(f"  MODERATE forward generalization ({comp:+.2f}%). Ship with shrinkage.")
    elif comp < 0.3:
        print(f"  WASH ({comp:+.2f}%). Offsets are season-specific. Do not ship.")
    else:
        print(f"  REJECTED (composite {comp:+.2f}%). Offsets actively harm forward.")


if __name__ == "__main__":
    main()
