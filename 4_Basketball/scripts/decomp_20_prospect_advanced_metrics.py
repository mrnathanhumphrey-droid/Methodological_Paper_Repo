"""Compute advanced metrics on 2026 NCAA prospects from PBP.

For each prospect identified by player_slug (NCAA id), compute:
  - STD: shot-type-diversity entropy across {layup, dunk, tip, hook, jumper_2pt, jumper_3pt}
  - And1R: and-1 conversion rate (scoring + foul drawn + FT make per poss)
  - FT_rate: free throws per minute (foul-drawing proxy)
  - DEF_rate: (steal + block + dreb) per minute (defensive activity)
  - TOV_rate: turnovers per minute
  - AST_RECEIVED: % of own makes that were assisted (read-and-react vs creation)
  - PSI: pass spread index (entropy across assist destinations)

These metrics inform the 2026 lottery synthesis — they're NCAA-level proxies of
the NBA novel offensive metrics suite we built earlier.

Output: data/parquet/prospect_advanced_metrics_2026.parquet
"""
from __future__ import annotations
import sys, warnings, re
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

PQ = Path("D:/NBA Projections/data/parquet")
PBP_PATH = Path("C:/NCAA D1 Mens/data/raw/play_by_play_2026.parquet")
GL_PATH = Path("C:/NCAA D1 Mens/data/processed/player_game_logs.csv")
OUT = PQ / "prospect_advanced_metrics_2026.parquet"

ASSIST_RE = re.compile(r"\(([^)]+) assists\)")


def shot_subtype(row):
    t = row.get("type_text")
    text = (row.get("text") or "").lower()
    if t == "DunkShot": return "DUNK"
    if t == "LayUpShot": return "LAYUP"
    if t == "TipShot": return "TIP"
    if t == "JumpShot":
        if "three point" in text or "3pt" in text or "3-foot" not in text and "three" in text:
            return "JUMP_3PT"
        if "hook" in text: return "HOOK"
        return "JUMP_2PT"
    return None


def entropy(p):
    p = np.asarray(p, dtype=float)
    p = p[p > 0]
    if not len(p): return 0.0
    p = p / p.sum()
    return float(-(p * np.log(p)).sum())


