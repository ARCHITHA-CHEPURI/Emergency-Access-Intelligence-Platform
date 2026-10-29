import networkx as nx
import pandas as pd
from pathlib import Path

GRAPH_PATH = Path("data/processed/ghmc_osm_graph.graphml")
INPUT_PATH = Path("data/processed/candidate_intersections.csv")
OUTPUT_PATH = Path("data/processed/genuine_junctions.csv")

print("Loading candidate intersections...")
df = pd.read_csv(INPUT_PATH)

print("Candidates:", len(df))

print("\nLoading network...")
G = nx.read_graphml(GRAPH_PATH)

print("Nodes:", G.number_of_nodes())
print("Edges:", G.number_of_edges())


# ---------------------------------------------------------
# A road junction should have connections to multiple
# distinct neighboring nodes.
# ---------------------------------------------------------

def count_unique_neighbors(node):
    neighbors = set(G.predecessors(node))
    neighbors.update(G.successors(node))
    return len(neighbors)


print("\nFiltering junction candidates...")

df["unique_neighbors"] = df["node_id"].astype(str).apply(
    count_unique_neighbors
)

# Keep nodes that connect to at least 3 distinct neighbors.
junctions = df[df["unique_neighbors"] >= 3].copy()

print("\n==========================================")
print("        GENUINE JUNCTION FILTER")
print("==========================================")

print("Original candidates:", len(df))
print("Genuine junction candidates:", len(junctions))

print("\nNeighbor distribution:")
print(
    junctions["unique_neighbors"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nTop junctions:")

print(
    junctions
    .sort_values(
        ["unique_neighbors", "degree"],
        ascending=False
    )
    .head(20)
    .to_string(index=False)
)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

junctions.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\nSaved:")
print(OUTPUT_PATH)

print("\nDONE.")