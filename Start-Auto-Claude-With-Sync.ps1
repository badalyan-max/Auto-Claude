#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Bombensicherer Auto Claude Starter mit automatischem GitHub Sync
.DESCRIPTION
    - Pullt automatisch neueste Änderungen von GitHub
    - Prüft auf Merge-Konflikte
    - Startet Auto Claude nur wenn alles sauber ist
    - 100% sichere Fehlerbehandlung
.PARAMETER Mode
    interactive = Interaktiver Spec Creator (Standard)
    run = Führt bestehende Spec aus (benötigt --spec)
    monitor = Startet Live Monitor
.PARAMETER Spec
    Spec Nummer (z.B. "001") für --run Mode
.PARAMETER Task
    Task Beschreibung für --interactive Mode
.PARAMETER NoPull
    Überspringt den Git Pull (für Tests)
.EXAMPLE
    .\Start-Auto-Claude-With-Sync.ps1
    .\Start-Auto-Claude-With-Sync.ps1 -Mode run -Spec 001
    .\Start-Auto-Claude-With-Sync.ps1 -Task "Add login feature"
#>

param(
    [ValidateSet("interactive", "run", "monitor")]
    [string]$Mode = "interactive",
    
    [string]$Spec = "",
    
    [string]$Task = "",
    
    [switch]$NoPull = $false
)

# ============================================================================
# KONFIGURATION
# ============================================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "apps\backend"
$LogFile = Join-Path $ProjectRoot ".auto-claude\sync-log.txt"

# Farben
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White",
        [switch]$NoNewline
    )
    
    $params = @{
        Object = $Message
        ForegroundColor = $Color
    }
    
    if ($NoNewline) {
        $params.Add("NoNewline", $true)
    }
    
    Write-Host @params
}

function Write-Log {
    param([string]$Message)
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    
    # Erstelle Log-Verzeichnis falls nötig
    $logDir = Split-Path $LogFile -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    Add-Content -Path $LogFile -Value $logMessage -Encoding UTF8
}

function Write-Header {
    param([string]$Text)
    
    Write-Host ""
    Write-ColorOutput "================================================================================" "Cyan"
    Write-ColorOutput "  $Text" "Cyan"
    Write-ColorOutput "================================================================================" "Cyan"
    Write-Host ""
}

function Write-Step {
    param(
        [string]$Number,
        [string]$Text
    )
    
    Write-ColorOutput "[$Number] " "Yellow" -NoNewline
    Write-ColorOutput $Text "White"
}

function Write-Success {
    param([string]$Text)
    Write-ColorOutput "  ✅ $Text" "Green"
}

function Write-Error-Message {
    param([string]$Text)
    Write-ColorOutput "  ❌ $Text" "Red"
}

function Write-Warning-Message {
    param([string]$Text)
    Write-ColorOutput "  ⚠️  $Text" "Yellow"
}

function Write-Info {
    param([string]$Text)
    Write-ColorOutput "  ℹ️  $Text" "Cyan"
}

# ============================================================================
# HAUPTFUNKTIONEN
# ============================================================================

function Test-GitRepository {
    <#
    .SYNOPSIS
        Prüft ob wir in einem Git Repository sind
    #>
    
    Write-Step "1" "Git Repository prüfen..."
    Write-Log "Prüfe Git Repository"
    
    try {
        $gitCheck = git rev-parse --is-inside-work-tree 2>&1
        
        if ($LASTEXITCODE -eq 0 -and $gitCheck -eq "true") {
            Write-Success "Git Repository erkannt"
            Write-Log "Git Repository OK"
            return $true
        } else {
            Write-Error-Message "Kein Git Repository gefunden!"
            Write-Log "ERROR: Kein Git Repository"
            return $false
        }
    } catch {
        Write-Error-Message "Git ist nicht installiert oder nicht im PATH!"
        Write-Log "ERROR: Git nicht verfügbar - $_"
        return $false
    }
}

function Get-CurrentBranch {
    <#
    .SYNOPSIS
        Ermittelt den aktuellen Branch
    #>
    
    try {
        $branch = git branch --show-current
        Write-Log "Aktueller Branch: $branch"
        return $branch
    } catch {
        Write-Log "ERROR: Branch konnte nicht ermittelt werden - $_"
        return $null
    }
}

