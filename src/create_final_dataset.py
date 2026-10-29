import pandas as pd
from pathlib import Path

INPUT_PATH = Path(
    "data/processed/final_junction_risk.csv"
)

OUTPUT_PATH = Path(
    "data/processed/emergency_junction_hotspots.csv"
)

print("==========================================")
print("      FINAL EMERGENCY HOTSPOT DATASET")
print("==========================================")

df = pd.read_csv(INPUT_PATH)

# ---------------------------------------------------------
# Keep useful fields for the final application
# ---------------------------------------------------------

columns = [
    "final_risk_rank",
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

missing = [
    c for c in columns
    if c not in df.columns
]

if missing:
    raise ValueError(
        f"Missing columns: {missing}"
    )

final = df[columns].copy()

# ---------------------------------------------------------
# Sort by risk
# ---------------------------------------------------------

final = final.sort_values(
    "final_risk_rank"
)

# ---------------------------------------------------------
# Add human-readable emergency priority
# ---------------------------------------------------------

def emergency_priority(category):

    if category == "CRITICAL":
        return "Immediate attention"

    if category == "HIGH":
        return "High attention"

    if category == "MEDIUM":
        return "Monitor"

    return "Low priority"


final["emergency_priority"] = (
    final["risk_category"]
    .apply(emergency_priority)
)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

final.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\nFinal records:", len(final))

print("\nFinal columns:")
for column in final.columns:
    print(" ", column)

print("\nTop 10 emergency hotspots:")

print(
    final.head(10).to_string(index=False)
)

print("\nSaved:")
print(OUTPUT_PATH)

print("\nDONE.")