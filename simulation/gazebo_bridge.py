"""
Gazebo SDF World Bridge & Hydro-Kinetic Simulation Orchestrator.
Parses simulation/worlds/bengaluru_silkboard_inundation.sdf, steps the 3D urban
inundation physics, streams Modbus RTU radar telemetry, executes ITMS Rainy Day
Inversion vision logic, computes Priority Dispatch Index (PDI), and generates
automated BBMP/BTP JSON dispatch events.
"""

import os
import math
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, List, Optional

import ai_engine
from simulation.modbus_radar import FMCWRadarEmulator
from simulation.itms_gantry_vision import (
    ITMSGantryVisionSimulator,
    generate_authentic_flooded_frame,
    generate_synthetic_deepfake_frame,
)

DEFAULT_SDF_PATH = os.path.join(
    os.path.dirname(__file__),
    "worlds",
    "bengaluru_silkboard_inundation.sdf",
)


def parse_sdf_world_config(sdf_path: str = DEFAULT_SDF_PATH) -> Dict[str, Any]:
    """Parse key physical & sensor parameters from the Gazebo SDF 1.9 world file."""
    cfg = {
        "world_name": "bengaluru_silkboard_inundation",
        "zone_id": "silk_board",
        "catch_basin_id": "CB-FMCW-SB-102",
        "max_capacity_cm": 120.0,
        "drainage_coeff_alpha": 0.38,
        "modbus_slave_id": 1,
        "modbus_baudrate": 9600,
        "rainy_day_speed_threshold_kmh": 18.0,
        "sdf_loaded": False,
    }
    if not os.path.exists(sdf_path):
        return cfg

    try:
        tree = ET.parse(sdf_path)
        root = tree.getroot()
        world = root.find("world")
        if world is not None:
            cfg["world_name"] = world.attrib.get("name", cfg["world_name"])
            plugin = world.find(".//plugin[@name='hk_rhs::HydroKineticWorldPlugin']")
            if plugin is not None:
                for tag, cast in [
                    ("zone_id", str),
                    ("catch_basin_id", str),
                    ("max_capacity_cm", float),
                    ("drainage_coeff_alpha", float),
                    ("modbus_slave_id", int),
                    ("modbus_baudrate", int),
                    ("rainy_day_speed_threshold_kmh", float),
                ]:
                    el = plugin.find(tag)
                    if el is not None and el.text:
                        cfg[tag] = cast(el.text.strip())
        cfg["sdf_loaded"] = True
    except Exception:
        pass
    return cfg


