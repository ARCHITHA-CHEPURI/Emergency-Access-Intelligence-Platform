import networkx as nx
import pandas as pd
from pathlib import Path

GRAPH_PATH = Path("data/processed/ghmc_osm_graph.graphml")
OUTPUT_PATH = Path("data/processed/candidate_intersections.csv")

print("Loading network...")
G = nx.read_graphml(GRAPH_PATH)

print(f"Nodes: {G.number_of_nodes()}")
print(f"Edges: {G.number_of_edges()}")

# Convert node IDs to strings consistently
G = nx.DiGraph(G)

print("\nFinding intersection candidates...")

candidates = []

for node in G.nodes():

    # Number of incoming and outgoing connections
    in_degree = G.in_degree(node)
    out_degree = G.out_degree(node)

    total_degree = in_degree + out_degree

    # Candidate intersection:
    # at least 3 connections
    if total_degree >= 3:

        data = G.nodes[node]

        candidates.append({
            "node_id": node,
            "in_degree": in_degree,
            "out_degree": out_degree,
            "degree": total_degree,
            "x": data.get("x"),
            "y": data.get("y")
        })

df = pd.DataFrame(candidates)

print("\n==========================================")
print("       INTERSECTION EXTRACTION")
print("==========================================")

print("Candidate intersections:", len(df))

if len(df) > 0:
    print("\nDegree distribution:")
    print(df["degree"].value_counts().sort_index().to_string())

    print("\nTop 20 highest-degree candidates:")
    print(
        df.sort_values("degree", ascending=False)
          .head(20)
          .to_string(index=False)
    )

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(OUTPUT_PATH, index=False)

print("\nSaved:")
print(OUTPUT_PATH)

print("\nDONE.")