import osmium
import pandas as pd
from pathlib import Path

PBF_PATH = Path("data/raw/telangana-latest.osm.pbf")
OUTPUT_PATH = Path("data/processed/hospitals.csv")


print("==========================================")
print("        HOSPITAL DATA EXTRACTION")
print("==========================================")
print()

if not PBF_PATH.exists():
    raise FileNotFoundError(
        f"OSM PBF not found: {PBF_PATH}"
    )

print(f"OSM PBF found: {PBF_PATH}")
print()
print("Searching for hospital features...")
print("Tags: amenity=hospital OR healthcare=hospital")


class HospitalHandler(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()
        self.hospitals = []

    def add_hospital(self, obj, lon, lat, element_type):
        tags = obj.tags

        # Hospital name
        name = tags.get("name", "")

        # Hospital category
        amenity = tags.get("amenity", "")
        healthcare = tags.get("healthcare", "")

        # Useful additional information
        emergency = tags.get("emergency", "")
        operator = tags.get("operator", "")
        phone = tags.get("phone", "")
        website = tags.get("website", "")

        self.hospitals.append({
            "osm_id": obj.id,
            "element_type": element_type,
            "name": name,
            "amenity": amenity,
            "healthcare": healthcare,
            "emergency": emergency,
            "operator": operator,
            "phone": phone,
            "website": website,
            "longitude": lon,
            "latitude": lat
        })

    def node(self, n):

        if (
            n.tags.get("amenity") == "hospital"
            or n.tags.get("healthcare") == "hospital"
        ):
            if n.location.valid():
                self.add_hospital(
                    n,
                    n.location.lon,
                    n.location.lat,
                    "node"
                )

    def way(self, w):

        if not (
            w.tags.get("amenity") == "hospital"
            or w.tags.get("healthcare") == "hospital"
        ):
            return

        # Calculate approximate centroid from available way nodes
        coordinates = []

        for node in w.nodes:
            if node.location.valid():
                coordinates.append(
                    (node.location.lon, node.location.lat)
                )

        if not coordinates:
            return

        longitude = sum(x for x, y in coordinates) / len(coordinates)
        latitude = sum(y for x, y in coordinates) / len(coordinates)

        self.add_hospital(
            w,
            longitude,
            latitude,
            "way"
        )


handler = HospitalHandler()

print()
print("Reading OSM PBF...")
print("This may take a little time for the Telangana extract.")
print()

handler.apply_file(
    str(PBF_PATH),
    locations=True
)

print()
print("OSM hospital elements found:", len(handler.hospitals))


# ---------------------------------------------------------
# Convert to DataFrame
# ---------------------------------------------------------

hospitals = pd.DataFrame(handler.hospitals)


if hospitals.empty:
    print()
    print("WARNING: No hospitals were found.")
    print("Check the PBF file and OSM hospital tags.")
else:

    # Remove exact duplicate records
    hospitals = hospitals.drop_duplicates(
        subset=[
            "osm_id",
            "element_type"
        ]
    )

    # Add a simple hospital ID
    hospitals.insert(
        0,
        "hospital_id",
        [
            f"H{i:05d}"
            for i in range(1, len(hospitals) + 1)
        ]
    )

    # Make sure output directory exists
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    hospitals.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print()
    print("==========================================")
    print("       HOSPITAL EXTRACTION RESULT")
    print("==========================================")

    print(f"Total hospitals: {len(hospitals)}")

    print()
    print("Element types:")
    print(
        hospitals["element_type"]
        .value_counts()
        .to_string()
    )

    print()
    print("Sample hospitals:")

    print(
        hospitals[
            [
                "hospital_id",
                "name",
                "element_type",
                "longitude",
                "latitude"
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    print()
    print("Saved:")
    print(OUTPUT_PATH)

print()
print("DONE.")