# Windows-Sicherheitseinstellungen für Claude Code anpassen

## Problem
Windows-Sicherheit blockiert einige Features von Claude Code. Diese Anleitung hilft Ihnen, die notwendigen Ausnahmen einzurichten.

## Lösung 1: Ausnahme für den Ordner hinzufügen (EMPFOHLEN)

### Schritt 1: Windows-Sicherheit öffnen
1. Drücken Sie `Windows-Taste + I` um die Einstellungen zu öffnen
2. Navigieren Sie zu **Datenschutz und Sicherheit** → **Windows-Sicherheit**
3. Klicken Sie auf **Viren- und Bedrohungsschutz**

### Schritt 2: Ausnahme hinzufügen
1. Scrollen Sie nach unten zu **Einstellungen für Viren- und Bedrohungsschutz**
2. Klicken Sie auf **Einstellungen verwalten**
3. Scrollen Sie nach unten zu **Ausschlüsse**
4. Klicken Sie auf **Ausschlüsse hinzufügen oder entfernen**
5. Klicken Sie auf **+ Ausschluss hinzufügen**
6. Wählen Sie **Ordner** aus
7. Navigieren Sie zu: `C:\Projekte\auto-claude`
8. Klicken Sie auf **Ordner auswählen**

### Schritt 3: Zusätzliche Ausnahmen (optional, aber empfohlen)
Fügen Sie auch diese Ordner als Ausnahmen hinzu:
- `C:\Projekte\auto-claude\apps\backend`
- `C:\Projekte\auto-claude\apps\frontend`
- Den Ordner, in dem die kompilierte .exe liegt (normalerweise in `apps\frontend\out` oder `dist`)

## Lösung 2: Kontrollierten Ordnerzugriff anpassen

Wenn der "Kontrollierte Ordnerzugriff" aktiviert ist:

1. Öffnen Sie **Windows-Sicherheit** (siehe oben)
2. Gehen Sie zu **Viren- und Bedrohungsschutz**
3. Klicken Sie auf **Ransomware-Schutz verwalten**
4. Unter **Kontrollierter Ordnerzugriff** klicken Sie auf **App durch kontrollierten Ordnerzugriff zulassen**
5. Klicken Sie auf **+ Zulässige App hinzufügen**
6. Navigieren Sie zur ausführbaren Datei Ihrer Claude Code App
7. Fügen Sie folgende Programme hinzu:
   - Die Electron-App (.exe)
   - Python-Interpreter (falls vorhanden im Projekt)

## Lösung 3: SmartScreen-Einstellungen anpassen

Für nicht signierte Electron-Apps:

1. Öffnen Sie **Windows-Sicherheit**
2. Gehen Sie zu **App- und Browsersteuerung**
3. Klicken Sie auf **Einstellungen für zuverlässigkeitsbasierten Schutz**
4. Sie können folgende Optionen auf **Aus** oder **Warnen** setzen:
   - Apps und Dateien überprüfen
   - SmartScreen für Microsoft Edge
   - SmartScreen für Microsoft Store-Apps

**WARNUNG**: Das Deaktivieren von SmartScreen reduziert Ihre Sicherheit. Tun Sie dies nur für vertrauenswürdige Anwendungen.

## Lösung 4: PowerShell-Skript für schnelle Konfiguration

Führen Sie PowerShell als **Administrator** aus und führen Sie folgende Befehle aus:

```powershell
# Füge Ordner als Defender-Ausnahme hinzu
Add-MpPreference -ExclusionPath "C:\Projekte\auto-claude"

# Überprüfen Sie, ob die Ausnahme hinzugefügt wurde
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
```

## Lösung 5: Echtzeit-Schutz vorübergehend deaktivieren (NUR ZUM TESTEN)

**WARNUNG**: Dies sollte nur vorübergehend zum Testen verwendet werden!

1. Öffnen Sie **Windows-Sicherheit**
2. Gehen Sie zu **Viren- und Bedrohungsschutz**
3. Klicken Sie auf **Einstellungen verwalten**
4. Schalten Sie **Echtzeitschutz** vorübergehend AUS
5. Testen Sie die App
6. Schalten Sie den Echtzeitschutz wieder EIN

## Nach der Konfiguration

1. Starten Sie Ihre Claude Code Anwendung neu
2. Testen Sie, ob alle Features funktionieren
3. Überprüfen Sie die Windows-Sicherheit-Benachrichtigungen

## Häufige Probleme

### Problem: "Diese App wurde aus Sicherheitsgründen blockiert"
**Lösung**: Führen Sie Lösung 3 (SmartScreen) aus oder signieren Sie Ihre Electron-App mit einem Code-Signing-Zertifikat.

### Problem: Python-Prozesse werden blockiert
**Lösung**: Fügen Sie den Python-Interpreter als Ausnahme hinzu:
- `C:\Projekte\auto-claude\apps\backend\venv\Scripts\python.exe`
- Oder wo immer Ihr Python installiert ist

### Problem: Node.js/Electron-Prozesse werden blockiert
**Lösung**: Fügen Sie diese als Ausnahmen hinzu:
- `C:\Projekte\auto-claude\apps\frontend\node_modules\.bin\`

## Sicherheitshinweise

⚠️ **Wichtig**: 
- Fügen Sie nur Ausnahmen für Anwendungen hinzu, denen Sie vertrauen
- Deaktivieren Sie nie dauerhaft den Echtzeitschutz
- Überprüfen Sie regelmäßig Ihre Ausnahmen
- Ziehen Sie in Betracht, Ihre Anwendung mit einem Code-Signing-Zertifikat zu signieren

## Alternative: Anwendung signieren

Für eine dauerhafte Lösung ohne Sicherheitsausnahmen:

1. Erwerben Sie ein Code-Signing-Zertifikat
2. Signieren Sie Ihre Electron-App
3. Windows wird die Anwendung dann automatisch als vertrauenswürdig erkennen

Weitere Informationen: https://www.electronjs.org/docs/latest/tutorial/code-signing

---

**Haben Sie weitere Fragen?** Zögern Sie nicht zu fragen!

