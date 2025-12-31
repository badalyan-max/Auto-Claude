# 🚀 Auto Claude - Schnellstart Diagnose

Probleme mit Auto Claude? Führen Sie diese Schritte aus:

---

## ⚡ Sofort-Diagnose (30 Sekunden)

```bash
cd apps/backend
python diagnose.py
```

Das Script überprüft:
- ✅ Python Version (benötigt 3.12+)
- ✅ `.env` Konfiguration
- ✅ Memory System (Graphiti)
- ✅ Hängende Tasks
- ✅ Worktrees Status

---

## 🔧 Probleme beheben

### Problem 1: Memory funktioniert nicht

**Symptom:** Memory-Anzeige ist leer, keine Daten sichtbar

**Lösung:**
```bash
cd apps/backend
python diagnose.py --fix-memory
```

Das Script:
1. Erstellt/aktualisiert `.env` Datei
2. Fragt nach Embedder Provider (Ollama/OpenAI/Voyage)
3. Fügt benötigte Konfiguration hinzu

**Danach:**
- Starten Sie die Electron App NEU
- Gehen Sie zu Settings → Project Settings → Memory
- Überprüfen Sie ob "Enabled" grün ist

---

### Problem 2: Tasks hängen im Kanban Board

**Symptom:** Tasks bleiben im "in_progress" Status hängen

**Lösung:**
```bash
cd apps/backend
python diagnose.py --fix-stuck-tasks
```

Das Script:
1. Findet alle hängenden Tasks
2. Zeigt Details an
3. Setzt Tasks zurück auf "backlog"

**Danach:**
- Öffnen Sie das Kanban Board
- Starten Sie den Task neu mit "Start"

---

### Problem 3: GitHub Push nach "Done"

**Überprüfung:**
```bash
cd apps/backend
python diagnose.py --check-github
```

Das Script zeigt:
- ✅ GitHub CLI Status
- ✅ Alle "done" Tasks
- ✅ Verfügbare Git Branches
- ✅ Auto Claude Branches

**Manueller Push:**
```bash
cd /pfad/zu/ihrem/projekt

# Überprüfen Sie den Status
git status

# Pushen Sie zu GitHub
git push origin main

# Optional: Feature-Branch pushen
git push origin auto-claude/001-your-spec-name
```

---

## 📊 Vollständige System-Diagnose

```bash
cd apps/backend

# Alle Checks ausführen
python diagnose.py

# Mit GitHub Check
python diagnose.py --check-github
```

### Erwartete Ausgabe (Beispiel)

```
============================================================
🔍 Auto Claude System Diagnose
============================================================

Projekt: C:\Projekte\auto-claude

============================================================
1️⃣  Python Version
============================================================

ℹ️  Python Version: 3.12.0
✅ Python 3.12 ist installiert (3.12+ erforderlich für LadybugDB)

============================================================
2️⃣  Konfigurationsdatei
============================================================

✅ .env Datei gefunden: C:\Projekte\auto-claude\apps\backend\.env

============================================================
3️⃣  Memory System (Graphiti)
============================================================

ℹ️  Memory Status:
  - Enabled: True
  - Available: True
  - Database: auto_claude_memory_ollama_embeddinggemma_768
  - DB Path: ~/.auto-claude/memories
  - Embedder Provider: ollama

✅ Memory Konfiguration ist OK!

ℹ️  Überprüfe Ollama: http://localhost:11434
✅ Ollama läuft!
✅ Embedding Model 'embeddinggemma' ist verfügbar!

============================================================
4️⃣  Task Status
============================================================

✅ Keine hängenden Tasks gefunden!

============================================================
5️⃣  Git Worktrees
============================================================

ℹ️  Gefunden: 2 Worktrees
  - 001-authentication
  - 002-dashboard

============================================================
📊 Zusammenfassung
============================================================

✅ Alle Systeme funktionieren! 🎉
```

---

## ❓ Häufige Fehler und Lösungen

### Fehler: "Python 3.10 ist zu alt"

**Problem:** LadybugDB benötigt Python 3.12+

**Lösung:**
```bash
# Windows
# Download von: https://www.python.org/downloads/

# macOS
brew install python@3.12

# Linux
sudo apt install python3.12
```

