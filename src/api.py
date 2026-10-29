from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
FRONTEND_DIR = BASE_DIR / "frontend"

HOTSPOTS_FILE = DATA_DIR / "emergency_junction_hotspots.csv"
CORRIDORS_FILE = DATA_DIR / "emergency_corridors.csv"


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Emergency Access Intelligence API",
    description=(
        "Geospatial decision-support API for identifying "
        "junctions where emergency access may be constrained."
    ),
    version="3.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# LOAD DATA
# ============================================================

if not HOTSPOTS_FILE.exists():
    raise FileNotFoundError(
        f"Hotspot dataset not found: {HOTSPOTS_FILE}"
    )

hotspots_df = pd.read_csv(HOTSPOTS_FILE)


if CORRIDORS_FILE.exists():
    corridors_df = pd.read_csv(CORRIDORS_FILE)
else:
    corridors_df = pd.DataFrame()


# ============================================================
# CLEAN DATA
# ============================================================

hotspots_df = hotspots_df.replace(
    {float("nan"): None}
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def records(df):
    """
    Convert DataFrame into JSON-safe records.
    """
    return df.where(pd.notnull(df), None).to_dict(
        orient="records"
    )


def get_risk_counts():

    counts = (
        hotspots_df["risk_category"]
        .value_counts()
        .to_dict()
    )

    return {
        "CRITICAL": int(counts.get("CRITICAL", 0)),
        "HIGH": int(counts.get("HIGH", 0)),
        "MEDIUM": int(counts.get("MEDIUM", 0)),
        "LOW": int(counts.get("LOW", 0))
    }


def classify_risk(score):
    if score >= 0.75:
        return "CRITICAL"
    if score >= 0.50:
        return "HIGH"
    if score >= 0.25:
        return "MEDIUM"
    return "LOW"


# ============================================================
# ROOT
# ============================================================

@app.get("/api")
def root():

    return {
        "name": "Emergency Access Intelligence API",
        "version": "3.0.0",
        "status": "running",
        "description": (
            "API for emergency-access risk intelligence "
            "and junction prioritization."
        )
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "hotspots_loaded": len(hotspots_df),
        "corridors_loaded": len(corridors_df)
    }


# ============================================================
# SUMMARY
# ============================================================

@app.get("/summary")
def summary():

    counts = get_risk_counts()

    return {
        "total_junctions": int(len(hotspots_df)),

        "critical": counts["CRITICAL"],
        "high": counts["HIGH"],
        "medium": counts["MEDIUM"],
        "low": counts["LOW"],

        "risk_corridors": int(len(corridors_df)),

        "mean_risk_score": round(
            float(
                hotspots_df["final_risk_score"].mean()
            ),
            4
        ),

        "max_risk_score": round(
            float(
                hotspots_df["final_risk_score"].max()
            ),
            4
        ),

        "mean_nearest_hospital_km": round(
            float(
                hotspots_df[
                    "nearest_hospital_distance_km"
                ].mean()
            ),
            3
        )
    }


# ============================================================
# ALL HOTSPOTS
# ============================================================

@app.get("/hotspots")
def get_hotspots(
    limit: int = Query(
        100,
        ge=1,
        le=5000
    )
):

    df = hotspots_df.head(limit)

    return {
        "count": len(df),
        "data": records(df)
    }


# ============================================================
# CRITICAL HOTSPOTS
# ============================================================

@app.get("/hotspots/critical")
def critical_hotspots():

    df = hotspots_df[
        hotspots_df["risk_category"] == "CRITICAL"
    ]

    return {
        "count": len(df),
        "data": records(df)
    }


# ============================================================
# HIGH HOTSPOTS
# ============================================================

@app.get("/hotspots/high")
def high_hotspots():

    df = hotspots_df[
        hotspots_df["risk_category"] == "HIGH"
    ]

    return {
        "count": len(df),
        "data": records(df)
    }


# ============================================================
# SINGLE HOTSPOT
# ============================================================

@app.get("/hotspots/{junction_id}")
def hotspot_details(junction_id: int):

    result = hotspots_df[
        hotspots_df["junction_id"] == junction_id
    ]

    if result.empty:

        raise HTTPException(
            status_code=404,
            detail="Junction not found"
        )

    return result.iloc[0].where(
        pd.notnull(result.iloc[0]),
        None
    ).to_dict()


# ============================================================
# FILTER BY RISK CATEGORY
# ============================================================

@app.get("/risk/{category}")
def risk_category(category: str):

    category = category.upper()

    allowed = [
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW"
    ]

    if category not in allowed:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid category. "
                "Use CRITICAL, HIGH, MEDIUM or LOW."
            )
        )

    df = hotspots_df[
        hotspots_df["risk_category"] == category
    ]

    return {
        "category": category,
        "count": len(df),
        "data": records(df)
    }


