"""Audit available phase4_v4_quadratic_tq_g per-stat ships per (stat, target_season).

Used to map historical season projections into the playoff backtest pipeline.
"""
import glob, re
from collections import defaultdict

pattern = re.compile(r'skill_backtest_([A-Z3]+)_phase4_v4_quadratic_tq_g_[0-9-]+__([0-9-]+)/per_player_projections\.csv$')
hits = defaultdict(list)

for f in glob.glob('audit_runs/*/skill_backtest_*_phase4_v4_quadratic_tq_g_*__*/per_player_projections.csv'):
    fn = f.replace('\\', '/')
    m = pattern.search(fn)
    if not m:
        continue
    stat, target = m.group(1), m.group(2)
    ts = fn.split('/')[1]
    hits[(stat, target)].append((ts, fn))

print('Latest phase4_v4_quadratic_tq_g ship per (stat, target_season):')
for k in sorted(hits.keys()):
    latest = sorted(hits[k])[-1]
    print(f'  {k}: {latest[1]}')
print()
print(f'total (stat, target_season) pairs: {len(hits)}')

stats = sorted({k[0] for k in hits})
targets = sorted({k[1] for k in hits})
print(f'\nstats covered: {stats}')
print(f'targets covered: {targets}')

print('\nCoverage matrix:')
header = '  stat / season   ' + '   '.join(f'{t:>8}' for t in targets)
print(header)
for s in stats:
    row = f'  {s:>14}   '
    for t in targets:
        row += f'{"X" if (s, t) in hits else "-":>8}   '
    print(row)
