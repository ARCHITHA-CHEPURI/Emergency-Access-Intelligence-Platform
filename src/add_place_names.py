from pathlib import Path
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree

# ==========================================
#     ADD AREA NAMES TO JUNCTIONS
# ==========================================

print("==========================================")
print("      ADDING AREA NAMES TO JUNCTIONS")
print("==========================================")

BASE_DIR = Path(__file__).resolve().parent.parent

JUNCTION_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "emergency_junction_hotspots.csv"
)

PLACE_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "osm_places.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "emergency_junctions_named.csv"
)

# ==========================================
# LOAD DATA
# ==========================================

print("\nLoading junction data...")

junctions = pd.read_csv(JUNCTION_FILE)

print(f"Junctions: {len(junctions)}")

print("\nLoading OSM places...")

places = pd.read_csv(PLACE_FILE)

print(f"OSM places: {len(places)}")

# ==========================================
# CLEAN PLACE DATA
# ==========================================

places = places.dropna(
    subset=["latitude", "longitude", "name"]
).copy()

junctions = junctions.dropna(
    subset=["latitude", "longitude"]
).copy()

print(f"\nUsable places: {len(places)}")
print(f"Usable junctions: {len(junctions)}")

# ==========================================
# BUILD SPATIAL INDEX
# ==========================================

print("\nBuilding spatial index...")

place_coordinates = places[
    ["latitude", "longitude"]
].to_numpy()

tree = cKDTree(place_coordinates)

# ==========================================
# FIND NEAREST PLACE
# ==========================================

print("Finding nearest named area for every junction...")

junction_coordinates = junctions[
    ["latitude", "longitude"]
].to_numpy()

distances, indices = tree.query(
    junction_coordinates,
    k=1
)

nearest_places = places.iloc[indices].reset_index(drop=True)

# ==========================================
# APPROXIMATE DISTANCE
# ==========================================

# Convert degree distance to approximate km.
# 1 degree latitude ~= 111 km.

distance_km = distances * 111.0

junctions["nearby_area"] = nearest_places["name"].values
junctions["nearby_area_type"] = nearest_places["place_type"].values
junctions["area_distance_km"] = np.round(
    distance_km,
    3
)

# ==========================================
# USER-FRIENDLY LOCATION
# ==========================================

junctions["location_label"] = (
    junctions["nearby_area"]
    + " area"
)

# ==========================================
# SAVE
# ==========================================

junctions.to_csv(
    OUTPUT_FILE,
    index=False
)

# ==========================================
# RESULT
# ==========================================

print("\n==========================================")
print("       AREA NAME RESULT")
print("==========================================")

print(f"Junctions processed: {len(junctions)}")

print("\nSample named junctions:")

sample_columns = [
    "final_risk_rank",
    "junction_id",
    "nearby_area",
    "nearby_area_type",
    "area_distance_km",
    "final_risk_score",
    "risk_category"
]

print(
    junctions[sample_columns]
    .head(20)
    .to_string(index=False)
)

print("\nSaved:")
print(OUTPUT_FILE)

print("\nDONE.")