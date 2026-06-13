"""
Build the opportunity-UPSIDE index per MIGPUMA-year: the variance/ceiling of
opportunity (what dreamers chase), distinct from the mean-opportunity index.

Indicators per (statefip, migpuma, year), household level (PERNUM==1, HHWT):
  p90_loginc   : log 90th-pctile household income (the ceiling)
  p90_p50      : P90/P50 ratio (how far the top stretches above the middle)
  top_share    : share of households above the national P95 income that year
  gini         : weighted Gini of household income (dispersion)
PCA-1 frozen on the 2012-2017 training window (parallel to the mean index),
oriented higher = more upside.

Outputs:
  data/derived/migpuma_upside_2010.parquet     (statefip, migpuma, year, upside_index + indicators)
  data/derived/pca_upside_loadings.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

GZ = Path(r"D:\Migration\data\raw\ipums\usa_00001.csv.gz")
CW = Path(r"D:\Migration\data\derived\puma_to_migpuma_2010.parquet")
OUT = Path(r"D:\Migration\data\derived\migpuma_upside_2010.parquet")
LOAD = Path(r"D:\Migration\data\derived\pca_upside_loadings.json")
COLS = ["YEAR", "SERIAL", "PERNUM", "HHWT", "STATEFIP", "PUMA", "GQ", "AGE", "HHINCOME"]
YEAR_MIN, YEAR_MAX = 2012, 2021
HHINCOME_NA = 9999999
TRAIN = list(range(2012, 2018))
FEATURES = ["p90_loginc", "p90_p50", "top_share", "gini"]


def wquantile(v, w, q):
    o = np.argsort(v); v, w = v[o], w[o]
    cw = np.cumsum(w)
    return float(np.interp(q * cw[-1], cw, v))


def wgini(v, w):
    o = np.argsort(v); v, w = v[o], w[o]
    cw = np.cumsum(w); cv = np.cumsum(v * w)
    if cv[-1] <= 0:
        return np.nan
    # weighted Gini via Lorenz
    return float(1 - 2 * np.sum(w * (cv - 0.5 * v * w)) / (cw[-1] * cv[-1]))


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    df = pd.read_csv(GZ, usecols=COLS)
    df = df[(df.YEAR >= YEAR_MIN) & (df.YEAR <= YEAR_MAX) & (df.AGE >= 18)
            & (df.GQ.isin([1, 2, 5])) & (df.PERNUM == 1) & (df.HHINCOME != HHINCOME_NA)].copy()
    cw = pd.read_parquet(CW).rename(columns={"statefip": "STATEFIP", "puma": "PUMA"})
    df = df.merge(cw, on=["STATEFIP", "PUMA"], how="left").dropna(subset=["migpuma"])
    df["migpuma"] = df.migpuma.astype(int)
    print(f"householder rows: {len(df):,}")

    # national P95 threshold per year
    natP95 = {int(y): wquantile(g.HHINCOME.to_numpy(float), g.HHWT.to_numpy(float), 0.95)
              for y, g in df.groupby("YEAR")}

    rows = []
    for (st, mg, yr), g in df.groupby(["STATEFIP", "migpuma", "YEAR"]):
        inc = g.HHINCOME.to_numpy(float); w = g.HHWT.to_numpy(float)
        if len(inc) < 20:
            continue
        p50 = wquantile(inc, w, 0.50); p90 = wquantile(inc, w, 0.90)
        if p50 <= 0:
            continue
        top = float(w[inc >= natP95[int(yr)]].sum() / w.sum())
        rows.append((st, mg, int(yr), np.log(max(p90, 1)), p90 / p50, top, wgini(inc, w)))
    up = pd.DataFrame(rows, columns=["statefip", "migpuma", "year"] + FEATURES).dropna()

    # PCA frozen on training window
    tr = up[up.year.isin(TRAIN)]
    Xtr = tr[FEATURES].to_numpy(float)
    mu = Xtr.mean(0); sd = Xtr.std(0, ddof=0)
    pca = PCA(n_components=len(FEATURES)).fit((Xtr - mu) / sd)
    pc1 = pca.components_[0].copy()
    if pc1[FEATURES.index("p90_p50")] < 0:  # orient: higher = more upside
        pc1 = -pc1
    up["upside_index"] = ((up[FEATURES].to_numpy(float) - mu) / sd) @ pc1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    up.to_parquet(OUT, index=False)
    LOAD.write_text(json.dumps(dict(
        features=FEATURES, train_years=TRAIN, scaler_mean=mu.tolist(),
        scaler_std=sd.tolist(), pc1_loadings=pc1.tolist(),
        pc1_explained_var=float(pca.explained_variance_ratio_[0]),
        orientation="higher = more opportunity-upside (P90/P50)"), indent=2))

    print(f"upside PC1 explained variance: {pca.explained_variance_ratio_[0]:.3f}")
    print("loadings:", {f: round(float(l), 3) for f, l in zip(FEATURES, pc1)})
    print(f"upside_index range [{up.upside_index.min():.2f}, {up.upside_index.max():.2f}]")
    # corr of upside vs mean opportunity index (are they distinct?)
    opp = pd.read_parquet(Path(r"D:\Migration\data\derived\migpuma_opportunity_2010.parquet"))
    m = up.merge(opp, on=["statefip", "migpuma", "year"])
    print(f"corr(upside_index, mean opportunity_index): {m.upside_index.corr(m.opportunity_index):.3f}  "
          f"(low = genuinely new dimension)")
    print(f"written: {OUT}")


if __name__ == "__main__":
    main()
