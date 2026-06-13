"""
CLTR tie-up #3 — CONFIRM the migration v1.7 pull-taxonomy held-out signature correlation (claimed r=0.999,
RESULTS_migration_substrate.md line 78, prose-only / no committed script / no results JSON).
Independent recompute from on-disk artifacts (read-only on D:/Migration):
  flow_taxonomy.parquet (flow per event) x P0_partition.parquet (demographic bins).
Signature vector = per PULL flow {young 18-29, kids, BA+, inc_lo} PERWT-weighted shares.
Held-out gate = pearson( signature(train 2012-17), signature(holdout 2018-21) ).
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import pearsonr
MIG = Path(r"D:/Migration")
OUT = Path(r"D:/IDP/analysis/CLTR_migration_heldout_confirm_2026_05_29.json")

ft = pd.read_parquet(MIG/"results/flow_taxonomy.parquet")[["YEAR","SERIAL","PERNUM","PERWT","flow"]]
p0 = pd.read_parquet(MIG/"data/derived/P0_partition.parquet")[["YEAR","SERIAL","PERNUM","age_bin","income_bin","family_bin","educ_bin"]]
d = ft.merge(p0, on=["YEAR","SERIAL","PERNUM"], how="left")

PULL = ["1 DREAMER","2 STABILITY","3 BOTH(up)","4 CLEARING"]   # v1.7 pull taxonomy (4 flows; 5=desperation push excluded)
FEAT = [("age_bin","18-29"),("family_bin","kids"),("educ_bin","BA+"),("income_bin","inc_lo")]

def signature(df, flows):
    vec=[]
    for f in flows:
        g=df[df.flow==f]; w=g.PERWT.sum()
        for col,lvl in FEAT:
            vec.append(100*g[g[col]==lvl].PERWT.sum()/w if w>0 else np.nan)
    return np.array(vec)

train=d[d.YEAR.between(2012,2017)]; hold=d[d.YEAR.between(2018,2021)]
def gate(flows):
    a=signature(train,flows); b=signature(hold,flows)
    r,p=pearsonr(a,b); return round(float(r),4), round(float(p),6), len(a)

r4,p4,n4=gate(PULL)
r5,p5,n5=gate(PULL+["5 DESPERATION"])
res={"check":"migration v1.7 pull-taxonomy held-out signature correlation",
 "claim_in_prose":"RESULTS_migration_substrate.md line 78: train(2012-17) vs holdout(2018-21) = 0.999 (>=0.80) PASS",
 "backing_before_this":"NONE — prose only; flow_taxonomy.py pools all years (no train/holdout split); no results JSON",
 "independent_recompute":{
   "n_train":int(len(train)),"n_holdout":int(len(hold)),
   "pull_4flows":{"signature_dim":n4,"heldout_r":r4,"p":p4},
   "with_desperation_5flows":{"signature_dim":n5,"heldout_r":r5,"p":p5}},
 "VERDICT":("CONFIRMED — recompute reproduces r=0.999 (>=0.80 gate); the taxonomy's demographic signature is near-identical train vs holdout"
            if r4>=0.99 else
            "PARTIAL — recompute gives r=%.3f (>=0.80 gate %s) but does not match the claimed 0.999 exactly; signature definition may differ"%(r4,"PASS" if r4>=0.80 else "FAIL")
            if r4>=0.80 else
            "DISCREPANCY — recompute r=%.3f fails the 0.80 gate; the prose 0.999 is not reproduced"%r4),
 "note":"This script is the committed, reproducible backing the prose lacked. Read-only on D:/Migration."}
OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2)); print("\nwrote",OUT)
