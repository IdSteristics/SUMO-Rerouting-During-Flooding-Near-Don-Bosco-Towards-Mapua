import os
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import pandas as pd


def parse_tripinfo(file_path):
  """Parses SUMO tripinfo XML file to extract travel metrics."""
  if not os.path.exists(file_path):
    raise FileNotFoundError(f"Missing required output file: {file_path}")

  tree = ET.parse(file_path)
  root = tree.getroot()

  delays = []
  durations = []
  v_types = []

  for trip in root.findall("tripinfo"):
    delays.append(float(trip.get("timeLoss")))
    durations.append(float(trip.get("duration")))
    v_types.append(trip.get("vType"))

  return pd.DataFrame(
      {"vType": v_types, "delay": delays, "duration": durations}
  )


def run_analysis():
  script_dir = os.path.dirname(os.path.abspath(__file__))

  dry_path = os.path.join(script_dir, "tripinfo_DRY.xml")
  mod_path = os.path.join(script_dir, "tripinfo_MODERATE.xml")
  heavy_path = os.path.join(script_dir, "tripinfo_HEAVY.xml")

  df_dry = parse_tripinfo(dry_path)
  df_mod = parse_tripinfo(mod_path)
  df_heavy = parse_tripinfo(heavy_path)

  summary = pd.DataFrame(
      {
          "Dry (Baseline)": [
              df_dry["delay"].mean(),
              df_dry["duration"].mean(),
          ],
          "Moderate Rain (5 mm/hr)": [
              df_mod["delay"].mean(),
              df_mod["duration"].mean(),
          ],
          "Heavy Rain + NOAH Flood Detour": [
              df_heavy["delay"].mean(),
              df_heavy["duration"].mean(),
          ],
      },
      index=["Avg Delay (sec/veh)", "Avg Total Travel Time (sec)"],
  )

  print("\n=======================================================")
  print("   UP NOAH & ERA5 TRAFFIC PERFORMANCE SUMMARY (KPIs)   ")
  print("=======================================================")
  print(summary.round(2))

  csv_out = os.path.join(script_dir, "simulation_results_summary.csv")
  summary.to_csv(csv_out)
  print(f"\nSaved KPI summary table to: {csv_out}")

  # Single clean plot window
  fig, ax = plt.subplots(figsize=(9.5, 5.5))
  summary.T.plot(kind="bar", ax=ax, width=0.7)

  ax.set_title(
      "Vehicle Delay & Travel Time Under ERA5 Rainfall & UP NOAH Flood"
      " Hazards",
      fontsize=11,
      pad=15,
  )
  ax.set_ylabel("Time (Seconds)", fontsize=10)
  ax.set_xlabel("Simulated Weather & Inundation Condition", fontsize=10)
  ax.set_xticklabels(summary.columns, rotation=0)
  ax.grid(axis="y", linestyle="--", alpha=0.7)

  # Annotate value labels on top of bars
  for p in ax.patches:
    if p.get_height() > 0:
      ax.annotate(
          f"{p.get_height():.1f}s",
          (p.get_x() + p.get_width() / 2.0, p.get_height()),
          ha="center",
          va="center",
          xytext=(0, 5),
          textcoords="offset points",
          fontsize=9,
      )

  plt.tight_layout()
  chart_out = os.path.join(script_dir, "kpi_weather_comparison.png")
  plt.savefig(chart_out, dpi=300)
  print(f"Saved single KPI comparison figure to: {chart_out}")

  plt.show()


if __name__ == "__main__":
  run_analysis()
