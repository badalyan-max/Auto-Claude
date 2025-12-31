"""
Git Change Detector
===================

Erkennt Git-Änderungen seit dem letzten Project-Index-Refresh und stellt
diese als Context für Roadmap/Ideation/Insights bereit.

ZWECK: Stellt sicher, dass externe Änderungen (z.B. von Lovable oder
        direkte Git-Commits) bei neuen Roadmaps/Ideationen berücksichtigt werden.
"""

import json
import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class GitChangeSummary:
    """Zusammenfassung der Git-Änderungen seit dem letzten Index-Refresh."""
    
    has_changes: bool
    commits_since_index: int
    changed_files: list[str]
    recent_commits: list[dict]
    summary: str


class GitChangeDetector:
    """Erkennt Git-Änderungen und triggert Index-Refresh bei Bedarf."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir).resolve()
        self._git_cmd = None
    
    def _find_git_command(self) -> str:
        """Findet Git-Command (Windows-kompatibel)."""
        if self._git_cmd:
            return self._git_cmd
        
        # Versuche git direkt (im PATH)
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                timeout=5,
                shell=True
            )
            if result.returncode == 0:
                self._git_cmd = "git"
                return "git"
        except Exception:
            pass
        
        # Windows: Versuche gängige Git-Installationspfade
        if platform.system() == "Windows":
            common_paths = [
                r"C:\Program Files\Git\cmd\git.exe",
                r"C:\Program Files (x86)\Git\cmd\git.exe",
                r"C:\Program Files\Git\bin\git.exe",
            ]
            for git_path in common_paths:
                if Path(git_path).exists():
                    self._git_cmd = git_path
                    return git_path
        
        # Fallback
        self._git_cmd = "git"
        return "git"
    
    def get_changes_since_index(self) -> GitChangeSummary:
        """
        Ermittelt alle Git-Änderungen seit dem letzten Project-Index-Refresh.
        
        Returns:
            GitChangeSummary mit allen relevanten Änderungen
        """
        index_path = self.project_dir / ".auto-claude" / "project_index.json"
        
        # Wenn kein Index existiert, alle Änderungen der letzten 7 Tage
        if not index_path.exists():
            return self._get_recent_changes(days=7)
        
        try:
            index_mtime = index_path.stat().st_mtime
            index_datetime = datetime.fromtimestamp(index_mtime)
        except OSError:
            return self._get_recent_changes(days=7)
        
        # Git-Commits seit Index-Timestamp
        try:
            # Format: ISO 8601 für git --since
            since_date = index_datetime.strftime("%Y-%m-%d %H:%M:%S")
            git_cmd = self._find_git_command()
            
            # Hole Commits seit Index
            cmd_str = f'"{git_cmd}" log "--since={since_date}" "--pretty=format:%H|%an|%ad|%s" "--date=iso"'
            result = subprocess.run(
                cmd_str,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10,
                shell=True,  # Windows-kompatibel
            )
            
            if result.returncode != 0:
                return GitChangeSummary(
                    has_changes=False,
                    commits_since_index=0,
                    changed_files=[],
                    recent_commits=[],
                    summary="Keine Git-History verfuegbar"
                )
            
            commits = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|", 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0][:8],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    })
            
            # Hole geänderte Dateien
            changed_files = self._get_changed_files_since(since_date)
            
            # Erstelle Zusammenfassung
            summary = self._create_summary(commits, changed_files)
            
            return GitChangeSummary(
                has_changes=len(commits) > 0,
                commits_since_index=len(commits),
                changed_files=changed_files,
                recent_commits=commits[:10],  # Maximal 10 neueste Commits
                summary=summary
            )
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as e:
            print(f"Warning: Git change detection failed: {e}")
            return GitChangeSummary(
                has_changes=False,
                commits_since_index=0,
                changed_files=[],
                recent_commits=[],
                summary="Git-Aenderungserkennung fehlgeschlagen"
            )
    
    def _get_recent_changes(self, days: int = 7) -> GitChangeSummary:
        """Hole die Änderungen der letzten N Tage."""
        try:
            git_cmd = self._find_git_command()
            
            cmd_str = f'"{git_cmd}" log "--since={days} days ago" "--pretty=format:%H|%an|%ad|%s" "--date=iso"'
            result = subprocess.run(
                cmd_str,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10,
                shell=True,
            )
            
            if result.returncode != 0:
                return GitChangeSummary(
                    has_changes=False,
                    commits_since_index=0,
                    changed_files=[],
                    recent_commits=[],
                    summary="Keine Git-History"
                )
            
            commits = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|", 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0][:8],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    })
            
            changed_files = self._get_changed_files_since(f"{days} days ago")
            summary = self._create_summary(commits, changed_files)
            
            return GitChangeSummary(
                has_changes=len(commits) > 0,
                commits_since_index=len(commits),
                changed_files=changed_files,
                recent_commits=commits[:10],
                summary=summary
            )
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            return GitChangeSummary(
                has_changes=False,
                commits_since_index=0,
                changed_files=[],
                recent_commits=[],
                summary=f"Keine Git-Aenderungen (letzte {days} Tage)"
            )
    
    def _get_changed_files_since(self, since: str) -> list[str]:
        """Hole alle geänderten Dateien seit einem bestimmten Zeitpunkt."""
        try:
            git_cmd = self._find_git_command()
            
            cmd_str = f'"{git_cmd}" log "--since={since}" "--name-only" "--pretty=format:"'
            result = subprocess.run(
                cmd_str,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10,
                shell=True,
            )
            
            if result.returncode != 0:
                return []
            
            # Dedupliziere Dateien
            files = set()
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    files.add(line)
            
            return sorted(files)
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            return []
    
    def _create_summary(self, commits: list[dict], changed_files: list[str]) -> str:
        """Erstelle eine lesbare Zusammenfassung der Änderungen."""
        if not commits:
            return "Keine Git-Aenderungen seit letztem Index-Refresh"
        
        lines = [
            f"{len(commits)} neue Commit(s) seit letztem Project-Index-Refresh",
            f"{len(changed_files)} Datei(en) geaendert",
            "",
            "Neueste Commits:"
        ]
        
        for commit in commits[:5]:  # Maximal 5 Commits
            lines.append(f"  - {commit['hash']}: {commit['message']}")
        
        if len(commits) > 5:
            lines.append(f"  ... und {len(commits) - 5} weitere")
        
        # Gruppiere Dateien nach Typ
        file_types = {}
        for file_path in changed_files:
            ext = Path(file_path).suffix or "no-ext"
            file_types[ext] = file_types.get(ext, 0) + 1
        
        if file_types:
            lines.append("")
            lines.append("Geaenderte Dateitypen:")
            for ext, count in sorted(file_types.items(), key=lambda x: -x[1])[:5]:
                lines.append(f"  - {ext}: {count} Datei(en)")
        
        return "\n".join(lines)
    
    def should_refresh_index_for_changes(self) -> bool:
        """
        Prüft ob der Project-Index aufgrund von Git-Änderungen refreshed werden sollte.
        
        Returns:
            True wenn relevante Code-Änderungen vorhanden sind
        """
        changes = self.get_changes_since_index()
        
        if not changes.has_changes:
            return False
        
        # Prüfe ob relevante Code-Dateien geändert wurden
        code_extensions = {
            ".py", ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte",
            ".go", ".rs", ".rb", ".php", ".java", ".cs", ".cpp", ".c"
        }
        
        for file_path in changes.changed_files:
            if Path(file_path).suffix in code_extensions:
                return True
        
        return False
    
    def get_context_for_agent(self, always_include_history: bool = True) -> str:
        """
        Erstellt einen Context-String für AI-Agenten mit Git-Änderungen.
        
        Args:
            always_include_history: Wenn True, immer Git-History zeigen (nicht nur neue Änderungen)
        
        Returns:
            Formatierter Context-String mit Git-Änderungen
        """
        changes = self.get_changes_since_index()
        
        # Wenn keine neuen Änderungen und always_include_history=True,
        # hole trotzdem die letzte Woche an Commits für den Kontext
        if not changes.has_changes and always_include_history:
            changes = self._get_recent_changes(days=7)
            
            if not changes.has_changes:
                # Fallback: hole letzte 10 Commits unabhängig vom Datum
                changes = self._get_last_n_commits(n=10)
        
        if not changes.has_changes:
            return ""
        
        context_parts = [
            "## Recent Git History (Project Changes)",
            "",
            changes.summary,
            ""
        ]
        
        if changes.recent_commits:
            context_parts.append("### Recent Commits:")
            context_parts.append("```")
            for commit in changes.recent_commits:
                context_parts.append(
                    f"{commit['hash']} - {commit['author']} - {commit['message']}"
                )
            context_parts.append("```")
            context_parts.append("")
        
        if changes.changed_files:
            context_parts.append(f"### Changed Files ({len(changes.changed_files)} total):")
            context_parts.append("```")
            # Zeige max. 20 Dateien
            for file_path in changes.changed_files[:20]:
                context_parts.append(f"  - {file_path}")
            if len(changes.changed_files) > 20:
                context_parts.append(f"  ... and {len(changes.changed_files) - 20} more")
            context_parts.append("```")
        
        context_parts.append("")
        context_parts.append(
            "**IMPORTANT**: Consider these recent project changes when "
            "generating roadmaps, insights, or ideations. They represent the "
            "current state and recent evolution of the codebase."
        )
        
        return "\n".join(context_parts)
    
    def _get_last_n_commits(self, n: int = 10) -> GitChangeSummary:
        """Hole die letzten N Commits unabhängig vom Datum."""
        try:
            git_cmd = self._find_git_command()
            
            cmd_str = f'"{git_cmd}" log "-n" "{n}" "--pretty=format:%H|%an|%ad|%s" "--date=iso"'
            result = subprocess.run(
                cmd_str,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10,
                shell=True,
            )
            
            if result.returncode != 0:
                return GitChangeSummary(
                    has_changes=False,
                    commits_since_index=0,
                    changed_files=[],
                    recent_commits=[],
                    summary="Keine Git-History"
                )
            
            commits = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|", 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0][:8],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    })
            
            # Hole geänderte Dateien der letzten N Commits
            cmd_files = f'"{git_cmd}" log "-n" "{n}" "--name-only" "--pretty=format:"'
            result_files = subprocess.run(
                cmd_files,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10,
                shell=True,
            )
            
            changed_files = []
            if result_files.returncode == 0:
                files = set()
                for line in result_files.stdout.strip().split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        files.add(line)
                changed_files = sorted(files)
            
            summary = self._create_summary(commits, changed_files)
            
            return GitChangeSummary(
                has_changes=len(commits) > 0,
                commits_since_index=len(commits),
                changed_files=changed_files,
                recent_commits=commits[:10],
                summary=summary
            )
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            return GitChangeSummary(
                has_changes=False,
                commits_since_index=0,
                changed_files=[],
                recent_commits=[],
                summary="Keine Git-History verfuegbar"
            )


def get_git_changes(project_dir: Path) -> GitChangeSummary:
    """
    Convenience-Funktion zum Abrufen von Git-Änderungen.
    
    Args:
        project_dir: Projekt-Verzeichnis
        
    Returns:
        GitChangeSummary mit allen Änderungen
    """
    detector = GitChangeDetector(project_dir)
    return detector.get_changes_since_index()


def get_git_context_for_agent(project_dir: Path) -> str:
    """
    Convenience-Funktion für Agent-Context mit Git-Änderungen.
    
    Args:
        project_dir: Projekt-Verzeichnis
        
    Returns:
        Formatierter Context-String
    """
    detector = GitChangeDetector(project_dir)
    return detector.get_context_for_agent()


def should_refresh_for_git_changes(project_dir: Path) -> bool:
    """
    Convenience-Funktion zum Prüfen ob Index-Refresh nötig ist.
    
    Args:
        project_dir: Projekt-Verzeichnis
        
    Returns:
        True wenn Refresh empfohlen
    """
    detector = GitChangeDetector(project_dir)
    return detector.should_refresh_index_for_changes()


if __name__ == "__main__":
    # Test-Modus
    import sys
    
    project_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    
    detector = GitChangeDetector(project_dir)
    changes = detector.get_changes_since_index()
    
    print("=" * 60)
    print("GIT CHANGE DETECTION")
    print("=" * 60)
    print(f"Project: {project_dir}")
    print(f"Has Changes: {changes.has_changes}")
    print(f"Commits: {changes.commits_since_index}")
    print(f"Changed Files: {len(changes.changed_files)}")
    print(f"Should Refresh: {detector.should_refresh_index_for_changes()}")
    print()
    print(changes.summary)
    print()
    
    if changes.has_changes:
        print("\n" + "=" * 60)
        print("AGENT CONTEXT")
        print("=" * 60)
        print(detector.get_context_for_agent())
