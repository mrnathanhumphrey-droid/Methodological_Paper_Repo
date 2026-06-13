"""Build outcome-calibrated training set: rookies_master + league label + age proxy.

Augments the 501-prospect historical pool with:
  - pre_nba_league_label: NCAA_<conference> (P5/MID/LOW grouping), "g_league", "intl_other"
  - pre_nba_age_proxy: derived from class (FR=19, SO=20, JR=21, SR=22) or years_pre_nba+18
  - position_bucket: G / W / B from combine position
  - source: which pre-NBA stat panel we used (ncaa / intl / both)

NCAA conference → tier mapping (3-tier):
  P5  = ACC / Big Ten / Big 12 / SEC / Pac-12 (legacy) / Big East
  MID = AAC / MWC / A-10 / WCC / CUSA / MAC / MVC / Sun Belt / Horizon
  LOW = everything else (CAA, Big Sky, OVC, Southern, etc.)

Output:
    data/parquet/rookies_outcome_training.parquet
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

PQ = Path("D:/NBA Projections/data/parquet")
OUT = PQ / "rookies_outcome_training.parquet"

CONF_P5 = {"ACC", "Big Ten", "Big 12", "SEC", "Pac-12", "Big East"}
CONF_MID = {"AAC", "American Athletic", "MWC", "Mountain West", "A-10", "Atlantic 10",
                       "WCC", "West Coast", "CUSA", "Conference USA", "MAC", "Mid-American",
                       "MVC", "Missouri Valley", "Sun Belt", "Horizon"}


def conf_tier(c):
    if pd.isna(c): return None
    s = str(c)
    if s in CONF_P5: return "P5"
    if s in CONF_MID: return "MID"
    return "LOW"


def position_bucket(p):
    if p is None or (isinstance(p, float) and np.isnan(p)): return "UNK"
    s = str(p).upper()
    if "C" in s and "F" not in s and "G" not in s: return "B"
    if "PF" in s or "PF" == s: return "B"
    if "C" in s: return "B"
    if "F" in s and "G" not in s: return "W"
    if "SF" in s or "PF" in s: return "W"
    if "G" in s: return "G"
    return "UNK"


def age_proxy(row):
    cls = row.get("ncaa_ncaa_class_at_draft")
    if pd.notna(cls):
        return {"FR": 19, "SO": 20, "JR": 21, "SR": 22}.get(str(cls), 20)
    yrs = row.get("intl_years_pre_nba")
    if pd.notna(yrs):
        return 18 + int(yrs)
    age = row.get("nba_y1_player_age")
    if pd.notna(age):
        return int(age)
    return 20


def main():
    m = pd.read_parquet(PQ / "rookies_master.parquet")
    ncaa = pd.read_parquet(PQ / "ncaa_player_seasons.parquet")
    print(f"  rookies_master: {len(m):,}")
    print(f"  ncaa_player_seasons: {len(ncaa):,}")

    last_conf = (ncaa.sort_values(["draft_year", "ncaa_season"])
                                 .groupby("draft_year")
                                 .agg(school_conference=("school_conference", "last")))
    school_conf = (ncaa.sort_values("ncaa_season")
                              .drop_duplicates("ncaa_player_slug", keep="last")
                              [["ncaa_player_slug", "school_conference", "school"]])

    name_to_conf = {}
    for _, r in ncaa.dropna(subset=["player_name_raw", "school_conference"]).iterrows():
        name_to_conf[r["player_name_raw"]] = r["school_conference"]
    print(f"  name→conference dict: {len(name_to_conf):,}")

    m["pre_nba_conference"] = m["player_name_raw"].map(name_to_conf)
    m["pre_nba_conf_tier"] = m["pre_nba_conference"].apply(conf_tier)

    def league_label(row):
        if pd.notna(row.get("pre_nba_conf_tier")):
            return f"NCAA_{row['pre_nba_conf_tier']}"
        if pd.notna(row.get("intl_league")):
            return f"intl_{row['intl_league']}"
        if row.get("has_intl"):
            return "intl_other"
        return "unknown"
    m["pre_nba_league_label"] = m.apply(league_label, axis=1)

    m["pre_nba_age"] = m.apply(age_proxy, axis=1)
    m["position_bucket"] = m["combine_position"].apply(position_bucket) if "combine_position" in m.columns else "UNK"

    for stat, lbl in [("pts_per40", "ppg_pre"), ("reb_per40", "rpg_pre"),
                                ("ast_per40", "apg_pre"), ("stl_per40", "spg_pre"),
                                ("blk_per40", "bpg_pre"), ("tov_per40", "tov_pre"),
                                ("fg3m_per40", "fg3m_pre"), ("fg_pct", "fg_pct_pre"),
                                ("fg3_pct", "fg3_pct_pre"), ("ft_pct", "ft_pct_pre")]:
        ncaa_c, intl_c = f"ncaa_{stat}", f"intl_{stat}"
        m[lbl] = np.nan
        if ncaa_c in m.columns: m[lbl] = m[ncaa_c]
        if intl_c in m.columns:
            m[lbl] = m[lbl].where(m[lbl].notna(), m[intl_c])

    print("\n=== league_label distribution ===")
    print(m["pre_nba_league_label"].value_counts().to_string())
    print("\n=== conference distribution (NCAA only) ===")
    print(m.loc[m["pre_nba_league_label"].str.startswith("NCAA_", na=False), "pre_nba_conference"].value_counts().head(20).to_string())
    print("\n=== age proxy distribution ===")
    print(m["pre_nba_age"].describe().round(1).to_string())

    keep_cols = [
        "nba_api_id", "player_name_raw", "draft_year", "draft_pick", "draft_round",
        "pre_nba_league_label", "pre_nba_conference", "pre_nba_conf_tier",
        "pre_nba_age", "position_bucket",
        "ppg_pre", "rpg_pre", "apg_pre", "spg_pre", "bpg_pre", "tov_pre", "fg3m_pre",
        "fg_pct_pre", "fg3_pct_pre", "ft_pct_pre",
        "has_nba_y1", "has_nba_y2", "has_nba_y3",
        "nba_y1_gp", "nba_y1_mpg",
        "nba_y1_pts_per36", "nba_y1_reb_per36", "nba_y1_ast_per36",
        "nba_y1_stl_per36", "nba_y1_blk_per36", "nba_y1_fg3m_per36", "nba_y1_tov_per36",
        "nba_y1_fg_pct", "nba_y1_fg3_pct", "nba_y1_ft_pct",
        "nba_y2_gp", "nba_y2_mpg", "nba_y2_pts_per36", "nba_y2_reb_per36",
        "nba_y2_ast_per36", "nba_y2_stl_per36", "nba_y2_blk_per36", "nba_y2_fg3m_per36",
    ]
    keep_cols = [c for c in keep_cols if c in m.columns]
    out = m[keep_cols].copy()
    out.to_parquet(OUT, index=False)
    print(f"\nwrote: {OUT}")
    print(f"  rows: {len(out):,}, cols: {len(out.columns)}")


if __name__ == "__main__":
    main()
