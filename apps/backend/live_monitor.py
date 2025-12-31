#!/usr/bin/env python3
"""
Auto Claude Live Terminal Monitor
==================================

Überwacht Auto Claude Prozesse und Logs in Echtzeit und identifiziert Fehler.

Usage:
    python live_monitor.py
    python live_monitor.py --spec 001
    python live_monitor.py --follow-logs
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Thread
from typing import Optional

# Colors for terminal output
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class LogAnalyzer:
    """Analysiert Log-Zeilen und identifiziert Fehler."""
    
    # Fehler-Patterns
    ERROR_PATTERNS = [
        (r"ERROR", "error"),
        (r"FAILED", "error"),
        (r"Exception", "error"),
        (r"Traceback", "error"),
        (r"CRITICAL", "critical"),
        (r"WARN(?:ING)?", "warning"),
        (r"Timeout", "warning"),
        (r"Retrying", "warning"),
        (r"deprecated", "info"),
        (r"SUCCESS", "success"),
        (r"COMPLETE", "success"),
    ]
    
    # Kritische Fehler (erfordern sofortige Aufmerksamkeit)
    CRITICAL_PATTERNS = [
        r"ModuleNotFoundError",
        r"ImportError",
        r"SyntaxError",
        r"MemoryError",
        r"ConnectionError",
        r"TimeoutError",
        r"PermissionError",
        r"FileNotFoundError",
    ]
    
    def analyze(self, line: str) -> dict:
        """Analysiert eine Log-Zeile."""
        result = {
            "line": line,
            "level": "info",
            "is_error": False,
            "is_critical": False,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Check für Fehler-Level
        for pattern, level in self.ERROR_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                result["level"] = level
                result["is_error"] = level in ("error", "critical", "warning")
                break
        
        # Check für kritische Fehler
        for pattern in self.CRITICAL_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                result["is_critical"] = True
                result["level"] = "critical"
                result["is_error"] = True
                break
        
        return result


class ProcessMonitor:
    """Überwacht laufende Auto Claude Prozesse."""
    
    def __init__(self):
        self.running_processes = []
    
    def find_auto_claude_processes(self):
        """Findet alle laufenden Auto Claude Prozesse."""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
                    capture_output=True,
                    text=True,
                    encoding='cp1252',  # Windows encoding
                )
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                
                processes = []
                for line in lines:
                    if "auto-claude" in line.lower() or "run.py" in line.lower():
                        parts = line.split('","')
                        if len(parts) >= 2:
                            pid = parts[1].strip('"')
                            processes.append({
                                "pid": pid,
                                "name": parts[0].strip('"'),
                            })
                
                return processes
            else:
                # Linux/macOS
                result = subprocess.run(
                    ["ps", "aux"],
                    capture_output=True,
                    text=True,
                )
                processes = []
                for line in result.stdout.split("\n"):
                    if "auto-claude" in line.lower() or "run.py" in line.lower():
                        parts = line.split()
                        if len(parts) >= 2:
                            processes.append({
                                "pid": parts[1],
                                "name": " ".join(parts[10:]),
                            })
                
                return processes
        
        except Exception as e:
            print(f"{Colors.YELLOW}[WARN] Fehler beim Suchen nach Prozessen: {e}{Colors.RESET}")
            return []
    
    def get_status(self):
        """Gibt den Status aller Prozesse zurück."""
        processes = self.find_auto_claude_processes()
        return {
            "timestamp": datetime.now().isoformat(),
            "process_count": len(processes),
            "processes": processes,
        }


class LogFollower:
    """Folgt Log-Dateien in Echtzeit (wie tail -f)."""
    
    def __init__(self, log_path: Path, analyzer: LogAnalyzer, source_name: str = None):
        self.log_path = log_path
        self.analyzer = analyzer
        self.source_name = source_name or log_path.name
        self.running = False
        self.error_count = 0
        self.warning_count = 0
        self.critical_count = 0
    
    def follow(self):
        """Folgt der Log-Datei in Echtzeit."""
        self.running = True
        
        try:
            with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                # Gehe zum Ende der Datei
                f.seek(0, 2)
                
                print(f"{Colors.CYAN}[INFO] Folge Log-Datei: {self.log_path}{Colors.RESET}")
                print(f"{Colors.CYAN}[INFO] Drücken Sie Ctrl+C zum Beenden{Colors.RESET}")
                print()
                
                while self.running:
                    line = f.readline()
                    if line:
                        self._process_line(line)
                    else:
                        time.sleep(0.1)  # Warte kurz wenn keine neuen Zeilen
        
        except FileNotFoundError:
            print(f"{Colors.RED}[ERROR] Log-Datei nicht gefunden: {self.log_path}{Colors.RESET}")
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}[INFO] Monitoring beendet{Colors.RESET}")
        finally:
            self.running = False
            self._print_summary()
    
    def _process_line(self, line: str):
        """Verarbeitet eine einzelne Log-Zeile."""
        line = line.rstrip()
        if not line:
            return
        
        result = self.analyzer.analyze(line)
        
        # Zähle Fehler
        if result["is_critical"]:
            self.critical_count += 1
        elif result["level"] == "error":
            self.error_count += 1
        elif result["level"] == "warning":
            self.warning_count += 1
        
        # Prefix mit Source-Name
        prefix = f"{Colors.MAGENTA}[{self.source_name}]{Colors.RESET} "
        
        # Formatiere Ausgabe basierend auf Level
        if result["is_critical"]:
            print(f"{prefix}{Colors.RED}{Colors.BOLD}[CRITICAL] {line}{Colors.RESET}")
        elif result["level"] == "error":
            print(f"{prefix}{Colors.RED}[ERROR] {line}{Colors.RESET}")
        elif result["level"] == "warning":
            print(f"{prefix}{Colors.YELLOW}[WARN] {line}{Colors.RESET}")
        elif result["level"] == "success":
            print(f"{prefix}{Colors.GREEN}[OK] {line}{Colors.RESET}")
        else:
            print(f"{prefix}{Colors.RESET}{line}{Colors.RESET}")
    
    def _print_summary(self):
        """Gibt eine Zusammenfassung aus."""
        print()
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}Monitoring Zusammenfassung:{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.RED}Kritische Fehler: {self.critical_count}{Colors.RESET}")
        print(f"{Colors.RED}Fehler: {self.error_count}{Colors.RESET}")
        print(f"{Colors.YELLOW}Warnungen: {self.warning_count}{Colors.RESET}")
        print()


class MultiLogFollower:
    """Folgt mehreren Log-Dateien gleichzeitig mit Threading."""
    
    def __init__(self, log_paths: list[tuple[Path, str]], analyzer: LogAnalyzer):
        self.log_paths = log_paths  # Liste von (path, source_name) Tupeln
        self.analyzer = analyzer
        self.followers = []
        self.threads = []
        self.running = False
        self.total_errors = 0
        self.total_warnings = 0
        self.total_critical = 0
    
    def follow_all(self):
        """Folgt allen Log-Dateien gleichzeitig."""
        self.running = True
        
        print(f"{Colors.CYAN}[INFO] Folge {len(self.log_paths)} Log-Quellen gleichzeitig:{Colors.RESET}")
        for log_path, source_name in self.log_paths:
            print(f"  {Colors.MAGENTA}• {source_name}{Colors.RESET}: {log_path}")
        print()
        print(f"{Colors.CYAN}[INFO] Drücken Sie Ctrl+C zum Beenden{Colors.RESET}")
        print()
        
        # Erstelle Follower für jede Log-Datei
        for log_path, source_name in self.log_paths:
            if log_path.exists():
                follower = LogFollower(log_path, self.analyzer, source_name)
                self.followers.append(follower)
                
                # Starte Thread für diesen Follower
                thread = Thread(target=follower.follow, daemon=True)
                thread.start()
                self.threads.append(thread)
            else:
                print(f"{Colors.YELLOW}[WARN] Log nicht gefunden: {log_path}{Colors.RESET}")
        
        if not self.threads:
            print(f"{Colors.RED}[ERROR] Keine gültigen Log-Dateien gefunden!{Colors.RESET}")
            return
        
        try:
            # Warte auf Ctrl+C
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}[INFO] Monitoring beendet{Colors.RESET}")
        finally:
            self.running = False
            self._stop_all_followers()
            self._print_summary()
    
    def _stop_all_followers(self):
        """Stoppt alle Follower."""
        for follower in self.followers:
            follower.running = False
        
        # Warte auf alle Threads
        for thread in self.threads:
            thread.join(timeout=1)
    
    def _print_summary(self):
        """Gibt eine Gesamtzusammenfassung aus."""
        # Sammle Statistiken von allen Followern
        for follower in self.followers:
            self.total_critical += follower.critical_count
            self.total_errors += follower.error_count
            self.total_warnings += follower.warning_count
        
        print()
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}Monitoring Zusammenfassung (Alle Quellen):{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.RED}Kritische Fehler: {self.total_critical}{Colors.RESET}")
        print(f"{Colors.RED}Fehler: {self.total_errors}{Colors.RESET}")
        print(f"{Colors.YELLOW}Warnungen: {self.total_warnings}{Colors.RESET}")
        print()
        
        # Details pro Quelle
        if self.followers:
            print(f"{Colors.BOLD}Details pro Quelle:{Colors.RESET}")
            for follower in self.followers:
                if follower.critical_count > 0 or follower.error_count > 0 or follower.warning_count > 0:
                    print(f"  {Colors.MAGENTA}[{follower.source_name}]{Colors.RESET}: "
                          f"{Colors.RED}Kritisch: {follower.critical_count}, "
                          f"Fehler: {follower.error_count}, "
                          f"{Colors.YELLOW}Warnungen: {follower.warning_count}{Colors.RESET}")
            print()


class AutoClaudeMonitor:
    """Haupt-Monitor für Auto Claude."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.analyzer = LogAnalyzer()
        self.process_monitor = ProcessMonitor()
    
    def show_status(self):
        """Zeigt den aktuellen Status."""
        print()
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}Auto Claude Live Monitor{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        print()
        
        # Prozess-Status
        status = self.process_monitor.get_status()
        print(f"{Colors.BOLD}Laufende Prozesse: {status['process_count']}{Colors.RESET}")
        
        if status["processes"]:
            for proc in status["processes"]:
                print(f"  {Colors.GREEN}[PID {proc['pid']}]{Colors.RESET} {proc['name']}")
        else:
            print(f"  {Colors.YELLOW}Keine Auto Claude Prozesse gefunden{Colors.RESET}")
        
        print()
        
        # Log-Dateien
        self._show_recent_logs()
    
    def _show_recent_logs(self):
        """Zeigt die neuesten Log-Einträge."""
        specs_dir = self.project_dir / ".auto-claude" / "specs"
        
        if not specs_dir.exists():
            print(f"{Colors.YELLOW}[INFO] Keine .auto-claude/specs/ gefunden{Colors.RESET}")
            return
        
        print(f"{Colors.BOLD}Neueste Log-Einträge:{Colors.RESET}")
        print()
        
        # Finde neueste Spec mit Logs
        specs = sorted(specs_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
        
        for spec_dir in specs[:3]:  # Zeige max 3 neueste
            if not spec_dir.is_dir():
                continue
            
            log_dir = spec_dir / "logs"
            if not log_dir.exists():
                continue
            
            # Finde neueste Log-Datei
            log_files = list(log_dir.glob("*.log"))
            if not log_files:
                continue
            
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            
            print(f"{Colors.CYAN}[{spec_dir.name}]{Colors.RESET} {latest_log.name}")
            
            # Zeige letzte 5 Zeilen
            try:
                with open(latest_log, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                    for line in lines[-5:]:
                        result = self.analyzer.analyze(line.rstrip())
                        if result["is_error"]:
                            print(f"  {Colors.RED}→ {line.rstrip()}{Colors.RESET}")
                        else:
                            print(f"  {Colors.RESET}→ {line.rstrip()}{Colors.RESET}")
            except Exception as e:
                print(f"  {Colors.YELLOW}→ Fehler beim Lesen: {e}{Colors.RESET}")
            
            print()
    
    def follow_spec_logs(self, spec_id: str):
        """Folgt den Logs eines spezifischen Specs."""
        specs_dir = self.project_dir / ".auto-claude" / "specs"
        spec_dir = specs_dir / spec_id
        
        if not spec_dir.exists():
            print(f"{Colors.RED}[ERROR] Spec nicht gefunden: {spec_id}{Colors.RESET}")
            return
        
        log_dir = spec_dir / "logs"
        if not log_dir.exists():
            print(f"{Colors.YELLOW}[WARN] Keine Logs gefunden für: {spec_id}{Colors.RESET}")
            return
        
        # Finde neueste Log-Datei
        log_files = list(log_dir.glob("*.log"))
        if not log_files:
            print(f"{Colors.YELLOW}[WARN] Keine Log-Dateien gefunden{Colors.RESET}")
            return
        
        latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
        
        follower = LogFollower(latest_log, self.analyzer)
        follower.follow()
    
    def follow_backend_logs(self):
        """Folgt den Backend-Logs."""
        log_file = self.project_dir / "apps" / "backend" / "logs" / "auto-claude.log"
        
        if not log_file.exists():
            print(f"{Colors.YELLOW}[WARN] Backend-Log nicht gefunden: {log_file}{Colors.RESET}")
            print(f"{Colors.CYAN}[INFO] Versuche alternative Pfade...{Colors.RESET}")
            
            # Versuche andere mögliche Pfade
            alternatives = [
                self.project_dir / "apps" / "backend" / "auto-claude.log",
                self.project_dir / "auto-claude.log",
            ]
            
            for alt in alternatives:
                if alt.exists():
                    log_file = alt
                    break
            else:
                print(f"{Colors.RED}[ERROR] Keine Log-Datei gefunden{Colors.RESET}")
                return
        
        follower = LogFollower(log_file, self.analyzer, "Backend")
        follower.follow()
    
    def follow_all_logs(self):
        """Folgt ALLEN Logs gleichzeitig: Backend + alle aktiven Specs."""
        log_paths = []
        
        # 1. Backend-Logs hinzufügen
        backend_log = self.project_dir / "apps" / "backend" / "logs" / "auto-claude.log"
        if backend_log.exists():
            log_paths.append((backend_log, "Backend"))
        else:
            # Versuche alternative Pfade
            alternatives = [
                self.project_dir / "apps" / "backend" / "auto-claude.log",
                self.project_dir / "auto-claude.log",
            ]
            for alt in alternatives:
                if alt.exists():
                    log_paths.append((alt, "Backend"))
                    break
        
        # 2. Alle Spec-Logs hinzufügen
        specs_dir = self.project_dir / ".auto-claude" / "specs"
        if specs_dir.exists():
            for spec_dir in specs_dir.iterdir():
                if not spec_dir.is_dir():
                    continue
                
                log_dir = spec_dir / "logs"
                if not log_dir.exists():
                    continue
                
                # Finde neueste Log-Datei für diesen Spec
                log_files = list(log_dir.glob("*.log"))
                if log_files:
                    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                    log_paths.append((latest_log, f"Spec:{spec_dir.name}"))
        
        if not log_paths:
            print(f"{Colors.YELLOW}[WARN] Keine Log-Dateien gefunden!{Colors.RESET}")
            print(f"{Colors.CYAN}[INFO] Starten Sie zuerst einen Task oder Backend-Prozess{Colors.RESET}")
            return
        
        # Starte Multi-Follower
        multi_follower = MultiLogFollower(log_paths, self.analyzer)
        multi_follower.follow_all()


def main():
    parser = argparse.ArgumentParser(description="Auto Claude Live Terminal Monitor")
    parser.add_argument("--spec", help="Folge Logs eines spezifischen Specs")
    parser.add_argument("--follow-logs", action="store_true", help="Folge Backend-Logs")
    parser.add_argument("--follow-all", action="store_true", help="Folge ALLEN Logs gleichzeitig (Backend + Specs)")
    parser.add_argument("--status", action="store_true", help="Zeige nur Status")
    
    args = parser.parse_args()
    
    # Finde Projekt-Verzeichnis
    project_dir = Path(__file__).parent.parent.parent.resolve()
    
    monitor = AutoClaudeMonitor(project_dir)
    
    if args.follow_all:
        monitor.follow_all_logs()
    elif args.spec:
        monitor.follow_spec_logs(args.spec)
    elif args.follow_logs:
        monitor.follow_backend_logs()
    elif args.status:
        monitor.show_status()
    else:
        # Standard: Zeige Status und starte interaktiv
        monitor.show_status()
        
        print()
        print(f"{Colors.BOLD}Optionen:{Colors.RESET}")
        print(f"  {Colors.GREEN}1. ALLE Logs folgen (Backend + Specs){Colors.RESET} {Colors.BOLD}[EMPFOHLEN]{Colors.RESET}")
        print(f"  2. Nur Backend-Logs folgen")
        print(f"  3. Nur Spec-Logs folgen")
        print(f"  4. Status aktualisieren")
        print(f"  5. Beenden")
        print()
        
        while True:
            try:
                choice = input(f"{Colors.CYAN}Wählen Sie eine Option (1-5): {Colors.RESET}").strip()
                
                if choice == "1":
                    monitor.follow_all_logs()
                elif choice == "2":
                    monitor.follow_backend_logs()
                elif choice == "3":
                    spec_id = input(f"{Colors.CYAN}Spec ID: {Colors.RESET}").strip()
                    monitor.follow_spec_logs(spec_id)
                elif choice == "4":
                    monitor.show_status()
                elif choice == "5":
                    break
                else:
                    print(f"{Colors.YELLOW}Ungültige Auswahl{Colors.RESET}")
            
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}[INFO] Beendet{Colors.RESET}")
                break


if __name__ == "__main__":
    main()

