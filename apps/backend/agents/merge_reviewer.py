"""
Merge Reviewer Agent Module
============================

Agent for reviewing code changes before merge and push to GitHub.
Used by the Smart Push system to ensure code quality.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.simple_client import create_simple_client
from phase_config import get_phase_model

logger = logging.getLogger(__name__)


@dataclass
class ConflictInfo:
    """Information about merge conflicts."""
    
    has_conflicts: bool
    files: list[str]
    resolution_strategy: str | None


@dataclass
class QualityIssue:
    """A code quality issue found during review."""
    
    severity: str  # "warning" or "error"
    file: str
    line: int | None
    issue: str


@dataclass
class TestResults:
    """Results from running tests."""
    
    ran: bool
    passed: bool
    details: str


@dataclass 
class CommitMessage:
    """Generated commit message."""
    
    title: str
    body: str
    
    def full_message(self) -> str:
        """Return full commit message."""
        return f"{self.title}\n\n{self.body}"


@dataclass
class ReviewResult:
    """Complete result of a merge review."""
    
    recommendation: str  # "MERGE", "REVIEW_NEEDED", or "REJECT"
    confidence: float
    summary: str
    conflicts: ConflictInfo
    quality_issues: list[QualityIssue]
    test_results: TestResults
    commit_message: CommitMessage
    details: str
    
    @classmethod
    def from_json(cls, data: dict) -> "ReviewResult":
        """Parse from JSON response."""
        conflicts_data = data.get("conflicts", {})
        conflicts = ConflictInfo(
            has_conflicts=conflicts_data.get("has_conflicts", False),
            files=conflicts_data.get("files", []),
            resolution_strategy=conflicts_data.get("resolution_strategy"),
        )
        
        quality_issues = [
            QualityIssue(
                severity=issue.get("severity", "warning"),
                file=issue.get("file", "unknown"),
                line=issue.get("line"),
                issue=issue.get("issue", "Unknown issue"),
            )
            for issue in data.get("quality_issues", [])
        ]
        
        test_data = data.get("test_results", {})
        test_results = TestResults(
            ran=test_data.get("ran", False),
            passed=test_data.get("passed", True),
            details=test_data.get("details", "Tests not run"),
        )
        
        commit_data = data.get("commit_message", {})
        commit_message = CommitMessage(
            title=commit_data.get("title", "chore: merge changes"),
            body=commit_data.get("body", ""),
        )
        
        return cls(
            recommendation=data.get("recommendation", "REVIEW_NEEDED"),
            confidence=data.get("confidence", 0.5),
            summary=data.get("summary", "No summary provided"),
            conflicts=conflicts,
            quality_issues=quality_issues,
            test_results=test_results,
            commit_message=commit_message,
            details=data.get("details", ""),
        )
    
    @classmethod
    def error_result(cls, error_message: str) -> "ReviewResult":
        """Create an error result when review fails."""
        return cls(
            recommendation="REVIEW_NEEDED",
            confidence=0.0,
            summary=f"Review failed: {error_message}",
            conflicts=ConflictInfo(has_conflicts=False, files=[], resolution_strategy=None),
            quality_issues=[],
            test_results=TestResults(ran=False, passed=False, details="Review failed"),
            commit_message=CommitMessage(title="chore: merge changes", body=""),
            details=f"Error during review: {error_message}",
        )


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _get_diff(project_dir: Path, branch: str) -> str:
    """Get diff between branch and main."""
    result = _run_git(["diff", "main", branch, "--stat"], project_dir)
    stat = result.stdout if result.returncode == 0 else ""
    
    # Get actual diff (limited for large diffs)
    result = _run_git(["diff", "main", branch], project_dir)
    diff = result.stdout if result.returncode == 0 else ""
    
    # Limit diff size to avoid token limits
    max_diff_size = 50000  # ~50KB
    if len(diff) > max_diff_size:
        diff = diff[:max_diff_size] + "\n\n... [DIFF TRUNCATED - too large for full review] ..."
    
    return f"=== DIFF STATS ===\n{stat}\n\n=== DIFF CONTENT ===\n{diff}"


def _check_conflicts(project_dir: Path, branch: str) -> ConflictInfo:
    """Check for merge conflicts."""
    # Get merge base
    result = _run_git(["merge-base", "main", branch], project_dir)
    if result.returncode != 0:
        return ConflictInfo(has_conflicts=False, files=[], resolution_strategy=None)
    
    merge_base = result.stdout.strip()
    
    # Use merge-tree to check for conflicts
    result = _run_git(["merge-tree", merge_base, "main", branch], project_dir)
    output = result.stdout
    
    # Check for conflict markers
    conflict_files = []
    if "conflict" in output.lower() or "<<<<<" in output:
        # Extract conflicting files
        for line in output.split("\n"):
            if "conflict" in line.lower():
                # Try to extract filename
                parts = line.split()
                for part in parts:
                    if "/" in part or "." in part:
                        conflict_files.append(part)
    
    return ConflictInfo(
        has_conflicts=len(conflict_files) > 0,
        files=conflict_files,
        resolution_strategy="Manual review required" if conflict_files else None,
    )


def _get_spec_summary(spec_dir: Path) -> str:
    """Get summary from spec.md if it exists."""
    spec_file = spec_dir / "spec.md"
    if not spec_file.exists():
        return "No spec.md found"
    
    try:
        content = spec_file.read_text(encoding="utf-8")
        # Get first 500 chars or until ## Features
        lines = content.split("\n")[:30]
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading spec: {e}"


def _load_prompt_template() -> str:
    """Load the merge reviewer prompt template."""
    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_file = prompts_dir / "merge_reviewer.md"
    
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    
    # Fallback minimal prompt
    return """You are reviewing code changes before merge. 
