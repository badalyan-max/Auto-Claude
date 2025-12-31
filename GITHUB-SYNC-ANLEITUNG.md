# 🔒 Auto Claude - Bombensicherer GitHub Sync

**Automatischer GitHub-Pull vor jedem Auto Claude Start**

---

## 📋 Überblick

Diese Lösung stellt sicher, dass Auto Claude **IMMER** die neuesten Änderungen von GitHub sieht, bevor er startet.

### Was macht das Script?

1. ✅ **Git Repository Check** - Prüft ob gültiges Git Repo
2. ✅ **Uncommitted Changes** - Warnt vor lokalen Änderungen
3. ✅ **GitHub Pull** - Holt neueste Änderungen von GitHub
4. ✅ **Merge-Konflikt Detection** - Erkennt Merge-Probleme sofort
5. ✅ **Python Environment Check** - Validiert Python & venv
6. ✅ **Auto Claude Start** - Startet erst wenn alles OK ist

---

## 🚀 Schnellstart

### Option 1: Desktop-Verknüpfungen (EMPFOHLEN)

```powershell
# Erstelle Desktop-Icons
.\Create-Safe-Sync-Shortcut.ps1
```

**Dann:**
- Doppelklick auf **"Auto Claude (Safe Sync)"** auf dem Desktop

### Option 2: Batch-Datei

```batch
Start-Auto-Claude-Safe.bat
```

### Option 3: PowerShell direkt

```powershell
.\Start-Auto-Claude-With-Sync-v2.ps1
```

---

## 📝 Verwendung

### Interaktiver Modus (Standard)

```powershell
# Startet Spec Creator interaktiv
.\Start-Auto-Claude-With-Sync-v2.ps1
```

### Mit Task-Beschreibung

```powershell
# Erstellt Spec automatisch aus Task
.\Start-Auto-Claude-With-Sync-v2.ps1 -Task "Add user authentication"
```

### Bestehende Spec ausführen

```powershell
# Führt Spec 001 aus
.\Start-Auto-Claude-With-Sync-v2.ps1 -Mode run -Spec 001
```

### Live Monitor

```powershell
# Startet Monitor
.\Start-Auto-Claude-With-Sync-v2.ps1 -Mode monitor
```

### Ohne GitHub Pull (für Tests)

```powershell
# Überspringt den Pull
.\Start-Auto-Claude-With-Sync-v2.ps1 -NoPull
```

---

## 🔍 Was passiert im Detail?

### 1. Git Repository Check

```
[1] Git Repository pruefen...
  [OK] Git Repository erkannt
```

**Prüft:**
- Ist aktuelles Verzeichnis ein Git Repo?
- Ist Git installiert?

**Bei Fehler:**
- Script bricht ab

---

### 2. Uncommitted Changes Check

```
[2] Lokale Aenderungen pruefen...
  [WARN] Uncommitted changes vorhanden:
       M apps/backend/core/client.py
       M apps/frontend/src/App.tsx

  [WARN] Diese Changes koennten zu Konflikten fuehren.
  [J] Ja, fortfahren  [N] Nein  [S] Stash changes
```

**Optionen:**
- **J** = Fortfahren (mit Risiko von Merge-Konflikten)
- **N** = Abbrechen (sicher)
- **S** = Stash Changes (Änderungen temporär speichern)

**Empfehlung:**
- Bei wichtigen Changes: `S` (Stash)
- Bei Test-Changes: `J` (Fortfahren)
- Bei Unsicherheit: `N` (Abbrechen)

---

### 3. GitHub Sync

```
[3] GitHub Sync starten...
  [INFO] Branch: develop
  [OK] Remote gefunden: origin
  [INFO] Fetching...
  [OK] Fetch OK
  [INFO] Pulling changes from origin/develop...
  [OK] Pull erfolgreich!
  [INFO] Geaenderte Dateien:
      - apps/backend/agents/coder.py
      - apps/frontend/src/components/Button.tsx
```

