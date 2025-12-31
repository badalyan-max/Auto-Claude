# Auto Claude Smart Starter with GitHub Sync
# Safe ASCII version without encoding issues

param(
    [ValidateSet("interactive", "run", "monitor")]
    [string]$Mode = "interactive",
    [string]$Spec = "",
    [string]$Task = "",
    [switch]$NoPull = $false
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "apps\backend"
$LogFile = Join-Path $ProjectRoot ".auto-claude\sync-log.txt"

# Helper Functions
function WriteLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logDir = Split-Path $LogFile -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    Add-Content -Path $LogFile -Value "[$timestamp] $Message" -Encoding UTF8 -ErrorAction SilentlyContinue
}

function WriteHeader {
    param([string]$Text)
    Write-Host ""
    Write-Host "====================================================================" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "====================================================================" -ForegroundColor Cyan
    Write-Host ""
}

function WriteStep {
    param([string]$Number, [string]$Text)
    Write-Host "[$Number] $Text" -ForegroundColor Yellow
}

function WriteOK {
    param([string]$Text)
    Write-Host "  [OK] $Text" -ForegroundColor Green
}

function WriteError {
    param([string]$Text)
    Write-Host "  [ERROR] $Text" -ForegroundColor Red
}

function WriteWarn {
    param([string]$Text)
    Write-Host "  [WARN] $Text" -ForegroundColor Yellow
}

function WriteInfo {
    param([string]$Text)
    Write-Host "  [INFO] $Text" -ForegroundColor Cyan
}

# Git Repository Check
function CheckGitRepository {
    WriteStep "1" "Git Repository pruefen..."
    WriteLog "Pruefe Git Repository"
    
    try {
        $gitCheck = git rev-parse --is-inside-work-tree 2>&1
        if ($LASTEXITCODE -eq 0 -and $gitCheck -eq "true") {
            WriteOK "Git Repository erkannt"
            WriteLog "Git Repository OK"
            return $true
        } else {
            WriteError "Kein Git Repository!"
            WriteLog "ERROR: Kein Git Repository"
            return $false
        }
    } catch {
        WriteError "Git nicht verfuegbar!"
        WriteLog "ERROR: Git nicht verfuegbar - $_"
        return $false
    }
}

# Uncommitted Changes Check
function CheckUncommittedChanges {
    WriteStep "2" "Lokale Aenderungen pruefen..."
    WriteLog "Pruefe uncommitted changes"
    
    try {
        $status = git status --porcelain
        
        if ([string]::IsNullOrWhiteSpace($status)) {
            WriteOK "Keine uncommitted changes"
            WriteLog "Keine uncommitted changes"
            return $true
        } else {
            WriteWarn "Uncommitted changes vorhanden:"
            $status -split "`n" | Select-Object -First 5 | ForEach-Object {
                if ($_.Trim()) {
                    Write-Host "      $_" -ForegroundColor Yellow
                }
            }
            WriteLog "WARN: Uncommitted changes gefunden"
            
            Write-Host ""
            WriteWarn "Diese Changes koennten zu Konflikten fuehren."
            Write-Host "  [J] Ja, fortfahren  [N] Nein  [S] Stash changes" -ForegroundColor Cyan
            $choice = Read-Host "  Ihre Wahl"
            
            switch ($choice.ToUpper()) {
                "J" {
                    WriteInfo "Fahre fort..."
                    WriteLog "User: Fortfahren"
                    return $true
                }
                "S" {
                    WriteInfo "Stashe changes..."
                    WriteLog "User: Stash"
                    git stash save "Auto-stash $(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')"
                    if ($LASTEXITCODE -eq 0) {
                        WriteOK "Changes gestashed"
                        WriteLog "Stash OK"
                        return $true
                    } else {
                        WriteError "Stash fehlgeschlagen"
                        WriteLog "ERROR: Stash failed"
                        return $false
                    }
                }
                default {
                    WriteInfo "Abgebrochen"
                    WriteLog "User: Abbruch"
                    return $false
                }
            }
        }
    } catch {
        WriteError "Status check failed: $_"
        WriteLog "ERROR: Status check - $_"
        return $false
    }
}

