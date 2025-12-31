#!/usr/bin/env python3
"""
Auto-Sync für Auto-Claude App
==============================

Überwacht das App-Verzeichnis auf Änderungen und synchronisiert automatisch
zu deinem GitHub Fork.

Features:
- Automatische Git Commits bei Änderungen
- Automatisches Push zum Fork
- Intelligentes Filtern (keine node_modules, build artifacts, etc.)
- Läuft im Hintergrund
- Status-Anzeige
"""

import os
import sys
import time
import subprocess
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Set, Dict, Optional
import logging

# Pfade
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
STATE_FILE = PROJECT_ROOT / ".auto-sync-state.json"
LOG_FILE = PROJECT_ROOT / ".auto-sync.log"

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Farben für Konsole
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


# Verzeichnisse und Dateien die IGNORIERT werden
IGNORED_PATTERNS = {
    # Build & Dependencies
    "node_modules",
    "dist",
    "out",
    ".venv",
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    
    # Auto-Claude Projektdaten (werden separat behandelt)
    ".auto-claude",
    ".worktrees",
    
    # Git
    ".git",
    
    # Temp & Logs
    "*.log",
    ".auto-sync-state.json",
    ".auto-sync.log",
    
    # IDE
    ".idea",
    ".vscode",
    "*.swp",
    "*.swo",
    
    # OS
    ".DS_Store",
    "Thumbs.db",
    
    # Python Runtime
    "python-runtime",
}


