"""
Namma Bengaluru - HK-RHS (Hydro-Kinetic Road Hazard System)
REVA University HACKathon 3.0 (AI for Smart Cities & Sustainability)
Team: Team CyberSentinel / Apex Achievers (BMSIT)
Team Members:
  - Gagan N Prasad (Lead Architect)
  - Machal Ritesh Govardhan (Product Strategist)
  - Manav Redhu (Technical Operator)
  - Chimbili Manju Ganesh (UI/UX Designer)

FastAPI Backend Server & Real-time Simulation Engine:
  - 60/77 GHz FMCW Radar Telemetry inside catch-basin soffit behind tilted HDPE radome
  - Differential Inflow Index (ΔH) computation to isolate cloudbursts from physical blockages
  - ITMS Edge-AI Computer Vision Accident & Deceleration Spikes Detection
  - Automated BBMP Desilting Work Orders & Police/112 ICCC Dispatch
  - Citizen Safety Portal API with AI photo validation & Cross-Host Sync
"""

import os
import time
import math
import random
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

# Hardcoded Gemini AI Core Engine & Configuration
import config
import ai_engine

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(
    title="Namma Bengaluru - HK-RHS",
    description="Hydro-Kinetic Road Hazard System | REVA University HACKathon 3.0 | Team CyberSentinel / Apex Achievers (BMSIT)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# DATA MODELS & SCHEMAS
# --------------------------------------------------------------------------

class IncidentInjection(BaseModel):
    zone_id: str
    incident_type: str  # "silt_clog", "cloudburst", "accident", "reset"
    severity: Optional[float] = 1.0

class CitizenReport(BaseModel):
    reporter_name: str = "Bengaluru Commuter"
    reporter_phone: str = "+91 98450 XXXXX"
    zone_id: str
    hazard_type: str  # "Waterlogging", "Severe Collision", "Drain Silt Overflow", "Pothole Hazard"
    latitude: float
    longitude: float
    description: str
    image_data: Optional[str] = None  # Base64 or mock image url
    ai_depth_cm: Optional[float] = None
    ai_confidence_pct: Optional[float] = None
    ai_authenticity_pct: Optional[float] = None
    severity_level: Optional[str] = "CRITICAL"

class CitizenStatusUpdate(BaseModel):
    report_id: str
    status: str  # "RECEIVED_BY_ICCC", "DISPATCHED_TO_BBMP", "IN_PROGRESS", "RESOLVED"
    notes: Optional[str] = None

class WorkOrderUpdate(BaseModel):
    order_id: str
    status: str  # "EN_ROUTE", "IN_PROGRESS", "RESOLVED"

class VmsUpdateRequest(BaseModel):
    zone_id: str
    vms_text: str
    vms_color: str = "AMBER"  # "GREEN", "AMBER", "RED"
    speed_limit_kmh: Optional[int] = 40
    diversion_active: Optional[bool] = False
    diversion_route: Optional[str] = None
    inspector_id: Optional[str] = "BTP-INSP-442"
    manual_override: Optional[bool] = True

class PoliceTacticalAction(BaseModel):
    alert_id: str
    zone_id: Optional[str] = None
    action: str  # "DISPATCH", "CORDON", "RESOLVE", "ACKNOWLEDGE"
    unit_assigned: Optional[str] = "BTP Highway Patrol #09 + 108 Ambulance"
    notes: Optional[str] = None
    dispatcher_badge: Optional[str] = "112-TAC-OP-88"

class BbmpWorkOrderAction(BaseModel):
    order_id: str
    action: str  # "EN_ROUTE", "ARRIVED_ON_SITE", "RESOLVED", "CLEARED"
    crew_id: Optional[str] = "BBMP-CREW-14"
    crew_notes: Optional[str] = None
    slurry_extracted_liters: Optional[float] = 1850.0

# --------------------------------------------------------------------------
# IN-MEMORY TELEMETRY & ZONE STATE
# --------------------------------------------------------------------------

ZONES_CONFIG = {
    "silk_board": {
        "id": "silk_board",
        "name": "Silk Board Junction - Hosur Rd",
        "lat": 12.9177,
        "lng": 77.6238,
        "ward": "Ward 174 (Bommanahalli / HSR)",
        "itms_pole_id": "BTP-ITMS-SB-04",
        "catch_basin_id": "CB-FMCW-SB-102",
        "max_capacity_cm": 120.0,
        "base_water_cm": 24.0,
        "base_rain_mmhr": 14.0,
        "drainage_coeff_alpha": 0.38,  # Drainage rate factor
        "vms_location": "Silk Board South Flyover Approach"
    },
    "orr_bellandur": {
        "id": "orr_bellandur",
        "name": "Outer Ring Road - Bellandur / EcoSpace",
        "lat": 12.9260,
        "lng": 77.6762,
        "ward": "Ward 150 (Bellandur Tech Corridor)",
        "itms_pole_id": "BTP-ITMS-ORR-12",
        "catch_basin_id": "CB-FMCW-ORR-208",
        "max_capacity_cm": 140.0,
        "base_water_cm": 18.0,
        "base_rain_mmhr": 16.0,
        "drainage_coeff_alpha": 0.42,
        "vms_location": "ORR Devarabisanahalli Flyover Gantry"
    },
    "hebbal": {
        "id": "hebbal",
        "name": "Hebbal Flyover - Airport Expressway",
        "lat": 13.0358,
        "lng": 77.5970,
        "ward": "Ward 7 (Byatarayanapura / Hebbal)",
        "itms_pole_id": "BTP-ITMS-HBL-01",
        "catch_basin_id": "CB-FMCW-HBL-044",
        "max_capacity_cm": 130.0,
        "base_water_cm": 15.0,
        "base_rain_mmhr": 12.0,
        "drainage_coeff_alpha": 0.40,
        "vms_location": "Hebbal Northbound Gantry (Airport Corridor)"
    },
    "majestic": {
        "id": "majestic",
        "name": "Majestic - Anand Rao Circle Underpass",
        "lat": 12.9767,
        "lng": 77.5713,
        "ward": "Ward 94 (Gandhinagar / Majestic)",
        "itms_pole_id": "BTP-ITMS-MAJ-09",
        "catch_basin_id": "CB-FMCW-MAJ-310",
        "max_capacity_cm": 150.0,
        "base_water_cm": 22.0,
        "base_rain_mmhr": 15.0,
        "drainage_coeff_alpha": 0.35,
        "vms_location": "Subhash Nagar / KBS Terminal Portal"
    },
    "kr_puram": {
        "id": "kr_puram",
        "name": "K.R. Puram Hanging Bridge & Tin Factory",
        "lat": 13.0012,
        "lng": 77.6838,
        "ward": "Ward 52 (K.R. Puram)",
        "itms_pole_id": "BTP-ITMS-KRP-03",
        "catch_basin_id": "CB-FMCW-KRP-117",
        "max_capacity_cm": 130.0,
        "base_water_cm": 19.0,
        "base_rain_mmhr": 10.0,
        "drainage_coeff_alpha": 0.39,
        "vms_location": "Old Madras Road Interchange Display"
    },
    "goraguntepalya": {
        "id": "goraguntepalya",
        "name": "Goraguntepalya / Yeshwanthpur Junction",
        "lat": 13.0285,
        "lng": 77.5407,
        "ward": "Ward 38 (Yeshwanthpur)",
        "itms_pole_id": "BTP-ITMS-GGP-07",
        "catch_basin_id": "CB-FMCW-GGP-089",
        "max_capacity_cm": 125.0,
        "base_water_cm": 16.0,
        "base_rain_mmhr": 8.0,
        "drainage_coeff_alpha": 0.37,
        "vms_location": "Tumkur Road NH4 Elevated Toll Approach"
    },
    "whitefield": {
        "id": "whitefield",
        "name": "Whitefield - ITPL Main Road / Hope Farm",
        "lat": 12.9856,
        "lng": 77.7374,
        "ward": "Ward 84 (Whitefield / ITPL Corridor)",
        "itms_pole_id": "BTP-ITMS-WTF-05",
        "catch_basin_id": "CB-FMCW-WTF-112",
        "max_capacity_cm": 135.0,
        "base_water_cm": 20.0,
        "base_rain_mmhr": 11.0,
        "drainage_coeff_alpha": 0.36,
        "vms_location": "ITPL Main Road Gantry / Hope Farm Jn"
    }
}

# Live dynamic state for each zone
live_zone_state = {}
work_orders = []
emergency_alerts = []
citizen_reports_list = []
system_log = []

def init_state():
    global live_zone_state, work_orders, emergency_alerts, citizen_reports_list, system_log
    live_zone_state = {}
    now = time.time()
    
    for zid, cfg in ZONES_CONFIG.items():
        live_zone_state[zid] = {
            "id": zid,
            "name": cfg["name"],
            "lat": cfg["lat"],
            "lng": cfg["lng"],
            "ward": cfg["ward"],
            "itms_pole_id": cfg["itms_pole_id"],
            "catch_basin_id": cfg["catch_basin_id"],
            # FMCW Radar Telemetry
            "radar_frequency_ghz": 77.0,
            "radome_status": "HDPE 3.2mm Sealed - Zero H2S Intrusion",
            "water_level_cm": cfg["base_water_cm"],
            "max_capacity_cm": cfg["max_capacity_cm"],
            "water_level_pct": round((cfg["base_water_cm"] / cfg["max_capacity_cm"]) * 100, 1),
            "rate_of_rise_cm_min": 0.4,
            "recession_rate_cm_min": 1.2,
            "rainfall_rate_mmhr": cfg["base_rain_mmhr"],
            # Hydro-Kinetic Mathematical Metrics
            "delta_h": 0.12,  # Differential Inflow Index
            "hazard_classification": "NORMAL_DRAINAGE",  # "NORMAL_DRAINAGE", "SILT_DEBRIS_CLOG", "CLOUDBURST_OVERLOAD"
            "risk_score": 0.18,  # 0.0 to 1.0
            # ITMS Edge-AI Computer Vision State
            "edge_cv_fps": 29.8,
            "edge_cv_inference_latency_ms": 14.2,
            "accident_detected": False,
            "accident_confidence": 0.0,
            "stalled_vehicle_count": 0,
            "deceleration_spike_detected": False,
            "traffic_speed_kmh": 42.0,
            # Dynamic VMS Highway Signage
            "vms_text": "CORRIDOR CLEAR • MAINTAIN SAFE LANE DISTANCE • SPEED 50 KM/H",
            "vms_color": "GREEN",
            "vms_speed_limit_kmh": 50,
            "vms_manual_override": False,
            "diversion_active": False,
            "diversion_route": "NONE",
            # Historical telemetry for live graphing
            "history_timestamps": [int(now - (i * 10)) for i in range(12, 0, -1)],
            "history_water_cm": [round(cfg["base_water_cm"] + random.uniform(-1.5, 1.5), 1) for _ in range(12)],
            "history_delta_h": [round(0.1 + random.uniform(-0.05, 0.08), 2) for _ in range(12)],
            "history_rainfall_mmhr": [round(cfg["base_rain_mmhr"] + random.uniform(-2.0, 2.0), 1) for _ in range(12)]
        }
        
    # Initial sample work order
    work_orders = [
        {
            "id": "BBMP-WO-8821",
            "zone_id": "silk_board",
            "zone_name": "Silk Board Junction - Hosur Rd",
            "ward": "Ward 174",
            "type": "HYDRO_JET_DESILTING",
            "cause": "Differential Inflow Index ΔH > 1.8 (Silt choke detected)",
            "priority": "HIGH",
            "status": "DISPATCHED",
            "unit": "BBMP Quick Reaction Silt-Suction Unit #14",
            "sla_minutes": 35,
            "catch_basin_id": "CB-FMCW-SB-102",
            "delta_h": 1.95,
            "water_level_cm": 74.5,
            "lat": 12.9177,
            "lng": 77.6238,
            "created_at": datetime.now().strftime("%H:%M:%S")
        }
    ]
    
    emergency_alerts = [
        {
            "id": "BTP-EMERG-712",
            "zone_id": "silk_board",
            "zone_name": "Silk Board Junction - Hosur Rd",
            "type": "ITMS_EDGE_AI_COLLISION",
            "message": "Carriageway multi-vehicle sideswipe captured by BTP-ITMS-SB-04. Deceleration -5.4 m/s². 1 lane impeded.",
            "severity": "CRITICAL",
            "status": "DISPATCHED",
            "assigned_unit": "BTP Highway Patrol #09",
            "itms_pole_id": "BTP-ITMS-SB-04",
            "lat": 12.9177,
            "lng": 77.6238,
            "deceleration": "-5.4 m/s²",
            "confidence": 95.2,
            "blocked_lanes": "Lane 1 (Right Flume)",
            "nearest_units": [
                {"name": "BTP Highway Patrol #09", "eta": "2 min", "dist": "0.8 km", "type": "PATROL"},
                {"name": "108 Ambulance (St. John's)", "eta": "4 min", "dist": "1.7 km", "type": "MEDICAL"},
                {"name": "BBMP Quick Tow Crane #04", "eta": "7 min", "dist": "3.1 km", "type": "TOW"}
            ],
            "timestamp": datetime.now().strftime("%H:%M:%S")
        },
        {
            "id": "ICCC-ALT-109",
            "zone_id": "hebbal",
            "zone_name": "Hebbal Flyover",
            "type": "WEATHER_MONSOON_ADVISORY",
            "message": "Continuous precipitation observed. Catch-basin telemetry within safe margin (18% capacity).",
            "severity": "INFO",
            "status": "MONITORING",
            "assigned_unit": "Ward 7 Drainage Patrol",
            "itms_pole_id": "BTP-ITMS-HBL-01",
            "lat": 13.0358,
            "lng": 77.5970,
            "deceleration": "0.0 m/s²",
            "confidence": 99.0,
            "blocked_lanes": "None (Carriageway Clear)",
            "nearest_units": [
                {"name": "BTP Expressway Interceptor #03", "eta": "5 min", "dist": "2.5 km", "type": "PATROL"}
            ],
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
    ]
    
    citizen_reports_list = [
        {
            "id": "CIT-REP-401",
            "reporter_name": "Rohan Deshmukh",
            "zone_name": "Silk Board Junction",
            "hazard_type": "Waterlogging",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "ai_verification": "VERIFIED (Water Depth ~26cm, Confidence 95.8%)",
            "status": "VALIDATED_BY_ICCC"
        }
    ]
    
    system_log = [
        f"[{datetime.now().strftime('%H:%M:%S')}] HK-RHS System Initialized across 6 Bengaluru High-Priority Arteries.",
        f"[{datetime.now().strftime('%H:%M:%S')}] 60/77 GHz FMCW Millimeter-Wave Radome telemetry online with zero civil excavation.",
        f"[{datetime.now().strftime('%H:%M:%S')}] ITMS Speed Camera Edge-AI vision neural net calibrated at 30 FPS."
    ]

init_state()

# --------------------------------------------------------------------------
# HYDRO-KINETIC CALCULATION ENGINE
# --------------------------------------------------------------------------

def update_zone_physics(zid: str):
    """
    Computes Differential Inflow Index (ΔH) and HK-RHS Corridor Risk Score.
    
    Mathematical Formulation:
      ΔH = (dh/dt) - α * R(t)
      Where:
        dh/dt: Rate of basin water level rise (cm/min)
        R(t): Local rainfall intensity (mm/hr scaled)
        α: Hydraulic discharge coefficient
        
      If ΔH > 0.8 with moderate rainfall (R < 35 mm/hr) -> PHYSICAL SILT BLOCKAGE
      If R > 55 mm/hr with balanced ΔH -> MACRO CLOUDBURST OVERLOAD
      
      HK-RHS Risk Score S = min(1.0, w1*(h/hmax) + w2*max(0, ΔH) + w3*I_accident + w4*I_congestion)
    """
    state = live_zone_state[zid]
    cfg = ZONES_CONFIG[zid]
    
    # Random drift simulation unless an active incident is pinned
    if not state.get("pinned_incident"):
        drift = random.uniform(-0.3, 0.4)
        state["rainfall_rate_mmhr"] = max(4.0, min(80.0, state["rainfall_rate_mmhr"] + drift * 0.8))
        
        # Basin inflow dynamics
        inflow = (state["rainfall_rate_mmhr"] * 0.05)
        outflow = cfg["drainage_coeff_alpha"] * (state["water_level_cm"] * 0.08)
        net_change = inflow - outflow + random.uniform(-0.1, 0.1)
        
        state["water_level_cm"] = max(5.0, min(cfg["max_capacity_cm"], state["water_level_cm"] + net_change))
        state["rate_of_rise_cm_min"] = max(0.05, round(inflow * 1.5, 2))
        
        # Calculate ΔH
        expected_rise = cfg["drainage_coeff_alpha"] * (state["rainfall_rate_mmhr"] / 10.0)
        raw_delta_h = (state["rate_of_rise_cm_min"] * 2.0) - expected_rise
        state["delta_h"] = max(0.0, round(raw_delta_h, 2))
        
        # Default classification
        state["hazard_classification"] = "NORMAL_DRAINAGE"

    # Compute percentage
    state["water_level_pct"] = round((state["water_level_cm"] / cfg["max_capacity_cm"]) * 100, 1)

    # Compute Corridor Risk Score (0.0 to 1.0)
    w_water = 0.35 * (state["water_level_cm"] / cfg["max_capacity_cm"])
    w_delta = 0.25 * min(1.0, state["delta_h"] / 2.5)
    w_accident = 0.30 if state["accident_detected"] else 0.0
    w_traffic = 0.10 * max(0.0, (60.0 - state["traffic_speed_kmh"]) / 60.0)
    
    total_score = min(1.0, max(0.05, w_water + w_delta + w_accident + w_traffic))
    state["risk_score"] = round(total_score, 2)
    
    # Update VMS Sign Advisory based on Risk Score & Events (unless manual override active)
    if state.get("vms_manual_override"):
        pass  # Respect active manual advisory pushed by BTP Traffic Inspector
    elif state["accident_detected"]:
        state["vms_text"] = "⚠️ ACCIDENT AHEAD IN LANE 1 & 2 • EMERGENCY TEAMS EN ROUTE • MERGE RIGHT • 20 KM/H"
        state["vms_color"] = "RED"
        state["vms_speed_limit_kmh"] = 20
    elif state["hazard_classification"] == "SILT_DEBRIS_CLOG":
        state["vms_text"] = "⚠️ WATERLOGGING WARNING • DRAIN SILT CHOKE IN PROGRESS • SLOW DOWN • 30 KM/H"
        state["vms_color"] = "AMBER"
        state["vms_speed_limit_kmh"] = 30
    elif state["hazard_classification"] == "CLOUDBURST_OVERLOAD":
        state["vms_text"] = "⛈️ MONSOON CLOUDBURST SURGE • HIGH WATER RESISTANCE • AVOID UNDERPASS"
        state["vms_color"] = "RED"
        state["vms_speed_limit_kmh"] = 20
    elif state["risk_score"] > 0.65:
        state["vms_text"] = "CAUTION: RISING SURFACE WATER • KEEP SAFE DISTANCE • SPEED LIMIT 40 KM/H"
        state["vms_color"] = "AMBER"
        state["vms_speed_limit_kmh"] = 40
    else:
        state["vms_text"] = "CORRIDOR CLEAR • MAINTAIN SAFE LANE DISTANCE • SPEED LIMIT 50 KM/H"
        state["vms_color"] = "GREEN"
        state["vms_speed_limit_kmh"] = 50

    # Append historical point
    now = int(time.time())
    state["history_timestamps"].append(now)
    state["history_water_cm"].append(round(state["water_level_cm"], 1))
    state["history_delta_h"].append(round(state["delta_h"], 2))
    state["history_rainfall_mmhr"].append(round(state["rainfall_rate_mmhr"], 1))
    
    # Keep last 15 points
    if len(state["history_timestamps"]) > 15:
        state["history_timestamps"] = state["history_timestamps"][-15:]
        state["history_water_cm"] = state["history_water_cm"][-15:]
        state["history_delta_h"] = state["history_delta_h"][-15:]
        state["history_rainfall_mmhr"] = state["history_rainfall_mmhr"][-15:]

# Background task to refresh physics continuously
async def simulation_loop():
    while True:
        try:
            for zid in ZONES_CONFIG.keys():
                update_zone_physics(zid)
        except Exception as e:
            print(f"Error in simulation loop: {e}")
        await asyncio.sleep(3.0)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulation_loop())

# --------------------------------------------------------------------------
# API ENDPOINTS
# --------------------------------------------------------------------------

@app.get("/api/state")
def get_full_state():
    """Returns real-time telemetry, risk scores, work orders, alerts, and logs."""
    return {
        "status": "ONLINE",
        "system_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project": "Namma Bengaluru - HK-RHS",
        "team": {
            "name": "Team CyberSentinel / Apex Achievers (BMSIT)",
            "members": [
                {"name": "Gagan N Prasad", "role": "Lead Architect"},
                {"name": "Machal Ritesh Govardhan", "role": "Product Strategist"},
                {"name": "Manav Redhu", "role": "Technical Operator"},
                {"name": "Chimbili Manju Ganesh", "role": "UI/UX Designer"}
            ]
        },
        "zones": live_zone_state,
        "work_orders": work_orders,
        "emergency_alerts": emergency_alerts,
        "citizen_reports": citizen_reports_list,
        "system_log": system_log[-12:]
    }

@app.get("/api/zones/{zone_id}")
def get_zone_detail(zone_id: str):
    if zone_id not in live_zone_state:
        raise HTTPException(status_code=404, detail="Zone not found")
    return live_zone_state[zone_id]

@app.post("/api/simulate/inject")
def inject_incident(injection: IncidentInjection):
    """
    Hackathon Live Demonstration Trigger:
    Simulates real-world urban crises:
      - 'silt_clog': Hydraulic ΔH anomaly with moderate rain -> auto BBMP desilting work order
      - 'cloudburst': Severe monsoon cloudburst -> regional surge & pump trigger
      - 'accident': ITMS Edge-AI detects high-deceleration collision -> automated Police/112 dispatch
      - 'reset': Restores baseline state
    """
    zid = injection.zone_id
    if zid not in live_zone_state:
        raise HTTPException(status_code=404, detail="Zone not found")
        
    state = live_zone_state[zid]
    cfg = ZONES_CONFIG[zid]
    timestamp_str = datetime.now().strftime("%H:%M:%S")

    if injection.incident_type == "silt_clog":
        state["pinned_incident"] = "silt_clog"
        state["rainfall_rate_mmhr"] = 18.0  # Moderate rain
        state["water_level_cm"] = cfg["max_capacity_cm"] * 0.72  # 72% full
        state["rate_of_rise_cm_min"] = 3.8
        state["delta_h"] = 2.45  # Massive inflow anomaly
        state["hazard_classification"] = "SILT_DEBRIS_CLOG"
        state["risk_score"] = 0.88
        state["traffic_speed_kmh"] = 18.0
        
        # Auto-create BBMP Desilting Work Order
        wo_id = f"BBMP-WO-{random.randint(9000, 9999)}"
        new_wo = {
            "id": wo_id,
            "zone_id": zid,
            "zone_name": state["name"],
            "ward": state["ward"],
            "type": "EMERGENCY_SILT_SUCTION",
            "cause": f"Differential Inflow Index ΔH ({state['delta_h']}) spiked while rain is moderate. Catch-basin choke confirmed.",
            "priority": "CRITICAL",
            "status": "DISPATCHED",
            "unit": f"BBMP Hydro-Vacuum Crew #{random.randint(10, 25)}",
            "sla_minutes": 25,
            "catch_basin_id": state["catch_basin_id"],
            "delta_h": state["delta_h"],
            "water_level_cm": state["water_level_cm"],
            "lat": state["lat"],
            "lng": state["lng"],
            "created_at": timestamp_str
        }
        work_orders.insert(0, new_wo)
        
        system_log.append(f"[{timestamp_str}] [ALGORITHM] ΔH Anomaly ({state['delta_h']}) isolated at {state['name']}. Physical silt blockage identified. BBMP Work Order {wo_id} issued.")
        
        return {"status": "SUCCESS", "message": f"Silt Blockage injected at {state['name']}. Work order {wo_id} dispatched.", "zone": state}

    elif injection.incident_type == "cloudburst":
        state["pinned_incident"] = "cloudburst"
        state["rainfall_rate_mmhr"] = 92.0  # Extreme cloudburst
        state["water_level_cm"] = cfg["max_capacity_cm"] * 0.89  # 89% full
        state["rate_of_rise_cm_min"] = 5.2
        state["delta_h"] = 0.42  # Uniform high inflow, not a blockage
        state["hazard_classification"] = "CLOUDBURST_OVERLOAD"
        state["risk_score"] = 0.94
        state["traffic_speed_kmh"] = 12.0
        
        # Trigger Dewatering Pump & Traffic Diversion Alert
        alt_id = f"ICCC-ALT-{random.randint(200, 999)}"
        new_alert = {
            "id": alt_id,
            "zone_id": zid,
            "zone_name": state["name"],
            "type": "MACRO_CLOUDBURST_RUNOFF",
            "message": f"Severe 92 mm/hr Cloudburst Runoff at {state['name']}. High-capacity 500 GPM dewatering pumps activated; VMS diversions posted.",
            "severity": "CRITICAL",
            "status": "DISPATCHED",
            "assigned_unit": "Regional Dewatering Sump Team",
            "lat": state["lat"],
            "lng": state["lng"],
            "timestamp": timestamp_str
        }
        emergency_alerts.insert(0, new_alert)
        
        system_log.append(f"[{timestamp_str}] [ALGORITHM] Macro Cloudburst (92 mm/hr) confirmed at {state['name']}. Regional flood sirens & dewatering pumps armed.")
        return {"status": "SUCCESS", "message": f"Cloudburst Inundation injected at {state['name']}.", "zone": state}

    elif injection.incident_type == "accident":
        state["pinned_incident"] = "accident"
        state["accident_detected"] = True
        state["accident_confidence"] = 96.4
        state["stalled_vehicle_count"] = 2
        state["deceleration_spike_detected"] = True
        state["traffic_speed_kmh"] = 4.0
        state["risk_score"] = 0.97
        
        # Emergency 112 / BTP Alert
        alt_id = f"BTP-EMERG-{random.randint(300, 999)}"
        new_alert = {
            "id": alt_id,
            "zone_id": zid,
            "zone_name": state["name"],
            "type": "ITMS_EDGE_AI_COLLISION",
            "message": f"Multi-vehicle impact detected by {state['itms_pole_id']}. Instant deceleration -6.8 m/s². 2 vehicles blocking Carriageway.",
            "severity": "EMERGENCY",
            "status": "PENDING_DISPATCH",
            "assigned_unit": "Awaiting Police 112 Dispatch",
            "itms_pole_id": state["itms_pole_id"],
            "lat": state["lat"],
            "lng": state["lng"],
            "deceleration": "-6.8 m/s²",
            "confidence": 96.4,
            "blocked_lanes": "Lanes 1 & 2 (Right Carriageway)",
            "nearest_units": [
                {"name": f"BTP Highway Patrol #{random.randint(1, 15):02d}", "eta": "3 min", "dist": "1.1 km", "type": "PATROL"},
                {"name": f"108 Emergency Ambulance #{random.randint(10, 30)}", "eta": "5 min", "dist": "2.2 km", "type": "MEDICAL"},
                {"name": "BTP Heavy Recovery Crane #02", "eta": "8 min", "dist": "3.8 km", "type": "TOW"}
            ],
            "timestamp": timestamp_str
        }
        emergency_alerts.insert(0, new_alert)
        
        system_log.append(f"[{timestamp_str}] [EDGE-AI CV] ITMS Pole {state['itms_pole_id']} captured collision (Conf: 96.4%). BTP Patrol & 108 Ambulance notified.")
        return {"status": "SUCCESS", "message": f"Collision event triggered by ITMS Edge-AI at {state['name']}.", "zone": state}

    elif injection.incident_type == "reset":
        state["pinned_incident"] = None
        state["accident_detected"] = False
        state["accident_confidence"] = 0.0
        state["stalled_vehicle_count"] = 0
        state["deceleration_spike_detected"] = False
        state["traffic_speed_kmh"] = 45.0
        state["water_level_cm"] = cfg["base_water_cm"]
        state["rainfall_rate_mmhr"] = cfg["base_rain_mmhr"]
        state["rate_of_rise_cm_min"] = 0.3
        state["delta_h"] = 0.12
        state["hazard_classification"] = "NORMAL_DRAINAGE"
        state["risk_score"] = 0.18
        
        system_log.append(f"[{timestamp_str}] [RESET] Telemetry normalized at {state['name']}.")
        return {"status": "SUCCESS", "message": f"{state['name']} reset to standard operating baseline.", "zone": state}

    else:
        raise HTTPException(status_code=400, detail="Invalid incident type")

@app.post("/api/citizen/report")
def submit_citizen_report(report: CitizenReport):
    """
    Accepts commuter hazard submissions, performs Google Gemini multimodal verification,
    creates automated BBMP/BTP work order, and synchronizes across all portals.
    """
    timestamp_str = datetime.now().strftime("%H:%M:%S")
    zid = report.zone_id if report.zone_id in live_zone_state else "silk_board"
    zone = live_zone_state[zid]
    
    # ----------------------------------------------------------------------
    # GOOGLE GEMINI AI MULTIMODAL VERIFICATION PIPELINE
    # ----------------------------------------------------------------------
    gemini_res = ai_engine.verify_citizen_hazard_upload(
        reporter_name=report.reporter_name,
        zone_id=zid,
        zone_name=zone["name"],
        hazard_type=report.hazard_type,
        description=report.description,
        image_base64=report.image_data
    )
    
    water_estimate = gemini_res.get("estimated_depth_cm", 34.0)
    confidence = gemini_res.get("confidence_pct", 96)
    authenticity = 99.4
    ai_summary = gemini_res.get("ai_summary", "Gemini Vision verified road inundation.")
    suggested_action = gemini_res.get("suggested_action", "Deploy BBMP Sucker Jetting Crew")
    kannada_advisory = gemini_res.get("kannada_advisory", "")
    model_used = gemini_res.get("model_used", "gemini-flash-lite-latest")
    
    verification_msg = f"GEMINI AI VERIFIED (Depth ~{water_estimate}cm, Conf: {confidence}%, Anti-Spoof: PASSED • {model_used})"
    rep_id = f"CIT-REP-{random.randint(500, 999)}"
    
    # Auto-generate linked municipal dispatch ticket in active queue
    wo_id = f"BBMP-WO-{random.randint(9100, 9999)}"
    if "Collision" in report.hazard_type:
        wo_type = "EMERGENCY_TRAFFIC_CLEARANCE"
        wo_unit = f"BTP Patrol & 108 Emergency Crew #{random.randint(4, 18)}"
        wo_cause = f"Citizen Report #{rep_id} ({report.reporter_name}): Carriageway collision obstructing corridor. {ai_summary[:70]}"
        initial_status = "ESCALATED_TO_ICCC"
    else:
        wo_type = "CITIZEN_ESCALATED_HYDRO_DESILTING"
        wo_unit = f"BBMP Silt-Suction Rapid Unit #{random.randint(11, 24)}"
        wo_cause = f"Citizen Report #{rep_id} ({report.reporter_name}): {report.hazard_type} (Gemini AI depth ~{water_estimate}cm). {ai_summary[:70]}"
        initial_status = "DISPATCHED_TO_BBMP"

    new_wo = {
        "id": wo_id,
        "zone_id": zid,
        "zone_name": zone["name"],
        "ward": zone["ward"],
        "type": wo_type,
        "cause": wo_cause,
        "priority": "CRITICAL" if water_estimate > 35 else "HIGH",
        "status": "DISPATCHED",
        "unit": wo_unit,
        "sla_minutes": 20 if water_estimate > 35 else 35,
        "created_at": timestamp_str,
        "linked_citizen_report": rep_id,
        "equipment_needed": suggested_action,
        "ai_rationale": ai_summary,
        "gemini_verified": True
    }
    work_orders.insert(0, new_wo)

    record = {
        "id": rep_id,
        "reporter_name": report.reporter_name,
        "reporter_phone": report.reporter_phone,
        "zone_id": zid,
        "zone_name": zone["name"],
        "ward": zone["ward"],
        "hazard_type": report.hazard_type,
        "description": report.description,
        "lat": report.latitude,
        "lng": report.longitude,
        "timestamp": timestamp_str,
        "ai_verification": verification_msg,
        "ai_depth_cm": water_estimate,
        "ai_confidence_pct": confidence,
        "ai_authenticity_pct": authenticity,
        "severity": gemini_res.get("severity", "CRITICAL"),
        "ai_summary": ai_summary,
        "kannada_advisory": kannada_advisory,
        "suggested_action": suggested_action,
        "status": initial_status,
        "linked_wo_id": wo_id,
        "model_used": model_used
    }
    citizen_reports_list.insert(0, record)
    
    # Create an ICCC emergency alert
    new_alert = {
        "id": f"CIT-ALERT-{random.randint(100, 900)}",
        "zone_id": zid,
        "zone_name": zone["name"],
        "type": f"CITIZEN_{report.hazard_type.upper().replace(' ', '_')}",
        "message": f"Gemini AI Verified: {ai_summary[:65]}...",
        "severity": "WARNING",
        "timestamp": timestamp_str
    }
    emergency_alerts.insert(0, new_alert)
    
    system_log.append(f"[{timestamp_str}] [GEMINI AI] Report #{rep_id} ({report.reporter_name}) verified at {zone['name']}. Work Order #{wo_id} prioritized.")
    
    return {
        "status": "RECEIVED",
        "report_id": rep_id,
        "work_order_id": wo_id,
        "ai_analysis": {
            "verified": True,
            "estimated_hazard_depth_cm": water_estimate,
            "ai_confidence_pct": confidence,
            "authenticity_pct": authenticity,
            "ai_summary": ai_summary,
            "kannada_advisory": kannada_advisory,
            "suggested_action": suggested_action,
            "model_used": model_used,
            "action_taken": f"Synced with BBMP Command Center (Work Order {wo_id})"
        }
    }

@app.get("/api/citizen/reports")
def get_all_citizen_reports():
    """Returns list of active citizen reports with municipal status."""
    return citizen_reports_list

@app.post("/api/citizen/status")
def update_citizen_report_status(update: CitizenStatusUpdate):
    """Updates municipal status of a citizen report and syncs linked work orders."""
    for r in citizen_reports_list:
        if r["id"] == update.report_id:
            r["status"] = update.status
            timestamp_str = datetime.now().strftime("%H:%M:%S")
            system_log.append(f"[{timestamp_str}] [CITIZEN SYNC] Report {r['id']} marked as {update.status}.")
            
            # Sync corresponding work order if resolved
            if update.status == "RESOLVED":
                for wo in work_orders:
                    if wo.get("linked_citizen_report") == r["id"] or wo.get("id") == r.get("linked_wo_id"):
                        wo["status"] = "RESOLVED"
            return {"status": "UPDATED", "report": r}
    raise HTTPException(status_code=404, detail="Citizen report not found")

@app.post("/api/workorders/update")
def update_work_order(update: WorkOrderUpdate):
    global work_orders
    for i, wo in enumerate(work_orders):
        if wo["id"] == update.order_id:
            timestamp_str = datetime.now().strftime("%H:%M:%S")
            if update.status == "DELETED":
                work_orders.pop(i)
                system_log.append(f"[{timestamp_str}] [BBMP DISPATCH] Work Order {update.order_id} cleared.")
                return {"status": "DELETED", "order_id": update.order_id}
            
            wo["status"] = update.status
            system_log.append(f"[{timestamp_str}] [BBMP DISPATCH] Work Order {wo['id']} marked as {update.status}.")
            # Also update linked citizen report if present
            if wo.get("linked_citizen_report"):
                for r in citizen_reports_list:
                    if r["id"] == wo["linked_citizen_report"]:
                        r["status"] = update.status
            return {"status": "UPDATED", "work_order": wo}
    raise HTTPException(status_code=404, detail="Work order not found")

@app.post("/api/workorders/clear-resolved")
def clear_resolved_work_orders():
    global work_orders
    before_count = len(work_orders)
    work_orders = [wo for wo in work_orders if wo.get("status") != "RESOLVED"]
    timestamp_str = datetime.now().strftime("%H:%M:%S")
    system_log.append(f"[{timestamp_str}] [BBMP DISPATCH] Cleared {before_count - len(work_orders)} resolved tickets.")
    return {"status": "SUCCESS", "cleared": before_count - len(work_orders), "remaining": len(work_orders)}

# --------------------------------------------------------------------------
# PROTOTYPE 3: FIELD RESPONDER & MUNICIPAL OPERATIVE ENDPOINTS
# --------------------------------------------------------------------------

@app.get("/api/responder/overview")
def get_responder_overview():
    """
    Consolidated real-time operational payload for Field Responders:
      - BBMP Desilting Crews
      - Police / Emergency 112 Dispatchers
      - BTP Traffic Inspectors
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Enrich work orders with live basin telemetry
    enriched_work_orders = []
    for wo in work_orders:
        zid = wo.get("zone_id", "silk_board")
        z_state = live_zone_state.get(zid, {})
        enriched_wo = dict(wo)
        enriched_wo["current_delta_h"] = z_state.get("delta_h", 0.12)
        enriched_wo["current_water_cm"] = z_state.get("water_level_cm", 20.0)
        enriched_wo["max_capacity_cm"] = z_state.get("max_capacity_cm", 120.0)
        enriched_wo["water_level_pct"] = z_state.get("water_level_pct", 20.0)
        enriched_wo["hazard_classification"] = z_state.get("hazard_classification", "NORMAL_DRAINAGE")
        enriched_wo["rate_of_rise_cm_min"] = z_state.get("rate_of_rise_cm_min", 0.4)
        enriched_wo["rainfall_rate_mmhr"] = z_state.get("rainfall_rate_mmhr", 12.0)
        enriched_wo["lat"] = z_state.get("lat", 12.9177)
        enriched_wo["lng"] = z_state.get("lng", 77.6238)
        enriched_wo["catch_basin_id"] = z_state.get("catch_basin_id", "CB-FMCW-SB-102")
        enriched_work_orders.append(enriched_wo)
        
    # AI Prioritization via Gemini Engine
    enriched_work_orders = ai_engine.prioritize_bbmp_work_orders_ai(enriched_work_orders, live_zone_state)

    # Active field units simulated fleet
    active_crews = [
        {"id": "BBMP-CREW-14", "name": "BBMP Hydro-Vac Jetting Unit #14", "role": "BBMP_DESILTING", "status": "ON_PATROL", "lat": 12.9190, "lng": 77.6210, "vehicle": "KA-01-GA-4412", "ward": "Ward 174"},
        {"id": "BBMP-CREW-22", "name": "BBMP Silt-Suction Rapid Tanker #22", "role": "BBMP_DESILTING", "status": "AVAILABLE", "lat": 12.9280, "lng": 77.6740, "vehicle": "KA-01-GA-8921", "ward": "Ward 150"},
        {"id": "BTP-PATROL-09", "name": "BTP Highway Interceptor #09", "role": "POLICE_112", "status": "STANDBY", "lat": 12.9160, "lng": 77.6250, "vehicle": "KA-02-G-9112", "officer": "SI Rameshwar"},
        {"id": "EMS-MEDIC-18", "name": "108 Emergency Ambulance #18", "role": "POLICE_112", "status": "STANDBY", "lat": 12.9320, "lng": 77.6200, "vehicle": "KA-02-E-1081", "base": "St. John's EMS"},
        {"id": "BTP-VMS-OP-01", "name": "BTP Traffic Inspector Gantry Console", "role": "BTP_INSPECTOR", "status": "ONLINE", "lat": 12.9767, "lng": 77.5713, "terminal": "ITMS-TMC-CONSOLE"}
    ]
    
    active_wo_count = sum(1 for w in work_orders if w.get("status") != "RESOLVED")
    emergency_count = sum(1 for e in emergency_alerts if e.get("status") in ["PENDING_DISPATCH", "DISPATCHED", "CORDON_ACTIVE"])
    vms_overrides = sum(1 for z in live_zone_state.values() if z.get("vms_manual_override"))
    resolved_count = sum(1 for w in work_orders if w.get("status") == "RESOLVED")
    
    return {
        "status": "ONLINE",
        "timestamp": now_str,
        "zones": live_zone_state,
        "bbmp_work_orders": enriched_work_orders,
        "police_alerts": emergency_alerts,
        "active_crews": active_crews,
        "system_log": system_log[-12:],
        "stats": {
            "active_work_orders": active_wo_count,
            "emergency_incidents": emergency_count,
            "vms_overrides_active": vms_overrides,
            "resolved_today": resolved_count
        }
    }

@app.post("/api/responder/workorder/action")
def handle_responder_workorder_action(action: BbmpWorkOrderAction):
    global work_orders
    timestamp_str = datetime.now().strftime("%H:%M:%S")
    target_wo = None
    
    for wo in work_orders:
        if wo["id"] == action.order_id:
            target_wo = wo
            break
            
    if not target_wo:
        raise HTTPException(status_code=404, detail="Work order not found")
        
    zid = target_wo.get("zone_id")
    z_name = target_wo.get("zone_name", "Bengaluru Corridor")
    
    if action.action == "EN_ROUTE":
        target_wo["status"] = "EN_ROUTE"
        system_log.append(f"[{timestamp_str}] [BBMP FIELD] Crew {action.crew_id} is EN ROUTE to {target_wo['id']} at {z_name}. {action.crew_notes or ''}")
        return {"status": "SUCCESS", "action": "EN_ROUTE", "work_order": target_wo}
        
    elif action.action in ["ARRIVED_ON_SITE", "ON_SITE"]:
        target_wo["status"] = "IN_PROGRESS"
        system_log.append(f"[{timestamp_str}] [BBMP FIELD] Crew {action.crew_id} ARRIVED ON SITE at {target_wo['id']}. High-pressure hydro-jetting initiated.")
        return {"status": "SUCCESS", "action": "IN_PROGRESS", "work_order": target_wo}
        
    elif action.action in ["RESOLVED", "CLEARED"]:
        target_wo["status"] = "RESOLVED"
        target_wo["resolved_at"] = timestamp_str
        target_wo["slurry_cleared_liters"] = action.slurry_extracted_liters or 1850.0
        
        # Closed-loop automation: Reset zone hydraulic blockage in live state!
        if zid in live_zone_state:
            state = live_zone_state[zid]
            cfg = ZONES_CONFIG[zid]
            state["pinned_incident"] = None
            state["water_level_cm"] = cfg["base_water_cm"]
            state["delta_h"] = 0.12
            state["rate_of_rise_cm_min"] = 0.3
            state["hazard_classification"] = "NORMAL_DRAINAGE"
            state["risk_score"] = 0.18
            state["traffic_speed_kmh"] = 45.0
            
        # Resolve linked citizen report if any
        if target_wo.get("linked_citizen_report"):
            for r in citizen_reports_list:
                if r["id"] == target_wo["linked_citizen_report"]:
                    r["status"] = "RESOLVED"
                    
        liters = action.slurry_extracted_liters or 1850.0
        system_log.append(f"[{timestamp_str}] [BBMP RESOLUTION] Work Order {target_wo['id']} CLEARED by {action.crew_id} at {z_name}. {liters:.0f}L silt extracted. Catch-basin ΔH restored to baseline 0.12.")
        return {"status": "SUCCESS", "action": "RESOLVED", "work_order": target_wo}
        
    else:
        raise HTTPException(status_code=400, detail="Unknown work order action")

@app.post("/api/responder/police/action")
def handle_responder_police_action(action: PoliceTacticalAction):
    global emergency_alerts
    timestamp_str = datetime.now().strftime("%H:%M:%S")
    target_alert = None
    
    for alt in emergency_alerts:
        if alt["id"] == action.alert_id:
            target_alert = alt
            break
            
    if not target_alert:
        raise HTTPException(status_code=404, detail="Emergency alert not found")
        
    zid = target_alert.get("zone_id", "silk_board")
    z_name = target_alert.get("zone_name", "Bengaluru Artery")
    
    if action.action == "DISPATCH":
        target_alert["status"] = "DISPATCHED"
        target_alert["assigned_unit"] = action.unit_assigned or "BTP Highway Interceptor #09 + 108 EMS"
        system_log.append(f"[{timestamp_str}] [POLICE 112] Dispatcher {action.dispatcher_badge} assigned {target_alert['assigned_unit']} to {target_alert['id']} at {z_name}. Priority Response.")
        return {"status": "SUCCESS", "action": "DISPATCHED", "alert": target_alert}
        
    elif action.action == "CORDON":
        target_alert["status"] = "CORDON_ACTIVE"
        if zid in live_zone_state:
            state = live_zone_state[zid]
            state["vms_text"] = "⚠️ POLICE EMERGENCY CORDON • LANES 1 & 2 BLOCKED • MERGE RIGHT • 20 KM/H"
            state["vms_color"] = "RED"
            state["vms_speed_limit_kmh"] = 20
            state["vms_manual_override"] = True
            state["traffic_speed_kmh"] = 15.0
        system_log.append(f"[{timestamp_str}] [POLICE 112] Tactical Cordon established at {z_name} by {action.dispatcher_badge}. Dynamic VMS gantry locked to RED.")
        return {"status": "SUCCESS", "action": "CORDON_ACTIVE", "alert": target_alert}
        
    elif action.action in ["RESOLVE", "CLEARED"]:
        target_alert["status"] = "RESOLVED"
        if zid in live_zone_state:
            state = live_zone_state[zid]
            state["accident_detected"] = False
            state["accident_confidence"] = 0.0
            state["stalled_vehicle_count"] = 0
            state["deceleration_spike_detected"] = False
            state["traffic_speed_kmh"] = 45.0
            state["pinned_incident"] = None
            state["risk_score"] = 0.18
            state["vms_manual_override"] = False
        system_log.append(f"[{timestamp_str}] [POLICE 112 CLEARANCE] Incident {target_alert['id']} at {z_name} CLEARED by {action.dispatcher_badge}. Carriageway restored to free-flow.")
        return {"status": "SUCCESS", "action": "RESOLVED", "alert": target_alert}
        
    else:
        raise HTTPException(status_code=400, detail="Unknown police tactical action")

@app.post("/api/responder/vms/update")
def handle_vms_update(req: VmsUpdateRequest):
    if req.zone_id not in live_zone_state:
        raise HTTPException(status_code=404, detail="Zone not found")
        
    state = live_zone_state[req.zone_id]
    state["vms_text"] = req.vms_text
    state["vms_color"] = req.vms_color
    state["vms_speed_limit_kmh"] = req.speed_limit_kmh or 40
    state["diversion_active"] = req.diversion_active or False
    if req.diversion_route:
        state["diversion_route"] = req.diversion_route
    state["vms_manual_override"] = True
    
    timestamp_str = datetime.now().strftime("%H:%M:%S")
    system_log.append(f"[{timestamp_str}] [BTP VMS OVERRIDE] Inspector {req.inspector_id} pushed gantry advisory to {state['name']}: '{req.vms_text}' (Speed: {req.speed_limit_kmh} km/h, Color: {req.vms_color}).")
    
    return {"status": "SUCCESS", "zone_id": req.zone_id, "vms": {
        "text": state["vms_text"],
        "color": state["vms_color"],
        "speed_limit_kmh": state["vms_speed_limit_kmh"],
        "diversion_active": state["diversion_active"],
        "diversion_route": state["diversion_route"]
    }}

@app.post("/api/responder/vms/reset")
def handle_vms_reset(data: Dict[str, str]):
    zid = data.get("zone_id")
    if not zid or zid not in live_zone_state:
        raise HTTPException(status_code=404, detail="Zone not found")
        
    state = live_zone_state[zid]
    state["vms_manual_override"] = False
    timestamp_str = datetime.now().strftime("%H:%M:%S")
    system_log.append(f"[{timestamp_str}] [BTP VMS RESET] Gantry at {state['name']} returned to automatic AI hydrodynamic schedule.")
    return {"status": "SUCCESS", "zone_id": zid}

# --------------------------------------------------------------------------
# GOOGLE GEMINI AI CORE INTEGRATION ENDPOINTS
# --------------------------------------------------------------------------

@app.post("/api/ai/verify-photo")
def ai_verify_photo_endpoint(payload: Dict[str, Any]):
    """
    Real-time multimodal photo depth estimation & anti-spoofing via Google Gemini.
    """
    reporter = payload.get("reporter_name", "Bengaluru Commuter")
    zid = payload.get("zone_id", "silk_board")
    zone = live_zone_state.get(zid, {})
    zname = zone.get("name", "Silk Board Junction - Hosur Rd")
    htype = payload.get("hazard_type", "Waterlogging")
    desc = payload.get("description", "Carriageway inundation")
    img = payload.get("image_base64")
    
    result = ai_engine.verify_citizen_hazard_upload(
        reporter_name=reporter,
        zone_id=zid,
        zone_name=zname,
        hazard_type=htype,
        description=desc,
        image_base64=img
    )
    return result

@app.post("/api/ai/cctv-summary")
def ai_cctv_summary_endpoint(payload: Dict[str, Any]):
    """
    Real-time ITMS optical camera feed synthesis from Gemini.
    """
    zid = payload.get("zone_id", "silk_board")
    zone = live_zone_state.get(zid, live_zone_state["silk_board"])
    summary = ai_engine.generate_live_cctv_summary(zone)
    return summary

@app.post("/api/ai/vms-generate")
def ai_vms_generate_endpoint(payload: Dict[str, Any]):
    """
    Dynamically generates bilingual highway VMS advisory text with Gemini.
    """
    zid = payload.get("zone_id", "silk_board")
    zone = live_zone_state.get(zid, live_zone_state["silk_board"])
    vms_res = ai_engine.generate_dynamic_vms_advisory_ai(zone)
    if payload.get("auto_apply", False):
        zone["vms_text"] = vms_res.get("vms_text_en", zone.get("vms_text", ""))
        zone["vms_color"] = vms_res.get("led_color", "AMBER")
        zone["vms_speed_limit_kmh"] = vms_res.get("recommended_speed_limit", 30)
        zone["vms_manual_override"] = True
    return vms_res

@app.post("/api/ai/video-analyze")
def ai_video_analyze_endpoint(payload: Dict[str, Any]):
    """
    Multimodal video frame edge-AI analysis via Google Gemini 3.8 / Flash.
    Computes structural diagnostics, object bounding logs, severity score, and automated dispatch.
    """
    frame_b64 = payload.get("frame_base64")
    corridor = payload.get("corridor_name", "Silk Board Junction - Hosur Rd")
    mode = payload.get("feed_mode", "waterlogging")
    timestamp_sec = float(payload.get("timestamp_sec", 0.0))
    
    result = ai_engine.analyze_video_frame_gemini(
        frame_base64=frame_b64,
        corridor_name=corridor,
        feed_mode=mode,
        timestamp_sec=timestamp_sec
    )
    return result

@app.post("/api/ai/video-dispatch")
def ai_video_dispatch_endpoint(payload: Dict[str, Any]):
    """
    Executes automated municipal dispatch directly from Video AI Studio output.
    Injects high-priority ticket into BBMP / BTP dispatch queues with SLA timer.
    """
    global work_orders, system_log
    corridor = payload.get("corridor_name", "Silk Board Junction - Hosur Rd")
    severity = float(payload.get("severity_score", 0.88))
    order_type = payload.get("order_type", "Rapid Hydro-Jetting & Silt Clearance")
    action_notes = payload.get("action_notes", "Automated Gemini Video Edge-AI Triggered Dispatch")
    zone_id = payload.get("zone_id", "silk_board")
    
    zone = live_zone_state.get(zone_id, live_zone_state.get("silk_board", {}))
    wo_id = f"BBMP-WO-AI-{random.randint(100, 999)}"
    sla = 25 if severity > 0.8 else 45
    timestamp_str = datetime.now().strftime("%H:%M:%S")
    
    new_order = {
        "id": wo_id,
        "zone_id": zone_id,
        "zone_name": zone.get("name", corridor),
        "ward": zone.get("ward", "Ward 174"),
        "catch_basin_id": zone.get("catch_basin_id", "CB-FMCW-SB-102"),
        "action_required": order_type,
        "equipment_type": "10,000L Silt-Suction Jetting Tanker & De-watering Pump" if "Jetting" in order_type or "Silt" in order_type else "BTP Emergency Incident Response Vehicle",
        "crew_assigned": "Crew SuperSucker-AI (Rapid Response)",
        "priority": "CRITICAL" if severity > 0.75 else "HIGH",
        "status": "DISPATCHED",
        "sla_minutes": sla,
        "sla_remaining_min": sla,
        "reported_by": "Google Gemini 3.8 Multimodal Video Core",
        "created_at": timestamp_str,
        "notes": action_notes,
        "gemini_verified": True
    }
    work_orders.insert(0, new_order)
    
    # If accident or critical waterlogging, set alert / override VMS
    if payload.get("vms_highway_advisory_en"):
        zone["vms_text"] = payload.get("vms_highway_advisory_en")
        zone["vms_color"] = "RED" if severity > 0.8 else "AMBER"
        zone["vms_speed_limit_kmh"] = int(payload.get("recommended_speed_limit", 20))
        zone["vms_manual_override"] = True

    system_log.append(f"[{timestamp_str}] [GEMINI VIDEO AI DISPATCH] {order_type} mobilized for {corridor} (Severity: {severity:.2f}, Ticket: {wo_id}). SLA: {sla}m.")
    
    return {
        "status": "SUCCESS",
        "work_order": new_order,
        "message": f"Municipal unit dispatched to {corridor} successfully."
    }

@app.get("/api/ai/status")
def ai_status_endpoint():
    """
    Returns live health of the hardcoded Gemini AI engine and candidate models.
    """
    return {
        "status": "ONLINE",
        "engine": "Google Gemini 3.8 / Flash (Active)",
        "api_key_configured": True,
        "key_fingerprint": config.GEMINI_API_KEY[:6] + "..." + config.GEMINI_API_KEY[-4:],
        "primary_model": config.GEMINI_MODELS[0],
        "candidate_models": config.GEMINI_MODELS,
        "pipelines_active": [
            "Multimodal Citizen Photo Depth Estimation",
            "Anti-Spoofing & Depth Meniscus Optical Check",
            "ITMS Edge-AI 30 FPS Kinematic Collision Flagging",
            "Dynamic BBMP Work Order SLA Prioritization",
            "Real-Time Bilingual (EN/KN) Highway VMS Generation"
        ]
    }

# Serve Field Responder Portal (Prototype 3 Route on port 8000 as well)
@app.get("/responder", response_class=HTMLResponse)
@app.get("/field", response_class=HTMLResponse)
def serve_responder_portal():
    responder_path = os.path.join(os.path.dirname(__file__), "responder.html")
    if os.path.exists(responder_path):
        with open(responder_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Responder Portal HTML not found.</h1>"

# Serve the Single-Page Command Center (Prototype 1)
@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>HK-RHS Backend Online. Please ensure index.html is present in the root directory.</h1>"

# Also serve Citizen Portal on main host as an alternate route (Prototype 2 Route)
@app.get("/citizen", response_class=HTMLResponse)
@app.get("/portal", response_class=HTMLResponse)
def serve_citizen_portal():
    citizen_path = os.path.join(os.path.dirname(__file__), "citizen.html")
    if os.path.exists(citizen_path):
        with open(citizen_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Citizen Portal HTML not found.</h1>"

@app.get("/manifest.json")
def serve_manifest():
    path = os.path.join(os.path.dirname(__file__), "manifest.json")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/manifest+json")
    return {"name": "HK-RHS Suraksha"}

@app.get("/sw.js")
def serve_sw():
    path = os.path.join(os.path.dirname(__file__), "sw.js")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/javascript")
    return ""

@app.get("/{filename}.png")
def serve_png_images(filename: str):
    path = os.path.join(os.path.dirname(__file__), f"{filename}.png")
    if os.path.exists(path):
        return FileResponse(path, media_type="image/png")
    return HTMLResponse(status_code=404, content="Image not found")

if __name__ == "__main__":
    import uvicorn
    print("\n==========================================================================")
    print("  NAMMA BENGALURU - HK-RHS (Hydro-Kinetic Road Hazard System)")
    print("  REVA University HACKathon 3.0 | AI for Smart Cities & Sustainability")
    print("  Team: Team CyberSentinel / Apex Achievers (BMSIT)")
    print("  Team Members: Gagan N Prasad, Machal Ritesh Govardhan, Manav Redhu, Chimbili Manju Ganesh")
    print("==========================================================================")
    print("  UNIFIED MASTER SMART CITY HUB RUNNING ON SINGLE PORT 8000:")
    print("  -> http://127.0.0.1:8000           (Unified Master Command Center)")
    print("     Mode 1: ICCC Video Wall         (Full 3-Column Command Wall)")
    print("     Mode 2: Citizen Safety PWA      (AI Photo Verification & SOS)")
    print("     Mode 3: Field Responder Portal  (BBMP Desilting & BTP Tactical)")
    print("     Mode 4: Tri-Portal Split View   (Closed-Loop Multi-Agency Cockpit)")
    print("  -> Direct Standalone Routes:")
    print("     • http://127.0.0.1:8000/citizen")
    print("     • http://127.0.0.1:8000/responder")
    print("==========================================================================\n")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