---

### Fehler: ".env Datei nicht gefunden"

**Lösung:**
```bash
cd apps/backend
python diagnose.py --fix-memory
```

---

### Fehler: "Kann keine Verbindung zu Ollama herstellen"

**Lösung:**
```bash
# 1. Ollama installieren
# Windows: Download von https://ollama.ai
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# 2. Ollama starten
ollama serve

# 3. Model herunterladen
ollama pull embeddinggemma
```

---

### Fehler: "Task X ist stuck in 'in_progress'"

**Lösung:**
```bash
cd apps/backend

# Automatisch reparieren
python diagnose.py --fix-stuck-tasks

# ODER: Manuell mit run.py
python run.py --spec 001 --recovery
```

---

### Fehler: "Memory zeigt keine Daten"

**Mögliche Ursachen:**

1. **Memory wurde noch nie initialisiert**
   - Lösung: Starten Sie einen Task, Memory wird automatisch initialisiert

2. **Embedder Provider nicht konfiguriert**
   - Lösung: `python diagnose.py --fix-memory`

3. **Ollama Model fehlt**
   - Lösung: `ollama pull embeddinggemma`

4. **Falscher Provider in .env**
   - Überprüfen Sie: `GRAPHITI_EMBEDDER_PROVIDER=ollama`

---

## 🎯 Checkliste: "Mein System funktioniert nicht"

Arbeiten Sie diese Liste ab:

- [ ] Python 3.12+ installiert? → `python --version`
- [ ] `.env` Datei existiert? → `ls apps/backend/.env`
- [ ] `GRAPHITI_ENABLED=true` gesetzt? → `cat apps/backend/.env | grep GRAPHITI`
- [ ] Ollama läuft? (wenn verwendet) → `curl http://localhost:11434`
- [ ] Embedding Model installiert? → `ollama list`
- [ ] Electron App neugestartet? → Schließen und neu öffnen
- [ ] Stuck Tasks? → `python diagnose.py --fix-stuck-tasks`

---

## 📞 Weitere Hilfe

Wenn die Probleme weiterhin bestehen:

### 1. Logs überprüfen

```bash
# Backend Logs
cat apps/backend/logs/auto-claude.log

# Memory Logs  
cat ~/.auto-claude/memories/debug.log

# Electron Logs (Windows)
%APPDATA%\auto-claude\logs\

# Electron Logs (macOS)
~/Library/Logs/auto-claude/

# Electron Logs (Linux)
~/.config/auto-claude/logs/
```

### 2. Debug-Modus aktivieren

In `apps/backend/.env`:
```bash
DEBUG=true
AUTO_CLAUDE_DEBUG=true
GRAPHITI_DEBUG=true
```

### 3. Vollständige Dokumentation

Siehe: `PROBLEMLÖSUNGEN.md` für detaillierte Anleitungen

### 4. GitHub Issue erstellen

Wenn nichts hilft, erstellen Sie ein Issue mit:

**Template:**
```markdown
## Problem Beschreibung
[Beschreiben Sie das Problem]

## System Info
- OS: Windows/macOS/Linux
- Python Version: [Ausgabe von `python --version`]
- Auto Claude Version: [Aus package.json]

## Diagnose Ausgabe
[Ausgabe von `python diagnose.py`]

## Logs
[Relevante Logs aus apps/backend/logs/]

## Schritte zum Reproduzieren
1. [Schritt 1]
2. [Schritt 2]
3. ...
```

---

## 🚀 Nächste Schritte

Nachdem Sie die Probleme behoben haben:

1. ✅ Testen Sie das Memory System
   - Erstellen Sie einen neuen Spec
   - Überprüfen Sie Memory Tab
   - Suchen Sie nach Memories

2. ✅ Testen Sie Task Workflow
   - Starten Sie einen Task
   - Beobachten Sie Status-Übergänge
   - Merge nach Completion

3. ✅ Testen Sie GitHub Integration
   - Merge einen Task
   - Push zu GitHub
   - Überprüfen Sie Remote

---

**Version:** 1.0  
**Letzte Aktualisierung:** 30.12.2025  
**Sprache:** Deutsch 🇩🇪

