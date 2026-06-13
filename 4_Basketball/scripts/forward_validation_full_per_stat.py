"""Full per-stat forward validation: 22-23 → 23-24 across PTS/REB/AST/STL/BLK/TOV.

Consumes audit dirs created by fire_v6_22_23_chain.sh.

For each stat:
  1. Load 22-23 audit (per_player_projections.csv)
  2. Compute residuals = actual - proj_mean
  3. Attach class features (position, age_bucket, offseason_traded, years_pro_bucket,
     draft_pick_tier, new_coach_this_season, mid_season_change) AS OF 22-23
  4. Run noise-floor SNR on each class
  5. Pick top-1 at SNR >= 1.5
  6. Compute class mean residuals
  7. Apply to 23-24 v6 ship via 23-24 class membership
  8. Compare 23-24 PTS/REB/etc MAE before/after
  9. Verdict per stat

Final output: VALIDATED_OFFSETS dict to paste into apply_v61_validated_offsets.py
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
SHIP_2324 = REPO / "audit_runs" / "unified_ship_v6" / "per_player_projections_2023-24.csv"

STATS = ["PTS", "REB", "AST", "STL", "BLK", "TOV"]
TRAIN_TAG = "2019-20-2020-21-2021-22"


def find_audit_dir(stat):
    """Find latest 22-23 audit dir for given stat."""
    pattern = f"skill_backtest_{stat}_phase4_v4_quadratic_tq_g_{TRAIN_TAG}__2022-23"
    candidates = list(REPO.glob(f"audit_runs/*/{pattern}"))
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.parent.name, reverse=True)
    return candidates[0]


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

    # Team
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    season_label = f"{target_year}-{str(target_year+1)[2:]}"
    s = box[box["season"] == season_label]
    team = s.groupby("nba_api_id")["team_abbr"].agg(
        lambda x: x.value_counts().idxmax()).reset_index()
    team.columns = ["nba_api_id", "team_for_season"]
    df = df.merge(team, on="nba_api_id", how="left")

    # Coaching flags
    cf = pd.read_parquet(PQ / "coaching_change_flags.parquet")
    cf_s = cf[cf["season"] == season_label][["team_abbr", "new_coach_this_season",
                                                "mid_season_change"]]
    df = df.merge(cf_s, left_on="team_for_season", right_on="team_abbr",
                   how="left", suffixes=("", "_cf"))
    df["new_coach_this_season"] = df["new_coach_this_season"].fillna(False).astype(bool)
    df["mid_season_change"] = df["mid_season_change"].fillna(False).astype(bool)

    # Offseason traded
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
    var = sub[res_col].var(ddof=1)
    n_per = grouped["count"].mean()
    se = np.sqrt(var / n_per)
    snr = sd_obs / se if se > 0 else np.nan
    return {"snr": snr, "means": dict(zip(grouped[class_col], grouped["mean"]))}


CLASSES = ["position", "age_bucket", "offseason_traded", "years_pro_bucket",
            "draft_pick_tier", "new_coach_this_season", "mid_season_change"]


def main():
    ship_2324 = pd.read_csv(SHIP_2324)
    ship_2324["nba_api_id"] = ship_2324["nba_api_id"].astype(int)
    ship_2324_feat = attach_class_features(ship_2324, target_year=2023)

    print("=" * 80)
    print("FULL PER-STAT FORWARD VALIDATION 22-23 -> 23-24")
    print("=" * 80)

    validated = {}  # stat -> {class_name: {class_value: offset}}
    rejected = {}   # stat -> reason

    for stat in STATS:
        print(f"\n----- {stat} -----")
        audit_dir = find_audit_dir(stat)
        if audit_dir is None:
            print(f"  NO AUDIT — skip. Run fire_v6_22_23_chain.sh first.")
            rejected[stat] = "no audit"
            continue
        print(f"  Audit: {audit_dir}")

        a22 = pd.read_csv(audit_dir / "per_player_projections.csv")
        a22["nba_api_id"] = a22["nba_api_id"].astype(int)
        a22 = a22.dropna(subset=["actual", "proj_mean"]).copy()
        a22[f"{stat}_residual"] = a22["actual"] - a22["proj_mean"]
        a22_feat = attach_class_features(a22, target_year=2022)

        # Find top-1 surviving class for stat
        candidates = []
        for c in CLASSES:
            r = noise_floor(a22_feat, c, f"{stat}_residual")
            if r and r["snr"] >= 1.5:
                candidates.append((c, r["snr"], r["means"]))
        if not candidates:
            print(f"  No surviving class at SNR>=1.5 in 22-23. REJECTED.")
            rejected[stat] = "no class survives 22-23"
            continue
        candidates.sort(key=lambda x: -x[1])
        top_cls, top_snr, top_means = candidates[0]
        print(f"  Top class: {top_cls} (SNR={top_snr:.2f})")
        print(f"  22-23 class means: " +
              ", ".join(f"{k}={v:+.3f}" for k, v in top_means.items()))

        # Apply to 23-24
        ship_2324_feat[f"{stat}_offset"] = ship_2324_feat[top_cls].map(top_means).fillna(0.0)
        ship_2324_feat[f"{stat}_proj_corrected"] = (
            ship_2324_feat[f"{stat}_proj"] + ship_2324_feat[f"{stat}_offset"])

        # Compute MAE before/after
        valid = ship_2324_feat.dropna(subset=[f"{stat}_actual", f"{stat}_proj"])
        b = (valid[f"{stat}_actual"] - valid[f"{stat}_proj"]).abs().mean()
        a = (valid[f"{stat}_actual"] - valid[f"{stat}_proj_corrected"]).abs().mean()
        delta_pct = 100 * (a - b) / b if b > 0 else 0
        print(f"  23-24 baseline MAE: {b:.4f}")
        print(f"  23-24 corrected MAE: {a:.4f}  ({delta_pct:+.2f}%)")

        # Verdict
        if delta_pct < -1.0:
            print(f"  -> STRONG forward generalization. Validated.")
            validated[stat] = {top_cls: top_means}
        elif delta_pct < -0.3:
            print(f"  -> MODERATE — ship with shrinkage.")
            # Cut offsets in half for shrinkage
            shrunk = {k: 0.5 * v for k, v in top_means.items()}
            validated[stat] = {top_cls: shrunk}
        else:
            print(f"  -> REJECTED — does not generalize.")
            rejected[stat] = f"delta_pct {delta_pct:+.2f}%"

        # Also check: do INDIVIDUAL class values agree across seasons?
        # Compute 23-24 class means within ship_2324_feat for same class
        s24_means = noise_floor(ship_2324_feat.assign(
            **{f"{stat}_residual": ship_2324_feat[f"{stat}_actual"] - ship_2324_feat[f"{stat}_proj"]}
        ), top_cls, f"{stat}_residual")
        if s24_means:
            agreed = []
            for k, v22 in top_means.items():
                v24 = s24_means["means"].get(k, np.nan)
                if not np.isnan(v24) and np.sign(v22) == np.sign(v24):
                    agreed.append(k)
            print(f"  Sign-agreement classes: {agreed}")

    # Print final spec
    print("\n" + "=" * 80)
    print("FINAL VALIDATED OFFSET TABLE (paste into apply_v61_validated_offsets.py)")
    print("=" * 80)
    if not validated:
        print("\n  NONE — no offsets survive cross-season validation.")
        print("  v6.1 = v6 (no class-offset patch).")
    else:
        for stat, spec in validated.items():
            for cls, means in spec.items():
                print(f"\n  {stat} via {cls}:")
                for k, v in means.items():
                    print(f"    {str(k):<14}  {v:+.3f}")

    if rejected:
        print(f"\nRejected stats: {rejected}")


if __name__ == "__main__":
    main()
