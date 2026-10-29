# Emergency Access Intelligence
## System Architecture

## 1. Overview

Emergency Access Intelligence is a geospatial
decision-support prototype designed to identify
locations where emergency access may be constrained.

The system combines road-network analysis,
junction prioritization and hospital accessibility.

---

## 2. Data Sources

### OpenStreetMap

Used for:

- Road network
- Junction information
- Named places
- Geographic context

### Hospital Dataset

Used for:

- Hospital locations
- Nearest hospital distance
- Hospitals within 5 km

---

## 3. Processing Pipeline

OpenStreetMap Road Network
        |
        v
Road Network Processing
        |
        v
Junction Detection
        |
        v
Physical Junction Clustering
        |
        v
Junction Feature Extraction
        |
        v
Junction Priority Score
        |
        +----------------------+
        |                      |
        v                      v
Hospital Locations       Road Network
        |                      |
        v                      |
Hospital Accessibility        |
        |                      |
        +----------+-----------+
                   |
                   v
          Emergency Risk Score
                   |
          +--------+--------+
          |                 |
          v                 v
   Risk Classification   Explainability
          |                 |
          +--------+--------+
                   |
                   v
           Corridor Analysis
                   |
                   v
        Intervention Analysis
                   |
                   v
             FastAPI API
                   |
                   v
          Interactive Dashboard

---

## 4. Risk Components

### Junction Priority

Represents the priority of a junction based
on the road-network analysis.

### Hospital Accessibility

Uses:

- Distance to nearest mapped hospital
- Number of hospitals within 5 km

### Final Risk

The system combines these indicators into
a normalized risk score between 0 and 1.

---

## 5. Risk Categories

The normalized risk score is converted into
four categories:

- Critical
- High
- Medium
- Low

---

## 6. Explainability

For each prioritized location the system
provides:

- Area name
- Risk category
- Risk score
- Junction priority
- Hospital access risk
- Nearest hospital distance
- Hospitals within 5 km
- Risk explanation
- Recommended action
- Data confidence

---

## 7. Corridor Analysis

Critical and High-risk junctions are grouped
into nearby corridor candidates.

These represent locations that may require
corridor-level investigation.

They should not be interpreted as actual
ambulance routes.

---

## 8. Intervention Analysis

The system identifies a primary concern and
suggests a possible planning intervention.

Examples:

- Hospital accessibility assessment
- Hospital connectivity investigation
- Junction traffic-flow assessment
- Emergency-access investigation
- Routine monitoring

These are planning recommendations rather
than guaranteed predictions of response-time
improvement.

---

## 9. Backend

Technology:

- Python
- FastAPI
- Pandas
- NumPy

The backend exposes endpoints for:

- Summary
- Hotspots
- Search
- Risk categories
- Corridors
- Map data
- Risk and hospital-distance analytics
- Hypothetical intervention scenarios
- Downloadable planning report

---

## 10. Frontend

Technology:

- HTML
- CSS
- JavaScript
- Leaflet.js

The dashboard provides:

- Interactive map
- Risk filters
- Area search
- Hotspot details
- Explainable risk
- Corridor candidates
- Priority table
- Risk and hospital-distance analytics
- A user-adjustable, hypothetical model-component scenario
- Downloadable planning summary report

Scenario results modify one input component in the existing weighted score
(60% junction priority, 40% hospital-access risk) and retain the dataset's
baseline normalization range. They are model comparisons only, not predictions
of travel-time or emergency-outcome improvements.

---

## 11. Deployment Considerations

The prototype can be extended using:

- Live traffic data
- Emergency incident data
- Historical ambulance response data
- Verified hospital data
- Municipal road information
- Traffic signal information

These additional datasets would be required
for operational deployment and empirical validation.