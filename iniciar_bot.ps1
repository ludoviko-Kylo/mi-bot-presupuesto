# Script de inicio para PowerShell
$Host.UI.RawUI.WindowTitle = "Bot de Presupuesto Personal - Telegram"

$scriptDir = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
Set-Location -Path $scriptDir

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  INICIANDO BOT DE PRESUPUESTO PERSONAL (TELEGRAM)         " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"
$mainPy = Join-Path $scriptDir "main.py"

if (-not (Test-Path $venvPython)) {
    Write-Host "[ERROR] No se encontro Python en el entorno virtual .venv." -ForegroundColor Red
    Write-Host "Asegurate de que la carpeta .venv este presente." -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host "[*] Usando entorno virtual (.venv)..." -ForegroundColor Green
Write-Host "[*] Ejecutando main.py..." -ForegroundColor Green
Write-Host ""

& $venvPython -u $mainPy

Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "[*] El bot se ha detenido." -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Read-Host "Presiona Enter para salir"

