# ============================================================
# Auto Claude - EXE Desktop Verknüpfung erstellen
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    Auto Claude EXE - Desktop Verknüpfung" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Pfade
$exePath = "C:\Projekte\auto-claude\apps\frontend\dist\win-unpacked\Auto-Claude.exe"
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "Auto Claude (EXE).lnk"

# Überprüfe ob EXE existiert
if (-not (Test-Path $exePath)) {
    Write-Host "[ERROR] Auto-Claude.exe nicht gefunden!" -ForegroundColor Red
    Write-Host "Pfad: $exePath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Bitte führen Sie zuerst den Build aus:" -ForegroundColor Yellow
    Write-Host "  npm run package:win" -ForegroundColor Cyan
    Write-Host ""
    pause
    exit 1
}

# Erstelle Verknüpfung
Write-Host "[INFO] Erstelle Desktop-Verknüpfung zur EXE..." -ForegroundColor Green

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $exePath
$Shortcut.WorkingDirectory = Split-Path $exePath
$Shortcut.Description = "Auto Claude - Autonomous Coding Framework (Standalone EXE)"
$Shortcut.Save()

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "    Verknüpfung erfolgreich erstellt!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Desktop-Verknüpfung: $shortcutPath" -ForegroundColor Cyan
Write-Host "EXE-Pfad: $exePath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Sie können jetzt Auto Claude direkt vom Desktop starten!" -ForegroundColor Green
Write-Host "(Keine Konsole mehr nötig!)" -ForegroundColor Green
Write-Host ""
pause

