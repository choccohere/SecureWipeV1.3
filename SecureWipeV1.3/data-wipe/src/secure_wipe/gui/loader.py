import os
import sys

def get_asset_path(filename: str) -> str:
    """Gets the absolute path to an asset file."""
    # If running as a frozen executable (e.g. via PyInstaller)
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, "secure_wipe", "assets", filename)
    
    # If running from source
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)

def get_theme_path() -> str:
    return get_asset_path("azure.tcl")

def get_icon_path() -> str:
    return get_asset_path("icon.ico")

def get_logo_path() -> str:
    return get_asset_path("logo.png")
