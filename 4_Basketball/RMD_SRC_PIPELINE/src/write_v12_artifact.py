"""
Read the v1.2 adjudication workflow output, persist the locked verdicts
artifact, and emit the diagnostic.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

WORKFLOW_OUT = Path(
    r"C:/Users/Nate/AppData/Local/Temp/claude/c--As-Above-So-Below-Master/"
    r"bff85813-d24e-404f-a28d-18647b4045be/tasks/w5pnptkwh.output"
)
# The actual path from the notification (one-off literal):
WORKFLOW_OUT = Path(
    r"C:/Users/Nate/AppData/Local/Temp/claude/c--As-Above-So-Below-Master/"
    r"bff85813-d24e-43ac-bed2-41c96a296123/tasks/w5pnptkwh.output"
)

# Try a few candidate locations (session UUID varies).
TASKS_DIR = Path(r"C:/Users/Nate/AppData/Local/Temp/claude/c--As-Above-So-Below-Master")
CANDIDATES = list(TASKS_DIR.rglob("w5pnptkwh.output"))

RESULTS = Path(r"D:/NBA Projections/RMD_SRC_PIPELINE/results")
OUT_JSON = RESULTS / "position_adjudication_v12.json"
DIAG = RESULTS / "adjudication_v12_diagnostic.md"


def main() -> int:
    if not CANDIDATES:
        sys.exit(f"No workflow output found under {TASKS_DIR}")
    src = CANDIDATES[0]
    print(f"Reading workflow output: {src}")
    envelope = json.loads(src.read_text(encoding="utf-8"))
    # Workflow envelope wraps the script return under `result`.
    raw = envelope.get("result", envelope)
    verdicts = raw["verdicts"]
    print(f"  n_total: {raw['n_total']}")
    print(f"  n_success: {raw['n_success']}")
    print(f"  n_failed: {raw['n_failed']}")
    print(f"  bucket_counts: {raw['bucket_counts']}")

    # Write the locked artifact (v1.2 §2.5).
    payload = {
        "locked_at_sha_v12": "1bfdb4c0dfa2b3754f67e9c2f91b2ab26fa01866",
        "n_total": raw["n_total"],
        "n_success": raw["n_success"],
        "n_failed": raw["n_failed"],
        "bucket_counts": raw["bucket_counts"],
        "verdicts": verdicts,
    }
    body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    OUT_JSON.write_bytes(body)
    sha = hashlib.sha256(body).hexdigest()
    print(f"\n  -> {OUT_JSON.name}  ({len(body):,} bytes)")
    print(f"  content SHA256: {sha}")

    manifest = RESULTS / "MANIFEST.txt"
    manifest.parent.mkdir(exist_ok=True)
    with manifest.open("a", encoding="utf-8") as f:
        f.write(f"{sha}  position_adjudication_v12.json  (v1.2 locked, 1bfdb4c)\n")

    # Diagnostic: how many verdicts changed the bucket vs metadata, confidence dist,
    # named flip examples.
    n_changed = sum(1 for v in verdicts
                     if v["adjudicated_bucket"] != v["metadata_bucket_v1"])
    n_unchanged = len(verdicts) - n_changed

    flip_matrix = Counter()
    for v in verdicts:
        if v["adjudicated_bucket"] != v["metadata_bucket_v1"]:
            flip_matrix[(v["metadata_bucket_v1"], v["adjudicated_bucket"])] += 1

    conf_dist = Counter(v["confidence"] for v in verdicts)
    conf_dist_flipped = Counter(v["confidence"] for v in verdicts
                                  if v["adjudicated_bucket"] != v["metadata_bucket_v1"])

    raw_dist = Counter(v["raw_assignment"] for v in verdicts)

    lines = [
        "# v1.2 adjudication diagnostic\n",
        f"Locked v1.2 SHA: `1bfdb4c0dfa2b3754f67e9c2f91b2ab26fa01866`",
        f"Verdicts artifact SHA256: `{sha}`",
        "",
        "## Headline",
        f"- Total adjudication targets: **{raw['n_total']}**",
        f"- Successful verdicts: **{raw['n_success']}**",
        f"- Failed verdicts (route to v1.0 metadata bucket): **{raw['n_failed']}**",
        f"- **Positionless (no_fit)** verdicts: **{raw_dist.get('no_fit', 0)}**",
        "",
        "## Final bucket distribution",
        f"- Center: {raw['bucket_counts'].get('Center', 0)}",
        f"- Forward: {raw['bucket_counts'].get('Forward', 0)}",
        f"- Guard: {raw['bucket_counts'].get('Guard', 0)}",
        f"- Positionless: {raw['bucket_counts'].get('Positionless', 0)}",
        "",
        "## Metadata vs adjudicated agreement",
        f"- Unchanged (adjudicator confirmed metadata bucket): {n_unchanged}",
        f"- Changed (adjudicator overrode metadata): {n_changed}",
        f"- Override rate: {100*n_changed/len(verdicts):.1f}%",
        "",
        "## Flip matrix (metadata -> adjudicated)",
        "| metadata | adjudicated | count |",
        "|---|---|---|",
    ]
    for (m, a), n in sorted(flip_matrix.items(), key=lambda x: -x[1]):
        lines.append(f"| {m} | {a} | {n} |")

    lines += ["", "## Confidence distribution (overall)",
              "| confidence | count | % |", "|---|---|---|"]
    for c in ["high", "medium", "low"]:
        n = conf_dist.get(c, 0)
        pct = 100 * n / max(1, len(verdicts))
        lines.append(f"| {c} | {n} | {pct:.1f}% |")

    lines += ["", "## Confidence distribution (flipped verdicts only)",
              "| confidence | count | % of flips |", "|---|---|---|"]
    for c in ["high", "medium", "low"]:
        n = conf_dist_flipped.get(c, 0)
        pct = 100 * n / max(1, n_changed)
        lines.append(f"| {c} | {n} | {pct:.1f}% |")

    # Named examples per flip type.
    flips_per_type: dict = {}
    for v in verdicts:
        if v["adjudicated_bucket"] != v["metadata_bucket_v1"]:
            key = f"{v['metadata_bucket_v1']} -> {v['adjudicated_bucket']}"
            flips_per_type.setdefault(key, []).append(v)

    lines += ["", "## Named flip examples (up to 8 per flip type)"]
    for key, vs in sorted(flips_per_type.items(), key=lambda x: -len(x[1])):
        lines.append(f"\n### {key} (n={len(vs)})")
        lines.append("| player | confidence | rationale (clipped) |")
        lines.append("|---|---|---|")
        for v in vs[:8]:
            rat = v["rationale"].replace("\n", " ").replace("|", "/")
            if len(rat) > 180:
                rat = rat[:177] + "..."
            lines.append(f"| {v['name']} | {v['confidence']} | {rat} |")

    DIAG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  -> {DIAG.name}")
    print()
    print(f"Override rate: {n_changed}/{len(verdicts)} = {100*n_changed/len(verdicts):.1f}%")
    print(f"Flip matrix: {dict(flip_matrix)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
