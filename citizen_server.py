"""
Namma Bengaluru - HK-RHS (Hydro-Kinetic Road Hazard System)
REVA University HACKathon 3.0 (AI for Smart Cities & Sustainability)
Team: Team CyberSentinel / Apex Achievers (BMSIT)
Team Members:
  - Gagan N Prasad (Lead Architect)
  - Machal Ritesh Govardhan (Product Strategist)
  - Manav Redhu (Technical Operator)
  - Chimbili Manju Ganesh (UI/UX Designer)

Prototype 2: Citizen Safety & Reporting PWA / Web Portal Server
Dedicated Host: http://127.0.0.1:8001
"""

import os
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

citizen_app = FastAPI(
    title="Namma Bengaluru - HK-RHS Citizen Safety PWA",
    description="Citizen Safety & Hazard Reporting Portal | REVA University HACKathon 3.0 | Team CyberSentinel / Apex Achievers (BMSIT)",
    version="1.0.0"
)

citizen_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@citizen_app.get("/", response_class=HTMLResponse)
@citizen_app.get("/citizen", response_class=HTMLResponse)
@citizen_app.get("/portal", response_class=HTMLResponse)
def serve_citizen_portal():
    path = os.path.join(BASE_DIR, "citizen.html")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Citizen Portal HTML not found.</h1>"

@citizen_app.get("/manifest.json")
def get_manifest():
    path = os.path.join(BASE_DIR, "manifest.json")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/manifest+json")
    return {"name": "HK-RHS Citizen Portal"}

@citizen_app.get("/sw.js")
def get_service_worker():
    path = os.path.join(BASE_DIR, "sw.js")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/javascript")
    return Response(content="", media_type="application/javascript")

# Serve media files directly on root if requested by preview
@citizen_app.get("/{filename}.png")
def get_png(filename: str):
    path = os.path.join(BASE_DIR, f"{filename}.png")
    if os.path.exists(path):
        return FileResponse(path, media_type="image/png")
    return Response(status_code=404)

if __name__ == "__main__":
    print("\n==========================================================================")
    print("  NAMMA BENGALURU - HK-RHS (Hydro-Kinetic Road Hazard System)")
    print("  PROTOTYPE 2: CITIZEN SAFETY & REPORTING PWA")
    print("  REVA University HACKathon 3.0 | AI for Smart Cities & Sustainability")
    print("  Team: Team CyberSentinel / Apex Achievers (BMSIT)")
    print("==========================================================================")
    print("  Serving Citizen Portal at: http://127.0.0.1:8001")
    print("  Syncing with ICCC Host at: http://127.0.0.1:8000")
    print("==========================================================================\n")
    uvicorn.run("citizen_server:citizen_app", host="127.0.0.1", port=8001, reload=True)
