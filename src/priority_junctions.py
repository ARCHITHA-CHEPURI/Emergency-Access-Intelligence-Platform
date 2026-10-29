import pandas as pd
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

INPUT_PATH = Path(
    "data/processed/junction_features.csv"
)

OUTPUT_PATH = Path(
    "data/processed/priority_junctions.csv"
)


# =========================================================
# SETTINGS
# =========================================================

TOP_N = 5000


print("==========================================")
print("       PRIORITY JUNCTION SELECTION")
print("==========================================\n")


# =========================================================
# LOAD FEATURES
# =========================================================

print("Loading junction features...")

df = pd.read_csv(INPUT_PATH)

print("Total junctions:", len(df))


# =========================================================
# REQUIRED COLUMNS
# =========================================================

required_columns = [
    "junction_id",
    "longitude",
    "latitude",
    "node_count",
    "max_degree",
    "max_neighbors",
    "road_count",
    "road_density",
    "structural_score",
]

missing = [
    col
    for col in required_columns
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )


# =========================================================
# CLEAN NUMERIC VALUES
# =========================================================

numeric_columns = [
    "node_count",
    "max_degree",
    "max_neighbors",
    "road_count",
    "road_density",
    "structural_score",
]

for col in numeric_columns:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df = df.dropna(
    subset=[
        "longitude",
        "latitude",
        "structural_score"
    ]
).copy()


# =========================================================
# NORMALIZATION FUNCTION
# =========================================================

def min_max_normalize(series):

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:
        return pd.Series(
            0.0,
            index=series.index
        )

    return (
        (series - minimum)
        / (maximum - minimum)
    )


# =========================================================
# NORMALIZE STRUCTURAL FEATURES
# =========================================================

df["structural_norm"] = (
    min_max_normalize(
        df["structural_score"]
    )
)

df["degree_norm"] = (
    min_max_normalize(
        df["max_degree"]
    )
)

df["neighbor_norm"] = (
    min_max_normalize(
        df["max_neighbors"]
    )
)

df["road_count_norm"] = (
    min_max_normalize(
        df["road_count"]
    )
)

df["density_norm"] = (
    min_max_normalize(
        df["road_density"]
    )
)


# =========================================================
# ROAD HIERARCHY SCORE
# =========================================================

hierarchy_columns = []

for col in [
    "primary_count",
    "secondary_count",
    "tertiary_count",
]:

    if col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        ).fillna(0)

        hierarchy_columns.append(col)


if hierarchy_columns:

    df["road_hierarchy_score"] = (
        df.get("primary_count", 0) * 3
        + df.get("secondary_count", 0) * 2
        + df.get("tertiary_count", 0) * 1
    )

else:

    df["road_hierarchy_score"] = 0


df["hierarchy_norm"] = (
    min_max_normalize(
        df["road_hierarchy_score"]
    )
)


# =========================================================
# PRIORITY SCORE
# =========================================================

df["priority_score"] = (

    0.35 * df["structural_norm"]

    + 0.20 * df["degree_norm"]

    + 0.15 * df["neighbor_norm"]

    + 0.15 * df["density_norm"]

    + 0.10 * df["road_count_norm"]

    + 0.05 * df["hierarchy_norm"]

)


# =========================================================
# SORT
# =========================================================

df = df.sort_values(
    "priority_score",
    ascending=False
).reset_index(drop=True)


# =========================================================
# SELECT TOP N
# =========================================================

selected = df.head(
    min(TOP_N, len(df))
).copy()


# =========================================================
# CREATE RANK
# =========================================================

selected.insert(
    0,
    "priority_rank",
    range(1, len(selected) + 1)
)


# =========================================================
# OUTPUT COLUMNS
# =========================================================

output_columns = [
    "priority_rank",
    "junction_id",
    "longitude",
    "latitude",
    "node_count",
    "max_degree",
    "max_neighbors",
    "road_count",
]

for col in [
    "primary_count",
    "secondary_count",
    "tertiary_count",
    "residential_count",
    "service_count",
]:

    if col in selected.columns:
        output_columns.append(col)


output_columns += [
    "road_density",
    "structural_score",
    "road_hierarchy_score",
    "priority_score",
]


selected = selected[
    output_columns
]


# =========================================================
# RESULT
# =========================================================

print("\n==========================================")
print("       PRIORITY SELECTION RESULT")
print("==========================================")

print(
    "Total junctions:",
    len(df)
)

print(
    "Selected priority junctions:",
    len(selected)
)

print(
    "Highest priority score:",
    round(
        selected["priority_score"].max(),
        6
    )
)

print(
    "Lowest selected priority score:",
    round(
        selected["priority_score"].min(),
        6
    )
)


print("\nTop 20 priority junctions:")

print(
    selected.head(20).to_string(
        index=False
    )
)


# =========================================================
# SAVE
# =========================================================

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

selected.to_csv(
    OUTPUT_PATH,
    index=False
)


print("\nSaved:")
print(OUTPUT_PATH)

print("\nDONE.")