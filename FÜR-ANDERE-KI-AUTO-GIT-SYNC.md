# Auto Git Sync - Anleitung für andere Cursor KIs

## 🎯 WICHTIG: Das ist speziell für Auto Claude!

**Diese Anleitung erklärt, wie Auto Git Sync für Auto Claude funktioniert.**
**Wenn du in einem ANDEREN Projekt arbeitest (z.B. craft-connect-buddy), musst du es anpassen!**

---

## 📚 Was ist Auto Claude?

**Auto Claude** ist ein Multi-Agent-System, das Software automatisch baut:

1. **User gibt Task-Beschreibung** → "Erstelle Login-Feature"
2. **Auto Claude erstellt Spec** → `.auto-claude/specs/001-login/spec.md`
3. **Auto Claude implementiert** → Code wird geschrieben
4. **Auto Claude setzt Status** → `implementation_plan.json` → `status: "done"`
5. **Auto Git Sync erkennt das** → Committet automatisch

### Projekt-Struktur:

```
auto-claude/
├── apps/
│   ├── backend/              # Python Backend
│   │   ├── auto_git_sync.py  # Auto Git Sync Script
│   │   └── run.py            # Haupt-Orchestrator
│   └── frontend/             # Electron Desktop App
├── .auto-claude/              # Auto Claude Daten (gitignored)
│   └── specs/                 # Alle Tasks/Specs
│       ├── 001-login/         # Ein Task
│       │   ├── spec.md
│       │   └── implementation_plan.json  # ← HIER steht der Status!
│       └── 002-auth/
│           └── ...
└── Create-GitSync-Shortcut.ps1
```

---

## 🔍 Wie funktioniert "Done" Erkennung?

### 1. Task-Struktur in Auto Claude

Jeder Task hat ein **`implementation_plan.json`** File:

```json
{
  "feature": "User Authentication System",
  "status": "done",              // ← HIER! Das ist der "Done" Status
  "planStatus": "completed",     // ← Oder hier
  "phases": [
    {
      "subtasks": [
        {
          "id": "subtask-1",
          "status": "completed",  // ← Alle Subtasks müssen "completed" sein
          "description": "..."
        }
      ]
    }
  ],
  "qa_signoff": {
    "status": "approved"          // ← Optional: QA muss approved sein
  }
}
```

### 2. Status-Werte in Auto Claude

**Mögliche `status` Werte:**
- `"backlog"` - Noch nicht gestartet
- `"in_progress"` - Wird gerade bearbeitet
- `"ai_review"` - QA läuft
- `"human_review"` - Wartet auf User-Review
- `"done"` - ✅ FERTIG! (Das ist was wir suchen!)

**Mögliche `planStatus` Werte:**
- `"pending"` - Noch nicht gestartet
- `"in_progress"` - Wird bearbeitet
- `"review"` - In Review
- `"completed"` - ✅ FERTIG!

### 3. Wie Auto Git Sync "Done" erkennt

**Code aus `auto_git_sync.py` (Zeile 81-150):**

```python
def find_done_tasks(self, spec_filter: Optional[str] = None) -> list[dict]:
    """Findet alle Tasks mit Status 'done' die noch nicht verarbeitet wurden."""
    done_tasks = []
    
    # 1. Gehe durch alle Specs
    for spec_dir in self.specs_dir.iterdir():
        plan_file = spec_dir / "implementation_plan.json"
        
        # 2. Lade implementation_plan.json
        with open(plan_file, 'r', encoding='utf-8') as f:
            plan = json.load(f)
        
        status = plan.get("status", "")
        plan_status = plan.get("planStatus", "")
        
        # 3. Prüfe ob "done"
        is_done = False
        
        if status == "done":
            is_done = True
        elif status == "human_review" and plan_status == "review":
            # Prüfe ob alle Subtasks completed sind
            all_completed = True
            for phase in plan.get("phases", []):
                for subtask in phase.get("subtasks", []):
                    if subtask.get("status") != "completed":
                        all_completed = False
                        break
                if not all_completed:
                    break
            
            if all_completed:
                is_done = True
        
        if is_done:
            done_tasks.append({
                "spec_id": spec_dir.name,
                "spec_dir": spec_dir,
                "plan": plan,
                "feature": plan.get("feature", "Unknown Feature")
            })
    
    return done_tasks
```

**Zusammenfassung:**
- ✅ Task ist "done" wenn `status == "done"`
- ✅ ODER wenn `status == "human_review"` + alle Subtasks `completed`
- ✅ Prüft alle 5 Sekunden (Watch Mode)
- ✅ Verhindert Duplikate via State-File

---

## 🔄 Wie Auto Git Sync funktioniert

### Workflow:

