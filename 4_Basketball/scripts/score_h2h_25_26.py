"""Direct h2h scoring on consensus_projections_dated.parquet 25-26 preseason data.

Drops in fantasypros (271 players, 2025-10-27 snap) + hashtagbasketball
(30 players, 2025-10-09 snap) for head-to-head vs v6.1 LOCKED.
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
import re
import unicodedata
from pathlib import Path

import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
OUT_DIR = REPO / "audit_runs" / "head_to_head_25_26"
OUT_DIR.mkdir(parents=True, exist_ok=True)

V6_1_SHIP = REPO / "audit_runs" / "unified_ship_v6_1_2025_26" / "per_player_projections_2025-26.csv"

# Map their schema -> canonical
THEIR_TO_OURS = {
    "pts_proj": "pts", "reb_proj": "reb", "ast_proj": "ast",
    "stl_proj": "stl", "blk_proj": "blk", "tov_proj": "tov",
    "threepm_proj": "fg3m", "min_proj": "mpg",
}
SCORED_STATS = ["pts", "reb", "ast", "stl", "blk", "tov", "fg3m", "mpg"]


def normalize_name(s):
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s]", " ", s).lower()
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv|v)$", "", s)
    return s


def main():
    print("[load] consensus_projections_dated.parquet")
    cp = pd.read_parquet(PQ / "consensus_projections_dated.parquet")
    s26 = cp[(cp["season"] == "2025-26") &
              (cp["projection_type"] == "preseason")].copy()
    print(f"  25-26 preseason rows: {len(s26)}")
    print(f"  sources: {s26['source'].value_counts().to_dict()}")

    # Drop the rankings-only source (no per-stat data we can score)
    s26 = s26[s26["source"] != "hashtagbasketball_rankings"]

    # Pick the latest snapshot per source per player
    s26 = (s26.sort_values("snapshot_date")
                .drop_duplicates(["source", "player_name"], keep="last"))

    print("\n[load] metadata")
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    sup = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "rookie_metadata_supplement.parquet"
    if sup.exists():
        s = pd.read_parquet(sup)
        meta = pd.concat([meta[["nba_api_id", "name"]],
                            s[["nba_api_id", "name"]]], ignore_index=True)
    meta["norm"] = meta["name"].apply(normalize_name)
    name_to_id = dict(zip(meta["norm"], meta["nba_api_id"].astype(int)))

    s26["norm"] = s26["player_name"].apply(normalize_name)
    s26["nba_api_id"] = s26["norm"].map(name_to_id)
    matched = s26[s26["nba_api_id"].notna()].copy()
    matched["nba_api_id"] = matched["nba_api_id"].astype(int)
    unmatched = s26[s26["nba_api_id"].isna()][["source", "player_name"]]
    print(f"  matched: {len(matched)} / {len(s26)}")
    print(f"  unmatched: {len(unmatched)}")
    if len(unmatched) > 0:
        print(unmatched.to_string(index=False))

    print("\n[load] 25-26 actuals")
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx = bx[(bx["season"] == "2025-26") &
              (bx["season_type"] == "Regular Season")].copy()
    bx["nba_api_id"] = bx["nba_api_id"].astype(int)
    bx["minutes"] = pd.to_numeric(bx["minutes"], errors="coerce")
    bx = bx[bx["minutes"] > 0]
    actuals = bx.groupby("nba_api_id").agg(
        gp_actual=("game_id", "nunique"),
        pts_actual=("PTS", "mean"), reb_actual=("REB", "mean"),
        ast_actual=("AST", "mean"), stl_actual=("STL", "mean"),
        blk_actual=("BLK", "mean"), tov_actual=("TOV", "mean"),
        fg3m_actual=("FG3M", "mean"), mpg_actual=("minutes", "mean"),
    ).reset_index()
    print(f"  actuals players: {len(actuals)}")

    print("\n[load] v6.1 LOCKED ship")
    ship = pd.read_csv(V6_1_SHIP)
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    v6 = ship[["nba_api_id", "name"]].copy()
    v6_map = {"PTS_per_game": "pts", "REB_per_game": "reb", "AST_per_game": "ast",
                "STL_per_game": "stl", "BLK_per_game": "blk", "TOV_per_game": "tov",
                "FG3M_per_game": "fg3m", "mpg": "mpg"}
    for src_c, dst in v6_map.items():
        if src_c in ship.columns:
            v6[f"{dst}_v6_1"] = ship[src_c]
    print(f"  v6.1 ship rows: {len(v6)}")

    # Cohort tags from v6.1 ship
    cohort_meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    if sup.exists():
        sp = pd.read_parquet(sup)
        cohort_meta = pd.concat([cohort_meta[["nba_api_id", "draft_year", "debut_year", "position"]],
                                   sp[["nba_api_id", "draft_year", "debut_year", "position"]]],
                                  ignore_index=True)
    cohort_meta["nba_api_id"] = cohort_meta["nba_api_id"].astype(int)
    cohort_meta["years_pro"] = cohort_meta["debut_year"].where(
        cohort_meta["debut_year"].notna(), cohort_meta["draft_year"] + 1)
    cohort_meta["years_pro"] = 2025 - cohort_meta["years_pro"]
    cohort_meta["ypb"] = pd.cut(cohort_meta["years_pro"],
                                  bins=[-1, 0, 3, 7, 12, 30],
                                  labels=["rookie", "1-3", "4-7", "8-12", "13+"]).astype(str)
    cohort_meta["cohort"] = cohort_meta["ypb"].apply(
        lambda y: "rookie" if y == "rookie" else
                  ("soph" if y == "1-3" else "vet"))

    # Score per source
    print("\n=== SCORING ===")
    rows = []
    for source in matched["source"].unique():
        sub = matched[matched["source"] == source].copy()
        sub = sub.merge(actuals, on="nba_api_id", how="inner")
        sub = sub.merge(v6[["nba_api_id"] + [c for c in v6.columns if c.endswith("_v6_1")]],
                          on="nba_api_id", how="inner")
        sub = sub.merge(cohort_meta[["nba_api_id", "cohort"]],
                          on="nba_api_id", how="left")
        n_total = len(sub)
        print(f"\n--- {source} (n={n_total}) ---")
        for stat in SCORED_STATS:
            their_col = next((c for c, s in THEIR_TO_OURS.items() if s == stat), None)
            if their_col is None or their_col not in sub.columns:
                continue
            actual_col = f"{stat}_actual"
            v6_col = f"{stat}_v6_1"
            df = sub.dropna(subset=[their_col, actual_col, v6_col]).copy()
            if df.empty:
                continue
            their_mae = (df[their_col] - df[actual_col]).abs().mean()
            their_bias = (df[their_col] - df[actual_col]).mean()
            v6_mae = (df[v6_col] - df[actual_col]).abs().mean()
            v6_bias = (df[v6_col] - df[actual_col]).mean()
            delta = v6_mae - their_mae
            delta_pct = delta / their_mae * 100 if their_mae else 0
            rows.append({
                "source": source, "stat": stat, "cohort": "ALL",
                "n": len(df),
                "their_mae": their_mae, "their_bias": their_bias,
                "v6_1_mae": v6_mae, "v6_1_bias": v6_bias,
                "delta_mae": delta, "delta_pct": delta_pct,
            })
            print(f"  {stat:>5}: n={len(df):3} "
                  f"their MAE={their_mae:.3f}  v6.1 MAE={v6_mae:.3f}  "
                  f"Δ={delta:+.3f} ({delta_pct:+5.1f}%)  "
                  f"bias their={their_bias:+.2f} v6.1={v6_bias:+.2f}")
            # Per-cohort breakdown
            for cohort_v in ["vet", "soph", "rookie"]:
                dfc = df[df["cohort"] == cohort_v]
                if len(dfc) < 5:
                    continue
                cm = (dfc[their_col] - dfc[actual_col]).abs().mean()
                vm = (dfc[v6_col] - dfc[actual_col]).abs().mean()
                d = vm - cm
                dp = d / cm * 100 if cm else 0
                rows.append({
                    "source": source, "stat": stat, "cohort": cohort_v,
                    "n": len(dfc),
                    "their_mae": cm, "their_bias": (dfc[their_col] - dfc[actual_col]).mean(),
                    "v6_1_mae": vm, "v6_1_bias": (dfc[v6_col] - dfc[actual_col]).mean(),
                    "delta_mae": d, "delta_pct": dp,
                })
                print(f"        {cohort_v:>6}: n={len(dfc):3} "
                      f"their={cm:.3f}  v6.1={vm:.3f}  Δ={d:+.3f} ({dp:+5.1f}%)")

    out = pd.DataFrame(rows)
    out_csv = OUT_DIR / "h2h_per_source_mae.csv"
    out.to_csv(out_csv, index=False)
    print(f"\n[save] {out_csv}")

    if len(unmatched) > 0:
        unmatched.to_csv(OUT_DIR / "h2h_unmatched_names.csv", index=False)


if __name__ == "__main__":
    main()
