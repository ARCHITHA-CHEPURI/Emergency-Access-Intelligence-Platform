import networkx as nx
import pandas as pd
import math
from pathlib import Path

# =========================================================
# PATHS
# =========================================================

GRAPH_PATH = Path("data/processed/ghmc_osm_graph.graphml")
CLUSTERS_PATH = Path("data/processed/junction_clusters.csv")
OUTPUT_PATH = Path("data/processed/junction_features.csv")


# =========================================================
# CONFIGURATION
# =========================================================

# Approximate radius used for local road-density calculation
# 30 m is consistent with the junction clustering threshold.
DENSITY_RADIUS_M = 30.0


# =========================================================
# LOAD DATA
# =========================================================

print("==========================================")
print("       JUNCTION FEATURE EXTRACTION")
print("==========================================")

print("\nLoading network...")

G = nx.read_graphml(GRAPH_PATH)

print("Network nodes:", G.number_of_nodes())
print("Network edges:", G.number_of_edges())
print("Directed:", G.is_directed())


print("\nLoading junction clusters...")

junctions = pd.read_csv(CLUSTERS_PATH)

print("Cluster rows:", len(junctions))

print("Columns:")
print(junctions.columns.tolist())


# =========================================================
# VALIDATE REQUIRED COLUMNS
# =========================================================

required_columns = [
    "junction_id",
    "node_count",
    "max_degree",
    "max_neighbors",
    "longitude",
    "latitude",
    "structural_score",
    "member_node_ids"
]

missing = [
    col for col in required_columns
    if col not in junctions.columns
]

if missing:
    raise ValueError(
        f"Missing required columns in junction_clusters.csv: {missing}"
    )


# =========================================================
# HELPERS
# =========================================================

def parse_member_nodes(value):
    """
    Convert comma-separated member node IDs into a list.
    """
    if pd.isna(value):
        return []

    value = str(value).strip()

    if not value:
        return []

    return [
        x.strip()
        for x in value.split(",")
        if x.strip()
    ]


def get_node_attribute(node_data, names):
    """
    Return the first available road-type attribute.
    """
    for name in names:
        value = node_data.get(name)

        if value is not None:
            return value

    return None


def classify_highway(value):
    """
    Normalize OSM highway values.
    """
    if value is None:
        return None

    value = str(value).lower().strip()

    # Handle list-like strings occasionally produced by GraphML
    value = value.replace("[", "").replace("]", "")
    value = value.replace("'", "").replace('"', "")

    if "primary" in value:
        return "primary"

    if "secondary" in value:
        return "secondary"

    if "tertiary" in value:
        return "tertiary"

    if "residential" in value:
        return "residential"

    return None


# =========================================================
# ROAD FEATURE EXTRACTION
# =========================================================

print("\nCalculating junction-level road features...")

road_counts = []
primary_counts = []
secondary_counts = []
tertiary_counts = []
residential_counts = []
road_density_values = []


# ---------------------------------------------------------
# Important:
# The GraphML network is a directed road graph.
#
# Each junction cluster contains the original OSM nodes
# belonging to that physical junction.
#
# We inspect edges touching those member nodes.
# ---------------------------------------------------------

