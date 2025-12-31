"""
Base Commands Module
====================

Core shell commands that are always safe regardless of project type.
These commands form the foundation of the security allowlist.
"""


# =============================================================================
# BASE COMMANDS - Always safe regardless of project type
# =============================================================================

BASE_COMMANDS: set[str] = {
    # Core shell
    "echo",
    "printf",
    "cat",
    "head",
    "tail",
    "less",
    "more",
    "ls",
    "pwd",
    "cd",
    "pushd",
    "popd",
    "cp",
    "mv",
    "mkdir",
    "rmdir",
    "touch",
    "ln",
    "find",
    "fd",
    "grep",
    "egrep",
    "fgrep",
    "rg",
    "ag",
    "sort",
    "uniq",
    "cut",
    "tr",
    "sed",
    "awk",
    "gawk",
    "wc",
    "diff",
    "cmp",
    "comm",
    "tee",
    "xargs",
    "read",
    "file",
    "stat",
    "tree",
    "du",
    "df",
    "which",
    "whereis",
    "type",
    "command",
    "date",
    "time",
    "sleep",
    "timeout",
    "watch",
    "true",
    "false",
    "test",
    "[",
    "[[",
    "env",
    "printenv",
    "export",
    "unset",
    "set",
    "source",
    ".",
    "eval",
    "exec",
    "exit",
    "return",
    "break",
    "continue",
    "sh",
    "bash",
    "zsh",
    "powershell",  # Windows PowerShell
    "pwsh",  # PowerShell Core
    "cmd",  # Windows Command Prompt
    # Archives
    "tar",
    "zip",
    "unzip",
    "gzip",
    "gunzip",
    "bzip2",
    "bunzip2",
    "xz",
    "unxz",
    "7z",
    # Network
    "curl",
    "wget",
    "ping",
    "host",
    "dig",
    "nslookup",
    "netstat",
    "ss",
    "ip",
    "ifconfig",
    "traceroute",
    "tracert",  # Windows traceroute
    "telnet",
    "nc",
    "netcat",
    # Git (full access for GitHub operations)
    "git",
    "gh",  # GitHub CLI
    "git-lfs",  # Git Large File Storage
    # Process management (with validation in security.py)
    "ps",
    "pgrep",
    "lsof",
    "jobs",
    "kill",
    "pkill",
    "killall",  # Validated for safe targets only
    "tasklist",  # Windows process list
    "taskkill",  # Windows task killer
    # File operations (with validation in security.py)
    "rm",
    "chmod",  # Validated for safe operations only
    "chown",
    "chgrp",
    "icacls",  # Windows permissions
    "attrib",  # Windows file attributes
    # System info
    "systemctl",
    "service",
    "sc",  # Windows Service Control
    "net",  # Windows network commands
    "reg",  # Windows Registry (read-only operations)
    "wmic",  # Windows Management Instrumentation
    "Get-Process",  # PowerShell cmdlet
    "Get-Service",  # PowerShell cmdlet
    "Get-ChildItem",  # PowerShell cmdlet
    "Set-Location",  # PowerShell cmdlet
    # Text tools
    "paste",
    "join",
    "split",
    "fold",
    "fmt",
    "nl",
    "rev",
    "shuf",
    "column",
    "expand",
    "unexpand",
    "iconv",
    # Misc safe
    "clear",
    "cls",  # Windows clear
    "reset",
    "man",
    "help",
    "uname",
    "whoami",
    "id",
    "basename",
    "dirname",
    "realpath",
    "readlink",
    "mktemp",
    "bc",
    "expr",
    "let",
    "seq",
    "yes",
    "jq",
    "yq",
    "xmllint",
    "md5sum",
    "sha256sum",
    "openssl",
    # Build & compilation
    "make",
    "cmake",
    "ninja",
    "msbuild",  # Windows build tool
    # Windows-specific utilities
    "dir",
    "copy",
    "xcopy",
    "move",
    "del",
    "erase",
    "ren",
    "rename",
    "md",
    "rd",
    "where",  # Windows which
    "findstr",  # Windows grep
    "more",
    "type",  # Windows cat
    "robocopy",
    # Development tools
    "code",  # VS Code CLI
    "nano",
    "vim",
    "vi",
    "emacs",
    "notepad",
    # Debugging
    "strace",
    "ltrace",
    "gdb",
    "lldb",
}

# =============================================================================
# VALIDATED COMMANDS - Need extra validation even when allowed
# =============================================================================

VALIDATED_COMMANDS: dict[str, str] = {
    "rm": "validate_rm",
    "chmod": "validate_chmod",
    "pkill": "validate_pkill",
    "kill": "validate_kill",
    "killall": "validate_killall",
}


__all__ = ["BASE_COMMANDS", "VALIDATED_COMMANDS"]
