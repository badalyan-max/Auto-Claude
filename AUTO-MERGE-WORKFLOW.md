# 🤖 Automatischer Merge & Changelog Workflow

## Übersicht

Auto-Claude führt jetzt **automatisch** folgende Schritte aus, wenn du einen Task auf "Done" setzt:

1. ✅ **Commit-Validierung** - Prüft alle Commits des Tasks mit AI
2. ✅ **Changelog-Generierung** - Erstellt automatisch einen Changelog-Eintrag
3. ✅ **Merge zu Main** - Merged den Task-Branch in den Main-Branch
4. ✅ **Push zu GitHub** - Pusht alle Änderungen automatisch

---

## 🎯 Workflow

### Schritt 1: Task auf "Done" setzen

Wenn du einen Task im Kanban Board auf **"Done"** ziehst oder manuell auf "Done" setzt, startet der automatische Workflow:

```
Task: "Add dark mode toggle"
Status: human_review → done
```

**Was passiert automatisch:**

---

### Schritt 2: Commit-Validierung 🔍

Auto-Claude prüft alle Commits des Tasks:

**Validierungskriterien:**
- ✅ Mindestens 1 Commit vorhanden
- ✅ Commit-Messages sind aussagekräftig (>10 Zeichen)
- ✅ Keine WIP/Temp-Commits
- ✅ Dateien wurden tatsächlich geändert
- ✅ Commits passen zur Task-Beschreibung

**AI Quality Score:**
- 100 = Perfekt
- 70-99 = Gut (Standard: 70 = Minimum)
- < 70 = Abgelehnt

**Bei Fehler:**
- Task bleibt auf "Done"
- Du erhältst eine Fehlermeldung mit Details
- Du kannst manuell mergen oder den Task nochmal bearbeiten

---

### Schritt 3: Changelog-Generierung 📝

**WICHTIG:** Changelog wird **VOR** dem Merge erstellt!

Auto-Claude generiert einen KI-basierten Changelog-Eintrag:

**Was wird analysiert:**
- ✅ Task-Titel und Beschreibung
- ✅ Spec.md (technische Spezifikation)
- ✅ Alle Git-Commits
- ✅ Geänderte Dateien
- ✅ Implementation Plan
- ✅ QA Report
- ✅ Session Insights (was hat funktioniert/nicht funktioniert)

**Changelog-Format:**

```markdown
## [2026-01-02] - Add dark mode toggle

### Added
- Dark mode toggle in settings panel
- Theme context provider for app-wide theme management
- CSS-in-JS dark theme styles
- LocalStorage persistence for theme preference

### Changed
- Updated Settings component to include theme switcher
- Modified App.tsx to wrap with ThemeProvider

### Technical Details
- Implemented using React Context API
- Dark theme uses CSS custom properties
- Auto-detects system theme preference

**Commits:** 3
**Files Changed:** 8
**Lines Added:** 245
**Lines Removed:** 12

---
```

**Wo wird es gespeichert:**
- Pfad: `CHANGELOG.md` (konfigurierbar)
- Modus: **Prepend** (neuer Eintrag ganz oben)

---

### Schritt 4: Merge zu Main 🔀

**Merge-Vorgang:**

```bash
# 1. Wechsel zum Main-Branch
git checkout main

# 2. Stage Changelog (wenn generiert)
git add CHANGELOG.md

# 3. Merge mit No-Fast-Forward (behält Historie)
git merge --no-ff -m "Merge task: Add dark mode toggle" auto-claude/task-001

# 4. Merge-Commit-Message (automatisch):
"""
Merge task: Add dark mode toggle

🤖 Auto-merged by Auto-Claude
Task completed and validated.

📝 Changelog updated: CHANGELOG.md
"""
```

**Merge-Commit enthält:**
- ✅ Task-Titel
- ✅ Auto-Claude Signatur
- ✅ Changelog-Referenz
- ✅ Validierungs-Info

---

### Schritt 5: Push zu GitHub ⬆️

**Automatischer Push:**

```bash
git push origin main
```

**Was wird gepusht:**
- ✅ Merge-Commit
- ✅ CHANGELOG.md (aktualisiert)
- ✅ Alle Task-Änderungen

**Bei Fehler:**
- Merge bleibt lokal erhalten
- Du kannst manuell pushen
- Keine Rollback-Notwendigkeit

---

## ⚙️ Konfiguration

### Auto-Merge aktivieren/deaktivieren

Standardmäßig **aktiviert**. Du kannst es in den Projekt-Einstellungen anpassen:

```typescript
// .auto-claude/project-settings.json
{
  "autoMerge": {
    "enabled": true,              // Auto-Merge aktivieren
    "requireAIValidation": true,  // AI-Validierung erforderlich
    "minQualityScore": 70,        // Minimaler Quality Score (0-100)
    "autoPush": true,             // Automatisch zu GitHub pushen
    "targetBranch": "main",       // Ziel-Branch
    "generateChangelog": true,    // Changelog generieren
    "changelogPath": "CHANGELOG.md" // Changelog-Datei
  }
}
```

### Changelog-Generierung deaktivieren

Wenn du keinen automatischen Changelog willst:

```json
{
  "autoMerge": {
    "generateChangelog": false  // Kein Changelog
  }
}
```

### AI-Validierung deaktivieren

**NICHT EMPFOHLEN**, aber möglich:

