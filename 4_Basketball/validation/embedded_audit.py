"""Embedded continuous-audit harness.

Per spec §5.5 + 2026-04-25 amendment §C, this module runs after every
meaningful model change and produces:
  - per-component validation against held-out seasons
  - per-archetype accuracy
  - Bayesian-specific diagnostics (R-hat, ESS, posterior predictive checks,
    prior sensitivity, calibration curves)
  - Bayesian vs ML disagreement tracking
  - beat-the-baseline comparisons against Wonka's audit data
  - **NEW (amendment §C):** projection vs. historical advanced-metric
    disagreement detection — flags players where projection disagrees with
    BOTH actuals AND advanced-metric expectations as systematic blind spots

Phase 1 deliverable: the scaffolding (directory layout, run-id schema, the
shape of the report). Real components plug in during Phases 2-6.

Output goes to `audit_runs/{timestamp}/` with the layout:
  per_component_metrics.csv
  per_archetype_metrics.csv
  bayesian_diagnostics.json
  vs_baseline_comparison.csv
  vs_ml_parallel_comparison.csv
  vs_advanced_metrics.csv          # NEW (amendment §C)
  archetype_blind_spots.md         # NEW (amendment §C)
  prior_sensitivity_report.md
  posterior_predictive_checks/  (plots — Phase 2+)
  summary.md
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from pydantic import BaseModel, Field

from config.paths import AUDIT_RUNS_DIR


logger = logging.getLogger(__name__)


# Pass-gate thresholds from spec §5.5.3 + amendment §C.
COMPONENT_REGRESSION_THRESHOLD: float = 0.10
CALIBRATION_TOLERANCE: float = 0.15
ADV_METRIC_BLIND_SPOT_FRACTION_LIMIT: float = 0.05  # >5% of universe = FAIL


class AdvMetricDisagreement(BaseModel):
    """One player's disagreement profile: projection vs. actuals vs. advanced
    metrics. Used by the §C audit dimension."""
    nba_api_id: int
    player_name: str
    category: str
    projected_mean: float
    actual_mean: float
    advanced_metric_implied_mean: float
    proj_vs_actual_z: float           # standardized residual: (proj - actual) / proj_stddev
    proj_vs_adv_z: float
    actual_vs_adv_z: float
    blind_spot: bool                  # True if proj disagrees with BOTH actuals AND adv metric


class AuditRun(BaseModel):
    """One full audit cycle. Created by `start_audit_run`, populated by
    component-level callers, finalized by `write_summary`."""
    run_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    components_run: list[str] = Field(default_factory=list)
    pass_gates: dict[str, bool] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    adv_metric_blind_spots: list[AdvMetricDisagreement] = Field(default_factory=list)

    @property
    def root(self) -> Path:
        return AUDIT_RUNS_DIR / self.run_id

    def passed(self) -> bool:
        """Hard gates per spec §5.5.3 + amendment §C. Phase 1: only the
        structural gates exist. Real metrics arrive in Phase 2 onward."""
        return all(self.pass_gates.values()) if self.pass_gates else True


def start_audit_run() -> AuditRun:
    AUDIT_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run = AuditRun(run_id=run_id, started_at=datetime.now(timezone.utc))
    run.root.mkdir(parents=True, exist_ok=True)
    logger.info("Audit run started: %s", run.root)
    return run


# ── Advanced-metric disagreement (amendment §C) ──────────────────


def detect_blind_spots(
    disagreements: list[AdvMetricDisagreement],
    z_threshold: float = 1.5,
) -> list[AdvMetricDisagreement]:
    """Flag the subset where projection disagrees with BOTH actuals and
    advanced-metric expectations beyond `z_threshold`. These are the
    systematic blind spots of the model — its projection is wrong relative
    to two independent reality checks."""
    out: list[AdvMetricDisagreement] = []
    for d in disagreements:
        if abs(d.proj_vs_actual_z) > z_threshold and abs(d.proj_vs_adv_z) > z_threshold:
            d.blind_spot = True
            out.append(d)
    return out


def write_adv_metric_audit(
    run: AuditRun,
    disagreements: list[AdvMetricDisagreement],
) -> tuple[Path, Path]:
    """Write the new amendment-§C outputs. Returns (csv_path, md_path)."""
    csv_path = run.root / "vs_advanced_metrics.csv"
    md_path = run.root / "archetype_blind_spots.md"

    if disagreements:
        rows = [d.model_dump(mode="python") for d in disagreements]
        pd.DataFrame(rows).to_csv(csv_path, index=False)
    else:
        # Header-only file so downstream consumers can always read
        pd.DataFrame(columns=list(AdvMetricDisagreement.model_fields.keys())).to_csv(
            csv_path, index=False,
        )

    blind = [d for d in disagreements if d.blind_spot]
    universe_size = len({d.nba_api_id for d in disagreements}) or 1
    blind_fraction = len({d.nba_api_id for d in blind}) / universe_size

    lines = [
        "# Archetype blind spots",
        "",
        f"Universe size: {universe_size} players × {len({d.category for d in disagreements})} categories",
        f"Blind-spot rows (disagreement on BOTH actuals and adv metrics): {len(blind)}",
        f"Blind-spot fraction (unique players): {blind_fraction:.2%}",
        f"Pass threshold: ≤ {ADV_METRIC_BLIND_SPOT_FRACTION_LIMIT:.0%}",
        f"Status: {'PASS' if blind_fraction <= ADV_METRIC_BLIND_SPOT_FRACTION_LIMIT else 'FAIL'}",
        "",
    ]
    if blind:
        # Group by player to avoid spamming one player's many cats
        by_player: dict[int, list[AdvMetricDisagreement]] = {}
        for d in blind:
            by_player.setdefault(d.nba_api_id, []).append(d)
        lines.append("## Top blind-spot players")
        lines.append("")
        for pid, ds in sorted(by_player.items(), key=lambda kv: -len(kv[1]))[:25]:
            ds_sorted = sorted(ds, key=lambda d: -abs(d.proj_vs_actual_z))
            lead = ds_sorted[0]
            lines.append(f"### {lead.player_name} (id {pid})")
            for d in ds_sorted:
                lines.append(
                    f"- {d.category}: proj={d.projected_mean:.2f} "
                    f"actual={d.actual_mean:.2f} adv_implied={d.advanced_metric_implied_mean:.2f} "
                    f"(z_actual={d.proj_vs_actual_z:+.2f}, z_adv={d.proj_vs_adv_z:+.2f})"
                )
            lines.append("")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Register pass gate
    run.pass_gates["adv_metric_blind_spots"] = (
        blind_fraction <= ADV_METRIC_BLIND_SPOT_FRACTION_LIMIT
    )
    run.adv_metric_blind_spots = blind
    run.metrics["adv_metric_blind_spot_fraction"] = blind_fraction

    logger.info(
        "Adv-metric audit: %d disagreements, %d blind-spot rows (%.1f%% of players); %s",
        len(disagreements), len(blind), blind_fraction * 100,
        "PASS" if run.pass_gates["adv_metric_blind_spots"] else "FAIL",
    )
    return csv_path, md_path


def write_summary(run: AuditRun) -> Path:
    """Write run.summary.md and the JSON dump. Returns the summary path."""
    run.ended_at = datetime.now(timezone.utc)
    summary_path = run.root / "summary.md"
    json_path = run.root / "run.json"

    lines: list[str] = [
        f"# Audit run {run.run_id}",
        "",
        f"- Started: {run.started_at.isoformat()}",
        f"- Ended: {run.ended_at.isoformat()}",
        f"- Components: {', '.join(run.components_run) or '(none)'}",
        f"- Overall: {'PASS' if run.passed() else 'FAIL'}",
        "",
        "## Pass gates",
    ]
    if run.pass_gates:
        for gate, passed in run.pass_gates.items():
            lines.append(f"- {'✓' if passed else '✗'} {gate}")
    else:
        lines.append("- (none registered yet — Phase 1 scaffolding)")
    if run.metrics:
        lines += ["", "## Metrics", "```", str(run.metrics), "```"]
    if run.notes:
        lines += ["", "## Notes", *(f"- {n}" for n in run.notes)]

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(run.model_dump_json(indent=2), encoding="utf-8")
    logger.info("Audit summary: %s", summary_path)
    return summary_path
