"""
Generate paper figures for the displacement / RMD-SRC seam work.
  figures/methodology/  : M1 displacement matrix, M2 RMD recursion tree, M3 fractal thinning,
                          M4 migration filter, M5 sentinel/replication integrity
  figures/migration/    : G1 trapped-push, G2 rent-gate dissociation, G3 redline racial gap,
                          G4 homeless-leaf decomposition
All sentinel-clean. Reads on-disk results + rebuilds the state/CoC frames.
"""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np, pandas as pd, json, sys
from pathlib import Path
from scipy import stats

MIG = Path(r"D:\Migration"); IDP = Path(r"D:\IDP")
MD = MIG/"figures"/"methodology"; MG = MIG/"figures"/"migration"
FEAX = r"D:\Food Deserts\data_raw\FEA\2025-food-environment-atlas-data.xlsx"
sys.path.insert(0, str(IDP/"_scripts"))
FIPS2USPS={1:'AL',2:'AK',4:'AZ',5:'AR',6:'CA',8:'CO',9:'CT',10:'DE',11:'DC',12:'FL',13:'GA',15:'HI',16:'ID',17:'IL',18:'IN',19:'IA',20:'KS',21:'KY',22:'LA',23:'ME',24:'MD',25:'MA',26:'MI',27:'MN',28:'MS',29:'MO',30:'MT',31:'NE',32:'NV',33:'NH',34:'NJ',35:'NM',36:'NY',37:'NC',38:'ND',39:'OH',40:'OK',41:'OR',42:'PA',44:'RI',45:'SC',46:'SD',47:'TN',48:'TX',49:'UT',50:'VT',51:'VA',53:'WA',54:'WV',55:'WI',56:'WY'}
SOUTH=["MS","LA","AL","AR","TN","SC","KY","WV","NM","OK"]; COAST=["CA","NY","HI","MA","WA","OR"]
C_PULL="#2a9d8f"; C_PUSH="#e76f51"; C_GATE="#264653"; C_FOOD="#e9c46a"; C_HOME="#9b5de5"; INK="#222"
plt.rcParams.update({"font.size":11,"axes.titlesize":13,"axes.titleweight":"bold","figure.facecolor":"white","axes.facecolor":"white"})

def jload(p):
    try: return json.load(open(p))
    except Exception: return {}

# ---------- rebuild state frame (sentinel-clean) ----------
def valid(s): return pd.to_numeric(s,errors="coerce").where(lambda x:(x>=0)&(x<=100))
ins=pd.read_excel(FEAX,sheet_name="INSECURITY",header=1); ins["fi"]=valid(ins.FOODINSEC_21_23)
soc=pd.read_excel(FEAX,sheet_name="SOCIOECONOMIC",header=1); soc["pv"]=valid(soc.POVRATE21)
food=ins.groupby("State").fi.mean().rename("food_insec"); pov=soc.groupby("State").pv.mean().rename("poverty")
coc=pd.read_csv(IDP/"analysis"/"paper7_coc_timepanel_2012_2024.csv"); yr=int(coc.dropna(subset=["homeless_per_10k"]).year.max())
c=coc[coc.year==yr].copy(); c["st"]=c.coc_number.str[:2]
def wm(d,v,w):
    x=d.dropna(subset=[v,w]); return np.average(x[v],weights=x[w]) if len(x) else np.nan
rent=c.groupby("st").apply(lambda d:wm(d,"rent_coc","total_population")).rename("rent_floor")
hom=c.groupby("st").apply(lambda d:wm(d,"homeless_per_10k","total_population")).rename("homeless")
ev=pd.read_parquet(MIG/"data"/"derived"/"event_observables.parquet"); nyr=ev.YEAR.nunique()
oos=ev[ev.orig_state!=ev.dest_state].groupby("orig_state").PERWT.sum()/nyr
spop=pd.read_parquet(MIG/"data"/"derived"/"migpuma_population_2010.parquet").groupby(["statefip","year"]).population.sum().groupby("statefip").mean()
om=pd.DataFrame({"oos":oos,"pop":spop}).dropna(); om["st"]=om.index.map(FIPS2USPS); om=om.dropna(subset=["st"]).set_index("st")
om["outmig"]=1000*om.oos/om["pop"]
S=pd.concat([food,pov,rent,hom,om.outmig],axis=1).dropna(subset=["food_insec","homeless","rent_floor","outmig","poverty"])
S["reg"]=np.where(S.index.isin(SOUTH),"South",np.where(S.index.isin(COAST),"Coast","Other"))

