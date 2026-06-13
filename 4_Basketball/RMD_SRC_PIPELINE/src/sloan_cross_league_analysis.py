"""Sloan adjudicated Test 1 cross-league analysis.

For each league (WNBA / NCAA_M / NCAA_W), computes per (season, observable,
arm) variance ratios under metadata + adjudicated bucketing, applies the
locked decision rules from the pre-reg, and writes results docs.

Per pre-reg SHA 28e3dc7 (three pre-regs filed 2026-06-01).

Usage: python sloan_cross_league_analysis.py {WNBA|NCAA_M|NCAA_W}
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

NBA_RMD = Path("D:/NBA Projections/RMD_SRC_PIPELINE")

LEAGUES = {
    "WNBA": {
        "root": Path("C:/WNBA Projections"),
        "seasons": [2023, 2024, 2025],
        "adj_path": Path("C:/WNBA Projections/audit_runs/test_1_replication/sloan_adjudicated/wnba_position_adjudication_v10.json"),
        "out_dir": Path("C:/WNBA Projections/audit_runs/test_1_replication/sloan_adjudicated"),
        "power_gate": 1.20,
        "stan_path": Path("C:/WNBA Projections/audit_runs/stan_robustness/wnba_stan_per_player_projections.csv"),
        "metadata_center_strings": ["Center", "Center-Forward", "Forward-Center"],
    },
    "NCAA_M": {
        "root": Path("C:/NCAA D1 Mens"),
        "seasons": [2024, 2025],
        "adj_path": Path("C:/NCAA D1 Mens/audit_runs/test_1_replication/sloan_adjudicated/ncaa_m_position_adjudication_v10.json"),
        "out_dir": Path("C:/NCAA D1 Mens/audit_runs/test_1_replication/sloan_adjudicated"),
        "power_gate": 1.10,
        "stan_path": Path("C:/NCAA D1 Mens/audit_runs/stan_robustness/ncaa_mens_stan_per_player_projections.csv"),
        "metadata_center_strings": None,  # uses logic below for NCAA
    },
    "NCAA_W": {
        "root": Path("C:/NCAA D1 Womens"),
        "seasons": [2024, 2025],
        "adj_path": Path("C:/NCAA D1 Womens/audit_runs/test_1_replication/sloan_adjudicated/ncaa_w_position_adjudication_v10.json"),
        "out_dir": Path("C:/NCAA D1 Womens/audit_runs/test_1_replication/sloan_adjudicated"),
        "power_gate": 1.10,
        "stan_path": Path("C:/NCAA D1 Womens/audit_runs/stan_robustness/ncaa_womens_stan_per_player_projections.csv"),
        "metadata_center_strings": None,
    },
}

OBSERVABLES = ["BLK", "PTS", "REB"]
MIN_GP_PER_SEASON = 10
BOOTSTRAP_B = 1000
BOOTSTRAP_SEED = 20260601

REF_BANDS = {
    "BLK": (1.26, 2.03),
    "PTS": (0.76, 1.02),
}


def metadata_bucket_wnba(pos: str) -> str:
    if isinstance(pos, str) and pos in ("Center", "Center-Forward", "Forward-Center"):
        return "Center"
    return "non-Center"


def metadata_bucket_ncaa(pos: str) -> str:
    if pos == "C":
        return "Center"
    if isinstance(pos, str) and "-" in pos and pos.split("-")[0] == "C":
        return "Center"
    return "non-Center"


def load_adjudication(adj_path: Path) -> dict:
    """Return dict slug -> {metadata_bucket, adjudicated_bucket}."""
    with open(adj_path, encoding="utf-8") as f:
        adj = json.load(f)
    out = {}
    for v in adj["verdicts"]:
        slug = str(v["player_slug"])
        out[slug] = {
            "metadata_bucket": v["metadata_bucket_inclusive"],
            "adjudicated_bucket": v["adjudicated_bucket"],
        }
    return out


def compute_player_residual_surgical(player_games: pd.DataFrame, stat_col: str) -> np.ndarray:
    """Career-mean residual: actual - career_mean (within the season subset)."""
    vals = player_games[stat_col].values.astype(float)
    if len(vals) < 1:
        return np.array([])
    career_mean = vals.mean()
    return vals - career_mean


def variance_ratio_with_ci(center_residuals: np.ndarray,
                            non_center_residuals: np.ndarray,
                            center_player_ids: np.ndarray,
                            non_center_player_ids: np.ndarray,
                            seed: int = BOOTSTRAP_SEED,
                            B: int = BOOTSTRAP_B) -> dict:
    """Variance ratio sigma_Center / sigma_non-Center with cluster bootstrap CI."""
    # Drop NaN values from residual arrays (game logs can have NaN for DNP rows)
    c_mask = ~np.isnan(center_residuals)
    nc_mask = ~np.isnan(non_center_residuals)
    center_residuals = center_residuals[c_mask]
    non_center_residuals = non_center_residuals[nc_mask]
    center_player_ids = center_player_ids[c_mask]
    non_center_player_ids = non_center_player_ids[nc_mask]

    sig_c = np.std(center_residuals, ddof=1) if len(center_residuals) > 1 else float("nan")
    sig_nc = np.std(non_center_residuals, ddof=1) if len(non_center_residuals) > 1 else float("nan")
    ratio = sig_c / sig_nc if sig_nc > 0 else float("nan")

    # Cluster bootstrap on player IDs
    rng = np.random.default_rng(seed)
    unique_c = np.unique(center_player_ids)
    unique_nc = np.unique(non_center_player_ids)

    # Pre-build per-player residual lookups
    c_lookup = {pid: center_residuals[center_player_ids == pid] for pid in unique_c}
    nc_lookup = {pid: non_center_residuals[non_center_player_ids == pid] for pid in unique_nc}

    boot_ratios = np.zeros(B)
    if len(unique_c) == 0 or len(unique_nc) == 0:
        boot_ratios[:] = float("nan")
    else:
        for b in range(B):
            sampled_c = rng.choice(unique_c, size=len(unique_c), replace=True)
            sampled_nc = rng.choice(unique_nc, size=len(unique_nc), replace=True)
            boot_c_arrs = [c_lookup[p] for p in sampled_c]
            boot_nc_arrs = [nc_lookup[p] for p in sampled_nc]
            boot_c = np.concatenate(boot_c_arrs) if boot_c_arrs else np.array([])
            boot_nc = np.concatenate(boot_nc_arrs) if boot_nc_arrs else np.array([])
            if len(boot_c) > 1 and len(boot_nc) > 1:
                sc = np.std(boot_c, ddof=1)
                snc = np.std(boot_nc, ddof=1)
                boot_ratios[b] = sc / snc if snc > 0 else float("nan")
            else:
                boot_ratios[b] = float("nan")
    ci_lo = float(np.nanpercentile(boot_ratios, 2.5))
    ci_hi = float(np.nanpercentile(boot_ratios, 97.5))

    # Levene's median-centered test
    if len(center_residuals) > 1 and len(non_center_residuals) > 1:
        try:
            lev_stat, p_lev = stats.levene(center_residuals, non_center_residuals, center="median")
        except Exception:
            lev_stat, p_lev = float("nan"), float("nan")
        try:
            bart_stat, p_bart = stats.bartlett(center_residuals, non_center_residuals)
        except Exception:
            bart_stat, p_bart = float("nan"), float("nan")
        # Two-sided F test
        if sig_nc > 0:
            f_stat = (sig_c ** 2) / (sig_nc ** 2)
            df_c = len(center_residuals) - 1
            df_nc = len(non_center_residuals) - 1
            p_f_right = 1 - stats.f.cdf(f_stat, df_c, df_nc)
            p_f = 2 * min(p_f_right, 1 - p_f_right)
        else:
            p_f = float("nan")
    else:
        p_lev = p_bart = p_f = float("nan")

    return {
        "sd_in": float(sig_c),
        "sd_out": float(sig_nc),
        "ratio": float(ratio),
        "ci95_lo": ci_lo,
        "ci95_hi": ci_hi,
        "p_levene": float(p_lev),
        "p_bartlett": float(p_bart),
        "p_F": float(p_f),
        "n_in": int(len(unique_c)),
        "n_out": int(len(unique_nc)),
    }


def disposition_blk(ratio: float, ci_lo: float, ci_hi: float, p_lev: float) -> str:
    lo, hi = REF_BANDS["BLK"]
    if np.isnan(ratio) or np.isnan(p_lev):
        return "INCONCLUSIVE_NAN"
    # CI overlap with [1.26, 2.03]
    overlaps_band = (ci_hi >= lo) and (ci_lo <= hi)
    if overlaps_band and p_lev < 0.05:
        return "PERSISTS"
    if overlaps_band and p_lev >= 0.05:
        return "PERSISTS-DIRECTIONAL"
    if ci_hi < lo and ci_lo > 1.0 and p_lev < 0.05:
        return "ATTENUATES"
    if ci_lo < 1.0 < ci_hi:
        return "REGIME-NULL"
    if ci_hi < 1.0:
        return "INVERTED"
    return "UNCLASSIFIED"


def disposition_pts(ratio: float, ci_lo: float, ci_hi: float, p_lev: float) -> str:
    lo, hi = REF_BANDS["PTS"]
    if np.isnan(ratio):
        return "INCONCLUSIVE_NAN"
    overlaps_band = (ci_hi >= lo) and (ci_lo <= hi)
    if overlaps_band and ratio < 1.0:
        return "DIRECTIONAL-PERSISTS"
    if ci_lo < 1.0 < ci_hi:
        return "NULL"
    if ci_lo > 1.0:
        return "INVERTED"
    return "UNCLASSIFIED"


def disposition_reb_walkback(ratio: float, ci_lo: float, ci_hi: float, p_lev: float) -> str:
    if np.isnan(ratio) or np.isnan(p_lev):
        return "INCONCLUSIVE_NAN"
    if ci_lo < 1.0 < ci_hi and p_lev > 0.05:
        return "WALK-BACK UPHELD"
    if ci_lo > 1.0 and p_lev < 0.05:
        return "WALK-BACK FALSIFIED"
    if ci_hi < 1.0:
        return "WALK-BACK FALSIFIED-INVERTED"
    return "UNCLASSIFIED"


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in LEAGUES:
        print("Usage: python sloan_cross_league_analysis.py {WNBA|NCAA_M|NCAA_W}")
        sys.exit(1)

    league = sys.argv[1]
    cfg = LEAGUES[league]
    cfg["out_dir"].mkdir(parents=True, exist_ok=True)

    # Load adjudication
    adj = load_adjudication(cfg["adj_path"])
    print(f"Loaded {len(adj)} adjudication verdicts for {league}")

    # Load metadata
    meta = pd.read_csv(cfg["root"] / "data/processed/player_metadata.csv")
    meta["position"] = meta["position"].fillna("Unknown")

    # Load game logs
    games = pd.read_csv(cfg["root"] / "data/processed/player_game_logs.csv")
    games["player_slug"] = games["player_slug"].astype(str)

    # Identify columns
    season_col = next((c for c in ["season", "year"] if c in games.columns), None)
    stat_col_map = {}
    for std, candidates in {
        "PTS": ["pts", "PTS"],
        "REB": ["trb", "TRB", "reb"],
        "AST": ["ast", "AST"],
        "BLK": ["blk", "BLK"],
    }.items():
        for c in candidates:
            if c in games.columns:
                stat_col_map[std] = c
                break
    if "REB" not in stat_col_map and "orb" in games.columns and "drb" in games.columns:
        games["_reb"] = games["orb"].fillna(0) + games["drb"].fillna(0)
        stat_col_map["REB"] = "_reb"

    # Filter to seasons
    games = games[games[season_col].isin(cfg["seasons"])].copy()
    print(f"Game logs in window: {len(games)} rows; stat cols: {stat_col_map}")

    # Build the metadata + adjudicated bucket map for ALL players (not just adjudicated ones)
    # NCAA metadata `player_slug` is a different ID scheme than game-logs `player_slug`,
    # so we additionally key by normalized full_name to bridge across systems.
    bucket_meta_fn = metadata_bucket_wnba if league == "WNBA" else metadata_bucket_ncaa
    player_buckets_by_slug = {}
    player_buckets_by_name = {}

    def norm_name(n):
        return str(n).strip().lower() if n is not None else ""

    for _, row in meta.iterrows():
        slug = str(row["player_slug"])
        name_key = norm_name(row.get("full_name"))
        meta_bucket = bucket_meta_fn(row["position"])
        if slug in adj:
            adj_bucket = adj[slug]["adjudicated_bucket"]
        else:
            adj_bucket = meta_bucket  # non-adjudicated players keep their metadata bucket
        rec = {
            "metadata_bucket": meta_bucket,
            "adjudicated_bucket": adj_bucket,
        }
        player_buckets_by_slug[slug] = rec
        if name_key:
            player_buckets_by_name[name_key] = rec

    # Add normalized name column to games for join fallback
    if "player" in games.columns:
        games["_name_key"] = games["player"].apply(norm_name)
    else:
        games["_name_key"] = ""

    def lookup_bucket(slug, name_key):
        rec = player_buckets_by_slug.get(slug)
        if rec is not None:
            return rec
        rec = player_buckets_by_name.get(name_key)
        if rec is not None:
            return rec
        return {"metadata_bucket": "non-Center", "adjudicated_bucket": "non-Center"}

    # Per-cell analysis
    cell_results = []
    n_in_lift_rows = []
    for season in cfg["seasons"]:
        season_games = games[games[season_col] == season].copy()
        # Per-player GP
        gp_by_slug = season_games.groupby("player_slug").size()
        qualifying_slugs = set(gp_by_slug[gp_by_slug >= MIN_GP_PER_SEASON].index)
        season_games = season_games[season_games["player_slug"].isin(qualifying_slugs)]
        print(f"\n{league} season {season}: {len(qualifying_slugs)} qualifying players, {len(season_games)} games")

        # Compute residuals per player (surgical: actual - player's season career mean)
        residuals_by_obs = {obs: [] for obs in OBSERVABLES}
        player_ids_by_obs = {obs: [] for obs in OBSERVABLES}
        bucket_meta_by_obs = {obs: [] for obs in OBSERVABLES}
        bucket_adj_by_obs = {obs: [] for obs in OBSERVABLES}

        for slug, pg in season_games.groupby("player_slug"):
            slug_str = str(slug)
            name_key = pg["_name_key"].iloc[0] if "_name_key" in pg.columns else ""
            bucket = lookup_bucket(slug_str, name_key)
            for obs in OBSERVABLES:
                stat_col = stat_col_map[obs]
                resid = compute_player_residual_surgical(pg, stat_col)
                residuals_by_obs[obs].extend(resid.tolist())
                player_ids_by_obs[obs].extend([slug] * len(resid))
                bucket_meta_by_obs[obs].extend([bucket["metadata_bucket"]] * len(resid))
                bucket_adj_by_obs[obs].extend([bucket["adjudicated_bucket"]] * len(resid))

        for obs in OBSERVABLES:
            residuals = np.array(residuals_by_obs[obs])
            player_ids = np.array(player_ids_by_obs[obs])
            bucket_meta_arr = np.array(bucket_meta_by_obs[obs])
            bucket_adj_arr = np.array(bucket_adj_by_obs[obs])

            for arm_name, bucket_arr in [("metadata", bucket_meta_arr), ("adjudicated", bucket_adj_arr)]:
                is_center = bucket_arr == "Center"
                center_resid = residuals[is_center]
                non_center_resid = residuals[~is_center]
                center_pids = player_ids[is_center]
                non_center_pids = player_ids[~is_center]
                res = variance_ratio_with_ci(
                    center_resid, non_center_resid, center_pids, non_center_pids
                )
                res["season"] = season
                res["observable"] = obs
                res["arm"] = arm_name
                res["method"] = "surgical"
                # Disposition (only on adjudicated; metadata is control)
                if arm_name == "adjudicated":
                    if obs == "BLK":
                        disp = disposition_blk(res["ratio"], res["ci95_lo"], res["ci95_hi"], res["p_levene"])
                    elif obs == "PTS":
                        disp = disposition_pts(res["ratio"], res["ci95_lo"], res["ci95_hi"], res["p_levene"])
                    else:  # REB walk-back
                        disp = disposition_reb_walkback(res["ratio"], res["ci95_lo"], res["ci95_hi"], res["p_levene"])
                    res["disposition"] = disp
                else:
                    res["disposition"] = "(control)"
                cell_results.append(res)
                print(f"  {arm_name} {obs} {season}: n_in={res['n_in']}, n_out={res['n_out']}, "
                      f"ratio={res['ratio']:.3f}, CI95=[{res['ci95_lo']:.3f}, {res['ci95_hi']:.3f}], "
                      f"p_lev={res['p_levene']:.4f}, disp={res['disposition']}")

            # n_in lift per observable per season
            n_in_meta = (bucket_meta_arr == "Center").sum()  # rows
            n_in_adj = (bucket_adj_arr == "Center").sum()
            # Counted at player level for the lift
            meta_centers = set(player_ids[bucket_meta_arr == "Center"])
            adj_centers = set(player_ids[bucket_adj_arr == "Center"])
            lift_player = len(adj_centers) / max(1, len(meta_centers))
            n_in_lift_rows.append({
                "season": season,
                "observable": obs,
                "n_in_meta_players": len(meta_centers),
                "n_in_adj_players": len(adj_centers),
                "lift_player": lift_player,
                "power_gate_pass": lift_player >= cfg["power_gate"],
            })

    cell_df = pd.DataFrame(cell_results)
    lift_df = pd.DataFrame(n_in_lift_rows)
    out_dir = cfg["out_dir"]
    cell_df.to_csv(out_dir / "variance_ratios_all_cells.csv", index=False)
    lift_df.to_csv(out_dir / "n_in_lift_table.csv", index=False)
    print(f"\nWrote {out_dir / 'variance_ratios_all_cells.csv'}")
    print(f"Wrote {out_dir / 'n_in_lift_table.csv'}")

    # Aggregate dispositions
    adj_only = cell_df[cell_df["arm"] == "adjudicated"]
    summary = adj_only.groupby("observable")["disposition"].value_counts().to_dict()
    print(f"\nAggregate dispositions (adjudicated arm, surgical method):")
    for (obs, disp), n in summary.items():
        print(f"  {obs}: {disp} x {n}")

    # Write minimal results markdown
    md_path = out_dir / f"SLOAN_ADJUDICATED_{league}_RESULTS.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Sloan Adjudicated Test 1 — {league} Results (surgical arm)\n\n")
        f.write(f"Pre-reg SHA: 28e3dc7\n")
        f.write(f"Adjudication artifact: {cfg['adj_path'].name}\n\n")
        f.write(f"## Per-cell variance ratios\n\n")
        f.write(cell_df.round(4).to_markdown(index=False))
        f.write(f"\n\n## n_in lift table\n\n")
        f.write(lift_df.round(4).to_markdown(index=False))
        f.write(f"\n\n## Aggregate dispositions (adjudicated, surgical)\n\n")
        for obs in OBSERVABLES:
            disps = adj_only[adj_only["observable"] == obs]["disposition"].tolist()
            f.write(f"- **{obs}**: {disps}\n")
        f.write(f"\n*Stan arm analysis pending Stan posterior file integration.*\n")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
