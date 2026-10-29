const API_BASE = window.location.origin;

let map;
let allHotspots = [];
let allCorridors = [];
let hotspotMarkers = [];
let corridorLayers = [];
let selectedHotspot = null;


// =====================================================
// START
// =====================================================

document.addEventListener("DOMContentLoaded", () => {

    console.log("🚑 Emergency Access Intelligence started");

    initializeMap();
    attachEvents();

    loadSummary();
    loadHotspots();
    loadCorridors();
    loadAnalytics();
});


// =====================================================
// MAP
// =====================================================

function initializeMap() {

    map = L.map("map").setView(
        [17.3850, 78.4867],
        11
    );

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            attribution: "&copy; OpenStreetMap contributors",
            maxZoom: 19
        }
    ).addTo(map);
}


// =====================================================
// EVENTS
// =====================================================

function attachEvents() {

    const searchInput =
        document.getElementById("searchInput");

    const searchButton =
        document.getElementById("searchButton");

    const filter =
        document.getElementById("riskFilter");

    const reset =
        document.getElementById("resetButton");
    const reportButton =
        document.getElementById("reportButton");
    const simulateButton =
        document.getElementById("simulateButton");
    const reduction =
        document.getElementById("scenarioReduction");


    // Search button
    if (searchButton) {

        searchButton.addEventListener(
            "click",
            performSearch
        );
    }


    // Press Enter to search
    if (searchInput) {

        searchInput.addEventListener(
            "keydown",
            event => {

                if (event.key === "Enter") {
                    performSearch();
                }

            }
        );
    }


    // Risk filter
    if (filter) {

        filter.addEventListener(
            "change",
            () => {

                updateView();

                // If an area is already searched,
                // zoom again to the matching results.
                const query =
                    searchInput?.value
                        .trim();

                if (query) {
                    zoomToSearchResults();
                }
            }
        );
    }


    // Reset
    if (reset) {

        reset.addEventListener(
            "click",
            resetDashboard
        );
    }

    if (reportButton) {
        reportButton.addEventListener("click", downloadPlanningReport);
    }

    if (simulateButton) {
        simulateButton.addEventListener("click", runInterventionScenario);
    }

    if (reduction) {
        reduction.addEventListener("input", () => {
            setText(
                "scenarioReductionValue",
                `${reduction.value}%`
            );
        });
    }
}


// =====================================================
// SEARCH
// =====================================================

function performSearch() {

    const searchInput =
        document.getElementById(
            "searchInput"
        );

    if (!searchInput) {
        return;
    }


    const query =
        searchInput.value
            .trim()
            .toLowerCase();


    if (!query) {

        alert(
            "Please enter an area name."
        );

        return;
    }


    if (!allHotspots.length) {

        alert(
            "Hotspot data is still loading. Please try again."
        );

        return;
    }


    console.log(
        "Searching for:",
        query
    );


    const matches =
        allHotspots.filter(item => {

            const area =
                String(
                    item.area_name || ""
                )
                .toLowerCase()
                .trim();


            return area.includes(query);
        });


    console.log(
        "Search matches:",
        matches.length
    );


    if (!matches.length) {

        // Remove markers
        clearHotspotMarkers();


        // Clear table
        updateTable([]);


        // Update selected location area
        showSearchMessage(
            `No junctions found for "${searchInput.value}".`
        );


        return;
    }


    // Display ONLY matching locations
    displayMarkers(matches);

    updateTable(matches);


    // Zoom map to matching area
    zoomToResults(matches);


    // Show first/highest-risk matching junction
    const first =
        [...matches].sort(
            (a, b) =>
                Number(
                    b.final_risk_score ?? 0
                ) -
                Number(
                    a.final_risk_score ?? 0
                )
        )[0];


    if (first) {

        selectLocation(first);
    }
}


// =====================================================
// ZOOM TO SEARCH RESULTS
// =====================================================

