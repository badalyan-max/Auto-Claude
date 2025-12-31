@echo off
REM Stoppt das Auto-Save System

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0Auto-Save-Zu-GitHub.ps1" -Stop
pause
