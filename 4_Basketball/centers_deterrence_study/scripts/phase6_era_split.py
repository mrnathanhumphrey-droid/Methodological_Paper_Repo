"""
Phase 6: Era split — three sub-tests.

6a: Box-axis archetype-success by era (2010-14 transition vs 2014-26 pace-and-space)
6b: BLK-vs-deterrence proxy noise widening — did BLK become noisier as 3PA share rose?
6c: Elite vs non-elite swiper gap widening in pace-and-space

Data constraint banked: tracking deterrence 2019-25 only; for 6a-6c we use season-level
box stats joined to deterrence where available.
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


def season_id_to_year(s: str) -> int:
    return int(s.split('-')[0])


def era_label(year: int) -> str:
    if year < 2014:
        return 'transition_2010_13'
    return 'pace_and_space_2014_25'


def main() -> None:
    seasons = pd.read_parquet(DATA_OUT / 'center_season_pool.parquet')
    success = pd.read_parquet(DATA_OUT / 'success_with_teammates.parquet')
    rim = pd.read_parquet(DATA_IN / 'player_def_rim.parquet')
    all_seasons = pd.read_parquet(DATA_IN / 'player_career_season_totals_rs.parquet')

    seasons['year'] = seasons['season_id'].apply(season_id_to_year)
    seasons['era'] = seasons['year'].apply(era_label)
    seasons['blk_per_36'] = seasons['blk'] / seasons['min'].clip(lower=1) * 36
    seasons['ast_per_36'] = seasons['ast'] / seasons['min'].clip(lower=1) * 36
    seasons['pra_per_36'] = (seasons['pts'] + seasons['reb'] + seasons['ast']) / seasons['min'].clip(lower=1) * 36
    seasons['fg3a_per_36'] = seasons['fg3a'] / seasons['min'].clip(lower=1) * 36
    seasons['ts_pct'] = seasons['pts'] / (2 * (seasons['fga'] + 0.44 * seasons['fta']).clip(lower=1))

    print(f'[load] center-seasons: {len(seasons)}')
    print(f'  era counts:\n{seasons.era.value_counts().to_string()}')

    print('\n=== 6a: BOX-AXIS ARCHETYPE-SUCCESS BY ERA ===')

    league_blk_mean = seasons.groupby('era')['blk_per_36'].mean()
    league_ast_mean = seasons.groupby('era')['ast_per_36'].mean()
    print(f'  era BLK/36 means:\n{league_blk_mean.to_string()}')
    print(f'  era AST/36 means:\n{league_ast_mean.to_string()}')

    seasons['blk_high'] = seasons.apply(
        lambda r: r['blk_per_36'] > league_blk_mean[r['era']], axis=1
    )
    seasons['ast_high'] = seasons.apply(
        lambda r: r['ast_per_36'] > league_ast_mean[r['era']], axis=1
    )
    seasons['season_quad_box'] = np.where(
        seasons['blk_high'] & seasons['ast_high'], 'two_way_unicorn',
        np.where(seasons['blk_high'] & ~seasons['ast_high'], 'swiper',
                 np.where(~seasons['blk_high'] & seasons['ast_high'], 'floor_general', 'dead_zone'))
    )

    print('\n  season-level quadrant x era counts:')
    print(seasons.groupby(['era', 'season_quad_box']).size().unstack(fill_value=0).to_string())

    print('\n  season-level PRA/36 by quadrant x era:')
    print(seasons.groupby(['era', 'season_quad_box'])['pra_per_36'].agg(['count', 'mean', 'median']).round(2).to_string())

    print('\n  season-level TS% by quadrant x era:')
    print(seasons.groupby(['era', 'season_quad_box'])['ts_pct'].agg(['count', 'mean', 'median']).round(3).to_string())

    print('\n=== 6b: BLK-AS-PROXY NOISE WIDENING WITH 3PA EXPLOSION ===')

    all_seasons['year'] = all_seasons['season_id'].apply(season_id_to_year)
    league_3pa = all_seasons.groupby('year').agg(
        league_3pa=('fg3a', 'sum'),
        league_fga=('fga', 'sum'),
    )
    league_3pa['league_3pa_share'] = league_3pa['league_3pa'] / league_3pa['league_fga'].clip(lower=1)
    print(f'  league 3PA share by year (proxy for spacing era):')
    print(league_3pa[['league_3pa_share']].round(3).to_string())

    rim = rim[rim['season_type'] == 'Regular Season'].copy()
    rim['rim_supp'] = rim['ns_lt_06_pct'] - rim['lt_06_pct']
    rim['season_year'] = rim['season'].apply(season_id_to_year)

    box_stats = seasons[['player_id', 'season_id', 'blk_per_36', 'min']].copy()
    rim_with_box = rim.rename(columns={'close_def_person_id': 'player_id', 'season': 'season_id'}).merge(
        box_stats, on=['player_id', 'season_id'], how='inner'
    )
    print(f'\n  rim x box join: {len(rim_with_box)} center-seasons in tracking era')

    if len(rim_with_box) > 0:
        rim_with_box['blk_quartile'] = pd.qcut(rim_with_box['blk_per_36'], q=4, labels=['Q1_low', 'Q2', 'Q3', 'Q4_high'])
        print('\n  BLK quartile vs deterrence (mean rim_supp by BLK rank, all tracking-era center-seasons):')
        print(rim_with_box.groupby('blk_quartile', observed=True)['rim_supp'].agg(['count', 'mean', 'std']).round(3).to_string())

        for season_yr in sorted(rim_with_box['season_year'].unique()):
            sub = rim_with_box[rim_with_box['season_year'] == season_yr]
            if len(sub) < 10:
                continue
            r, p = stats.spearmanr(sub['blk_per_36'].values, sub['rim_supp'].values)
            print(f'  {season_yr}-{season_yr+1}: n={len(sub)} BLK->rim_supp Spearman r={r:.3f} p={p:.4f}')

    print('\n=== 6c: ELITE vs NON-ELITE SWIPER GAP IN PACE-AND-SPACE ===')

    sw_seasons = seasons[seasons['season_quad_box'] == 'swiper'].merge(
        success[['player_id', 'name', 'quadrant_deterrence', 'rim_supp_mean', 'success_composite']],
        on='player_id', how='left'
    )

    sw_seasons['is_elite_swiper'] = sw_seasons['rim_supp_mean'] >= sw_seasons['rim_supp_mean'].median()

    print('\n  pace-and-space era only — swiper x elite-vs-non-elite:')
    pace_sw = sw_seasons[sw_seasons['era'] == 'pace_and_space_2014_25']
    if len(pace_sw) > 0:
        out = pace_sw.groupby('is_elite_swiper').agg(
            n=('player_id', 'count'),
            mean_pra=('pra_per_36', 'mean'),
            median_pra=('pra_per_36', 'median'),
            mean_ts=('ts_pct', 'mean'),
            n_unique_players=('player_id', 'nunique'),
        ).round(3)
        print(out.to_string())

    print('\n  transition era only — swiper x elite-vs-non-elite:')
    trans_sw = sw_seasons[sw_seasons['era'] == 'transition_2010_13']
    if len(trans_sw) > 0:
        out = trans_sw.groupby('is_elite_swiper').agg(
            n=('player_id', 'count'),
            mean_pra=('pra_per_36', 'mean'),
            median_pra=('pra_per_36', 'median'),
            mean_ts=('ts_pct', 'mean'),
            n_unique_players=('player_id', 'nunique'),
        ).round(3)
        print(out.to_string())

    print('\n  comparing era gaps (effect of pace-and-space on tier separation):')
    for era_name in ['transition_2010_13', 'pace_and_space_2014_25']:
        sub = sw_seasons[sw_seasons['era'] == era_name]
        if len(sub) < 4:
            continue
        elite = sub[sub['is_elite_swiper']]['pra_per_36'].dropna().values
        nonelite = sub[~sub['is_elite_swiper']]['pra_per_36'].dropna().values
        if len(elite) < 3 or len(nonelite) < 3:
            continue
        gap = elite.mean() - nonelite.mean()
        try:
            U, p = stats.mannwhitneyu(elite, nonelite, alternative='greater')
        except Exception:
            U, p = np.nan, np.nan
        print(f'  {era_name}: elite n={len(elite)} nonelite n={len(nonelite)} '
              f'PRA gap={gap:.3f} U={U:.1f} p={p:.4f}')

    print('\n=== 6d: BAM ADEBAYO ARC — DOES THE FLOOR-GENERAL ARCHETYPE EMERGE POST-2014? ===')

    fg_seasons = seasons.merge(
        success[['player_id', 'name', 'quadrant_deterrence', 'success_composite']].rename(columns={'name': 'player_name'}),
        on='player_id', how='left'
    )
    fg_pace = fg_seasons[(fg_seasons['season_quad_box'] == 'floor_general') & (fg_seasons['era'] == 'pace_and_space_2014_25')]
    fg_trans = fg_seasons[(fg_seasons['season_quad_box'] == 'floor_general') & (fg_seasons['era'] == 'transition_2010_13')]
    print(f'  floor general season counts: transition={len(fg_trans)}, pace-and-space={len(fg_pace)}')
    print(f'  unique players: transition={fg_trans.player_id.nunique()}, pace-and-space={fg_pace.player_id.nunique()}')

    if len(fg_trans) > 0:
        print(f'  transition era FG-archetype players: {sorted(fg_trans.player_name.dropna().unique())}')
    if len(fg_pace) > 0:
        print(f'  pace-and-space era FG-archetype players: {sorted(fg_pace.player_name.dropna().unique())}')

    print('\n  swiper season counts by era:')
    sw_trans = fg_seasons[(fg_seasons['season_quad_box'] == 'swiper') & (fg_seasons['era'] == 'transition_2010_13')]
    sw_pace = fg_seasons[(fg_seasons['season_quad_box'] == 'swiper') & (fg_seasons['era'] == 'pace_and_space_2014_25')]
    print(f'  swiper unique players: transition={sw_trans.player_id.nunique()}, pace-and-space={sw_pace.player_id.nunique()}')

    print('\n=== 6e: SUCCESS_COMPOSITE BY ERA-PROPORTION ===')
    print('  Per-player: what % of seasons in pace-and-space era? vs success composite')
    sea_with_succ = seasons.merge(
        success[['player_id', 'name', 'success_composite']].rename(columns={'name': 'player_name'}),
        on='player_id', how='left'
    )
    player_era = sea_with_succ.groupby('player_id').agg(
        player_name=('player_name', 'first'),
        n_total=('season_id', 'count'),
        n_pace=('era', lambda s: (s == 'pace_and_space_2014_25').sum()),
        success_composite=('success_composite', 'first'),
    ).reset_index()
    player_era['pct_pace'] = player_era['n_pace'] / player_era['n_total']
    r, p = stats.spearmanr(player_era['pct_pace'], player_era['success_composite'])
    print(f'  Spearman r (pct_pace, success): {r:.3f}, p={p:.4f}')

    seasons.to_parquet(DATA_OUT / 'era_split_seasons.parquet', index=False)
    print(f'\n[write] {DATA_OUT / "era_split_seasons.parquet"}')


if __name__ == '__main__':
    main()
