"""Edge-metric computation per PRE_REG_SCOUTS_v1.md §4.1.

For each (scout S, archetype × league cell C) with sufficient coverage:

  deviation_i      = scout_S_rank(i) - consensus_rank(i)
  outcome_score_i  ∈ {0, 1, 2, 3, 5} per archetype (bust=0, never_played=0,
                     role_player=1, rotation=2, starter=3, star=5)
  edge(S, C)       = corr(-deviation_i, outcome_score_i | i ∈ C)

Consensus rank = MEAN rank across NAMED scouts who covered prospect i.
We use only the §2.3 pre-reg named scouts to define consensus:
  vecenie_athletic, oconnor_ringer, hollinger_athletic,
  givony_espn, givony_draftexpress.
Tankathon (aggregator) is excluded from consensus by pre-reg design — it's
the F4 null control. We compare it AGAINST consensus, not part of it.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DR = Path(r"D:\Draft Resolve\data\parquet")
CELLS_PATH = Path(__file__).parent / "audit_runs" / "v1" / "prospect_cells.parquet"

# §2.3 pre-reg named scouts. These define CONSENSUS.
NAMED_SCOUTS = {
    "vecenie_athletic", "oconnor_ringer", "hollinger_athletic",
    "givony_espn", "givony_draftexpress",
}
# Tankathon is the aggregator null control.
AGGREGATOR_SCOUT = "tankathon_aggregator"

# Outcome score map per pre-reg §4.1
OUTCOME_SCORE = {
    "star": 5, "starter": 3, "rotation": 2, "role_player": 1,
    "bust": 0, "never_played": 0,
}


def load_scouts_and_outcomes() -> tuple[pd.DataFrame, pd.DataFrame]:
    ranks = pd.read_parquet(DR / "scout_ranks_raw.parquet")
    # Drop unmatched (no nba_api_id) — can't be tied to outcome
    ranks = ranks.dropna(subset=["nba_api_id"]).copy()
    ranks["nba_api_id"] = ranks["nba_api_id"].astype(int)

    outcomes_raw = pd.read_parquet(
        Path(r"D:\Draft Resolve\data\audit_runs\retrospective_v0\prospect_outcomes.parquet")
    )
    outcomes_raw["outcome_score"] = outcomes_raw["archetype"].map(OUTCOME_SCORE)
    outcomes = outcomes_raw[["nba_api_id", "archetype", "outcome_score",
                              "right_censored"]].rename(
        columns={"archetype": "career_archetype"}
    ).copy()
    return ranks, outcomes


def compute_consensus_rank(ranks: pd.DataFrame) -> pd.DataFrame:
    """Per (nba_api_id, draft_year), consensus = mean over named scouts."""
    named = ranks[ranks["scout"].isin(NAMED_SCOUTS)]
    consensus = (named.groupby(["nba_api_id", "draft_year"])["rank"]
                       .agg(consensus_rank="mean", n_scouts_covering="count")
                       .reset_index())
    return consensus


def attach_cells_and_outcomes(ranks: pd.DataFrame,
                               cells: pd.DataFrame,
                               outcomes: pd.DataFrame,
                               consensus: pd.DataFrame) -> pd.DataFrame:
    df = ranks.merge(
        cells[["nba_api_id", "archetype", "league", "cell"]],
        on="nba_api_id", how="left",
    )
    df = df.merge(outcomes, on="nba_api_id", how="left")
    df = df.merge(consensus, on=["nba_api_id", "draft_year"], how="left")
    df["deviation"] = df["rank"] - df["consensus_rank"]
    return df


def compute_edge_table(df_full: pd.DataFrame, min_cell_n: int = 15,
                        uncensored_cutoff: int = 2021) -> pd.DataFrame:
    """One row per (scout, cell) with n >= min_cell_n + uncensored cohort.

    Pre-reg §4.1 edge metric. Note we use uncensored outcomes (≤2021) so the
    outcome_score is meaningful.
    """
    sub = df_full[
        (df_full["draft_year"] <= uncensored_cutoff) &
        df_full["outcome_score"].notna() &
        df_full["consensus_rank"].notna() &
        df_full["n_scouts_covering"].fillna(0).ge(2)  # need ≥2 scouts for consensus
    ].copy()
    rows = []
    for (scout, cell), g in sub.groupby(["scout", "cell"]):
        n = len(g)
        if n < min_cell_n:
            continue
        # edge = corr(-deviation, outcome_score). Bigger NEGATIVE deviation
        # (scout ranked HIGHER than consensus) AND higher outcome = edge.
        r = (-g["deviation"]).astype(float).corr(g["outcome_score"].astype(float))
        if pd.isna(r):
            continue
        # Fisher-transform SE for the correlation: 1/sqrt(n-3)
        fisher_se = 1.0 / np.sqrt(max(n - 3, 1)) if n > 3 else np.nan
        rows.append({
            "scout": scout,
            "cell": cell,
            "n": n,
            "edge": r,
            "fisher_se": fisher_se,
            "mean_dev": g["deviation"].mean(),
            "in_prereg": scout in NAMED_SCOUTS,
            "is_aggregator": scout == AGGREGATOR_SCOUT,
        })
    out = pd.DataFrame(rows).sort_values(["cell", "edge"])
    return out


def main():
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    cells = pd.read_parquet(CELLS_PATH)
    ranks, outcomes = load_scouts_and_outcomes()
    consensus = compute_consensus_rank(ranks)
    df_full = attach_cells_and_outcomes(ranks, cells, outcomes, consensus)
    edge_table = compute_edge_table(df_full)
    print(f"Edge table: {len(edge_table)} (scout, cell) cells with n≥15")
    print()
    print("Per scout — number of cells, mean edge, edge std:")
    print(edge_table.groupby("scout").agg(
        n_cells=("cell", "count"),
        mean_edge=("edge", "mean"),
        std_edge=("edge", "std"),
        median_n=("n", "median"),
    ).round(3).to_string())
    print()
    print("Per cell — number of scouts, edge across scouts:")
    print(edge_table.groupby("cell").agg(
        n_scouts=("scout", "count"),
        mean_edge=("edge", "mean"),
        max_edge=("edge", "max"),
        min_edge=("edge", "min"),
    ).round(3).to_string())
    print()
    print("Full edge table:")
    print(edge_table[["scout", "cell", "n", "edge", "fisher_se", "in_prereg",
                       "is_aggregator"]].to_string(index=False))
    out_path = Path(__file__).parent / "audit_runs" / "v1" / "edge_table.parquet"
    edge_table.to_parquet(out_path, index=False)
    df_full.to_parquet(Path(__file__).parent / "audit_runs" / "v1" / "scouts_with_cells.parquet",
                        index=False)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
