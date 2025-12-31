# PowerShell-Skript zum Konfigurieren von Windows-Sicherheit für Claude Code
# MUSS ALS ADMINISTRATOR AUSGEFÜHRT WERDEN!

# Farben für Output
$SuccessColor = 'Green'
$ErrorColor = 'Red'
$InfoColor = 'Cyan'

Write-Host "================================================" -ForegroundColor $InfoColor
Write-Host "Windows-Sicherheit für Claude Code konfigurieren" -ForegroundColor $InfoColor
Write-Host "================================================" -ForegroundColor $InfoColor
Write-Host ""

# Prüfen, ob als Administrator ausgeführt wird
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "FEHLER: Dieses Skript muss als Administrator ausgeführt werden!" -ForegroundColor $ErrorColor
    Write-Host "Rechtsklicken Sie auf PowerShell und wählen Sie 'Als Administrator ausführen'" -ForegroundColor $ErrorColor
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 1
}

Write-Host "✓ Als Administrator ausgeführt" -ForegroundColor $SuccessColor
Write-Host ""

# Projektordner
$projectPath = "C:\Projekte\auto-claude"

# Prüfen, ob der Ordner existiert
if (-not (Test-Path $projectPath)) {
    Write-Host "WARNUNG: Projektordner nicht gefunden: $projectPath" -ForegroundColor $ErrorColor
    $projectPath = Read-Host "Bitte geben Sie den korrekten Pfad ein"
    if (-not (Test-Path $projectPath)) {
        Write-Host "Ordner existiert nicht. Abbruch." -ForegroundColor $ErrorColor
        exit 1
    }
}

Write-Host "Projektordner gefunden: $projectPath" -ForegroundColor $SuccessColor
Write-Host ""

# Funktion zum Hinzufügen von Defender-Ausnahmen
function Add-DefenderExclusion {
    param (
        [string]$Path
    )
    
    try {
        Write-Host "Füge Ausnahme hinzu: $Path" -ForegroundColor $InfoColor
        Add-MpPreference -ExclusionPath $Path -ErrorAction Stop
        Write-Host "✓ Erfolgreich hinzugefügt" -ForegroundColor $SuccessColor
        return $true
    }
    catch {
        Write-Host "✗ Fehler beim Hinzufügen: $_" -ForegroundColor $ErrorColor
        return $false
    }
}

# Hauptprojektordner ausschließen
Write-Host "1. Füge Hauptprojektordner als Ausnahme hinzu..." -ForegroundColor $InfoColor
$success = Add-DefenderExclusion -Path $projectPath

# Backend ausschließen
$backendPath = Join-Path $projectPath "apps\backend"
if (Test-Path $backendPath) {
    Write-Host ""
    Write-Host "2. Füge Backend-Ordner als Ausnahme hinzu..." -ForegroundColor $InfoColor
    Add-DefenderExclusion -Path $backendPath
}

# Frontend ausschließen
$frontendPath = Join-Path $projectPath "apps\frontend"
if (Test-Path $frontendPath) {
    Write-Host ""
    Write-Host "3. Füge Frontend-Ordner als Ausnahme hinzu..." -ForegroundColor $InfoColor
    Add-DefenderExclusion -Path $frontendPath
}

# Python ausschließen (falls vorhanden)
$pythonPaths = @(
    (Join-Path $projectPath "apps\backend\venv"),
    (Join-Path $projectPath ".venv")
)

foreach ($pythonPath in $pythonPaths) {
    if (Test-Path $pythonPath) {
        Write-Host ""
        Write-Host "4. Füge Python-Umgebung als Ausnahme hinzu..." -ForegroundColor $InfoColor
        Add-DefenderExclusion -Path $pythonPath
    }
}

# Node modules ausschließen
$nodeModulesPath = Join-Path $projectPath "apps\frontend\node_modules"
if (Test-Path $nodeModulesPath) {
    Write-Host ""
    Write-Host "5. Füge Node-Modules als Ausnahme hinzu..." -ForegroundColor $InfoColor
    Add-DefenderExclusion -Path $nodeModulesPath
}

# Aktuelle Ausnahmen anzeigen
Write-Host ""
Write-Host "================================================" -ForegroundColor $InfoColor
Write-Host "Aktuelle Windows Defender Ausnahmen:" -ForegroundColor $InfoColor
Write-Host "================================================" -ForegroundColor $InfoColor
try {
    $exclusions = Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
    if ($exclusions) {
        foreach ($exclusion in $exclusions) {
            if ($exclusion -like "*auto-claude*") {
                Write-Host "✓ $exclusion" -ForegroundColor $SuccessColor
            }
        }
    } else {
        Write-Host "Keine Ausnahmen gefunden" -ForegroundColor $ErrorColor
    }
}
catch {
    Write-Host "Fehler beim Abrufen der Ausnahmen: $_" -ForegroundColor $ErrorColor
}

Write-Host ""
Write-Host "================================================" -ForegroundColor $InfoColor
Write-Host "Zusätzliche Empfehlungen:" -ForegroundColor $InfoColor
Write-Host "================================================" -ForegroundColor $InfoColor
Write-Host ""
Write-Host "Wenn Sie weiterhin Probleme haben:" -ForegroundColor $InfoColor
Write-Host "1. Öffnen Sie Windows-Sicherheit manuell" -ForegroundColor $InfoColor
Write-Host "2. Gehen Sie zu 'App- und Browsersteuerung'" -ForegroundColor $InfoColor
Write-Host "3. Passen Sie SmartScreen-Einstellungen an" -ForegroundColor $InfoColor
Write-Host "4. Überprüfen Sie 'Kontrollierter Ordnerzugriff'" -ForegroundColor $InfoColor
Write-Host ""
Write-Host "Für Details siehe: WINDOWS_SICHERHEIT_ANLEITUNG.md" -ForegroundColor $SuccessColor
Write-Host ""

# Optional: Frage ob SmartScreen-Warnung deaktiviert werden soll
Write-Host "Möchten Sie SmartScreen-Warnungen für Apps aus dem Internet deaktivieren?" -ForegroundColor $InfoColor
Write-Host "WARNUNG: Dies reduziert Ihre Sicherheit!" -ForegroundColor $ErrorColor
$response = Read-Host "Ja/Nein (j/n)"

if ($response -eq 'j' -or $response -eq 'J' -or $response -eq 'ja' -or $response -eq 'Ja') {
    Write-Host ""
    Write-Host "SmartScreen-Einstellungen können nur manuell über die GUI geändert werden." -ForegroundColor $InfoColor
    Write-Host "Öffne Windows-Sicherheit für Sie..." -ForegroundColor $InfoColor
    Start-Process "windowsdefender://threatsettings"
}

Write-Host ""
Write-Host "================================================" -ForegroundColor $SuccessColor
Write-Host "Konfiguration abgeschlossen!" -ForegroundColor $SuccessColor
Write-Host "================================================" -ForegroundColor $SuccessColor
Write-Host ""
Write-Host "Bitte starten Sie Ihre Claude Code Anwendung neu." -ForegroundColor $InfoColor
Write-Host ""

Read-Host "Drücken Sie Enter zum Beenden"

