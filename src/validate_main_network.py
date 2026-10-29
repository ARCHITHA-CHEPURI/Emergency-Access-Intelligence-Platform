import networkx as nx

INPUT = r"data\processed\ghmc_main_component.graphml"

print("Loading main network...")
G = nx.read_graphml(INPUT)

print("\n========== MAIN NETWORK ==========")
print("Nodes:", G.number_of_nodes())
print("Edges:", G.number_of_edges())
print("Directed:", G.is_directed())

components = list(nx.weakly_connected_components(G))

print("Weak components:", len(components))
print("Largest component:", max(len(c) for c in components))

print("\nValidation complete.")