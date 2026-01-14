#!/usr/bin/env python3
"""
Cursor Trial Reset Tool

Performs a complete reset of all Cursor fingerprints and storage.
Compatible with Cursor 2.x.

Made By Y0oshi
Instagram: @rde0


WARNING: This will clear Local Storage and Session Storage databases.
Your Cursor settings will be preserved, but some cached data will be lost.
"""

import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
import platform


def get_cursor_base_dir() -> Path:
    """Get the base Cursor application support directory."""
    system = platform.system()
    if system == "Windows":
        return Path(os.getenv("APPDATA", "")) / "Cursor"
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Cursor"
    elif system == "Linux":
        return Path.home() / ".config" / "Cursor"
    else:
        raise OSError(f"Unsupported operating system: {system}")


def get_storage_file() -> Path:
    return get_cursor_base_dir() / "User" / "globalStorage" / "storage.json"


def get_machineid_file() -> Path:
    return get_cursor_base_dir() / "machineid"


def backup_dir(dir_path: Path, backup_name: str) -> Path | None:
    """Create a timestamped backup of a directory."""
    if dir_path.exists():
        backup_base = get_cursor_base_dir() / "backups"
        backup_base.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_base / f"{backup_name}.backup_{timestamp}"
        shutil.copytree(dir_path, backup_path)
        print(f"📦 Backup created: {backup_path}")
        return backup_path
    return None


def backup_file(file_path: Path, backup_name: str) -> Path | None:
    """Create a timestamped backup of a file."""
    if file_path.exists():
        backup_base = get_cursor_base_dir() / "backups"
        backup_base.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_base / f"{backup_name}.backup_{timestamp}"
        shutil.copy2(file_path, backup_path)
        print(f"📦 Backup created: {backup_path}")
        return backup_path
    return None


def kill_cursor_processes() -> bool:
    """Terminate all running Cursor processes."""
    system = platform.system()
    killed = False
    
    try:
        if system == "Darwin":
            result = subprocess.run(
                ["pkill", "-9", "-f", "Cursor"],
                capture_output=True,
                text=True
            )
            killed = result.returncode == 0
        elif system == "Linux":
            result = subprocess.run(
                ["pkill", "-9", "-f", "cursor"],
                capture_output=True,
                text=True
            )
            killed = result.returncode == 0
        elif system == "Windows":
            result = subprocess.run(
                ["taskkill", "/F", "/IM", "Cursor.exe"],
                capture_output=True,
                text=True
            )
            killed = result.returncode == 0
    except Exception as e:
        print(f"⚠️  Could not terminate Cursor processes: {e}")
        return False
    
    if killed:
        print("🔪 Cursor processes terminated.")
    else:
        print("ℹ️  No Cursor processes found running.")
    
    return True


def generate_machine_id() -> str:
    """Generate a random 64-character hex machine ID."""
    return os.urandom(32).hex()


def generate_uuid() -> str:
    """Generate a random UUID string."""
    return str(uuid.uuid4())


def clear_local_storage() -> bool:
    """Clear the Local Storage leveldb database."""
    ls_dir = get_cursor_base_dir() / "Local Storage" / "leveldb"
    if ls_dir.exists():
        backup_dir(ls_dir, "Local_Storage_leveldb")
        shutil.rmtree(ls_dir)
        ls_dir.mkdir(parents=True, exist_ok=True)
        print(f"🗑️  Cleared: {ls_dir}")
        return True
    return False


def clear_session_storage() -> bool:
    """Clear the Session Storage database."""
    ss_dir = get_cursor_base_dir() / "Session Storage"
    if ss_dir.exists():
        backup_dir(ss_dir, "Session_Storage")
        shutil.rmtree(ss_dir)
        ss_dir.mkdir(parents=True, exist_ok=True)
        print(f"🗑️  Cleared: {ss_dir}")
        return True
    return False


def reset_windows_machine_guid() -> bool:
    """
    Resets the MachineGuid in Windows Registry.
    Requires Administrator privileges.
    """
    if platform.system() != "Windows":
        return False
        
    try:
        import winreg
    except ImportError:
        return False

    print("Step 3b: Resetting Windows Registry MachineGuid...")
    key_path = r"SOFTWARE\Microsoft\Cryptography"
    value_name = "MachineGuid"
    
    try:
        # Open key with write permissions
        # Try 64-bit view first
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY)
        except OSError:
            # Fallback to default view
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_ALL_ACCESS)
            
        old_guid, _ = winreg.QueryValueEx(key, value_name)
        
        # Generate new UUID
        new_guid = str(uuid.uuid4())
        
        # Set new value
        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, new_guid)
        winreg.CloseKey(key)
        
        print(f"✅ Windows MachineGuid reset: {old_guid} -> {new_guid}")
        return True
    except PermissionError:
        print("⚠️  Permission denied: Run command prompt as Administrator to reset Windows Registry.")
        return False
    except Exception as e:
        print(f"⚠️  Failed to reset MachineGuid: {e}")
        return False


def reset_machineid_file() -> str:
    """Reset the machineid file."""
    machineid_file = get_machineid_file()
    backup_file(machineid_file, "machineid")
    
    new_id = generate_uuid()
    with open(machineid_file, 'w', encoding='utf-8') as f:
        f.write(new_id)
    
    print(f"✅ Reset: {machineid_file}")
    return new_id


def reset_storage_json() -> dict:
    """Reset all Cursor device IDs in storage.json."""
    storage_file = get_storage_file()
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    backup_file(storage_file, "storage.json")
    
    if storage_file.exists():
        with open(storage_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    
    new_ids = {
        "telemetry.machineId": generate_machine_id(),
        "telemetry.macMachineId": generate_machine_id(),
        "telemetry.devDeviceId": generate_uuid(),
        "telemetry.sqmId": generate_uuid(),
    }
    
    data.update(new_ids)
    
    with open(storage_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Reset: {storage_file}")
    return new_ids


def main():
    print("=" * 60)
    print("🔄 Cursor Trial Reset Tool v3 (Aggressive)")
    print("=" * 60)
    print()
    print("⚠️  This will clear Local Storage and Session Storage.")
    print("    Your settings are preserved. Backups will be created.")
    print()
    
    # Step 1: Kill Cursor
    print("Step 1: Terminating Cursor processes...")
    kill_cursor_processes()
    import time
    time.sleep(1)  # Give processes time to fully terminate
    print()
    
    # Step 2: Clear Local Storage (contains trial tracking data)
    print("Step 2: Clearing Local Storage database...")
    clear_local_storage()
    print()
    
    # Step 3: Clear Session Storage
    print("Step 3: Clearing Session Storage...")
    clear_session_storage()
    print()
    
    # Step 3b: Windows Registry (Windows only)
    reset_windows_machine_guid()
    print()
    
    # Step 4: Reset machineid file
    print("Step 4: Resetting machineid file...")
    try:
        new_machineid = reset_machineid_file()
    except Exception as e:
        print(f"⚠️  Could not reset machineid: {e}")
        new_machineid = None
    print()
    
    # Step 5: Reset storage.json IDs
    print("Step 5: Resetting storage.json IDs...")
    try:
        new_ids = reset_storage_json()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    if new_machineid:
        new_ids["machineid (file)"] = new_machineid
    
    print()
    print("🎉 Complete reset successful!")
    print()
    print("New IDs:")
    print(json.dumps(new_ids, indent=2))
    print()
    print("=" * 60)
    print("⚠️  IMPORTANT:")
    print("   1. Open Cursor")
    print("   2. Create a new account / Sign in with a NEW email")
    print("=" * 60)


if __name__ == "__main__":
    main()