function zoomToResults(results) {

    if (!results.length) {
        return;
    }


    const validPoints =
        results
            .map(item => {

                const lat =
                    Number(item.latitude);

                const lng =
                    Number(item.longitude);

                if (
                    Number.isFinite(lat) &&
                    Number.isFinite(lng)
                ) {

                    return [lat, lng];
                }

                return null;

            })
            .filter(Boolean);


    if (!validPoints.length) {
        return;
    }


    // One location
    if (validPoints.length === 1) {

        map.setView(
            validPoints[0],
            15
        );

        return;
    }


    // Multiple junctions
    const bounds =
        L.latLngBounds(
            validPoints
        );


    map.fitBounds(
        bounds,
        {
            padding: [50, 50],
            maxZoom: 15
        }
    );
}


// =====================================================
// ZOOM TO CURRENT SEARCH RESULTS
// =====================================================

function zoomToSearchResults() {

    const searchInput =
        document.getElementById(
            "searchInput"
        );


    if (!searchInput) {
        return;
    }


    const query =
        searchInput.value
            .trim()
            .toLowerCase();


    if (!query) {
        return;
    }


    const matches =
        allHotspots.filter(item => {

            const area =
                String(
                    item.area_name || ""
                )
                .toLowerCase();


            return area.includes(query);
        });


    if (matches.length) {

        zoomToResults(matches);
    }
}


// =====================================================
// RESET DASHBOARD
// =====================================================

function resetDashboard() {

    const searchInput =
        document.getElementById(
            "searchInput"
        );

    const filter =
        document.getElementById(
            "riskFilter"
        );


    if (searchInput) {
        searchInput.value = "";
    }


    if (filter) {
        filter.value = "ALL";
    }


    updateView();


    map.setView(
        [17.3850, 78.4867],
        11
    );


    resetSelectedLocation();
}


// =====================================================
// SUMMARY
// =====================================================

async function loadSummary() {

    try {

        const response =
            await fetch(
                `${API_BASE}/summary`
            );


        if (!response.ok) {
            throw new Error(
                `Summary API error: ${response.status}`
            );
        }


        const data =
            await response.json();


        console.log(
            "Summary:",
            data
        );


        setText(
            "criticalCount",
            data.critical ?? 0
        );


        setText(
            "highCount",
            data.high ?? 0
        );


        setText(
            "mediumCount",
            data.medium ?? 0
        );


        setText(
            "lowCount",
            data.low ?? 0
        );


        setText(
            "corridorCount",
            data.risk_corridors ?? 0
        );


    } catch (error) {

        console.error(
            "Summary error:",
            error
        );
    }
}


// =====================================================
// ANALYTICS
// =====================================================

async function loadAnalytics() {
    const status = document.getElementById("analyticsStatus");
    try {
        const response = await fetch(`${API_BASE}/analytics`);
        if (!response.ok) {
            throw new Error(`Analytics API error: ${response.status}`);
        }

        const data = await response.json();
        const riskLabels = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
        const maxRiskCount = Math.max(
            1,
            ...riskLabels.map(label => Number(data.risk_distribution[label] || 0))
        );
        const summary = document.getElementById("analyticsSummary");
        const bands = document.getElementById("distanceBands");

        if (summary) {
            summary.innerHTML = riskLabels.map(label => {
                const count = Number(data.risk_distribution[label] || 0);
                return `
                    <div class="analytics-card">
                        <span>${label}</span>
                        <strong>${count.toLocaleString()}</strong>
                        <div class="analytics-bar-track">
                            <div class="analytics-bar ${label.toLowerCase()}"
                                 style="width:${(count / maxRiskCount) * 100}%"></div>
                        </div>
                    </div>
                `;
            }).join("");
        }

        if (bands) {
            bands.innerHTML = `
                <div class="analytics-card">
                    <span>Mean nearest mapped hospital</span>
                    <strong>${Number(data.mean_nearest_hospital_km).toFixed(3)} km</strong>
                </div>
                <div class="analytics-card">
                    <span>No mapped hospital within 5 km</span>
                    <strong>${Number(data.junctions_without_hospital_within_5km).toLocaleString()}</strong>
                </div>
                ${data.hospital_distance_bands.map(band => `
                    <div class="analytics-card">
                        <span>${escapeHtml(band.label)}</span>
                        <strong>${Number(band.count).toLocaleString()}</strong>
                    </div>
                `).join("")}
            `;
        }

        if (status) {
            status.textContent = `Analytics for ${Number(data.total_junctions).toLocaleString()} analyzed junctions.`;
        }
    } catch (error) {
        console.error("Analytics error:", error);
        if (status) {
            status.textContent = "Unable to load analytics. Check that the API is running.";
        }
    }
}


