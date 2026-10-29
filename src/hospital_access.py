import pandas as pd
import numpy as np

from pathlib import Path
from sklearn.neighbors import BallTree


PRIORITY_PATH = Path(
    "data/processed/priority_junctions.csv"
)

HOSPITAL_PATH = Path(
    "data/processed/hospitals_clean.csv"
)

OUTPUT_PATH = Path(
    "data/processed/junction_hospital_access.csv"
)

EARTH_RADIUS_KM = 6371.0088


print("==========================================")
print("       HOSPITAL ACCESSIBILITY ANALYSIS")
print("==========================================")

# ---------------------------------------------------------
# Load priority junctions
# ---------------------------------------------------------

print("\nLoading priority junctions...")

junctions = pd.read_csv(
    PRIORITY_PATH
)

print(
    "Priority junctions:",
    len(junctions)
)

# ---------------------------------------------------------
# Load hospitals
# ---------------------------------------------------------

print("\nLoading hospitals...")

hospitals = pd.read_csv(
    HOSPITAL_PATH
)

print(
    "Hospitals:",
    len(hospitals)
)

# ---------------------------------------------------------
# Required columns
# ---------------------------------------------------------

required_junction_columns = [
    "junction_id",
    "longitude",
    "latitude"
]

required_hospital_columns = [
    "hospital_id",
    "name",
    "longitude",
    "latitude"
]

for col in required_junction_columns:
    if col not in junctions.columns:
        raise ValueError(
            f"Priority junction file missing: {col}"
        )

for col in required_hospital_columns:
    if col not in hospitals.columns:
        raise ValueError(
            f"Hospital file missing: {col}"
        )

# ---------------------------------------------------------
# Clean coordinates
# ---------------------------------------------------------

junctions["longitude"] = pd.to_numeric(
    junctions["longitude"],
    errors="coerce"
)

junctions["latitude"] = pd.to_numeric(
    junctions["latitude"],
    errors="coerce"
)

hospitals["longitude"] = pd.to_numeric(
    hospitals["longitude"],
    errors="coerce"
)

hospitals["latitude"] = pd.to_numeric(
    hospitals["latitude"],
    errors="coerce"
)

junctions = junctions.dropna(
    subset=["longitude", "latitude"]
).copy()

hospitals = hospitals.dropna(
    subset=["longitude", "latitude"]
).copy()

# ---------------------------------------------------------
# Convert coordinates to radians
# BallTree haversine expects radians.
# ---------------------------------------------------------

junction_coords = np.radians(
    junctions[
        ["latitude", "longitude"]
    ].values
)

hospital_coords = np.radians(
    hospitals[
        ["latitude", "longitude"]
    ].values
)

# ---------------------------------------------------------
# Build spatial tree
# ---------------------------------------------------------

print("\nBuilding hospital spatial index...")

tree = BallTree(
    hospital_coords,
    metric="haversine"
)

# ---------------------------------------------------------
# Find nearest hospital
# ---------------------------------------------------------

print(
    "\nFinding nearest hospital for each junction..."
)

distances, indices = tree.query(
    junction_coords,
    k=1
)

nearest_distance_km = (
    distances[:, 0] *
    EARTH_RADIUS_KM
)

nearest_indices = indices[:, 0]

junctions[
    "nearest_hospital_id"
] = hospitals.iloc[
    nearest_indices
]["hospital_id"].values

junctions[
    "nearest_hospital_name"
] = hospitals.iloc[
    nearest_indices
]["name"].values

junctions[
    "nearest_hospital_distance_km"
] = np.round(
    nearest_distance_km,
    3
)

# ---------------------------------------------------------
# Count hospitals within different radii
# ---------------------------------------------------------

print("\nCalculating hospital coverage...")

for radius_km in [1, 2, 5]:

    radius_radians = (
        radius_km /
        EARTH_RADIUS_KM
    )

    counts = tree.query_radius(
        junction_coords,
        r=radius_radians,
        count_only=True
    )

    junctions[
        f"hospitals_within_{radius_km}km"
    ] = counts.astype(int)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

junctions.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\n==========================================")
print("       HOSPITAL ACCESS RESULT")
print("==========================================")

print(
    "Junctions analyzed:",
    len(junctions)
)

print(
    "Hospitals analyzed:",
    len(hospitals)
)

print("\nSample results:")

print(
    junctions[
        [
            "junction_id",
            "latitude",
            "longitude",
            "nearest_hospital_name",
            "nearest_hospital_distance_km",
            "hospitals_within_1km",
            "hospitals_within_2km",
            "hospitals_within_5km"
        ]
    ]
    .head(20)
    .to_string(index=False)
)

print("\nSaved:")
print(OUTPUT_PATH)

print("\nDONE.")