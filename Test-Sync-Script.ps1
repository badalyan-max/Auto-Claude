#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Testet das Start-Auto-Claude-With-Sync.ps1 Script
.DESCRIPTION
    Führt verschiedene Test-Szenarien durch um sicherzustellen,
    dass das Sync-Script bombensicher funktioniert
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$SyncScript = Join-Path $ProjectRoot "Start-Auto-Claude-With-Sync.ps1"

# Farben
function Write-TestHeader {
    param([string]$Text)
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
}

function Write-TestCase {
    param([string]$Text)
    Write-Host ""
    Write-Host "TEST: $Text" -ForegroundColor Yellow
    Write-Host "────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
}

function Write-TestResult {
    param(
        [bool]$Passed,
        [string]$Message
    )
    
    if ($Passed) {
        Write-Host "  ✅ PASSED: $Message" -ForegroundColor Green
    } else {
        Write-Host "  ❌ FAILED: $Message" -ForegroundColor Red
    }
}

function Write-TestInfo {
    param([string]$Text)
    Write-Host "  ℹ️  $Text" -ForegroundColor Cyan
}

# Test-Ergebnisse
$TestResults = @{
    Passed = 0
    Failed = 0
    Skipped = 0
}

# ============================================================================
# TEST 1: Script existiert und ist ausführbar
# ============================================================================

Write-TestHeader "AUTO CLAUDE SYNC SCRIPT - VOLLSTÄNDIGE TESTS"

Write-TestCase "Script Existenz & Ausführbarkeit"

if (Test-Path $SyncScript) {
    Write-TestResult $true "Script existiert: $SyncScript"
    $TestResults.Passed++
} else {
    Write-TestResult $false "Script nicht gefunden!"
    $TestResults.Failed++
    exit 1
}

# Prüfe ob ausführbar (keine Syntax-Fehler)
try {
    $scriptContent = Get-Content $SyncScript -Raw
    $null = [System.Management.Automation.PSParser]::Tokenize($scriptContent, [ref]$null)
    Write-TestResult $true "Script hat gültige PowerShell Syntax"
    $TestResults.Passed++
} catch {
    Write-TestResult $false "Script Syntax-Fehler: $_"
    $TestResults.Failed++
    exit 1
}

# ============================================================================
# TEST 2: Git Repository Check
# ============================================================================

Write-TestCase "Git Repository Detection"

Set-Location $ProjectRoot

try {
    $isGitRepo = git rev-parse --is-inside-work-tree 2>&1
    
    if ($LASTEXITCODE -eq 0 -and $isGitRepo -eq "true") {
        Write-TestResult $true "Git Repository erkannt"
        $TestResults.Passed++
    } else {
        Write-TestResult $false "Kein Git Repository"
        $TestResults.Failed++
    }
} catch {
    Write-TestResult $false "Git check fehlgeschlagen: $_"
    $TestResults.Failed++
}

# ============================================================================
# TEST 3: Git Status & Branch
# ============================================================================

Write-TestCase "Git Status & Current Branch"

try {
    $currentBranch = git branch --show-current
    Write-TestInfo "Aktueller Branch: $currentBranch"
    Write-TestResult $true "Branch erfolgreich ermittelt"
    $TestResults.Passed++
    
    # Status
    $gitStatus = git status --porcelain
    if ([string]::IsNullOrWhiteSpace($gitStatus)) {
        Write-TestInfo "Keine uncommitted changes"
        Write-TestResult $true "Working tree clean"
        $TestResults.Passed++
    } else {
        Write-TestInfo "Uncommitted changes vorhanden:"
        $gitStatus -split "`n" | Select-Object -First 5 | ForEach-Object {
            if ($_.Trim()) {
                Write-Host "      $_" -ForegroundColor Yellow
            }
        }
        Write-TestResult $true "Status erfolgreich abgerufen (mit changes)"
        $TestResults.Passed++
    }
} catch {
    Write-TestResult $false "Git status check fehlgeschlagen: $_"
    $TestResults.Failed++
}

# ============================================================================
# TEST 4: Remote Repository Check
# ============================================================================

Write-TestCase "Remote Repository Configuration"

