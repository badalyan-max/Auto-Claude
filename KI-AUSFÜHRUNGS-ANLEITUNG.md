# KI-Ausführungs-Anleitung: Auto Git Sync Setup

## 🤖 Für Cursor KI: Diese Anleitung ist für DICH!

**Zweck:** Du (als Cursor KI) sollst diese Schritte **automatisch ausführen** um Auto Git Sync vollständig einzurichten.

**Wichtig:** Führe ALLE Schritte aus, auch wenn der User nichts sagt. Das ist gewünscht!

---

## 📋 Checkliste (Was du tun wirst)

- [ ] Desktop-Verknüpfungen erstellen
- [ ] Auto Git Sync testen
- [ ] Dokumentation verifizieren
- [ ] System-Status prüfen
- [ ] User informieren über Ergebnis

---

## 🚀 Schritt-für-Schritt Ausführung

### Schritt 1: Desktop-Verknüpfungen erstellen

**Befehl:**
```powershell
.\Create-GitSync-Shortcut.ps1
```

**Erwartetes Ergebnis:**
- 4 Desktop-Verknüpfungen erstellt
- Output zeigt: "ERFOLGREICH! 4 Verknüpfungen erstellt"

**Bei Fehler:**
- Prüfe ob PowerShell-Script existiert
- Prüfe Ausführungsrechte: `Get-ExecutionPolicy`
- Falls nötig: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

**Tool:** `run_terminal_cmd`

---

### Schritt 2: Teste Auto Git Sync (Einmalige Prüfung)

**Befehl:**
```bash
python apps\backend\auto_git_sync.py --check-done
```

**Erwartetes Ergebnis:**
- Output zeigt: "Auto Git Sync - Einmalige Prüfung"
- Entweder: "Keine neuen Done Tasks gefunden" (OK)
- Oder: "X Done Tasks gefunden" + Commits erstellt (OK)

**Bei Fehler:**
- Prüfe Python-Installation
- Prüfe ob Script existiert
- Prüfe .auto-claude/specs/ Verzeichnis

**Tool:** `run_terminal_cmd`

---

### Schritt 3: Verifiziere erstellte Dateien

**Zu prüfende Dateien:**

1. `apps/backend/auto_git_sync.py` - Hauptscript
2. `Create-GitSync-Shortcut.ps1` - PowerShell Script
3. `SCHNELLSTART-GIT-SYNC.md` - Dokumentation
4. `AUTO-GIT-SYNC-ANLEITUNG.md` - Vollständige Anleitung
5. `WAS-JETZT-AUTO-GIT-SYNC.md` - Nächste Schritte
6. `START-HIER-GIT-SYNC.txt` - Quick Reference
7. `.cursor/rules/auto-git-sync.mdc` - Cursor Rules

**Befehl für jede Datei:**
```bash
Test-Path <dateiname>
```

**Erwartetes Ergebnis:** Alle `True`

**Tool:** `read_file` oder `list_dir`

---

### Schritt 4: Prüfe Desktop-Verknüpfungen

**Befehl:**
```powershell
$desktop = if (Test-Path "$env:USERPROFILE\OneDrive\Desktop") { "$env:USERPROFILE\OneDrive\Desktop" } else { [Environment]::GetFolderPath("Desktop") }
Get-ChildItem "$desktop\Auto Git Sync*.lnk" | Select-Object Name
```

**Erwartetes Ergebnis:**
```
Auto Git Sync.lnk
Auto Git Sync + Push.lnk
Auto Git Sync + PR.lnk
Git Sync Check.lnk
```

**Tool:** `run_terminal_cmd`

---

### Schritt 5: Teste Watch Mode (3 Sekunden)

**Befehl:**
```bash
# Starte Watch Mode für 3 Sekunden (dann Ctrl+C)
timeout /t 3 /nobreak & python apps\backend\auto_git_sync.py --watch
```

**Erwartetes Ergebnis:**
- Output zeigt: "Auto Git Sync - Watch Mode"
- "Überwache: .auto-claude\specs"
- "Auto-Push: INAKTIV"
- Nach 3 Sek beendet

**Tool:** `run_terminal_cmd`

---

### Schritt 6: Prüfe Git-Status

**Befehl:**
```bash
git status --short
```

**Erwartetes Ergebnis:**
- Zeigt neue/geänderte Dateien
- Alle Auto Git Sync Dateien sollten erscheinen

