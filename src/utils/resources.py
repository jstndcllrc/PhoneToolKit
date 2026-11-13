"""Resource path handling for PyInstaller bundled executable"""
import sys
import os
from pathlib import Path


def get_base_path() -> Path:
    """Get the base path for resources, works both in dev and PyInstaller bundle"""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        return Path(sys._MEIPASS)
    else:
        # Running in development:
        # resources.py is in src/utils/, so .parent.parent.parent is the project root
        project_root = Path(__file__).resolve().parent.parent.parent
        if (project_root / "resources").exists():
            return project_root
        # Fallback to parent of src
        return Path(__file__).resolve().parent.parent


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource file"""
    return get_base_path() / "resources" / relative_path


def get_data_path(relative_path: str) -> Path:
    """Get absolute path to data file (for user data, not bundled)"""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle - use executable directory
        return Path(sys.executable).parent / "data" / relative_path
    else:
        # Running in development
        return get_base_path() / "data" / relative_path


def ensure_data_dirs():
    """Ensure data directories exist"""
    data_dirs = [
        get_data_path(""),
        get_data_path("logs"),
        get_data_path("exports"),
    ]
    for d in data_dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
