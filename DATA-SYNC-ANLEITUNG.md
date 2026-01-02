# 🔄 Auto-Claude Data Synchronisation

## Übersicht

Deine Auto-Claude Kanban-Daten werden über einen separaten Git-Branch `data-sync` synchronisiert.

### Was wird synchronisiert?
- ✅ Kanban Board (Tasks, Status, Prioritäten)
- ✅ Task Specs & Requirements
- ✅ Insights & Sessions
- ✅ Projekt-Index

### Was wird NICHT synchronisiert?
- ❌ Code-Änderungen (bleiben auf `develop` Branch)
- ❌ Log-Dateien
- ❌ Temporäre Build-Artefakte

---

## 🚀 Erstmalige Einrichtung auf neuem Gerät (Laptop)

### Schritt 1: Repository klonen
```bash
cd ~/Projekte
git clone https://github.com/badalyan-max/Auto-Claude.git auto-claude
cd auto-claude
```

### Schritt 2: Data-Sync Branch auschecken
```bash
git fetch origin data-sync
git checkout data-sync
```

### Schritt 3: Zurück zu develop wechseln (für normale Arbeit)
```bash
git checkout develop
```

### Schritt 4: Daten aus data-sync holen
```bash
# Kopiere .auto-claude Daten vom data-sync Branch
git checkout data-sync -- .auto-claude/
```

✅ **Fertig!** Du hast jetzt alle Kanban-Daten vom PC auf deinem Laptop.

---

## 🔄 Tägliche Synchronisation

### Auf PC: Daten zu GitHub pushen

**Manuell:**
```bash
# 1. Zu data-sync Branch wechseln
git checkout data-sync

# 2. Aktuelle .auto-claude Daten übernehmen
git add .auto-claude

# 3. Committen
git commit -m "sync: update kanban data [$(date +%Y-%m-%d)]"

# 4. Pushen
git push origin data-sync

# 5. Zurück zu develop
git checkout develop
```

**Automatisch mit Skript:**
```bash
./Data-Sync-Push.ps1
```

---

### Auf Laptop: Daten von GitHub holen

**Manuell:**
```bash
# 1. Zu data-sync Branch wechseln
git checkout data-sync

# 2. Neueste Daten holen
git pull origin data-sync

# 3. Zurück zu develop
git checkout develop

# 4. Daten kopieren
git checkout data-sync -- .auto-claude/
```

**Automatisch mit Skript:**
```bash
./Data-Sync-Pull.ps1
```

---

## ⚡ Automatisierungs-Skripte

### `Data-Sync-Push.ps1` (PC → GitHub)
Pusht deine lokalen Kanban-Daten zu GitHub.

### `Data-Sync-Pull.ps1` (GitHub → Laptop)
Holt die neuesten Kanban-Daten vom PC.

### `Data-Sync-Status.ps1`
Zeigt den Synchronisations-Status an.

---

## 🎯 Best Practices

### ✅ DO:
- Pushe Daten am Ende deiner Arbeitssession (PC)
- Hole Daten am Anfang deiner Arbeitssession (Laptop)
- Nutze die Automatisierungs-Skripte
- Führe `Data-Sync-Status.ps1` regelmäßig aus

### ❌ DON'T:
- Bearbeite Kanban-Daten auf beiden Geräten gleichzeitig
- Vergiss nicht zu pushen nach Änderungen
- Mixe Code und Daten nicht im selben Branch

---

## 🔧 Troubleshooting

### Problem: "Merge conflicts in .auto-claude/"
**Lösung:**
```bash
# Auf data-sync Branch
git checkout data-sync
git fetch origin data-sync

# Deine Version bevorzugen:
git merge origin/data-sync -X ours

# ODER Remote-Version bevorzugen:
git merge origin/data-sync -X theirs
```

### Problem: "Daten scheinen veraltet"
**Lösung:**
```bash
# Prüfe wann letzter Sync war
git log data-sync -1 --format="%ci - %s"

# Forciere Update
./Data-Sync-Pull.ps1 -Force
```

### Problem: "Branch data-sync existiert nicht"
**Lösung:**
```bash
git fetch origin data-sync:data-sync
git checkout data-sync
```

---

## 📊 Workflow-Diagramm

```
PC (Hauptarbeit)          GitHub              Laptop (Unterwegs)
─────────────────         ──────              ──────────────────
      │                      │                        │
  [Arbeite]                  │                        │
      │                      │                        │
  [Pushe Daten] ────────────►│                        │
      │              (data-sync branch)                │
      │                      │                        │
      │                      │◄─────── [Hole Daten]   │
      │                      │                        │
      │                      │                   [Arbeite]
      │                      │                        │
      │                      │◄─────── [Pushe Daten]  │
      │                      │                        │
  [Hole Daten] ◄─────────────│                        │
      │                      │                        │
```

---

## 🎓 Erweiterte Tipps

### Automatischer Sync beim Start
Füge zu deiner PowerShell-Profile hinzu (`$PROFILE`):
```powershell
# Auto-Claude Data Sync beim Terminal-Start
if (Test-Path "C:\Projekte\auto-claude") {
    cd C:\Projekte\auto-claude
    .\Data-Sync-Status.ps1
}
```

### Sync vor dem Herunterfahren
Erstelle eine geplante Aufgabe (Task Scheduler), die beim Herunterfahren läuft:
```powershell
# Trigger: System shutdown
# Action: PowerShell.exe -File "C:\Projekte\auto-claude\Data-Sync-Push.ps1"
```

---

## 📝 Hinweise

- Die `.gitignore` ist auf dem `develop` Branch so konfiguriert, dass `.auto-claude/` ignoriert wird
- Auf dem `data-sync` Branch ist `.auto-claude/` NICHT ignoriert
- Code-Änderungen bleiben auf `develop` und werden normal committed
- Daten-Änderungen werden nur auf `data-sync` committed

**Fragen?** Siehe [PROBLEMLÖSUNGEN.md](PROBLEMLÖSUNGEN.md) oder frag Claude! 🤖
