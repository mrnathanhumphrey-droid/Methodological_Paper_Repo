"""
Paper 7 — Eviction Lab parse + PRE_REG_026 US channel decomposition partial fit.

Inputs:
- allstates_weekly_2020_2021.csv (state × week eviction filings vs prepandemic baseline)
- allstates_monthly_2020_2021.csv (state × month eviction filings)

The monthly aggregates are the analytical workhorse; weekly used to verify trajectory.

PRE_REG_026 channel-orthogonality partial fit:
- Build state-level eviction-channel intensity (filings vs prepandemic baseline)
- Cross with state-level prediction map (Prediction set B)
- Test directional concordance only (data is 2020-2021, not 2007-2024)
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(r"D:/IDP/data/paper7/eviction_lab")
OUT_JSON = Path(r"D:/IDP/analysis/paper7_eviction_lab_2026_05_27.json")
OUT_DIG = Path(
    r"D:/IDP/papers/PAPER_7_SDP_FRAMEWORK/digs/2026_05_27_eviction_lab_partial_fit.md"
)


def state_normalize(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.title()


def main() -> None:
    monthly_p = DATA / "allstates_monthly_2020_2021.csv"
    weekly_p = DATA / "allstates_weekly_2020_2021.csv"
    print(f"[evict] loading monthly: {monthly_p.stat().st_size/1e6:.1f} MB")
    monthly = pd.read_csv(monthly_p, low_memory=False)
    print(f"[evict] monthly rows = {len(monthly):,} | cols = {list(monthly.columns)}")
    # Use state-aggregate type (rather than census tract)
    monthly["type"] = monthly["type"].astype(str).str.strip()
    state_agg = monthly[monthly["type"].str.contains("State", case=False, na=False)].copy()
    if state_agg.empty:
        # Fall back to aggregating tracts to state level via state name column
        print("[evict] no State-type rows; aggregating tracts -> state")
        state_agg = (
            monthly.groupby(["state", "month"], as_index=False)[
                ["filings_2020", "filings_avg", "filings_avg_prepandemic_baseline"]
            ]
            .sum(min_count=1)
        )
    else:
        state_agg = state_agg[
            [
                "state",
                "month",
                "filings_2020",
                "filings_avg",
                "filings_avg_prepandemic_baseline",
            ]
        ].copy()

    state_agg["state"] = state_normalize(state_agg["state"])
    state_agg["filings_2020"] = pd.to_numeric(state_agg["filings_2020"], errors="coerce")
    state_agg["filings_avg_prepandemic_baseline"] = pd.to_numeric(
        state_agg["filings_avg_prepandemic_baseline"], errors="coerce"
    )

    # Per-state ratio across 2020-2021 (2020 vs prepandemic baseline)
    per_state = state_agg.groupby("state", as_index=False).agg(
        filings_2020_sum=("filings_2020", "sum"),
        baseline_sum=("filings_avg_prepandemic_baseline", "sum"),
        months=("month", "nunique"),
    )
    per_state["ratio_2020_vs_baseline"] = per_state["filings_2020_sum"] / per_state[
        "baseline_sum"
    ].replace(0, np.nan)
    per_state = per_state.sort_values("ratio_2020_vs_baseline", ascending=False)
    print(f"[evict] per-state aggregated: {len(per_state)} states")
    print(per_state.head(15).to_string(index=False))

    # PRE_REG_026 Prediction set B — state → predicted dominant channel
    predicted = {
        "California": "Unaffordability",
        "New York": "Eviction",
        "Mississippi": "Institutional/DV",
        "Texas": "Disaster+Unaffordability",
        "Florida": "Disaster+Unaffordability",
        "Louisiana": "Disaster+Institutional",
        "Massachusetts": "Unaffordability",
        "Michigan": "Eviction+Institutional",
    }
    # If eviction ratio is high → consistent with "Eviction-driven" channel
    # If ratio is low (pandemic-moratorium-protected) → ambiguous
    # Eviction-channel match = state's ratio_2020_vs_baseline is in top quartile
    if not per_state.empty:
        q75 = per_state["ratio_2020_vs_baseline"].quantile(0.75)
    else:
        q75 = np.nan
    print(f"[evict] top-quartile eviction-ratio threshold: {q75}")

    channel_results: dict[str, dict] = {}
    for state, predicted_channel in predicted.items():
        row = per_state[per_state["state"] == state]
        if row.empty:
            channel_results[state] = {
                "predicted_channel": predicted_channel,
                "ratio_2020_vs_baseline": None,
                "observed_eviction_top_quartile": None,
                "consistent_with_eviction_channel": None,
            }
            continue
        r = float(row.iloc[0]["ratio_2020_vs_baseline"])
        in_top = bool(r >= q75) if not np.isnan(q75) else None
        consistent = (
            ("Eviction" in predicted_channel and in_top is True)
            or ("Eviction" not in predicted_channel and in_top is False)
        )
        channel_results[state] = {
            "predicted_channel": predicted_channel,
            "ratio_2020_vs_baseline": r,
            "observed_eviction_top_quartile": in_top,
            "consistent_with_eviction_channel": consistent,
        }
    n_consistent = sum(
        1
        for r in channel_results.values()
        if r["consistent_with_eviction_channel"] is True
    )
    print(f"[evict] state predictions consistent with eviction-channel: {n_consistent} of {len(channel_results)}")

    # ALSO read weekly for headline filing-trajectory note (no full parse)
    print(f"[evict] checking weekly: {weekly_p.stat().st_size/1e6:.1f} MB")
    # Lighter touch — just head + dtypes; full weekly is 240MB
    weekly_head = pd.read_csv(weekly_p, nrows=5)
    weekly_cols = list(weekly_head.columns)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {
                "source_monthly": str(monthly_p),
                "n_rows_monthly": int(len(monthly)),
                "per_state": per_state.to_dict(orient="records"),
                "top_quartile_threshold": (None if np.isnan(q75) else float(q75)),
                "channel_predictions": channel_results,
                "states_consistent_n": int(n_consistent),
                "weekly_columns": weekly_cols,
                "note": (
                    "Eviction Lab 2020-2021 covers pandemic + early-recovery window; "
                    "filings depressed by COVID moratoria, so the absolute ratio "
                    "below-baseline is expected. This fit tests RELATIVE state "
                    "ordering (which states had highest ratio_2020_vs_baseline) "
                    "against PRE_REG_026 Prediction set B."
                ),
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    per_state.to_csv(
        r"D:/IDP/analysis/paper7_eviction_per_state_2026_05_27.csv", index=False
    )
    print(f"[evict] wrote {OUT_JSON}")
    print("[evict] DONE")


if __name__ == "__main__":
    main()
