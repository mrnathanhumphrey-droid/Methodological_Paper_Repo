"""Merge per-chunk workflow output JSONs into per-league
position_adjudication_v10.json artifacts.

Inputs per league:
- WNBA: 1 chunk → wnba_chunk0_verdicts.raw.json
- NCAA M: 3 chunks → ncaa_m_chunk{0,1,2}_verdicts.raw.json
- NCAA W: 2 chunks → ncaa_w_chunk{0,1}_verdicts.raw.json

Output: per-league `<league>_position_adjudication_v10.json` matching the
NBA v1.2 artifact shape, plus a SHA256 fingerprint written to a sidecar
.sha256 file (recorded in `SHA_LOCK.txt` later).

Per pre-reg SHA 28e3dc7.
"""
import hashlib
import json
import sys
from pathlib import Path

CONFIG = {
    "WNBA": {
        "in_dir": Path("C:/WNBA Projections/audit_runs/test_1_replication/sloan_adjudicated"),
        "raw_files": ["wnba_chunk0_verdicts.raw.json"],
        "canonical_path": Path("C:/WNBA Projections/audit_runs/test_1_replication/sloan_adjudicated/wnba_position_adjudication_v10.json"),
        "pre_reg_sha": "28e3dc7",
    },
    "NCAA_M": {
        "in_dir": Path("C:/NCAA D1 Mens/audit_runs/test_1_replication/sloan_adjudicated"),
        "raw_files": [f"ncaa_m_chunk{i}_verdicts.raw.json" for i in range(3)],
        "canonical_path": Path("C:/NCAA D1 Mens/audit_runs/test_1_replication/sloan_adjudicated/ncaa_m_position_adjudication_v10.json"),
        "pre_reg_sha": "28e3dc7",
    },
    "NCAA_W": {
        "in_dir": Path("C:/NCAA D1 Womens/audit_runs/test_1_replication/sloan_adjudicated"),
        "raw_files": [f"ncaa_w_chunk{i}_verdicts.raw.json" for i in range(2)],
        "canonical_path": Path("C:/NCAA D1 Womens/audit_runs/test_1_replication/sloan_adjudicated/ncaa_w_position_adjudication_v10.json"),
        "pre_reg_sha": "28e3dc7",
    },
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in CONFIG:
        print("Usage: python merge_cross_league_verdicts.py {WNBA|NCAA_M|NCAA_W}")
        sys.exit(1)

    league = sys.argv[1]
    cfg = CONFIG[league]
    cfg["in_dir"].mkdir(parents=True, exist_ok=True)

    all_verdicts = []
    chunk_summary = []
    for fname in cfg["raw_files"]:
        path = cfg["in_dir"] / fname
        if not path.exists():
            print(f"MISSING: {path}")
            sys.exit(2)
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        # The task output is a JSON envelope; the actual workflow return is under "result"
        result = raw.get("result", raw)
        verdicts = result.get("verdicts", [])
        chunk_idx = result.get("chunk_idx", "?")
        chunk_total = result.get("chunk_total", "?")
        n_total = result.get("n_total", len(verdicts))
        n_success = result.get("n_success", sum(1 for v in verdicts if v.get("verdict") is not None))
        n_failed = result.get("n_failed", n_total - n_success)
        bucket_counts = result.get("bucket_counts", {})
        chunk_summary.append({
            "file": fname,
            "chunk_idx": chunk_idx,
            "chunk_total": chunk_total,
            "n_total": n_total,
            "n_success": n_success,
            "n_failed": n_failed,
            "bucket_counts": bucket_counts,
        })
        all_verdicts.extend(verdicts)
        print(f"  loaded {fname}: chunk {chunk_idx}/{chunk_total}, {n_success}/{n_total} success, buckets={bucket_counts}")

    # Normalize verdicts: each entry becomes a single flat object
    normalized = []
    flip_count = 0
    flip_examples = []
    for entry in all_verdicts:
        prof = entry.get("profile", {})
        v = entry.get("verdict")
        if v is None:
            # Agent failure — route to metadata bucket per pre-reg discipline guard #8
            adjudicated_bucket = prof.get("metadata_bucket_inclusive", "non-Center")
            confidence = "agent_failure"
            rationale = entry.get("agent_failure_reason", "verdict was null")
            no_fit_reason = ""
            assignment = "agent_failure"
        else:
            assignment = v.get("assignment")
            confidence = v.get("confidence")
            rationale = v.get("rationale", "")
            no_fit_reason = v.get("no_fit_reason", "")
            # Map agent assignment -> adjudicated bucket
            if assignment == "no_fit":
                adjudicated_bucket = "Positionless"
            elif assignment in ("Center", "Forward", "Guard"):
                adjudicated_bucket = assignment
            else:
                adjudicated_bucket = prof.get("metadata_bucket_inclusive", "non-Center")

        # Flag flips: metadata Center vs adjudicated non-Center, or vice versa
        metadata_bucket = prof.get("metadata_bucket_inclusive", "non-Center")
        is_center_meta = metadata_bucket == "Center"
        is_center_adj = adjudicated_bucket == "Center"
        if is_center_meta != is_center_adj:
            flip_count += 1
            if len(flip_examples) < 10:
                flip_examples.append({
                    "name": prof.get("name"),
                    "metadata_bucket": metadata_bucket,
                    "adjudicated_bucket": adjudicated_bucket,
                    "metadata_position": prof.get("metadata_position"),
                    "height_inches": prof.get("height_inches"),
                })

        normalized.append({
            "name": prof.get("name"),
            "player_slug": prof.get("player_slug"),
            "metadata_position": prof.get("metadata_position"),
            "metadata_bucket_inclusive": metadata_bucket,
            "height_inches": prof.get("height_inches"),
            "assignment": assignment,
            "adjudicated_bucket": adjudicated_bucket,
            "confidence": confidence,
            "rationale": rationale,
            "no_fit_reason": no_fit_reason,
        })

    # Aggregate bucket counts
    bucket_counts = {}
    for n in normalized:
        b = n["adjudicated_bucket"]
        bucket_counts[b] = bucket_counts.get(b, 0) + 1

    print(f"\n{league} merged: {len(normalized)} verdicts total")
    print(f"  bucket counts: {bucket_counts}")
    print(f"  metadata->adjudicated Center-side flips: {flip_count}")
    if flip_examples:
        print(f"  flip examples (first 10):")
        for ex in flip_examples:
            print(f"    {ex['name']} ({ex['metadata_position']}, {ex['height_inches']}\") "
                  f"{ex['metadata_bucket']} -> {ex['adjudicated_bucket']}")

    out = {
        "league": league,
        "pre_reg_sha": cfg["pre_reg_sha"],
        "n_verdicts": len(normalized),
        "bucket_counts": bucket_counts,
        "center_flip_count": flip_count,
        "chunk_summary": chunk_summary,
        "verdicts": normalized,
    }

    canonical_path = cfg["canonical_path"]
    with open(canonical_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {canonical_path}")

    # SHA256 of canonical artifact
    with open(canonical_path, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest()
    sidecar = canonical_path.with_suffix(canonical_path.suffix + ".sha256")
    sidecar.write_text(h + "\n", encoding="utf-8")
    print(f"SHA256: {h}")
    print(f"Wrote {sidecar}")


if __name__ == "__main__":
    main()
