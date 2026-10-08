import json
import os
import traci

DON_BOSCO_EDGE = "762046241#1"
AMORSOLO_EDGE = "-22648376#1"
OSMENA_EDGE = "242803598#1"
HAZARD_JSON = "sumo_edge_flood_hazards.json"


def load_flood_hazards():
  if os.path.exists(HAZARD_JSON):
    with open(HAZARD_JSON, "r") as f:
      return json.load(f)
  return {}


def draw_visual_floods(flood_registry, scenario_name):
  """Draws scenario-differentiated water overlays along flood-affected road edges."""
  for edge_id, hazard in flood_registry.items():
    try:
      shape = traci.lane.getShape(f"{edge_id}_0")
      if len(shape) >= 2:
        poly_id = f"flood_poly_{edge_id}"

        if scenario_name == "MODERATE":
          # Faint, narrow, highly translucent puddles for moderate rain (5 mm/hr)
          if hazard in ["YELLOW_LOW", "ORANGE_MEDIUM"]:
            color = (160, 215, 255, 70)  # Very light translucent blue
            width = 2.0
          else:
            continue

        elif scenario_name == "HEAVY":
          # Deep, wide, dark blue inundation overlays for heavy typhoon rain (28.5 mm/hr)
          if hazard in ["ORANGE_MEDIUM", "RED_HIGH"]:
            color = (0, 70, 220, 200)  # Dark solid blue
            width = 5.0
          elif hazard == "YELLOW_LOW":
            color = (80, 160, 240, 130)  # Medium blue
            width = 3.5
          else:
            continue

        traci.polygon.add(
            polygonID=poly_id,
            shape=shape,
            color=color,
            fill=True,
            layer=100,
            lineWidth=width,
        )
    except Exception:
      pass


def run_scenario(scenario_name="DRY", era5_mm_hr=0.0):
  flood_registry = load_flood_hazards()

  print(f"\n==========================================")
  print(f"Running Scenario: {scenario_name} (ERA5 Rainfall: {era5_mm_hr} mm/hr)")
  print(f"==========================================")

  sumo_cmd = [
      "sumo-gui",
      "-c",
      "mapua_makati.sumocfg",
      "--tripinfo-output",
      f"tripinfo_{scenario_name}.xml",
  ]
  traci.start(sumo_cmd)

  # Physical speed limits & scenario-specific visual water rendering
  if scenario_name == "MODERATE":
    for edge_id, hazard in flood_registry.items():
      if hazard in ["YELLOW_LOW", "ORANGE_MEDIUM"]:
        traci.edge.setMaxSpeed(edge_id, 8.33)  # 30 km/h
    draw_visual_floods(flood_registry, scenario_name="MODERATE")

  elif scenario_name == "HEAVY":
    for edge_id, hazard in flood_registry.items():
      if hazard in ["ORANGE_MEDIUM", "RED_HIGH"]:
        traci.edge.setMaxSpeed(edge_id, 0.5)  # Crawl speed (1.8 km/h)
      elif hazard == "YELLOW_LOW":
        traci.edge.setMaxSpeed(edge_id, 8.33)  # 30 km/h
    draw_visual_floods(flood_registry, scenario_name="HEAVY")

  # Main simulation step loop
  while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    departed_vehs = traci.simulation.getDepartedIDList()

    if scenario_name == "MODERATE":
      for veh_id in departed_vehs:
        traci.vehicle.setSpeedFactor(veh_id, 0.82)

    elif scenario_name == "HEAVY":
      for veh_id in departed_vehs:
        traci.vehicle.setSpeedFactor(veh_id, 0.55)

      # Dynamic sedan rerouting around Don Bosco flood bottleneck
      for veh_id in traci.vehicle.getIDList():
        if traci.vehicle.getTypeID(veh_id) == "sedan":
          current_road = traci.vehicle.getRoadID(veh_id)

          if current_road == DON_BOSCO_EDGE or current_road.startswith(
              "762046241"
          ):
            amorsolo_occ = traci.edge.getLastStepOccupancy(AMORSOLO_EDGE)
            osmena_occ = traci.edge.getLastStepOccupancy(OSMENA_EDGE)

            if amorsolo_occ < osmena_occ:
              traci.vehicle.setVia(veh_id, [AMORSOLO_EDGE])
            else:
              traci.vehicle.setVia(veh_id, [OSMENA_EDGE])

            traci.vehicle.rerouteTraveltime(veh_id)

  traci.close()
  print(f"Finished {scenario_name}. Output: tripinfo_{scenario_name}.xml")


if __name__ == "__main__":
  run_scenario("DRY", era5_mm_hr=0.0)
  run_scenario("MODERATE", era5_mm_hr=5.0)
  run_scenario("HEAVY", era5_mm_hr=21.1)
