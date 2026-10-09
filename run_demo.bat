@echo off
title Namma Bengaluru - HK-RHS Unified Master Platform
color 0B
echo =========================================================================
echo    NAMMA BENGALURU - HK-RHS (Hydro-Kinetic Road Hazard System)
echo    REVA University HACKathon 3.0 ^| AI for Smart Cities ^& Sustainability
echo    Team: Team CyberSentinel / Apex Achievers (BMSIT)
echo    Team Members:
echo      - Gagan N Prasad (Lead Architect)
echo      - Machal Ritesh Govardhan (Product Strategist)
echo      - Manav Redhu (Technical Operator)
echo      - Chimbili Manju Ganesh (UI/UX Designer)
echo =========================================================================
echo.
echo [1/3] Checking Python environment...
python --version
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b
)

echo.
echo [2/3] Unified Master Platform Architecture:
echo   - Master Single-Port Hub:     http://127.0.0.1:8000
echo   - Mode 1: ICCC Video Wall     (Command & Control Center)
echo   - Mode 2: Citizen Portal      (Safety PWA & AI Depth Estimator)
echo   - Mode 3: Field Responder     (BBMP & Traffic Police Tactical Console)
echo   - Mode 4: Tri-Portal Split    (Multi-Agency Closed-Loop Cockpit)
echo.
echo [3/3] Launching HK-RHS Unified Engine on Port 8000...
start "" "http://127.0.0.1:8000"
python main.py
pause
