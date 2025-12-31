@echo off
REM Auto Claude Safe Starter - with GitHub Sync
REM Ruft das PowerShell Script auf

cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -File "Start-Auto-Claude-With-Sync-v2.ps1" %*

pause
