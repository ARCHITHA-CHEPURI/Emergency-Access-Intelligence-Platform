import geopandas as gpd
from shapely.geometry import Point
from collections import Counter

INPUT = "data/processed/ghmc_roads_normalized.gpkg"

print("Loading sample...")

roads = gpd.read_file(
    INPUT,
    layer="roads",
    rows=5000
)

# Project to metres
roads = roads.to_crs("EPSG:32644")

print("Roads:", len(roads))
print("CRS:", roads.crs)

# Spatial index
sindex = roads.sindex

endpoint_counts = Counter()

print("Finding nearby road endpoints...")

for idx, geom in enumerate(roads.geometry):

    coords = list(geom.coords)

    start = Point(coords[0])
    end = Point(coords[-1])

    for point in (start, end):

        candidates = list(
            sindex.query(
                point,
                predicate="intersects"
            )
        )

        endpoint_counts[point.wkb] += len(candidates)

print("Unique endpoints:", len(endpoint_counts))

print("\nEndpoint connection distribution:")

for connections, count in sorted(
    Counter(endpoint_counts.values()).items()
):
    print(f"{connections} connected roads: {count}")

print("\nTEST COMPLETE")