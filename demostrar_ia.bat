@echo off
title Demostracion de Inteligencia Artificial - KompasAPPbeta
color 0B

echo ============================================================
echo   DEMOSTRACION DE PRACTICAS DE IA (P04 A P09) - KOMPAS
echo ============================================================
echo.

if exist "backend\app\main.py" (
    cd backend
)

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python -m scripts.demostracion_ia

echo.
pause