def run_git_command(cmd: list, cwd: Path = PROJECT_ROOT) -> tuple[bool, str]:
    """Führt Git-Befehl aus und gibt Erfolg + Output zurück."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def get_git_status() -> Optional[str]:
    """Holt Git Status (nur geänderte Dateien)."""
    success, output = run_git_command(["git", "status", "--short"])
    if success:
        return output.strip()
    return None


def has_changes() -> bool:
    """Prüft ob es Git-Änderungen gibt."""
    status = get_git_status()
    return bool(status)


def get_changed_files() -> Set[str]:
    """Gibt Liste der geänderten Dateien zurück."""
    status = get_git_status()
    if not status:
        return set()
    
    files = set()
    for line in status.split('\n'):
        if not line.strip():
            continue
        # Format: " M file.py" oder "?? file.py"
        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2:
            files.add(parts[1])
    
    return files


def should_ignore_file(filepath: str) -> bool:
    """Prüft ob Datei ignoriert werden soll."""
    path = Path(filepath)
    
    # Prüfe jedes Pattern
    for pattern in IGNORED_PATTERNS:
        if pattern.startswith("*."):
            # Dateiendung
            if path.suffix == pattern[1:]:
                return True
        else:
            # Verzeichnis oder Dateiname
            if pattern in path.parts or path.name == pattern:
                return True
    
    return False


def filter_relevant_changes(files: Set[str]) -> Set[str]:
    """Filtert nur relevante App-Änderungen (keine node_modules etc.)."""
    return {f for f in files if not should_ignore_file(f)}


def create_smart_commit_message(files: Set[str]) -> str:
    """Erstellt intelligente Commit-Nachricht basierend auf Dateien."""
    if not files:
        return "chore: Auto-Sync Änderungen"
    
    # Analysiere Dateitypen
    has_backend = any("apps/backend" in f for f in files)
    has_frontend = any("apps/frontend" in f for f in files)
    has_docs = any(f.endswith(".md") for f in files)
    has_scripts = any("scripts/" in f or f.endswith(".ps1") or f.endswith(".bat") for f in files)
    has_config = any(f in ["package.json", ".env", "requirements.txt"] for f in files)
    
    # Bestimme Typ
    if has_backend and has_frontend:
        prefix = "feat"
        scope = "app"
    elif has_backend:
        prefix = "feat"
        scope = "backend"
    elif has_frontend:
        prefix = "feat"
        scope = "frontend"
    elif has_docs:
        prefix = "docs"
        scope = ""
    elif has_scripts:
        prefix = "chore"
        scope = "scripts"
    elif has_config:
        prefix = "chore"
        scope = "config"
    else:
        prefix = "chore"
        scope = ""
    
    # Erstelle Nachricht
    scope_str = f"({scope})" if scope else ""
    
    # Füge Dateiliste hinzu (max 3)
    file_list = sorted(list(files))[:3]
    files_str = ", ".join(Path(f).name for f in file_list)
    if len(files) > 3:
        files_str += f", +{len(files) - 3} weitere"
    
    timestamp = datetime.now().strftime("%H:%M")
    
    return f"{prefix}{scope_str}: Auto-Sync [{timestamp}] - {files_str}"


def commit_and_push() -> bool:
    """Committed Änderungen und pushed zum Fork."""
    
    # 1. Hole geänderte Dateien
    all_files = get_changed_files()
    if not all_files:
        logger.debug("Keine Änderungen gefunden")
        return False
    
    # 2. Filtere relevante Änderungen
    relevant_files = filter_relevant_changes(all_files)
    if not relevant_files:
        logger.debug(f"Alle {len(all_files)} Änderungen gefiltert (node_modules, etc.)")
        return False
    
    logger.info(f"{Colors.CYAN}📝 {len(relevant_files)} Änderungen gefunden{Colors.RESET}")
    for file in sorted(list(relevant_files)[:5]):  # Zeige max 5
        logger.info(f"   - {file}")
    if len(relevant_files) > 5:
        logger.info(f"   ... und {len(relevant_files) - 5} weitere")
    
    # 3. Add Dateien
    success, output = run_git_command(["git", "add", "-A"])
    if not success:
        logger.error(f"{Colors.RED}❌ Git add fehlgeschlagen: {output}{Colors.RESET}")
        return False
    
    # 4. Commit mit intelligenter Nachricht
    commit_msg = create_smart_commit_message(relevant_files)
    success, output = run_git_command(["git", "commit", "-m", commit_msg])
    if not success:
        if "nothing to commit" in output.lower():
            logger.debug("Nichts zu committen")
            return False
        logger.error(f"{Colors.RED}❌ Git commit fehlgeschlagen: {output}{Colors.RESET}")
        return False
    
    logger.info(f"{Colors.GREEN}✅ Committed: {commit_msg}{Colors.RESET}")
    
    # 5. Push zum Fork
    logger.info(f"{Colors.CYAN}⬆️  Pushe zu deinem Fork...{Colors.RESET}")
    success, output = run_git_command(["git", "push", "origin", "develop"])
    if not success:
        logger.error(f"{Colors.RED}❌ Git push fehlgeschlagen: {output}{Colors.RESET}")
        logger.info(f"{Colors.YELLOW}💡 Tipp: Prüfe deine GitHub-Authentifizierung{Colors.RESET}")
        return False
    
    logger.info(f"{Colors.GREEN}✅ Push erfolgreich! Änderungen in deinem Fork gespeichert{Colors.RESET}")
    return True


def load_state() -> Dict:
    """Lädt State aus Datei."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {
        "last_sync": None,
        "total_syncs": 0,
        "last_files": []
    }


def save_state(state: Dict):
    """Speichert State in Datei."""
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception as e:
        logger.warning(f"State speichern fehlgeschlagen: {e}")