function Test-UncommittedChanges {
    <#
    .SYNOPSIS
        Prüft auf uncommitted Changes
    #>
    
    Write-Step "2" "Lokale Änderungen prüfen..."
    Write-Log "Prüfe uncommitted changes"
    
    try {
        $status = git status --porcelain
        
        if ([string]::IsNullOrWhiteSpace($status)) {
            Write-Success "Keine uncommitted Changes"
            Write-Log "Keine uncommitted changes"
            return $true
        } else {
            Write-Warning-Message "Es gibt uncommitted Changes:"
            $status -split "`n" | ForEach-Object {
                if ($_.Trim()) {
                    Write-ColorOutput "      $_" "Yellow"
                }
            }
            
            Write-Log "WARN: Uncommitted changes gefunden"
            
            # Frage User ob fortfahren
            Write-Host ""
            Write-ColorOutput "  Möchten Sie fortfahren? Diese Changes könnten zu Konflikten führen." "Yellow"
            Write-ColorOutput "  [J] Ja, fortfahren  [N] Nein, abbrechen  [S] Stash changes" "Cyan"
            
            $choice = Read-Host "  Ihre Wahl"
            
            switch ($choice.ToUpper()) {
                "J" {
                    Write-Info "Fahre fort mit uncommitted changes..."
                    Write-Log "User wählte: Fortfahren mit uncommitted changes"
                    return $true
                }
                "S" {
                    Write-Info "Stashe uncommitted changes..."
                    Write-Log "User wählte: Stash changes"
                    
                    git stash save "Auto-stash before sync $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
                    
                    if ($LASTEXITCODE -eq 0) {
                        Write-Success "Changes gestashed"
                        Write-Log "Changes erfolgreich gestashed"
                        return $true
                    } else {
                        Write-Error-Message "Stash fehlgeschlagen!"
                        Write-Log "ERROR: Stash fehlgeschlagen"
                        return $false
                    }
                }
                default {
                    Write-Info "Abgebrochen durch User"
                    Write-Log "User wählte: Abbrechen"
                    return $false
                }
            }
        }
    } catch {
        Write-Error-Message "Fehler beim Prüfen der Changes: $_"
        Write-Log "ERROR: Status check fehlgeschlagen - $_"
        return $false
    }
}

function Sync-WithRemote {
    <#
    .SYNOPSIS
        Synchronisiert mit GitHub (Pull)
    #>
    
    Write-Step "3" "GitHub Sync starten..."
    Write-Log "Starte GitHub Sync"
    
    $branch = Get-CurrentBranch
    
    if (-not $branch) {
        Write-Error-Message "Branch konnte nicht ermittelt werden"
        return $false
    }
    
    Write-Info "Branch: $branch"
    
    # Prüfe Remote
    try {
        $remotes = git remote
        
        if ([string]::IsNullOrWhiteSpace($remotes)) {
            Write-Warning-Message "Kein Remote Repository konfiguriert"
            Write-Info "Fahre ohne Pull fort (nur lokal)"
            Write-Log "WARN: Kein Remote vorhanden"
            return $true
        }
        
        Write-Success "Remote gefunden: origin"
        Write-Log "Remote OK"
        
    } catch {
        Write-Warning-Message "Remote check fehlgeschlagen: $_"
        Write-Log "WARN: Remote check failed - $_"
        return $true  # Trotzdem fortfahren
    }
    
    # Fetch zuerst
    Write-Info "Fetching remote changes..."
    Write-Log "Fetching..."
    
    try {
        $fetchOutput = git fetch origin $branch 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Fetch erfolgreich"
            Write-Log "Fetch OK"
        } else {
            Write-Warning-Message "Fetch hatte Probleme (möglicherweise offline?)"
            Write-Log "WARN: Fetch exit code $LASTEXITCODE - $fetchOutput"
            
            # Frage ob fortfahren
            Write-Host ""
            Write-ColorOutput "  Möchten Sie ohne Remote-Sync fortfahren?" "Yellow"
            $choice = Read-Host "  [J/N]"
            
            if ($choice.ToUpper() -ne "J") {
                Write-Log "User wählte: Abbrechen nach Fetch-Fehler"
                return $false
            }
            
            Write-Log "User wählte: Fortfahren ohne Fetch"
            return $true
        }
    } catch {
        Write-Warning-Message "Fetch exception: $_"
        Write-Log "WARN: Fetch exception - $_"
    }
    
    # Prüfe ob Remote Updates hat
    $localCommit = git rev-parse HEAD
    $remoteCommit = git rev-parse "origin/$branch" 2>$null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Warning-Message "Remote branch existiert nicht"
        Write-Info "Fahre ohne Pull fort"
        Write-Log "WARN: Remote branch nicht gefunden"
        return $true
    }
    
    if ($localCommit -eq $remoteCommit) {
        Write-Success "Bereits auf dem neuesten Stand"
        Write-Log "Bereits aktuell"
        return $true
    }
    
    # Pull durchführen
    Write-Info "Pulling changes from origin/$branch..."
    Write-Log "Pulling..."
    
    try {
        $pullOutput = git pull origin $branch 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Pull erfolgreich!"
            Write-Log "Pull OK - $pullOutput"
            
            # Zeige geänderte Dateien
            $changes = git diff --name-only $localCommit HEAD
            if ($changes) {
                Write-Info "Geänderte Dateien:"
                $changes -split "`n" | ForEach-Object {
                    if ($_.Trim()) {
                        Write-ColorOutput "      - $_" "Cyan"
                    }
                }
            }
            
            return $true
        } else {
            Write-Error-Message "Pull fehlgeschlagen!"
            Write-Log "ERROR: Pull failed - exit code $LASTEXITCODE - $pullOutput"
            
            # Prüfe auf Merge-Konflikte
            if ($pullOutput -match "CONFLICT|Merge conflict") {
                Write-Error-Message "MERGE-KONFLIKT erkannt!"
                Write-Info "Bitte lösen Sie die Konflikte manuell:"
                Write-ColorOutput "      1. git status" "Cyan"
                Write-ColorOutput "      2. Konflikte lösen" "Cyan"
                Write-ColorOutput "      3. git add ." "Cyan"
                Write-ColorOutput "      4. git commit" "Cyan"
                Write-Log "ERROR: Merge conflict"
            }
            
            return $false
        }
    } catch {
        Write-Error-Message "Pull exception: $_"
        Write-Log "ERROR: Pull exception - $_"
        return $false
    }
}

