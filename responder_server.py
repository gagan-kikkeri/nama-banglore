"""
Namma Bengaluru - HK-RHS (Hydro-Kinetic Road Hazard System)
REVA University HACKathon 3.0 (AI for Smart Cities & Sustainability)
Team: Team CyberSentinel / Apex Achievers (BMSIT)
Team Members:
  - Gagan N Prasad (Lead Architect)
  - Machal Ritesh Govardhan (Product Strategist)
  - Manav Redhu (Technical Operator)
  - Chimbili Manju Ganesh (UI/UX Designer)

Prototype 3: Field Responder & Municipal Operative Portal Server
Dedicated Host: http://127.0.0.1:8002
"""

import os
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

responder_app = FastAPI(
    title="Namma Bengaluru - HK-RHS Field Responder Portal",
    description="Field Responder & Municipal Operative Portal | REVA University HACKathon 3.0 | Team CyberSentinel / Apex Achievers (BMSIT)",
    version="1.0.0"
)

responder_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@responder_app.get("/", response_class=HTMLResponse)
@responder_app.get("/responder", response_class=HTMLResponse)
@responder_app.get("/field", response_class=HTMLResponse)
def serve_responder_portal():
    path = os.path.join(BASE_DIR, "responder.html")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Field Responder Portal HTML not found.</h1>"

@responder_app.get("/manifest.json")
def get_manifest():
    path = os.path.join(BASE_DIR, "manifest.json")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/manifest+json")
    return {"name": "HK-RHS Field Responder"}

@responder_app.get("/sw.js")
def get_service_worker():
    path = os.path.join(BASE_DIR, "sw.js")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/javascript")
    return Response(content="", media_type="application/javascript")

@responder_app.get("/{filename}.png")
def get_png(filename: str):
    path = os.path.join(BASE_DIR, f"{filename}.png")
    if os.path.exists(path):
        return FileResponse(path, media_type="image/png")
    return Response(status_code=404)

if __name__ == "__main__":
    print("\n==========================================================================")
    print("  NAMMA BENGALURU - HK-RHS (Hydro-Kinetic Road Hazard System)")
    print("  PROTOTYPE 3: FIELD RESPONDER & MUNICIPAL OPERATIVE PORTAL")
    print("  REVA University HACKathon 3.0 | AI for Smart Cities & Sustainability")
    print("  Team: Team CyberSentinel / Apex Achievers (BMSIT)")
    print("==========================================================================")
    print("  Serving Field Responder Portal at: http://127.0.0.1:8002")
    print("  Bidirectional Sync with ICCC at:  http://127.0.0.1:8000")
    print("==========================================================================\n")
    uvicorn.run("responder_server:responder_app", host="127.0.0.1", port=8002, reload=True)
