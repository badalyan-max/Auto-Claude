# 🔧 Auto Claude - Problemlösungen

Lösungen für die aktuellen Probleme mit Auto Claude.

---

## 📋 Inhaltsverzeichnis

1. [Memory-System funktioniert nicht](#1-memory-system-funktioniert-nicht)
2. [Kanban Board: Abbrüche bei Planning/Coding](#2-kanban-board-abbrüche-bei-planningcoding)
3. [GitHub Integration und "Done" Status](#3-github-integration-und-done-status)

---

## 1. Memory-System funktioniert nicht

### Problem
Das Memory-System (Graphiti) zeigt keine Daten an. Die Memory-Anzeige bleibt leer.

### Ursachen
Das Memory-System basiert auf **Graphiti** mit einer eingebetteten Graph-Datenbank (LadybugDB). Häufigste Ursachen:

- ❌ `GRAPHITI_ENABLED` ist nicht auf `true` gesetzt
- ❌ Fehlende Embedder-Provider-Konfiguration (für semantische Suche)
- ❌ Python Version < 3.12 (LadybugDB benötigt Python 3.12+)
- ❌ Memory wurde für diesen Spec noch nicht initialisiert

### Lösung: Memory-Konfiguration überprüfen

#### Schritt 1: `.env` Datei erstellen/überprüfen

Die `.env` Datei sollte sich in `apps/backend/.env` befinden.

**Minimale Konfiguration (mit Ollama - lokal, kostenlos):**

```bash
# Memory aktivieren
GRAPHITI_ENABLED=true

# Embedder Provider (für semantische Suche)
GRAPHITI_EMBEDDER_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=embeddinggemma
OLLAMA_EMBEDDING_DIM=768

# Alternativ: OpenAI (benötigt API Key)
# GRAPHITI_EMBEDDER_PROVIDER=openai
# OPENAI_API_KEY=your-api-key-here
```

**Vollständige Konfiguration mit allen Optionen:**

```bash
# ================================
# MEMORY-SYSTEM (Graphiti + LadybugDB)
# ================================

# Core - Memory aktivieren
GRAPHITI_ENABLED=true

# Embedder Provider (wählen Sie einen):
# - ollama (lokal, kostenlos, keine API Keys)
# - openai (beste Qualität, benötigt API Key)
# - voyage (spezialisiert für Embeddings, benötigt API Key)
# - google (Gemini, benötigt API Key)
GRAPHITI_EMBEDDER_PROVIDER=ollama

# Database Settings
GRAPHITI_DATABASE=auto_claude_memory
GRAPHITI_DB_PATH=~/.auto-claude/memories

# ================================
# OLLAMA (Lokal - Empfohlen für Beginner)
# ================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=embeddinggemma
OLLAMA_EMBEDDING_DIM=768

# Andere unterstützte Ollama Modelle:
# - qwen3-embedding:0.6b (dim: 1024)
# - qwen3-embedding:4b (dim: 2560)
# - nomic-embed-text (dim: 768)
# - mxbai-embed-large (dim: 1024)

# ================================
# OPENAI (Wenn Sie OpenAI bevorzugen)
# ================================
# OPENAI_API_KEY=sk-...
# OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# ================================
# VOYAGE AI (Spezialisiert für Embeddings)
# ================================
# VOYAGE_API_KEY=pa-...
# VOYAGE_EMBEDDING_MODEL=voyage-3

# ================================
# GOOGLE AI (Gemini)
# ================================
# GOOGLE_API_KEY=...
# GOOGLE_EMBEDDING_MODEL=text-embedding-004

# ================================
# AZURE OPENAI
# ================================
# AZURE_OPENAI_API_KEY=...
# AZURE_OPENAI_BASE_URL=https://your-resource.openai.azure.com/
# AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

#### Schritt 2: Ollama installieren und starten (wenn Sie Ollama verwenden)

```bash
# Ollama installieren (einmalig)
# Windows: Download von https://ollama.ai
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# Ollama starten
ollama serve

# Embedding-Modell herunterladen
ollama pull embeddinggemma
```

#### Schritt 3: Python Version überprüfen

```bash
python --version
# Muss 3.12 oder höher sein!
```

Wenn Python < 3.12:
- **Windows:** Download von [python.org](https://www.python.org/downloads/)
- **macOS:** `brew install python@3.12`
- **Linux:** `sudo apt install python3.12`

#### Schritt 4: Memory Status überprüfen

Öffnen Sie die Electron App und gehen Sie zu:
1. **Settings** → **Project Settings**
2. Scrollen Sie zu **"Memory"** Section
3. Überprüfen Sie den Status:
   - ✅ "Enabled" sollte grün sein
   - ✅ "Episodes" sollte die Anzahl gespeicherter Memories zeigen

#### Schritt 5: Memory manuell initialisieren (falls nötig)

```bash
cd apps/backend

# Memory für einen Spec initialisieren
python -c "
from pathlib import Path
from integrations.graphiti.memory import get_graphiti_memory
import asyncio

async def init():
    spec_dir = Path('.auto-claude/specs/001-your-spec-name')
    project_dir = Path.cwd().parent.parent  # Root des Projekts
    
    memory = get_graphiti_memory(spec_dir, project_dir)
    await memory.initialize()
    print('Memory initialized!')

asyncio.run(init())
"
```

#### Schritt 6: Memory testen

```bash
cd apps/backend

# Memory Status abrufen
python -c "
from integrations.graphiti.config import get_graphiti_status
import json
status = get_graphiti_status()
print(json.dumps(status, indent=2))
"
```

**Erwartete Ausgabe (wenn alles funktioniert):**

```json
{
  "enabled": true,
  "available": true,
  "database": "auto_claude_memory_ollama_embeddinggemma_768",
  "db_path": "~/.auto-claude/memories",
  "llm_provider": "openai",
  "embedder_provider": "ollama",
  "reason": "",
  "errors": []
}
```

---

## 2. Kanban Board: Abbrüche bei Planning/Coding

### Problem
Tasks werden beim Planning oder Coding plötzlich abgebrochen und nicht wieder aufgenommen. Das führt zu:
- ⚠️ Verschwendeten Credits
- ⚠️ Unvollständigen Tasks
- ⚠️ Tasks bleiben im `in_progress` Status hängen

### Ursachen

#### 2.1 Task-Status-Konflikte
Das System erkennt nicht, dass ein Prozess noch läuft und markiert den Task fälschlicherweise als "stuck".

#### 2.2 Worktree-Probleme
Wenn ein Task abgebrochen wird, bleibt der Worktree in einem inkonsistenten Zustand.

#### 2.3 Process-Tracking-Fehler
Der AgentManager verliert die Verbindung zum laufenden Prozess.

### Lösungen

#### Lösung 1: Task-Recovery durchführen

Wenn ein Task im `in_progress` Status hängen geblieben ist:

```bash
cd apps/backend

# Task-Status überprüfen
python run.py --spec 001 --status

# Task wiederherstellen
python run.py --spec 001 --recovery

# Wenn das nicht funktioniert, manuell zurücksetzen
python run.py --spec 001 --reset-status
```

#### Lösung 2: Stuck Tasks im UI beheben

1. Öffnen Sie das Kanban Board
2. Finden Sie den hängenden Task
3. Klicken Sie auf den Task
4. Im Task-Detail-Panel:
   - Klicken Sie auf **"Resume"** (wenn verfügbar)
   - ODER: Klicken Sie auf **"Stop"** und dann **"Start"** für einen Neustart

#### Lösung 3: Worktree-Cleanup

```bash
cd apps/backend

# Alle Worktrees auflisten
git worktree list

# Hängende Worktrees entfernen
git worktree remove .worktrees/001-your-spec --force

# ODER: Alle alten Worktrees aufräumen
python -c "
from core.worktree import cleanup_old_worktrees
from pathlib import Path
cleanup_old_worktrees(Path.cwd().parent.parent)
"
```

#### Lösung 4: Process-Tracking reparieren

Das Problem tritt oft auf, wenn die Electron App neu gestartet wird, während ein Task läuft.

**Prävention:**
1. **Nicht die App neu starten** während ein Task `in_progress` ist
2. Warten Sie bis Task zu `human_review` wechselt
3. Dann können Sie die App sicher neu starten

**Wenn es bereits passiert ist:**

```bash
# 1. Alle Python-Prozesse auflisten
# Windows:
tasklist | findstr python

# macOS/Linux:
ps aux | grep python

# 2. Hängende Auto Claude Prozesse beenden
# Windows:
taskkill /F /PID <process-id>

# macOS/Linux:
kill -9 <process-id>

# 3. Task-Status zurücksetzen
cd apps/backend
python run.py --spec 001 --reset-status
```

#### Lösung 5: Credit-Verschwendung minimieren

Um Credits zu sparen bei wiederholten Abbrüchen:

**A) Kleinere Subtasks erstellen**

Bearbeiten Sie `implementation_plan.json`:

```json
{
  "phases": [
    {
      "name": "Phase 1",
      "subtasks": [
        {
          "id": "1.1",
          "description": "Kleinere, fokussierte Aufgabe",
          "estimated_tokens": 5000  // ← Reduzieren Sie diese Zahl
        }
      ]
    }
  ]
}
```

**B) Checkpoints aktivieren**

In `.env`:
```bash
# Speichert Fortschritt häufiger
AUTO_CLAUDE_CHECKPOINT_INTERVAL=300  # Alle 5 Minuten
```

**C) Recovery Mode nutzen**

```bash
# Statt neu zu starten, Recovery verwenden
python run.py --spec 001 --recovery
```

---

## 3. GitHub Integration und "Done" Status

### Ihre Frage
> "Kann Cursor sehen, wenn ich ein Projekt auf 'Done' habe, damit er GitHub Commands machen kann (pushen etc.)?"

### Antwort: Ja, aber mit wichtigen Einschränkungen

#### Wie funktioniert der "Done" Status?

**1. Task-Status-Workflow:**

```
backlog → in_progress → ai_review → human_review → done
```

**2. Ein Task wird auf "done" gesetzt durch:**

✅ **Merge-Workflow (empfohlen):**
```bash
# Backend CLI
cd apps/backend
python run.py --spec 001 --merge

# Oder: Im UI
Kanban Board → Task → "Merge to Main" Button
```

❌ **NICHT durch Drag & Drop:**
Der Code blockiert direkte Änderungen zu "done" wenn ein Worktree existiert:

```typescript
// Aus: apps/frontend/src/main/ipc-handlers/task/execution-handlers.ts:334
if (status === 'done') {
  const hasWorktree = existsSync(worktreePath);
  
  if (hasWorktree) {
    return {
      success: false,
      error: "Cannot set status to 'done' directly. Use merge workflow."
    };
  }
}
```

#### Wie Cursor den "Done" Status erkennt

**1. Über das File-System:**

Cursor kann den Task-Status aus `implementation_plan.json` lesen:

```bash
# Datei-Pfad
.auto-claude/specs/001-your-spec/implementation_plan.json
```

**Struktur:**
```json
{
  "status": "done",
  "planStatus": "completed",
  "updated_at": "2025-12-30T10:30:00Z",
  "phases": [...]
}
```

**2. Cursor kann automatisch darauf reagieren:**

Cursor kann eine Rule erstellen wie:

```markdown
# .cursorrules oder im Chat
When a task in .auto-claude/specs/*/implementation_plan.json 
has status="done", automatically:

1. Read the spec directory name
2. Check if branch auto-claude/{spec-name} exists
3. If yes:
   - git checkout main
   - git merge auto-claude/{spec-name}
   - git push origin main
   - git push origin auto-claude/{spec-name}  (optional)
```

#### GitHub Commands nach "Done" Status

**Manuell (empfohlen):**

```bash
# 1. Merge wurde bereits durchgeführt (Status = done)
# 2. Jetzt zu GitHub pushen

cd /pfad/zu/ihrem/projekt

# Aktuellen Branch überprüfen
git branch

# Zum main Branch wechseln
git checkout main

# Pushen zu GitHub
git push origin main

# Optional: Feature-Branch auch pushen
git push origin auto-claude/001-your-spec-name
```

**Automatisiert mit GitHub Integration:**

Die GitHub Integration ist bereits im Code vorhanden:

```python
# apps/backend/runners/github/gh_client.py

class GHClient:
    async def pr_create(
        self,
        title: str,
        body: str,
        base: str = "main",
        head: str = None,
    ) -> int:
        """Create a pull request."""
        ...
    
    async def pr_merge(
        self,
        pr_number: int,
        merge_method: str = "squash",
    ) -> None:
        """Merge a pull request."""
        ...
```

**Auto-Push aktivieren (experimentell):**

Erstellen Sie ein Script `auto-push-done-tasks.py`:

```python
#!/usr/bin/env python3
"""
Automatisches Pushen von Tasks die auf 'done' sind.
"""

import json
import subprocess
from pathlib import Path

def find_done_tasks(project_dir: Path) -> list:
    """Finde alle Tasks mit status='done'."""
    specs_dir = project_dir / ".auto-claude" / "specs"
    done_tasks = []
    
    for spec_dir in specs_dir.iterdir():
        if not spec_dir.is_dir():
            continue
        
        plan_file = spec_dir / "implementation_plan.json"
        if not plan_file.exists():
            continue
        
        try:
            with open(plan_file) as f:
                plan = json.load(f)
            
            if plan.get("status") == "done":
                done_tasks.append({
                    "spec_id": spec_dir.name,
                    "branch": f"auto-claude/{spec_dir.name}"
                })
        except Exception as e:
            print(f"Error reading {plan_file}: {e}")
    
    return done_tasks

def push_to_github(project_dir: Path, branch: str):
    """Push branch zu GitHub."""
    try:
        # Check if branch exists
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Branch {branch} does not exist")
            return False
        
        # Push to GitHub
        result = subprocess.run(
            ["git", "push", "origin", branch],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully pushed {branch}")
            return True
        else:
            print(f"❌ Failed to push {branch}: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error pushing {branch}: {e}")
        return False

def main():
    project_dir = Path.cwd()
    
    # Finde alle done tasks
    done_tasks = find_done_tasks(project_dir)
    
    if not done_tasks:
        print("No tasks with status='done' found")
        return
    
    print(f"Found {len(done_tasks)} done tasks")
    
    # Push main branch
    print("\n📤 Pushing main branch...")
    push_to_github(project_dir, "main")
    
    # Optional: Push feature branches
    for task in done_tasks:
        print(f"\n📤 Pushing {task['branch']}...")
        push_to_github(project_dir, task["branch"])

if __name__ == "__main__":
    main()
```

**Verwendung:**

```bash
# Script ausführbar machen
chmod +x auto-push-done-tasks.py

# Ausführen
python auto-push-done-tasks.py
```

#### GitHub Actions Integration

Erstellen Sie `.github/workflows/auto-push-done.yml`:

```yaml
name: Auto Push Done Tasks

on:
  # Manuell auslösen
  workflow_dispatch:
  
  # Oder: Automatisch alle 30 Minuten
  schedule:
    - cron: '*/30 * * * *'

jobs:
  check-and-push:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Alle Branches holen
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Find and push done tasks
        run: python auto-push-done-tasks.py
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

#### Cursor Integration

**Option 1: Cursor Rules**

Erstellen Sie `.cursorrules`:

```markdown
# Auto Claude Done Task Handler

When you detect a task has been completed (status="done" in implementation_plan.json):

1. Inform the user
2. Ask if they want to push to GitHub
3. If yes:
   - git checkout main
   - git push origin main
   - git push origin auto-claude/{spec-name}

Example:
"Task 001-authentication is now complete (status=done). 
Would you like me to push the changes to GitHub?"
```

**Option 2: Cursor Composer mit MCP**

Cursor kann mit dem GitHub MCP Server direkt interagieren:

```bash
# In Cursor Chat:
"Check all tasks in .auto-claude/specs/ and push 
any completed ones to GitHub"
```

---

## 🎯 Zusammenfassung

### Memory-Problem
1. ✅ `.env` Datei erstellen in `apps/backend/.env`
2. ✅ `GRAPHITI_ENABLED=true` setzen
3. ✅ Embedder konfigurieren (Ollama empfohlen)
4. ✅ Python 3.12+ verwenden
5. ✅ Memory initialisieren

### Kanban Board Abbrüche
1. ✅ Recovery-Workflow nutzen: `python run.py --spec 001 --recovery`
2. ✅ Worktrees aufräumen wenn nötig
3. ✅ App nicht neu starten während Task läuft
4. ✅ Kleinere Subtasks erstellen für weniger Credit-Verschwendung

### GitHub "Done" Status
1. ✅ Tasks werden auf "done" gesetzt durch Merge-Workflow
2. ✅ Cursor kann `implementation_plan.json` lesen
3. ✅ Automatisches Pushen möglich via:
   - Python Script
   - GitHub Actions
   - Cursor Rules/MCP
4. ✅ Empfehlung: Manuelles Pushen nach Review für Sicherheit

---

## 📞 Weitere Hilfe

Wenn die Probleme weiterhin bestehen:

1. **Logs überprüfen:**
   ```bash
   # Backend Logs
   cat apps/backend/logs/auto-claude.log
   
   # Memory Logs
   cat ~/.auto-claude/memories/debug.log
   ```

2. **Debug-Modus aktivieren:**
   ```bash
   # In .env
   DEBUG=true
   AUTO_CLAUDE_DEBUG=true
   ```

3. **System-Info sammeln:**
   ```bash
   python --version
   node --version
   git --version
   ollama --version  # wenn verwendet
   ```

4. **GitHub Issue erstellen:**
   - Repository: `https://github.com/your-repo/auto-claude`
   - Template: Bug Report
   - Logs anhängen (ohne sensible Daten!)

---

**Version:** 1.0  
**Letzte Aktualisierung:** 30.12.2025  
**Sprache:** Deutsch 🇩🇪

