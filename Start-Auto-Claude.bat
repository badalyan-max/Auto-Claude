@echo off
REM ============================================================
REM Auto Claude - Desktop Starter
REM ============================================================
REM
REM Dieses Script startet die Auto Claude Electron App
REM
REM Sie koennen dieses Script einfach doppelklicken um die App zu starten!
REM ============================================================

echo.
echo ============================================================
echo         Auto Claude wird gestartet...
echo ============================================================
echo.

REM Wechsle zum Projekt-Verzeichnis
cd /d "C:\Projekte\auto-claude"

REM Zeige aktuelles Verzeichnis
echo [INFO] Arbeitsverzeichnis: %CD%
echo.

REM Starte die Electron App im Development Mode
echo [INFO] Starte Electron App (Development Mode)...
echo [INFO] Bitte warten, das kann einen Moment dauern...
echo.

REM Starte npm run dev
call npm run dev

REM Falls Fehler auftreten, halte das Fenster offen
if errorlevel 1 (
    echo.
    echo [ERROR] Beim Starten ist ein Fehler aufgetreten!
    echo.
    echo Moegliche Loesungen:
    echo 1. Stellen Sie sicher dass Node.js installiert ist
    echo 2. Fuehren Sie "npm install" im Projektverzeichnis aus
    echo 3. Ueberpruefen Sie ob alle Dependencies installiert sind
    echo.
    pause
    exit /b 1
)

