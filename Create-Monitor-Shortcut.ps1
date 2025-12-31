# ============================================================
# Auto Claude Monitor - Desktop Verknüpfung erstellen
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    Auto Claude Live Monitor - Verknüpfung" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Pfade
$projectPath = "C:\Projekte\auto-claude"
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "Auto Claude Monitor.lnk"
$batPath = Join-Path $projectPath "Monitor-Auto-Claude.bat"
$iconPath = Join-Path $projectPath "apps\frontend\resources\icon.ico"

# Überprüfe ob Batch-Datei existiert
if (-not (Test-Path $batPath)) {
    Write-Host "[ERROR] Monitor-Auto-Claude.bat nicht gefunden!" -ForegroundColor Red
    Write-Host "Pfad: $batPath" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

# Erstelle Verknüpfung
Write-Host "[INFO] Erstelle Desktop-Verknüpfung..." -ForegroundColor Green

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = $batPath
$Shortcut.WorkingDirectory = $projectPath
$Shortcut.Description = "Auto Claude Live Monitor - Echtzeit-Überwachung und Fehleranalyse"

# Setze Icon falls vorhanden
if (Test-Path $iconPath) {
    $Shortcut.IconLocation = $iconPath
    Write-Host "[INFO] Icon gesetzt" -ForegroundColor Green
}

# Speichere Verknüpfung
$Shortcut.Save()

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "    Verknüpfung erfolgreich erstellt!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Desktop-Verknüpfung: $shortcutPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Sie können jetzt den Live-Monitor vom Desktop starten!" -ForegroundColor Green
Write-Host ""
Write-Host "Tipp: Öffnen Sie auch das Web-Dashboard:" -ForegroundColor Yellow
Write-Host "  $projectPath\apps\backend\live_dashboard.html" -ForegroundColor Cyan
Write-Host ""
pause