```
1. Auto Claude setzt Status auf "done"
   → implementation_plan.json wird aktualisiert
         ↓
2. Auto Git Sync prüft alle 5 Sekunden
   → find_done_tasks() findet neuen "done" Task
         ↓
3. Auto Git Sync erstellt Commit
   → git add .
   → git commit -m "feat(auto-claude): [feature]"
         ↓
4. Optional: Push zu GitHub
   → git push origin [branch]
         ↓
5. Optional: PR erstellen
   → gh pr create --title "..." --body "..."
         ↓
6. State speichern
   → .auto-claude/git_sync_state.json
   → Verhindert doppelte Verarbeitung
```

### Datei-Struktur:

```
.auto-claude/
├── specs/
│   ├── 001-login/
│   │   └── implementation_plan.json  # ← Wird überwacht
│   └── 002-auth/
│       └── implementation_plan.json
└── git_sync_state.json              # ← State-Tracking
    {
      "processed_tasks": ["001-login"],
      "last_updated": "2025-12-30T15:30:00"
    }
```

---

## 🛠️ Für andere Projekte adaptieren

### Wenn du es für craft-connect-buddy (oder anderes Projekt) nutzen willst:

**Du musst anpassen:**

1. **Task-Struktur erkennen**
   - Wo werden Tasks gespeichert?
   - Wie sieht die Status-Datei aus?
   - Welche Status-Werte gibt es?

2. **Datei-Pfade anpassen**
   ```python
   # Auto Claude:
   self.specs_dir = project_dir / ".auto-claude" / "specs"
   plan_file = spec_dir / "implementation_plan.json"
   
   # Für craft-connect-buddy (Beispiel):
   self.tasks_dir = project_dir / ".worktrees"  # Oder wo auch immer
   status_file = task_dir / "status.json"       # Oder wie auch immer
   ```

3. **Status-Erkennung anpassen**
   ```python
   # Auto Claude:
   if plan.get("status") == "done":
       is_done = True
   
   # Für craft-connect-buddy (Beispiel):
   if status_file.get("state") == "completed":
       is_done = True
   ```

4. **Watch-Mechanismus anpassen**
   - Auto Claude: Polling alle 5 Sekunden
   - Alternative: File-Watcher (watchdog)
   - Alternative: GitHub Webhooks
   - Alternative: Database-Queries

---

## 📝 Beispiel: Adaption für craft-connect-buddy

### Option 1: Datei-basiert (wie Auto Claude)

```python
# auto_git_sync_craft.py

import json
import subprocess
from pathlib import Path
import time

class CraftConnectGitSync:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        # ANPASSEN: Wo sind deine Tasks?
        self.tasks_dir = project_dir / ".worktrees"  # Oder wo auch immer
        self.processed_tasks = set()
    
    def find_done_tasks(self):
        """Finde done Tasks - ANPASSEN für deine Struktur!"""
        done_tasks = []
        
        for task_dir in self.tasks_dir.iterdir():
            # ANPASSEN: Wie sieht deine Status-Datei aus?
            status_file = task_dir / "status.json"  # Oder "task.json" oder...
            
            if not status_file.exists():
                continue
            
            with open(status_file) as f:
                status = json.load(f)
            
            # ANPASSEN: Wie erkennt man "done"?
            if status.get("state") == "completed":  # Oder "done" oder...
                done_tasks.append({
                    "task_id": task_dir.name,
                    "task_dir": task_dir,
                    "status": status
                })
        
        return done_tasks
    
    def create_commit(self, task):
        """Commit erstellen - ANPASSEN für deine Commit-Messages!"""
        task_name = task["task_id"]
        
        # ANPASSEN: Deine Commit-Message-Format
        message = f"feat: complete {task_name} (auto-synced)"
        
        subprocess.run(["git", "add", "."], cwd=self.project_dir)
        subprocess.run(["git", "commit", "-m", message], cwd=self.project_dir)
    
    def watch_mode(self):
        """Watch Mode - ANPASSEN für deine Polling-Intervalle!"""
        while True:
            done_tasks = self.find_done_tasks()
            
            for task in done_tasks:
                if task["task_id"] not in self.processed_tasks:
                    self.create_commit(task)
                    self.processed_tasks.add(task["task_id"])
            
            time.sleep(5)  # ANPASSEN: Dein Polling-Interval
```

### Option 2: GitHub API-basiert

```python
# auto_git_sync_github.py

import requests
import subprocess
from pathlib import Path

class GitHubGitSync:
    def __init__(self, repo: str, token: str):
        self.repo = repo  # "user/repo"
        self.token = token
        self.api_base = f"https://api.github.com/repos/{repo}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def find_done_issues(self):
        """Finde done Issues via GitHub API"""
        # ANPASSEN: Welche Labels/States bedeuten "done"?
        response = requests.get(
            f"{self.api_base}/issues",
            headers=self.headers,
            params={
                "state": "closed",  # Oder "open" mit Label "done"
                "labels": "done"    # Oder was auch immer
            }
        )
        
        return response.json()
    
    def create_commit_from_issue(self, issue):
        """Commit basierend auf Issue"""
        # ANPASSEN: Wie erstellst du Commits aus Issues?
        message = f"fix: {issue['title']} (closes #{issue['number']})"
        
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", message])
```

