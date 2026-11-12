"""
End-to-End Localhost Verification Script for Namma Bengaluru - HK-RHS Gazebo Simulation.
Validates:
  1. Custom SDF World parsing (manhole, drainage culvert, 77 GHz FMCW radar, ITMS gantry)
  2. Modbus RTU / RS-485 frame encoding, decoding & CRC-16 validation
  3. ITMS Gantry "Rainy Day Inversion" compute reallocation trigger
  4. Multimodal Generative AI + Spatial-Temporal Forensic Verification (authentic vs deepfake)
  5. Priority Dispatch Index (PDI) & Automated BBMP/BTP JSON dispatch queues on http://127.0.0.1:8000
"""

import sys
import requests

BASE_URL = "http://127.0.0.1:8000"


def main() -> int:
    print(f"[1/5] Checking FastAPI localhost broker at {BASE_URL}/api/state ...")
    r_state = requests.get(f"{BASE_URL}/api/state", timeout=5)
    assert r_state.status_code == 200, f"/api/state failed: {r_state.status_code}"
    print("      OK: Master FastAPI broker online.")

    print("[2/5] Checking Gazebo SDF world & Modbus RTU / RS-485 radar stream ...")
    r_sim = requests.get(f"{BASE_URL}/api/simulation/status", timeout=5)
    assert r_sim.status_code == 200, f"/api/simulation/status failed: {r_sim.status_code}"
    sim = r_sim.json()
    sdf = sim["gazebo_runtime"]["sdf_world"]
    assert sdf["loaded"] is True, "SDF world failed to load"
    assert "manhole_01" in sdf["models"] and "drainage_culvert_01" in sdf["models"]
    modbus = sim["radar_modbus_rtu"]
    assert modbus["crc16_valid"] is True, "Modbus RTU CRC-16 check failed"
    print(f"      OK: SDF={sdf['world_name']} | Models={len(sdf['models'])} | Modbus RX={modbus['rx_frame_hex']}")

    print("[3/5] Verifying 'Rainy Day Inversion' trigger logic ...")
    r_clear = requests.post(f"{BASE_URL}/api/simulation/control", json={"scenario": "clear_weather"}, timeout=5).json()
    vis_clear = r_clear["itms_gantry_vision"]
    assert vis_clear["rainy_day_inversion_active"] is False, "Expected normal ITMS mode in clear_weather"
    assert vis_clear["vehicle_detection_fps"] == 30.0

    r_clog = requests.post(f"{BASE_URL}/api/simulation/control", json={"scenario": "silt_clog"}, timeout=5).json()
    vis_clog = r_clog["itms_gantry_vision"]
    assert vis_clog["rainy_day_inversion_active"] is True, "Expected Rainy Day Inversion in silt_clog"
    assert vis_clog["vehicle_detection_fps"] == 5.0
    assert vis_clog["compute_allocation"]["water_pooling_segmentation_pct"] == 45
    assert vis_clog["compute_allocation"]["grate_obstruction_segmentation_pct"] == 35
    print(
        f"      OK: Clear={vis_clear['mode']} ({vis_clear['vehicle_detection_fps']} FPS) -> "
        f"SiltClog={vis_clog['mode']} ({vis_clog['vehicle_detection_fps']} FPS, 80% Seg Compute)"
    )

    print("[4/5] Verifying Gantry Camera Frame Stream & PDI Automated Dispatch ...")
    r_frame = requests.get(f"{BASE_URL}/api/simulation/gantry-frame", timeout=5).json()
    assert r_frame["image_base64"].startswith("data:image/jpeg;base64,"), "Invalid gantry JPEG frame"
    pdi = r_clog["priority_dispatch_index"]
    assert pdi["pdi_score"] >= 50.0, f"Expected elevated PDI in silt_clog, got {pdi['pdi_score']}"
    assert len(r_clog["automated_dispatch_queue"]) >= 1, "Expected automated BBMP/BTP dispatch event"
    print(f"      OK: Gantry JPEG frame streamed | PDI={pdi['pdi_score']} ({pdi['priority_tier']})")

    print("[5/5] Verifying Multimodal Forensic Verification (Deepfake Rejection vs Authentic Acceptance) ...")
    r_fake = requests.post(f"{BASE_URL}/api/simulation/forensic-test", json={"mode": "synthetic_deepfake"}, timeout=10).json()
    assert r_fake["verdict"] == "INVALID / REJECTED", f"Deepfake was not rejected: {r_fake}"
    assert r_fake["municipal_dispatch_allowed"] is False

    r_real = requests.post(f"{BASE_URL}/api/simulation/forensic-test", json={"mode": "authentic"}, timeout=10).json()
    assert r_real["verdict"] == "VERIFIED_AUTHENTIC", f"Authentic image was not accepted: {r_real}"
    assert r_real["municipal_dispatch_allowed"] is True
    print(f"      OK: Deepfake -> {r_fake['verdict']} | Authentic -> {r_real['verdict']}")

    print("\nALL GAZEBO SIMULATION & LOCALHOST CHECKS PASSED SUCCESSFULLY!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