async function runInterventionScenario() {
    if (!selectedHotspot) {
        setText("simulationResult", "Select a junction on the map or in the table first.");
        return;
    }

    const component = document.getElementById("scenarioComponent")?.value;
    const reduction = document.getElementById("scenarioReduction")?.value || "25";
    const result = document.getElementById("simulationResult");
    if (result) {
        result.textContent = "Calculating hypothetical scenario...";
    }

    try {
        const response = await fetch(
            `${API_BASE}/simulate/${encodeURIComponent(selectedHotspot.junction_id)}` +
            `?component=${encodeURIComponent(component)}` +
            `&reduction_pct=${encodeURIComponent(reduction)}`
        );
        if (!response.ok) {
            throw new Error(`Scenario API error: ${response.status}`);
        }

        const data = await response.json();
        if (result) {
            result.innerHTML = `
                <strong>${escapeHtml(data.area_name || "Selected junction")}</strong>
                <p>Baseline model score: ${Number(data.current_risk_score).toFixed(3)}
                    (${escapeHtml(data.current_risk_category)})</p>
                <p>Scenario model score: ${Number(data.scenario_risk_score).toFixed(3)}
                    (${escapeHtml(data.scenario_risk_category)})</p>
                <p>Model-score change: ${Number(data.score_change).toFixed(3)}</p>
                <small>${escapeHtml(data.disclaimer)}</small>
            `;
        }
    } catch (error) {
        console.error("Scenario error:", error);
        if (result) {
            result.textContent = "Unable to calculate this scenario. Check that the API is running.";
        }
    }
}


async function downloadPlanningReport() {
    try {
        const response = await fetch(`${API_BASE}/planning-report`);
        if (!response.ok) {
            throw new Error(`Planning report API error: ${response.status}`);
        }

        const report = await response.blob();
        const url = URL.createObjectURL(report);
        const link = document.createElement("a");
        link.href = url;
        link.download = "emergency-access-planning-report.txt";
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) {
        console.error("Planning report error:", error);
        alert("Unable to generate the planning report. Check that the API is running.");
    }
}


// =====================================================
// HOTSPOTS
// =====================================================

async function loadHotspots() {

    try {

        const response =
            await fetch(
                `${API_BASE}/hotspots?limit=5000`
            );


        if (!response.ok) {
            throw new Error(
                `Hotspot API error: ${response.status}`
            );
        }


        const data =
            await response.json();


        console.log(
            "Hotspots API response:",
            data
        );


        // API returns:
        // {
        //     count: 5000,
        //     data: [...]
        // }

        if (Array.isArray(data)) {

            allHotspots = data;

        } else if (
            Array.isArray(data.data)
        ) {

            allHotspots = data.data;

        } else if (
            Array.isArray(data.hotspots)
        ) {

            allHotspots = data.hotspots;

        } else {

            allHotspots = [];
        }


        console.log(
            "Total hotspots:",
            allHotspots.length
        );


        updateView();


    } catch (error) {

        console.error(
            "Hotspot error:",
            error
        );


        const tbody =
            document.getElementById(
                "hotspotTableBody"
            );


        if (tbody) {

            tbody.innerHTML = `
                <tr>
                    <td colspan="6"
                        class="empty-message">
                        Unable to load hotspot data.
                    </td>
                </tr>
            `;
        }
    }
}


