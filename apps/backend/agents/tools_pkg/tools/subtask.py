"""
Subtask Management Tools
========================

Tools for managing subtask status in implementation_plan.json.

IMPORTANT: Includes validation to prevent fake completions!
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from claude_agent_sdk import tool

    SDK_TOOLS_AVAILABLE = True
except ImportError:
    SDK_TOOLS_AVAILABLE = False
    tool = None

from .validation import validate_subtask_completion, SessionCommitTracker

logger = logging.getLogger(__name__)

# Global tracker for session commits (initialized per session)
_session_tracker: SessionCommitTracker | None = None


def init_session_tracker(project_dir: Path) -> None:
    """Initialize the session commit tracker at the start of a session."""
    global _session_tracker
    _session_tracker = SessionCommitTracker(project_dir)
    logger.info(f"Session tracker initialized. Start commit count: {_session_tracker.session_start_commit_count}")


def create_subtask_tools(spec_dir: Path, project_dir: Path) -> list:
    """
    Create subtask management tools.

    Args:
        spec_dir: Path to the spec directory
        project_dir: Path to the project root

    Returns:
        List of subtask tool functions
    """
    if not SDK_TOOLS_AVAILABLE:
        return []

    tools = []

    # Initialize session tracker if not already done
    global _session_tracker
    if _session_tracker is None:
        init_session_tracker(project_dir)

    # -------------------------------------------------------------------------
    # Tool: update_subtask_status
    # -------------------------------------------------------------------------
    @tool(
        "update_subtask_status",
        "Update the status of a subtask in implementation_plan.json. Use this when completing or starting a subtask.",
        {"subtask_id": str, "status": str, "notes": str},
    )
    async def update_subtask_status(args: dict[str, Any]) -> dict[str, Any]:
        """Update subtask status in the implementation plan.

        IMPORTANT: When marking as 'completed', validation checks are performed
        to ensure actual work was done (files created, commits made).
        """
        subtask_id = args["subtask_id"]
        status = args["status"]
        notes = args.get("notes", "")

        valid_statuses = ["pending", "in_progress", "completed", "failed"]
        if status not in valid_statuses:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Invalid status '{status}'. Must be one of: {valid_statuses}",
                    }
                ]
            }

        # =====================================================================
        # VALIDATION: Prevent fake completions
        # =====================================================================
        if status == "completed":
            commit_count_before = None
            if _session_tracker:
                commit_count_before = _session_tracker.session_start_commit_count

            is_valid, validation_message = validate_subtask_completion(
                project_dir=project_dir,
                spec_dir=spec_dir,
                subtask_id=subtask_id,
                notes=notes,
                commit_count_before=commit_count_before,
            )

            if not is_valid:
                logger.warning(f"VALIDATION FAILED for {subtask_id}: {validation_message}")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"VALIDATION FAILED: Cannot mark '{subtask_id}' as completed.\n\n"
                                    f"Reason: {validation_message}\n\n"
                                    f"You must actually create the files and make commits before marking a subtask as completed. "
                                    f"Please complete the actual implementation first.",
                        }
                    ]
                }

            # Log warnings but allow completion
            if validation_message.startswith("WARNINGS:"):
                logger.warning(f"Completion allowed with warnings for {subtask_id}: {validation_message}")

        plan_file = spec_dir / "implementation_plan.json"
        if not plan_file.exists():
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: implementation_plan.json not found",
                    }
                ]
            }

        try:
            with open(plan_file) as f:
                plan = json.load(f)

            # Find and update the subtask
            subtask_found = False
            for phase in plan.get("phases", []):
                for subtask in phase.get("subtasks", []):
                    if subtask.get("id") == subtask_id:
                        subtask["status"] = status
                        if notes:
                            subtask["notes"] = notes
                        subtask["updated_at"] = datetime.now(timezone.utc).isoformat()

                        # Track validation result for completed subtasks
                        if status == "completed":
                            subtask["validated"] = True
                            subtask["validation_time"] = datetime.now(timezone.utc).isoformat()
                            if _session_tracker and _session_tracker.has_new_commits():
                                subtask["has_commits"] = True
                                commits = _session_tracker.get_session_commits()
                                if commits:
                                    subtask["session_commits"] = commits[:5]  # Store up to 5 commit refs

                        subtask_found = True
                        break
                if subtask_found:
                    break

            if not subtask_found:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: Subtask '{subtask_id}' not found in implementation plan",
                        }
                    ]
                }

            # Update plan metadata
            plan["last_updated"] = datetime.now(timezone.utc).isoformat()

            with open(plan_file, "w") as f:
                json.dump(plan, f, indent=2)

            result_message = f"Successfully updated subtask '{subtask_id}' to status '{status}'"
            if status == "completed":
                result_message += " (VALIDATED: actual work confirmed)"

            return {
                "content": [
                    {
                        "type": "text",
                        "text": result_message,
                    }
                ]
            }

        except json.JSONDecodeError as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Invalid JSON in implementation_plan.json: {e}",
                    }
                ]
            }
        except Exception as e:
            return {
                "content": [
                    {"type": "text", "text": f"Error updating subtask status: {e}"}
                ]
            }

    tools.append(update_subtask_status)

    return tools
