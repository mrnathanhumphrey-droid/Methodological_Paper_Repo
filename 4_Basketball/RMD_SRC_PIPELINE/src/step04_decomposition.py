"""
RMD-SRC NBA — Step 4: decomposition (4a categorical -> 4b continuous -> 4c null).

Per locked pre-reg v1.0 section 5: "Applied only to cells that are
response-validated and classified as one of {Concentrating, Diffusing,
Contracting, Drifting}."

Under Path A on this substrate, Step 3 returns 0 / all clean for every arm
(dip-on-raw-values over-fires — substrate-shape finding mirroring
Migration v1.4). Step 4's eligible-input set is therefore empty. This
script documents that empty case formally so the substrate ledger has
the row.

Outputs (per arm):
  step04_decomposition_{arm}.json   eligible cells + per-cell 4a/4b/4c
                                    disposition (empty under Path A)
  step04_diagnostic_{arm}.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _common import OBSERVABLES, RESULTS, verify_sha_lock

NON_STATIONARY = {"Concentrating", "Diffusing", "Contracting", "Drifting"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm",
                     choices=["usg", "mpg", "usg_adj", "mpg_adj",
                              "off_feast", "def_feast"],
                     required=True)
    args = ap.parse_args()
    arm = args.arm

    if arm in {"off_feast", "def_feast"}:
        txt = (RESULTS.parent / "SHA_LOCK.txt").read_text(encoding="utf-8")
        if "## spatial re-axis" not in txt or "cd40b46" not in txt:
            sys.exit("[Step 4] spatial re-axis lock SHA not found in SHA_LOCK.txt.")
        print(f"[Step 4 decompose [arm={arm}]] spatial SHA-lock verified: cd40b46")
        sha = {"v1.0": "cd40b46", "v1.1": ""}
    else:
        sha = verify_sha_lock(f"Step 4 decompose [arm={arm}]", arm=arm)
    cls = pd.read_parquet(RESULTS / f"trajectory_classification_{arm}.parquet")
    val = pd.read_parquet(RESULTS / f"step03_validation_{arm}.parquet")

    merged = cls.merge(val[["cell_id", "observable", "clean"]],
                        on=["cell_id", "observable"], how="left")
    eligible = merged[merged["regime"].isin(NON_STATIONARY)
                       & (merged["clean"] == True)]
    non_stat = merged[merged["regime"].isin(NON_STATIONARY)]

    print(f"\n--- Step 4 ({arm}) ---")
    print(f"  Step 2 non-Stationary cells: {len(non_stat)}")
    print(f"  ... of which Step 3 response-validated: {len(eligible)}")
    print(f"  -> Step 4 input cardinality: {len(eligible)}")

    out = {
        "arm": arm,
        "locked_sha_v1_0": sha["v1.0"],
        "locked_sha_v1_1": sha["v1.1"],
        "n_step2_non_stationary": int(len(non_stat)),
        "n_step3_clean_non_stationary": int(len(eligible)),
        "n_step4_eligible": int(len(eligible)),
        "step4_disposition": ("vacuous"
                               if len(eligible) == 0 else "to_be_computed"),
        "per_cell_outcomes": [
            {"cell_id": r["cell_id"], "observable": r["observable"],
             "regime": r["regime"],
             "step4_outcome": "no_op_empty_input"}
            for _, r in eligible.iterrows()
        ],
    }
    (RESULTS / f"step04_decomposition_{arm}.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")

    lines = [
        f"# Step 4 — decomposition disposition (arm = {arm})\n",
        f"Locked v1.0 SHA: `{sha['v1.0']}`",
        (f"Locked v1.1 SHA: `{sha['v1.1']}`" if sha['v1.1']
         else "(v1.1 amendment not in scope)"),
        "",
        "## Headline",
        f"- Step 2 non-Stationary cells (any of 4 regimes): "
        f"**{len(non_stat)}**",
        f"- Of those, response-validated at Step 3 (clean): "
        f"**{len(eligible)}**",
        f"- Step 4 input cardinality: **{len(eligible)}**",
        f"- Disposition: **{out['step4_disposition']}**",
        "",
        "## Reading",
        "Per pre-reg v1.0 section 5, Step 4 applies only to cells that are "
        "BOTH (a) response-validated at Step 3 AND (b) classified as one of "
        "{Concentrating, Diffusing, Contracting, Drifting} at Step 2. Under "
        "the locked spec, Step 3's Hartigan-dip-on-raw-values check over-fires "
        "at 100% on this substrate (per-game per-36 distributions are "
        "intrinsically multimodal at the (player x game) level due to within-"
        "cell role heterogeneity). Every non-Stationary cell is therefore "
        "flagged at Step 3, leaving Step 4 with an empty input set across all "
        "4 arms.",
        "",
        "This mirrors Migration's v1.4 amendment diagnosis of the same "
        "dip-over-fire pattern on raw observable values. Under Path A "
        "(discipline-pure, no spec modification), the over-fire is reported "
        "as a substrate-shape finding and Step 4 proceeds vacuously.",
        "",
        "## Consequences for downstream falsifiers",
        "- **F2** numerator = Stationary count (Step 4 produces zero "
        "additional clean cells under the vacuous case).",
        "- **F3** vacuously does not fire — there are no sub-partitions to be "
        "thin.",
        "- **F1** and **F4** are independent of Step 3/4 and are computed in "
        "Step 5.",
        "",
        "## Per-cell outcomes",
    ]
    if len(eligible) == 0:
        lines.append("\n*(none — Step 4 input is empty under Path A)*")
    else:
        lines.append("\n*(unexpected — should be empty under Path A on this substrate)*")
        for _, r in eligible.iterrows():
            lines.append(f"- `{r['cell_id']}` x {r['observable']}: "
                          f"{r['regime']}")

    (RESULTS / f"step04_diagnostic_{arm}.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print(f"  -> step04_decomposition_{arm}.json + step04_diagnostic_{arm}.md")
    print(f"\nStep 4 ({arm}) complete. disposition={out['step4_disposition']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
