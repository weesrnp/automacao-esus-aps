@echo off
chcp 65001 > nul
echo ===================================================
echo   ENCERRANDO AUTOMACAO ESUS APS
echo ===================================================

echo Parar automacao > "%~dp0PARAR.txt"
echo [OK] Sinal de parada enviado (PARAR.txt criado).

wmic process where "name='python.exe' and commandline like '%%main_automacao%%'" call terminate > nul 2>&1
echo [OK] Processos de automacao finalizados.

echo.
echo ===================================================
echo   AUTOMACAO PARADA COM SUCESSO!
echo ===================================================
timeout /t 3 > nul
