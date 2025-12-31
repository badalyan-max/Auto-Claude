@echo off
REM Auto Claude mit GitHub Pull - Holt automatisch Lovable-Aenderungen
REM ====================================================================

cd /d "C:\Projekte\auto-claude"

echo.
echo ====================================================================
echo   Auto Claude mit GitHub Pull
echo ====================================================================
echo.

REM 1. Git Pull ausfuehren
echo [1] Hole aktuelle Aenderungen von GitHub...
git pull origin develop

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARNUNG] Git Pull hatte Probleme. Druecke eine Taste um trotzdem fortzufahren...
    pause
)

echo   [OK] GitHub Pull abgeschlossen!
echo.

REM 2. Auto Claude starten (normale EXE)
echo [2] Starte Auto Claude...
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
)

echo.
echo ====================================================================
echo   Dieses Fenster kann geschlossen werden
echo ====================================================================
echo.
timeout /t 5
