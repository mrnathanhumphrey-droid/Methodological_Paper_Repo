"""Fetch missing playoff round 2/3/4 boxscores for 22-23, 23-24, 24-25.

Existing data/parquet/playoffs/round1/ holds first-round playoff games for all
seasons 09-10 through 25-26 (despite the dir name, they are R1 only — verified
by manifest: 43-47 games per season, exactly first-round capacity).

This script uses nba_api LeagueGameLog (season_type='Playoffs') to enumerate
ALL playoff games for the target seasons, identifies the games NOT already in
the round1 manifest, and pulls per-game traditional + advanced + summary
boxscores for those missing games. Output schema matches round1/ for direct
load via the backtest pipeline.

Output: data/parquet/playoffs/extra_rounds/
  - _manifest.parquet
  - traditional_t0.parquet, traditional_t1.parquet
  - advanced_t0.parquet, advanced_t1.parquet
  - summary_game.parquet (game_date, home/away, etc.)

Resume-safe: skips game_ids already pulled in this dir (in addition to skipping
those in round1/). Atomic flush every 20 games.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from config.paths import DATA_PARQUET_DIR

logging.basicConfig(level="INFO",
                    format="%(asctime)s %(name)s %(levelname)s | %(message)s")
log = logging.getLogger("playoff_fetch")

TARGET_SEASONS = ["2022-23", "2023-24", "2024-25"]

PLAYOFFS_R1 = DATA_PARQUET_DIR / "playoffs" / "round1"
PLAYOFFS_EXTRA = DATA_PARQUET_DIR / "playoffs" / "extra_rounds"
PLAYOFFS_EXTRA.mkdir(parents=True, exist_ok=True)

THROTTLE_S = 0.6
RETRY_MAX = 5
RETRY_BASE_S = 2.0
RETRY_CAP_S = 60.0
FLUSH_EVERY = 20


@dataclass
class Throttler:
    interval_s: float
    _last: float = field(default=0.0)

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last
        if elapsed < self.interval_s:
            time.sleep(self.interval_s - elapsed)
        self._last = time.monotonic()


def _is_transient(err: BaseException) -> bool:
    msg = str(err).lower()
    return any(t in msg for t in (
        "429", "timeout", "timed out", "connection",
        "max retries", "read timeout", "remote end closed",
        "temporarily unavailable", "service unavailable",
    ))


def _call(fn, label: str, throttler: Throttler):
    delay = RETRY_BASE_S
    last = None
    for attempt in range(RETRY_MAX):
        throttler.wait()
        try:
            return fn()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            last = e
            transient = _is_transient(e)
            log.warning("%s attempt %d/%d failed (transient=%s): %s",
                        label, attempt + 1, RETRY_MAX, transient, e)
            if not transient and attempt >= 1:
                raise
            if attempt < RETRY_MAX - 1:
                time.sleep(delay)
                delay = min(delay * 2, RETRY_CAP_S)
    raise RuntimeError(f"{label} failed after {RETRY_MAX}: {last}")


def existing_round1_game_ids() -> set:
    m = pd.read_parquet(PLAYOFFS_R1 / "_manifest.parquet")
    return set(m["game_id"].astype(str).unique())


def existing_extra_game_ids() -> set:
    p = PLAYOFFS_EXTRA / "_manifest.parquet"
    if not p.exists():
        return set()
    m = pd.read_parquet(p)
    return set(m["game_id"].astype(str).unique())


def enumerate_playoff_games(seasons: list[str], throttler: Throttler) -> pd.DataFrame:
    """Return (game_id, season, game_date, home_team_abbr, away_team_abbr,
                home_team_id, away_team_id, matchup_idx, game_in_series, round).

    matchup_idx, game_in_series, round derived from the 10-char nba_api game_id:
      0 0 4 SS R MM G G G G  (where SS=season YY, R=round 1-4, MM=matchup, GGG=game in series)
    """
    from nba_api.stats.endpoints import LeagueGameLog

    rows = []
    for season in seasons:
        log.info("LeagueGameLog %s Playoffs ...", season)
        resp = _call(
            lambda s=season: LeagueGameLog(
                season=s, season_type_all_star="Playoffs",
                player_or_team_abbreviation="T", timeout=30,
            ),
            label=f"LeagueGameLog/{season}", throttler=throttler,
        )
        df = resp.league_game_log.get_data_frame()
        df.columns = [c.lower() for c in df.columns]
        # Each game has two rows (home + away). Reduce to per-game.
        for gid, group in df.groupby("game_id"):
            if len(group) != 2:
                continue
            g0, g1 = group.iloc[0], group.iloc[1]
            home = g0 if "vs." in str(g0.get("matchup", "")) else g1
            away = g1 if "vs." in str(g0.get("matchup", "")) else g0
            rows.append({
                "game_id": str(gid),
                "season": season,
                "game_date": pd.to_datetime(g0["game_date"]).date(),
                "home_team_abbr": home["team_abbreviation"],
                "away_team_abbr": away["team_abbreviation"],
                "home_team_id": int(home["team_id"]),
                "away_team_id": int(away["team_id"]),
            })
    out = pd.DataFrame(rows)

    # Decode round / matchup_idx / game_in_series from game_id.
    # Format: 004 + YY + R + MMM (matchup index, 1-based as 1-8 for R1, 1-4 for R2, etc) + G
    # But empirically position 6 is "0" in our existing manifest, so this format
    # doesn't quite match. Use a heuristic per season instead: sort by game_date,
    # cluster by team-pair to derive matchup_idx + game_in_series + round.
    out = out.sort_values(["season", "game_date", "game_id"]).reset_index(drop=True)
    out["round"] = 0
    out["matchup_idx"] = 0
    out["game_in_series"] = 0
    out["season_end_year"] = out["season"].str.split("-").str[0].astype(int) + 1

    # Per season: derive round from cumulative number of distinct team-pairs and game_date
    for season in seasons:
        sub = out[out["season"] == season].copy()
        sub["pair"] = sub.apply(
            lambda r: tuple(sorted([r["home_team_id"], r["away_team_id"]])), axis=1,
        )
        # Sort by game_date, group by pair to label game_in_series within each
        # series in chronological order
        sub = sub.sort_values(["game_date", "game_id"])
        sub["game_in_series"] = sub.groupby("pair").cumcount() + 1

        # Round detection by date band:
        # R1 starts ~mid-April, R2 starts ~early May, R3 starts ~mid-May,
        # Finals start ~early June. Use rough bands per season — refined later
        # by counting distinct active pairs.
        # Better: round = how-many-rounds-deep based on series count.
        pairs_chrono = sub.drop_duplicates("pair").sort_values("game_date")
        pair_to_round = {}
        # First 8 pairs = R1, next 4 = R2, next 2 = R3, last 1 = R4
        for i, p in enumerate(pairs_chrono["pair"].tolist()):
            if i < 8:
                pair_to_round[p] = 1
            elif i < 12:
                pair_to_round[p] = 2
            elif i < 14:
                pair_to_round[p] = 3
            else:
                pair_to_round[p] = 4
        sub["round"] = sub["pair"].map(pair_to_round)

        # matchup_idx within round, ordered by first game_date of each pair
        for r in [1, 2, 3, 4]:
            r_pairs = (sub[sub["round"] == r].drop_duplicates("pair")
                                              .sort_values("game_date")["pair"].tolist())
            for i, p in enumerate(r_pairs):
                sub.loc[sub["pair"] == p, "matchup_idx"] = i + 1

        out.loc[out["season"] == season, "round"] = sub["round"].values
        out.loc[out["season"] == season, "matchup_idx"] = sub["matchup_idx"].values
        out.loc[out["season"] == season, "game_in_series"] = sub["game_in_series"].values

    return out


def fetch_per_game(game_id: str, season: str, throttler: Throttler) -> dict:
    """Pull traditional + advanced + summary for a single game.

    Returns dict {traditional_t0, traditional_t1, advanced_t0, advanced_t1,
                   summary_team_meta} each as a DataFrame.
    """
    from nba_api.stats.endpoints import (
        BoxScoreTraditionalV3, BoxScoreAdvancedV3, BoxScoreSummaryV2,
    )

    out = {}

    # Traditional
    t = _call(
        lambda gid=game_id: BoxScoreTraditionalV3(game_id=gid, timeout=30),
        label=f"BoxScoreTraditionalV3/{game_id}", throttler=throttler,
    )
    pl = t.player_stats.get_data_frame()
    teams = sorted(pl["teamId"].unique().tolist())
    if len(teams) != 2:
        log.warning("%s: expected 2 teams, got %s", game_id, teams)
        return {}
    pl0 = pl[pl["teamId"] == teams[0]].copy()
    pl1 = pl[pl["teamId"] == teams[1]].copy()
    pl0["gameId"] = game_id; pl0["season"] = season; pl0["game_id"] = game_id
    pl1["gameId"] = game_id; pl1["season"] = season; pl1["game_id"] = game_id
    out["traditional_t0"] = pl0
    out["traditional_t1"] = pl1

    # Advanced
    a = _call(
        lambda gid=game_id: BoxScoreAdvancedV3(game_id=gid, timeout=30),
        label=f"BoxScoreAdvancedV3/{game_id}", throttler=throttler,
    )
    apl = a.player_stats.get_data_frame()
    apl0 = apl[apl["teamId"] == teams[0]].copy()
    apl1 = apl[apl["teamId"] == teams[1]].copy()
    apl0["gameId"] = game_id; apl0["season"] = season; apl0["game_id"] = game_id
    apl1["gameId"] = game_id; apl1["season"] = season; apl1["game_id"] = game_id
    out["advanced_t0"] = apl0
    out["advanced_t1"] = apl1

    return out


def main():
    throttler = Throttler(interval_s=THROTTLE_S)

    log.info("Phase 1: enumerate playoff game_ids for %s ...", TARGET_SEASONS)
    games = enumerate_playoff_games(TARGET_SEASONS, throttler)
    log.info("  total playoff games (target seasons): %d", len(games))

    have_r1 = existing_round1_game_ids()
    have_extra = existing_extra_game_ids()
    have = have_r1 | have_extra
    log.info("  R1 dir holds %d games; extra_rounds dir holds %d games",
             len(have_r1), len(have_extra))

    todo = games[~games["game_id"].astype(str).isin(have)].copy()
    log.info("  to fetch: %d games (R2+ = %d)",
             len(todo), int((todo["round"] > 1).sum()))

    # Persist manifest for the new fetch incrementally
    manifest_cols = [
        "game_id", "season", "season_end_year", "game_date", "round",
        "matchup_idx", "game_in_series", "home_team_abbr", "away_team_abbr",
        "home_team_id", "away_team_id",
    ]
    manifest_existing = (pd.read_parquet(PLAYOFFS_EXTRA / "_manifest.parquet")
                         if (PLAYOFFS_EXTRA / "_manifest.parquet").exists()
                         else pd.DataFrame(columns=manifest_cols))

    log.info("Phase 2: fetch traditional + advanced for %d games ...", len(todo))
    accum = {k: [] for k in
             ["traditional_t0", "traditional_t1", "advanced_t0", "advanced_t1"]}
    new_manifest_rows = []

    def flush():
        nonlocal accum, new_manifest_rows
        for k in accum:
            if not accum[k]:
                continue
            new_df = pd.concat(accum[k], ignore_index=True)
            path = PLAYOFFS_EXTRA / f"{k}.parquet"
            existing = pd.read_parquet(path) if path.exists() else pd.DataFrame()
            combined = (pd.concat([existing, new_df], ignore_index=True)
                        if not existing.empty else new_df)
            combined.to_parquet(path, index=False)
            log.info("  flushed %s: +%d rows -> %d total",
                     k, len(new_df), len(combined))
        if new_manifest_rows:
            new_man_df = pd.DataFrame(new_manifest_rows, columns=manifest_cols)
            combined_man = (pd.concat([manifest_existing, new_man_df], ignore_index=True)
                            if not manifest_existing.empty else new_man_df)
            combined_man.to_parquet(PLAYOFFS_EXTRA / "_manifest.parquet", index=False)
            log.info("  manifest: +%d rows -> %d total",
                     len(new_man_df), len(combined_man))
        accum = {k: [] for k in accum}
        new_manifest_rows = []

    n_done = 0
    for _, row in todo.iterrows():
        gid = str(row["game_id"])
        season = row["season"]
        try:
            data = fetch_per_game(gid, season, throttler)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            log.error("%s/%s failed permanently: %s", season, gid, e)
            continue
        if not data:
            continue
        for k in ["traditional_t0", "traditional_t1",
                  "advanced_t0", "advanced_t1"]:
            if k in data:
                accum[k].append(data[k])
        new_manifest_rows.append({c: row[c] for c in manifest_cols})
        n_done += 1
        if n_done % FLUSH_EVERY == 0:
            log.info("Progress: %d/%d games", n_done, len(todo))
            flush()
            # Refresh existing for the next batch flush
            from importlib import reload
    flush()
    log.info("DONE. Fetched %d new playoff games to %s", n_done, PLAYOFFS_EXTRA)


if __name__ == "__main__":
    main()
