#!/usr/bin/env python3
"""
Cursor Reset CLI

Interactive command-line interface for managing Cursor trial resets.
Bypasses trial limits by regenerating device fingerprints.

Copyright (c) 2026 Y0oshi
Instagram: @rde0

All rights reserved. This software is provided for educational purposes only.
Unauthorized distribution or commercial use is prohibited.

Commands:
    /start  - Run aggressive reset (clears all storage)
    /light  - Run light reset (modifies config files only)
    /status - View current machine identifiers
    /help   - Display available commands
    /exit   - Close the application
"""

import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
import platform


# ------------------------------------------------------------
# Path Resolution
# ------------------------------------------------------------

def get_cursor_base_dir():
    """
    Returns the base directory where Cursor stores its configuration.
    Location varies by operating system.
    """
    system = platform.system()
    
    if system == "Windows":
        return Path(os.getenv("APPDATA", "")) / "Cursor"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Cursor"
    elif system == "Linux":
        return Path.home() / ".config" / "Cursor"
    else:
        raise OSError(f"Unsupported operating system: {system}")


def get_storage_file():
    """Returns path to the main storage.json configuration file."""
    return get_cursor_base_dir() / "User" / "globalStorage" / "storage.json"


def get_machineid_file():
    """Returns path to the machineid file (primary fingerprint in v2.x)."""
    return get_cursor_base_dir() / "machineid"


# ------------------------------------------------------------
# ID Generation
# ------------------------------------------------------------

def generate_hex_id():
    """Generates a 64-character hexadecimal machine identifier."""
    return os.urandom(32).hex()


def generate_uuid_id():
    """Generates a standard UUID string."""
    return str(uuid.uuid4())


# ------------------------------------------------------------
# Process Management
# ------------------------------------------------------------

def terminate_cursor():
    """
    Forcefully terminates all running Cursor processes.
    Returns True if processes were killed, False otherwise.
    """
    system = platform.system()
    
    try:
        if system == "Darwin":
            result = subprocess.run(["pkill", "-9", "-f", "Cursor"], capture_output=True)
        elif system == "Linux":
            result = subprocess.run(["pkill", "-9", "-f", "cursor"], capture_output=True)
        elif system == "Windows":
            result = subprocess.run(["taskkill", "/F", "/IM", "Cursor.exe"], capture_output=True)
        else:
            return False
        return result.returncode == 0
    except Exception:
        return False


# ------------------------------------------------------------
# Backup Operations
# ------------------------------------------------------------

def backup_directory(source_path, backup_name):
    """
    Creates a timestamped backup of a directory and clears the original.
    Returns True on success, False if source doesn't exist.
    """
    if not source_path.exists():
        return False
    
    backup_root = get_cursor_base_dir() / "backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_root / f"{backup_name}.backup_{timestamp}"
    
    shutil.copytree(source_path, backup_path)
    shutil.rmtree(source_path)
    source_path.mkdir(parents=True, exist_ok=True)
    
    return True


def backup_single_file(file_path, backup_name):
    """
    Creates a timestamped backup of a single file.
    Returns True on success, False if file doesn't exist.
    """
    if not file_path.exists():
        return False
    
    backup_root = get_cursor_base_dir() / "backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_root / f"{backup_name}.backup_{timestamp}"
    
    shutil.copy2(file_path, backup_path)
    return True


# ------------------------------------------------------------
# Reset Commands
# ------------------------------------------------------------

def reset_windows_machine_guid():
    """
    Resets the MachineGuid in Windows Registry.
    Requires Administrator privileges.
    """
    if platform.system() != "Windows":
        return
        
    try:
        import winreg
    except ImportError:
        return

    print("  [3b] Resetting Windows Registry...", end=" ")
    key_path = r"SOFTWARE\Microsoft\Cryptography"
    value_name = "MachineGuid"
    
    try:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY)
        except OSError:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS)
            
        # Generate new UUID
        new_guid = str(uuid.uuid4())
        
        # Set new value
        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, new_guid)
        winreg.CloseKey(key)
        
        print(f"done ({new_guid})")
    except PermissionError:
        print("failed (Run as Admin)")
    except Exception:
        print("failed")


