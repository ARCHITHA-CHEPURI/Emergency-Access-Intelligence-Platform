import osmium
from collections import Counter


PBF_FILE = "data/raw/telangana-latest.osm.pbf"


class OSMRoadTest(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()

        self.nodes = 0
        self.ways = 0
        self.road_ways = 0
        self.named_roads = 0

        self.highway_types = Counter()

    def node(self, n):
        self.nodes += 1

    def way(self, w):
        self.ways += 1

        highway = w.tags.get("highway")

        if highway:
            self.road_ways += 1
            self.highway_types[highway] += 1

            if w.tags.get("name"):
                self.named_roads += 1


print("Reading:", PBF_FILE)

handler = OSMRoadTest()
handler.apply_file(PBF_FILE, locations=False)

print()
print("========== OSM TEST ==========")
print("Nodes:", handler.nodes)
print("Ways:", handler.ways)
print("Road ways:", handler.road_ways)
print("Named road ways:", handler.named_roads)

print()
print("Highway types:")

for highway, count in handler.highway_types.most_common():
    print(f"{highway:20} {count}")

print()
print("TEST COMPLETE")