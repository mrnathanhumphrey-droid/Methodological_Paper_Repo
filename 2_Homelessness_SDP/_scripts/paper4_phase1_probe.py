"""Probe UCDP-GED v25 + cluster panels for P4-C classifier setup."""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding="utf-8")

UCDP = "D:/IDP/data/ucdp/GEDEvent_v25_1.csv"
print("=== UCDP-GED v25 ===")
# Read just header + sample
u = pd.read_csv(UCDP, nrows=5)
print(f"Columns: {list(u.columns)}")
print(u.head(3))
print()

# Read more fully to check ISO3 + violence type
u = pd.read_csv(UCDP, usecols=["country", "country_id", "year", "type_of_violence",
                                "deaths_a", "deaths_b", "deaths_civilians", "deaths_unknown",
                                "best", "high", "low",
                                "adm_1", "side_a", "side_b"])
print(f"Total rows: {len(u)}")
print(f"Years: {u['year'].min()}-{u['year'].max()}")
print(f"violence types: {sorted(u['type_of_violence'].dropna().unique().tolist())}")
print(f"Sample country names: {u['country'].drop_duplicates().head(10).tolist()}")

# Count events 2020-2024 by violence type
u24 = u[u["year"].between(2020, 2024)]
print(f"\n2020-2024 events by violence type:")
print(u24.groupby("type_of_violence")["best"].agg(["count", "sum"]))