def main():
    print("=== loading PBP + game logs ===")
    pbp = pd.read_parquet(PBP_PATH)
    print(f"  PBP rows: {len(pbp):,}")
    pool = pd.read_parquet(PQ / "draft_2026_candidate_pool.parquet")
    pool_ncaa = pool[pool["has_ncaa"]].copy()
    print(f"  NCAA 2026 prospects in pool: {len(pool_ncaa)}")

    gl = pd.read_csv(GL_PATH, usecols=["team", "player", "player_slug", "season", "mp_minutes"])
    gl_26 = gl[gl["season"] == 2026].copy()
    name_slug_min = (gl_26.dropna(subset=["player_slug"])
                                       .groupby(["player", "player_slug"])
                                       .agg(mp_total=("mp_minutes", "sum"))
                                       .reset_index())
    name_slug_min["player_slug"] = name_slug_min["player_slug"].astype(str).str.replace(r"\.0$", "", regex=True)

    from rapidfuzz import process, fuzz
    name_pool_list = name_slug_min["player"].tolist()

    pool_ncaa["ncaa_player_slug"] = pool_ncaa["ncaa_match_name"].apply(
        lambda n: name_slug_min[name_slug_min["player"] == n]["player_slug"].iloc[0]
        if n in set(name_slug_min["player"]) else
        (name_slug_min[name_slug_min["player"] == process.extractOne(n, name_pool_list, score_cutoff=85)[0]]["player_slug"].iloc[0]
        if n and process.extractOne(n, name_pool_list, score_cutoff=85) else None)
    )

    matched = pool_ncaa[pool_ncaa["ncaa_player_slug"].notna()]
    print(f"  matched to PBP slug: {len(matched)}/{len(pool_ncaa)}")

    pbp["athlete_id_str"] = pbp["athlete_id_1"].apply(
        lambda x: str(int(x)) if pd.notna(x) else None)
    pbp["assist_name"] = pbp["text"].apply(
        lambda t: ASSIST_RE.search(t).group(1) if isinstance(t, str) and ASSIST_RE.search(t) else None)

    rows = []
    for _, r in matched.iterrows():
        slug = r["ncaa_player_slug"]
        actions = pbp[pbp["athlete_id_str"] == slug]
        if not len(actions):
            continue

        mp = float(name_slug_min[name_slug_min["player_slug"] == slug]["mp_total"].iloc[0])
        if mp < 100: continue

        scoring_makes = actions[
            actions["type_text"].isin(["JumpShot", "LayUpShot", "DunkShot", "TipShot"])
            & (actions["scoring_play"] == True)
        ].copy()
        scoring_makes["subtype"] = scoring_makes.apply(shot_subtype, axis=1)
        subtype_dist = scoring_makes["subtype"].value_counts()
        std = entropy(subtype_dist.values)

        all_attempts = actions[actions["type_text"].isin(["JumpShot", "LayUpShot", "DunkShot", "TipShot"])]
        n_makes = len(scoring_makes)
        n_attempts = len(all_attempts)

        ft_makes = actions[actions["type_text"] == "MadeFreeThrow"]
        ft_makes_n = len(ft_makes)
        ft_rate = ft_makes_n / (mp / 40.0)

        steals = (actions["type_text"] == "Steal").sum()
        blocks = (actions["type_text"] == "Block Shot").sum()
        dreb = (actions["type_text"] == "Defensive Rebound").sum()
        oreb = (actions["type_text"] == "Offensive Rebound").sum()
        tov = (actions["type_text"] == "Lost Ball Turnover").sum()
        pf = (actions["type_text"] == "PersonalFoul").sum()

        def_rate = (steals + blocks + dreb) / (mp / 40.0)
        tov_rate = tov / (mp / 40.0)
        pf_rate = pf / (mp / 40.0)

        ast_credited_to_this_player = pbp[
            (pbp["assist_name"].notna())
            & (pbp["text"].astype(str).str.contains(r["ncaa_match_name"], na=False))
            & (pbp["assist_name"].str.contains(r["ncaa_match_name"], na=False))
        ]
        n_assists_made = len(pbp[pbp["assist_name"] == r["ncaa_match_name"]])
        assist_targets = pbp[pbp["assist_name"] == r["ncaa_match_name"]]
        target_dist = assist_targets["text"].apply(
            lambda t: t.split(" makes")[0].strip() if isinstance(t, str) else None
        ).value_counts() if len(assist_targets) else pd.Series(dtype=int)
        psi = entropy(target_dist.values) if len(target_dist) else 0.0

        rows.append({
            "player_name": r["player_name"],
            "ncaa_match_name": r["ncaa_match_name"],
            "ncaa_player_slug": slug,
            "mp_total": mp,
            "n_attempts": int(n_attempts), "n_makes": int(n_makes),
            "n_dunks": int(subtype_dist.get("DUNK", 0)),
            "n_layups": int(subtype_dist.get("LAYUP", 0)),
            "n_jumpers_2pt": int(subtype_dist.get("JUMP_2PT", 0)),
            "n_jumpers_3pt": int(subtype_dist.get("JUMP_3PT", 0)),
            "n_tips": int(subtype_dist.get("TIP", 0)),
            "n_hooks": int(subtype_dist.get("HOOK", 0)),
            "STD": std,
            "ft_makes": ft_makes_n, "ft_rate_per40": ft_rate,
            "n_steals": int(steals), "n_blocks": int(blocks),
            "n_dreb": int(dreb), "n_oreb": int(oreb),
            "n_tov": int(tov), "n_pf": int(pf),
            "def_event_rate_per40": def_rate,
            "tov_rate_per40": tov_rate,
            "pf_rate_per40": pf_rate,
            "n_assists_made": n_assists_made,
            "PSI": psi,
            "n_unique_assist_targets": len(target_dist),
        })

    df = pd.DataFrame(rows)
    df.to_parquet(OUT, index=False)
    df.to_csv(OUT.with_suffix(".csv"), index=False)
    print(f"\nwrote: {OUT}")
    print(f"  rows: {len(df)}")

    print("\n=== top 15 by STD (shot type diversity, high = versatile) ===")
    cols = ["player_name", "mp_total", "n_makes", "STD", "n_dunks", "n_layups",
              "n_jumpers_2pt", "n_jumpers_3pt"]
    print(df.sort_values("STD", ascending=False).head(15)[cols].round(2).to_string(index=False))

    print("\n=== top 15 by PSI (pass spread, high = redistributor) ===")
    print(df[df["n_assists_made"] >= 30].sort_values("PSI", ascending=False).head(15)[
        ["player_name", "n_assists_made", "n_unique_assist_targets", "PSI"]].round(2).to_string(index=False))

    print("\n=== top 15 by FT rate per-40 (foul drawing) ===")
    print(df.sort_values("ft_rate_per40", ascending=False).head(15)[
        ["player_name", "mp_total", "ft_makes", "ft_rate_per40"]].round(2).to_string(index=False))

    print("\n=== top 15 by defensive event rate per-40 (stl+blk+dreb) ===")
    print(df.sort_values("def_event_rate_per40", ascending=False).head(15)[
        ["player_name", "mp_total", "n_steals", "n_blocks", "n_dreb", "def_event_rate_per40"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
