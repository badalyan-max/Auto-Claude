# Auto-Claude Data Sync - Pull von GitHub
# Verwendung: .\Data-Sync-Pull.ps1

param(
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🔄 Auto-Claude Data Sync - PULL" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Prüfe ob wir im richtigen Verzeichnis sind
if (-not (Test-Path ".git")) {
    Write-Host "❌ Fehler: Nicht im Git-Repository!" -ForegroundColor Red
    Write-Host "   Bitte wechsle zu: C:\Projekte\auto-claude" -ForegroundColor Yellow
    exit 1
}

# Aktuellen Branch speichern
Write-Host "📍 Aktueller Branch: " -NoNewline
$currentBranch = git branch --show-current
Write-Host "$currentBranch" -ForegroundColor Green

# Warne vor lokalen Änderungen in .auto-claude
if (Test-Path ".auto-claude") {
    $localChanges = git status --porcelain .auto-claude
    if ($localChanges -and -not $Force) {
        Write-Host ""
        Write-Host "⚠️  WARNUNG: Lokale Änderungen in .auto-claude gefunden!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Änderungen:" -ForegroundColor Cyan
        git status --short .auto-claude
        Write-Host ""
        Write-Host "Diese Änderungen werden überschrieben!" -ForegroundColor Red
        Write-Host ""
        $confirmation = Read-Host "Fortfahren? (j/N)"
        if ($confirmation -ne "j" -and $confirmation -ne "J") {
            Write-Host "❌ Abgebrochen!" -ForegroundColor Yellow
            exit 0
        }
    }
}

# Zu data-sync Branch wechseln
Write-Host ""
Write-Host "🔀 Wechsle zu data-sync Branch..." -ForegroundColor Yellow
try {
    git checkout data-sync 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Branch 'data-sync' existiert nicht!" -ForegroundColor Red
        Write-Host "   Hole Branch von GitHub..." -ForegroundColor Yellow
        git fetch origin data-sync:data-sync
        git checkout data-sync
    }
} catch {
    Write-Host "❌ Fehler beim Branch-Wechsel!" -ForegroundColor Red
    exit 1
}

# Hole neueste Änderungen von GitHub
Write-Host "📥 Hole neueste Änderungen von GitHub..." -ForegroundColor Yellow
git fetch origin data-sync

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Fetch fehlgeschlagen!" -ForegroundColor Red
    git checkout $currentBranch
    exit 1
}

# Prüfe ob es Updates gibt
$behind = git rev-list HEAD..origin/data-sync --count
if ($behind -eq 0) {
    Write-Host "✅ Bereits auf dem neuesten Stand!" -ForegroundColor Green
} else {
    Write-Host "📦 $behind neue(s) Update(s) verfügbar!" -ForegroundColor Cyan

    # Zeige Änderungen
    Write-Host ""
    Write-Host "📝 Änderungen:" -ForegroundColor Cyan
    git log HEAD..origin/data-sync --oneline --no-decorate

    # Pull Änderungen
    Write-Host ""
    Write-Host "⬇️  Übernehme Änderungen..." -ForegroundColor Yellow
    git pull origin data-sync

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Pull fehlgeschlagen!" -ForegroundColor Red
        git checkout $currentBranch
        exit 1
    }
}

# Zurück zum ursprünglichen Branch
Write-Host ""
Write-Host "🔙 Wechsle zurück zu $currentBranch..." -ForegroundColor Yellow
git checkout $currentBranch

# Kopiere .auto-claude Daten vom data-sync Branch
Write-Host "📋 Übernehme .auto-claude Daten..." -ForegroundColor Yellow
git checkout data-sync -- .auto-claude/

Write-Host ""
Write-Host "✅ Data-Sync erfolgreich abgeschlossen!" -ForegroundColor Green
Write-Host "🎯 Deine Kanban-Daten sind jetzt aktuell." -ForegroundColor Green
Write-Host ""

# Zeige letzten Sync-Zeitpunkt
$lastSync = git log data-sync -1 --format="%ci - %s"
Write-Host "🕐 Letzter Sync: $lastSync" -ForegroundColor Cyan
Write-Host ""
