@echo off
title KompasAPPbeta - Servidor Backend FastAPI
color 0A

echo ============================================================
echo           KOMPAS APP BETA - INICIO DEL BACKEND
echo ============================================================
echo.

if exist "app\main.py" (
    goto INICIAR
)

if exist "backend\app\main.py" (
    cd backend
    goto INICIAR
)

echo [ERROR] No se encontro app\main.py.
pause
exit /b 1

:INICIAR
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activando entorno virtual venv...
    call venv\Scripts\activate.bat
)

echo.
echo [INFO] Direccion IP local para app/.env:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    echo    - http:%%a:8000
)
echo.
echo ============================================================
echo  Documentacion interactiva Swagger: http://localhost:8000/docs
echo  Modulo de IA y Machine Learning:  http://localhost:8000/docs#/ia_kompas
echo ============================================================
echo.
start http://localhost:8000/docs

echo [INFO] Iniciando servidor Uvicorn en http://0.0.0.0:8000...
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] El servidor se detuvo con codigo de error %errorlevel%.
    pause
)

