"""Build the Sloan-paper headline scatter: metadata-Forward players in the
2019-26 qualifying union by (height_inches, REB_per_36), with the 46
metadata-Forward -> adjudicated-Center flip players highlighted in red.

Output:
- D:/NBA Projections/paper_draft/figures/forward_misbucket_scatter.png
- D:/NBA Projections/paper_draft/figures/forward_misbucket_scatter.svg

Per the Sloan paper §3-§5 cross-league discipline. Uses the v1.2 adjudication
artifact (SHA256 eb615269... locked under commit 1bfdb4c).
"""
import json
import sys
from pathlib import Path

# Force UTF-8 stdout so player names with diacritics print on Windows
sys.stdout.reconfigure(encoding="utf-8")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

ROOT = Path("D:/NBA Projections")
META_PATH = ROOT / "data/parquet/player_metadata_enriched.parquet"
BOX_PATH = ROOT / "data/parquet/historical_box_scores.parquet"
ADJ_PATH = ROOT / "RMD_SRC_PIPELINE/results/position_adjudication_v12.json"
OUT_DIR = ROOT / "paper_draft/figures"
OUT_PNG = OUT_DIR / "forward_misbucket_scatter.png"
OUT_SVG = OUT_DIR / "forward_misbucket_scatter.svg"

# Labels for the 8 most recognizable F->C flips per Sloan paper §5.4.1 narrative
LABEL_PRIORITY = [
    "Anthony Davis", "Giannis Antetokounmpo", "Kevin Love", "Mason Plumlee",
    "Kristaps Porziņģis", "Kelly Olynyk", "Dwight Powell", "Taj Gibson",
]

SEASONS_IN_WINDOW = [
    "2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26",
]
MIN_GAMES_TOTAL = 30  # need enough minutes to be visible on the scatter

