#!/usr/bin/env python3
"""
PhoneToolKit - All-in-One Android Device Management Tool
Combines Virus Remover (ADB App Uninstaller) and Finance Lock Guide
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFontDatabase

from ui.main_window import MainWindow
from utils.resources import get_resource_path


def setup_application():
    """Configure application-wide settings"""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("PhoneToolKit")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PhoneToolKit")

    # Set application font
    font = app.font()
    font.setFamily("Segoe UI")
    font.setPointSize(9)
    app.setFont(font)

    # Load application icon if available
    icon_path = get_resource_path("icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    return app


def main():
    """Main entry point"""
    app = setup_application()

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()