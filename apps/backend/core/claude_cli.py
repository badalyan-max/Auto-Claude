"""
Claude CLI Path Resolution
===========================

Central utility for finding the Claude CLI executable path.
This ensures consistent path resolution across all modules that need to call the Claude CLI.
"""

import os
import shutil
from pathlib import Path


def find_claude_cli() -> str:
    """
    Find the Claude CLI executable path.
    
    Tries multiple methods in order:
    1. Environment variable CLAUDE_CLI_PATH (from .env or system)
    2. shutil.which('claude') - checks PATH
    3. Common Windows installation paths
    4. Fallback to 'claude' (will fail if not in PATH)
    
    Returns:
        Path to claude executable (prefers .cmd on Windows)
    """
    # Check environment variable first (from .env file or system)
    env_path = os.environ.get("CLAUDE_CLI_PATH")
    if env_path:
        env_path = Path(env_path).expanduser().resolve()
        # If it's a .ps1 file, try to find the .cmd version
        if env_path.suffix == ".ps1":
            cmd_path = env_path.with_suffix(".cmd")
            if cmd_path.exists():
                return str(cmd_path)
        if env_path.exists():
            return str(env_path)
    
    # Try to find in PATH
    claude_path = shutil.which("claude")
    if claude_path:
        claude_path = Path(claude_path)
        # On Windows, prefer .cmd over .ps1
        if claude_path.suffix == ".ps1":
            cmd_path = claude_path.with_suffix(".cmd")
            if cmd_path.exists():
                return str(cmd_path)
        return claude_path
    
    # Common Windows npm installation paths
    npm_paths = [
        Path.home() / "AppData" / "Roaming" / "npm" / "claude.cmd",
        Path.home() / "AppData" / "Roaming" / "npm" / "claude",
    ]
    for path in npm_paths:
        if path.exists():
            return str(path)
    
    # Fallback to 'claude' (will fail if not in PATH, but preserves original behavior)
    return "claude"

