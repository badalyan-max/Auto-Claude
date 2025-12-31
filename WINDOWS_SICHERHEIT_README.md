# 🛡️ Windows-Sicherheit für Claude Code konfigurieren

## 🚀 Schnellstart (EMPFOHLEN)

**Einfachste Methode:**
1. Doppelklicken Sie auf `Windows-Sicherheit-Konfigurieren.bat`
2. Bestätigen Sie die UAC-Administratorabfrage
3. Folgen Sie den Anweisungen im PowerShell-Fenster
4. Starten Sie Claude Code neu

Das war's! ✅

---

## 📋 Verfügbare Dateien

### 1. `Windows-Sicherheit-Konfigurieren.bat` ⭐
- **Eine-Klick-Lösung**
- Führt das PowerShell-Skript automatisch als Administrator aus
- **EMPFOHLEN für die meisten Benutzer**

### 2. `configure-windows-security.ps1`
- PowerShell-Skript für automatische Konfiguration
- Fügt Windows Defender-Ausnahmen hinzu
- Zeigt aktuelle Ausnahmen an
- Kann auch manuell als Administrator ausgeführt werden

### 3. `WINDOWS_SICHERHEIT_ANLEITUNG.md`
- Detaillierte Schritt-für-Schritt-Anleitung
- Manuelle Konfigurationsoptionen
- Problemlösungen
- Zusätzliche Sicherheitshinweise

---

## 🎯 Was wird konfiguriert?

Das Skript fügt folgende Ordner als Windows Defender-Ausnahmen hinzu:

- ✅ `C:\Projekte\auto-claude` (Hauptprojekt)
- ✅ `C:\Projekte\auto-claude\apps\backend` (Backend)
- ✅ `C:\Projekte\auto-claude\apps\frontend` (Frontend)
- ✅ Python-Umgebungen (falls vorhanden)
- ✅ Node-Modules (falls vorhanden)

---

## ❓ Häufige Fragen

### Warum blockiert Windows meine App?
Windows-Sicherheit kann nicht signierte Electron-Apps als potenzielle Bedrohung einstufen, besonders wenn sie:
- Python-Prozesse starten
- Dateisystemzugriff benötigen
- Netzwerkverbindungen herstellen

### Ist das sicher?
Ja, wenn Sie dem Code vertrauen! Die Skripte fügen nur Ausnahmen für Ihren Projektordner hinzu. Sie deaktivieren NICHT den Windows Defender komplett.

### Funktioniert das Skript nicht?
Siehe `WINDOWS_SICHERHEIT_ANLEITUNG.md` für manuelle Konfigurationsschritte.

### Muss ich das nach jedem Windows-Update wiederholen?
Normalerweise NEIN. Die Ausnahmen bleiben bestehen. Bei größeren Windows-Updates sollten Sie sie jedoch überprüfen.

---

## 🔒 Sicherheitshinweise

⚠️ **Wichtig:**
- Diese Skripte benötigen Administratorrechte
- Fügen Sie nur Ausnahmen für vertrauenswürdige Software hinzu
- Überprüfen Sie regelmäßig Ihre Defender-Ausnahmen
- Deaktivieren Sie niemals dauerhaft den Echtzeitschutz

---

## 🐛 Probleme?

1. Lesen Sie `WINDOWS_SICHERHEIT_ANLEITUNG.md` für detaillierte Lösungen
2. Überprüfen Sie, ob das Skript als Administrator ausgeführt wurde
3. Prüfen Sie die PowerShell-Ausgabe auf Fehlermeldungen
4. Starten Sie Windows nach der Konfiguration neu (falls nötig)

---

## 📞 Weitere Hilfe

Wenn Sie weiterhin Probleme haben:
1. Öffnen Sie Windows-Sicherheit manuell
2. Prüfen Sie unter "Viren- und Bedrohungsschutz" → "Ausschlüsse"
3. Prüfen Sie "App- und Browsersteuerung" → SmartScreen-Einstellungen
4. Prüfen Sie "Ransomware-Schutz" → Kontrollierter Ordnerzugriff

---

**Viel Erfolg! 🎉**

