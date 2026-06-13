"""
Phase 2: Archetype space for center pool.

Two layers:
  A. Wide-era box-score archetype axes (2010-2026)
     - BLK per 36 (proxy axis, era-distorted)
     - AST per 36 (connector axis)
     - TS%, 3PA/36, REB/36, STL/36
     - K=4 cluster on (BLK/36, AST/36)
  B. Tracking-era deterrence axes (2019-2026)
     - rim_supp = ns_lt_06_pct - lt_06_pct (suppression rate)
     - rim_def_volume_per_36 = fga_lt_06 / min * 36
     - z-scored vs pool
     - K=4 cluster on (deterrence_score, AST/36)
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
STUDY = ROOT / 'centers_deterrence_study'
DATA_OUT = STUDY / 'data'


def quadrant_label(blk_z: float, ast_z: float) -> str:
    if blk_z >= 0 and ast_z >= 0:
        return 'two_way_unicorn'
    if blk_z >= 0 and ast_z < 0:
        return 'swiper'
    if blk_z < 0 and ast_z >= 0:
        return 'floor_general'
    return 'dead_zone'


def quadrant_label_det(det_z: float, ast_z: float) -> str:
    if det_z >= 0 and ast_z >= 0:
        return 'two_way_unicorn'
    if det_z >= 0 and ast_z < 0:
        return 'swiper'
    if det_z < 0 and ast_z >= 0:
        return 'floor_general'
    return 'dead_zone'


def kmeans_naive(X: np.ndarray, k: int, seed: int = 42, max_iter: int = 200) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    idx = rng.choice(n, size=k, replace=False)
    centers = X[idx].copy()
    labels = np.zeros(n, dtype=int)
    for _ in range(max_iter):
        d = np.linalg.norm(X[:, None, :] - centers[None, :, :], axis=2)
        new_labels = d.argmin(axis=1)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for c in range(k):
            mask = labels == c
            if mask.sum() > 0:
                centers[c] = X[mask].mean(axis=0)
    return labels, centers


def main() -> None:
    career = pd.read_parquet(DATA_OUT / 'center_career_pool.parquet')
    seasons = pd.read_parquet(DATA_OUT / 'center_season_pool.parquet')
    print(f'[load] career pool: {len(career)} centers, {len(seasons)} center-seasons')

    career['blk_per_36_z'] = (career['blk_per_36'] - career['blk_per_36'].mean()) / career['blk_per_36'].std()
    career['ast_per_36_z'] = (career['ast_per_36'] - career['ast_per_36'].mean()) / career['ast_per_36'].std()
    career['reb_per_36_z'] = (career['reb_per_36'] - career['reb_per_36'].mean()) / career['reb_per_36'].std()
    career['stl_per_36_z'] = (career['stl_per_36'] - career['stl_per_36'].mean()) / career['stl_per_36'].std()
    career['fg3a_per_36_z'] = (career['fg3a_per_36'] - career['fg3a_per_36'].mean()) / career['fg3a_per_36'].std()
    career['ts_pct_z'] = (career['ts_pct'] - career['ts_pct'].mean()) / career['ts_pct'].std()

    career['quadrant_box'] = career.apply(
        lambda r: quadrant_label(r['blk_per_36_z'], r['ast_per_36_z']), axis=1
    )

    feat = career[['blk_per_36_z', 'ast_per_36_z']].values
    labels, centers = kmeans_naive(feat, k=4, seed=42)
    career['kmeans_box_k4'] = labels

    print('\n[quadrant_box] hand-coded quadrant counts:')
    print(career['quadrant_box'].value_counts().to_string())

    print('\n[quadrant_box] swipers (high BLK, low AST):')
    sw = career[career['quadrant_box'] == 'swiper'].sort_values('blk_per_36', ascending=False)
    print(sw[['name', 'blk_per_36', 'ast_per_36', 'reb_per_36']].to_string(index=False))

    print('\n[quadrant_box] floor generals (low BLK, high AST):')
    fg = career[career['quadrant_box'] == 'floor_general'].sort_values('ast_per_36', ascending=False)
    print(fg[['name', 'blk_per_36', 'ast_per_36', 'reb_per_36']].to_string(index=False))

    print('\n[quadrant_box] two-way unicorns (high BLK, high AST):')
    uni = career[career['quadrant_box'] == 'two_way_unicorn'].sort_values('blk_per_36', ascending=False)
    print(uni[['name', 'blk_per_36', 'ast_per_36', 'reb_per_36']].to_string(index=False))

    print('\n[quadrant_box] dead zone candidates (low BLK, low AST):')
    dz = career[career['quadrant_box'] == 'dead_zone'].sort_values('blk_per_36', ascending=False)
    print(dz[['name', 'blk_per_36', 'ast_per_36', 'reb_per_36']].to_string(index=False))

    print('\n[archetype] career deterrence axis (tracking era 2019-26)...')
    rim = pd.read_parquet(DATA_IN / 'player_def_rim.parquet')
    rim = rim[rim['season_type'] == 'Regular Season'].copy()
    rim['rim_supp'] = rim['ns_lt_06_pct'] - rim['lt_06_pct']
    rim['min_est'] = rim['gp'] * 30
    rim['rim_def_vol_per_36'] = rim['fga_lt_06'] / rim['min_est'] * 36

    rim_career = rim.groupby('close_def_person_id').apply(
        lambda g: pd.Series({
            'rim_supp_mean': np.average(g['rim_supp'], weights=g['fga_lt_06'].clip(lower=1)),
            'rim_supp_pct_allowed_mean': np.average(g['lt_06_pct'], weights=g['fga_lt_06'].clip(lower=1)),
            'rim_def_vol_per_36_mean': g['rim_def_vol_per_36'].mean(),
            'fga_lt_06_total': g['fga_lt_06'].sum(),
            'rim_n_seasons': g['season'].nunique(),
        }),
        include_groups=False,
    ).reset_index().rename(columns={'close_def_person_id': 'player_id'})

    merged = career.merge(rim_career, on='player_id', how='left')
    has_rim = merged.dropna(subset=['rim_supp_mean']).copy()
    print(f'[archetype] centers with rim defense data: {len(has_rim)} of {len(career)}')

    has_rim['rim_supp_z'] = (has_rim['rim_supp_mean'] - has_rim['rim_supp_mean'].mean()) / has_rim['rim_supp_mean'].std()
    has_rim['rim_vol_z'] = (has_rim['rim_def_vol_per_36_mean'] - has_rim['rim_def_vol_per_36_mean'].mean()) / has_rim['rim_def_vol_per_36_mean'].std()
    has_rim['deterrence_score'] = has_rim['rim_supp_z']

    has_rim['quadrant_deterrence'] = has_rim.apply(
        lambda r: quadrant_label_det(r['deterrence_score'], r['ast_per_36_z']), axis=1
    )

    print('\n[deterrence quadrant] counts:')
    print(has_rim['quadrant_deterrence'].value_counts().to_string())

    print('\n[deterrence] elite suppression (top 10):')
    top_supp = has_rim.sort_values('rim_supp_mean', ascending=False).head(10)
    print(top_supp[['name', 'blk_per_36', 'ast_per_36', 'rim_supp_mean', 'rim_supp_pct_allowed_mean', 'quadrant_deterrence']].to_string(index=False))

    print('\n[deterrence] elite floor-general by deterrence (high supp, high AST):')
    fg_det = has_rim[has_rim['quadrant_deterrence'] == 'floor_general'].sort_values('rim_supp_mean', ascending=False)
    print(fg_det[['name', 'blk_per_36', 'ast_per_36', 'rim_supp_mean', 'rim_supp_pct_allowed_mean']].to_string(index=False))

    print('\n[deterrence] swiper deterrence (high supp, low AST):')
    sw_det = has_rim[has_rim['quadrant_deterrence'] == 'swiper'].sort_values('rim_supp_mean', ascending=False)
    print(sw_det[['name', 'blk_per_36', 'ast_per_36', 'rim_supp_mean', 'rim_supp_pct_allowed_mean']].to_string(index=False))

    print('\n[deterrence] two-way unicorns (high supp, high AST):')
    uni_det = has_rim[has_rim['quadrant_deterrence'] == 'two_way_unicorn'].sort_values('rim_supp_mean', ascending=False)
    print(uni_det[['name', 'blk_per_36', 'ast_per_36', 'rim_supp_mean', 'rim_supp_pct_allowed_mean']].to_string(index=False))

    print('\n[deterrence] DEAD ZONE (low supp, low AST):')
    dz_det = has_rim[has_rim['quadrant_deterrence'] == 'dead_zone'].sort_values('rim_supp_mean', ascending=False)
    print(dz_det[['name', 'blk_per_36', 'ast_per_36', 'rim_supp_mean', 'rim_supp_pct_allowed_mean']].to_string(index=False))

    print('\n[critical test] BLK-vs-deterrence agreement check')
    has_rim['blk_quadrant'] = has_rim['quadrant_box']
    confusion = has_rim.groupby(['blk_quadrant', 'quadrant_deterrence']).size().unstack(fill_value=0)
    print(confusion.to_string())

    has_rim_full = career.merge(
        has_rim[['player_id', 'rim_supp_mean', 'rim_supp_pct_allowed_mean', 'rim_def_vol_per_36_mean',
                  'rim_supp_z', 'rim_vol_z', 'deterrence_score', 'quadrant_deterrence']],
        on='player_id', how='left'
    )
    has_rim_full.to_parquet(DATA_OUT / 'archetype_career.parquet', index=False)

    summary = {
        'built_at': pd.Timestamp.utcnow().isoformat(),
        'n_careers': int(len(career)),
        'n_with_deterrence': int(len(has_rim)),
        'quadrant_box_counts': career['quadrant_box'].value_counts().to_dict(),
        'quadrant_deterrence_counts': has_rim['quadrant_deterrence'].value_counts().to_dict(),
        'blk_vs_deterrence_confusion': confusion.to_dict(),
    }
    with open(DATA_OUT / 'archetype_build_summary.json', 'w') as fh:
        json.dump(summary, fh, indent=2)
    print(f'\n[write] {DATA_OUT / "archetype_career.parquet"}')
    print(f'[write] {DATA_OUT / "archetype_build_summary.json"}')


if __name__ == '__main__':
    main()