// =====================================================
// CORRIDORS
// =====================================================

async function loadCorridors() {

    try {

        const response =
            await fetch(
                `${API_BASE}/corridors`
            );


        if (!response.ok) {
            throw new Error(
                `Corridor API error: ${response.status}`
            );
        }


        const data =
            await response.json();


        console.log(
            "Corridors API response:",
            data
        );


        if (Array.isArray(data)) {

            allCorridors = data;

        } else if (
            Array.isArray(data.data)
        ) {

            allCorridors = data.data;

        } else if (
            Array.isArray(data.corridors)
        ) {

            allCorridors = data.corridors;

        } else {

            allCorridors = [];
        }


        console.log(
            "Total corridors:",
            allCorridors.length
        );


        displayCorridors();

        displayCorridorMap();


    } catch (error) {

        console.error(
            "Corridor error:",
            error
        );


        const container =
            document.getElementById(
                "corridorList"
            );


        if (container) {

            container.innerHTML = `
                <p class="empty-message">
                    Unable to load corridor analysis.
                </p>
            `;
        }
    }
}


// =====================================================
// UPDATE VIEW
// =====================================================

function updateView() {

    if (!allHotspots.length) {
        return;
    }


    const search =
        (
            document.getElementById(
                "searchInput"
            )?.value || ""
        )
        .trim()
        .toLowerCase();


    const filter =
        document.getElementById(
            "riskFilter"
        )?.value || "ALL";


    const filtered =
        allHotspots.filter(item => {

            const area =
                String(
                    item.area_name || ""
                )
                .toLowerCase();


            const category =
                String(
                    item.risk_category ||
                    item.category ||
                    ""
                )
                .toUpperCase();


            const matchesSearch =
                !search ||
                area.includes(search);


            const matchesFilter =
                filter === "ALL" ||
                category === filter;


            return (
                matchesSearch &&
                matchesFilter
            );
        });


    displayMarkers(filtered);

    updateTable(filtered);
}


// =====================================================
// CLEAR HOTSPOT MARKERS
// =====================================================

function clearHotspotMarkers() {

    hotspotMarkers.forEach(
        marker => {

            if (map.hasLayer(marker)) {
                map.removeLayer(marker);
            }

        }
    );


    hotspotMarkers = [];
}


// =====================================================
// MARKERS
// =====================================================

function displayMarkers(data) {

    clearHotspotMarkers();


    const filter =
        document.getElementById(
            "riskFilter"
        )?.value || "ALL";


    const search =
        (
            document.getElementById(
                "searchInput"
            )?.value || ""
        ).trim();


    let mapData = data;


    /*
        Normal dashboard:

        Show:
        Critical
        High
        Medium

        Hide Low until:
        - LOW filter is selected
        - user searches an area
    */

    if (
        filter === "ALL" &&
        search === ""
    ) {

        mapData =
            data.filter(item => {

                const category =
                    String(
                        item.risk_category ||
                        ""
                    ).toUpperCase();


                return (
                    category === "CRITICAL" ||
                    category === "HIGH" ||
                    category === "MEDIUM"
                );
            });
    }


    console.log(
        "Displaying markers:",
        mapData.length
    );


    mapData.forEach(item => {

        const lat =
            Number(item.latitude);

        const lng =
            Number(item.longitude);


        if (
            !Number.isFinite(lat) ||
            !Number.isFinite(lng)
        ) {
            return;
        }


        const category =
            String(
                item.risk_category ||
                "LOW"
            ).toUpperCase();


        const marker =
            L.circleMarker(
                [lat, lng],
                {

                    radius:
                        category === "CRITICAL"
                            ? 10
                            : category === "HIGH"
                                ? 8
                                : category === "MEDIUM"
                                    ? 6
                                    : 5,


                    fillColor:
                        getRiskColor(
                            category
                        ),


                    color:
                        category === "CRITICAL"
                            ? "#7f1d1d"
                            : "#ffffff",


                    weight:
                        category === "CRITICAL"
                            ? 2
                            : 1,


                    fillOpacity:
                        category === "LOW"
                            ? 0.55
                            : 0.9
                }
            );


        marker.bindPopup(
            createPopup(item)
        );


        marker.on(
            "click",
            () => selectLocation(item)
        );


        marker.addTo(map);

        hotspotMarkers.push(marker);
    });
}