# ============================================================
# SEARCH BY AREA NAME
# ============================================================

@app.get("/search")
def search_hotspots(
    q: str = Query(
        ...,
        min_length=1
    )
):

    query = q.lower().strip()

    mask = (
        hotspots_df["area_name"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.contains(
            query,
            regex=False
        )
    )

    df = hotspots_df[mask]

    return {
        "query": q,
        "count": len(df),
        "data": records(df.head(100))
    }


# ============================================================
# MAP DATA
# ============================================================

@app.get("/map")
def map_data(
    limit: int = Query(
        500,
        ge=1,
        le=5000
    )
):

    columns = [
        "junction_id",
        "longitude",
        "latitude",
        "final_risk_score",
        "risk_category",
        "priority_score",
        "hospital_access_risk",
        "nearest_hospital_distance_km",
        "hospitals_within_5km",
        "area_name",
        "area_type",
        "risk_explanation",
        "recommended_action",
        "data_confidence"
    ]

    available_columns = [
        c for c in columns
        if c in hotspots_df.columns
    ]

    df = hotspots_df[
        available_columns
    ].head(limit)

    return {
        "count": len(df),
        "data": records(df)
    }


# ============================================================
# CORRIDORS
# ============================================================

@app.get("/corridors")
def get_corridors():

    if corridors_df.empty:

        return {
            "count": 0,
            "data": []
        }

    return {
        "count": len(corridors_df),
        "data": records(corridors_df)
    }


# ============================================================
# TOP CORRIDORS
# ============================================================

@app.get("/corridors/top")
def top_corridors(
    limit: int = Query(
        10,
        ge=1,
        le=100
    )
):

    if corridors_df.empty:

        return {
            "count": 0,
            "data": []
        }

    sort_column = None

    for column in [
        "corridor_priority",
        "mean_risk",
        "priority_score"
    ]:

        if column in corridors_df.columns:

            sort_column = column
            break

    if sort_column:

        df = corridors_df.sort_values(
            sort_column,
            ascending=False
        ).head(limit)

    else:

        df = corridors_df.head(limit)

    return {
        "count": len(df),
        "data": records(df)
    }


# ============================================================
# ANALYTICS
# ============================================================

@app.get("/analytics")
def analytics():
    distances = pd.to_numeric(
        hotspots_df["nearest_hospital_distance_km"],
        errors="coerce"
    )
    coverage = pd.to_numeric(
        hotspots_df["hospitals_within_5km"],
        errors="coerce"
    )

    bands = [
        ("Under 0.5 km", distances < 0.5),
        ("0.5-1 km", (distances >= 0.5) & (distances < 1)),
        ("1-3 km", (distances >= 1) & (distances < 3)),
        ("3 km or more", distances >= 3)
    ]

    return {
        "total_junctions": int(len(hotspots_df)),
        "risk_distribution": get_risk_counts(),
        "mean_nearest_hospital_km": round(float(distances.mean()), 3),
        "junctions_without_hospital_within_5km": int((coverage == 0).sum()),
        "hospital_distance_bands": [
            {"label": label, "count": int(mask.sum())}
            for label, mask in bands
        ]
    }


# ============================================================
# INTERVENTION SCENARIO
# ============================================================

@app.get("/simulate/{junction_id}")
def simulate_intervention(
    junction_id: int,
    component: str = "hospital_access_risk",
    reduction_pct: float = Query(25, ge=0, le=100)
):
    if component not in {"hospital_access_risk", "priority_score"}:
        raise HTTPException(
            status_code=400,
            detail="Component must be hospital_access_risk or priority_score."
        )

    result = hotspots_df[hotspots_df["junction_id"] == junction_id]
    if result.empty:
        raise HTTPException(status_code=404, detail="Junction not found")

    priority = pd.to_numeric(hotspots_df["priority_score"], errors="coerce")
    hospital_risk = pd.to_numeric(
        hotspots_df["hospital_access_risk"],
        errors="coerce"
    )
    baseline_raw = 0.60 * priority + 0.40 * hospital_risk
    score_min = float(baseline_raw.min())
    score_max = float(baseline_raw.max())

    selected = result.iloc[0]
    current_priority = float(selected["priority_score"])
    current_hospital_risk = float(selected["hospital_access_risk"])
    current_component = (
        current_hospital_risk
        if component == "hospital_access_risk"
        else current_priority
    )
    adjusted_component = current_component * (1 - reduction_pct / 100)

    scenario_priority = (
        adjusted_component
        if component == "priority_score"
        else current_priority
    )
    scenario_hospital_risk = (
        adjusted_component
        if component == "hospital_access_risk"
        else current_hospital_risk
    )
    scenario_raw = 0.60 * scenario_priority + 0.40 * scenario_hospital_risk

    def normalize(raw_score):
        if score_max == score_min:
            return 0.0
        return max(0.0, min(1.0, (raw_score - score_min) / (score_max - score_min)))

    current_score = normalize(
        0.60 * current_priority + 0.40 * current_hospital_risk
    )
    scenario_score = normalize(scenario_raw)

    return {
        "junction_id": junction_id,
        "area_name": selected.get("area_name"),
        "component": component,
        "reduction_pct": reduction_pct,
        "current_component_value": round(current_component, 4),
        "scenario_component_value": round(adjusted_component, 4),
        "current_risk_score": round(current_score, 4),
        "current_risk_category": classify_risk(current_score),
        "scenario_risk_score": round(scenario_score, 4),
        "scenario_risk_category": classify_risk(scenario_score),
        "score_change": round(scenario_score - current_score, 4),
        "disclaimer": (
            "Hypothetical change to one model component only. "
            "This is not a measured prediction of travel time, "
            "hospital access, or emergency outcomes."
        )
    }


# ============================================================
# PLANNING REPORT
# ============================================================

@app.get("/planning-report")
def planning_report():
    summary_data = summary()
    top_hotspots = hotspots_df.nlargest(10, "final_risk_score")
    report_lines = [
        "EMERGENCY ACCESS INTELLIGENCE - PLANNING SUMMARY",
        "",
        "Decision-support prototype; not for live dispatch or navigation.",
        "The model uses mapped road-junction priority and hospital-access indicators.",
        "It does not include live traffic, road closures, signal timing, or validated response-time data.",
        "",
        f"Junctions analyzed: {summary_data['total_junctions']}",
        f"Mapped hospitals: {len(pd.read_csv(DATA_DIR / 'hospitals_clean.csv'))}",
        f"Risk corridors: {summary_data['risk_corridors']}",
        f"Mean nearest mapped hospital distance: {summary_data['mean_nearest_hospital_km']} km",
        "",
        "RISK DISTRIBUTION"
    ]
    report_lines.extend(
        f"{category}: {summary_data[category.lower()]}"
        for category in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
    )
    report_lines.extend(["", "TOP 10 JUNCTIONS"])

    for _, row in top_hotspots.iterrows():
        report_lines.append(
            f"Rank {int(row['final_risk_rank'])}: "
            f"{row.get('area_name') or 'Unnamed area'} "
            f"(ID {int(row['junction_id'])}) - "
            f"{row['risk_category']}, score {float(row['final_risk_score']):.3f}; "
            f"nearest hospital {float(row['nearest_hospital_distance_km']):.2f} km; "
            f"{int(row['hospitals_within_5km'])} hospitals within 5 km."
        )

    return PlainTextResponse(
        "\n".join(report_lines) + "\n",
        headers={
            "Content-Disposition": (
                'attachment; filename="emergency-access-planning-report.txt"'
            )
        }
    )


# ============================================================
# START MESSAGE
# ============================================================

print("=" * 60)
print("Emergency Access Intelligence API")
print("=" * 60)
print(f"Hotspots loaded : {len(hotspots_df)}")
print(f"Corridors loaded: {len(corridors_df)}")
print(f"Data directory  : {DATA_DIR}")
print("=" * 60)

app.mount(
    "/",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="frontend"
)