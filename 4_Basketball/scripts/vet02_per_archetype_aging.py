"""
VET02 NBA Stage 1.5 — Per-Archetype Aging (NHL N02 pattern)
Pre-reg: D:/NBA Projections/docs/PREREG_VET02_PER_ARCHETYPE_AGING_2026_06_11.md
"""
import io
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
import statsmodels.api as sm

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SIGNATURES = {
    0: ("ENERGY_POST_BIG", ["oreb_fg", "blk_perc", "rim_fg"]),
    1: ("3_AND_D_MOVEMENT", ["three_fg", "three_perc", "stl_per_play"]),
    2: ("PERIMETER_CREATOR", ["usage", "three_fg", "ast_perc"]),
    3: ("MIXED_UTILITY_WING", ["efg_perc", "three_fg"]),
    4: ("BIG_FRAME_CREATOR", ["usage", "ast_perc", "rim_fg", "blk_perc"]),
    5: ("BENCH_PLAYMAKER", ["ast_perc", "ast_usage_ratio"]),
    6: ("RIM_BIG_SHOTBLOCKER", ["blk_perc", "rim_fg", "oreb_fg"]),
}

MPG_FLOOR = 15
AGE_MIN, AGE_MAX = 19, 40
SEASON_MIN = 2014


def load():
    v = pd.read_parquet("D:/NBA Projections/data/parquet/veteran_archetypes.parquet")
    c = pd.read_parquet("D:/NBA Projections/data/parquet/ctg_players.parquet")
    j = c.merge(v[["p_id", "cluster", "archetype_labels"]], on="p_id", how="inner")
    j = j[(j["age"] >= AGE_MIN) & (j["age"] <= AGE_MAX) &
          (j["mpg"] >= MPG_FLOOR) & (j["season"] >= SEASON_MIN)]
    return j


def fit_one(df, cluster, metric):
    sub = df[df["cluster"] == cluster].dropna(subset=[metric, "age", "p_id"]).copy()
    if len(sub) < 30:
        return None
    sub["m_dm"] = sub.groupby("p_id")[metric].transform(lambda x: x - x.mean())
    sub["a_c"] = sub["age"] - 28.0
    X = sm.add_constant(np.column_stack([sub["a_c"], sub["a_c"] ** 2]))
    y = sub["m_dm"].values
    try:
        m = sm.OLS(y, X).fit()
    except Exception:
        return None
    b1, b2 = m.params[1], m.params[2]
    p_b1, p_b2 = m.pvalues[1], m.pvalues[2]
    if b2 != 0:
        peak_age_raw = 28.0 - b1 / (2.0 * b2)
        if AGE_MIN <= peak_age_raw <= AGE_MAX:
            peak_age = peak_age_raw
        else:
            peak_age = float("nan")
    else:
        peak_age = float("nan")
    return {
        "cluster": cluster,
        "metric": metric,
        "n": len(sub),
        "n_players": sub["p_id"].nunique(),
        "b1": float(b1),
        "b2": float(b2),
        "p_b1": float(p_b1),
        "p_b2": float(p_b2),
        "peak_age": float(peak_age) if not np.isnan(peak_age) else None,
        "r2": float(m.rsquared),
    }


