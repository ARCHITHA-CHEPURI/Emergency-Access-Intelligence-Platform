import os
import json
import math

import osmium
import networkx as nx

from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.prepared import prep


# ============================================================
# FILE PATHS
# ============================================================

PBF_FILE = r"data\raw\telangana-latest.osm.pbf"
BOUNDARY_FILE = r"data\boundaries\ghmc_boundary.json"
OUTPUT_GRAPH = r"data\processed\ghmc_osm_graph.graphml"


# ============================================================
# ROAD TYPES
# ============================================================

ROAD_TYPES = {
    "motorway",
    "motorway_link",

    "trunk",
    "trunk_link",

    "primary",
    "primary_link",

    "secondary",
    "secondary_link",

    "tertiary",
    "tertiary_link",

    "unclassified",
    "residential",
    "living_street",
    "road",

    # Keep service roads for now because they can provide
    # access to important locations.
    "service",
}


# ============================================================
# LOAD GHMC BOUNDARY
# ============================================================

print("Loading GHMC boundary...")

with open(BOUNDARY_FILE, "r", encoding="utf-8") as f:
    boundary_data = json.load(f)

feature = boundary_data["features"][0]

rings = feature["geometry"]["rings"]

polygons = []

for ring in rings:

    if len(ring) >= 4:
        polygon = Polygon(ring)

        if not polygon.is_empty:
            polygons.append(polygon)


if len(polygons) == 1:

    boundary = polygons[0]

else:

    boundary = MultiPolygon(polygons)


print("Boundary:", boundary.geom_type)
print("Valid:", boundary.is_valid)
print("Bounds:", boundary.bounds)


# Prepare boundary for faster spatial tests
boundary_prepared = prep(boundary)


# ============================================================
# GRAPH
# ============================================================

# MultiDiGraph allows multiple OSM ways between the same
# pair of nodes.
G = nx.MultiDiGraph()


# ============================================================
# STATISTICS
# ============================================================

ways_seen = 0
road_ways = 0
ways_in_ghmc = 0

nodes_added = 0
edges_added = 0

invalid_location_ways = 0
short_ways = 0


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def haversine(lon1, lat1, lon2, lat2):

    R = 6371000.0

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


# ============================================================
# OSMIUM HANDLER
# ============================================================

