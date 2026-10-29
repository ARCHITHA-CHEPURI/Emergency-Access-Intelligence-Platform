import networkx as nx
import pandas as pd
import numpy as np

from pathlib import Path
from sklearn.cluster import DBSCAN
from pyproj import Transformer


# =========================================================
# PATHS
# =========================================================

GRAPH_PATH = Path(
    "data/processed/ghmc_osm_graph.graphml"
)

INPUT_PATH = Path(
    "data/processed/genuine_junctions.csv"
)

OUTPUT_PATH = Path(
    "data/processed/junction_clusters.csv"
)


# =========================================================
# SETTINGS
# =========================================================

# Physical junctions within 30 metres are grouped together.
DISTANCE_METERS = 30


print("==========================================")
print("       PHYSICAL JUNCTION CLUSTERING")
print("==========================================\n")


# =========================================================
# LOAD NETWORK
# =========================================================

print("Loading network...")

G = nx.read_graphml(GRAPH_PATH)

print("Network nodes:", G.number_of_nodes())
print("Network edges:", G.number_of_edges())
print("Directed:", G.is_directed())


# =========================================================
# LOAD GENUINE JUNCTIONS
# =========================================================

print("\nLoading genuine junctions...")

junctions = pd.read_csv(INPUT_PATH)

print("Genuine junction nodes:", len(junctions))

print("\nInput columns:")
print(list(junctions.columns))


# =========================================================
# FIX COORDINATE COLUMN NAMES
# =========================================================

# filter_junctions.py produces x/y.
# Convert them to longitude/latitude for consistency.

if "longitude" not in junctions.columns:

    if "x" in junctions.columns:
        junctions["longitude"] = junctions["x"]

    else:
        raise ValueError(
            "Longitude coordinate not found. "
            "Expected either 'longitude' or 'x'."
        )


if "latitude" not in junctions.columns:

    if "y" in junctions.columns:
        junctions["latitude"] = junctions["y"]

    else:
        raise ValueError(
            "Latitude coordinate not found. "
            "Expected either 'latitude' or 'y'."
        )


# =========================================================
# REMOVE INVALID COORDINATES
# =========================================================

junctions["longitude"] = pd.to_numeric(
    junctions["longitude"],
    errors="coerce"
)

junctions["latitude"] = pd.to_numeric(
    junctions["latitude"],
    errors="coerce"
)

before = len(junctions)

junctions = junctions.dropna(
    subset=["longitude", "latitude"]
).copy()

removed = before - len(junctions)

print("\nInvalid coordinate rows removed:", removed)


if len(junctions) == 0:
    raise ValueError(
        "No valid junction coordinates available."
    )


# =========================================================
# CONVERT WGS84 → UTM ZONE 44N
# =========================================================

print("\nProjecting coordinates to metres...")

transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32644",
    always_xy=True
)

x_m, y_m = transformer.transform(
    junctions["longitude"].values,
    junctions["latitude"].values
)

junctions["x_m"] = x_m
junctions["y_m"] = y_m


# =========================================================
# CLUSTER NEARBY JUNCTION NODES
# =========================================================

print("\nClustering nearby junction nodes...")
print(
    f"Distance threshold: {DISTANCE_METERS} metres"
)

coordinates = junctions[
    ["x_m", "y_m"]
].to_numpy()


clustering = DBSCAN(
    eps=DISTANCE_METERS,
    min_samples=1,
    metric="euclidean",
    algorithm="ball_tree"
)

labels = clustering.fit_predict(coordinates)

junctions["cluster_label"] = labels


# =========================================================
# BUILD PHYSICAL JUNCTION CLUSTERS
# =========================================================

clusters = []

for label, group in junctions.groupby(
    "cluster_label"
):

    # -----------------------------------------------------
    # Representative coordinate
    # -----------------------------------------------------

    longitude = group["longitude"].mean()
    latitude = group["latitude"].mean()

    # -----------------------------------------------------
    # Structural information
    # -----------------------------------------------------

    node_count = len(group)

    max_degree = group["degree"].max()

    max_neighbors = group[
        "unique_neighbors"
    ].max()

    # -----------------------------------------------------
    # Preserve all member node IDs
    # -----------------------------------------------------

    member_nodes = [
        str(x)
        for x in group["node_id"].tolist()
    ]

    member_node_ids = ",".join(
        member_nodes
    )

    # -----------------------------------------------------
    # Structural score
    # -----------------------------------------------------

    structural_score = (
        max_degree * 2
        + max_neighbors * 3
        + np.log1p(node_count)
    )

    clusters.append(
        {
            "cluster_id": int(label) + 1,
            "node_count": node_count,
            "max_degree": int(max_degree),
            "max_neighbors": int(max_neighbors),
            "longitude": longitude,
            "latitude": latitude,
            "structural_score": structural_score,
            "member_node_ids": member_node_ids,
        }
    )


clusters_df = pd.DataFrame(clusters)


# =========================================================
# SORT BY STRUCTURAL IMPORTANCE
# =========================================================

clusters_df = clusters_df.sort_values(
    "structural_score",
    ascending=False
).reset_index(drop=True)


# =========================================================
# CREATE JUNCTION IDs
# =========================================================

clusters_df["junction_id"] = [
    f"J{i:06d}"
    for i in range(1, len(clusters_df) + 1)
]


# Put junction_id first.

column_order = [
    "junction_id",
    "cluster_id",
    "node_count",
    "max_degree",
    "max_neighbors",
    "longitude",
    "latitude",
    "structural_score",
    "member_node_ids",
]

clusters_df = clusters_df[
    column_order
]


# =========================================================
# STATISTICS
# =========================================================

print("\n==========================================")
print("       JUNCTION CLUSTERING RESULT")
print("==========================================")

print(
    "Original junction nodes:",
    len(junctions)
)

print(
    "Physical junction clusters:",
    len(clusters_df)
)

reduction = (
    1
    - len(clusters_df) / len(junctions)
) * 100

print(
    f"Reduction: {reduction:.2f} %"
)


# =========================================================
# CLUSTER SIZE DISTRIBUTION
# =========================================================

print("\nCluster size distribution:")

print(
    clusters_df["node_count"]
    .value_counts()
    .sort_index()
    .head(20)
    .to_string()
)


# =========================================================
# TOP STRUCTURAL CANDIDATES
# =========================================================

print("\nTop 20 structural candidates:")

print(
    clusters_df[
        [
            "junction_id",
            "node_count",
            "max_degree",
            "max_neighbors",
            "longitude",
            "latitude",
            "structural_score",
        ]
    ]
    .head(20)
    .to_string(index=False)
)


# =========================================================
# SAVE
# =========================================================

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

clusters_df.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\nSaved:")
print(OUTPUT_PATH)

print("\nDONE.")