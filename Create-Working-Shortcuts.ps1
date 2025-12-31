# Erstellt funktionierende Desktop-Verknuepfungen
# Diese Version verwendet Batch-Dateien als Target (100% zuverlaessig)

param(
    [switch]$AllUsers = $false
)

$ErrorActionPreference = "Stop"

# Desktop Path
if ($AllUsers) {
    $desktopPath = [Environment]::GetFolderPath("CommonDesktopDirectory")
} else {
    $oneDriveDesktop = Join-Path $env:USERPROFILE "OneDrive\Desktop"
    if (Test-Path $oneDriveDesktop) {
        $desktopPath = $oneDriveDesktop
    } else {
        $desktopPath = [Environment]::GetFolderPath("Desktop")
    }
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  Desktop-Verknuepfungen erstellen (FUNKTIONIERENDE Version)" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = $PSScriptRoot

Write-Host "[INFO] Projekt: $projectRoot" -ForegroundColor Cyan
Write-Host "[INFO] Desktop: $desktopPath" -ForegroundColor Cyan
Write-Host ""

# Erstelle Verknuepfungen
$shortcuts = @(
    @{
        Name = "Auto Claude (Safe Sync)"
        Target = Join-Path $projectRoot "Start-Safe-Sync.bat"
        Description = "Auto Claude mit automatischem GitHub Pull"
        Icon = "powershell.exe"
    },
    @{
        Name = "Auto Claude (Safe Sync - NoPull)"
        Target = Join-Path $projectRoot "Start-Safe-Sync-NoPull.bat"
        Description = "Auto Claude ohne GitHub Pull (Offline-Modus)"
        Icon = "powershell.exe"
    }
)

foreach ($shortcut in $shortcuts) {
    Write-Host "Erstelle: $($shortcut.Name)" -ForegroundColor Yellow
    
    # Prueffe ob Target existiert
    if (-not (Test-Path $shortcut.Target)) {
        Write-Host "  [ERROR] Target nicht gefunden: $($shortcut.Target)" -ForegroundColor Red
        continue
    }
    
    $shortcutPath = Join-Path $desktopPath "$($shortcut.Name).lnk"
    
    try {
        # Loesche alte Verknuepfung falls vorhanden
        if (Test-Path $shortcutPath) {
            Remove-Item $shortcutPath -Force
            Write-Host "  [INFO] Alte Verknuepfung geloescht" -ForegroundColor Yellow
        }
        
        # Erstelle neue Verknuepfung
        $WScriptShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WScriptShell.CreateShortcut($shortcutPath)
        $Shortcut.TargetPath = $shortcut.Target
        $Shortcut.WorkingDirectory = $projectRoot
        $Shortcut.Description = $shortcut.Description
        $Shortcut.IconLocation = "$($shortcut.Icon),0"
        $Shortcut.Save()
        
        # Validiere
        Start-Sleep -Milliseconds 500
        if (Test-Path $shortcutPath) {
            # Lese zurueck zur Validierung
            $CreatedShortcut = $WScriptShell.CreateShortcut($shortcutPath)
            if ($CreatedShortcut.TargetPath -eq $shortcut.Target) {
                Write-Host "  [OK] Erfolgreich erstellt: $shortcutPath" -ForegroundColor Green
                Write-Host "      Target: $($CreatedShortcut.TargetPath)" -ForegroundColor Gray
            } else {
                Write-Host "  [WARN] Erstellt aber Target stimmt nicht" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  [ERROR] Datei wurde nicht erstellt" -ForegroundColor Red
        }
    } catch {
        Write-Host "  [ERROR] Fehler: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  FERTIG!" -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Gehe zu deinem Desktop und teste:" -ForegroundColor Cyan
Write-Host "  -> Doppelklick auf 'Auto Claude (Safe Sync)'" -ForegroundColor Yellow
Write-Host ""
Write-Host "Das sollte jetzt ein PowerShell-Fenster oeffnen und Auto Claude starten!" -ForegroundColor Green
Write-Host ""
