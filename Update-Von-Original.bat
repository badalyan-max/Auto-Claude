@echo off
REM Batch-Wrapper für das PowerShell Update-Skript
REM Doppelklick-freundlich!

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0Update-Von-Original.ps1"
pause
