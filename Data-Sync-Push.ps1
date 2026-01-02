# Auto-Claude Data Sync - Push zu GitHub
# Verwendung: .\Data-Sync-Push.ps1

param(
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🔄 Auto-Claude Data Sync - PUSH" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Prüfe ob wir im richtigen Verzeichnis sind
if (-not (Test-Path ".git")) {
    Write-Host "❌ Fehler: Nicht im Git-Repository!" -ForegroundColor Red
    Write-Host "   Bitte wechsle zu: C:\Projekte\auto-claude" -ForegroundColor Yellow
    exit 1
}

# Prüfe ob .auto-claude existiert
if (-not (Test-Path ".auto-claude")) {
    Write-Host "⚠️  Warnung: .auto-claude Verzeichnis nicht gefunden!" -ForegroundColor Yellow
    Write-Host "   Nichts zu synchronisieren." -ForegroundColor Yellow
    exit 0
}

# Aktuellen Branch speichern
Write-Host "📍 Aktueller Branch: " -NoNewline
$currentBranch = git branch --show-current
Write-Host "$currentBranch" -ForegroundColor Green

# Zu data-sync Branch wechseln
Write-Host ""
Write-Host "🔀 Wechsle zu data-sync Branch..." -ForegroundColor Yellow
try {
    git checkout data-sync 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Branch 'data-sync' existiert nicht!" -ForegroundColor Red
        Write-Host "   Erstelle Branch..." -ForegroundColor Yellow
        git checkout -b data-sync
    }
} catch {
    Write-Host "❌ Fehler beim Branch-Wechsel!" -ForegroundColor Red
    exit 1
}

# Hole neueste Änderungen von Remote
Write-Host "📥 Hole neueste Änderungen von GitHub..." -ForegroundColor Yellow
git fetch origin data-sync 2>$null

# Merge falls nötig (automatisch mit ours-Strategie bei Konflikten)
$remoteBranchExists = git ls-remote --heads origin data-sync
if ($remoteBranchExists) {
    Write-Host "🔀 Merge Remote-Änderungen..." -ForegroundColor Yellow
    git merge origin/data-sync -X ours --no-edit 2>$null
}

# Füge .auto-claude Änderungen hinzu
Write-Host ""
Write-Host "📦 Füge .auto-claude Daten hinzu..." -ForegroundColor Yellow
git add .auto-claude

# Prüfe ob es Änderungen gibt
$changes = git status --porcelain
if (-not $changes) {
    Write-Host "✅ Keine neuen Änderungen zu synchronisieren!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔙 Wechsle zurück zu $currentBranch..." -ForegroundColor Yellow
    git checkout $currentBranch
    Write-Host ""
    Write-Host "✨ Fertig!" -ForegroundColor Green
    exit 0
}

# Zeige Änderungen
Write-Host ""
Write-Host "📝 Änderungen:" -ForegroundColor Cyan
git status --short .auto-claude

if ($DryRun) {
    Write-Host ""
    Write-Host "🔍 DRY RUN - Keine Änderungen durchgeführt!" -ForegroundColor Yellow
    git checkout $currentBranch
    exit 0
}

# Erstelle Commit
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$commitMessage = "sync: update kanban data [$timestamp]"

Write-Host ""
Write-Host "💾 Erstelle Commit..." -ForegroundColor Yellow
git commit -m $commitMessage

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Commit fehlgeschlagen!" -ForegroundColor Red
    git checkout $currentBranch
    exit 1
}

# Pushe zu GitHub
Write-Host "📤 Pushe zu GitHub..." -ForegroundColor Yellow
git push origin data-sync

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Push fehlgeschlagen!" -ForegroundColor Red
    Write-Host "   Versuche: git push origin data-sync --force" -ForegroundColor Yellow
    git checkout $currentBranch
    exit 1
}

# Zurück zum ursprünglichen Branch
Write-Host ""
Write-Host "🔙 Wechsle zurück zu $currentBranch..." -ForegroundColor Yellow
git checkout $currentBranch

Write-Host ""
Write-Host "✅ Data-Sync erfolgreich abgeschlossen!" -ForegroundColor Green
Write-Host "🎯 Deine Kanban-Daten sind jetzt auf GitHub." -ForegroundColor Green
Write-Host ""
Write-Host "💡 Auf dem Laptop:" -ForegroundColor Cyan
Write-Host "   .\Data-Sync-Pull.ps1" -ForegroundColor White
Write-Host ""
