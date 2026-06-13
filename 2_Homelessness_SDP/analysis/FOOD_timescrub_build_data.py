"""Build per-year data for the interactive rent-gate scrubber.
CoC PIT homelessness x ACS CoC rent, 2012-2024 -> per-year points + rent->homeless r/slope.
Output: analysis/FOOD_timescrub_data.json (consumed by FOOD_make_timescrub_html.py)."""
import pandas as pd, numpy as np, json
from scipy import stats
coc = pd.read_csv(r"D:\IDP\analysis\paper7_coc_timepanel_2012_2024.csv")
coc["st"] = coc.coc_number.str[:2]
SOUTH = {"MS","LA","AL","AR","TN","SC","KY","WV","NM","OK"}; COAST = {"CA","NY","HI","MA","WA","OR"}
region = lambda s: "South" if s in SOUTH else ("Coast" if s in COAST else "Other")
trend, points = [], {}
for y, g in coc.groupby("year"):
    d = g.dropna(subset=["homeless_per_10k", "rent_coc"])
    if len(d) < 30: continue
    r, _ = stats.pearsonr(d.rent_coc, d.homeless_per_10k)
    slope = float(np.polyfit(d.rent_coc, d.homeless_per_10k, 1)[0])
    trend.append({"year": int(y), "r": round(float(r), 3), "slope": round(slope, 5), "n": int(len(d))})
    points[int(y)] = [{"rent": round(float(rr.rent_coc), 0), "hom": round(float(rr.homeless_per_10k), 1),
                       "reg": region(rr.st), "coc": rr.coc_number} for _, rr in d.iterrows()]
json.dump({"trend": trend, "points": points}, open(r"D:\IDP\analysis\FOOD_timescrub_data.json", "w"))
print("years", [t["year"] for t in trend], "| r range", min(t["r"] for t in trend), "->", max(t["r"] for t in trend))
