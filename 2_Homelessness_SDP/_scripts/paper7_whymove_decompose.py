"""
Bridge-1 UPGRADE: IPUMS-CPS WHYMOVE individual-level decomposition.
WHYMOVE x poverty(OFFPOV) x move-distance(MIGRATE1), ASECWT-weighted, 2016-2024.

The published CPS table gave poverty and move-type as SEPARATE marginals; the
microdata gives the full cross — the clean test of whether the affordability-PUSH
share of INTERCITY / INTERSTATE moves is poverty-concentrated.

Codes from DDI (not memory):
  WHYMOVE push = {12 cheaper housing, 19 foreclosure/eviction}
          pull_housing = {9 own home,10 new/better,11 better nbhd}
          job = {4,5,6,7,8}; family = {1,2,3,20}; other = {13..18}
  MIGRATE1: 3 within county; 4 diff county same state; 5 between states; 6 abroad
            intercity = {4,5}; interstate = {5}
  OFFPOV: 1 below, 2 above
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
from ipumspy import readers

ROOT=Path(r"D:/IDP")
DDI=ROOT/"data/paper7/ipums_cps/cps_00003.xml"
OUT=ROOT/"analysis/paper7_whymove_decomp_2026_05_28.json"

PUSH={12,19}; PULL_H={9,10,11}; JOB={4,5,6,7,8}; FAM={1,2,3,20}
def wshare(d, mask_num, w):
    den=d[w].sum()
    return float(d.loc[mask_num,w].sum()/den) if den>0 else np.nan

def main():
    ddi=readers.read_ipums_ddi(str(DDI))
    df=readers.read_microdata(ddi, ROOT/"data/paper7/ipums_cps/cps_00003.csv.gz")
    df.columns=[c.upper() for c in df.columns]
    for c in ["WHYMOVE","MIGRATE1","OFFPOV","YEAR"]: df[c]=pd.to_numeric(df[c],errors="coerce")
    df["ASECWT"]=pd.to_numeric(df["ASECWT"],errors="coerce")

    movers=df[df["WHYMOVE"].between(1,20)].copy()
    movers["push"]=movers["WHYMOVE"].isin(PUSH)
    movers["pull_h"]=movers["WHYMOVE"].isin(PULL_H)
    movers["job"]=movers["WHYMOVE"].isin(JOB)
    movers["fam"]=movers["WHYMOVE"].isin(FAM)

    res={"n_movers_raw":int(len(movers)),"framing":"ASECWT-weighted; push=cheaper-housing+eviction"}

    def block(sub, label):
        out={"n":int(len(sub))}
        for pov,code in [("below",1),("above",2)]:
            s=sub[sub["OFFPOV"]==code]
            out[pov]={"push":round(wshare(s,s["push"],"ASECWT"),4),
                      "pull_housing":round(wshare(s,s["pull_h"],"ASECWT"),4),
                      "job":round(wshare(s,s["job"],"ASECWT"),4),
                      "fam":round(wshare(s,s["fam"],"ASECWT"),4),
                      "n":int(len(s))}
        b,a=out["below"]["push"],out["above"]["push"]
        out["push_ratio_below_over_above"]=round(b/a,3) if a and a>0 else None
        return out

    inter=movers[movers["MIGRATE1"].isin([4,5])]          # intercity
    interstate=movers[movers["MIGRATE1"]==5]              # between states
    local=movers[movers["MIGRATE1"]==3]                   # within county
    res["INTERCITY_moves"]=block(inter,"intercity")
    res["INTERSTATE_moves"]=block(interstate,"interstate")
    res["LOCAL_moves"]=block(local,"local")

    # pooled (all movers) push by poverty for reference
    res["ALL_movers"]=block(movers,"all")

    # by-year intercity push ratio (below/above) to see stability + moratorium dip
    yr={}
    for y in sorted(movers["YEAR"].dropna().unique()):
        s=inter[inter["YEAR"]==y]
        b=wshare(s[s["OFFPOV"]==1],s[s["OFFPOV"]==1]["push"],"ASECWT")
        a=wshare(s[s["OFFPOV"]==2],s[s["OFFPOV"]==2]["push"],"ASECWT")
        yr[int(y)]={"push_below":round(b,4),"push_above":round(a,4),
                    "ratio":round(b/a,3) if a and a>0 else None,"n":int(len(s))}
    res["intercity_push_by_year"]=yr

    # disposition
    ic=res["INTERCITY_moves"]
    res["disposition"]={
        "intercity_push_below":ic["below"]["push"],"intercity_push_above":ic["above"]["push"],
        "ratio":ic["push_ratio_below_over_above"],
        "reading":("affordability-push IS poverty-concentrated among intercity movers (ratio>1.3)"
                   if (ic["push_ratio_below_over_above"] or 0)>=1.3 else
                   "push only weakly/not poverty-concentrated even at individual level")}
    OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2)); print("\nwrote",OUT)

if __name__=="__main__": main()