// =====================================================
// RISK COLOR
// =====================================================

function getRiskColor(category) {

    if (category === "CRITICAL")
        return "#dc2626";

    if (category === "HIGH")
        return "#ea580c";

    if (category === "MEDIUM")
        return "#eab308";

    if (category === "LOW")
        return "#16a34a";

    return "#64748b";
}


// =====================================================
// POPUP
// =====================================================

function createPopup(item) {

    const area =
        item.area_name ||
        "Unnamed Area";


    const category =
        String(
            item.risk_category ||
            "UNKNOWN"
        ).toUpperCase();


    const score =
        Number(
            item.final_risk_score ?? 0
        ).toFixed(3);


    const distance =
        Number(
            item.nearest_hospital_distance_km ?? 0
        ).toFixed(2);


    return `

        <div class="map-popup">

            <h3>
                ${escapeHtml(area)}
            </h3>

            <p>
                <strong>Junction:</strong>
                ${item.junction_id ?? "-"}
            </p>

            <p>
                <strong>Risk:</strong>

                <span class="risk-badge ${category.toLowerCase()}">
                    ${category}
                </span>
            </p>

            <p>
                <strong>Risk Score:</strong>
                ${score}
            </p>

            <p>
                <strong>Nearest Hospital:</strong>
                ${distance} km
            </p>

            <button
                class="popup-button"
                onclick="window.selectLocationById(${item.junction_id})"
            >
                View Details
            </button>

        </div>

    `;
}


// =====================================================
// SELECT LOCATION
// =====================================================

function selectLocation(item) {
    selectedHotspot = item;
    const simulateButton = document.getElementById("simulateButton");
    if (simulateButton) {
        simulateButton.disabled = false;
    }
    setText(
        "simulationResult",
        `Ready to simulate a scenario for ${item.area_name || `junction ${item.junction_id}`}.`
    );

    const selected =
        document.getElementById(
            "selectedLocation"
        );


    const explanation =
        document.getElementById(
            "riskExplanation"
        );


    const action =
        document.getElementById(
            "recommendedAction"
        );


    const confidence =
        document.getElementById(
            "dataConfidence"
        );


    const area =
        item.area_name ||
        "Unnamed Area";


    const category =
        String(
            item.risk_category ||
            "UNKNOWN"
        ).toUpperCase();


    const score =
        Number(
            item.final_risk_score ?? 0
        ).toFixed(3);


    const priority =
        Number(
            item.priority_score ?? 0
        ).toFixed(3);


    const hospitalRisk =
        Number(
            item.hospital_access_risk ?? 0
        ).toFixed(3);


    const distance =
        Number(
            item.nearest_hospital_distance_km ?? 0
        ).toFixed(2);


    const hospitals =
        Number(
            item.hospitals_within_5km ?? 0
        );


    const areaType =
        item.area_type ||
        "Unknown";


    if (selected) {

        selected.innerHTML = `

            <div class="selected-header">

                <div>

                    <span class="small-label">
                        SELECTED LOCATION
                    </span>

                    <h2>
                        ${escapeHtml(area)}
                    </h2>

                </div>

                <span class="risk-badge large ${category.toLowerCase()}">
                    ${category}
                </span>

            </div>


            <div class="detail-grid">

                <div>
                    <span>Risk Score</span>
                    <strong>${score}</strong>
                </div>

                <div>
                    <span>Priority Score</span>
                    <strong>${priority}</strong>
                </div>

                <div>
                    <span>Hospital Access Risk</span>
                    <strong>${hospitalRisk}</strong>
                </div>

                <div>
                    <span>Nearest Hospital</span>
                    <strong>${distance} km</strong>
                </div>

                <div>
                    <span>Hospitals Within 5 km</span>
                    <strong>${hospitals}</strong>
                </div>

                <div>
                    <span>Area Type</span>
                    <strong>
                        ${escapeHtml(areaType)}
                    </strong>
                </div>

            </div>

        `;
    }


    if (explanation) {

        explanation.innerHTML = `

            <h3>
                Why Is It Risky?
            </h3>

            <p>
                ${escapeHtml(
                    item.risk_explanation ||
                    generateExplanation(item)
                )}
            </p>

        `;
    }


    if (action) {

        action.innerHTML = `

            <h3>
                Recommended Action
            </h3>

            <p>
                ${escapeHtml(
                    item.recommended_action ||
                    generateAction(item)
                )}
            </p>

        `;
    }


    if (confidence) {

        confidence.innerHTML = `

            <strong>Data Confidence:</strong>

            ${escapeHtml(
                item.data_confidence ||
                "Medium"
            )}

            <br>

            <small>
                Based on mapped road and hospital
                data. Operational use requires
                validation with real traffic and
                emergency-response data.
            </small>

        `;
    }
}


