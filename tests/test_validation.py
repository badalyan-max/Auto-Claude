"""
Test Suite for Auto-Claude Validation System
=============================================

Tests to ensure the validation system prevents fake completions.

Run with: python -m pytest tests/test_validation.py -v
Or directly: python tests/test_validation.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))

from agents.tools_pkg.tools.validation import (
    CompletionValidator,
    SessionCommitTracker,
    validate_subtask_completion,
)


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, name: str):
        self.passed += 1
        print(f"  ✅ PASS: {name}")

    def add_fail(self, name: str, reason: str):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  ❌ FAIL: {name}")
        print(f"      Reason: {reason}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TEST RESULTS: {self.passed}/{total} passed")
        if self.errors:
            print(f"\nFailed tests:")
            for name, reason in self.errors:
                print(f"  - {name}: {reason}")
        print(f"{'='*60}")
        return self.failed == 0


def test_completion_validator_detects_fake_commit(results: TestResults):
    """Test that validator detects when a claimed commit doesn't exist."""
    test_name = "detect_fake_commit"

    # Use the Auto-Claude project dir (has git)
    project_dir = Path(__file__).parent.parent
    spec_dir = project_dir / "specs" / "test"

    validator = CompletionValidator(project_dir, spec_dir)

    # Test with a fake commit hash
    is_valid, message = validator.validate_before_completion(
        subtask_id="test.1",
        claimed_commit="fake12345abcdef"  # This commit doesn't exist
    )

    if not is_valid and "does not exist" in message:
        results.add_pass(test_name)
    else:
        results.add_fail(test_name, f"Should reject fake commit. Got: valid={is_valid}, msg={message}")


def test_completion_validator_accepts_real_commit(results: TestResults):
    """Test that validator accepts a real commit hash."""
    test_name = "accept_real_commit"

    project_dir = Path(__file__).parent.parent
    spec_dir = project_dir / "specs" / "test"

    # Get the actual latest commit
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            results.add_fail(test_name, "Could not get HEAD commit")
            return
        real_commit = result.stdout.strip()[:7]  # Short hash
    except Exception as e:
        results.add_fail(test_name, f"Git error: {e}")
        return

    validator = CompletionValidator(project_dir, spec_dir)

    is_valid, message = validator.validate_before_completion(
        subtask_id="test.2",
        claimed_commit=real_commit
    )

    if is_valid or "WARNINGS" in message:
        results.add_pass(test_name)
    else:
        results.add_fail(test_name, f"Should accept real commit {real_commit}. Got: valid={is_valid}, msg={message}")


def test_completion_validator_detects_missing_files(results: TestResults):
    """Test that validator detects when claimed files don't exist."""
    test_name = "detect_missing_files"

    project_dir = Path(__file__).parent.parent
    spec_dir = project_dir / "specs" / "test"

    validator = CompletionValidator(project_dir, spec_dir)

    # Test with files that don't exist
    is_valid, message = validator.validate_before_completion(
        subtask_id="test.3",
        claimed_files=[
            "src/components/FakeComponent.tsx",
            "src/hooks/useFakeHook.ts"
        ]
    )

    if not is_valid and "do not exist" in message:
        results.add_pass(test_name)
    else:
        results.add_fail(test_name, f"Should reject missing files. Got: valid={is_valid}, msg={message}")


def test_completion_validator_accepts_real_files(results: TestResults):
    """Test that validator accepts files that actually exist."""
    test_name = "accept_real_files"

    project_dir = Path(__file__).parent.parent
    spec_dir = project_dir / "specs" / "test"

    validator = CompletionValidator(project_dir, spec_dir)

    # Test with files that exist (relative to project dir)
    is_valid, message = validator.validate_before_completion(
        subtask_id="test.4",
        claimed_files=[
            "README.md",  # This should exist in Auto-Claude repo
        ]
    )

    if is_valid or "WARNINGS" in message:
        results.add_pass(test_name)
    else:
        results.add_fail(test_name, f"Should accept existing files. Got: valid={is_valid}, msg={message}")


def test_session_tracker_detects_no_commits(results: TestResults):
    """Test that session tracker correctly identifies when no new commits were made."""
    test_name = "session_tracker_no_commits"

    project_dir = Path(__file__).parent.parent

    tracker = SessionCommitTracker(project_dir)

    # Without making any commits, has_new_commits should be False
    if not tracker.has_new_commits():
        results.add_pass(test_name)
    else:
        results.add_fail(test_name, "Should report no new commits when none were made")


def test_validate_subtask_completion_parses_notes(results: TestResults):
    """Test that validate_subtask_completion correctly parses notes for claimed items."""
    test_name = "parse_notes_for_claims"

    project_dir = Path(__file__).parent.parent
    spec_dir = project_dir / "specs" / "test"

    # Notes that claim to have created files and made commits
    notes = """
    Created src/components/FakeWidget.tsx
    Modified utils/helper.py
    Committed in abc123def456
    """

    is_valid, message = validate_subtask_completion(
        project_dir=project_dir,
        spec_dir=spec_dir,
        subtask_id="test.5",
        notes=notes,
        commit_count_before=None,
    )

    # Should fail because the claimed files/commits don't exist
    if not is_valid:
        results.add_pass(test_name)
    else:
        results.add_fail(test_name, f"Should reject notes with fake claims. Got: valid={is_valid}, msg={message}")


def test_completion_without_work_gives_warning(results: TestResults):
    """Test that completing without any work gives warnings."""
    test_name = "warn_no_work_done"

    project_dir = Path(__file__).parent.parent
    spec_dir = project_dir / "specs" / "test"

    # Get current commit count
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        commit_count = int(result.stdout.strip()) if result.returncode == 0 else 0
    except:
        commit_count = 0

    is_valid, message = validate_subtask_completion(
        project_dir=project_dir,
        spec_dir=spec_dir,
        subtask_id="test.6",
        notes="Just marking as done",  # No file/commit claims
        commit_count_before=commit_count,  # Same as current = no new commits
    )

    # Should be valid but with warnings about no commits
    if "WARNINGS" in message or "No new commits" in message:
        results.add_pass(test_name)
    else:
        results.add_fail(test_name, f"Should warn about no work. Got: valid={is_valid}, msg={message}")


def run_all_tests():
    """Run all validation tests."""
    print("\n" + "="*60)
    print("AUTO-CLAUDE VALIDATION SYSTEM TESTS")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    results = TestResults()

    print("Testing CompletionValidator:")
    test_completion_validator_detects_fake_commit(results)
    test_completion_validator_accepts_real_commit(results)
    test_completion_validator_detects_missing_files(results)
    test_completion_validator_accepts_real_files(results)

    print("\nTesting SessionCommitTracker:")
    test_session_tracker_detects_no_commits(results)

    print("\nTesting validate_subtask_completion:")
    test_validate_subtask_completion_parses_notes(results)
    test_completion_without_work_gives_warning(results)

    success = results.summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
