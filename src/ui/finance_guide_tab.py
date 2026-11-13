"""Finance Guide Tab - Searchable Database + Reference Cards"""
import logging
import webbrowser
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGroupBox, QScrollArea,
    QFrame, QSplitter, QTextEdit, QLineEdit, QMessageBox,
    QToolButton, QMenu, QSizePolicy, QSpacerItem, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSettings, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QCursor, QAction

from services.finance_guide import (
    FINANCE_GUIDE_DATA, UnlockMethod, Brand, LockType,
    get_all_brands, get_all_lock_types, search_methods, get_method_summary
)

logger = logging.getLogger(__name__)


class MethodCard(QFrame):
    """Collapsible card for a single unlock method with full theme support"""

    def __init__(self, method: UnlockMethod, dark_mode: bool = False, parent=None):
        super().__init__(parent)
        self.method = method
        self.dark_mode = dark_mode
        self.expanded = False
        # Store references to theme-sensitive labels
        self.brand_label = None
        self.lock_label = None
        self.perm_label = None
        self.diff_label = None
        self.models_label = None
        self.method_text = None
        self.tool_frames = []
        self.tool_cost_labels = []
        self.warn_label = None
        self.warning_texts = []
        self.notes_text = None
        self._init_ui()
        self.update_theme(dark_mode)

    def _init_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header (always visible)
        header_layout = QHBoxLayout()

        # Brand + Lock type badges
        self.brand_label = QLabel(self.method.brand.value)
        header_layout.addWidget(self.brand_label)

        self.lock_label = QLabel(self.method.lock_type.value)
        header_layout.addWidget(self.lock_label)

        # Permanency indicator
        self.perm_label = QLabel("✅ Permanent" if self.method.is_permanent else "⚠️ Semi-Permanent")
        header_layout.addWidget(self.perm_label)

        header_layout.addStretch()

        # Difficulty
        self.diff_label = QLabel(f"Difficulty: {self.method.difficulty}")
        header_layout.addWidget(self.diff_label)

        # Expand button
        self.expand_btn = QToolButton()
        self.expand_btn.setText("▼")
        self.expand_btn.setFixedSize(26, 26)
        self.expand_btn.clicked.connect(self._toggle_expand)
        header_layout.addWidget(self.expand_btn)

        layout.addLayout(header_layout)

        # Models (always visible)
        self.models_label = QLabel(f"📱 Models: {self.method.models}")
        self.models_label.setWordWrap(True)
        layout.addWidget(self.models_label)

        # Expandable content
        self.content_widget = QWidget()
        self.content_widget.setVisible(False)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(0, 8, 0, 0)

        # Method steps
        method_label = QLabel("📋 Method:")
        method_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        content_layout.addWidget(method_label)

        self.method_text = QLabel(self.method.method)
        self.method_text.setWordWrap(True)
        self.method_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_layout.addWidget(self.method_text)

        # Tools
        if self.method.tools:
            tools_label = QLabel("🔧 Required Tools:")
            tools_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            content_layout.addWidget(tools_label)

            self.tool_frames = []
            self.tool_cost_labels = []
            for tool in self.method.tools:
                tool_frame = QFrame()
                self.tool_frames.append(tool_frame)
                tool_layout = QHBoxLayout(tool_frame)
                tool_layout.setContentsMargins(8, 6, 8, 6)

                tool_name = QLabel(f"<b>{tool.name}</b> - {tool.description}")
                tool_name.setTextFormat(Qt.TextFormat.RichText)
                tool_layout.addWidget(tool_name)

                tool_layout.addStretch()

                if tool.url:
                    open_btn = QPushButton("Open")
                    open_btn.setFixedSize(65, 26)
                    open_btn.clicked.connect(lambda checked, url=tool.url: webbrowser.open(url))
                    tool_layout.addWidget(open_btn)

                if tool.cost:
                    cost_label = QLabel(f"({tool.cost})")
                    self.tool_cost_labels.append(cost_label)
                    tool_layout.addWidget(cost_label)

                content_layout.addWidget(tool_frame)

        # Warnings
        if self.method.warnings:
            self.warn_label = QLabel("⚠️ Warnings:")
            content_layout.addWidget(self.warn_label)

            self.warning_texts = []
            for warning in self.method.warnings:
                warn_text = QLabel(f"• {warning}")
                warn_text.setWordWrap(True)
                self.warning_texts.append(warn_text)
                content_layout.addWidget(warn_text)

        # Notes
        if self.method.notes:
            notes_label = QLabel("📝 Notes:")
            notes_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            content_layout.addWidget(notes_label)

            self.notes_text = QLabel(self.method.notes)
            self.notes_text.setWordWrap(True)
            content_layout.addWidget(self.notes_text)

        # Copy button
        copy_btn = QPushButton("📋 Copy Method to Clipboard")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        content_layout.addWidget(copy_btn)

        layout.addWidget(self.content_widget)

    def update_theme(self, dark_mode: bool):
        """Update colors based on light/dark mode"""
        self.dark_mode = dark_mode
        if dark_mode:
            # Card frame
            self.setStyleSheet("""
                MethodCard {
                    background-color: #1e1e1e;
                    border: 1px solid #334155;
                    border-radius: 10px;
                    margin: 4px;
                }
                MethodCard:hover {
                    border-color: #00d4aa;
                }
            """)
            # Header badges - Brand (teal)
            self.brand_label.setStyleSheet("""
                background-color: #00d4aa; color: #000000; padding: 3px 8px;
                border-radius: 4px; font-size: 11px; font-weight: bold;
            """)
            # Header badges - Lock type (amber)
            self.lock_label.setStyleSheet("""
                background-color: #f59e0b; color: #000000; padding: 3px 8px;
                border-radius: 4px; font-size: 11px; font-weight: bold;
            """)
            # Permanency indicator
            if self.method.is_permanent:
                self.perm_label.setStyleSheet("color: #10b981; font-size: 11px; font-weight: bold;")
            else:
                self.perm_label.setStyleSheet("color: #f59e0b; font-size: 11px; font-weight: bold;")
            # Models
            self.models_label.setStyleSheet("color: #e2e8f0; font-size: 12px;")
            # Difficulty
            diff_colors = {"Easy": "#10b981", "Medium": "#f59e0b", "Hard": "#ef4444"}
            diff_color = diff_colors.get(self.method.difficulty, "#94a3b8")
            self.diff_label.setStyleSheet(f"color: {diff_color}; font-size: 11px; font-weight: bold;")
            # Method text area
            self.method_text.setStyleSheet("""
                background: #252525;
                color: #f1f5f9;
                padding: 12px;
                border: 1px solid #334155;
                border-radius: 8px;
                font-family: "Consolas", "Monospace";
                font-size: 12px;
                line-height: 1.5;
            """)
            # Tool frames
            if hasattr(self, 'tool_frames'):
                for frame in self.tool_frames:
                    frame.setStyleSheet("background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 6px;")
            # Tool cost labels
            for cost_label in self.tool_cost_labels:
                cost_label.setStyleSheet("color: #fbbf24; font-size: 11px; font-weight: bold;")
            # Warnings
            if self.warn_label:
                self.warn_label.setStyleSheet("font-weight: bold; color: #fca5a5; font-size: 12px;")
            for warn_text in self.warning_texts:
                warn_text.setStyleSheet("color: #fca5a5; font-size: 11px;")
            # Notes
            if hasattr(self, 'notes_text') and self.notes_text:
                self.notes_text.setStyleSheet("color: #94a3b8; font-size: 11px; font-style: italic;")
        else:
            # Card frame
            self.setStyleSheet("""
                MethodCard {
                    background-color: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 10px;
                    margin: 4px;
                }
                MethodCard:hover {
                    border-color: #00b4a6;
                }
            """)
            # Header badges - Brand (teal)
            self.brand_label.setStyleSheet("""
                background-color: #00b4a6; color: white; padding: 3px 8px;
                border-radius: 4px; font-size: 11px; font-weight: bold;
            """)
            # Header badges - Lock type (amber)
            self.lock_label.setStyleSheet("""
                background-color: #d97706; color: white; padding: 3px 8px;
                border-radius: 4px; font-size: 11px; font-weight: bold;
            """)
            # Permanency indicator
            if self.method.is_permanent:
                self.perm_label.setStyleSheet("color: #059669; font-size: 11px; font-weight: bold;")
            else:
                self.perm_label.setStyleSheet("color: #d97706; font-size: 11px; font-weight: bold;")
            # Models
            self.models_label.setStyleSheet("color: #1e293b; font-size: 12px;")
            # Difficulty
            diff_colors = {"Easy": "#059669", "Medium": "#d97706", "Hard": "#e11d48"}
            diff_color = diff_colors.get(self.method.difficulty, "#64748b")
            self.diff_label.setStyleSheet(f"color: {diff_color}; font-size: 11px; font-weight: bold;")
            # Method text area
            self.method_text.setStyleSheet("""
                background: #f8fafc;
                color: #1e293b;
                padding: 12px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                font-family: "Consolas", "Monospace";
                font-size: 12px;
                line-height: 1.5;
            """)
            # Tool frames
            if hasattr(self, 'tool_frames'):
                for frame in self.tool_frames:
                    frame.setStyleSheet("background: #ecfeff; border: 1px solid #a7f3d0; border-radius: 8px; padding: 6px;")
            # Tool cost labels
            for cost_label in self.tool_cost_labels:
                cost_label.setStyleSheet("color: #ff9800; font-size: 11px; font-weight: bold;")
            # Warnings
            if self.warn_label:
                self.warn_label.setStyleSheet("font-weight: bold; color: #f44336; font-size: 12px;")
            for warn_text in self.warning_texts:
                warn_text.setStyleSheet("color: #f44336; font-size: 11px;")
            # Notes
            if hasattr(self, 'notes_text') and self.notes_text:
                self.notes_text.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")

    def _toggle_expand(self):
        self.expanded = not self.expanded
        self.content_widget.setVisible(self.expanded)
        self.expand_btn.setText("▲" if self.expanded else "▼")

    def _copy_to_clipboard(self):
        from PySide6.QtWidgets import QApplication
        text = f"""{self.method.brand.value} - {self.method.lock_type.value}
Models: {self.method.models}
Method: {self.method.method}
Permanent: {'Yes' if self.method.is_permanent else 'No (Semi-permanent)'}
Difficulty: {self.method.difficulty}
"""
        if self.method.tools:
            text += "\nTools:\n"
            for tool in self.method.tools:
                text += f"  - {tool.name}: {tool.description}"
                if tool.url:
                    text += f" ({tool.url})"
                text += "\n"
        if self.method.warnings:
            text += "\nWarnings:\n"
            for w in self.method.warnings:
                text += f"  ⚠️ {w}\n"
        if self.method.notes:
            text += f"\nNotes: {self.method.notes}\n"

        QApplication.clipboard().setText(text)
        btn = self.sender()
        if btn and isinstance(btn, QPushButton):
            btn.setText("✅ Copied!")
            QTimer.singleShot(1500, lambda: btn.setText("📋 Copy Method to Clipboard"))


