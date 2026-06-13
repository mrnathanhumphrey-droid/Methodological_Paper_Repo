"""Parquet directory watcher for fetcher landing detection.

Snapshots the state of D:\\NBA Projections\\data\\parquet\\ — file size,
mtime, row count, schema fingerprint per parquet. Diffs against last snapshot
to report new files, grown files, and any unexpected changes.

Usage:
    python scripts/parquet_watcher.py               # diff vs last snapshot
    python scripts/parquet_watcher.py --baseline    # reset baseline to current state
    python scripts/parquet_watcher.py --watch       # poll every N minutes (default 30)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO = Path(r"D:\NBA Projections")
PARQUET_DIR = REPO / "data" / "parquet"
STATE_FILE = REPO / "data" / "parquet_state_snapshot.json"


def fingerprint(p: Path) -> dict:
    stat = p.stat()
    info = {
        "path": str(p.relative_to(PARQUET_DIR)),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "mtime_human": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }
    if p.suffix == ".parquet" and stat.st_size > 0:
        try:
            df = pd.read_parquet(p)
            info["rows"] = int(len(df))
            cols_str = "|".join(sorted(df.columns.astype(str).tolist()))
            info["schema_hash"] = hashlib.md5(cols_str.encode()).hexdigest()[:8]
            info["columns"] = list(df.columns.astype(str))
        except Exception as e:
            info["error"] = f"read_failed: {e}"
    return info


def take_snapshot() -> dict:
    snap = {}
    for p in sorted(PARQUET_DIR.glob("**/*")):
        if p.is_file():
            try:
                snap[str(p.relative_to(PARQUET_DIR))] = fingerprint(p)
            except Exception as e:
                snap[str(p.relative_to(PARQUET_DIR))] = {"error": str(e)}
    return snap


def load_baseline() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_baseline(snap: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump({
            "captured_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "n_files": len(snap),
            "files": snap,
        }, f, indent=2)


def diff_snapshots(baseline: dict, current: dict) -> dict:
    base_files = set(baseline.get("files", {}).keys())
    curr_files = set(current.keys())

    new = sorted(curr_files - base_files)
    removed = sorted(base_files - curr_files)
    changed = []
    unchanged = []

    for path in sorted(curr_files & base_files):
        b = baseline["files"][path]
        c = current[path]
        if b.get("size") == c.get("size") and b.get("mtime") == c.get("mtime"):
            unchanged.append(path)
        else:
            entry = {"path": path}
            if b.get("size") != c.get("size"):
                entry["size_old"] = b.get("size")
                entry["size_new"] = c.get("size")
                entry["size_delta"] = c.get("size", 0) - b.get("size", 0)
            if b.get("rows") != c.get("rows"):
                entry["rows_old"] = b.get("rows")
                entry["rows_new"] = c.get("rows")
            if b.get("schema_hash") != c.get("schema_hash"):
                entry["schema_changed"] = True
                entry["columns_old"] = b.get("columns")
                entry["columns_new"] = c.get("columns")
            entry["mtime_new"] = c.get("mtime_human")
            changed.append(entry)
    return {"new": new, "removed": removed, "changed": changed, "unchanged_count": len(unchanged)}


def report(diff: dict, current: dict, baseline: dict) -> None:
    print(f"=== Parquet directory diff ({datetime.now().isoformat(timespec='seconds')}) ===")
    if baseline:
        print(f"Baseline: {baseline.get('captured_at_utc')}")
        print(f"Files in baseline: {baseline.get('n_files', 0)}")
    print(f"Files now: {len(current)}")
    print(f"Unchanged: {diff['unchanged_count']}")
    print()

    if diff["new"]:
        print(f"--- NEW ({len(diff['new'])}) ---")
        for path in diff["new"]:
            info = current[path]
            size_kb = info.get("size", 0) // 1024
            rows = info.get("rows", "—")
            cols = len(info.get("columns", [])) if info.get("columns") else "—"
            print(f"  + {path:<60s} {size_kb:>7d} KB  {rows} rows  {cols} cols")
        print()

    if diff["changed"]:
        print(f"--- CHANGED ({len(diff['changed'])}) ---")
        for entry in diff["changed"]:
            line = f"  ~ {entry['path']:<60s}"
            if "size_delta" in entry:
                delta = entry["size_delta"]
                sign = "+" if delta >= 0 else ""
                line += f" size {sign}{delta // 1024} KB"
            if "rows_new" in entry:
                old = entry.get("rows_old", "?")
                new = entry.get("rows_new", "?")
                line += f"  rows {old} -> {new}"
            if entry.get("schema_changed"):
                line += "  [SCHEMA CHANGED]"
            print(line)
        print()

    if diff["removed"]:
        print(f"--- REMOVED ({len(diff['removed'])}) ---")
        for path in diff["removed"]:
            print(f"  - {path}")
        print()

    if not diff["new"] and not diff["changed"] and not diff["removed"]:
        print("No changes since last baseline.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--baseline", action="store_true",
                   help="Reset baseline to current state (don't diff)")
    p.add_argument("--watch", action="store_true",
                   help="Poll every N minutes")
    p.add_argument("--interval", type=int, default=30,
                   help="Polling interval in minutes (with --watch)")
    args = p.parse_args()

    if args.watch:
        print(f"Watching {PARQUET_DIR} every {args.interval} min. Ctrl-C to stop.")
        while True:
            current = take_snapshot()
            baseline = load_baseline()
            diff = diff_snapshots(baseline, current)
            if diff["new"] or diff["changed"] or diff["removed"]:
                report(diff, current, baseline)
                save_baseline(current)
                print()
            time.sleep(args.interval * 60)
        return

    current = take_snapshot()
    if args.baseline or not STATE_FILE.exists():
        save_baseline(current)
        print(f"Baseline saved: {len(current)} files captured.")
        return

    baseline = load_baseline()
    diff = diff_snapshots(baseline, current)
    report(diff, current, baseline)
    save_baseline(current)


if __name__ == "__main__":
    main()
