# Creates Desktop Shortcut for Safe Auto Claude with GitHub Sync

param(
    [switch]$AllUsers = $false
)

$ErrorActionPreference = "Stop"

# Determine Desktop path
if ($AllUsers) {
    $desktopPath = [Environment]::GetFolderPath("CommonDesktopDirectory")
} else {
    # Try OneDrive Desktop first
    $oneDriveDesktop = Join-Path $env:USERPROFILE "OneDrive\Desktop"
    if (Test-Path $oneDriveDesktop) {
        $desktopPath = $oneDriveDesktop
    } else {
        $desktopPath = [Environment]::GetFolderPath("Desktop")
    }
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  Auto Claude - Desktop Verknuepfung erstellen" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[INFO] Desktop Pfad: $desktopPath" -ForegroundColor Cyan

$projectRoot = $PSScriptRoot
$scriptPath = Join-Path $projectRoot "Start-Auto-Claude-With-Sync-v2.ps1"
$batchPath = Join-Path $projectRoot "Start-Auto-Claude-Safe.bat"

# Check if script exists
if (-not (Test-Path $scriptPath)) {
    Write-Host "[ERROR] Script nicht gefunden: $scriptPath" -ForegroundColor Red
    exit 1
}

# Create shortcuts
$shortcuts = @(
    @{
        Name = "Auto Claude (Safe Sync)"
        Target = "powershell.exe"
        Arguments = "-ExecutionPolicy Bypass -NoExit -File `"$scriptPath`""
        Description = "Auto Claude mit GitHub Sync"
    },
    @{
        Name = "Auto Claude (Safe Sync - No Pull)"
        Target = "powershell.exe"
        Arguments = "-ExecutionPolicy Bypass -NoExit -File `"$scriptPath`" -NoPull"
        Description = "Auto Claude ohne GitHub Pull"
    },
    @{
        Name = "Auto Claude Monitor"
        Target = "powershell.exe"
        Arguments = "-ExecutionPolicy Bypass -NoExit -File `"$scriptPath`" -Mode monitor"
        Description = "Auto Claude Live Monitor"
    }
)

foreach ($shortcut in $shortcuts) {
    $shortcutPath = Join-Path $desktopPath "$($shortcut.Name).lnk"
    
    Write-Host ""
    Write-Host "Erstelle: $($shortcut.Name)" -ForegroundColor Yellow
    
    try {
        $WScriptShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WScriptShell.CreateShortcut($shortcutPath)
        $Shortcut.TargetPath = $shortcut.Target
        $Shortcut.Arguments = $shortcut.Arguments
        $Shortcut.WorkingDirectory = $projectRoot
        $Shortcut.Description = $shortcut.Description
        $Shortcut.Save()
        
        Write-Host "  [OK] Erstellt: $shortcutPath" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Fehler: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  Fertig! Verknuepfungen auf dem Desktop verfuegbar." -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
