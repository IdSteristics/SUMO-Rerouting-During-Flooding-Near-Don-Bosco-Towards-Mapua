import json
import os
import sys
from pathlib import Path
import geopandas as gpd
from shapely.geometry import LineString

# Base directory relative to where the script is saved
BASE_DIR = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()

# 1. Locate and Import SUMO's sumolib
if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
for path in [
    r"C:\Program Files (x86)\Eclipse\Sumo\tools",
    r"C:\Program Files\Eclipse\Sumo\tools",
    r"C:\sumo\tools",
]:
    if os.path.exists(path) and path not in sys.path:
        sys.path.append(path)

try:
    import sumolib
except ImportError:
    raise ImportError(
        "Could not import sumolib. Ensure SUMO is installed on your system or SUMO_HOME is set."
    )

# 2. Dynamic File Search for SUMO Network (.net.xml.gz or .net.xml)
TARGET_NETFILE = "osm.net.xml.gz"
net_matches = list(BASE_DIR.rglob(TARGET_NETFILE))

if net_matches:
    NET_FILE_PATH = net_matches[0]
else:
    # Fallback to any SUMO network file in the directory hierarchy
    all_nets = list(BASE_DIR.rglob("*.net.xml.gz")) + list(BASE_DIR.rglob("*.net.xml"))
    if all_nets:
        NET_FILE_PATH = all_nets[0]
    else:
        raise FileNotFoundError(
            f"Could not find '{TARGET_NETFILE}' or any .net.xml / .net.xml.gz file within {BASE_DIR}"
        )

# 3. Dynamic File Search for UP NOAH Shapefile (.shp)
TARGET_SHAPEFILE = "ph137602000_fh5yr_10m.shp"
shp_matches = list(BASE_DIR.rglob(TARGET_SHAPEFILE))

if shp_matches:
    SHAPEFILE_PATH = shp_matches[0]
else:
    # Fallback to any shapefile in the directory hierarchy
    all_shps = list(BASE_DIR.rglob("*.shp"))
    if all_shps:
        SHAPEFILE_PATH = all_shps[0]
    else:
        raise FileNotFoundError(
            f"Could not find '{TARGET_SHAPEFILE}' or any .shp file within {BASE_DIR}"
        )

print(f"Reading SUMO network file from: {NET_FILE_PATH}")
net = sumolib.net.readNet(str(NET_FILE_PATH))

# 4. Retrieve SUMO Location Net Offset (UTM Zone 51N)
offset_x, offset_y = net.getLocationOffset()
print(f"SUMO Net Offset: X = {offset_x}, Y = {offset_y}")

edge_data = []
for edge in net.getEdges():
    edge_id = edge.getID()
    if not edge_id.startswith(":"):  # Exclude internal junction edges
        # Convert local SUMO meters to global UTM Zone 51N meters
        utm_shape = [(x - offset_x, y - offset_y) for x, y in edge.getShape()]
        if len(utm_shape) >= 2:
            edge_data.append({"edge_id": edge_id, "geometry": LineString(utm_shape)})

# Build GeoDataFrame in native UTM Zone 51N (EPSG:32651)
edges_gdf = gpd.GeoDataFrame(edge_data, crs="EPSG:32651")

# 5. Load UP NOAH Shapefile
print(f"Loading UP NOAH Shapefile from: {SHAPEFILE_PATH}")
noah_gdf = gpd.read_file(SHAPEFILE_PATH)

if noah_gdf.crs != "EPSG:32651":
    print("Reprojecting NOAH Shapefile to EPSG:32651 (UTM Zone 51N)...")
    noah_gdf = noah_gdf.to_crs("EPSG:32651")

# Auto-detect hazard attribute column
hazard_col = next(
    (
        col
        for col in ["gridcode", "HAZARD", "Var", "DN", "Leg"]
        if col in noah_gdf.columns
    ),
    noah_gdf.columns[0],
)
print(f"Using hazard attribute column: '{hazard_col}'")

# 6. Spatial Intersect (SUMO Edges <-> NOAH Flood Polygons)
print("Performing Spatial Intersect in UTM Zone 51N meters...")
joined = gpd.sjoin(edges_gdf, noah_gdf, how="inner", predicate="intersects")

# Map hazard levels
HAZARD_LABEL_MAP = {
    1: "YELLOW_LOW",
    2: "ORANGE_MEDIUM",
    3: "RED_HIGH",
    "1": "YELLOW_LOW",
    "2": "ORANGE_MEDIUM",
    "3": "RED_HIGH",
    "Low": "YELLOW_LOW",
    "Medium": "ORANGE_MEDIUM",
    "High": "RED_HIGH",
    "LOW": "YELLOW_LOW",
    "MEDIUM": "ORANGE_MEDIUM",
    "HIGH": "RED_HIGH",
}

edge_hazard_registry = {}
for _, row in joined.iterrows():
    eid = row["edge_id"]
    h_val = row[hazard_col]
    h_label = HAZARD_LABEL_MAP.get(h_val, "YELLOW_LOW")

    # Retain highest severity if edge intersects multiple hazard polygons
    if eid not in edge_hazard_registry or h_label in [
        "ORANGE_MEDIUM",
        "RED_HIGH",
    ]:
        edge_hazard_registry[eid] = h_label

# Save Output JSON directly to script directory
out_json = BASE_DIR / "sumo_edge_flood_hazards.json"
with open(out_json, "w") as f:
    json.dump(edge_hazard_registry, f, indent=2)

print("\n==========================================")
print(
    f"SUCCESS: Mapped {len(edge_hazard_registry)} flooded edges from UP NOAH!"
)
print(f"Saved hazard mapping registry to: {out_json}")
print("==========================================")
