<#
.SYNOPSIS
    Stoppt Auto-Sync Hintergrund-Prozess

.EXAMPLE
    .\Stop-Auto-Sync.ps1
#>

Write-Host ""
Write-Host "🛑 Stoppe Auto-Sync..." -ForegroundColor Cyan
Write-Host ""

# Finde laufende Prozesse
$processes = Get-Process python* -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*app_auto_sync.py*"
}

if (-not $processes) {
    Write-Host "ℹ️  Kein Auto-Sync Prozess gefunden" -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

foreach ($proc in $processes) {
    Write-Host "   Stoppe PID $($proc.Id)..." -ForegroundColor Yellow
    Stop-Process -Id $proc.Id -Force
}

Write-Host ""
Write-Host "✅ Auto-Sync gestoppt!" -ForegroundColor Green
Write-Host ""

# Lösche PID-Datei
$pidFile = Join-Path $PSScriptRoot ".auto-sync.pid"
if (Test-Path $pidFile) {
    Remove-Item $pidFile
}
