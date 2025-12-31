@echo off
REM Auto Claude Safe Sync - OHNE Pull (fuer Offline/Tests)

echo.
echo ====================================================================
echo   AUTO CLAUDE - SAFE SYNC (OHNE GITHUB PULL)
echo ====================================================================
echo.
echo [INFO] Starte Auto Claude ohne GitHub Pull...
echo.

cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -NoExit -Command "& '%~dp0Start-Auto-Claude-With-Sync-v2.ps1' -NoPull"

if errorlevel 1 (
    echo.
    echo [ERROR] Fehler beim Start!
    echo.
    pause
)
