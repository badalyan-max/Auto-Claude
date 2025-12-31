@echo off
REM ============================================================
REM Auto Claude Live Monitor - Windows Starter
REM ============================================================

echo.
echo ============================================================
echo         Auto Claude Live Monitor
echo ============================================================
echo.

cd /d "C:\Projekte\auto-claude"

REM Aktiviere Python Virtual Environment falls vorhanden
if exist "apps\backend\.venv\Scripts\activate.bat" (
    call apps\backend\.venv\Scripts\activate.bat
)

REM Starte Monitor mit "Follow All" Option
echo.
echo Starte Monitor mit ALLEN Logs...
echo.

python apps\backend\live_monitor.py --follow-all

if errorlevel 1 (
    echo.
    echo [FEHLER] Monitor konnte nicht gestartet werden.
    echo.
    echo Versuche interaktiven Modus...
    python apps\backend\live_monitor.py
)

pause

