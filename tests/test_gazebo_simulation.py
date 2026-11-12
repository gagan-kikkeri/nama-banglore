"""
Local Validation Suite for Namma Bengaluru HK-RHS Gazebo Simulation & FastAPI Broker.
Validates:
  1. Gazebo SDF 1.9 world parsing
  2. 77 GHz FMCW Radar Modbus RTU / RS-485 CRC-16 framing & decoding
  3. ITMS Gantry Vision 'Rainy Day Inversion' compute reallocation
  4. Priority Dispatch Index (PDI) & automated BBMP/BTP JSON dispatch events
  5. Multimodal Generative AI / Forensic deepfake rejection
"""

from simulation.gazebo_bridge import GazeboHydroKineticBridge, parse_sdf_world_config
from simulation.modbus_radar import (
    FMCWRadarEmulator,
    build_read_holding_registers_response,
    decode_modbus_rtu_response,
)
from simulation.itms_gantry_vision import ITMSGantryVisionSimulator


def test_sdf_world_loaded():
    cfg = parse_sdf_world_config()
    assert cfg["sdf_loaded"] is True
    assert cfg["world_name"] == "bengaluru_silkboard_inundation"
    assert cfg["catch_basin_id"] == "CB-FMCW-SB-102"
    assert cfg["modbus_slave_id"] == 1


def test_modbus_rtu_crc_and_registers():
    emulator = FMCWRadarEmulator(slave_id=1, baudrate=9600, frequency_ghz=77.0)
    stream = emulator.sample_and_stream(
        hw_cm=74.5,
        dh_dt_cm_min=3.42,
        rainfall_mmhr=78.0,
        grate_obstruction_pct=62.0,
        delta_h=2.15,
    )
    decoded = stream["decoded"]
    assert decoded["crc_valid"] is True
    assert decoded["hw_cm"] == 74.5
    assert decoded["dh_dt_cm_min"] == 3.42
    assert decoded["rainfall_mmhr"] == 78.0
    assert decoded["grate_obstruction_pct"] == 62.0
    assert decoded["delta_h"] == 2.15


def test_rainy_day_inversion_trigger():
    vision = ITMSGantryVisionSimulator(speed_threshold_kmh=18.0)

    normal = vision.evaluate_rainy_day_inversion(
        traffic_speed_kmh=38.0,
        water_level_cm=20.0,
        grate_obstruction_pct=10.0,
        rainfall_mmhr=10.0,
    )
    assert normal["rainy_day_inversion_active"] is False
    assert normal["compute_allocation"]["high_speed_vehicle_detection_pct"] == 70

    inverted = vision.evaluate_rainy_day_inversion(
        traffic_speed_kmh=11.5,
        water_level_cm=75.0,
        grate_obstruction_pct=65.0,
        rainfall_mmhr=82.0,
    )
    assert inverted["rainy_day_inversion_active"] is True
    assert inverted["compute_allocation"]["high_speed_vehicle_detection_pct"] == 15
    assert inverted["compute_allocation"]["water_pooling_segmentation_pct"] == 50
    assert inverted["compute_allocation"]["grate_obstruction_segmentation_pct"] == 35


def test_pdi_dispatch_and_forensics():
    bridge = GazeboHydroKineticBridge()
    snap = bridge.set_scenario("heavy_rain_inversion")

    pdi = snap["priority_dispatch_index"]
    assert pdi["pdi_score"] >= 55.0
    agencies = {e["target_agency"] for e in pdi["automated_dispatch_events"]}
    assert "BBMP_STORMWATER" in agencies
    assert "BTP_TRAFFIC_ICCC" in agencies

    forensic_res = bridge.run_forensic_verification_suite()
    assert forensic_res["suite_passed"] is True
    assert forensic_res["authentic_sample"]["status"] == "VERIFIED_AUTHENTIC"
    assert forensic_res["synthetic_deepfake_sample"]["status"] == "INVALID / REJECTED"