# Sync with Remote
function SyncWithRemote {
    WriteStep "3" "GitHub Sync starten..."
    WriteLog "Starte GitHub Sync"
    
    $branch = git branch --show-current
    WriteInfo "Branch: $branch"
    WriteLog "Branch: $branch"
    
    # Check Remote
    try {
        $remotes = git remote
        if ([string]::IsNullOrWhiteSpace($remotes)) {
            WriteWarn "Kein Remote konfiguriert"
            WriteInfo "Fahre ohne Pull fort (nur lokal)"
            WriteLog "WARN: Kein Remote"
            return $true
        }
        WriteOK "Remote gefunden: origin"
        WriteLog "Remote OK"
    } catch {
        WriteWarn "Remote check failed: $_"
        WriteLog "WARN: Remote check failed - $_"
        return $true
    }
    
    # Fetch
    WriteInfo "Fetching..."
    WriteLog "Fetching..."
    
    try {
        $fetchOutput = git fetch origin $branch 2>&1
        if ($LASTEXITCODE -eq 0) {
            WriteOK "Fetch OK"
            WriteLog "Fetch OK"
        } else {
            WriteWarn "Fetch hatte Probleme (offline?)"
            WriteLog "WARN: Fetch exit $LASTEXITCODE"
            Write-Host ""
            Write-Host "  Fortfahren ohne Remote-Sync? [J/N]" -ForegroundColor Yellow
            $choice = Read-Host
            if ($choice.ToUpper() -ne "J") {
                WriteLog "User: Abbruch nach Fetch"
                return $false
            }
            WriteLog "User: Fortfahren ohne Fetch"
            return $true
        }
    } catch {
        WriteWarn "Fetch exception: $_"
        WriteLog "WARN: Fetch exception - $_"
    }
    
    # Check if remote has updates
    $localCommit = git rev-parse HEAD
    $remoteCommit = git rev-parse "origin/$branch" 2>$null
    
    if ($LASTEXITCODE -ne 0) {
        WriteWarn "Remote branch existiert nicht"
        WriteInfo "Fahre ohne Pull fort"
        WriteLog "WARN: Remote branch nicht gefunden"
        return $true
    }
    
    if ($localCommit -eq $remoteCommit) {
        WriteOK "Bereits auf dem neuesten Stand"
        WriteLog "Bereits aktuell"
        return $true
    }
    
    # Pull
    WriteInfo "Pulling changes from origin/$branch..."
    WriteLog "Pulling..."
    
    try {
        $pullOutput = git pull origin $branch 2>&1
        if ($LASTEXITCODE -eq 0) {
            WriteOK "Pull erfolgreich!"
            WriteLog "Pull OK"
            
            # Show changed files
            $changes = git diff --name-only $localCommit HEAD
            if ($changes) {
                WriteInfo "Geaenderte Dateien:"
                $changes -split "`n" | Select-Object -First 10 | ForEach-Object {
                    if ($_.Trim()) {
                        Write-Host "      - $_" -ForegroundColor Cyan
                    }
                }
            }
            return $true
        } else {
            WriteError "Pull fehlgeschlagen!"
            WriteLog "ERROR: Pull failed - exit $LASTEXITCODE"
            
            if ($pullOutput -match "CONFLICT|Merge conflict") {
                WriteError "MERGE-KONFLIKT erkannt!"
                WriteInfo "Bitte loesen Sie die Konflikte manuell:"
                Write-Host "      1. git status" -ForegroundColor Cyan
                Write-Host "      2. Konflikte loesen" -ForegroundColor Cyan
                Write-Host "      3. git add ." -ForegroundColor Cyan
                Write-Host "      4. git commit" -ForegroundColor Cyan
                WriteLog "ERROR: Merge conflict"
            }
            return $false
        }
    } catch {
        WriteError "Pull exception: $_"
        WriteLog "ERROR: Pull exception - $_"
        return $false
    }
}

# Python Environment Check
function CheckPythonEnvironment {
    WriteStep "4" "Python Environment pruefen..."
    WriteLog "Pruefe Python Environment"
    
    try {
        $pythonVersion = python --version 2>&1
        WriteOK "Python: $pythonVersion"
        WriteLog "Python OK: $pythonVersion"
    } catch {
        WriteError "Python nicht gefunden!"
        WriteLog "ERROR: Python nicht verfuegbar"
        return $false
    }
    
    $venvPath = Join-Path $BackendDir ".venv"
    if (Test-Path $venvPath) {
        WriteOK "Virtual Environment gefunden"
        WriteLog "venv OK"
        return $true
    } else {
        WriteWarn "Virtual Environment nicht gefunden"
        WriteInfo "Erstelle neues venv..."
        WriteLog "WARN: venv nicht gefunden"
        
        try {
            Push-Location $BackendDir
            python -m venv .venv
            
            if ($LASTEXITCODE -eq 0) {
                WriteOK "venv erstellt"
                WriteLog "venv erstellt"
                
                WriteInfo "Installiere Dependencies..."
                .\.venv\Scripts\python.exe -m pip install -r requirements.txt
                
                if ($LASTEXITCODE -eq 0) {
                    WriteOK "Dependencies installiert"
                    WriteLog "Dependencies OK"
                    Pop-Location
                    return $true
                } else {
                    WriteError "Dependencies Installation fehlgeschlagen"
                    WriteLog "ERROR: pip install failed"
                    Pop-Location
                    return $false
                }
            } else {
                WriteError "venv Erstellung fehlgeschlagen"
                WriteLog "ERROR: venv creation failed"
                Pop-Location
                return $false
            }
        } catch {
            WriteError "Exception: $_"
            WriteLog "ERROR: venv setup - $_"
            Pop-Location
            return $false
        }
    }
}

