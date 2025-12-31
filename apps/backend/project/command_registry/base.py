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
    # ===========================================================================
    # FULL ACCESS MODE - Additional commands for unrestricted access
    # (Same permissions as Claude in Cursor / user on their own machine)
    # ===========================================================================
    # System administration (unrestricted)
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    "init",
    "telinit",
    "runlevel",
    # User & permission management
    "useradd",
    "userdel",
    "usermod",
    "groupadd",
    "groupdel",
    "groupmod",
    "passwd",
    "chpasswd",
    "newgrp",
    "su",
    "sudo",
    "visudo",
    "doas",
    # File system (unrestricted)
    "mount",
    "umount",
    "fdisk",
    "mkfs",
    "fsck",
    "dd",
    "parted",
    "lsblk",
    "blkid",
    "losetup",
    # Network administration
    "iptables",
    "ip6tables",
    "nft",
    "ufw",
    "firewall-cmd",
    "route",
    "arp",
    "brctl",
    "ethtool",
    "iwconfig",
    "nmcli",
    "systemd-resolve",
    "resolvectl",
    # Package management (all distros)
    "apt",
    "apt-get",
    "apt-cache",
    "dpkg",
    "yum",
    "dnf",
    "rpm",
    "zypper",
    "pacman",
    "brew",
    "port",
    "emerge",
    "snap",
    "flatpak",
    # Windows administration (full access)
    "runas",
    "net",  # net user, net localgroup, etc.
    "netsh",
    "schtasks",
    "bcdedit",
    "dism",
    "sfc",
    "chkdsk",
    "diskpart",
    "format",
    "wevtutil",
    "eventcreate",
    "cipher",
    "compact",
    "defrag",
    # Windows Registry (full access including write)
    # Note: reg is already in BASE_COMMANDS for read; now full access
    "regedit",
    "reg.exe",
    # PowerShell full access cmdlets
    "Start-Process",
    "Stop-Process",
    "Restart-Service",
    "Start-Service",
    "Stop-Service",
    "New-Item",
    "Remove-Item",
    "Copy-Item",
    "Move-Item",
    "Set-ItemProperty",
    "Get-ItemProperty",
    "New-ItemProperty",
    "Remove-ItemProperty",
    "Set-ExecutionPolicy",
    "Invoke-Command",
    "Invoke-Expression",
    "Invoke-WebRequest",
    # Database administration (full access)
    "dropdb",
    "createdb",
    "dropuser",
    "createuser",
    "pg_dump",
    "pg_restore",
    "pg_ctl",
    "mysqldump",
    "mysqladmin",
    "mysqlimport",
    "mongodump",
    "mongorestore",
    "mongo",
    "mongosh",
    "redis-cli",
    "redis-server",
    "sqlite3",
    # Container & orchestration
    "docker",
    "docker-compose",
    "podman",
    "buildah",
    "skopeo",
    "kubectl",
    "helm",
    "minikube",
    "kind",
    "k3s",
    "k9s",
    "crictl",
    "ctr",
    "nerdctl",
    # Cloud CLIs
    "aws",
    "gcloud",
    "az",
    "doctl",
    "linode-cli",
    "vultr-cli",
    "hcloud",
    "scaleway",
    "oci",
    "eksctl",
    "kops",
    # Infrastructure as Code
    "terraform",
    "terragrunt",
    "pulumi",
    "ansible",
    "ansible-playbook",
    "ansible-galaxy",
    "salt",
    "puppet",
    "chef",
    "vagrant",
    "packer",
    # Secrets & security
    "vault",
    "sops",
    "age",
    "gpg",
    "ssh-keygen",
    "ssh-add",
    "ssh-agent",
    "keychain",
    "pass",
    "gopass",
    # Cron & scheduling
    "crontab",
    "at",
    "batch",
    "atq",
    "atrm",
    # Logging & monitoring
    "journalctl",
    "dmesg",
    "logger",
    "logrotate",
    "tail",  # Already in base, but ensure it's here
    "multitail",
    # Misc admin
    "screen",
    "tmux",
    "byobu",
    "nohup",
    "disown",
    "bg",
    "fg",
    "nice",
    "renice",
    "ionice",
    "cpulimit",
    "ulimit",
    "setfacl",
    "getfacl",
    "xattr",
    "semanage",
    "restorecon",
    "chcon",
    "getenforce",
    "setenforce",
}

# =============================================================================
# VALIDATED COMMANDS - Commands that trigger extra validation
# =============================================================================
# NOTE: In FULL ACCESS MODE (default since 31.12.2025), these validations
# are BYPASSED. See security/validator_registry.py for details.
#
# To re-enable validation:
# 1. Set environment variable: FULL_ACCESS_MODE=false
# 2. Or edit security/validator_registry.py
#
# The validations would check:
# - rm: Block dangerous patterns like rm -rf /
# - chmod: Only allow safe modes like +x, 755
# - pkill/kill/killall: Only allow killing dev processes
VALIDATED_COMMANDS: dict[str, str] = {
    "rm": "validate_rm",
    "chmod": "validate_chmod",
    "pkill": "validate_pkill",
    "kill": "validate_kill",
    "killall": "validate_killall",
}


__all__ = ["BASE_COMMANDS", "VALIDATED_COMMANDS"]
