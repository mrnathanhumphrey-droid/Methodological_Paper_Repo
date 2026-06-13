"""
Paper 7 — STRUCTURAL-EXPLANATION first-look (EXPLORATORY, not a locked pre-reg).

Question: does the STRUCTURE of America (legislative policy + social conditions)
explain the homelessness displacement geography + the residual "noise" left by
the gross bimodal (street vs sheltered) pattern?

SDP-legitimacy logic (falsifiable):
  NULL  (homelessness is individual/random): structural vars should NOT predict
        the geography or the FORM of displacement.
  SDP   (homelessness is structurally produced): structural vars predict both
        the LEVEL (rate) and the FORM (unsheltered vs sheltered) of displacement.
  If structural R^2 is high -- especially for unsheltered_share via right-to-
  shelter + climate -- SDP is empirically legitimate: the structure sets the
  form and distribution of displacement, not individuals.

Structural variables (hand-coded high-confidence policy set + ACS cost-burden).
Values are first-look approximations; full pre-reg will pull authoritative series
(Wharton WRLURI zoning, CDC WONDER opioid, BLS min wage, KFF Medicaid dates).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import r2_score

ROOT = Path(r"D:/IDP")
PANEL = ROOT / "analysis/paper7_sdp_state_year_panel.parquet"
OUT = ROOT / "analysis/paper7_structural_firstlook_2026_05_27.json"

# Right-to-shelter (legal duty): NY strong (Callahan 1981), MA families (1983),
# DC seasonal (HSRA 2005). 2=strong statewide, 1=partial/families/seasonal, 0=none.
RTS = {'NY': 2, 'MA': 1, 'DC': 1}
# Medicaid expansion (ACA) — non-expansion as of 2024 (KFF). expanded=1 else 0.
NON_EXPANSION = {'AL', 'FL', 'GA', 'KS', 'MS', 'SC', 'TN', 'TX', 'WI', 'WY'}
# Local rent regulation NOT preempted by state (allowed): CA NY NJ MD OR ME MN DC WA.
RENT_CONTROL_ALLOWED = {'CA', 'NY', 'NJ', 'MD', 'OR', 'ME', 'MN', 'DC', 'WA'}
# January mean temp (deg F), approximate first-look climate gradient.
JAN_TEMP = {
    'AL': 46, 'AK': 5, 'AZ': 48, 'AR': 42, 'CA': 47, 'CO': 25, 'CT': 28,
    'DE': 34, 'DC': 36, 'FL': 60, 'GA': 46, 'HI': 73, 'ID': 24, 'IL': 26,
    'IN': 28, 'IA': 20, 'KS': 31, 'KY': 35, 'LA': 53, 'ME': 18, 'MD': 34,
    'MA': 29, 'MI': 24, 'MN': 12, 'MS': 47, 'MO': 32, 'MT': 22, 'NE': 25,
    'NV': 36, 'NH': 22, 'NJ': 33, 'NM': 36, 'NY': 26, 'NC': 41, 'ND': 11,
    'OH': 29, 'OK': 38, 'OR': 41, 'PA': 30, 'RI': 30, 'SC': 46, 'SD': 18,
    'TN': 40, 'TX': 50, 'UT': 28, 'VT': 18, 'VA': 38, 'WA': 40, 'WV': 33,
    'WI': 18, 'WY': 22,
}

STATES = set(JAN_TEMP) | {'DC'}


def loo_r2(X, y):
    """Leave-one-out R^2 (honest out-of-sample for n~51 cross-section)."""
    Xs = StandardScaler().fit_transform(X)
    preds = np.zeros_like(y, dtype=float)
    for tr, te in LeaveOneOut().split(Xs):
        m = LinearRegression().fit(Xs[tr], y[tr])
        preds[te] = m.predict(Xs[te])
    return r2_score(y, preds), preds


def main() -> None:
    df = pd.read_parquet(PANEL)
    d = df[(df.year == 2024) & (df.state.isin(STATES))].copy()
    d['rts'] = d.state.map(RTS).fillna(0)
    d['medicaid_exp'] = (~d.state.isin(NON_EXPANSION)).astype(int)
    d['rent_control'] = d.state.isin(RENT_CONTROL_ALLOWED).astype(int)
    d['jan_temp'] = d.state.map(JAN_TEMP)
    d = d.dropna(subset=['unsheltered_share', 'homeless_per_10k', 'cb_share',
                         'jan_temp'])

    struct = ['rts', 'medicaid_exp', 'rent_control', 'jan_temp', 'cb_share']
    res = {'n_states': int(len(d)),
           'framing': 'EXPLORATORY first-look; not a locked pre-reg',
           'sdp_logic': 'structure predicts FORM+LEVEL of displacement => SDP legit'}

    # ---- Outcome 1: FORM of displacement (unsheltered share) ----
    y = d['unsheltered_share'].values
    r2_full, _ = loo_r2(d[struct].values, y)
    r2_climate, _ = loo_r2(d[['jan_temp']].values, y)
    r2_rts, _ = loo_r2(d[['rts']].values, y)
    r2_climate_rts, _ = loo_r2(d[['jan_temp', 'rts']].values, y)
    # in-sample coefficients (standardized) for direction
    Xs = StandardScaler().fit_transform(d[struct].values)
    coef = dict(zip(struct, LinearRegression().fit(Xs, y).coef_.round(4)))
    res['form_unsheltered_share'] = {
        'loo_r2_full_structure': round(r2_full, 4),
        'loo_r2_climate_only': round(r2_climate, 4),
        'loo_r2_rts_only': round(r2_rts, 4),
        'loo_r2_climate_plus_rts': round(r2_climate_rts, 4),
        'std_coefficients': coef,
    }

    # ---- Outcome 2: LEVEL of displacement (homeless per 10k) ----
    y2 = d['homeless_per_10k'].values
    r2_lvl, _ = loo_r2(d[struct].values, y2)
    r2_lvl_cb, _ = loo_r2(d[['cb_share']].values, y2)
    coef2 = dict(zip(struct, LinearRegression().fit(Xs, y2).coef_.round(4)))
    res['level_homeless_per_10k'] = {
        'loo_r2_full_structure': round(r2_lvl, 4),
        'loo_r2_costburden_only': round(r2_lvl_cb, 4),
        'std_coefficients': coef2,
    }

    # ---- Outcome 3: does structure explain the NOISE left by climate? ----
    # residual of unsheltered_share after climate-only model, predicted by policy
    Xc = StandardScaler().fit_transform(d[['jan_temp']].values)
    clim_pred = LinearRegression().fit(Xc, y).predict(Xc)
    resid = y - clim_pred
    policy = ['rts', 'medicaid_exp', 'rent_control', 'cb_share']
    r2_resid, _ = loo_r2(d[policy].values, resid)
    coef3 = dict(zip(policy, LinearRegression().fit(
        StandardScaler().fit_transform(d[policy].values), resid).coef_.round(4)))
    res['noise_residual_after_climate'] = {
        'note': 'residual unsheltered_share after climate-only model, predicted by POLICY vars',
        'loo_r2_policy_on_residual': round(r2_resid, 4),
        'std_coefficients': coef3,
    }

    # ---- RTS natural-experiment contrast ----
    rts_states = d[d.rts > 0]
    non_rts = d[d.rts == 0]
    res['rts_natural_experiment'] = {
        'rts_states': sorted(rts_states.state.tolist()),
        'mean_unsheltered_share_RTS': round(float(rts_states.unsheltered_share.mean()), 4),
        'mean_unsheltered_share_nonRTS': round(float(non_rts.unsheltered_share.mean()), 4),
        'ratio': round(float(non_rts.unsheltered_share.mean() /
                             rts_states.unsheltered_share.mean()), 2),
    }

    OUT.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    print(f"\n[structural] wrote {OUT}")


if __name__ == "__main__":
    main()
