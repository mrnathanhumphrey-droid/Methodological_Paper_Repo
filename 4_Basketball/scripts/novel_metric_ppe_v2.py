"""PPE v2 — Pass-Pattern Entropy with team-shot-share baseline.

V1 failure mode: normalized entropy over n_unique_targets is dominated by
small-sample noise. Mid-volume role players hit ~1.0 entropy because their
30 assists ÷ 19 targets ≈ near-uniform by force.

V2 fixes:
1. Min sample threshold: n_assists >= 200
2. Baseline = TEAM SHOT-SHARE distribution (the natural floor for who scores)
   - For each player, get their team's scoring distribution among the players
     they actually assisted (a teammate who doesn't score gets share=0)
   - Then PPE = KL-divergence(player_assist_dist || team_score_share)
   - High KL = player distributes DIFFERENTLY from team scoring → creative
   - Low KL = player distributes proportionally to who naturally scores → bog standard
3. Also report: HHI (concentration index) and "Top-3 share" (concrete read)

Test bed: same 2024-25 PBP.
"""
from __future__ import annotations
import sys, re, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

PBP = "D:/NBA Projections/data/parquet/pbp/pbp_2024-25.parquet"
OUT = Path("D:/NBA Projections/data/results")
OUT_PATH = OUT / "ppe_v2_2024_25.parquet"

ASSIST_RX = re.compile(r"\(([A-Za-zÀ-ÿ\-\'\.À-ſ ]+?)\s+\d+\s+AST\)")
MIN_N = 200  # min assists to qualify


