@echo off
REM Auto Claude Safe Sync - Bombensichere Version
REM Direkt ausfuehrbar via Desktop-Icon

echo.
echo ====================================================================
echo   AUTO CLAUDE - SAFE SYNC MIT GITHUB
echo ====================================================================
echo.
echo [INFO] Starte Auto Claude mit automatischem GitHub Pull...
echo.

cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -NoExit -Command "& '%~dp0Start-Auto-Claude-With-Sync-v2.ps1'"

if errorlevel 1 (
    echo.
    echo [ERROR] Fehler beim Start!
    echo.
    pause
)