Analyze the diff and provide your recommendation as JSON with:
- recommendation: MERGE, REVIEW_NEEDED, or REJECT
- confidence: 0.0 to 1.0
- summary: brief description
- conflicts: {has_conflicts, files, resolution_strategy}
- quality_issues: [{severity, file, line, issue}]
- test_results: {ran, passed, details}
- commit_message: {title, body}
- details: any additional notes"""


async def run_merge_review(
    project_dir: Path,
    spec_dir: Path,
    branch_name: str,
    run_tests: bool = True,
    verbose: bool = False,
) -> ReviewResult:
    """
    Run AI-powered merge review on a branch.
    
    Args:
        project_dir: The project root directory
        spec_dir: Directory containing the spec being merged
        branch_name: The branch to review (e.g., "auto-claude/001-feature")
        run_tests: Whether to run tests as part of review
        verbose: Show detailed output
        
    Returns:
        ReviewResult with recommendation and details
    """
    logger.info(f"Starting merge review for {branch_name}")
    
    try:
        # Gather context
        diff = _get_diff(project_dir, branch_name)
        conflicts = _check_conflicts(project_dir, branch_name)
        spec_summary = _get_spec_summary(spec_dir)
        
        # Build the review prompt
        prompt_template = _load_prompt_template()
        
        review_prompt = f"""
{prompt_template}

---

## REVIEW CONTEXT

**Spec Name**: {spec_dir.name}
**Branch**: {branch_name}
**Project Directory**: {project_dir}

### Spec Summary
{spec_summary}

### Conflict Pre-Check
Has conflicts: {conflicts.has_conflicts}
Conflicting files: {conflicts.files if conflicts.files else "None"}

### Diff to Review
{diff}

---

Now analyze this diff and provide your review as JSON.
"""

        # Get model for merge_reviewer
        model = get_phase_model("merge_reviewer")
        
        # Use simple client for single-shot review
        client = create_simple_client(
            model=model,
            max_thinking_tokens=5000,  # Medium thinking for review
        )
        
        # Run the review
        if verbose:
            print(f"  Running AI review with {model}...")
        
        response = client.send_message(review_prompt)
        
        # Parse JSON response
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response (may be wrapped in markdown code blocks)
        json_text = response_text
        if "```json" in json_text:
            start = json_text.find("```json") + 7
            end = json_text.find("```", start)
            json_text = json_text[start:end].strip()
        elif "```" in json_text:
            start = json_text.find("```") + 3
            end = json_text.find("```", start)
            json_text = json_text[start:end].strip()
        
        try:
            review_data = json.loads(json_text)
            result = ReviewResult.from_json(review_data)
            logger.info(f"Review complete: {result.recommendation}")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse review JSON: {e}")
            # Try to extract key info from text
            return ReviewResult(
                recommendation="REVIEW_NEEDED",
                confidence=0.5,
                summary="Review completed but response parsing failed",
                conflicts=conflicts,
                quality_issues=[],
                test_results=TestResults(ran=False, passed=True, details="Parsing failed"),
                commit_message=CommitMessage(
                    title=f"feat: merge {spec_dir.name}",
                    body=f"Merge changes from {branch_name}",
                ),
                details=f"Original response (parsing failed):\n{response_text[:1000]}",
            )
            
    except Exception as e:
        logger.error(f"Merge review failed: {e}")
        return ReviewResult.error_result(str(e))


def run_merge_review_sync(
    project_dir: Path,
    spec_dir: Path,
    branch_name: str,
    run_tests: bool = True,
    verbose: bool = False,
) -> ReviewResult:
    """Synchronous wrapper for run_merge_review."""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        run_merge_review(project_dir, spec_dir, branch_name, run_tests, verbose)
    )
