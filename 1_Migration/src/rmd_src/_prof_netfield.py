import time, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, r"src\rmd_src")
import netfield_stageA as m

D = m.DERIVED
years = m.TRAIN
print("start", flush=True)
t = time.time(); f = m.place_field(years)
print(f"place_field: {time.time()-t:.1f}s rows={len(f)} dup={int(f.duplicated(['statefip','migpuma']).sum())}", flush=True)
t = time.time(); mass = m.place_mass(years)
print(f"place_mass: {time.time()-t:.1f}s rows={len(mass)} dup={int(mass.duplicated(['statefip','migpuma']).sum())}", flush=True)
geo = pd.read_parquet(D / "migpuma_geometry_2010.parquet")
print(f"geo rows={len(geo)} dup={int(geo.duplicated(['statefip','migpuma']).sum())}", flush=True)
t = time.time(); ev = pd.read_parquet(D / "event_observables.parquet"); od = m.corridor_flows(ev, years)
print(f"corridor_flows: {time.time()-t:.1f}s rows={len(od)}", flush=True)

t = time.time()
o = f.add_prefix("o_").rename(columns={"o_statefip": "orig_state", "o_migpuma": "orig_migpuma"})
d = f.add_prefix("d_").rename(columns={"d_statefip": "dest_state", "d_migpuma": "dest_migpuma"})
od = od.merge(o, on=["orig_state", "orig_migpuma"], how="inner")
od = od.merge(d, on=["dest_state", "dest_migpuma"], how="inner")
print(f"merge field: {time.time()-t:.1f}s rows={len(od)}", flush=True)
t = time.time()
mo = mass.rename(columns={"statefip": "orig_state", "migpuma": "orig_migpuma", "mass": "mass_o"})
md = mass.rename(columns={"statefip": "dest_state", "migpuma": "dest_migpuma", "mass": "mass_d"})
od = od.merge(mo, on=["orig_state", "orig_migpuma"], how="inner")
od = od.merge(md, on=["dest_state", "dest_migpuma"], how="inner")
print(f"merge mass: {time.time()-t:.1f}s rows={len(od)}", flush=True)
t = time.time()
g = geo.set_index(["statefip", "migpuma"])[["lon", "lat"]]
od = od.join(g.rename(columns={"lon": "o_lon", "lat": "o_lat"}), on=["orig_state", "orig_migpuma"])
od = od.join(g.rename(columns={"lon": "d_lon", "lat": "d_lat"}), on=["dest_state", "dest_migpuma"])
print(f"join geo: {time.time()-t:.1f}s rows={len(od)}", flush=True)
print("DONE", flush=True)
