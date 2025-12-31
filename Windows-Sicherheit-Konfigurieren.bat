@echo off
:: Batch-Datei zum automatischen Ausführen des PowerShell-Skripts als Administrator
:: Einfach Doppelklick auf diese Datei und bestätigen Sie die UAC-Abfrage

echo ================================================
echo Windows-Sicherheit für Claude Code konfigurieren
echo ================================================
echo.
echo Dieses Skript benötigt Administratorrechte.
echo Bitte bestätigen Sie die folgende UAC-Abfrage.
echo.
pause

:: Prüfen ob PowerShell verfügbar ist
where powershell >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo FEHLER: PowerShell wurde nicht gefunden!
    echo Bitte installieren Sie PowerShell oder führen Sie das Skript manuell aus.
    pause
    exit /b 1
)

:: PowerShell-Skript als Administrator ausführen
powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList '-ExecutionPolicy Bypass -File \"%~dp0configure-windows-security.ps1\"'"

echo.
echo Wenn ein neues PowerShell-Fenster geöffnet wurde, folgen Sie den Anweisungen dort.
echo Falls nicht, führen Sie das Skript configure-windows-security.ps1 manuell als Administrator aus.
echo.
pause