class GHMCHandler(osmium.SimpleHandler):

    def way(self, w):

        global ways_seen
        global road_ways
        global ways_in_ghmc

        global nodes_added
        global edges_added

        global invalid_location_ways
        global short_ways

        ways_seen += 1

        # ----------------------------------------------------
        # Check highway type
        # ----------------------------------------------------

        highway = w.tags.get("highway")

        if highway not in ROAD_TYPES:
            return

        road_ways += 1

        # ----------------------------------------------------
        # A valid road way needs at least two nodes
        # ----------------------------------------------------

        if len(w.nodes) < 2:

            short_ways += 1
            return

        # ----------------------------------------------------
        # Get coordinates of OSM nodes
        # ----------------------------------------------------

        coords = []

        for node in w.nodes:

            try:

                lon = node.lon
                lat = node.lat

            except osmium.InvalidLocationError:

                invalid_location_ways += 1

                # Skip this way instead of crashing the
                # entire extraction.
                return

            coords.append(
                (float(lon), float(lat))
            )


        # ----------------------------------------------------
        # Check whether the way touches GHMC
        # ----------------------------------------------------

        inside = False

        for lon, lat in coords:

            point = Point(lon, lat)

            if boundary_prepared.covers(point):

                inside = True
                break


        if not inside:
            return


        ways_in_ghmc += 1


        # ----------------------------------------------------
        # Road attributes
        # ----------------------------------------------------

        name = w.tags.get("name", "")

        # Useful OSM attributes for later analysis
        oneway = w.tags.get("oneway", "no")

        bridge = w.tags.get("bridge", "no")

        tunnel = w.tags.get("tunnel", "no")

        maxspeed = w.tags.get("maxspeed", "")


        # ----------------------------------------------------
        # Add nodes and edges
        # ----------------------------------------------------

        for i in range(len(w.nodes) - 1):

            node1 = w.nodes[i]
            node2 = w.nodes[i + 1]

            lon1, lat1 = coords[i]
            lon2, lat2 = coords[i + 1]


            point1 = Point(lon1, lat1)
            point2 = Point(lon2, lat2)


            # ------------------------------------------------
            # Keep only segments whose endpoints are inside
            # GHMC.
            # ------------------------------------------------

            if not boundary_prepared.covers(point1):

                continue

            if not boundary_prepared.covers(point2):

                continue


            u = int(node1.ref)
            v = int(node2.ref)


            # ------------------------------------------------
            # Add OSM nodes
            # ------------------------------------------------

            if u not in G:

                G.add_node(
                    u,
                    x=lon1,
                    y=lat1
                )

                nodes_added += 1


            if v not in G:

                G.add_node(
                    v,
                    x=lon2,
                    y=lat2
                )

                nodes_added += 1


            # ------------------------------------------------
            # Calculate segment length
            # ------------------------------------------------

            length_m = haversine(
                lon1,
                lat1,
                lon2,
                lat2
            )


            # ------------------------------------------------
            # Determine direction
            # ------------------------------------------------

            # OSM:
            # oneway=yes / 1 / true
            # means traffic follows the way direction.
            #
            # Otherwise we initially allow both directions.

            is_oneway = str(oneway).lower() in {
                "yes",
                "1",
                "true"
            }


            # ------------------------------------------------
            # Common edge attributes
            # ------------------------------------------------

            attributes = {
                "osm_way_id": int(w.id),
                "highway": highway,
                "name": name,
                "length_m": float(length_m),
                "oneway": str(oneway),
                "bridge": str(bridge),
                "tunnel": str(tunnel),
                "maxspeed": str(maxspeed)
            }


            # ------------------------------------------------
            # Add forward edge
            # ------------------------------------------------

            G.add_edge(
                u,
                v,
                **attributes
            )

            edges_added += 1


            # ------------------------------------------------
            # Add reverse edge if not one-way
            # ------------------------------------------------

            if not is_oneway:

                G.add_edge(
                    v,
                    u,
                    **attributes
                )

                edges_added += 1


# ============================================================
# READ PBF
# ============================================================

print()
print("Reading OSM PBF...")

print(
    "This may take a while because Telangana contains "
    "millions of OSM elements."
)

print()


handler = GHMCHandler()


try:

    handler.apply_file(
        PBF_FILE,
        locations=True
    )

except Exception as e:

    print()
    print("ERROR while reading OSM PBF:")
    print(type(e).__name__)
    print(str(e))

    raise


# ============================================================
# REMOVE ISOLATED NODES
# ============================================================

print()
print("Removing isolated nodes...")

isolated_nodes = list(
    nx.isolates(G)
)

print(
    "Isolated nodes:",
    len(isolated_nodes)
)

if isolated_nodes:

    G.remove_nodes_from(
        isolated_nodes
    )


# ============================================================
# GRAPH STATISTICS
# ============================================================

print()
print("==========================================")
print("          NETWORK EXTRACTION RESULT")
print("==========================================")

print(
    "Ways inspected:",
    ways_seen
)

print(
    "Road ways:",
    road_ways
)

print(
    "Road ways entering GHMC:",
    ways_in_ghmc
)

print(
    "Ways with invalid locations:",
    invalid_location_ways
)

print(
    "Ways with fewer than 2 nodes:",
    short_ways
)

print(
    "Nodes:",
    G.number_of_nodes()
)

print(
    "Edges:",
    G.number_of_edges()
)

print(
    "Weakly connected components:",
    nx.number_weakly_connected_components(G)
)


# ============================================================
# LARGEST COMPONENT
# ============================================================

if G.number_of_nodes() > 0:

    components = list(
        nx.weakly_connected_components(G)
    )

    largest_component = max(
        components,
        key=len
    )

    print(
        "Largest component nodes:",
        len(largest_component)
    )


# ============================================================
# SAVE GRAPH
# ============================================================

print()
print("Saving graph...")

os.makedirs(
    os.path.dirname(OUTPUT_GRAPH),
    exist_ok=True
)


nx.write_graphml(
    G,
    OUTPUT_GRAPH
)


print()
print("Saved:")
print(OUTPUT_GRAPH)

print()
print("DONE.")