<#
.SYNOPSIS
    Startet Auto-Sync im Hintergrund (unsichtbar)

.DESCRIPTION
    Startet die automatische Synchronisation im Hintergrund.
    Läuft unsichtbar und pushed alle 60 Sekunden Änderungen zu deinem Fork.
    
    Um zu stoppen: Task-Manager → "python.exe" (app_auto_sync.py) beenden
    
.EXAMPLE
    .\Start-Auto-Sync-Hintergrund.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  AUTO-SYNC IM HINTERGRUND STARTEN" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Prüfe ob bereits läuft
$existing = Get-Process python* -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*app_auto_sync.py*"
}

if ($existing) {
    Write-Host "⚠️  Auto-Sync läuft bereits!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "PID: $($existing.Id)" -ForegroundColor Cyan
    Write-Host ""
    
    $response = Read-Host "Neustart? (j/n)"
    if ($response -eq "j" -or $response -eq "J") {
        Write-Host "Stoppe alten Prozess..." -ForegroundColor Yellow
        Stop-Process -Id $existing.Id -Force
        Start-Sleep -Seconds 2
    } else {
        Write-Host "Abgebrochen." -ForegroundColor Yellow
        exit 0
    }
}

# Finde Python
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
    pause
    exit 1
}

# Starte im Hintergrund
$scriptPath = Join-Path $PSScriptRoot "apps\backend\app_auto_sync.py"
$logPath = Join-Path $PSScriptRoot ".auto-sync.log"

Write-Host "🚀 Starte Auto-Sync im Hintergrund..." -ForegroundColor Cyan
Write-Host ""

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $pythonCmd
$psi.Arguments = "`"$scriptPath`" --watch --interval 60"
$psi.WorkingDirectory = $PSScriptRoot
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.WindowStyle = "Hidden"

$process = [System.Diagnostics.Process]::Start($psi)

Write-Host "✅ Auto-Sync gestartet!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Details:" -ForegroundColor Cyan
Write-Host "   PID: $($process.Id)" -ForegroundColor White
Write-Host "   Log: .auto-sync.log" -ForegroundColor White
Write-Host "   Fork: https://github.com/badalyan-max/Auto-Claude" -ForegroundColor White
Write-Host ""
Write-Host "💡 Zum Stoppen:" -ForegroundColor Yellow
Write-Host "   Task-Manager → Python-Prozess (PID $($process.Id)) beenden" -ForegroundColor White
Write-Host "   Oder: Stop-Process -Id $($process.Id)" -ForegroundColor White
Write-Host ""
Write-Host "📝 Log ansehen:" -ForegroundColor Yellow
Write-Host "   Get-Content .auto-sync.log -Wait -Tail 20" -ForegroundColor White
Write-Host ""

# Speichere PID für späteres Stoppen
$pidFile = Join-Path $PSScriptRoot ".auto-sync.pid"
$process.Id | Out-File $pidFile

Write-Host "✅ Fertig! Auto-Sync läuft im Hintergrund." -ForegroundColor Green
Write-Host ""
