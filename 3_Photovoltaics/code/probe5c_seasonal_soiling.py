"""Probe 5c — Seasonal soiling pattern at DKA Alice Springs.

If rain-driven cleaning is the real mechanism (Probe 5b weak-positive), then
DRY-season soiling rate should be HIGHER than WET-season (no cleaning + more
dust mobilization). Tests it by classifying each SRR interval by mid-date
season and comparing daily PR-decline slopes across all systems."""
import os, glob, warnings, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
from probe4_dka_run import parse_file, m_number, phase_label, CATALOG, POA_COL, PWR_COL
from probe5_dka_soiling import daily_pr_and_insol
import rdtools.soiling as rsoil

DKA = ROOT / "data/raw/dka"
OUT = ROOT / "data/processed/probe5c_seasonal_soiling.csv"

# Alice Springs seasons (Southern Hemisphere, monsoonal influence):
WET = {12, 1, 2}   # Dec, Jan, Feb (summer monsoon)
DRY = {6, 7, 8}    # Jun, Jul, Aug (winter, very dry)
# Transitional months Mar-May, Sep-Nov excluded for sharper contrast


def intervals(pr, ins):
    sr, sr_ci, info = rsoil.soiling_srr(pr, ins, reps=100)
    summary = info.get("soiling_interval_summary") if isinstance(info, dict) else None
    if summary is None and isinstance(info, (list, tuple)):
        for item in info:
            if isinstance(item, pd.DataFrame) and "soiling_rate" in item.columns:
                summary = item; break
    return summary


def classify_season(d):
    m = pd.Timestamp(d).month
    if m in WET: return "wet"
    if m in DRY: return "dry"
    return "trans"


def main():
    all_intervals = []
    for p in sorted(glob.glob(str(DKA / "*Site_DKA-M*.csv"))):
        fname = os.path.basename(p)
        mnum = m_number(fname)
        if mnum is None:
            continue
        phase = phase_label(fname)
        cat = CATALOG.get(mnum, ("?", "?", "?", None))
        brand, tech, mount, vint = cat
        pr, ins, st = daily_pr_and_insol(p)
        if st != "ok":
            continue
        try:
            summ = intervals(pr, ins)
        except Exception as e:
            print(f"M{mnum:<2d} {phase}: ERR {type(e).__name__}: {str(e)[:50]}")
            continue
        if summ is None or len(summ) == 0:
            continue
        s = summ.copy()
        s["mid_date"] = pd.to_datetime(s["start"]) + (pd.to_datetime(s["end"]) - pd.to_datetime(s["start"])) / 2
        s["season"] = s["mid_date"].map(classify_season)
        s["M_num"] = mnum; s["phase"] = phase; s["technology"] = tech; s["mount"] = mount
        all_intervals.append(s)
        print(f"M{mnum:<2d} {phase:>5s} {tech:>9s} | {len(s)} intervals "
              f"(wet={int((s['season']=='wet').sum())}, dry={int((s['season']=='dry').sum())}, "
              f"trans={int((s['season']=='trans').sum())})")
    if not all_intervals:
        print("no intervals collected"); return
    df = pd.concat(all_intervals, ignore_index=True)
    df.to_csv(OUT, index=False)
    print(f"\nTotal intervals: {len(df)}")
    # filter to intervals classified as soiling (negative rate)
    soil = df[df["soiling_rate"] < 0].copy()
    soil["daily_loss_pct"] = -soil["soiling_rate"] * 100  # convert -fraction/day to %/day positive
    print(f"Soiling-classified intervals (negative slope): {len(soil)}")
    print()
    print("=== Daily soiling loss rate by season (across all systems & intervals) ===")
    print(f"{'season':>8s} {'n':>5s} {'mean %/day':>11s} {'median':>8s} {'std':>8s}")
    for season in ["wet", "trans", "dry"]:
        g = soil[soil["season"] == season]["daily_loss_pct"]
        if len(g):
            print(f"{season:>8s} {len(g):5d} {g.mean():11.4f} {g.median():8.4f} {g.std():8.4f}")
    # statistical test: dry > wet (Mann-Whitney, one-sided)
    dry = soil[soil["season"] == "dry"]["daily_loss_pct"]
    wet = soil[soil["season"] == "wet"]["daily_loss_pct"]
    if len(dry) >= 5 and len(wet) >= 5:
        u, p_oneside = stats.mannwhitneyu(dry, wet, alternative="greater")
        print(f"\nMann-Whitney one-sided test (dry > wet daily loss): U={u:.0f}, p={p_oneside:.4f}")
        ratio = dry.median() / wet.median() if wet.median() > 0 else float("nan")
        print(f"Median dry/wet daily-loss ratio: {ratio:.2f}x")
    # by-system: each system's mean rate per season (paired comparison)
    print("\n=== Per-system dry-vs-wet means (paired) ===")
    pivot = soil.groupby(["M_num", "phase", "season"])["daily_loss_pct"].mean().unstack()
    if "dry" in pivot.columns and "wet" in pivot.columns:
        paired = pivot.dropna(subset=["dry", "wet"]).copy()
        paired["dry_minus_wet"] = paired["dry"] - paired["wet"]
        print(paired[["wet", "dry", "dry_minus_wet"]].round(4).to_string())
        n_higher = int((paired["dry_minus_wet"] > 0).sum())
        n_total = len(paired)
        # sign test
        p_sign = stats.binomtest(n_higher, n_total, 0.5, alternative="greater").pvalue if n_total else None
        print(f"\nSign test: {n_higher}/{n_total} systems have dry > wet, binomial p={p_sign:.4f}")
    print(f"\nWrote {OUT}")

if __name__ == "__main__":
    main()
