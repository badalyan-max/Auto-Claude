<#
.SYNOPSIS
    Zeigt Status des Auto-Sync Systems

.EXAMPLE
    .\Auto-Sync-Status.ps1
#>

$ErrorActionPreference = "Stop"

# Finde Python
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "❌ Python nicht gefunden!" -ForegroundColor Red
    exit 1
}

# Zeige Status
& $pythonCmd apps\backend\app_auto_sync.py --status

# Prüfe ob läuft
Write-Host ""
$running = Get-Process python* -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*app_auto_sync.py*"
}

if ($running) {
    Write-Host "🟢 Auto-Sync läuft (PID: $($running.Id))" -ForegroundColor Green
} else {
    Write-Host "🔴 Auto-Sync läuft NICHT" -ForegroundColor Red
    Write-Host ""
    Write-Host "Zum Starten:" -ForegroundColor Yellow
    Write-Host "   .\Start-Auto-Sync.bat" -ForegroundColor Cyan
}

Write-Host ""
