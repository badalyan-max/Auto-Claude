<#
.SYNOPSIS
    Automatisches Backup-System für Auto Claude zu GitHub

.DESCRIPTION
    Überwacht Änderungen an der App und speichert sie automatisch in deinen Fork.
    - Checked alle 5 Minuten auf Änderungen
    - Committed und pushed automatisch
    - Ignoriert Projekt-Specs (.auto-claude/specs/)
    - Läuft im Hintergrund

.EXAMPLE
    .\Auto-Save-Zu-GitHub.ps1
#>

param(
    [switch]$Stop,
    [switch]$Status
)

$ErrorActionPreference = "Continue"

# Farben
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }

# Konfig
$PROJECT_DIR = "c:\Projekte\auto-claude"
$LOCK_FILE = Join-Path $PROJECT_DIR ".auto-save-running.lock"
$LOG_FILE = Join-Path $PROJECT_DIR ".auto-save.log"
$CHECK_INTERVAL = 300  # 5 Minuten in Sekunden

function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
}

function Get-AutoSaveStatus {
    if (Test-Path $LOCK_FILE) {
        try {
            $lockData = Get-Content $LOCK_FILE -Raw | ConvertFrom-Json
            $processId = $lockData.pid
            
            # Prüfe ob Prozess noch läuft
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($process) {
                Write-Success "Auto-Save läuft (PID: $processId)"
                Write-Host "   Gestartet: $($lockData.started)" -ForegroundColor White
                Write-Host "   Intervall: $CHECK_INTERVAL Sekunden (5 Minuten)" -ForegroundColor White
                return $true
            } else {
                Write-Warning "Lock-File existiert, aber Prozess läuft nicht mehr"
                Remove-Item $LOCK_FILE -Force
                return $false
            }
        } catch {
            Write-Warning "Fehler beim Lesen der Lock-Datei: $_"
            return $false
        }
    } else {
        Write-Info "Auto-Save läuft NICHT"
        return $false
    }
}

function Stop-AutoSave {
    if (Test-Path $LOCK_FILE) {
        try {
            $lockData = Get-Content $LOCK_FILE -Raw | ConvertFrom-Json
            $processId = $lockData.pid
            
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($process) {
                Stop-Process -Id $processId -Force
                Write-Success "Auto-Save beendet (PID: $processId)"
            }
            
            Remove-Item $LOCK_FILE -Force
            Write-Log "Auto-Save gestoppt"
        } catch {
            Write-Error "Fehler beim Stoppen: $_"
        }
    } else {
        Write-Info "Auto-Save läuft nicht"
    }
}

