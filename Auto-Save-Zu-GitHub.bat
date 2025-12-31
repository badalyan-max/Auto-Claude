@echo off
REM Startet das Auto-Save System
REM Doppelklick-freundlich!

cd /d "%~dp0"

REM Starte in neuem PowerShell-Fenster (bleibt offen)
start "Auto-Claude Auto-Save" powershell -ExecutionPolicy Bypass -NoExit -File "%~dp0Auto-Save-Zu-GitHub.ps1"

echo.
echo Auto-Save Fenster geoeffnet!
echo Du kannst dieses Fenster schliessen.
echo.
timeout /t 3
