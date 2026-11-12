"""
Namma Bengaluru - HK-RHS (Hydro-Kinetic Road Hazard System)
ITMS Gantry Camera & Edge-AI Vision Simulator with "Rainy Day Inversion" Trigger.

Implements dynamic compute reallocation on the Edge-AI NPU/GPU:
  - Normal Flow (traffic_speed >= 18 km/h):
      80% compute -> High-speed Vehicle / ANPR / Deceleration Tracking (30 FPS)
      20% compute -> Background Water-Pooling & Grate-Obstruction Monitoring (4 FPS)
  - Rainy Day Inversion (traffic_speed < 18 km/h):
      20% compute -> Throttled Vehicle Detection (5 FPS)
      45% compute -> Real-Time Water-Pooling Semantic Segmentation (24 FPS)
      35% compute -> Storm-Drain Grate-Obstruction Segmentation (20 FPS)
"""

import io
import base64
import random
from typing import Dict, Any
from PIL import Image, ImageDraw


class ITMSGantryVisionEngine:
    """
    Simulates /hk_rhs/itms/gantry_cam/image_raw frame processing and executes
    the Rainy Day Inversion compute-reallocation state machine.
    """

    SPEED_THRESHOLD_KMH = 18.0
    RAIN_THRESHOLD_MMHR = 15.0

    def __init__(self, camera_id: str = "BTP-ITMS-SB-01", width: int = 640, height: int = 360):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.frame_seq = 0

    def evaluate_rainy_day_inversion(
        self,
        traffic_speed_kmh: float,
        rainfall_mmhr: float,
        water_level_cm: float,
        grate_obstruction_pct: float,
        stalled_vehicles: int = 1,
    ) -> Dict[str, Any]:
        """
        Evaluate the Rainy Day Inversion trigger and return Edge-AI compute allocation
        alongside water-pooling and grate-obstruction segmentation metrics.
        """
        self.frame_seq += 1
        speed_triggered = traffic_speed_kmh < self.SPEED_THRESHOLD_KMH
        rain_heavy = rainfall_mmhr >= self.RAIN_THRESHOLD_MMHR
        inversion_active = speed_triggered and (rain_heavy or water_level_cm >= 30.0)

        if inversion_active:
            mode = "RAINY_DAY_INVERSION"
            vehicle_det_fps = 5.0
            compute_split = {
                "vehicle_detection_pct": 20,
                "water_pooling_segmentation_pct": 45,
                "grate_obstruction_segmentation_pct": 35,
            }
            seg_fps = 24.0
            trigger_reason = (
                f"Traffic speed ({traffic_speed_kmh:.1f} km/h < {self.SPEED_THRESHOLD_KMH} km/h) "
                f"under monsoon conditions ({rainfall_mmhr:.1f} mm/hr). "
                "Throttling high-speed vehicle tracker to 5 FPS; reallocating 80% NPU compute to flood & grate segmentation."
            )
        else:
            mode = "HIGH_SPEED_ITMS_FLOW"
            vehicle_det_fps = 30.0
            compute_split = {
                "vehicle_detection_pct": 80,
                "water_pooling_segmentation_pct": 12,
                "grate_obstruction_segmentation_pct": 8,
            }
            seg_fps = 4.0
            trigger_reason = (
                f"Corridor speed ({traffic_speed_kmh:.1f} km/h >= {self.SPEED_THRESHOLD_KMH} km/h). "
                "Primary compute allocated to high-speed ANPR & collision kinematics."
            )

        # Derive water-pooling road surface coverage % from Gazebo water level H_w(t)
        water_pooling_pct = round(min(94.0, max(4.0, (water_level_cm / 110.0) * 88.0)), 1)
        grate_obs = round(min(98.0, max(5.0, grate_obstruction_pct)), 1)

        return {
            "camera_id": self.camera_id,
            "gazebo_topic": "/hk_rhs/itms/gantry_cam/image_raw",
            "frame_seq": self.frame_seq,
            "mode": mode,
            "rainy_day_inversion_active": inversion_active,
            "trigger_threshold_kmh": self.SPEED_THRESHOLD_KMH,
            "vehicle_detection_fps": vehicle_det_fps,
            "segmentation_fps": seg_fps,
            "compute_allocation": compute_split,
            "segmentation_output": {
                "water_pooling_coverage_pct": water_pooling_pct,
                "grate_obstruction_pct": grate_obs,
                "stalled_vehicles_tracked": stalled_vehicles,
                "manhole_overflow_detected": water_level_cm > 65.0,
            },
            "trigger_reason": trigger_reason,
        }

    def render_gantry_frame_b64(
        self,
        telemetry: Dict[str, Any],
        water_level_cm: float,
        rainfall_mmhr: float,
        traffic_speed_kmh: float,
    ) -> str:
        """
        Render a 640x360 synthetic Gazebo gantry camera frame with rain streaks,
        water-pooling segmentation mask, drainage grate ROI, and Rainy Day Inversion HUD.
        """
        img = Image.new("RGB", (self.width, self.height), (24, 30, 38))
        draw = ImageDraw.Draw(img, "RGBA")

        # Wet asphalt roadbed
        draw.rectangle([0, 95, self.width, self.height], fill=(34, 39, 46, 255))
        # Lane markings & crosswalk
        for x in range(30, 610, 85):
            draw.rectangle([x, 210, x + 42, 218], fill=(205, 208, 210, 210))
        for y in range(255, 345, 22):
            draw.rectangle([80, y, 165, y + 11], fill=(220, 222, 225, 190))

        # Water-pooling semantic segmentation overlay
        seg = telemetry["segmentation_output"]
        pool_pct = seg["water_pooling_coverage_pct"]
        pool_alpha = int(min(185, 55 + pool_pct * 1.3))
        draw.polygon(
            [(180, 175), (590, 165), (625, 340), (140, 345)],
            fill=(14, 165, 233, pool_alpha),
            outline=(56, 189, 248, 230),
        )

        # Drainage grate + manhole ROI box (right carriageway curb)
        grate_obs = seg["grate_obstruction_pct"]
        grate_color = (244, 63, 94, 230) if grate_obs > 55 else (245, 158, 11, 220)
        draw.rectangle([455, 235, 565, 295], fill=(45, 38, 30, 220), outline=grate_color, width=3)
        draw.text((458, 218), f"GRATE OBS: {grate_obs:.0f}%", fill=grate_color)

        # Simulated vehicles (throttled bounding boxes in Rainy Day Inversion)
        veh_color = (250, 204, 21, 180) if telemetry["rainy_day_inversion_active"] else (16, 185, 129, 230)
        draw.rectangle([215, 130, 325, 195], fill=(175, 182, 192, 255), outline=veh_color, width=2)
        draw.text((217, 115), f"VEH {traffic_speed_kmh:.0f}km/h", fill=veh_color)

        # Slanted monsoon rain streaks
        rng = random.Random(self.frame_seq)
        streak_count = int(min(180, max(10, rainfall_mmhr * 1.8)))
        for _ in range(streak_count):
            rx = rng.randint(0, self.width - 10)
            ry = rng.randint(0, self.height - 20)
            draw.line([(rx, ry), (rx - 6, ry + 16)], fill=(186, 230, 253, 125), width=1)

        # Top Edge-AI Tactical HUD Banner
        draw.rectangle([0, 0, self.width, 46], fill=(9, 13, 22, 230))
        mode_tag = "RAINY DAY INVERSION [ACTIVE]" if telemetry["rainy_day_inversion_active"] else "HIGH-SPEED ITMS [NORMAL]"
        mode_col = (56, 189, 248, 255) if telemetry["rainy_day_inversion_active"] else (52, 211, 153, 255)
        draw.text((12, 8), f"CAM: {self.camera_id} | {mode_tag} | H_w={water_level_cm:.1f}cm", fill=mode_col)
        comp = telemetry["compute_allocation"]
        draw.text(
            (12, 26),
            f"NPU Compute -> Veh:{comp['vehicle_detection_pct']}% ({telemetry['vehicle_detection_fps']:.0f}fps) | "
            f"WaterSeg:{comp['water_pooling_segmentation_pct']}% | GrateSeg:{comp['grate_obstruction_segmentation_pct']}%",
            fill=(203, 213, 225, 255),
        )

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=82)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")
