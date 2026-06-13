"""
Fit the opportunity-index PCA on the pooled 2012-2017 training panel
(PRE_REG v1.1 A1: training-window-only, frozen) and apply to all years.

Features (PRE_REG v1.0 §2.5): med_hhinc, emp_pop_2554, ba_share, affordability.
Standardize with TRAINING mean/std (frozen), take PC1, orient so higher =
more opportunity (positive loading on income). Apply frozen transform to all
2012-2021 rows.

Outputs:
  data/derived/migpuma_opportunity_2010.parquet  (statefip, migpuma, year, opportunity_index)
  data/derived/pca_opportunity_loadings.json     (frozen scaler + loadings + meta)
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

SRC = Path(r"D:\Migration\data\derived\migpuma_socioecon_2010.parquet")
OUT = Path(r"D:\Migration\data\derived\migpuma_opportunity_2010.parquet")
LOAD = Path(r"D:\Migration\data\derived\pca_opportunity_loadings.json")
FEATURES = ["med_hhinc", "emp_pop_2554", "ba_share", "affordability"]
TRAIN_YEARS = list(range(2012, 2018))  # 2012-2017 inclusive


def main():
    df = pd.read_parquet(SRC)
    train = df[df.year.isin(TRAIN_YEARS)]
    Xtr = train[FEATURES].to_numpy(float)

    mu = Xtr.mean(axis=0)
    sd = Xtr.std(axis=0, ddof=0)
    Ztr = (Xtr - mu) / sd

    pca = PCA(n_components=len(FEATURES))
    pca.fit(Ztr)
    pc1 = pca.components_[0].copy()
    evr = pca.explained_variance_ratio_.tolist()

    # orient: higher index = more opportunity -> positive loading on income
    inc_i = FEATURES.index("med_hhinc")
    if pc1[inc_i] < 0:
        pc1 = -pc1

    # apply frozen transform to ALL rows
    Xall = df[FEATURES].to_numpy(float)
    Zall = (Xall - mu) / sd
    df["opportunity_index"] = Zall @ pc1

    out = df[["statefip", "migpuma", "year", "opportunity_index"]].copy()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)

    loadings = {
        "features": FEATURES,
        "train_years": TRAIN_YEARS,
        "scaler_mean": mu.tolist(),
        "scaler_std": sd.tolist(),
        "pc1_loadings": pc1.tolist(),
        "explained_variance_ratio_all_pcs": evr,
        "pc1_explained_variance_ratio": evr[0],
        "orientation": "higher = more opportunity (positive on med_hhinc)",
        "n_train_rows": int(len(train)),
    }
    LOAD.write_text(json.dumps(loadings, indent=2), encoding="utf-8")

    print(f"PC1 explained variance: {evr[0]:.3f}  (all PCs: {[round(x,3) for x in evr]})")
    print("PC1 loadings (oriented):")
    for f, l in zip(FEATURES, pc1):
        print(f"  {f:<16} {l:+.3f}")
    print(f"\ntraining rows (2012-2017): {len(train):,}")
    print(f"opportunity_index range: [{out.opportunity_index.min():.2f}, {out.opportunity_index.max():.2f}], "
          f"mean {out.opportunity_index.mean():.3f}")
    print(f"written: {OUT}")
    print(f"frozen loadings: {LOAD}")


if __name__ == "__main__":
    main()