---

## ❓ Fragen die du beantworten musst (für andere Projekte)

### 1. Wo werden Tasks gespeichert?

**Auto Claude:**
```
.auto-claude/specs/001-task/implementation_plan.json
```

**Dein Projekt:**
- [ ] Lokale Dateien? → Welcher Pfad?
- [ ] GitHub Issues? → Welches Repo?
- [ ] Database? → Welche Tabelle?
- [ ] Anderes System? → Welches?

### 2. Wie sieht die Status-Datei aus?

**Auto Claude:**
```json
{
  "status": "done",
  "planStatus": "completed"
}
```

**Dein Projekt:**
- [ ] JSON? → Welche Keys?
- [ ] YAML? → Welche Struktur?
- [ ] Database? → Welche Felder?
- [ ] API Response? → Welches Format?

### 3. Welche Status-Werte bedeuten "done"?

**Auto Claude:**
- `status == "done"` ODER
- `status == "human_review"` + alle Subtasks `completed`

**Dein Projekt:**
- [ ] `"completed"`?
- [ ] `"done"`?
- [ ] `"closed"`?
- [ ] Anderes?

### 4. Wie soll überwacht werden?

**Auto Claude:**
- Polling alle 5 Sekunden
- Prüft `implementation_plan.json` Files

**Dein Projekt:**
- [ ] File-Watcher (watchdog)?
- [ ] Polling (wie Auto Claude)?
- [ ] GitHub Webhooks?
- [ ] Database-Queries?
- [ ] Anderes?

### 5. Wie automatisch soll es sein?

**Auto Claude:**
- ✅ Voll automatisch (mit `--auto-push`)
- ⚠️ Mit Bestätigung (ohne `--auto-push`)

**Dein Projekt:**
- [ ] Voll automatisch?
- [ ] Mit Bestätigung?
- [ ] Nur Benachrichtigung?

---

## 🎯 Zusammenfassung für andere KIs

### Wenn du Auto Git Sync für ein ANDERES Projekt nutzen willst:

1. **Verstehe die Auto Claude Struktur** (siehe oben)
2. **Identifiziere deine Task-Struktur** (Wo? Wie?)
3. **Passe die Pfade an** (`.auto-claude/specs/` → dein Pfad)
4. **Passe die Status-Erkennung an** (`status == "done"` → deine Logik)
5. **Passe den Watch-Mechanismus an** (Polling → deine Methode)
6. **Teste gründlich** (Starte ohne `--auto-push`!)

### WICHTIG:

❌ **Kopiere NICHT blind!**  
✅ **Verstehe die Logik und adaptiere sie!**

❌ **Nutze NICHT Auto Claude Pfade in anderen Projekten!**  
✅ **Passe alle Pfade an dein Projekt an!**

❌ **Starte NICHT mit `--auto-push`!**  
✅ **Teste erst ohne Push, dann aktivieren!**

---

## 📚 Referenzen

### Auto Claude Dokumentation:

- **Haupt-Dokumentation:** `CLAUDE.md`
- **Auto Git Sync Anleitung:** `AUTO-GIT-SYNC-ANLEITUNG.md`
- **Schnellstart:** `SCHNELLSTART-GIT-SYNC.md`
- **Cursor Integration:** `.cursor/rules/auto-git-sync.mdc`

### Code-Referenzen:

- **Haupt-Script:** `apps/backend/auto_git_sync.py`
- **Implementation Plan:** `apps/backend/implementation_plan/plan.py`
- **Status-Management:** `apps/backend/ui/status.py`

---

## 💡 Tipps für die Adaption

### 1. Starte klein

```python
# Erstmal nur Erkennung testen
def test_done_detection():
    done_tasks = find_done_tasks()
    print(f"Found {len(done_tasks)} done tasks")
    for task in done_tasks:
        print(f"  - {task['task_id']}")
```

### 2. Teste ohne Auto-Push

```bash
# Erstmal nur committen (sicher)
python auto_git_sync.py --watch

# Dann mit Push (wenn sicher)
python auto_git_sync.py --watch --auto-push
```

### 3. Nutze State-File

```python
# Verhindert doppelte Verarbeitung
processed_tasks = set()  # In Memory
sync_state_file = Path(".git_sync_state.json")  # Persistent
```

### 4. Logge alles

```python
print(f"[INFO] Found done task: {task_id}")
print(f"[INFO] Creating commit...")
print(f"[OK] Commit created: {commit_hash}")
```

---

**Version:** 1.0  
**Erstellt:** 30.12.2025  
**Für:** Andere Cursor KIs die Auto Git Sync adaptieren wollen  
**Zweck:** Klare Erklärung wie Auto Git Sync für Auto Claude funktioniert

