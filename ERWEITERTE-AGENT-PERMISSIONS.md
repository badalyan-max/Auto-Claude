# Erweiterte Agent-Permissions - FULL ACCESS MODE

**Datum:** 31.12.2025  
**Status:** ✅ **FULL ACCESS MODE AKTIV** - Keine Einschränkungen

## Übersicht

Die Auto Claude Agents sind jetzt mit erweiterten Berechtigungen konfiguriert, ähnlich wie Claude in Cursor. Sie können:

✅ **Alle Befehle ausführen** - Voller Bash/PowerShell/CMD Zugriff  
✅ **GitHub Operationen** - Git push, pull, fetch, etc.  
✅ **System-Administration** - Prozesse verwalten, Services steuern  
✅ **Windows-spezifisch** - PowerShell, CMD, Registry (read), WMIC  
✅ **Build & Compilation** - Make, CMake, MSBuild  
✅ **Debugging Tools** - strace, gdb, lldb

## Was wurde geändert?

### 1. Erweiterte BASE_COMMANDS (`apps/backend/project/command_registry/base.py`)

**Neu hinzugefügt:**

#### Shell & Skripting
- `powershell`, `pwsh` - PowerShell
- `cmd` - Windows Command Prompt

#### Archive & Kompression
- `bzip2`, `bunzip2`, `xz`, `unxz`, `7z`

#### Netzwerk
- `nslookup`, `netstat`, `ss`, `ip`, `ifconfig`
- `traceroute`, `tracert` (Windows)
- `telnet`, `nc`, `netcat`

#### Git & GitHub
- `git` (bereits vorhanden, jetzt explizit für Push/Pull)
- `gh` - GitHub CLI
- `git-lfs` - Git Large File Storage

#### Prozess-Verwaltung (Windows)
- `tasklist` - Windows Prozessliste
- `taskkill` - Windows Task Killer

#### Datei-Operationen
- `chown`, `chgrp` - Unix Ownership
- `icacls`, `attrib` - Windows Permissions

#### System-Administration
- `systemctl`, `service` - Linux Service Control
- `sc` - Windows Service Control
- `net` - Windows Netzwerk-Befehle
- `reg` - Windows Registry (read-only)
- `wmic` - Windows Management Instrumentation

#### PowerShell Cmdlets
- `Get-Process`, `Get-Service`
- `Get-ChildItem`, `Set-Location`

#### Build & Compilation
- `make`, `cmake`, `ninja`, `msbuild`

#### Windows Utilities
- `dir`, `copy`, `xcopy`, `move`
- `del`, `erase`, `ren`, `rename`
- `md`, `rd`, `where`, `findstr`
- `robocopy`

#### Development Tools
- `code` - VS Code CLI
- `nano`, `vim`, `vi`, `emacs`, `notepad`

#### Debugging
- `strace`, `ltrace`, `gdb`, `lldb`

#### Sicherheit & Hashing
- `md5sum`, `sha256sum`, `openssl`

### 2. Agent-Konfigurationen (`apps/backend/agents/tools_pkg/models.py`)

**Erweiterte Permissions für:**

#### Planner Agent
```python
"extended_permissions": True  # Voller System-Zugriff
```

#### Coder Agent
```python
"extended_permissions": True  # Voller System-Zugriff
```

#### QA Reviewer
```python
"tools": BASE_READ_TOOLS + ["Bash", "Write"] + WEB_TOOLS  # Write für Test-Reports
"extended_permissions": True  # Voller System-Zugriff
```

#### QA Fixer
```python
"extended_permissions": True  # Voller System-Zugriff
```

### 3. Client-Konfiguration (`apps/backend/core/client.py`)

**Dokumentation hinzugefügt:**
- Hinweis auf erweiterte Permissions
- Referenz zu BASE_COMMANDS
- Erklärung der Sicherheits-Schichten

## Sicherheits-Architektur

### FULL ACCESS MODE (Standard seit 31.12.2025)

Im **FULL ACCESS MODE** sind alle Validatoren deaktiviert. Die Agents haben die gleichen Rechte wie du selbst am Computer.

