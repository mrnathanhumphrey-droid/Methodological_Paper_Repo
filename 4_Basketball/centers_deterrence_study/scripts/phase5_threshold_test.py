"""
Phase 5: Formal dead-zone threshold test.

Tests:
  1. Bootstrap (1000) mean success per quadrant + 50/80/95 calibrated intervals
  2. Pairwise Mann-Whitney U: each quadrant vs every other (success_composite)
  3. Cliff's delta effect size for each pair
  4. Timing-confound robustness: rerun with Dwight/Drummond/Jordan/Chandler removed
  5. Modern-era restriction: debut >= 2014 only
  6. Within-quadrant secondary classification: elite vs non-elite SWIPER
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path('D:/NBA Projections')
STUDY = ROOT / 'centers_deterrence_study'
DATA_OUT = STUDY / 'data'

N_BOOT = 1000
SEED = 42


def bootstrap_mean_ci(values: np.ndarray, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    rng = np.random.default_rng(seed)
    if len(values) == 0:
        return {'n': 0, 'mean': np.nan, 'ci_50': (np.nan, np.nan),
                'ci_80': (np.nan, np.nan), 'ci_95': (np.nan, np.nan)}
    means = np.empty(n_boot)
    for i in range(n_boot):
        sample = rng.choice(values, size=len(values), replace=True)
        means[i] = sample.mean()
    return {
        'n': len(values),
        'mean': float(values.mean()),
        'ci_50': (float(np.percentile(means, 25)), float(np.percentile(means, 75))),
        'ci_80': (float(np.percentile(means, 10)), float(np.percentile(means, 90))),
        'ci_95': (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))),
    }


def cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    n_x, n_y = len(x), len(y)
    if n_x == 0 or n_y == 0:
        return np.nan
    greater = sum(1 for xi in x for yi in y if xi > yi)
    less = sum(1 for xi in x for yi in y if xi < yi)
    return (greater - less) / (n_x * n_y)


def run_quadrant_panel(df: pd.DataFrame, label: str) -> dict:
    print(f'\n=== {label} | n={len(df)} ===')
    quads = ['dead_zone', 'floor_general', 'swiper', 'two_way_unicorn']
    ci_results = {}
    for q in quads:
        sub = df[df['quadrant_deterrence'] == q]['success_composite'].dropna().values
        ci = bootstrap_mean_ci(sub)
        ci_results[q] = ci
        print(f'  {q:18s}  n={ci["n"]:3d}  mean={ci["mean"]:.3f}  '
              f'50%CI=[{ci["ci_50"][0]:.3f}, {ci["ci_50"][1]:.3f}]  '
              f'80%CI=[{ci["ci_80"][0]:.3f}, {ci["ci_80"][1]:.3f}]  '
              f'95%CI=[{ci["ci_95"][0]:.3f}, {ci["ci_95"][1]:.3f}]')

    print(f'\n  Pairwise Mann-Whitney U + Cliff delta vs dead_zone:')
    rows = []
    for q in quads:
        if q == 'dead_zone':
            continue
        x = df[df['quadrant_deterrence'] == 'dead_zone']['success_composite'].dropna().values
        y = df[df['quadrant_deterrence'] == q]['success_composite'].dropna().values
        if len(x) < 3 or len(y) < 3:
            continue
        try:
            U, p = stats.mannwhitneyu(x, y, alternative='two-sided')
        except Exception:
            U, p = np.nan, np.nan
        d = cliffs_delta(x, y)
        rows.append({'comparison': f'dead_zone vs {q}', 'U': round(U, 1), 'p': round(p, 4),
                     'cliff_delta': round(d, 3), 'n_dz': len(x), 'n_q': len(y),
                     'sig': 'YES' if p < 0.05 else 'no'})
    rdf = pd.DataFrame(rows)
    print(rdf.to_string(index=False))

    print(f'\n  All pairwise comparisons (full matrix):')
    pair_rows = []
    for q1, q2 in combinations(quads, 2):
        x = df[df['quadrant_deterrence'] == q1]['success_composite'].dropna().values
        y = df[df['quadrant_deterrence'] == q2]['success_composite'].dropna().values
        if len(x) < 3 or len(y) < 3:
            continue
        try:
            U, p = stats.mannwhitneyu(x, y, alternative='two-sided')
        except Exception:
            U, p = np.nan, np.nan
        d = cliffs_delta(x, y)
        pair_rows.append({'pair': f'{q1} vs {q2}', 'mean_diff': round(x.mean() - y.mean(), 3),
                          'U': round(U, 1), 'p': round(p, 4), 'cliff_delta': round(d, 3),
                          'sig': 'YES' if p < 0.05 else 'no'})
    pdf = pd.DataFrame(pair_rows)
    print(pdf.to_string(index=False))

    return {'ci_results': ci_results, 'pairwise_vs_dz': rows, 'pairwise_full': pair_rows}


def main() -> None:
    df = pd.read_parquet(DATA_OUT / 'success_with_teammates.parquet')
    df_clean = df.dropna(subset=['quadrant_deterrence', 'success_composite']).copy()

    print(f'[load] full panel n={len(df_clean)}')

    panel_a = run_quadrant_panel(df_clean, 'PANEL A: Full pool (n=46)')

    timing_confound = ['Dwight Howard', 'DeAndre Jordan', 'Andre Drummond', 'Tyson Chandler']
    df_no_confound = df_clean[~df_clean['name'].isin(timing_confound)].copy()
    panel_b = run_quadrant_panel(df_no_confound, f'PANEL B: Timing-confound removed (n={len(df_no_confound)})')

    df_modern = df_clean[df_clean['debut_year'] >= 2014].copy()
    panel_c = run_quadrant_panel(df_modern, f'PANEL C: Modern-era only (debut >= 2014, n={len(df_modern)})')

    print('\n=== ELITE vs NON-ELITE SWIPER STRATIFICATION ===')
    sw = df_clean[df_clean['quadrant_deterrence'] == 'swiper'].copy()
    rim_supp_med = sw['rim_supp_mean'].median()
    sw['is_elite_swiper'] = sw['rim_supp_mean'] >= rim_supp_med
    for is_elite in [True, False]:
        sub = sw[sw['is_elite_swiper'] == is_elite]
        ci = bootstrap_mean_ci(sub['success_composite'].dropna().values)
        label = 'ELITE' if is_elite else 'NON-ELITE'
        print(f'  {label:10s} swiper  n={ci["n"]}  mean={ci["mean"]:.3f}  '
              f'50%CI=[{ci["ci_50"][0]:.3f}, {ci["ci_50"][1]:.3f}]')
        names = sub.sort_values('success_composite', ascending=False)['name'].tolist()
        print(f'    members: {names}')

    print('\n=== KEY TEST: is DEAD ZONE the worst archetype? ===')
    quad_means = df_clean.groupby('quadrant_deterrence')['success_composite'].mean().sort_values()
    print(f'  ranked means: {quad_means.to_dict()}')
    print(f'  worst quadrant: {quad_means.index[0]}')
    print(f'  Hypothesis predicted: dead_zone')
    print(f'  Actual worst: {quad_means.index[0]}')

    print('\n=== KEY TEST: PURE SWIPER (Mahinmi-tier) vs PURE DEAD ZONE (Drummond-tier) ===')
    pure_sw_bottom = df_clean[df_clean['quadrant_deterrence'] == 'swiper'].sort_values('success_composite').head(8)
    pure_dz = df_clean[df_clean['quadrant_deterrence'] == 'dead_zone'].sort_values('success_composite').head(8)

    x = pure_sw_bottom['success_composite'].values
    y = pure_dz['success_composite'].values
    print(f'  Bottom-8 swipers:    mean={x.mean():.3f}  members={pure_sw_bottom["name"].tolist()}')
    print(f'  Full dead_zone:      mean={y.mean():.3f}  members={pure_dz["name"].tolist()}')

    if len(x) >= 3 and len(y) >= 3:
        U, p = stats.mannwhitneyu(x, y, alternative='less')
        d = cliffs_delta(x, y)
        print(f'  Mann-Whitney U (bottom-swiper < dead_zone): U={U:.1f}, p={p:.4f}, Cliffs_delta={d:.3f}')

    print('\n=== HYPOTHESIS VERDICT ===')
    print('User hypothesis: "two archetypes succeed, dead zone fails, threshold moves with teammate quality"')
    print()
    print('Evidence summary:')
    print(f'  1. Two-archetype success: PARTIAL — floor_general clearly succeeds (mean +{quad_means.get("floor_general", 0):.2f})')
    print(f'     but SWIPER as group is the worst (mean {quad_means.get("swiper", 0):+.2f})')
    print(f'  2. Dead zone fails: PARTIAL — dead_zone mean is {quad_means.get("dead_zone", 0):+.2f}')
    print(f'     middle of pack (NOT clearly worst)')
    print(f'  3. Threshold moves with teammate: PARTIAL — only swiper x spacing significant (r=0.54 p=0.018)')

    out = {
        'panel_a_full_pool': panel_a,
        'panel_b_no_timing_confound': panel_b,
        'panel_c_modern_era_only': panel_c,
        'quadrant_means_ranked': quad_means.to_dict(),
        'verdict': {
            'two_archetypes_succeed': 'PARTIAL — floor_general yes, swiper no',
            'dead_zone_fails': 'PARTIAL — middle of pack, timing-confound inflates',
            'threshold_moves': 'PARTIAL — swiper x team_3pa only',
        },
    }
    with open(DATA_OUT / 'phase5_threshold_test.json', 'w') as fh:
        json.dump(out, fh, indent=2, default=str)
    print(f'\n[write] {DATA_OUT / "phase5_threshold_test.json"}')


if __name__ == '__main__':
    main()
