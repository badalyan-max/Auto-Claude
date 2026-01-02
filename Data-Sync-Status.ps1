# Auto-Claude Data Sync - Status anzeigen
# Verwendung: .\Data-Sync-Status.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🔄 Auto-Claude Data Sync - STATUS" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Prüfe ob wir im richtigen Verzeichnis sind
if (-not (Test-Path ".git")) {
    Write-Host "❌ Fehler: Nicht im Git-Repository!" -ForegroundColor Red
    Write-Host "   Bitte wechsle zu: C:\Projekte\auto-claude" -ForegroundColor Yellow
    exit 1
}

# Aktueller Branch
$currentBranch = git branch --show-current
Write-Host "📍 Aktueller Branch:  " -NoNewline
Write-Host "$currentBranch" -ForegroundColor Green

# Prüfe ob data-sync Branch existiert
Write-Host ""
Write-Host "─────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

$dataSyncExists = git branch --list data-sync
if (-not $dataSyncExists) {
    Write-Host "⚠️  Branch 'data-sync' existiert noch nicht!" -ForegroundColor Yellow
    Write-Host "   Erstelle ihn mit: git checkout -b data-sync" -ForegroundColor Yellow
    exit 0
}

Write-Host "✅ Branch 'data-sync':  " -NoNewline
Write-Host "Existiert" -ForegroundColor Green

# Hole Remote-Informationen
Write-Host ""
Write-Host "🌐 Prüfe GitHub..." -ForegroundColor Yellow
git fetch origin data-sync 2>$null

# Vergleiche lokal vs remote
$ahead = git rev-list origin/data-sync..data-sync --count 2>$null
$behind = git rev-list data-sync..origin/data-sync --count 2>$null

Write-Host ""
Write-Host "─────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

if ($ahead -eq 0 -and $behind -eq 0) {
    Write-Host "✅ Synchronisation:   " -NoNewline
    Write-Host "Auf dem neuesten Stand!" -ForegroundColor Green
} else {
    if ($ahead -gt 0) {
        Write-Host "⬆️  Lokale Änderungen: " -NoNewline
        Write-Host "$ahead Commit(s) nicht gepusht" -ForegroundColor Yellow
        Write-Host "   → Führe aus: .\Data-Sync-Push.ps1" -ForegroundColor Cyan
    }
    if ($behind -gt 0) {
        Write-Host "⬇️  Remote-Änderungen: " -NoNewline
        Write-Host "$behind Commit(s) nicht abgerufen" -ForegroundColor Yellow
        Write-Host "   → Führe aus: .\Data-Sync-Pull.ps1" -ForegroundColor Cyan
    }
}

# Letzter Sync-Zeitpunkt
Write-Host ""
Write-Host "─────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

$lastLocalSync = git log data-sync -1 --format="%ci|%s" 2>$null
if ($lastLocalSync) {
    $parts = $lastLocalSync -split '\|'
    $date = [DateTime]::Parse($parts[0])
    $message = $parts[1]

    Write-Host "🕐 Letzter Sync (Lokal):" -ForegroundColor Cyan
    Write-Host "   Datum:   $($date.ToString('dd.MM.yyyy HH:mm:ss'))" -ForegroundColor White
    Write-Host "   Message: $message" -ForegroundColor White
}

$lastRemoteSync = git log origin/data-sync -1 --format="%ci|%s" 2>$null
if ($lastRemoteSync) {
    $parts = $lastRemoteSync -split '\|'
    $date = [DateTime]::Parse($parts[0])
    $message = $parts[1]

    Write-Host ""
    Write-Host "🕐 Letzter Sync (GitHub):" -ForegroundColor Cyan
    Write-Host "   Datum:   $($date.ToString('dd.MM.yyyy HH:mm:ss'))" -ForegroundColor White
    Write-Host "   Message: $message" -ForegroundColor White
}

# Lokale Änderungen in .auto-claude
Write-Host ""
Write-Host "─────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

if (Test-Path ".auto-claude") {
    $localChanges = git status --porcelain .auto-claude
    if ($localChanges) {
        Write-Host "⚠️  Lokale Änderungen:" -ForegroundColor Yellow
        Write-Host ""
        git status --short .auto-claude
        Write-Host ""
        Write-Host "   Diese werden beim nächsten Pull überschrieben!" -ForegroundColor Red
    } else {
        Write-Host "✅ Lokale Änderungen:  " -NoNewline
        Write-Host "Keine" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  .auto-claude Verzeichnis nicht gefunden!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "─────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# Hilfe-Kommandos
Write-Host "💡 Verfügbare Kommandos:" -ForegroundColor Cyan
Write-Host "   .\Data-Sync-Push.ps1   - Pushe Daten zu GitHub" -ForegroundColor White
Write-Host "   .\Data-Sync-Pull.ps1   - Hole Daten von GitHub" -ForegroundColor White
Write-Host "   .\Data-Sync-Status.ps1 - Zeige diesen Status" -ForegroundColor White

Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