def main():
    print("[VET02] Loading + joining...")
    df = load()
    print(f"  n_player_seasons after filter = {len(df)}")
    print(f"  unique players = {df['p_id'].nunique()}")

    rows = []
    for c, (label, metrics) in SIGNATURES.items():
        print(f"\n[VET02] Cluster {c} ({label}):")
        for m in metrics:
            r = fit_one(df, c, m)
            if r is None:
                print(f"  {m}: n<30 or null")
                continue
            peak_str = f"{r['peak_age']:.2f}" if r["peak_age"] is not None else "n/a"
            print(f"  {m}: n={r['n']} | b1={r['b1']:+.5f} (p={r['p_b1']:.3f}) | "
                  f"b2={r['b2']:+.6f} (p={r['p_b2']:.3f}) | peak={peak_str} | "
                  f"r²={r['r2']:.4f}")
            r["cluster_label"] = label
            rows.append(r)

    res = pd.DataFrame(rows)

    # Gates
    # G1: per-cluster, >=1 sig metric b2 < 0 and p_b2 < 0.05
    g1_per_cluster = {}
    for c in SIGNATURES:
        sub = res[res["cluster"] == c]
        pass_ = ((sub["b2"] < 0) & (sub["p_b2"] < 0.05)).any()
        g1_per_cluster[c] = bool(pass_)
    G1 = sum(g1_per_cluster.values()) == len(SIGNATURES)
    print(f"\nG1 (each cluster ≥1 sig-metric parabola DOWN p<0.05): "
          f"{sum(g1_per_cluster.values())}/{len(SIGNATURES)} {'PASS' if G1 else 'FAIL'}")
    for c, ok in g1_per_cluster.items():
        print(f"   C{c}: {'PASS' if ok else 'FAIL'}")

    # G2: shared signature (usage OR ast_perc) cross-cluster peak-age range ≥ 2yr
    shared_peaks = {}
    for met in ["usage", "ast_perc"]:
        sub = res[(res["metric"] == met) & (res["b2"] < 0) & (res["peak_age"].notnull())]
        if len(sub) >= 2:
            r = sub["peak_age"].max() - sub["peak_age"].min()
            shared_peaks[met] = (sub.set_index("cluster_label")["peak_age"].to_dict(), r)
    G2 = any(p[1] >= 2.0 for p in shared_peaks.values())
    print(f"\nG2 (shared sig cross-cluster peak-age range ≥ 2yr): "
          f"{'PASS' if G2 else 'FAIL'}")
    for k, (peaks, r) in shared_peaks.items():
        print(f"   {k}: range = {r:.2f} yr | peaks = "
              + ", ".join(f"{n}={a:.1f}" for n, a in peaks.items()))

    # G3: per-cluster sig-metric R² > 0.005
    r2_pass = res[res["r2"] > 0.005]
    cluster_g3 = res.groupby("cluster")["r2"].max() > 0.005
    G3_n = int(cluster_g3.sum())
    G3 = G3_n == len(SIGNATURES)
    print(f"\nG3 (each cluster ≥1 sig-metric R²>0.005): "
          f"{G3_n}/{len(SIGNATURES)} {'PASS' if G3 else 'FAIL'}")

    # G4: C4 ast_perc peak LATER than C2 ast_perc peak by ≥ 2yr
    c4_ast = res[(res["cluster"] == 4) & (res["metric"] == "ast_perc")]
    c2_ast = res[(res["cluster"] == 2) & (res["metric"] == "ast_perc")]
    G4 = False
    if len(c4_ast) and len(c2_ast):
        p4 = c4_ast.iloc[0]["peak_age"]
        p2 = c2_ast.iloc[0]["peak_age"]
        if p4 is not None and p2 is not None:
            G4 = (p4 - p2) >= 2.0
            print(f"\nG4 (C4 BIG-FRAME ast_perc peak ≥ C2 PERIMETER ast_perc peak + 2yr): "
                  f"C4={p4:.2f} vs C2={p2:.2f} = {p4 - p2:+.2f} yr "
                  f"{'PASS' if G4 else 'FAIL'}")

    # G5: rim metrics peak EARLIER than craft (ast_perc) by ≥ 2yr within C0/C4/C6
    g5_per = {}
    for c in [0, 4, 6]:
        rim_metrics = ["rim_fg", "blk_perc"]
        ast = res[(res["cluster"] == c) & (res["metric"] == "ast_perc")]
        if not len(ast) or ast.iloc[0]["peak_age"] is None:
            g5_per[c] = None
            continue
        ast_peak = ast.iloc[0]["peak_age"]
        rim_rows = res[(res["cluster"] == c) & (res["metric"].isin(rim_metrics))
                       & (res["peak_age"].notnull())]
        if not len(rim_rows):
            g5_per[c] = None
            continue
        rim_min = rim_rows["peak_age"].min()
        g5_per[c] = (ast_peak - rim_min) >= 2.0
        print(f"\nG5 cluster C{c}: ast_peak={ast_peak:.2f}, rim_min={rim_min:.2f}, "
              f"delta={ast_peak - rim_min:+.2f} {'PASS' if g5_per[c] else 'FAIL'}")
    G5 = sum(1 for v in g5_per.values() if v is True) >= 1

    # G6: ≥5/7 clusters with at least one sig fit passing G3
    G6 = G3_n >= 5

    gates = {
        "G1_each_cluster_has_DOWN_parabola_p005": G1,
        "G2_shared_sig_range_2yr": G2,
        "G3_each_cluster_R2_005": G3,
        "G4_BIG_FRAME_ast_later_PERIMETER": G4,
        "G5_rim_before_craft": G5,
        "G6_5of7_R2_005": G6,
    }
    passed = sum(1 for v in gates.values() if v)
    print(f"\nGates passed: {passed}/6")
    if passed == 6:
        verdict = "SHIP_CLEAN"
    elif passed >= 4:
        verdict = "SHIP_CAVEAT"
    else:
        verdict = "DISCONFIRMED"
    print(f"\nVERDICT: {verdict}")

    # outputs
    Path("D:/NBA Projections/data/parquet").mkdir(parents=True, exist_ok=True)
    res.to_parquet("D:/NBA Projections/data/parquet/per_archetype_aging_curves_vet02.parquet",
                   index=False)
    payload = {
        "batch": "VET02_per_archetype_aging",
        "n_fits": len(res),
        "gates": gates,
        "gates_passed": passed,
        "verdict": verdict,
        "shared_peaks": {k: {n: float(a) for n, a in p[0].items()}
                         for k, p in shared_peaks.items()},
        "per_cluster_G1": g1_per_cluster,
    }
    with open("D:/NBA Projections/data/parquet/per_archetype_aging_curves_vet02_verdict.json", "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"\nWrote per_archetype_aging_curves_vet02.parquet ({len(res)} fits)")


if __name__ == "__main__":
    main()
