# ============================================================
# Auto Claude - Desktop Verknüpfung erstellen
# ============================================================
#
# Dieses Script erstellt eine Verknüpfung auf dem Desktop
# zum einfachen Starten von Auto Claude
#
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    Auto Claude - Desktop Verknüpfung erstellen" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Pfade
$projectPath = "C:\Projekte\auto-claude"
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "Auto Claude.lnk"
$iconPath = Join-Path $projectPath "apps\frontend\resources\icon.ico"
$batPath = Join-Path $projectPath "Start-Auto-Claude.bat"

# Überprüfe ob Projekt existiert
if (-not (Test-Path $projectPath)) {
    Write-Host "[ERROR] Projekt-Verzeichnis nicht gefunden: $projectPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Bitte passen Sie den Pfad in diesem Script an!" -ForegroundColor Yellow
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
$Shortcut.Description = "Auto Claude - Autonomous Coding Framework"

# Setze Icon falls vorhanden
if (Test-Path $iconPath) {
    $Shortcut.IconLocation = $iconPath
    Write-Host "[INFO] Icon gesetzt: $iconPath" -ForegroundColor Green
} else {
    Write-Host "[WARN] Icon nicht gefunden, verwende Standard-Icon" -ForegroundColor Yellow
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
Write-Host "Sie können jetzt Auto Claude vom Desktop aus starten!" -ForegroundColor Green
Write-Host ""
pause

