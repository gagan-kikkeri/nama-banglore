"""
Namma Bengaluru - HK-RHS (Hydro-Kinetic Road Hazard System)
REVA University HACKathon 3.0 (AI for Smart Cities & Sustainability)
Team: Team CyberSentinel / Apex Achievers (BMSIT)
Team Members:
  - Gagan N Prasad (Lead Architect)
  - Machal Ritesh Govardhan (Product Strategist)
  - Manav Redhu (Technical Operator)
  - Chimbili Manju Ganesh (UI/UX Designer)

Triple-Host Multi-Process Runner:
  - Prototype 1 (ICCC Dashboard):         http://127.0.0.1:8000
  - Prototype 2 (Citizen Safety PWA):     http://127.0.0.1:8001
  - Prototype 3 (Field Responder Portal): http://127.0.0.1:8002
"""

import sys
import time
import webbrowser
import threading
import uvicorn

def run_iccc_server():
    print("[ICCC HOST] Starting Integrated Command & Control Center on http://127.0.0.1:8000 ...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="warning")

def run_citizen_server():
    print("[CITIZEN HOST] Starting Citizen Safety PWA Portal on http://127.0.0.1:8001 ...")
    uvicorn.run("citizen_server:citizen_app", host="127.0.0.1", port=8001, log_level="warning")

def run_responder_server():
    print("[RESPONDER HOST] Starting Field Responder Portal on http://127.0.0.1:8002 ...")
    uvicorn.run("responder_server:responder_app", host="127.0.0.1", port=8002, log_level="warning")

def open_browsers():
    time.sleep(2.0)
    print("\n[BROWSER] Opening Triple Prototypes for Live Demonstration...")
    print("  -> Opening Prototype 1 (ICCC Dashboard) on http://127.0.0.1:8000 ...")
    webbrowser.open("http://127.0.0.1:8000")
    time.sleep(1.2)
    print("  -> Opening Prototype 2 (Citizen Safety PWA) on http://127.0.0.1:8001 ...")
    webbrowser.open("http://127.0.0.1:8001")
    time.sleep(1.2)
    print("  -> Opening Prototype 3 (Field Responder Portal) on http://127.0.0.1:8002 ...")
    webbrowser.open("http://127.0.0.1:8002")

if __name__ == "__main__":
    print("\n==========================================================================")
    print("  NAMMA BENGALURU - HK-RHS (Hydro-Kinetic Road Hazard System)")
    print("  REVA University HACKathon 3.0 | AI for Smart Cities & Sustainability")
    print("  Team: Team CyberSentinel / Apex Achievers (BMSIT)")
    print("==========================================================================")
    print("  PROTOTYPE 1 (ICCC Dashboard):         http://127.0.0.1:8000")
    print("  PROTOTYPE 2 (Citizen PWA Portal):     http://127.0.0.1:8001")
    print("  PROTOTYPE 3 (Field Responder Portal): http://127.0.0.1:8002")
    print("  Cross-Host Bidirectional Sync:        ACTIVE (Full Tri-Portal Closed Loop)")
    print("==========================================================================\n")

    t1 = threading.Thread(target=run_iccc_server, daemon=True)
    t2 = threading.Thread(target=run_citizen_server, daemon=True)
    t3 = threading.Thread(target=run_responder_server, daemon=True)
    t_browser = threading.Thread(target=open_browsers, daemon=True)

    t1.start()
    t2.start()
    t3.start()
    t_browser.start()

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nShutting down HK-RHS triple prototype servers. Goodbye!")
        sys.exit(0)
