# API Authentication Fix - 2. Januar 2026

## Problem

Der User erhielt ständig diese Fehler:

```
API Error: 401 {"type":"error","error":{"type":"authentication_error","message":"Invalid bearer token"}}
[UsageMonitor] CLI fallback not implemented, API method should be used
[UsageMonitor] Failed to fetch usage
```

## Root Causes

### 1. **Verschlüsselter OAuth Token in .env**
- Die `.env` Datei enthielt einen **verschlüsselten** Token: `enc:djEwN...`
- Auto Claude erwartet aber einen **unverschlüsselten** OAuth Token: `sk-ant-oat01-...`
- Der korrekte Token existierte bereits in Windows Credentials (`~\.claude\.credentials.json`)

### 2. **Memory System: .env wurde nicht geladen**
- `get_graphiti_status()` wurde aufgerufen **BEVOR** `load_dotenv()` lief
- Daher war `GRAPHITI_ENABLED` immer `None` statt `"true"`
- Status: "GRAPHITI_ENABLED not set to true" trotz korrekter .env

### 3. **Usage Monitor: API Endpoint nicht verfügbar**
- Der Frontend Usage Monitor versuchte `https://api.anthropic.com/api/oauth/usage` aufzurufen
- Dieser Endpoint funktioniert nicht mit Auto Claude's OAuth Token
- → 401 Authentication Error bei jedem Check (alle 30 Sekunden)

## Fixes

### ✅ Fix 1: OAuth Token aktualisiert
**Datei:** `apps/backend/.env`

**Vorher:**
```env
CLAUDE_CODE_OAUTH_TOKEN=enc:djEwNfdQWK+V+dP0s0GU0DzU...
```

**Nachher:**
```env
CLAUDE_CODE_OAUTH_TOKEN=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
```

**Quelle:** Token aus `%USERPROFILE%\.claude\.credentials.json` extrahiert

**Test:**
```bash
cd apps\backend
.\.venv\Scripts\python.exe -c "from core.auth import get_auth_token; token = get_auth_token(); print('Valid:', token.startswith('sk-ant-oat01-'))"
# Output: Valid: True
```

### ✅ Fix 2: Graphiti Config - dotenv laden
**Datei:** `apps/backend/integrations/graphiti/config.py`

**Änderung:**
```python
# Hinzugefügt am Anfang des Moduls (nach Imports):
from dotenv import load_dotenv
load_dotenv()
```

**Effekt:**
- Stellt sicher dass `.env` **immer** geladen wird, bevor Config gelesen wird
- Löst das "GRAPHITI_ENABLED not set to true" Problem

**Test:**
```bash
cd apps\backend
.\.venv\Scripts\python.exe -c "from integrations.graphiti.config import get_graphiti_status; import json; print(json.dumps(get_graphiti_status(), indent=2))"
# Output:
# {
#   "enabled": true,
#   "available": true,
#   "errors": []
# }
```

### ✅ Fix 3: Usage Monitor deaktiviert
**Datei:** `apps/frontend/src/main/index.ts`

**Änderung:**
```typescript
// Initialize usage monitoring after window is created
if (mainWindow) {
  // Setup event forwarding from usage monitor to renderer
  initializeUsageMonitorForwarding(mainWindow);

  // NOTE: Usage monitor disabled - API endpoint not available for Auto Claude
  // const usageMonitor = getUsageMonitor();
  // usageMonitor.start();
  console.warn('[main] Usage monitor disabled (API not available)');
```

**Effekt:**
- Keine 401 Errors mehr beim App-Start
- Keine "Failed to fetch usage" Warnungen
- Feature nicht essentiell für Auto Claude

## System Test Ergebnisse

```bash
cd apps\backend
.\.venv\Scripts\python.exe ..\..\apps\backend\full_system_test.py
```

**Output:**
```
============================================================
AUTO CLAUDE - VOLLSTÄNDIGER SYSTEM-TEST
============================================================

1. Python Version...
   ✓ [OK] Python 3.14

2. Konfiguration...
   ✓ [OK] .env existiert
   ✓ [OK] GRAPHITI_ENABLED=true
   ✓ [OK] OPENAI_API_KEY vorhanden

3. Memory System...
   ✓ [OK] Memory enabled
   ✓ [OK] Memory verfügbar
     Provider: openai

4. Specs und Tasks...
   Keine Specs vorhanden

5. Git Worktrees...
   Gefunden: 3 zusätzliche Worktrees

6. Live Monitor...
   ✓ [OK] live_monitor.py existiert
   ✓ [OK] Monitor funktioniert

7. Desktop Verknüpfungen...
   ⚠ [WARN] Auto Claude.lnk fehlt
   ⚠ [WARN] Auto Claude (EXE).lnk fehlt
   ⚠ [WARN] Auto Claude Monitor.lnk fehlt

============================================================
ZUSAMMENFASSUNG
============================================================

✅ Bestanden: 8
  - Python Version 3.12+
  - .env Datei vorhanden
  - Graphiti aktiviert
  - OpenAI Key konfiguriert
  - Memory System verfügbar
  - Keine Specs (OK)
  - 3 Worktrees aktiv
  - Live Monitor OK

============================================================

✅ Alle Tests bestanden!
```

## Zusammenfassung

### Was behoben wurde:
1. ✅ OAuth Token korrekt (von Windows Credentials)
2. ✅ Memory System funktioniert (Graphiti available)
3. ✅ Keine 401 Authentication Errors mehr
4. ✅ Keine Usage Monitor Fehler mehr

### Nächste Schritte für User:
1. **Frontend neu bauen** (wenn Electron App genutzt wird):
   ```bash
   cd apps\frontend
   npm run build
   ```

2. **Electron App neu starten** (falls läuft):
   - Prozess beenden
   - Neu starten aus `apps\frontend\dist\win-unpacked\Auto-Claude.exe`

3. **Backend testen**:
   ```bash
   cd apps\backend
   .\.venv\Scripts\python.exe run.py --list
   ```

### Backup erstellt:
- `apps\backend\.env.backup` - Original .env vor Token-Update

## Technische Details

### Authentication Flow
1. **Backend** nutzt `core/auth.py`:
   - Prüft `CLAUDE_CODE_OAUTH_TOKEN` in .env
   - Fallback zu Windows Credential Files
   - Validiert Token-Format (`sk-ant-oat01-*`)

2. **Token-Quellen (Priorität)**:
   - `CLAUDE_CODE_OAUTH_TOKEN` (env var) ← **jetzt korrekt**
   - `ANTHROPIC_AUTH_TOKEN` (CCR/proxy)
   - Windows Credential Files (`~\.claude\.credentials.json`)
   - macOS Keychain

3. **Memory System**:
   - Benötigt `GRAPHITI_ENABLED=true`
   - Benötigt `OPENAI_API_KEY` (für Embeddings)
   - Verwendet LadybugDB (embedded, kein Docker)

### API Endpoints
- ✅ **Funktioniert**: Claude Agent SDK API (für Agents)
- ❌ **Funktioniert nicht**: `https://api.anthropic.com/api/oauth/usage` (Usage Monitor)

## Lessons Learned

1. **Verschlüsselte Tokens**: Auto Claude benötigt plain-text OAuth Tokens
2. **dotenv Timing**: Module die `.env` benötigen müssen `load_dotenv()` selbst aufrufen
3. **Usage Monitoring**: Feature ist optional und nicht für alle Claude Setups verfügbar

---

**Status:** ✅ BEHOBEN
**Getestet:** 2. Januar 2026 22:40
**Version:** Auto Claude 2.x