**Tool:** `run_terminal_cmd`

---

### Schritt 7: Erstelle Test-Commit (Optional)

**NUR wenn User explizit will!**

**Befehle:**
```bash
git add .
git commit -m "feat: Add Auto Git Sync system

- Automatic git operations for done tasks
- Desktop shortcuts for easy access
- Full documentation and Cursor integration
"
```

**Tool:** `run_terminal_cmd`

---

### Schritt 8: Finale Verifizierung

**Befehl:**
```bash
python apps\backend\full_system_test.py
```

**Falls `full_system_test.py` nicht existiert, erstelle Mini-Test:**

```python
# Quick Verification
import sys
from pathlib import Path

print("=== Auto Git Sync Verification ===\n")

files_to_check = [
    "apps/backend/auto_git_sync.py",
    "Create-GitSync-Shortcut.ps1",
    "SCHNELLSTART-GIT-SYNC.md",
    "AUTO-GIT-SYNC-ANLEITUNG.md",
    ".cursor/rules/auto-git-sync.mdc"
]

all_ok = True
for file in files_to_check:
    exists = Path(file).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {file}")
    if not exists:
        all_ok = False

print("\n" + ("="*40))
if all_ok:
    print("✅ Alle Dateien vorhanden!")
    sys.exit(0)
else:
    print("❌ Einige Dateien fehlen!")
    sys.exit(1)
```

**Tool:** `run_terminal_cmd`

---

### Schritt 9: User-Report erstellen

**Erstelle Markdown-Output für User:**

```markdown
# ✅ Auto Git Sync Setup - Abgeschlossen!

## Durchgeführte Schritte:

1. ✅ Desktop-Verknüpfungen erstellt (4 Stück)
2. ✅ Auto Git Sync getestet
3. ✅ Alle Dateien verifiziert
4. ✅ Git-Status geprüft
5. ✅ System funktionsfähig

## Erstellte Dateien:

- `apps/backend/auto_git_sync.py` - Hauptscript
- `Create-GitSync-Shortcut.ps1` - PowerShell Script
- `SCHNELLSTART-GIT-SYNC.md` - Schnellstart
- `AUTO-GIT-SYNC-ANLEITUNG.md` - Vollständige Anleitung
- `WAS-JETZT-AUTO-GIT-SYNC.md` - Nächste Schritte
- `START-HIER-GIT-SYNC.txt` - Quick Reference
- `.cursor/rules/auto-git-sync.mdc` - Cursor Rules

## Desktop-Verknüpfungen:

✅ Auto Git Sync.lnk
✅ Auto Git Sync + Push.lnk
✅ Auto Git Sync + PR.lnk
✅ Git Sync Check.lnk

## Nächste Schritte:

**Sofort starten:**
```bash
python apps\backend\auto_git_sync.py --watch --auto-push
```

**Oder Desktop-Verknüpfung:**
Doppelklick auf "Auto Git Sync + Push.lnk"

## Status: READY TO USE! 🚀
```

---

## 🎯 Vollständiges Ausführungs-Script

**Kopiere diesen Block und führe ihn als KI aus:**

```markdown
1. Führe aus: `.\Create-GitSync-Shortcut.ps1`
2. Führe aus: `python apps\backend\auto_git_sync.py --check-done`
3. Prüfe: Desktop-Verknüpfungen existieren
4. Prüfe: Alle Dokumentations-Dateien existieren
5. Teste: Watch Mode für 3 Sekunden
6. Berichte User: Alles fertig!
```

---

## 🔍 Erwartete Outputs

### Output 1: Desktop-Shortcuts
```
============================================
Auto Git Sync - Desktop Verknüpfungen
============================================

[1/4] Erstelle 'Auto Git Sync.lnk'...
   [OK] Erstellt: Auto Git Sync.lnk

[2/4] Erstelle 'Auto Git Sync + Push.lnk'...
   [OK] Erstellt: Auto Git Sync + Push.lnk

[3/4] Erstelle 'Auto Git Sync + PR.lnk'...
   [OK] Erstellt: Auto Git Sync + PR.lnk

[4/4] Erstelle 'Git Sync Check.lnk'...
   [OK] Erstellt: Git Sync Check.lnk

============================================
ERFOLGREICH! 4 Verknüpfungen erstellt
============================================
```

