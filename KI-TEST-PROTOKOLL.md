# 🤖 KI-Test-Protokoll für Auto Claude

**Zweck:** Anleitung für die KI, um Auto Claude selbstständig zu testen und Probleme zu identifizieren, OHNE dass der User jedes Mal "teste dies/das" sagen muss.

**Verwendung:** Wenn der User ein Problem meldet oder die KI Änderungen vornimmt, soll sie AUTOMATISCH dieses Protokoll durchlaufen.

---

## 📋 Standard-Test-Workflow

### **1. System-Diagnose (IMMER ZUERST)**

```bash
cd C:\Projekte\auto-claude
python apps\backend\diagnose.py
```

**Was prüfen:**
- ✅ Python Version (muss 3.12+ sein)
- ✅ .env Datei existiert
- ✅ Memory System aktiviert (GRAPHITI_ENABLED=true)
- ✅ OpenAI API Key konfiguriert
- ✅ Keine hängenden Tasks
- ✅ Keine Worktrees

**Output interpretieren:**
```
[OK] = Alles gut
[ERROR] = MUSS behoben werden
[WARN] = Kann Problem verursachen
```

---

### **2. Memory-System prüfen**

```bash
cd C:\Projekte\auto-claude
python apps\backend\diagnose.py --check-memory
```

**Wenn nicht vorhanden, erstelle Check:**
```python
# In Python ausführen
from integrations.graphiti.config import get_graphiti_status
import json
print(json.dumps(get_graphiti_status(), indent=2))
```

**Erwartetes Ergebnis:**
```json
{
  "enabled": true,
  "available": true,
  "database": "auto_claude_memory_...",
  "embedder_provider": "openai"
}
```

**Falls "available": false:**
- Prüfe GRAPHITI_ENABLED in .env
- Prüfe OPENAI_API_KEY vorhanden
- Prüfe Python 3.12+

---

### **3. Live-Monitor testen**

```bash
# Status check
python apps\backend\live_monitor.py --status

# Follow-all Test (sollte "keine Logs" sagen wenn nichts läuft)
timeout /t 5 & python apps\backend\live_monitor.py --follow-all
```

**Erwartetes Verhalten:**
- Status zeigt laufende Prozesse (oder "Keine gefunden")
- Follow-all wartet auf Logs oder zeigt "Keine Log-Dateien gefunden"
- KEINE Python-Fehler (ModuleNotFoundError, etc.)

---

### **4. Specs und Tasks prüfen**

```bash
# Prüfe ob Spec-Verzeichnis existiert
dir .auto-claude\specs 2>nul || echo "Keine Specs vorhanden"

# Liste alle Specs
dir .auto-claude\specs /b 2>nul

# Prüfe Implementation Plans
dir .auto-claude\specs\*\implementation_plan.json /s /b 2>nul
```

**Was prüfen:**
- Existieren Specs?
- Haben sie implementation_plan.json?
- Status in den Plans prüfen

**Plan-Status auslesen:**
```python
import json
from pathlib import Path

specs_dir = Path(".auto-claude/specs")
if specs_dir.exists():
    for spec in specs_dir.iterdir():
        plan = spec / "implementation_plan.json"
        if plan.exists():
            data = json.loads(plan.read_text())
            print(f"{spec.name}: Status={data.get('status', 'unknown')}")
```

---

### **5. Logs analysieren**

```bash
# Backend-Logs (falls vorhanden)
type apps\backend\logs\auto-claude.log 2>nul | findstr /i "error critical exception"

# Neueste Spec-Logs
dir .auto-claude\specs\*\logs\*.log /s /b /o:d 2>nul
```

