"""Main Window for PhoneToolKit"""
import logging
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QStatusBar, QLabel, QMenuBar, QMenu,
    QMessageBox, QSplashScreen, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, QSettings, QSize
from PySide6.QtGui import QIcon, QFont, QPixmap, QAction, QKeySequence, QPalette, QColor

from ui.virus_remover_tab import VirusRemoverTab
from ui.finance_guide_tab import FinanceGuideTab
from ui.help_tab import HelpTab
from utils.resources import get_resource_path, ensure_data_dirs
from utils.theme_assets import checkmark_url

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with tabbed interface"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PhoneToolKit v1.0.0 — by jstndcllrc")
        self.setMinimumSize(1000, 720)
        self.resize(1200, 850)

        # Ensure data directories exist
        ensure_data_dirs()

        # Auto-detect timer for devices
        self.auto_detect_timer = QTimer()
        self.auto_detect_timer.setInterval(5000)  # Check every 5 seconds
        self.auto_detect_timer.timeout.connect(self._auto_detect_devices)
        self.auto_detect_enabled = True

        # Track previous device state for auto-detect
        self._last_device_serials = set()
        self._last_device_count = 0

        self._init_ui()
        self._load_settings()
        self._setup_menu()
        self._setup_status_bar()
        self._apply_theme()

        # Set window icon
        icon_path = get_resource_path("icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Start auto-detect after UI is ready
        QTimer.singleShot(1000, self._start_auto_detect)

    def _init_ui(self):
        """Initialize UI components"""
        # Central tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.setCentralWidget(self.tabs)

        # Create tabs
        self.virus_tab = VirusRemoverTab()
        self.finance_tab = FinanceGuideTab()
        self.help_tab = HelpTab()

        # Add tabs with icons
        self.tabs.addTab(self.virus_tab, "🦠 Virus Remover")
        self.tabs.addTab(self.finance_tab, "🔓 Finance Guide")
        self.tabs.addTab(self.help_tab, "📚 Help & Docs")

        # Connect tab change signal
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Connect devices_updated signal from virus tab for non-blocking UI status updates
        self.virus_tab.devices_updated.connect(self._on_devices_updated)

        # Pass auto-detect timer to virus tab
        self.virus_tab.set_auto_detect_timer(self.auto_detect_timer)

    def _apply_theme(self):
        """Apply application theme - supports light/dark mode"""
        settings = QSettings("PhoneToolKit", "MainWindow")
        dark_mode = settings.value("darkMode", False, type=bool)

        if dark_mode:
            self._apply_dark_theme()
        else:
            self._apply_light_theme()

        # Update child tabs that maintain custom sub-styles
        if hasattr(self, 'finance_tab') and hasattr(self.finance_tab, 'update_theme'):
            self.finance_tab.update_theme(dark_mode)
        if hasattr(self, 'help_tab') and hasattr(self.help_tab, 'update_theme'):
            self.help_tab.update_theme(dark_mode)

    def _apply_light_theme(self):
        """Apply modern light theme - HIGH CONTRAST, MODERN, EYE-FRIENDLY"""
        qss = """
            /* ===== COLOR PALETTE (Light) ===== */
            /* Primary: Professional Blue #1e40af */
            /* Accent: Vibrant Teal #0d9488 */
            /* Surface: Pure White #ffffff */
            /* Elevated: Light Gray #f1f5f9 */
            /* Border: Clear Gray #cbd5e1 */
            /* Text Primary: Near Black #0f172a */
            /* Text Secondary: Medium Slate #475569 */
            /* Success: Emerald #059669 */
            /* Warning: Amber #d97706 */
            /* Danger: Red #dc2626 */
            /* Focus Ring: Teal #0d9488 */

            /* ===== BASE ===== */
            QMainWindow {
                background-color: #f8fafc;
                color: #0f172a;
            }
            QWidget {
                color: #0f172a;
                font-family: "Segoe UI", "Microsoft YaHei UI", "PingFang SC", sans-serif;
            }

            /* ===== TABS ===== */
            QTabWidget::pane {
                border: 2px solid #cbd5e1;
                background: #ffffff;
                border-radius: 8px;
                margin-top: -1px;
            }
            QTabBar::tab {
                background: #f1f5f9;
                border: 2px solid #cbd5e1;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 12px 24px;
                margin-right: 2px;
                font-weight: 700;
                font-size: 13px;
                color: #334155;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom: 3px solid #0d9488;
                color: #0d9488;
            }
            QTabBar::tab:hover:!selected {
                background: #e2e8f0;
                color: #1e40af;
            }

            /* ===== GROUP BOXES ===== */
            QGroupBox {
                font-weight: 700;
                font-size: 14px;
                border: 2px solid #cbd5e1;
                border-radius: 10px;
                margin-top: 18px;
                padding-top: 16px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 10px;
                color: #1e40af;
                background-color: #ffffff;
            }

            /* ===== BUTTONS ===== */
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px 20px;
                min-height: 32px;
                font-size: 13px;
                font-weight: 600;
                color: #0f172a;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                border-color: #94a3b8;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
                border-color: #64748b;
            }
            QPushButton:disabled {
                color: #94a3b8;
                background-color: #f1f5f9;
                border-color: #e2e8f0;
            }
            /* Primary button - TEAL with WHITE text */
            QPushButton[primary="true"] {
                background-color: #0d9488;
                border-color: #0f766e;
                color: #ffffff;
            }
            QPushButton[primary="true"]:hover {
                background-color: #0f766e;
                border-color: #115e59;
            }
            QPushButton[primary="true"]:pressed {
                background-color: #115e59;
            }
            /* Danger button - RED with WHITE text */
            QPushButton[danger="true"] {
                background-color: #dc2626;
                border-color: #b91c1c;
                color: #ffffff;
            }
            QPushButton[danger="true"]:hover {
                background-color: #b91c1c;
                border-color: #991b1b;
            }
            QPushButton[danger="true"]:pressed {
                background-color: #991b1b;
            }

            /* ===== INPUTS ===== */
            QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {
                border: 2px solid #cbd5e1;
                border-radius: 8px;
                padding: 10px 14px;
                background: #ffffff;
                font-size: 13px;
                font-weight: 500;
                color: #0f172a;
                selection-background-color: #0d9488;
                selection-color: #ffffff;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border-color: #0d9488;
                outline: none;
            }
            QLineEdit:disabled, QComboBox:disabled, QTextEdit:disabled {
                background-color: #f1f5f9;
                color: #94a3b8;
                border-color: #e2e8f0;
            }
            QComboBox {
                padding-right: 36px;
            }
            QComboBox::drop-down {
                border: none;
                width: 32px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 7px solid #475569;
                margin-right: 12px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #cbd5e1;
                background: #ffffff;
                selection-background-color: #0d9488;
                selection-color: #ffffff;
                outline: none;
                color: #0f172a;
            }

            /* ===== TABLES ===== */
            QTableWidget {
                border: 2px solid #cbd5e1;
                gridline-color: #e2e8f0;
                background: #ffffff;
                alternate-background-color: #f8fafc;
                font-size: 13px;
                color: #0f172a;
            }
            QTableWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #e2e8f0;
                color: #0f172a;
            }
            QTableWidget::item:selected {
                background-color: #0d9488;
                color: #ffffff;
            }
            QTableWidget::item:hover {
                background-color: #f0fdfa;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                border: 2px solid #cbd5e1;
                border-bottom: 3px solid #cbd5e1;
                padding: 8px 10px;
                font-weight: 700;
                font-size: 12px;
                color: #334155;
            }

            /* ===== SPLITTER ===== */
            QSplitter::handle {
                background-color: #cbd5e1;
            }
            QSplitter::handle:hover {
                background-color: #0d9488;
            }
            QSplitter::handle:vertical {
                height: 6px;
            }
            QSplitter::handle:horizontal {
                width: 6px;
            }

            /* ===== SCROLLBARS ===== */
            QScrollBar:vertical {
                background: #f1f5f9;
                width: 12px;
                border: none;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #94a3b8;
                min-height: 50px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #64748b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }

            /* ===== PROGRESS BAR ===== */
            QProgressBar {
                border: 2px solid #cbd5e1;
                border-radius: 8px;
                text-align: center;
                background: #f1f5f9;
                height: 24px;
                font-size: 12px;
                font-weight: 600;
                color: #0f172a;
            }
            QProgressBar::chunk {
                background-color: #0d9488;
                border-radius: 6px;
            }

            /* ===== STATUS BAR ===== */
            QStatusBar {
                background: #f1f5f9;
                border-top: 2px solid #cbd5e1;
                color: #334155;
            }

            /* ===== MENUS ===== */
            QMenuBar {
                background: #ffffff;
                border-bottom: 2px solid #cbd5e1;
                padding: 4px;
            }
            QMenuBar::item {
                padding: 10px 18px;
                background: transparent;
                border-radius: 6px;
                color: #0f172a;
                font-weight: 500;
            }
            QMenuBar::item:selected {
                background: #f0fdfa;
                color: #0d9488;
            }
            QMenu {
                background: #ffffff;
                border: 2px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px;
            }
            QMenu::item {
                padding: 10px 28px;
                border-radius: 6px;
                color: #0f172a;
            }
            QMenu::item:selected {
                background: #0d9488;
                color: #ffffff;
            }
            QMenu::separator {
                height: 2px;
                background: #cbd5e1;
                margin: 8px 16px;
            }

            /* ===== CHECKBOXES ===== */
            QCheckBox {
                spacing: 10px;
                color: #0f172a;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border-radius: 5px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #cbd5e1;
                background: #ffffff;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #0d9488;
                background: #f0fdfa;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #0d9488;
                background: #0d9488;
                image: __CHECKMARK__;
            }
            QCheckBox::indicator:checked:hover {
                background: #0f766e;
                border-color: #0f766e;
            }

            /* ===== ITEM VIEW CHECK INDICATORS (Installed Applications) =====
               The Select column uses native checkable items. Without explicit
               rules, the native style draws its own indicator whose size and
               shape vary by platform/DPR and can double up with checkbox
               styling. Styling the indicator here guarantees exactly one
               uniformly sized, centred checkbox in every row. */
            QTableWidget#packageTable::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
            }
            QTableWidget#packageTable::indicator:unchecked {
                border: 2px solid #cbd5e1;
                background: #ffffff;
            }
            QTableWidget#packageTable::indicator:unchecked:hover {
                border-color: #0d9488;
                background: #f0fdfa;
            }
            QTableWidget#packageTable::indicator:checked {
                border: 2px solid #0d9488;
                background: #0d9488;
                image: __CHECKMARK__;
            }
            QTableWidget#packageTable::indicator:checked:hover {
                background: #0f766e;
                border-color: #0f766e;
            }

            /* ===== LABELS ===== */
            QLabel {
                color: #0f172a;
            }

            /* ===== TOOLTIPS ===== */
            QToolTip {
                background-color: #0f172a;
                color: #ffffff;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
            }
        """
        self.setStyleSheet(
            qss.replace("__CHECKMARK__", checkmark_url("#ffffff"))
        )

    def _apply_dark_theme(self):
        """Apply modern dark theme - HIGH CONTRAST, MODERN, EYE-FRIENDLY"""
        qss = """
            /* ===== COLOR PALETTE (Dark) ===== */
            /* Primary: Bright Teal #00d4aa */
            /* Accent: Vibrant Teal #14f0b8 */
            /* Surface: True Black #0a0a0a */
            /* Elevated: Dark Charcoal #1a1a1a */
            /* Border: Clear Gray #334155 */
            /* Text Primary: Pure White #ffffff */
            /* Text Secondary: Medium Gray #cbd5e1 */
            /* Success: Emerald #10b981 */
            /* Warning: Amber #f59e0b */
            /* Danger: Red #ef4444 */
            /* Focus Ring: Teal #00d4aa */

            /* ===== BASE ===== */
            QMainWindow {
                background-color: #0a0a0a;
                color: #ffffff;
            }
            QWidget {
                color: #ffffff;
                font-family: "Segoe UI", "Microsoft YaHei UI", "PingFang SC", sans-serif;
            }

            /* ===== TABS ===== */
            QTabWidget::pane {
                border: 2px solid #334155;
                background: #1a1a1a;
                border-radius: 8px;
                margin-top: -1px;
            }
            QTabBar::tab {
                background: #1a1a1a;
                border: 2px solid #334155;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 12px 24px;
                margin-right: 2px;
                font-weight: 700;
                font-size: 13px;
                color: #94a3b8;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: #0a0a0a;
                border-bottom: 3px solid #00d4aa;
                color: #00d4aa;
            }
            QTabBar::tab:hover:!selected {
                background: #2a2a2a;
                color: #ffffff;
            }

            /* ===== GROUP BOXES ===== */
            QGroupBox {
                font-weight: 700;
                font-size: 14px;
                border: 2px solid #334155;
                border-radius: 10px;
                margin-top: 18px;
                padding-top: 16px;
                background-color: #1a1a1a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 10px;
                color: #00d4aa;
                background-color: #1a1a1a;
            }

            /* ===== BUTTONS ===== */
            QPushButton {
                background-color: #1a1a1a;
                border: 2px solid #334155;
                border-radius: 8px;
                padding: 10px 20px;
                min-height: 32px;
                font-size: 13px;
                font-weight: 600;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                border-color: #475569;
            }
            QPushButton:pressed {
                background-color: #0a0a0a;
                border-color: #334155;
            }
            QPushButton:disabled {
                color: #565656;
                background-color: #1a1a1a;
                border-color: #2a2a2a;
            }
            /* Primary button - TEAL with BLACK text */
            QPushButton[primary="true"] {
                background-color: #00d4aa;
                border-color: #00b894;
                color: #000000;
            }
            QPushButton[primary="true"]:hover {
                background-color: #00c09a;
                border-color: #00a086;
            }
            QPushButton[primary="true"]:pressed {
                background-color: #00a086;
            }
            /* Danger button - RED with WHITE text */
            QPushButton[danger="true"] {
                background-color: #ef4444;
                border-color: #dc2626;
                color: #ffffff;
            }
            QPushButton[danger="true"]:hover {
                background-color: #dc2626;
                border-color: #b91c1c;
            }
            QPushButton[danger="true"]:pressed {
                background-color: #b91c1c;
            }

            /* ===== INPUTS ===== */
            QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {
                border: 2px solid #334155;
                border-radius: 8px;
                padding: 10px 14px;
                background: #1a1a1a;
                font-size: 13px;
                font-weight: 500;
                color: #ffffff;
                selection-background-color: #00d4aa;
                selection-color: #000000;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border-color: #00d4aa;
                outline: none;
            }
            QLineEdit:disabled, QComboBox:disabled, QTextEdit:disabled {
                background-color: #0a0a0a;
                color: #565656;
                border-color: #2a2a2a;
            }
            QComboBox {
                padding-right: 36px;
            }
            QComboBox::drop-down {
                border: none;
                width: 32px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 7px solid #94a3b8;
                margin-right: 12px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #334155;
                background: #1a1a1a;
                selection-background-color: #00d4aa;
                selection-color: #000000;
                outline: none;
                color: #ffffff;
            }

            /* ===== TABLES ===== */
            QTableWidget {
                border: 2px solid #334155;
                gridline-color: #2a2a2a;
                background: #1a1a1a;
                alternate-background-color: #1f1f1f;
                font-size: 13px;
                color: #ffffff;
            }
            QTableWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #2a2a2a;
                color: #ffffff;
            }
            QTableWidget::item:selected {
                background-color: #00d4aa;
                color: #000000;
            }
            QTableWidget::item:hover {
                background-color: #1a2e2a;
            }
            QHeaderView::section {
                background-color: #1f1f1f;
                border: 2px solid #334155;
                border-bottom: 3px solid #334155;
                padding: 8px 10px;
                font-weight: 700;
                font-size: 12px;
                color: #cbd5e1;
            }

            /* ===== SPLITTER ===== */
            QSplitter::handle {
                background-color: #334155;
            }
            QSplitter::handle:hover {
                background-color: #00d4aa;
            }
            QSplitter::handle:vertical {
                height: 6px;
            }
            QSplitter::handle:horizontal {
                width: 6px;
            }

            /* ===== SCROLLBARS ===== */
            QScrollBar:vertical {
                background: #0a0a0a;
                width: 12px;
                border: none;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #475569;
                min-height: 50px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #64748b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }

            /* ===== PROGRESS BAR ===== */
            QProgressBar {
                border: 2px solid #334155;
                border-radius: 8px;
                text-align: center;
                background: #1a1a1a;
                height: 24px;
                font-size: 12px;
                font-weight: 600;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #00d4aa;
                border-radius: 6px;
            }

            /* ===== STATUS BAR ===== */
            QStatusBar {
                background: #1a1a1a;
                border-top: 2px solid #334155;
                color: #94a3b8;
            }

            /* ===== MENUS ===== */
            QMenuBar {
                background: #0a0a0a;
                border-bottom: 2px solid #334155;
                padding: 4px;
            }
            QMenuBar::item {
                padding: 10px 18px;
                background: transparent;
                border-radius: 6px;
                color: #ffffff;
                font-weight: 500;
            }
            QMenuBar::item:selected {
                background: #002b24;
                color: #00d4aa;
            }
            QMenu {
                background: #1a1a1a;
                border: 2px solid #334155;
                border-radius: 8px;
                padding: 8px;
            }
            QMenu::item {
                padding: 10px 28px;
                border-radius: 6px;
                color: #ffffff;
            }
            QMenu::item:selected {
                background: #002b24;
                color: #00d4aa;
            }
            QMenu::separator {
                height: 2px;
                background: #334155;
                margin: 8px 16px;
            }

            /* ===== CHECKBOXES ===== */
            QCheckBox {
                spacing: 10px;
                color: #ffffff;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border-radius: 5px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #475569;
                background: #1a1a1a;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #00d4aa;
                background: #001f1a;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #00d4aa;
                background: #00d4aa;
                image: __CHECKMARK__;
            }
            QCheckBox::indicator:checked:hover {
                background: #00b894;
                border-color: #00b894;
            }

            /* ===== ITEM VIEW CHECK INDICATORS (Installed Applications) =====
               Same rationale as the light theme: style the native item-view
               indicator explicitly so each row shows exactly one checkbox,
               identical in size, border and centring across rows. */
            QTableWidget#packageTable::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
            }
            QTableWidget#packageTable::indicator:unchecked {
                border: 2px solid #475569;
                background: #1a1a1a;
            }
            QTableWidget#packageTable::indicator:unchecked:hover {
                border-color: #00d4aa;
                background: #001f1a;
            }
            QTableWidget#packageTable::indicator:checked {
                border: 2px solid #00d4aa;
                background: #00d4aa;
                image: __CHECKMARK__;
            }
            QTableWidget#packageTable::indicator:checked:hover {
                background: #00b894;
                border-color: #00b894;
            }

            /* ===== LABELS ===== */
            QLabel {
                color: #ffffff;
            }

            /* ===== TOOLTIPS ===== */
            QToolTip {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
            }
        """

        self.setStyleSheet(
            qss.replace("__CHECKMARK__", checkmark_url("#000000"))
        )

    def toggle_theme(self):
        """Toggle between light and dark theme"""
        settings = QSettings("PhoneToolKit", "MainWindow")
        dark_mode = not settings.value("darkMode", False, type=bool)
        settings.setValue("darkMode", dark_mode)
        self._apply_theme()
        # Update menu checkbox
        if hasattr(self, 'theme_action'):
            self.theme_action.setChecked(dark_mode)

    def _setup_menu(self):
        """Setup menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        refresh_action = QAction("🔄 Refresh Devices", self)
        refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
        refresh_action.triggered.connect(self.virus_tab.refresh_devices)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        export_log_action = QAction("📤 Export Virus Remover Log", self)
        export_log_action.triggered.connect(self.virus_tab._export_log)
        file_menu.addAction(export_log_action)

        file_menu.addSeparator()

        exit_action = QAction("❌ Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        virus_action = QAction("🦠 Virus Remover", self)
        virus_action.setShortcut("Ctrl+1")
        virus_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        view_menu.addAction(virus_action)

        finance_action = QAction("🔓 Finance Guide", self)
        finance_action.setShortcut("Ctrl+2")
        finance_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        view_menu.addAction(finance_action)

        help_action = QAction("📚 Help & Docs", self)
        help_action.setShortcut("Ctrl+3")
        help_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        view_menu.addAction(help_action)

        view_menu.addSeparator()

        # Theme toggle - CHECKABLE ACTION
        self.theme_action = QAction("🌙 Dark Mode", self)
        self.theme_action.setCheckable(True)
        self.theme_action.setChecked(self._is_dark_mode())
        self.theme_action.setToolTip("Toggle between Light and Dark theme")
        self.theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(self.theme_action)

        # Auto-detect toggle
        self.auto_detect_action = QAction("🔍 Auto-Detect Devices", self)
        self.auto_detect_action.setCheckable(True)
        self.auto_detect_action.setChecked(self.auto_detect_enabled)
        self.auto_detect_action.triggered.connect(self._toggle_auto_detect)
        view_menu.addAction(self.auto_detect_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        adb_restart = QAction("🔧 Restart ADB Server", self)
        adb_restart.triggered.connect(self._restart_adb)
        tools_menu.addAction(adb_restart)

        tools_menu.addSeparator()

        expand_all = QAction("🔽 Expand All Finance Cards", self)
        expand_all.triggered.connect(self.finance_tab._expand_all)
        tools_menu.addAction(expand_all)

        collapse_all = QAction("🔼 Collapse All Finance Cards", self)
        collapse_all.triggered.connect(self.finance_tab._collapse_all)
        tools_menu.addAction(collapse_all)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        contents_action = QAction("📖 Contents", self)
        contents_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        contents_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        help_menu.addAction(contents_action)

        help_menu.addSeparator()

        about_action = QAction("ℹ️ About PhoneToolKit", self)
        about_action.triggered.connect(self.help_tab._show_about)
        help_menu.addAction(about_action)

    def _is_dark_mode(self):
        settings = QSettings("PhoneToolKit", "MainWindow")
        return settings.value("darkMode", False, type=bool)

    def _toggle_auto_detect(self, enabled: bool):
        self.auto_detect_enabled = enabled
        if enabled:
            if not self.virus_tab.current_device:
                self.auto_detect_timer.start()
                self.status_label.setText("Auto-detect scanning for devices...")
                self.auto_detect_indicator.setStyleSheet("color: #00d4aa; padding: 0 8px; font-size: 11px; font-weight: 600;")
                self.auto_detect_indicator.setText("🔍 Auto-detect: ON")
            else:
                self.auto_detect_timer.stop()
                self.status_label.setText("Device connected (scanning paused)")
                self.auto_detect_indicator.setStyleSheet("color: #059669; padding: 0 8px; font-size: 11px; font-weight: 600;")
                self.auto_detect_indicator.setText("📱 Device Connected")
        else:
            self.auto_detect_timer.stop()
            self.status_label.setText("Auto-detect disabled")
            self.auto_detect_indicator.setStyleSheet("color: #ef4444; padding: 0 8px; font-size: 11px; font-weight: 600;")
            self.auto_detect_indicator.setText("🔍 Auto-detect: OFF")

    def _start_auto_detect(self):
        if self.auto_detect_enabled and not self.virus_tab.current_device:
            self.auto_detect_timer.start()

    def _auto_detect_devices(self):
        """Auto-detect devices in background asynchronously without blocking the GUI thread"""
        if not self.auto_detect_enabled:
            return

        # If device is already detected, stop scanning immediately!
        if self.virus_tab.current_device:
            if self.auto_detect_timer.isActive():
                self.auto_detect_timer.stop()
            self.auto_detect_indicator.setText("📱 Device Connected")
            self.auto_detect_indicator.setStyleSheet("color: #059669; padding: 0 10px; font-size: 11px; font-weight: 600;")
            return

        # Delegate device check to virus_tab worker thread (completely non-blocking)
        self.virus_tab.refresh_devices(silent=True)

    def _on_devices_updated(self, devices: list):
        """Handle device list update from background worker thread"""
        current_serials = {d.serial for d in devices}
        current_count = len(devices)

        self._last_device_serials = current_serials
        self._last_device_count = current_count

        if devices:
            dev = devices[0]
            # Device detected! Stop background scanning timer immediately as requested
            if self.auto_detect_timer.isActive():
                self.auto_detect_timer.stop()
                logger.info("Device detected: stopping background scanning timer")

            self.auto_detect_indicator.setText("📱 Device Connected")
            self.auto_detect_indicator.setToolTip("Scanning stopped: device is connected. Click 'Refresh Devices' to scan again.")
            self.auto_detect_indicator.setStyleSheet("color: #059669; padding: 0 10px; font-size: 11px; font-weight: 600;")

            self.device_status.setText(f"📱 {dev.model or dev.serial}")
            if self._is_dark_mode():
                self.device_status.setStyleSheet("color: #00d4aa; padding: 0 10px; font-weight: 600;")
            else:
                self.device_status.setStyleSheet("color: #00d4aa; padding: 0 10px; font-weight: 600;")
            self.status_label.setText(f"Connected: {dev.model or dev.serial}")
        else:
            self.device_status.setText("No device")
            self.device_status.setStyleSheet("color: #94a3b8; padding: 0 10px;")
            self.status_label.setText("No device connected")

            # When no device is connected, keep scanning active so plugged-in devices are detected
            if self.auto_detect_enabled and not self.auto_detect_timer.isActive():
                self.auto_detect_timer.start()
                self.auto_detect_indicator.setText("🔍 Auto-detect: ON")
                self.auto_detect_indicator.setStyleSheet("color: #00d4aa; padding: 0 10px; font-size: 11px; font-weight: 600;")

    def _setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 0 10px; font-weight: 500;")
        self.status_bar.addWidget(self.status_label)

        # Auto-detect indicator
        self.auto_detect_indicator = QLabel("🔍 Auto-detect: ON")
        self.auto_detect_indicator.setStyleSheet("color: #00d4aa; padding: 0 10px; font-size: 11px; font-weight: 600;")
        self.status_bar.addPermanentWidget(self.auto_detect_indicator)

        self.device_status = QLabel("No device")
        self.device_status.setStyleSheet("color: #94a3b8; padding: 0 10px;")
        self.status_bar.addPermanentWidget(self.device_status)

        self.version_label = QLabel("v1.0.0")
        self.version_label.setStyleSheet("color: #64748b; padding: 0 10px;")
        self.status_bar.addPermanentWidget(self.version_label)

        # Developer credit in status bar
        import webbrowser
        self.dev_label = QLabel("<a href='https://www.facebook.com/jstndcllrc/' style='color:#00d4aa;text-decoration:none;font-weight:600;'>Built by jstndcllrc</a>")
        self.dev_label.setOpenExternalLinks(True)
        self.dev_label.setToolTip("Facebook: https://www.facebook.com/jstndcllrc/")
        self.dev_label.setStyleSheet("padding: 0 10px; font-size: 11px;")
        self.status_bar.addPermanentWidget(self.dev_label)

    def _on_tab_changed(self, index: int):
        """Handle tab change"""
        tab_names = ["Virus Remover", "Finance Guide", "Help & Docs"]
        if 0 <= index < len(tab_names):
            self.status_label.setText(f"Current: {tab_names[index]}")

        # Update device status from virus tab
        if index == 0 and self.virus_tab.current_device:
            self.device_status.setText(f"📱 {self.virus_tab.current_device.model or self.virus_tab.current_device.serial}")
            if self._is_dark_mode():
                self.device_status.setStyleSheet("color: #00d4aa; padding: 0 10px; font-weight: 600;")
            else:
                self.device_status.setStyleSheet("color: #00d4aa; padding: 0 10px; font-weight: 600;")
        else:
            self.device_status.setText("No device")
            self.device_status.setStyleSheet("color: #94a3b8; padding: 0 10px;")

    def _restart_adb(self):
        """Restart ADB server"""
        from services.adb_service import get_adb_service, CREATE_NO_WINDOW
        import subprocess
        try:
            adb_path = get_adb_service().adb_path
            subprocess.run([adb_path, "kill-server"], capture_output=True, timeout=5,
                           encoding="utf-8", errors="replace", creationflags=CREATE_NO_WINDOW)
            subprocess.run([adb_path, "start-server"], capture_output=True, timeout=5,
                           encoding="utf-8", errors="replace", creationflags=CREATE_NO_WINDOW)
            result = subprocess.run([adb_path, "devices"], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=5,
                                    creationflags=CREATE_NO_WINDOW)
            self.status_label.setText("ADB server restarted")
            QMessageBox.information(self, "ADB Restarted", f"ADB server restarted.\n\nDevices:\n{result.stdout}")
            # Reset device tracking after ADB restart and force refresh
            self._last_device_serials = set()
            self._last_device_count = 0
            self.virus_tab.refresh_devices(silent=False, force_reload=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to restart ADB:\n{e}")

    def _load_settings(self):
        """Load window settings"""
        settings = QSettings("PhoneToolKit", "MainWindow")

        # Window geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            # Ensure window has ample vertical height if previously saved with a cramped size
            if self.height() < 820:
                self.resize(max(self.width(), 1200), 850)
        else:
            # Center on screen
            screen = self.screen().availableGeometry()
            self.move(
                (screen.width() - self.width()) // 2,
                (screen.height() - self.height()) // 2
            )

        # Window state
        state = settings.value("windowState")
        if state:
            self.restoreState(state)

        # Last tab
        last_tab = settings.value("lastTab", 0, type=int)
        self.tabs.setCurrentIndex(last_tab)

    def _save_settings(self):
        """Save window settings"""
        settings = QSettings("PhoneToolKit", "MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("lastTab", self.tabs.currentIndex())

    def closeEvent(self, event):
        """Handle window close"""
        self._save_settings()

        # Stop auto-detect timer
        self.auto_detect_timer.stop()

        # Safely stop background workers without crashing GIL
        for tab in [self.virus_tab, self.finance_tab]:
            if hasattr(tab, '_stop_worker'):
                tab._stop_worker()
            elif hasattr(tab, 'worker') and tab.worker and tab.worker.isRunning():
                if hasattr(tab.worker, 'cancel'):
                    tab.worker.cancel()
                tab.worker.wait(1000)

        event.accept()