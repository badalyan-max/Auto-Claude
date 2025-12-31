# Git-Änderungen-Erkennung für Auto Claude

## 🎯 Problem gelöst

**Vorher:** Wenn Du externe Änderungen (z.B. über Lovable oder direkte Git-Commits) machst, berücksichtigt Auto Claude diese nicht bei neuen Roadmaps/Ideationen/Insights.

**Jetzt:** Auto Claude erkennt automatisch Git-Änderungen seit dem letzten Project-Index-Refresh und stellt diese als Context für AI-Agenten bereit.

---

## ✨ Features

### 1. Automatische Git-Änderungserkennung

Das neue `GitChangeDetector`-System erkennt:

- **Commits seit letztem Index-Refresh**
- **Geänderte Dateien** (mit Typ-Analyse)
- **Code vs. Dokumentation** (nur Code-Änderungen triggern Index-Refresh)
- **Lesbare Zusammenfassung** für AI-Agenten

### 2. Integration in Project-Index

Der `project_index_manager` prüft jetzt automatisch:

```python
from project_index_manager import should_refresh_index

# Prüft auch Git-Änderungen!
if should_refresh_index(project_dir):
    refresh_project_index(project_dir)
```

**Refresh-Trigger:**
- Index existiert nicht
- Index älter als 1 Stunde
- Trigger-Dateien geändert (package.json, etc.)
- **NEU:** Code-Dateien in Git geändert (.py, .ts, .tsx, .js, etc.)

### 3. Context für AI-Agenten

Roadmap/Ideation/Insights Agents erhalten jetzt automatisch Git-Context:

```
## 📝 Recent Git Changes (External Modifications)

📝 3 neue Commit(s) seit letztem Project-Index-Refresh
📁 8 Datei(en) geändert

Neueste Commits:
  • a1b2c3d4: Add authentication feature
  • e5f6g7h8: Update frontend components
  • i9j0k1l2: Fix responsive layout

Geänderte Dateitypen:
  • .tsx: 4 Datei(en)
  • .ts: 3 Datei(en)
  • .md: 1 Datei(en)

IMPORTANT: These external changes should be considered when
generating roadmaps, insights, or ideations.
```

---

## 🚀 Verwendung

### Diagnose: Git-Änderungen prüfen

```bash
cd apps/backend
python diagnose.py --check-git-changes
```

**Output:**
```
6️⃣  Git-Änderungen seit letztem Index
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠ 3 neue Commit(s), 8 Datei(en) geändert

📝 3 neue Commit(s) seit letztem Project-Index-Refresh
📁 8 Datei(en) geändert

Neueste Commits:
  • a1b2c3d4: Add authentication feature
  • e5f6g7h8: Update frontend components

⚠️  Index-Refresh empfohlen für Code-Änderungen!
Tipp: Der Index wird automatisch beim nächsten Roadmap/Ideation-Run aktualisiert
```

### Automatische Integration

**Roadmap:**
```bash
python apps/backend/runners/roadmap_runner.py --project .
# Git-Changes werden automatisch erkannt und als Context bereitgestellt
```

**Ideation:**
```bash
python apps/backend/runners/ideation_runner.py --project .
# Context enthält nun auch Git-Änderungen!
```

**Insights:**
```bash
python apps/backend/runners/insights_runner.py --project .
# Insights berücksichtigen externe Änderungen
```

### Programmatische Verwendung

```python
from git_change_detector import (
    GitChangeDetector,
    get_git_changes,
    get_git_context_for_agent,
    should_refresh_for_git_changes,
)
from pathlib import Path

project_dir = Path.cwd()

# 1. Änderungen abrufen
detector = GitChangeDetector(project_dir)
changes = detector.get_changes_since_index()

print(f"Has changes: {changes.has_changes}")
print(f"Commits: {changes.commits_since_index}")
print(f"Files: {len(changes.changed_files)}")

# 2. Context für AI-Agent
context = detector.get_context_for_agent()
# → Formatierter String für Agent-Prompts

# 3. Prüfen ob Refresh nötig
if detector.should_refresh_index_for_changes():
    print("Index-Refresh empfohlen!")

# Convenience-Funktionen
changes = get_git_changes(project_dir)
context = get_git_context_for_agent(project_dir)
should_refresh = should_refresh_for_git_changes(project_dir)
```