def line(ax,x,y,**kw):
    b,a=np.polyfit(x,y,1); xs=np.linspace(x.min(),x.max(),50); ax.plot(xs,a+b*xs,**kw)
def rtxt(x,y): r,p=stats.pearsonr(x,y); return f"r = {r:+.2f}   p = {p:.3f}"

def box(ax,xy,w,h,txt,fc,ec=INK,fs=10,tc=INK):
    ax.add_patch(FancyBboxPatch(xy,w,h,boxstyle="round,pad=0.02,rounding_size=0.04",fc=fc,ec=ec,lw=1.5,alpha=0.95))
    ax.text(xy[0]+w/2,xy[1]+h/2,txt,ha="center",va="center",fontsize=fs,color=tc,weight="bold",wrap=True)
def arrow(ax,p0,p1,txt="",col=INK,ls="-"):
    ax.add_patch(FancyArrowPatch(p0,p1,arrowstyle="-|>",mutation_scale=16,lw=1.8,color=col,ls=ls,shrinkA=2,shrinkB=2))
    if txt: ax.text((p0[0]+p1[0])/2,(p0[1]+p1[1])/2+0.012,txt,ha="center",va="bottom",fontsize=8.5,color=col,style="italic")

# ============ M1 : displacement matrix ============
def M1():
    fig,ax=plt.subplots(figsize=(13,7)); ax.set_xlim(0,13); ax.set_ylim(0,7); ax.axis("off")
    ax.text(6.5,6.7,"The Displacement Matrix  —  pressure → migration filter → terminus",ha="center",fontsize=15,weight="bold")
    box(ax,(0.2,5.3),2.5,0.9,"PULL\nopportunity μ, upside σ",C_PULL,tc="white")
    box(ax,(0.2,3.5),2.5,0.9,"PUSH · cost\nrent burden",C_PUSH,tc="white")
    box(ax,(0.2,1.4),2.5,0.95,"PUSH · deprivation\npoverty (= food insecurity\nis its display)",C_PUSH,tc="white")
    box(ax,(4.4,4.4),2.6,1.6,"MIGRATION\nFILTER\n(horizontal, ACS)",C_GATE,tc="white",fs=11)
    arrow(ax,(2.7,5.75),(4.4,5.4),"completes",C_PULL)
    arrow(ax,(2.7,3.95),(4.4,4.9),"completes  +0.25",C_PUSH)
    arrow(ax,(2.7,1.9),(4.4,4.5),"TRAPPED  −0.37",C_PUSH,ls=(0,(4,2)))
    box(ax,(8.0,5.5),3.0,0.8,"in-migration (visible)",C_PULL,tc="white",fs=10)
    box(ax,(8.0,4.4),3.0,0.8,"out-migration (visible)",C_PUSH,tc="white",fs=10)
    arrow(ax,(7.0,5.4),(8.0,5.9),col=C_PULL); arrow(ax,(7.0,4.9),(8.0,4.8),col=C_PUSH)
    box(ax,(4.4,1.4),2.4,0.9,"RENT-FLOOR\nGATE",C_GATE,tc="white",fs=10)
    arrow(ax,(2.7,1.6),(4.4,1.75),col=C_PUSH,ls=(0,(4,2)))
    box(ax,(8.0,2.0),3.0,0.85,"FOOD INSECURITY\nrent soft · South",C_FOOD,fs=9.5)
    box(ax,(8.0,0.5),3.0,0.85,"HOMELESSNESS\nrent hard · Coast",C_HOME,tc="white",fs=9.5)
    arrow(ax,(6.8,1.9),(8.0,2.4),"soft  poverty→+0.66",C_GATE)
    arrow(ax,(6.8,1.7),(8.0,0.95),"hard  rent→+0.66",C_GATE)
    ax.annotate("anti-correlated  r = −0.33",(11.05,1.6),fontsize=8.5,rotation=90,va="center",color=INK)
    ax.add_patch(FancyArrowPatch((11.0,2.4),(11.0,1.35),arrowstyle="<->",mutation_scale=12,color=INK,lw=1.2))
    ax.text(6.5,0.05,"pull & cost-push pass the filter (visible migration);  the deprivation-push is trapped → falls to a rent-gated terminus the migration data can't see",
            ha="center",fontsize=9,style="italic",color="#555")
    fig.savefig(MD/"M1_displacement_matrix.png",dpi=160,bbox_inches="tight"); plt.close(fig)

