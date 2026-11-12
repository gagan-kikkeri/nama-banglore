"""
ITMS Gantry & Edge-AI Vision Simulator (Rainy Day Inversion Engine).
Simulates the overhead gantry camera (BTP-ITMS-SB-01) overlooking the flooded
intersection, renders live camera frames under heavy rain, and executes the
Rainy Day Inversion compute reallocation when traffic speed drops below threshold.
"""

import io
import base64
import random
import numpy as np
from PIL import Image, ImageDraw
from typing import Dict, Any, List


class ITMSGantryVisionSimulator:
    """
    Simulates Edge-AI optical inference on ITMS Gantry camera frames (640x360)
    with dynamic 'Rainy Day Inversion' compute reallocation.
    """

    def __init__(self, camera_id: str = "BTP-ITMS-SB-01", speed_threshold_kmh: float = 18.0):
        self.camera_id = camera_id
        self.speed_threshold_kmh = speed_threshold_kmh
        self.frame_counter = 0

    def evaluate_rainy_day_inversion(
        self,
        traffic_speed_kmh: float,
        water_level_cm: float,
        grate_obstruction_pct: float,
        rainfall_mmhr: float,
    ) -> Dict[str, Any]:
        """
        Implements the 'Rainy Day Inversion' trigger logic:
        When traffic speed drops below threshold, throttle high-speed vehicle
        detection and reallocate Edge-AI GPU/NPU compute to water-pooling and
        grate-obstruction segmentation models.
        """
        inversion_active = traffic_speed_kmh < self.speed_threshold_kmh

        if inversion_active:
            compute_allocation = {
                "high_speed_vehicle_detection_pct": 15,
                "water_pooling_segmentation_pct": 50,
                "grate_obstruction_segmentation_pct": 35,
            }
            active_models = [
                "WaterPool-SegNet-v3 (50% NPU)",
                "GrateClog-MaskRCNN (35% NPU)",
                "VehicleTrack-Lite (15% NPU - Throttled)",
            ]
            mode_label = "RAINY_DAY_INVERSION_ACTIVE"
        else:
            compute_allocation = {
                "high_speed_vehicle_detection_pct": 70,
                "water_pooling_segmentation_pct": 15,
                "grate_obstruction_segmentation_pct": 15,
            }
            active_models = [
                "YOLOv8-TrafficFlow-HighFPS (70% NPU)",
                "WaterPool-SegNet-Standby (15% NPU)",
                "GrateClog-Monitor (15% NPU)",
            ]
            mode_label = "NORMAL_TRAFFIC_DETECTION"

        water_pool_area_pct = round(min(94.0, max(2.0, (water_level_cm / 120.0) * 95.0)), 1)

        detections: List[Dict[str, Any]] = [
            {
                "label": "Water-Pooling Segmentation Mask",
                "confidence": 0.96 if inversion_active else 0.84,
                "area_coverage_pct": water_pool_area_pct,
                "bbox": [90, 175, 550, 345],
            },
            {
                "label": "Stormwater Grate Obstruction",
                "confidence": 0.94 if inversion_active else 0.78,
                "obstruction_pct": round(grate_obstruction_pct, 1),
                "bbox": [430, 235, 515, 295],
            },
            {
                "label": "BMTC Bus / Heavy Vehicle",
                "confidence": 0.88 if inversion_active else 0.97,
                "speed_kmh": round(traffic_speed_kmh, 1),
                "bbox": [165, 130, 315, 225],
            },
        ]

        return {
            "camera_id": self.camera_id,
            "mode": mode_label,
            "rainy_day_inversion_active": inversion_active,
            "speed_threshold_kmh": self.speed_threshold_kmh,
            "observed_traffic_speed_kmh": round(traffic_speed_kmh, 1),
            "compute_allocation": compute_allocation,
            "active_models": active_models,
            "water_pooling_coverage_pct": water_pool_area_pct,
            "grate_obstruction_pct": round(grate_obstruction_pct, 1),
            "rainfall_mmhr": round(rainfall_mmhr, 1),
            "detections": detections,
        }

    def render_gantry_frame_base64(
        self,
        water_level_cm: float,
        grate_obstruction_pct: float,
        rainfall_mmhr: float,
        traffic_speed_kmh: float,
    ) -> str:
        """
        Render a 640x360 simulated ITMS gantry camera frame of the flooded intersection
        under heavy rain conditions and return it as a JPEG data URL.
        """
        self.frame_counter += 1
        w, h = 640, 360

        # Base asphalt road with realistic aggregate noise
        rng = np.random.default_rng(self.frame_counter)
        base = np.zeros((h, w, 3), dtype=np.uint8)
        base[:, :, 0] = np.clip(rng.normal(46, 14, (h, w)), 10, 255).astype(np.uint8)
        base[:, :, 1] = np.clip(rng.normal(50, 14, (h, w)), 10, 255).astype(np.uint8)
        base[:, :, 2] = np.clip(rng.normal(56, 15, (h, w)), 10, 255).astype(np.uint8)

        img = Image.fromarray(base, mode="RGB")
        draw = ImageDraw.Draw(img, "RGBA")

        # Lane markings
        for x in range(40, w, 90):
            draw.rectangle([x, 178, x + 45, 185], fill=(225, 225, 210, 210))

        # Manhole & drainage grate at (430..515, 235..295)
        draw.rectangle([430, 235, 515, 295], fill=(28, 30, 34, 255), outline=(110, 120, 130, 255), width=2)
        for gx in range(438, 512, 12):
            draw.line([gx, 238, gx, 292], fill=(70, 75, 80, 255), width=3)

        # Silt/debris clogging overlay on grate
        if grate_obstruction_pct > 15:
            clog_h = int(60 * min(1.0, grate_obstruction_pct / 100.0))
            draw.rectangle([432, 295 - clog_h, 513, 293], fill=(95, 72, 45, 220))

        # Flooded water-pooling contour proportional to H_w(t)
        pool_alpha = int(min(185, max(35, (water_level_cm / 120.0) * 195)))
        pool_expand = int(min(115, (water_level_cm / 120.0) * 120))
        draw.ellipse(
            [140 - pool_expand, 200 - pool_expand // 3, 540 + pool_expand // 2, 330 + pool_expand // 4],
            fill=(24, 95, 145, pool_alpha),
            outline=(56, 189, 248, 200),
            width=2,
        )

        # Simulated vehicles (moving based on frame counter & speed)
        shift = int((self.frame_counter * max(1.0, traffic_speed_kmh) * 0.4) % 220)
        bus_x = 120 + (shift if traffic_speed_kmh > 10 else 20)
        draw.rectangle([bus_x, 125, bus_x + 130, 195], fill=(15, 95, 190, 255), outline=(220, 235, 255, 255), width=2)
        draw.rectangle([bus_x + 10, 135, bus_x + 120, 158], fill=(180, 220, 250, 220))

        # Heavy rain streaks
        rain_drops = int(min(260, max(20, rainfall_mmhr * 2.5)))
        for _ in range(rain_drops):
            rx = random.randint(0, w - 1)
            ry = random.randint(0, h - 1)
            draw.line([rx, ry, rx - 4, ry + 14], fill=(195, 225, 255, 120), width=1)

        # Telemetry HUD stamp
        mode_txt = "RAINY DAY INVERSION" if traffic_speed_kmh < self.speed_threshold_kmh else "NORMAL FLOW"
        draw.rectangle([8, 8, 430, 34], fill=(5, 10, 20, 200))
        draw.text((14, 14), f"{self.camera_id} | {mode_txt} | Hw={water_level_cm:.1f}cm | v={traffic_speed_kmh:.1f}km/h", fill=(56, 189, 248, 255))

        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"


def generate_authentic_flooded_frame() -> str:
    """Generate a high-texture authentic road inundation frame (with physical camera grain)."""
    w, h = 640, 360
    rng = np.random.default_rng(42)
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    arr[:, :, 0] = np.clip(rng.normal(75, 28, (h, w)), 0, 255).astype(np.uint8)
    arr[:, :, 1] = np.clip(rng.normal(78, 28, (h, w)), 0, 255).astype(np.uint8)
    arr[:, :, 2] = np.clip(rng.normal(82, 29, (h, w)), 0, 255).astype(np.uint8)
    # Puddle region with sky reflection & ripples
    arr[140:290, 120:520, 0] = np.clip(rng.normal(55, 22, (150, 400)), 0, 255).astype(np.uint8)
    arr[140:290, 120:520, 1] = np.clip(rng.normal(95, 22, (150, 400)), 0, 255).astype(np.uint8)
    arr[140:290, 120:520, 2] = np.clip(rng.normal(135, 24, (150, 400)), 0, 255).astype(np.uint8)

    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")


def generate_synthetic_deepfake_frame() -> str:
    """Generate a synthetic AI-style 512x512 smooth latent diffusion deepfake test frame."""
    size = 512
    y_grad = np.linspace(40, 160, size, dtype=np.float32)[:, None]
    x_grad = np.linspace(30, 180, size, dtype=np.float32)[None, :]
    r = np.clip(0.5 * y_grad + 0.3 * x_grad, 0, 255).astype(np.uint8)
    g = np.clip(0.6 * y_grad + 0.4 * x_grad, 0, 255).astype(np.uint8)
    b = np.clip(0.8 * y_grad + 0.5 * x_grad, 0, 255).astype(np.uint8)
    arr = np.stack([r, g, b], axis=-1)

    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")
