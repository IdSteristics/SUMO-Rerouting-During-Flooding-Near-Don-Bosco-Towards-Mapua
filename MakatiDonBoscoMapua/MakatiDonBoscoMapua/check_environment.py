import os
import subprocess
import sys
from pathlib import Path

# Base directory relative to where the script is saved
BASE_DIR = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()

# 1. Auto-detect SUMO tools
if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
for path in [
    r"C:\Program Files (x86)\Eclipse\Sumo\tools",
    r"C:\Program Files\Eclipse\Sumo\tools",
    r"C:\sumo\tools",
]:
    if os.path.exists(path) and path not in sys.path:
        sys.path.append(path)


def run_check():
    print("==================================================")
    print("      SUMO-NOAH LOCAL ENVIRONMENT CHECKER         ")
    print("==================================================")
    print(f"Directory: {BASE_DIR}")

    # 1. Complete list of all Python imports across project scripts
    libraries = [
        ("geopandas", "GeoPandas"),
        ("shapely", "Shapely"),
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),  # Fixed: Imported in Process_ERA5.py
        ("matplotlib", "Matplotlib"),
        ("traci", "TraCI"),
        ("sumolib", "Sumolib"),
        ("xarray", "Xarray"),
        ("netCDF4", "NetCDF4 (xarray engine)"),  # Fixed: Required for xarray .nc support
    ]

    print("\n--- 1. Python Libraries ---")
    for mod, name in libraries:
        try:
            __import__(mod)
            print(f" [PASS]    {name:<25} -> Installed")
        except ImportError:
            print(f" [MISSING] {name:<25} -> Auto-installing...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", mod],
                    stdout=subprocess.DEVNULL,
                )
                print(f" [SUCCESS] {name:<25} -> Installed successfully")
            except subprocess.CalledProcessError:
                print(f" [FAILED]  {name:<25} -> Pip install failed")

    # 2. Project Input Files Check
    files = [
        "osm.net.xml.gz",
        "mapua_makati.sumocfg",
        "mapua_makati.rou.xml",
        "ph137602000_fh5yr_10m.shp",
        "era5_2012_2017_makati_single.nc",
    ]
    print("\n--- 2. Required Input Files ---")
    for filename in files:
        matches = list(BASE_DIR.rglob(filename))
        if not matches and filename.endswith(".nc"):
            matches = list(BASE_DIR.rglob("era5_2012_2017_makati_single*"))

        if matches:
            rel_path = matches[0].relative_to(BASE_DIR)
            print(f" [FOUND]   {filename:<32} -> (located at: ./{rel_path})")
        else:
            print(f" [MISSING] {filename:<32} -> Not found in directory tree")

    print("\nEnvironment check complete!")


if __name__ == "__main__":
    run_check()
