# 🇩🇪 Auto Claude - Deutsche Hilfe

Vollständige Dokumentation und Problemlösungen auf Deutsch.

---

## 🆘 Sie haben Probleme? START HIER!

### Schnell-Diagnose (30 Sekunden)

```bash
cd apps/backend
python diagnose.py
```

Dieses Tool findet automatisch alle Probleme und zeigt Ihnen, wie Sie sie beheben können.

---

## 📚 Dokumentation

### 1. Schnellstart & Diagnose

**Datei:** [`SCHNELLSTART-DIAGNOSE.md`](SCHNELLSTART-DIAGNOSE.md)

**Inhalt:**
- ⚡ Sofort-Diagnose in 30 Sekunden
- 🔧 Probleme beheben (Memory, Tasks, GitHub)
- 📊 Vollständige System-Diagnose
- ❓ Häufige Fehler und Lösungen

**Wann verwenden:** Wenn etwas nicht funktioniert und Sie schnell eine Lösung brauchen.

---

### 2. Vollständige Problemlösungen

**Datei:** [`PROBLEMLÖSUNGEN.md`](PROBLEMLÖSUNGEN.md)

**Inhalt:**
- **Problem 1:** Memory-System funktioniert nicht
  - Ursachen
  - Schritt-für-Schritt Lösungen
  - Konfigurationsbeispiele
  - Testing

- **Problem 2:** Kanban Board Abbrüche
  - Planning/Coding Prozesse werden abgebrochen
  - Task Recovery
  - Worktree Cleanup
  - Credit-Verschwendung minimieren

- **Problem 3:** GitHub Integration & "Done" Status
  - Wie der "Done" Status funktioniert
  - GitHub Commands nach Completion
  - Automatisches Pushen
  - Cursor Integration

**Wann verwenden:** Für detaillierte Erklärungen und erweiterte Lösungen.

---

### 3. Original Dokumentation (Englisch)

**Datei:** [`CLAUDE.md`](CLAUDE.md)

**Inhalt:**
- Vollständige Projekt-Architektur
- Alle Befehle und Workflows
- Entwickler-Guidelines
- API Dokumentation

**Wann verwenden:** Für Entwicklung und technische Details.

---

## 🔧 Diagnose-Tool

### Installation

Das Tool ist bereits enthalten, keine Installation nötig!

```bash
cd apps/backend
python diagnose.py
```

### Verwendung

#### 1. Alle Probleme finden

```bash
python diagnose.py
```

Überprüft:
- ✅ Python Version (benötigt 3.12+)
- ✅ `.env` Konfiguration
- ✅ Memory System (Graphiti)
- ✅ Ollama Status (wenn verwendet)
- ✅ Hängende Tasks
- ✅ Worktrees

#### 2. Memory reparieren

```bash
python diagnose.py --fix-memory
```

Interaktiv:
1. Erstellt/aktualisiert `.env`
2. Wählt Embedder Provider
3. Fügt Konfiguration hinzu

#### 3. Hängende Tasks reparieren

```bash
python diagnose.py --fix-stuck-tasks
```

Automatisch:
- Findet alle Tasks mit `status='in_progress'`
- Zeigt Details
- Setzt auf `backlog` zurück

#### 4. GitHub Status überprüfen

```bash
python diagnose.py --check-github
```

Zeigt:
- GitHub CLI Status
- Alle "done" Tasks
- Verfügbare Branches
- Push-Optionen

---

## 🎯 Häufige Probleme & Sofort-Lösungen

### Problem: Memory zeigt nichts an

**Symptom:** Memory-Anzeige im UI ist leer, keine Daten sichtbar.

**Ursache:** Memory (Graphiti) ist nicht konfiguriert oder deaktiviert.

**Lösung:**

```bash
cd apps/backend
python diagnose.py --fix-memory
```

Dann Electron App neu starten.

