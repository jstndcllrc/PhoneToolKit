"""Virus Remover Tab - ADB App Uninstaller"""
import logging
import os
from typing import List, Optional
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QCheckBox, QGroupBox,
    QTextEdit, QProgressBar, QMessageBox, QSplitter,
    QFrame, QScrollArea, QSizePolicy, QStyle, QStyleOptionViewItem
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSettings, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QAction

from services.adb_service import get_adb_service, Device, Package, ADBDeviceError
from utils.icon_provider import get_package_icon

logger = logging.getLogger(__name__)

# Qt's "no maximum" value for widget dimensions (0xFFFFFF).
# PySide6 does not re-export QWIDGETSIZE_MAX, so keep it locally.
WIDGET_MAX_SIZE = 16777215


class ADBWorker(QThread):
    """Background worker for ADB operations with safe cancellation"""
    devices_found = Signal(list)
    packages_found = Signal(list)
    uninstall_result = Signal(str, bool, str)  # package_name, success, message
    install_result = Signal(bool, str)  # success, message
    log_message = Signal(str)
    finished = Signal()
    error = Signal(str)
    device_error = Signal(str, str)  # error_message, operation

    def __init__(self, operation: str, silent: bool = False, **kwargs):
        super().__init__()
        self.operation = operation
        self.silent = silent
        self.kwargs = kwargs
        self.adb = get_adb_service()
        self._is_cancelled = False

    def cancel(self):
        """Request graceful worker cancellation"""
        self._is_cancelled = True

    def run(self):
        try:
            if self._is_cancelled:
                return

            if self.operation == "get_devices":
                self._get_devices()
            elif self.operation == "get_packages":
                self._get_packages()
            elif self.operation == "uninstall":
                self._uninstall_packages()
            elif self.operation == "install":
                self._install_apk()
        except ADBDeviceError as e:
            if not self._is_cancelled:
                self.device_error.emit(str(e), self.operation)
        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(str(e))
        finally:
            if not self._is_cancelled:
                self.finished.emit()

    def _get_devices(self):
        if not self.silent and not self._is_cancelled:
            self.log_message.emit("Scanning for connected devices...")
        devices = self.adb.get_devices()
        if not self._is_cancelled:
            self.devices_found.emit(devices)
            if not self.silent:
                self.log_message.emit(f"Found {len(devices)} device(s)")

    def _get_packages(self):
        serial = self.kwargs.get("serial")
        third_party = self.kwargs.get("third_party", True)
        if not serial:
            if not self._is_cancelled:
                self.error.emit("No device serial provided")
            return

        if not self.silent and not self._is_cancelled:
            self.log_message.emit(f"Fetching packages for {serial}...")
        try:
            packages = self.adb.get_packages(serial, third_party)
            if not self._is_cancelled:
                self.packages_found.emit(packages)
                if not self.silent:
                    self.log_message.emit(f"Found {len(packages)} package(s)")
        except ADBDeviceError as e:
            if not self._is_cancelled:
                self.device_error.emit(str(e), self.operation)
        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(f"Failed to fetch packages: {e}")

    def _uninstall_packages(self):
        serial = self.kwargs.get("serial")
        packages = self.kwargs.get("packages", [])
        user_only = self.kwargs.get("user_only", True)

        if not serial or not packages:
            if not self._is_cancelled:
                self.error.emit("Missing parameters for uninstall")
            return

        for pkg in packages:
            if self._is_cancelled:
                break
            self.log_message.emit(f"Uninstalling {pkg}...")
            success, msg = self.adb.uninstall_package(serial, pkg, user_only)
            if not self._is_cancelled:
                self.uninstall_result.emit(pkg, success, msg)
                if success:
                    self.log_message.emit(f"✓ {pkg}: {msg}")
                else:
                    self.log_message.emit(f"✗ {pkg}: {msg}")

    def _install_apk(self):
        serial = self.kwargs.get("serial")
        apk_path = self.kwargs.get("apk_path")
        allow_downgrade = self.kwargs.get("allow_downgrade", False)
        allow_test = self.kwargs.get("allow_test", False)

        if not serial or not apk_path:
            if not self._is_cancelled:
                self.error.emit("Missing parameters for install")
            return

        self.log_message.emit(f"Installing {os.path.basename(apk_path)}...")
        try:
            success, msg = self.adb.install_apk(serial, apk_path, allow_downgrade, allow_test)
            if not self._is_cancelled:
                self.install_result.emit(success, msg)
                if success:
                    self.log_message.emit(f"✓ Install successful: {msg}")
                else:
                    self.log_message.emit(f"✗ Install failed: {msg}")
        except ADBDeviceError as e:
            if not self._is_cancelled:
                self.device_error.emit(str(e), self.operation)
        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(f"Install failed: {e}")