**Was passiert:**
1. Ermittelt aktuellen Branch (z.B. `develop`)
2. Prüft ob Remote (GitHub) erreichbar ist
3. `git fetch` - Prüft auf neue Commits
4. Vergleicht lokal vs. remote
5. `git pull` - Holt Änderungen wenn nötig
6. Zeigt geänderte Dateien an

**Offline-Modus:**
- Wenn kein Internet: Script fragt ob fortfahren ohne Pull

**Merge-Konflikte:**
- Bei Konflikt: Script zeigt Anleitung zur manuellen Lösung
- Script bricht ab (sicher!)

---

### 4. Python Environment Check

```
[4] Python Environment pruefen...
  [OK] Python: Python 3.14.0
  [OK] Virtual Environment gefunden
```

**Prüft:**
- Python installiert?
- Python Version >= 3.12?
- Virtual Environment existiert?

**Auto-Fix:**
- Erstellt venv automatisch wenn fehlend
- Installiert Dependencies automatisch

---

### 5. Auto Claude Start

```
[5] Auto Claude starten...
  [INFO] Starte interaktiv

====================================================================
  ALLE CHECKS BESTANDEN - STARTE AUTO CLAUDE
====================================================================

[Auto Claude läuft...]
```

**Startet:**
- `spec_runner.py --interactive` (Standard)
- `spec_runner.py --task "..."` (mit Task)
- `run.py --spec 001` (Run Mode)
- `live_monitor.py --follow-all` (Monitor Mode)

---

## 📊 Szenarien & Workflows

### Szenario 1: Lovable macht Änderungen

**Workflow:**

```mermaid
Lovable (Online)
    ↓ commit + push
GitHub (Remote)
    ↓ (automatisch beim nächsten Start)
Start-Auto-Claude-With-Sync-v2.ps1
    ↓ git pull
Lokales Projekt (aktualisiert)
    ↓
Auto Claude (sieht neue Änderungen)
```

**Ablauf:**
1. Du arbeitest in Lovable, machst Änderungen
2. Lovable pusht zu GitHub
3. Du startest Auto Claude mit Safe Sync Script
4. Script pullt automatisch von GitHub
5. Auto Claude sieht die Lovable-Änderungen sofort!

**Wichtig:**
- Du musst **NICHTS** manuell machen
- Kein `git pull` nötig
- Alles automatisch!

---

### Szenario 2: Auto Claude & Lovable parallel

**Problem:**
- Auto Claude arbeitet lokal
- Lovable arbeitet online
- Beide pushen zu GitHub

**Lösung:**

1. **Auto Claude Session beenden**
   ```powershell
   # Warte bis Auto Claude fertig ist
   # Oder CTRL+C zum Abbrechen
   ```

2. **Pull vor neuem Start**
   ```powershell
   # Script pullt automatisch!
   .\Start-Auto-Claude-With-Sync-v2.ps1
   ```

3. **Merge-Konflikte behandeln**
   ```bash
   # Falls Konflikt:
   git status
   # Löse Konflikte in Dateien
   git add .
   git commit -m "Merged conflicts"
   ```

4. **Auto Claude neu starten**
   ```powershell
   .\Start-Auto-Claude-With-Sync-v2.ps1
   ```

---

### Szenario 3: Offline arbeiten

**Problem:**
- Kein Internet
- Script kann nicht pullen

**Lösung:**

```powershell
# Starte ohne Pull
.\Start-Auto-Claude-With-Sync-v2.ps1 -NoPull
```

**Oder:**
- Script fragt automatisch: "Fortfahren ohne Remote-Sync?"
- Drücke `J` für Ja

**Hinweis:**
- Auto Claude sieht nur lokale Änderungen
- Beim nächsten Online-Start: Automatischer Sync

---

### Szenario 4: Uncommitted Changes

**Problem:**
- Du hast lokale Änderungen
- Script will pullen
- Möglicher Konflikt

**Optionen:**

**A) Stash Changes (EMPFOHLEN)**
```powershell
# Script fragt:
[J] Ja, fortfahren  [N] Nein  [S] Stash changes

# Drücke: S
# → Changes werden gestashed
# → Pull erfolgt
# → Auto Claude startet

# Später wiederherstellen:
git stash pop
```

