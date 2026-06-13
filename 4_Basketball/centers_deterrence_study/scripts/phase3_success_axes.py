"""
Phase 3: Success quantification + predictive power test.

Success axes (built from on-disk data only):
  - career_min : volume of coach trust across career
  - po_min : playoff minutes lifetime (team success + role on team)
  - po_seasons : playoff longevity
  - pra_per_36 : production volume rate
  - ts_pct : shooting efficiency

Predictive test:
  - Does BLK quadrant or deterrence quadrant better discriminate success?
  - Kruskal-Wallis H test per quadrant scheme per success axis
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path('D:/NBA Projections')
DATA_IN = ROOT / 'data' / 'parquet'
STUDY = ROOT / 'centers_deterrence_study'
DATA_OUT = STUDY / 'data'


def main() -> None:
    arch = pd.read_parquet(DATA_OUT / 'archetype_career.parquet')
    po = pd.read_parquet(DATA_IN / 'player_career_season_totals_po.parquet')

    po_career = po.groupby('player_id').agg(
        po_gp=('gp', 'sum'),
        po_min=('min', 'sum'),
        po_seasons=('season_id', 'nunique'),
        po_pts=('pts', 'sum'),
        po_reb=('reb', 'sum'),
        po_ast=('ast', 'sum'),
        po_blk=('blk', 'sum'),
    ).reset_index()

    df = arch.merge(po_career, on='player_id', how='left').fillna(
        {'po_gp': 0, 'po_min': 0, 'po_seasons': 0, 'po_pts': 0, 'po_reb': 0, 'po_ast': 0, 'po_blk': 0}
    )

    df['pra_per_36'] = (df['pts'] + df['reb'] + df['ast']) / df['min'].clip(lower=1) * 36
    df['po_min_per_season'] = df['po_min'] / df['po_seasons'].clip(lower=1)

    success_axes = ['po_min', 'po_seasons', 'po_min_per_season', 'min', 'pra_per_36', 'ts_pct']
    for col in success_axes:
        df[f'{col}_z'] = (df[col] - df[col].mean()) / df[col].std()
    df['success_composite'] = (
        df['po_min_z'] + df['min_z'] + df['pra_per_36_z'] + df['ts_pct_z']
    ) / 4

    print('[success] all 46 centers by composite (top 15):')
    cols = ['name', 'quadrant_box', 'quadrant_deterrence', 'po_seasons', 'po_min', 'min', 'pra_per_36', 'ts_pct', 'success_composite']
    print(df.sort_values('success_composite', ascending=False).head(15)[cols].to_string(index=False))

    print('\n[success] all 46 centers by composite (bottom 10):')
    print(df.sort_values('success_composite', ascending=True).head(10)[cols].to_string(index=False))

    print('\n[predictive test] mean success by BLK quadrant:')
    blk_grp = df.groupby('quadrant_box')['success_composite'].agg(['count', 'mean', 'std', 'median']).round(3)
    print(blk_grp.to_string())

    print('\n[predictive test] mean success by DETERRENCE quadrant:')
    det_grp = df.groupby('quadrant_deterrence')['success_composite'].agg(['count', 'mean', 'std', 'median']).round(3)
    print(det_grp.to_string())

    print('\n[predictive test] Kruskal-Wallis H tests (does quadrant scheme discriminate success?):')
    rows = []
    for axis in success_axes + ['success_composite']:
        for scheme in ['quadrant_box', 'quadrant_deterrence']:
            groups = [df.loc[df[scheme] == q, axis].dropna().values for q in df[scheme].unique()]
            groups = [g for g in groups if len(g) >= 3]
            if len(groups) < 2:
                continue
            try:
                h, p = stats.kruskal(*groups)
            except Exception:
                h, p = np.nan, np.nan
            rows.append({'axis': axis, 'scheme': scheme, 'H': round(h, 3), 'p': round(p, 4),
                          'n_groups': len(groups), 'sig': 'YES' if p < 0.05 else 'no'})
    kw_df = pd.DataFrame(rows)
    print(kw_df.to_string(index=False))

    print('\n[predictive test] per-quadrant success summary (det axis, full):')
    for q in ['dead_zone', 'floor_general', 'swiper', 'two_way_unicorn']:
        sub = df[df['quadrant_deterrence'] == q].sort_values('success_composite', ascending=False)
        if len(sub) == 0:
            continue
        print(f'\n  === {q} (n={len(sub)}) ===')
        print(sub[['name', 'po_seasons', 'po_min', 'min', 'pra_per_36', 'ts_pct', 'success_composite']].to_string(index=False))

    print('\n[critical contrast] Dead zone by deterrence — these are the failure-archetype candidates:')
    dead_det = df[df['quadrant_deterrence'] == 'dead_zone'].sort_values('success_composite', ascending=False)
    print(dead_det[['name', 'blk_per_36', 'ast_per_36', 'rim_supp_mean', 'po_seasons', 'po_min', 'success_composite']].to_string(index=False))

    print('\n[critical contrast] Two-way unicorns by deterrence — the rare combo:')
    twu_det = df[df['quadrant_deterrence'] == 'two_way_unicorn'].sort_values('success_composite', ascending=False)
    print(twu_det[['name', 'blk_per_36', 'ast_per_36', 'rim_supp_mean', 'po_seasons', 'po_min', 'success_composite']].to_string(index=False))

    print('\n[axis comparison] How DIFFERENT is the success distribution under BLK vs deterrence?')
    blk_mean_diff = df.groupby('quadrant_box')['success_composite'].mean()
    det_mean_diff = df.groupby('quadrant_deterrence')['success_composite'].mean()
    print(f'  BLK quadrant range of means:  {blk_mean_diff.max() - blk_mean_diff.min():.3f}  (max={blk_mean_diff.max():.3f}, min={blk_mean_diff.min():.3f})')
    print(f'  DET quadrant range of means:  {det_mean_diff.max() - det_mean_diff.min():.3f}  (max={det_mean_diff.max():.3f}, min={det_mean_diff.min():.3f})')

    df.to_parquet(DATA_OUT / 'success_panel.parquet', index=False)
    kw_df.to_csv(DATA_OUT / 'predictive_kw_tests.csv', index=False)
    print(f'\n[write] {DATA_OUT / "success_panel.parquet"}')
    print(f'[write] {DATA_OUT / "predictive_kw_tests.csv"}')


if __name__ == '__main__':
    main()
