"""
RMD-SRC Step 0 — build the exogenous demographic partition ℙ₀.

Per PRE_REG v1.0 §2.4 / §3.1 and v1.1 amendment:
  - Scope: ACS 2012-2021 (single 2010-vintage PUMA era), AGE>=18, GQ in {1,2,5}
  - Event: cross-PUMA migration = MIGRATE1D in {24, 31, 32}
      24 = different house, within state, between PUMAs
      31/32 = different state (contiguous / non-contiguous)
    Excluded: 10 same house, 23 within-PUMA (not an event), 40 abroad (immigration, v2)
  - ℙ₀ cell = age_bin x income_bin x family_bin x educ_bin (48 raw cells)
      age:    18-29 / 30-44 / 45-59 / 60+
      income: within-year person-weighted HHINCOME tertiles (bottom/mid/top third)
      family: with-children (NCHILD>0) / without
      educ:   BA+ (EDUCD>=101) / less-than-BA
  - Collapse rule (n<500 events/yr -> merge nearest neighbor by age then income)
    is applied in 'finalize' mode only, after inspecting counts.

Modes:
  diagnose (default): derive bins, report 48-cell event counts per year +
                      income-N/A rate + scope tallies. No files written.
  finalize:           apply collapse map, write P0_partition.parquet,
                      freeze SHA256 to prereg/P0_hash.txt.

The partition is the pre-registration anchor: it depends only on demographics
and event-counts, NOT on the observable outcomes (distance/density/opportunity),
so building it does not violate the "lock before outcome statistics" rule.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd

GZ = Path(r"D:\Migration\data\raw\ipums\usa_00001.csv.gz")
DERIVED = Path(r"D:\Migration\data\derived")
COLS = ["YEAR", "SERIAL", "PERNUM", "PERWT", "STATEFIP", "PUMA", "GQ", "AGE",
        "MARST", "NCHILD", "EDUCD", "HHINCOME", "MIGRATE1D", "MIGPLAC1", "MIGPUMA1"]

EVENT_CODES = {24, 31, 32}     # cross-PUMA migration
HHINCOME_NA = 9999999
YEAR_MIN, YEAR_MAX = 2012, 2021  # v1.1 single-vintage locked scope
AGE_BINS = [18, 30, 45, 60, np.inf]
AGE_LABELS = ["18-29", "30-44", "45-59", "60+"]


def weighted_tertile_edges(vals: np.ndarray, wts: np.ndarray) -> tuple[float, float]:
    """Person-weighted 1/3 and 2/3 cut points."""
    order = np.argsort(vals)
    v = vals[order]
    w = wts[order]
    cw = np.cumsum(w)
    total = cw[-1]
    t1 = v[np.searchsorted(cw, total / 3.0)]
    t2 = v[np.searchsorted(cw, 2.0 * total / 3.0)]
    return float(t1), float(t2)


def load_scope() -> pd.DataFrame:
    df = pd.read_csv(GZ, usecols=COLS)
    n_all = len(df)
    df = df[(df.YEAR >= YEAR_MIN) & (df.YEAR <= YEAR_MAX)
            & (df.AGE >= 18) & (df.GQ.isin([1, 2, 5]))].copy()
    print(f"rows all-years: {n_all:,}  ->  locked scope {YEAR_MIN}-{YEAR_MAX}, age>=18, hh: {len(df):,}")
    return df


def derive_bins(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df["age_bin"] = pd.cut(df.AGE, bins=AGE_BINS, labels=AGE_LABELS, right=False)

    df["family_bin"] = np.where(df.NCHILD > 0, "kids", "nokids")
    df["educ_bin"] = np.where(df.EDUCD >= 101, "BA+", "<BA")

    # income: within-year person-weighted HHINCOME tertiles; N/A held out
    valid = df.HHINCOME != HHINCOME_NA
    na_rate = 1.0 - valid.mean()
    print(f"HHINCOME N/A rate in scope: {100*na_rate:.3f}%  ({(~valid).sum():,} rows)")
    df["income_bin"] = pd.Series(pd.NA, index=df.index, dtype="object")
    edges = {}
    for yr, g in df[valid].groupby("YEAR"):
        t1, t2 = weighted_tertile_edges(g.HHINCOME.to_numpy(float), g.PERWT.to_numpy(float))
        inc = g.HHINCOME.to_numpy(float)
        b = np.where(inc <= t1, "inc_lo", np.where(inc <= t2, "inc_mid", "inc_hi"))
        df.loc[g.index, "income_bin"] = b
        edges[int(yr)] = {"t1": t1, "t2": t2}
        print(f"  {yr} income tertile edges: ${t1:,.0f} / ${t2:,.0f}")

    df["is_event"] = df.MIGRATE1D.isin(EVENT_CODES)
    df["raw_cell"] = (df.age_bin.astype(str) + "|" + df.income_bin.astype(str)
                      + "|" + df.family_bin + "|" + df.educ_bin)
    return df, edges


# ---- v1.2 locked collapse algorithm ------------------------------------
INC_LABELS = ["inc_lo", "inc_mid", "inc_hi"]
AGE_IDX = {l: i for i, l in enumerate(AGE_LABELS)}
INC_IDX = {l: i for i, l in enumerate(INC_LABELS)}
COLLAPSE_FLOOR = 500


def _adjacent(pairs_a: set, pairs_b: set, axis: str) -> bool:
    """True if some raw (age,inc) pair in A is grid-adjacent to one in B along `axis`."""
    for (aa, ai) in pairs_a:
        for (ba, bi) in pairs_b:
            if axis == "age" and ai == bi and abs(aa - ba) == 1:
                return True
            if axis == "income" and aa == ba and abs(ai - bi) == 1:
                return True
    return False


def collapse_block(block_counts: dict, years: list[int]) -> list[set]:
    """
    block_counts: {(age_idx, inc_idx): np.array over years} event counts.
    Returns list of cells; each cell is a set of (age_idx, inc_idx) raw pairs.
    Deterministic agglomerative merge, age-adjacency preferred over income.
    """
    cells = [{p} for p in block_counts]  # singletons

    def minyear(cell):
        tot = np.zeros(len(years))
        for p in cell:
            tot += block_counts[p]
        return int(tot.min())

    def sort_key(cell):
        ages = sorted(a for a, _ in cell)
        incs = sorted(i for _, i in cell)
        return (minyear(cell), ages[0], incs[0])

    while True:
        sparse = [c for c in cells if minyear(c) < COLLAPSE_FLOOR]
        if not sparse:
            break
        target = min(sparse, key=sort_key)
        others = [c for c in cells if c is not target]
        age_adj = [c for c in others if _adjacent(target, c, "age")]
        pool = age_adj if age_adj else [c for c in others if _adjacent(target, c, "income")]
        partner = min(pool, key=sort_key)
        cells = [c for c in cells if c is not target and c is not partner]
        cells.append(target | partner)
    return cells


def _span_label(pairs: set) -> str:
    ages = sorted({a for a, _ in pairs})
    incs = sorted({i for _, i in pairs})
    age_s = "∪".join(AGE_LABELS[a] for a in ages)
    inc_s = "∪".join(INC_LABELS[i] for i in incs)
    return f"{age_s} | {inc_s}"


def build_collapse_map(df: pd.DataFrame, years: list[int]):
    """Returns (raw_cell -> cell_id dict, definitions list)."""
    ev = df[df.is_event & df.income_bin.notna()]
    raw2cid = {}
    definitions = []
    cid_n = 0
    for (fam, edu), _ in df.groupby(["family_bin", "educ_bin"]):
        block = ev[(ev.family_bin == fam) & (ev.educ_bin == edu)]
        bc = {}
        for (a, i), g in block.groupby(["age_bin", "income_bin"], observed=True):
            arr = g.groupby("YEAR").size().reindex(years, fill_value=0).to_numpy(float)
            bc[(AGE_IDX[str(a)], INC_IDX[str(i)])] = arr
        # ensure all 12 raw combos exist (zero if absent)
        for a in range(len(AGE_LABELS)):
            for i in range(len(INC_LABELS)):
                bc.setdefault((a, i), np.zeros(len(years)))
        cells = collapse_block(bc, years)
        for cell in cells:
            cid_n += 1
            cid = f"C{cid_n:02d}"
            tot = np.zeros(len(years))
            for p in cell:
                tot += bc[p]
            for (a, i) in cell:
                raw = f"{AGE_LABELS[a]}|{INC_LABELS[i]}|{fam}|{edu}"
                raw2cid[raw] = cid
            definitions.append({
                "cell_id": cid, "family": fam, "educ": edu,
                "span": _span_label(cell),
                "raw_members": sorted(f"{AGE_LABELS[a]}|{INC_LABELS[i]}" for a, i in cell),
                "n_raw_cells": len(cell),
                "total_events": int(tot.sum()),
                "min_year_events": int(tot.min()),
            })
    return raw2cid, definitions


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def finalize(df: pd.DataFrame, edges: dict):
    df = df[df.income_bin.notna()].copy()
    years = sorted(int(y) for y in df.YEAR.unique())
    raw2cid, definitions = build_collapse_map(df, years)

    df["cell_id"] = df.raw_cell.map(raw2cid)
    assert df.cell_id.notna().all(), "unmapped raw_cell"

    DERIVED.mkdir(parents=True, exist_ok=True)
    keep = ["YEAR", "SERIAL", "PERNUM", "PERWT", "STATEFIP", "PUMA",
            "MIGPLAC1", "MIGPUMA1", "age_bin", "income_bin", "family_bin",
            "educ_bin", "raw_cell", "cell_id", "is_event"]
    out = df[keep].copy()
    out["age_bin"] = out["age_bin"].astype(str)
    pq = DERIVED / "P0_partition.parquet"
    out.to_parquet(pq, index=False)

    k = len(definitions)
    n_events = int(df.is_event.sum())
    defs = {
        "built_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scope": {"years": years, "age_min": 18, "gq": [1, 2, 5]},
        "event_codes_MIGRATE1D": sorted(EVENT_CODES),
        "collapse_floor_events_per_year": COLLAPSE_FLOOR,
        "income_tertile_edges_by_year": edges,
        "n_species": k,
        "n_persons": int(len(out)),
        "n_events": n_events,
        "cells": sorted(definitions, key=lambda d: d["cell_id"]),
    }
    defs_path = DERIVED / "P0_cell_definitions.json"
    defs_path.write_text(json.dumps(defs, indent=2, ensure_ascii=False), encoding="utf-8")

    digest = sha256_of(pq)
    print(f"\nℙ₀ built: {k} species, {len(out):,} persons, {n_events:,} events")
    print(f"partition: {pq}")
    print(f"definitions: {defs_path}")
    print(f"SHA256(P0_partition.parquet) = {digest}")

    print(f"\nspecies summary (sorted by min/yr events):")
    print(f"{'cell_id':<7} {'family':<6} {'educ':<4} {'span':<32} {'total':>9} {'min/yr':>7}")
    for d in sorted(definitions, key=lambda d: d["min_year_events"]):
        print(f"{d['cell_id']:<7} {d['family']:<6} {d['educ']:<4} {d['span']:<32} "
              f"{d['total_events']:>9,} {d['min_year_events']:>7,}")

    # write hash ledger entry
    hash_file = Path(r"D:\Migration\prereg\P0_hash.txt")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (f"---\nversion: v1.2\ncomputed_at: {ts}\n"
             f"partition_file: data/derived/P0_partition.parquet\n"
             f"sha256: {digest}\nrow_count: {len(out)}\ncell_count: {k}\n"
             f"source_data: IPUMS usa_00001.csv.gz (extract #1) + scope 2012-2021\n"
             f"code_commit: step0_build_p0.py (v1.2 collapse)\n"
             f"notes: 10 sub-500 cells merged per v1.2 deterministic algorithm; "
             f"K={k} (12-16 prior superseded, see PRE_REG_v1.2_amendment.md)\n---\n")
    with hash_file.open("a", encoding="utf-8") as f:
        f.write(entry)
    print(f"\nhash appended to {hash_file}")
    return digest


def diagnose(df: pd.DataFrame):
    ev = df[df.is_event & df.income_bin.notna()]
    print(f"\ntotal events (cross-PUMA, scope, valid income): {len(ev):,}")
    print(f"distinct raw cells present: {ev.raw_cell.nunique()} / 48 possible")

    ct = ev.groupby(["raw_cell", "YEAR"]).size().unstack(fill_value=0)
    min_per_yr = ct.min(axis=1).sort_values()
    total = ct.sum(axis=1)
    out = pd.DataFrame({"total_events": total, "min_year_events": min_per_yr})
    out = out.sort_values("min_year_events")

    print(f"\n48-cell event counts (sorted by worst-year count):")
    print(f"{'cell':<28} {'total':>10} {'min/yr':>8}  below500?")
    for cell, row in out.iterrows():
        flag = "  <500" if row.min_year_events < 500 else ""
        print(f"{cell:<28} {int(row.total_events):>10,} {int(row.min_year_events):>8,}{flag}")

    n_sparse = (out.min_year_events < 500).sum()
    print(f"\ncells with a year < 500 events: {n_sparse} / {len(out)}")
    print(f"cells comfortably >= 500 every year: {len(out) - n_sparse}")
    print("\n(no files written in diagnose mode; review then run finalize)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["diagnose", "finalize"], default="diagnose")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    df = load_scope()
    df, edges = derive_bins(df)

    if args.mode == "diagnose":
        diagnose(df)
        return 0

    finalize(df, edges)
    return 0


if __name__ == "__main__":
    sys.exit(main())
