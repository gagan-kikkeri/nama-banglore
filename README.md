# Namma Bengaluru - HK-RHS (Hydro-Kinetic Road Hazard System)
**REVA University HACKathon 3.0 (AI for Smart Cities & Sustainability)**  
**Team: Team CyberSentinel / Apex Achievers (BMSIT)**

---

### 👥 Team Members
- **Gagan N Prasad** — Lead Architect
- **Machal Ritesh Govardhan** — Product Strategist
- **Manav Redhu** — Technical Operator
- **Chimbili Manju Ganesh** — UI/UX Designer

---

## 🌟 Executive Summary: Unified Master Platform Architecture (Single Port 8000)

Namma Bengaluru suffers severe dual arterial crises during monsoon spells: catastrophic urban waterlogging and high-speed collision blockages across critical corridors (Silk Board, Outer Ring Road, Hebbal Flyover, Whitefield, Majestic, K.R. Puram, Goraguntepalya).

**HK-RHS** addresses this with **zero new civil excavation** through a **Single Unified Master Web Application** hosted on `http://127.0.0.1:8000` featuring seamless 1-click switching and live Tri-Portal Split Screen demonstration:

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   HK-RHS UNIFIED MASTER PLATFORM (http://127.0.0.1:8000)                  │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  [🖥️ Mode 1: ICCC Video Wall]   [📱 Mode 2: Citizen PWA]   [🚒 Mode 3: Field Responder]  │
│                                [⚡ Mode 4: Tri-Portal Split View]                        │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  MODE 1: ICCC Command Center Video Wall                                                  │
│  • 60/77 GHz FMCW Millimeter-Wave Radar Telemetry & HDPE Radome Window Isolation         │
│  • Differential Inflow Index (ΔH = ∂h/∂t - αR) Catch-Basin Choke Isolation               │
│  • ITMS Edge-AI Optical Kinematics & High-Speed Deceleration Collision Flagging         │
│  • Clickable KPI Inspector Modals with Live SLA Timers & Diagnostic Audit Log            │
│                                                                                          │
│  MODE 2: Citizen Safety & Hazard PWA Portal (/citizen)                                   │
│  • 1-Tap Commuter Waterlogging & Accident Geo-Reporting with AI Photo Depth Estimator    │
│  • Live Risk Heatmap across Bengaluru's 6 Key Arterial Corridors                         │
│                                                                                          │
│  MODE 3: Field Responder & Municipal Dispatch Console (/responder)                      │
│  • BBMP Stormwater Wing: Hydro-Jetting Dispatches with SLA Timers & "Mark Done" action   │
│  • BTP Traffic Police: Real-Time Dynamic VMS Message Override & Cordon Management       │
│                                                                                          │
│  MODE 4: Tri-Portal Multi-Agency Closed-Loop Cockpit                                     │
│  • Side-by-side synchronized live view of ICCC, Citizen App, and Tactical Console        │
│  • 4-step closed-loop trigger suite (Cloudburst -> Citizen SOS -> Crew Resolved -> Clear)│
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏛️ Triple-Host Architectural Breakdown

### 1. Prototype 1: Main ICCC Command Center Dashboard
- **Host:** `http://127.0.0.1:8000`
- **Municipal Oversight:** Real-time citywide resilience monitoring across 6 critical Bengaluru arterial corridors.
- **Corrosion-Immune Sensing Stack:** 60/77 GHz FMCW millimeter-wave radar inside catch-basin soffits behind tilted 3.2mm HDPE radome windows, isolating harsh sewer gases ($H_2S$, $CH_4$) and moisture.
- **Hydro-Kinetic Physics Engine ($\Delta H$):**
  $$\Delta H = \frac{\partial h_{\text{basin}}}{\partial t} - \alpha \cdot R(t)$$
  - $\Delta H > 0.80$ with moderate rain $\rightarrow$ **Physical Silt / Debris Choke Anomaly**.
  - High $R(t) > 60\text{ mm/hr}$ with balanced $\Delta H$ $\rightarrow$ **Macro Regional Cloudburst Overload**.
- **Edge-AI Collision Detection:** Repurposes existing BTP ITMS camera infrastructure for 30 FPS vehicle kinematics and $-6.8\text{ m/s}^2$ deceleration spike flagging.
- **Automated Dispatch:** Instantly generates BBMP work orders and alerts emergency 112 responders.

---

### 2. Prototype 2: Citizen Safety & Reporting PWA Portal
- **Host:** `http://127.0.0.1:8001` (also accessible via `http://127.0.0.1:8000/citizen`)
- **Mobile-Responsive Native PWA:** Designed for smartphone commuters with installable manifest, service worker cache, and bilingual Kannada/English branding.
- **1-Tap Incident Submission:** Waterlogging, Collisions, Potholes, and Drainage overflows.
- **On-Device AI Verification:** Simulates MobileNetV3/WaterSeg optical depth estimation (~34.2 cm) with anti-spoof authenticity verification (98.6%).
- **Live Ticket Tracker:** Real-time status progression from `RECEIVED` $\rightarrow$ `DISPATCHED_TO_BBMP` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `RESOLVED`.
- **Instant Cross-Host Sync:** Submitting a hazard automatically pings the ICCC Dashboard on port 8000, creating an active work order and triggering an audible/visual sync toast.

---

### 3. Prototype 3: Field Responder & Municipal Operative Portal
- **Host:** `http://127.0.0.1:8002` (also accessible via `http://127.0.0.1:8000/responder`)
- **Role-Based Authentication & View Switcher:**
  1. **BBMP Desilting Crews (Quick Reaction Silt-Suction Unit #14):**
     - Geo-fenced drainage work orders queue with live SLA countdown timers.
     - Live Catch-basin $\Delta H$ choke telemetry cards with mathematical diagnosis.
     - Desilting Priority Routing Map with GPS shortest-path calculation.
     - 1-tap "En Route", "Arrived / Hydro-Jetting", and "1-Tap Sump Cleared & Verified" modal (records slurry volume extracted and resets basin blockage across all hosts).
  2. **Police / Emergency 112 Dispatchers (KSP / BTP Dial 112 Tactical Console):**
     - Dedicated tactical feed for Edge-AI computer vision collision alerts.
     - Exact accident coordinates, ITMS pole ID, $-6.8\text{ m/s}^2$ deceleration metrics, and blocked lanes.
     - Nearest emergency responder routing table (BTP Patrol #09, 108 Ambulance Unit #18, Heavy Recovery Crane #04).
     - Simulated night/rain camera video feed with optical bounding box HUD overlays (`[COLLISION_ALERT]`, `[DECEL: -6.8 m/s²]`, `[FPS: 29.8]`).
     - 1-tap Tactical Commands: "Acknowledge Collision", "Dispatch 108 Ambulance + Patrol", "Cordon Lanes 1 & 2", and "Incident Cleared & Traffic Restored".
  3. **BTP Traffic Inspectors (Bengaluru Traffic Police ITMS Division):**
     - Control panel for managing dynamic Variable Message Signs (VMS) across all 6 corridors.
     - Overhead LED Gantry Matrix Display Simulator with glowing amber/red/green matrix typography.
     - 1-click Preset Advisories ("Corridor Clear", "Drain Silt Choke Warning", "Severe Cloudburst Flooding", "Accident Ahead / Merge Right").
     - Highway Speed Limit Advisories controls (Instant overrides: 20, 30, 40, 50, 60 km/h).
     - Emergency Traffic Diversion Corridors controls (Toggle regional diversion routing).
     - 1-tap "Broadcast to Highway Gantries & ICCC" which immediately pushes live overrides to Prototype 1!

---

## ⚡ Real-Time Bidirectional Synchronization & Closed-Loop Automation

The HK-RHS platform showcases true closed-loop smart city automation:

1. **Municipal Closed Loop:**
   - Silt choke injected on Port 8000 $\rightarrow$ Instantly appears on BBMP Crew feed on Port 8002.
   - Crew taps "1-Tap Sump Cleared" on Port 8002 $\rightarrow$ Immediately clears the work order, normalizes catch-basin $\Delta H$ back to 0.12, resets risk score to 0.18, and marks the citizen ticket on Port 8001 as `RESOLVED`.
2. **Emergency 112 Closed Loop:**
   - Collision detected by ITMS on Port 8000 $\rightarrow$ Flashes red on Police 112 feed on Port 8002.
   - Dispatcher cordons lanes $\rightarrow$ Overhead highway VMS turns red on all screens.
   - Dispatcher marks "Traffic Restored" $\rightarrow$ Carriageway speed normalizes to 45 km/h and alert clears across all dashboards.
3. **BTP VMS Dynamic Push:**
   - Inspector overrides speed limit or diversion on Port 8002 $\rightarrow$ Instantly reflected on the ICCC Command Center's live corridor wall on Port 8000.

---

## 🚀 Quick Start Guide (How to Run Locally)

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.12 / 3.14)
- Modern Web Browser (Chrome, Edge, Firefox)

### 2. Install Dependencies
```bash
pip install fastapi uvicorn pydantic
```

### 3. Launch All 3 Prototypes Concurrently
Double-click `run_demo.bat` or run in terminal:
```bash
python run_triple_hosts.py
```
This automatically starts:
- **Prototype 1 (ICCC Dashboard):** `http://127.0.0.1:8000`
- **Prototype 2 (Citizen Safety PWA):** `http://127.0.0.1:8001`
- **Prototype 3 (Field Responder Portal):** `http://127.0.0.1:8002`
- And automatically opens all three browser tabs for live demonstration!

*Alternatively, launch servers individually:*
```bash
# Terminal 1: Prototype 1 (ICCC Dashboard)
python main.py

# Terminal 2: Prototype 2 (Citizen Portal)
python citizen_server.py

# Terminal 3: Prototype 3 (Field Responder Portal)
python responder_server.py
```

---

## 🎯 Step-by-Step Demonstration Script for Judges (HACKathon 3.0 Pitch)

### Step 1: Arrange the 3 Screens
- Open **Prototype 1 (ICCC Dashboard)** on `http://127.0.0.1:8000` on the main screen.
- Open **Prototype 2 (Citizen Portal)** on `http://127.0.0.1:8001` on a mobile window.
- Open **Prototype 3 (Field Responder Portal)** on `http://127.0.0.1:8002` on a third window.

### Step 2: Citizen Hazard Submission $\rightarrow$ ICCC $\rightarrow$ BBMP Field Crew
1. On **Prototype 2 (`:8001`)**: Select **Waterlogging**, choose **📍 Silk Board**, click **Load Flood Scene** (watch AI scan ~34.8 cm depth), and tap **1-TAP SUBMIT TO BBMP ICCC**.
2. On **Prototype 1 (`:8000`)**: Observe the **⚡ CROSS-HOST TELEMETRY SYNC** toast pop up and the new work order `#BBMP-WO-xxxx` enter the dispatch queue.
3. On **Prototype 3 (`:8002`)**: Under **BBMP Desilting Crew**, observe the new ticket appear in real time with high priority, route map, and SLA countdown!
4. Tap **Set En Route**, then tap **1-Tap Sump Cleared & Verified** (enter 1850L slurry extracted).
5. Watch **Prototype 1 (`:8000`)** and **Prototype 2 (`:8001`)** immediately show the ticket marked **RESOLVED** with zero manual reloading!

### Step 3: Edge-AI Collision Detection $\rightarrow$ Police 112 Tactical Response
1. On **Prototype 1 (`:8000`)**: Click **💥 Collision** under Incident Simulation Controls.
2. The corridor turns red, displaying a $-6.8\text{ m/s}^2$ deceleration impact.
3. Switch to **Prototype 3 (`:8002`)** and click **Police / 112 Dispatch**:
   - Hear the synthesized tactical audio alert.
   - Inspect the ITMS Optical HUD showing bounding boxes (`OBJ #1: STALLED`, `OBJ #2: IMPACT`).
   - View nearest emergency units (BTP Patrol #09: 0.8 km • 2m ETA, 108 EMS: 1.7 km • 4m ETA).
   - Click **Cordon Lanes 1 & 2** $\rightarrow$ Overhead VMS switches to RED merge advisory.
   - Click **Restore Traffic & Clear** $\rightarrow$ Accident clears, traffic speed restores to 45 km/h on Prototype 1!

### Step 4: BTP Traffic Inspector Dynamic VMS Override
1. On **Prototype 3 (`:8002`)**: Switch to **BTP Traffic Inspector**.
2. Select **Hebbal Flyover** or **Bellandur EcoSpace**.
3. Click preset **🟡 Silt Choke Warning (30 km/h)** and tap **1-TAP BROADCAST TO HIGHWAY GANTRY**.
4. Observe the authentic LED Gantry Simulator render the glowing amber text.
5. Switch to **Prototype 1 (`:8000`)**: Notice the VMS card on Hebbal immediately update to show the Inspector's advisory and speed limit!

---

## 📁 Repository Structure

```
hackathon 3.0/
├── main.py              # Prototype 1 FastAPI Backend, FMCW Radar Physics, ΔH Calculation, ITMS Edge-AI Engine, ICCC Dashboard
├── index.html           # Prototype 1 ICCC Dashboard (Leaflet Dark Map, Chart.js Waveforms, 4 Modal Inspectors, VMS Display)
├── citizen_server.py    # Prototype 2 Dedicated Server on Port 8001
├── citizen.html         # Prototype 2 Citizen Safety PWA (Mobile-First UI, 1-Tap Form, On-Device AI Scanner, Live Tracker)
├── responder_server.py  # Prototype 3 Dedicated Server on Port 8002
├── responder.html       # Prototype 3 Field Responder Portal (BBMP Crew, Police 112, BTP Inspector Console, LED Simulator)
├── manifest.json        # PWA Web App Manifest
├── sw.js                # PWA Service Worker for offline resilience
├── run_triple_hosts.py  # Multi-host concurrent runner for all 3 prototypes
├── run_dual_hosts.py    # Multi-host runner (aliased for backwards compatibility)
├── run_demo.bat         # 1-Click launcher script for Windows
├── README.md            # Comprehensive documentation & pitch evaluation walkthrough
```

---

## 🏆 Hackathon Submission Details
- **Event:** REVA University HACKathon 3.0 (AI for Smart Cities & Sustainability)
- **Institution:** BMS Institute of Technology and Management (BMSIT), Bengaluru
- **Team Name:** Team CyberSentinel / Apex Achievers
- **Team Members:**
  1. Gagan N Prasad (Lead Architect)
  2. Machal Ritesh Govardhan (Product Strategist)
  3. Manav Redhu (Technical Operator)
  4. Chimbili Manju Ganesh (UI/UX Designer)