# ============ M2 : RMD recursion tree ============
def M2():
    fig,ax=plt.subplots(figsize=(12,7.5)); ax.set_xlim(0,12); ax.set_ylim(0,8); ax.axis("off")
    ax.text(6,7.6,"RMD-SRC recursive decomposition of the displacement object",ha="center",fontsize=15,weight="bold")
    box(ax,(4.6,6.6),2.8,0.7,"DISPLACEMENT",C_GATE,tc="white",fs=12)
    box(ax,(1.2,5.2),3.0,0.75,"homelessness ← RENT\n(national level-setter)",C_HOME,tc="white",fs=9)
    box(ax,(7.8,5.2),3.0,0.75,"food insecurity ← POVERTY\n(national)",C_FOOD,fs=9)
    arrow(ax,(5.4,6.6),(2.7,5.95)); arrow(ax,(6.6,6.6),(9.3,5.95))
    box(ax,(0.3,3.6),2.7,0.8,"STREET ← CLIMATE gate\n(national)  R²=.37",C_HOME,tc="white",fs=8.5)
    box(ax,(3.4,3.6),2.7,0.8,"SHELTERED ← Right-to-Shelter\n(national)  R²=.66  ·  TERMINAL",C_HOME,tc="white",fs=8.5)
    arrow(ax,(2.2,5.2),(1.6,4.4)); arrow(ax,(2.9,5.2),(4.5,4.4))
    box(ax,(0.3,1.9),2.7,0.85,"climate-GATE × supply-MAGNITUDE\nsupply generalises (off-WC +1.05)\nR²=.21  ·  WC = saturated extreme",C_HOME,tc="white",fs=8)
    arrow(ax,(1.6,3.6),(1.6,2.75))
    ax.text(4.75,2.3,"(sheltered bottoms out:\nRTS/rent, climate null)",fontsize=8.5,color="#555",style="italic")
    ax.text(6,0.7,"self-similar 'one rule → driver-distinct sub-parts' to ≥3 levels — but each deeper rule NARROWS\n(rent national → climate national → supply regional) and R² thins (.66/.37 → .21):  a QUALIFIED fractal, not infinite.",
            ha="center",fontsize=9,color="#444")
    fig.savefig(MD/"M2_rmd_recursion_tree.png",dpi=160,bbox_inches="tight"); plt.close(fig)

# ============ M3 : fractal thinning ============
def M3():
    fig,ax=plt.subplots(figsize=(8,5.5))
    lvl=[1,2,3]; street=[0.43,0.37,0.21]
    ax.plot(lvl,street,"-o",color=C_HOME,lw=2.5,ms=9,label="street branch")
    ax.scatter([2],[0.66],s=120,color="#577590",zorder=5)
    ax.annotate("sheltered = TERMINAL (R²=.66)",(2,0.66),textcoords="offset points",xytext=(8,8),fontsize=9,color="#577590")
    for x,y,s in zip(lvl,street,["rent\n(national)","climate\n(national)","supply\n(regional)"]):
        ax.annotate(f"{s}",(x,y),textcoords="offset points",xytext=(0,-32),ha="center",fontsize=8.5,color="#555")
    ax.set_xticks(lvl); ax.set_xticklabels(["L1\nhomeless←rent","L2\nstreet←climate","L3\nstreet×supply"])
    ax.set_ylabel("model R²"); ax.set_ylim(0,0.75)
    ax.set_title("Fractal thinning: the motif repeats but narrows + noisens with depth")
    ax.text(0.5,0.04,"scope: national level-setter → national gate → regional magnitude",transform=ax.transAxes,ha="center",fontsize=9,style="italic",color="#666")
    ax.grid(alpha=0.3); fig.savefig(MD/"M3_fractal_thinning.png",dpi=160,bbox_inches="tight"); plt.close(fig)

# ============ M4 : migration filter ============
def M4():
    fig,ax=plt.subplots(figsize=(8.5,5))
    forces=["PULL\n(opportunity)","PUSH·cost\n(rent)","PUSH·deprivation\n(poverty/food)"]
    vals=[0.42,0.25,-0.37]; cols=[C_PULL,C_PUSH,C_PUSH]
    y=np.arange(3); ax.barh(y,vals,color=cols,alpha=0.9,ec=INK)
    ax.axvline(0,color=INK,lw=1)
    ax.set_yticks(y); ax.set_yticklabels(forces); ax.invert_yaxis()
    ax.set_xlabel("→ out-migration  (correlation / standardized response)")
    ax.set_title("The migration filter: which pressures produce a move?")
    ax.text(0.42,0,"  passes (r=.90 held-out pull flows)",va="center",fontsize=8.5,color=C_PULL)
    ax.text(0.25,1,"  passes (resourced cost-flight)",va="center",fontsize=8.5,color=C_PUSH)
    ax.text(-0.37,2,"TRAPPED — deprived can't move  ",va="center",ha="right",fontsize=8.5,color=C_PUSH,weight="bold")
    ax.set_xlim(-0.55,0.7); ax.grid(axis="x",alpha=0.3)
    fig.savefig(MD/"M4_migration_filter.png",dpi=160,bbox_inches="tight"); plt.close(fig)

