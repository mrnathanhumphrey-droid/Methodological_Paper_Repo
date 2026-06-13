"""Pure projection engine for the daily RS producer.

Implements Phase 1c LOCKED architecture (fire SHA `2a75b7d`,
pre-reg `4676342`):

  for player p, stat S, game with n_g prior games this season:
    if (S, bucket(n_g)) in SHIP_CELLS:
      proj = (n_g * rolling_emp + k * v61_per_game) / (n_g + k)
    else:
      proj = rolling_emp if n_g >= 1 else v61_per_game  # v6.1 fallback game 1

  bucket(n_g):
    B1 if n_g in [0, 9]
    B2 if [10, 24]
    B3 if [25, 49]
    B4 if >= 50

  SHIP_CELLS = {(PTS, B1), (REB, B1), (AST, B1)}
  k_S^B1     = {3.169 PTS, 3.362 REB, 3.233 AST}

Reads fitted k values from runs/run_nba_rs_phase_1c_22_25/shrinkage_k_v1_per_bucket.json.

Testable in isolation: no I/O beyond loading the k-map at init.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

ROOT = Path("D:/NBA Projections")
PHASE_1C_KMAP = ROOT / "runs/run_nba_rs_phase_1c_22_25/shrinkage_k_v1_per_bucket.json"
PHASE_1C_KMAP_USG = ROOT / "runs/run_nba_rs_phase_1c_22_25/shrinkage_k_v1_2_usg.json"
PHASE_1C_RMSE = ROOT / "runs/run_nba_rs_phase_1c_22_25/rmse_holdout_25_26_per_cell.csv"
PHASE_1C_BOOTSTRAP = ROOT / "runs/run_nba_rs_phase_1c_22_25/bootstrap_ci_per_cell.csv"

RAW_STATS = ("PTS", "REB", "AST", "BLK", "STL", "TOV", "FG3M")
RATE_STATS = ("USG",)  # rate stats: same shrinkage logic, NO MPG scaling at producer
PASSTHROUGH_STATS = ("FGM", "FGA", "FTM", "FTA", "FG3A")
ALL_STATS = RAW_STATS + RATE_STATS + PASSTHROUGH_STATS

BUCKETS = (
    ("B1_1-10", 0, 9),
    ("B2_11-25", 10, 24),
    ("B3_26-50", 25, 49),
    ("B4_51+", 50, 1_000_000),
)


def bucket_of(n_g: int) -> str:
    if n_g <= 9:
        return "B1_1-10"
    if n_g <= 24:
        return "B2_11-25"
    if n_g <= 49:
        return "B3_26-50"
    return "B4_51+"


class RSDailyProjector:
    """Holds the fitted k-map + per-cell hold-out RMSE + ship cells from v1.1."""

    def __init__(self):
        self.k_map: Dict[Tuple[str, str], float] = {}
        self.rmse_map: Dict[Tuple[str, str], float] = {}
        self.ship_cells: set = set()
        self.spec_version = "phase_1c_v1.2"
        self._load_kmap()
        self._load_rmse_map()
        self._load_ship_cells()

    def _load_kmap(self):
        pkg = json.loads(PHASE_1C_KMAP.read_text())
        for cell in pkg["cell_results"]:
            if "k_fit" in cell:
                self.k_map[(cell["stat"], cell["bucket"])] = float(cell["k_fit"])
        if PHASE_1C_KMAP_USG.exists():
            pkg_usg = json.loads(PHASE_1C_KMAP_USG.read_text())
            for bname, info in pkg_usg.get("buckets", {}).items():
                if "k_fit" in info:
                    self.k_map[("USG", bname)] = float(info["k_fit"])

    def _load_rmse_map(self):
        df = pd.read_csv(PHASE_1C_RMSE)
        for _, r in df.iterrows():
            self.rmse_map[(r["stat"], r["bucket"])] = float(r["RMSE_B"])

    def _load_ship_cells(self):
        """Read v1.1 bootstrap-CI ship cells from bootstrap_ci_per_cell.csv."""
        df = pd.read_csv(PHASE_1C_BOOTSTRAP)
        self.ship_cells = {
            (r["stat"], r["bucket"]) for _, r in df.iterrows()
            if r["ship_final"] == "B_v1.1"
        }

    def is_ship_cell(self, stat: str, n_g: int) -> bool:
        return (stat, bucket_of(n_g)) in self.ship_cells

    def project_single(self, *, stat: str, n_g: int,
                       rolling_emp: float, v61_per_game: float,
                       v61_sd: float) -> dict:
        """Project one (player × game × stat) row. Pure function."""
        bucket = bucket_of(n_g)
        ship = self.is_ship_cell(stat, n_g)
        if ship:
            k = self.k_map[(stat, bucket)]
            denom = n_g + k
            if denom == 0:
                proj = float(v61_per_game)
            else:
                proj = (n_g * rolling_emp + k * v61_per_game) / denom
            used_shrinkage = True
        else:
            if n_g == 0 or (rolling_emp is None or (isinstance(rolling_emp, float) and np.isnan(rolling_emp))):
                proj = float(v61_per_game)
            else:
                proj = float(rolling_emp)
            used_shrinkage = False

        proj = max(0.0, proj)

        sd = float(v61_sd) if v61_sd is not None and not (isinstance(v61_sd, float) and np.isnan(v61_sd)) else float("nan")
        rmse = self.rmse_map.get((stat, bucket), float("nan"))

        return {
            "projected_mean": proj,
            "projected_sd": sd,
            "model_rmse": rmse,
            "used_shrinkage": used_shrinkage,
            "bucket": bucket,
        }

    def project_passthrough(self, *, stat: str, v61_per_game: float,
                            v61_sd: float) -> dict:
        """M/A passthrough — no shrinkage applied. Used to derive % stats."""
        return {
            "projected_mean": max(0.0, float(v61_per_game)),
            "projected_sd": float(v61_sd) if v61_sd is not None and not (isinstance(v61_sd, float) and np.isnan(v61_sd)) else float("nan"),
            "model_rmse": float("nan"),
            "used_shrinkage": False,
            "bucket": "passthrough",
        }