**Details:** Siehe [`PROBLEMLÖSUNGEN.md` → Abschnitt 1](PROBLEMLÖSUNGEN.md#1-memory-system-funktioniert-nicht)

---

### Problem: Planning/Coding bricht ab

**Symptom:** Tasks im Kanban Board bleiben im `in_progress` Status hängen.

**Ursache:** Prozess wurde unterbrochen oder App wurde neu gestartet.

**Lösung:**

```bash
cd apps/backend

# Option 1: Recovery
python run.py --spec 001 --recovery

# Option 2: Automatische Reparatur
python diagnose.py --fix-stuck-tasks
```

**Details:** Siehe [`PROBLEMLÖSUNGEN.md` → Abschnitt 2](PROBLEMLÖSUNGEN.md#2-kanban-board-abbrüche-bei-planningcoding)

---

### Problem: GitHub Push nach "Done"

**Frage:** "Kann Cursor sehen wenn ein Task 'done' ist, um zu GitHub zu pushen?"

**Antwort:** Ja! Cursor kann `implementation_plan.json` lesen und reagieren.

**Manuelle Lösung:**

```bash
# Nach erfolgreichem Merge (Status = done)
git checkout main
git push origin main
```

**Automatische Lösung:**

Siehe [`PROBLEMLÖSUNGEN.md` → Abschnitt 3](PROBLEMLÖSUNGEN.md#3-github-integration-und-done-status) für:
- Python Script für Auto-Push
- GitHub Actions Integration
- Cursor Rules Setup

---

## 📋 Checkliste: Erste Schritte

Wenn Sie Auto Claude das erste Mal verwenden:

### 1. System-Anforderungen überprüfen

- [ ] Python 3.12+ installiert
  ```bash
  python --version
  ```

- [ ] Node.js installiert (für Frontend)
  ```bash
  node --version
  ```

- [ ] Git installiert
  ```bash
  git --version
  ```

### 2. Installation

- [ ] Dependencies installieren
  ```bash
  # Von Root
  npm run install:all
  ```

- [ ] Backend Setup
  ```bash
  cd apps/backend
  uv venv
  uv pip install -r requirements.txt
  ```

### 3. Konfiguration

- [ ] `.env` Datei erstellen
  ```bash
  cd apps/backend
  python diagnose.py --fix-memory
  ```

- [ ] Claude Token setzen
  ```bash
  claude setup-token
  # Token in apps/backend/.env: CLAUDE_CODE_OAUTH_TOKEN=...
  ```

### 4. Optional: Ollama für Memory

- [ ] Ollama installieren
  - Windows: https://ollama.ai
  - macOS: `brew install ollama`
  - Linux: `curl -fsSL https://ollama.ai/install.sh | sh`

- [ ] Ollama starten
  ```bash
  ollama serve
  ```

- [ ] Embedding Model laden
  ```bash
  ollama pull embeddinggemma
  ```

### 5. Erste Diagnose

- [ ] System Check durchführen
  ```bash
  cd apps/backend
  python diagnose.py
  ```

- [ ] Alle Checks sollten ✅ sein
  - Python Version
  - .env Datei
  - Memory System
  - Keine hängenden Tasks

### 6. Electron App starten

- [ ] App starten
  ```bash
  # Von Root
  npm run dev
  ```

- [ ] Einstellungen überprüfen
  - Settings → Project Settings
  - Memory sollte "Enabled" sein (grün)

### 7. Ersten Spec erstellen

- [ ] Spec erstellen
  ```bash
  cd apps/backend
  python spec_runner.py --task "Erstelle eine Login-Seite"
  ```

- [ ] Spec ausführen
  ```bash
  python run.py --spec 001
  ```

### 8. Workflow testen

- [ ] Task im Kanban Board beobachten
  - `backlog` → `in_progress` → `ai_review` → `human_review`

- [ ] Changes reviewen
  ```bash
  python run.py --spec 001 --review
  ```

- [ ] Mergen
  ```bash
  python run.py --spec 001 --merge
  ```

- [ ] Zu GitHub pushen
  ```bash
  git push origin main
  ```

---

## 🚨 Notfall-Hilfe

Wenn gar nichts funktioniert:

### 1. Vollständiges Reset

```bash
# Backend cleanup
cd apps/backend
rm -rf .venv
rm -rf __pycache__
rm -f .env

# Frontend cleanup
cd ../frontend
rm -rf node_modules
rm -rf out

# Neu installieren
cd ../..
npm run install:all
```

### 2. Memory zurücksetzen

```bash
# Memory Datenbank löschen
rm -rf ~/.auto-claude/memories/

# Neu konfigurieren
cd apps/backend
python diagnose.py --fix-memory
```

### 3. Alle Tasks zurücksetzen

```bash
cd apps/backend
python diagnose.py --fix-stuck-tasks
```

### 4. Worktrees aufräumen

```bash
# Alle Worktrees auflisten
git worktree list

# Einzeln entfernen
git worktree remove .worktrees/001-spec-name --force

# Alle entfernen
rm -rf .worktrees/
git worktree prune
```

---

## 📞 Support

### Option 1: Selbsthilfe

1. **Diagnose Tool ausführen**
   ```bash
   python diagnose.py
   ```

2. **Dokumentation lesen**
   - [`SCHNELLSTART-DIAGNOSE.md`](SCHNELLSTART-DIAGNOSE.md) für schnelle Lösungen
   - [`PROBLEMLÖSUNGEN.md`](PROBLEMLÖSUNGEN.md) für Details

3. **Logs überprüfen**
   ```bash
   # Backend
   cat apps/backend/logs/auto-claude.log
   
   # Memory
   cat ~/.auto-claude/memories/debug.log
   
   # Electron
   # Windows: %APPDATA%\auto-claude\logs\
   # macOS: ~/Library/Logs/auto-claude/
   # Linux: ~/.config/auto-claude/logs/
   ```

### Option 2: Community

- **GitHub Issues:** https://github.com/your-repo/auto-claude/issues
- **Discussions:** https://github.com/your-repo/auto-claude/discussions

### Option 3: GitHub Issue erstellen

**Template:**

```markdown
## Problem

[Kurze Beschreibung]

## System Info

- OS: [Windows 11 / macOS 14 / Ubuntu 22.04]
- Python: [Ausgabe von `python --version`]
- Auto Claude: [Version aus package.json]

## Diagnose

```bash
# Ausgabe von:
python diagnose.py
```

## Logs

[Relevante Logs aus apps/backend/logs/]

## Reproduzieren

1. [Schritt 1]
2. [Schritt 2]
3. [Fehler tritt auf]
```

---

## 🎓 Lernressourcen

### Video-Tutorials (geplant)

- [ ] Installation & Setup
- [ ] Erste Schritte
- [ ] Memory System nutzen
- [ ] Task Workflow
- [ ] GitHub Integration

### Blog Posts (geplant)

- [ ] "Auto Claude in 10 Minuten"
- [ ] "Memory verstehen und nutzen"
- [ ] "Advanced Workflows"
- [ ] "Troubleshooting Guide"

---

## 🔗 Nützliche Links

- **Hauptdokumentation (EN):** [`CLAUDE.md`](CLAUDE.md)
- **Problemlösungen (DE):** [`PROBLEMLÖSUNGEN.md`](PROBLEMLÖSUNGEN.md)
- **Schnellstart (DE):** [`SCHNELLSTART-DIAGNOSE.md`](SCHNELLSTART-DIAGNOSE.md)
- **Release Notes:** [`CHANGELOG.md`](CHANGELOG.md)
- **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md)

---

## 💡 Tipps & Tricks

### Tipp 1: Kleinere Tasks = Weniger Credits

Erstellen Sie kleinere, fokussierte Specs statt große Features:

```bash
# Gut ✅
python spec_runner.py --task "Login Button mit Email/Password"

# Zu groß ❌
python spec_runner.py --task "Komplettes Authentifizierungs-System mit OAuth, 2FA, Password Reset, etc."
```

### Tipp 2: Recovery nutzen statt Neustart

Wenn ein Task abbricht:

```bash
# Statt neu zu starten ❌
python run.py --spec 001

# Recovery verwenden ✅
python run.py --spec 001 --recovery
```

Spart Credits und behält bereits gemachte Arbeit.

### Tipp 3: Memory nutzen

Das Memory-System merkt sich:
- Was funktioniert hat
- Was schief ging
- Best Practices
- Projekt-spezifische Patterns

Je mehr Sie es nutzen, desto besser werden die Ergebnisse!

### Tipp 4: Regelmäßig Diagnosis

Führen Sie regelmäßig aus:

```bash
python diagnose.py
```

Findet Probleme bevor sie groß werden.

---

## 📊 Statistiken

Nach erfolgreicher Einrichtung können Sie sehen:

### Memory Stats

```bash
# Im UI:
Settings → Project Settings → Memory
- Episodes: Anzahl gespeicherter Memories
- Last Session: Letzte Session-Nummer
```

### Task Stats

```bash
# Im Kanban Board:
- Backlog: [Anzahl]
- In Progress: [Anzahl]
- Review: [Anzahl]
- Done: [Anzahl]
```

### Credits Used

Wird angezeigt in:
- Task Details
- Session Logs
- `.auto-claude/specs/*/logs/`

---

## 🎯 Nächste Schritte

Nachdem alles funktioniert:

1. ✅ **Erstellen Sie Ihren ersten Spec**
   ```bash
   python spec_runner.py --task "Ihr erstes Feature"
   ```

2. ✅ **Beobachten Sie den Workflow**
   - Öffnen Sie Kanban Board
   - Schauen Sie zu wie Auto Claude arbeitet

3. ✅ **Reviewen und Mergen**
   - Review: `--review`
   - Merge: `--merge`
   - Push zu GitHub

4. ✅ **Memory nutzen**
   - Schauen Sie sich Memory Tab an
   - Suchen Sie nach relevanten Insights
   - Lassen Sie Auto Claude von vergangenen Sessions lernen

5. ✅ **Experimentieren**
   - Verschiedene Spec-Typen
   - Verschiedene Complexitäts-Level
   - Parallele Tasks (subagents)

---

**Viel Erfolg mit Auto Claude! 🚀**

Bei Fragen: Starten Sie mit `python diagnose.py`

---

**Version:** 1.0  
**Letzte Aktualisierung:** 30.12.2025  
**Sprache:** Deutsch 🇩🇪  
**Maintainer:** Auto Claude Team

