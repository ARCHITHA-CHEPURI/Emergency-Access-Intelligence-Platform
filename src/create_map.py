from pathlib import Path
import pandas as pd
import folium

# ==========================================
#        EMERGENCY HOTSPOT MAP
# ==========================================

print("==========================================")
print("        EMERGENCY HOTSPOT MAP")
print("==========================================")

BASE_DIR = Path(__file__).resolve().parent.parent

RISK_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "emergency_junctions_named.csv"
)

HOSPITAL_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "hospitals_clean.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "emergency_hotspot_map.html"
)

# ==========================================
# LOAD RISK DATA
# ==========================================

print("\nLoading named risk data...")

risk_df = pd.read_csv(RISK_FILE)

print(
    f"Total risk records: {len(risk_df)}"
)

# ==========================================
# SELECT TOP 500
# ==========================================

map_df = risk_df.head(500).copy()

print(
    f"Risk junctions selected for map: {len(map_df)}"
)

# ==========================================
# LOAD HOSPITALS
# ==========================================

print("\nLoading hospitals...")

hospitals = pd.read_csv(HOSPITAL_FILE)

hospitals = hospitals.dropna(
    subset=[
        "latitude",
        "longitude"
    ]
).copy()

# ==========================================
# FIND HOSPITALS NEAR TOP HOTSPOTS
# ==========================================

min_lat = map_df["latitude"].min()
max_lat = map_df["latitude"].max()

min_lon = map_df["longitude"].min()
max_lon = map_df["longitude"].max()

# Add geographic buffer
BUFFER = 0.08

nearby_hospitals = hospitals[
    (hospitals["latitude"] >= min_lat - BUFFER)
    & (hospitals["latitude"] <= max_lat + BUFFER)
    & (hospitals["longitude"] >= min_lon - BUFFER)
    & (hospitals["longitude"] <= max_lon + BUFFER)
].copy()

print(
    f"Nearby hospitals plotted: "
    f"{len(nearby_hospitals)}"
)

# ==========================================
# CREATE MAP
# ==========================================

center_lat = map_df["latitude"].mean()
center_lon = map_df["longitude"].mean()

m = folium.Map(
    location=[
        center_lat,
        center_lon
    ],
    zoom_start=10,
    control_scale=True
)

# ==========================================
# HOSPITAL LAYER
# ==========================================

hospital_group = folium.FeatureGroup(
    name="Hospitals"
)

for _, hospital in nearby_hospitals.iterrows():

    hospital_name = str(
        hospital.get(
            "name",
            "Hospital"
        )
    )

    folium.CircleMarker(
        location=[
            hospital["latitude"],
            hospital["longitude"]
        ],
        radius=3,
        tooltip=f"🏥 {hospital_name}",
        popup=f"""
        <b>🏥 Hospital</b><br>
        <b>Name:</b> {hospital_name}
        """,
        fill=True,
        fill_opacity=0.8
    ).add_to(hospital_group)

hospital_group.add_to(m)

# ==========================================
# RISK LAYERS
# ==========================================

critical_group = folium.FeatureGroup(
    name="🚨 Critical"
)

high_group = folium.FeatureGroup(
    name="🔴 High"
)

medium_group = folium.FeatureGroup(
    name="🟠 Medium"
)

low_group = folium.FeatureGroup(
    name="🟢 Low"
)

# ==========================================
# ADD JUNCTION MARKERS
# ==========================================

for _, row in map_df.iterrows():

    category = str(
        row["risk_category"]
    ).upper()

    # --------------------------------------
    # LOCATION
    # --------------------------------------

    area = str(
        row.get(
            "nearby_area",
            "Unknown area"
        )
    )

    area_type = str(
        row.get(
            "nearby_area_type",
            "area"
        )
    )

    area_distance = float(
        row.get(
            "area_distance_km",
            0
        )
    )

    # --------------------------------------
    # RISK
    # --------------------------------------

    risk_score = float(
        row["final_risk_score"]
    )

    rank = int(
        row["final_risk_rank"]
    )

    # --------------------------------------
    # HOSPITAL
    # --------------------------------------

    hospital_distance = float(
        row[
            "nearest_hospital_distance_km"
        ]
    )

    hospitals_5km = int(
        row["hospitals_within_5km"]
    )

    # --------------------------------------
    # PRIORITY
    # --------------------------------------

    emergency_priority = str(
        row.get(
            "emergency_priority",
            "Monitor"
        )
    )

    # --------------------------------------
    # POPUP
    # --------------------------------------

    popup_html = f"""
    <div style="width:300px">

        <h3>🚨 Emergency Hotspot</h3>

        <b>📍 Area:</b> {area}<br>
        <b>Area type:</b> {area_type}<br>
        <b>Approx. area distance:</b>
        {area_distance:.2f} km<br><br>

        <b>⚠️ Risk level:</b> {category}<br>
        <b>Risk score:</b> {risk_score:.3f}<br>
        <b>Priority rank:</b> #{rank}<br><br>

        <b>🏥 Nearest hospital:</b>
        {hospital_distance:.2f} km<br>

        <b>🏥 Hospitals within 5 km:</b>
        {hospitals_5km}<br><br>

        <b>🚑 Recommended action:</b>
        {emergency_priority}<br><br>

        <small>
        Technical junction reference:
        {int(row["junction_id"])}
        </small>

    </div>
    """

    # --------------------------------------
    # TOOLTIP
    # --------------------------------------

    tooltip_text = (
        f"🚨 {category} | "
        f"📍 {area} | "
        f"Risk {risk_score:.2f}"
    )

    # --------------------------------------
    # MARKER
    # --------------------------------------

    marker = folium.CircleMarker(
        location=[
            row["latitude"],
            row["longitude"]
        ],
        radius=7 if category == "CRITICAL" else 5,
        tooltip=tooltip_text,
        popup=folium.Popup(
            popup_html,
            max_width=350
        ),
        fill=True,
        fill_opacity=0.85
    )

    # --------------------------------------
    # ADD TO CATEGORY
    # --------------------------------------

    if category == "CRITICAL":
        marker.add_to(critical_group)

    elif category == "HIGH":
        marker.add_to(high_group)

    elif category == "MEDIUM":
        marker.add_to(medium_group)

    else:
        marker.add_to(low_group)

# ==========================================
# ADD LAYERS
# ==========================================

critical_group.add_to(m)
high_group.add_to(m)
medium_group.add_to(m)
low_group.add_to(m)

# ==========================================
# LAYER CONTROL
# ==========================================

folium.LayerControl(
    collapsed=False
).add_to(m)

# ==========================================
# SAVE
# ==========================================

m.save(OUTPUT_FILE)

# ==========================================
# RESULT
# ==========================================

print("\n==========================================")
print("       MAP CREATION RESULT")
print("==========================================")

print(
    f"Risk junctions mapped: {len(map_df)}"
)

print(
    f"Hospitals mapped: "
    f"{len(nearby_hospitals)}"
)

print("\nSaved:")
print(OUTPUT_FILE)

print("\nDONE.")