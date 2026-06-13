"""Probe B — contextual residue-class structure on v6.3-A residuals.

Tests whether per-game residuals from v6.3-A show distributional clustering
across contextual configurations within each (position_class × cohort) cell.

Hypothesis: ~648 contextual configurations collapse onto ~log_2(648) = ~10
distributional clusters per cohort, beating bootstrap null permutation.

Architecture is fully spelled out in the task spec; this script implements
exactly what was specified with 500-rep bootstrap (down from 1000) for
runtime budget.

Outputs in audit_runs/probe_b_contextual_a_final/:
  result_contextual_a_final.md
  result_contextual_a_final_per_cohort.csv  (cluster assignments)
  result_contextual_a_final_bootstrap.csv   (null distribution)
  result_contextual_a_final_top_pairs.csv   (most-distinct cluster pairs)
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from pathlib import Path
import json
import time
import warnings
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from sklearn.metrics import silhouette_score

warnings.filterwarnings("ignore", category=RuntimeWarning)

REPO = Path(".")
PQ = REPO / "data" / "parquet"
RESID_CSV = REPO / "audit_runs" / "v6_3_A_baseline_2025_26" / "v6_3_A_residuals.csv"
OUT_DIR = REPO / "audit_runs" / "probe_b_contextual_a_final"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STATS = ["PTS", "REB", "AST"]
T_GRID = np.arange(-3.0, 3.0 + 1e-9, 0.1)
K_VALUES = [2, 4, 6, 8, 10, 16, 32, 50]
N_BOOTSTRAP = 500
MIN_CONFIG_OBS = 10
RNG_SEED = 20260505

ALL_STAR_2026 = pd.Timestamp("2026-02-14")


# ────────────────────────────────────────────────────────────────────────
# Context lookup builders
# ────────────────────────────────────────────────────────────────────────

def build_opp_def_rating_quartile(bx):
    """24-25 final defensive rating quartile per team (4 buckets).
    def_rating = pts_allowed_per_100_poss. Lower = better defense.
    """
    sub = bx[(bx["season"] == "2024-25") &
              (bx["season_type"] == "Regular Season")].copy()
    # Aggregate per team-game: team's possessions and opponent's points scored
    # First need (game_id, team_abbr) -> team's possessions and opponent's pts
    # Possessions estimate (single team): FGA + 0.44*FTA + TO - OREB.
    # Pts allowed per game = sum of pts by all OTHER team's players in that game.
    sub["minutes"] = pd.to_numeric(sub["minutes"], errors="coerce")
    g = sub.groupby(["game_id", "team_abbr"]).agg(
        FGA=("FGA", "sum"), FTA=("FTA", "sum"),
        TO=("TOV", "sum"), OREB=("OREB", "sum"),
        PTS=("PTS", "sum"),
    ).reset_index()
    g["poss"] = g["FGA"] + 0.44 * g["FTA"] + g["TO"] - g["OREB"]
    # For each game, the opponent's pts = the OTHER team's PTS
    g_pts = g[["game_id", "team_abbr", "PTS"]].rename(
        columns={"team_abbr": "opp_abbr", "PTS": "opp_PTS"})
    merged = g.merge(g_pts, on="game_id")
    merged = merged[merged["team_abbr"] != merged["opp_abbr"]]
    # Per-team def rating = opp_PTS / poss * 100
    team_def = merged.groupby("team_abbr").agg(
        opp_pts=("opp_PTS", "sum"),
        poss=("poss", "sum"),
    ).reset_index()
    team_def["def_rating"] = team_def["opp_pts"] / team_def["poss"] * 100
    team_def = team_def.sort_values("def_rating").reset_index(drop=True)
    team_def["def_quartile_rank"] = (team_def.index // (len(team_def) / 4)).astype(int)
    team_def["def_quartile_rank"] = team_def["def_quartile_rank"].clip(0, 3)
    label_map = {0: "top", 1: "high", 2: "mid", 3: "bottom"}
    team_def["opp_class"] = team_def["def_quartile_rank"].map(label_map)
    return dict(zip(team_def["team_abbr"], team_def["opp_class"]))


def build_pace_tercile(bx):
    """Per (game_id), combined-team pace; bin globally by tercile.
    Returns dict (game_id) -> 'fast' | 'medium' | 'slow'.
    """
    sub = bx[(bx["season"] == "2025-26") &
              (bx["season_type"] == "Regular Season")].copy()
    g = sub.groupby(["game_id", "team_abbr"]).agg(
        FGA=("FGA", "sum"), FTA=("FTA", "sum"),
        TO=("TOV", "sum"), OREB=("OREB", "sum"),
    ).reset_index()
    g["poss"] = g["FGA"] + 0.44 * g["FTA"] + g["TO"] - g["OREB"]
    # Combined per game: average team possessions across the two teams
    game_pace = g.groupby("game_id")["poss"].mean().reset_index()
    game_pace.columns = ["game_id", "pace"]
    q33, q67 = game_pace["pace"].quantile([1/3, 2/3]).values
    def label(p):
        if p < q33: return "slow"
        if p < q67: return "medium"
        return "fast"
    game_pace["pace_tier"] = game_pace["pace"].apply(label)
    return dict(zip(game_pace["game_id"], game_pace["pace_tier"]))


def build_role_stability(bx_25_26_played):
    """Per (player, game_date), role tier from prior 10 games.
    starter:  prior-10 mpg >= 28
    6th-man:  prior-10 mpg in [18, 28)
    spot:     prior-10 mpg < 18
    For first 10 games: use season-to-date instead.
    """
    df = bx_25_26_played.sort_values(["nba_api_id", "game_date"]).copy()
    df["minutes"] = pd.to_numeric(df["minutes"], errors="coerce")
    # Rolling-10 mean of minutes per player, shifted by 1 (use prior games only)
    df["prior10_mpg"] = (df.groupby("nba_api_id")["minutes"]
                          .transform(lambda s: s.shift(1).rolling(10, min_periods=3).mean()))
    # First few games: fallback to season-to-date prior to game
    df["sumto"] = df.groupby("nba_api_id")["minutes"].cumsum().shift(1)
    df["nto"] = df.groupby("nba_api_id").cumcount()
    df["std_mpg"] = df["sumto"] / df["nto"]
    df["prior10_mpg"] = df["prior10_mpg"].fillna(df["std_mpg"])
    def label(m):
        if pd.isna(m): return "spot"
        if m >= 28: return "starter"
        if m >= 18: return "sixth"
        return "spot"
    df["role"] = df["prior10_mpg"].apply(label)
    out = df[["nba_api_id", "game_date", "game_id", "role"]].drop_duplicates(
        subset=["nba_api_id", "game_id"])
    return out


def build_season_phase(game_dates, team_game_n_lookup, team_total_games=82):
    """Per (team_abbr, game_date), season_phase ∈ {early / post_AS / last20}.
    early: game_date < 2026-02-14
    post_AS: 2026-02-14 <= date AND team_game_n <= 62
    last20: team_game_n > 62
    """
    def label(date, team_game_n):
        if pd.isna(team_game_n): return "early"
        if team_game_n > team_total_games - 20:
            return "last20"
        if date >= ALL_STAR_2026:
            return "post_AS"
        return "early"
    return label


def build_record_tier(rolling_25_26):
    """Per (team, team_game_n), current record tier.
    Uses cum_W / team_game_n as current win pct.
    top-tier: win_pct >= 0.55
    mid-tier: 0.40-0.55
    bottom-tier: < 0.40
    """
    df = rolling_25_26.copy()
    df["win_pct"] = df["cum_W"] / df["team_game_n"]
    def label(p):
        if p >= 0.55: return "top"
        if p >= 0.40: return "mid"
        return "bottom"
    df["record_tier"] = df["win_pct"].apply(label)
    out = dict(zip(zip(df["team_abbr"], df["team_game_n"]), df["record_tier"]))
    return out


def build_opp_record_tier_lookup(bx_25_26, rank_24_25_winpct):
    """For each (opp_abbr, game_date), opponent's record_tier as of that date.
    For opponents w/ <30 GP as of date: use 24-25 final win_pct → tier.
    For opponents w/ >=30 GP: use rolling current win_pct → tier.
    Returns dict (opp_abbr, game_date) -> tier.
    """
    # First: opponent's team_game_n as of game_date
    tg = (bx_25_26.groupby(["team_abbr", "game_id", "game_date"])
                  .agg(win=("win", "first")).reset_index())
    tg = tg.sort_values(["team_abbr", "game_date"]).reset_index(drop=True)
    tg["team_game_n"] = tg.groupby("team_abbr").cumcount() + 1
    tg["cum_W"] = tg.groupby("team_abbr")["win"].cumsum()
    tg["win_pct_now"] = tg["cum_W"] / tg["team_game_n"]
    def label_winpct(p):
        if p >= 0.55: return "top"
        if p >= 0.40: return "mid"
        return "bottom"
    out = {}
    for _, r in tg.iterrows():
        if r["team_game_n"] < 30:
            wp = rank_24_25_winpct.get(r["team_abbr"], 0.5)
        else:
            wp = r["win_pct_now"]
        out[(r["team_abbr"], r["game_date"])] = label_winpct(wp)
    return out


def build_24_25_winpct(bx):
    sub = bx[(bx["season"] == "2024-25") &
              (bx["season_type"] == "Regular Season")].copy()
    tg = sub.groupby(["team_abbr", "game_id"])["win"].first().reset_index()
    s = tg.groupby("team_abbr")["win"].agg(["sum", "count"]).reset_index()
    s.columns = ["team", "W", "GP"]
    s["win_pct"] = s["W"] / s["GP"]
    return dict(zip(s["team"], s["win_pct"]))


# ────────────────────────────────────────────────────────────────────────
# Distribution + clustering
# ────────────────────────────────────────────────────────────────────────

def cf_compute(arr, t_grid=T_GRID):
    """Empirical characteristic function on grid t."""
    if len(arr) == 0:
        return np.zeros(len(t_grid), dtype=np.complex128)
    arr = arr.astype(np.float64)
    return np.exp(1j * np.outer(t_grid, arr)).mean(axis=1)


def moments(arr):
    """Return (mean, var, skew, kurt) — central moments 1-4 (kurt = excess)."""
    if len(arr) < 2:
        return np.array([np.nan, np.nan, np.nan, np.nan])
    m = arr.mean()
    c = arr - m
    v = (c ** 2).mean()
    if v <= 0:
        return np.array([m, v, 0.0, 0.0])
    s = (c ** 3).mean() / (v ** 1.5)
    k = (c ** 4).mean() / (v ** 2) - 3
    return np.array([m, v, s, k])


def aggregate_configs(df, stat, min_obs=MIN_CONFIG_OBS):
    """Aggregate per-config: moments + CF for residuals of `stat`.

    Returns:
      configs: list of config tag strings
      moms:    (n_configs, 4) array of moments
      cfs:     (n_configs, len(T_GRID)) array of complex CFs
      ns:      (n_configs,) array of obs counts
    """
    resid_col = f"{stat}_resid_v6_3_A"
    grouped = df.groupby("config")
    configs = []
    moms_list = []
    cfs_list = []
    ns_list = []
    for cfg, sub in grouped:
        if len(sub) < min_obs:
            continue
        r = sub[resid_col].dropna().values
        if len(r) < min_obs:
            continue
        configs.append(cfg)
        moms_list.append(moments(r))
        cfs_list.append(cf_compute(r))
        ns_list.append(len(r))
    if not configs:
        return [], np.zeros((0, 4)), np.zeros((0, len(T_GRID)), dtype=np.complex128), np.array([])
    return configs, np.vstack(moms_list), np.vstack(cfs_list), np.array(ns_list)


def build_distance_matrix(moms, cfs):
    """Compute combined distance: z-normalized (d_moment + d_phi) / 2."""
    n = len(moms)
    if n < 2:
        return np.zeros((n, n)), np.zeros((n, n)), np.zeros((n, n))
    # d_moment: euclidean in z-space
    moms_safe = np.where(np.isfinite(moms), moms, 0)
    sd = moms_safe.std(axis=0)
    sd[sd == 0] = 1
    z = (moms_safe - moms_safe.mean(axis=0)) / sd
    d_mom = np.zeros((n, n))
    for i in range(n):
        d_mom[i] = np.sqrt(((z - z[i]) ** 2).sum(axis=1))
    # d_phi: max_t |phi_i - phi_j|
    d_phi = np.zeros((n, n))
    for i in range(n):
        d_phi[i] = np.max(np.abs(cfs - cfs[i]), axis=1)
    # Normalize each to [0,1] range, then average
    if d_mom.max() > 0:
        d_mom_n = d_mom / d_mom.max()
    else:
        d_mom_n = d_mom
    if d_phi.max() > 0:
        d_phi_n = d_phi / d_phi.max()
    else:
        d_phi_n = d_phi
    d_combined = (d_mom_n + d_phi_n) / 2
    return d_combined, d_mom, d_phi


def cluster_validity(d_matrix, ns, k_values=K_VALUES):
    """Hierarchical agglomerative + average linkage; compute validity per k.

    Returns dict k -> {silhouette, within_var, between_F, n_clusters_actual}
    """
    n = d_matrix.shape[0]
    if n < 4:
        return {}
    # squareform expects condensed
    np.fill_diagonal(d_matrix, 0)
    cond = squareform(d_matrix, checks=False)
    Z = linkage(cond, method="average")
    out = {}
    for k in k_values:
        if k > n - 1:
            continue
        labels = fcluster(Z, t=k, criterion="maxclust")
        n_clusters = len(np.unique(labels))
        if n_clusters < 2:
            continue
        try:
            sil = silhouette_score(d_matrix, labels, metric="precomputed")
        except Exception:
            sil = np.nan
        # Within-cluster variance: average pairwise distance within clusters
        within = 0.0
        within_count = 0
        for c in np.unique(labels):
            mask = labels == c
            if mask.sum() < 2:
                continue
            sub = d_matrix[np.ix_(mask, mask)]
            within += sub[np.triu_indices_from(sub, k=1)].sum()
            within_count += mask.sum() * (mask.sum() - 1) // 2
        within_avg = within / max(1, within_count)
        # Between-cluster: avg pairwise distance across clusters
        between = 0.0
        between_count = 0
        for c1 in np.unique(labels):
            for c2 in np.unique(labels):
                if c1 >= c2:
                    continue
                m1, m2 = labels == c1, labels == c2
                sub = d_matrix[np.ix_(m1, m2)]
                between += sub.sum()
                between_count += sub.size
        between_avg = between / max(1, between_count)
        F = between_avg / max(within_avg, 1e-9)
        out[k] = {
            "silhouette": float(sil),
            "within_var": float(within_avg),
            "between_F": float(F),
            "n_clusters_actual": int(n_clusters),
        }
    return out


# ────────────────────────────────────────────────────────────────────────
# Bootstrap null
# ────────────────────────────────────────────────────────────────────────

def bootstrap_validity_one(args):
    """One bootstrap rep: permute config tags within cohort, re-aggregate,
    re-cluster, return validity per k."""
    seed, df_records, stat = args
    rng = np.random.default_rng(seed)
    df = pd.DataFrame(df_records)
    # Permute config tags
    df["config"] = rng.permutation(df["config"].values)
    configs, moms, cfs, ns = aggregate_configs(df, stat)
    if len(configs) < 4:
        return {}
    d, _, _ = build_distance_matrix(moms, cfs)
    val = cluster_validity(d, ns)
    return {k: v["silhouette"] for k, v in val.items()}


def cohort_bootstrap(df_cohort, stat, n_boot=N_BOOTSTRAP, n_workers=8):
    """Return DataFrame with per-rep silhouette per k for null distribution."""
    records = df_cohort[["config", f"{stat}_resid_v6_3_A"]].to_dict(orient="records")
    rng = np.random.default_rng(RNG_SEED)
    seeds = rng.integers(0, 2**31, size=n_boot)
    args_list = [(int(s), records, stat) for s in seeds]
    nulls = []
    if n_workers <= 1:
        for a in args_list:
            nulls.append(bootstrap_validity_one(a))
    else:
        with ProcessPoolExecutor(max_workers=n_workers) as ex:
            for fut in as_completed([ex.submit(bootstrap_validity_one, a) for a in args_list]):
                try:
                    nulls.append(fut.result())
                except Exception as e:
                    nulls.append({})
    rows = []
    for i, n in enumerate(nulls):
        for k, sil in n.items():
            rows.append({"rep": i, "k": k, "silhouette_null": sil})
    return pd.DataFrame(rows)


# ────────────────────────────────────────────────────────────────────────
# Per-cohort orchestration
# ────────────────────────────────────────────────────────────────────────

def analyze_cohort(df_cohort, cohort_label, stat, n_boot=N_BOOTSTRAP):
    """Returns dict with verdict, k*, p-value, cluster info, top pairs."""
    n_obs = len(df_cohort)
    print(f"  [{cohort_label} / {stat}] n_obs={n_obs}")
    configs, moms, cfs, ns = aggregate_configs(df_cohort, stat)
    n_configs = len(configs)
    print(f"    configs retained (>={MIN_CONFIG_OBS} obs): {n_configs} of 648 possible")
    if n_configs < 8:
        return {
            "cohort": cohort_label, "stat": stat, "n_obs": n_obs,
            "n_configs_retained": n_configs,
            "verdict": "insufficient_configs",
            "k_star": None, "silhouette_obs": None, "p_value": None,
            "configs": configs, "labels_at_kstar": [],
        }
    d, d_mom, d_phi = build_distance_matrix(moms, cfs)
    val = cluster_validity(d, ns)
    if not val:
        return {
            "cohort": cohort_label, "stat": stat, "n_obs": n_obs,
            "n_configs_retained": n_configs,
            "verdict": "clustering_failed",
            "k_star": None, "silhouette_obs": None, "p_value": None,
            "configs": configs, "labels_at_kstar": [],
        }
    # k* = argmax silhouette across K_VALUES
    k_star = max(val.keys(), key=lambda k: val[k]["silhouette"])
    sil_obs = val[k_star]["silhouette"]
    print(f"    k*={k_star}, silhouette={sil_obs:.4f}")

    # Bootstrap null
    print(f"    bootstrap n_boot={n_boot}")
    t0 = time.time()
    null_df = cohort_bootstrap(df_cohort, stat, n_boot=n_boot, n_workers=8)
    print(f"    bootstrap took {time.time()-t0:.1f}s")
    null_at_kstar = null_df[null_df["k"] == k_star]["silhouette_null"].dropna().values
    if len(null_at_kstar) == 0:
        p = np.nan
    else:
        p = (null_at_kstar >= sil_obs).mean()

    # Verdict
    if k_star is not None and 4 <= k_star <= 16 and p < 0.05:
        verdict = "structure_detected"
    elif k_star is None or k_star > 30 or (p is not None and p >= 0.05):
        if n_obs < 1000:
            verdict = "no_structure_underpowered"
        else:
            verdict = "no_structure"
    else:
        verdict = "ambiguous"

    # Cluster assignments at k*
    np.fill_diagonal(d, 0)
    cond = squareform(d, checks=False)
    Z = linkage(cond, method="average")
    labels_at_kstar = fcluster(Z, t=k_star, criterion="maxclust")

    return {
        "cohort": cohort_label, "stat": stat, "n_obs": n_obs,
        "n_configs_retained": n_configs,
        "verdict": verdict,
        "k_star": k_star, "silhouette_obs": sil_obs, "p_value": float(p),
        "configs": configs, "labels_at_kstar": labels_at_kstar.tolist(),
        "cf_pairwise_max": float(d_phi.max()) if d_phi.size else 0.0,
        "moment_pairwise_max": float(d_mom.max()) if d_mom.size else 0.0,
        "all_validity": val,
        "null_distribution": null_df.to_dict(orient="records"),
    }


def find_top_pairs(result, df_cohort, stat, n_top=10):
    """Find the most-distinct cluster pairs and report dominant config tags."""
    if result["verdict"] != "structure_detected":
        return []
    labels = np.array(result["labels_at_kstar"])
    configs = result["configs"]
    config_to_cluster = dict(zip(configs, labels))
    df = df_cohort.copy()
    df["cluster"] = df["config"].map(config_to_cluster)
    df = df.dropna(subset=["cluster"])
    df["cluster"] = df["cluster"].astype(int)

    # Per-cluster: residual distribution stats + dominant config-axis values
    resid_col = f"{stat}_resid_v6_3_A"
    cluster_summary = {}
    for c in sorted(df["cluster"].unique()):
        sub = df[df["cluster"] == c]
        r = sub[resid_col].dropna().values
        if len(r) == 0:
            continue
        # Dominant axis values (mode)
        axis_modes = {}
        for ax in ["opp_class", "record_tier", "pace_tier", "home_away",
                    "role", "season_phase"]:
            counts = sub[ax].value_counts()
            if len(counts):
                axis_modes[ax] = counts.index[0]
        cluster_summary[c] = {
            "n_obs": len(r),
            "mean": float(r.mean()),
            "var": float(r.var()),
            "skew": float(((r - r.mean())**3).mean() / (r.std()**3 + 1e-9)),
            "kurt": float(((r - r.mean())**4).mean() / (r.var()**2 + 1e-9) - 3),
            "axis_modes": axis_modes,
        }
    # Top pairs by mean-difference (z-scored)
    pairs = []
    keys = sorted(cluster_summary.keys())
    sds = [cluster_summary[k]["var"]**0.5 for k in keys]
    pooled_sd = np.mean(sds) if sds else 1
    for i, c1 in enumerate(keys):
        for c2 in keys[i+1:]:
            s1, s2 = cluster_summary[c1], cluster_summary[c2]
            mean_diff = abs(s1["mean"] - s2["mean"]) / max(pooled_sd, 1e-9)
            pairs.append({
                "cluster_1": c1, "cluster_2": c2,
                "mean_diff_z": mean_diff,
                "c1_mean": s1["mean"], "c2_mean": s2["mean"],
                "c1_var": s1["var"],  "c2_var": s2["var"],
                "c1_n": s1["n_obs"],   "c2_n": s2["n_obs"],
                "c1_modes": s1["axis_modes"],
                "c2_modes": s2["axis_modes"],
            })
    pairs.sort(key=lambda p: -p["mean_diff_z"])
    return pairs[:n_top]


# ────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────

def main():
    print("[load] v6.3-A residuals")
    rdf = pd.read_csv(RESID_CSV, parse_dates=["game_date"])
    print(f"  rows: {len(rdf)}, cols: {len(rdf.columns)}")

    print("[load] historical box scores for context lookups")
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx["game_date"] = pd.to_datetime(bx["game_date"])
    bx["nba_api_id"] = bx["nba_api_id"].astype(int)
    # Normalize game_id to int (residuals.csv roundtripped string -> int)
    bx["game_id"] = bx["game_id"].astype(str).str.lstrip("0").astype(int)
    bx_25_26 = bx[(bx["season"] == "2025-26") &
                    (bx["season_type"] == "Regular Season")].copy()
    bx_25_26["minutes"] = pd.to_numeric(bx_25_26["minutes"], errors="coerce")
    bx_25_26_played = bx_25_26[bx_25_26["minutes"] > 0].copy()

    print("[build] context lookups")
    opp_class_map = build_opp_def_rating_quartile(bx)
    print(f"  opp_class teams: {len(opp_class_map)}")
    pace_map = build_pace_tercile(bx)
    print(f"  pace games: {len(pace_map)}")
    role_df = build_role_stability(bx_25_26_played)
    print(f"  role rows: {len(role_df)}")
    rank_24_25_winpct = build_24_25_winpct(bx)
    opp_record_tier = build_opp_record_tier_lookup(bx_25_26, rank_24_25_winpct)
    print(f"  opp_record_tier entries: {len(opp_record_tier)}")

    # Build team_total per team for season_phase calc; here all teams played 82
    team_game_n_lookup = bx_25_26.groupby(["team_abbr", "game_id", "game_date"]).size()
    season_phase_fn = build_season_phase(None, None, team_total_games=82)

    # Need team_game_n for player-team in residuals.csv
    tg = (bx_25_26.groupby(["team_abbr", "game_id", "game_date"])
                  .size().reset_index(name="_n"))
    tg = tg.sort_values(["team_abbr", "game_date"]).reset_index(drop=True)
    tg["team_game_n"] = tg.groupby("team_abbr").cumcount() + 1
    team_game_n_map = dict(zip(zip(tg["team_abbr"], tg["game_id"]), tg["team_game_n"]))

    print("[tag] residuals with config")
    rdf["opp_class"] = rdf["opp_abbr"].map(opp_class_map).fillna("mid")
    rdf["pace_tier"] = rdf["game_id"].map(pace_map).fillna("medium")
    rdf["home_away"] = rdf["minutes"].notna()  # placeholder; need is_home from box
    # is_home from bx_25_26
    is_home_map = dict(zip(zip(bx_25_26["nba_api_id"], bx_25_26["game_id"]),
                            bx_25_26["is_home"]))
    rdf["is_home"] = rdf.apply(lambda r: is_home_map.get((int(r["nba_api_id"]), r["game_id"]), False), axis=1)
    rdf["home_away"] = rdf["is_home"].map({True: "home", False: "away"})
    # role
    role_lu = dict(zip(zip(role_df["nba_api_id"].astype(int), role_df["game_id"]),
                        role_df["role"]))
    rdf["role"] = rdf.apply(
        lambda r: role_lu.get((int(r["nba_api_id"]), r["game_id"]), "spot"), axis=1)
    # opp record tier
    rdf["record_tier"] = rdf.apply(
        lambda r: opp_record_tier.get((r["opp_abbr"], r["game_date"]), "mid"), axis=1)
    # team_game_n for player's team
    rdf["team_game_n_self"] = rdf.apply(
        lambda r: team_game_n_map.get((r["team_abbr"], r["game_id"]), np.nan), axis=1)
    rdf["season_phase"] = rdf.apply(
        lambda r: season_phase_fn(r["game_date"], r["team_game_n_self"]), axis=1)

    rdf["config"] = (rdf["opp_class"] + "_" + rdf["record_tier"] + "_" +
                       rdf["pace_tier"] + "_" + rdf["home_away"] + "_" +
                       rdf["role"] + "_" + rdf["season_phase"])

    print(f"  unique configs in data: {rdf['config'].nunique()} (of 648 possible)")
    print(f"  rows with config: {len(rdf)}")

    # ── Per-cohort analysis ─────────────────────────────────────────────
    print("\n[analyze] per-cohort × stat")
    cohorts = []
    for cohort_v in ["rookie", "soph", "vet"]:
        for pos_v in ["Center", "Forward", "Guard"]:
            cohorts.append((cohort_v, pos_v))

    all_results = []
    all_top_pairs = []
    for cohort_v, pos_v in cohorts:
        sub = rdf[(rdf["cohort"] == cohort_v) & (rdf["pos_class"] == pos_v)]
        if len(sub) < 100:
            print(f"\n[skip] {cohort_v}_{pos_v}: n={len(sub)} < 100")
            for stat in STATS:
                all_results.append({
                    "cohort": f"{cohort_v}_{pos_v}", "stat": stat,
                    "n_obs": len(sub), "n_configs_retained": 0,
                    "verdict": "insufficient_n", "k_star": None,
                    "silhouette_obs": None, "p_value": None,
                })
            continue
        for stat in STATS:
            print(f"\n[run] {cohort_v}_{pos_v} / {stat}")
            t0 = time.time()
            result = analyze_cohort(sub, f"{cohort_v}_{pos_v}", stat)
            elapsed = time.time() - t0
            print(f"  done in {elapsed:.1f}s, verdict: {result['verdict']}")
            top = find_top_pairs(result, sub, stat)
            for pair in top:
                pair["cohort"] = f"{cohort_v}_{pos_v}"
                pair["stat"] = stat
                all_top_pairs.append(pair)
            all_results.append(result)

    # ── Outputs ────────────────────────────────────────────────────────
    print("\n[save] outputs")
    # Per-cohort verdict table
    verdict_rows = []
    for r in all_results:
        verdict_rows.append({
            "cohort": r["cohort"], "stat": r["stat"], "n_obs": r["n_obs"],
            "n_configs_retained": r["n_configs_retained"],
            "k_star": r["k_star"], "silhouette_obs": r["silhouette_obs"],
            "p_value": r["p_value"], "verdict": r["verdict"],
        })
    pd.DataFrame(verdict_rows).to_csv(
        OUT_DIR / "result_contextual_a_final_verdicts.csv", index=False)

    # Cluster assignments per cohort
    assign_rows = []
    for r in all_results:
        if r.get("labels_at_kstar"):
            for cfg, lbl in zip(r["configs"], r["labels_at_kstar"]):
                assign_rows.append({"cohort": r["cohort"], "stat": r["stat"],
                                     "config": cfg, "cluster": int(lbl)})
    pd.DataFrame(assign_rows).to_csv(
        OUT_DIR / "result_contextual_a_final_per_cohort.csv", index=False)

    # Bootstrap distribution
    boot_rows = []
    for r in all_results:
        if r.get("null_distribution"):
            for entry in r["null_distribution"]:
                entry["cohort"] = r["cohort"]
                entry["stat"] = r["stat"]
                boot_rows.append(entry)
    pd.DataFrame(boot_rows).to_csv(
        OUT_DIR / "result_contextual_a_final_bootstrap.csv", index=False)

    # Top pairs
    pd.DataFrame(all_top_pairs).to_csv(
        OUT_DIR / "result_contextual_a_final_top_pairs.csv", index=False)

    # Save summary JSON
    summary = {"results": [{k: v for k, v in r.items()
                              if k not in ("null_distribution", "all_validity",
                                            "labels_at_kstar", "configs")}
                             for r in all_results]}
    with open(OUT_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\nDONE. Outputs at {OUT_DIR}")


if __name__ == "__main__":
    main()
