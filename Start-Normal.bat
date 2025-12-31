@echo off
REM Auto Claude normal starten (ohne GitHub Pull)
REM ====================================================================

cd /d "C:\Projekte\auto-claude"

echo.
echo ====================================================================
echo   Auto Claude (Normal)
echo ====================================================================
echo.

set EXE_PATH=apps\frontend\dist\win-unpacked\Auto-Claude.exe

if exist "%EXE_PATH%" (
    start "" "%EXE_PATH%"
    echo   [OK] Auto Claude gestartet!
) else (
    echo   [ERROR] Auto Claude EXE nicht gefunden!
    echo   Pfad: %EXE_PATH%
    echo.
    echo   Bitte erst das Projekt builden:
    echo     npm run build
    pause
)
