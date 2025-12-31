@echo off
REM Startet Auto-Sync für die Auto-Claude App
REM Doppelklick-freundlich!

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0Start-Auto-Sync.ps1"
