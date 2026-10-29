from pathlib import Path

import pandas as pd


# =====================================================
# PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "emergency_junction_hotspots.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "intervention_analysis.csv"
)


# =====================================================
# LOAD
# =====================================================

print("=" * 60)
print("EMERGENCY INTERVENTION ANALYSIS")
print("=" * 60)

df = pd.read_csv(INPUT_FILE)

print(f"Loaded records: {len(df)}")


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def classify_primary_concern(row):

    hospital_risk = float(
        row.get("hospital_access_risk", 0)
    )

    priority = float(
        row.get("priority_score", 0)
    )

    distance = float(
        row.get(
            "nearest_hospital_distance_km",
            0
        )
    )

    if hospital_risk >= 0.7:

        return (
            "Hospital Accessibility"
        )

    if distance >= 3:

        return (
            "Hospital Connectivity"
        )

    if priority >= 0.7:

        return (
            "Junction Priority"
        )

    if priority >= 0.4:

        return (
            "Traffic / Junction Investigation"
        )

    return (
        "Routine Monitoring"
    )


def recommend_intervention(row):

    concern =classify_primary_concern(row)

    category = str(
        row.get(
            "risk_category",
            "LOW"
        )
    ).upper()


    if concern == "Hospital Accessibility":

        return (
            "Assess emergency-access connectivity "
            "to nearby healthcare facilities."
        )


    if concern == "Hospital Connectivity":

        return (
            "Investigate road connectivity and "
            "alternative emergency-access links "
            "to healthcare facilities."
        )


    if concern == "Junction Priority":

        return (
            "Conduct detailed junction and "
            "traffic-flow assessment."
        )


    if concern == "Traffic / Junction Investigation":

        return (
            "Monitor junction conditions and "
            "investigate emergency vehicle access."
        )


    return (
        "Routine monitoring and reassessment "
        "when additional traffic or incident "
        "data becomes available."
    )


def urgency(row):

    category = str(
        row.get(
            "risk_category",
            "LOW"
        )
    ).upper()

    if category == "CRITICAL":
        return "Immediate Investigation"

    if category == "HIGH":
        return "High Priority Investigation"

    if category == "MEDIUM":
        return "Monitor"

    return "Routine"


def scenario_note(row):

    concern = classify_primary_concern(row)

    return (
        f"Reducing the identified {concern.lower()} "
        "constraint could potentially improve "
        "emergency accessibility. This is a planning "
        "scenario, not a measured prediction of "
        "response-time improvement."
    )


# =====================================================
# APPLY ANALYSIS
# =====================================================

df["primary_concern"] = df.apply(
    classify_primary_concern,
    axis=1
)

df["suggested_intervention"] = df.apply(
    recommend_intervention,
    axis=1
)

df["intervention_priority"] = df.apply(
    urgency,
    axis=1
)

df["scenario_assessment"] = df.apply(
    scenario_note,
    axis=1
)


# =====================================================
# SELECT USEFUL COLUMNS
# =====================================================

columns = [
    "final_risk_rank",
    "junction_id",
    "area_name",
    "risk_category",
    "final_risk_score",
    "priority_score",
    "hospital_access_risk",
    "nearest_hospital_distance_km",
    "hospitals_within_5km",
    "primary_concern",
    "suggested_intervention",
    "intervention_priority",
    "scenario_assessment"
]


columns = [
    col
    for col in columns
    if col in df.columns
]


result = df[columns].copy()


# =====================================================
# SAVE
# =====================================================

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# =====================================================
# SUMMARY
# =====================================================

print()
print("Intervention analysis completed.")
print()

print(
    result[
        [
            "primary_concern",
            "intervention_priority"
        ]
    ]
    .value_counts()
)

print()
print(f"Saved to:")
print(OUTPUT_FILE)

print("=" * 60)