// =====================================================
// SEARCH MESSAGE
// =====================================================

function showSearchMessage(message) {

    const selected =
        document.getElementById(
            "selectedLocation"
        );


    const explanation =
        document.getElementById(
            "riskExplanation"
        );


    const action =
        document.getElementById(
            "recommendedAction"
        );


    if (selected) {

        selected.innerHTML = `

            <div class="selected-header">

                <div>

                    <span class="small-label">
                        SEARCH RESULT
                    </span>

                    <h2>
                        No Location Found
                    </h2>

                </div>

            </div>

            <p>
                ${escapeHtml(message)}
            </p>

        `;
    }


    if (explanation) {

        explanation.innerHTML = `

            <h3>
                Search Information
            </h3>

            <p>
                Try another nearby locality,
                neighbourhood or area name.
            </p>

        `;
    }


    if (action) {

        action.innerHTML = `

            <h3>
                What You Can Do
            </h3>

            <p>
                Search using a place name that
                appears in the mapped OpenStreetMap
                place data.
            </p>

        `;
    }
}


// =====================================================
// RESET SELECTED LOCATION
// =====================================================

function resetSelectedLocation() {

    const selected =
        document.getElementById(
            "selectedLocation"
        );


    const explanation =
        document.getElementById(
            "riskExplanation"
        );


    const action =
        document.getElementById(
            "recommendedAction"
        );


    const confidence =
        document.getElementById(
            "dataConfidence"
        );


    if (selected) {

        selected.innerHTML = `

            <div class="selected-header">

                <div>

                    <span class="small-label">
                        SELECTED LOCATION
                    </span>

                    <h2>
                        Select a marker
                    </h2>

                </div>

            </div>

            <p>
                Select a marker on the map to view details.
            </p>

        `;
    }


    if (explanation) {

        explanation.innerHTML = `

            <h3>
                Why Is It Risky?
            </h3>

            <p>
                Select a junction to see the risk explanation.
            </p>

        `;
    }


    if (action) {

        action.innerHTML = `

            <h3>
                Recommended Action
            </h3>

            <p>
                Select a junction to see the recommended action.
            </p>

        `;
    }


    if (confidence) {

        confidence.innerHTML = `

            <strong>
                Data Confidence:
            </strong>

            Select a location to view confidence information.

        `;
    }
}


// =====================================================
// SELECT BY ID
// =====================================================

