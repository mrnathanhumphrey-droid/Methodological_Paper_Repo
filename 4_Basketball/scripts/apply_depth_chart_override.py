"""Depth-chart-aware MPG override: consume the live Rotowire depth chart and
adjust per-player MPG when the player's current role differs from what rolling
priors suggest.

Architecture decision (documented after failed redistribution-from-rolling-MPG
attempt at scripts/build_mpg_redistribution_model.py): empirical minutes
redistribution is too diffuse for a per-position lookup. Instead, consume the
LIVE depth-chart fetcher's role assignments directly — depth_order=1 means
"starting tier" regardless of what the player's rolling MPG was last month.

Rule:
  For each player on the v6.1 LOCKED ship CSV:
    1. Look up current depth_order in Rotowire snapshot (most recent fetch).
    2. Compute tier_mpg = season-typical MPG at that team+depth from
       derived_depth_chart (24-25 medians).
    3. Compute override_factor: only apply when the rolling-prior MPG and
       tier_mpg disagree by more than MPG_MISMATCH_THRESHOLD. This avoids
       overriding players whose rolling MPG already reflects their role.
    4. Blend: override_mpg = w_tier × tier_mpg + (1 − w_tier) × rolling_mpg
       where w_tier = 0.6 when mismatch detected, 0.0 otherwise.
    5. Scale every cat by override_mpg / rolling_mpg.

Reads:
  audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv
  data/parquet/depth_charts_rotowire.parquet (most recent snapshot)
  data/parquet/derived_depth_chart.parquet (24-25 tier MPG)
  data/parquet/player_metadata_enriched.parquet (name → nba_api_id mapping)

Writes:
  audit_runs/unified_ship_v6_3_depth_aware_2025_26/per_player_projections_2025-26.csv
  audit_runs/unified_ship_v6_3_depth_aware_2025_26/override_log.csv (which players changed and by how much)
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from pathlib import Path
import numpy as np
import pandas as pd

PQ = Path("data/parquet")
SHIP_IN = Path("audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv")
OUT_DIR = Path("audit_runs/unified_ship_v6_3_depth_aware_2025_26")
SHIP_OUT = OUT_DIR / "per_player_projections_2025-26.csv"
LOG_OUT = OUT_DIR / "override_log.csv"

MPG_MISMATCH_THRESHOLD = 5.0   # only override if |rolling - tier| > 5 min
W_TIER_ON_MISMATCH = 0.6       # blend weight: 60% tier, 40% rolling
TIER_CAP_HIGH = 38.0           # never project above this
TIER_CAP_LOW = 4.0             # never project below this for active players
MAX_SCALE_FACTOR = 2.0         # cap upward scaling — per-min rates from low-MPG samples are unreliable
MIN_ROLLING_MPG_FOR_OVERRIDE = 5.0  # skip override if rolling MPG is too low to be a reliable base for scaling

# Per-game stat columns affected (means scale linearly with MPG)
SCALE_COLS = [
    "PTS_per_game", "PTS_per_game_sd",
    "REB_per_game", "REB_per_game_sd",
    "AST_per_game", "AST_per_game_sd",
    "STL_per_game", "STL_per_game_sd",
    "BLK_per_game", "BLK_per_game_sd",
    "TOV_per_game", "TOV_per_game_sd",
    "FGM_per_game", "FGM_per_game_sd",
    "FGA_per_game", "FGA_per_game_sd",
    "FG3M_per_game", "FG3M_per_game_sd",
    "FG3A_per_game", "FG3A_per_game_sd",
    "FTM_per_game", "FTM_per_game_sd",
    "FTA_per_game", "FTA_per_game_sd",
]


def build_tier_mpg_lookup() -> dict:
    """Per (team_abbr, depth_order) median MPG from 24-25 derived_depth_chart."""
    ddc = pd.read_parquet(PQ / "derived_depth_chart.parquet")
    last = ddc[ddc["season"] == "2024-25"].copy()
    by_td = last.groupby(["team_abbr", "depth_order"])["mpg"].median().reset_index()
    out = {}
    for _, r in by_td.iterrows():
        out[(r["team_abbr"], int(r["depth_order"]))] = float(r["mpg"])
    # Fallback: pooled-across-teams median per depth
    pooled = last.groupby("depth_order")["mpg"].median().to_dict()
    out["_pooled"] = {int(k): float(v) for k, v in pooled.items()}
    return out


def _normalize_name(s: str) -> str:
    """Strip Jr./Sr./III, accents, punctuation; lower."""
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s)).encode("ASCII", "ignore").decode("ASCII")
    s = s.lower().strip()
    for suffix in (" jr.", " jr", " sr.", " sr", " iii", " ii", " iv"):
        if s.endswith(suffix):
            s = s[: -len(suffix)].strip()
    s = s.replace(".", "").replace("'", "").replace("-", " ")
    s = " ".join(s.split())  # collapse whitespace
    return s


def build_name_to_id() -> dict[str, int]:
    """Best-effort name normalization → nba_api_id from player_metadata_enriched.

    Multiple keys per player (exact + normalized) for matching against
    depth-chart names that may omit Jr./accents."""
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    meta["nba_api_id"] = meta["nba_api_id"].astype(int)
    out = {}
    for _, r in meta.iterrows():
        name = str(r["name"]).strip()
        out[name] = int(r["nba_api_id"])
        out[name.lower()] = int(r["nba_api_id"])
        out[_normalize_name(name)] = int(r["nba_api_id"])
    return out


def lookup_id(name_to_id: dict, raw_name: str) -> int | None:
    if pd.isna(raw_name):
        return None
    s = str(raw_name).strip()
    if s in name_to_id:
        return name_to_id[s]
    if s.lower() in name_to_id:
        return name_to_id[s.lower()]
    norm = _normalize_name(s)
    return name_to_id.get(norm)


def load_current_depth_chart() -> pd.DataFrame:
    """Load most recent Rotowire snapshot.

    Returns: (team_abbr, player_name, depth_order, position) — one row per
    (team, player) keyed to the player's minimum depth_order observed
    (handles multi-position eligible players)."""
    dc = pd.read_parquet(PQ / "depth_charts_rotowire.parquet")
    dc = dc.copy()
    # Most recent snapshot only
    latest_date = dc["snapshot_date"].max()
    dc = dc[dc["snapshot_date"] == latest_date].copy()
    # Collapse multi-position rows to the player's lowest (= best) depth_order
    grp = dc.groupby(["team_abbr", "player_name"]).agg(
        depth_order=("depth_order", "min"),
        position=("position", "first"),
        two_way=("two_way", "first"),
    ).reset_index()
    grp["depth_order"] = grp["depth_order"].astype(int)
    return grp


def main():
    if not SHIP_IN.exists():
        raise FileNotFoundError(f"v6.1 LOCKED ship not found: {SHIP_IN}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    ship = pd.read_csv(SHIP_IN)
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    print(f"Ship rows: {len(ship)}")

    tier_lookup = build_tier_mpg_lookup()
    name_to_id = build_name_to_id()
    dc = load_current_depth_chart()
    snapshot_date = pd.read_parquet(PQ / "depth_charts_rotowire.parquet")["snapshot_date"].max()
    print(f"Rotowire depth chart snapshot date: {snapshot_date}")
    print(f"Depth chart rows: {len(dc)}")

    # Map depth chart rows to nba_api_id (with name normalization)
    dc["nba_api_id"] = dc["player_name"].apply(lambda n: lookup_id(name_to_id, n))
    matched = dc["nba_api_id"].notna().sum()
    print(f"Depth chart name → nba_api_id matched: {matched}/{len(dc)} ({matched/len(dc):.1%})")
    if matched < len(dc):
        unmatched = dc[dc["nba_api_id"].isna()]["player_name"].unique()
        print(f"  unmatched names: {sorted(unmatched.tolist())[:10]}{'...' if len(unmatched) > 10 else ''}")

    dc_keyed = dc.dropna(subset=["nba_api_id"]).copy()
    dc_keyed["nba_api_id"] = dc_keyed["nba_api_id"].astype(int)

    # Build tier_mpg per row
    def tier_mpg_for(team, depth):
        if (team, depth) in tier_lookup:
            return tier_lookup[(team, depth)]
        return tier_lookup["_pooled"].get(depth, tier_lookup["_pooled"].get(2, 18.0))

    dc_keyed["tier_mpg"] = [
        tier_mpg_for(r["team_abbr"], int(r["depth_order"])) for _, r in dc_keyed.iterrows()
    ]

    # Join to ship — left join so we keep all ship rows even if no depth chart entry
    merged = ship.merge(
        dc_keyed[["nba_api_id", "depth_order", "tier_mpg", "two_way"]],
        on="nba_api_id", how="left"
    )

    # For ship rows without a depth-chart entry: no override (keep rolling MPG)
    merged["has_dc"] = merged["depth_order"].notna()
    n_no_dc = (~merged["has_dc"]).sum()
    print(f"Ship players without current depth-chart entry: {n_no_dc} (no override applied)")

    # Compute override
    merged["rolling_mpg"] = merged["mpg"]
    merged["mismatch"] = (merged["tier_mpg"] - merged["rolling_mpg"]).abs()
    # Don't override when rolling MPG is too low to be a reliable scaling base
    # (per-minute rates from 1-3 mpg samples are noise). For those players,
    # accept the tier MPG won't fix per-minute rates — leave them at baseline.
    merged["reliable_base"] = merged["rolling_mpg"] >= MIN_ROLLING_MPG_FOR_OVERRIDE
    merged["apply_override"] = (
        merged["has_dc"]
        & (merged["mismatch"] > MPG_MISMATCH_THRESHOLD)
        & merged["reliable_base"]
    )
    # Two-way contracts: cap MPG lower (limited NBA availability)
    merged.loc[merged["two_way"] == True, "apply_override"] = (
        merged.loc[merged["two_way"] == True, "apply_override"]
        & (merged.loc[merged["two_way"] == True, "tier_mpg"] < merged.loc[merged["two_way"] == True, "rolling_mpg"])
    )

    merged["override_mpg"] = merged["rolling_mpg"].copy()
    apply_mask = merged["apply_override"]
    merged.loc[apply_mask, "override_mpg"] = (
        W_TIER_ON_MISMATCH * merged.loc[apply_mask, "tier_mpg"]
        + (1.0 - W_TIER_ON_MISMATCH) * merged.loc[apply_mask, "rolling_mpg"]
    )
    merged["override_mpg"] = merged["override_mpg"].clip(lower=TIER_CAP_LOW, upper=TIER_CAP_HIGH)

    # Compute scale factor + cap upward scaling (low-MPG → starter scaling is
    # already filtered out by MIN_ROLLING_MPG_FOR_OVERRIDE, but cap as belt+suspenders)
    raw_scale = np.where(
        merged["rolling_mpg"] > 0,
        merged["override_mpg"] / merged["rolling_mpg"],
        1.0
    )
    merged["scale_factor"] = np.clip(raw_scale, 0.4, MAX_SCALE_FACTOR)

    # Apply scale to per-game cat columns
    out = merged.copy()
    for col in SCALE_COLS:
        if col in out.columns:
            out[col] = out[col] * out["scale_factor"]
    out["mpg"] = out["override_mpg"]

    # Save the override log
    log = merged[merged["apply_override"]][[
        "nba_api_id", "name", "depth_order", "tier_mpg",
        "rolling_mpg", "override_mpg", "scale_factor"
    ]].copy()
    log = log.sort_values("scale_factor")

    print()
    print(f"Override applied to {apply_mask.sum()} players")
    print(f"  → bumped UP (scale > 1.0): {(merged['scale_factor'] > 1.001).sum()}")
    print(f"  → cut DOWN (scale < 1.0):  {(merged['scale_factor'] < 0.999).sum()}")

    if apply_mask.sum() > 0:
        print()
        print("Sample of biggest BUMPS:")
        bumps = log.sort_values("scale_factor", ascending=False).head(8)
        print(bumps[["name", "depth_order", "tier_mpg", "rolling_mpg", "override_mpg", "scale_factor"]].to_string(index=False))
        print()
        print("Sample of biggest CUTS:")
        cuts = log.sort_values("scale_factor", ascending=True).head(8)
        print(cuts[["name", "depth_order", "tier_mpg", "rolling_mpg", "override_mpg", "scale_factor"]].to_string(index=False))

    # Drop helper columns before writing
    drop_cols = ["depth_order", "tier_mpg", "two_way", "has_dc", "mismatch",
                 "apply_override", "rolling_mpg", "override_mpg", "scale_factor",
                 "reliable_base"]
    out = out.drop(columns=[c for c in drop_cols if c in out.columns])
    out.to_csv(SHIP_OUT, index=False)
    log.to_csv(LOG_OUT, index=False)
    print()
    print(f"Wrote {len(out)} rows -> {SHIP_OUT}")
    print(f"Override log ({len(log)} entries) -> {LOG_OUT}")


if __name__ == "__main__":
    main()
