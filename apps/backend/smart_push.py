#!/usr/bin/env python3
"""
Smart Push - Intelligentes Push-und-Merge-Tool für Auto Claude
================================================================

Universelles Tool für alle Projekte, das mit Auto Claude bearbeitet werden.
Merged fertige Specs interaktiv in main mit vollständigem Claude Code Review.

Features:
- Findet alle done Specs in jedem Projekt
- KI-gestütztes Code Review vor dem Merge
- Interaktive Bestätigung pro Spec
- Intelligente Commit-Messages
- Automatischer Push zu GitHub

Usage:
    # Im Projekt-Verzeichnis:
    python C:\\Projekte\\auto-claude\\apps\\backend\\smart_push.py
    
    # Mit explizitem Projekt-Pfad:
    python smart_push.py --project "C:\\Projekte\\craft-connect"
    
    # Nur bestimmte Spec:
    python smart_push.py --spec 001
    
    # Ohne KI-Review (schneller):
    python smart_push.py --no-review
    
    # Trockenlauf:
    python smart_push.py --dry-run
"""

from __future__ import annotations

import argparse
import io
import sys
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding for Unicode output
if sys.platform == "win32":
    try:
        # Try to set UTF-8 mode
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # Fallback silently if encoding fix fails

# Add backend to path for imports
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from core.worktree import WorktreeManager


# Colors for terminal output
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def print_header(text: str, char: str = "═", width: int = 70) -> None:
    """Print a styled header."""
    print()
    print(f"{Colors.CYAN}{Colors.BOLD}{char * width}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  {text}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{char * width}{Colors.RESET}")
    print()


def print_subheader(text: str) -> None:
    """Print a subheader."""
    print(f"\n{Colors.BOLD}{Colors.WHITE}{text}{Colors.RESET}")
    print(f"{Colors.DIM}{'─' * 50}{Colors.RESET}")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.RESET}")


def print_step(number: int, text: str) -> None:
    """Print a numbered step."""
    print(f"{Colors.MAGENTA}[{number}]{Colors.RESET} {text}")


def ask_user(prompt: str, options: str = "J/N", default: str = "J") -> str:
    """Ask user for input with options."""
    try:
        full_prompt = f"{Colors.YELLOW}{prompt} [{options}]: {Colors.RESET}"
        response = input(full_prompt).strip().upper()
        return response if response else default.upper()
    except (EOFError, KeyboardInterrupt):
        print()
        return "N"


def display_spec_table(specs: list[dict], wt_manager: WorktreeManager) -> None:
    """Display specs in a nice table format."""
    if not specs:
        print_warning("Keine fertigen Specs gefunden.")
        return
    
    print(f"\n{Colors.BOLD}┌{'─' * 68}┐{Colors.RESET}")
    print(f"{Colors.BOLD}│{Colors.CYAN}  #  │ Spec Name                        │ Status    │ Änderungen {Colors.RESET}{Colors.BOLD}│{Colors.RESET}")
    print(f"{Colors.BOLD}├{'─' * 68}┤{Colors.RESET}")
    
    for i, spec in enumerate(specs, 1):
        name = spec["name"][:32].ljust(32)
        status = f"{Colors.GREEN}✓ Done{Colors.RESET}".ljust(19)
        
        # Get change stats
        stats = wt_manager.get_branch_diff_stats(spec["branch"])
        changes = f"+{stats['additions']}/-{stats['deletions']}"
        
        print(f"{Colors.BOLD}│{Colors.RESET}  {i}  │ {name} │ {status} │ {changes.ljust(10)} {Colors.BOLD}│{Colors.RESET}")
    
    print(f"{Colors.BOLD}└{'─' * 68}┘{Colors.RESET}")


def display_review_result(result) -> None:
    """Display the AI review result in a nice format."""
    print_subheader("KI-Review Ergebnis")
    
    # Recommendation with color
    rec = result.recommendation
    if rec == "MERGE":
        rec_color = Colors.GREEN
        rec_icon = "✅"
    elif rec == "REVIEW_NEEDED":
        rec_color = Colors.YELLOW
        rec_icon = "⚠️"
    else:
        rec_color = Colors.RED
        rec_icon = "❌"
    
    print(f"  Empfehlung: {rec_color}{rec_icon} {rec}{Colors.RESET} (Konfidenz: {result.confidence:.0%})")
    print(f"  Summary: {result.summary}")
    
    # Conflicts
    if result.conflicts.has_conflicts:
        print_warning(f"  Konflikte in: {', '.join(result.conflicts.files)}")
    else:
        print_success("  Keine Merge-Konflikte")
    
    # Quality issues
    if result.quality_issues:
        print(f"  {Colors.YELLOW}Qualitätsprobleme: {len(result.quality_issues)}{Colors.RESET}")
        for issue in result.quality_issues[:3]:  # Show first 3
            severity = "⚠️" if issue.severity == "warning" else "❌"
            print(f"    {severity} {issue.file}: {issue.issue}")
        if len(result.quality_issues) > 3:
            print(f"    ... und {len(result.quality_issues) - 3} weitere")
    else:
        print_success("  Keine Qualitätsprobleme gefunden")
    
    # Tests
    if result.test_results.ran:
        if result.test_results.passed:
            print_success(f"  Tests: {result.test_results.details}")
        else:
            print_error(f"  Tests fehlgeschlagen: {result.test_results.details}")
    
    # Commit message preview
    print(f"\n  {Colors.DIM}Vorgeschlagene Commit-Message:{Colors.RESET}")
    print(f"  {Colors.WHITE}{result.commit_message.title}{Colors.RESET}")