window.selectLocationById =
function(id) {

    const item =
        allHotspots.find(
            x =>
                String(x.junction_id) ===
                String(id)
        );


    if (!item) {

        console.warn(
            "Junction not found:",
            id
        );

        return;
    }


    selectLocation(item);


    const lat =
        Number(item.latitude);

    const lng =
        Number(item.longitude);


    if (
        Number.isFinite(lat) &&
        Number.isFinite(lng)
    ) {

        map.setView(
            [lat, lng],
            16
        );
    }
};


// =====================================================
// EXPLANATION
// =====================================================

function generateExplanation(item) {

    const hospitalRisk =
        Number(
            item.hospital_access_risk ?? 0
        );


    const priority =
        Number(
            item.priority_score ?? 0
        );


    const distance =
        Number(
            item.nearest_hospital_distance_km ?? 0
        );


    if (hospitalRisk >= 0.7) {

        return `
            High hospital-access risk combined with
            elevated junction priority. The nearest
            mapped hospital is approximately
            ${distance.toFixed(2)} km away.
        `;
    }


    if (priority >= 0.7) {

        return `
            High junction priority indicates that
            this location may require additional
            emergency-access investigation.
        `;
    }


    return `
        The location has moderate junction priority
        and/or hospital-access concerns.
    `;
}


// =====================================================
// ACTION
// =====================================================

function generateAction(item) {

    const category =
        String(
            item.risk_category || ""
        ).toUpperCase();


    if (category === "CRITICAL") {

        return `
            Prioritize this location for detailed
            traffic-flow, road-connectivity and
            emergency-access assessment.
        `;
    }


    if (category === "HIGH") {

        return `
            Investigate emergency accessibility
            and monitor traffic-flow conditions.
        `;
    }


    if (category === "MEDIUM") {

        return `
            Monitor the location and reassess when
            additional traffic or incident data
            becomes available.
        `;
    }


    return `
        Routine monitoring; reassess when additional
        traffic or incident data becomes available.
    `;
}


// =====================================================
// TABLE
// =====================================================

function updateTable(data) {

    const tbody =
        document.getElementById(
            "hotspotTableBody"
        );


    if (!tbody) {
        return;
    }


    const rows =
        [...data]
            .sort(
                (a, b) =>
                    Number(
                        a.final_risk_rank ??
                        999999
                    )
                    -
                    Number(
                        b.final_risk_rank ??
                        999999
                    )
            )
            .slice(0, 50);


    if (!rows.length) {

        tbody.innerHTML = `

            <tr>

                <td
                    colspan="6"
                    class="empty-message"
                >
                    No matching locations found.
                </td>

            </tr>

        `;

        return;
    }


    tbody.innerHTML =
        rows.map(item => {

            const category =
                String(
                    item.risk_category ||
                    "LOW"
                ).toUpperCase();


            const access =
                Number(
                    item.hospital_access_risk ?? 0
                );


            const distance =
                Number(
                    item.nearest_hospital_distance_km ?? 0
                );


            return `

                <tr>

                    <td>
                        ${item.final_risk_rank ?? "-"}
                    </td>

                    <td>

                        <strong>
                            ${escapeHtml(
                                item.area_name ||
                                "Unnamed Area"
                            )}
                        </strong>

                    </td>

                    <td>

                        <span
                            class="risk-badge ${category.toLowerCase()}"
                        >
                            ${category}
                        </span>

                    </td>

                    <td>

                        <div class="access-cell">

                            <strong>
                                ${access.toFixed(3)}
                            </strong>

                            <small>
                                ${getAccessLabel(access)}
                            </small>

                        </div>

                    </td>

                    <td>
                        ${distance.toFixed(2)} km
                    </td>

                    <td>

                        <button
                            class="table-button"
                            onclick="window.selectLocationById(${item.junction_id})"
                        >
                            View
                        </button>

                    </td>

                </tr>

            `;

        }).join("");
}


// =====================================================
// HOSPITAL ACCESS LABEL
// =====================================================

function getAccessLabel(score) {

    if (score >= 0.7)
        return "Very High";

    if (score >= 0.3)
        return "Moderate";

    if (score >= 0.1)
        return "Low";

    return "Very Low";
}