---

## 🔧 Technische Details

### GitChangeSummary Dataclass

```python
@dataclass
class GitChangeSummary:
    has_changes: bool              # Ob Änderungen vorliegen
    commits_since_index: int       # Anzahl neuer Commits
    changed_files: list[str]       # Liste geänderter Dateien
    recent_commits: list[dict]     # Neueste Commits (max. 10)
    summary: str                   # Lesbare Zusammenfassung
```

### Code-Dateien (triggern Refresh)

```python
CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".vue", ".svelte", ".go", ".rs", ".rb",
    ".php", ".java", ".cs", ".cpp", ".c"
}
```

Nur Änderungen an diesen Dateitypen triggern einen Index-Refresh.

**Beispiel:** README.md-Änderungen alleine triggern **keinen** Refresh.

### Git-Kommandos

```bash
# Commits seit Index-Timestamp
git log --since="2024-01-01 12:00:00" --pretty=format:"%H|%an|%ad|%s"

# Geänderte Dateien
git log --since="2024-01-01 12:00:00" --name-only --pretty=format:
```

---

## 📊 Workflow-Integration

### Vorher (Problem)

```
1. User: Ändert Code auf Lovable → Git Push
2. Auto Claude: Startet neue Roadmap
3. Agent: Sieht NUR:
   - Alte project_index.json
   - Eigene Memories
   ❌ Externe Änderungen NICHT berücksichtigt!
```

### Jetzt (Lösung)

```
1. User: Ändert Code auf Lovable → Git Push
2. Auto Claude: Startet neue Roadmap
3. System: Prüft Git-Änderungen
4. System: Refreshed Index wenn nötig
5. Agent: Sieht:
   ✅ Aktuelle project_index.json
   ✅ Eigene Memories
   ✅ Git-Änderungen als Context
   → VOLLSTÄNDIGER ÜBERBLICK!
```

---

## 🧪 Tests

```bash
# Tests ausführen
cd apps/backend
pytest test_git_change_detector.py -v
```

**Test-Coverage:**
- ✅ Keine Änderungen
- ✅ Mit neuen Commits
- ✅ Code-Änderungen → Refresh empfohlen
- ✅ Nur README-Änderungen → Kein Refresh
- ✅ Context-String für AI-Agenten
- ✅ Kein Git-Repo (Graceful Degradation)
- ✅ Convenience-Funktionen

---

## 🎨 Beispiel-Output

### Diagnose mit Git-Änderungen

```
6️⃣  Git-Änderungen seit letztem Index
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠ 5 neue Commit(s), 12 Datei(en) geändert

📝 5 neue Commit(s) seit letztem Project-Index-Refresh
📁 12 Datei(en) geändert

Neueste Commits:
  • abc12345: feat: Add user authentication
  • def67890: fix: Responsive layout issues
  • ghi24680: refactor: Clean up components
  • jkl13579: docs: Update README
  • mno86420: style: Format code

Geänderte Dateitypen:
  • .tsx: 6 Datei(en)
  • .ts: 4 Datei(en)
  • .md: 2 Datei(en)

⚠️  Index-Refresh empfohlen für Code-Änderungen!
Tipp: Der Index wird automatisch beim nächsten Roadmap/Ideation-Run aktualisiert
```

### Agent-Context

```markdown
## 📝 Recent Git Changes (External Modifications)

📝 3 neue Commit(s) seit letztem Project-Index-Refresh
📁 8 Datei(en) geändert

### Recent Commits:
```
abc12345 - John Doe - feat: Add authentication
def67890 - Jane Smith - fix: Responsive layout
ghi24680 - John Doe - refactor: Components
```

### Changed Files (8 total):
```
  - apps/frontend/src/components/Auth.tsx
  - apps/frontend/src/components/Login.tsx
  - apps/frontend/src/hooks/useAuth.ts
  - apps/backend/auth/oauth.py
  - apps/backend/auth/session.py
  - README.md
