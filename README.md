# Emergency Access Intelligence

A geospatial decision-support prototype for exploring road-junction priority,
mapped hospital access, and potential emergency-access constraints in the
Greater Hyderabad Municipal Corporation (GHMC) area.

The project includes a processed dataset of 5,000 junctions and 2,916 mapped
hospitals, a FastAPI API, and a Leaflet dashboard. The risk model combines
normalized junction priority (60%) and hospital-access risk (40%), then
normalizes the result against the analyzed dataset and classifies locations as
Critical, High, Medium, or Low.

This is a planning prototype, **not** a live emergency dispatch or navigation
system. It does not use real-time traffic, road closures, signal timing, or
validated ambulance response-time data. Hospital locations and road
information are based on OpenStreetMap and may be incomplete or out of date.
Model scores and intervention scenarios must not be interpreted as measured
travel-time or emergency-outcome predictions.

## Requirements

- Python 3.11 or newer
- The processed CSV files in `data/processed/`
- Internet access in the browser to load the OpenStreetMap tiles and Leaflet
  assets used by the dashboard

The local working copy may contain the original OSM extract and intermediate
geospatial outputs. These large source and derived files are excluded from Git;
the processed CSVs required to run and validate the dashboard are tracked.
Rebuilding the pipeline requires separately obtaining the OSM extract,
installing the optional geospatial dependencies listed under the `pipeline`
extra, and sufficient time and disk space.

## Install

From the project directory, create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

For data-pipeline development, install its optional dependencies as well:

```powershell
python -m pip install -e ".[pipeline]"
```

## Run

Start the API and dashboard from the project directory:

```powershell
python -m uvicorn src.api:app --reload
```

Open <http://127.0.0.1:8000/>. The dashboard and API share one server; the
frontend uses the current page's origin, so no separate frontend server or
hard-coded API address is needed.

Useful endpoints:

| URL | Description |
| --- | --- |
| `/api` | API status and version |
| `/health` | Loaded dataset counts |
| `/docs` | Interactive OpenAPI documentation |
| `/summary` | Risk counts and overall summary |
| `/analytics` | Risk distribution and hospital-distance bands |
| `/hotspots` | Junction hotspot records |
| `/search?q=Osman` | Search by area name |
| `/corridors` | Candidate high-risk corridors |
| `/simulate/{junction_id}` | Hypothetical model-component scenario |
| `/planning-report` | Downloadable planning summary |

The scenario endpoint accepts `component=hospital_access_risk` or
`component=priority_score` and `reduction_pct` from 0 to 100. It changes one
component for one junction while keeping the original dataset's normalization
range fixed. This makes the score comparison interpretable; it does not
simulate a real intervention or estimate its impact on emergency response.

## Validate and test

Run the dataset validation:

```powershell
$env:PYTHONIOENCODING = "utf-8"
python src\validate_project.py
```

Run the API tests:

```powershell
python -m pip install -e ".[test]"
python -m pytest
```

The tests use the processed project data and do not download data or contact
external services.

## Data pipeline

The numbered processing stages are implemented as individual scripts in
`src/`. The final dataset and the order of transformations are described in
[docs/architecture.mD](docs/architecture.mD). Generated processed files should
be validated before they are used by the API:

```powershell
python src\validate_project.py
```

The primary runtime input files are:

- `data/processed/emergency_junction_hotspots.csv`
- `data/processed/emergency_corridors.csv`
- `data/processed/hospitals_clean.csv`