**B) Commit Changes**
```bash
# Vor Script-Start:
git add .
git commit -m "My changes"

# Dann Script starten:
.\Start-Auto-Claude-With-Sync-v2.ps1
```

**C) Fortfahren mit Risiko**
```powershell
# Script fragt:
[J] Ja, fortfahren  [N] Nein  [S] Stash changes

# Drücke: J
# → Pull erfolgt (kann Konflikte geben)
```

---

## 🔧 Konfiguration

### Automatisches Stashing

Wenn du **IMMER** uncommitted changes stashen willst:

**Bearbeite:** `Start-Auto-Claude-With-Sync-v2.ps1`

```powershell
# Suche diese Zeile (ca. Zeile 120):
Write-Host "  [J] Ja, fortfahren  [N] Nein  [S] Stash changes" -ForegroundColor Cyan
$choice = Read-Host "  Ihre Wahl"

# Ersetze mit:
WriteInfo "Uncommitted changes werden automatisch gestashed..."
$choice = "S"  # Automatisch stashen
```

### Kein Pull bei bestimmten Branches

**Bearbeite:** `Start-Auto-Claude-With-Sync-v2.ps1`

```powershell
# Nach Zeile "WriteStep '3' 'GitHub Sync starten...'" einfügen:

$branch = git branch --show-current

# Skip Pull für bestimmte Branches
$skipBranches = @("feature-123", "experimental")
if ($skipBranches -contains $branch) {
    WriteWarn "Branch $branch: Pull uebersprungen"
    WriteLog "Skip pull for branch: $branch"
    return $true
}
```

---

## 📜 Log-Dateien

### Wo sind die Logs?

```
.auto-claude\sync-log.txt
```

### Log-Format

```
[2025-12-31 14:23:45] NEUER START
[2025-12-31 14:23:45] Mode: interactive, Spec: , Task: , NoPull: False
[2025-12-31 14:23:45] Pruefe Git Repository
[2025-12-31 14:23:45] Git Repository OK
[2025-12-31 14:23:46] Pruefe uncommitted changes
[2025-12-31 14:23:46] WARN: Uncommitted changes gefunden
[2025-12-31 14:23:52] User: Stash
[2025-12-31 14:23:53] Stash OK
[2025-12-31 14:23:53] Starte GitHub Sync
[2025-12-31 14:23:53] Branch: develop
[2025-12-31 14:23:54] Remote OK
[2025-12-31 14:23:55] Fetching...
[2025-12-31 14:23:56] Fetch OK
[2025-12-31 14:23:57] Pulling...
[2025-12-31 14:23:59] Pull OK
[2025-12-31 14:24:00] Pruefe Python Environment
[2025-12-31 14:24:00] Python OK: Python 3.14.0
[2025-12-31 14:24:00] venv OK
[2025-12-31 14:24:01] Starte Auto Claude - Mode: interactive
[2025-12-31 14:24:01] spec_runner.py --interactive
[2025-12-31 14:30:15] Auto Claude beendet - Exit: 0
[2025-12-31 14:30:15] Erfolgreich beendet
```

### Logs lesen

```powershell
# Letzte 20 Zeilen
Get-Content .auto-claude\sync-log.txt -Tail 20

# Fehler suchen
Select-String -Path .auto-claude\sync-log.txt -Pattern "ERROR"

# Heute
Get-Content .auto-claude\sync-log.txt | Where-Object { $_ -match "2025-12-31" }
```

---

## ❌ Fehlerbehebung

### Fehler: "Kein Git Repository"

**Ursache:**
- Du bist nicht im Projekt-Verzeichnis
- Kein Git initialisiert

**Lösung:**
```powershell
cd C:\Projekte\auto-claude
.\Start-Auto-Claude-With-Sync-v2.ps1
```

---

### Fehler: "Pull fehlgeschlagen"

**Ursache:**
- Merge-Konflikt
- Keine Berechtigung
- Remote nicht erreichbar