class GazeboHydroKineticBridge:
    """
    Live Digital Twin Bridge connecting the Gazebo SDF world, Modbus RTU radar
    emulator, ITMS Rainy Day Inversion vision engine, and FastAPI ICCC broker.
    """

    def __init__(self, sdf_path: str = DEFAULT_SDF_PATH):
        self.sdf_path = sdf_path
        self.world_cfg = parse_sdf_world_config(sdf_path)
        self.radar = FMCWRadarEmulator(
            slave_id=self.world_cfg["modbus_slave_id"],
            baudrate=self.world_cfg["modbus_baudrate"],
            frequency_ghz=77.0,
        )
        self.vision = ITMSGantryVisionSimulator(
            camera_id="BTP-ITMS-SB-01",
            speed_threshold_kmh=self.world_cfg["rainy_day_speed_threshold_kmh"],
        )
        self.reset()

    def reset(self) -> Dict[str, Any]:
        """Reset Gazebo world state to baseline dry/light-drizzle operating conditions."""
        self.sim_time_s = 0.0
        self.step_count = 0
        self.scenario = "baseline_monsoon"
        self.hw_cm = 22.0
        self.dh_dt_cm_min = 0.35
        self.rainfall_mmhr = 12.0
        self.grate_obstruction_pct = 12.0
        self.delta_h = 0.14
        self.traffic_speed_kmh = 40.0
        self.history: List[Dict[str, Any]] = []
        return self.get_telemetry_snapshot(include_frame=False)

    def set_scenario(self, scenario: str) -> Dict[str, Any]:
        """Inject a physical inundation or blockage scenario into the Gazebo world."""
        self.scenario = scenario
        if scenario == "heavy_rain_inversion":
            self.rainfall_mmhr = 78.0
            self.grate_obstruction_pct = 62.0
            self.hw_cm = max(self.hw_cm, 64.0)
            self.traffic_speed_kmh = 11.5
        elif scenario == "silt_clog":
            self.rainfall_mmhr = 22.0
            self.grate_obstruction_pct = 84.0
            self.hw_cm = max(self.hw_cm, 78.0)
            self.traffic_speed_kmh = 13.0
        elif scenario == "cloudburst":
            self.rainfall_mmhr = 96.0
            self.grate_obstruction_pct = 28.0
            self.hw_cm = max(self.hw_cm, 88.0)
            self.traffic_speed_kmh = 9.5
        elif scenario == "reset":
            return self.reset()
        return self.step(dt_seconds=1.0)

    def compute_pdi(self) -> Dict[str, Any]:
        """
        Compute Priority Dispatch Index (PDI: 0..100) from live Gazebo telemetry
        and emit automated JSON dispatch payloads for BBMP and BTP queues.
        """
        max_cap = self.world_cfg["max_capacity_cm"]
        depth_norm = min(100.0, (self.hw_cm / max_cap) * 100.0)
        inflow_norm = min(100.0, max(0.0, self.delta_h) * 35.0)
        clog_norm = min(100.0, max(0.0, self.grate_obstruction_pct))
        congestion_norm = min(100.0, max(0.0, ((45.0 - self.traffic_speed_kmh) / 45.0) * 100.0))

        pdi_score = round(
            0.35 * depth_norm +
            0.25 * inflow_norm +
            0.20 * clog_norm +
            0.20 * congestion_norm,
            2,
        )

        if pdi_score >= 75.0:
            tier = "CRITICAL_EMERGENCY"
        elif pdi_score >= 55.0:
            tier = "HIGH_PRIORITY"
        elif pdi_score >= 30.0:
            tier = "MODERATE_WATCH"
        else:
            tier = "NORMAL"

        dispatch_events: List[Dict[str, Any]] = []
        ts = datetime.now().strftime("%H:%M:%S")

        if pdi_score >= 55.0:
            if self.grate_obstruction_pct >= 50.0 or self.delta_h >= 1.2:
                dispatch_events.append({
                    "target_agency": "BBMP_STORMWATER",
                    "action": "DISPATCH_HYDRO_VACUUM_DESILTING",
                    "priority": tier,
                    "pdi_score": pdi_score,
                    "zone_id": self.world_cfg["zone_id"],
                    "catch_basin_id": self.world_cfg["catch_basin_id"],
                    "rationale": f"Gazebo FMCW radar Delta-H={self.delta_h:.2f} & grate obstruction={self.grate_obstruction_pct:.1f}%",
                    "timestamp": ts,
                })
            else:
                dispatch_events.append({
                    "target_agency": "BBMP_DEWATERING",
                    "action": "ACTIVATE_500GPM_DEWATERING_PUMP",
                    "priority": tier,
                    "pdi_score": pdi_score,
                    "zone_id": self.world_cfg["zone_id"],
                    "catch_basin_id": self.world_cfg["catch_basin_id"],
                    "rationale": f"Macro runoff surge H_w={self.hw_cm:.1f}cm under {self.rainfall_mmhr:.1f}mm/hr rainfall",
                    "timestamp": ts,
                })

            if self.traffic_speed_kmh < self.world_cfg["rainy_day_speed_threshold_kmh"]:
                dispatch_events.append({
                    "target_agency": "BTP_TRAFFIC_ICCC",
                    "action": "TRIGGER_VMS_DIVERSION_AND_WARDENS",
                    "priority": tier,
                    "pdi_score": pdi_score,
                    "zone_id": self.world_cfg["zone_id"],
                    "vms_message": f"FLOODING AHEAD ({self.hw_cm:.0f}CM) • DIVERT VIA SERVICE LANE • 15 KM/H",
                    "rationale": f"Rainy Day Inversion active: corridor speed dropped to {self.traffic_speed_kmh:.1f} km/h",
                    "timestamp": ts,
                })

        return {
            "pdi_score": pdi_score,
            "priority_tier": tier,
            "components": {
                "depth_factor": round(depth_norm, 1),
                "inflow_anomaly_factor": round(inflow_norm, 1),
                "grate_obstruction_factor": round(clog_norm, 1),
                "traffic_collapse_factor": round(congestion_norm, 1),
            },
            "automated_dispatch_events": dispatch_events,
        }

    def step(self, dt_seconds: float = 1.0, steps: int = 1) -> Dict[str, Any]:
        """Advance the Gazebo 3D hydro-kinetic physics loop by `steps` ticks."""
        max_cap = self.world_cfg["max_capacity_cm"]
        alpha = self.world_cfg["drainage_coeff_alpha"]

        for _ in range(max(1, steps)):
            self.step_count += 1
            self.sim_time_s += dt_seconds

            # Inflow rate from rainfall (cm/min)
            inflow_cm_min = (self.rainfall_mmhr / 60.0) * 3.8
            # Effective culvert discharge reduced by grate obstruction
            effective_alpha = alpha * max(0.08, 1.0 - (self.grate_obstruction_pct / 100.0))
            outflow_cm_min = effective_alpha * math.sqrt(max(1.0, self.hw_cm))

            dh_dt = inflow_cm_min - outflow_cm_min
            self.dh_dt_cm_min = round(dh_dt, 2)
            self.hw_cm = round(max(8.0, min(max_cap * 0.96, self.hw_cm + dh_dt * (dt_seconds / 10.0) * 6.0)), 2)

            # Differential Inflow Index Delta-H: isolates physical clog vs pure rain
            expected_dh = (self.rainfall_mmhr / 60.0) * 0.85
            self.delta_h = round(max(0.05, (self.grate_obstruction_pct / 35.0) + max(0.0, dh_dt - expected_dh) * 0.35), 2)

            # Traffic speed collapses nonlinearly with rising water depth
            target_speed = max(6.5, 44.0 - (self.hw_cm / max_cap) * 38.0 - (self.rainfall_mmhr / 120.0) * 8.0)
            self.traffic_speed_kmh = round(0.7 * self.traffic_speed_kmh + 0.3 * target_speed, 1)

        return self.get_telemetry_snapshot(include_frame=False)

    def get_telemetry_snapshot(self, include_frame: bool = False) -> Dict[str, Any]:
        """Return full synchronized snapshot: SDF config, Modbus radar, ITMS vision, and PDI."""
        radar_payload = self.radar.sample_and_stream(
            hw_cm=self.hw_cm,
            dh_dt_cm_min=self.dh_dt_cm_min,
            rainfall_mmhr=self.rainfall_mmhr,
            grate_obstruction_pct=self.grate_obstruction_pct,
            delta_h=self.delta_h,
        )
        vision_payload = self.vision.evaluate_rainy_day_inversion(
            traffic_speed_kmh=self.traffic_speed_kmh,
            water_level_cm=self.hw_cm,
            grate_obstruction_pct=self.grate_obstruction_pct,
            rainfall_mmhr=self.rainfall_mmhr,
        )
        if include_frame:
            vision_payload["frame_jpeg_data_url"] = self.vision.render_gantry_frame_base64(
                water_level_cm=self.hw_cm,
                grate_obstruction_pct=self.grate_obstruction_pct,
                rainfall_mmhr=self.rainfall_mmhr,
                traffic_speed_kmh=self.traffic_speed_kmh,
            )

        pdi_payload = self.compute_pdi()

        return {
            "status": "ONLINE",
            "sdf_world": self.world_cfg,
            "sim_time_s": round(self.sim_time_s, 2),
            "step_count": self.step_count,
            "scenario": self.scenario,
            "fmcw_radar_modbus": radar_payload,
            "itms_gantry_vision": vision_payload,
            "priority_dispatch_index": pdi_payload,
        }

    def run_forensic_verification_suite(self) -> Dict[str, Any]:
        """
        Route both a genuine flooded-road camera frame and an injected synthetic
        deepfake frame through ai_engine.verify_citizen_hazard_upload() to validate
        automated forensic rejection and spatial-temporal consistency.
        """
        authentic_b64 = generate_authentic_flooded_frame()
        deepfake_b64 = generate_synthetic_deepfake_frame()

        authentic_res = ai_engine.verify_citizen_hazard_upload(
            reporter_name="Gazebo Sim Citizen #1",
            zone_id=self.world_cfg["zone_id"],
            zone_name="Silk Board Junction - Hosur Rd",
            hazard_type="Waterlogging",
            description=f"Flooded carriageway near catch-basin {self.world_cfg['catch_basin_id']}",
            image_base64=authentic_b64,
            simulate_deepfake=False,
            filename="silkboard_cam_capture.jpg",
        )

        deepfake_res = ai_engine.verify_citizen_hazard_upload(
            reporter_name="Gazebo Sim Spoofer #2",
            zone_id=self.world_cfg["zone_id"],
            zone_name="Silk Board Junction - Hosur Rd",
            hazard_type="Waterlogging",
            description="Injected synthetic deepfake waterlogging image",
            image_base64=deepfake_b64,
            simulate_deepfake=False,
            filename="synthetic_gan_flood.png",
        )

        passed = (
            (not authentic_res.get("is_ai_created"))
            and authentic_res.get("status") == "VERIFIED_AUTHENTIC"
            and bool(deepfake_res.get("is_ai_created"))
            and deepfake_res.get("status") == "INVALID / REJECTED"
        )

        return {
            "suite_passed": passed,
            "authentic_sample": {
                "is_ai_created": authentic_res.get("is_ai_created"),
                "status": authentic_res.get("status"),
                "municipal_action": authentic_res.get("municipal_action"),
                "estimated_depth_cm": authentic_res.get("estimated_depth_cm"),
                "forensic_audit_notes": authentic_res.get("forensic_audit_notes"),
            },
            "synthetic_deepfake_sample": {
                "is_ai_created": deepfake_res.get("is_ai_created"),
                "status": deepfake_res.get("status"),
                "municipal_action": deepfake_res.get("municipal_action"),
                "rejection_reason": deepfake_res.get("rejection_reason"),
                "forensic_audit_notes": deepfake_res.get("forensic_audit_notes"),
            },
        }