def watch_and_sync(interval: int = 60):
    """Überwacht Änderungen und synchronisiert automatisch."""
    
    logger.info(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    logger.info(f"{Colors.BOLD}{Colors.CYAN}AUTO-SYNC FÜR AUTO-CLAUDE APP GESTARTET{Colors.RESET}")
    logger.info(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    logger.info("")
    logger.info(f"📂 Projekt: {PROJECT_ROOT}")
    logger.info(f"⏱️  Intervall: {interval} Sekunden")
    logger.info(f"📝 Log: {LOG_FILE}")
    logger.info(f"🔄 Fork: https://github.com/badalyan-max/Auto-Claude")
    logger.info("")
    logger.info(f"{Colors.YELLOW}Drücke Ctrl+C zum Beenden{Colors.RESET}")
    logger.info("")
    
    state = load_state()
    check_count = 0
    
    try:
        while True:
            check_count += 1
            
            # Prüfe auf Änderungen
            if has_changes():
                files = get_changed_files()
                relevant = filter_relevant_changes(files)
                
                if relevant:
                    logger.info(f"{Colors.CYAN}{'─'*60}{Colors.RESET}")
                    logger.info(f"{Colors.BOLD}🔄 Sync #{state['total_syncs'] + 1}{Colors.RESET}")
                    
                    if commit_and_push():
                        state["last_sync"] = datetime.now().isoformat()
                        state["total_syncs"] += 1
                        state["last_files"] = list(relevant)
                        save_state(state)
                        
                        logger.info(f"{Colors.GREEN}✅ Sync #{state['total_syncs']} erfolgreich!{Colors.RESET}")
                    else:
                        logger.warning(f"{Colors.YELLOW}⚠️  Sync fehlgeschlagen{Colors.RESET}")
                    
                    logger.info(f"{Colors.CYAN}{'─'*60}{Colors.RESET}")
                    logger.info("")
            else:
                if check_count % 10 == 0:  # Alle 10 Checks
                    logger.debug(f"✓ Check #{check_count} - Keine Änderungen")
            
            # Warte
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info("")
        logger.info(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        logger.info(f"{Colors.BOLD}{Colors.CYAN}AUTO-SYNC BEENDET{Colors.RESET}")
        logger.info(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        logger.info("")
        logger.info(f"📊 Statistik:")
        logger.info(f"   Gesamt-Syncs: {state['total_syncs']}")
        if state['last_sync']:
            logger.info(f"   Letzter Sync: {state['last_sync']}")
        logger.info("")
        logger.info(f"{Colors.GREEN}Alle Änderungen sind sicher in deinem Fork!{Colors.RESET}")
        logger.info(f"🔗 https://github.com/badalyan-max/Auto-Claude")
        logger.info("")


def show_status():
    """Zeigt aktuellen Status."""
    print()
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}AUTO-SYNC STATUS{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print()
    
    # State laden
    state = load_state()
    
    print(f"📊 Statistik:")
    print(f"   Gesamt-Syncs: {state['total_syncs']}")
    if state['last_sync']:
        last_sync_dt = datetime.fromisoformat(state['last_sync'])
        print(f"   Letzter Sync: {last_sync_dt.strftime('%d.%m.%Y %H:%M:%S')}")
    else:
        print(f"   Letzter Sync: Noch nie")
    print()
    
    # Aktuelle Änderungen
    if has_changes():
        files = get_changed_files()
        relevant = filter_relevant_changes(files)
        
        print(f"{Colors.YELLOW}⚠️  Ungespeicherte Änderungen: {len(relevant)}{Colors.RESET}")
        for file in sorted(list(relevant)[:10]):
            print(f"   - {file}")
        if len(relevant) > 10:
            print(f"   ... und {len(relevant) - 10} weitere")
    else:
        print(f"{Colors.GREEN}✅ Alles synchronisiert!{Colors.RESET}")
    
    print()
    print(f"🔗 Dein Fork: https://github.com/badalyan-max/Auto-Claude")
    print()


def main():
    """Hauptfunktion."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Auto-Sync für Auto-Claude App",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python app_auto_sync.py --watch              # Startet Überwachung (60s Intervall)
  python app_auto_sync.py --watch --interval 30  # 30 Sekunden Intervall
  python app_auto_sync.py --status             # Zeigt Status
  python app_auto_sync.py --sync-now           # Einmaliger Sync
        """
    )
    
    parser.add_argument("--watch", action="store_true", help="Überwache Änderungen kontinuierlich")
    parser.add_argument("--interval", type=int, default=60, help="Check-Intervall in Sekunden (default: 60)")
    parser.add_argument("--status", action="store_true", help="Zeige aktuellen Status")
    parser.add_argument("--sync-now", action="store_true", help="Synchronisiere jetzt (einmalig)")
    
    args = parser.parse_args()
    
    # Wechsle ins Projekt-Verzeichnis
    os.chdir(PROJECT_ROOT)
    
    if args.status:
        show_status()
    elif args.sync_now:
        print()
        print(f"{Colors.CYAN}🔄 Führe einmaligen Sync durch...{Colors.RESET}")
        print()
        if commit_and_push():
            print()
            print(f"{Colors.GREEN}✅ Sync erfolgreich!{Colors.RESET}")
            print()
        else:
            print()
            print(f"{Colors.YELLOW}ℹ️  Keine Änderungen zum Synchronisieren{Colors.RESET}")
            print()
    elif args.watch:
        watch_and_sync(interval=args.interval)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
