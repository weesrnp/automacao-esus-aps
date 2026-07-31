@echo off
chcp 65001 > nul
echo ===================================================
echo   ATUALIZANDO AUTOMAÇÃO ESUS APS (GIT PULL)
echo ===================================================

cd /d "%~dp0"

echo.
echo -> Verificando novas atualizações no GitHub...
git pull origin master

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===================================================
    echo   [OK] ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!
    echo ===================================================
) else (
    echo.
    echo ===================================================
    echo   ! ERRO AO ATUALIZAR. Verifique sua conexão.
    echo ===================================================
)

echo.
pause
