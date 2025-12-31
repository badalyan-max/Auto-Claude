<#
.SYNOPSIS
    Erstellt Desktop-Verknüpfungen für Auto-Sync

.DESCRIPTION
    Erstellt 3 praktische Desktop-Verknüpfungen:
    1. "Auto-Sync Starten" - Startet sichtbar im Fenster
    2. "Auto-Sync Hintergrund" - Startet unsichtbar
    3. "Auto-Sync Status" - Zeigt aktuellen Status
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ERSTELLE AUTO-SYNC DESKTOP-VERKNÜPFUNGEN" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Desktop-Pfad finden
$desktopPath = [Environment]::GetFolderPath("Desktop")
if (-not (Test-Path $desktopPath)) {
    $desktopPath = "$env:USERPROFILE\OneDrive\Desktop"
}

if (-not (Test-Path $desktopPath)) {
    Write-Host "❌ Desktop nicht gefunden!" -ForegroundColor Red
    exit 1
}

# Projekt-Root
$projectRoot = $PSScriptRoot

# WScript.Shell Objekt
$shell = New-Object -ComObject WScript.Shell

# 1. Auto-Sync Starten (Vordergrund)
Write-Host "📝 Erstelle 'Auto-Sync Starten'..." -ForegroundColor Cyan
$shortcut = $shell.CreateShortcut((Join-Path $desktopPath "Auto-Sync Starten.lnk"))
$shortcut.TargetPath = Join-Path $projectRoot "Start-Auto-Sync.bat"
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description = "Startet Auto-Sync für Auto-Claude App"
$shortcut.IconLocation = "shell32.dll,238"  # Sync-Icon
$shortcut.Save()
Write-Host "   ✅ Erstellt" -ForegroundColor Green

# 2. Auto-Sync Hintergrund
Write-Host "📝 Erstelle 'Auto-Sync Hintergrund'..." -ForegroundColor Cyan
$shortcut = $shell.CreateShortcut((Join-Path $desktopPath "Auto-Sync Hintergrund.lnk"))
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$projectRoot\Start-Auto-Sync-Hintergrund.ps1`""
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description = "Startet Auto-Sync unsichtbar im Hintergrund"
$shortcut.IconLocation = "shell32.dll,238"
$shortcut.Save()
Write-Host "   ✅ Erstellt" -ForegroundColor Green

# 3. Auto-Sync Status
Write-Host "📝 Erstelle 'Auto-Sync Status'..." -ForegroundColor Cyan
$shortcut = $shell.CreateShortcut((Join-Path $desktopPath "Auto-Sync Status.lnk"))
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -NoExit -File `"$projectRoot\Auto-Sync-Status.ps1`""
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description = "Zeigt Auto-Sync Status"
$shortcut.IconLocation = "shell32.dll,77"  # Info-Icon
$shortcut.Save()
Write-Host "   ✅ Erstellt" -ForegroundColor Green

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ ALLE VERKNÜPFUNGEN ERSTELLT!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Auf deinem Desktop findest du jetzt:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. 🔄 Auto-Sync Starten" -ForegroundColor White
Write-Host "     → Startet im Fenster (siehst was passiert)" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. 🔄 Auto-Sync Hintergrund" -ForegroundColor White
Write-Host "     → Läuft unsichtbar im Hintergrund" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. ℹ️  Auto-Sync Status" -ForegroundColor White
Write-Host "     → Zeigt ob läuft + Statistiken" -ForegroundColor Gray
Write-Host ""
Write-Host "Empfehlung: Nutze 'Auto-Sync Hintergrund' für automatisches Backup!" -ForegroundColor Yellow
Write-Host ""
