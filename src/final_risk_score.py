import pandas as pd
from pathlib import Path

PRIORITY_PATH = Path("data/processed/priority_junctions.csv")
HOSPITAL_PATH = Path("data/processed/junction_hospital_scores.csv")
OUTPUT_PATH = Path("data/processed/final_junction_risk.csv")

print("==========================================")
print("        FINAL JUNCTION RISK SCORING")
print("==========================================")

# ---------------------------------------------------------
# Load priority junctions
# ---------------------------------------------------------

print("\nLoading priority junctions...")
priority = pd.read_csv(PRIORITY_PATH)

print("Priority junctions:", len(priority))

# ---------------------------------------------------------
# Load hospital accessibility scores
# ---------------------------------------------------------

print("\nLoading hospital scores...")
hospital = pd.read_csv(HOSPITAL_PATH)

print("Hospital-scored junctions:", len(hospital))

# ---------------------------------------------------------
# Check required columns
# ---------------------------------------------------------

required_priority = [
    "junction_id",
    "longitude",
    "latitude",
    "priority_score"
]

required_hospital = [
    "junction_id",
    "hospital_access_risk",
    "hospital_accessibility_score"
]

missing_priority = [
    c for c in required_priority
    if c not in priority.columns
]

missing_hospital = [
    c for c in required_hospital
    if c not in hospital.columns
]

if missing_priority:
    raise ValueError(
        f"Missing columns in priority_junctions.csv: {missing_priority}"
    )

if missing_hospital:
    raise ValueError(
        f"Missing columns in junction_hospital_scores.csv: {missing_hospital}"
    )

# ---------------------------------------------------------
# Keep only the hospital columns required for final scoring
# This prevents priority_score_x / priority_score_y problems.
# ---------------------------------------------------------

hospital = hospital[
    [
        "junction_id",
        "hospital_access_risk",
        "hospital_accessibility_score",
        "nearest_hospital_name",
        "nearest_hospital_distance_km",
        "hospitals_within_1km",
        "hospitals_within_2km",
        "hospitals_within_5km"
    ]
].copy()

# ---------------------------------------------------------
# Merge
# ---------------------------------------------------------

print("\nMerging priority and hospital information...")

df = priority.merge(
    hospital,
    on="junction_id",
    how="inner"
)

print("Merged junctions:", len(df))

if len(df) == 0:
    raise ValueError("No junctions matched during merge.")

# ---------------------------------------------------------
# Final risk score
#
# Higher priority_score = more important junction
# Higher hospital_access_risk = worse medical accessibility
#
# Weighted score:
#   60% junction priority
#   40% hospital access risk
# ---------------------------------------------------------

df["final_risk_score"] = (
    0.60 * df["priority_score"]
    + 0.40 * df["hospital_access_risk"]
)

# ---------------------------------------------------------
# Normalize final score to 0-1
# ---------------------------------------------------------

min_score = df["final_risk_score"].min()
max_score = df["final_risk_score"].max()

if max_score > min_score:
    df["final_risk_score"] = (
        (df["final_risk_score"] - min_score)
        / (max_score - min_score)
    )
else:
    df["final_risk_score"] = 0.0

# ---------------------------------------------------------
# Risk category
# ---------------------------------------------------------

def risk_category(score):
    if score >= 0.75:
        return "CRITICAL"
    elif score >= 0.50:
        return "HIGH"
    elif score >= 0.25:
        return "MEDIUM"
    else:
        return "LOW"


df["risk_category"] = df["final_risk_score"].apply(risk_category)

# ---------------------------------------------------------
# Rank
# ---------------------------------------------------------

df = df.sort_values(
    "final_risk_score",
    ascending=False
).reset_index(drop=True)

df["final_risk_rank"] = range(1, len(df) + 1)

# ---------------------------------------------------------
# Output columns
# ---------------------------------------------------------

output_columns = [
    "final_risk_rank",
    "junction_id",
    "longitude",
    "latitude",
    "priority_score",
    "hospital_access_risk",
    "hospital_accessibility_score",
    "nearest_hospital_name",
    "nearest_hospital_distance_km",
    "hospitals_within_1km",
    "hospitals_within_2km",
    "hospitals_within_5km",
    "final_risk_score",
    "risk_category"
]

df = df[output_columns]

# ---------------------------------------------------------
# Results
# ---------------------------------------------------------

print("\n==========================================")
print("       FINAL RISK SCORE RESULT")
print("==========================================")

print("Junctions scored:", len(df))

print("\nRisk category distribution:")
print(
    df["risk_category"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nFinal risk score statistics:")
print(
    df["final_risk_score"]
    .describe()
    .to_string()
)

print("\nTop 20 highest-risk junctions:")

print(
    df[
        [
            "final_risk_rank",
            "junction_id",
            "longitude",
            "latitude",
            "priority_score",
            "hospital_access_risk",
            "nearest_hospital_distance_km",
            "hospitals_within_5km",
            "final_risk_score",
            "risk_category"
        ]
    ]
    .head(20)
    .to_string(index=False)
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

print("\nSaved:")
print(OUTPUT_PATH)

print("\nDONE.")

