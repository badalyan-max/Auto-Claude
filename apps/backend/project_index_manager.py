"""
Project Index Manager
=====================

Centralized management of project_index.json with automatic refresh capabilities.
Ensures the index stays up-to-date when project files change.
"""

import json
import os
import time
from pathlib import Path


# Files that trigger index refresh when modified
INDEX_TRIGGER_FILES = [
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "supabase/config.toml",
    "supabase/functions",  # Directory
    "supabase/migrations",  # Directory
]

# Maximum age of index before forcing refresh (1 hour)
MAX_INDEX_AGE_SECONDS = 3600


def get_project_index_path(project_dir: Path) -> Path:
    """Get the path to the project index file."""
    return project_dir / ".auto-claude" / "project_index.json"


def should_refresh_index(project_dir: Path, force: bool = False, check_git: bool = True) -> bool:
    """
    Determine if the project index should be refreshed.

    Checks:
    1. If force=True, always refresh
    2. If index doesn't exist, refresh
    3. If index is older than MAX_INDEX_AGE_SECONDS, refresh
    4. If any trigger files are newer than index, refresh
    5. If check_git=True, check for code changes in Git history

    Args:
        project_dir: Root directory of the project
        force: Force refresh regardless of age/changes
        check_git: Check Git history for code changes (default: True)

    Returns:
        True if index should be refreshed
    """
    if force:
        return True

    index_path = get_project_index_path(project_dir)

    # Index doesn't exist - needs creation
    if not index_path.exists():
        return True

    index_mtime = index_path.stat().st_mtime
    current_time = time.time()

    # Index is too old (> 1 hour)
    if current_time - index_mtime > MAX_INDEX_AGE_SECONDS:
        return True

    # Check if any trigger files are newer than index
    for trigger in INDEX_TRIGGER_FILES:
        trigger_path = project_dir / trigger

        if not trigger_path.exists():
            continue

        # Handle directories
        if trigger_path.is_dir():
            # Check if any file in directory is newer
            try:
                for file_path in trigger_path.rglob("*"):
                    if file_path.is_file() and file_path.stat().st_mtime > index_mtime:
                        return True
            except (OSError, PermissionError):
                continue
        # Handle files
        elif trigger_path.is_file():
            if trigger_path.stat().st_mtime > index_mtime:
                return True

    # Check Git history for code changes (NEW!)
    if check_git:
        try:
            from git_change_detector import should_refresh_for_git_changes
            
            if should_refresh_for_git_changes(project_dir):
                return True
        except Exception:
            # Git check failed, continue without it
            pass

    return False


def load_project_index(project_dir: Path, auto_refresh: bool = True) -> dict:
    """
    Load project index with optional auto-refresh.

    Args:
        project_dir: Root directory of the project
        auto_refresh: If True, automatically refresh stale index

    Returns:
        Project index dictionary
    """
    project_dir = Path(project_dir).resolve()
    index_path = get_project_index_path(project_dir)

    # Check if refresh is needed
    if auto_refresh and should_refresh_index(project_dir):
        try:
            refresh_project_index(project_dir)
        except Exception as e:
            # If refresh fails, try to load existing index
            print(f"Warning: Failed to refresh project index: {e}")
            if not index_path.exists():
                return {}

    # Load existing index
    if index_path.exists():
        try:
            with open(index_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Failed to load project index: {e}")
            return {}

    return {}


def refresh_project_index(project_dir: Path) -> bool:
    """
    Regenerate the project index by running the analyzer.

    Args:
        project_dir: Root directory of the project

    Returns:
        True if refresh succeeded, False otherwise
    """
    from analysis.analyzers import analyze_project

    project_dir = Path(project_dir).resolve()
    index_path = get_project_index_path(project_dir)

    # Ensure .auto-claude directory exists
    index_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Run analyzer
        index_data = analyze_project(project_dir)

        # Save to file
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2)

        return True
    except Exception as e:
        print(f"Error refreshing project index: {e}")
        return False


def get_index_age(project_dir: Path) -> float | None:
    """
    Get the age of the project index in seconds.

    Args:
        project_dir: Root directory of the project

    Returns:
        Age in seconds, or None if index doesn't exist
    """
    index_path = get_project_index_path(project_dir)

    if not index_path.exists():
        return None

    index_mtime = index_path.stat().st_mtime
    return time.time() - index_mtime


def get_index_status(project_dir: Path | str) -> dict:
    """
    Get detailed status information about the project index.

    Args:
        project_dir: Root directory of the project (Path or string)

    Returns:
        Dictionary with status information
    """
    # Accept both Path and string
    if isinstance(project_dir, str):
        project_dir = Path(project_dir)
    
    index_path = get_project_index_path(project_dir)
    age = get_index_age(project_dir)

    status = {
        "exists": index_path.exists(),
        "path": str(index_path),
        "age_seconds": age,
        "is_stale": should_refresh_index(project_dir),
    }

    if age is not None:
        status["age_human"] = _format_age(age)

    # Check which trigger files have changed
    if index_path.exists():
        index_mtime = index_path.stat().st_mtime
        changed_files = []

        for trigger in INDEX_TRIGGER_FILES:
            trigger_path = project_dir / trigger

            if not trigger_path.exists():
                continue

            if trigger_path.is_dir():
                try:
                    for file_path in trigger_path.rglob("*"):
                        if (
                            file_path.is_file()
                            and file_path.stat().st_mtime > index_mtime
                        ):
                            changed_files.append(str(file_path.relative_to(project_dir)))
                            break  # Only report directory once
                except (OSError, PermissionError):
                    continue
            elif trigger_path.is_file():
                if trigger_path.stat().st_mtime > index_mtime:
                    changed_files.append(str(trigger_path.relative_to(project_dir)))

        status["changed_files"] = changed_files

    return status


def _format_age(seconds: float) -> str:
    """Format age in seconds to human-readable string."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m"
    elif seconds < 86400:
        return f"{int(seconds / 3600)}h"
    else:
        return f"{int(seconds / 86400)}d"