// =====================================================
// CORRIDORS
// =====================================================

function displayCorridors() {

    const container =
        document.getElementById(
            "corridorList"
        );


    if (!container) {
        return;
    }


    if (!allCorridors.length) {

        container.innerHTML = `

            <p class="empty-message">
                No corridor candidates identified.
            </p>

        `;

        return;
    }


    container.innerHTML =
        allCorridors.map(
            (corridor, index) => {

                const priority =
                    Number(
                        corridor.corridor_priority ??
                        corridor.priority ??
                        0
                    );


                return `

                    <div class="corridor-card">

                        <div class="corridor-header">

                            <div>

                                <span class="small-label">
                                    CORRIDOR CANDIDATE
                                </span>

                                <h3>
                                    🚨 Corridor ${index + 1}
                                </h3>

                            </div>

                            <strong>
                                Priority:
                                ${priority.toFixed(3)}
                            </strong>

                        </div>


                        <div class="corridor-stats">

                            <div>

                                <span>
                                    Junctions
                                </span>

                                <strong>
                                    ${
                                        corridor.junction_count ??
                                        corridor.junctions ??
                                        "-"
                                    }
                                </strong>

                            </div>


                            <div>

                                <span>
                                    Critical
                                </span>

                                <strong>
                                    ${
                                        corridor.critical_count ??
                                        corridor.critical ??
                                        "-"
                                    }
                                </strong>

                            </div>


                            <div>

                                <span>
                                    High
                                </span>

                                <strong>
                                    ${
                                        corridor.high_count ??
                                        corridor.high ??
                                        "-"
                                    }
                                </strong>

                            </div>

                        </div>


                        <div class="corridor-areas">

                            <strong>
                                Areas:
                            </strong>

                            ${
                                escapeHtml(
                                    corridor.areas ||
                                    corridor.area_names ||
                                    "Multiple nearby areas"
                                )
                            }

                        </div>


                        <p class="corridor-note">

                            Nearby Critical/High junctions
                            grouped for corridor-level
                            investigation.

                        </p>

                    </div>

                `;

            }
        ).join("");
}


// =====================================================
// CORRIDOR MAP
// =====================================================

function displayCorridorMap() {

    corridorLayers.forEach(
        layer => {

            if (map.hasLayer(layer)) {
                map.removeLayer(layer);
            }

        }
    );


    corridorLayers = [];


    allCorridors.forEach(corridor => {

        const lat =
            Number(
                corridor.centroid_latitude ??
                corridor.latitude ??
                corridor.lat
            );


        const lng =
            Number(
                corridor.centroid_longitude ??
                corridor.longitude ??
                corridor.lng ??
                corridor.lon
            );


        if (
            !Number.isFinite(lat) ||
            !Number.isFinite(lng)
        ) {
            return;
        }


        const marker =
            L.circleMarker(
                [lat, lng],
                {
                    radius: 12,
                    color: "#7c3aed",
                    weight: 3,
                    fillColor: "#a855f7",
                    fillOpacity: 0.35
                }
            );


        marker.bindPopup(`

            <div class="map-popup">

                <h3>
                    🚨 Corridor Candidate
                </h3>

                <p>

                    <strong>
                        Priority:
                    </strong>

                    ${
                        Number(
                            corridor.corridor_priority ??
                            0
                        ).toFixed(3)
                    }

                </p>

                <p>

                    <strong>
                        Junctions:
                    </strong>

                    ${
                        corridor.junction_count ??
                        corridor.junctions ??
                        "-"
                    }

                </p>

            </div>

        `);


        marker.addTo(map);

        corridorLayers.push(marker);
    });
}


// =====================================================
// HELPERS
// =====================================================

function setText(id, value) {

    const element =
        document.getElementById(id);


    if (element) {
        element.textContent = value;
    }
}


function escapeHtml(value) {

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}