# Filter to plausible Forward height range; clip outliers
HEIGHT_MIN = 72  # 6'0"
HEIGHT_MAX = 90  # 7'6"
REB36_MAX = 18.0  # cap for visualization


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    meta = pd.read_parquet(META_PATH)
    print(f"Loaded metadata: {len(meta)} players")

    # Load adjudication artifact
    with open(ADJ_PATH, encoding="utf-8") as f:
        adj = json.load(f)
    print(f"Loaded {len(adj['verdicts'])} adjudication verdicts")

    # Build flip set: metadata=Forward -> adjudicated=Center
    flip_ids = set()
    flip_names = []
    for v in adj["verdicts"]:
        if v["metadata_bucket_v1"] == "Forward" and v["adjudicated_bucket"] == "Center":
            flip_ids.add(int(v["nba_api_id"]))
            flip_names.append(v["name"])
    print(f"F -> C flip count: {len(flip_ids)}")
    print(f"Sample flips: {flip_names[:10]}")

    # Filter metadata to Forwards
    forwards = meta[meta["position"] == "Forward"].copy()
    print(f"Metadata Forwards (all-time): {len(forwards)}")

    # Restrict to 2019-26 window: must have at least one season in the window
    in_window = forwards["seasons_active"].apply(
        lambda s: any(season in SEASONS_IN_WINDOW for season in (s if isinstance(s, list) or hasattr(s, '__iter__') else []))
    )
    forwards = forwards[in_window].copy()
    print(f"Forwards with 2019-26 activity: {len(forwards)}")

    # Load box scores, filter to window + min games
    bs = pd.read_parquet(BOX_PATH, columns=["nba_api_id", "season", "REB", "minutes"])
    bs = bs[bs["season"].isin(SEASONS_IN_WINDOW)]
    print(f"Box score rows in window: {len(bs)}")

    # Aggregate per player: total minutes, total REB
    agg = bs.groupby("nba_api_id").agg(
        n_games=("REB", "size"),
        total_minutes=("minutes", "sum"),
        total_reb=("REB", "sum"),
    ).reset_index()
    agg["REB_per_36"] = (agg["total_reb"] / agg["total_minutes"]) * 36.0
    agg = agg[agg["n_games"] >= MIN_GAMES_TOTAL]
    print(f"Players passing min-games filter: {len(agg)}")

    # Join metadata
    forwards = forwards.merge(agg, on="nba_api_id", how="inner")
    print(f"Forward players plotted: {len(forwards)}")

    # Mark flip players
    forwards["is_flip"] = forwards["nba_api_id"].isin(flip_ids)
    n_flip_on_plot = forwards["is_flip"].sum()
    print(f"Flip players present on plot: {n_flip_on_plot} / {len(flip_ids)}")

    # Clip outliers for visualization (don't drop, just clip)
    forwards["REB_per_36_clip"] = forwards["REB_per_36"].clip(upper=REB36_MAX)
    forwards["height_inches_clip"] = forwards["height_inches"].clip(lower=HEIGHT_MIN, upper=HEIGHT_MAX)

    # Plot
    fig, ax = plt.subplots(figsize=(10, 7))

    # Non-flip Forwards: light gray
    non_flip = forwards[~forwards["is_flip"]]
    ax.scatter(
        non_flip["height_inches_clip"], non_flip["REB_per_36_clip"],
        s=22, alpha=0.35, color="#888888", edgecolor="none",
        label=f"metadata-Forward, not flipped (n={len(non_flip)})",
    )

    # Flip players: red
    flip = forwards[forwards["is_flip"]]
    ax.scatter(
        flip["height_inches_clip"], flip["REB_per_36_clip"],
        s=70, alpha=0.85, color="#d62728", edgecolor="black", linewidth=0.6,
        label=f"metadata-F → adjudicated-C (n={len(flip)} of 46)",
        zorder=3,
    )

    # Label priority players if present
    for nm in LABEL_PRIORITY:
        row = flip[flip["name"] == nm]
        if len(row) == 0:
            print(f"  [warn] priority label not found in flip set: {nm}")
            continue
        r = row.iloc[0]
        # nudge label slightly above and right of the marker
        ax.annotate(
            r["name"],
            xy=(r["height_inches_clip"], r["REB_per_36_clip"]),
            xytext=(4, 4), textcoords="offset points",
            fontsize=8.5, fontweight="bold", color="#222222",
            zorder=4,
        )

    # NBA-typical height boundary annotations
    ax.axvline(82, color="#444444", linestyle=":", linewidth=0.8, alpha=0.6)
    ax.text(82.1, ax.get_ylim()[1] * 0.05, "6'10\"", fontsize=8, color="#444444",
            rotation=0, va="bottom", ha="left")

    ax.set_xlabel("Height (inches)", fontsize=11)
    ax.set_ylabel("REB per 36 (2019-26 window)", fontsize=11)
    ax.set_title(
        "NBA metadata-Forward players, 2019–26 qualifying union\n"
        "Adjudication identifies 46 on-court Centers labeled as Forward by the metadata",
        fontsize=12, fontweight="bold",
    )
    ax.legend(loc="upper left", framealpha=0.92, fontsize=9)
    ax.grid(True, alpha=0.25, linestyle="--", linewidth=0.5)
    ax.set_xlim(HEIGHT_MIN - 0.5, HEIGHT_MAX + 0.5)
    ax.set_ylim(0, REB36_MAX + 0.5)

    # Source footer
    fig.text(
        0.02, 0.01,
        "Source: NBA player_metadata_enriched + historical_box_scores; adjudication artifact SHA256 eb615269... (commit 1bfdb4c)",
        fontsize=7, color="#666666",
    )

    plt.tight_layout(rect=[0, 0.025, 1, 1])
    plt.savefig(OUT_PNG, dpi=180, bbox_inches="tight")
    plt.savefig(OUT_SVG, bbox_inches="tight")
    print(f"\nWrote {OUT_PNG}")
    print(f"Wrote {OUT_SVG}")


if __name__ == "__main__":
    main()
