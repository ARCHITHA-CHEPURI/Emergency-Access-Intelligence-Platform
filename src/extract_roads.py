import json
import pyogrio
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon


# --------------------------------------------------
# Paths
# --------------------------------------------------

OSM_FILE = "data/raw/telangana-latest.osm.pbf"
GHMC_FILE = "data/boundaries/ghmc_boundary.json"
OUTPUT_FILE = "data/processed/ghmc_roads.gpkg"


# --------------------------------------------------
# 1. Load GHMC boundary
# --------------------------------------------------

print("Loading GHMC boundary...")

with open(GHMC_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

rings = data["features"][0]["geometry"]["rings"]

polygons = [Polygon(ring) for ring in rings]

if len(polygons) == 1:
    ghmc = polygons[0]
else:
    ghmc = MultiPolygon(polygons)

print("Boundary:", ghmc.geom_type)
print("Valid:", ghmc.is_valid)
print("Bounds:", ghmc.bounds)


# --------------------------------------------------
# 2. Read OSM roads
# --------------------------------------------------

print("\nReading OSM road data...")

roads = pyogrio.read_dataframe(
    OSM_FILE,
    layer="lines",
    columns=["osm_id", "name", "highway", "geometry"]
)

print("Total line features:", len(roads))


# --------------------------------------------------
# 3. Keep only road-related features
# --------------------------------------------------

ROAD_TYPES = {
    "motorway",
    "motorway_link",
    "trunk",
    "trunk_link",
    "primary",
    "primary_link",
    "secondary",
    "secondary_link",
    "tertiary",
    "tertiary_link",
    "residential",
    "living_street",
    "unclassified",
    "road",
    "service",
}

roads = roads[roads["highway"].isin(ROAD_TYPES)].copy()

print("Road features after filtering:", len(roads))


# --------------------------------------------------
# 4. Convert to GeoDataFrame
# --------------------------------------------------

roads = gpd.GeoDataFrame(
    roads,
    geometry="geometry",
    crs="EPSG:4326"
)


# --------------------------------------------------
# 5. Spatial filtering
# --------------------------------------------------

print("\nFiltering roads to GHMC boundary...")

ghmc_gdf = gpd.GeoDataFrame(
    {"geometry": [ghmc]},
    crs="EPSG:4326"
)

roads = gpd.clip(roads, ghmc_gdf)

print("Road features inside GHMC:", len(roads))


# --------------------------------------------------
# 6. Save
# --------------------------------------------------

print("\nSaving:", OUTPUT_FILE)

roads.to_file(
    OUTPUT_FILE,
    layer="roads",
    driver="GPKG"
)

print("DONE.")