"""
FOOD-edge: WHY does NH-White over-emit from HOLC grade-D (redlined) origins (v1.9 residual)?

v1.9: NH-White redline_D beta +0.74 (p<1e-5, survives density); NH-Black flat (+0.13).
Three competing mechanisms, tested by re-fitting the race-stratified gravity with extra
ORIGIN covariates (train 2012-2017, origin-MIGPUMA-clustered SE, HOLC-covered origins):

  GENTRIFICATION : redline_D x rent_growth(2012->2019).  If the interaction carries the White
                   effect and redline_D main effect attenuates -> Whites leave TRANSITIONING grade-D.
  EXPENSIVE-CORE : add rent_level + opportunity_level.  If redline_D drops to null -> it was just
                   high-cost/high-opportunity cores, not redline-specific.
  REDLINE-PURE   : redline_D survives all controls (as it survived density).
  TRAPPED-PUSH-BY-RACE (contrast): is White>Black differential a resource gradient?
                   proxied by whether Black stays null and White is carried by gentrification.

Output: results/FOOD_redline_mechanism.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm

D = Path(r"D:\Migration\data\derived"); R = Path(r"D:\Migration\results")
TRAIN = list(range(2012, 2018)); MIN_FLOW = 50

FLOWS = pd.read_parquet(D/"race_corridor_flows_2010.parquet")
POPR = pd.read_parquet(D/"migpuma_population_by_race_2010.parquet")
GEO = pd.read_parquet(D/"migpuma_geometry_2010.parquet")
HOLC = pd.read_parquet(D/"migpuma_holc_2010.parquet")
SOC = pd.read_parquet(D/"migpuma_socioecon_2010.parquet")
OPP = pd.read_parquet(D/"migpuma_opportunity_2010.parquet")
CENT = GEO.set_index(["statefip","migpuma"])[["lon","lat"]]


def haversine(lo1,la1,lo2,la2):
    R_=6371.0088; lo1,la1,lo2,la2=map(np.radians,[lo1,la1,lo2,la2])
    a=np.sin((la2-la1)/2)**2+np.cos(la1)*np.cos(la2)*np.sin((lo2-lo1)/2)**2
    return 2*R_*np.arcsin(np.sqrt(a))


def origin_covars():
    s=SOC.copy()
    r12=s[s.year==2012].set_index(["statefip","migpuma"]).med_rent
    r19=s[s.year==2019].set_index(["statefip","migpuma"]).med_rent
    i12=s[s.year==2012].set_index(["statefip","migpuma"]).med_hhinc
    i19=s[s.year==2019].set_index(["statefip","migpuma"]).med_hhinc
    rent_growth=(np.log(r19)-np.log(r12)).rename("rent_growth")
    inc_growth=(np.log(i19)-np.log(i12)).rename("inc_growth")
    rent_lvl=s[s.year.isin(TRAIN)].groupby(["statefip","migpuma"]).med_rent.mean().rename("rent_lvl")
    opp_lvl=OPP[OPP.year.isin(TRAIN)].groupby(["statefip","migpuma"]).opportunity_index.mean().rename("opp_lvl")
    cov=pd.concat([rent_growth,inc_growth,rent_lvl,opp_lvl],axis=1).reset_index()
    return cov

COV=origin_covars()


def build(race):
    f=FLOWS[(FLOWS.race_group==race)&(FLOWS.YEAR.isin(TRAIN))]
    od=f.groupby(["orig_state","orig_migpuma","dest_state","dest_migpuma"]).flow.sum().reset_index()
    pr=POPR[(POPR.race_group==race)&(POPR.year.isin(TRAIN))].groupby(["statefip","migpuma"]).population.mean().reset_index()
    od=od.merge(pr.rename(columns={"statefip":"orig_state","migpuma":"orig_migpuma","population":"mass_o"}),on=["orig_state","orig_migpuma"])
    od=od.merge(pr.rename(columns={"statefip":"dest_state","migpuma":"dest_migpuma","population":"mass_d"}),on=["dest_state","dest_migpuma"])
    od=od.merge(HOLC[["statefip","migpuma","redline_D_share"]].rename(columns={"statefip":"orig_state","migpuma":"orig_migpuma"}),on=["orig_state","orig_migpuma"])
    od=od.merge(COV.rename(columns={"statefip":"orig_state","migpuma":"orig_migpuma"}),on=["orig_state","orig_migpuma"],how="left")
    od=od.join(CENT.rename(columns={"lon":"o_lon","lat":"o_lat"}),on=["orig_state","orig_migpuma"])
    od=od.join(CENT.rename(columns={"lon":"d_lon","lat":"d_lat"}),on=["dest_state","dest_migpuma"])
    od=od.dropna(subset=["o_lon","d_lon","mass_o","mass_d","rent_growth","rent_lvl","opp_lvl"])
    od=od[(od.mass_o>0)&(od.mass_d>0)&(od.flow>=MIN_FLOW)].copy()
    od["dist"]=haversine(od.o_lon,od.o_lat,od.d_lon,od.d_lat).clip(lower=1)
    od["log_mass_o"]=np.log(od.mass_o); od["log_mass_d"]=np.log(od.mass_d); od["log_dist"]=np.log(od.dist)
    od["offset"]=np.log(len(TRAIN)); od["grp"]=od.orig_state*1000+od.orig_migpuma
    # z-score the continuous origin covars so interaction/coefs are comparable
    for c in ["rent_growth","inc_growth","rent_lvl","opp_lvl"]:
        od[c+"_z"]=(od[c]-od[c].mean())/od[c].std()
    od["redline_x_growth"]=od.redline_D_share*od.rent_growth_z
    return od


def fit(od,extra):
    cols=["log_mass_o","log_mass_d","log_dist"]+extra
    X=sm.add_constant(od[cols].to_numpy(float))
    res=sm.GLM(od.flow.to_numpy(float),X,family=sm.families.Poisson(),offset=od.offset.to_numpy(float)).fit(cov_type="cluster",cov_kwds={"groups":od.grp.to_numpy()})
    return dict(zip(["const"]+cols,res.params)),dict(zip(["const"]+cols,res.pvalues))


def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    out={}
    for race in ["NH_White","NH_Black"]:
        od=build(race); rec={"n":int(len(od)),"n_origins":int(od.grp.nunique())}
        b0,p0=fit(od,["redline_D_share"])
        b1,p1=fit(od,["redline_D_share","rent_growth_z","redline_x_growth"])
        b2,p2=fit(od,["redline_D_share","rent_lvl_z","opp_lvl_z"])
        rec["baseline"]={"redline":round(b0["redline_D_share"],3),"p":round(p0["redline_D_share"],4)}
        rec["gentrification"]={"redline":round(b1["redline_D_share"],3),"p_redline":round(p1["redline_D_share"],4),
                               "redline_x_rentgrowth":round(b1["redline_x_growth"],3),"p_interaction":round(p1["redline_x_growth"],4),
                               "rent_growth":round(b1["rent_growth_z"],3),"p_rg":round(p1["rent_growth_z"],4)}
        rec["expensive_core"]={"redline":round(b2["redline_D_share"],3),"p_redline":round(p2["redline_D_share"],4),
                               "rent_lvl":round(b2["rent_lvl_z"],3),"p_rl":round(p2["rent_lvl_z"],4),
                               "opp_lvl":round(b2["opp_lvl_z"],3),"p_opp":round(p2["opp_lvl_z"],4)}
        out[race]=rec
        print(f"=== {race} (n={rec['n']}, {rec['n_origins']} origins) ===")
        print(f"  baseline redline      : {rec['baseline']['redline']:+.3f} p={rec['baseline']['p']:.2e}")
        print(f"  +gentrify: redline {rec['gentrification']['redline']:+.3f} (p={rec['gentrification']['p_redline']:.3f}) | redline×rentGrowth {rec['gentrification']['redline_x_rentgrowth']:+.3f} (p={rec['gentrification']['p_interaction']:.3f})")
        print(f"  +levels  : redline {rec['expensive_core']['redline']:+.3f} (p={rec['expensive_core']['p_redline']:.3f}) | rent_lvl {rec['expensive_core']['rent_lvl']:+.3f} (p={rec['expensive_core']['p_rl']:.3f}) | opp_lvl {rec['expensive_core']['opp_lvl']:+.3f} (p={rec['expensive_core']['p_opp']:.3f})")
    R.mkdir(parents=True,exist_ok=True)
    (R/"FOOD_redline_mechanism.json").write_text(json.dumps(out,indent=2))
    print(f"\nwritten: {R/'FOOD_redline_mechanism.json'}")


if __name__=="__main__":
    main()
