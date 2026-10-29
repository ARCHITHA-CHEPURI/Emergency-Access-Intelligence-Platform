import osmium
import pandas as pd
from pathlib import Path

# ==========================================
#        OSM PLACE NAME EXTRACTION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

PBF_FILE = BASE_DIR / "data" / "raw" / "telangana-latest.osm.pbf"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "osm_places.csv"


class PlaceHandler(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()
        self.places = []

    def node(self, n):

        place_type = n.tags.get("place")
        name = n.tags.get("name")

        if not place_type or not name:
            return

        allowed_types = {
            "neighbourhood",
            "suburb",
            "locality",
            "village",
            "town",
            "city"
        }

        if place_type not in allowed_types:
            return

        if not n.location.valid():
            return

        self.places.append({
            "osm_id": n.id,
            "name": name,
            "place_type": place_type,
            "longitude": n.location.lon,
            "latitude": n.location.lat
        })


print("==========================================")
print("        OSM PLACE NAME EXTRACTION")
print("==========================================")
print()

if not PBF_FILE.exists():
    raise FileNotFoundError(
        f"OSM PBF not found:\n{PBF_FILE}"
    )

print(f"OSM PBF found: {PBF_FILE}")
print()
print("Searching for named places...")
print(
    "Types: neighbourhood, suburb, locality, "
    "village, town, city"
)
print()
print("Reading OSM PBF...")
print("This may take a little time.")
print()

handler = PlaceHandler()
handler.apply_file(str(PBF_FILE), locations=True)

df = pd.DataFrame(handler.places)

if df.empty:
    raise RuntimeError("No named places found in OSM PBF.")

# Remove duplicates
df = df.drop_duplicates(
    subset=["name", "place_type", "longitude", "latitude"]
).reset_index(drop=True)

# Sort by type and name
type_order = {
    "neighbourhood": 1,
    "suburb": 2,
    "locality": 3,
    "village": 4,
    "town": 5,
    "city": 6
}

df["type_order"] = df["place_type"].map(type_order)
df = df.sort_values(
    ["type_order", "name"]
).drop(columns=["type_order"])

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("==========================================")
print("       PLACE EXTRACTION RESULT")
print("==========================================")

print(f"Total places: {len(df)}")

print()
print("Place types:")

print(
    df["place_type"]
    .value_counts()
)

print()
print("Sample places:")

print(
    df.head(20).to_string(index=False)
)

print()
print("Saved:")
print(OUTPUT_FILE)

print()
print("DONE.")