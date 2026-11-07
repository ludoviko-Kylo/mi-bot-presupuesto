@echo off
chcp 65001 >nul
title Bot de Presupuesto Personal - Telegram

:: Asegurar que el directorio actual sea la carpeta de este archivo
cd /d "%~dp0"

echo ============================================================
echo   INICIANDO BOT DE PRESUPUESTO PERSONAL (TELEGRAM)
echo ============================================================
echo.

:: Verificar si existe el ejecutable de Python en el entorno virtual
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo [ERROR] No se encontro Python en la carpeta .venv.
    echo Asegurate de que la carpeta .venv este presente.
    echo.
    pause
    exit /b 1
)

:: Ejecutar directamente con el Python del entorno virtual
echo [*] Usando entorno virtual (.venv)...
echo [*] Ejecutando main.py...
echo.

"%~dp0.venv\Scripts\python.exe" -u "%~dp0main.py"

:: Si el bot se detiene, no cerrar la ventana de golpe
echo.
echo ============================================================
echo [*] El bot se ha detenido.
echo ============================================================
pause
