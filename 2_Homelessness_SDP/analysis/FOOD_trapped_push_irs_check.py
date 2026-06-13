"""
FOOD-edge firm-up: replicate the trapped-push with an INDEPENDENT instrument.

The ACS cross-PUMA measure gave food_insec -> out-migration r=-0.37 (deprivation push
SUPPRESSES leaving). Here we re-test with IRS county-to-county OUTFLOW (tax filers) — a
different data source — to see if two independent instruments agree.

IRS sentinel: n2 = -1 means disclosure-suppressed -> filtered (the FEA lesson).
Out-of-state out-migrants from state S = sum n2 over real county->county rows with
y1_state=S, y2_state in 1..56 and != S. Rate = annual avg / ACS state population.
Output: analysis/FOOD_trapped_push_irs_check.json
"""
from __future__ import annotations
import glob, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats

IDP = Path(r"D:\IDP")
IRS = r"D:\Migration\data\raw\irs_soi\countyoutflow{}.csv"
POP = r"D:\Migration\data\derived\migpuma_population_2010.parquet"
FEAX = r"D:\Food Deserts\data_raw\FEA\2025-food-environment-atlas-data.xlsx"
YEARS = ["1213","1314","1415","1516","1617","1718","1819","1920","2021","2122"]
FIPS2USPS = {1:'AL',2:'AK',4:'AZ',5:'AR',6:'CA',8:'CO',9:'CT',10:'DE',11:'DC',12:'FL',13:'GA',15:'HI',16:'ID',17:'IL',18:'IN',19:'IA',20:'KS',21:'KY',22:'LA',23:'ME',24:'MD',25:'MA',26:'MI',27:'MN',28:'MS',29:'MO',30:'MT',31:'NE',32:'NV',33:'NH',34:'NJ',35:'NM',36:'NY',37:'NC',38:'ND',39:'OH',40:'OK',41:'OR',42:'PA',44:'RI',45:'SC',46:'SD',47:'TN',48:'TX',49:'UT',50:'VT',51:'VA',53:'WA',54:'WV',55:'WI',56:'WY'}


def main():
    rows = []
    supp = 0
    for yy in YEARS:
        f = IRS.format(yy)
        if not glob.glob(f):
            continue
        d = pd.read_csv(f, encoding="latin-1", dtype={"y1_statefips": int, "y1_countyfips": int,
                                  "y2_statefips": int, "y2_countyfips": int})
        supp += int((d.n2 <= 0).sum())
        d = d[(d.y1_countyfips != 0) & (d.y2_countyfips != 0) &
              (d.y2_statefips.between(1, 56)) & (d.n2 > 0)]              # real flows, sentinel-filtered
        oos = d[d.y1_statefips != d.y2_statefips]                        # left the state
        g = oos.groupby("y1_statefips").n2.sum().rename(yy)
        rows.append(g)
    irs = pd.concat(rows, axis=1)
    irs["oos_annual"] = irs.mean(axis=1)
    irs = irs[["oos_annual"]].reset_index().rename(columns={"y1_statefips": "fips"})
    irs["st"] = irs.fips.map(FIPS2USPS)

    spop = pd.read_parquet(POP).groupby(["statefip","year"]).population.sum().groupby("statefip").mean()
    irs = irs.merge(spop.rename("pop").reset_index().rename(columns={"statefip":"fips"}), on="fips")
    irs["irs_oos_per1k"] = 1000 * irs.oos_annual / irs["pop"]

    ins = pd.read_excel(FEAX, sheet_name="INSECURITY", header=1)
    ins["fi"] = pd.to_numeric(ins.FOODINSEC_21_23, errors="coerce").where(lambda x:(x>=0)&(x<=100))
    food = ins.groupby("State").fi.mean().rename("food_insec")
    soc = pd.read_excel(FEAX, sheet_name="SOCIOECONOMIC", header=1)
    soc["pv"] = pd.to_numeric(soc.POVRATE21, errors="coerce").where(lambda x:(x>=0)&(x<=100))
    pov = soc.groupby("State").pv.mean().rename("poverty")

    M = irs.set_index("st").join([food, pov]).dropna(subset=["irs_oos_per1k","food_insec","poverty"])
    def cr(a,b): r,p=stats.pearsonr(M[a],M[b]); return {"r":round(float(r),3),"p":round(float(p),4)}
    out = {"n":int(len(M)), "irs_suppressed_cells_filtered":int(supp),
           "irs_oos_rate_range":[round(M.irs_oos_per1k.min(),1),round(M.irs_oos_per1k.max(),1)],
           "food_insec~irs_outmig": cr("food_insec","irs_oos_per1k"),
           "poverty~irs_outmig": cr("poverty","irs_oos_per1k"),
           "ACS_comparison":{"food_insec~acs_outmig":-0.369,"poverty~acs_outmig":-0.073}}
    (IDP/"analysis"/"FOOD_trapped_push_irs_check.json").write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
    print("\ntop IRS out-migration states:")
    print(M.sort_values("irs_oos_per1k",ascending=False)[["irs_oos_per1k","food_insec","poverty"]].head(6).round(1).to_string())
    print("\nbottom (lowest out-migration):")
    print(M.sort_values("irs_oos_per1k")[["irs_oos_per1k","food_insec","poverty"]].head(6).round(1).to_string())


if __name__=="__main__":
    main()
