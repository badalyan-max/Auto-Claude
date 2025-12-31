# Create-SmartPush-Shortcut.ps1
# Creates desktop shortcuts for Smart Push

$ErrorActionPreference = "Stop"

# Paths
$ScriptDir = $PSScriptRoot
$SmartPushScript = Join-Path $ScriptDir "Smart-Push.ps1"

# Find Desktop path
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
        
        Write-Host "[OK] Created: $Name" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "[ERROR] Failed: $Name - $_" -ForegroundColor Red
        return $false
    }
}

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  SMART PUSH - Create Desktop Shortcuts" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Desktop path: $DesktopPath" -ForegroundColor Cyan
Write-Host ""

# Main shortcut - Interactive mode
Create-Shortcut -Name "Smart Push" -TargetPath "powershell.exe" -Arguments "-ExecutionPolicy Bypass -NoExit -File `"$SmartPushScript`"" -Description "Smart Push - AI-powered merge and push for Auto Claude projects"

# Quick Push - No review
Create-Shortcut -Name "Smart Push (Quick)" -TargetPath "powershell.exe" -Arguments "-ExecutionPolicy Bypass -NoExit -File `"$SmartPushScript`" -NoReview -Push" -Description "Smart Push Quick - Fast merge without AI review + push"

# Dry Run - Test mode
Create-Shortcut -Name "Smart Push (Test)" -TargetPath "powershell.exe" -Arguments "-ExecutionPolicy Bypass -NoExit -File `"$SmartPushScript`" -DryRun" -Description "Smart Push Test - Shows what would happen without changes"

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Green
Write-Host "  Done! 3 shortcuts created on desktop." -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Available Shortcuts:" -ForegroundColor Cyan
Write-Host "  - Smart Push        : Interactive mode with AI review" -ForegroundColor White
Write-Host "  - Smart Push Quick  : Fast without review + auto push" -ForegroundColor White
Write-Host "  - Smart Push Test   : Dry run without real changes" -ForegroundColor White
Write-Host ""

Write-Host "Press Enter to close..." -ForegroundColor Gray
Read-Host