```

**IMPORTANT**: These external changes should be considered when
generating roadmaps, insights, or ideations. They represent real
code modifications that may not be reflected in Auto Claude's memory yet.
```

---

## 🔍 Fehlerbehebung

### Git nicht gefunden

**Problem:** `Git not found` Fehler

**Lösung:**
```bash
# Windows: Git installieren
winget install Git.Git

# Oder von https://git-scm.com/download/win
```

### Keine Änderungen erkannt

**Problem:** Git-Änderungen vorhanden, aber nicht erkannt

**Diagnose:**
```bash
# Prüfe ob Git-History vorhanden
git log --oneline -n 5

# Prüfe Index-Timestamp
ls -la .auto-claude/project_index.json

# Manuelle Diagnose
python -c "from git_change_detector import get_git_changes; from pathlib import Path; print(get_git_changes(Path.cwd()))"
```

### Index wird nicht aktualisiert

**Problem:** Index wird nicht automatisch aktualisiert

**Lösung:**
```bash
# Manueller Refresh
cd apps/backend
python -c "from project_index_manager import refresh_project_index; from pathlib import Path; refresh_project_index(Path('.'))"

# Oder mit force-flag
python runners/roadmap_runner.py --project . --refresh
```

---

## 📚 Dateien

**Neue Dateien:**
- `apps/backend/git_change_detector.py` - Haupt-Implementierung
- `apps/backend/test_git_change_detector.py` - Tests
- `GIT-ÄNDERUNGEN-ERKENNUNG.md` - Diese Dokumentation

**Geänderte Dateien:**
- `apps/backend/project_index_manager.py` - Git-Check in `should_refresh_index()`
- `apps/backend/runners/roadmap/phases.py` - Git-Context in Discovery-Phase
- `apps/backend/runners/insights_runner.py` - Git-Context in `load_project_context()`
- `apps/backend/ideation/analyzer.py` - Git-Context in `gather_context()`
- `apps/backend/diagnose.py` - Neuer Check `--check-git-changes`

---

## 🎯 Best Practices

### Wann wird der Index aktualisiert?

**Automatisch:**
- Bei jedem Roadmap-Run (wenn Git-Änderungen)
- Bei jedem Ideation-Run (wenn Git-Änderungen)
- Bei jedem Insights-Run (wenn Git-Änderungen)

**Manuell:**
```bash
# Force-Refresh
python runners/roadmap_runner.py --project . --refresh
```

### Wann solltest Du prüfen?

**Nach externen Änderungen:**
```bash
# Nach Lovable-Sync
git pull
python apps/backend/diagnose.py --check-git-changes

# Nach direkten Commits
git commit -m "..."
python apps/backend/diagnose.py --check-git-changes
```

### Performance

- **Schnell:** Git-Kommandos dauern <1 Sekunde
- **Lazy:** Nur bei Bedarf ausgeführt (nicht bei jedem Tool-Call)
- **Graceful:** Funktioniert auch ohne Git (degradiert zu "keine Änderungen")

---

## 🚀 Nächste Schritte

1. **Nach Lovable-Sync:**
   ```bash
   git pull
   python apps/backend/diagnose.py --check-git-changes
   ```

2. **Vor neuer Roadmap:**
   ```bash
   # Prüft und refreshed automatisch!
   python apps/backend/runners/roadmap_runner.py --project .
   ```

3. **Vor neuen Insights:**
   ```bash
   # Context enthält Git-Änderungen!
   python apps/backend/runners/insights_runner.py --project .
   ```

---

**Version:** 1.0  
**Erstellt:** 31.12.2024  
**Problem:** Externe Git-Änderungen werden nicht berücksichtigt  
**Lösung:** Automatische Git-Änderungserkennung mit Agent-Context  

**WICHTIG:** Diese Funktion läuft AUTOMATISCH! Du musst nichts tun - die AI-Agenten erhalten automatisch den vollständigen Context inkl. aller externen Änderungen.
