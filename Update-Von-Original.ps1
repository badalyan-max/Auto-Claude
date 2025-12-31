<#
.SYNOPSIS
    Holt automatisch Updates vom Original-Entwickler und kombiniert sie mit deinen Änderungen

.DESCRIPTION
    Dieses Skript:
    1. Holt neue Features vom Original-Entwickler (AndyMik90)
    2. Kombiniert sie automatisch mit deinen eigenen Änderungen
    3. Löst Konflikte intelligent oder zeigt sie dir an
    4. Pushed alles zu deinem Fork

.EXAMPLE
    .\Update-Von-Original.ps1
#>

$ErrorActionPreference = "Stop"

# Farben für bessere Lesbarkeit
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  AUTO CLAUDE - UPDATE VOM ORIGINAL-ENTWICKLER" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Prüfe ob wir im richtigen Verzeichnis sind
if (-not (Test-Path ".git")) {
    Write-Error "Fehler: Muss im auto-claude Verzeichnis ausgeführt werden!"
    Write-Host ""
    Write-Host "Führe aus: cd c:\Projekte\auto-claude" -ForegroundColor Yellow
    exit 1
}

# 1. Aktuellen Branch prüfen
Write-Info "Prüfe aktuellen Branch..."
$currentBranch = git branch --show-current
Write-Host "   Branch: $currentBranch" -ForegroundColor White

if ($currentBranch -ne "develop") {
    Write-Warning "Du bist nicht auf 'develop' Branch!"
    Write-Host "   Wechsle zu develop..." -ForegroundColor Yellow
    git checkout develop
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Fehler beim Wechseln zum develop Branch"
        exit 1
    }
}

# 2. Lokale Änderungen prüfen
Write-Info "Prüfe lokale Änderungen..."
$status = git status --short
if ($status) {
    Write-Warning "Du hast ungespeicherte Änderungen!"
    Write-Host ""
    Write-Host "Änderungen:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    
    $response = Read-Host "Möchtest du sie jetzt committen? (j/n)"
    if ($response -eq "j" -or $response -eq "J") {
        git add -A
        $commitMsg = Read-Host "Commit-Nachricht (Enter für Standard)"
        if ([string]::IsNullOrWhiteSpace($commitMsg)) {
            $commitMsg = "feat: Meine Änderungen vor Update vom Original"
        }
        git commit -m $commitMsg
        Write-Success "Änderungen gespeichert!"
    } else {
        Write-Warning "Bitte speichere deine Änderungen manuell mit:"
        Write-Host "   git add -A" -ForegroundColor Yellow
        Write-Host "   git commit -m 'Meine Änderungen'" -ForegroundColor Yellow
        exit 1
    }
}

# 3. Updates vom Original holen
Write-Info "Hole Updates vom Original-Entwickler (AndyMik90)..."
git fetch upstream
if ($LASTEXITCODE -ne 0) {
    Write-Error "Fehler beim Holen der Updates!"
    exit 1
}

# Prüfe ob es neue Commits gibt
$behindCount = git rev-list --count develop..upstream/develop 2>$null
if ($behindCount -eq 0) {
    Write-Success "Du bist bereits auf dem neuesten Stand!"
    Write-Host ""
    Write-Host "Keine neuen Updates vom Original-Entwickler verfügbar." -ForegroundColor Green
    exit 0
}

Write-Success "Neue Updates gefunden: $behindCount Commits"

# Zeige die neuen Commits
Write-Host ""
Write-Host "Neue Features vom Original-Entwickler:" -ForegroundColor Cyan
Write-Host "───────────────────────────────────────" -ForegroundColor Cyan
git log --oneline --graph develop..upstream/develop | ForEach-Object {
    Write-Host "  $_" -ForegroundColor White
}
Write-Host ""

# 4. Merge durchführen
Write-Info "Kombiniere Updates mit deinen Änderungen..."
git merge upstream/develop --no-edit

if ($LASTEXITCODE -ne 0) {
    # Merge-Konflikt aufgetreten
    Write-Warning "MERGE-KONFLIKT aufgetreten!"
    Write-Host ""
    Write-Host "Git konnte einige Änderungen nicht automatisch kombinieren." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Betroffene Dateien:" -ForegroundColor Yellow
    git diff --name-only --diff-filter=U | ForEach-Object {
        Write-Host "  - $_" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host "  SO LÖST DU DEN KONFLIKT:" -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Öffne die Dateien in VS Code/Cursor" -ForegroundColor Cyan
    Write-Host "2. Suche nach Zeilen mit: <<<<<<< HEAD" -ForegroundColor Cyan
    Write-Host "3. Entscheide welche Version du behalten willst:" -ForegroundColor Cyan
    Write-Host "   - Dein Code steht zwischen <<<<<<< und =======" -ForegroundColor White
    Write-Host "   - Original-Code steht zwischen ======= und >>>>>>>" -ForegroundColor White
    Write-Host "4. Lösche die Konflikt-Marker (<<<, ===, >>>)" -ForegroundColor Cyan
    Write-Host "5. Speichere die Dateien" -ForegroundColor Cyan
    Write-Host "6. Führe aus:" -ForegroundColor Cyan
    Write-Host "   git add ." -ForegroundColor Yellow
    Write-Host "   git commit -m 'Merge-Konflikt gelöst'" -ForegroundColor Yellow
    Write-Host "   git push origin develop" -ForegroundColor Yellow
    Write-Host ""
    
    # Öffne Cursor im Konflikt-Modus
    $response = Read-Host "Cursor jetzt öffnen zum Lösen? (j/n)"
    if ($response -eq "j" -or $response -eq "J") {
        Write-Info "Öffne Cursor..."
        cursor .
    }
    
    exit 1
}

Write-Success "Updates erfolgreich kombiniert!"

# 5. Zu deinem Fork pushen
Write-Info "Lade Updates zu deinem Fork hoch..."
git push origin develop

if ($LASTEXITCODE -ne 0) {
    Write-Error "Fehler beim Pushen zum Fork!"
    Write-Host ""
    Write-Host "Versuche manuell:" -ForegroundColor Yellow
    Write-Host "   git push origin develop --force-with-lease" -ForegroundColor Yellow
    exit 1
}

Write-Success "Updates erfolgreich hochgeladen!"

# Zusammenfassung
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ UPDATE ERFOLGREICH ABGESCHLOSSEN!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Was passiert ist:" -ForegroundColor Cyan
Write-Host "  ✅ $behindCount neue Commits vom Original geholt" -ForegroundColor White
Write-Host "  ✅ Mit deinen Änderungen kombiniert" -ForegroundColor White
Write-Host "  ✅ Zu deinem Fork hochgeladen" -ForegroundColor White
Write-Host ""
Write-Host "Dein Fork: https://github.com/badalyan-max/Auto-Claude" -ForegroundColor Cyan
Write-Host ""

# Zeige die letzten Commits
Write-Host "Letzte Commits:" -ForegroundColor Cyan
git log --oneline --graph -10 | ForEach-Object {
    Write-Host "  $_" -ForegroundColor White
}
Write-Host ""

Write-Host "Fertig! 🎉" -ForegroundColor Green
Write-Host ""
