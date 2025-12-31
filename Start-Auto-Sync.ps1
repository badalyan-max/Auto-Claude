<#
.SYNOPSIS
    Startet automatische Synchronisation der Auto-Claude App zu deinem Fork

.DESCRIPTION
    Überwacht kontinuierlich Änderungen an der App und pushed sie automatisch
    zu deinem GitHub Fork (badalyan-max/Auto-Claude).
    
    Läuft im Vordergrund, damit du siehst was passiert.
    
.EXAMPLE
    .\Start-Auto-Sync.ps1
#>

$ErrorActionPreference = "Stop"

# Farben
function Write-Header { param($Text) Write-Host "`n$Text`n" -ForegroundColor Cyan }
function Write-Success { param($Text) Write-Host "✅ $Text" -ForegroundColor Green }
function Write-Info { param($Text) Write-Host "ℹ️  $Text" -ForegroundColor Cyan }

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  AUTO-SYNC FÜR AUTO-CLAUDE APP" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Prüfe ob im richtigen Verzeichnis
if (-not (Test-Path ".git")) {
    Write-Host "❌ Fehler: Muss im auto-claude Verzeichnis ausgeführt werden!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Führe aus: cd c:\Projekte\auto-claude" -ForegroundColor Yellow
    pause
    exit 1
}

# Prüfe Python
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $version -match "Python 3\.1[2-9]") {
            $pythonCmd = $cmd
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "❌ Python 3.12+ nicht gefunden!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Bitte installiere Python 3.12 oder höher" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Success "Python gefunden: $pythonCmd"
Write-Info "Fork: https://github.com/badalyan-max/Auto-Claude"
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Starte Auto-Sync
try {
    & $pythonCmd apps\backend\app_auto_sync.py --watch --interval 60
} catch {
    Write-Host ""
    Write-Host "❌ Fehler beim Starten: $_" -ForegroundColor Red
    Write-Host ""
    pause
    exit 1
}
