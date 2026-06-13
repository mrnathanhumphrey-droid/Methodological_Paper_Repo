# Chrome handoff status — 2026-05-21

## Completed
- **EM-DAT** ✓ — `public_emdat_incl_hist_2026-05-18.xlsx` landed at `data/emdat/` (8.7 MB)
- **Copernicus CDS API key** ✓ — written to `~/.cdsapirc`

## Pending licence step (one-click)
- **ERA5 dataset licences** — visit https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means?tab=download#manage-licences and accept all required licences. Without this the API job will 403 "required licences not accepted." Will retry the ERA5 fetch after.

## Pending registration approvals
- **ReliefWeb appname** submitted as `ResolveResearch+IDP+jpofjd$%`. **~2 day approval window.** Until approved, ReliefWeb API returns 403 "not using an approved appname." Retry the disasters + reports endpoints after approval.

## Still to action
- **IDMC direct API key** — request `client_id` via web form at https://www.internal-displacement.org/database/api-documentation/. Not blocking; HDX mirror works.
- **ACAPS API token** — subscribe at https://api.acaps.org/. Not blocking; HDX mirror works.
- **GTD** — registration at https://www.start.umd.edu/gtd-download. Likely closed as of 2025 per recon. If denied, drop and rely on UCDP-GED + GDELT.
- **MICS** — register at https://mics.unicef.org/surveys for per-country household surveys. Defer until threads emerge.
- **DHS Program** — per-project proposal at https://dhsprogram.com/. Defer until threads emerge (1-2 week approval).
