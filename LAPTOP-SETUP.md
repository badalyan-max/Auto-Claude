# 💻 Auto-Claude Setup für deinen Laptop

## 🎯 Schnellstart (5 Minuten)

### 1️⃣ **Repository klonen**

```bash
# Klone dein Fork (mit deinen Kanban-Daten)
git clone https://github.com/badalyan-max/Auto-Claude.git
cd Auto-Claude

# Wechsle zum develop Branch
git checkout develop
```

### 2️⃣ **Kanban-Daten holen**

```powershell
# Hole deine Kanban-Daten vom PC
.\sync-kanban-data.ps1 pull
```

### 3️⃣ **Dependencies installieren**

```bash
# Backend
cd apps/backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 4️⃣ **Auto-Claude starten**

```bash
npm run start
```

## ✅ Das war's! 🎉

Du hast jetzt:
- ✅ Den gleichen Code wie auf deinem PC
- ✅ Das gleiche Kanban-Board
- ✅ Alle Tasks und Specifications
- ✅ Die Sync-Skripte

---

## 🔄 Täglicher Workflow

### **Morgens (bevor du arbeitest):**

```powershell
# Hole neueste Code-Updates
git pull origin develop

# Hole neueste Kanban-Daten
.\sync-kanban-data.ps1 pull
```

### **Abends (nach der Arbeit):**

```powershell
# Pushe Code-Änderungen
git add .
git commit -m "deine nachricht"
git push origin develop

# Pushe Kanban-Daten
.\sync-kanban-data.ps1 push
```

---

## 📋 Sync-Befehle Übersicht

```powershell
# Status prüfen
.\sync-kanban-data.ps1 status

# Daten vom PC holen
.\sync-kanban-data.ps1 pull

# Daten zum PC senden
.\sync-kanban-data.ps1 push
```

---

## 🆘 Troubleshooting

### **Fehler: "data-sync branch not found"**
```powershell
# Hole alle Branches
git fetch origin
git checkout data-sync
git checkout develop
.\sync-kanban-data.ps1 pull
```

### **Fehler: "Merge conflict"**
```powershell
# Falls beide Geräte gleichzeitig genutzt wurden
# Auf dem Gerät mit den NEUEREN Daten:
.\sync-kanban-data.ps1 push

# Auf dem anderen Gerät:
git fetch origin data-sync
git checkout data-sync
git reset --hard origin/data-sync
git checkout develop
```

### **"Ich sehe keine Kanban-Daten"**
```powershell
# Prüfe, ob .auto-claude existiert
ls .auto-claude

# Falls nicht:
.\sync-kanban-data.ps1 pull
```

---

## 🔐 Upstream Updates holen (vom Original-Repo)

```bash
# Einmalig: Upstream konfigurieren (falls nicht vorhanden)
git remote add upstream https://github.com/AndyMik90/auto-claude.git

# Regelmäßig: Updates holen
git fetch upstream
git checkout develop
git merge upstream/develop
git push origin develop
```

---

## 📊 Technische Details

### **Branch-Struktur**

```
origin (dein Fork: github.com/badalyan-max/Auto-Claude)
├── develop      ← Code + Sync-Skripte
└── data-sync    ← Kanban-Daten (.auto-claude/)

upstream (Original: github.com/AndyMik90/auto-claude)
└── develop      ← Neueste Features
```

### **Welcher Branch für was?**

| Branch | Inhalt | Sync-Methode |
|--------|--------|--------------|
| `develop` | Code, Scripts | `git pull/push` |
| `data-sync` | Kanban-Daten | `.\sync-kanban-data.ps1` |

---

## 💡 Pro-Tipps

1. **Immer zuerst pullen!**
   - Bevor du arbeitest → `pull`
   - Verhindert Konflikte

2. **Status prüfen bei Unsicherheit**
   ```powershell
   .\sync-kanban-data.ps1 status
   git status
   ```

3. **Backup vor großen Änderungen**
   ```powershell
   # Erstelle Backup
   Copy-Item .auto-claude .auto-claude-backup -Recurse
   ```

4. **Beide Branches getrennt halten**
   - Code → `develop`
   - Daten → `data-sync`
   - Niemals mischen!

---

## 🎯 Checkliste

- [ ] Repository geklont
- [ ] Dependencies installiert (Backend + Frontend)
- [ ] Kanban-Daten gepullt (`.\sync-kanban-data.ps1 pull`)
- [ ] Auto-Claude gestartet (`npm run start`)
- [ ] Kanban-Board sichtbar (sollte identisch zum PC sein)
- [ ] Sync-Test: Erstelle eine Test-Task, pushe sie, und pull auf dem PC

---

## ❓ Fragen?

Siehe auch:
- 📖 [KANBAN-SYNC-ANLEITUNG.md](./KANBAN-SYNC-ANLEITUNG.md) - Ausführliche Sync-Dokumentation
- 🔧 [sync-kanban-data.ps1](./sync-kanban-data.ps1) - Das Sync-Skript

Viel Erfolg auf dem Laptop! 🚀
