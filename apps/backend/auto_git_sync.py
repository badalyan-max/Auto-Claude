#!/usr/bin/env python3
"""
Auto Git Sync für Auto Claude
==============================

Überwacht Tasks, die auf "Done" gesetzt werden und führt automatisch
Git-Operationen aus: Commit → Push → GitHub PR (optional).

Funktionen:
- Erkennt wenn Tasks Status = "done" erreichen
- Erstellt automatisch Commits für done Tasks
- Pusht zu GitHub (optional)
- Erstellt Pull Requests (optional)
- Macht Änderungen in Auto Claude sichtbar

Usage:
    python auto_git_sync.py --watch           # Überwacht alle Tasks
    python auto_git_sync.py --spec 001        # Nur einen Spec überwachen
    python auto_git_sync.py --check-done      # Prüft einmalig auf done Tasks
    python auto_git_sync.py --auto-push       # Aktiviert automatisches Pushen
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Colors
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class GitSyncManager:
    """Verwaltet automatische Git-Synchronisation für done Tasks."""
    
    def __init__(self, project_dir: Path, auto_push: bool = False, create_pr: bool = False):
        self.project_dir = project_dir
        self.specs_dir = project_dir / ".auto-claude" / "specs"
        self.auto_push = auto_push
        self.create_pr = create_pr
        self.processed_tasks: set[str] = set()  # Verhindert doppelte Verarbeitung
        self.sync_state_file = project_dir / ".auto-claude" / "git_sync_state.json"
        
        # Lade gespeicherten State
        self._load_state()
    
    def _load_state(self):
        """Lädt den gespeicherten State (welche Tasks bereits verarbeitet wurden)."""
        if self.sync_state_file.exists():
            try:
                with open(self.sync_state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.processed_tasks = set(state.get("processed_tasks", []))
                    print(f"{Colors.CYAN}[INFO] {len(self.processed_tasks)} bereits verarbeitete Tasks geladen{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.YELLOW}[WARN] Konnte State nicht laden: {e}{Colors.RESET}")
    
    def _save_state(self):
        """Speichert den aktuellen State."""
        self.sync_state_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.sync_state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "processed_tasks": list(self.processed_tasks),
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"{Colors.YELLOW}[WARN] Konnte State nicht speichern: {e}{Colors.RESET}")
    
    def find_done_tasks(self, spec_filter: Optional[str] = None) -> list[dict]:
        """Findet alle Tasks mit Status 'done' die noch nicht verarbeitet wurden."""
        done_tasks = []
        
        if not self.specs_dir.exists():
            return done_tasks
        
        for spec_dir in self.specs_dir.iterdir():
            if not spec_dir.is_dir():
                continue
            
            # Filter nach spezifischem Spec
            if spec_filter and spec_dir.name != spec_filter:
                continue
            
            # Prüfe ob schon verarbeitet
            if spec_dir.name in self.processed_tasks:
                continue
            
            plan_file = spec_dir / "implementation_plan.json"
            if not plan_file.exists():
                continue
            
            try:
                with open(plan_file, 'r', encoding='utf-8') as f:
                    plan = json.load(f)
                
                status = plan.get("status", "")
                plan_status = plan.get("planStatus", "")
                
                # Check: Status = "done" ODER (status = "human_review" UND alle subtasks completed)
                is_done = False
                
                if status == "done":
                    is_done = True
                elif status == "human_review" and plan_status == "review":
                    # Prüfe ob alle Subtasks completed sind
                    all_completed = True
                    for phase in plan.get("phases", []):
                        for subtask in phase.get("subtasks", []):
                            if subtask.get("status") != "completed":
                                all_completed = False
                                break
                        if not all_completed:
                            break
                    
                    if all_completed:
                        is_done = True
                
                if is_done:
                    done_tasks.append({
                        "spec_id": spec_dir.name,
                        "spec_dir": spec_dir,
                        "plan": plan,
                        "feature": plan.get("feature", "Unknown Feature")
                    })
            
            except Exception as e:
                print(f"{Colors.YELLOW}[WARN] Fehler beim Lesen von {spec_dir.name}: {e}{Colors.RESET}")
        
        return done_tasks
    
    def get_git_branch(self) -> str:
        """Gibt den aktuellen Git-Branch zurück."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"{Colors.RED}[ERROR] Konnte Branch nicht ermitteln: {e}{Colors.RESET}")
            return "main"
    
    def create_commit_for_task(self, task: dict) -> bool:
        """Erstellt einen Git-Commit für einen done Task."""
        spec_id = task["spec_id"]
        feature = task["feature"]
        
        print()
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}Git Commit für Task: {spec_id}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.CYAN}Feature: {feature}{Colors.RESET}")
        print()
        
        try:
            # 1. Git Status prüfen
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout.strip():
                print(f"{Colors.YELLOW}[INFO] Keine Änderungen zum Committen{Colors.RESET}")
                return True
            
            print(f"{Colors.GREEN}[OK] Änderungen gefunden:{Colors.RESET}")
            print(result.stdout)
            
            # 2. Alle Änderungen stagen
            print(f"\n{Colors.CYAN}[INFO] Stage alle Änderungen...{Colors.RESET}")
            subprocess.run(
                ["git", "add", "."],
                cwd=self.project_dir,
                check=True
            )
            
            # 3. Commit-Message erstellen
            commit_msg = self._generate_commit_message(task)
            
            print(f"{Colors.CYAN}[INFO] Erstelle Commit:{Colors.RESET}")
            print(f"{Colors.BOLD}{commit_msg}{Colors.RESET}")
            print()
            
            # 4. Commit erstellen
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.project_dir,
                check=True
            )
            
            print(f"{Colors.GREEN}[OK] Commit erfolgreich erstellt!{Colors.RESET}")
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}[ERROR] Git-Fehler: {e}{Colors.RESET}")
            return False
    
    def _generate_commit_message(self, task: dict) -> str:
        """Generiert eine aussagekräftige Commit-Message."""
        spec_id = task["spec_id"]
        feature = task["feature"]
        plan = task["plan"]
        
        # Zähle completed subtasks
        completed = 0
        total = 0
        for phase in plan.get("phases", []):
            for subtask in phase.get("subtasks", []):
                total += 1
                if subtask.get("status") == "completed":
                    completed += 1
        
        msg = f"feat(auto-claude): {feature}\n\n"
        msg += f"Auto Claude Task: {spec_id}\n"
        msg += f"Subtasks completed: {completed}/{total}\n"
        msg += f"Status: DONE ✅\n\n"
        msg += f"Generated by: Auto Git Sync\n"
        msg += f"Timestamp: {datetime.now().isoformat()}"
        
        return msg
    
    def push_to_remote(self, branch: Optional[str] = None) -> bool:
        """Pusht den aktuellen Branch zu GitHub."""
        if not self.auto_push:
            print(f"{Colors.YELLOW}[INFO] Auto-Push ist deaktiviert. Nutze --auto-push um zu aktivieren.{Colors.RESET}")
            return False
        
        try:
            current_branch = branch or self.get_git_branch()
            
            print()
            print(f"{Colors.CYAN}[INFO] Pushe Branch: {current_branch}{Colors.RESET}")
            
            subprocess.run(
                ["git", "push", "origin", current_branch],
                cwd=self.project_dir,
                check=True
            )
            
            print(f"{Colors.GREEN}[OK] Push erfolgreich!{Colors.RESET}")
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}[ERROR] Push fehlgeschlagen: {e}{Colors.RESET}")
            return False
    
    def create_github_pr(self, task: dict) -> bool:
        """Erstellt einen GitHub Pull Request (benötigt gh CLI)."""
        if not self.create_pr:
            return False
        
        spec_id = task["spec_id"]
        feature = task["feature"]
        
        try:
            # Prüfe ob gh CLI verfügbar
            subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                check=True
            )
            
            print()
            print(f"{Colors.CYAN}[INFO] Erstelle GitHub PR...{Colors.RESET}")
            
            # PR erstellen
            pr_body = f"Auto Claude Task: {spec_id}\n\n{feature}\n\nGenerated by: Auto Git Sync"
            
            result = subprocess.run(
                [
                    "gh", "pr", "create",
                    "--title", f"feat: {feature}",
                    "--body", pr_body,
                    "--base", "main"
                ],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            print(f"{Colors.GREEN}[OK] PR erstellt!{Colors.RESET}")
            print(result.stdout)
            return True
        
        except FileNotFoundError:
            print(f"{Colors.YELLOW}[WARN] GitHub CLI (gh) nicht gefunden. Installiere mit: winget install GitHub.cli{Colors.RESET}")
            return False
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}[ERROR] PR-Erstellung fehlgeschlagen: {e}{Colors.RESET}")
            if e.stderr:
                print(f"{Colors.RED}{e.stderr}{Colors.RESET}")
            return False
    
    def process_done_task(self, task: dict) -> bool:
        """Verarbeitet einen done Task komplett."""
        spec_id = task["spec_id"]
        
        # 1. Commit erstellen
        if not self.create_commit_for_task(task):
            return False
        
        # 2. Push (wenn aktiviert)
        if self.auto_push:
            self.push_to_remote()
        
        # 3. PR erstellen (wenn aktiviert)
        if self.create_pr:
            self.create_github_pr(task)
        
        # 4. Als verarbeitet markieren
        self.processed_tasks.add(spec_id)
        self._save_state()
        
        print()
        print(f"{Colors.GREEN}{Colors.BOLD}[OK] Task {spec_id} erfolgreich verarbeitet!{Colors.RESET}")
        print()
        
        return True
    
    def watch_mode(self, spec_filter: Optional[str] = None):
        """Überwacht kontinuierlich auf done Tasks."""
        print()
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}Auto Git Sync - Watch Mode{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        print()
        print(f"{Colors.CYAN}[INFO] Überwache: {self.specs_dir}{Colors.RESET}")
        if spec_filter:
            print(f"{Colors.CYAN}[INFO] Filter: {spec_filter}{Colors.RESET}")
        print(f"{Colors.CYAN}[INFO] Auto-Push: {Colors.GREEN if self.auto_push else Colors.RED}{'AKTIV' if self.auto_push else 'INAKTIV'}{Colors.RESET}")
        print(f"{Colors.CYAN}[INFO] Auto-PR: {Colors.GREEN if self.create_pr else Colors.RED}{'AKTIV' if self.create_pr else 'INAKTIV'}{Colors.RESET}")
        print()
        print(f"{Colors.CYAN}[INFO] Drücken Sie Ctrl+C zum Beenden{Colors.RESET}")
        print()
        
        check_count = 0
        
        try:
            while True:
                check_count += 1
                
                # Finde done Tasks
                done_tasks = self.find_done_tasks(spec_filter)
                
                if done_tasks:
                    print(f"\n{Colors.GREEN}[OK] {len(done_tasks)} neue Done Tasks gefunden!{Colors.RESET}\n")
                    
                    for task in done_tasks:
                        self.process_done_task(task)
                else:
                    # Stilles Polling (nur alle 10 Checks eine Nachricht)
                    if check_count % 10 == 0:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"{Colors.CYAN}[{timestamp}] Keine neuen Done Tasks... (Check #{check_count}){Colors.RESET}")
                
                # Warte 5 Sekunden
                time.sleep(5)
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}[INFO] Watch Mode beendet{Colors.RESET}")
            print(f"{Colors.CYAN}[INFO] Insgesamt {len(self.processed_tasks)} Tasks verarbeitet{Colors.RESET}")
            print()
    
    def check_done_once(self, spec_filter: Optional[str] = None) -> int:
        """Prüft einmalig auf done Tasks und verarbeitet sie."""
        print()
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}Auto Git Sync - Einmalige Prüfung{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        print()
        
        done_tasks = self.find_done_tasks(spec_filter)
        
        if not done_tasks:
            print(f"{Colors.YELLOW}[INFO] Keine neuen Done Tasks gefunden{Colors.RESET}")
            return 0
        
        print(f"{Colors.GREEN}[OK] {len(done_tasks)} Done Tasks gefunden:{Colors.RESET}")
        for task in done_tasks:
            print(f"  {Colors.CYAN}• {task['spec_id']}{Colors.RESET}: {task['feature']}")
        print()
        
        success_count = 0
        for task in done_tasks:
            if self.process_done_task(task):
                success_count += 1
        
        print()
        print(f"{Colors.GREEN}{Colors.BOLD}[OK] {success_count}/{len(done_tasks)} Tasks erfolgreich verarbeitet{Colors.RESET}")
        print()
        
        return success_count


def main():
    parser = argparse.ArgumentParser(
        description="Auto Git Sync für Auto Claude - Automatische Git-Operationen für done Tasks"
    )
    parser.add_argument("--watch", action="store_true", help="Watch-Mode: Kontinuierliche Überwachung")
    parser.add_argument("--spec", help="Nur einen spezifischen Spec überwachen")
    parser.add_argument("--check-done", action="store_true", help="Einmalige Prüfung auf done Tasks")
    parser.add_argument("--auto-push", action="store_true", help="Aktiviert automatisches Pushen zu GitHub")
    parser.add_argument("--create-pr", action="store_true", help="Erstellt automatisch GitHub Pull Requests")
    parser.add_argument("--reset-state", action="store_true", help="Setzt den verarbeiteten State zurück")
    
    args = parser.parse_args()
    
    # Finde Projekt-Verzeichnis
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent.parent.resolve()
    
    # Reset State wenn angefordert
    if args.reset_state:
        state_file = project_dir / ".auto-claude" / "git_sync_state.json"
        if state_file.exists():
            state_file.unlink()
            print(f"{Colors.GREEN}[OK] State zurückgesetzt{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}[INFO] Kein State gefunden{Colors.RESET}")
        return
    
    # Erstelle Manager
    manager = GitSyncManager(
        project_dir=project_dir,
        auto_push=args.auto_push,
        create_pr=args.create_pr
    )
    
    # Führe gewünschte Operation aus
    if args.watch:
        manager.watch_mode(args.spec)
    elif args.check_done:
        manager.check_done_once(args.spec)
    else:
        # Standard: Einmalige Prüfung
        manager.check_done_once(args.spec)


if __name__ == "__main__":
    main()

