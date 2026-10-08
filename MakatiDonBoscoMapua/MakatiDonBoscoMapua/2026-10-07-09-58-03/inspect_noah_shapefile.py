import os
from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt

# Determine script folder directory (works regardless of execution path)
BASE_DIR = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()

# Search recursively for the specific shapefile in BASE_DIR or any subfolder
TARGET_FILENAME = "ph137602000_fh5yr_10m.shp"
shapefile_matches = list(BASE_DIR.rglob(TARGET_FILENAME))

if shapefile_matches:
    SHAPEFILE_PATH = shapefile_matches[0]
else:
    # Fallback: search for any available .shp file in the directory tree
    any_shp = list(BASE_DIR.rglob("*.shp"))
    if any_shp:
        SHAPEFILE_PATH = any_shp[0]
    else:
        raise FileNotFoundError(f"Could not find '{TARGET_FILENAME}' or any .shp file within {BASE_DIR}")

print(f"Loading shapefile from: {SHAPEFILE_PATH}")
gdf = gpd.read_file(SHAPEFILE_PATH)

print("\n==========================================")
print("   UP NOAH 5-YEAR FLOOD HAZARD METADATA   ")
print("==========================================")
print(f"CRS (Coordinate System): {gdf.crs}")
print(f"Total Flood Polygons: {len(gdf)}")

print("\n--- Available Data Attributes (Columns) ---")
print(gdf.columns.tolist())

# Detect hazard level column (e.g., 'Var', 'HAZARD', 'gridcode', 'Leg')
hazard_col = next(
    (
        col
        for col in ["Var", "HAZARD", "gridcode", "Leg", "DN"]
        if col in gdf.columns
    ),
    gdf.columns[0],
)

print(f"\n--- Distribution of Flood Hazard Levels (Column: '{hazard_col}') ---")
print(gdf[hazard_col].value_counts())

# Generate Flood Hazard Map
fig, ax = plt.subplots(figsize=(10, 8))
gdf.plot(
    ax=ax,
    column=hazard_col,
    legend=True,
    cmap="YlOrRd",  # Yellow (Low) -> Orange (Medium) -> Red (High)
    edgecolor="black",
    linewidth=0.1,
)

plt.title(
    "UP Project NOAH 5-Year Flood Hazard Map - City of Makati",
    fontsize=12,
    pad=15,
)
plt.xlabel("Longitude (WGS84)")
plt.ylabel("Latitude (WGS84)")
plt.grid(True, linestyle="--", alpha=0.5)

# Save figure into the script's directory
output_image = BASE_DIR / "up_noah_makati_5yr_map.png"
plt.savefig(output_image, dpi=300)
print(f"\nPlot saved as '{output_image}'.")
plt.show()
