import pandas as pd
import numpy as np
from pathlib import Path


INPUT_PATH = Path(
    "data/processed/junction_hospital_access.csv"
)

OUTPUT_PATH = Path(
    "data/processed/junction_hospital_scores.csv"
)


print("==========================================")
print("       HOSPITAL ACCESS SCORING")
print("==========================================")

print("\nLoading hospital accessibility data...")

df = pd.read_csv(
    INPUT_PATH
)

print(
    "Junctions:",
    len(df)
)

# ---------------------------------------------------------
# Distance risk
#
# 0 km  -> low risk
# 5+ km -> maximum distance risk
# ---------------------------------------------------------

df[
    "distance_risk"
] = np.clip(
    df[
        "nearest_hospital_distance_km"
    ] / 5.0,
    0,
    1
)

# ---------------------------------------------------------
# Coverage risk
#
# 5 or more hospitals within 5 km
# gives minimum coverage risk.
# ---------------------------------------------------------

df[
    "coverage_score"
] = np.clip(
    df[
        "hospitals_within_5km"
    ] / 5.0,
    0,
    1
)

df[
    "coverage_risk"
] = (
    1 -
    df["coverage_score"]
)

# ---------------------------------------------------------
# Combined hospital access risk
#
# Distance is more important than raw count.
# ---------------------------------------------------------

df[
    "hospital_access_risk"
] = (
    0.70 *
    df["distance_risk"]
    +
    0.30 *
    df["coverage_risk"]
)

df[
    "hospital_accessibility_score"
] = (
    1 -
    df["hospital_access_risk"]
)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\n==========================================")
print("       HOSPITAL ACCESS SCORE RESULT")
print("==========================================")

print(
    "Junctions scored:",
    len(df)
)

print("\nScore statistics:")

print(
    df[
        [
            "hospital_access_risk",
            "hospital_accessibility_score"
        ]
    ]
    .describe()
    .to_string()
)

print("\nMost access-constrained junctions:")

print(
    df.sort_values(
        "hospital_access_risk",
        ascending=False
    )[
        [
            "junction_id",
            "nearest_hospital_name",
            "nearest_hospital_distance_km",
            "hospitals_within_5km",
            "hospital_access_risk"
        ]
    ]
    .head(20)
    .to_string(index=False)
)

print("\nSaved:")
print(OUTPUT_PATH)

print("\nDONE.")