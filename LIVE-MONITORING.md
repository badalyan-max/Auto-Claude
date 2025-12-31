# 🔍 Auto Claude Live-Monitoring

Echtzeit-Überwachung und Fehleranalyse für Auto Claude.

---

## 📦 Was wurde erstellt?

### 1. **Live Monitor (Python)** 🐍
**Datei:** `apps/backend/live_monitor.py`

Ein Terminal-basiertes Monitoring-Tool, das:
- ✅ Laufende Auto Claude Prozesse findet
- ✅ Logs in Echtzeit verfolgt (wie `tail -f`)
- ✅ Fehler automatisch identifiziert und hervorhebt
- ✅ Kritische Fehler sofort meldet
- ✅ Statistiken über Fehler/Warnungen führt

### 2. **Windows Starter** 🪟
**Datei:** `Monitor-Auto-Claude.bat`

Einfacher Doppelklick-Starter für den Live Monitor.

### 3. **Web Dashboard** 🌐
**Datei:** `apps/backend/live_dashboard.html`

Ein schönes visuelles Dashboard mit:
- 📊 Echtzeit-Statistiken
- 🖥️ Prozess-Übersicht
- 📝 Live-Logs
- ⚠️ Fehler-Counter
- 💾 Memory-Status

---

## 🚀 Verwendung

### Option A: Terminal-Monitor (EMPFOHLEN für Live-Debugging)

#### Methode 1: Batch-Datei (Einfachste)
```batch
# Doppelklick auf:
Monitor-Auto-Claude.bat
```

#### Methode 2: Direkt mit Python
```bash
# Im Projekt-Root
cd C:\Projekte\auto-claude

# Status anzeigen
python apps\backend\live_monitor.py --status

# Backend-Logs folgen
python apps\backend\live_monitor.py --follow-logs

# Logs eines spezifischen Specs folgen
python apps\backend\live_monitor.py --spec 001

# Interaktiver Modus (empfohlen)
python apps\backend\live_monitor.py
```

### Option B: Web Dashboard (Schöne Übersicht)

```bash
# Öffne im Browser:
C:\Projekte\auto-claude\apps\backend\live_dashboard.html

# Oder: Doppelklick auf die HTML-Datei
```

---

## 🎯 Features im Detail

### Terminal-Monitor

#### 1. Status-Ansicht
```
============================================================
Auto Claude Live Monitor
============================================================

Laufende Prozesse: 2
  [PID 12345] python.exe run.py --spec 001
  [PID 12346] Auto-Claude.exe

Neueste Log-Einträge:
[001-authentication] session_2025_12_30_14_30.log
  → [INFO] Agent session started
  → [OK] Task completed successfully
  → [ERROR] Connection timeout
```

#### 2. Live-Log-Following
```
[INFO] Folge Log-Datei: .auto-claude/specs/001/logs/session.log
[INFO] Drücken Sie Ctrl+C zum Beenden

[INFO] Loading project context...
[OK] Context loaded successfully
[WARN] High token usage detected (15000 tokens)
[ERROR] API rate limit exceeded
[CRITICAL] ModuleNotFoundError: No module named 'graphiti'
```

#### 3. Fehler-Identifikation

Das Tool erkennt automatisch:
- ❌ **Kritische Fehler** (rot, fett):
  - `ModuleNotFoundError`
  - `ImportError`
  - `SyntaxError`
  - `MemoryError`
  - `ConnectionError`
  - `TimeoutError`
  - `PermissionError`

- 🔴 **Normale Fehler** (rot):
  - `ERROR`
  - `FAILED`
  - `Exception`
  - `Traceback`

- ⚠️ **Warnungen** (gelb):
  - `WARNING`
  - `Timeout`
  - `Retrying`
  - `deprecated`

- ✅ **Erfolge** (grün):
  - `SUCCESS`
  - `COMPLETE`
  - `passed`

#### 4. Zusammenfassung
```
============================================================
Monitoring Zusammenfassung:
============================================================
Kritische Fehler: 1
Fehler: 3
Warnungen: 5
```

### Web Dashboard

#### Features:
- 📊 **Live-Statistiken**
  - Prozess-Anzahl
  - Aktive Specs
  - Fehler-Counter
  - Memory-Status

- 🖥️ **Prozess-Übersicht**
  - PIDs anzeigen
  - Prozess-Namen
  - Status (läuft/gestoppt)

- 📝 **Live-Logs**
  - Farbcodierte Log-Einträge
  - Automatisches Scrollen
  - Zeitstempel
  - Filterung nach Level

- 🔄 **Auto-Refresh**
  - Aktualisiert alle 5 Sekunden
  - Manueller Refresh-Button

---

## 💡 Verwendungs-Szenarien

### Szenario 1: Task läuft, Sie wollen live zusehen

```bash
# Terminal 1: Start Auto Claude
python apps\backend\run.py --spec 001

# Terminal 2: Monitor starten
python apps\backend\live_monitor.py --follow-logs

# Jetzt sehen Sie alle Logs in Echtzeit!
```

### Szenario 2: Fehlersuche nach Task-Abbruch

```bash
# Monitor starten
python apps\backend\live_monitor.py --spec 001

# Zeigt die letzten Logs und folgt neuen Einträgen
# Fehler werden automatisch hervorgehoben
```

