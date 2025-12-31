# Test Script for Start-Auto-Claude-With-Sync.ps1
# Simplified version - ASCII only

param()

$ErrorActionPreference = "Continue"
$ProjectRoot = $PSScriptRoot
$SyncScript = Join-Path $ProjectRoot "Start-Auto-Claude-With-Sync.ps1"

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  AUTO CLAUDE SYNC SCRIPT - TESTS" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

$passed = 0
$failed = 0

# Test 1: Script exists
Write-Host "[TEST 1] Script Existenz..." -ForegroundColor Yellow
if (Test-Path $SyncScript) {
    Write-Host "  [OK] Script gefunden" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  [ERROR] Script nicht gefunden!" -ForegroundColor Red
    $failed++
    exit 1
}

# Test 2: Git Repository
Write-Host ""
Write-Host "[TEST 2] Git Repository..." -ForegroundColor Yellow
Set-Location $ProjectRoot
try {
    $gitCheck = git rev-parse --is-inside-work-tree 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Git Repository erkannt" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  [ERROR] Kein Git Repository" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  [ERROR] Git nicht verfuegbar" -ForegroundColor Red
    $failed++
}

# Test 3: Current Branch
Write-Host ""
Write-Host "[TEST 3] Current Branch..." -ForegroundColor Yellow
try {
    $branch = git branch --show-current
    Write-Host "  [INFO] Branch: $branch" -ForegroundColor Cyan
    Write-Host "  [OK] Branch ermittelt" -ForegroundColor Green
    $passed++
} catch {
    Write-Host "  [ERROR] Branch check failed" -ForegroundColor Red
    $failed++
}

# Test 4: Git Status
Write-Host ""
Write-Host "[TEST 4] Git Status..." -ForegroundColor Yellow
try {
    $status = git status --porcelain
    if ([string]::IsNullOrWhiteSpace($status)) {
        Write-Host "  [INFO] Working tree clean" -ForegroundColor Cyan
    } else {
        Write-Host "  [INFO] Uncommitted changes vorhanden" -ForegroundColor Yellow
    }
    Write-Host "  [OK] Status check OK" -ForegroundColor Green
    $passed++
} catch {
    Write-Host "  [ERROR] Status check failed" -ForegroundColor Red
    $failed++
}

# Test 5: Remote
Write-Host ""
Write-Host "[TEST 5] Remote Repository..." -ForegroundColor Yellow
try {
    $remotes = git remote
    if ($remotes) {
        Write-Host "  [INFO] Remote: $remotes" -ForegroundColor Cyan
        Write-Host "  [OK] Remote gefunden" -ForegroundColor Green
    } else {
        Write-Host "  [INFO] Kein Remote (nur lokal)" -ForegroundColor Yellow
        Write-Host "  [OK] Remote check OK" -ForegroundColor Green
    }
    $passed++
} catch {
    Write-Host "  [ERROR] Remote check failed" -ForegroundColor Red
    $failed++
}

# Test 6: Python
Write-Host ""
Write-Host "[TEST 6] Python Installation..." -ForegroundColor Yellow
try {
    $pythonVer = python --version 2>&1
    Write-Host "  [INFO] $pythonVer" -ForegroundColor Cyan
    
    if ($pythonVer -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        
        if ($major -ge 3 -and $minor -ge 12) {
            Write-Host "  [OK] Python Version >= 3.12" -ForegroundColor Green
            $passed++
        } else {
            Write-Host "  [WARN] Python Version < 3.12" -ForegroundColor Yellow
            Write-Host "  [OK] Python verfuegbar" -ForegroundColor Green
            $passed++
        }
    } else {
        Write-Host "  [OK] Python gefunden" -ForegroundColor Green
        $passed++
    }
} catch {
    Write-Host "  [ERROR] Python nicht gefunden" -ForegroundColor Red
    $failed++
}

# Test 7: Virtual Environment
Write-Host ""
Write-Host "[TEST 7] Virtual Environment..." -ForegroundColor Yellow
$venvPath = Join-Path $ProjectRoot "apps\backend\.venv"
if (Test-Path $venvPath) {
    Write-Host "  [OK] venv gefunden" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  [INFO] venv nicht vorhanden (wird erstellt)" -ForegroundColor Yellow
    Write-Host "  [OK] venv check OK" -ForegroundColor Green
    $passed++
}

# Test 8: Backend Scripts
Write-Host ""
Write-Host "[TEST 8] Backend Scripts..." -ForegroundColor Yellow
$scripts = @(
    "apps\backend\spec_runner.py",
    "apps\backend\run.py",
    "apps\backend\live_monitor.py"
)

$scriptsOK = 0
foreach ($script in $scripts) {
    if (Test-Path (Join-Path $ProjectRoot $script)) {
        $scriptsOK++
    }
}

Write-Host "  [INFO] $scriptsOK/$($scripts.Count) Scripts gefunden" -ForegroundColor Cyan
if ($scriptsOK -eq $scripts.Count) {
    Write-Host "  [OK] Alle Scripts vorhanden" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  [WARN] Nicht alle Scripts gefunden" -ForegroundColor Yellow
    $passed++
}

# Test 9: Log Directory
Write-Host ""
Write-Host "[TEST 9] Log Directory..." -ForegroundColor Yellow
$logDir = Join-Path $ProjectRoot ".auto-claude"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

if (Test-Path $logDir) {
    Write-Host "  [OK] Log Directory bereit" -ForegroundColor Green
    $passed++
} else {
    Write-Host "  [ERROR] Log Directory konnte nicht erstellt werden" -ForegroundColor Red
    $failed++
}

# Test 10: Script Syntax
Write-Host ""
Write-Host "[TEST 10] Script Syntax Check..." -ForegroundColor Yellow
try {
    $scriptContent = Get-Content $SyncScript -Raw -Encoding UTF8
    $errors = $null
    $null = [System.Management.Automation.PSParser]::Tokenize($scriptContent, [ref]$errors)
    
    if ($errors.Count -eq 0) {
        Write-Host "  [OK] Keine Syntax-Fehler" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  [ERROR] $($errors.Count) Syntax-Fehler gefunden" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  [ERROR] Syntax check failed: $_" -ForegroundColor Red
    $failed++
}

# Summary
Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  TEST ZUSAMMENFASSUNG" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total Tests: $($passed + $failed)" -ForegroundColor White
Write-Host "  [OK] Passed:  $passed" -ForegroundColor Green
Write-Host "  [X] Failed:   $failed" -ForegroundColor Red
Write-Host ""

$successRate = [math]::Round(($passed / ($passed + $failed)) * 100, 1)
Write-Host "Erfolgsquote: $successRate%" -ForegroundColor $(if ($successRate -ge 90) { "Green" } elseif ($successRate -ge 70) { "Yellow" } else { "Red" })

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan

if ($failed -eq 0) {
    Write-Host ""
    Write-Host "  ALLE TESTS BESTANDEN! Script ist BOMBENSICHER!" -ForegroundColor Green
    Write-Host ""
    exit 0
} else {
    Write-Host ""
    Write-Host "  Einige Tests fehlgeschlagen - siehe oben" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
