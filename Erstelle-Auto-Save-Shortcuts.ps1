<#
.SYNOPSIS
    Erstellt Desktop-Verknüpfungen für das Auto-Save System
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Erstelle Desktop-Verknüpfungen für Auto-Save System..." -ForegroundColor Cyan
Write-Host ""

# Desktop-Pfad finden
$desktopPath = [Environment]::GetFolderPath("Desktop")
if (-not (Test-Path $desktopPath)) {
    $desktopPath = "$env:USERPROFILE\OneDrive\Desktop"
}

if (-not (Test-Path $desktopPath)) {
    Write-Host "Desktop nicht gefunden!" -ForegroundColor Red
    exit 1
}

# Projekt-Root
$projectRoot = $PSScriptRoot

# WScript.Shell für Verknüpfungen
$shell = New-Object -ComObject WScript.Shell

# 1. Auto-Save STARTEN
$shortcutPath = Join-Path $desktopPath "Auto-Save Starten.lnk"
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $projectRoot "Auto-Save-Zu-GitHub.bat"
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description = "Startet automatisches GitHub Backup"
$shortcut.IconLocation = "shell32.dll,265"  # Grüner Pfeil (Start)
$shortcut.Save()
Write-Host "✅ Erstellt: Auto-Save Starten.lnk" -ForegroundColor Green

# 2. Auto-Save STATUS
$shortcutPath = Join-Path $desktopPath "Auto-Save Status.lnk"
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $projectRoot "Auto-Save-Status.bat"
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description = "Zeigt Auto-Save Status"
$shortcut.IconLocation = "shell32.dll,278"  # Info-Icon
$shortcut.Save()
Write-Host "✅ Erstellt: Auto-Save Status.lnk" -ForegroundColor Green

# 3. Auto-Save STOPPEN
$shortcutPath = Join-Path $desktopPath "Auto-Save Stoppen.lnk"
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $projectRoot "Auto-Save-Stoppen.bat"
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description = "Stoppt automatisches GitHub Backup"
$shortcut.IconLocation = "shell32.dll,240"  # Roter Stop
$shortcut.Save()
Write-Host "✅ Erstellt: Auto-Save Stoppen.lnk" -ForegroundColor Green

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✅ DESKTOP-VERKNÜPFUNGEN ERSTELLT!" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Auf deinem Desktop findest du jetzt:" -ForegroundColor White
Write-Host "  🟢 Auto-Save Starten   - Aktiviert Auto-Backup" -ForegroundColor Green
Write-Host "  🔵 Auto-Save Status    - Zeigt Status an" -ForegroundColor Cyan
Write-Host "  🔴 Auto-Save Stoppen   - Deaktiviert Auto-Backup" -ForegroundColor Red
Write-Host ""
