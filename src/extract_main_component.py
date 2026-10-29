import networkx as nx

INPUT = r"data\processed\ghmc_osm_graph.graphml"
OUTPUT = r"data\processed\ghmc_main_component.graphml"

print("Loading GHMC road network...")
G = nx.read_graphml(INPUT)

print(f"Original nodes: {G.number_of_nodes()}")
print(f"Original edges: {G.number_of_edges()}")

print("\nFinding weakly connected components...")
components = nx.weakly_connected_components(G)

largest_component = max(components, key=len)

print(f"Largest component nodes: {len(largest_component)}")

# Keep only the largest component
G_main = G.subgraph(largest_component).copy()

print(f"Main network nodes: {G_main.number_of_nodes()}")
print(f"Main network edges: {G_main.number_of_edges()}")

print(
    f"Coverage: "
    f"{100 * G_main.number_of_nodes() / G.number_of_nodes():.2f}%"
)

print("\nSaving main network...")
nx.write_graphml(G_main, OUTPUT)

print(f"Saved: {OUTPUT}")
print("DONE.")