def cmd_start():
    """
    Aggressive reset: Clears Local Storage, Session Storage, and regenerates all IDs.
    This is the recommended approach for Cursor 2.x.
    """
    print("\n[*] Starting Aggressive Reset (v3)...")
    print("-" * 45)
    
    # Step 1: Terminate Cursor
    print("  [1/5] Terminating Cursor processes...", end=" ")
    if terminate_cursor():
        print("done")
    else:
        print("(not running)")
    
    time.sleep(1)
    
    # Step 2: Clear Local Storage database
    print("  [2/5] Clearing Local Storage...", end=" ")
    local_storage_path = get_cursor_base_dir() / "Local Storage" / "leveldb"
    if backup_directory(local_storage_path, "Local_Storage"):
        print("done")
    else:
        print("(not found)")
    
    # Step 3: Clear Session Storage
    print("  [3/5] Clearing Session Storage...", end=" ")
    session_storage_path = get_cursor_base_dir() / "Session Storage"
    if backup_directory(session_storage_path, "Session_Storage"):
        print("done")
    else:
        print("(not found)")
        
    reset_windows_machine_guid()
    
    # Step 4: Reset machineid file
    print("  [4/5] Resetting machineid file...", end=" ")
    machineid_path = get_machineid_file()
    backup_single_file(machineid_path, "machineid")
    new_machineid = generate_uuid_id()
    with open(machineid_path, 'w') as file:
        file.write(new_machineid)
    print("done")
    
    # Step 5: Reset storage.json telemetry IDs
    print("  [5/5] Resetting storage.json...", end=" ")
    storage_path = get_storage_file()
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    backup_single_file(storage_path, "storage.json")
    
    config_data = {}
    if storage_path.exists():
        try:
            with open(storage_path, 'r') as file:
                config_data = json.load(file)
        except (json.JSONDecodeError, IOError):
            pass
    
    new_identifiers = {
        "telemetry.machineId": generate_hex_id(),
        "telemetry.macMachineId": generate_hex_id(),
        "telemetry.devDeviceId": generate_uuid_id(),
        "telemetry.sqmId": generate_uuid_id(),
    }
    config_data.update(new_identifiers)
    
    with open(storage_path, 'w') as file:
        json.dump(config_data, file, indent=2)
    print("done")
    
    # Summary
    print("-" * 45)
    print("[+] Reset complete!")
    print("\n[i] New identifiers generated:")
    for key, value in new_identifiers.items():
        print(f"    {key}: {value[:24]}...")
    print(f"    machineid: {new_machineid}")
    
    print("\n[!] Next steps:")
    print("    1. Open Cursor")
    print("    2. Create a new account / Sign in with a NEW email")


def cmd_light():
    """
    Light reset: Only modifies configuration files without clearing databases.
    Use this for older Cursor versions (pre-2.x).
    """
    print("\n[*] Starting Light Reset (v2)...")
    print("-" * 45)
    
    # Step 1: Terminate Cursor
    print("  [1/3] Terminating Cursor processes...", end=" ")
    if terminate_cursor():
        print("done")
    else:
        print("(not running)")
    
    # Step 2: Reset machineid file
    print("  [2/3] Resetting machineid file...", end=" ")
    machineid_path = get_machineid_file()
    backup_single_file(machineid_path, "machineid")
    new_machineid = generate_uuid_id()
    with open(machineid_path, 'w') as file:
        file.write(new_machineid)
    print("done")
    
    # Step 3: Reset storage.json
    print("  [3/3] Resetting storage.json...", end=" ")
    storage_path = get_storage_file()
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    backup_single_file(storage_path, "storage.json")
    
    config_data = {}
    if storage_path.exists():
        try:
            with open(storage_path, 'r') as file:
                config_data = json.load(file)
        except (json.JSONDecodeError, IOError):
            pass
    
    new_identifiers = {
        "telemetry.machineId": generate_hex_id(),
        "telemetry.macMachineId": generate_hex_id(),
        "telemetry.devDeviceId": generate_uuid_id(),
        "telemetry.sqmId": generate_uuid_id(),
    }
    config_data.update(new_identifiers)
    
    with open(storage_path, 'w') as file:
        json.dump(config_data, file, indent=2)
    print("done")
    
    print("-" * 45)
    print("[+] Light reset complete!")
    print("\n[!] Note: If this doesn't work, try /start for aggressive reset.")