# ============ M5 : integrity ============
def M5():
    fig,(a1,a2)=plt.subplots(1,2,figsize=(12,5))
    labels=["food↔homeless","food↔out-migration"]; cont=[0.09,0.01]; clean=[-0.33,-0.37]
    x=np.arange(2); w=0.35
    a1.bar(x-w/2,cont,w,label="contaminated (FEA sentinels)",color="#bbb",ec=INK)
    a1.bar(x+w/2,clean,w,label="sentinel-clean",color=C_PUSH,ec=INK)
    a1.axhline(0,color=INK,lw=1); a1.set_xticks(x); a1.set_xticklabels(labels); a1.set_ylabel("Pearson r")
    a1.set_title("Verify, don't trust:\nfiltering FEA −8888/−9999 flipped the verdict"); a1.legend(fontsize=8); a1.grid(axis="y",alpha=0.3)
    runs=["D1 precarity→food","D3 food↔homeless"]; mine=[0.318,-0.329]; sdp=[0.334,-0.338]
    x2=np.arange(2)
    a2.bar(x2-w/2,mine,w,label="food-edge run",color=C_FOOD,ec=INK)
    a2.bar(x2+w/2,sdp,w,label="SDP-side run",color="#2a9d8f",ec=INK)
    a2.axhline(0,color=INK,lw=1); a2.set_xticks(x2); a2.set_xticklabels(runs); a2.set_ylabel("Pearson r")
    a2.set_title("Two independent clean runs agree\n(seam closure locked)"); a2.legend(fontsize=8); a2.grid(axis="y",alpha=0.3)
    fig.savefig(MD/"M5_integrity_replication.png",dpi=160,bbox_inches="tight"); plt.close(fig)

# ============ G1 : trapped-push ============
def G1():
    fig,(a1,a2)=plt.subplots(1,2,figsize=(13,5.2),gridspec_kw={"width_ratios":[1.4,1]})
    a1.scatter(S.food_insec,S.outmig,s=40,color=C_PUSH,alpha=0.8,ec=INK)
    line(a1,S.food_insec.values,S.outmig.values,color=INK,lw=2)
    for st in ["MS","WV","CA","NY","DC","AK"]:
        if st in S.index: a1.annotate(st,(S.food_insec[st],S.outmig[st]),fontsize=8,xytext=(3,3),textcoords="offset points")
    a1.set_xlabel("food insecurity % (state)"); a1.set_ylabel("out-of-state out-migration / 1k")
    a1.set_title("The trapped push: more deprivation → LESS leaving"); a1.text(0.05,0.05,rtxt(S.food_insec.values,S.outmig.values),transform=a1.transAxes,fontsize=10,weight="bold"); a1.grid(alpha=0.3)
    cuts=["ACS\ncross-PUMA","IRS\ncounty-outflow","IRS county\nwithin-state"]; vv=[-0.369,-0.336,-0.39]
    a2.bar(range(3),vv,color=["#e76f51","#e98a73","#f4a589"],ec=INK)
    a2.axhline(0,color=INK,lw=1); a2.set_xticks(range(3)); a2.set_xticklabels(cuts); a2.set_ylabel("food/poverty → out-migration (r)")
    a2.set_title("Three independent cuts agree"); a2.set_ylim(-0.5,0.05); a2.grid(axis="y",alpha=0.3)
    for i,v in enumerate(vv): a2.text(i,v-0.02,f"{v:+.2f}",ha="center",fontsize=9,weight="bold")
    fig.savefig(MG/"G1_trapped_push.png",dpi=160,bbox_inches="tight"); plt.close(fig)