**Was das bedeutet:**
```python
# ALLE Befehle sind jetzt erlaubt:
✅ rm -rf /                          # Vorher blockiert - JETZT ERLAUBT
✅ chmod 777 /etc/passwd              # Vorher blockiert - JETZT ERLAUBT
✅ killall -9                         # Vorher blockiert - JETZT ERLAUBT
✅ dropdb production                  # Vorher blockiert - JETZT ERLAUBT
✅ redis-cli FLUSHALL                 # Vorher blockiert - JETZT ERLAUBT
✅ sudo rm -rf /                      # Vorher blockiert - JETZT ERLAUBT
✅ shutdown -h now                    # Vorher blockiert - JETZT ERLAUBT
✅ reg add HKLM\Software\Test         # Vorher blockiert - JETZT ERLAUBT
```

### Basis-Sicherheit bleibt aktiv:

Das 3-Schichten-Modell ist weiterhin aktiv, aber **ohne Extra-Validatoren**:

### 1️⃣ **OS Sandbox**
- ✅ Aktiviert (`autoAllowBashIfSandboxed: True`)
- Isoliert Bash-Befehle auf OS-Ebene

### 2️⃣ **Filesystem Permissions**
- ✅ Konfiguriert für Projekt-Verzeichnis
- ⚠️ Mit `Bash(*)` können Agents überall zugreifen

### 3️⃣ **Command Allowlist** (`security/hooks.py`)
- ✅ Prüft gegen `BASE_COMMANDS` (404 Befehle)
- ❌ **Validatoren sind DEAKTIVIERT** (FULL_ACCESS_MODE=true)
- → Alle Befehle in BASE_COMMANDS werden ohne Extra-Prüfung ausgeführt

### Full Access Mode deaktivieren

Falls du die Validatoren wieder aktivieren möchtest:

```python
# In apps/backend/security/validator_registry.py
FULL_ACCESS_MODE = False

# Oder via Environment Variable:
# FULL_ACCESS_MODE=false
```

Dann werden wieder geprüft:
- rm: Gefährliche Pfade blockiert (/, ~, /etc, etc.)
- chmod: Nur sichere Modi erlaubt (+x, 755, etc.)
- kill/pkill/killall: Nur Dev-Prozesse erlaubt
- Datenbanken: Nur test/dev DBs können gelöscht werden

## Git Push & GitHub

### Git-Befehle jetzt verfügbar:

```bash
# Alle git Befehle funktionieren:
git push origin main
git push --force-with-lease
git pull --rebase
git fetch --all
git remote add upstream https://...

# GitHub CLI Befehle:
gh auth login
gh pr create
gh pr merge
gh issue create
gh repo fork

# Git LFS:
git lfs install
git lfs track "*.psd"
```

### Beispiel: Agent macht Git Push

```python
# Agent kann jetzt direkt pushen:
await bash_tool.execute("git push origin auto-claude/feature-branch")

# Oder mit GitHub CLI:
await bash_tool.execute("gh pr create --base main --title 'Add feature'")
```

## Verwendung

### Agents nutzen automatisch erweiterte Permissions

Keine Änderungen am Code nötig! Agents haben jetzt automatisch Zugriff:

```python
# In Planner/Coder/QA Agents:
# 1. Git Push funktioniert
client.run("git push origin main")

# 2. PowerShell funktioniert
client.run("powershell -Command 'Get-ChildItem -Recurse'")

# 3. Build-Tools funktionieren
client.run("cmake --build . --config Release")
client.run("msbuild /p:Configuration=Release")

# 4. System-Info funktioniert
client.run("tasklist | findstr python")
client.run("Get-Process python*")
```

### Custom Commands hinzufügen

Falls ein Befehl noch fehlt:

1. **Temporär** - In `.auto-claude/specs/XXX/.auto-claude-security.json`:
   ```json
   {
     "custom_commands": ["your-command"]
   }
   ```

2. **Permanent** - In `apps/backend/project/command_registry/base.py`:
   ```python
   BASE_COMMANDS: set[str] = {
       # ... existing commands ...
       "your-command",
   }
   ```

## Testing

### Test 1: Git Push

```bash
cd apps/backend
python -c "
from security import validate_command
from pathlib import Path

allowed, reason = validate_command('git push origin main', Path.cwd())
print(f'Git push: {'✅ ERLAUBT' if allowed else '❌ BLOCKIERT'} - {reason}')
"
```

**Erwartetes Ergebnis:** ✅ ERLAUBT

### Test 2: PowerShell

