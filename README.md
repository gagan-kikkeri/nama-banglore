# Namma Bengaluru - HK-RHS (Hydro-Kinetic Road Hazard System)
**REVA University HACKathon 3.0 (AI for Smart Cities & Sustainability)**  
**Team Apex Achievers (BMSIT)**

---

### Team Members
- **Gagan N Prasad** — Lead Architect
- **Machal Ritesh Govardhan** — Product Strategist
- **Manav Redhu** — Technical Operator

---

## 🌟 Executive Summary & Core Innovation

Namma Bengaluru suffers severe dual arterial crises during monsoon spells: catastrophic urban waterlogging and high-speed collision blockages across critical junctions (Silk Board, Outer Ring Road, Hebbal Flyover, Majestic). 

**HK-RHS solves this with zero new civil excavation:**
1. **Infrastructure Reuse:** Repurposes existing **Bengaluru Traffic Police (BTP) ITMS** speed camera poles and on-premise edge computing units for real-time edge computer vision inference.
2. **Corrosion-Immune Sensing Stack:** Mounts **60/77 GHz FMCW millimeter-wave radar** inside catch-basin neck soffits behind a **2–4 mm tilted, recycled HDPE radome window**, isolating corrosive sewer gases ($H_2S$, methane) and humidity while maintaining radar transparency.
3. **Differential Inflow Index ($\Delta H$):** An analytical hydrodynamic formula that mathematically distinguishes between **macro cloudburst runoff overload** and **physical silt/debris blockages**:
   $$\Delta H = \frac{\partial h_{\text{basin}}}{\partial t} - \alpha \cdot R(t)$$
4. **Automated Municipal Dispatch:** Connects the **Integrated Command and Control Center (ICCC)** directly to **BBMP stormwater desilting crews**, dynamic roadside **Variable Message Signs (VMS)**, and emergency **112 / BTP units**.
5. **Citizen Safety Portal:** Mobile web interface allowing commuters to report road hazards with 1-tap geo-tagging and AI photo verification.

---

## 🚀 Quick Start Guide (How to Run Locally)

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Web Browser (Chrome, Edge, Firefox)

### 2. Install Dependencies (if not already installed)
```bash
pip install fastapi uvicorn pydantic
```

### 3. Launch the HK-RHS System
In this directory (`c:\Users\TUF\OneDrive\Desktop\hackathon 3.0`), run:
```bash
python main.py
```
*Or using Uvicorn directly:*
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 4. Open the Command Center
Open your browser and navigate to:
```
http://127.0.0.1:8000
```

---

## 🎯 Live Demonstration Guide for Judges

In the dashboard, scroll down to the **Hackathon Evaluation Mode / Live Demonstration Triggers** panel:

| Scenario Button | What it Simulates | What the Judges See |
|---|---|---|
| **1. Silt/Debris Clog (Silk Board)** | Spikes $\Delta H = 2.45$ under moderate rainfall ($18\text{ mm/hr}$). | Algorithm diagnoses **Physical Silt Choke** $\rightarrow$ Automatically issues and routes a **BBMP Hydro-Vacuum Desilting Work Order** with a 25-minute SLA. |
| **2. Monsoon Cloudburst (Hebbal)** | Surges rainfall to $92\text{ mm/hr}$ with uniform balanced rise. | Algorithm diagnoses **Macro Cloudburst Overload** $\rightarrow$ Activates 500 GPM dewatering pumps and flips highway VMS to Red Flood Diversion. |
| **3. High-Speed Crash (ORR Bellandur)** | Simulated multi-vehicle collision detected by ITMS camera. | Edge-AI CV flags $-6.8\text{ m/s}^2$ deceleration spike and carriageway obstruction $\rightarrow$ Dispatches BTP Patrol & 112 emergency response. |
| **4. Normalize System** | Resets all telemetry to standard monsoon baseline. | Clear status, green VMS advisories, normal drainage metrics. |
| **Citizen Safety Portal** | Click **Citizen Portal** in the top header. | Fill out a hazard report, click photo to trigger AI water depth verification (~32 cm), and submit to watch it sync directly into the ICCC dispatch queue! |

---

## 📁 Project Structure
- `main.py` — FastAPI backend, FMCW radar physics engine, $\Delta H$ calculation, Edge-AI simulator, and dispatch queue.
- `index.html` — Responsive Dark-Mode ICCC Dashboard with Leaflet map, Chart.js telemetry graphs, ITMS camera feed HUD, Dynamic VMS simulator, and Citizen Safety PWA.
- `README.md` — Project architecture documentation and demo instructions.