def main():
    print("=== loading PBP ===")
    df = pd.read_parquet(PBP)
    made = df[df["action_type"] == "Made Shot"].dropna(subset=["description","person_id","team_id"]).copy()
    made["assister_last"] = made["description"].str.extract(ASSIST_RX, expand=False)

    # Roster lookup (per game-team-player_name -> person_id)
    sample = df.dropna(subset=["player_name","person_id","team_id"])
    roster = sample.groupby(["game_id","team_id","player_name"])["person_id"].first().reset_index()
    pid_to_name = roster.drop_duplicates(subset=["person_id"]).set_index("person_id")["player_name"].to_dict()

    # Resolve assister_id
    rmap = {(g,t,p): pid for g,t,p,pid in zip(roster["game_id"], roster["team_id"],
                                                roster["player_name"], roster["person_id"])}
    assists = made.dropna(subset=["assister_last"]).copy()
    assists["assister_last"] = assists["assister_last"].str.strip()
    assists["assister_id"] = [rmap.get((g,t,a)) for g,t,a in
                                zip(assists["game_id"], assists["team_id"], assists["assister_last"])]
    # fallback by last-token
    unm = assists[assists["assister_id"].isna()]
    if len(unm):
        roster["last_token"] = roster["player_name"].str.split().str[-1]
        rmap2 = {(g,t,lt): pid for g,t,lt,pid in zip(roster["game_id"], roster["team_id"],
                                                       roster["last_token"], roster["person_id"])}
        alt = [rmap2.get((g,t,a)) for g,t,a in zip(unm["game_id"], unm["team_id"], unm["assister_last"])]
        assists.loc[unm.index, "assister_id"] = alt
    assists = assists.dropna(subset=["assister_id"]).copy()
    assists["assister_id"] = assists["assister_id"].astype(int)
    assists["scorer_id"] = assists["person_id"].astype(int)
    print(f"  resolved assists: {len(assists):,}")

    # Determine each assister's primary team this season (modal team_id)
    assister_team = (assists.groupby("assister_id")["team_id"].agg(lambda s: s.value_counts().idxmax())
                              .reset_index().rename(columns={"team_id":"primary_team"}))
    assists = assists.merge(assister_team, on="assister_id")
    # restrict to assists thrown for the assister's primary team (handles trade-deadline noise)
    assists = assists[assists["team_id"] == assists["primary_team"]]

    # Team scoring distribution: each scorer's MADE-SHOT count on each team
    team_scoring = (made.groupby(["team_id","person_id"]).size()
                          .reset_index(name="team_makes"))
    team_totals  = team_scoring.groupby("team_id")["team_makes"].sum().reset_index().rename(columns={"team_makes":"team_total_makes"})
    team_scoring = team_scoring.merge(team_totals, on="team_id")
    team_scoring["team_share"] = team_scoring["team_makes"] / team_scoring["team_total_makes"]
    # lookup dict: (team_id, person_id) -> team_share
    team_share_map = {(t,p): s for t,p,s in zip(team_scoring["team_id"], team_scoring["person_id"],
                                                  team_scoring["team_share"])}

    rows = []
    for aid, sub in assists.groupby("assister_id"):
        n = len(sub)
        if n < MIN_N: continue
        team = int(sub["primary_team"].iloc[0])
        target_counts = sub["scorer_id"].value_counts()
        targets = target_counts.index.values
        p = target_counts.values / n   # player's actual distribution

        # Baseline: team scoring share among the SAME set of targets
        baseline = np.array([team_share_map.get((team, int(t)), 1e-6) for t in targets])
        baseline = baseline / baseline.sum()  # renormalize on the support

        # KL(player || baseline) — positive = distributing differently than team scoring
        # Sign: if KL > 0 and player spreads more evenly, "creative spreader"; if KL > 0
        # and player concentrates HARDER than baseline, "tunnel-vision"
        # We want a signed metric → compute Shannon entropy of player + baseline separately
        H_p = -np.sum(p * np.log(p + 1e-12))
        H_b = -np.sum(baseline * np.log(baseline + 1e-12))
        kl  = float(np.sum(p * np.log((p + 1e-12) / (baseline + 1e-12))))
        # H_p - H_b > 0 means player MORE spread than team baseline (positive creativity)
        spread_premium = H_p - H_b
        # HHI for concentration
        hhi = float(np.sum(p**2))
        top1_share = float(p.max())
        top3_share = float(np.sort(p)[-3:].sum())
        n_meaningful = int((p >= 0.02).sum())  # targets with >=2% share

        top_idx = int(target_counts.index[0])
        rows.append({
            "assister_id":  int(aid),
            "assister_name":  pid_to_name.get(int(aid), str(aid)),
            "primary_team": team,
            "n_assists":    int(n),
            "n_targets":    int(len(p)),
            "H_player":     float(H_p),
            "H_baseline":   float(H_b),
            "spread_premium": float(spread_premium),  # H_p - H_b
            "kl_to_baseline": float(kl),
            "hhi":          float(hhi),
            "top1_share":   top1_share,
            "top3_share":   top3_share,
            "n_meaningful": n_meaningful,
            "top_target":   pid_to_name.get(top_idx, str(top_idx)),
        })
    ppe = pd.DataFrame(rows)
    print(f"  qualifying passers (n>={MIN_N}): {len(ppe)}")

    ppe.to_parquet(OUT_PATH, index=False)
    ppe.to_csv(OUT_PATH.with_suffix(".csv"), index=False)
    print(f"\nwrote: {OUT_PATH}")

    # ===== Face-validity checks =====
    cols_show = ["assister_name","n_assists","n_targets","H_player","H_baseline",
                  "spread_premium","top1_share","top3_share","top_target"]

    print("\n=== TOP 25 by spread_premium (H_p - H_b) — SPREAD MORE EVENLY than team scoring ===")
    print(ppe.sort_values("spread_premium", ascending=False)[cols_show].head(25).round(3).to_string(index=False))

    print("\n=== BOTTOM 15 by spread_premium — CONCENTRATE MORE than team scoring ===")
    print(ppe.sort_values("spread_premium", ascending=True)[cols_show].head(15).round(3).to_string(index=False))

    print("\n=== TOP 25 by KL_to_baseline (any deviation from team scoring distribution) ===")
    print(ppe.sort_values("kl_to_baseline", ascending=False)[cols_show].head(25).round(3).to_string(index=False))

    # The face-validity bet: high spread_premium should show genuine "spread the wealth" PGs.
    # The bottom should show stars whose role is to feed The Guy.


if __name__ == "__main__":
    main()
