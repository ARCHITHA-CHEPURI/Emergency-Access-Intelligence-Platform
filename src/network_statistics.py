import networkx as nx

INPUT = r"data\processed\ghmc_main_component.graphml"

print("Loading network...")
G = nx.read_graphml(INPUT)

print("\n========== NETWORK STATISTICS ==========")

print("Nodes:", G.number_of_nodes())
print("Edges:", G.number_of_edges())

degrees = [d for _, d in G.degree()]

print("Average degree:", round(sum(degrees) / len(degrees), 2))
print("Maximum degree:", max(degrees))
print("Minimum degree:", min(degrees))

degree_counts = {}
for d in degrees:
    degree_counts[d] = degree_counts.get(d, 0) + 1

print("\nDegree distribution:")
for degree in sorted(degree_counts):
    print(f"Degree {degree}: {degree_counts[degree]}")

print("\nDONE.")