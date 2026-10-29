import pandas as pd
import json
import os

print("=" * 50)
print("       GEOJSON HOTSPOT GENERATION")
print("=" * 50)

INPUT = "data/processed/emergency_junction_hotspots.csv"
OUTPUT = "data/processed/emergency_hotspots.geojson"

print("\nLoading emergency hotspot dataset...")

df = pd.read_csv(INPUT)

print(f"Records loaded: {len(df)}")

features = []

for _, row in df.iterrows():

    properties = {
        "final_risk_rank": int(row["final_risk_rank"]),
        "junction_id": str(row["junction_id"]),
        "priority_score": round(float(row["priority_score"]), 6),
        "hospital_access_risk": round(
            float(row["hospital_access_risk"]), 6
        ),
        "nearest_hospital_distance_km": round(
            float(row["nearest_hospital_distance_km"]), 3
        ),
        "hospitals_within_5km": int(row["hospitals_within_5km"]),
        "final_risk_score": round(
            float(row["final_risk_score"]), 6
        ),
        "risk_category": str(row["risk_category"]),
        "emergency_priority": str(row["emergency_priority"])
    }

    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [
                float(row["longitude"]),
                float(row["latitude"])
            ]
        },
        "properties": properties
    }

    features.append(feature)

geojson = {
    "type": "FeatureCollection",
    "features": features
}

os.makedirs(
    os.path.dirname(OUTPUT),
    exist_ok=True
)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(geojson, f, indent=2)

print("\n" + "=" * 50)
print("       GEOJSON GENERATION RESULT")
print("=" * 50)

print(f"Features created: {len(features)}")
print("\nSaved:")
print(OUTPUT)

print("\nDONE.")