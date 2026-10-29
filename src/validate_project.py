from pathlib import Path

import pandas as pd


# =====================================================
# PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = (
    BASE_DIR
    / "data"
    / "processed"
)

FINAL_FILE = (
    DATA_DIR
    / "emergency_junction_hotspots.csv"
)

HOSPITAL_FILE = (
    DATA_DIR
    / "hospitals_clean.csv"
)

CORRIDOR_FILE = (
    DATA_DIR
    / "emergency_corridors.csv"
)

INTERVENTION_FILE = (
    DATA_DIR
    / "intervention_analysis.csv"
)


# =====================================================
# HEADER
# =====================================================

print()
print("=" * 65)
print("      EMERGENCY ACCESS INTELLIGENCE")
print("          FINAL VALIDATION REPORT")
print("=" * 65)


errors = []


# =====================================================
# FILE CHECK
# =====================================================

def check_file(path, name):

    if path.exists():

        print(
            f"✓ {name:<35} PASS"
        )

        return True

    print(
        f"✗ {name:<35} FAIL"
    )

    errors.append(
        f"Missing file: {name}"
    )

    return False


check_file(
    FINAL_FILE,
    "Final hotspot dataset"
)

check_file(
    HOSPITAL_FILE,
    "Clean hospital dataset"
)

check_file(
    CORRIDOR_FILE,
    "Corridor analysis"
)

check_file(
    INTERVENTION_FILE,
    "Intervention analysis"
)


# =====================================================
# FINAL DATASET
# =====================================================

df = None

if FINAL_FILE.exists():

    df = pd.read_csv(
        FINAL_FILE
    )

    print()
    print("DATASET")
    print("-" * 65)

    print(
        f"Junctions analyzed       : {len(df)}"
    )


    # -------------------------------------------------
    # REQUIRED COLUMNS
    # -------------------------------------------------

    required_columns = [
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


    missing_columns = [
        col
        for col in required_columns
        if col not in df.columns
    ]


    if missing_columns:

        print(
            "✗ Required columns         FAIL"
        )

        errors.append(
            "Missing columns: "
            + ", ".join(
                missing_columns
            )
        )

    else:

        print(
            "✓ Required columns         PASS"
        )


    # -------------------------------------------------
    # DUPLICATES
    # -------------------------------------------------

    duplicate_count =df["junction_id"].duplicated().sum()

    if duplicate_count == 0:

        print(
            "✓ Duplicate junction IDs   PASS"
        )

    else:

        print(
            "✗ Duplicate junction IDs   FAIL"
        )

        errors.append(
            f"Duplicate IDs: {duplicate_count}"
        )


    # -------------------------------------------------
    # COORDINATES
    # -------------------------------------------------

    missing_coords =df[
            [
                "longitude",
                "latitude"
            ]
        ].isna().any(axis=1).sum()


    if missing_coords == 0:

        print(
            "✓ Coordinates               PASS"
        )

    else:

        print(
            "✗ Coordinates               FAIL"
        )

        errors.append(
            f"Missing coordinates: {missing_coords}"
        )


    # -------------------------------------------------
    # RISK SCORE
    # -------------------------------------------------

    scores =pd.to_numeric(
            df["final_risk_score"],
            errors="coerce"
        )


    invalid_scores =(
            scores.isna()
            |
            (scores < 0)
            |
            (scores > 1)
        ).sum()


    if invalid_scores == 0:

        print(
            "✓ Risk score range         PASS"
        )

    else:

        print(
            "✗ Risk score range         FAIL"
        )

        errors.append(
            f"Invalid risk scores: {invalid_scores}"
        )


    # -------------------------------------------------
    # CATEGORIES
    # -------------------------------------------------

    valid_categories = {
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW"
    }


    categories =set(
            df["risk_category"]
            .dropna()
            .astype(str)
            .str.upper()
        )


    invalid_categories =categories - valid_categories


    if not invalid_categories:

        print(
            "✓ Risk categories          PASS"
        )

    else:

        print(
            "✗ Risk categories          FAIL"
        )

        errors.append(
            "Invalid categories: "
            + ", ".join(
                invalid_categories
            )
        )


# =====================================================
# HOSPITALS
# =====================================================

if HOSPITAL_FILE.exists():

    hospitals =pd.read_csv(
            HOSPITAL_FILE
        )

    print()
    print("HOSPITAL DATA")
    print("-" * 65)

    print(
        f"Hospitals analyzed        : {len(hospitals)}"
    )


# =====================================================
# RISK DISTRIBUTION
# =====================================================

if df is not None:

    print()
    print("RISK DISTRIBUTION")
    print("-" * 65)

    counts =(
            df["risk_category"]
            .astype(str)
            .str.upper()
            .value_counts()
        )


    for category in [
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW"
    ]:

        print(
            f"{category:<25}: "
            f"{counts.get(category, 0)}"
        )


# =====================================================
# HOSPITAL ACCESS
# =====================================================

if df is not None:

    print()
    print("HOSPITAL ACCESS")
    print("-" * 65)


    distance = pd.to_numeric(
            df[
                "nearest_hospital_distance_km"
            ],
            errors="coerce"
        )


    print(
        "Mean nearest hospital    : "
        f"{distance.mean():.3f} km"
    )


    print(
        "Maximum distance         : "
        f"{distance.max():.3f} km"
    )


# =====================================================
# CORRIDORS
# =====================================================

if CORRIDOR_FILE.exists():

    corridors = pd.read_csv(
            CORRIDOR_FILE
        )

    print()
    print("CORRIDOR ANALYSIS")
    print("-" * 65)

    print(
        f"Corridor candidates      : "
        f"{len(corridors)}"
    )


# =====================================================
# INTERVENTIONS
# =====================================================

if INTERVENTION_FILE.exists():

    interventions = pd.read_csv(
            INTERVENTION_FILE
        )

    print()
    print("INTERVENTION ANALYSIS")
    print("-" * 65)

    print(
        f"Locations analyzed       : "
        f"{len(interventions)}"
    )


# =====================================================
# FINAL STATUS
# =====================================================

print()
print("=" * 65)


if errors:

    print(
        "PROJECT VALIDATION: FAIL"
    )

    print()

    for error in errors:

        print(
            " -",
            error
        )

else:

    print(
        "PROJECT VALIDATION: PASS"
    )


print("=" * 65)
print()