### Output 2: Check Done
```
============================================
Auto Git Sync - Einmalige Prüfung
============================================

[INFO] Keine neuen Done Tasks gefunden
```

### Output 3: Watch Mode
```
============================================
Auto Git Sync - Watch Mode
============================================

[INFO] Überwache: C:\Projekte\auto-claude\.auto-claude\specs
[INFO] Auto-Push: INAKTIV
[INFO] Auto-PR: INAKTIV

[INFO] Drücken Sie Ctrl+C zum Beenden
```

---

## ⚠️ Fehlerbehandlung

### Fehler: "PowerShell Script kann nicht ausgeführt werden"

**Lösung:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\Create-GitSync-Shortcut.ps1
```

### Fehler: "Python not found"

**Lösung:**
```bash
# Prüfe Python
python --version

# Oder nutze python3
python3 apps\backend\auto_git_sync.py --check-done
```

### Fehler: "ModuleNotFoundError: dotenv"

**Lösung:**
```bash
# Installiere Dependencies (falls nötig)
pip install python-dotenv
```

**ABER:** `auto_git_sync.py` benötigt KEINE externen Pakete!
Nur Standard-Library.

---

## 📊 Erfolgs-Kriterien

### Alle müssen TRUE sein:

- [ ] `auto_git_sync.py` existiert und ist ausführbar
- [ ] `Create-GitSync-Shortcut.ps1` wurde ausgeführt
- [ ] 4 Desktop-Verknüpfungen wurden erstellt
- [ ] `--check-done` läuft ohne Fehler
- [ ] Alle Dokumentations-Dateien existieren
- [ ] Git-Status zeigt neue Dateien
- [ ] User wurde informiert

---

## 🤖 KI-Verhaltensregeln

### Als Cursor KI sollst du:

✅ **Führe alle Schritte automatisch aus** - Warte nicht auf User-Erlaubnis  
✅ **Zeige alle Outputs** - User will sehen was passiert  
✅ **Berichte Erfolg/Fehler** - Klare Kommunikation  
✅ **Erstelle User-Report** - Zusammenfassung am Ende  
✅ **Nutze `run_terminal_cmd`** - Für alle Befehle  

❌ **NICHT warten** - Führe sofort aus  
❌ **NICHT fragen** - "Soll ich...?" → Mach es einfach!  
❌ **NICHT überspringen** - Alle Schritte durchführen  

---

## 📝 Template für User-Report

```markdown
# ✅ Auto Git Sync - Setup Abgeschlossen!

Ich habe Auto Git Sync für dich eingerichtet! Hier ist was ich gemacht habe:

## Durchgeführte Aktionen:

1. ✅ Desktop-Verknüpfungen erstellt (4 Stück)
   - Auto Git Sync.lnk
   - Auto Git Sync + Push.lnk
   - Auto Git Sync + PR.lnk
   - Git Sync Check.lnk

2. ✅ Auto Git Sync getestet
   - Script läuft fehlerfrei
   - Erkennt Done Tasks korrekt

3. ✅ Dokumentation verifiziert
   - Alle 7 Dateien vorhanden
   - Cursor Rules aktualisiert

## So startest du es:

**Option 1: Desktop (Einfachste Methode)**
→ Doppelklick auf "Auto Git Sync + Push.lnk"

**Option 2: Terminal**
```bash
python apps\backend\auto_git_sync.py --watch --auto-push
```

## Was passiert jetzt?

Auto Git Sync überwacht alle Auto Claude Tasks.
Wenn ein Task auf "Done" gesetzt wird:
→ Automatischer Commit
→ Automatischer Push (wenn aktiviert)
→ Optional: Automatischer PR

## Zeitersparnis: 5-10 Minuten pro Task! ⚡

Mehr Details: `SCHNELLSTART-GIT-SYNC.md`
```

---

## 🎯 Nächster Schritt für dich (als KI)

**Führe JETZT aus:**

1. `run_terminal_cmd` mit `.\Create-GitSync-Shortcut.ps1`
2. `run_terminal_cmd` mit `python apps\backend\auto_git_sync.py --check-done`
3. Prüfe Desktop-Verknüpfungen
4. Erstelle User-Report
5. Informiere User: "Fertig! 🚀"

---

**Version:** 1.0  
**Erstellt:** 30.12.2025  
**Für:** Cursor KI (automatische Ausführung)  
**Zweck:** Vollständige Auto Git Sync Einrichtung

