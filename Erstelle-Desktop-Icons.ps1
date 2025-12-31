# Erstellt NUR die notwendigen Desktop-Icons

$ErrorActionPreference = "Stop"

# Desktop-Pfad
$oneDriveDesktop = Join-Path $env:USERPROFILE "OneDrive\Desktop"
if (Test-Path $oneDriveDesktop) {
    $desktopPath = $oneDriveDesktop
} else {
    $desktopPath = [Environment]::GetFolderPath("Desktop")
}

$projectRoot = "C:\Projekte\auto-claude"

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  Erstelle Desktop-Icons" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

# Icon 1: MIT GitHub Pull (für Lovable-Änderungen)
$shortcut1Path = Join-Path $desktopPath "Auto Claude (MIT Lovable).lnk"
$target1 = Join-Path $projectRoot "Start-Mit-GitHub-Pull.bat"

Write-Host "[1] Erstelle: Auto Claude (MIT Lovable)" -ForegroundColor Yellow
Write-Host "    Beschreibung: Holt automatisch Aenderungen von GitHub" -ForegroundColor Gray

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($shortcut1Path)
$Shortcut.TargetPath = $target1
$Shortcut.WorkingDirectory = $projectRoot
$Shortcut.Description = "Auto Claude mit GitHub Pull - holt Lovable-Aenderungen"
$Shortcut.Save()

Write-Host "    [OK] Erstellt!" -ForegroundColor Green
Write-Host ""

# Icon 2: OHNE GitHub Pull (normal)
$shortcut2Path = Join-Path $desktopPath "Auto Claude (Normal).lnk"
$target2 = Join-Path $projectRoot "Start-Normal.bat"

Write-Host "[2] Erstelle: Auto Claude (Normal)" -ForegroundColor Yellow
Write-Host "    Beschreibung: Normaler Start ohne GitHub Pull" -ForegroundColor Gray

$Shortcut2 = $WScriptShell.CreateShortcut($shortcut2Path)
$Shortcut2.TargetPath = $target2
$Shortcut2.WorkingDirectory = $projectRoot
$Shortcut2.Description = "Auto Claude normal - ohne GitHub Pull"
$Shortcut2.Save()

Write-Host "    [OK] Erstellt!" -ForegroundColor Green
Write-Host ""

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  Fertig! 2 Icons auf dem Desktop:" -ForegroundColor Green
Write-Host ""
Write-Host "  1. Auto Claude (MIT Lovable)  <- FUER LOVABLE-AENDERUNGEN" -ForegroundColor Cyan
Write-Host "  2. Auto Claude (Normal)       <- NORMALER START" -ForegroundColor Gray
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
