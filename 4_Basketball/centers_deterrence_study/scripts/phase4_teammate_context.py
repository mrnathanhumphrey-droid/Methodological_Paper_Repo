"""
Phase 4: Teammate context.

For each center-season:
  - best_teammate_pra36 (top non-center teammate by PRA/36 weighted by MIN)
  - best_teammate_min_share (top teammate's share of team MIN)
  - primary_creator_ast36 (highest AST/36 teammate with >=1000 MIN)
  - team_3pa_per_game (spacing proxy)
  - n_teammates_above_pra_threshold (depth)

Then aggregate to player-careers and test:
  - Within each archetype quadrant: does success correlate with teammate quality?
  - Is there a threshold below which the archetype fails?
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

MIN_TEAMMATE_QUALIFIER = 800
PRA_PER_36_THRESHOLD = 25.0


def compute_teammate_features(center_seasons: pd.DataFrame, all_seasons: pd.DataFrame) -> pd.DataFrame:
    all_seasons = all_seasons.copy()
    all_seasons['pra_per_36'] = (all_seasons['pts'] + all_seasons['reb'] + all_seasons['ast']) / all_seasons['min'].clip(lower=1) * 36
    all_seasons['ast_per_36'] = all_seasons['ast'] / all_seasons['min'].clip(lower=1) * 36
    all_seasons['fg3a_per_36'] = all_seasons['fg3a'] / all_seasons['min'].clip(lower=1) * 36
    all_seasons['ts_pct'] = all_seasons['pts'] / (2 * (all_seasons['fga'] + 0.44 * all_seasons['fta']).clip(lower=1))

    rows = []
    for _, row in center_seasons.iterrows():
        team_id = row['team_id']
        season_id = row['season_id']
        center_id = row['player_id']
        if pd.isna(team_id) or team_id == 0:
            rows.append({'player_id': center_id, 'season_id': season_id, 'team_id': team_id,
                         'best_teammate_pra36': np.nan, 'best_teammate_min': np.nan,
                         'primary_creator_ast36': np.nan, 'team_3pa_per_36': np.nan,
                         'n_teammates_above_pra': 0, 'team_total_min': np.nan,
                         'team_total_3pa': np.nan})
            continue

        team_roster = all_seasons[
            (all_seasons['team_id'] == team_id)
            & (all_seasons['season_id'] == season_id)
            & (all_seasons['player_id'] != center_id)
            & (all_seasons['min'] >= MIN_TEAMMATE_QUALIFIER)
        ].copy()

        if len(team_roster) == 0:
            rows.append({'player_id': center_id, 'season_id': season_id, 'team_id': team_id,
                         'best_teammate_pra36': np.nan, 'best_teammate_min': np.nan,
                         'primary_creator_ast36': np.nan, 'team_3pa_per_36': np.nan,
                         'n_teammates_above_pra': 0, 'team_total_min': np.nan,
                         'team_total_3pa': np.nan})
            continue

        best_idx = team_roster['pra_per_36'].idxmax()
        primary_creator_idx = team_roster['ast_per_36'].idxmax()
        full_team = all_seasons[
            (all_seasons['team_id'] == team_id)
            & (all_seasons['season_id'] == season_id)
        ]
        team_total_min = full_team['min'].sum()
        team_total_3pa = full_team['fg3a'].sum()
        team_3pa_per_36 = team_total_3pa / team_total_min.clip(min=1) * 36 * 5

        rows.append({
            'player_id': center_id,
            'season_id': season_id,
            'team_id': team_id,
            'best_teammate_pra36': team_roster.loc[best_idx, 'pra_per_36'],
            'best_teammate_min': team_roster.loc[best_idx, 'min'],
            'best_teammate_name_proxy_id': team_roster.loc[best_idx, 'player_id'],
            'primary_creator_ast36': team_roster.loc[primary_creator_idx, 'ast_per_36'],
            'primary_creator_id': team_roster.loc[primary_creator_idx, 'player_id'],
            'team_3pa_per_36': team_3pa_per_36,
            'n_teammates_above_pra': int((team_roster['pra_per_36'] >= PRA_PER_36_THRESHOLD).sum()),
            'team_total_min': team_total_min,
            'team_total_3pa': team_total_3pa,
        })
    return pd.DataFrame(rows)


def main() -> None:
    center_seasons = pd.read_parquet(DATA_OUT / 'center_season_pool.parquet')
    all_seasons = pd.read_parquet(DATA_IN / 'player_career_season_totals_rs.parquet')
    success_panel = pd.read_parquet(DATA_OUT / 'success_panel.parquet')

    print(f'[load] center-seasons: {len(center_seasons)} | all player-seasons: {len(all_seasons)}')

    teammate = compute_teammate_features(center_seasons, all_seasons)
    print(f'[compute] teammate feature rows: {len(teammate)}')
    print(f'[compute] non-null: best_teammate_pra36={teammate.best_teammate_pra36.notna().sum()}, '
          f'primary_creator_ast36={teammate.primary_creator_ast36.notna().sum()}')

    teammate.to_parquet(DATA_OUT / 'teammate_season.parquet', index=False)

    tm_career = teammate.groupby('player_id').agg(
        avg_best_teammate_pra36=('best_teammate_pra36', 'mean'),
        max_best_teammate_pra36=('best_teammate_pra36', 'max'),
        avg_primary_creator_ast36=('primary_creator_ast36', 'mean'),
        max_primary_creator_ast36=('primary_creator_ast36', 'max'),
        avg_team_3pa_per_36=('team_3pa_per_36', 'mean'),
        avg_n_teammates_above_pra=('n_teammates_above_pra', 'mean'),
        n_seasons_with_data=('best_teammate_pra36', lambda s: s.notna().sum()),
    ).reset_index()

    df = success_panel.merge(tm_career, on='player_id', how='left')

    print('\n[career] teammate context top 10 by avg_best_teammate_pra36 (best supporting cast):')
    cols = ['name', 'quadrant_deterrence', 'avg_best_teammate_pra36', 'avg_primary_creator_ast36',
            'avg_team_3pa_per_36', 'avg_n_teammates_above_pra', 'success_composite']
    print(df.sort_values('avg_best_teammate_pra36', ascending=False).head(10)[cols].to_string(index=False))

    print('\n[career] teammate context bottom 10 (worst supporting cast):')
    print(df.sort_values('avg_best_teammate_pra36', ascending=True).head(10)[cols].to_string(index=False))

    print('\n[within-archetype correlation] success_composite ~ avg_best_teammate_pra36 within each deterrence quadrant:')
    rows = []
    for q in ['dead_zone', 'floor_general', 'swiper', 'two_way_unicorn']:
        sub = df[(df['quadrant_deterrence'] == q) & df['avg_best_teammate_pra36'].notna()]
        if len(sub) < 4:
            continue
        for tm_axis in ['avg_best_teammate_pra36', 'avg_primary_creator_ast36', 'avg_team_3pa_per_36', 'avg_n_teammates_above_pra']:
            x = sub[tm_axis].values
            y = sub['success_composite'].values
            r, p = stats.spearmanr(x, y)
            rows.append({'quadrant': q, 'teammate_axis': tm_axis, 'n': len(sub),
                         'spearman_r': round(r, 3), 'p': round(p, 4),
                         'sig': 'YES' if p < 0.05 else 'no'})
    corr_df = pd.DataFrame(rows)
    print(corr_df.to_string(index=False))

    print('\n[threshold test] does FLOOR GENERAL need a creator? split at primary_creator_ast36 median:')
    fg = df[(df['quadrant_deterrence'] == 'floor_general') & df['avg_primary_creator_ast36'].notna()].copy()
    if len(fg) >= 4:
        med = fg['avg_primary_creator_ast36'].median()
        fg['has_creator'] = fg['avg_primary_creator_ast36'] >= med
        print(f'  median primary_creator_ast36 in floor_general: {med:.2f}')
        for has_c in [True, False]:
            sub = fg[fg['has_creator'] == has_c]
            print(f'  has_creator={has_c}: n={len(sub)}, mean success={sub["success_composite"].mean():.3f}')
            print(f'    members: {sub.sort_values("success_composite", ascending=False)[["name","avg_primary_creator_ast36","success_composite"]].to_string(index=False)}')

    print('\n[threshold test] does SWIPER need teammates? split at avg_n_teammates_above_pra median:')
    sw = df[(df['quadrant_deterrence'] == 'swiper') & df['avg_n_teammates_above_pra'].notna()].copy()
    if len(sw) >= 4:
        med = sw['avg_n_teammates_above_pra'].median()
        sw['has_help'] = sw['avg_n_teammates_above_pra'] >= med
        print(f'  median teammates above PRA threshold in swiper: {med:.2f}')
        for has_h in [True, False]:
            sub = sw[sw['has_help'] == has_h]
            print(f'  has_help={has_h}: n={len(sub)}, mean success={sub["success_composite"].mean():.3f}')
            print(f'    members: {sub.sort_values("success_composite", ascending=False)[["name","avg_n_teammates_above_pra","success_composite"]].to_string(index=False)}')

    print('\n[threshold test] does DEAD ZONE need teammates? split at avg_best_teammate_pra36 median:')
    dz = df[(df['quadrant_deterrence'] == 'dead_zone') & df['avg_best_teammate_pra36'].notna()].copy()
    if len(dz) >= 4:
        med = dz['avg_best_teammate_pra36'].median()
        dz['has_help'] = dz['avg_best_teammate_pra36'] >= med
        print(f'  median best teammate PRA/36 in dead_zone: {med:.2f}')
        for has_h in [True, False]:
            sub = dz[dz['has_help'] == has_h]
            print(f'  has_help={has_h}: n={len(sub)}, mean success={sub["success_composite"].mean():.3f}')

    df.to_parquet(DATA_OUT / 'success_with_teammates.parquet', index=False)
    corr_df.to_csv(DATA_OUT / 'within_archetype_correlations.csv', index=False)

    print(f'\n[write] {DATA_OUT / "teammate_season.parquet"}')
    print(f'[write] {DATA_OUT / "success_with_teammates.parquet"}')
    print(f'[write] {DATA_OUT / "within_archetype_correlations.csv"}')


if __name__ == '__main__':
    main()
