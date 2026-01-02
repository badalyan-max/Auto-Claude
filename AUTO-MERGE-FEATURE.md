# Auto-Merge Feature 🚀

## Übersicht

Das **Auto-Merge Feature** automatisiert den Merge-Prozess von fertigen Tasks in den `main` Branch mit AI-Validierung und automatischem GitHub-Push.

## 🎯 Was macht es?

Wenn du einen Task im Kanban Board auf **"Done"** ziehst, passiert Folgendes automatisch:

1. ✅ **Commit-Prüfung**: Alle Commits des Tasks werden validiert
2. 🤖 **AI-Validierung**: Claude prüft Vollständigkeit und Qualität
3. 🔀 **Auto-Merge**: Task wird in `main` Branch gemerged
4. 📤 **GitHub-Push**: Änderungen werden zu GitHub gepusht

## 📋 Workflow

```
Task zu "Done" ziehen
       ↓
   Commit-Prüfung
       ↓
  AI-Validierung (optional)
       ↓
  Merge zu main (--no-ff)
       ↓
   Push zu GitHub
       ↓
  ✅ Task fertig!
```

## 🛡️ Sicherheit

### AI-Validierung prüft:

- ✅ Mindestens 1 Commit vorhanden
- ✅ Commit-Messages aussagekräftig (min. 10 Zeichen)
- ✅ Keine WIP/Temp-Commits
- ✅ Dateien wurden tatsächlich geändert
- ✅ Commits beziehen sich auf Task-Beschreibung
- ✅ Quality-Score >= Minimum (default 70/100)

### Fehler-Szenarien:

| Szenario | Verhalten |
|----------|-----------|
| Keine Commits | ❌ Merge wird abgebrochen |
| Quality-Score zu niedrig | ❌ Merge wird abgebrochen, Issues werden angezeigt |
| WIP-Commits | ⚠️ Quality-Score reduziert |
| Merge-Konflikt | ❌ Merge wird abgebrochen, manueller Fix nötig |
| Push fehlgeschlagen | ✅ Merge bleibt, nur Push-Warnung |

## ⚙️ Konfiguration

### Standard-Einstellungen

```typescript
{
  enabled: true,                    // Auto-Merge aktiv
  requireAIValidation: true,        // AI-Validierung erforderlich
  minQualityScore: 70,              // Minimum Quality-Score (0-100)
  autoPush: true,                   // Automatischer Push zu GitHub
  targetBranch: "main"              // Ziel-Branch für Merge
}
```

### Einstellungen ändern

Aktuell sind die Einstellungen hardcoded. In Zukunft:

1. Settings → Project Settings → Auto-Merge
2. Einstellungen nach Bedarf anpassen
3. Speichern

## 🎨 UI-Elemente

### Progress-Anzeige

Unter jedem "Done"-Task wird der Auto-Merge-Status angezeigt:

- 🔵 **In Progress**: Spinner + Progress Bar (0-100%)
- ✅ **Success**: Grünes Häkchen + Details (Commits, Push-Status)
- ❌ **Failed**: Rotes X + Fehler + AI-Issues

### Statusmeldungen

```
✅ Auto-merge complete!
   ├─ Merged 3 commit(s) to main
   ├─ Pushed to GitHub
   └─ AI Validation: 85/100 Quality Score

❌ Auto-merge failed
   └─ Error: Quality score 45 below minimum 70
       └─ Issues:
           • Commit message too short: "fix"
           • WIP commit found: "wip: testing"
```

## 🔧 Technische Details

### Komponenten

| Datei | Zweck |
|-------|-------|
| `auto-merge-service.ts` | Kern-Logik für Auto-Merge |
| `AutoMergeProgress.tsx` | UI-Komponente für Progress-Anzeige |
| `execution-handlers.ts` | Integration in Task-Status-Update |
| `ipc.ts` | IPC-Channels für Events |

### IPC-Events

- `TASK_AUTO_MERGE_PROGRESS`: Progress-Updates (0-100%)
- `TASK_AUTO_MERGE_COMPLETE`: Merge erfolgreich
- `TASK_AUTO_MERGE_FAILED`: Merge fehlgeschlagen

### Git-Befehle

```bash
# 1. Commits holen
git log main..auto-claude/TASK-ID --format=%H

# 2. Commit-Details
git show HASH --stat
git diff-tree --no-commit-id --name-only -r HASH

# 3. Merge (--no-ff für Merge-Commit)
git checkout main
git merge --no-ff -m "Merge task: TITLE" auto-claude/TASK-ID

# 4. Push
git push origin main
```

