#!/usr/bin/env python3
"""
Test Full Access Mode - Alle Befehle erlaubt
============================================

Testet ob die "gefaehrlichen" Befehle jetzt auch erlaubt sind.
"""

from pathlib import Path
from security import validate_command
from project.command_registry.base import BASE_COMMANDS

print("="*70)
print("FULL ACCESS MODE TEST")
print("="*70)
print()

# Test "gefaehrliche" Befehle die vorher blockiert waren
dangerous_commands = [
    ("rm -rf /", "RM Root"),
    ("rm -rf /*", "RM Root Wildcard"),
    ("rm -rf ~/*", "RM Home"),
    ("chmod 777 /etc/passwd", "CHMOD Systemdatei"),
    ("chmod 777 anything", "CHMOD beliebig"),
    ("killall -9", "KILLALL alle"),
    ("killall python", "KILLALL Python"),
    ("pkill -9 systemd", "PKILL System-Prozess"),
    ("kill -9 1", "KILL PID 1"),
    ("dropdb production", "DROP Production DB"),
    ("psql -c 'DROP TABLE users'", "DROP TABLE"),
    ("redis-cli FLUSHALL", "Redis FLUSHALL"),
    ("mongo --eval 'db.dropDatabase()'", "Mongo DROP DB"),
    ("shutdown -h now", "Shutdown"),
    ("reboot", "Reboot"),
    ("sudo rm -rf /", "SUDO RM"),
    ("docker rm -f $(docker ps -a -q)", "Docker RM ALL"),
    ("kubectl delete all --all", "K8s DELETE ALL"),
    ("terraform destroy -auto-approve", "Terraform DESTROY"),
    ("reg add HKLM\\Software\\Test", "Registry WRITE"),
]

passed = 0
failed = 0

print("Teste 'gefaehrliche' Befehle (sollten jetzt ALLE erlaubt sein):")
print("-"*70)

for cmd, desc in dangerous_commands:
    allowed, reason = validate_command(cmd, Path.cwd())
    
    if allowed:
        status = "[OK] ERLAUBT"
        passed += 1
    else:
        status = f"[X] BLOCKIERT - {reason}"
        failed += 1
    
    print(f"{desc:30s} {status}")

print("-"*70)
print()

# Statistik
total = len(dangerous_commands)
percentage = (passed / total * 100) if total > 0 else 0

print(f"Ergebnis: {passed}/{total} ({percentage:.1f}%) erlaubt")
print()

# BASE_COMMANDS Statistik
print(f"Total BASE_COMMANDS: {len(BASE_COMMANDS)}")
print()

# Pruefen ob Full Access Mode aktiv
from security.validator_registry import FULL_ACCESS_MODE
print(f"FULL_ACCESS_MODE: {FULL_ACCESS_MODE}")

if FULL_ACCESS_MODE and percentage >= 90:
    print()
    print("="*70)
    print("[OK] ERFOLG! Full Access Mode ist AKTIV!")
    print("    - Alle Validatoren sind deaktiviert")
    print("    - Agents haben volle Systemkontrolle")
    print("    - Wie Claude in Cursor")
    print("="*70)
elif not FULL_ACCESS_MODE:
    print()
    print("[!] FULL_ACCESS_MODE ist DEAKTIVIERT")
    print("    Setze FULL_ACCESS_MODE=true in .env oder validator_registry.py")
else:
    print()
    print("[X] Einige Befehle sind noch blockiert - pruefe die Konfiguration")
