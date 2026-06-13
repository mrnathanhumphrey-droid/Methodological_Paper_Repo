"""25-26 cohort widening — adds sophs + 2025 rookies to the v4-lite ship.

Two cohorts handled:
  - SOPHS + VET-NOT-IN-FIT: 24-25 NBA actives (≥10 GP) NOT in the main-fit
    133-player cohort. Use 24-25 per-36 directly as 25-26 projection.
    Variance: main-fit median per-36 sd × 1.2 (tighter sample than fit).

  - 2025 ROOKIES: 59 draft picks, no NBA data yet, no nba_api_id, no NCAA
    2024-25 data ingested. Project from draft_pick × stat regression fit on
    historical rookies (n ≈ 990 NBA rookies, 2014-15 → 2024-25). Synthetic
    IDs in 9990000+ range (e.g. pick 1 = 9990001) until real IDs appear.
    Variance: main-fit median per-36 sd × 2.0 (no individual data).

Output: audit_runs/cohort_widening_v0_2025_26/per_player_projections.csv
Schema matches v1 unifier output so v1 can concat with the v4-lite vet rows.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
SAVE_DIR = REPO / "audit_runs" / "cohort_widening_v0_2025_26"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

TEST_SEASON = "2025-26"

STATS = ["PTS", "REB", "AST", "STL", "BLK", "TOV",
         "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA"]

MIN_SOPH_GP = 10
SOPH_SD_MULT = 1.2
ROOKIE_SD_MULT = 2.0
ROOKIE_ID_BASE = 9990000  # pick 1 -> 9990001, etc.


def find_v4_audit(stat: str) -> Path | None:
    """Latest v4-lite PTS audit subdir for our 25-26 test season.

    Mirrors _v4_audit logic in scratch._unified_projection_ship_2025_26.
    """
    audit = REPO / "audit_runs"
    cands = []
    for run in audit.iterdir():
        if not run.is_dir(): continue
        for sub in run.iterdir():
            if not sub.is_dir(): continue
            if f"_{stat}_phase4_v4" not in sub.name: continue
            if not sub.name.endswith(f"__{TEST_SEASON}"): continue
            proj = sub / "per_player_projections.csv"
            if proj.exists():
                df = pd.read_csv(proj)
                with_act = df.dropna(subset=["actual"])
                if len(with_act) >= 100:
                    cands.append((sub.stat().st_mtime, sub))
    if not cands:
        return None
    return sorted(cands, key=lambda c: c[0])[-1][1]


def load_main_fit_sd_baseline() -> tuple[dict[str, float], set[int]]:
    """Median proj_sd per stat AND the set of nba_api_ids in the main fit
    cohort. Source: per-stat v4-lite audits (one per stat). Falls back
    to PTS audit alone if some stats missing."""
    sd_baseline = {}
    vet_ids = set()
    for s in STATS:
        adir = find_v4_audit(s)
        if adir is None:
            continue
        df = pd.read_csv(adir / "per_player_projections.csv")
        df = df.dropna(subset=["actual"])
        df["nba_api_id"] = df["nba_api_id"].astype(int)
        sd_baseline[s] = float(df["proj_sd"].median())
        if not vet_ids:
            vet_ids = set(df["nba_api_id"].tolist())
        else:
            # Take union: any player in any v4-lite audit is "in main fit"
            vet_ids |= set(df["nba_api_id"].tolist())
    if not sd_baseline:
        raise FileNotFoundError(
            "No v4-lite audits found for 25-26 test. Run cli.run_v4lite_overnight first."
        )
    return sd_baseline, vet_ids


def load_24_25_per36(min_gp: int, half: str = "h2_with_full_fallback",
                      h2_min_gp: int = 10) -> pd.DataFrame:
    """Aggregate 24-25 regular-season box scores to per-36 stats per player.

    half: "full"                  → full-season per-36
          "h2_with_full_fallback" → late-half per-36 for rate stats (use full
                                    when player has <h2_min_gp H2 games);
                                    MPG always full-season because H2 MPG
                                    is too noisy (load management / tanking).
    Empirical justification: 24-25→25-26 sophs tested. H2 baseline shrinks
    PTS bias from −1.20 to −0.42, REB r jumps 0.74→0.81, usage proxy r
    jumps 0.51→0.60. MPG is the exception: H2 r=0.50 vs full r=0.54.
    """
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx = bx[(bx["season"] == "2024-25") & (bx["season_type"] == "Regular Season")].copy()
    bx["minutes"] = pd.to_numeric(bx["minutes"], errors="coerce")
    bx = bx.dropna(subset=["minutes"])
    bx = bx[bx["minutes"] > 0]

    def _agg(df):
        return df.groupby("nba_api_id").agg(
            gp=("game_id", "count"),
            minutes_total=("minutes", "sum"),
            PTS=("PTS", "sum"), REB=("REB", "sum"), AST=("AST", "sum"),
            STL=("STL", "sum"), BLK=("BLK", "sum"), TOV=("TOV", "sum"),
            FGM=("FGM", "sum"), FGA=("FGA", "sum"),
            FG3M=("FG3M", "sum"), FG3A=("FG3A", "sum"),
            FTM=("FTM", "sum"), FTA=("FTA", "sum"),
        ).reset_index()

    full = _agg(bx)
    full = full[full["gp"] >= min_gp].copy()
    full["mpg_full"] = full["minutes_total"] / full["gp"]
    factor_full = 36.0 / full["minutes_total"]
    for s in STATS:
        full[f"{s}_per36_full"] = full[s] * factor_full

    if half == "full":
        out = full.rename(columns={f"{s}_per36_full": f"{s}_proj" for s in STATS})
        out = out.rename(columns={"mpg_full": "mpg"})
        return out[["nba_api_id", "gp", "mpg"] + [f"{s}_proj" for s in STATS]]

    # H2-with-full-fallback path
    bx2 = bx.copy()
    bx2["game_date"] = pd.to_datetime(bx2["game_date"])
    bx2 = bx2.sort_values(["nba_api_id", "game_date"])
    bx2["rank"] = bx2.groupby("nba_api_id").cumcount()
    bx2["gp_total"] = bx2.groupby("nba_api_id")["game_id"].transform("count")
    h2_only = bx2[bx2["rank"] >= bx2["gp_total"] / 2.0].copy()
    h2 = _agg(h2_only)
    h2 = h2[h2["gp"] >= h2_min_gp].copy()
    factor_h2 = 36.0 / h2["minutes_total"]
    for s in STATS:
        h2[f"{s}_per36_h2"] = h2[s] * factor_h2

    # Merge: prefer H2 rate stats, fall back to full where H2 missing
    h2_cols = ["nba_api_id"] + [f"{s}_per36_h2" for s in STATS]
    merged = full.merge(h2[h2_cols], on="nba_api_id", how="left")
    n_h2_used = merged[f"PTS_per36_h2"].notna().sum()
    n_full_fallback = merged[f"PTS_per36_h2"].isna().sum()
    print(f"  H2 rate-stat baseline: {n_h2_used} sophs/players "
          f"(fallback to full-season for {n_full_fallback})")

    for s in STATS:
        merged[f"{s}_proj"] = merged[f"{s}_per36_h2"].fillna(merged[f"{s}_per36_full"])
    merged["mpg"] = merged["mpg_full"]  # always full-season MPG
    return merged[["nba_api_id", "gp", "mpg"] + [f"{s}_proj" for s in STATS]]


def load_rookie_per36_history() -> pd.DataFrame:
    """All NBA rookies (first-season per-36) joined with draft_pick."""
    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx = bx[bx["season_type"] == "Regular Season"].copy()
    bx["minutes"] = pd.to_numeric(bx["minutes"], errors="coerce")
    bx = bx.dropna(subset=["minutes"])
    bx = bx[bx["minutes"] > 0]
    first = bx.groupby("nba_api_id")["season"].min().reset_index().rename(
        columns={"season": "rookie_season"}
    )
    bx = bx.merge(first, on="nba_api_id")
    bx_rk = bx[bx["season"] == bx["rookie_season"]].copy()
    agg = bx_rk.groupby(["nba_api_id", "rookie_season"]).agg(
        gp=("game_id", "count"),
        minutes_total=("minutes", "sum"),
        **{s: (s, "sum") for s in STATS},
    ).reset_index()
    agg = agg[agg["gp"] >= 10].copy()
    factor = 36.0 / agg["minutes_total"]
    for s in STATS:
        agg[f"{s}_per36"] = agg[s] * factor

    draft = pd.read_parquet(PQ / "nba_draft_data.parquet")
    draft = draft.dropna(subset=["nba_api_id"])
    draft["nba_api_id"] = draft["nba_api_id"].astype(int)
    draft = draft[["nba_api_id", "draft_pick", "draft_year"]].drop_duplicates(
        subset=["nba_api_id"], keep="first"
    )
    return agg.merge(draft, on="nba_api_id", how="inner")


def fit_pick_regressions(rookies: pd.DataFrame) -> dict[str, dict]:
    """Per-stat OLS: per36 = a + b * log(draft_pick).

    Log-pick because rookie-impact decays roughly log-linearly with pick #
    (#1 vs #2 differs more than #57 vs #58).
    """
    rookies = rookies.copy()
    rookies["log_pick"] = np.log(rookies["draft_pick"].astype(float))
    coefs = {}
    for s in STATS:
        col = f"{s}_per36"
        sub = rookies[["log_pick", col]].dropna()
        if len(sub) < 30:
            continue
        x = sub["log_pick"].values
        y = sub[col].values
        b = np.cov(x, y, ddof=1)[0, 1] / x.var(ddof=1)
        a = y.mean() - b * x.mean()
        yhat = a + b * x
        ss_res = ((y - yhat) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        # Floor at 0 for non-negative stats
        coefs[s] = {
            "intercept": float(a), "slope_log_pick": float(b),
            "r2": float(r2), "n": int(len(sub)),
            "pop_mean": float(y.mean()), "pop_sd": float(y.std()),
        }
    return coefs


def project_sophs(sd_baseline: dict[str, float], vet_ids: set[int]) -> pd.DataFrame:
    """24-25 actives ≥10 GP not in main-fit cohort."""
    print(f"  vet cohort (excluded): {len(vet_ids)} players")

    soph = load_24_25_per36(MIN_SOPH_GP)
    soph["nba_api_id"] = soph["nba_api_id"].astype(int)
    soph = soph[~soph["nba_api_id"].isin(vet_ids)].copy()
    print(f"  24-25 active soph + vet-not-in-fit: {len(soph)} players")

    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    meta["nba_api_id"] = meta["nba_api_id"].astype(int)
    soph = soph.merge(meta[["nba_api_id", "name"]], on="nba_api_id", how="left")

    for s in STATS:
        soph[f"{s}_sd"] = sd_baseline.get(s, 1.0) * SOPH_SD_MULT
        soph[f"{s}_actual"] = float("nan")

    soph = soph.rename(columns={"mpg": "mpg_naive"})
    keep = ["nba_api_id", "name"]
    for s in STATS:
        keep += [f"{s}_proj", f"{s}_sd", f"{s}_actual"]
    keep.append("mpg_naive")
    soph["__cohort"] = "soph_or_unfit_vet"
    return soph[keep + ["__cohort"]]


def _combine_pos_to_class(pos: str | None) -> str | None:
    """Map combine position string ('PG', 'SF-PF', etc.) to G/F/C class."""
    if not pos or pd.isna(pos):
        return None
    first = pos.split("-")[0].strip().upper()
    if first in ("PG", "SG"):
        return "G"
    if first in ("SF", "PF"):
        return "F"
    if first == "C":
        return "C"
    return None


def _combine_pos_to_full(pos: str | None) -> str | None:
    """Map combine position to a 'Guard' / 'Forward' / 'Center' string for
    metadata.position column compatibility with player_metadata_enriched."""
    cls = _combine_pos_to_class(pos)
    if cls == "G":
        return "Guard"
    if cls == "F":
        return "Forward"
    if cls == "C":
        return "Center"
    return None


def _load_ncaa_translation_factors() -> dict[str, dict] | None:
    """Locked NCAA→NBA per-stat translation factors. Returns dict[stat]->coefs
    or None if not yet calibrated."""
    p = PQ / "translation_factors.parquet"
    if not p.exists():
        return None
    tf = pd.read_parquet(p)
    ncaa = tf[tf["league"] == "ncaa"]
    out = {}
    for _, row in ncaa.iterrows():
        out[row["stat"]] = {
            "intercept": float(row["intercept"]),
            "slope": float(row["slope"]),
            "r2": float(row["r2"]),
            "n": int(row["n"]),
        }
    return out if out else None


def _load_2025_ncaa_per40() -> pd.DataFrame:
    """2025 draft class's 24-25 NCAA per-40 stats, ready to translate.

    Derives per-40 for FG3M/FG3A (missing in raw join) from per-game / mpg.
    """
    nc = pd.read_parquet(PQ / "ncaa_player_seasons.parquet")
    nc = nc[(nc["ncaa_season"] == "2024-25") & (nc["draft_year"] == 2025)].copy()
    # Derive missing per-40 columns where source per-game exists
    for stat in ["FG3M", "FG3A", "FTM", "FTA"]:
        pg_col = f"{stat.lower()}_pg"
        p40_col = f"{stat.lower()}_per40"
        if pg_col in nc.columns and "mpg" in nc.columns:
            mpg = pd.to_numeric(nc["mpg"], errors="coerce")
            pg = pd.to_numeric(nc[pg_col], errors="coerce")
            with np.errstate(divide="ignore", invalid="ignore"):
                derived = pg * 40.0 / mpg
            if p40_col in nc.columns:
                nc[p40_col] = pd.to_numeric(nc[p40_col], errors="coerce").fillna(derived)
            else:
                nc[p40_col] = derived
    return nc


def project_rookies(sd_baseline: dict[str, float]) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """2025 draft class projector. Two paths:

    PATH A — NCAA translation (for picks with 24-25 NCAA stats): apply locked
             per-stat regression NCAA_per40 -> NBA_rookie_per36.
    PATH B — draft-pick log regression (fallback for intl/G-League pathway):
             fit on historical rookies with non-NaN draft_pick.

    Locked translation factors come from translation_factors.parquet. Calibration
    sample is 2014-2023 NCAA→NBA pairs — does NOT include 24-25 NCAA → 25-26 NBA
    (which would be leakage onto the test season we're projecting).
    """
    rookie_history = load_rookie_per36_history()
    print(f"  historical rookies for regression: {len(rookie_history)}")
    coefs = fit_pick_regressions(rookie_history)
    for s, c in coefs.items():
        print(f"    {s}: intercept={c['intercept']:.3f}, slope_log_pick={c['slope_log_pick']:+.3f}, R²={c['r2']:.3f}, n={c['n']}")

    ncaa_tf = _load_ncaa_translation_factors()
    if ncaa_tf:
        print(f"  NCAA translation factors loaded: {len(ncaa_tf)} stats covered")
        ncaa_25 = _load_2025_ncaa_per40()
        print(f"  2025 NCAA per-40 entries: {len(ncaa_25)}")
    else:
        ncaa_25 = pd.DataFrame()
        print("  NCAA translation factors NOT FOUND — using draft-pick regression for all rookies")

    draft = pd.read_parquet(PQ / "nba_draft_data.parquet")
    d25 = draft[draft["draft_year"] == 2025].copy()
    d25 = d25.dropna(subset=["draft_pick"])
    d25["draft_pick"] = d25["draft_pick"].astype(int)
    d25["log_pick"] = np.log(d25["draft_pick"].astype(float))
    print(f"  2025 draft picks: {len(d25)}")

    # Combine measurables -> position. Match by player_name_raw.
    cm = pd.read_parquet(PQ / "nba_combine_measurables.parquet")
    cm25 = cm[cm["draft_year"] == 2025][["player_name_raw", "position"]].copy()
    cm25 = cm25.rename(columns={"position": "combine_position"})
    d25 = d25.merge(cm25, on="player_name_raw", how="left")
    n_with_pos = d25["combine_position"].notna().sum()
    print(f"  combine positions matched: {n_with_pos}/{len(d25)}")

    # Build base frame for rookies
    rookies = pd.DataFrame({
        "nba_api_id": ROOKIE_ID_BASE + d25["draft_pick"].values,
        "name": d25["player_name_raw"].values,
        "draft_pick": d25["draft_pick"].values,
        "log_pick": d25["log_pick"].values,
    })

    # Match NCAA stats by name where available
    ncaa_join = pd.DataFrame()
    if not ncaa_25.empty:
        ncaa_cols_keep = ["player_name_raw"] + [f"{s.lower()}_per40" for s in STATS]
        ncaa_cols_keep = [c for c in ncaa_cols_keep if c in ncaa_25.columns]
        ncaa_join = ncaa_25[ncaa_cols_keep].rename(
            columns={"player_name_raw": "name"}
        )
        rookies = rookies.merge(ncaa_join, on="name", how="left")
        n_ncaa = rookies[f"{STATS[0].lower()}_per40"].notna().sum() if f"{STATS[0].lower()}_per40" in rookies.columns else 0
        print(f"  rookies with NCAA 24-25 stats (PATH A — translation): {n_ncaa}")
        print(f"  rookies without NCAA 24-25 (PATH B — draft-pick fallback): {len(rookies) - n_ncaa}")

    # HYBRID v3 — per-stat method preference based on empirical 25-26 scoring:
    #   NCAA-preferred (rate-driven, transfers from college):
    #       REB, AST, STL, BLK, TOV, FTM, FTA  (BLK r jumped 0.36→0.66 with NCAA)
    #   PICK-preferred (volume-driven, NBA-usage-capped):
    #       PTS, FGM, FGA, FG3M, FG3A          (NCAA loses the pecking-order signal)
    NCAA_PREFERRED = {"REB", "AST", "STL", "BLK", "TOV", "FTM", "FTA"}
    PICK_PREFERRED = {"PTS", "FGM", "FGA", "FG3M", "FG3A"}

    method_log = {s: {"ncaa_translated": 0, "pick_regression": 0, "fallback_mean": 0}
                  for s in STATS}

    for s in STATS:
        ncaa_col = f"{s.lower()}_per40"
        proj_vals = []
        for idx, row in rookies.iterrows():
            ncaa_val = row.get(ncaa_col, np.nan) if ncaa_col in rookies.columns else np.nan
            ncaa_available = ncaa_tf and s in ncaa_tf and pd.notna(ncaa_val)

            if s in NCAA_PREFERRED and ncaa_available:
                tf = ncaa_tf[s]
                proj_vals.append(max(0.0, tf["intercept"] + tf["slope"] * float(ncaa_val)))
                method_log[s]["ncaa_translated"] += 1
            elif s in PICK_PREFERRED and s in coefs:
                c = coefs[s]
                proj_vals.append(max(0.0, c["intercept"] + c["slope_log_pick"] * row["log_pick"]))
                method_log[s]["pick_regression"] += 1
            elif ncaa_available:
                tf = ncaa_tf[s]
                proj_vals.append(max(0.0, tf["intercept"] + tf["slope"] * float(ncaa_val)))
                method_log[s]["ncaa_translated"] += 1
            elif s in coefs:
                c = coefs[s]
                proj_vals.append(max(0.0, c["intercept"] + c["slope_log_pick"] * row["log_pick"]))
                method_log[s]["pick_regression"] += 1
            else:
                proj_vals.append(float(rookie_history[f"{s}_per36"].mean()))
                method_log[s]["fallback_mean"] += 1
        rookies[f"{s}_proj"] = proj_vals
        rookies[f"{s}_sd"] = sd_baseline.get(s, 1.0) * ROOKIE_SD_MULT
        rookies[f"{s}_actual"] = float("nan")

    print(f"  Method usage per stat (NCAA / pick / mean):")
    for s, m in method_log.items():
        print(f"    {s:<5}: NCAA={m['ncaa_translated']:>3}  pick={m['pick_regression']:>3}  mean={m['fallback_mean']:>3}")
    # Drop the per-40 raw columns (used only for projection)
    drop_cols = [c for c in rookies.columns if c.endswith("_per40")]
    if drop_cols:
        rookies = rookies.drop(columns=drop_cols)

    # Rookie mpg projection: log-pick regression on historical rookie mpg
    rh = rookie_history.copy()
    rh["mpg"] = (rh["minutes_total"] / rh["gp"]).astype(float)
    rh["log_pick"] = np.log(rh["draft_pick"].astype(float))
    sub = rh[["log_pick", "mpg"]].dropna()
    b = np.cov(sub["log_pick"], sub["mpg"], ddof=1)[0, 1] / sub["log_pick"].var(ddof=1)
    a = sub["mpg"].mean() - b * sub["log_pick"].mean()
    rookies["mpg_naive"] = (a + b * rookies["log_pick"]).clip(lower=8.0, upper=36.0)
    print(f"  mpg regression: intercept={a:.2f}, slope={b:+.3f}; pick1 -> {a + b * np.log(1):.1f}, pick60 -> {a + b * np.log(60):.1f}")

    rookies["__cohort"] = "rookie_2025"
    keep = ["nba_api_id", "name"]
    for s in STATS:
        keep += [f"{s}_proj", f"{s}_sd", f"{s}_actual"]
    keep.append("mpg_naive")

    # Metadata supplement: nba_api_id, name, position, team, draft_year, debut_year
    # This is what v6.1 applier + Wonka writer need to look up for synthetic IDs.
    meta_sup = pd.DataFrame({
        "nba_api_id": ROOKIE_ID_BASE + d25["draft_pick"].values,
        "name": d25["player_name_raw"].values,
        "position": d25["combine_position"].apply(_combine_pos_to_full).values,
        "draft_year": 2025,
        "debut_year": 2025,  # 25-26 is their first season
        "draft_pick": d25["draft_pick"].values,
        "drafted_by_team": d25["drafted_by_team"].values,
    })
    # Default unknown positions to "Forward" (most common, lowest harm) and
    # log how many we defaulted.
    n_default = meta_sup["position"].isna().sum()
    meta_sup["position"] = meta_sup["position"].fillna("Forward")
    if n_default:
        print(f"  defaulted {n_default} rookies to 'Forward' position (no combine match)")

    return rookies[keep + ["__cohort"]], coefs, meta_sup


def main():
    print("=" * 75)
    print("25-26 cohort widening (sophs + 2025 rookies)")
    print("=" * 75)
    print()

    sd_baseline, vet_ids = load_main_fit_sd_baseline()
    print(f"Main-fit cohort (from v4-lite audits): {len(vet_ids)} players")
    print("Main-fit sd baseline (median per-36 sd):")
    for s, v in sd_baseline.items():
        print(f"  {s:<5}: {v:.3f}")
    print()

    print("--- SOPH + VET-NOT-IN-FIT cohort ---")
    sophs = project_sophs(sd_baseline, vet_ids)
    print(f"  produced: {len(sophs)} rows")
    print()

    print("--- 2025 ROOKIE cohort ---")
    rookies, coefs, meta_sup = project_rookies(sd_baseline)
    print(f"  produced: {len(rookies)} rows")
    # Save the metadata supplement for v6.1 applier + Wonka writer.
    sup_path = SAVE_DIR / "rookie_metadata_supplement.parquet"
    meta_sup.to_parquet(sup_path, index=False)
    print(f"  metadata supplement -> {sup_path}")
    print()

    combined = pd.concat([sophs, rookies], ignore_index=True)
    print(f"Total cohort widening rows: {len(combined)}")
    print(f"  cohort breakdown: {combined['__cohort'].value_counts().to_dict()}")

    out = SAVE_DIR / "per_player_projections.csv"
    combined.to_csv(out, index=False)
    print(f"\nWrote {out}")

    metadata = {
        "version": "cohort_widening_v1_2025_26",
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "n_sophs_or_unfit_vets": int((combined["__cohort"] == "soph_or_unfit_vet").sum()),
        "n_rookies_2025": int((combined["__cohort"] == "rookie_2025").sum()),
        "min_soph_gp": MIN_SOPH_GP,
        "soph_sd_mult": SOPH_SD_MULT,
        "rookie_sd_mult": ROOKIE_SD_MULT,
        "rookie_id_base": ROOKIE_ID_BASE,
        "sd_baseline_per_stat": sd_baseline,
        "rookie_pick_regression_coefs": coefs,
        "soph_baseline_lever": "h2_with_full_fallback (rate stats from "
                               "24-25 second half; MPG from full season). "
                               "Empirical: shrinks soph PTS bias −1.20 → "
                               "−0.42, REB r 0.74→0.81, usage r 0.51→0.60.",
        "notes": "v1 cohort widening. Sophs use 24-25 H2 per-36 with full "
                 "fallback (MPG always full season). Rookies use draft-pick "
                 "log regression on historical rookies (NCAA 2024-25 data "
                 "not yet ingested, so per-player NCAA translation deferred). "
                 "Synthetic rookie IDs in 9990000+ range.",
    }
    with open(SAVE_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata -> {SAVE_DIR}/metadata.json")


if __name__ == "__main__":
    main()
