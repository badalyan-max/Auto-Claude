<#
.SYNOPSIS
    Erstellt Desktop-Verknüpfungen für Smart Push
.DESCRIPTION
    Erstellt zwei Shortcuts auf dem Desktop:
    1. Smart Push - Interaktiver Modus (fragt nach Projekt)
    2. Smart Push Quick - Für schnelles Pushen ohne Review
#>

$ErrorActionPreference = "Stop"

# Pfade
$ScriptDir = $PSScriptRoot
$SmartPushScript = Join-Path $ScriptDir "Smart-Push.ps1"

# Desktop-Pfad finden
$DesktopPath = [Environment]::GetFolderPath("Desktop")
if (-not (Test-Path $DesktopPath)) {
    $DesktopPath = Join-Path $env:USERPROFILE "Desktop"
}
if (-not (Test-Path $DesktopPath)) {
    $DesktopPath = Join-Path $env:USERPROFILE "OneDrive\Desktop"
}

function Create-Shortcut {
    param(
        [string]$Name,
        [string]$TargetPath,
        [string]$Arguments,
        [string]$Description,
        [string]$IconIndex = "0"
    )
    
    $ShortcutPath = Join-Path $DesktopPath "$Name.lnk"
    
    try {
        $WScriptShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
        $Shortcut.TargetPath = $TargetPath
        $Shortcut.Arguments = $Arguments
        $Shortcut.WorkingDirectory = $ScriptDir
        $Shortcut.Description = $Description
        $Shortcut.IconLocation = "powershell.exe,$IconIndex"
        $Shortcut.Save()
        
        Write-Host "✅ Erstellt: $Name" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Fehler bei $Name : $_" -ForegroundColor Red
        return $false
    }
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  SMART PUSH - Desktop-Verknüpfungen erstellen" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "Desktop-Pfad: $DesktopPath" -ForegroundColor Cyan
Write-Host ""

# Hauptverknüpfung - Interaktiver Modus
Create-Shortcut `
    -Name "Smart Push" `
    -TargetPath "powershell.exe" `
    -Arguments "-ExecutionPolicy Bypass -NoExit -File `"$SmartPushScript`"" `
    -Description "Smart Push - KI-gestütztes Merge und Push für Auto Claude Projekte"

# Quick Push - Ohne Review
Create-Shortcut `
    -Name "Smart Push (Quick)" `
    -TargetPath "powershell.exe" `
    -Arguments "-ExecutionPolicy Bypass -NoExit -File `"$SmartPushScript`" -NoReview -Push" `
    -Description "Smart Push Quick - Schnelles Merge ohne KI-Review + Push"

# Dry Run - Testmodus
Create-Shortcut `
    -Name "Smart Push (Test)" `
    -TargetPath "powershell.exe" `
    -Arguments "-ExecutionPolicy Bypass -NoExit -File `"$SmartPushScript`" -DryRun" `
    -Description "Smart Push Test - Zeigt was passieren würde ohne Änderungen"

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  Fertig! 3 Verknüpfungen auf dem Desktop erstellt." -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

Write-Host "Verfügbare Shortcuts:" -ForegroundColor Cyan
Write-Host "  🔹 Smart Push        - Interaktiver Modus mit KI-Review" -ForegroundColor White
Write-Host "  🔹 Smart Push Quick  - Schnell ohne Review + automatischer Push" -ForegroundColor White
Write-Host "  🔹 Smart Push Test   - Testlauf ohne echte Änderungen" -ForegroundColor White
Write-Host ""

Write-Host "Drücke Enter zum Beenden..." -ForegroundColor Gray
Read-Host
