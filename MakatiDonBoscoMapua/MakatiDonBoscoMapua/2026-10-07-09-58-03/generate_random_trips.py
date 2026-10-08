import json
import os
import random
import sys
import xml.etree.ElementTree as ET

# Import sumolib
if "SUMO_HOME" in os.environ:
  sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
for path in [
    r"C:\Program Files (x86)\Eclipse\Sumo\tools",
    r"C:\Program Files\Eclipse\Sumo\tools",
    r"C:\sumo\tools",
]:
  if os.path.exists(path) and path not in sys.path:
    sys.path.append(path)

import sumolib

NET_FILE = "osm.net.xml.gz"
HAZARD_JSON = "sumo_edge_flood_hazards.json"
MAPUA_DESTINATION = "755483232"
OUTPUT_ROU = "mapua_makati.rou.xml"

print(f"Reading SUMO network: {NET_FILE}...")
net = sumolib.net.readNet(NET_FILE)

flood_hazards = {}
if os.path.exists(HAZARD_JSON):
  with open(HAZARD_JSON, "r") as f:
    flood_hazards = json.load(f)

mapua_edge = net.getEdge(MAPUA_DESTINATION)

print("Scanning network edges for topological reachability to Mapúa...")
valid_origins = []

for edge in net.getEdges():
  eid = edge.getID()
  if (
      not eid.startswith(":")
      and edge.allows("passenger")
      and edge.getLength() > 20.0
      and eid != MAPUA_DESTINATION
  ):
    hazard = flood_hazards.get(eid, "NONE")
    if hazard not in ["ORANGE_MEDIUM", "RED_HIGH"]:
      path, cost = net.getShortestPath(edge, mapua_edge)
      if path is not None:
        valid_origins.append(eid)

print(
    f"Identified {len(valid_origins)} verified reachable dry/low-hazard origin"
    " edges."
)

num_origins = min(20, len(valid_origins))
sampled_origins = random.sample(valid_origins, num_origins)

routes_xml = ET.Element("routes")

# Vehicle Type Definitions (Yellow Sedans & Orange SUVs Only)
ET.SubElement(
    routes_xml,
    "vType",
    attrib={
        "id": "sedan",
        "accel": "2.6",
        "decel": "4.5",
        "length": "4.5",
        "maxSpeed": "13.89",
        "vClass": "passenger",
        "color": "yellow",
    },
)
ET.SubElement(
    routes_xml,
    "vType",
    attrib={
        "id": "suv",
        "accel": "2.2",
        "decel": "4.0",
        "length": "5.0",
        "maxSpeed": "13.89",
        "vClass": "passenger",
        "color": "orange",
    },
)

# Vehicle Classes: Sedans and SUVs
vtypes = ["sedan", "suv"]
flow_counter = 1

for origin_edge in sampled_origins:
  vtype = random.choice(vtypes)
  rate = random.randint(30, 80)  # Flow rate in vehicles per hour

  ET.SubElement(
      routes_xml,
      "flow",
      attrib={
          "id": f"flow_rand_{flow_counter}",
          "type": vtype,
          "begin": "0",
          "end": "3600",
          "vehsPerHour": str(rate),
          "from": origin_edge,
          "to": MAPUA_DESTINATION,
      },
  )
  flow_counter += 1

tree = ET.ElementTree(routes_xml)
ET.indent(tree, space="    ")
tree.write(OUTPUT_ROU, encoding="utf-8", xml_declaration=True)

print(
    f"\nSUCCESS: Generated '{OUTPUT_ROU}' with {flow_counter - 1} randomized"
    f" origin flows (Sedans & SUVs only) targeting Mapúa ({MAPUA_DESTINATION})!"
)
