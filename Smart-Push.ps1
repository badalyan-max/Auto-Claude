# Smart-Push.ps1
# Smart Push - Intelligent push and merge tool for Auto Claude projects
#
# Usage:
#   .\Smart-Push.ps1
#   .\Smart-Push.ps1 -Project "C:\Projects\my-project"
#   .\Smart-Push.ps1 -Spec 001 -Push
#   .\Smart-Push.ps1 -NoReview -DryRun

param(
    [string]$Project = "",
    [string]$Spec = "",
    [switch]$NoReview = $false,
    [switch]$DryRun = $false,
    [switch]$Push = $false,
    [switch]$Auto = $false
)

$ErrorActionPreference = "Stop"

# Paths
$ScriptDir = $PSScriptRoot
$AutoClaudeDir = $ScriptDir
$BackendDir = Join-Path $AutoClaudeDir "apps\backend"
$PythonScript = Join-Path $BackendDir "smart_push.py"

# Colors
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-ColorOutput "========================================================================" "Cyan"
    Write-ColorOutput "  $Text" "Cyan"
    Write-ColorOutput "========================================================================" "Cyan"
    Write-Host ""
}

function Write-Success { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warn { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

# ============================================================================
# MAIN
# ============================================================================

Write-Header "SMART PUSH - Launcher"

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python found: $pythonVersion"
} catch {
    Write-Err "Python not found! Please install Python."
    exit 1
}

# Check if script exists
if (-not (Test-Path $PythonScript)) {
    Write-Err "smart_push.py not found: $PythonScript"
    exit 1
}

Write-Success "Smart Push script found"

# Determine project directory
if ($Project) {
    $ProjectDir = $Project
} else {
    # If we are in Auto Claude itself, ask for the project
    $CurrentDir = Get-Location
    
    if ($CurrentDir -like "*auto-claude*") {
        Write-Info "You are in the Auto Claude directory."
        Write-Host ""
        Write-Host "Please enter the project path (or Enter for current):" -ForegroundColor Yellow
        $inputProject = Read-Host "Project path"
        
        if ($inputProject) {
            $ProjectDir = $inputProject
        } else {
            $ProjectDir = $CurrentDir
        }
    } else {
        $ProjectDir = $CurrentDir
    }
}

Write-Info "Project: $ProjectDir"

# Build arguments
$arguments = @()

if ($ProjectDir) {
    $arguments += "--project"
    $arguments += "`"$ProjectDir`""
}

if ($Spec) {
    $arguments += "--spec"
    $arguments += $Spec
}

if ($NoReview) {
    $arguments += "--no-review"
}

if ($DryRun) {
    $arguments += "--dry-run"
}

if ($Push) {
    $arguments += "--push"
}

if ($Auto) {
    $arguments += "--auto"
}

# Change to backend directory (for imports)
Push-Location $BackendDir

try {
    Write-Host ""
    Write-ColorOutput "Starting Smart Push..." "Cyan"
    Write-Host ""
    
    # Execute Python script
    $cmd = "python `"$PythonScript`" $($arguments -join ' ')"
    
    if ($arguments.Count -gt 0) {
        Write-Info "Command: python smart_push.py $($arguments -join ' ')"
    }
    
    Write-Host ""
    
    Invoke-Expression $cmd
    
    $exitCode = $LASTEXITCODE
    
} finally {
    Pop-Location
}

Write-Host ""

if ($exitCode -eq 0) {
    Write-Success "Smart Push completed!"
} else {
    Write-Warn "Smart Push finished with code: $exitCode"
}

# Wait for Enter if in console
if ($Host.Name -eq "ConsoleHost") {
    Write-Host ""
    Write-Host "Press Enter to close..." -ForegroundColor Gray
    Read-Host
}
