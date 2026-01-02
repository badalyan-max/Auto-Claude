#!/usr/bin/env pwsh
# ============================================================================
# Auto-Claude Data Sync - PULL from GitHub
# ============================================================================
# Synchronisiert .auto-claude Daten vom data-sync Branch
#
# Verwendung:
#   .\sync-from-cloud.ps1
#
# Autor: Auto-Claude Data Sync System
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host "🔄 Auto-Claude Data Sync - PULL from Cloud" -ForegroundColor Cyan
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

# Prüfen ob lokale Änderungen existieren, die nicht gepusht wurden
$localChanges = git status --porcelain .auto-claude
if ($localChanges) {
    Write-Host ""
    Write-Host "⚠️  Warning: You have local changes in .auto-claude:" -ForegroundColor Yellow
    Write-Host ""
    git status --short .auto-claude
    Write-Host ""
    Write-Host "These changes will be OVERWRITTEN by the cloud data!" -ForegroundColor Red
    $response = Read-Host "Continue? (y/n)"

    if ($response -ne "y") {
        Write-Host "❌ Aborting sync." -ForegroundColor Red
        git checkout $currentBranch
        exit 1
    }

    Write-Host ""
    Write-Host "💾 Creating backup of local changes..." -ForegroundColor Cyan
    $backupDir = ".auto-claude-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item -Path ".auto-claude" -Destination $backupDir -Recurse
    Write-Host "✅ Backup created: $backupDir" -ForegroundColor Green
}

# Neueste Daten vom Remote holen
Write-Host ""
Write-Host "📥 Fetching latest data from remote..." -ForegroundColor Cyan
git fetch origin data-sync

# Prüfen wie viele Commits wir behind sind
$behind = git rev-list --count HEAD..origin/data-sync 2>$null
if ($behind -eq 0) {
    Write-Host "✅ Already up to date! No new data to sync." -ForegroundColor Green
    Write-Host ""
    Write-Host "🔀 Switching back to $currentBranch..." -ForegroundColor Yellow
    git checkout $currentBranch
    exit 0
}

Write-Host "📊 Remote has $behind new commit(s)" -ForegroundColor Yellow

# Pull mit Overwrite
Write-Host ""
Write-Host "🔄 Pulling data from cloud..." -ForegroundColor Cyan
git reset --hard origin/data-sync

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to pull data" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ SUCCESS! Data synced from cloud!" -ForegroundColor Green
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
Write-Host "🎉 Done! Your Kanban data is now up to date." -ForegroundColor Cyan
Write-Host "   Changes synced:" -ForegroundColor Gray
Write-Host "   - Kanban Board" -ForegroundColor Gray
Write-Host "   - Tasks & Specs" -ForegroundColor Gray
Write-Host "   - Insights & Sessions" -ForegroundColor Gray
Write-Host ""