def cmd_status():
    """Displays the current machine identifiers stored by Cursor."""
    print("\n[i] Current Machine Identifiers")
    print("-" * 45)
    
    # Read machineid file
    machineid_path = get_machineid_file()
    if machineid_path.exists():
        with open(machineid_path, 'r') as file:
            print(f"  machineid: {file.read().strip()}")
    else:
        print("  machineid: (not found)")
    
    # Read storage.json
    storage_path = get_storage_file()
    if storage_path.exists():
        try:
            with open(storage_path, 'r') as file:
                config_data = json.load(file)
            
            telemetry_keys = [
                "telemetry.machineId",
                "telemetry.macMachineId",
                "telemetry.devDeviceId",
                "telemetry.sqmId"
            ]
            
            for key in telemetry_keys:
                value = config_data.get(key, "(not set)")
                if len(str(value)) > 36:
                    value = str(value)[:36] + "..."
                print(f"  {key}: {value}")
        except (json.JSONDecodeError, IOError):
            print("  storage.json: (corrupted or unreadable)")
    else:
        print("  storage.json: (not found)")
    print()


def cmd_help():
    """Displays the help menu with available commands."""
    print("""
+------------------------------------------------------------+
|                  Cursor Reset CLI - Commands               |
+------------------------------------------------------------+
|  /start   Run aggressive reset (recommended for v2.x)      |
|  /light   Run light reset (for older versions)             |
|  /status  Display current machine identifiers              |
|  /help    Show this help menu                              |
|  /exit    Exit the application                             |
+------------------------------------------------------------+
""")


# ------------------------------------------------------------
# Main Application Loop
# ------------------------------------------------------------

