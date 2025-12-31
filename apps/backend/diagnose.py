#!/usr/bin/env python3
"""
Auto Claude System Diagnose
============================

Überprüft alle wichtigen Komponenten und findet Probleme.

Usage:
    python diagnose.py
    python diagnose.py --fix-memory
    python diagnose.py --fix-stuck-tasks
    python diagnose.py --check-github
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load .env
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Color output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str):
    # Remove emojis for Windows compatibility
    text_clean = text.encode('ascii', 'ignore').decode('ascii')
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text_clean}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")


def print_error(text: str):
    print(f"{Colors.RED}[ERROR] {text}{Colors.RESET}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.RESET}")


def print_info(text: str):
    print(f"{Colors.BLUE}[INFO] {text}{Colors.RESET}")


def check_python_version() -> bool:
    """Check Python version."""
    print_info(f"Python Version: {sys.version}")
    
    if sys.version_info >= (3, 12):
        print_success(f"Python {sys.version_info.major}.{sys.version_info.minor} ist installiert (3.12+ erforderlich für LadybugDB)")
        return True
    else:
        print_error(f"Python {sys.version_info.major}.{sys.version_info.minor} ist zu alt!")
        print_warning("LadybugDB benötigt Python 3.12 oder höher")
        print_info("Installieren Sie Python 3.12+: https://www.python.org/downloads/")
        return False


def check_env_file() -> bool:
    """Check if .env file exists."""
    env_path = Path(__file__).parent / ".env"
    
    if env_path.exists():
        print_success(f".env Datei gefunden: {env_path}")
        return True
    else:
        print_error(".env Datei nicht gefunden!")
        print_info("Erstellen Sie apps/backend/.env basierend auf .env.example")
        return False


def check_memory_config() -> dict:
    """Check Graphiti memory configuration."""
    from integrations.graphiti.config import get_graphiti_status
    
    status = get_graphiti_status()
    
    print_info(f"Memory Status:")
    print(f"  - Enabled: {status['enabled']}")
    print(f"  - Available: {status['available']}")
    print(f"  - Database: {status['database']}")
    print(f"  - DB Path: {status['db_path']}")
    print(f"  - Embedder Provider: {status['embedder_provider']}")
    
    if not status['enabled']:
        print_error("Memory ist DEAKTIVIERT!")
        print_info("Setzen Sie GRAPHITI_ENABLED=true in .env")
        return status
    
    if not status['available']:
        print_error(f"Memory ist nicht verfügbar: {status['reason']}")
        if status['errors']:
            for error in status['errors']:
                print_warning(f"  - {error}")
        return status
    
    print_success("Memory Konfiguration ist OK!")
    return status


def check_ollama() -> bool:
    """Check if Ollama is running and model is available."""
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.environ.get("OLLAMA_EMBEDDING_MODEL", "")
    
    if not ollama_model:
        print_info("Ollama wird nicht als Embedder verwendet")
        return True
    
    print_info(f"Überprüfe Ollama: {ollama_url}")
    
    try:
        import requests
        # Check if Ollama is running
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print_success("Ollama läuft!")
            
            # Check if model is available
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            if ollama_model in model_names:
                print_success(f"Embedding Model '{ollama_model}' ist verfügbar!")
                return True
            else:
                print_warning(f"Model '{ollama_model}' nicht gefunden!")
                print_info("Verfügbare Modelle:")
                for name in model_names:
                    print(f"  - {name}")
                print_info(f"\nInstallieren Sie das Model mit:")
                print(f"  ollama pull {ollama_model}")
                return False
        else:
            print_error(f"Ollama antwortet mit Status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Kann keine Verbindung zu Ollama herstellen!")
        print_info("Starten Sie Ollama mit: ollama serve")
        return False
    except ImportError:
        print_warning("requests Modul nicht installiert")
        print_info("Installieren Sie: pip install requests")
        return False


def check_stuck_tasks(project_dir: Path) -> list:
    """Find tasks stuck in 'in_progress' status."""
    specs_dir = project_dir / ".auto-claude" / "specs"
    
    if not specs_dir.exists():
        print_info("Keine .auto-claude/specs/ gefunden")
        return []
    
    stuck_tasks = []
    
    for spec_dir in specs_dir.iterdir():
        if not spec_dir.is_dir():
            continue
        
        plan_file = spec_dir / "implementation_plan.json"
        if not plan_file.exists():
            continue
        
        try:
            with open(plan_file) as f:
                plan = json.load(f)
            
            status = plan.get("status", "")
            if status == "in_progress":
                stuck_tasks.append({
                    "spec_id": spec_dir.name,
                    "status": status,
                    "updated_at": plan.get("updated_at", "unknown")
                })
        except Exception as e:
            print_warning(f"Fehler beim Lesen von {plan_file}: {e}")
    
    return stuck_tasks


def check_worktrees(project_dir: Path) -> list:
    """Check for existing worktrees."""
    worktrees_dir = project_dir / ".worktrees"
    
    if not worktrees_dir.exists():
        print_info("Keine .worktrees/ gefunden")
        return []
    
    worktrees = []
    for worktree in worktrees_dir.iterdir():
        if worktree.is_dir():
            worktrees.append(worktree.name)
    
    return worktrees


def check_github_config() -> bool:
    """Check GitHub CLI configuration."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print_success("GitHub CLI ist konfiguriert!")
            print_info(result.stdout.strip())
            return True
        else:
            print_error("GitHub CLI ist nicht authentifiziert!")
            print_info("Führen Sie aus: gh auth login")
            return False
    except FileNotFoundError:
        print_error("GitHub CLI (gh) ist nicht installiert!")
        print_info("Installieren Sie: https://cli.github.com/")
        return False
    except subprocess.TimeoutExpired:
        print_warning("GitHub CLI Timeout")
        return False


