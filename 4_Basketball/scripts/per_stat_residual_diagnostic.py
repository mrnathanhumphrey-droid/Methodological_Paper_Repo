"""Per-stat noise-floor diagnostic: residuals on PTS/REB/AST/STL/BLK/TOV/FTA/FTM directly.

For each (stat, class) combination, run the Collatz noise-floor test.
Identifies which class structures are real for which stats — directly.

Then build a per-stat per-class offset ablation harness (NOT the MPG cascade)
that adds offsets to projected stat values directly, and measures MAE delta.

This avoids the v6 MPG/per-min compensation issue caught in the previous test.
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


def attach_features_and_residuals(base):
    """Adds position, age_bucket, offseason_traded, team_2324 + per-stat residuals."""
    df = base.copy()
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    df = df.merge(meta[["nba_api_id", "position", "birth_date"]],
                  on="nba_api_id", how="left")
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
    df["age_2023"] = (pd.Timestamp("2023-10-24") - df["birth_date"]).dt.days / 365.25
    df["age_bucket"] = pd.cut(df["age_2023"],
                               bins=[0, 24, 27, 30, 33, 50],
                               labels=["<=24", "25-26", "27-29", "30-32", "33+"]).astype(str)

    # team 23-24 (dominant)
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    s23 = box[box["season"] == "2023-24"]
    team_23 = s23.groupby("nba_api_id")["team_abbr"].agg(
        lambda x: x.value_counts().idxmax()).reset_index()
    team_23.columns = ["nba_api_id", "team_2324"]
    df = df.merge(team_23, on="nba_api_id", how="left")

    # offseason traded
    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    traded = set(tx[(tx["transaction_type"] == "trade") &
                    (tx["event_date"] >= "2023-04-15") &
                    (tx["event_date"] <= "2023-10-24") &
                    (tx["nba_api_id"].notna())]["nba_api_id"].astype(int))
    df["offseason_traded"] = df["nba_api_id"].isin(traded)

    # Per-stat residuals: residual = actual - projected, per-game basis (the *_proj
    # columns are per-game and *_actual matches per-game). Verify with nan handling.
    for stat in STATS_WITH_ACTUAL:
        proj = f"{stat}_proj"
        actual = f"{stat}_actual"
        if proj in df.columns and actual in df.columns:
            df[f"{stat}_residual"] = df[actual] - df[proj]
    return df


def noise_floor_for_class_stat(df, class_col, stat):
    """Run noise-floor test for a single (class, stat) combination."""
    res_col = f"{stat}_residual"
    if res_col not in df.columns:
        return None
    sub = df.dropna(subset=[class_col, res_col]).copy()
    grouped = sub.groupby(class_col, observed=True)[res_col].agg(["mean", "count"]).reset_index()
    grouped = grouped[grouped["count"] >= 2]
    if len(grouped) < 2:
        return None
    sd_obs = grouped["mean"].std(ddof=1)
    overall_var = sub[res_col].var(ddof=1)
    n_per_class = grouped["count"].mean()
    se_samp = np.sqrt(overall_var / n_per_class)
    snr = sd_obs / se_samp if se_samp > 0 else np.nan
    tau2 = max(0.0, sd_obs**2 - se_samp**2)
    return {
        "class": class_col, "stat": stat, "n_classes": len(grouped),
        "sd_observed": sd_obs, "se_sampling": se_samp, "snr": snr,
        "tau_corrected": np.sqrt(tau2),
        "class_means": dict(zip(grouped[class_col], grouped["mean"])),
        "class_counts": dict(zip(grouped[class_col], grouped["count"])),
    }


def apply_per_stat_offsets(base, offsets):
    """offsets: dict {stat: dict[nba_api_id -> delta]}.
    Returns shocked DF and MAE table."""
    df = base.copy()
    for stat, pid_to_delta in offsets.items():
        col = f"{stat}_proj"
        if col not in df.columns:
            continue
        df[col] = df.apply(
            lambda r: r[col] + pid_to_delta.get(int(r["nba_api_id"]), 0.0)
            if pd.notna(r[col]) else r[col],
            axis=1
        )
    return df


def loo_class_means(df, class_col, residual_col):
    """LOO per-class mean for each row."""
    sub = df.dropna(subset=[class_col, residual_col]).copy()
    out = {}
    for cls, idx in sub.groupby(class_col, observed=True).groups.items():
        idx = list(idx)
        for i in idx:
            others = [j for j in idx if j != i]
            mean = sub.loc[others, residual_col].mean() if others else 0.0
            out[i] = mean
    return out


def main():
    base = load_baseline()
    df = attach_features_and_residuals(base)
    df = df.dropna(subset=["PTS_residual"])
    print(f"Cohort with actuals: {len(df)}")

    # ============== STAGE 1: noise-floor across stats x classes ==============
    print("\n" + "=" * 78)
    print("PER-STAT NOISE-FLOOR DIAGNOSTIC")
    print("=" * 78)
    classes = ["position", "age_bucket", "offseason_traded"]
    rows = []
    for stat in STATS_WITH_ACTUAL:
        for c in classes:
            res = noise_floor_for_class_stat(df, c, stat)
            if res is None:
                continue
            rows.append({
                "stat": res["stat"], "class": res["class"],
                "snr": res["snr"], "sd_obs": res["sd_observed"],
                "se_samp": res["se_sampling"], "tau": res["tau_corrected"],
                "verdict": ("REAL" if res["snr"] >= 1.5 else
                            "marginal" if res["snr"] >= 1.05 else
                            "NOISE"),
            })
    snr_df = pd.DataFrame(rows)
    print(snr_df.to_string(index=False))

    # ============== STAGE 2: top per-class effects for each stat ==============
    print("\n" + "=" * 78)
    print("TOP CLASS EFFECTS PER STAT (mean residual)")
    print("=" * 78)
    for stat in STATS_WITH_ACTUAL:
        res_col = f"{stat}_residual"
        print(f"\n  -- {stat} --")
        for c in classes:
            sub = df.dropna(subset=[c, res_col])
            g = sub.groupby(c, observed=True)[res_col].agg(["mean", "count"]).reset_index()
            top = g.sort_values("mean", key=abs, ascending=False).head(3)
            for _, r in top.iterrows():
                print(f"    [{c}] {r[c]!s:<14}  resid={r['mean']:+.3f}  n={r['count']}")

    # ============== STAGE 3: build LOO per-stat per-class offsets and ablate ==============
    # Strategy: for each stat, ONLY apply offsets where SNR >= 1.5. Compose across
    # surviving classes (sum of class means).
    print("\n" + "=" * 78)
    print("PER-STAT OFFSET ABLATION (LOO, only SNR>=1.5 classes)")
    print("=" * 78)
    base_mae = per_stat_mae(base)

    # Build the offset map per stat
    surviving = {}  # stat -> list of class cols with snr >= 1.5
    for stat in STATS_WITH_ACTUAL:
        cols = []
        for c in classes:
            r = snr_df[(snr_df["stat"] == stat) & (snr_df["class"] == c)]
            if len(r) > 0 and r.iloc[0]["snr"] >= 1.5:
                cols.append(c)
        surviving[stat] = cols
        print(f"\n  {stat}: surviving classes = {cols}")

    # Build per-stat LOO offsets
    offsets = {}  # stat -> {pid: delta}
    for stat in STATS_WITH_ACTUAL:
        if not surviving[stat]:
            continue
        res_col = f"{stat}_residual"
        sub = df.dropna(subset=[res_col]).copy()
        loo_per_class = {}
        for c in surviving[stat]:
            loo_per_class[c] = loo_class_means(sub, c, res_col)
        # Compose
        per_stat_offset = {}
        for idx, row in sub.iterrows():
            pid = int(row["nba_api_id"])
            d = 0.0
            for c in surviving[stat]:
                d += loo_per_class[c].get(idx, 0.0)
            per_stat_offset[pid] = d
        offsets[stat] = per_stat_offset

    if not offsets:
        print("\n  No (stat, class) survived SNR>=1.5 — nothing to ablate.")
        return

    # Ablate
    print(f"\nApplying offsets to: {list(offsets.keys())}")
    shocked = apply_per_stat_offsets(base, offsets)
    new_mae = per_stat_mae(shocked)
    print(f"\n--- Per-stat MAE before/after (LOO offsets, SNR>=1.5 only) ---")
    rows = []
    for stat in sorted(set(list(base_mae.keys()) + list(new_mae.keys()))):
        b = base_mae.get(stat, np.nan)
        n = new_mae.get(stat, np.nan)
        delta = n - b if not (np.isnan(b) or np.isnan(n)) else np.nan
        pct = 100 * delta / b if b > 0 else np.nan
        rows.append({"stat": stat, "baseline": b, "ablated": n,
                      "delta": delta, "pct": pct})
    out = pd.DataFrame(rows)
    out["baseline"] = out["baseline"].apply(lambda x: f"{x:.4f}")
    out["ablated"] = out["ablated"].apply(lambda x: f"{x:.4f}")
    out["delta"] = out["delta"].apply(lambda x: f"{x:+.4f}")
    out["pct"] = out["pct"].apply(lambda x: f"{x:+.2f}%" if not pd.isna(x) else "")
    print(out.to_string(index=False))

    # Composite
    pcts = [100 * (new_mae[s] - base_mae[s]) / base_mae[s]
            for s in STATS_WITH_ACTUAL if s in new_mae and base_mae.get(s, 0) > 0]
    print(f"\n  Composite avg pct (8 stats): {np.mean(pcts):+.2f}%")

    # ============== STAGE 4: marginal-class ablation (SNR >= 1.05) ==============
    print("\n" + "=" * 78)
    print("PER-STAT OFFSET ABLATION (LOO, SNR>=1.05 — marginal included)")
    print("=" * 78)
    surviving_loose = {}
    for stat in STATS_WITH_ACTUAL:
        cols = []
        for c in classes:
            r = snr_df[(snr_df["stat"] == stat) & (snr_df["class"] == c)]
            if len(r) > 0 and r.iloc[0]["snr"] >= 1.05:
                cols.append(c)
        surviving_loose[stat] = cols

    offsets2 = {}
    for stat in STATS_WITH_ACTUAL:
        if not surviving_loose[stat]:
            continue
        res_col = f"{stat}_residual"
        sub = df.dropna(subset=[res_col]).copy()
        loo_per_class = {c: loo_class_means(sub, c, res_col) for c in surviving_loose[stat]}
        per_stat_offset = {}
        for idx, row in sub.iterrows():
            pid = int(row["nba_api_id"])
            d = sum(loo_per_class[c].get(idx, 0.0) for c in surviving_loose[stat])
            per_stat_offset[pid] = d
        offsets2[stat] = per_stat_offset

    shocked2 = apply_per_stat_offsets(base, offsets2)
    new_mae2 = per_stat_mae(shocked2)
    rows = []
    for stat in sorted(STATS_WITH_ACTUAL):
        b = base_mae.get(stat, np.nan)
        n = new_mae2.get(stat, np.nan)
        delta = n - b if not (np.isnan(b) or np.isnan(n)) else np.nan
        pct = 100 * delta / b if b > 0 else np.nan
        rows.append({"stat": stat,
                      "surviving_classes": surviving_loose[stat],
                      "baseline": f"{b:.4f}", "ablated": f"{n:.4f}",
                      "pct": f"{pct:+.2f}%" if not pd.isna(pct) else ""})
    print(pd.DataFrame(rows).to_string(index=False))
    pcts2 = [100 * (new_mae2[s] - base_mae[s]) / base_mae[s]
             for s in STATS_WITH_ACTUAL if s in new_mae2 and base_mae.get(s, 0) > 0]
    print(f"\n  Composite avg pct (loose, 8 stats): {np.mean(pcts2):+.2f}%")


if __name__ == "__main__":
    main()
