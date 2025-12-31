#!/usr/bin/env python3
"""
Git Worktree Manager - Per-Spec Architecture
=============================================

Each spec gets its own worktree:
- Worktree path: .worktrees/{spec-name}/
- Branch name: auto-claude/{spec-name}

This allows:
1. Multiple specs to be worked on simultaneously
2. Each spec's changes are isolated
3. Branches persist until explicitly merged
4. Clear 1:1:1 mapping: spec → worktree → branch
"""

import asyncio
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class WorktreeError(Exception):
    """Error during worktree operations."""

    pass


@dataclass
class WorktreeInfo:
    """Information about a spec's worktree."""

    path: Path
    branch: str
    spec_name: str
    base_branch: str
    is_active: bool = True
    commit_count: int = 0
    files_changed: int = 0
    additions: int = 0
    deletions: int = 0


class WorktreeManager:
    """
    Manages per-spec Git worktrees.

    Each spec gets its own worktree in .worktrees/{spec-name}/ with
    a corresponding branch auto-claude/{spec-name}.
    """

    def __init__(self, project_dir: Path, base_branch: str | None = None):
        self.project_dir = project_dir
        self.base_branch = base_branch or self._detect_base_branch()
        self.worktrees_dir = project_dir / ".worktrees"
        self._merge_lock = asyncio.Lock()

    def _detect_base_branch(self) -> str:
        """
        Detect the base branch for worktree creation.

        Priority order:
        1. DEFAULT_BRANCH environment variable
        2. Auto-detect main/master (if they exist)
        3. Fall back to current branch (with warning)

        Returns:
            The detected base branch name
        """
        # 1. Check for DEFAULT_BRANCH env var
        env_branch = os.getenv("DEFAULT_BRANCH")
        if env_branch:
            # Verify the branch exists
            result = subprocess.run(
                ["git", "rev-parse", "--verify", env_branch],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode == 0:
                return env_branch
            else:
                print(
                    f"Warning: DEFAULT_BRANCH '{env_branch}' not found, auto-detecting..."
                )

        # 2. Auto-detect main/master
        for branch in ["main", "master"]:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", branch],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode == 0:
                return branch

        # 3. Fall back to current branch with warning
        current = self._get_current_branch()
        print("Warning: Could not find 'main' or 'master' branch.")
        print(f"Warning: Using current branch '{current}' as base for worktree.")
        print("Tip: Set DEFAULT_BRANCH=your-branch in .env to avoid this.")
        return current

    def _get_current_branch(self) -> str:
        """Get the current git branch."""
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=self.project_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise WorktreeError(f"Failed to get current branch: {result.stderr}")
        return result.stdout.strip()

    def _run_git(
        self, args: list[str], cwd: Path | None = None
    ) -> subprocess.CompletedProcess:
        """Run a git command and return the result."""
        return subprocess.run(
            ["git"] + args,
            cwd=cwd or self.project_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def _unstage_gitignored_files(self) -> None:
        """
        Unstage any staged files that are gitignored in the current branch,
        plus any files in the .auto-claude directory which should never be merged.

        This is needed after a --no-commit merge because files that exist in the
        source branch (like spec files in .auto-claude/specs/) get staged even if
        they're gitignored in the target branch.
        """
        # Get list of staged files
        result = self._run_git(["diff", "--cached", "--name-only"])
        if result.returncode != 0 or not result.stdout.strip():
            return

        staged_files = result.stdout.strip().split("\n")

        # Files to unstage: gitignored files + .auto-claude directory files
        files_to_unstage = set()

        # 1. Check which staged files are gitignored
        # git check-ignore returns the files that ARE ignored
        result = subprocess.run(
            ["git", "check-ignore", "--stdin"],
            cwd=self.project_dir,
            input="\n".join(staged_files),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.stdout.strip():
            for file in result.stdout.strip().split("\n"):
                if file.strip():
                    files_to_unstage.add(file.strip())

        # 2. Always unstage .auto-claude directory files - these are project-specific
        # and should never be merged from the worktree branch
        auto_claude_patterns = [".auto-claude/", "auto-claude/specs/"]
        for file in staged_files:
            file = file.strip()
            if not file:
                continue
            for pattern in auto_claude_patterns:
                if file.startswith(pattern) or f"/{pattern}" in file:
                    files_to_unstage.add(file)
                    break

        if files_to_unstage:
            print(
                f"Unstaging {len(files_to_unstage)} auto-claude/gitignored file(s)..."
            )
            # Unstage each file
            for file in files_to_unstage:
                self._run_git(["reset", "HEAD", "--", file])

    def setup(self) -> None:
        """Create worktrees directory if needed."""
        self.worktrees_dir.mkdir(exist_ok=True)

    # ==================== Per-Spec Worktree Methods ====================

    def get_worktree_path(self, spec_name: str) -> Path:
        """Get the worktree path for a spec."""
        return self.worktrees_dir / spec_name

    def get_branch_name(self, spec_name: str) -> str:
        """Get the branch name for a spec."""
        return f"auto-claude/{spec_name}"

    def worktree_exists(self, spec_name: str) -> bool:
        """Check if a worktree exists for a spec."""
        return self.get_worktree_path(spec_name).exists()

    def get_worktree_info(self, spec_name: str) -> WorktreeInfo | None:
        """Get info about a spec's worktree."""
        worktree_path = self.get_worktree_path(spec_name)
        if not worktree_path.exists():
            return None

        # Verify the branch exists in the worktree
        result = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=worktree_path)
        if result.returncode != 0:
            return None

        actual_branch = result.stdout.strip()

        # Get statistics
        stats = self._get_worktree_stats(spec_name)

        return WorktreeInfo(
            path=worktree_path,
            branch=actual_branch,
            spec_name=spec_name,
            base_branch=self.base_branch,
            is_active=True,
            **stats,
        )

    def _check_branch_namespace_conflict(self) -> str | None:
        """
        Check if a branch named 'auto-claude' exists, which would block creating
        branches in the 'auto-claude/*' namespace.

        Git stores branch refs as files under .git/refs/heads/, so a branch named
        'auto-claude' creates a file that prevents creating the 'auto-claude/'
        directory needed for 'auto-claude/{spec-name}' branches.

        Returns:
            The conflicting branch name if found, None otherwise.
        """
        result = self._run_git(["rev-parse", "--verify", "auto-claude"])
        if result.returncode == 0:
            return "auto-claude"
        return None

    def _get_worktree_stats(self, spec_name: str) -> dict:
        """Get diff statistics for a worktree."""
        worktree_path = self.get_worktree_path(spec_name)

        stats = {
            "commit_count": 0,
            "files_changed": 0,
            "additions": 0,
            "deletions": 0,
        }

        if not worktree_path.exists():
            return stats

        # Commit count
        result = self._run_git(
            ["rev-list", "--count", f"{self.base_branch}..HEAD"], cwd=worktree_path
        )
        if result.returncode == 0:
            stats["commit_count"] = int(result.stdout.strip() or "0")

        # Diff stats
        result = self._run_git(
            ["diff", "--shortstat", f"{self.base_branch}...HEAD"], cwd=worktree_path
        )
        if result.returncode == 0 and result.stdout.strip():
            # Parse: "3 files changed, 50 insertions(+), 10 deletions(-)"
            match = re.search(r"(\d+) files? changed", result.stdout)
            if match:
                stats["files_changed"] = int(match.group(1))
            match = re.search(r"(\d+) insertions?", result.stdout)
            if match:
                stats["additions"] = int(match.group(1))
            match = re.search(r"(\d+) deletions?", result.stdout)
            if match:
                stats["deletions"] = int(match.group(1))

        return stats

    def _is_branch_merged(self, branch_name: str) -> bool:
        """
        Check if a branch is merged into the base branch.
        
        Returns:
            True if branch is fully merged, False otherwise
        """
        result = self._run_git(["branch", "--merged", self.base_branch])
        if result.returncode != 0:
            return False
        
        # Check if our branch is in the list of merged branches
        merged_branches = result.stdout.strip().split("\n")
        return any(branch_name in line for line in merged_branches)

    def create_worktree(self, spec_name: str) -> WorktreeInfo:
        """
        Create a worktree for a spec.
        
        Smart Branch Re-Use (Option A):
        - If branch exists and is merged → Delete and recreate (safe)
        - If branch exists and not merged → Reuse existing work (preserve user work)
        - If branch doesn't exist → Create new

        Args:
            spec_name: The spec folder name (e.g., "002-implement-memory")

        Returns:
            WorktreeInfo for the created worktree

        Raises:
            WorktreeError: If a branch namespace conflict exists or worktree creation fails
        """
        worktree_path = self.get_worktree_path(spec_name)
        branch_name = self.get_branch_name(spec_name)

        # Check for branch namespace conflict (e.g., 'auto-claude' blocking 'auto-claude/*')
        conflicting_branch = self._check_branch_namespace_conflict()
        if conflicting_branch:
            raise WorktreeError(
                f"Branch '{conflicting_branch}' exists and blocks creating '{branch_name}'.\n"
                f"\n"
                f"Git branch names work like file paths - a branch named 'auto-claude' prevents\n"
                f"creating branches under 'auto-claude/' (like 'auto-claude/{spec_name}').\n"
                f"\n"
                f"Fix: Rename the conflicting branch:\n"
                f"  git branch -m {conflicting_branch} {conflicting_branch}-backup"
            )

        # Remove existing worktree if present (from crashed previous run)
        if worktree_path.exists():
            self._run_git(["worktree", "remove", "--force", str(worktree_path)])

        # OPTION A: Smart Branch Re-Use
        # Check if branch exists
        result = self._run_git(["rev-parse", "--verify", branch_name])
        branch_exists = result.returncode == 0

        if branch_exists:
            # Branch exists - check if it's merged
            if self._is_branch_merged(branch_name):
                # Merged = safe to delete and recreate
                print(f"ℹ️  Branch {branch_name} is merged - recreating fresh")
                self._run_git(["branch", "-D", branch_name])
                branch_exists = False
            else:
                # Not merged = reuse to preserve work
                print(f"♻️  Branch {branch_name} exists with unmerged work - reusing")

        # Create or checkout worktree
        if branch_exists:
            # Reuse existing branch (has unmerged work)
            result = self._run_git(
                ["worktree", "add", str(worktree_path), branch_name]
            )
            action = "Reused existing"
        else:
            # Create new branch from base
            result = self._run_git(
                ["worktree", "add", "-b", branch_name, str(worktree_path), self.base_branch]
            )
            action = "Created new"

        if result.returncode != 0:
            raise WorktreeError(
                f"Failed to create worktree for {spec_name}: {result.stderr}"
            )

        print(f"{action} worktree: {worktree_path.name} on branch {branch_name}")

        return WorktreeInfo(
            path=worktree_path,
            branch=branch_name,
            spec_name=spec_name,
            base_branch=self.base_branch,
            is_active=True,
        )

    def get_or_create_worktree(self, spec_name: str) -> WorktreeInfo:
        """
        Get existing worktree or create a new one for a spec.

        Args:
            spec_name: The spec folder name

        Returns:
            WorktreeInfo for the worktree
        """
        existing = self.get_worktree_info(spec_name)
        if existing:
            print(f"Using existing worktree: {existing.path}")
            return existing

        return self.create_worktree(spec_name)

    def remove_worktree(self, spec_name: str, delete_branch: bool = False) -> None:
        """
        Remove a spec's worktree.

        Args:
            spec_name: The spec folder name
            delete_branch: Whether to also delete the branch
        """
        worktree_path = self.get_worktree_path(spec_name)
        branch_name = self.get_branch_name(spec_name)

        if worktree_path.exists():
            result = self._run_git(
                ["worktree", "remove", "--force", str(worktree_path)]
            )
            if result.returncode == 0:
                print(f"Removed worktree: {worktree_path.name}")
            else:
                print(f"Warning: Could not remove worktree: {result.stderr}")
                shutil.rmtree(worktree_path, ignore_errors=True)

        if delete_branch:
            self._run_git(["branch", "-D", branch_name])
            print(f"Deleted branch: {branch_name}")

        self._run_git(["worktree", "prune"])

    def merge_worktree(
        self, spec_name: str, delete_after: bool = False, no_commit: bool = False
    ) -> bool:
        """
        Merge a spec's worktree branch back to base branch.

        Args:
            spec_name: The spec folder name
            delete_after: Whether to remove worktree and branch after merge
            no_commit: If True, merge changes but don't commit (stage only for review)

        Returns:
            True if merge succeeded
        """
        info = self.get_worktree_info(spec_name)
        if not info:
            print(f"No worktree found for spec: {spec_name}")
            return False

        if no_commit:
            print(
                f"Merging {info.branch} into {self.base_branch} (staged, not committed)..."
            )
        else:
            print(f"Merging {info.branch} into {self.base_branch}...")

        # Switch to base branch in main project
        result = self._run_git(["checkout", self.base_branch])
        if result.returncode != 0:
            print(f"Error: Could not checkout base branch: {result.stderr}")
            return False

        # Merge the spec branch
        merge_args = ["merge", "--no-ff", info.branch]
        if no_commit:
            # --no-commit stages the merge but doesn't create the commit
            merge_args.append("--no-commit")
        else:
            merge_args.extend(["-m", f"auto-claude: Merge {info.branch}"])

        result = self._run_git(merge_args)

        if result.returncode != 0:
            print("Merge conflict! Aborting merge...")
            self._run_git(["merge", "--abort"])
            return False

        if no_commit:
            # Unstage any files that are gitignored in the main branch
            # These get staged during merge because they exist in the worktree branch
            self._unstage_gitignored_files()
            print(
                f"Changes from {info.branch} are now staged in your working directory."
            )
            print("Review the changes, then commit when ready:")
            print("  git commit -m 'your commit message'")
        else:
            print(f"Successfully merged {info.branch}")

        if delete_after:
            self.remove_worktree(spec_name, delete_branch=True)

        return True

    def commit_in_worktree(self, spec_name: str, message: str) -> bool:
        """Commit all changes in a spec's worktree."""
        worktree_path = self.get_worktree_path(spec_name)
        if not worktree_path.exists():
            return False

        self._run_git(["add", "."], cwd=worktree_path)
        result = self._run_git(["commit", "-m", message], cwd=worktree_path)

        if result.returncode == 0:
            return True
        elif "nothing to commit" in result.stdout + result.stderr:
            return True
        else:
            print(f"Commit failed: {result.stderr}")
            return False

    # ==================== Listing & Discovery ====================

    def list_all_worktrees(self) -> list[WorktreeInfo]:
        """List all spec worktrees."""
        worktrees = []

        if not self.worktrees_dir.exists():
            return worktrees

        for item in self.worktrees_dir.iterdir():
            if item.is_dir():
                info = self.get_worktree_info(item.name)
                if info:
                    worktrees.append(info)

        return worktrees

    def list_all_spec_branches(self) -> list[str]:
        """List all auto-claude branches (even if worktree removed)."""
        result = self._run_git(["branch", "--list", "auto-claude/*"])
        if result.returncode != 0:
            return []

        branches = []
        for line in result.stdout.strip().split("\n"):
            branch = line.strip().lstrip("* ")
            if branch:
                branches.append(branch)

        return branches

    def get_changed_files(self, spec_name: str) -> list[tuple[str, str]]:
        """Get list of changed files in a spec's worktree."""
        worktree_path = self.get_worktree_path(spec_name)
        if not worktree_path.exists():
            return []

        result = self._run_git(
            ["diff", "--name-status", f"{self.base_branch}...HEAD"], cwd=worktree_path
        )

        files = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) == 2:
                files.append((parts[0], parts[1]))

        return files

    def get_change_summary(self, spec_name: str) -> dict:
        """Get a summary of changes in a worktree."""
        files = self.get_changed_files(spec_name)

        new_files = sum(1 for status, _ in files if status == "A")
        modified_files = sum(1 for status, _ in files if status == "M")
        deleted_files = sum(1 for status, _ in files if status == "D")

        return {
            "new_files": new_files,
            "modified_files": modified_files,
            "deleted_files": deleted_files,
        }

    def cleanup_all(self) -> None:
        """Remove all worktrees and their branches."""
        for worktree in self.list_all_worktrees():
            self.remove_worktree(worktree.spec_name, delete_branch=True)

    def cleanup_stale_worktrees(self) -> None:
        """Remove worktrees that aren't registered with git."""
        if not self.worktrees_dir.exists():
            return

        # Get list of registered worktrees
        result = self._run_git(["worktree", "list", "--porcelain"])
        registered_paths = set()
        for line in result.stdout.split("\n"):
            if line.startswith("worktree "):
                registered_paths.add(Path(line.split(" ", 1)[1]))

        # Remove unregistered directories
        for item in self.worktrees_dir.iterdir():
            if item.is_dir() and item not in registered_paths:
                print(f"Removing stale worktree directory: {item.name}")
                shutil.rmtree(item, ignore_errors=True)

        self._run_git(["worktree", "prune"])

    def cleanup_merged_tasks(self, dry_run: bool = False) -> dict:
        """
        OPTION B: Cleanup tasks that are safely merged into base branch.
        
        This is SAFE because:
        - Only removes branches that are fully merged
        - Never deletes unmerged work
        - Preserves spec directories for history
        
        Args:
            dry_run: If True, only report what would be cleaned, don't actually delete
            
        Returns:
            dict with cleanup statistics:
            {
                "cleaned": [list of spec names cleaned],
                "kept_unmerged": [list of spec names with unmerged work],
                "errors": [list of error messages]
            }
        """
        result = {
            "cleaned": [],
            "kept_unmerged": [],
            "errors": []
        }
        
        # Get all auto-claude branches
        all_branches = self.list_all_spec_branches()
        
        if not all_branches:
            print("ℹ️  No auto-claude branches found")
            return result
        
        print(f"\n🔍 Checking {len(all_branches)} auto-claude branch(es)...")
        
        for branch_name in all_branches:
            # Extract spec name from branch (auto-claude/XXX-name → XXX-name)
            spec_name = branch_name.replace("auto-claude/", "")
            
            # Check if merged
            if self._is_branch_merged(branch_name):
                # SAFE TO DELETE - branch is fully merged
                if dry_run:
                    print(f"  [DRY RUN] Would clean: {spec_name} ✓ (merged)")
                    result["cleaned"].append(spec_name)
                else:
                    print(f"  🧹 Cleaning merged task: {spec_name}")
                    
                    try:
                        # Remove worktree if it exists
                        worktree_path = self.get_worktree_path(spec_name)
                        if worktree_path.exists():
                            remove_result = self._run_git(
                                ["worktree", "remove", "--force", str(worktree_path)]
                            )
                            if remove_result.returncode != 0:
                                # Force remove with shutil if git fails
                                shutil.rmtree(worktree_path, ignore_errors=True)
                        
                        # Delete the branch
                        delete_result = self._run_git(["branch", "-D", branch_name])
                        if delete_result.returncode == 0:
                            result["cleaned"].append(spec_name)
                            print(f"    ✓ Removed branch and worktree")
                        else:
                            result["errors"].append(f"{spec_name}: {delete_result.stderr}")
                            print(f"    ✗ Failed to delete branch: {delete_result.stderr}")
                    
                    except Exception as e:
                        result["errors"].append(f"{spec_name}: {str(e)}")
                        print(f"    ✗ Error during cleanup: {e}")
            else:
                # NOT MERGED - keep it!
                print(f"  ⚠️  Keeping unmerged task: {spec_name} (has unmerged work)")
                result["kept_unmerged"].append(spec_name)
        
        # Prune stale worktree references
        if not dry_run:
            self._run_git(["worktree", "prune"])
        
        # Print summary
        print(f"\n📊 Cleanup Summary:")
        print(f"  ✅ Cleaned (merged): {len(result['cleaned'])}")
        print(f"  ⚠️  Kept (unmerged): {len(result['kept_unmerged'])}")
        print(f"  ❌ Errors: {len(result['errors'])}")
        
        if result["errors"]:
            print("\n⚠️  Errors encountered:")
            for error in result["errors"]:
                print(f"    - {error}")
        
        return result

    def get_test_commands(self, spec_name: str) -> list[str]:
        """Detect likely test/run commands for the project."""
        worktree_path = self.get_worktree_path(spec_name)
        commands = []

        if (worktree_path / "package.json").exists():
            commands.append("npm install && npm run dev")
            commands.append("npm test")

        if (worktree_path / "requirements.txt").exists():
            commands.append("pip install -r requirements.txt")

        if (worktree_path / "Cargo.toml").exists():
            commands.append("cargo run")
            commands.append("cargo test")

        if (worktree_path / "go.mod").exists():
            commands.append("go run .")
            commands.append("go test ./...")

        if not commands:
            commands.append("# Check the project's README for run instructions")

        return commands

    # ==================== Backward Compatibility ====================
    # These methods provide backward compatibility with the old single-worktree API

    def get_staging_path(self) -> Path | None:
        """
        Backward compatibility: Get path to any existing spec worktree.
        Prefer using get_worktree_path(spec_name) instead.
        """
        worktrees = self.list_all_worktrees()
        if worktrees:
            return worktrees[0].path
        return None

    def get_staging_info(self) -> WorktreeInfo | None:
        """
        Backward compatibility: Get info about any existing spec worktree.
        Prefer using get_worktree_info(spec_name) instead.
        """
        worktrees = self.list_all_worktrees()
        if worktrees:
            return worktrees[0]
        return None

    def merge_staging(self, delete_after: bool = True) -> bool:
        """
        Backward compatibility: Merge first found worktree.
        Prefer using merge_worktree(spec_name) instead.
        """
        worktrees = self.list_all_worktrees()
        if worktrees:
            return self.merge_worktree(worktrees[0].spec_name, delete_after)
        return False

    def remove_staging(self, delete_branch: bool = True) -> None:
        """
        Backward compatibility: Remove first found worktree.
        Prefer using remove_worktree(spec_name) instead.
        """
        worktrees = self.list_all_worktrees()
        if worktrees:
            self.remove_worktree(worktrees[0].spec_name, delete_branch)

    def get_or_create_staging(self, spec_name: str) -> WorktreeInfo:
        """
        Backward compatibility: Alias for get_or_create_worktree.
        """
        return self.get_or_create_worktree(spec_name)

    def staging_exists(self) -> bool:
        """
        Backward compatibility: Check if any spec worktree exists.
        Prefer using worktree_exists(spec_name) instead.
        """
        return len(self.list_all_worktrees()) > 0

    def commit_in_staging(self, message: str) -> bool:
        """
        Backward compatibility: Commit in first found worktree.
        Prefer using commit_in_worktree(spec_name, message) instead.
        """
        worktrees = self.list_all_worktrees()
        if worktrees:
            return self.commit_in_worktree(worktrees[0].spec_name, message)
        return False

    def has_uncommitted_changes(self, in_staging: bool = False) -> bool:
        """Check if there are uncommitted changes."""
        worktrees = self.list_all_worktrees()
        if in_staging and worktrees:
            cwd = worktrees[0].path
        else:
            cwd = None
        result = self._run_git(["status", "--porcelain"], cwd=cwd)
        return bool(result.stdout.strip())

    # ==================== Smart Push Methods ====================
    # These methods support the Smart Push tool for AI-reviewed merges
    
    def get_done_unmerged_specs(self, specs_dir: Path | None = None) -> list[dict]:
        """
        Find all specs that are done but not yet merged into main.
        
        Args:
            specs_dir: Path to specs directory (default: project_dir/.auto-claude/specs/)
            
        Returns:
            List of dicts with spec info: {name, branch, spec_dir, plan, is_merged}
        """
        import json
        
        if specs_dir is None:
            specs_dir = self.project_dir / ".auto-claude" / "specs"
        
        if not specs_dir.exists():
            return []
        
        done_specs = []
        
        for spec_dir in specs_dir.iterdir():
            if not spec_dir.is_dir():
                continue
            
            plan_file = spec_dir / "implementation_plan.json"
            if not plan_file.exists():
                continue
            
            try:
                plan = json.loads(plan_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            
            # Check if done
            status = plan.get("status", "")
            plan_status = plan.get("planStatus", "")
            
            is_done = False
            if status == "done":
                is_done = True
            elif status == "human_review" and plan_status == "review":
                # Check if all subtasks completed
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
            
            if not is_done:
                continue
            
            # Check if branch exists
            branch_name = self.get_branch_name(spec_dir.name)
            result = self._run_git(["rev-parse", "--verify", branch_name])
            if result.returncode != 0:
                continue  # No branch, skip
            
            # Check if already merged
            is_merged = self._is_branch_merged(branch_name)
            
            if not is_merged:
                done_specs.append({
                    "name": spec_dir.name,
                    "branch": branch_name,
                    "spec_dir": spec_dir,
                    "plan": plan,
                    "feature": plan.get("feature", "Unknown Feature"),
                    "is_merged": False,
                })
        
        return done_specs
    
    def get_branch_diff_stats(self, branch_name: str) -> dict:
        """
        Get statistics about changes in a branch compared to main.
        
        Returns:
            Dict with: files_changed, additions, deletions, commits
        """
        stats = {
            "files_changed": 0,
            "additions": 0,
            "deletions": 0,
            "commits": 0,
        }
        
        # Get file count
        result = self._run_git(["diff", "--shortstat", f"{self.base_branch}...{branch_name}"])
        if result.returncode == 0 and result.stdout:
            # Parse: " 5 files changed, 100 insertions(+), 20 deletions(-)"
            output = result.stdout.strip()
            import re
            
            files_match = re.search(r"(\d+) files? changed", output)
            if files_match:
                stats["files_changed"] = int(files_match.group(1))
            
            add_match = re.search(r"(\d+) insertions?\(\+\)", output)
            if add_match:
                stats["additions"] = int(add_match.group(1))
            
            del_match = re.search(r"(\d+) deletions?\(-\)", output)
            if del_match:
                stats["deletions"] = int(del_match.group(1))
        
        # Get commit count
        result = self._run_git(["rev-list", "--count", f"{self.base_branch}..{branch_name}"])
        if result.returncode == 0:
            try:
                stats["commits"] = int(result.stdout.strip())
            except ValueError:
                pass
        
        return stats
    
    def merge_with_message(
        self, 
        branch_name: str, 
        commit_message: str,
        delete_after: bool = False
    ) -> bool:
        """
        Merge a branch into main with a custom commit message.
        
        Args:
            branch_name: The branch to merge
            commit_message: Custom commit message
            delete_after: Whether to delete the branch after merge
            
        Returns:
            True if merge succeeded
        """
        # Ensure we're on base branch
        result = self._run_git(["checkout", self.base_branch])
        if result.returncode != 0:
            print(f"Error: Could not checkout {self.base_branch}: {result.stderr}")
            return False
        
        # Perform merge
        result = self._run_git(["merge", "--no-ff", branch_name, "-m", commit_message])
        
        if result.returncode != 0:
            if "conflict" in result.stderr.lower() or "conflict" in result.stdout.lower():
                print("Merge conflict detected! Aborting...")
                self._run_git(["merge", "--abort"])
                return False
            print(f"Merge failed: {result.stderr}")
            return False
        
        print(f"Successfully merged {branch_name}")
        
        if delete_after:
            # Extract spec name from branch
            spec_name = branch_name.replace("auto-claude/", "")
            
            # Remove worktree if exists
            worktree_path = self.get_worktree_path(spec_name)
            if worktree_path.exists():
                self._run_git(["worktree", "remove", "--force", str(worktree_path)])
            
            # Delete branch
            self._run_git(["branch", "-D", branch_name])
            print(f"Deleted branch: {branch_name}")
        
        return True
    
    def push_to_remote(self, branch: str | None = None) -> bool:
        """
        Push a branch to remote.
        
        Args:
            branch: Branch to push (default: current branch)
            
        Returns:
            True if push succeeded
        """
        if branch is None:
            result = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
            branch = result.stdout.strip() if result.returncode == 0 else self.base_branch
        
        result = self._run_git(["push", "origin", branch])
        
        if result.returncode != 0:
            print(f"Push failed: {result.stderr}")
            return False
        
        print(f"Successfully pushed {branch} to origin")
        return True


# Keep STAGING_WORKTREE_NAME for backward compatibility in imports
STAGING_WORKTREE_NAME = "auto-claude"
