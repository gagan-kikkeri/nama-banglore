@echo off
title Namma Bengaluru - HK-RHS Command Center
color 0B
echo =========================================================================
echo    NAMMA BENGALURU - HK-RHS (Hydro-Kinetic Road Hazard System)
echo    REVA University HACKathon 3.0 ^| AI for Smart Cities ^& Sustainability
echo    Team: Apex Achievers (BMSIT)
echo =========================================================================
echo.
echo [1/2] Checking Python environment...
python --version
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b
)

echo.
echo [2/2] Launching HK-RHS ICCC Backend and Command Center...
echo Serving at: http://127.0.0.1:8000
echo Opening web browser in 3 seconds...
start "" http://127.0.0.1:8000
echo.
python main.py
pause