def main():
    # Terminal color codes
    RED = "\033[91m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Determine terminal width for centering
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 90
    
    # Resize terminal on macOS if too narrow
    if platform.system() == "Darwin" and terminal_width < 90:
        print("\033[8;35;95t", end="")
        terminal_width = 95
    
    def center_text(text):
        """Centers text based on terminal width."""
        text_length = len(text)
        padding = max(0, (terminal_width - text_length) // 2)
        return " " * padding + text
    
    # ASCII art banner
    banner_lines = [
        "⠈⠙⠒⢦⣄⣸⣿⣿⠟⠉⠀⠀⠀⠀⠀⡀⠀⠀⡠⠀⢀⡄⠀⠀⠀⠙⢿⣤⡀⠀⠈⠙⢦⡀⠈⠙⣦⠀⠀⠁⠲⠿⣦⣤⣶⣷⢀⠀⠀⢀",
        "⠚⠉⣉⣭⣿⡟⠛⠁⠀⢀⡀⠀⠀⣠⡞⠃⢀⠞⠁⠀⣼⠁⠀⢰⠀⠀⡌⠁⠈⢦⡀⠀⠀⠙⢆⠀⠈⢧⠀⠀⠀⢤⡈⠻⣿⠿⣶⣇⣀⡀",
        "⣴⣿⠟⣹⣾⡏⠀⢠⠂⡤⠀⣠⠾⠋⠀⠀⣱⠂⠀⣰⣿⠀⢸⠈⡆⠀⠸⣆⠀⠀⢻⡄⠀⠰⡄⠁⠀⠈⣇⠀⠀⠀⢳⡀⠈⠻⡟⠷⣤⣌",
        "⠟⢡⡾⢣⡿⠁⠀⡎⡼⠀⢠⠁⢀⠄⢀⣾⠃⠀⡼⠋⢻⠀⠘⡀⢡⠀⠀⢹⣆⠀⠀⢿⣆⠀⠹⣆⣆⠀⢸⡀⠀⠀⠀⢷⡀⠀⠘⣆⠘⢧",
        "⠀⡽⢁⣿⠁⠀⢰⢃⠇⠀⡎⢀⠎⠀⢸⡏⠀⡜⠁⠀⢸⡀⠀⣇⠈⠂⠀⠀⣿⡆⠀⢸⠙⢦⡀⢻⣿⡆⠈⡇⠀⢠⠀⠸⡷⡄⠀⠘⡄⠀",
        "⡼⠁⠈⣿⠀⢀⣿⢸⠀⢰⡇⡸⠀⠀⣾⠀⡜⠀⠀⠀⠀⡇⠀⡿⡄⠀⠀⠀⢸⡹⣄⠀⡇⠀⠱⣄⣿⣿⡀⡇⠀⠈⣇⠀⣧⠘⢆⠀⢙⠀",
        "⠁⠀⠀⡇⢀⣾⡟⣰⢀⡟⡇⡇⠀⠀⣧⣼⣀⣀⣠⣄⣄⣼⡀⡇⢱⡀⠀⠀⠈⡿⣿⠶⡧⣄⣀⣸⣿⣽⣿⡇⠀⠀⢻⡀⢸⡆⠈⢧⠸⠀",
        "⠀⠀⠀⣇⡼⢸⣿⣿⣸⢤⣿⠁⡤⣾⣿⠋⠁⣀⣤⢤⣽⡲⢷⢸⠀⢳⡀⠀⠀⢱⣸⣄⣧⣤⣄⡈⠉⢿⣿⢧⠀⠀⢸⡇⢸⣿⠀⠀⢷⠂",
        "⠀⠀⠀⢹⠁⡞⢈⣿⡿⢮⣻⠀⡴⠡⢄⣴⣿⣯⣼⠀⠀⠉⠀⢿⡆⠀⠱⡀⠀⠸⣷⣿⣿⣤⡏⠙⣦⣘⠷⠺⡆⠀⢠⣷⢸⠘⡄⠀⠀⠀",
        "⠀⠀⠀⢈⣀⡇⢸⣏⠃⡖⢿⣴⠁⠀⠘⢿⣻⣿⣿⠀⠀⠀⠀⠀⠁⠀⠀⠱⡄⠀⡟⣿⣿⣿⠃⠀⠸⠃⠀⠀⣿⠀⢸⣿⡟⣟⡇⠀⠀⠀",
        "⠀⠀⠀⢸⢸⠇⢸⠘⢦⡳⢼⣽⡀⠀⠀⠀⠉⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢧⡇⠀⠈⠁⠀⠀⠀⠀⠀⢰⣿⣇⢸⢿⡆⢿⡇⠀⠀⢀",
        "⠀⠀⠀⢸⣸⠀⢸⠀⠀⠈⢢⠉⢻⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⡾⠛⣹⡞⢈⡇⢸⡇⠀⠀⢸",
        "⠀⠀⠀⠀⣿⠀⢸⠀⠀⠀⢸⠛⠋⢷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣷⢿⠀⠀⢸⣿⢸⡇⠀⠀⢸",
        "⠀⠀⠀⠀⣿⠀⢸⠆⠀⠀⢸⠀⠀⠈⢳⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⠏⡇⣸⠀⠀⢸⣿⠘⣧⠀⡀⢸",
        "⠀⠀⠀⠀⣿⠀⣿⠀⠀⠀⢸⠀⡀⠀⢠⠙⢦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⠀⠀⠀⠀⠀⣠⣞⠁⡸⠀⣿⡆⠀⠈⣿⣾⣻⠀⣿⠀",
        "⠀⠀⠀⠀⢸⠀⡏⠀⠀⠀⢸⢠⢇⠀⠘⡄⠀⠙⢦⡀⠀⠀⠀⠀⠀⢰⠟⠉⠐⠊⣇⠀⢀⡠⠞⣹⠏⢀⠇⠀⠋⣧⠀⠀⢹⣿⡏⠀⠿⡆",
        "⠀⠀⠀⠀⢸⠀⡇⠀⡤⠀⣼⣼⢸⠀⠀⢿⡀⠀⠀⡟⠷⣤⡀⠀⢀⡎⠀⡄⠀⡀⠸⣴⣿⣀⣠⡏⠀⠘⠀⠀⢸⠸⣄⣀⣀⣿⣧⣀⣠⢳",
        "⠀⠆⠀⠀⢸⣾⠀⡼⠀⠀⣷⠃⢸⠀⠀⠸⣷⡏⢯⡇⠀⠈⠻⣷⡼⠠⠖⠁⠀⠋⠀⣿⣏⡗⠈⠱⣖⢶⢶⠒⣺⡿⢿⢷⡶⠛⠉⠉⠉⠚",
        "⠀⠀⡀⠀⢸⡇⣰⠁⠀⢸⡏⠀⠈⣇⣀⣠⡿⠀⠀⠱⣄⠀⠀⢠⡇⠰⠆⢀⣠⣼⣇⣿⡏⠀⠀⠀⠈⢿⠾⢋⣝⣻⣿⣿⠃⠀⠀⠀⠀⠀",
        "⡀⠀⡇⠀⢸⣧⠃⠀⠀⣾⠁⠀⣀⣿⣿⡿⠀⠀⠀⠀⠈⠣⣀⣼⣕⣤⣤⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀⠘⣯⣡⣏⣽⣻⡿⠀⠀⠀⠀⠀⠀",
        "⠃⠀⠃⠀⣾⠃⠀⣀⣼⣷⠒⢻⣛⣿⣷⣧⠀⠀⠀⠀⠀⠀⣸⠉⠉⠉⠉⠉⠙⠋⠉⠉⠙⡇⠀⠀⠀⠀⢹⢭⣼⣾⣻⡇⠀⠀⠀⠀⠀⠀",
        "⠀⢸⠀⣸⣥⡖⣿⠿⣿⣿⢻⣟⠻⣏⣭⣿⠀⠀⠀⠀⠀⠀⠙⣶⣦⠤⣤⣤⢤⡤⣤⠖⠚⠁⠀⠀⠀⠀⠈⣏⣬⣹⣾⠁⠀⠀⠀⠀⠀⠀",
        "⠀⣠⠔⠋⠹⣯⠟⣷⢈⣭⠗⣦⡷⣎⣙⣻⠀⠀⠀⠀⠀⠀⣼⣿⣿⡞⠁⢸⢀⣿⠽⠗⠲⡀⠀⠀⠀⠀⠀⢿⡞⣿⣿⡄⠀⠀⠀⠀⠀⠀",
        "⡞⠁⠀⠀⠀⠘⣿⣱⣯⢀⡼⠟⣤⢞⣺⣿⡄⠀⠀⠀⢀⣼⣿⠿⢋⡠⠔⠋⠁⠀⠀⠀⠀⢻⣤⡀⠀⠀⠀⢸⣿⡟⣿⡇⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠘⣿⣇⠨⣡⢹⣻⣄⣿⣮⡇⠀⣀⣴⣿⠟⠉⠉⠉⠐⠂⠐⠒⠒⠒⠒⠒⠸⢯⣟⣲⣄⡀⢸⣿⡽⣿⡇⠀⠀⠀⠀⠀⠀",
    ]
    
    # Display banner
    print(f"\n{RED}")
    for line in banner_lines:
        print(center_text(line))
    
    # Display title and credits
    print()
    print(center_text(f"{BOLD}Cursor Reset CLI{RESET}{RED}"))
    print()
    print(center_text("Made by Y0oshi  |  IG: @rde0"))
    print(f"{RESET}")
    print()
    print(f"{CYAN}" + center_text("Type /start to reset Cursor trial"))
    print(center_text("Type /help for all commands") + f"{RESET}")
    
    # Command dispatcher
    available_commands = {
        "/start": cmd_start,
        "/light": cmd_light,
        "/status": cmd_status,
        "/help": cmd_help,
    }
    
    # Main input loop
    while True:
        try:
            user_input = input("\n> ").strip().lower()
            
            if not user_input:
                continue
            
            if user_input in ["/exit", "/quit", "exit", "quit"]:
                print("\nGoodbye!")
                break
            
            if user_input in available_commands:
                available_commands[user_input]()
            else:
                print(f"[?] Unknown command: {user_input}")
                print("    Type /help for available commands.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