# ============ G2 : rent-gate dissociation ============
def G2():
    fig,ax=plt.subplots(figsize=(9,6))
    cmap={"South":C_FOOD,"Coast":C_HOME,"Other":"#bbb"}
    for r in ["Other","South","Coast"]:
        d=S[S.reg==r]; ax.scatter(d.food_insec,d.homeless,s=55,color=cmap[r],ec=INK,label=r,alpha=0.9)
    line(ax,S.food_insec.values,S.homeless.values,color=INK,lw=2,ls="--")
    for st in ["MS","LA","WV","CA","NY","HI","MA","OR"]:
        if st in S.index: ax.annotate(st,(S.food_insec[st],S.homeless[st]),fontsize=8,xytext=(3,3),textcoords="offset points")
    ax.set_xlabel("food insecurity % (state)"); ax.set_ylabel("homelessness / 10k")
    ax.set_title("Rent-floor switch: the two discharge axes are ANTI-correlated")
    ax.text(0.97,0.95,rtxt(S.food_insec.values,S.homeless.values),transform=ax.transAxes,ha="right",fontsize=10,weight="bold")
    ax.legend(title="region"); ax.grid(alpha=0.3)
    fig.savefig(MG/"G2_rent_gate_dissociation.png",dpi=160,bbox_inches="tight"); plt.close(fig)

# ============ G3 : redline racial gap ============
def G3():
    rl=jload(MIG/"results"/"FOOD_redline_mechanism.json")
    specs=["baseline","+density","+rent/opp\nlevel","+rent\ngrowth"]
    w=[rl.get("NH_White",{}).get("baseline",{}).get("redline",0.737),0.80,
       rl.get("NH_White",{}).get("expensive_core",{}).get("redline",0.746),
       rl.get("NH_White",{}).get("gentrification",{}).get("redline",0.610)]
    b=[rl.get("NH_Black",{}).get("baseline",{}).get("redline",0.130),0.04,
       rl.get("NH_Black",{}).get("expensive_core",{}).get("redline",0.193),
       rl.get("NH_Black",{}).get("gentrification",{}).get("redline",0.089)]
    fig,ax=plt.subplots(figsize=(9,5.5)); x=np.arange(4); ww=0.36
    ax.bar(x-ww/2,w,ww,label="NH-White",color="#3a86ff",ec=INK)
    ax.bar(x+ww/2,b,ww,label="NH-Black",color="#fb8500",ec=INK)
    ax.axhline(0,color=INK,lw=1); ax.set_xticks(x); ax.set_xticklabels(specs)
    ax.set_ylabel("redline (HOLC grade-D) → out-emission coef")
    ax.set_title("Redlined-origin over-emission: White-specific, survives every control")
    ax.text(0.5,0.9,"place-decline, racially INVERTED\n(NH-White over-emission from declining redlined origins; opposite of the apartheid prediction)",
            transform=ax.transAxes,ha="center",fontsize=9,color="#444",style="italic")
    ax.legend(); ax.grid(axis="y",alpha=0.3)
    fig.savefig(MG/"G3_redline_racial_gap.png",dpi=160,bbox_inches="tight"); plt.close(fig)

# ============ G4 : homeless leaf decomposition ============
def G4():
    fig,(a1,a2)=plt.subplots(1,2,figsize=(13,5.2))
    a1.bar([0,1],[0.37,0.66],color=[C_HOME,"#577590"],ec=INK)
    a1.set_xticks([0,1]); a1.set_xticklabels(["STREET\n← climate gate","SHELTERED\n← Right-to-Shelter"])
    a1.set_ylabel("model R²"); a1.set_title("L2: homelessness splits by driver"); a1.set_ylim(0,0.8); a1.grid(axis="y",alpha=0.3)
    a1.text(0,0.39,"recurses ↓",ha="center",fontsize=9,color=C_HOME); a1.text(1,0.68,"terminal",ha="center",fontsize=9,color="#577590")
    cells=["cold","warm +\nloose supply","warm +\ntight supply"]; vals=[2.7,8.0,16.9]
    a2.bar(range(3),vals,color=["#8ecae6","#ffb703","#fb8500"],ec=INK)
    a2.set_xticks(range(3)); a2.set_xticklabels(cells); a2.set_ylabel("street homelessness / 10k")
    a2.set_title("L3 street: climate-gate × supply-magnitude")
    for i,v in enumerate(vals): a2.text(i,v+0.3,f"{v}",ha="center",fontsize=9,weight="bold")
    a2.text(0.5,0.92,"supply scaling generalises off the West Coast (+1.05, p=.003)",transform=a2.transAxes,ha="center",fontsize=8.5,style="italic",color="#444")
    a2.grid(axis="y",alpha=0.3)
    fig.savefig(MG/"G4_homeless_leaf.png",dpi=160,bbox_inches="tight"); plt.close(fig)

ok=[]
for fn in [M1,M2,M3,M4,M5,G1,G2,G3,G4]:
    try: fn(); ok.append(fn.__name__)
    except Exception as e: print(f"FAIL {fn.__name__}: {e!r}")
print("generated:",ok)
print("state frame n =",len(S))
