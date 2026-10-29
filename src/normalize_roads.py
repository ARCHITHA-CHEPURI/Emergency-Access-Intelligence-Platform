import geopandas as gpd
from shapely.geometry import LineString, MultiLineString

INPUT = "data/processed/ghmc_roads.gpkg"
OUTPUT = "data/processed/ghmc_roads_normalized.gpkg"

print("Reading GHMC roads...")

gdf = gpd.read_file(INPUT, layer="roads")

print("Original features:", len(gdf))
print("Original geometry types:")
print(gdf.geometry.geom_type.value_counts())

# Split MultiLineStrings into individual LineStrings
gdf = gdf.explode(index_parts=False).reset_index(drop=True)

# Keep only LineStrings
gdf = gdf[gdf.geometry.geom_type == "LineString"].copy()

# Remove empty/invalid geometries
gdf = gdf[
    gdf.geometry.notna()
    & ~gdf.geometry.is_empty
    & gdf.geometry.is_valid
].copy()

# Remove lines with fewer than 2 coordinates
gdf = gdf[
    gdf.geometry.apply(lambda geom: len(geom.coords) >= 2)
].copy()

print("\nNormalized features:", len(gdf))
print("Geometry types:")
print(gdf.geometry.geom_type.value_counts())

print("\nBounds:")
print(gdf.total_bounds)

print("\nSaving:", OUTPUT)

gdf.to_file(
    OUTPUT,
    layer="roads",
    driver="GPKG"
)

print("DONE.")