**Lösung 1: Merge-Konflikt**
```bash
git status
# Zeigt Konflikt-Dateien

# Öffne Datei, löse Konflikte
# Suche nach:
<<<<<<< HEAD
deine lokale Version
=======
GitHub Version
>>>>>>> origin/develop

# Löse Konflikt, dann:
git add .
git commit -m "Resolved conflicts"
```

**Lösung 2: Starte ohne Pull**
```powershell
.\Start-Auto-Claude-With-Sync-v2.ps1 -NoPull
```

---

### Fehler: "Python nicht gefunden"

**Ursache:**
- Python nicht installiert
- Nicht im PATH

**Lösung:**
```powershell
# Prüfe Python
python --version

# Falls nicht gefunden:
# 1. Python 3.12+ installieren von python.org
# 2. "Add to PATH" aktivieren bei Installation
```

---

### Fehler: "Read-Host exception"

**Ursache:**
- Script läuft nicht-interaktiv
- z.B. in Git Bash oder via `cmd`

**Lösung:**
```powershell
# Starte mit PowerShell (NICHT cmd oder Git Bash)
powershell -ExecutionPolicy Bypass -File "Start-Auto-Claude-With-Sync-v2.ps1"
```

---

## 🧪 Tests

### Vollständiger Test

```powershell
.\Test-Sync-Script-Simple.ps1
```

**Erwartetes Ergebnis:**
```
====================================================================
  AUTO CLAUDE SYNC SCRIPT - TESTS
====================================================================

[TEST 1] Script Existenz...
  [OK] Script gefunden

[TEST 2] Git Repository...
  [OK] Git Repository erkannt

...

====================================================================
  TEST ZUSAMMENFASSUNG
====================================================================

Total Tests: 10
  [OK] Passed:  10
  [X] Failed:   0

Erfolgsquote: 100%

  ALLE TESTS BESTANDEN! Script ist BOMBENSICHER!
```

### Manueller Test: Dry Run

```powershell
# Starte mit NoPull (sicher)
.\Start-Auto-Claude-With-Sync-v2.ps1 -NoPull
```

**Erwartete Ausgabe:**
```
====================================================================
  AUTO CLAUDE - SMART STARTER MIT GITHUB SYNC
====================================================================

[1] Git Repository pruefen...
  [OK] Git Repository erkannt

[2] Lokale Aenderungen pruefen...
  [OK] Keine uncommitted changes

[3] GitHub Sync starten...
  [WARN] Pull uebersprungen (--NoPull)

[4] Python Environment pruefen...
  [OK] Python: Python 3.14.0
  [OK] Virtual Environment gefunden

====================================================================
  ALLE CHECKS BESTANDEN - STARTE AUTO CLAUDE
====================================================================
```

---

## 📚 Weitere Dokumentation

- **Schnellstart:** `START-HIER-GIT-SYNC.txt`
- **Auto Git Sync:** `SCHNELLSTART-GIT-SYNC.md`
- **Hauptdokumentation:** `CLAUDE.md`
- **Probleme:** `PROBLEMLÖSUNGEN.md`

---

## ✅ Checkliste

Hast du alles richtig konfiguriert?

- [ ] Git installiert (`git --version`)
- [ ] Python 3.12+ installiert (`python --version`)
- [ ] In Projekt-Verzeichnis (`cd C:\Projekte\auto-claude`)
- [ ] Script existiert (`Start-Auto-Claude-With-Sync-v2.ps1`)
- [ ] Desktop-Verknüpfungen erstellt (`.\Create-Safe-Sync-Shortcut.ps1`)
- [ ] Test erfolgreich (`.\Test-Sync-Script-Simple.ps1`)
- [ ] Dry Run erfolgreich (`.\Start-Auto-Claude-With-Sync-v2.ps1 -NoPull`)

**Wenn alle Checkboxen ✅:**
→ **Du bist bereit! 🚀**

---

**Version:** 1.0  
**Datum:** 31.12.2025  
**Status:** BOMBENSICHER ✅
