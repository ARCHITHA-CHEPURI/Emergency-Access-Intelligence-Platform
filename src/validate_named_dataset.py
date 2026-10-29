from pathlib import Path
import pandas as pd

# ==========================================
#       VALIDATE NAMED DATASET
# ==========================================

print("==========================================")
print("       NAMED DATASET VALIDATION")
print("==========================================")

BASE_DIR = Path(__file__).resolve().parent.parent

FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "emergency_junctions_named.csv"
)

df = pd.read_csv(FILE)

print(f"\nTotal junctions: {len(df)}")

required_columns = [
    "junction_id",
    "nearby_area",
    "nearby_area_type",
    "area_distance_km",
    "location_label",
    "final_risk_score",
    "risk_category"
]

missing = [
    col for col in required_columns
    if col not in df.columns
]

print("\nMissing required columns:", missing)

print("\nMissing area names:")
print(
    df["nearby_area"]
    .isna()
    .sum()
)

print("\nArea types:")
print(
    df["nearby_area_type"]
    .value_counts()
)

print("\nSample locations:")

print(
    df[
        [
            "final_risk_rank",
            "junction_id",
            "nearby_area",
            "nearby_area_type",
            "area_distance_km",
            "risk_category"
        ]
    ]
    .head(20)
    .to_string(index=False)
)

if not missing and df["nearby_area"].notna().all():
    print("\n==========================================")
    print("       VALIDATION RESULT")
    print("==========================================")
    print("STATUS: PASS")
else:
    print("\nSTATUS: CHECK REQUIRED")

print("\nDONE.")