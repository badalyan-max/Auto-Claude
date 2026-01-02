# 🔄 Auto-Claude Data Synchronization

Dieses System ermöglicht die Synchronisation deiner **Kanban Board Daten** zwischen verschiedenen Geräten über GitHub.

## 📋 Was wird synchronisiert?

- ✅ **Kanban Board** - Alle deine Tasks und deren Status
- ✅ **Task Specs** - Alle Task-Spezifikationen und Requirements
- ✅ **Insights** - Session-Daten und Analysen
- ✅ **Project Index** - Projekt-Metadaten

## 🎯 Konzept

### Zwei-Branch-System:

1. **`develop` Branch** (Haupt-Branch)
   - Enthält den **Code** von Auto-Claude
   - `.auto-claude/` ist im `.gitignore` (Daten werden NICHT getrackt)
   - Für normale Entwicklung

2. **`data-sync` Branch** (Daten-Branch)
   - Enthält `.auto-claude/` Verzeichnis
   - Nur für Daten-Synchronisation
   - Wird NICHT für Code-Entwicklung verwendet

## 🚀 Verwendung

### Auf dem PC (Daten HOCHLADEN):

```powershell
# Aktualisiert GitHub mit deinen lokalen Kanban-Daten
.\sync-to-cloud.ps1
```

**Was passiert:**
1. Wechselt zum `data-sync` Branch
2. Fügt `.auto-claude` Änderungen hinzu
3. Erstellt einen Commit
4. Pusht zu GitHub
5. Wechselt zurück zu deinem vorherigen Branch

### Auf dem Laptop (Daten HERUNTERLADEN):

```powershell
# Lädt neueste Kanban-Daten von GitHub
.\sync-from-cloud.ps1
```

**Was passiert:**
1. Wechselt zum `data-sync` Branch
2. Holt neueste Daten von GitHub
3. Überschreibt lokale `.auto-claude` mit Cloud-Daten
4. Wechselt zurück zu deinem vorherigen Branch

## 📖 Typischer Workflow

### Szenario: Du arbeitest auf dem PC, willst dann auf dem Laptop weiterarbeiten

**Auf dem PC:**
```powershell
# 1. Arbeite normal mit Auto-Claude
# 2. Bevor du den PC verlässt:
.\sync-to-cloud.ps1
```

**Auf dem Laptop:**
```powershell
# 1. Bevor du mit Auto-Claude arbeitest:
.\sync-from-cloud.ps1

# 2. Arbeite mit Auto-Claude

# 3. Bevor du fertig bist:
.\sync-to-cloud.ps1
```

**Zurück auf dem PC:**
```powershell
# 1. Bevor du startest:
.\sync-from-cloud.ps1

# 2. Arbeite weiter...
```

## ⚠️ Wichtige Hinweise

### DO's ✅

- ✅ **Immer** `sync-from-cloud.ps1` ausführen, BEVOR du mit Auto-Claude arbeitest
- ✅ **Immer** `sync-to-cloud.ps1` ausführen, NACHDEM du mit Auto-Claude fertig bist
- ✅ Bei Konflikten wird ein Backup erstellt (`.auto-claude-backup-[timestamp]`)

### DON'Ts ❌

- ❌ **NICHT** gleichzeitig auf mehreren Geräten arbeiten (führt zu Konflikten!)
- ❌ **NICHT** manuell auf dem `data-sync` Branch entwickeln
- ❌ **NICHT** `.auto-claude` Dateien manuell in `develop` Branch committen

## 🔧 Erste Einrichtung auf neuem Gerät

Auf deinem **Laptop** (oder anderem Gerät):

```powershell
# 1. Repository klonen
git clone https://github.com/badalyan-max/Auto-Claude.git
cd Auto-Claude

# 2. Zum develop Branch wechseln
git checkout develop

# 3. Data-sync Branch holen
git fetch origin data-sync
git checkout data-sync
git checkout develop

# 4. Neueste Daten holen
.\sync-from-cloud.ps1

# 5. Fertig! Du hast jetzt dieselben Kanban-Daten wie auf dem PC
```

## 🐛 Troubleshooting

### Problem: "Failed to switch to data-sync branch"

**Lösung:**
```powershell
# Prüfe ob Branch existiert
git branch -a

# Falls nicht, hole ihn:
git fetch origin data-sync:data-sync
```

### Problem: "Merge conflict detected"

**Lösung:**
```powershell
# Lokale Änderungen verwerfen und Cloud-Version nehmen:
git checkout data-sync
git reset --hard origin/data-sync
git checkout develop
```

### Problem: Lokale Änderungen gehen verloren

**Lösung:**
```powershell
# Sync-Skripte erstellen automatisch Backups!
# Suche nach: .auto-claude-backup-[timestamp]

# Wiederherstellen:
Remove-Item .auto-claude -Recurse -Force
Copy-Item .auto-claude-backup-[timestamp] .auto-claude -Recurse
```

## 📊 Status prüfen

```powershell
# Auf welchem Branch bin ich?
git branch

# Gibt es neue Daten in der Cloud?
git fetch origin data-sync
git log HEAD..origin/data-sync --oneline

# Habe ich lokale Änderungen?
git diff data-sync origin/data-sync
```

## 🎯 Best Practices

1. **Sync-Routine:**
   - Morgens: `sync-from-cloud.ps1` 📥
   - Abends: `sync-to-cloud.ps1` 📤

2. **Vor wichtigen Tasks:**
   - Immer neueste Daten holen
   - Verhindert Arbeit auf veraltetem Stand

3. **Bei Laptop-Wechsel:**
   - Immer pushen vom aktuellen Gerät
   - Dann pullen auf neuem Gerät

## 💡 Tipp: Automatisierung

Du kannst die Sync-Skripte in deine tägliche Routine einbauen:

```powershell
# Morgens beim Start:
.\sync-from-cloud.ps1 && npm run dev

# Abends beim Beenden:
.\sync-to-cloud.ps1
```

## 🔐 Sicherheit

- ✅ Daten werden über **privates GitHub Repository** synchronisiert
- ✅ Nur du hast Zugriff (Fork in deinem Account)
- ✅ Automatische Backups bei Konflikten
- ✅ Git-History erlaubt Zurückrollen zu alten Ständen

## 📚 Weitere Infos

- **Code-Updates** werden weiterhin über `develop` Branch verwaltet
- **Daten-Updates** nur über `data-sync` Branch
- Beide Systeme arbeiten unabhängig voneinander

---

**Happy Syncing! 🚀**

Bei Fragen oder Problemen: Check die Skript-Ausgaben, sie sind sehr detailliert!
