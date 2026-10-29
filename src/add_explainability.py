from pathlib import Path
import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "final_junction_risk.csv"
)

PLACES_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "osm_places.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "emergency_junction_hotspots.csv"
)


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def haversine_distance(lat, lon, lats, lons):
    """
    Calculate distance between one point and many points.
    Returns distance in kilometres.
    """

    earth_radius_km = 6371.0

    lat1 = np.radians(lat)
    lat2 = np.radians(lats)

    dlat = np.radians(lats - lat)
    dlon = np.radians(lons - lon)

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2) ** 2
    )

    return (
        2
        * earth_radius_km
        * np.arcsin(np.sqrt(a))
    )


# ============================================================
# FIND NEAREST AREA
# ============================================================

def find_nearest_place(latitude, longitude, places):

    distances = haversine_distance(
        latitude,
        longitude,
        places["latitude"].to_numpy(),
        places["longitude"].to_numpy()
    )

    nearest_index = int(np.argmin(distances))

    nearest_place = places.iloc[nearest_index]

    nearest_distance = float(
        distances[nearest_index]
    )

    return nearest_place, nearest_distance


# ============================================================
# CREATE RISK EXPLANATION
# ============================================================

def create_risk_explanation(row):

    reasons = []

    priority_score = float(
        row["priority_score"]
    )

    hospital_risk = float(
        row["hospital_access_risk"]
    )

    hospital_distance = float(
        row["nearest_hospital_distance_km"]
    )

    hospitals_within_5km = int(
        row["hospitals_within_5km"]
    )


    # Junction priority
    if priority_score >= 0.75:

        reasons.append(
            "Very high junction priority"
        )

    elif priority_score >= 0.50:

        reasons.append(
            "High junction priority"
        )

    elif priority_score >= 0.25:

        reasons.append(
            "Moderate junction priority"
        )


    # Hospital accessibility
    if hospital_risk >= 0.75:

        reasons.append(
            "Poor hospital accessibility"
        )

    elif hospital_risk >= 0.50:

        reasons.append(
            "Limited hospital accessibility"
        )


    # Hospital distance
    if hospital_distance >= 3:

        reasons.append(
            f"Nearest hospital is "
            f"{hospital_distance:.2f} km away"
        )


    # Hospitals within 5 km
    if hospitals_within_5km == 0:

        reasons.append(
            "No hospitals within 5 km"
        )

    elif hospitals_within_5km <= 2:

        reasons.append(
            f"Only {hospitals_within_5km} "
            f"hospital(s) within 5 km"
        )


    if not reasons:

        reasons.append(
            "No single dominant risk factor; "
            "location is lower priority for monitoring"
        )


    return " • ".join(reasons)


# ============================================================
# RECOMMENDED ACTION
# ============================================================

def create_recommendation(row):

    risk_category = row["risk_category"]

    priority_score = float(
        row["priority_score"]
    )

    hospital_risk = float(
        row["hospital_access_risk"]
    )

    hospital_distance = float(
        row["nearest_hospital_distance_km"]
    )

    hospitals_within_5km = int(
        row["hospitals_within_5km"]
    )


    # Critical + poor hospital access
    if (
        risk_category == "CRITICAL"
        and hospital_risk >= 0.75
    ):

        return (
            "Prioritize emergency-access assessment "
            "and healthcare coverage review."
        )


    # Critical / high junction priority
    if (
        risk_category in ["CRITICAL", "HIGH"]
        and priority_score >= 0.50
    ):

        return (
            "Prioritize traffic-flow and "
            "emergency-access investigation."
        )


    # Poor hospital coverage
    if (
        hospital_distance >= 3
        or hospitals_within_5km == 0
    ):

        return (
            "Review emergency healthcare accessibility "
            "and alternative access routes."
        )


    # Medium
    if risk_category == "MEDIUM":

        return (
            "Monitor and consider further "
            "emergency-access assessment."
        )


    # Low
    return (
        "Routine monitoring; reassess when "
        "traffic or incident data becomes available."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("       ADDING EXPLAINABILITY TO HOTSPOTS")
    print("=" * 60)


    # --------------------------------------------------------
    # Check files
    # --------------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )


    if not PLACES_FILE.exists():

        raise FileNotFoundError(
            f"OSM places file not found:\n{PLACES_FILE}"
        )


    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    print("\nLoading junction risk data...")

    df = pd.read_csv(INPUT_FILE)

    print(
        f"Junction records loaded: {len(df)}"
    )


    print("\nLoading OSM places...")

    places = pd.read_csv(PLACES_FILE)

    print(
        f"Named places loaded: {len(places)}"
    )


    # --------------------------------------------------------
    # Clean place coordinates
    # --------------------------------------------------------

    places["latitude"] = pd.to_numeric(
        places["latitude"],
        errors="coerce"
    )

    places["longitude"] = pd.to_numeric(
        places["longitude"],
        errors="coerce"
    )

    places = places.dropna(
        subset=["latitude", "longitude"]
    ).reset_index(drop=True)


    # --------------------------------------------------------
    # Match junctions to nearest named place
    # --------------------------------------------------------

    print("\nMatching junctions to nearby areas...")

    area_names = []
    area_types = []
    area_distances = []


    for _, row in df.iterrows():

        place, distance = find_nearest_place(
            float(row["latitude"]),
            float(row["longitude"]),
            places
        )

        area_names.append(
            str(place["name"])
        )

        area_types.append(
            str(place["place_type"])
        )

        area_distances.append(
            round(distance, 3)
        )


    df["area_name"] = area_names

    df["area_type"] = area_types

    df["area_match_distance_km"] = (
        area_distances
    )


    # --------------------------------------------------------
    # Explain risk
    # --------------------------------------------------------

    print("\nGenerating risk explanations...")

    df["risk_explanation"] = df.apply(
        create_risk_explanation,
        axis=1
    )


    # --------------------------------------------------------
    # Recommendations
    # --------------------------------------------------------

    print(
        "Generating recommended actions..."
    )

    df["recommended_action"] = df.apply(
        create_recommendation,
        axis=1
    )


    # --------------------------------------------------------
    # Data confidence
    # --------------------------------------------------------

    print(
        "Calculating data confidence..."
    )

    df["data_confidence"] = np.where(
        (
            df["area_match_distance_km"] <= 2
        )
        & (
            df["nearest_hospital_distance_km"]
            .notna()
        ),
        "Medium",
        "Low"
    )


    # --------------------------------------------------------
    # Data limitations
    # --------------------------------------------------------

    df["data_limitations"] = (
        "No live traffic, signal timing, road closure "
        "or validated historical emergency-response "
        "data in the base model."
    )


    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )


    print("\n" + "=" * 60)

    print(
        f"Saved: {OUTPUT_FILE}"
    )

    print(
        f"Final records: {len(df)}"
    )

    print("\nNew columns added:")

    print(
        "  area_name"
    )

    print(
        "  area_type"
    )

    print(
        "  area_match_distance_km"
    )

    print(
        "  risk_explanation"
    )

    print(
        "  recommended_action"
    )

    print(
        "  data_confidence"
    )

    print(
        "  data_limitations"
    )

    print("\nDONE.")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()