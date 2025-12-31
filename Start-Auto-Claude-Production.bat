@echo off
REM ============================================================
REM Auto Claude - Production Starter
REM ============================================================
REM
REM Dieses Script startet die Auto Claude App im Production Mode
REM (schnellerer Start als Development Mode)
REM
REM ============================================================

echo.
echo ============================================================
echo         Auto Claude (Production) wird gestartet...
echo ============================================================
echo.

REM Wechsle zum Projekt-Verzeichnis
cd /d "C:\Projekte\auto-claude"

REM Zeige aktuelles Verzeichnis
echo [INFO] Arbeitsverzeichnis: %CD%
echo.

REM Baue die App falls noch nicht gebaut
if not exist "apps\frontend\out" (
    echo [INFO] App wurde noch nicht gebaut. Baue jetzt...
    echo [INFO] Dies kann beim ersten Mal einige Minuten dauern...
    echo.
    call npm run build
    if errorlevel 1 (
        echo.
        echo [ERROR] Build fehlgeschlagen!
        echo.
        pause
        exit /b 1
    )
)

REM Starte die gebaute App
echo [INFO] Starte Auto Claude...
echo.

call npm start

REM Falls Fehler auftreten, halte das Fenster offen
if errorlevel 1 (
    echo.
    echo [ERROR] Beim Starten ist ein Fehler aufgetreten!
    echo.
    pause
    exit /b 1
)