def process_single_spec(
    spec: dict,
    wt_manager: WorktreeManager,
    enable_review: bool,
    dry_run: bool,
    verbose: bool,
) -> bool:
    """
    Process a single spec: review, merge, and report.
    
    Returns True if successfully merged.
    """
    spec_name = spec["name"]
    branch_name = spec["branch"]
    spec_dir = spec["spec_dir"]
    feature = spec["feature"]
    
    print_subheader(f"Spec: {spec_name}")
    print(f"  Branch: {Colors.CYAN}{branch_name}{Colors.RESET}")
    print(f"  Feature: {feature}")
    
    # Get stats
    stats = wt_manager.get_branch_diff_stats(branch_name)
    print(f"  Änderungen: {stats['files_changed']} Dateien, +{stats['additions']}/-{stats['deletions']}, {stats['commits']} Commits")
    
    # Ask if user wants to process this spec
    choice = ask_user(f"\n  Spec {spec_name} reviewen und mergen?", "J/N/D(etails)", "J")
    
    if choice == "D":
        # Show more details
        print(f"\n  {Colors.DIM}Geänderte Dateien:{Colors.RESET}")
        files = wt_manager.get_changed_files(spec_name)
        for status, file_path in files[:10]:
            status_icon = {"A": "+", "M": "~", "D": "-"}.get(status, "?")
            print(f"    {status_icon} {file_path}")
        if len(files) > 10:
            print(f"    ... und {len(files) - 10} weitere")
        
        # Ask again after showing details
        choice = ask_user(f"\n  Jetzt mergen?", "J/N", "J")
    
    if choice != "J":
        print_info("Übersprungen")
        return False
    
    # Run AI review if enabled
    review_result = None
    if enable_review:
        print(f"\n  {Colors.CYAN}🤖 Starte KI-Review...{Colors.RESET}")
        
        try:
            from agents.merge_reviewer import run_merge_review_sync
            review_result = run_merge_review_sync(
                project_dir=wt_manager.project_dir,
                spec_dir=spec_dir,
                branch_name=branch_name,
                run_tests=True,
                verbose=verbose,
            )
            display_review_result(review_result)
        except Exception as e:
            print_warning(f"KI-Review fehlgeschlagen: {e}")
            print_info("Fahre ohne Review fort...")
    
    # Final confirmation before merge
    if review_result and review_result.recommendation == "REJECT":
        print_error("KI empfiehlt: NICHT MERGEN")
        if ask_user("Trotzdem mergen?", "J/N", "N") != "J":
            return False
    elif review_result and review_result.recommendation == "REVIEW_NEEDED":
        print_warning("KI empfiehlt: Manuelles Review")
        if ask_user("Trotzdem mergen?", "J/N", "J") != "J":
            return False
    
    if dry_run:
        print_info("DRY RUN - Merge würde hier durchgeführt werden")
        return True
    
    # Perform merge
    print(f"\n  {Colors.CYAN}Merge in {wt_manager.base_branch}...{Colors.RESET}")
    
    # Use AI-generated commit message if available
    if review_result and review_result.commit_message.title:
        commit_message = review_result.commit_message.full_message()
    else:
        # Generate simple commit message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_message = f"feat: {feature}\n\nAuto Claude Spec: {spec_name}\nMerged: {timestamp}"
    
    success = wt_manager.merge_with_message(
        branch_name=branch_name,
        commit_message=commit_message,
        delete_after=False,  # Keep branch for now
    )
    
    if success:
        print_success(f"Erfolgreich gemerged!")
        return True
    else:
        print_error("Merge fehlgeschlagen!")
        return False