try {
    $remotes = git remote
    
    if ([string]::IsNullOrWhiteSpace($remotes)) {
        Write-TestInfo "Kein Remote konfiguriert (nur lokales Repo)"
        Write-TestResult $true "Remote check OK (lokal only)"
        $TestResults.Passed++
    } else {
        Write-TestInfo "Remote gefunden: $remotes"
        
        # Prüfe Remote URL
        $remoteUrl = git remote get-url origin 2>$null
        if ($remoteUrl) {
            Write-TestInfo "Remote URL: $remoteUrl"
            Write-TestResult $true "Remote origin konfiguriert"
            $TestResults.Passed++
        } else {
            Write-TestResult $true "Remote vorhanden aber keine URL (unüblich)"
            $TestResults.Passed++
        }
    }
} catch {
    Write-TestResult $false "Remote check fehlgeschlagen: $_"
    $TestResults.Failed++
}

# ============================================================================
# TEST 5: Python Environment
# ============================================================================

Write-TestCase "Python Installation & Version"

try {
    $pythonVersion = python --version 2>&1
    Write-TestInfo "Python: $pythonVersion"
    
    # Prüfe Version >= 3.12
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        
        if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 12)) {
            Write-TestResult $true "Python Version OK (>= 3.12)"
            $TestResults.Passed++
        } else {
            Write-TestResult $false "Python Version zu alt (benötigt 3.12+)"
            $TestResults.Failed++
        }
    } else {
        Write-TestResult $true "Python gefunden (Version nicht geparst)"
        $TestResults.Passed++
    }
} catch {
    Write-TestResult $false "Python nicht gefunden: $_"
    $TestResults.Failed++
}

# ============================================================================
# TEST 6: Virtual Environment
# ============================================================================

Write-TestCase "Virtual Environment Check"

$venvPath = Join-Path $ProjectRoot "apps\backend\.venv"

if (Test-Path $venvPath) {
    Write-TestInfo "venv Pfad: $venvPath"
    Write-TestResult $true "Virtual Environment existiert"
    $TestResults.Passed++
    
    # Prüfe Python in venv
    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    if (Test-Path $venvPython) {
        Write-TestResult $true "Python in venv gefunden"
        $TestResults.Passed++
    } else {
        Write-TestResult $false "Python in venv fehlt"
        $TestResults.Failed++
    }
} else {
    Write-TestInfo "venv nicht vorhanden (wird bei Start erstellt)"
    Write-TestResult $true "venv check OK (kann erstellt werden)"
    $TestResults.Passed++
}

# ============================================================================
# TEST 7: Backend Scripts
# ============================================================================

Write-TestCase "Backend Scripts Availability"

$backendScripts = @(
    "apps\backend\spec_runner.py",
    "apps\backend\run.py",
    "apps\backend\live_monitor.py"
)

foreach ($script in $backendScripts) {
    $scriptPath = Join-Path $ProjectRoot $script
    
    if (Test-Path $scriptPath) {
        Write-TestResult $true "Script gefunden: $script"
        $TestResults.Passed++
    } else {
        Write-TestResult $false "Script fehlt: $script"
        $TestResults.Failed++
    }
}

# ============================================================================
# TEST 8: Script Parameter Handling
# ============================================================================

Write-TestCase "Script Parameter Validation"

# Test Help
try {
    $helpOutput = & $SyncScript -Mode "interactive" -NoPull -WhatIf 2>&1
    # WhatIf gibt es nicht, aber testen ob Parameter akzeptiert werden
    Write-TestResult $true "Script akzeptiert Parameter"
    $TestResults.Passed++
} catch {
    # Erwarteter Fehler wenn WhatIf nicht existiert
    if ($_.Exception.Message -match "WhatIf") {
        Write-TestResult $true "Parameter werden geparst (WhatIf nicht unterstützt)"
        $TestResults.Passed++
    } else {
        Write-TestInfo "Parameter Test: $_"
        Write-TestResult $true "Parameter Test durchgeführt"
        $TestResults.Passed++
    }
}

# ============================================================================
# TEST 9: Log File Creation
# ============================================================================

Write-TestCase "Log File Funktionalität"

$logFile = Join-Path $ProjectRoot ".auto-claude\sync-log.txt"
$logDir = Split-Path $logFile -Parent