function Test-PythonEnvironment {
    <#
    .SYNOPSIS
        Prüft Python und Virtual Environment
    #>
    
    Write-Step "4" "Python Environment prüfen..."
    Write-Log "Prüfe Python Environment"
    
    # Prüfe Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Success "Python: $pythonVersion"
        Write-Log "Python OK: $pythonVersion"
    } catch {
        Write-Error-Message "Python nicht gefunden!"
        Write-Log "ERROR: Python nicht verfügbar"
        return $false
    }
    
    # Prüfe Virtual Environment
    $venvPath = Join-Path $BackendDir ".venv"
    
    if (Test-Path $venvPath) {
        Write-Success "Virtual Environment gefunden"
        Write-Log "venv OK"
        return $true
    } else {
        Write-Warning-Message "Virtual Environment nicht gefunden"
        Write-Info "Erstelle neues Virtual Environment..."
        Write-Log "WARN: venv nicht gefunden, erstelle neu"
        
        try {
            Push-Location $BackendDir
            
            python -m venv .venv
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Virtual Environment erstellt"
                Write-Log "venv erfolgreich erstellt"
                
                # Installiere Dependencies
                Write-Info "Installiere Dependencies..."
                
                .\.venv\Scripts\python.exe -m pip install -r requirements.txt
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "Dependencies installiert"
                    Write-Log "Dependencies OK"
                    Pop-Location
                    return $true
                } else {
                    Write-Error-Message "Dependencies Installation fehlgeschlagen"
                    Write-Log "ERROR: pip install failed"
                    Pop-Location
                    return $false
                }
            } else {
                Write-Error-Message "Virtual Environment Erstellung fehlgeschlagen"
                Write-Log "ERROR: venv creation failed"
                Pop-Location
                return $false
            }
        } catch {
            Write-Error-Message "Exception: $_"
            Write-Log "ERROR: venv setup exception - $_"
            Pop-Location
            return $false
        }
    }
}

