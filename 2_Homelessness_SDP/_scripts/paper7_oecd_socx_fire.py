"""
Paper 7 — OECD SOCX parse + PRE_REG_027 social-spending × homelessness correlation.

Input: OECD SOCX aggregates CSV (public expenditure % GDP, by country and year).
Output: per-country welfare % GDP (latest year) merged with my Phase 1
        cross-country panel; correlation test fired.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(r"D:/IDP/data/paper7/oecd_socx/socx.csv")
PANEL_PRIOR = Path(r"D:/IDP/data/paper7/phase1_comparison_table_final.csv")
OUT_JSON = Path(r"D:/IDP/analysis/paper7_socx_correlation_2026_05_27.json")
OUT_DIG = Path(
    r"D:/IDP/papers/PAPER_7_SDP_FRAMEWORK/digs/2026_05_27_socx_correlation.md"
)


def main() -> None:
    df = pd.read_csv(SRC, low_memory=False)
    print(f"[socx] loaded {len(df):,} rows from {SRC.name}")
    print(f"[socx] columns: {list(df.columns)[:8]} ...")

    # Filter to total public social expenditure % GDP
    # (PT_B1GQ = % GDP; ES10 = Public; _T = Total programme type)
    keep = df[
        (df["UNIT_MEASURE"] == "PT_B1GQ")
        & (df["EXPEND_SOURCE"] == "ES10")
        & (df["PROGRAMME_TYPE"] == "_T")
        & (df["SPENDING_TYPE"] == "_T")
    ].copy()
    keep["OBS_VALUE"] = pd.to_numeric(keep["OBS_VALUE"], errors="coerce")
    keep["TIME_PERIOD"] = pd.to_numeric(keep["TIME_PERIOD"], errors="coerce")
    print(f"[socx] after filter: {len(keep):,} rows")

    # Latest available year per country
    latest = (
        keep.dropna(subset=["OBS_VALUE", "TIME_PERIOD"])
        .sort_values("TIME_PERIOD")
        .groupby("REF_AREA", as_index=False)
        .last()[["REF_AREA", "Reference area", "TIME_PERIOD", "OBS_VALUE"]]
    )
    latest = latest.rename(
        columns={
            "REF_AREA": "iso3",
            "Reference area": "country",
            "TIME_PERIOD": "year_socx",
            "OBS_VALUE": "social_spend_pct_gdp",
        }
    )
    print(f"[socx] latest-year social-spend table: {len(latest)} countries")
    print(latest.sort_values("social_spend_pct_gdp", ascending=False).head(10).to_string(index=False))

    # Merge with my Phase 1 panel
    if PANEL_PRIOR.exists():
        prior = pd.read_csv(PANEL_PRIOR)
        prior_cols = list(prior.columns)
        print(f"[socx] phase1 panel cols: {prior_cols[:6]}")
        # Best-effort merge on iso3 if present, else country name
        merge_key = (
            "iso3"
            if "iso3" in prior.columns
            else ("ISO3" if "ISO3" in prior.columns else None)
        )
        if merge_key:
            merged = prior.merge(latest, left_on=merge_key, right_on="iso3", how="left")
        else:
            merged = prior.merge(
                latest,
                left_on=prior.columns[0],
                right_on="country",
                how="left",
            )
    else:
        print("[socx] Phase 1 panel not found; SOCX-only output")
        merged = latest

    # Try correlation if homelessness column present
    correlations: dict[str, dict] = {}
    homeless_cols = [
        c for c in merged.columns if "homeless" in c.lower() or "homless" in c.lower()
    ]
    mil_cols = [
        c
        for c in merged.columns
        if "mil" in c.lower() and ("spend" in c.lower() or "gdp" in c.lower())
    ]
    print(f"[socx] candidate homeless cols: {homeless_cols}")
    print(f"[socx] candidate mil-spend cols: {mil_cols}")

    if homeless_cols and "social_spend_pct_gdp" in merged.columns:
        for hc in homeless_cols:
            d = merged[[hc, "social_spend_pct_gdp"]].apply(
                pd.to_numeric, errors="coerce"
            ).dropna()
            if len(d) >= 5:
                r = float(np.corrcoef(d[hc], d["social_spend_pct_gdp"])[0, 1])
                correlations[f"social_spend_vs_{hc}"] = {"r": r, "n": int(len(d))}
                print(f"[socx] r({hc}, social_spend) = {r:+.3f} on n={len(d)}")
    if mil_cols and homeless_cols:
        for mc in mil_cols:
            for hc in homeless_cols:
                d = merged[[hc, mc]].apply(pd.to_numeric, errors="coerce").dropna()
                if len(d) >= 5:
                    r = float(np.corrcoef(d[hc], d[mc])[0, 1])
                    correlations[f"{mc}_vs_{hc}"] = {"r": r, "n": int(len(d))}
                    print(f"[socx] r({hc}, {mc}) = {r:+.3f} on n={len(d)}")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {
                "source": str(SRC),
                "n_rows_raw": int(len(df)),
                "n_countries_latest": int(len(latest)),
                "latest": latest.to_dict(orient="records"),
                "correlations": correlations,
                "merged_columns": list(merged.columns),
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    # Persist merged panel
    merged.to_csv(
        r"D:/IDP/analysis/paper7_socx_merged_2026_05_27.csv", index=False
    )
    print(f"[socx] wrote {OUT_JSON}")
    print("[socx] DONE")


if __name__ == "__main__":
    main()