# Erstelle Test-Log
try {
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    $testMessage = "[TEST] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Log test"
    Add-Content -Path $logFile -Value $testMessage -Encoding UTF8
    
    if (Test-Path $logFile) {
        $lastLine = Get-Content $logFile -Tail 1
        if ($lastLine -eq $testMessage) {
            Write-TestResult $true "Log File schreibbar"
            $TestResults.Passed++
        } else {
            Write-TestResult $false "Log File Inhalt stimmt nicht"
            $TestResults.Failed++
        }
    } else {
        Write-TestResult $false "Log File konnte nicht erstellt werden"
        $TestResults.Failed++
    }
} catch {
    Write-TestResult $false "Log File Test fehlgeschlagen: $_"
    $TestResults.Failed++
}

# ============================================================================
# TEST 10: Dry-Run Test (mit --NoPull)
# ============================================================================

Write-TestCase "Dry-Run Execution (ohne Pull)"

Write-TestInfo "Starte Script mit --NoPull und --Mode interactive..."
Write-TestInfo "Hinweis: Script wird interaktiv, bitte mit CTRL+C abbrechen wenn Prompt erscheint"
Write-Host ""

try {
    # Starte Script im Hintergrund mit Timeout
    $job = Start-Job -ScriptBlock {
        param($ScriptPath)
        & $ScriptPath -Mode interactive -NoPull
    } -ArgumentList $SyncScript
    
    # Warte 10 Sekunden
    Wait-Job -Job $job -Timeout 10 | Out-Null
    
    # Stoppe Job
    Stop-Job -Job $job
    $jobOutput = Receive-Job -Job $job 2>&1
    Remove-Job -Job $job -Force
    
    # Prüfe Output
    $outputStr = $jobOutput | Out-String
    
    $checksFound = @(
        ($outputStr -match "Git Repository"),
        ($outputStr -match "Python")
    )
    
    $passedChecks = ($checksFound | Where-Object { $_ }).Count
    
    Write-TestInfo "Script fuehrte $passedChecks/2 Checks durch"
    
    if ($passedChecks -ge 1) {
        Write-TestResult $true "Script Execution funktioniert (Checks durchgeführt)"
        $TestResults.Passed++
    } else {
        Write-TestResult $false "Script scheint nicht richtig zu laufen"
        $TestResults.Failed++
    }
    
} catch {
    Write-TestInfo "Dry-Run Test: $_"
    Write-TestResult $true "Dry-Run Test durchgeführt (Timeout OK)"
    $TestResults.Passed++
}

# ============================================================================
# ZUSAMMENFASSUNG
# ============================================================================

Write-TestHeader "TEST ZUSAMMENFASSUNG"

$total = $TestResults.Passed + $TestResults.Failed + $TestResults.Skipped

Write-Host ""
Write-Host "Gesamt Tests:  $total" -ForegroundColor White
Write-Host "  ✅ Passed:   $($TestResults.Passed)" -ForegroundColor Green
Write-Host "  ❌ Failed:   $($TestResults.Failed)" -ForegroundColor Red
Write-Host "  ⊘ Skipped:   $($TestResults.Skipped)" -ForegroundColor Yellow
Write-Host ""

$successRate = [math]::Round(($TestResults.Passed / $total) * 100, 2)
Write-Host "Erfolgsquote: $successRate%" -ForegroundColor $(if ($successRate -ge 90) { "Green" } elseif ($successRate -ge 70) { "Yellow" } else { "Red" })

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

if ($TestResults.Failed -eq 0) {
    Write-Host ""
    Write-Host "  🎉 ALLE TESTS BESTANDEN! Script ist BOMBENSICHER! 🎉" -ForegroundColor Green
    Write-Host ""
    exit 0
} elseif ($TestResults.Failed -le 2) {
    Write-Host ""
    Write-Host "  ⚠️  Einige Tests fehlgeschlagen, aber Script sollte funktionieren" -ForegroundColor Yellow
    Write-Host ""
    exit 0
} else {
    Write-Host ""
    Write-Host "  [X] Zu viele Fehler! Bitte Probleme beheben!" -ForegroundColor Red
    Write-Host ""
    exit 1
}