### Szenario 3: Prozess-Überwachung

```bash
# Status-Check
python apps\backend\live_monitor.py --status

# Zeigt:
# - Welche Prozesse laufen
# - Welche PIDs
# - Neueste Log-Einträge
```

### Szenario 4: Dashboard für Übersicht

```bash
# Öffne Dashboard im Browser
start apps\backend\live_dashboard.html

# Dann in einem anderen Terminal:
python apps\backend\run.py --spec 001

# Dashboard zeigt live den Status!
```

---

## 🔧 Erweiterte Features

### Interaktiver Modus

```bash
python apps\backend\live_monitor.py

# Zeigt Menü:
Optionen:
  1. Backend-Logs folgen
  2. Spec-Logs folgen
  3. Status aktualisieren
  4. Beenden

Wählen Sie eine Option (1-4):
```

### Filter nach Fehler-Level

Im Python-Code können Sie eigene Patterns hinzufügen:

```python
# In live_monitor.py, Zeile ~50
ERROR_PATTERNS = [
    (r"MEIN_FEHLER", "error"),
    (r"CUSTOM_WARNING", "warning"),
]
```

---

## 🎨 Anpassungen

### Farben ändern

Terminal-Farben in `live_monitor.py`:
```python
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    # ... anpassen nach Wunsch
```

Web-Dashboard-Farben in `live_dashboard.html`:
```css
.stat-value.error {
    color: #ef4444;  /* Rot */
}
```

### Refresh-Interval ändern

Web-Dashboard:
```javascript
// In live_dashboard.html, letzte Zeile
setInterval(refreshDashboard, 5000);  // 5000ms = 5 Sekunden
```

---

## 📊 Beispiel-Output

### Terminal-Monitor:
```
============================================================
Auto Claude Live Monitor
============================================================

Laufende Prozesse: 1
  [PID 12345] python.exe run.py --spec 001-authentication

Neueste Log-Einträge:

[001-authentication] session_2025_12_30_14_30.log
  → [INFO] Starting planner agent
  → [OK] Implementation plan created (5 subtasks)
  → [INFO] Starting coder agent for subtask 1.1
  → [WARN] High token usage: 15000 tokens
  → [ERROR] API rate limit exceeded, retrying...

============================================================
```

### Nach Live-Following:
```
[INFO] Folge Log-Datei: .auto-claude/specs/001/logs/session.log
[INFO] Drücken Sie Ctrl+C zum Beenden

[INFO] Coder agent session started
[INFO] Implementing authentication system
[OK] Created login.py
[OK] Created auth_service.py
[WARN] Test coverage below 80%
[ERROR] Import error in auth_service.py
[CRITICAL] ModuleNotFoundError: No module named 'bcrypt'
^C
[INFO] Monitoring beendet

============================================================
Monitoring Zusammenfassung:
============================================================
Kritische Fehler: 1
Fehler: 1
Warnungen: 1
```

---

## 🚨 Troubleshooting

### Problem: "Keine Prozesse gefunden"

**Lösung:**
- Auto Claude läuft noch nicht
- Starten Sie erst einen Task: `python run.py --spec 001`

### Problem: "Log-Datei nicht gefunden"

**Lösung:**
- Spec hat noch keine Logs erstellt
- Warten Sie bis Task startet
- Oder geben Sie korrekten Spec-Namen an

### Problem: "Encoding-Fehler"

**Lösung:**
Das Tool verwendet automatisch:
- UTF-8 für Log-Dateien
- CP1252 für Windows-Prozesse
- Falls Fehler: Tool mit Admin-Rechten starten

### Problem: "Python-Modul nicht gefunden"

**Lösung:**
```bash
# Virtual Environment aktivieren
cd apps\backend
.venv\Scripts\activate

# Dann Monitor starten
python live_monitor.py
```

---

## 🎯 Nächste Schritte

1. ✅ **Testen Sie den Monitor:**
   ```bash
   python apps\backend\live_monitor.py --status
   ```

2. ✅ **Öffnen Sie das Dashboard:**
   ```bash
   start apps\backend\live_dashboard.html
   ```

3. ✅ **Starten Sie einen Task und monitoren Sie ihn:**
   ```bash
   # Terminal 1
   python apps\backend\run.py --spec 001
   
   # Terminal 2
   python apps\backend\live_monitor.py --follow-logs
   ```

4. ✅ **Desktop-Verknüpfung erstellen:**
   - Rechtsklick auf `Monitor-Auto-Claude.bat`
   - "Verknüpfung erstellen"
   - Verknüpfung auf Desktop ziehen

---

## 🔗 Integration mit Auto Claude

Der Monitor ist vollständig integriert mit:
- ✅ Auto Claude Logs
- ✅ Spec-Verzeichnissen
- ✅ Implementation Plans
- ✅ QA Reports
- ✅ Memory System

Er liest automatisch aus:
- `.auto-claude/specs/*/logs/`
- `apps/backend/logs/`
- Python stdout/stderr

---

**Version:** 1.0  
**Erstellt:** 30.12.2025  
**Sprache:** Deutsch 🇩🇪  

**Genießen Sie das Live-Monitoring!** 🔍✨

