@echo off
REM Zeigt den Status des Auto-Save Systems

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0Auto-Save-Zu-GitHub.ps1" -Status
pause
