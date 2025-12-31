# Project Index Auto-Refresh

## Übersicht

Der Project Index (`project_index.json`) wird jetzt automatisch aktualisiert, wenn sich relevante Projektdateien ändern. Dies stellt sicher, dass KI-Agenten immer die aktuellste Projektstruktur sehen.

## Features

### 1. Automatischer Refresh bei veralteten Daten

Der `ContextBuilder` prüft automatisch, ob der Index aktualisiert werden muss:

```python
from project_index_manager import load_project_index

# Lädt Index mit automatischem Refresh wenn nötig
index = load_project_index(project_dir, auto_refresh=True)
```

**Refresh-Trigger:**
- Index existiert nicht
- Index ist älter als 1 Stunde
- Trigger-Dateien sind neuer als Index:
  - `package.json`
  - `requirements.txt`
  - `pyproject.toml`
  - `Cargo.toml`
  - `go.mod`
  - `supabase/config.toml`
  - `supabase/functions/*` (alle Dateien)
  - `supabase/migrations/*` (alle Dateien)

### 2. Index-Status-API

Neue API zum Abfragen des Index-Status:

```python
from project_index_manager import get_index_status

status = get_index_status(project_dir)
# {
#   "exists": true,
#   "age_seconds": 1234.56,
#   "age_human": "20m",
#   "is_stale": false,
#   "changed_files": []
# }
```

### 3. Git Hook für automatische Updates

Ein `post-merge` Hook aktualisiert den Index automatisch nach `git pull`:

```bash
# Installation
git config core.hooksPath apps/backend/.githooks
chmod +x apps/backend/.githooks/post-merge
```

Der Hook läuft nur, wenn relevante Dateien im Merge geändert wurden.

### 4. IPC-Handler für Frontend

Neuer IPC-Channel `CONTEXT_INDEX_STATUS` zum Abfragen des Status:

```typescript
const result = await window.electronAPI.getIndexStatus(projectId);
// {
#   success: true,
#   data: {
#     exists: true,
#     age_seconds: 1234.56,
#     age_human: "20m",
#     is_stale: false,
#     changed_files: []
#   }
# }
```

## Verwendung

### Backend (Python)

```python
from project_index_manager import (
    load_project_index,
    should_refresh_index,
    refresh_project_index,
    get_index_status
)

# Auto-Refresh beim Laden
index = load_project_index(project_dir, auto_refresh=True)

# Manuell prüfen
if should_refresh_index(project_dir):
    refresh_project_index(project_dir)

# Status abfragen
status = get_index_status(project_dir)
```

### Frontend (TypeScript)

```typescript
// Status abfragen
const status = await window.electronAPI.getIndexStatus(projectId);

// Manueller Refresh
const newIndex = await window.electronAPI.refreshProjectIndex(projectId);
```

## Vorteile

1. **Immer aktuell**: Agenten sehen neue Edge Functions, Migrations, Dependencies
2. **Automatisch**: Kein manuelles Refresh nötig nach `git pull`
3. **Performant**: Nur Refresh wenn wirklich nötig (max. 1x pro Stunde)
4. **Transparent**: Status-API zeigt genau, was sich geändert hat

## Beispiel: Neue Supabase Edge Function

```bash
# 1. Neue Function erstellen
mkdir supabase/functions/new-function
echo "export default () => 'Hello'" > supabase/functions/new-function/index.ts

# 2. Git commit & push
git add supabase/functions/new-function
git commit -m "Add new-function"
git push

# 3. Anderer Entwickler pullt
git pull  # → post-merge Hook läuft automatisch

# 4. Index ist aktualisiert
# Nächster Agent-Task sieht "new-function" in der Liste
```

## Migration

### Bestehende Projekte

Keine Änderungen nötig! Der Auto-Refresh ist abwärtskompatibel:
- Bestehende Indizes werden weiterhin geladen
- Refresh läuft nur wenn nötig
- Fallback auf manuelle Regeneration bleibt erhalten

### Git Hooks aktivieren (optional)

```bash
# Im Projekt-Root
git config core.hooksPath apps/backend/.githooks

# Unix/macOS/Linux
chmod +x apps/backend/.githooks/post-merge
```

## Troubleshooting

### Index wird nicht aktualisiert

```python
# Status prüfen
from project_index_manager import get_index_status
status = get_index_status(project_dir)
print(status)

# Manuell forcieren
from project_index_manager import refresh_project_index
refresh_project_index(project_dir)
```

### Git Hook läuft nicht

```bash
# Hook-Pfad prüfen
git config core.hooksPath

# Hook ausführbar machen
chmod +x apps/backend/.githooks/post-merge

# Manuell testen
./apps/backend/.githooks/post-merge
```

## Implementierung

- **Backend**: `apps/backend/project_index_manager.py`
- **Context Builder**: `apps/backend/context/builder.py`
- **IPC Handler**: `apps/frontend/src/main/ipc-handlers/context/project-context-handlers.ts`
- **Git Hook**: `apps/backend/.githooks/post-merge`

