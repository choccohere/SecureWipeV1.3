import os
import platform
import sys

def check_admin_privileges() -> bool:
    """Checks for administrative (root/Administrator) privileges."""
    system = platform.system()
    if system == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    elif system == "Linux":
        return os.geteuid() == 0
    return False

def ensure_admin():
    if not check_admin_privileges():
        system = platform.system()
        if system == "Windows":
            print("ERROR: This application requires Administrator privileges. Please run as Administrator.")
        else:
            print("ERROR: This application requires root privileges. Please run with sudo.")
        sys.exit(1)