**Log-Analyse durchführen:**
```python
import re
from pathlib import Path

# Fehler-Patterns
error_patterns = [
    r"ERROR",
    r"CRITICAL",
    r"Exception",
    r"Traceback",
    r"ModuleNotFoundError",
    r"ImportError",
]

def analyze_log(log_file):
    if not Path(log_file).exists():
        return
    
    errors = []
    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f, 1):
            for pattern in error_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    errors.append((i, line.strip()))
    
    return errors

# Analysiere neueste Logs
logs_dir = Path(".auto-claude/specs")
if logs_dir.exists():
    for spec_dir in logs_dir.iterdir():
        log_dir = spec_dir / "logs"
        if log_dir.exists():
            for log in log_dir.glob("*.log"):
                errors = analyze_log(log)
                if errors:
                    print(f"\n{spec_dir.name} - {log.name}:")
                    for line_no, error in errors[-5:]:  # Letzte 5 Fehler
                        print(f"  Line {line_no}: {error}")
```

---

### **6. Git-Status prüfen**

```bash
# Aktueller Branch
git branch --show-current

# Uncommitted Changes
git status --short

# Auto-Claude Branches
git branch | findstr "auto-claude"

# Worktrees
git worktree list 2>nul
```

**Was prüfen:**
- Sind uncommitted Changes vorhanden? (Könnte zu Problemen führen)
- Existieren alte auto-claude Branches?
- Hängende Worktrees?

---

### **7. Prozess-Monitoring**

```powershell
# Python-Prozesse mit auto-claude
Get-Process python* | Where-Object {$_.CommandLine -like "*auto-claude*" -or $_.CommandLine -like "*run.py*"}

# Electron-Prozesse
Get-Process | Where-Object {$_.ProcessName -like "*Auto-Claude*"}
```

**Interpretation:**
- Mehrere python.exe mit run.py = Mehrere Tasks laufen
- Keine Prozesse = Nichts läuft derzeit
- Prozesse ohne Terminal = Zombie-Prozesse?

---

## 🔍 Problem-Spezifische Tests

### **Problem: "Memory funktioniert nicht"**

**Test-Workflow:**

1. **Status prüfen:**
   ```bash
   python apps\backend\diagnose.py
   # Schaue auf Memory System Sektion
   ```

2. **.env prüfen:**
   ```bash
   type apps\backend\.env | findstr "GRAPHITI"
   ```
   
   **Muss enthalten:**
   - `GRAPHITI_ENABLED=true`
   - `GRAPHITI_EMBEDDER_PROVIDER=openai` (oder ollama/voyage)
   - `OPENAI_API_KEY=sk-...` (falls OpenAI)

3. **Graphiti Connection testen:**
   ```python
   from integrations.graphiti.memory import get_graphiti_memory
   from pathlib import Path
   
   spec_dir = Path(".auto-claude/specs/test")
   spec_dir.mkdir(parents=True, exist_ok=True)
   
   memory = get_graphiti_memory(spec_dir, Path.cwd())
   print(f"Enabled: {memory.is_enabled}")
   print(f"Initialized: {memory.is_initialized}")
   ```

4. **Falls Fehler:**
   - Prüfe Python Version (muss 3.12+)
   - Prüfe API Key gültig
   - Prüfe .env encoding (muss UTF-8 sein)

---

### **Problem: "Tasks hängen im Kanban Board"**

**Test-Workflow:**

1. **Hängende Tasks finden:**
   ```bash
   python apps\backend\diagnose.py --fix-stuck-tasks
   ```

2. **Implementation Plans prüfen:**
   ```python
   import json
   from pathlib import Path
   
   for spec in Path(".auto-claude/specs").iterdir():
       plan_file = spec / "implementation_plan.json"
       if plan_file.exists():
           plan = json.loads(plan_file.read_text())
           status = plan.get("status", "unknown")
           
           # Prüfe auf "in_progress" ohne laufenden Prozess
           if status == "in_progress":
               print(f"⚠️ {spec.name} ist 'in_progress'")
               
               # Prüfe ob Prozess läuft
               # (Code hier um Prozess zu prüfen)
   ```

3. **Worktrees prüfen:**
   ```bash
   git worktree list
   dir .worktrees 2>nul
   ```

4. **Automatische Reparatur:**
   ```bash
   python apps\backend\diagnose.py --fix-stuck-tasks
   ```

---

### **Problem: "GitHub Push nach 'Done' Status"**

**Test-Workflow:**