class FinanceGuideTab(QWidget):
    """Finance Guide tab with searchable database and reference cards"""

    def __init__(self):
        super().__init__()
        self.filtered_methods: List[UnlockMethod] = FINANCE_GUIDE_DATA.copy()
        self._init_ui()
        self._load_settings()
        self._update_display()

    def _is_dark_mode(self) -> bool:
        settings = QSettings("PhoneToolKit", "MainWindow")
        return settings.value("darkMode", False, type=bool)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # ===== Header with stats =====
        header_layout = QHBoxLayout()

        title = QLabel("📖 Finance Lock Removal Guide")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #1e3a5f;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        summary = get_method_summary()
        stats_label = QLabel(
            f"📊 {summary['total_methods']} methods • "
            f"{summary['brands']} brands • "
            f"{summary['lock_types']} lock types • "
            f"✅ {summary['permanent']} permanent • "
            f"⚠️ {summary['semi_permanent']} semi-permanent"
        )
        stats_label.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 500;")
        header_layout.addWidget(stats_label)

        layout.addLayout(header_layout)

        # ===== Filter/Toolbar =====
        filter_group = QGroupBox("Filters & Search")
        filter_layout = QGridLayout(filter_group)

        # Search
        filter_layout.addWidget(QLabel("🔍 Search:"), 0, 0)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by brand, model, lock type, tool...")
        self.search_box.textChanged.connect(self._on_search)
        filter_layout.addWidget(self.search_box, 0, 1, 1, 3)

        # Brand filter
        filter_layout.addWidget(QLabel("Brand:"), 1, 0)
        self.brand_combo = QComboBox()
        self.brand_combo.addItem("All Brands", None)
        for brand in get_all_brands():
            self.brand_combo.addItem(brand.value, brand)
        self.brand_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.brand_combo, 1, 1)

        # Lock type filter
        filter_layout.addWidget(QLabel("Lock Type:"), 1, 2)
        self.lock_combo = QComboBox()
        self.lock_combo.addItem("All Types", None)
        for lt in get_all_lock_types():
            self.lock_combo.addItem(lt.value, lt)
        self.lock_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.lock_combo, 1, 3)

        # View mode
        filter_layout.addWidget(QLabel("View:"), 2, 0)
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Reference Cards", "Table View", "Wizard Mode"])
        self.view_combo.currentIndexChanged.connect(self._on_view_changed)
        filter_layout.addWidget(self.view_combo, 2, 1)

        # Show only permanent
        self.permanent_only_cb = QCheckBox("Show Permanent Only")
        self.permanent_only_cb.toggled.connect(self._on_filter_changed)
        filter_layout.addWidget(self.permanent_only_cb, 2, 2)

        # Expand all / Collapse all
        self.expand_all_btn = QPushButton("🔽 Expand All")
        self.expand_all_btn.clicked.connect(self._expand_all)
        filter_layout.addWidget(self.expand_all_btn, 2, 3)

        self.collapse_all_btn = QPushButton("🔼 Collapse All")
        self.collapse_all_btn.clicked.connect(self._collapse_all)
        filter_layout.addWidget(self.collapse_all_btn, 2, 4)

        layout.addWidget(filter_group)

        # ===== Content Area =====
        self.stacked_content = QWidget()
        content_layout = QVBoxLayout(self.stacked_content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # --- Cards View (default) ---
        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cards_layout.setSpacing(8)
        self.cards_scroll.setWidget(self.cards_container)
        content_layout.addWidget(self.cards_scroll)

        # --- Table View ---
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels([
            "Brand", "Lock Type", "Models", "Method", "Permanent", "Difficulty"
        ])
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setWordWrap(True)
        self.table_widget.setVisible(False)
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        content_layout.addWidget(self.table_widget)

        # --- Wizard View ---
        self.wizard_widget = self._create_wizard()
        self.wizard_widget.setVisible(False)
        content_layout.addWidget(self.wizard_widget)

        layout.addWidget(self.stacked_content, 1)

    def _create_wizard(self) -> QWidget:
        """Create step-by-step wizard widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        step1 = QGroupBox("Step 1: Select Device Brand")
        step1_layout = QVBoxLayout(step1)
        self.wizard_brand_combo = QComboBox()
        self.wizard_brand_combo.addItem("Select brand...", None)
        for brand in get_all_brands():
            self.wizard_brand_combo.addItem(brand.value, brand)
        self.wizard_brand_combo.currentIndexChanged.connect(self._wizard_brand_changed)
        step1_layout.addWidget(self.wizard_brand_combo)
        layout.addWidget(step1)

        step2 = QGroupBox("Step 2: Select Finance Lock Type")
        step2_layout = QVBoxLayout(step2)
        self.wizard_lock_combo = QComboBox()
        self.wizard_lock_combo.addItem("Select lock type...", None)
        self.wizard_lock_combo.setEnabled(False)
        self.wizard_lock_combo.currentIndexChanged.connect(self._wizard_lock_changed)
        step2_layout.addWidget(self.wizard_lock_combo)
        layout.addWidget(step2)

        step3 = QGroupBox("Step 3: Unlock Instructions")
        step3_layout = QVBoxLayout(step3)
        self.wizard_result = QTextEdit()
        self.wizard_result.setReadOnly(True)
        self.wizard_result.setFont(QFont("Consolas", 10))
        step3_layout.addWidget(self.wizard_result)
        layout.addWidget(step3, 1)

        return widget

    def update_theme(self, dark_mode: bool):
        """Update cards and table theme"""
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), MethodCard):
                item.widget().update_theme(dark_mode)

        # Update table view theme
        if dark_mode:
            self.table_widget.setStyleSheet("""
                QTableWidget {
                    background-color: #1a1a1a;
                    color: #f1f5f9;
                    border: 2px solid #334155;
                    gridline-color: #334155;
                    alternate-background-color: #252525;
                    font-size: 13px;
                }
                QHeaderView::section {
                    background-color: #1e1e1e;
                    color: #00d4aa;
                    border: 1px solid #334155;
                    padding: 8px;
                    font-weight: 600;
                }
                QTableWidget::item:selected {
                    background-color: #00d4aa;
                    color: #000000;
                }
            """)
            self.wizard_result.setStyleSheet("""
                QTextEdit {
                    background-color: #1a1a1a;
                    color: #f1f5f9;
                    border: 2px solid #334155;
                    border-radius: 8px;
                    padding: 12px;
                    font-family: 'Consolas', 'Monospace';
                    font-size: 11px;
                }
            """)
        else:
            self.table_widget.setStyleSheet("""
                QTableWidget {
                    background-color: #ffffff;
                    color: #0f172a;
                    border: 2px solid #cbd5e1;
                    gridline-color: #e2e8f0;
                    alternate-background-color: #f8fafc;
                    font-size: 13px;
                }
                QHeaderView::section {
                    background-color: #f1f5f9;
                    color: #1e40af;
                    border: 1px solid #cbd5e1;
                    padding: 8px;
                    font-weight: 600;
                }
                QTableWidget::item:selected {
                    background-color: #0d9488;
                    color: #ffffff;
                }
            """)
            self.wizard_result.setStyleSheet("""
                QTextEdit {
                    background-color: #ffffff;
                    color: #0f172a;
                    border: 2px solid #cbd5e1;
                    border-radius: 8px;
                    padding: 12px;
                    font-family: 'Consolas', 'Monospace';
                    font-size: 11px;
                }
            """)

    def _load_settings(self):
        settings = QSettings("PhoneToolKit", "FinanceGuide")
        self.view_combo.setCurrentIndex(settings.value("view_mode", 0, type=int))
        self.permanent_only_cb.setChecked(settings.value("permanent_only", False, type=bool))
        self.brand_combo.setCurrentIndex(settings.value("brand_filter", 0, type=int))
        self.lock_combo.setCurrentIndex(settings.value("lock_filter", 0, type=int))

    def _save_settings(self):
        settings = QSettings("PhoneToolKit", "FinanceGuide")
        settings.setValue("view_mode", self.view_combo.currentIndex())
        settings.setValue("permanent_only", self.permanent_only_cb.isChecked())
        settings.setValue("brand_filter", self.brand_combo.currentIndex())
        settings.setValue("lock_filter", self.lock_combo.currentIndex())

    def closeEvent(self, event):
        self._save_settings()
        super().closeEvent(event)

    def _on_search(self, text: str):
        self._apply_filters()

    def _on_filter_changed(self):
        self._apply_filters()

    def _on_view_changed(self, index: int):
        self.cards_scroll.setVisible(index == 0)
        self.table_widget.setVisible(index == 1)
        self.wizard_widget.setVisible(index == 2)
        if index == 1:
            self._populate_table()
        elif index == 2:
            self._reset_wizard()

    def _apply_filters(self):
        """Apply all filters and update display"""
        search_text = self.search_box.text().lower().strip()
        brand = self.brand_combo.currentData()
        lock_type = self.lock_combo.currentData()
        permanent_only = self.permanent_only_cb.isChecked()

        self.filtered_methods = []
        for method in FINANCE_GUIDE_DATA:
            if brand and method.brand != brand:
                continue
            if lock_type and method.lock_type != lock_type:
                continue
            if permanent_only and not method.is_permanent:
                continue
            if search_text:
                searchable = (
                    method.brand.value.lower() + " " +
                    method.lock_type.value.lower() + " " +
                    method.models.lower() + " " +
                    method.method.lower() + " " +
                    method.notes.lower() + " " +
                    " ".join(t.name.lower() + " " + t.description.lower() for t in method.tools)
                )
                if search_text not in searchable:
                    continue

            self.filtered_methods.append(method)

        self._update_display()

    def _update_display(self):
        """Update the current view with filtered methods"""
        self._populate_cards()

        if self.table_widget.isVisible():
            self._populate_table()

        if self.wizard_widget.isVisible():
            self._wizard_brand_changed(self.wizard_brand_combo.currentIndex())

    def _populate_cards(self):
        """Populate cards view with theme-aware styling"""
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        dark_mode = self._is_dark_mode()
        for method in self.filtered_methods:
            card = MethodCard(method, dark_mode=dark_mode)
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _populate_table(self):
        """Populate table view"""
        self.table_widget.setRowCount(len(self.filtered_methods))
        for row, method in enumerate(self.filtered_methods):
            items = [
                method.brand.value,
                method.lock_type.value,
                method.models,
                method.method[:200] + "..." if len(method.method) > 200 else method.method,
                "✅ Yes" if method.is_permanent else "⚠️ No (Semi)",
                method.difficulty,
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 4 and not method.is_permanent:
                    item.setForeground(QColor("#ff9800"))
                elif col == 5:
                    colors = {"Easy": "#4caf50", "Medium": "#ff9800", "Hard": "#f44336"}
                    item.setForeground(QColor(colors.get(method.difficulty, "#666")))
                self.table_widget.setItem(row, col, item)

        self.table_widget.resizeRowsToContents()

    def _reset_wizard(self):
        self.wizard_brand_combo.blockSignals(True)
        self.wizard_brand_combo.setCurrentIndex(0)
        self.wizard_brand_combo.blockSignals(False)
        self.wizard_lock_combo.blockSignals(True)
        self.wizard_lock_combo.clear()
        self.wizard_lock_combo.addItem("Select lock type...", None)
        self.wizard_lock_combo.setEnabled(False)
        self.wizard_lock_combo.blockSignals(False)
        self.wizard_result.clear()

    def _wizard_brand_changed(self, index: int):
        brand = self.wizard_brand_combo.currentData()
        self.wizard_lock_combo.blockSignals(True)
        self.wizard_lock_combo.clear()
        self.wizard_lock_combo.addItem("Select lock type...", None)

        if brand:
            lock_types = set()
            for method in FINANCE_GUIDE_DATA:
                if method.brand == brand:
                    lock_types.add(method.lock_type)
            for lt in sorted(lock_types, key=lambda x: x.value):
                self.wizard_lock_combo.addItem(lt.value, lt)
            self.wizard_lock_combo.setEnabled(True)
        else:
            self.wizard_lock_combo.setEnabled(False)

        self.wizard_lock_combo.blockSignals(False)
        self.wizard_result.clear()

    def _wizard_lock_changed(self, index: int):
        brand = self.wizard_brand_combo.currentData()
        lock_type = self.wizard_lock_combo.currentData()

        if not brand or not lock_type:
            self.wizard_result.clear()
            return

        for method in FINANCE_GUIDE_DATA:
            if method.brand == brand and method.lock_type == lock_type:
                self._show_wizard_result(method)
                return

        self.wizard_result.clear()

    def _show_wizard_result(self, method: UnlockMethod):
        text = f"""╔══════════════════════════════════════════════════════════════════╗
║           FINANCE LOCK REMOVAL INSTRUCTIONS                       ║
╠══════════════════════════════════════════════════════════════════╣
║ Brand:        {method.brand.value:<50} ║
║ Lock Type:    {method.lock_type.value:<50} ║
║ Models:       {method.models:<50} ║
║ Permanent:    {'Yes ✅' if method.is_permanent else 'No ⚠️ (Semi-permanent)'}║
║ Difficulty:   {method.difficulty:<50} ║
╠══════════════════════════════════════════════════════════════════╣
║ METHOD:                                                           ║
╠══════════════════════════════════════════════════════════════════╣
{method.method}
╠══════════════════════════════════════════════════════════════════╣
"""
        if method.tools:
            text += "║ REQUIRED TOOLS:                                                   ║\n╠══════════════════════════════════════════════════════════════════╣\n"
            for tool in method.tools:
                text += f"║   • {tool.name}: {tool.description:<50} ║\n"
                if tool.url:
                    text += f"║     URL: {tool.url:<55} ║\n"
                if tool.cost:
                    text += f"║     Cost: {tool.cost:<55} ║\n"
            text += "╠══════════════════════════════════════════════════════════════════╣\n"

        if method.warnings:
            text += "║ ⚠️ WARNINGS:                                                        ║\n╠══════════════════════════════════════════════════════════════════╣\n"
            for w in method.warnings:
                text += f"║   ⚠️ {w:<60} ║\n"
            text += "╠══════════════════════════════════════════════════════════════════╣\n"

        if method.notes:
            text += f"║ NOTES: {method.notes:<56} ║\n"
            text += "╠══════════════════════════════════════════════════════════════════╣\n"

        text += "╚══════════════════════════════════════════════════════════════════╝"

        self.wizard_result.setPlainText(text)

    def _expand_all(self):
        """Expand all cards"""
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), MethodCard):
                card = item.widget()
                if not card.expanded:
                    card._toggle_expand()

    def _collapse_all(self):
        """Collapse all cards"""
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), MethodCard):
                card = item.widget()
                if card.expanded:
                    card._toggle_expand()
