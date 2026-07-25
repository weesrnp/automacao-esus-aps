@echo off
chcp 65001 > nul
echo ===================================================
echo   INICIANDO AUTOMACAO ESUS APS
echo ===================================================

if exist "%~dp0PARAR.txt" del /f /q "%~dp0PARAR.txt"

cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe main_automacao.py
) else (
    python main_automacao.py
)

pause
