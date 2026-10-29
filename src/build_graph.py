import osmnx as ox
import networkx as nx

INPUT_FILE = "data/processed/ghmc_roads.gpkg"
OUTPUT_FILE = "data/processed/ghmc_graph.graphml"

print("Loading GHMC roads...")

gdf = ox.io.load_graphml if False else None

# Read the processed road layer
import geopandas as gpd

roads = gpd.read_file(INPUT_FILE, layer="roads")

print("Road features:", len(roads))
print("CRS:", roads.crs)

# OSMnx expects LineString geometries for graph creation.
roads = roads.explode(index_parts=False).reset_index(drop=True)

print("After geometry normalization:", len(roads))
print("Geometry types:")
print(roads.geometry.geom_type.value_counts())

# Convert to a graph
print("\nBuilding graph...")

G = ox.convert.graph_from_gdfs(
    nodes=None,
    gdf_edges=roads,
)

print("\nGraph created.")
print("Nodes:", len(G.nodes))
print("Edges:", len(G.edges))

print("\nConnected components:")

components = sorted(
    nx.weakly_connected_components(G),
    key=len,
    reverse=True
)

for i, component in enumerate(components[:10], 1):
    print(f"{i}: {len(component)} nodes")

print("\nSaving graph...")

ox.io.save_graphml(G, OUTPUT_FILE)

print("Saved:", OUTPUT_FILE)