#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Erstellt Desktop-Verknüpfungen für Auto Git Sync

.DESCRIPTION
    Erstellt mehrere Verknüpfungen für verschiedene Git Sync Modi:
    - Auto Git Sync (Watch Mode ohne Push)
    - Auto Git Sync + Push (Watch Mode mit Auto-Push)
    - Auto Git Sync + Push + PR (Volle Automation)
    - Git Sync Check (Einmalige Prüfung)

.EXAMPLE
    .\Create-GitSync-Shortcut.ps1
#>

# Finde Desktop-Pfad (OneDrive oder lokal)
$desktopPath = if (Test-Path "$env:USERPROFILE\OneDrive\Desktop") {
    "$env:USERPROFILE\OneDrive\Desktop"
} else {
    [Environment]::GetFolderPath("Desktop")
}

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "Auto Git Sync - Desktop Verknüpfungen" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Projekt-Verzeichnis
$projectPath = $PSScriptRoot
Write-Host "[INFO] Projekt-Pfad: $projectPath" -ForegroundColor Gray

# Python-Pfad finden
$pythonExe = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonExe) {
    Write-Host "[FEHLER] Python nicht gefunden! Bitte installieren: https://www.python.org/" -ForegroundColor Red
    exit 1
}

$pythonPath = $pythonExe.Source
Write-Host "[INFO] Python gefunden: $pythonPath" -ForegroundColor Gray

# Script-Pfad
$syncScript = Join-Path $projectPath "apps\backend\auto_git_sync.py"

if (-not (Test-Path $syncScript)) {
    Write-Host "[FEHLER] auto_git_sync.py nicht gefunden: $syncScript" -ForegroundColor Red
    exit 1
}

# WScript.Shell für Verknüpfungs-Erstellung
$shell = New-Object -ComObject WScript.Shell

# ============================================
# 1. Auto Git Sync (Watch Mode)
# ============================================
Write-Host "`n[1/4] Erstelle 'Auto Git Sync.lnk'..." -ForegroundColor Cyan

$shortcut1 = $shell.CreateShortcut("$desktopPath\Auto Git Sync.lnk")
$shortcut1.TargetPath = $pythonPath
$shortcut1.Arguments = "`"$syncScript`" --watch"
$shortcut1.WorkingDirectory = $projectPath
$shortcut1.Description = "Auto Git Sync - Watch Mode (committet done Tasks)"
$shortcut1.IconLocation = "$env:SystemRoot\System32\imageres.dll,27"  # Git-Icon
$shortcut1.Save()

Write-Host "   [OK] Erstellt: Auto Git Sync.lnk" -ForegroundColor Green
Write-Host "   - Modus: Watch Mode" -ForegroundColor Gray
Write-Host "   - Committet automatisch done Tasks" -ForegroundColor Gray
Write-Host "   - KEIN automatisches Pushen" -ForegroundColor Gray

# ============================================
# 2. Auto Git Sync + Push
# ============================================
Write-Host "`n[2/4] Erstelle 'Auto Git Sync + Push.lnk'..." -ForegroundColor Cyan

$shortcut2 = $shell.CreateShortcut("$desktopPath\Auto Git Sync + Push.lnk")
$shortcut2.TargetPath = $pythonPath
$shortcut2.Arguments = "`"$syncScript`" --watch --auto-push"
$shortcut2.WorkingDirectory = $projectPath
$shortcut2.Description = "Auto Git Sync - Watch Mode + Auto-Push"
$shortcut2.IconLocation = "$env:SystemRoot\System32\imageres.dll,190"  # Upload-Icon
$shortcut2.Save()

Write-Host "   [OK] Erstellt: Auto Git Sync + Push.lnk" -ForegroundColor Green
Write-Host "   - Modus: Watch Mode + Auto-Push" -ForegroundColor Gray
Write-Host "   - Committet UND pusht automatisch" -ForegroundColor Gray
Write-Host "   - KEIN PR-Erstellung" -ForegroundColor Gray

# ============================================
# 3. Auto Git Sync + Push + PR
# ============================================
Write-Host "`n[3/4] Erstelle 'Auto Git Sync + PR.lnk'..." -ForegroundColor Cyan

