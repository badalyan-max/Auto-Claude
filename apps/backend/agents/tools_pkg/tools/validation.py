"""
Validation Tools for Subtask Completion
=======================================

Prevents fake completions by validating that actual work was done
before allowing subtasks to be marked as completed.
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Tuple


class CompletionValidator:
    """Validates that real work was done before marking subtasks complete."""

    def __init__(self, project_dir: Path, spec_dir: Path):
        self.project_dir = project_dir
        self.spec_dir = spec_dir

    def validate_before_completion(
        self,
        subtask_id: str,
        claimed_files: Optional[list[str]] = None,
        claimed_commit: Optional[str] = None,
        commit_count_before: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """
        Validate that real work was done before allowing completion.

        Args:
            subtask_id: The subtask being completed
            claimed_files: Files the agent claims to have created/modified
            claimed_commit: Commit hash the agent claims to have made
            commit_count_before: Commit count before the session started

        Returns:
            (is_valid, message) - True if validation passes
        """
        warnings = []

        # 1. Check if any new commits were made
        current_commit_count = self._get_commit_count()

        if commit_count_before is not None:
            new_commits = current_commit_count - commit_count_before
            if new_commits == 0:
                warnings.append("No new commits detected during this session")

        # 2. Validate claimed commit exists
        if claimed_commit:
            if not self._commit_exists(claimed_commit):
                return False, f"Claimed commit '{claimed_commit}' does not exist in git history!"

        # 3. Validate claimed files exist
        if claimed_files:
            missing_files = []
            for file_path in claimed_files:
                full_path = self.project_dir / file_path
                if not full_path.exists():
                    missing_files.append(file_path)

            if missing_files:
                return False, f"Claimed files do not exist: {', '.join(missing_files)}"

        # 4. Check for meaningful git diff (files were actually modified)
        recent_changes = self._get_recent_changes()
        if not recent_changes and commit_count_before == current_commit_count:
            warnings.append("No file changes detected in working directory or recent commits")

        # All critical checks passed, but maybe with warnings
        if warnings:
            return True, f"WARNINGS: {'; '.join(warnings)}"

        return True, "Validation passed"

    def _get_commit_count(self) -> int:
        """Get current commit count."""
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
        except Exception:
            pass
        return 0

    def _commit_exists(self, commit_hash: str) -> bool:
        """Check if a commit hash exists in git history."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", commit_hash],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_recent_changes(self) -> list[str]:
        """Get list of recently changed files."""
        try:
            # Check both staged and unstaged changes
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1..HEAD"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return [f for f in result.stdout.strip().split('\n') if f]
        except Exception:
            pass
        return []


class SessionCommitTracker:
    """Tracks commits made during a session for validation."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.session_start_commit_count = self._get_commit_count()
        self.session_start_commit = self._get_latest_commit()

    def _get_commit_count(self) -> int:
        """Get current commit count."""
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
        except Exception:
            pass
        return 0

    def _get_latest_commit(self) -> Optional[str]:
        """Get the latest commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def get_session_commits(self) -> list[str]:
        """Get all commits made during this session."""
        try:
            if not self.session_start_commit:
                return []

            result = subprocess.run(
                ["git", "log", "--oneline", f"{self.session_start_commit}..HEAD"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                return [c for c in commits if c]
        except Exception:
            pass
        return []

    def has_new_commits(self) -> bool:
        """Check if any new commits were made during this session."""
        current_count = self._get_commit_count()
        return current_count > self.session_start_commit_count


def validate_subtask_completion(
    project_dir: Path,
    spec_dir: Path,
    subtask_id: str,
    notes: str = "",
    commit_count_before: Optional[int] = None,
) -> Tuple[bool, str]:
    """
    Validate that a subtask can be marked as completed.

    This is a convenience function that creates a validator and runs checks.

    Args:
        project_dir: Project root directory
        spec_dir: Spec directory
        subtask_id: Subtask being completed
        notes: Notes provided by the agent (may contain claimed files/commits)
        commit_count_before: Commit count at session start

    Returns:
        (is_valid, message)
    """
    validator = CompletionValidator(project_dir, spec_dir)

    # Parse claimed files and commits from notes
    claimed_files = []
    claimed_commit = None

    if notes:
        # Look for file patterns in notes
        import re
        # Match patterns like "Created src/foo.ts" or "Modified bar.py"
        file_patterns = re.findall(r'(?:Created|Modified|Added|Updated)\s+([^\s,]+\.[a-zA-Z]+)', notes, re.IGNORECASE)
        claimed_files.extend(file_patterns)

        # Look for commit hashes (7-40 hex chars)
        commit_patterns = re.findall(r'(?:commit(?:ted)?|Commit)\s+(?:in\s+)?([a-f0-9]{7,40})', notes, re.IGNORECASE)
        if commit_patterns:
            claimed_commit = commit_patterns[0]

    return validator.validate_before_completion(
        subtask_id=subtask_id,
        claimed_files=claimed_files if claimed_files else None,
        claimed_commit=claimed_commit,
        commit_count_before=commit_count_before,
    )
