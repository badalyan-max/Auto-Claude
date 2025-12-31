<#
.SYNOPSIS
    Erstellt Desktop-Verknüpfung für das Update-Skript
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Erstelle Desktop-Verknüpfung für Update-Skript..." -ForegroundColor Cyan

# Desktop-Pfad finden
$desktopPath = [Environment]::GetFolderPath("Desktop")
if (-not (Test-Path $desktopPath)) {
    $desktopPath = "$env:USERPROFILE\OneDrive\Desktop"
}

if (-not (Test-Path $desktopPath)) {
    Write-Host "Desktop nicht gefunden!" -ForegroundColor Red
    exit 1
}

# Pfade
$projectRoot = $PSScriptRoot
$targetPath = Join-Path $projectRoot "Update-Von-Original.bat"
$shortcutPath = Join-Path $desktopPath "Update Auto Claude.lnk"

# WScript.Shell Objekt erstellen
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description = "Hole Updates vom Original-Entwickler"
$shortcut.IconLocation = "shell32.dll,13"  # Download-Icon
$shortcut.Save()

Write-Host "✅ Verknüpfung erstellt: $shortcutPath" -ForegroundColor Green
Write-Host ""
Write-Host "Du kannst jetzt einfach auf dem Desktop doppelklicken:" -ForegroundColor Cyan
Write-Host "  'Update Auto Claude'" -ForegroundColor Yellow
Write-Host ""
