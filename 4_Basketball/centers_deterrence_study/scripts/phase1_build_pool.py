"""
Phase 1: Build center pool, 1998-2026.

Inclusive classifier (matches paper's NBA Test 1 protocol):
any position string containing 'C' or 'Center' substring -> Center.

Min thresholds:
  - season MIN >= 1000
  - career qualifying center-seasons >= 3
  - career MIN at center >= 5000

Inputs (read-only):
  D:/NBA Projections/data/parquet/player_career_season_totals_rs.parquet
  D:/NBA Projections/data/parquet/player_metadata_enriched.parquet

Outputs:
  D:/NBA Projections/centers_deterrence_study/data/center_season_pool.parquet
  D:/NBA Projections/centers_deterrence_study/data/center_career_pool.parquet
  D:/NBA Projections/centers_deterrence_study/data/pool_build_summary.json
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path('D:/NBA Projections')
DATA_IN = ROOT / 'data' / 'parquet'
OUT = ROOT / 'centers_deterrence_study' / 'data'

SEASON_MIN_THRESHOLD = 1000
CAREER_MIN_THRESHOLD = 5000
CAREER_SEASON_THRESHOLD = 3


def is_center_position(pos: str | None) -> bool:
    if pos is None or (isinstance(pos, float) and np.isnan(pos)):
        return False
    s = str(pos).strip().upper()
    if not s:
        return False
    if 'C' == s or 'C-F' == s or 'F-C' == s or 'C/F' == s or 'F/C' == s:
        return True
    if 'CENTER' in s:
        return True
    if s.startswith('C') and len(s) <= 3:
        return True
    return False


def main() -> None:
    seasons = pd.read_parquet(DATA_IN / 'player_career_season_totals_rs.parquet')
    meta = pd.read_parquet(DATA_IN / 'player_metadata_enriched.parquet')

    print(f'[load] seasons rows={len(seasons):,}  unique players={seasons.player_id.nunique():,}')
    print(f'[load] metadata rows={len(meta):,}')

    in_meta = seasons[seasons['player_id'].isin(meta['nba_api_id'])]
    not_in_meta = seasons[~seasons['player_id'].isin(meta['nba_api_id'])]
    print(f'[diag] seasons with metadata join: {in_meta.player_id.nunique():,} players / {len(in_meta):,} rows')
    print(f'[diag] seasons WITHOUT metadata join: {not_in_meta.player_id.nunique():,} players / {len(not_in_meta):,} rows')
    if len(not_in_meta) > 0:
        sample_missing = not_in_meta.groupby('player_id').season_id.agg(['min', 'max', 'count']).sort_values('max').head(20)
        print(f'[diag] missing-metadata sample (earliest careers):\n{sample_missing}')


    meta_keep = meta[['nba_api_id', 'name', 'position', 'height_inches', 'weight_lbs',
                      'draft_year', 'draft_pick', 'debut_year']].rename(columns={'nba_api_id': 'player_id'})
    df = seasons.merge(meta_keep, on='player_id', how='left')

    df['is_center'] = df['position'].apply(is_center_position)
    df['min_per_g'] = df['min'] / df['gp'].clip(lower=1)
    df['blk_per_36'] = df['blk'] / df['min'].clip(lower=1) * 36
    df['ast_per_36'] = df['ast'] / df['min'].clip(lower=1) * 36
    df['reb_per_36'] = df['reb'] / df['min'].clip(lower=1) * 36
    df['stl_per_36'] = df['stl'] / df['min'].clip(lower=1) * 36
    df['fga_per_36'] = df['fga'] / df['min'].clip(lower=1) * 36
    df['fg3a_per_36'] = df['fg3a'] / df['min'].clip(lower=1) * 36
    df['ts_pct'] = df['pts'] / (2 * (df['fga'] + 0.44 * df['fta']).clip(lower=1))

    center_seasons = df[df['is_center'] & (df['min'] >= SEASON_MIN_THRESHOLD)].copy()
    print(f'[filter] center-seasons (min>={SEASON_MIN_THRESHOLD}): {len(center_seasons):,}  unique players={center_seasons.player_id.nunique():,}')

    career = center_seasons.groupby('player_id').agg(
        name=('name', 'first'),
        height_inches=('height_inches', 'first'),
        weight_lbs=('weight_lbs', 'first'),
        draft_year=('draft_year', 'first'),
        draft_pick=('draft_pick', 'first'),
        debut_year=('debut_year', 'first'),
        position=('position', 'first'),
        n_center_seasons=('season_id', 'nunique'),
        first_season=('season_id', 'min'),
        last_season=('season_id', 'max'),
        gp=('gp', 'sum'),
        gs=('gs', 'sum'),
        min=('min', 'sum'),
        pts=('pts', 'sum'),
        reb=('reb', 'sum'),
        ast=('ast', 'sum'),
        stl=('stl', 'sum'),
        blk=('blk', 'sum'),
        tov=('tov', 'sum'),
        fga=('fga', 'sum'),
        fg3a=('fg3a', 'sum'),
        fta=('fta', 'sum'),
    ).reset_index()

    career['blk_per_36'] = career['blk'] / career['min'].clip(lower=1) * 36
    career['ast_per_36'] = career['ast'] / career['min'].clip(lower=1) * 36
    career['reb_per_36'] = career['reb'] / career['min'].clip(lower=1) * 36
    career['stl_per_36'] = career['stl'] / career['min'].clip(lower=1) * 36
    career['fga_per_36'] = career['fga'] / career['min'].clip(lower=1) * 36
    career['fg3a_per_36'] = career['fg3a'] / career['min'].clip(lower=1) * 36
    career['ts_pct'] = career['pts'] / (2 * (career['fga'] + 0.44 * career['fta']).clip(lower=1))
    career['min_per_g'] = career['min'] / career['gp'].clip(lower=1)

    pool = career[
        (career['min'] >= CAREER_MIN_THRESHOLD)
        & (career['n_center_seasons'] >= CAREER_SEASON_THRESHOLD)
    ].copy().sort_values('min', ascending=False).reset_index(drop=True)

    print(f'[filter] career pool (min>={CAREER_MIN_THRESHOLD:,}, seasons>={CAREER_SEASON_THRESHOLD}): {len(pool):,}')

    print(f'[head] career BLK/36 leaders (top 15):')
    print(pool.sort_values('blk_per_36', ascending=False).head(15)[
        ['name', 'n_center_seasons', 'gp', 'min', 'blk_per_36', 'ast_per_36', 'reb_per_36']
    ].to_string(index=False))

    print(f'\n[head] career AST/36 leaders (top 15):')
    print(pool.sort_values('ast_per_36', ascending=False).head(15)[
        ['name', 'n_center_seasons', 'gp', 'min', 'blk_per_36', 'ast_per_36', 'reb_per_36']
    ].to_string(index=False))

    eligible_seasons = center_seasons[center_seasons['player_id'].isin(pool['player_id'])].copy()
    eligible_seasons = eligible_seasons.sort_values(['player_id', 'season_id']).reset_index(drop=True)

    OUT.mkdir(parents=True, exist_ok=True)
    eligible_seasons.to_parquet(OUT / 'center_season_pool.parquet', index=False)
    pool.to_parquet(OUT / 'center_career_pool.parquet', index=False)

    summary = {
        'pool_built_at': pd.Timestamp.utcnow().isoformat(),
        'season_min_threshold': SEASON_MIN_THRESHOLD,
        'career_min_threshold': CAREER_MIN_THRESHOLD,
        'career_season_threshold': CAREER_SEASON_THRESHOLD,
        'pool_n_players': int(len(pool)),
        'pool_n_seasons': int(len(eligible_seasons)),
        'season_range': [str(eligible_seasons.season_id.min()), str(eligible_seasons.season_id.max())],
        'classifier': 'inclusive (matches paper NBA Test 1 protocol)',
        'pool_career_blk_per_36': {
            'min': float(pool.blk_per_36.min()),
            'p25': float(pool.blk_per_36.quantile(0.25)),
            'median': float(pool.blk_per_36.median()),
            'p75': float(pool.blk_per_36.quantile(0.75)),
            'p90': float(pool.blk_per_36.quantile(0.90)),
            'max': float(pool.blk_per_36.max()),
        },
        'pool_career_ast_per_36': {
            'min': float(pool.ast_per_36.min()),
            'p25': float(pool.ast_per_36.quantile(0.25)),
            'median': float(pool.ast_per_36.median()),
            'p75': float(pool.ast_per_36.quantile(0.75)),
            'p90': float(pool.ast_per_36.quantile(0.90)),
            'max': float(pool.ast_per_36.max()),
        },
    }
    with open(OUT / 'pool_build_summary.json', 'w') as fh:
        json.dump(summary, fh, indent=2)
    print(f'\n[write] {OUT / "center_career_pool.parquet"}')
    print(f'[write] {OUT / "center_season_pool.parquet"}')
    print(f'[write] {OUT / "pool_build_summary.json"}')


if __name__ == '__main__':
    main()