def main():
    """Main entry point for Smart Push."""
    parser = argparse.ArgumentParser(
        description="Smart Push - Intelligentes Push-und-Merge-Tool für Auto Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  smart_push.py                          # Im aktuellen Projekt
  smart_push.py --project ~/craft-connect # Explizites Projekt
  smart_push.py --spec 001               # Nur eine Spec
  smart_push.py --no-review              # Ohne KI-Review
  smart_push.py --dry-run                # Testlauf
        """
    )
    
    parser.add_argument(
        "--project", "-p",
        type=str,
        help="Projekt-Verzeichnis (default: aktuelles Verzeichnis)"
    )
    parser.add_argument(
        "--spec", "-s",
        type=str,
        help="Nur diese Spec verarbeiten (z.B. '001' oder '001-login')"
    )
    parser.add_argument(
        "--no-review",
        action="store_true",
        help="KI-Review überspringen (schneller, weniger sicher)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Testlauf - zeigt was passieren würde, ohne Änderungen"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatisch ohne Rückfragen (VORSICHT!)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Ausführliche Ausgabe"
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Nach Merge automatisch zu GitHub pushen"
    )
    
    args = parser.parse_args()
    
    # Determine project directory
    if args.project:
        project_dir = Path(args.project).resolve()
    else:
        project_dir = Path.cwd().resolve()
    
    # Verify it's a valid project
    if not (project_dir / ".git").exists():
        print_error(f"Kein Git Repository: {project_dir}")
        sys.exit(1)
    
    # Check for .auto-claude directory
    specs_dir = project_dir / ".auto-claude" / "specs"
    if not specs_dir.exists():
        print_error(f"Keine Auto Claude Specs gefunden in: {project_dir}")
        print_info("Ist dies ein Projekt, das mit Auto Claude bearbeitet wurde?")
        sys.exit(1)
    
    # Get project name
    project_name = project_dir.name
    
    # Print header
    print_header(f"SMART PUSH - {project_name}")
    
    if args.dry_run:
        print_warning("DRY RUN MODUS - Keine Änderungen werden durchgeführt")
    
    if args.no_review:
        print_warning("KI-Review ist deaktiviert")
    
    # Initialize worktree manager
    wt_manager = WorktreeManager(project_dir)
    
    print_info(f"Projekt: {project_dir}")
    print_info(f"Base Branch: {wt_manager.base_branch}")
    
    # Find done specs
    print_step(1, "Suche fertige Specs...")
    
    done_specs = wt_manager.get_done_unmerged_specs(specs_dir)
    
    # Filter by spec name if specified
    if args.spec:
        done_specs = [s for s in done_specs if args.spec in s["name"]]
    
    if not done_specs:
        print_warning("Keine fertigen, ungemergten Specs gefunden.")
        if args.spec:
            print_info(f"Filter: {args.spec}")
        sys.exit(0)
    
    print_success(f"{len(done_specs)} fertige Spec(s) gefunden")
    
    # Display table
    display_spec_table(done_specs, wt_manager)
    
    # Process specs
    print_step(2, "Verarbeite Specs...")
    
    merged_count = 0
    skipped_count = 0
    failed_count = 0
    
    for spec in done_specs:
        try:
            if args.auto:
                # Auto mode - no prompts, just merge
                print_subheader(f"Spec: {spec['name']}")
                if not args.dry_run:
                    commit_msg = f"feat: {spec['feature']}\n\nAuto Claude Spec: {spec['name']}"
                    if wt_manager.merge_with_message(spec["branch"], commit_msg, delete_after=False):
                        merged_count += 1
                        print_success("Gemerged")
                    else:
                        failed_count += 1
                else:
                    print_info("DRY RUN - würde mergen")
                    merged_count += 1
            else:
                success = process_single_spec(
                    spec=spec,
                    wt_manager=wt_manager,
                    enable_review=not args.no_review,
                    dry_run=args.dry_run,
                    verbose=args.verbose,
                )
                if success:
                    merged_count += 1
                else:
                    skipped_count += 1
        except KeyboardInterrupt:
            print()
            print_warning("Abgebrochen durch Benutzer")
            break
        except Exception as e:
            print_error(f"Fehler bei {spec['name']}: {e}")
            failed_count += 1
    
    # Push if requested and something was merged
    if args.push and merged_count > 0 and not args.dry_run:
        print_step(3, f"Pushe {wt_manager.base_branch} zu GitHub...")
        if wt_manager.push_to_remote(wt_manager.base_branch):
            print_success("Erfolgreich gepusht!")
        else:
            print_error("Push fehlgeschlagen!")
    
    # Summary
    print_header("ZUSAMMENFASSUNG")
    print(f"  {Colors.GREEN}Gemerged: {merged_count}{Colors.RESET}")
    print(f"  {Colors.YELLOW}Übersprungen: {skipped_count}{Colors.RESET}")
    print(f"  {Colors.RED}Fehlgeschlagen: {failed_count}{Colors.RESET}")
    
    if merged_count > 0 and not args.push and not args.dry_run:
        print()
        print_info("Änderungen sind lokal gemerged.")
        print_info(f"Zum Pushen: git push origin {wt_manager.base_branch}")
        print_info("Oder: python smart_push.py --push")
    
    print()


if __name__ == "__main__":
    main()