```json
{
  "autoMerge": {
    "requireAIValidation": false  // Keine AI-Validierung
  }
}
```

---

## 🚨 Fehlerbehandlung

### Fehler 1: "No commits found for this task"

**Ursache:** Task-Branch hat keine Commits

**Lösung:**
1. Prüfe ob der Branch existiert: `git branch -a | grep auto-claude`
2. Checke ob Commits vorhanden sind: `git log auto-claude/task-001`
3. Manuell committen falls nötig

---

### Fehler 2: "AI validation failed: Task appears incomplete"

**Ursache:** AI hält die Commits für unvollständig

**Lösung:**
1. Prüfe AI-Feedback in der Fehlermeldung
2. Fehlende Dateien nachreichen
3. Task nochmal auf "in_progress" setzen
4. Ergänzungen vornehmen
5. Erneut auf "done" setzen

---

### Fehler 3: "Changelog generation failed"

**Ursache:** AI konnte keinen Changelog erstellen

**Lösung:**
- **Nicht kritisch!** Merge läuft trotzdem weiter
- Du kannst den Changelog manuell nachpflegen
- Prüfe ob Claude CLI verfügbar ist

---

### Fehler 4: "Push failed"

**Ursache:** GitHub-Push fehlgeschlagen

**Lösung:**
- **Merge ist erfolgreich!** Nur Push fehlgeschlagen
- Manuell pushen: `git push origin main`
- Prüfe Git-Credentials
- Prüfe Internet-Verbindung

---

## 📊 UI-Feedback

### Progress-Meldungen

Während des Auto-Merge siehst du folgende Progress-Meldungen:

```
10%  - Checking task commits...
30%  - Analyzing commits...
50%  - Validating with AI...
60%  - Generating changelog... (optional)
70%  - Merging to main...
90%  - Pushing to GitHub...
100% - Complete!
```

### Success-Notification

Nach erfolgreichem Merge:

```
✅ Auto-Merge erfolgreich!
   - 3 Commits merged
   - Changelog generiert: CHANGELOG.md
   - Gepusht zu GitHub
```

### Failure-Notification

Bei Fehler:

```
❌ Auto-Merge fehlgeschlagen
   - AI validation failed: Quality score 45 below minimum 70
   - Issues:
     • Commit message too short: "fix"
     • No files were changed in commits
```

---

## 🔧 Manueller Fallback

Falls Auto-Merge fehlschlägt, kannst du manuell mergen:

```bash
# 1. Checkout main
git checkout main

# 2. Merge Task-Branch
git merge --no-ff auto-claude/task-001

# 3. Push
git push origin main
```

---

## 🎓 Best Practices

### ✅ DO:

1. **Aussagekräftige Commit-Messages verwenden**
   ```bash
   ✅ "feat: Add dark mode toggle with theme context"
   ❌ "fix"
   ```

2. **Alle Dateien committen**
   - Keine fehlenden Änderungen

3. **Task vollständig abschließen**
   - Alle Subtasks completed
   - QA durchgeführt

4. **Changelog kontrollieren**
   - Nach Merge: CHANGELOG.md öffnen
   - Ggf. manuell nachbearbeiten

### ❌ DON'T:

1. **WIP-Commits nicht auf Done setzen**
   ```bash
   ❌ "WIP: testing stuff"
   ```

2. **Leere Commits vermeiden**
   ```bash
   ❌ git commit --allow-empty
   ```

3. **Nicht zu früh auf "Done" setzen**
   - Erst wenn wirklich fertig

---

## 📝 Changelog-Beispiel

**Vor Auto-Merge:**
```markdown
# Changelog

All notable changes to this project will be documented in this file.

```

**Nach Auto-Merge:**
```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [2026-01-02] - Add dark mode toggle

### Added
- Dark mode toggle in settings panel
- Theme context provider for app-wide theme management
- CSS-in-JS dark theme styles
- LocalStorage persistence for theme preference

### Changed
- Updated Settings component to include theme switcher
- Modified App.tsx to wrap with ThemeProvider

### Technical Details
- Implemented using React Context API
- Dark theme uses CSS custom properties
- Auto-detects system theme preference

**Commits:** 3
**Files Changed:** 8
**Lines Added:** 245
**Lines Removed:** 12

---

```

---

## 🚀 Zusammenfassung

**Was du tun musst:**
1. Task auf "Done" setzen ✅

**Was Auto-Claude macht:**
1. Commits validieren ✅
2. Changelog generieren ✅
3. Zu Main mergen ✅
4. Zu GitHub pushen ✅

**Ergebnis:**
- ✅ Task ist merged
- ✅ Changelog ist aktualisiert
- ✅ Code ist auf GitHub
- ✅ Du kannst direkt weiterarbeiten

---

## 🆘 Support

Bei Problemen:

1. Prüfe Logs: Auto-Claude Terminal Output
2. Schaue in CHANGELOG.md ob Eintrag erstellt wurde
3. Prüfe Git-Status: `git status`
4. Prüfe Git-Log: `git log -n 5`

**Häufigste Probleme:**
- Claude CLI nicht installiert → Changelog-Generierung schlägt fehl (nicht kritisch)
- Git-Credentials fehlen → Push schlägt fehl (lokal gemerged bleibt erhalten)
- Quality Score zu niedrig → Commits nochmal überprüfen

---

**Viel Erfolg mit dem automatischen Workflow!** 🎉
