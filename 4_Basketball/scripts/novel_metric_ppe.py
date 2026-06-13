"""PPE — Pass-Pattern Entropy (novel offensive metric, T1).

Per assister, compute Shannon entropy of the assist-target distribution. High
entropy = passes go to many different teammates (creative, hard to scout).
Low entropy = predictable target distribution.

PBP parsing: made-shot descriptions encode assister as "(LastName N AST)".
We resolve LastName → person_id by matching against same-team players in
that game.

Outputs:
  D:/NBA Projections/data/results/ppe_2024_25.parquet
  Columns: assister_id, assister_name, n_assists, n_targets, entropy_nats,
           entropy_normalized, max_share, top_target_name, top_target_share

Face-validity check: Jokic / Haliburton / LeBron / CP3 should top normalized
PPE. One-track finishers (PnR-roll-and-go-to-Westbrook era distributors with
narrow distribution) should bottom out.
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
OUT.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT / "ppe_2024_25.parquet"

ASSIST_RX = re.compile(r"\(([A-Za-zÀ-ÿ\-\'\.À-ſ ]+?)\s+\d+\s+AST\)")


def main():
    print("=== loading PBP ===")
    df = pd.read_parquet(PBP)
    print(f"  rows: {len(df):,}")

    # Made shot rows
    made = df[df["action_type"] == "Made Shot"].copy()
    made = made.dropna(subset=["description", "person_id", "team_id"])
    print(f"  made shots: {len(made):,}")

    # Parse assister last name from description
    made["assister_last"] = made["description"].str.extract(ASSIST_RX, expand=False)
    assists = made.dropna(subset=["assister_last"]).copy()
    assists["assister_last"] = assists["assister_last"].str.strip()
    print(f"  shots with assist: {len(assists):,}")

    # Build per-game (team_id, last_name) -> person_id lookup using all PBP players
    # We use player_name (already last-name-ish in this dataset). Let's verify.
    sample_players = df.dropna(subset=["player_name", "person_id", "team_id"])
    print(f"  unique players in PBP: {sample_players['person_id'].nunique():,}")
    print(f"  player_name samples: {sample_players['player_name'].dropna().head(10).tolist()}")
    # player_name appears to be SURNAME only ("Bamba", "Wagner", "Allen", "Giddey", ...)
    # So matching assister_last to player_name on same team is straightforward.

    # Build (game_id, team_id, player_name) -> person_id map
    roster = (sample_players.groupby(["game_id", "team_id", "player_name"])["person_id"]
                              .first().reset_index())
    print(f"  game-team-player rows: {len(roster):,}")

    # Some surnames have spaces/initials. Try exact match first, then disambiguation.
    # Join: assists row to roster on (game_id, team_id, assister_last == player_name)
    assists["g_t_a"] = list(zip(assists["game_id"], assists["team_id"], assists["assister_last"]))
    roster_map = {(g, t, p): pid for g, t, p, pid in zip(roster["game_id"], roster["team_id"],
                                                           roster["player_name"], roster["person_id"])}
    assists["assister_id"] = assists["g_t_a"].map(roster_map)
    matched = assists["assister_id"].notna().sum()
    print(f"  assister-resolution rate: {matched:,}/{len(assists):,} ({matched/len(assists)*100:.1f}%)")

    # Fall-back: for unmatched, try matching by last-token of player_name (handles "Ja. Green" -> "Green")
    unm = assists[assists["assister_id"].isna()].copy()
    if len(unm) > 0:
        # Build alt map keyed by last-word of player_name
        roster2 = roster.copy()
        roster2["last_token"] = roster2["player_name"].str.split().str[-1]
        roster2_map = {(g, t, lt): pid for g, t, lt, pid in zip(roster2["game_id"], roster2["team_id"],
                                                                 roster2["last_token"], roster2["person_id"])}
        unm["g_t_a_last"] = list(zip(unm["game_id"], unm["team_id"], unm["assister_last"]))
        unm["alt_id"] = unm["g_t_a_last"].map(roster2_map)
        assists.loc[unm.index, "assister_id"] = unm["alt_id"]
    matched = assists["assister_id"].notna().sum()
    print(f"  assister-resolution after fallback: {matched:,}/{len(assists):,} ({matched/len(assists)*100:.1f}%)")

    # Drop unresolved
    assists = assists.dropna(subset=["assister_id"]).copy()
    assists["assister_id"] = assists["assister_id"].astype(int)
    assists["scorer_id"] = assists["person_id"].astype(int)

    # Resolve assister name (canonical)
    pid_to_name = roster.drop_duplicates(subset=["person_id"]).set_index("person_id")["player_name"].to_dict()
    assists["assister_name"] = assists["assister_id"].map(pid_to_name)
    assists["scorer_name"] = assists["scorer_id"].map(pid_to_name)

    # === Compute PPE per assister ===
    print("\n=== computing PPE ===")
    rows = []
    for aid, sub in assists.groupby("assister_id"):
        n = len(sub)
        if n < 30: continue   # min sample for stable entropy
        target_counts = sub["scorer_id"].value_counts()
        p = target_counts.values / target_counts.sum()
        H = -np.sum(p * np.log(p + 1e-12))   # entropy in nats
        H_max = np.log(len(p))               # max possible (uniform across targets)
        H_norm = H / H_max if H_max > 0 else 0.0
        top_target_id = int(target_counts.index[0])
        top_target_share = float(target_counts.iloc[0] / n)
        top_target_name = pid_to_name.get(top_target_id, str(top_target_id))
        rows.append({
            "assister_id":   int(aid),
            "assister_name": pid_to_name.get(int(aid), str(aid)),
            "n_assists":     int(n),
            "n_targets":     int(len(p)),
            "entropy_nats":  float(H),
            "entropy_norm":  float(H_norm),
            "max_share":     float(target_counts.iloc[0] / n),
            "top_target":    top_target_name,
            "top_target_share": top_target_share,
        })
    ppe = pd.DataFrame(rows).sort_values("entropy_norm", ascending=False)
    print(f"  qualifying passers (>=30 assists): {len(ppe)}")

    ppe.to_parquet(OUT_PATH, index=False)
    ppe.to_csv(OUT_PATH.with_suffix(".csv"), index=False)
    print(f"\nwrote: {OUT_PATH}")

    # === face-validity report ===
    print("\n=== TOP 25 by normalized PPE (creative distributors) ===")
    cols = ["assister_name","n_assists","n_targets","entropy_norm","top_target","top_target_share"]
    print(ppe[cols].head(25).round(3).to_string(index=False))

    print("\n=== BOTTOM 15 by normalized PPE (predictable distributors) ===")
    print(ppe[cols].tail(15).round(3).to_string(index=False))

    # Volume context
    print("\n=== TOP 25 by raw entropy (volume + creativity) ===")
    ppe_by_raw = ppe.sort_values("entropy_nats", ascending=False)
    print(ppe_by_raw[["assister_name","n_assists","n_targets","entropy_nats","entropy_norm"]].head(25).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
