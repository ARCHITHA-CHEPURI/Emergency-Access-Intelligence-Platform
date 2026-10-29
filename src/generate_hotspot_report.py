import pandas as pd
from pathlib import Path

INPUT_PATH = Path(
    "data/processed/final_junction_risk.csv"
)

OUTPUT_PATH = Path(
    "data/processed/top_50_risk_junctions.csv"
)

print("==========================================")
print("       TOP RISK JUNCTION REPORT")
print("==========================================")

df = pd.read_csv(INPUT_PATH)

# Sort by final risk
top = (
    df.sort_values(
        "final_risk_score",
        ascending=False
    )
    .head(50)
    .copy()
)

top["hotspot_rank"] = range(1, len(top) + 1)

columns = [
    "hotspot_rank",
    "junction_id",
    "longitude",
    "latitude",
    "priority_score",
    "hospital_access_risk",
    "nearest_hospital_distance_km",
    "hospitals_within_5km",
    "final_risk_score",
    "risk_category"
]

top = top[columns]

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

top.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\nTop 50 risk junctions:")

print(
    top.head(20).to_string(index=False)
)

print("\nSaved:")
print(OUTPUT_PATH)

print("\nDONE.")