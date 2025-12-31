#!/usr/bin/env python3
"""
Vollständiger System-Test für Auto Claude
==========================================

Testet alle wichtigen Komponenten automatisch.
"""

import json
import subprocess
import sys
from pathlib import Path

# Colors
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")


def run_full_test():
    """Führt vollständigen System-Test durch."""
    print_header("AUTO CLAUDE - VOLLSTÄNDIGER SYSTEM-TEST")
    
    results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }
    
    # 1. Python Version
    print(f"{Colors.CYAN}1. Python Version...{Colors.RESET}")
    if sys.version_info >= (3, 12):
        print(f"{Colors.GREEN}   [OK] Python {sys.version_info.major}.{sys.version_info.minor}{Colors.RESET}")
        results["passed"].append("Python Version 3.12+")
    else:
        print(f"{Colors.RED}   [ERROR] Python {sys.version_info.major}.{sys.version_info.minor} (ZU ALT!){Colors.RESET}")
        results["failed"].append(f"Python {sys.version_info.major}.{sys.version_info.minor} zu alt (benötigt 3.12+)")
    
    # 2. .env Datei
    print(f"\n{Colors.CYAN}2. Konfiguration...{Colors.RESET}")
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print(f"{Colors.GREEN}   [OK] .env existiert{Colors.RESET}")
        results["passed"].append(".env Datei vorhanden")
        
        # Prüfe wichtige Einträge
        env_content = env_file.read_text()
        if "GRAPHITI_ENABLED=true" in env_content:
            print(f"{Colors.GREEN}   [OK] GRAPHITI_ENABLED=true{Colors.RESET}")
            results["passed"].append("Graphiti aktiviert")
        else:
            print(f"{Colors.YELLOW}   [WARN] GRAPHITI_ENABLED nicht true{Colors.RESET}")
            results["warnings"].append("Graphiti nicht aktiviert")
        
        if "OPENAI_API_KEY" in env_content:
            print(f"{Colors.GREEN}   [OK] OPENAI_API_KEY vorhanden{Colors.RESET}")
            results["passed"].append("OpenAI Key konfiguriert")
        else:
            print(f"{Colors.YELLOW}   [WARN] OPENAI_API_KEY fehlt{Colors.RESET}")
            results["warnings"].append("OpenAI Key fehlt")
    else:
        print(f"{Colors.RED}   [ERROR] .env fehlt{Colors.RESET}")
        results["failed"].append(".env Datei fehlt")
    
    # 3. Memory System
    print(f"\n{Colors.CYAN}3. Memory System...{Colors.RESET}")
    try:
        from integrations.graphiti.config import get_graphiti_status
        status = get_graphiti_status()
        
        if status["enabled"]:
            print(f"{Colors.GREEN}   [OK] Memory enabled{Colors.RESET}")
        else:
            print(f"{Colors.RED}   [ERROR] Memory disabled{Colors.RESET}")
        
        if status["available"]:
            print(f"{Colors.GREEN}   [OK] Memory verfuegbar{Colors.RESET}")
            print(f"     Provider: {status['embedder_provider']}")
            results["passed"].append("Memory System verfügbar")
        else:
            print(f"{Colors.RED}   [ERROR] Memory nicht verfuegbar: {status['reason']}{Colors.RESET}")
            results["failed"].append(f"Memory: {status['reason']}")
            if status.get("errors"):
                for err in status["errors"]:
                    print(f"{Colors.YELLOW}     [WARN] {err}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}   ✗ Memory System Error: {e}{Colors.RESET}")
        results["failed"].append(f"Memory System: {e}")
    
    # 4. Specs und Tasks
    print(f"\n{Colors.CYAN}4. Specs und Tasks...{Colors.RESET}")
    project_root = Path(__file__).parent.parent.parent
    specs_dir = project_root / ".auto-claude" / "specs"
    
    if specs_dir.exists():
        specs = list(specs_dir.iterdir())
        print(f"   Gefunden: {len(specs)} Specs")
        
        stuck = 0
        done = 0
        in_progress = 0
        
        for spec_dir in specs:
            if not spec_dir.is_dir():
                continue
            
            plan_file = spec_dir / "implementation_plan.json"
            if plan_file.exists():
                try:
                    plan = json.loads(plan_file.read_text())
                    status_val = plan.get("status", "unknown")
                    
                    if status_val == "done":
                        done += 1
                    elif status_val == "in_progress":
                        in_progress += 1
                        # TODO: Pruefeob Prozess wirklich laeuft
                        print(f"{Colors.YELLOW}   [WARN] {spec_dir.name} ist 'in_progress'{Colors.RESET}")
                except Exception as e:
                    print(f"{Colors.YELLOW}   [WARN] Fehler in {spec_dir.name}: {e}{Colors.RESET}")
        
        print(f"   Status: {done} done, {in_progress} in_progress")
        
        if in_progress > 0:
            results["warnings"].append(f"{in_progress} Tasks möglicherweise stuck")
        else:
            results["passed"].append("Keine stuck Tasks")
    else:
        print(f"   Keine Specs vorhanden")
        results["passed"].append("Keine Specs (OK)")
    
    # 5. Worktrees
    print(f"\n{Colors.CYAN}5. Git Worktrees...{Colors.RESET}")
    try:
        result = subprocess.run(
            ["git", "worktree", "list"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=project_root
        )
        
        if result.returncode == 0:
            worktrees = [line for line in result.stdout.split("\n") if line.strip()]
            print(f"   Gefunden: {len(worktrees) - 1} zusätzliche Worktrees")  # -1 für main
            
            if len(worktrees) > 1:
                for wt in worktrees[1:]:
                    print(f"   - {wt}")
                results["passed"].append(f"{len(worktrees) - 1} Worktrees aktiv")
            else:
                print(f"{Colors.GREEN}   [OK] Keine zusaetzlichen Worktrees{Colors.RESET}")
                results["passed"].append("Keine zusätzlichen Worktrees")
    except Exception as e:
        print(f"{Colors.YELLOW}   [WARN] Worktree check: {e}{Colors.RESET}")
        results["warnings"].append(f"Worktree check: {e}")
    
    # 6. Live Monitor
    print(f"\n{Colors.CYAN}6. Live Monitor...{Colors.RESET}")
    monitor_script = Path(__file__).parent / "live_monitor.py"
    if monitor_script.exists():
        print(f"{Colors.GREEN}   [OK] live_monitor.py existiert{Colors.RESET}")
        
        try:
            result = subprocess.run(
                [sys.executable, str(monitor_script), "--status"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=project_root,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                print(f"{Colors.GREEN}   [OK] Monitor funktioniert{Colors.RESET}")
                results["passed"].append("Live Monitor OK")
            else:
                print(f"{Colors.RED}   [ERROR] Monitor Exit Code: {result.returncode}{Colors.RESET}")
                if result.stderr:
                    print(f"     Error: {result.stderr[:200]}")
                results["failed"].append("Live Monitor Error")
        except subprocess.TimeoutExpired:
            print(f"{Colors.YELLOW}   [WARN] Monitor Timeout{Colors.RESET}")
            results["warnings"].append("Monitor Timeout")
        except Exception as e:
            print(f"{Colors.RED}   [ERROR] Monitor: {e}{Colors.RESET}")
            results["failed"].append(f"Monitor: {e}")
    else:
        print(f"{Colors.RED}   [ERROR] live_monitor.py nicht gefunden{Colors.RESET}")
        results["failed"].append("live_monitor.py fehlt")
    
    # 7. Desktop Verknüpfungen
    print(f"\n{Colors.CYAN}7. Desktop Verknüpfungen...{Colors.RESET}")
    desktop_path = Path.home() / "OneDrive" / "Desktop"
    if not desktop_path.exists():
        desktop_path = Path.home() / "Desktop"
    
    shortcuts = [
        "Auto Claude.lnk",
        "Auto Claude (EXE).lnk",
        "Auto Claude Monitor.lnk",
    ]
    
    found_shortcuts = 0
    for shortcut in shortcuts:
        if (desktop_path / shortcut).exists():
            print(f"{Colors.GREEN}   [OK] {shortcut}{Colors.RESET}")
            found_shortcuts += 1
        else:
            print(f"{Colors.YELLOW}   [WARN] {shortcut} fehlt{Colors.RESET}")
    
    if found_shortcuts > 0:
        results["passed"].append(f"{found_shortcuts} Desktop-Verknüpfungen")
    
    # Zusammenfassung
    print_header("ZUSAMMENFASSUNG")
    
    print(f"{Colors.GREEN}{Colors.BOLD}[OK] Bestanden: {len(results['passed'])}{Colors.RESET}")
    for test in results["passed"]:
        print(f"{Colors.GREEN}  - {test}{Colors.RESET}")
    
    if results["warnings"]:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}[WARN] Warnungen: {len(results['warnings'])}{Colors.RESET}")
        for warn in results["warnings"]:
            print(f"{Colors.YELLOW}  - {warn}{Colors.RESET}")
    
    if results["failed"]:
        print(f"\n{Colors.RED}{Colors.BOLD}[ERROR] Fehlgeschlagen: {len(results['failed'])}{Colors.RESET}")
        for fail in results["failed"]:
            print(f"{Colors.RED}  - {fail}{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    # Exit Code
    if results["failed"]:
        print(f"{Colors.RED}System hat Probleme - siehe Fehler oben{Colors.RESET}")
        return False
    elif results["warnings"]:
        print(f"{Colors.YELLOW}System funktioniert mit Warnungen{Colors.RESET}")
        return True
    else:
        print(f"{Colors.GREEN}Alle Tests bestanden!{Colors.RESET}")
        return True


if __name__ == "__main__":
    success = run_full_test()
    sys.exit(0 if success else 1)