function Start-AutoClaudeMode {
    <#
    .SYNOPSIS
        Startet Auto Claude im gewählten Modus
    #>
    
    param(
        [string]$RunMode,
        [string]$SpecNumber,
        [string]$TaskDescription
    )
    
    Write-Step "5" "Auto Claude starten..."
    Write-Log "Starte Auto Claude - Mode: $RunMode"
    
    Push-Location $BackendDir
    
    try {
        switch ($RunMode) {
            "interactive" {
                if ($TaskDescription) {
                    Write-Info "Starte Spec Creator mit Task: $TaskDescription"
                    Write-Log "Starting spec_runner.py mit --task '$TaskDescription'"
                    
                    python spec_runner.py --task $TaskDescription
                } else {
                    Write-Info "Starte interaktiven Spec Creator"
                    Write-Log "Starting spec_runner.py --interactive"
                    
                    python spec_runner.py --interactive
                }
            }
            
            "run" {
                if (-not $SpecNumber) {
                    Write-Error-Message "Spec Nummer erforderlich für --run Mode!"
                    Write-Log "ERROR: Spec number missing"
                    Pop-Location
                    return $false
                }
                
                Write-Info "Führe Spec $SpecNumber aus"
                Write-Log "Starting run.py --spec $SpecNumber"
                
                python run.py --spec $SpecNumber
            }
            
            "monitor" {
                Write-Info "Starte Live Monitor"
                Write-Log "Starting live_monitor.py"
                
                python live_monitor.py --follow-all
            }
            
            default {
                Write-Error-Message "Unbekannter Modus: $RunMode"
                Write-Log "ERROR: Unknown mode: $RunMode"
                Pop-Location
                return $false
            }
        }
        
        Write-Log "Auto Claude beendet - Exit Code: $LASTEXITCODE"
        Pop-Location
        return $true
        
    } catch {
        Write-Error-Message "Exception beim Starten von Auto Claude: $_"
        Write-Log "ERROR: Start exception - $_"
        Pop-Location
        return $false
    }
}

# ============================================================================
# HAUPTPROGRAMM
# ============================================================================

function Main {
    Clear-Host
    
    Write-Header "AUTO CLAUDE - SMART STARTER MIT GITHUB SYNC 🚀"
    
    Write-Log "=========================================="
    Write-Log "NEUER START"
    Write-Log "Mode: $Mode, Spec: $Spec, Task: $Task, NoPull: $NoPull"
    Write-Log "=========================================="
    
    # Wechsle zu Project Root
    Set-Location $ProjectRoot
    
    # 1. Git Repository Check
    if (-not (Test-GitRepository)) {
        Write-Host ""
        Write-ColorOutput "❌ ABBRUCH: Kein Git Repository" "Red"
        Write-Log "ABBRUCH: Kein Git Repository"
        exit 1
    }
    
    # 2. Uncommitted Changes Check
    if (-not (Test-UncommittedChanges)) {
        Write-Host ""
        Write-ColorOutput "❌ ABBRUCH: Uncommitted Changes Problem" "Red"
        Write-Log "ABBRUCH: Uncommitted Changes"
        exit 1
    }
    
    # 3. GitHub Sync (außer wenn --NoPull)
    if (-not $NoPull) {
        if (-not (Sync-WithRemote)) {
            Write-Host ""
            Write-ColorOutput "❌ ABBRUCH: GitHub Sync fehlgeschlagen" "Red"
            Write-Log "ABBRUCH: Sync fehlgeschlagen"
            exit 1
        }
    } else {
        Write-Warning-Message "Pull übersprungen (--NoPull)"
        Write-Log "Pull übersprungen"
    }
    
    # 4. Python Environment Check
    if (-not (Test-PythonEnvironment)) {
        Write-Host ""
        Write-ColorOutput "❌ ABBRUCH: Python Environment Problem" "Red"
        Write-Log "ABBRUCH: Python Environment"
        exit 1
    }
    
    # 5. Auto Claude starten
    Write-Host ""
    Write-Header "ALLE CHECKS BESTANDEN ✅"
    Write-Host ""
    
    Start-Sleep -Seconds 1
    
    if (-not (Start-AutoClaudeMode -RunMode $Mode -SpecNumber $Spec -TaskDescription $Task)) {
        Write-Host ""
        Write-ColorOutput "❌ Auto Claude wurde mit Fehler beendet" "Red"
        Write-Log "FEHLER: Auto Claude Exit"
        exit 1
    }
    
    Write-Host ""
    Write-ColorOutput "✅ Fertig!" "Green"
    Write-Log "Erfolgreich beendet"
}

# ============================================================================
# SCRIPT START
# ============================================================================

try {
    Main
} catch {
    Write-Host ""
    Write-ColorOutput "❌ KRITISCHER FEHLER: $_" "Red"
    Write-Log "KRITISCHER FEHLER: $_"
    Write-Log $_.ScriptStackTrace
    exit 1
}
