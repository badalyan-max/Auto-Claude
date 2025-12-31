#!/usr/bin/env python3
"""
Test-Script für erweiterte Agent-Permissions
============================================

Testet ob die erweiterten Befehle erlaubt sind.
"""

from pathlib import Path
from security import validate_command
from project.command_registry.base import BASE_COMMANDS

# Colors
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def test_command(cmd: str, description: str) -> bool:
    """Testet ob ein Befehl erlaubt ist."""
    allowed, reason = validate_command(cmd, Path.cwd())
    
    # Windows-kompatible Symbole
    status = f"{Colors.GREEN}[OK] ERLAUBT{Colors.RESET}" if allowed else f"{Colors.RED}[X] BLOCKIERT{Colors.RESET}"
    print(f"{description:40s} {status}")
    
    if not allowed and reason:
        print(f"  {Colors.YELLOW}Grund: {reason}{Colors.RESET}")
    
    return allowed


def main():
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}TEST: Erweiterte Agent-Permissions{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    
    results = []
    
    # Git Operations
    print(f"{Colors.CYAN}Git & GitHub:{Colors.RESET}")
    results.append(test_command("git push origin main", "Git Push"))
    results.append(test_command("git push --force-with-lease", "Git Force Push (safe)"))
    results.append(test_command("git pull --rebase", "Git Pull"))
    results.append(test_command("gh pr create --title 'Test'", "GitHub CLI PR"))
    results.append(test_command("git lfs install", "Git LFS"))
    
    # Windows Commands
    print(f"\n{Colors.CYAN}Windows:{Colors.RESET}")
    results.append(test_command("powershell -Command Get-Process", "PowerShell"))
    results.append(test_command("cmd /c dir", "CMD"))
    results.append(test_command("tasklist", "Task List"))
    results.append(test_command("where python", "Where (Windows which)"))
    results.append(test_command("reg query HKCU\\Software", "Registry Query (read)"))
    
    # Build Tools
    print(f"\n{Colors.CYAN}Build & Compilation:{Colors.RESET}")
    results.append(test_command("make", "Make"))
    results.append(test_command("cmake --build .", "CMake"))
    results.append(test_command("msbuild /p:Configuration=Release", "MSBuild"))
    results.append(test_command("ninja", "Ninja"))
    
    # System Administration
    print(f"\n{Colors.CYAN}System Administration:{Colors.RESET}")
    results.append(test_command("systemctl status nginx", "SystemCtl"))
    results.append(test_command("netstat -an", "Netstat"))
    results.append(test_command("ps aux", "Process List"))
    
    # Development Tools
    print(f"\n{Colors.CYAN}Development Tools:{Colors.RESET}")
    results.append(test_command("code .", "VS Code CLI"))
    results.append(test_command("nano test.txt", "Nano"))
    results.append(test_command("vim test.txt", "Vim"))
    
    # Compression
    print(f"\n{Colors.CYAN}Archive & Compression:{Colors.RESET}")
    results.append(test_command("7z a archive.7z .", "7-Zip"))
    results.append(test_command("bzip2 file.txt", "bzip2"))
    results.append(test_command("xz file.txt", "xz"))
    
    # Security & Hashing
    print(f"\n{Colors.CYAN}Security & Hashing:{Colors.RESET}")
    results.append(test_command("sha256sum file.txt", "SHA256"))
    results.append(test_command("md5sum file.txt", "MD5"))
    results.append(test_command("openssl version", "OpenSSL"))
    
    # Network
    print(f"\n{Colors.CYAN}Network:{Colors.RESET}")
    results.append(test_command("traceroute google.com", "Traceroute"))
    results.append(test_command("nslookup google.com", "NSLookup"))
    results.append(test_command("telnet localhost 8080", "Telnet"))
    
    # Prüfe BASE_COMMANDS
    print(f"\n{Colors.CYAN}BASE_COMMANDS Statistik:{Colors.RESET}")
    print(f"  Anzahl Befehle: {Colors.GREEN}{len(BASE_COMMANDS)}{Colors.RESET}")
    
    # Prüfe spezifische Befehle in BASE_COMMANDS
    check_commands = ["git", "powershell", "msbuild", "cmake", "7z", "sha256sum"]
    print(f"\n{Colors.CYAN}In BASE_COMMANDS:{Colors.RESET}")
    for cmd in check_commands:
        in_base = cmd in BASE_COMMANDS
        status = f"{Colors.GREEN}[OK]{Colors.RESET}" if in_base else f"{Colors.RED}[X]{Colors.RESET}"
        print(f"  {cmd:20s} {status}")
    
    # Zusammenfassung
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}ZUSAMMENFASSUNG:{Colors.RESET}")
    print(f"  Bestanden: {Colors.GREEN}{passed}/{total}{Colors.RESET} ({percentage:.1f}%)")
    
    if percentage >= 90:
        print(f"\n{Colors.GREEN}{Colors.BOLD}[OK] ERFOLG! Erweiterte Permissions funktionieren!{Colors.RESET}")
    elif percentage >= 70:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}[!] TEILWEISE: Einige Befehle funktionieren nicht{Colors.RESET}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}[X] FEHLER: Viele Befehle blockiert{Colors.RESET}")
    
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    
    return percentage >= 90


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