# Start Auto Claude
function StartAutoClaude {
    param([string]$RunMode, [string]$SpecNumber, [string]$TaskDescription)
    
    WriteStep "5" "Auto Claude starten..."
    WriteLog "Starte Auto Claude - Mode: $RunMode"
    
    Push-Location $BackendDir
    
    try {
        switch ($RunMode) {
            "interactive" {
                if ($TaskDescription) {
                    WriteInfo "Starte mit Task: $TaskDescription"
                    WriteLog "spec_runner.py --task '$TaskDescription'"
                    python spec_runner.py --task $TaskDescription
                } else {
                    WriteInfo "Starte interaktiv"
                    WriteLog "spec_runner.py --interactive"
                    python spec_runner.py --interactive
                }
            }
            "run" {
                if (-not $SpecNumber) {
                    WriteError "Spec Nummer erforderlich!"
                    WriteLog "ERROR: Spec number missing"
                    Pop-Location
                    return $false
                }
                WriteInfo "Fuehre Spec $SpecNumber aus"
                WriteLog "run.py --spec $SpecNumber"
                python run.py --spec $SpecNumber
            }
            "monitor" {
                WriteInfo "Starte Monitor"
                WriteLog "live_monitor.py"
                python live_monitor.py --follow-all
            }
            default {
                WriteError "Unbekannter Modus: $RunMode"
                WriteLog "ERROR: Unknown mode: $RunMode"
                Pop-Location
                return $false
            }
        }
        
        WriteLog "Auto Claude beendet - Exit: $LASTEXITCODE"
        Pop-Location
        return $true
    } catch {
        WriteError "Start exception: $_"
        WriteLog "ERROR: Start exception - $_"
        Pop-Location
        return $false
    }
}

# Main Program
Clear-Host
WriteHeader "AUTO CLAUDE - SMART STARTER MIT GITHUB SYNC"

WriteLog "=========================================="
WriteLog "NEUER START"
WriteLog "Mode: $Mode, Spec: $Spec, Task: $Task, NoPull: $NoPull"
WriteLog "=========================================="

Set-Location $ProjectRoot

# Run checks
if (-not (CheckGitRepository)) {
    Write-Host ""
    Write-Host "[ABBRUCH] Kein Git Repository" -ForegroundColor Red
    WriteLog "ABBRUCH: Kein Git Repository"
    exit 1
}

if (-not (CheckUncommittedChanges)) {
    Write-Host ""
    Write-Host "[ABBRUCH] Uncommitted Changes Problem" -ForegroundColor Red
    WriteLog "ABBRUCH: Uncommitted Changes"
    exit 1
}

if (-not $NoPull) {
    if (-not (SyncWithRemote)) {
        Write-Host ""
        Write-Host "[ABBRUCH] GitHub Sync fehlgeschlagen" -ForegroundColor Red
        WriteLog "ABBRUCH: Sync failed"
        exit 1
    }
} else {
    WriteWarn "Pull uebersprungen (--NoPull)"
    WriteLog "Pull uebersprungen"
}

if (-not (CheckPythonEnvironment)) {
    Write-Host ""
    Write-Host "[ABBRUCH] Python Environment Problem" -ForegroundColor Red
    WriteLog "ABBRUCH: Python Environment"
    exit 1
}

Write-Host ""
WriteHeader "ALLE CHECKS BESTANDEN - STARTE AUTO CLAUDE"
Write-Host ""

Start-Sleep -Seconds 1

if (-not (StartAutoClaude -RunMode $Mode -SpecNumber $Spec -TaskDescription $Task)) {
    Write-Host ""
    Write-Host "[ERROR] Auto Claude Exit mit Fehler" -ForegroundColor Red
    WriteLog "ERROR: Auto Claude Exit"
    exit 1
}

Write-Host ""
Write-Host "[OK] Fertig!" -ForegroundColor Green
WriteLog "Erfolgreich beendet"
