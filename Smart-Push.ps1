<#
.SYNOPSIS
    Smart Push - Intelligentes Push-und-Merge-Tool für Auto Claude Projekte
.DESCRIPTION
    Dieses Skript ermöglicht One-Click Push und Merge für alle Auto Claude Projekte.
    Es findet fertige Specs, führt KI-Reviews durch und merged sie interaktiv in main.
.PARAMETER Project
    Pfad zum Projekt (default: aktuelles Verzeichnis)
.PARAMETER Spec
    Nur eine bestimmte Spec verarbeiten
.PARAMETER NoReview
    KI-Review überspringen
.PARAMETER DryRun
    Testlauf ohne echte Änderungen
.PARAMETER Push
    Nach Merge automatisch pushen
.PARAMETER Auto
    Vollautomatisch ohne Rückfragen
.EXAMPLE
    .\Smart-Push.ps1
    .\Smart-Push.ps1 -Project "C:\Projekte\craft-connect"
    .\Smart-Push.ps1 -Spec 001 -Push
    .\Smart-Push.ps1 -NoReview -DryRun
#>

param(
    [string]$Project = "",
    [string]$Spec = "",
    [switch]$NoReview = $false,
    [switch]$DryRun = $false,
    [switch]$Push = $false,
    [switch]$Auto = $false
)

$ErrorActionPreference = "Stop"

# Pfade
$ScriptDir = $PSScriptRoot
$AutoClaudeDir = $ScriptDir  # Dieses Skript liegt im Auto Claude Root
$BackendDir = Join-Path $AutoClaudeDir "apps\backend"
$PythonScript = Join-Path $BackendDir "smart_push.py"

# Farben
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-ColorOutput "════════════════════════════════════════════════════════════════════════" "Cyan"
    Write-ColorOutput "  $Text" "Cyan"
    Write-ColorOutput "════════════════════════════════════════════════════════════════════════" "Cyan"
    Write-Host ""
}

function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }

# ============================================================================
# HAUPTPROGRAMM
# ============================================================================

Write-Header "SMART PUSH - Launcher"

# Prüfe Python
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python gefunden: $pythonVersion"
} catch {
    Write-Error "Python nicht gefunden! Bitte Python installieren."
    exit 1
}

# Prüfe ob Skript existiert
if (-not (Test-Path $PythonScript)) {
    Write-Error "smart_push.py nicht gefunden: $PythonScript"
    exit 1
}

Write-Success "Smart Push Script gefunden"

# Bestimme Projekt-Verzeichnis
if ($Project) {
    $ProjectDir = $Project
} else {
    # Wenn wir in Auto Claude selbst sind, frage nach dem Projekt
    $CurrentDir = Get-Location
    
    if ($CurrentDir -like "*auto-claude*") {
        Write-Info "Du bist im Auto Claude Verzeichnis."
        Write-Host ""
        Write-Host "Bitte gib den Pfad zum Projekt ein (oder Enter für aktuelles):" -ForegroundColor Yellow
        $inputProject = Read-Host "Projekt-Pfad"
        
        if ($inputProject) {
            $ProjectDir = $inputProject
        } else {
            $ProjectDir = $CurrentDir
        }
    } else {
        $ProjectDir = $CurrentDir
    }
}

Write-Info "Projekt: $ProjectDir"

# Baue Argumente
$args = @()

if ($ProjectDir) {
    $args += "--project"
    $args += "`"$ProjectDir`""
}

if ($Spec) {
    $args += "--spec"
    $args += $Spec
}

if ($NoReview) {
    $args += "--no-review"
}

if ($DryRun) {
    $args += "--dry-run"
}

if ($Push) {
    $args += "--push"
}

if ($Auto) {
    $args += "--auto"
}

# Wechsle ins Backend-Verzeichnis (für imports)
Push-Location $BackendDir

try {
    Write-Host ""
    Write-ColorOutput "Starte Smart Push..." "Cyan"
    Write-Host ""
    
    # Führe Python-Skript aus
    $cmd = "python `"$PythonScript`" $($args -join ' ')"
    
    if ($args.Count -gt 0) {
        Write-Info "Befehl: python smart_push.py $($args -join ' ')"
    }
    
    Write-Host ""
    
    Invoke-Expression $cmd
    
    $exitCode = $LASTEXITCODE
    
} finally {
    Pop-Location
}

Write-Host ""

if ($exitCode -eq 0) {
    Write-Success "Smart Push abgeschlossen!"
} else {
    Write-Warning "Smart Push beendet mit Code: $exitCode"
}

# Warte auf Enter wenn nicht im Terminal
if ($Host.Name -eq "ConsoleHost") {
    Write-Host ""
    Write-Host "Drücke Enter zum Beenden..." -ForegroundColor Gray
    Read-Host
}
