import platform
import sys
import subprocess
from ..core.wiper import DiskManager, WipeEngine
from ..utils.auth import ensure_admin

def print_welcome_msg():
    print("""
============================================================
  ____              _     __        _____ ____  _____ 
 / ___|  ___  _ __ (_)_ __ \\ \\      / /_ _|  _ \\| ____|
 | |   / _ \\| '_ \\| | '__| \\ \\ /\\ / / | || |_) |  _|  
 | |__| (_) | | | | | |     \\ V  V /  | ||  __/| |___ 
 \\____|\\___/|_| |_|_|_|      \\_/\\_/  |___|_|   |_____|
                                                     
============================================================
                  DATA WIPE UTILITY
============================================================

 ⚠️  WARNING: This process will IRREVERSIBLY ERASE 
    all data on the selected disk.

    Double-check your target before continuing.  
    There is NO recovery once started.  

============================================================
""")

def run_cli():
    ensure_admin()
    print_welcome_msg()

    disks = DiskManager.get_disks()
    if not disks:
        print("No disks found.")
        return

    print("List of available disks:")
    for disk in disks:
        print(f"  Disk {disk.number}: {disk.friendly_name} ({disk.size_gb:.1f} GB)")

    while True:
        choice = input("\nSelect which disk to wipe: ").strip()
        selected_disk = next((d for d in disks if d.number == choice), None)
        if selected_disk:
            break
        print(f"Error: Invalid disk number '{choice}'.")

    print(f"\n⚠️  About to wipe {selected_disk.friendly_name}. This is your final chance to abort.")
    confirm = input("Type 'ERASE' to confirm and start wiping: ")
    if confirm != 'ERASE':
        print("Operation cancelled.")
        return

    wiper = WipeEngine.get_system_wiper()
    system = platform.system()

    try:
        # Step 1: Wipe
        print("\n[1/3] Wiping disk...")
        wipe_cmd = wiper.wipe(selected_disk.path)
        subprocess.run(wipe_cmd, check=True)

        # Step 2: Initialize
        print("[2/3] Initializing disk (GPT)...")
        init_cmd = wiper.initialize_disk(selected_disk.path)
        subprocess.run(init_cmd, check=True)

        # Step 3: Partition and Format
        print("[3/3] Partitioning and formatting...")
        if system == "Windows":
            format_cmd = wiper.format_disk(selected_disk.path)
            subprocess.run(format_cmd, check=True)
        else:
            # Linux needs extra steps
            subprocess.run(wiper.create_partition(selected_disk.path), check=True)
            partition_path = f"{selected_disk.path}p1" if "nvme" in selected_disk.path else f"{selected_disk.path}1"
            subprocess.run(wiper.format_disk(partition_path), check=True)

        print(f"\n✅ All operations for {selected_disk.friendly_name} completed successfully!")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ An operation failed: {e}")
    except KeyboardInterrupt:
        print("\n\nOperation aborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
