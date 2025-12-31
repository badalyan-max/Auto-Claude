"""
Backward compatibility shim - import from integrations.graphiti instead.

This module provides backward compatibility for the old import path:
    from graphiti_memory import GraphitiMemory, is_graphiti_enabled

New code should prefer importing from the graphiti package:
    from integrations.graphiti import GraphitiMemory
"""

# Re-export everything from integrations.graphiti.memory
from integrations.graphiti.memory import (
    EPISODE_TYPE_CODEBASE_DISCOVERY,
    EPISODE_TYPE_GOTCHA,
    EPISODE_TYPE_HISTORICAL_CONTEXT,
    EPISODE_TYPE_PATTERN,
    EPISODE_TYPE_QA_RESULT,
    EPISODE_TYPE_SESSION_INSIGHT,
    EPISODE_TYPE_TASK_OUTCOME,
    MAX_CONTEXT_RESULTS,
    GraphitiMemory,
    GroupIdMode,
    get_graphiti_memory,
    test_graphiti_connection,
)

# Re-export is_graphiti_enabled from config for convenience
from integrations.graphiti.config import is_graphiti_enabled

__all__ = [
    "GraphitiMemory",
    "GroupIdMode",
    "is_graphiti_enabled",
    "get_graphiti_memory",
    "test_graphiti_connection",
    "EPISODE_TYPE_SESSION_INSIGHT",
    "EPISODE_TYPE_CODEBASE_DISCOVERY",
    "EPISODE_TYPE_PATTERN",
    "EPISODE_TYPE_GOTCHA",
    "EPISODE_TYPE_TASK_OUTCOME",
    "EPISODE_TYPE_QA_RESULT",
    "EPISODE_TYPE_HISTORICAL_CONTEXT",
    "MAX_CONTEXT_RESULTS",
]

