# ================================================================
# Auto-Claude Kanban Data Synchronization Script
# ================================================================
# This script manages Kanban board data synchronization via Git
# using a separate 'data-sync' branch.
#
# Usage:
#   .\sync-kanban-data.ps1 push    # Push local Kanban data to GitHub
#   .\sync-kanban-data.ps1 pull    # Pull Kanban data from GitHub
#   .\sync-kanban-data.ps1 status  # Check sync status
# ================================================================

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('push', 'pull', 'status')]
    [string]$Action
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

# ================================================================
# Configuration
# ================================================================
$DATA_DIR = ".auto-claude"
$DATA_BRANCH = "data-sync"
$MAIN_BRANCH = "develop"
$STASH_NAME = "auto-claude-data-sync-stash"

# ================================================================
# Helper Functions
# ================================================================

function Get-CurrentBranch {
    return git rev-parse --abbrev-ref HEAD
}

function Test-DataDirectory {
    if (-not (Test-Path $DATA_DIR)) {
        Write-Error "❌ Data directory '$DATA_DIR' not found!"
        exit 1
    }
}

function Backup-GitIgnore {
    Write-Info "📋 Creating backup of .gitignore..."
    Copy-Item .gitignore .gitignore.backup -Force
}

function Restore-GitIgnore {
    if (Test-Path .gitignore.backup) {
        Write-Info "📋 Restoring .gitignore..."
        Move-Item .gitignore.backup .gitignore -Force
    }
}

function Remove-DataFromGitIgnore {
    Write-Info "🔧 Temporarily removing .auto-claude/ from .gitignore..."
    $content = Get-Content .gitignore
    $filtered = $content | Where-Object { $_ -notmatch '^\s*\.auto-claude/' }
    $filtered | Set-Content .gitignore
}

function Add-DataToGitIgnore {
    Write-Info "🔧 Re-adding .auto-claude/ to .gitignore..."
    if (-not (Select-String -Path .gitignore -Pattern '^\s*\.auto-claude/' -Quiet)) {
        Add-Content .gitignore "`n.auto-claude/"
    }
}

# ================================================================
# Main Actions
# ================================================================

function Push-KanbanData {
    Write-Info "🚀 Starting Kanban data push to GitHub..."

    Test-DataDirectory

    $originalBranch = Get-CurrentBranch
    Write-Info "📍 Current branch: $originalBranch"

    # Backup .gitignore
    Backup-GitIgnore

    try {
        # Switch to data-sync branch (or create it)
        Write-Info "🔀 Switching to '$DATA_BRANCH' branch..."
        git checkout $DATA_BRANCH 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "⚠️  Branch '$DATA_BRANCH' doesn't exist. Creating it..."
            git checkout -b $DATA_BRANCH
        }

        # Remove .auto-claude from .gitignore temporarily
        Remove-DataFromGitIgnore

        # Add and commit data
        Write-Info "📦 Adding Kanban data..."
        git add $DATA_DIR

        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        git commit -m "sync: Kanban data update [$timestamp]" 2>$null

        if ($LASTEXITCODE -eq 0) {
            Write-Success "✅ Data committed successfully!"

            # Push to GitHub
            Write-Info "⬆️  Pushing to GitHub..."
            git push -u origin $DATA_BRANCH

            if ($LASTEXITCODE -eq 0) {
                Write-Success "✅ Kanban data successfully pushed to GitHub!"
            } else {
                Write-Error "❌ Failed to push to GitHub!"
            }
        } else {
            Write-Warning "⚠️  No changes to commit."
        }

    } finally {
        # Restore .gitignore
        Restore-GitIgnore

        # Switch back to original branch
        Write-Info "🔙 Switching back to '$originalBranch' branch..."
        git checkout $originalBranch
    }

    Write-Success "`n✨ Push completed!"
}

function Pull-KanbanData {
    Write-Info "📥 Starting Kanban data pull from GitHub..."

    $originalBranch = Get-CurrentBranch
    Write-Info "📍 Current branch: $originalBranch"

    # Backup .gitignore
    Backup-GitIgnore

    try {
        # Fetch latest data
        Write-Info "🔄 Fetching latest data from GitHub..."
        git fetch origin $DATA_BRANCH

        # Switch to data-sync branch
        Write-Info "🔀 Switching to '$DATA_BRANCH' branch..."
        git checkout $DATA_BRANCH 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "⚠️  Branch '$DATA_BRANCH' doesn't exist locally. Creating it..."
            git checkout -b $DATA_BRANCH origin/$DATA_BRANCH
        } else {
            # Pull latest changes
            Write-Info "⬇️  Pulling latest changes..."
            git pull origin $DATA_BRANCH
        }

        if ($LASTEXITCODE -eq 0) {
            Write-Success "✅ Kanban data successfully pulled from GitHub!"

            # Copy data to working directory
            if (Test-Path $DATA_DIR) {
                Write-Info "📂 Kanban data is now available in $DATA_DIR"
            }
        } else {
            Write-Error "❌ Failed to pull data from GitHub!"
        }

    } finally {
        # Restore .gitignore
        Restore-GitIgnore

        # Switch back to original branch
        Write-Info "🔙 Switching back to '$originalBranch' branch..."
        git checkout $originalBranch
    }

    Write-Success "`n✨ Pull completed!"
}

function Show-SyncStatus {
    Write-Info "📊 Kanban Data Sync Status"
    Write-Info "========================================`n"

    # Check if data directory exists
    if (Test-Path $DATA_DIR) {
        $dataSize = (Get-ChildItem $DATA_DIR -Recurse | Measure-Object -Property Length -Sum).Sum
        $dataSizeMB = [math]::Round($dataSize / 1MB, 2)
        Write-Success "✅ Local data directory: EXISTS ($dataSizeMB MB)"

        # Count tasks
        $tasksFile = Join-Path $DATA_DIR "tasks.json"
        if (Test-Path $tasksFile) {
            $tasks = Get-Content $tasksFile | ConvertFrom-Json
            Write-Info "   📋 Tasks: $($tasks.Count)"
        }
    } else {
        Write-Warning "⚠️  Local data directory: NOT FOUND"
    }

    # Check remote branch
    Write-Info "`n🌐 Checking remote '$DATA_BRANCH' branch..."
    git fetch origin $DATA_BRANCH 2>$null

    if ($LASTEXITCODE -eq 0) {
        Write-Success "✅ Remote branch '$DATA_BRANCH': EXISTS"

        # Get last sync time
        $lastCommit = git log origin/$DATA_BRANCH -1 --format="%ci" 2>$null
        if ($lastCommit) {
            Write-Info "   🕒 Last sync: $lastCommit"
        }
    } else {
        Write-Warning "⚠️  Remote branch '$DATA_BRANCH': NOT FOUND"
        Write-Info "   💡 Run '.\sync-kanban-data.ps1 push' to create it"
    }

    # Current branch
    $currentBranch = Get-CurrentBranch
    Write-Info "`n📍 Current branch: $currentBranch"

    Write-Info "`n========================================`n"
}

# ================================================================
# Execute Action
# ================================================================

switch ($Action) {
    'push' { Push-KanbanData }
    'pull' { Pull-KanbanData }
    'status' { Show-SyncStatus }
}
