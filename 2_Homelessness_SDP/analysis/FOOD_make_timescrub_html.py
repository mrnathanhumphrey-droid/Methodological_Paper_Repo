"""Emit a self-contained interactive year-scrubber HTML (Plotly CDN, data inlined)
to figures/migration/. Scrub years -> watch the rent-floor gate (rent->homeless slope)
strengthen and regional differentiation emerge."""
import json
from pathlib import Path
data = json.load(open(r"D:\IDP\analysis\FOOD_timescrub_data.json"))
OUT = Path(r"D:\Migration\figures\migration\interactive_rent_gate_scrubber.html")
OUT.parent.mkdir(parents=True, exist_ok=True)

HTML = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>The rent-floor gate, 2012-2024 — an interactive displacement scrubber</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
 body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:0;background:#0f1117;color:#e7e9ee}
 .wrap{max-width:1000px;margin:0 auto;padding:24px}
 h1{font-size:22px;margin:0 0 4px} .sub{color:#9aa0ac;font-size:14px;margin:0 0 18px;line-height:1.4}
 #scrubber{height:560px} #trend{height:230px;margin-top:8px}
 .foot{color:#7b8190;font-size:12px;margin-top:14px;line-height:1.5;border-top:1px solid #262a33;padding-top:10px}
 b{color:#e9c46a}
</style></head><body><div class="wrap">
<h1>The rent-floor gate, tightening</h1>
<p class="sub">Each dot is a Continuum-of-Care region. Scrub the years and watch homelessness lock onto the <b>rent floor</b> &mdash;
the gate that converts the (everywhere-present) deprivation push into displacement. Color = region.
The push itself can't be seen in migration data; this is the terminus where it lands.</p>
<div id="scrubber"></div><div id="trend"></div>
<p class="foot">Source: HUD CoC PIT (homelessness, 2012&ndash;2024) &times; ACS CoC median gross rent. 2021 PIT unsheltered counts were COVID-disrupted (dip).
Food-insecurity (the other discharge axis) is state-resolved and not animatable by year, so it is reported as a static cross-section elsewhere.
Part of the RMD-SRC displacement cascade &mdash; seam closure locked by two independent clean runs.</p>
</div>
<script>
const DATA = __DATA__;
const COL = {South:"#e9c46a", Coast:"#9b5de5", Other:"#5c6370"};
const years = DATA.trend.map(t=>t.year);
function lsq(xs,ys){let n=xs.length,sx=0,sy=0,sxx=0,sxy=0;for(let i=0;i<n;i++){sx+=xs[i];sy+=ys[i];sxx+=xs[i]*xs[i];sxy+=xs[i]*ys[i];}
 let b=(n*sxy-sx*sy)/(n*sxx-sx*sx),a=(sy-b*sx)/n;return {a,b};}
function tracesFor(y){
 const pts=DATA.points[y]; const groups={};
 ["Other","South","Coast"].forEach(r=>{const g=pts.filter(p=>p.reg===r);
   groups[r]={x:g.map(p=>p.rent),y:g.map(p=>p.hom),text:g.map(p=>p.coc),mode:"markers",type:"scatter",name:r,
     marker:{color:COL[r],size:7,line:{color:"#0f1117",width:0.5},opacity:0.85},hovertemplate:"%{text}<br>rent $%{x}<br>%{y}/10k<extra></extra>"};});
 const xs=pts.map(p=>p.rent), ys=pts.map(p=>p.hom); const f=lsq(xs,ys);
 const xmin=Math.min(...xs),xmax=Math.max(...xs);
 const fit={x:[xmin,xmax],y:[f.a+f.b*xmin,f.a+f.b*xmax],mode:"lines",type:"scatter",name:"rent gate",
   line:{color:"#e76f51",width:3},hoverinfo:"skip"};
 return [groups.Other,groups.South,groups.Coast,fit];
}
const rByYear={}; DATA.trend.forEach(t=>rByYear[t.year]=t.r);
function annot(y){return [{x:0.03,y:0.97,xref:"paper",yref:"paper",showarrow:false,align:"left",
   text:`<b>${y}</b><br>rent &rarr; homeless  r = <b>${rByYear[y].toFixed(2)}</b>`,
   font:{size:18,color:"#e7e9ee"},bgcolor:"rgba(20,24,33,0.6)",borderpad:6}];}
const layout={paper_bgcolor:"#0f1117",plot_bgcolor:"#161a22",font:{color:"#c8ccd4"},
 margin:{l:60,r:20,t:30,b:50},xaxis:{title:"CoC median gross rent ($/mo)",gridcolor:"#262a33",range:[300,2300]},
 yaxis:{title:"homelessness / 10k",gridcolor:"#262a33",range:[0,95]},
 legend:{orientation:"h",y:1.08,x:0.5,xanchor:"center"},annotations:annot(years[0]),
 updatemenus:[{type:"buttons",x:0,y:-0.16,xanchor:"left",direction:"left",showactive:false,buttons:[
   {label:"▶ Play",method:"animate",args:[null,{fromcurrent:true,frame:{duration:650,redraw:true},transition:{duration:300}}]},
   {label:"❚❚ Pause",method:"animate",args:[[null],{mode:"immediate",frame:{duration:0,redraw:false}}]}]}],
 sliders:[{active:0,x:0.12,len:0.86,xanchor:"left",y:-0.13,currentvalue:{prefix:"year: ",font:{size:14,color:"#e9c46a"}},
   steps:years.map(y=>({label:String(y),method:"animate",args:[[String(y)],{mode:"immediate",frame:{duration:300,redraw:true},transition:{duration:200}}]}))}]};
Plotly.newPlot("scrubber",tracesFor(years[0]),layout,{responsive:true,displayModeBar:false}).then(()=>{
 Plotly.addFrames("scrubber",years.map(y=>({name:String(y),data:tracesFor(y),layout:{annotations:annot(y)}})));});
// trend chart: r by year (the gate strengthening)
Plotly.newPlot("trend",[{x:years,y:DATA.trend.map(t=>t.r),mode:"lines+markers",line:{color:"#e76f51",width:3},marker:{size:8,color:"#e9c46a"},hovertemplate:"%{x}: r=%{y}<extra></extra>"}],
 {paper_bgcolor:"#0f1117",plot_bgcolor:"#161a22",font:{color:"#c8ccd4"},margin:{l:60,r:20,t:24,b:34},
  title:{text:"rent &rarr; homeless correlation by year (the gate strengthening)",font:{size:13}},
  xaxis:{gridcolor:"#262a33"},yaxis:{title:"r",gridcolor:"#262a33",range:[0,0.4]},
  annotations:[{x:2021,y:0.20,text:"2021 COVID<br>PIT disruption",showarrow:true,arrowcolor:"#7b8190",font:{size:10,color:"#9aa0ac"},ay:-30}]},
 {responsive:true,displayModeBar:false});
</script></body></html>"""

OUT.write_text(HTML.replace("__DATA__", json.dumps(data)), encoding="utf-8")
print("wrote", OUT, "size", OUT.stat().st_size, "bytes; years", [t["year"] for t in data["trend"]])
