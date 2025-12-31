"""
Tests für Git Change Detector
==============================

Testet die Git-Änderungserkennung und Context-Generierung.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from git_change_detector import GitChangeDetector, get_git_changes


@pytest.fixture
def git_repo(tmp_path):
    """Erstellt ein temporäres Git-Repository für Tests."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    
    # Git init
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    
    # Initial commit
    (repo_dir / "README.md").write_text("# Test Project")
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    
    return repo_dir


def test_no_changes(git_repo):
    """Test wenn keine Änderungen vorliegen."""
    # Erstelle Index
    index_dir = git_repo / ".auto-claude"
    index_dir.mkdir()
    index_file = index_dir / "project_index.json"
    index_file.write_text(json.dumps({"project_root": str(git_repo)}))
    
    detector = GitChangeDetector(git_repo)
    changes = detector.get_changes_since_index()
    
    assert not changes.has_changes
    assert changes.commits_since_index == 0
    assert len(changes.changed_files) == 0


def test_with_new_commits(git_repo):
    """Test mit neuen Commits seit Index-Erstellung."""
    # Erstelle Index
    index_dir = git_repo / ".auto-claude"
    index_dir.mkdir()
    index_file = index_dir / "project_index.json"
    index_file.write_text(json.dumps({"project_root": str(git_repo)}))
    
    # Warte kurz, dann mache neue Commits
    import time
    time.sleep(0.1)
    
    # Neuer Commit
    (git_repo / "src" / "app.ts").parent.mkdir(parents=True)
    (git_repo / "src" / "app.ts").write_text("console.log('Hello');")
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add app.ts"],
        cwd=git_repo,
        check=True,
        capture_output=True,
    )
    
    # Noch ein Commit
    (git_repo / "src" / "utils.ts").write_text("export const util = 1;")
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add utils.ts"],
        cwd=git_repo,
        check=True,
        capture_output=True,
    )
    
    detector = GitChangeDetector(git_repo)
    changes = detector.get_changes_since_index()
    
    assert changes.has_changes
    assert changes.commits_since_index >= 2
    assert len(changes.changed_files) >= 2
    assert "src/app.ts" in changes.changed_files
    assert "src/utils.ts" in changes.changed_files


def test_should_refresh_for_code_changes(git_repo):
    """Test ob Refresh für Code-Änderungen empfohlen wird."""
    # Erstelle Index
    index_dir = git_repo / ".auto-claude"
    index_dir.mkdir()
    index_file = index_dir / "project_index.json"
    index_file.write_text(json.dumps({"project_root": str(git_repo)}))
    
    import time
    time.sleep(0.1)
    
    # Code-Änderung
    (git_repo / "app.py").write_text("print('Hello')")
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add Python file"],
        cwd=git_repo,
        check=True,
        capture_output=True,
    )
    
    detector = GitChangeDetector(git_repo)
    assert detector.should_refresh_index_for_changes()


def test_should_not_refresh_for_doc_changes(git_repo):
    """Test dass nur README-Änderungen keinen Refresh triggern."""
    # Erstelle Index
    index_dir = git_repo / ".auto-claude"
    index_dir.mkdir()
    index_file = index_dir / "project_index.json"
    index_file.write_text(json.dumps({"project_root": str(git_repo)}))
    
    import time
    time.sleep(0.1)
    
    # Nur README ändern
    (git_repo / "README.md").write_text("# Updated README")
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Update README"],
        cwd=git_repo,
        check=True,
        capture_output=True,
    )
    
    detector = GitChangeDetector(git_repo)
    # README alleine sollte keinen Refresh triggern
    assert not detector.should_refresh_index_for_changes()


def test_get_context_for_agent(git_repo):
    """Test Context-String für AI-Agenten."""
    # Erstelle Index
    index_dir = git_repo / ".auto-claude"
    index_dir.mkdir()
    index_file = index_dir / "project_index.json"
    index_file.write_text(json.dumps({"project_root": str(git_repo)}))
    
    import time
    time.sleep(0.1)
    
    # Neue Commits
    (git_repo / "feature.ts").write_text("export const feature = true;")
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add new feature"],
        cwd=git_repo,
        check=True,
        capture_output=True,
    )
    
    detector = GitChangeDetector(git_repo)
    context = detector.get_context_for_agent()
    
    assert context
    assert "Recent Git Changes" in context
    assert "Add new feature" in context
    assert "feature.ts" in context
    assert "IMPORTANT" in context


def test_no_git_repo(tmp_path):
    """Test Verhalten wenn kein Git-Repo vorhanden."""
    non_git_dir = tmp_path / "no_git"
    non_git_dir.mkdir()
    
    detector = GitChangeDetector(non_git_dir)
    changes = detector.get_changes_since_index()
    
    assert not changes.has_changes
    assert changes.commits_since_index == 0


def test_convenience_functions(git_repo):
    """Test Convenience-Funktionen."""
    # Erstelle Index
    index_dir = git_repo / ".auto-claude"
    index_dir.mkdir()
    index_file = index_dir / "project_index.json"
    index_file.write_text(json.dumps({"project_root": str(git_repo)}))
    
    # Test ohne Änderungen
    changes = get_git_changes(git_repo)
    assert not changes.has_changes
    
    # Mit Änderungen
    import time
    time.sleep(0.1)
    
    (git_repo / "test.py").write_text("print('test')")
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add test"],
        cwd=git_repo,
        check=True,
        capture_output=True,
    )
    
    changes = get_git_changes(git_repo)
    assert changes.has_changes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