class PackageTableWidget(QTableWidget):
    """Custom table widget for package list with native sorting and check states"""

    def __init__(self):
        super().__init__()
        # Object name is used by the theme stylesheets to target this table's
        # check indicators (QTableWidget#packageTable::indicator) without
        # affecting any other tables in the application.
        self.setObjectName("packageTable")
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["Select", "App Name", "Package Name", "Type"])
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)  # Disabled during population

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(0, 65)
        self.setColumnWidth(3, 100)

        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(32)
        # Center checkboxes vertically in cells
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setShowGrid(True)
        # Keep this floor small: a hard 350px minimum made the table taller than
        # the surrounding "Installed Applications" group box, so the layout
        # pushed the action bar out of the frame and painted it over the table.
        # The splitter, not the table, decides how much room the list gets.
        self.setMinimumHeight(96)
        self.setIconSize(QSize(24, 24))
        self.cellClicked.connect(self._on_cell_clicked)
        # Position of the last mouse press inside the viewport, recorded so
        # _on_cell_clicked() can tell a click on the checkbox apart from a
        # click elsewhere in the Select cell (cellClicked only reports row/col).
        self._press_pos = None

    def mousePressEvent(self, event):
        self._press_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def _indicator_rect(self, row: int):
        """Geometry of the check indicator in the Select cell of ``row``.

        Queried through the same style sub-element the item delegate uses when
        it draws/activates the checkbox, so hit-testing always matches the
        painted control (including the theme stylesheet sizes).
        """
        item = self.item(row, 0)
        if item is None:
            return None
        option = QStyleOptionViewItem()
        option.rect = self.visualItemRect(item)
        option.state = QStyle.StateFlag.State_Enabled
        # The checkbox sub-element rect is only computed when the option
        # declares a check indicator; without this flag Qt returns an empty
        # rectangle and the hit test would never match.
        option.features |= QStyleOptionViewItem.ViewItemFeature.HasCheckIndicator
        if item.checkState() == Qt.CheckState.Checked:
            option.state |= QStyle.StateFlag.State_On
        return self.style().subElementRect(
            QStyle.SubElement.SE_ItemViewItemCheckIndicator, option, self)

    def _on_cell_clicked(self, row: int, col: int):
        """Toggle checkbox if user clicks directly on the Select column cell"""
        if col == 0:
            item = self.item(row, 0)
            if item and (item.flags() & Qt.ItemFlag.ItemIsEnabled):
                indicator = self._indicator_rect(row)
                press_pos = self._press_pos
                self._press_pos = None
                if (indicator is not None and press_pos is not None
                        and indicator.contains(press_pos)):
                    # The click landed on the checkbox itself, which the item
                    # view's delegate has already toggled. Toggling again here
                    # would cancel that out and make the checkbox appear
                    # unclickable (two toggles = no net change).
                    return
                new_state = (Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked
                             else Qt.CheckState.Checked)
                item.setCheckState(new_state)

    def populate_packages(self, packages: List[Package]):
        """Populate table with packages efficiently and safely"""
        # Disable sorting while populating to avoid layout re-sort storms
        self.setSortingEnabled(False)
        self.setRowCount(len(packages))

        for row, pkg in enumerate(packages):
            # Column 0: Checkable native item (lightweight, sorts properly with rows)
            check_item = QTableWidgetItem()
            check_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable |
                Qt.ItemFlag.ItemIsEnabled |
                Qt.ItemFlag.ItemIsSelectable
            )
            check_item.setCheckState(Qt.CheckState.Unchecked)
            check_item.setData(Qt.ItemDataRole.UserRole, pkg.package_name)
            check_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            # Center the checkbox in the cell
            check_item.setText("")
            self.setItem(row, 0, check_item)

            # Column 1: App name with icon
            app_icon = get_package_icon(pkg.package_name, pkg.label, pkg.is_system)
            name_item = QTableWidgetItem(app_icon, pkg.label or pkg.package_name)
            name_item.setData(Qt.ItemDataRole.UserRole, pkg.package_name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.setItem(row, 1, name_item)

            # Column 2: Package name
            pkg_item = QTableWidgetItem(pkg.package_name)
            pkg_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.setItem(row, 2, pkg_item)

            # Column 3: Type
            type_text = "System" if pkg.is_system else "User"
            type_item = QTableWidgetItem(type_text)
            type_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            if pkg.is_system:
                type_item.setForeground(QColor("#ff9800"))
            self.setItem(row, 3, type_item)

        # Re-enable sorting after population
        self.setSortingEnabled(True)

    def get_selected_packages(self) -> List[str]:
        """Get list of selected package names"""
        selected = []
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                pkg_name = item.data(Qt.ItemDataRole.UserRole)
                if pkg_name:
                    selected.append(pkg_name)
        return selected

    def select_all(self, checked: bool = True):
        """Select/deselect all visible rows"""
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for row in range(self.rowCount()):
            if not self.isRowHidden(row):
                item = self.item(row, 0)
                if item and (item.flags() & Qt.ItemFlag.ItemIsEnabled):
                    item.setCheckState(state)

    def filter_packages(self, text: str):
        """Filter packages by name"""
        text = text.lower().strip()
        for row in range(self.rowCount()):
            name_item = self.item(row, 1)
            pkg_item = self.item(row, 2)
            if name_item and pkg_item:
                match = (text in name_item.text().lower() or
                         text in pkg_item.text().lower())
                self.setRowHidden(row, not match)


class VirusRemoverTab(QWidget):
    """Main Virus Remover tab widget"""
    devices_updated = Signal(list)  # Signal emitted when devices list updates

    def __init__(self):
        super().__init__()
        self.current_device: Optional[Device] = None
        self.current_packages: List[Package] = []
        self.worker: Optional[ADBWorker] = None
        self.auto_detect_timer = None
        # Track device state for auto-detect
        self._last_device_count = 0
        self._last_device_serials = set()
        self._silent_refresh = False
        self._log_expanded = True
        self._log_expanded_sizes = None
        self._init_ui()
        self._load_settings()
        self.refresh_devices()

    def set_auto_detect_timer(self, timer):
        """Set the auto-detect timer from main window"""
        self.auto_detect_timer = timer

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 8, 10, 8)

        # ===== Device Selection Section (Compact single-row) =====
        device_group = QGroupBox("Device Connection")
        device_layout = QHBoxLayout(device_group)
        device_layout.setContentsMargins(12, 10, 12, 8)
        device_layout.setSpacing(10)

        device_label = QLabel("ADB Device:")
        device_label.setStyleSheet("font-weight: 600; font-size: 12px;")
        device_layout.addWidget(device_label)

        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(320)
        self.device_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.device_combo.currentIndexChanged.connect(self._on_device_changed)
        device_layout.addWidget(self.device_combo, 1)

        self.refresh_btn = QPushButton("🔄 Refresh Devices")
        self.refresh_btn.setProperty("primary", True)
        self.refresh_btn.clicked.connect(lambda: self.refresh_devices(silent=False, force_reload=True))
        device_layout.addWidget(self.refresh_btn)

        self.adb_status_label = QLabel("Checking ADB...")
        self.adb_status_label.setStyleSheet("font-size: 11px; font-weight: 500;")
        device_layout.addWidget(self.adb_status_label)

        layout.addWidget(device_group)

        # ===== Splitter for Package List and Activity Log =====
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setChildrenCollapsible(False)

        # ===== Package List Section =====
        pkg_group = QGroupBox("Installed Applications")
        pkg_layout = QVBoxLayout(pkg_group)
        pkg_layout.setContentsMargins(10, 12, 10, 8)
        pkg_layout.setSpacing(8)
        # Guarantees the toolbar, table and action bar fit inside the frame, so
        # the action bar can never be pushed out over the table again.
        pkg_group.setMinimumHeight(300)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.search_box = QComboBox()
        self.search_box.setEditable(True)
        self.search_box.setPlaceholderText("🔍 Search apps...")
        self.search_box.setMinimumWidth(260)
        self.search_box.lineEdit().textChanged.connect(self._on_search)
        toolbar.addWidget(self.search_box)

        self.show_system_cb = QCheckBox("Show System Apps")
        self.show_system_cb.setChecked(False)
        self.show_system_cb.toggled.connect(self._toggle_system_apps)
        toolbar.addWidget(self.show_system_cb)

        toolbar.addStretch()

        # These buttons will use the theme from main_window
        self.select_all_btn = QPushButton("☑ Select All")
        self.select_all_btn.clicked.connect(lambda: self.package_table.select_all(True))
        toolbar.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("☐ Deselect All")
        self.deselect_all_btn.clicked.connect(lambda: self.package_table.select_all(False))
        toolbar.addWidget(self.deselect_all_btn)

        self.clear_selection_btn = QPushButton("🧹 Clear Selection")
        self.clear_selection_btn.clicked.connect(self._clear_selection)
        toolbar.addWidget(self.clear_selection_btn)

        pkg_layout.addLayout(toolbar)

        # Package table (expands to take all available space)
        self.package_table = PackageTableWidget()
        self.package_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        pkg_layout.addWidget(self.package_table, 1)

        # Action bar at bottom of Installed Applications
        action_bar = QHBoxLayout()
        action_bar.setContentsMargins(4, 4, 4, 2)
        action_bar.setSpacing(12)

        self.pkg_count_label = QLabel("No device selected")
        self.pkg_count_label.setStyleSheet("font-weight: 600; font-size: 12px;")
        action_bar.addWidget(self.pkg_count_label)

        action_bar.addStretch()

        self.user_only_cb = QCheckBox("Current User Only (--user 0)")
        self.user_only_cb.setChecked(True)
        self.user_only_cb.setToolTip(
            "Uninstall for current user only (keeps app data for other users). "
            "Uncheck to uninstall for all users (requires root)."
        )
        action_bar.addWidget(self.user_only_cb)

        self.install_apk_btn = QPushButton("📥 Install APK")
        self.install_apk_btn.setProperty("primary", True)
        self.install_apk_btn.setEnabled(False)
        self.install_apk_btn.clicked.connect(self._install_apk)
        action_bar.addWidget(self.install_apk_btn)

        self.uninstall_btn = QPushButton("🗑 Uninstall Selected")
        self.uninstall_btn.setProperty("danger", True)
        self.uninstall_btn.setEnabled(False)
        self.uninstall_btn.clicked.connect(self._confirm_uninstall)
        action_bar.addWidget(self.uninstall_btn)

        pkg_layout.addLayout(action_bar)

        self.splitter.addWidget(pkg_group)

        # ===== Progress & Log Section =====
        self.log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(self.log_group)
        log_layout.setContentsMargins(10, 10, 10, 6)
        log_layout.setSpacing(6)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        log_layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        # The splitter owns how tall the log gets; a fixed ceiling here made the
        # log group fight its own contents and pushed the frame out of shape.
        self.log_text.setMinimumHeight(48)
        self.log_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        log_layout.addWidget(self.log_text)

        log_btns = QHBoxLayout()

        self.clear_log_btn = QPushButton("🗑 Clear Log")
        self.clear_log_btn.clicked.connect(self.log_text.clear)
        log_btns.addWidget(self.clear_log_btn)

        self.export_log_btn = QPushButton("📤 Export Log")
        self.export_log_btn.clicked.connect(self._export_log)
        log_btns.addWidget(self.export_log_btn)

        log_btns.addStretch()

        self.toggle_log_btn = QPushButton("▲ Hide Log")
        self.toggle_log_btn.clicked.connect(self._toggle_log)
        log_btns.addWidget(self.toggle_log_btn)

        log_layout.addLayout(log_btns)

        self.splitter.addWidget(self.log_group)

        # The app list keeps the lion's share; the log is a fixed-ish strip.
        self.splitter.setStretchFactor(0, 5)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setChildrenCollapsible(False)
        # Height is resolved from the real splitter size (see _apply_splitter_sizes)
        # so the ratio holds at any window size instead of assuming 710px tall.
        self._requested_log_ratio = 0.22
        QTimer.singleShot(0, self._apply_initial_splitter_sizes)

        layout.addWidget(self.splitter, 1)

        # Initial log message
        self._log("PhoneToolKit Virus Remover ready")
        self._log("Connect an Android device with USB debugging enabled")

    def _apply_initial_splitter_sizes(self):
        """Split the real height between the two panes once layout has settled."""
        log_ratio = getattr(self, "_requested_log_ratio", 0.22)
        if getattr(self, "_log_expanded", True):
            self._apply_splitter_sizes((1.0 - log_ratio, log_ratio))
        else:
            self._apply_splitter_sizes((1.0, 0.0))

    def _toggle_log(self):
        """Collapse/expand the Activity Log, handing its space to Installed Applications"""
        self._set_log_expanded(not self._log_expanded)

    def _set_log_expanded(self, expanded: bool):
        """Single source of truth for the Activity Log collapsed state.

        Collapsing shrinks the log group to just its button row instead of
        hiding widgets and then forcing absolute splitter sizes; absolute
        sizes do not match the real height of the splitter and used to shove
        the Installed Applications action bar out through the group box border.
        """
        self._log_expanded = expanded

        # Clear/Export are meaningless while the log is collapsed, so hide them
        # along with the text view and let the frame shrink-wrap its button row.
        for widget in (self.log_text, self.clear_log_btn, self.export_log_btn):
            widget.setVisible(expanded)

        if expanded:
            self.log_group.setMinimumHeight(0)
            self.log_group.setMaximumHeight(WIDGET_MAX_SIZE)
            self.toggle_log_btn.setText("▲ Hide Log")
            self.toggle_log_btn.setToolTip("Collapse the log to give the app list more room")
            self._apply_splitter_sizes(self._log_expanded_sizes or (0.72, 0.28))
        else:
            # Remember the current proportions so Show Log restores them
            self._log_expanded_sizes = self._splitter_proportions()
            # Let Qt shrink-wrap the frame around the toggle button. The hint
            # already includes the border, title strip and layout margins, so
            # nothing gets clipped (a hand-computed constant did).
            self.log_group.setMinimumHeight(0)
            self.log_group.setMaximumHeight(self.log_group.minimumSizeHint().height())
            self.toggle_log_btn.setText("▼ Show Log")
            self.toggle_log_btn.setToolTip("Expand the activity log")
            self._apply_splitter_sizes((1.0, 0.0))

    def _splitter_proportions(self):
        """Current splitter sizes as fractions of the usable height"""
        sizes = self.splitter.sizes()
        total = sum(sizes)
        if total <= 0:
            return None
        return tuple(s / total for s in sizes)

    def _apply_splitter_sizes(self, fractions):
        """Size the splitter relative to its real height, never in absolute pixels"""
        usable = self.splitter.height() - self.splitter.handleWidth()
        if usable <= 0:
            return
        first = int(usable * fractions[0])
        # Remaining pixels belong to the log pane; never let it go negative.
        self.splitter.setSizes([first, max(usable - first, 0)])

    def _load_settings(self):
        settings = QSettings("PhoneToolKit", "VirusRemover")
        self.user_only_cb.setChecked(settings.value("user_only", True, type=bool))
        self.show_system_cb.setChecked(settings.value("show_system", False, type=bool))

    def _save_settings(self):
        settings = QSettings("PhoneToolKit", "VirusRemover")
        settings.setValue("user_only", self.user_only_cb.isChecked())
        settings.setValue("show_system", self.show_system_cb.isChecked())

    def _stop_worker(self):
        """Safely stop any running background worker without crashing Python GIL"""
        if hasattr(self, 'refresh_btn') and self.refresh_btn.text() != "🔄 Refresh Devices":
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("🔄 Refresh Devices")

        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            try:
                self.worker.devices_found.disconnect()
            except (RuntimeError, TypeError):
                pass
            try:
                self.worker.packages_found.disconnect()
            except (RuntimeError, TypeError):
                pass
            try:
                self.worker.uninstall_result.disconnect()
            except (RuntimeError, TypeError):
                pass
            try:
                self.worker.log_message.disconnect()
            except (RuntimeError, TypeError):
                pass
            try:
                self.worker.finished.disconnect()
            except (RuntimeError, TypeError):
                pass
            try:
                self.worker.error.disconnect()
            except (RuntimeError, TypeError):
                pass
            try:
                self.worker.device_error.disconnect()
            except (RuntimeError, TypeError):
                pass
            self.worker.wait(1000)

    def closeEvent(self, event):
        self._save_settings()
        self._stop_worker()
        super().closeEvent(event)

    def refresh_devices(self, silent: bool = False, force_reload: bool = False):
        """Refresh device list asynchronously"""
        self._silent_refresh = silent

        if not silent:
            self.refresh_btn.setEnabled(False)
            self.refresh_btn.setText("🔄 Scanning...")
            self._log("Scanning for devices...")

        # Gracefully stop any running worker
        self._stop_worker()

        self.worker = ADBWorker("get_devices", silent=silent)
        self.worker.devices_found.connect(lambda devs: self._on_devices_found(devs, force_reload))
        self.worker.log_message.connect(self._log)
        self.worker.error.connect(self._on_error)
        self.worker.device_error.connect(self._on_device_error)
        self.worker.finished.connect(lambda: self.refresh_btn.setEnabled(True))
        self.worker.finished.connect(lambda: self.refresh_btn.setText("🔄 Refresh Devices"))
        self.worker.start()

    def _on_devices_found(self, devices: List[Device], force_reload: bool = False):
        """Handle device list from ADB - immediately stops scanning once device is detected"""
        # Always restore refresh button state as soon as scan finishes
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 Refresh Devices")

        current_serial = self.device_combo.currentData()
        current_serials = {d.serial for d in devices}
        current_count = len(devices)

        # Check if device list actually changed
        devices_changed = (current_serials != self._last_device_serials or
                          current_count != self._last_device_count)

        self._last_device_serials = current_serials
        self._last_device_count = current_count

        self.device_combo.blockSignals(True)
        self.device_combo.clear()

        if not devices:
            self.device_combo.addItem("No devices found", None)
            self.adb_status_label.setText("❌ No devices connected. Enable USB debugging.")
            self.adb_status_label.setStyleSheet("font-size: 11px;")
            if devices_changed:
                self._log("No devices connected")
            # When no device is connected, keep scanning timer active to detect plugged devices
            if self.auto_detect_timer and not self.auto_detect_timer.isActive():
                self.auto_detect_timer.start()
        else:
            # Device detected! Stop auto-detect scanning immediately as requested
            if self.auto_detect_timer and self.auto_detect_timer.isActive():
                self.auto_detect_timer.stop()
                logger.info("Device detected: stopped auto_detect_timer in virus tab")

            self.adb_status_label.setText(f"✅ {len(devices)} device(s) connected")
            self.adb_status_label.setStyleSheet("font-size: 11px;")
            for dev in devices:
                display = f"{dev.model or dev.serial} ({dev.serial}) - {dev.status}"
                self.device_combo.addItem(display, dev.serial)

            # Restore selection
            index = self.device_combo.findData(current_serial)
            if index >= 0:
                self.device_combo.setCurrentIndex(index)
            else:
                self.device_combo.setCurrentIndex(0)

            if devices_changed:
                self._log(f"Device detected: {len(devices)} device(s) connected. Scanning stopped.")

        self.device_combo.blockSignals(False)

        # Notify listeners (e.g. main window status bar)
        self.devices_updated.emit(devices)

        # Handle package loading
        self._on_device_changed(self.device_combo.currentIndex(), force_reload=force_reload)

    def _on_device_changed(self, index: int, force_reload: bool = False):
        """Handle device selection change"""
        serial = self.device_combo.currentData()
        if serial:
            device_still_connected = False
            for row in range(self.device_combo.count()):
                if self.device_combo.itemData(row) == serial:
                    device_still_connected = True
                    break

            if device_still_connected:
                # Reload if forced, if device changed, or if table is empty
                if force_reload or self.current_device is None or self.current_device.serial != serial or self.package_table.rowCount() == 0:
                    self.current_device = Device(serial, "", "", "", "")
                    self._load_packages(serial)
            else:
                self._log(f"Device {serial} disconnected")
                self.current_device = None
                self.package_table.setRowCount(0)
                self.pkg_count_label.setText("Device disconnected")
                self.uninstall_btn.setEnabled(False)
                self.install_apk_btn.setEnabled(False)
                # Resume scanning
                if self.auto_detect_timer and not self.auto_detect_timer.isActive():
                    self.auto_detect_timer.start()
        else:
            self.current_device = None
            self.package_table.setRowCount(0)
            self.pkg_count_label.setText("No device selected")
            self.uninstall_btn.setEnabled(False)
            self.install_apk_btn.setEnabled(False)
            # Resume scanning when no device is selected
            if self.auto_detect_timer and not self.auto_detect_timer.isActive():
                self.auto_detect_timer.start()

    def _load_packages(self, serial: str):
        """Load packages for selected device"""
        is_silent = self._silent_refresh
        if not is_silent:
            self.pkg_count_label.setText("Loading packages...")
        self.uninstall_btn.setEnabled(False)
        self.install_apk_btn.setEnabled(False)
        self.package_table.setRowCount(0)

        self._stop_worker()

        self.worker = ADBWorker("get_packages", serial=serial,
                                 third_party=not self.show_system_cb.isChecked(),
                                 silent=is_silent)
        self.worker.packages_found.connect(self._on_packages_found)
        self.worker.log_message.connect(self._log)
        self.worker.error.connect(self._on_error)
        self.worker.device_error.connect(self._on_device_error)
        self.worker.finished.connect(lambda: self._on_packages_finished(serial))
        self.worker.start()

    def _on_packages_found(self, packages: List[Package]):
        self.current_packages = packages
        self.package_table.populate_packages(packages)
        self.package_table.viewport().update()

        count = len(packages)
        sys_count = sum(1 for p in packages if p.is_system)
        user_count = count - sys_count
        self.pkg_count_label.setText(
            f"Total: {count} apps ({user_count} user, {sys_count} system)"
        )
        self.uninstall_btn.setEnabled(count > 0)
        self.install_apk_btn.setEnabled(True)  # Enable install when device is connected
        self._log(f"Loaded {count} packages")

    def _on_packages_finished(self, serial: str):
        """Check if device is still connected after package loading"""
        if self.package_table.rowCount() == 0 and self.current_device:
            device_still_connected = False
            for row in range(self.device_combo.count()):
                if self.device_combo.itemData(row) == serial:
                    device_still_connected = True
                    break

            if not device_still_connected:
                self._log(f"Device {serial} disconnected during package loading")
                self.current_device = None
                self.package_table.setRowCount(0)
                self.pkg_count_label.setText("Device disconnected")
                self.uninstall_btn.setEnabled(False)
                if self.auto_detect_timer and not self.auto_detect_timer.isActive():
                    self.auto_detect_timer.start()

    def _toggle_system_apps(self, checked: bool):
        """Toggle system apps visibility"""
        if self.current_device:
            self._load_packages(self.current_device.serial)

    def _on_search(self, text: str):
        """Filter package list"""
        self.package_table.filter_packages(text)

    def _confirm_uninstall(self):
        """Confirm uninstall action"""
        selected = self.package_table.get_selected_packages()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one app to uninstall.")
            return

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Confirm Uninstall")
        msg.setText(f"Uninstall {len(selected)} selected app(s)?")
        msg.setInformativeText(
            f"Selected packages:\n{', '.join(selected[:10])}"
            + ("..." if len(selected) > 10 else "") +
            f"\n\nMode: {'Current user only (--user 0)' if self.user_only_cb.isChecked() else 'All users (requires root)'}"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            self._uninstall_selected(selected)

    def _uninstall_selected(self, packages: List[str]):
        """Execute uninstall for selected packages"""
        if not self.current_device:
            return

        serial = self.current_device.serial
        device_still_connected = False
        for row in range(self.device_combo.count()):
            if self.device_combo.itemData(row) == serial:
                device_still_connected = True
                break

        if not device_still_connected:
            self._log(f"Device {serial} is no longer connected")
            QMessageBox.warning(self, "Device Disconnected", "The device was disconnected. Please reconnect and try again.")
            self.current_device = None
            self.package_table.setRowCount(0)
            self.pkg_count_label.setText("Device disconnected")
            self.uninstall_btn.setEnabled(False)
            return

        self.uninstall_btn.setEnabled(False)
        self.install_apk_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(packages))
        self.progress_bar.setValue(0)

        self._stop_worker()

        self.worker = ADBWorker("uninstall",
                                 serial=serial,
                                 packages=packages,
                                 user_only=self.user_only_cb.isChecked())
        self.worker.uninstall_result.connect(self._on_uninstall_result)
        self.worker.log_message.connect(self._log)
        self.worker.error.connect(self._on_error)
        self.worker.device_error.connect(self._on_device_error)
        self.worker.finished.connect(lambda: self._on_uninstall_finished(serial))
        self.worker.start()

    def _install_apk(self):
        """Handle APK installation via file picker"""
        if not self.current_device:
            QMessageBox.warning(self, "No Device", "Please select a connected device first.")
            return

        from PySide6.QtWidgets import QFileDialog
        apk_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select APK to Install",
            "",
            "Android Package (*.apk);;All Files (*.*)"
        )

        if not apk_path:
            return

        serial = self.current_device.serial
        device_still_connected = False
        for row in range(self.device_combo.count()):
            if self.device_combo.itemData(row) == serial:
                device_still_connected = True
                break

        if not device_still_connected:
            self._log(f"Device {serial} is no longer connected")
            QMessageBox.warning(self, "Device Disconnected", "The device was disconnected. Please reconnect and try again.")
            self.current_device = None
            self.package_table.setRowCount(0)
            self.pkg_count_label.setText("Device disconnected")
            self.uninstall_btn.setEnabled(False)
            self.install_apk_btn.setEnabled(False)
            return

        # Show options dialog
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle("Install APK Options")
        dialog.setMinimumWidth(350)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(f"APK: {os.path.basename(apk_path)}"))

        allow_downgrade_cb = QCheckBox("Allow downgrade (-d)")
        allow_downgrade_cb.setToolTip("Install even if the app version is older than installed version")
        layout.addWidget(allow_downgrade_cb)

        allow_test_cb = QCheckBox("Allow test packages (-t)")
        allow_test_cb.setToolTip("Allow installation of test-only packages")
        layout.addWidget(allow_test_cb)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self.uninstall_btn.setEnabled(False)
        self.install_apk_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setValue(0)

        self._stop_worker()

        self.worker = ADBWorker("install",
                                 serial=serial,
                                 apk_path=apk_path,
                                 allow_downgrade=allow_downgrade_cb.isChecked(),
                                 allow_test=allow_test_cb.isChecked())
        self.worker.install_result.connect(self._on_install_result)
        self.worker.log_message.connect(self._log)
        self.worker.error.connect(self._on_error)
        self.worker.device_error.connect(self._on_device_error)
        self.worker.finished.connect(lambda: self._on_install_finished(serial))
        self.worker.start()

    def _on_install_result(self, success: bool, message: str):
        """Handle install result"""
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)

        if success:
            QMessageBox.information(self, "Install Successful", f"APK installed successfully!\n\n{message}")
            self._log(f"✓ APK installed: {message}")
        else:
            QMessageBox.critical(self, "Install Failed", f"Failed to install APK:\n\n{message}")
            self._log(f"✗ APK install failed: {message}")

    def _on_install_finished(self, serial: str):
        """Handle install completion"""
        self.uninstall_btn.setEnabled(True)
        self.install_apk_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._log("Install operation completed")

        # Refresh package list to show newly installed app
        device_still_connected = False
        for row in range(self.device_combo.count()):
            if self.device_combo.itemData(row) == serial:
                device_still_connected = True
                break

        if device_still_connected and self.current_device and self.current_device.serial == serial:
            self._load_packages(serial)
        else:
            self._log(f"Device {serial} disconnected during install")
            self.current_device = None
            self.package_table.setRowCount(0)
            self.pkg_count_label.setText("Device disconnected")
            self.uninstall_btn.setEnabled(False)
            self.install_apk_btn.setEnabled(False)
            if self.auto_detect_timer and not self.auto_detect_timer.isActive():
                self.auto_detect_timer.start()

    def _on_uninstall_result(self, package: str, success: bool, message: str):
        """Handle individual uninstall result with visual feedback"""
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        for row in range(self.package_table.rowCount()):
            item0 = self.package_table.item(row, 0)
            if item0 and item0.data(Qt.ItemDataRole.UserRole) == package:
                name_item = self.package_table.item(row, 1)
                if success:
                    if name_item:
                        name_item.setForeground(QColor("#059669"))  # Success green
                    item0.setCheckState(Qt.CheckState.Unchecked)
                    item0.setFlags(item0.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                else:
                    if name_item:
                        name_item.setForeground(QColor("#e11d48"))  # Error red
                break

    def _on_uninstall_finished(self, serial: str):
        """Handle uninstall completion"""
        self.uninstall_btn.setEnabled(True)
        self.install_apk_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._log("Uninstall operation completed")

        # Show success message with count
        total_packages = self.progress_bar.maximum()
        QMessageBox.information(
            self,
            "Uninstall Complete",
            f"Uninstall operation completed for {total_packages} selected app(s).\n\n"
            f"Check the activity log for individual results."
        )

        device_still_connected = False
        for row in range(self.device_combo.count()):
            if self.device_combo.itemData(row) == serial:
                device_still_connected = True
                break

        if device_still_connected and self.current_device and self.current_device.serial == serial:
            self._load_packages(serial)
        else:
            self._log(f"Device {serial} disconnected during uninstall")
            self.current_device = None
            self.package_table.setRowCount(0)
            self.pkg_count_label.setText("Device disconnected")
            self.uninstall_btn.setEnabled(False)
            if self.auto_detect_timer and not self.auto_detect_timer.isActive():
                self.auto_detect_timer.start()

    def _on_error(self, error: str):
        """Handle worker error"""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 Refresh Devices")
        self._log(f"❌ Error: {error}")
        QMessageBox.critical(self, "Error", error)

    def _on_device_error(self, error: str, operation: str = ""):
        """Handle device disconnection error"""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 Refresh Devices")
        self._log(f"⚠ Device disconnected: {error}")
        self.current_device = None
        self.package_table.setRowCount(0)
        self.pkg_count_label.setText("Device disconnected")
        self.uninstall_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        # Resume auto-detect scanning to pick up reconnected devices
        if self.auto_detect_timer and not self.auto_detect_timer.isActive():
            self.auto_detect_timer.start()

        # Only show disruptive modal popup if an active uninstall was taking place
        if operation == "uninstall":
            QMessageBox.warning(self, "Device Disconnected",
                                "The device was disconnected during the uninstall operation.\n"
                                "Please reconnect your device and try again.")

    def _log(self, message: str):
        """Add message to log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _export_log(self):
        """Export log to file"""
        from utils.resources import get_data_path
        from datetime import datetime

        log_dir = get_data_path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        filename = log_dir / f"virus_remover_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.toPlainText())
            self._log(f"Log exported to {filename}")
            QMessageBox.information(self, "Export Complete", f"Log saved to:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def _clear_selection(self):
        """Clear all checkbox selections"""
        self.package_table.select_all(False)
        self._log("Selection cleared")
