import time, sys
import numpy as np, pandas as pd, statsmodels.api as sm
sys.path.insert(0, r"src\rmd_src")
import netfield_stageA as m

geo = pd.read_parquet(m.DERIVED / "migpuma_geometry_2010.parquet")
tr = m.build_design(m.TRAIN, geo, len(m.TRAIN))
print(f"design rows={len(tr)}", flush=True)
cols = ["log_mass_o", "log_mass_d", "log_dist", "dN"]
X = sm.add_constant(tr[cols].to_numpy(float))
y = tr.flow.to_numpy(float)
off = tr.offset.to_numpy(float)

t = time.time()
res_plain = sm.GLM(y, X, family=sm.families.Poisson(), offset=off).fit()
print(f"PLAIN fit: {time.time()-t:.1f}s  betas={np.round(res_plain.params,4).tolist()}", flush=True)

t = time.time()
res_cl = sm.GLM(y, X, family=sm.families.Poisson(), offset=off).fit(
    cov_type="cluster", cov_kwds={"groups": tr.grp.to_numpy()})
print(f"CLUSTER fit: {time.time()-t:.1f}s  bN p={res_cl.pvalues[-1]:.2e}", flush=True)
print("DONE", flush=True)
