import pandas as pd
from pathlib import Path

INPUT_PATH = Path(
    "data/processed/final_junction_risk.csv"
)

print("==========================================")
print("       FINAL RESULT VALIDATION")
print("==========================================")

df = pd.read_csv(INPUT_PATH)

print("\nTotal junctions:", len(df))

# ---------------------------------------------------------
# Required columns
# ---------------------------------------------------------

required = [
    "junction_id",
    "longitude",
    "latitude",
    "priority_score",
    "hospital_access_risk",
    "nearest_hospital_distance_km",
    "hospitals_within_5km",
    "final_risk_score",
    "risk_category",
    "final_risk_rank"
]

missing = [
    c for c in required
    if c not in df.columns
]

print("\nMissing required columns:", missing)

# ---------------------------------------------------------
# Missing values
# ---------------------------------------------------------

print("\nMissing values:")
print(
    df[required]
    .isna()
    .sum()
    .to_string()
)

# ---------------------------------------------------------
# Duplicate junctions
# ---------------------------------------------------------

duplicates = df["junction_id"].duplicated().sum()

print("\nDuplicate junction IDs:", duplicates)

# ---------------------------------------------------------
# Risk range
# ---------------------------------------------------------

print("\nRisk score range:")
print(
    "Minimum:",
    df["final_risk_score"].min()
)

print(
    "Maximum:",
    df["final_risk_score"].max()
)

# ---------------------------------------------------------
# Categories
# ---------------------------------------------------------

print("\nRisk category distribution:")
print(
    df["risk_category"]
    .value_counts()
    .sort_index()
)

# ---------------------------------------------------------
# Rank validation
# ---------------------------------------------------------

print("\nRank range:")
print(
    "Minimum:",
    df["final_risk_rank"].min()
)

print(
    "Maximum:",
    df["final_risk_rank"].max()
)

# ---------------------------------------------------------
# Final validation
# ---------------------------------------------------------

valid_scores = (
    df["final_risk_score"].between(0, 1).all()
)

valid_ranks = (
    df["final_risk_rank"].nunique() == len(df)
)

print("\n==========================================")
print("       VALIDATION RESULT")
print("==========================================")

print(
    "Risk scores between 0 and 1:",
    valid_scores
)

print(
    "Unique final ranks:",
    valid_ranks
)

if (
    len(missing) == 0
    and duplicates == 0
    and valid_scores
    and valid_ranks
):
    print("\nSTATUS: PASS")
else:
    print("\nSTATUS: CHECK REQUIRED")

print("\nDONE.")