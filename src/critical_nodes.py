import networkx as nx

INPUT = r"data\processed\ghmc_main_component.graphml"
OUTPUT = r"data\processed\critical_nodes.csv"

print("Loading network...")
G = nx.read_graphml(INPUT)

print("Calculating approximate betweenness centrality...")

centrality = nx.betweenness_centrality(
    G,
    k=1000,
    normalized=True,
    seed=42
)

top_nodes = sorted(
    centrality.items(),
    key=lambda x: x[1],
    reverse=True
)[:100]

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("node_id,betweenness\n")

    for node, score in top_nodes:
        f.write(f"{node},{score}\n")

print("\n========== TOP CRITICAL NODES ==========")

for rank, (node, score) in enumerate(top_nodes[:20], start=1):
    print(
        f"{rank:2d}. Node={node} "
        f"Betweenness={score:.8f}"
    )

print(f"\nSaved: {OUTPUT}")
print("DONE.")