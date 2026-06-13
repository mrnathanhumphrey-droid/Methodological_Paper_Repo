"""Probe 5 — Soiling extraction at DKA Alice Springs (the test PVDAQ Probe 3 couldn't do).

Arid + on-site measured POA + 5-min cadence → SRR should work where PVDAQ failed.
Reuses Probe 4 loader; runs rdtools.soiling.soiling_srr per array."""
import os, glob, warnings, re
from pathlib import Path
import sys
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
from probe4_dka_run import parse_file, m_number, phase_label, CATALOG, POA_COL, PWR_COL
import rdtools.soiling as rsoil

DKA = ROOT / "data/raw/dka"
OUT = ROOT / "data/processed/probe5_dka_soiling.csv"


def daily_pr_and_insol(p):
    df, st = parse_file(p)
    if df is None or len(df) < 100000:
        return None, None, "too_short"
    pwr = df[PWR_COL].clip(lower=0, upper=df[PWR_COL].quantile(0.9999))
    pdc0 = float(pwr.quantile(0.99))
    if pdc0 <= 0.1:
        return None, None, "no_power"
    poa = df[POA_COL].clip(lower=0, upper=2000)
    dt_h = 1 / 12
    daily_e = (pwr * dt_h).resample("D").sum()
    daily_ins = (poa / 1000.0 * dt_h).resample("D").sum()
    pr = daily_e / (daily_ins * pdc0)
    mask = (daily_ins > 0.5) & (pr.between(0.2, 1.3))
    pr = pr[mask]
    ins = daily_ins[mask]
    if len(pr) < 365 * 2:
        return None, None, f"short_clean(n={len(pr)})"
    # normalize PR to ~1 baseline (high-quantile = clean) so SRR sawtooth is interpretable
    pr_norm = pr / pr.quantile(0.985)
    pr_norm.index = pd.to_datetime(pr_norm.index)
    ins.index = pd.to_datetime(ins.index)
    pr_norm = pr_norm.asfreq("D"); ins = ins.reindex(pr_norm.index)
    return pr_norm, ins, "ok"


def main():
    files = sorted(glob.glob(str(DKA / "*Site_DKA-M*.csv")))
    rows = []
    print(f"{'M':>3s} {'phase':>5s} {'tech':>9s} {'mount':>11s} | "
          f"{'soil_loss%':>10s} {'CI':>16s} {'n_days':>7s} {'status':>40s}")
    print("-" * 110)
    for p in files:
        fname = os.path.basename(p)
        mnum = m_number(fname)
        if mnum is None:
            continue
        phase = phase_label(fname)
        cat = CATALOG.get(mnum, ("?", "?", "?", None))
        brand, tech, mount, vint = cat
        row = {"file": fname, "M_num": mnum, "phase": phase, "brand": brand,
               "technology": tech, "mount": mount, "vintage": vint}
        pr, ins, st = daily_pr_and_insol(p)
        if st != "ok":
            row.update({"status": st})
            rows.append(row)
            print(f"M{mnum:<2d} {phase:>5s} {tech:>9s} {mount:>11s} | -- {st}")
            continue
        try:
            sr, sr_ci, info = rsoil.soiling_srr(pr, ins, reps=200)
            loss = float((1 - sr) * 100)
            ci_low = float((1 - sr_ci[1]) * 100); ci_high = float((1 - sr_ci[0]) * 100)
            row.update({"status": "ok", "soiling_loss_pct": loss,
                        "ci_low_pct": ci_low, "ci_high_pct": ci_high,
                        "soiling_ratio": float(sr), "n_days": int(len(pr))})
            print(f"M{mnum:<2d} {phase:>5s} {tech:>9s} {mount:>11s} | "
                  f"{loss:9.2f}% [{ci_low:+.2f},{ci_high:+.2f}] {len(pr):7d} ok")
        except Exception as e:
            row.update({"status": f"srr_err:{type(e).__name__}", "err_msg": str(e)[:80]})
            print(f"M{mnum:<2d} {phase:>5s} {tech:>9s} {mount:>11s} | -- {row['status']}")
        rows.append(row)
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT, index=False)
    print(f"\nWrote {OUT} ({len(df_out)} rows)")
    ok = df_out[df_out["status"] == "ok"]
    if len(ok):
        print(f"\n=== Soiling summary (n_ok={len(ok)}) ===")
        print(f"  median annual soiling loss: {ok['soiling_loss_pct'].median():.2f}%")
        print(f"  IQR: [{ok['soiling_loss_pct'].quantile(.25):.2f}%, {ok['soiling_loss_pct'].quantile(.75):.2f}%]")
        print(f"  range: [{ok['soiling_loss_pct'].min():.2f}%, {ok['soiling_loss_pct'].max():.2f}%]")
        print(f"\n  by technology:")
        for t, g in ok.groupby("technology"):
            print(f"    {t:>10s} n={len(g):2d}  median={g['soiling_loss_pct'].median():5.2f}%  "
                  f"[range {g['soiling_loss_pct'].min():.2f}, {g['soiling_loss_pct'].max():.2f}]")
        print(f"\n  by mount:")
        for m_, g in ok.groupby("mount"):
            print(f"    {str(m_):>11s} n={len(g):2d}  median={g['soiling_loss_pct'].median():5.2f}%")

if __name__ == "__main__":
    main()