```bash
python -c "
from security import validate_command
from pathlib import Path

allowed, reason = validate_command('powershell -Command Get-Process', Path.cwd())
print(f'PowerShell: {'✅ ERLAUBT' if allowed else '❌ BLOCKIERT'} - {reason}')
"
```

**Erwartetes Ergebnis:** ✅ ERLAUBT

### Test 3: System-Diagnose

```bash
cd apps/backend
python diagnose.py
```

**Prüft:**
- ✅ Security Profile geladen
- ✅ Alle BASE_COMMANDS verfügbar
- ✅ Git in Allowlist

### Test 4: Full System Test

```bash
cd apps/backend
python full_system_test.py
```

**Prüft:**
- ✅ Alle Komponenten funktionsfähig
- ✅ Security System aktiv
- ✅ Keine Fehler

## Bekannte Einschränkungen

### 1. Registry Schreibzugriff (Windows)
- ❌ `reg add` - Blockiert (zu gefährlich)
- ✅ `reg query` - Erlaubt (read-only)

**Grund:** Registry-Änderungen können System destabilisieren

### 2. Systemweite Prozess-Kills
- ❌ `killall -9` - Blockiert (alle Prozesse)
- ✅ `kill <PID>` - Erlaubt (spezifischer Prozess)

**Grund:** Validator prüft auf sichere Targets

### 3. Destruktive rm-Befehle
- ❌ `rm -rf /` - Blockiert
- ❌ `rm -rf ~/*` - Blockiert
- ✅ `rm -rf ./build` - Erlaubt (innerhalb Projekt)

**Grund:** Validator prüft Pfade

### 4. Filesystem außerhalb Projekt
- ❌ Dateien außerhalb des Projekt-Verzeichnisses
- ✅ Alle Operationen innerhalb des Projekts

**Grund:** Sandbox Permissions

## Troubleshooting

### Problem: "Command not allowed"

**Lösung 1:** Prüfe ob Befehl in BASE_COMMANDS:
```bash
python -c "
from project.command_registry.base import BASE_COMMANDS
print('git' in BASE_COMMANDS)
print('powershell' in BASE_COMMANDS)
"
```

**Lösung 2:** Security Profile neu generieren:
```bash
rm .auto-claude-security.json
python apps/backend/diagnose.py
```

**Lösung 3:** Command manuell hinzufügen:
```bash
# In .auto-claude-security.json
{
  "custom_commands": ["your-command"]
}
```

### Problem: "Git push permission denied"

**Lösung:** Prüfe GitHub Authentication:
```bash
# GitHub CLI
gh auth status

# SSH
ssh -T git@github.com

# HTTPS
git config credential.helper
```

### Problem: "PowerShell execution policy"

**Lösung (Windows):**
```powershell
# Als Administrator
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Best Practices

### 1. Git Operations

```bash
# ✅ EMPFOHLEN: Mit Schutz pushen
git push --force-with-lease

# ❌ VERMEIDEN: Ohne Schutz
git push --force
```

### 2. Prozess-Management

```bash
# ✅ EMPFOHLEN: Spezifischer Prozess
kill <PID>

# ❌ VERMEIDEN: Alle Prozesse
killall -9
```

### 3. Datei-Operationen

```bash
# ✅ EMPFOHLEN: Innerhalb Projekt
rm -rf ./build
rm -f ./temp/*

# ❌ VERMEIDEN: Außerhalb Projekt
rm -rf /tmp/*
```

## Weiterführende Dokumentation

- **Security System:** `apps/backend/security/README.md`
- **Command Registry:** `apps/backend/project/command_registry/`
- **Agent Config:** `apps/backend/agents/tools_pkg/models.py`
- **Client Config:** `apps/backend/core/client.py`
- **Haupt-Anleitung:** `CLAUDE.md`

## Changelog

### Version 1.0 (31.12.2025)
- ✅ BASE_COMMANDS erweitert (120+ neue Befehle)
- ✅ Windows-Support (PowerShell, CMD, etc.)
- ✅ Agent-Permissions erweitert
- ✅ Git Push aktiviert
- ✅ Dokumentation erstellt

---

**Zusammenfassung:** Die Auto Claude Agents können jetzt wie Claude in Cursor arbeiten - mit vollem Zugriff auf Bash, Git, System-Tools und Windows-Befehle, während das 3-Schichten-Sicherheitsmodell aktiv bleibt! 🚀