1. **"Done" Tasks finden:**
   ```python
   import json
   from pathlib import Path
   
   done_tasks = []
   for spec in Path(".auto-claude/specs").iterdir():
       plan = spec / "implementation_plan.json"
       if plan.exists():
           data = json.loads(plan.read_text())
           if data.get("status") == "done":
               done_tasks.append({
                   "spec": spec.name,
                   "branch": f"auto-claude/{spec.name}"
               })
   
   print(f"Found {len(done_tasks)} done tasks")
   for task in done_tasks:
       print(f"  - {task['spec']}")
   ```

2. **Branch-Status prüfen:**
   ```bash
   git branch | findstr "auto-claude"
   ```

3. **GitHub CLI testen:**
   ```bash
   gh auth status
   ```

4. **Wenn User will pushen:**
   ```bash
   git push origin main
   # Oder für Feature-Branch:
   git push origin auto-claude/001-spec-name
   ```

---

### **Problem: "Electron App startet nicht"**

**Test-Workflow:**

1. **Build-Status prüfen:**
   ```bash
   dir apps\frontend\dist\win-unpacked\Auto-Claude.exe
   ```

2. **Dependencies prüfen:**
   ```bash
   cd apps\frontend
   npm list --depth=0 2>nul | findstr "UNMET"
   ```

3. **Logs prüfen:**
   ```bash
   # Windows AppData Logs
   type "%APPDATA%\auto-claude-ui\logs\main.log" 2>nul | findstr /i "error"
   ```

4. **Neustart versuchen:**
   ```bash
   # Prozesse beenden
   taskkill /F /IM "Auto-Claude.exe" 2>nul
   
   # Neu starten
   start "" "apps\frontend\dist\win-unpacked\Auto-Claude.exe"
   ```

---

## 📊 Vollständiger Test-Durchlauf

**Wenn User sagt: "Teste alles" oder "Prüfe das System"**

```python
# Vollständiger automatischer Test
# apps/backend/full_system_test.py

def run_full_test():
    print("="*60)
    print("AUTO CLAUDE - VOLLSTÄNDIGER SYSTEM-TEST")
    print("="*60)
    
    results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }
    
    # 1. Python Version
    print("\n1. Python Version...")
    import sys
    if sys.version_info >= (3, 12):
        results["passed"].append("Python Version OK")
    else:
        results["failed"].append(f"Python {sys.version_info.major}.{sys.version_info.minor} zu alt")
    
    # 2. .env Datei
    print("2. Konfiguration...")
    from pathlib import Path
    if (Path(__file__).parent / ".env").exists():
        results["passed"].append(".env existiert")
    else:
        results["failed"].append(".env fehlt")
    
    # 3. Memory System
    print("3. Memory System...")
    try:
        from integrations.graphiti.config import get_graphiti_status
        status = get_graphiti_status()
        if status["available"]:
            results["passed"].append("Memory verfügbar")
        else:
            results["failed"].append(f"Memory: {status['reason']}")
    except Exception as e:
        results["failed"].append(f"Memory Error: {e}")
    
    # 4. Hängende Tasks
    print("4. Task Status...")
    specs_dir = Path(".auto-claude/specs")
    if specs_dir.exists():
        import json
        stuck = 0
        for spec in specs_dir.iterdir():
            plan = spec / "implementation_plan.json"
            if plan.exists():
                data = json.loads(plan.read_text())
                if data.get("status") == "in_progress":
                    # TODO: Prüfe ob Prozess läuft
                    stuck += 1
        
        if stuck > 0:
            results["warnings"].append(f"{stuck} Tasks möglicherweise stuck")
        else:
            results["passed"].append("Keine stuck Tasks")
    else:
        results["passed"].append("Keine Specs vorhanden")
    
    # 5. Live Monitor
    print("5. Live Monitor...")
    try:
        import subprocess
        result = subprocess.run(
            ["python", "apps/backend/live_monitor.py", "--status"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            results["passed"].append("Live Monitor funktioniert")
        else:
            results["failed"].append("Live Monitor Error")
    except Exception as e:
        results["failed"].append(f"Live Monitor: {e}")
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)
    
    print(f"\n✅ Bestanden: {len(results['passed'])}")
    for test in results["passed"]:
        print(f"  - {test}")
    
    if results["warnings"]:
        print(f"\n⚠️ Warnungen: {len(results['warnings'])}")
        for warn in results["warnings"]:
            print(f"  - {warn}")
    
    if results["failed"]:
        print(f"\n❌ Fehlgeschlagen: {len(results['failed'])}")
        for fail in results["failed"]:
            print(f"  - {fail}")
    
    print("\n" + "="*60)
    
    return len(results["failed"]) == 0

if __name__ == "__main__":
    success = run_full_test()
    exit(0 if success else 1)
```

