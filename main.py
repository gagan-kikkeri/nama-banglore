"""
Namma Bengaluru - HK-RHS (Hydro-Kinetic Road Hazard System)
REVA University HACKathon 3.0 (AI for Smart Cities & Sustainability)
Team: Apex Achievers (BMSIT)
Team Members:
  - Gagan N Prasad (Lead Architect)
  - Machal Ritesh Govardhan (Product Strategist)
  - Manav Redhu (Technical Operator)

FastAPI Backend Server & Real-time Simulation Engine:
  - 60/77 GHz FMCW Radar Telemetry inside catch-basin soffit behind tilted HDPE radome
  - Differential Inflow Index (ΔH) computation to isolate cloudbursts from physical blockages
  - ITMS Edge-AI Computer Vision Accident & Deceleration Spikes Detection
  - Automated BBMP Desilting Work Orders & Police/112 ICCC Dispatch
  - Citizen Safety Portal API with AI photo validation
"""

import os
import time
import math
import random
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(
    title="Namma Bengaluru - HK-RHS",
    description="Hydro-Kinetic Road Hazard System | REVA University HACKathon 3.0 | Team Apex Achievers (BMSIT)",
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

class WorkOrderUpdate(BaseModel):
    order_id: str
    status: str  # "EN_ROUTE", "IN_PROGRESS", "RESOLVED"

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
            "created_at": datetime.now().strftime("%H:%M:%S")
        }
    ]
    
    emergency_alerts = [
        {
            "id": "ICCC-ALT-109",
            "zone_id": "hebbal",
            "zone_name": "Hebbal Flyover",
            "type": "WEATHER_MONSOON_ADVISORY",
            "message": "Continuous precipitation observed. Catch-basin telemetry within safe margin (18% capacity).",
            "severity": "INFO",
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
    
    # Update VMS Sign Advisory based on Risk Score & Events
    if state["accident_detected"]:
        state["vms_text"] = "⚠️ ACCIDENT AHEAD IN LANE 1 & 2 • EMERGENCY TEAMS EN ROUTE • MERGE RIGHT • 20 KM/H"
        state["vms_color"] = "RED"
    elif state["hazard_classification"] == "SILT_DEBRIS_CLOG":
        state["vms_text"] = "⚠️ WATERLOGGING WARNING • DRAIN SILT CHOKE IN PROGRESS • SLOW DOWN • 30 KM/H"
        state["vms_color"] = "AMBER"
    elif state["hazard_classification"] == "CLOUDBURST_OVERLOAD":
        state["vms_text"] = "⛈️ MONSOON CLOUDBURST SURGE • HIGH WATER RESISTANCE • AVOID UNDERPASS"
        state["vms_color"] = "RED"
    elif state["risk_score"] > 0.65:
        state["vms_text"] = "CAUTION: RISING SURFACE WATER • KEEP SAFE DISTANCE • SPEED LIMIT 40 KM/H"
        state["vms_color"] = "AMBER"
    else:
        state["vms_text"] = "CORRIDOR CLEAR • MAINTAIN SAFE LANE DISTANCE • SPEED LIMIT 50 KM/H"
        state["vms_color"] = "GREEN"

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
            "name": "Apex Achievers (BMSIT)",
            "members": [
                {"name": "Gagan N Prasad", "role": "Lead Architect"},
                {"name": "Machal Ritesh Govardhan", "role": "Product Strategist"},
                {"name": "Manav Redhu", "role": "Technical Operator"}
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
    Accepts commuter hazard submissions, performs mock AI optical validation,
    and forwards confirmed incidents to the municipal queue.
    """
    timestamp_str = datetime.now().strftime("%H:%M:%S")
    zid = report.zone_id if report.zone_id in live_zone_state else "silk_board"
    zone = live_zone_state[zid]
    
    # Mock AI Optical Verification of commuter photo
    water_estimate = round(random.uniform(22.0, 38.0), 1)
    confidence = round(random.uniform(92.0, 98.5), 1)
    verification_msg = f"AI VISION VERIFIED (Estimated Inundation {water_estimate} cm, Confidence {confidence}%)"
    
    rep_id = f"CIT-REP-{random.randint(500, 999)}"
    record = {
        "id": rep_id,
        "reporter_name": report.reporter_name,
        "reporter_phone": report.reporter_phone,
        "zone_name": zone["name"],
        "hazard_type": report.hazard_type,
        "description": report.description,
        "lat": report.latitude,
        "lng": report.longitude,
        "timestamp": timestamp_str,
        "ai_verification": verification_msg,
        "status": "ESCALATED_TO_ICCC"
    }
    
    citizen_reports_list.insert(0, record)
    
    # Create an ICCC emergency alert
    new_alert = {
        "id": f"CIT-ALERT-{random.randint(100, 900)}",
        "zone_id": zid,
        "zone_name": zone["name"],
        "type": f"CITIZEN_{report.hazard_type.upper().replace(' ', '_')}",
        "message": f"Commuter report confirmed by AI Vision: {report.description[:60]}...",
        "severity": "WARNING",
        "timestamp": timestamp_str
    }
    emergency_alerts.insert(0, new_alert)
    
    system_log.append(f"[{timestamp_str}] [CITIZEN SAFETY] New report #{rep_id} from {report.reporter_name} at {zone['name']}. {verification_msg}")
    
    return {
        "status": "RECEIVED",
        "report_id": rep_id,
        "ai_analysis": {
            "verified": True,
            "estimated_hazard_depth_cm": water_estimate,
            "ai_confidence_pct": confidence,
            "action_taken": "Synced with BBMP Command Center"
        }
    }

@app.post("/api/workorders/update")
def update_work_order(update: WorkOrderUpdate):
    for wo in work_orders:
        if wo["id"] == update.order_id:
            wo["status"] = update.status
            timestamp_str = datetime.now().strftime("%H:%M:%S")
            system_log.append(f"[{timestamp_str}] [BBMP DISPATCH] Work Order {wo['id']} marked as {update.status}.")
            return {"status": "UPDATED", "work_order": wo}
    raise HTTPException(status_code=404, detail="Work order not found")

# Serve the Single-Page Command Center
@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>HK-RHS Backend Online. Please ensure index.html is present in the root directory.</h1>"

if __name__ == "__main__":
    import uvicorn
    print("\n==========================================================================")
    print("  NAMMA BENGALURU - HK-RHS (Hydro-Kinetic Road Hazard System)")
    print("  REVA University HACKathon 3.0 | AI for Smart Cities & Sustainability")
    print("  Team Apex Achievers (BMSIT)")
    print("==========================================================================")
    print("  Starting local server on: http://127.0.0.1:8000")
    print("==========================================================================\n")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
