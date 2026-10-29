import pandas as pd
from pathlib import Path

INPUT_PATH = Path(
    "data/processed/final_junction_risk.csv"
)

print("==========================================")
print("         RISK SUMMARY ANALYSIS")
print("==========================================")

df = pd.read_csv(INPUT_PATH)

# ---------------------------------------------------------
# Category counts
# ---------------------------------------------------------

category_counts = (
    df["risk_category"]
    .value_counts()
)

total = len(df)

print("\nRisk categories:")

for category in [
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW"
]:

    count = int(
        category_counts.get(category, 0)
    )

    percentage = (
        count / total * 100
    )

    print(
        f"{category:8s}: "
        f"{count:5d} "
        f"({percentage:.2f}%)"
    )

# ---------------------------------------------------------
# Critical/high junctions
# ---------------------------------------------------------

high_risk = df[
    df["risk_category"].isin(
        ["CRITICAL", "HIGH"]
    )
]

print("\nHigh-priority junctions:")
print(len(high_risk))

# ---------------------------------------------------------
# Hospital access
# ---------------------------------------------------------

print("\nHospital accessibility:")

print(
    "Mean nearest hospital distance:",
    round(
        df["nearest_hospital_distance_km"].mean(),
        3
    ),
    "km"
)

print(
    "Maximum nearest hospital distance:",
    round(
        df["nearest_hospital_distance_km"].max(),
        3
    ),
    "km"
)

print(
    "Mean hospitals within 5 km:",
    round(
        df["hospitals_within_5km"].mean(),
        2
    )
)

# ---------------------------------------------------------
# Highest risk
# ---------------------------------------------------------

highest = df.loc[
    df["final_risk_score"].idxmax()
]

print("\nHighest-risk junction:")

print(
    highest[
        [
            "junction_id",
            "latitude",
            "longitude",
            "final_risk_score",
            "hospital_access_risk",
            "nearest_hospital_distance_km",
            "hospitals_within_5km"
        ]
    ].to_string()
)

print("\nDONE.")