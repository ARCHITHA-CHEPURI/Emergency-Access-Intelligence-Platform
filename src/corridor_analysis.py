from pathlib import Path
import math
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "emergency_junction_hotspots.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "emergency_corridors.csv"
)


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def haversine_distance(lat1, lon1, lat2, lon2):

    earth_radius_km = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlat = lat2 - lat1
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return (
        2
        * earth_radius_km
        * math.asin(math.sqrt(a))
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("          EMERGENCY CORRIDOR ANALYSIS")
    print("=" * 60)

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print(
        f"\nTotal junctions: {len(df)}"
    )

    high_risk = df[
        df["risk_category"].isin(
            ["CRITICAL", "HIGH"]
        )
    ].copy()

    print(
        f"Critical/High junctions: {len(high_risk)}"
    )

    if high_risk.empty:

        empty = pd.DataFrame(
            columns=[
                "corridor_id",
                "junction_count",
                "critical_count",
                "high_count",
                "mean_risk",
                "centroid_latitude",
                "centroid_longitude",
                "junction_ids",
                "areas",
                "corridor_priority",
                "interpretation"
            ]
        )

        empty.to_csv(
            OUTPUT_FILE,
            index=False
        )

        print("\nNo Critical/High junctions found.")
        return


    assigned_junctions = set()

    corridor_rows = []

    corridor_radius_km = 1.5


    # ========================================================
    # FIND NEARBY GROUPS
    # ========================================================

    for _, seed in high_risk.iterrows():

        seed_id = int(
            seed["junction_id"]
        )

        if seed_id in assigned_junctions:
            continue


        nearby = []


        for _, candidate in high_risk.iterrows():

            candidate_id = int(
                candidate["junction_id"]
            )

            distance = haversine_distance(
                float(seed["latitude"]),
                float(seed["longitude"]),
                float(candidate["latitude"]),
                float(candidate["longitude"])
            )

            if distance <= corridor_radius_km:

                nearby.append(candidate)


        corridor_df = pd.DataFrame(
            nearby
        )


        if corridor_df.empty:
            continue


        junction_ids = [
            int(x)
            for x in corridor_df["junction_id"]
        ]

        assigned_junctions.update(
            junction_ids
        )


        # ====================================================
        # STATISTICS
        # ====================================================

        junction_count = len(
            corridor_df
        )

        critical_count = int(
            (
                corridor_df["risk_category"]
                == "CRITICAL"
            ).sum()
        )

        high_count = int(
            (
                corridor_df["risk_category"]
                == "HIGH"
            ).sum()
        )

        mean_risk = float(
            corridor_df["final_risk_score"].mean()
        )


        # ====================================================
        # CENTROID
        # ====================================================

        centroid_latitude = float(
            corridor_df["latitude"].mean()
        )

        centroid_longitude = float(
            corridor_df["longitude"].mean()
        )


        # ====================================================
        # CORRIDOR PRIORITY
        # ====================================================

        junction_factor = min(
            1.0,
            junction_count / 5
        )

        critical_factor = min(
            1.0,
            critical_count / 2
        )

        corridor_priority = (
            junction_factor * 0.35
            + critical_factor * 0.35
            + mean_risk * 0.30
        )


        # ====================================================
        # AREAS
        # ====================================================

        if "area_name" in corridor_df.columns:

            areas = (
                corridor_df["area_name"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            areas = areas[:5]

            area_text = " | ".join(
                areas
            )

        else:

            area_text = (
                "Area information unavailable"
            )


        # ====================================================
        # STORE
        # ====================================================

        corridor_rows.append({

            "corridor_id":
                len(corridor_rows) + 1,

            "junction_count":
                junction_count,

            "critical_count":
                critical_count,

            "high_count":
                high_count,

            "mean_risk":
                round(
                    mean_risk,
                    4
                ),

            "centroid_latitude":
                round(
                    centroid_latitude,
                    6
                ),

            "centroid_longitude":
                round(
                    centroid_longitude,
                    6
                ),

            "junction_ids":
                ",".join(
                    map(
                        str,
                        junction_ids
                    )
                ),

            "areas":
                area_text,

            "corridor_priority":
                round(
                    corridor_priority,
                    4
                ),

            "interpretation":
                (
                    "Cluster of high-risk junctions "
                    "requiring corridor-level "
                    "emergency-access investigation."
                )
        })


    # ========================================================
    # SAVE
    # ========================================================

    corridor_df = pd.DataFrame(
        corridor_rows
    )


    if not corridor_df.empty:

        corridor_df = corridor_df.sort_values(
            "corridor_priority",
            ascending=False
        ).reset_index(
            drop=True
        )


    corridor_df.to_csv(
        OUTPUT_FILE,
        index=False
    )


    print(
        "\n" + "=" * 60
    )

    print(
        f"Corridors identified: "
        f"{len(corridor_df)}"
    )

    print(
        f"Saved: {OUTPUT_FILE}"
    )


    if not corridor_df.empty:

        print("\nTop corridors:")

        print(
            corridor_df[
                [
                    "corridor_id",
                    "junction_count",
                    "critical_count",
                    "high_count",
                    "mean_risk",
                    "centroid_latitude",
                    "centroid_longitude",
                    "areas",
                    "corridor_priority"
                ]
            ]
            .head(10)
            .to_string(index=False)
        )


    print("\nDONE.")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()