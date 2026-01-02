#!/usr/bin/env pwsh
# ============================================================================
# Auto-Claude Data Sync - PUSH to GitHub
# ============================================================================
# Synchronisiert lokale .auto-claude Daten zum data-sync Branch
#
# Verwendung:
#   .\sync-to-cloud.ps1
#
# Autor: Auto-Claude Data Sync System
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host "🔄 Auto-Claude Data Sync - PUSH to Cloud" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Aktuellen Branch speichern
$currentBranch = git branch --show-current
Write-Host "📍 Current branch: $currentBranch" -ForegroundColor Yellow

# Prüfen ob wir auf data-sync Branch sind
if ($currentBranch -eq "data-sync") {
    Write-Host "✅ Already on data-sync branch" -ForegroundColor Green
} else {
    Write-Host "🔀 Switching to data-sync branch..." -ForegroundColor Yellow

    # Uncommitted changes prüfen
    $status = git status --porcelain
    if ($status) {
        Write-Host "⚠️  Warning: You have uncommitted changes on $currentBranch" -ForegroundColor Yellow
        Write-Host ""
        git status --short
        Write-Host ""
        $response = Read-Host "Do you want to stash these changes? (y/n)"

        if ($response -eq "y") {
            Write-Host "💾 Stashing changes..." -ForegroundColor Cyan
            git stash push -m "Auto-stash before data-sync on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        } else {
            Write-Host "❌ Aborting sync. Please commit or stash your changes first." -ForegroundColor Red
            exit 1
        }
    }

    # Zu data-sync wechseln
    git checkout data-sync
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to switch to data-sync branch" -ForegroundColor Red
        exit 1
    }
}

# Neueste Daten vom Remote holen
Write-Host ""
Write-Host "📥 Fetching latest data from remote..." -ForegroundColor Cyan
git fetch origin data-sync

# Prüfen ob Remote-Changes existieren
$behind = git rev-list --count HEAD..origin/data-sync 2>$null
if ($behind -gt 0) {
    Write-Host "⚠️  Remote has $behind new commit(s). Pulling first..." -ForegroundColor Yellow
    git pull origin data-sync --rebase

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Merge conflict detected! Please resolve manually." -ForegroundColor Red
        exit 1
    }
}

# .auto-claude Daten hinzufügen
Write-Host ""
Write-Host "📦 Adding .auto-claude data..." -ForegroundColor Cyan
git add .auto-claude

# Prüfen ob es Änderungen gibt
$changes = git diff --cached --name-only
if (-not $changes) {
    Write-Host "✅ No changes to sync. Everything is up to date!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔀 Switching back to $currentBranch..." -ForegroundColor Yellow
    git checkout $currentBranch
    exit 0
}

Write-Host ""
Write-Host "📝 Changed files:" -ForegroundColor Yellow
git diff --cached --name-status | ForEach-Object {
    Write-Host "   $_" -ForegroundColor Gray
}

# Commit erstellen
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host ""
Write-Host "💾 Creating commit..." -ForegroundColor Cyan
git commit -m "sync: Update .auto-claude data [$timestamp]

Synchronized Kanban board, tasks, specs, and insights from PC."

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create commit" -ForegroundColor Red
    exit 1
}

# Push zu GitHub
Write-Host ""
Write-Host "🚀 Pushing to GitHub..." -ForegroundColor Cyan
git push origin data-sync

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to push to GitHub" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ SUCCESS! Data synced to cloud!" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green

# Zurück zum ursprünglichen Branch
if ($currentBranch -ne "data-sync") {
    Write-Host ""
    Write-Host "🔀 Switching back to $currentBranch..." -ForegroundColor Yellow
    git checkout $currentBranch

    # Stashed changes zurückholen
    $stashList = git stash list | Select-String "Auto-stash before data-sync"
    if ($stashList) {
        Write-Host "📤 Restoring stashed changes..." -ForegroundColor Cyan
        git stash pop
    }
}

Write-Host ""
Write-Host "🎉 Done! Your Kanban data is now on GitHub." -ForegroundColor Cyan
Write-Host "   On your laptop, run: .\sync-from-cloud.ps1" -ForegroundColor Gray
Write-Host ""
