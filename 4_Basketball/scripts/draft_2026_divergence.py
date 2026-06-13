"""
2026 draft — model (oc4) vs consensus (Vecenie + other scout boards) divergence map.

Surfaces:
  - Top 25 by model rank
  - Top 25 by consensus rank
  - Model steals (model top 15, consensus ≥ 20 OR not on board)
  - Model fades (consensus top 10, model ≥ 20)
  - Biggest |Δrank|

For draft night in 5 days.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path(r"D:/NBA Projections")
DR_SCOUT = Path(r"D:/Draft Resolve/data/parquet/scout_ranks_raw.parquet")


def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    import unicodedata, re
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip()
    for suf in [' jr.', ' sr.', ' iii', ' ii']:
        if s.endswith(suf):
            s = s[: -len(suf)].strip()
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def main():
    print('=' * 78)
    print('2026 Draft — Model vs Consensus Divergence Map')
    print('=' * 78)

    oc4 = pd.read_parquet(ROOT / 'data' / 'parquet' / 'draft_2026_outcome_calibrated_v4.parquet')
    print(f'[load] oc4: {len(oc4)} prospects')

    scout = pd.read_parquet(DR_SCOUT)
    scout = scout[scout['draft_year'] == 2026].copy()
    scout['rank'] = pd.to_numeric(scout['rank'], errors='coerce')
    scout = scout[scout['rank'].notna()].copy()
    print(f'[load] 2026 scout rows: {len(scout)} from {scout["scout"].nunique()} sources')

    scout['name_norm'] = scout['player_name_raw'].map(normalize_name)
    consensus = scout.groupby('name_norm').agg(
        consensus_rank=('rank', 'mean'),
        n_scouts=('rank', 'count'),
        scout_min=('rank', 'min'),
        scout_max=('rank', 'max'),
        display_name=('player_name_raw', 'first'),
    ).reset_index()

    oc4['name_norm'] = oc4['player_name_raw'].map(normalize_name) if 'player_name_raw' in oc4.columns else oc4['player_name'].map(normalize_name)
    df = oc4.merge(consensus, on='name_norm', how='outer', suffixes=('_oc4', '_cons'))

    df['model_rank'] = df['oc4_rank']
    df['model_name'] = df['player_name'] if 'player_name' in df.columns else None
    df['display_name'] = df['display_name'].fillna(df['model_name'])
    df['consensus_rank'] = df['consensus_rank']
    df['has_model'] = df['oc4_rank'].notna()
    df['has_consensus'] = df['consensus_rank'].notna()

    print(f'\n[merge] {len(df)} rows total')
    print(f'  in both: {(df["has_model"] & df["has_consensus"]).sum()}')
    print(f'  model only: {(df["has_model"] & ~df["has_consensus"]).sum()}')
    print(f'  consensus only: {(~df["has_model"] & df["has_consensus"]).sum()}')

    print(f'\n=== TOP 25 by MODEL rank (oc4) ===')
    cols_model = ['model_rank', 'display_name', 'position', 'pre_nba_league_label',
                   'consensus_rank', 'archetype', 'oc4_tier']
    top_m = df[df['has_model']].sort_values('model_rank').head(25)
    print(top_m[cols_model].to_string(index=False))

    print(f'\n=== TOP 25 by CONSENSUS rank (Vecenie + others) ===')
    cols_cons = ['consensus_rank', 'display_name', 'position', 'model_rank',
                  'archetype', 'oc4_tier']
    top_c = df[df['has_consensus']].sort_values('consensus_rank').head(25)
    print(top_c[cols_cons].to_string(index=False))

    print(f'\n=== ★ MODEL STEALS (model top 15, consensus ≥ 20 OR not on board) ===')
    steals = df[
        (df['model_rank'] <= 15)
        & ((df['consensus_rank'] >= 20) | (df['consensus_rank'].isna()))
    ].sort_values('model_rank')
    if len(steals):
        print(steals[['model_rank', 'display_name', 'consensus_rank', 'position',
                      'pre_nba_league_label', 'archetype']].to_string(index=False))
    else:
        print('  none')

    print(f'\n=== ✗ MODEL FADES (consensus top 10, model ≥ 20 OR off board) ===')
    fades = df[
        (df['consensus_rank'] <= 10)
        & ((df['model_rank'] >= 20) | (df['model_rank'].isna()))
    ].sort_values('consensus_rank')
    if len(fades):
        print(fades[['consensus_rank', 'display_name', 'model_rank', 'position',
                     'archetype']].to_string(index=False))
    else:
        print('  none')

    print(f'\n=== BIGGEST DIVERGENCES (|model_rank - consensus_rank|) ===')
    both = df[df['has_model'] & df['has_consensus']].copy()
    both['delta'] = both['consensus_rank'] - both['model_rank']
    both['abs_delta'] = both['delta'].abs()
    big = both.sort_values('abs_delta', ascending=False).head(20)
    print(big[['display_name', 'consensus_rank', 'model_rank', 'delta',
               'position', 'archetype']].to_string(index=False))

    out = Path(r"D:/NBA Projections/data/parquet/draft_2026_divergence.parquet")
    df.to_parquet(out, index=False)
    print(f'\n[write] {out}')


if __name__ == '__main__':
    main()
