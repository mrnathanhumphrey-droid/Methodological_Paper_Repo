"""
Probe 2 — bulk PLR driver over the 5 viable PVCZ cells.
Resumable (skips system_ids already in the output CSV), thread-pooled I/O.

Usage:
  python code/probe2_run_bulk.py            # all 5 viable cells
  python code/probe2_run_bulk.py T5:H4      # one cell
  python code/probe2_run_bulk.py --workers 12
"""
import sys, json, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
from probe2_plr_pipeline import compute_plr

OUT = ROOT / "data/processed/probe2_plr_results.csv"
VIABLE = ["T3:H3", "T4:H3", "T5:H2", "T5:H3", "T5:H4"]
_lock = threading.Lock()


def main():
    args = [a for a in sys.argv[1:]]
    workers = 10
    if "--workers" in args:
        i = args.index("--workers"); workers = int(args[i + 1]); del args[i:i + 2]
    cells = [a for a in args if ":" in a] or VIABLE

    idx = pd.read_csv(ROOT / "data/raw/datasets/PVDAQ_systems_20250729.csv").iloc[:, :26].set_index("system_id")
    cohort = pd.read_csv(ROOT / "data/processed/probe2_cohort_p0.csv")
    cohort = cohort[cohort["P0_primary_TH"].isin(cells)]

    done = set()
    if OUT.exists():
        done = set(pd.read_csv(OUT)["system_id"].tolist())
    todo = [int(s) for s in cohort["system_id"] if int(s) not in done]
    print(f"Cells {cells}: {len(cohort)} systems, {len(done)} done, {len(todo)} to run, {workers} workers")

    def work(sid):
        row = idx.loc[sid]
        tilt = row["tilt"] if pd.notna(row["tilt"]) else min(abs(row["latitude"]), 30)
        az = row["azimuth"] if (pd.notna(row["azimuth"]) and row["azimuth"] >= 0) else 180
        try:
            return compute_plr(sid, float(row["latitude"]), float(row["longitude"]),
                               float(tilt), float(az), float(row["dc_capacity_kW"]))
        except Exception as e:
            return {"system_id": sid, "status": f"exc:{type(e).__name__}:{e}"}

    # fixed schema (union of all possible result keys) — avoids ragged CSV from heterogeneous dicts
    COLS = ["system_id", "status", "plr_pct_yr", "ci_low", "ci_high",
            "n_days", "n_years", "pi_median", "first", "last"]
    n_ok = n_err = 0
    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(work, sid): sid for sid in todo}
        for k, fut in enumerate(as_completed(futs), 1):
            res = fut.result()
            results.append(res)
            if res.get("status") == "ok":
                n_ok += 1
            else:
                n_err += 1
            if k % 25 == 0 or k == len(todo):
                print(f"  [{k}/{len(todo)}] ok={n_ok} other={n_err} last=sys{res['system_id']}:{res.get('status')} "
                      f"{('PLR=%.2f' % res['plr_pct_yr']) if res.get('status')=='ok' else ''}", flush=True)
    # single write with fixed columns (append-merge with any prior run)
    new = pd.DataFrame(results).reindex(columns=COLS)
    if OUT.exists():
        prev = pd.read_csv(OUT)
        new = pd.concat([prev.reindex(columns=COLS), new], ignore_index=True).drop_duplicates("system_id", keep="last")
    new.to_csv(OUT, index=False)
    print(f"DONE. ok={n_ok} other={n_err}. Results -> {OUT}")


if __name__ == "__main__":
    main()