$shortcut3 = $shell.CreateShortcut("$desktopPath\Auto Git Sync + PR.lnk")
$shortcut3.TargetPath = $pythonPath
$shortcut3.Arguments = "`"$syncScript`" --watch --auto-push --create-pr"
$shortcut3.WorkingDirectory = $projectPath
$shortcut3.Description = "Auto Git Sync - Volle Automation (Commit + Push + PR)"
$shortcut3.IconLocation = "$env:SystemRoot\System32\imageres.dll,299"  # Cloud-Icon
$shortcut3.Save()

Write-Host "   [OK] Erstellt: Auto Git Sync + PR.lnk" -ForegroundColor Green
Write-Host "   - Modus: Volle Automation" -ForegroundColor Gray
Write-Host "   - Committet + Pusht + Erstellt PR" -ForegroundColor Gray
Write-Host "   - Benötigt GitHub CLI (gh)" -ForegroundColor Gray

# ============================================
# 4. Git Sync Check (Einmalig)
# ============================================
Write-Host "`n[4/4] Erstelle 'Git Sync Check.lnk'..." -ForegroundColor Cyan

$shortcut4 = $shell.CreateShortcut("$desktopPath\Git Sync Check.lnk")
$shortcut4.TargetPath = $pythonPath
$shortcut4.Arguments = "`"$syncScript`" --check-done --auto-push"
$shortcut4.WorkingDirectory = $projectPath
$shortcut4.Description = "Git Sync Check - Einmalige Prüfung + Commit + Push"
$shortcut4.IconLocation = "$env:SystemRoot\System32\imageres.dll,109"  # Check-Icon
$shortcut4.Save()

Write-Host "   [OK] Erstellt: Git Sync Check.lnk" -ForegroundColor Green
Write-Host "   - Modus: Einmalige Prüfung" -ForegroundColor Gray
Write-Host "   - Prüft einmal, committet + pusht" -ForegroundColor Gray
Write-Host "   - Beendet sich danach" -ForegroundColor Gray

# ============================================
# Zusammenfassung
# ============================================
Write-Host "`n============================================" -ForegroundColor Green
Write-Host "ERFOLGREICH! 4 Verknüpfungen erstellt" -ForegroundColor Green
Write-Host "============================================`n" -ForegroundColor Green

Write-Host "Desktop-Verknüpfungen:" -ForegroundColor Cyan
Write-Host "  1. Auto Git Sync.lnk" -ForegroundColor White
Write-Host "     -> Watch Mode (nur committen)" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Auto Git Sync + Push.lnk" -ForegroundColor White
Write-Host "     -> Watch Mode + Auto-Push" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Auto Git Sync + PR.lnk" -ForegroundColor White
Write-Host "     -> Volle Automation (benötigt gh CLI)" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Git Sync Check.lnk" -ForegroundColor White
Write-Host "     -> Einmalige Prüfung + Push" -ForegroundColor Gray
Write-Host ""

Write-Host "Empfohlene Verwendung:" -ForegroundColor Yellow
Write-Host "  - Entwicklung: 'Auto Git Sync.lnk' (nur committen)" -ForegroundColor Gray
Write-Host "  - Production:  'Auto Git Sync + Push.lnk' (committen + pushen)" -ForegroundColor Gray
Write-Host "  - Vollautomatisch: 'Auto Git Sync + PR.lnk' (alles)" -ForegroundColor Gray
Write-Host ""

Write-Host "Hinweis für PR-Erstellung:" -ForegroundColor Yellow
Write-Host "  GitHub CLI installieren: winget install GitHub.cli" -ForegroundColor Gray
Write-Host "  Dann authentifizieren: gh auth login" -ForegroundColor Gray
Write-Host ""

Write-Host "Drücken Sie eine Taste zum Beenden..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