# Haupt-Funktion
function Start-AutoSave {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  AUTO-SAVE ZU GITHUB - GESTARTET" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    # Wechsle ins Projekt-Verzeichnis
    Set-Location $PROJECT_DIR
    
    # Erstelle Lock-File
    $lockData = @{
        pid = $PID
        started = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    } | ConvertTo-Json
    $lockData | Out-File -FilePath $LOCK_FILE -Encoding UTF8
    
    Write-Log "Auto-Save gestartet (PID: $PID)"
    Write-Success "Auto-Save aktiviert!"
    Write-Host ""
    Write-Host "Was passiert:" -ForegroundColor Cyan
    Write-Host "  ✓ Prüft alle 5 Minuten auf Änderungen" -ForegroundColor White
    Write-Host "  ✓ Committed automatisch mit Zeitstempel" -ForegroundColor White
    Write-Host "  ✓ Pushed zu deinem Fork (badalyan-max/Auto-Claude)" -ForegroundColor White
    Write-Host "  ✓ Ignoriert .auto-claude/specs/ (Projekte)" -ForegroundColor White
    Write-Host ""
    Write-Host "Läuft im Hintergrund - Du kannst dieses Fenster schließen!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Zum Stoppen:" -ForegroundColor Yellow
    Write-Host "  .\Auto-Save-Zu-GitHub.ps1 -Stop" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Status prüfen:" -ForegroundColor Yellow
    Write-Host "  .\Auto-Save-Zu-GitHub.ps1 -Status" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Log ansehen:" -ForegroundColor Yellow
    Write-Host "  Get-Content .auto-save.log -Tail 20" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    $lastCommitHash = ""
    $consecutiveErrors = 0
    
    while ($true) {
        try {
            # Prüfe auf Änderungen (ignoriere .auto-claude/specs/)
            $status = git status --short 2>&1 | Where-Object {
                $_ -and 
                $_ -notmatch "^\?\?" -and  # Ignoriere untracked files erstmal
                $_ -notmatch "\.auto-claude[/\\]specs" -and  # Ignoriere specs
                $_ -notmatch "\.auto-save" -and  # Ignoriere Auto-Save Dateien
                $_ -notmatch "node_modules" -and  # Ignoriere node_modules
                $_ -notmatch "\.git" -and  # Ignoriere .git
                $_ -notmatch "\.worktrees"  # Ignoriere worktrees
            }
            
            if ($status) {
                Write-Log "Änderungen erkannt - starte Auto-Save"
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] " -NoNewline -ForegroundColor Gray
                Write-Host "Änderungen gefunden - speichere zu GitHub..." -ForegroundColor Yellow
                
                # Zeige was geändert wurde
                Write-Host "   Geänderte Dateien:" -ForegroundColor Gray
                $status | ForEach-Object {
                    Write-Host "     $_" -ForegroundColor White
                }
                
                # Add (nur tracked files)
                git add -u
                
                # Commit mit Zeitstempel
                $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                $commitMsg = "auto-save: Automatisches Backup vom $timestamp"
                git commit -m $commitMsg 2>&1 | Out-Null
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Log "Committed: $commitMsg"
                    
                    # Push zu origin (deinem Fork)
                    Write-Host "   Pushing zu GitHub..." -ForegroundColor Cyan
                    $pushResult = git push origin develop 2>&1
                    
                    if ($LASTEXITCODE -eq 0) {
                        Write-Success "Erfolgreich zu GitHub gespeichert!"
                        Write-Log "Erfolgreich gepushed"
                        $consecutiveErrors = 0
                        
                        # Zeige die letzten 3 Commits
                        Write-Host "   Letzte Backups:" -ForegroundColor Gray
                        git log --oneline -3 | ForEach-Object {
                            Write-Host "     $_" -ForegroundColor White
                        }
                    } else {
                        Write-Warning "Push fehlgeschlagen: $pushResult"
                        Write-Log "Push-Fehler: $pushResult"
                        $consecutiveErrors++
                    }
                } else {
                    Write-Warning "Commit fehlgeschlagen (möglicherweise keine Änderungen)"
                }
                
                Write-Host ""
            } else {
                # Stille Prüfung - nur ins Log
                Write-Log "Keine Änderungen erkannt"
            }
            
            # Bei zu vielen Fehlern stoppen
            if ($consecutiveErrors -gt 5) {
                Write-Error "Zu viele Fehler hintereinander - Auto-Save wird beendet"
                Write-Log "Auto-Save beendet wegen zu vieler Fehler"
                break
            }
            
            # Warte bis zur nächsten Prüfung
            Start-Sleep -Seconds $CHECK_INTERVAL
            
        } catch {
            Write-Warning "Fehler im Auto-Save Loop: $_"
            Write-Log "Fehler: $_"
            $consecutiveErrors++
            Start-Sleep -Seconds 60  # Bei Fehler 1 Minute warten
        }
    }
    
    # Cleanup
    if (Test-Path $LOCK_FILE) {
        Remove-Item $LOCK_FILE -Force
    }
}

# Haupt-Logik
if ($Status) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  AUTO-SAVE STATUS" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Get-AutoSaveStatus
    Write-Host ""
    
    if (Test-Path $LOG_FILE) {
        Write-Host "Letzte Log-Einträge:" -ForegroundColor Cyan
        Get-Content $LOG_FILE -Tail 10 | ForEach-Object {
            Write-Host "  $_" -ForegroundColor White
        }
    }
    Write-Host ""
    exit 0
}

if ($Stop) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  AUTO-SAVE STOPPEN" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Stop-AutoSave
    Write-Host ""
    exit 0
}

# Prüfe ob bereits läuft
if (Test-Path $LOCK_FILE) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host "  AUTO-SAVE LÄUFT BEREITS" -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host ""
    
    $isRunning = Get-AutoSaveStatus
    
    if ($isRunning) {
        Write-Host ""
        Write-Host "Möchtest du es neu starten?" -ForegroundColor Yellow
        $response = Read-Host "(j/n)"
        
        if ($response -eq "j" -or $response -eq "J") {
            Stop-AutoSave
            Start-Sleep -Seconds 2
        } else {
            Write-Host ""
            Write-Info "Auto-Save läuft weiter"
            exit 0
        }
    }
}

# Starte Auto-Save
Start-AutoSave
