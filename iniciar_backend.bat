@echo off
title KompasAPPbeta - Servidor Backend FastAPI
color 0A

echo ============================================================
echo           KOMPAS APP BETA - INICIO DEL BACKEND
echo ============================================================
echo.

:: Detectar directorio de trabajo
if exist "backend\app\main.py" (
    cd backend
)

if not exist "app\main.py" (
    echo [ERROR] No se encontro la aplicacion backend.
    echo Asegurate de ejecutar este archivo desde la raiz de KompasAPPbeta o la carpeta backend.
    pause
    exit /b 1
)

:: Verificar entorno virtual
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activando entorno virtual venv...
    call venv\Scripts\activate.bat
) else (
    echo [ADVERTENCIA] No se encontro la carpeta venv local. Se intentara usar el Python del sistema.
)

:: Mostrar IPs disponibles para conexion de la app movil
echo.
echo [INFO] Direccion IP local para configurar en app/.env (EXPO_PUBLIC_API_URL):
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    echo    - http:%%a:8000
)
echo.
echo ============================================================
echo  Documentacion interactiva Swagger: http://localhost:8000/docs
echo  Modulo de IA y Machine Learning:  http://localhost:8000/docs#/ia_kompas
echo ============================================================
echo.
echo [INFO] Abriendo documentacion de IA en el navegador...
start http://localhost:8000/docs

echo [INFO] Iniciando servidor Uvicorn en http://0.0.0.0:8000...
echo Presiona CTRL + C para detener el servidor.
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] El servidor se detuvo con codigo de error %errorlevel%.
    pause
)

