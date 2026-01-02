# 📋 Kanban Data Synchronization - Anleitung

## 🎯 Überblick

Dieses System ermöglicht es dir, deine Kanban-Board-Daten zwischen verschiedenen Geräten (PC, Laptop) über Git zu synchronisieren.

## 🔧 Funktionsweise

- **Separater Branch**: Alle Kanban-Daten werden in einem separaten `data-sync` Branch gespeichert
- **Code bleibt sauber**: Dein `develop` Branch enthält KEINEN Kanban-Daten
- **Einfache Synchronisation**: Einfache PowerShell-Befehle zum Push/Pull

## 📦 Was wird synchronisiert?

Das gesamte `.auto-claude/` Verzeichnis:
- ✅ Kanban Board Tasks
- ✅ Specifications
- ✅ Insights & Sessions
- ✅ Terminal-Konfigurationen
- ✅ Alle anderen Projekt-Daten

## 🚀 Verwendung

### 1️⃣ **Daten zu GitHub pushen** (vom PC)

```powershell
.\sync-kanban-data.ps1 push
```

**Wann?** Nach Änderungen am Kanban-Board, die du auf dem Laptop haben möchtest.

### 2️⃣ **Daten von GitHub pullen** (auf dem Laptop)

```powershell
.\sync-kanban-data.ps1 pull
```

**Wann?** Bevor du auf dem Laptop arbeitest, um die neuesten Daten zu erhalten.

### 3️⃣ **Status prüfen**

```powershell
.\sync-kanban-data.ps1 status
```

**Zeigt:**
- Ob lokale Daten existieren
- Wann der letzte Sync war
- Größe der Daten

## 📋 Workflow-Beispiel

### **Auf dem PC:**

```powershell
# 1. Arbeite normal mit Auto-Claude
# 2. Kanban-Board aktualisiert sich automatisch
# 3. Am Ende des Arbeitstages:
.\sync-kanban-data.ps1 push
```

### **Auf dem Laptop:**

```powershell
# 1. Bevor du arbeitest:
.\sync-kanban-data.ps1 pull

# 2. Arbeite normal mit Auto-Claude
# 3. Am Ende:
.\sync-kanban-data.ps1 push
```

## ⚠️ Wichtige Hinweise

### **Konflikte vermeiden**

- ✅ **Immer zuerst pullen** bevor du arbeitest
- ✅ **Pushe regelmäßig** deine Änderungen
- ⚠️ Arbeite **nicht gleichzeitig** auf beiden Geräten

### **Bei Konflikten**

Falls du trotzdem Konflikte bekommst:

```powershell
# Auf dem Gerät mit den NEUEREN Daten:
.\sync-kanban-data.ps1 push --force

# Auf dem anderen Gerät:
.\sync-kanban-data.ps1 pull
```

## 🔐 Sicherheit

- ✅ Daten sind in deinem **privaten Fork**
- ✅ Separater Branch - nicht im Haupt-Code
- ✅ Nur du hast Zugriff

## 🛠️ Setup auf neuem Gerät

1. **Auto-Claude klonen:**
   ```bash
   git clone https://github.com/badalyan-max/Auto-Claude.git
   cd Auto-Claude
   git checkout develop
   ```

2. **Kanban-Daten holen:**
   ```powershell
   .\sync-kanban-data.ps1 pull
   ```

3. **Fertig!** 🎉

## 📊 Technische Details

### **Branch-Struktur**

```
develop          ← Dein Code (ohne .auto-claude/)
└── data-sync    ← Deine Kanban-Daten (mit .auto-claude/)
```

### **Was passiert beim Push?**

1. Wechselt zu `data-sync` Branch
2. Entfernt temporär `.auto-claude/` aus `.gitignore`
3. Committed die Daten
4. Pusht zu GitHub
5. Stellt `.gitignore` wieder her
6. Wechselt zurück zu `develop`

### **Was passiert beim Pull?**

1. Fetched `data-sync` Branch
2. Wechselt zu `data-sync` Branch
3. Pulled die neuesten Daten
4. Wechselt zurück zu `develop`
5. Daten sind nun in `.auto-claude/` verfügbar

## ❓ FAQ

**Q: Kann ich die Daten auch manuell syncen?**
A: Ja, aber das Skript macht es einfacher und verhindert Fehler.

**Q: Was ist, wenn ich das Skript auf einem Gerät vergesse?**
A: Kein Problem! Beim nächsten Pull bekommst du die neuesten Daten.

**Q: Werden meine Code-Änderungen auch synchronisiert?**
A: Nein, nur die Kanban-Daten. Code-Updates machst du wie gewohnt mit `git push/pull` auf dem `develop` Branch.

**Q: Kann ich beide Branches gleichzeitig pushen?**
A: Ja! Code und Daten sind unabhängig:
```powershell
git push origin develop          # Code
.\sync-kanban-data.ps1 push      # Daten
```

## 🎯 Best Practices

1. **Tägliche Routine:**
   - Morgens: `pull` (Daten holen)
   - Abends: `push` (Daten sichern)

2. **Vor wichtigen Sessions:**
   - Immer zuerst `pull`
   - Dann arbeiten
   - Danach `push`

3. **Status prüfen:**
   - Unsicher? → `.\sync-kanban-data.ps1 status`

## 🚀 Los geht's!

Probiere es jetzt aus:

```powershell
# Status prüfen
.\sync-kanban-data.ps1 status

# Erste Synchronisation
.\sync-kanban-data.ps1 push
```

Viel Erfolg! 🎉