for index, row in junctions.iterrows():

    member_nodes = parse_member_nodes(
        row["member_node_ids"]
    )

    # Convert to graph-compatible IDs
    member_nodes = [
        node for node in member_nodes
        if node in G
    ]

    member_set = set(member_nodes)

    roads = set()

    primary = set()
    secondary = set()
    tertiary = set()
    residential = set()

    # -----------------------------------------------------
    # Inspect edges connected to junction members
    # -----------------------------------------------------

    for node in member_nodes:

        # Incoming edges
        for source, target, data in G.in_edges(
            node,
            data=True
        ):

            edge_id = (
                str(source),
                str(target)
            )

            roads.add(edge_id)

            highway = classify_highway(
                get_node_attribute(
                    data,
                    ["highway", "road_type", "type"]
                )
            )

            if highway == "primary":
                primary.add(edge_id)

            elif highway == "secondary":
                secondary.add(edge_id)

            elif highway == "tertiary":
                tertiary.add(edge_id)

            elif highway == "residential":
                residential.add(edge_id)

        # Outgoing edges
        for source, target, data in G.out_edges(
            node,
            data=True
        ):

            edge_id = (
                str(source),
                str(target)
            )

            roads.add(edge_id)

            highway = classify_highway(
                get_node_attribute(
                    data,
                    ["highway", "road_type", "type"]
                )
            )

            if highway == "primary":
                primary.add(edge_id)

            elif highway == "secondary":
                secondary.add(edge_id)

            elif highway == "tertiary":
                tertiary.add(edge_id)

            elif highway == "residential":
                residential.add(edge_id)

    # -----------------------------------------------------
    # Road counts
    # -----------------------------------------------------

    road_counts.append(len(roads))
    primary_counts.append(len(primary))
    secondary_counts.append(len(secondary))
    tertiary_counts.append(len(tertiary))
    residential_counts.append(len(residential))

    # -----------------------------------------------------
    # Local road density
    #
    # Simple approximation:
    #
    # number of connected road segments
    # divided by physical junction cluster size
    #
    # This is deliberately kept stable and inexpensive.
    # -----------------------------------------------------

    node_count = max(
        int(row["node_count"]),
        1
    )

    density = len(roads) / node_count

    road_density_values.append(density)

    # Progress indicator
    if (index + 1) % 10000 == 0:
        print(
            f"Processed: {index + 1} / {len(junctions)}"
        )


# =========================================================
# ADD FEATURES
# =========================================================

junctions["road_count"] = road_counts

junctions["primary_count"] = primary_counts

junctions["secondary_count"] = secondary_counts

junctions["tertiary_count"] = tertiary_counts

junctions["residential_count"] = residential_counts

junctions["road_density"] = road_density_values


# =========================================================
# ROAD HIERARCHY SCORE
# =========================================================

print("\nCalculating road hierarchy score...")


def hierarchy_score(row):

    score = 0.0

    score += row["primary_count"] * 1.0

    score += row["secondary_count"] * 0.75

    score += row["tertiary_count"] * 0.50

    score += row["residential_count"] * 0.10

    return score


junctions["road_hierarchy_score"] = junctions.apply(
    hierarchy_score,
    axis=1
)


# =========================================================
# NORMALIZATION
# =========================================================

def minmax(series):

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:
        return pd.Series(
            [0.0] * len(series),
            index=series.index
        )

    return (
        (series - minimum)
        / (maximum - minimum)
    )


print("\nNormalizing structural features...")


degree_score = minmax(
    junctions["max_degree"]
)

neighbor_score = minmax(
    junctions["max_neighbors"]
)

node_score = minmax(
    junctions["node_count"]
)

density_score = minmax(
    junctions["road_density"]
)

hierarchy_score = minmax(
    junctions["road_hierarchy_score"]
)


# =========================================================
# STRUCTURAL SCORE
# =========================================================

junctions["structural_score"] = (
    0.30 * degree_score
    + 0.25 * neighbor_score
    + 0.20 * node_score
    + 0.15 * density_score
    + 0.10 * hierarchy_score
) * 100


# =========================================================
# SORT
# =========================================================

junctions = junctions.sort_values(
    "structural_score",
    ascending=False
).reset_index(drop=True)


# =========================================================
# FINAL COLUMN ORDER
# =========================================================

final_columns = [
    "junction_id",
    "longitude",
    "latitude",
    "node_count",
    "max_degree",
    "max_neighbors",
    "road_count",
    "primary_count",
    "secondary_count",
    "tertiary_count",
    "residential_count",
    "road_density",
    "road_hierarchy_score",
    "structural_score"
]

junctions = junctions[final_columns]


# =========================================================
# RESULT
# =========================================================

print("\n==========================================")
print("       FEATURE EXTRACTION RESULT")
print("==========================================")

print(
    "Junction clusters:",
    len(junctions)
)

print("\nFeature columns:")

for column in junctions.columns:
    print(" ", column)


print("\nTop 20 structural junctions:")

print(
    junctions.head(20).to_string(
        index=False
    )
)


print("\nStructural score statistics:")

print(
    junctions["structural_score"].describe()
)


# =========================================================
# SAVE
# =========================================================

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

junctions.to_csv(
    OUTPUT_PATH,
    index=False
)


print("\nSaved:")
print(OUTPUT_PATH)

print("\nDONE.")