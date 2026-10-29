import pandas as pd
from pathlib import Path

INPUT_PATH = Path("data/processed/hospitals.csv")
OUTPUT_PATH = Path("data/processed/hospitals_clean.csv")

print("==========================================")
print("        HOSPITAL DATA CLEANING")
print("==========================================")

print("\nLoading hospitals...")
df = pd.read_csv(INPUT_PATH)

print("Raw hospital records:", len(df))

required = ["hospital_id", "longitude", "latitude"]

for col in required:
    if col not in df.columns:
        raise ValueError(
            f"Missing required column: {col}"
        )

# ---------------------------------------------------------
# Clean coordinates
# ---------------------------------------------------------

df["longitude"] = pd.to_numeric(
    df["longitude"],
    errors="coerce"
)

df["latitude"] = pd.to_numeric(
    df["latitude"],
    errors="coerce"
)

before = len(df)

df = df.dropna(
    subset=["longitude", "latitude"]
).copy()

df = df[
    (df["longitude"] >= 77.0) &
    (df["longitude"] <= 82.0) &
    (df["latitude"] >= 15.0) &
    (df["latitude"] <= 20.0)
].copy()

invalid_removed = before - len(df)

# ---------------------------------------------------------
# Clean hospital names
# ---------------------------------------------------------

if "name" not in df.columns:
    df["name"] = df["hospital_id"].astype(str)

df["name"] = (
    df["name"]
    .fillna("")
    .astype(str)
    .str.strip()
)

df.loc[
    df["name"] == "",
    "name"
] = df.loc[
    df["name"] == "",
    "hospital_id"
].astype(str)

# ---------------------------------------------------------
# Remove duplicate hospital representations
#
# OSM can represent the same physical hospital using
# multiple elements.
# ---------------------------------------------------------

df["name_key"] = (
    df["name"]
    .str.lower()
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
)

df["lat_key"] = df["latitude"].round(6)
df["lon_key"] = df["longitude"].round(6)

before_duplicates = len(df)

df = df.drop_duplicates(
    subset=["name_key", "lat_key", "lon_key"]
).copy()

duplicates_removed = (
    before_duplicates - len(df)
)

df = df.drop(
    columns=[
        "name_key",
        "lat_key",
        "lon_key"
    ]
)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\n==========================================")
print("       CLEANING RESULT")
print("==========================================")

print("Raw hospitals:", before)
print("Invalid coordinate rows removed:", invalid_removed)
print("Duplicate records removed:", duplicates_removed)
print("Clean hospitals:", len(df))

print("\nColumns:")
print(df.columns.tolist())

print("\nSample:")
print(
    df[
        [
            "hospital_id",
            "name",
            "longitude",
            "latitude"
        ]
    ]
    .head(10)
    .to_string(index=False)
)

print("\nSaved:")
print(OUTPUT_PATH)

print("\nDONE.")