## 📊 AI-Validierung Details

### Quality-Score-Berechnung

Startwert: **100 Punkte**

Abzüge:
- -50: Keine Commits
- -10: Zu kurze Commit-Message
- -5: WIP/Temp-Commit
- -30: Keine Dateiänderungen
- -15: Commits passen nicht zur Task-Beschreibung

Mindest-Score: **0**, Maximal-Score: **100**

### Keyword-Matching

Task-Beschreibung → Extrahiere Keywords (min. 4 Zeichen, Top 10)
Commits-Text → Suche nach Keywords
Match-Rate → Beeinflusst Quality-Score

## 🚀 Beispiel-Workflow

### Erfolgreicher Auto-Merge

```
1. Task "Add dark mode toggle" → "Done" ziehen

2. Auto-Merge startet:
   ├─ Checking task commits... (10%)
   ├─ Analyzing commits... (30%)
   │   └─ Found 3 commits
   ├─ Validating with AI... (50%)
   │   └─ Quality: 85/100 ✓
   ├─ Merging to main... (70%)
   │   └─ Merge commit: a3f8b2d
   └─ Pushing to GitHub... (90%)
       └─ Success! (100%)

3. Ergebnis:
   ✅ Merged 3 commit(s) to main
   ✅ Pushed to GitHub
   ℹ️  AI Validation: 85/100 Quality Score
```

### Fehlgeschlagener Auto-Merge

```
1. Task "Quick fix" → "Done" ziehen

2. Auto-Merge startet:
   ├─ Checking task commits... (10%)
   ├─ Analyzing commits... (30%)
   │   └─ Found 2 commits
   └─ Validating with AI... (50%)
       └─ Quality: 45/100 ✗

3. Ergebnis:
   ❌ AI validation failed: Quality score 45 below minimum 70

   Issues:
   • Commit message too short: "fix"
   • WIP commit found: "wip: testing"

   → Task bleibt auf "Done", kein Merge
   → Commits überarbeiten und erneut versuchen
```

## 🛠️ Entwickler-Notizen

### Auto-Merge deaktivieren (während Entwicklung)

```typescript
// apps/frontend/src/main/auto-merge-service.ts

const DEFAULT_CONFIG: AutoMergeConfig = {
  enabled: false, // ← Hier auf false setzen
  // ...
};
```

### Debug-Logs

```bash
# Im Electron DevTools Console:
[AutoMerge] Starting auto-merge for task: TASK-ID
[AutoMerge] Found 3 commits
[AutoMerge] Merge successful: a3f8b2d
```

### Testing

1. Erstelle Test-Task
2. Mache 2-3 Commits im Task-Branch
3. Ziehe Task auf "Done"
4. Beobachte Auto-Merge-Progress
5. Prüfe `git log main` für Merge-Commit

## 📚 Weiterführende Links

- [Git Merge Strategies](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging)
- [Worktree Workflow](./WORKTREE-WORKFLOW.md)
- [Task States](./TASK-STATES.md)

## ❓ FAQ

### **Kann ich Auto-Merge deaktivieren?**
Ja, in `auto-merge-service.ts` → `DEFAULT_CONFIG.enabled = false`

### **Was passiert bei Merge-Konflikten?**
Auto-Merge wird abgebrochen, manueller Fix nötig. Fehlermeldung wird angezeigt.

### **Kann ich einen anderen Branch als `main` verwenden?**
Ja, in `DEFAULT_CONFIG.targetBranch = "develop"` ändern.

### **Was passiert, wenn Push fehlschlägt?**
Merge bleibt bestehen, nur Push-Warnung. Manuell `git push` ausführen.

### **Wie ändere ich den Quality-Score-Threshold?**
In `DEFAULT_CONFIG.minQualityScore = 50` ändern (0-100).

### **Werden alte Tasks auch auto-merged?**
Nein, nur Tasks die **NEU** auf "Done" gezogen werden triggern Auto-Merge.

## 🎯 Roadmap

### Geplante Features:

- [ ] UI-Settings für Auto-Merge-Konfiguration
- [ ] Echte Claude-API Integration für AI-Validierung
- [ ] Custom Validation Rules (Regex, File-Patterns)
- [ ] Pre-Merge-Hooks für Custom-Scripts
- [ ] Slack/Discord-Benachrichtigungen bei Merge
- [ ] Auto-Release-Tagging bei Merge
- [ ] Merge-Queue für mehrere Tasks
- [ ] Rollback-Funktion bei fehlerhaften Merges

---

**Happy Auto-Merging! 🚀**
