@echo off
:: EINFACHES Skript zum Hinzufügen von Windows Defender-Ausnahmen
:: Dieses Skript öffnet ein Administrator-PowerShell-Fenster

echo.
echo ========================================
echo Windows Defender-Ausnahmen hinzufügen
echo ========================================
echo.
echo WICHTIG:
echo 1. Es öffnet sich gleich ein neues PowerShell-Fenster
echo 2. Bestätigen Sie die UAC-Abfrage mit "Ja"
echo 3. Warten Sie, bis die Konfiguration abgeschlossen ist
echo 4. Das Fenster zeigt Ihnen die Ergebnisse an
echo.
pause

:: Öffne PowerShell als Administrator und führe Befehle direkt aus
powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoExit', '-Command', 'Set-ExecutionPolicy Bypass -Scope Process -Force; Write-Host \"\" -ForegroundColor Cyan; Write-Host \"==============================================\" -ForegroundColor Cyan; Write-Host \"Windows Defender-Ausnahmen hinzufügen\" -ForegroundColor Cyan; Write-Host \"==============================================\" -ForegroundColor Cyan; Write-Host \"\"; try { Write-Host \"Füge Ausnahme hinzu: C:\Projekte\auto-claude\" -ForegroundColor Yellow; Add-MpPreference -ExclusionPath \"C:\Projekte\auto-claude\"; Write-Host \"✓ Erfolgreich!\" -ForegroundColor Green; Write-Host \"\"; Write-Host \"Füge Ausnahme hinzu: C:\Projekte\auto-claude\apps\backend\" -ForegroundColor Yellow; Add-MpPreference -ExclusionPath \"C:\Projekte\auto-claude\apps\backend\"; Write-Host \"✓ Erfolgreich!\" -ForegroundColor Green; Write-Host \"\"; Write-Host \"Füge Ausnahme hinzu: C:\Projekte\auto-claude\apps\frontend\" -ForegroundColor Yellow; Add-MpPreference -ExclusionPath \"C:\Projekte\auto-claude\apps\frontend\"; Write-Host \"✓ Erfolgreich!\" -ForegroundColor Green; Write-Host \"\"; Write-Host \"==============================================\" -ForegroundColor Green; Write-Host \"ERFOLGREICH KONFIGURIERT!\" -ForegroundColor Green; Write-Host \"==============================================\" -ForegroundColor Green; Write-Host \"\"; Write-Host \"Alle Ausnahmen wurden hinzugefügt.\" -ForegroundColor White; Write-Host \"Starten Sie Claude Code jetzt neu.\" -ForegroundColor Yellow; } catch { Write-Host \"FEHLER: $_\" -ForegroundColor Red; } Write-Host \"\"; Write-Host \"Dieses Fenster kann geschlossen werden.\" -ForegroundColor Gray; Write-Host \"Drücken Sie eine beliebige Taste...\" -ForegroundColor Gray; $null = $Host.UI.RawUI.ReadKey(\"NoEcho,IncludeKeyDown\")'"

echo.
echo Konfiguration wird ausgeführt...
echo Siehe das Administrator-PowerShell-Fenster für den Status.
echo.
pause