def check_done_tasks(project_dir: Path) -> list:
    """Find tasks with 'done' status."""
    specs_dir = project_dir / ".auto-claude" / "specs"
    
    if not specs_dir.exists():
        return []
    
    done_tasks = []
    
    for spec_dir in specs_dir.iterdir():
        if not spec_dir.is_dir():
            continue
        
        plan_file = spec_dir / "implementation_plan.json"
        if not plan_file.exists():
            continue
        
        try:
            with open(plan_file) as f:
                plan = json.load(f)
            
            if plan.get("status") == "done":
                done_tasks.append({
                    "spec_id": spec_dir.name,
                    "branch": f"auto-claude/{spec_dir.name}",
                    "updated_at": plan.get("updated_at", "unknown")
                })
        except Exception:
            pass
    
    return done_tasks


def check_git_branches(project_dir: Path) -> dict:
    """Check Git branches."""
    try:
        result = subprocess.run(
            ["git", "branch", "-a"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            branches = result.stdout.strip().split("\n")
            current_branch = None
            all_branches = []
            
            for branch in branches:
                branch = branch.strip()
                if branch.startswith("* "):
                    current_branch = branch[2:]
                all_branches.append(branch.lstrip("* "))
            
            return {
                "current": current_branch,
                "all": all_branches
            }
    except Exception as e:
        print_warning(f"Fehler beim Abrufen der Git Branches: {e}")
    
    return {"current": None, "all": []}


def fix_memory():
    """Interactive memory configuration fix."""
    print_header("Memory Konfiguration reparieren")
    
    env_path = Path(__file__).parent / ".env"
    
    # Create .env if it doesn't exist
    if not env_path.exists():
        print_info("Erstelle .env Datei...")
        with open(env_path, "w") as f:
            f.write("# Auto Claude Configuration\n\n")
    
    # Read current .env
    with open(env_path, "r") as f:
        env_content = f.read()
    
    # Check if GRAPHITI_ENABLED exists
    if "GRAPHITI_ENABLED" not in env_content:
        print_info("Füge GRAPHITI_ENABLED=true hinzu...")
        env_content += "\n# Memory System\nGRAPHITI_ENABLED=true\n"
    
    # Ask for embedder provider
    print("\nWählen Sie einen Embedder Provider:")
    print("1. Ollama (lokal, kostenlos)")
    print("2. OpenAI (beste Qualität, benötigt API Key)")
    print("3. Voyage AI (spezialisiert, benötigt API Key)")
    
    choice = input("\nEingabe (1-3) [1]: ").strip() or "1"
    
    if choice == "1":
        # Ollama
        if "GRAPHITI_EMBEDDER_PROVIDER" not in env_content:
            env_content += "\nGRAPHITI_EMBEDDER_PROVIDER=ollama\n"
        if "OLLAMA_BASE_URL" not in env_content:
            env_content += "OLLAMA_BASE_URL=http://localhost:11434\n"
        if "OLLAMA_EMBEDDING_MODEL" not in env_content:
            env_content += "OLLAMA_EMBEDDING_MODEL=embeddinggemma\n"
        if "OLLAMA_EMBEDDING_DIM" not in env_content:
            env_content += "OLLAMA_EMBEDDING_DIM=768\n"
        
        print_success("Ollama Konfiguration hinzugefügt!")
        print_info("\nNächste Schritte:")
        print("1. Installieren Sie Ollama: https://ollama.ai")
        print("2. Starten Sie Ollama: ollama serve")
        print("3. Laden Sie das Model: ollama pull embeddinggemma")
    
    elif choice == "2":
        # OpenAI
        api_key = input("\nOpenAI API Key: ").strip()
        if api_key:
            if "GRAPHITI_EMBEDDER_PROVIDER" not in env_content:
                env_content += "\nGRAPHITI_EMBEDDER_PROVIDER=openai\n"
            if "OPENAI_API_KEY" not in env_content:
                env_content += f"OPENAI_API_KEY={api_key}\n"
            print_success("OpenAI Konfiguration hinzugefügt!")
    
    elif choice == "3":
        # Voyage
        api_key = input("\nVoyage API Key: ").strip()
        if api_key:
            if "GRAPHITI_EMBEDDER_PROVIDER" not in env_content:
                env_content += "\nGRAPHITI_EMBEDDER_PROVIDER=voyage\n"
            if "VOYAGE_API_KEY" not in env_content:
                env_content += f"VOYAGE_API_KEY={api_key}\n"
            print_success("Voyage Konfiguration hinzugefügt!")
    
    # Write updated .env
    with open(env_path, "w") as f:
        f.write(env_content)
    
    print_success(f"\n.env Datei aktualisiert: {env_path}")
    print_info("\nStarten Sie die Electron App neu, um die Änderungen zu übernehmen")


def fix_stuck_tasks(project_dir: Path):
    """Fix stuck tasks."""
    print_header("Hängende Tasks reparieren")
    
    stuck = check_stuck_tasks(project_dir)
    
    if not stuck:
        print_success("Keine hängenden Tasks gefunden!")
        return
    
    print_warning(f"Gefunden: {len(stuck)} hängende Tasks")
    for task in stuck:
        print(f"  - {task['spec_id']} (updated: {task['updated_at']})")
    
    fix = input("\nMöchten Sie diese Tasks zurücksetzen? (y/N): ").strip().lower()
    
    if fix == "y":
        for task in stuck:
            spec_dir = project_dir / ".auto-claude" / "specs" / task["spec_id"]
            plan_file = spec_dir / "implementation_plan.json"
            
            try:
                with open(plan_file, "r") as f:
                    plan = json.load(f)
                
                plan["status"] = "backlog"
                plan["planStatus"] = "pending"
                
                with open(plan_file, "w") as f:
                    json.dump(plan, f, indent=2)
                
                print_success(f"Task {task['spec_id']} zurückgesetzt auf 'backlog'")
            except Exception as e:
                print_error(f"Fehler beim Zurücksetzen von {task['spec_id']}: {e}")


def check_git_changes(project_dir: Path) -> dict:
    """
    Prüft ob Git-Änderungen seit letztem Project-Index-Refresh vorliegen.
    
    Returns:
        Dict mit Änderungsinformationen
    """
    try:
        from git_change_detector import GitChangeDetector
        
        detector = GitChangeDetector(project_dir)
        changes = detector.get_changes_since_index()
        
        return {
            "has_changes": changes.has_changes,
            "commits": changes.commits_since_index,
            "changed_files": len(changes.changed_files),
            "should_refresh": detector.should_refresh_index_for_changes(),
            "summary": changes.summary,
        }
    except Exception as e:
        return {
            "error": str(e),
            "has_changes": False,
        }


def main():
    parser = argparse.ArgumentParser(description="Auto Claude System Diagnose")
    parser.add_argument("--fix-memory", action="store_true", help="Memory Konfiguration reparieren")
    parser.add_argument("--fix-stuck-tasks", action="store_true", help="Hängende Tasks reparieren")
    parser.add_argument("--check-github", action="store_true", help="GitHub Konfiguration überprüfen")
    parser.add_argument("--check-git-changes", action="store_true", help="Git-Änderungen seit letztem Index prüfen")
    
    args = parser.parse_args()
    
    # Find project directory (3 levels up from apps/backend/diagnose.py)
    project_dir = Path(__file__).parent.parent.parent.resolve()
    
    print_header("🔍 Auto Claude System Diagnose")
    print_info(f"Projekt: {project_dir}")
    
    # Run fixes if requested
    if args.fix_memory:
        fix_memory()
        return
    
    if args.fix_stuck_tasks:
        fix_stuck_tasks(project_dir)
        return
    
    # Otherwise run full diagnostic
    
    # 1. Python Version
    print_header("1️⃣  Python Version")
    python_ok = check_python_version()
    
    # 2. .env File
    print_header("2️⃣  Konfigurationsdatei")
    env_ok = check_env_file()
    
    # 3. Memory System
    print_header("3️⃣  Memory System (Graphiti)")
    if env_ok:
        memory_status = check_memory_config()
        
        # Check Ollama if used
        if memory_status.get("embedder_provider") == "ollama":
            print()
            ollama_ok = check_ollama()
    else:
        print_warning("Überspringe Memory Check (keine .env)")
    
    # 4. Stuck Tasks
    print_header("4️⃣  Task Status")
    stuck = check_stuck_tasks(project_dir)
    if stuck:
        print_warning(f"Gefunden: {len(stuck)} hängende Tasks (status='in_progress')")
        for task in stuck:
            print(f"  - {task['spec_id']}")
        print_info("\nZum Reparieren: python diagnose.py --fix-stuck-tasks")
    else:
        print_success("Keine hängenden Tasks gefunden!")
    
    # 5. Worktrees
    print_header("5️⃣  Git Worktrees")
    worktrees = check_worktrees(project_dir)
    if worktrees:
        print_info(f"Gefunden: {len(worktrees)} Worktrees")
        for wt in worktrees:
            print(f"  - {wt}")
    else:
        print_success("Keine Worktrees vorhanden")
    
    # 6. Git Changes (NEW!)
    if args.check_git_changes:
        print_header("6️⃣  Git-Änderungen seit letztem Index")
        git_status = check_git_changes(project_dir)
        
        if "error" in git_status:
            print_error(f"Fehler beim Prüfen: {git_status['error']}")
        elif git_status["has_changes"]:
            print_warning(f"{git_status['commits']} neue Commit(s), {git_status['changed_files']} Datei(en) geändert")
            print()
            print(git_status["summary"])
            
            if git_status["should_refresh"]:
                print()
                print_warning("⚠️  Index-Refresh empfohlen für Code-Änderungen!")
                print_info("Tipp: Der Index wird automatisch beim nächsten Roadmap/Ideation-Run aktualisiert")
        else:
            print_success("Keine Git-Änderungen seit letztem Index-Refresh")
    
    # 7. GitHub Configuration
    if args.check_github:
        print_header("7️⃣  GitHub Konfiguration")
        github_ok = check_github_config()
        
        # Check for done tasks
        print()
        done = check_done_tasks(project_dir)
        if done:
            print_success(f"Gefunden: {len(done)} abgeschlossene Tasks (status='done')")
            for task in done:
                print(f"  - {task['spec_id']}")
            
            # Check Git branches
            print()
            branches = check_git_branches(project_dir)
            if branches["current"]:
                print_info(f"Aktueller Branch: {branches['current']}")
                print_info(f"Verfügbare Branches: {len(branches['all'])}")
                
                # Check if auto-claude branches exist
                auto_branches = [b for b in branches['all'] if 'auto-claude/' in b]
                if auto_branches:
                    print_info(f"Auto Claude Branches: {len(auto_branches)}")
                    for b in auto_branches:
                        print(f"  - {b}")
        else:
            print_info("Keine abgeschlossenen Tasks gefunden")
    
    # Summary
    print_header("📊 Zusammenfassung")
    
    issues = []
    if not python_ok:
        issues.append("Python Version < 3.12")
    if not env_ok:
        issues.append(".env Datei fehlt")
    if stuck:
        issues.append(f"{len(stuck)} hängende Tasks")
    
    if issues:
        print_warning("Gefundene Probleme:")
        for issue in issues:
            print(f"  ❌ {issue}")
        
        print("\n" + "="*60)
        print(f"{Colors.BOLD}Empfohlene Aktionen:{Colors.RESET}")
        print("="*60)
        
        if not env_ok or not python_ok:
            print("\n1. Memory konfigurieren:")
            print("   python diagnose.py --fix-memory")
        
        if stuck:
            print("\n2. Hängende Tasks reparieren:")
            print("   python diagnose.py --fix-stuck-tasks")
        
        print("\n3. Vollständige Anleitung:")
        print("   Siehe: PROBLEMLÖSUNGEN.md")
    else:
        print_success("Alle Systeme funktionieren!")
    
    print()


if __name__ == "__main__":
    main()

