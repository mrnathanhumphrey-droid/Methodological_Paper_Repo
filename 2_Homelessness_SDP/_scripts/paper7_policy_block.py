"""
PRE_REG_029 — hand-coded state policy block (high-confidence factual values only).

Sources noted inline. DEFERRED (flagged in pre-reg §4 pre-conditions): TANF max
benefit, psychiatric bed capacity, prison-release / foster-exit rates — not
hand-coded to avoid low-confidence values polluting a locked fit. Wharton zoning
fetched separately; if blocked, hand-coded published ranking substituted.

All values are a 2024 snapshot (the cross-section outcome year). Panel reads use
the value in force at PIT-year start (handled in build script for the few that
changed within window: Medicaid expansion year, min-wage step-ups).
"""

# Right-to-shelter legal duty (PRE_REG_026/029): 2 strong, 1 partial/seasonal, 0 none
RTS = {"NY": 2, "MA": 1, "DC": 1}

# Medicaid expansion (ACA). Non-expansion states as of 2024 (KFF tracker).
NON_EXPANSION = {"AL", "FL", "GA", "KS", "MS", "SC", "TN", "TX", "WI", "WY"}
# Expansion effective year for panel lagging (KFF). 2014 = original wave; later adopters listed.
MEDICAID_EXP_YEAR = {
    "AK": 2015, "AZ": 2014, "AR": 2014, "CA": 2014, "CO": 2014, "CT": 2014,
    "DE": 2014, "DC": 2014, "HI": 2014, "ID": 2020, "IL": 2014, "IN": 2015,
    "IA": 2014, "KY": 2014, "LA": 2016, "ME": 2019, "MD": 2014, "MA": 2014,
    "MI": 2014, "MN": 2014, "MO": 2021, "MT": 2016, "NE": 2020, "NV": 2014,
    "NH": 2014, "NJ": 2014, "NM": 2014, "NY": 2014, "NC": 2023, "ND": 2014,
    "OH": 2014, "OK": 2021, "OR": 2014, "PA": 2015, "RI": 2014, "SD": 2023,
    "UT": 2020, "VT": 2014, "VA": 2019, "WA": 2014, "WV": 2014,
    # non-expansion: AL FL GA KS MS SC TN TX WI WY -> None
}

# Local rent regulation NOT preempted by state (allowed). NMHC state preemption map.
RENT_CONTROL_ALLOWED = {"CA", "NY", "NJ", "MD", "OR", "ME", "MN", "DC", "WA"}

# Statewide just-cause / good-cause eviction protection (high-confidence statewide only).
JUST_CAUSE = {"CA", "OR", "NJ", "NH", "WA"}  # OR 2019, CA AB1482 2019, NJ longstanding, NH, WA 2021

# State minimum wage 2024 (USD/hr). Federal floor 7.25. DOL / state tables.
MIN_WAGE_2024 = {
    "AL": 7.25, "AK": 11.73, "AZ": 14.35, "AR": 11.00, "CA": 16.00, "CO": 14.42,
    "CT": 15.69, "DE": 13.25, "DC": 17.50, "FL": 13.00, "GA": 7.25, "HI": 14.00,
    "ID": 7.25, "IL": 14.00, "IN": 7.25, "IA": 7.25, "KS": 7.25, "KY": 7.25,
    "LA": 7.25, "ME": 14.15, "MD": 15.00, "MA": 15.00, "MI": 10.33, "MN": 10.85,
    "MS": 7.25, "MO": 12.30, "MT": 10.30, "NE": 12.00, "NV": 12.00, "NH": 7.25,
    "NJ": 15.13, "NM": 12.00, "NY": 15.00, "NC": 7.25, "ND": 7.25, "OH": 10.45,
    "OK": 7.25, "OR": 14.20, "PA": 7.25, "RI": 14.00, "SC": 7.25, "SD": 11.20,
    "TN": 7.25, "TX": 7.25, "UT": 7.25, "VT": 13.67, "VA": 12.00, "WA": 16.28,
    "WV": 8.75, "WI": 7.25, "WY": 7.25,
}

# January mean temperature (deg F), approximate climate gradient (first-look table).
JAN_TEMP = {
    "AL": 46, "AK": 5, "AZ": 48, "AR": 42, "CA": 47, "CO": 25, "CT": 28,
    "DE": 34, "DC": 36, "FL": 60, "GA": 46, "HI": 73, "ID": 24, "IL": 26,
    "IN": 28, "IA": 20, "KS": 31, "KY": 35, "LA": 53, "ME": 18, "MD": 34,
    "MA": 29, "MI": 24, "MN": 12, "MS": 47, "MO": 32, "MT": 22, "NE": 25,
    "NV": 36, "NH": 22, "NJ": 33, "NM": 36, "NY": 26, "NC": 41, "ND": 11,
    "OH": 29, "OK": 38, "OR": 41, "PA": 30, "RI": 30, "SC": 46, "SD": 18,
    "TN": 40, "TX": 50, "UT": 28, "VT": 18, "VA": 38, "WA": 40, "WV": 33,
    "WI": 18, "WY": 22,
}

ALL_STATES = sorted(set(JAN_TEMP) | {"DC"})


def policy_frame():
    import pandas as pd
    rows = []
    for s in ALL_STATES:
        rows.append({
            "state": s,
            "rts": RTS.get(s, 0),
            "medicaid_exp": 0 if s in NON_EXPANSION else 1,
            "medicaid_exp_year": MEDICAID_EXP_YEAR.get(s),
            "rent_control_allowed": int(s in RENT_CONTROL_ALLOWED),
            "just_cause_eviction": int(s in JUST_CAUSE),
            "min_wage_2024": MIN_WAGE_2024.get(s, 7.25),
            "jan_temp": JAN_TEMP.get(s),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = policy_frame()
    print(df.to_string(index=False))
    print(f"\n{len(df)} states; deferred: TANF, psych-beds, prison/foster (pre-reg §4)")
