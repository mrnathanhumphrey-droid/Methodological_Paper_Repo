"""
RMD-SRC Step 5 / §3.7 F4 holdout protocol -- T=2 fallback.

Per locked PRE_REG_v1.0 §3.7 operational fallback for T=2:
  'between-population regime stability at the leaf level using train→holdout
   pop partitioning'.

Implementation: Within each region, compute pairwise Cohen's κ between
trajectory-classifiable pops' 7-observable regime label vectors. Average κ
within region is the F4 statistic. Threshold: average κ ≥ 0.4 to NOT fire.

Output:
  results/step5_F4_holdout.parquet
"""

from pathlib import Path
import hashlib
import datetime
import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score
from itertools import combinations

ROOT = Path(r"D:/Phenotype_Research")
RESULTS = ROOT / "results"
PREREG = ROOT / "prereg"

REGIMES = RESULTS / "step2_regimes.parquet"
OUT = RESULTS / "step5_F4_holdout.parquet"
FALSIFIER_PARQUET = RESULTS / "step4_falsifier_report.parquet"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    regimes = pd.read_parquet(REGIMES)
    # 7-obs regime vector per Pop, drop Insufficient_T pops
    pivot = regimes.pivot(index="population", columns="observable",
                          values="regime")
    pops_traj = [p for p in pivot.index
                 if (pivot.loc[p] != "Insufficient_T").all()]
    pivot_t = pivot.loc[pops_traj]
    print(f"trajectory-classifiable pops: {pops_traj}")
    print("\nregime vectors:")
    print(pivot_t.to_string())

    # region map
    region_map = regimes.drop_duplicates("population").set_index("population")["region"]

    # pairwise κ within region
    rows = []
    for region in ["lowland", "mountain"]:
        pops = [p for p in pops_traj if region_map[p] == region]
        for a, b in combinations(pops, 2):
            va = pivot_t.loc[a].tolist()
            vb = pivot_t.loc[b].tolist()
            k = cohen_kappa_score(va, vb)
            agree = sum(x == y for x, y in zip(va, vb)) / len(va)
            rows.append({"region": region, "pop_a": a, "pop_b": b,
                         "kappa": k, "raw_agreement": agree,
                         "n_observables": len(va)})

    kdf = pd.DataFrame(rows)
    print("\n=== pairwise κ within region ===")
    print(kdf.round(3).to_string(index=False))

    if len(kdf) > 0:
        avg_k = kdf["kappa"].mean()
        avg_acc = kdf["raw_agreement"].mean()
        n_pairs = len(kdf)
    else:
        avg_k, avg_acc, n_pairs = float("nan"), float("nan"), 0

    F4_threshold = 0.40
    F4_fires = avg_k < F4_threshold if not np.isnan(avg_k) else None

    print(f"\n=== F4 ACCOUNTING ===")
    print(f"  n pairs evaluated: {n_pairs}")
    print(f"  average κ:        {avg_k:.3f}")
    print(f"  average accuracy: {avg_acc:.3f}")
    print(f"  threshold:        κ ≥ {F4_threshold} to NOT fire")
    print(f"  F4 fires:         {F4_fires}")

    out_df = pd.DataFrame([{
        "n_pairs": n_pairs,
        "avg_kappa": avg_k,
        "avg_raw_agreement": avg_acc,
        "threshold": F4_threshold,
        "F4_fires": F4_fires,
    }])
    kdf.to_parquet(RESULTS / "step5_F4_pairs.parquet", index=False)
    out_df.to_parquet(OUT, index=False)

    # update falsifier report
    fals = pd.read_parquet(FALSIFIER_PARQUET)
    fals = pd.concat([fals,
                      pd.DataFrame([{"falsifier": "F4",
                                     "value": avg_k,
                                     "threshold_op": "<",
                                     "threshold": F4_threshold,
                                     "fires": bool(F4_fires) if F4_fires is not None else None}])],
                     ignore_index=True)
    fals.to_parquet(FALSIFIER_PARQUET, index=False)
    print("\nupdated falsifier_report.parquet with F4 row")

    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log = PREREG / "step5_log.txt"
    log.write_text(
        f"# RMD-SRC Gymnadenia Step 5 / §3.7 F4 holdout\n"
        f"# Generated: {ts}\n"
        f"# Per PRE_REG v1.0 §3.7 T=2 fallback\n\n"
        f"step5_F4_holdout.parquet sha = {sha256_file(OUT)}\n"
        f"step5_F4_pairs.parquet sha   = {sha256_file(RESULTS/'step5_F4_pairs.parquet')}\n\n"
        f"n pairs        = {n_pairs}\n"
        f"avg kappa      = {avg_k:.4f}\n"
        f"threshold      = >= {F4_threshold}\n"
        f"F4 fires       = {F4_fires}\n",
        encoding="utf-8",
    )
    print(f"\nWrote {log}")


if __name__ == "__main__":
    main()