---

## 🎯 KI-Verhaltensregeln

### **IMMER wenn Code geändert wird:**

1. ✅ **Teste die Änderung sofort**
   - Führe relevante Tests aus
   - Prüfe Logs auf Fehler
   - Validiere Output

2. ✅ **Diagnose VORHER und NACHHER**
   ```bash
   # Vorher
   python apps\backend\diagnose.py > before.txt
   
   # Änderungen machen
   # ...
   
   # Nachher
   python apps\backend\diagnose.py > after.txt
   
   # Vergleich zeigen
   ```

3. ✅ **Log-Analyse durchführen**
   - Prüfe auf neue Fehler
   - Suche nach CRITICAL/ERROR
   - Zeige User relevante Fehler

### **IMMER wenn User Problem meldet:**

1. ✅ **Reproduziere das Problem**
   - Versuche selbst das Problem zu erzeugen
   - Dokumentiere Schritte

2. ✅ **Diagnostiziere systematisch**
   - Nutze diagnose.py
   - Prüfe relevante Logs
   - Analysiere Implementation Plans

3. ✅ **Teste die Lösung**
   - Implementiere Fix
   - Teste ob Problem behoben
   - Validiere keine neuen Probleme

### **NIEMALS:**

❌ Sage "Bitte testen Sie..." - **ICH teste!**
❌ Sage "Führen Sie aus..." - **ICH führe aus!**
❌ Erstelle Code ohne zu testen
❌ Ändere .env ohne zu validieren
❌ Lösche Dateien ohne Backup

---

## 📝 Test-Checkliste

**Vor jeder Antwort an User:**

- [ ] Habe ich diagnose.py ausgeführt?
- [ ] Habe ich relevante Logs geprüft?
- [ ] Habe ich meine Änderungen getestet?
- [ ] Habe ich nach neuen Fehlern gesucht?
- [ ] Kann ich dem User konkrete Testergebnisse zeigen?

**Bei Problemen:**

- [ ] Problem reproduziert?
- [ ] Logs analysiert?
- [ ] Root Cause identifiziert?
- [ ] Fix getestet?
- [ ] Keine Regression?

---

## 🚀 Quick Commands für KI

```bash
# Standard-Diagnose
python apps\backend\diagnose.py

# Memory prüfen
python apps\backend\diagnose.py --check-memory

# Stuck Tasks reparieren
python apps\backend\diagnose.py --fix-stuck-tasks

# Live Monitor testen
python apps\backend\live_monitor.py --status

# Logs analysieren
python apps\backend\live_monitor.py --follow-all

# Implementation Plans prüfen
dir .auto-claude\specs\*\implementation_plan.json /s /b

# Prozesse finden
Get-Process python* | Where-Object {$_.CommandLine -like "*auto-claude*"}

# Git Status
git status --short
git worktree list
git branch | findstr "auto-claude"
```

---

## 📖 Dokumentations-Referenzen

Für Details siehe:
- `CLAUDE.md` - Vollständige Architektur
- `PROBLEMLÖSUNGEN.md` - Bekannte Probleme & Lösungen
- `LIVE-MONITORING.md` - Monitor-Dokumentation
- `HILFE-DEUTSCH.md` - User-Dokumentation

---

**Version:** 1.0  
**Erstellt:** 30.12.2025  
**Zweck:** KI-Selbsttest-Protokoll  
**Sprache:** Deutsch 🇩🇪

**WICHTIG: Die KI soll dieses Protokoll bei JEDEM Problem automatisch durchlaufen, OHNE dass der User sagen muss "teste das"!**

