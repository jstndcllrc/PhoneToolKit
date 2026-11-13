"""Help & Documentation Tab"""
import logging
import webbrowser
from typing import Dict, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QSplitter, QGroupBox, QScrollArea,
    QFrame, QSizePolicy, QTabWidget, QMessageBox
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont, QColor, QDesktopServices
from PySide6.QtCore import QUrl

logger = logging.getLogger(__name__)


class HelpTab(QWidget):
    """Help and documentation tab with built-in guides"""

    def __init__(self):
        super().__init__()
        self.header = None
        self._init_ui()
        self.update_theme(self._is_dark_mode())

    def _is_dark_mode(self) -> bool:
        settings = QSettings("PhoneToolKit", "MainWindow")
        return settings.value("darkMode", False, type=bool)

    def update_theme(self, dark_mode: bool):
        """Update styling for help tab based on light/dark mode"""
        if dark_mode:
            self.content_area.setStyleSheet("""
                QTextEdit {
                    background-color: #1a1a1a;
                    color: #f1f5f9;
                    border: 2px solid #334155;
                    border-radius: 8px;
                    padding: 16px;
                }
            """)
            # Update header color for dark mode
            if self.header:
                self.header.setStyleSheet("font-size: 18px; font-weight: 700; color: #00d4aa;")
        else:
            self.content_area.setStyleSheet("""
                QTextEdit {
                    background-color: #ffffff;
                    color: #0f172a;
                    border: 2px solid #cbd5e1;
                    border-radius: 8px;
                    padding: 16px;
                }
            """)
            # Update header color for light mode
            if self.header:
                self.header.setStyleSheet("font-size: 18px; font-weight: 700; color: #1e3a5f;")
        # Refresh current content with updated styling
        current_item = self.nav_tree.currentItem()
        if current_item:
            topic = current_item.data(0, Qt.ItemDataRole.UserRole)
            if topic:
                self._show_topic(topic)
            else:
                self._show_welcome()
        else:
            self._show_welcome()

    def _wrap_html(self, body: str) -> str:
        """Wrap HTML content with theme-appropriate styling"""
        dark = self._is_dark_mode()
        if dark:
            bg_page = "#0a0a0a"
            bg_card = "#1a1a1a"
            text_color = "#f1f5f9"
            border_color = "#334155"
            link_color = "#00d4aa"
        else:
            bg_page = "#f8fafc"
            bg_card = "#ffffff"
            text_color = "#0f172a"
            border_color = "#cbd5e1"
            link_color = "#0d9488"
        return f"""
        <html>
        <head>
        <style>
            body {{ 
                color: {text_color}; 
                background-color: {bg_page};
                font-family: 'Segoe UI', Arial, sans-serif; 
                line-height: 1.6; 
                font-size: 13px; 
            }}
            a {{ color: {link_color}; text-decoration: none; font-weight: 600; }}
            a:hover {{ text-decoration: underline; }}
            pre {{ 
                background-color: {bg_card}; 
                color: {text_color}; 
                border: 1px solid {border_color}; 
                border-radius: 8px; 
                padding: 14px; 
                font-family: 'Consolas', 'Monospace'; 
                font-size: 12px; 
                overflow-x: auto; 
            }}
            code {{ 
                background-color: {bg_card}; 
                color: {text_color}; 
                border-radius: 4px; 
                padding: 2px 6px; 
                font-family: 'Consolas', 'Monospace'; 
            }}
            table {{ 
                border-collapse: collapse; 
                width: 100%; 
                border: 1px solid {border_color}; 
                margin: 12px 0; 
            }}
            th {{ 
                background-color: {bg_card}; 
                color: {text_color}; 
                border: 1px solid {border_color}; 
                padding: 10px 12px; 
                font-weight: 600; 
            }}
            td {{ 
                border: 1px solid {border_color}; 
                padding: 10px 12px; 
                color: {text_color}; 
            }}
            h2 {{ 
                color: {link_color};
                border-bottom: 2px solid {border_color}; 
                padding-bottom: 8px; 
                margin-top: 24px;
            }}
            h3 {{ 
                color: {text_color};
                margin-top: 18px; 
            }}
            li {{ margin-bottom: 6px; }}
            strong {{ color: {text_color}; }}
            ul {{ padding-left: 24px; }}
            ol {{ padding-left: 24px; }}
            blockquote {{
                border-left: 3px solid {link_color};
                padding-left: 16px;
                margin: 16px 0;
                color: {text_color};
                opacity: 0.9;
            }}
        </style>
        </head>
        <body>
        {body}
        </body>
        </html>
        """

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        self.header = QLabel("📚 Help & Documentation")
        self.header.setStyleSheet("font-size: 18px; font-weight: 700; color: #1e3a5f;")
        layout.addWidget(self.header)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, 1)

        # Left: Navigation tree
        nav_group = QGroupBox("Contents")
        nav_layout = QVBoxLayout(nav_group)

        self.nav_tree = QTreeWidget()
        self.nav_tree.setHeaderHidden(True)
        self.nav_tree.setMinimumWidth(250)
        self.nav_tree.itemClicked.connect(self._on_nav_click)
        nav_layout.addWidget(self.nav_tree)

        splitter.addWidget(nav_group)

        # Right: Content area
        self.content_area = QTextEdit()
        self.content_area.setReadOnly(True)
        self.content_area.setFont(QFont("Segoe UI", 10))
        self.content_area.setStyleSheet("""
            QTextEdit {
                background-color: #f8fafc;
                color: #1e293b;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        splitter.addWidget(self.content_area)

        splitter.setSizes([280, 720])

        # Build navigation tree
        self._build_nav_tree()

        # Footer buttons
        footer = QHBoxLayout()
        footer.addStretch()

        self.check_updates_btn = QPushButton("🔄 Check for Updates")
        self.check_updates_btn.clicked.connect(self._check_updates)
        footer.addWidget(self.check_updates_btn)

        self.report_issue_btn = QPushButton("🐛 Report Issue")
        self.report_issue_btn.clicked.connect(self._report_issue)
        footer.addWidget(self.report_issue_btn)

        self.about_btn = QPushButton("ℹ️ About")
        self.about_btn.clicked.connect(self._show_about)
        footer.addWidget(self.about_btn)

        layout.addLayout(footer)

        # Show welcome content
        self._show_welcome()

    def _build_nav_tree(self):
        """Build the navigation tree"""
        # Getting Started
        getting_started = QTreeWidgetItem(self.nav_tree, ["🚀 Getting Started"])
        getting_started.setData(0, Qt.ItemDataRole.UserRole, "getting_started")
        QTreeWidgetItem(getting_started, ["Quick Start Guide"]).setData(0, Qt.ItemDataRole.UserRole, "quick_start")
        QTreeWidgetItem(getting_started, ["System Requirements"]).setData(0, Qt.ItemDataRole.UserRole, "requirements")
        QTreeWidgetItem(getting_started, ["Installing ADB Drivers"]).setData(0, Qt.ItemDataRole.UserRole, "adb_drivers")

        # Virus Remover
        virus = QTreeWidgetItem(self.nav_tree, ["🦠 Virus Remover (ADB Uninstaller)"])
        virus.setData(0, Qt.ItemDataRole.UserRole, "virus_remover")
        QTreeWidgetItem(virus, ["Connecting Your Device"]).setData(0, Qt.ItemDataRole.UserRole, "connect_device")
        QTreeWidgetItem(virus, ["Selecting Apps to Remove"]).setData(0, Qt.ItemDataRole.UserRole, "select_apps")
        QTreeWidgetItem(virus, ["Understanding --user 0"]).setData(0, Qt.ItemDataRole.UserRole, "user_zero")
        QTreeWidgetItem(virus, ["Troubleshooting"]).setData(0, Qt.ItemDataRole.UserRole, "virus_troubleshoot")

        # Finance Guide
        finance = QTreeWidgetItem(self.nav_tree, ["🔓 Finance Lock Guide"])
        finance.setData(0, Qt.ItemDataRole.UserRole, "finance_guide")
        QTreeWidgetItem(finance, ["How to Use the Guide"]).setData(0, Qt.ItemDataRole.UserRole, "finance_usage")
        QTreeWidgetItem(finance, ["Transsion (Tecno/Infinix/Itel)"]).setData(0, Qt.ItemDataRole.UserRole, "finance_transsion")
        QTreeWidgetItem(finance, ["Honor Devices"]).setData(0, Qt.ItemDataRole.UserRole, "finance_honor")
        QTreeWidgetItem(finance, ["Xiaomi/Redmi/POCO"]).setData(0, Qt.ItemDataRole.UserRole, "finance_xiaomi")
        QTreeWidgetItem(finance, ["Oppo/Realme"]).setData(0, Qt.ItemDataRole.UserRole, "finance_oppo")
        QTreeWidgetItem(finance, ["Vivo Devices"]).setData(0, Qt.ItemDataRole.UserRole, "finance_vivo")
        QTreeWidgetItem(finance, ["Understanding Permanent vs Semi-Permanent"]).setData(0, Qt.ItemDataRole.UserRole, "finance_permanent")
        QTreeWidgetItem(finance, ["Tool References (AMT, UT, TSM, FCKTOOL)"]).setData(0, Qt.ItemDataRole.UserRole, "finance_tools")

        # Advanced Topics
        advanced = QTreeWidgetItem(self.nav_tree, ["⚙️ Advanced Topics"])
        advanced.setData(0, Qt.ItemDataRole.UserRole, "advanced")
        QTreeWidgetItem(advanced, ["ADB Command Reference"]).setData(0, Qt.ItemDataRole.UserRole, "adb_commands")
        QTreeWidgetItem(advanced, ["Backup Before Uninstall"]).setData(0, Qt.ItemDataRole.UserRole, "backup")
        QTreeWidgetItem(advanced, ["Recovering from Bootloop"]).setData(0, Qt.ItemDataRole.UserRole, "recovery")

        # Resources
        resources = QTreeWidgetItem(self.nav_tree, ["🔗 External Resources"])
        resources.setData(0, Qt.ItemDataRole.UserRole, "resources")
        QTreeWidgetItem(resources, ["GMS Reseller (FRP Server)"]).setData(0, Qt.ItemDataRole.UserRole, "url_gms")
        QTreeWidgetItem(resources, ["ADB Official Downloads"]).setData(0, Qt.ItemDataRole.UserRole, "url_adb")
        QTreeWidgetItem(resources, ["XDA Developers Forum"]).setData(0, Qt.ItemDataRole.UserRole, "url_xda")

        self.nav_tree.expandAll()

    def _on_nav_click(self, item: QTreeWidgetItem, column: int):
        """Handle navigation item click"""
        topic = item.data(0, Qt.ItemDataRole.UserRole)
        if topic:
            self._show_topic(topic)

    def _show_topic(self, topic: str):
        """Display help topic content"""
        content = self._get_topic_content(topic)
        self.content_area.setHtml(self._wrap_html(content))

    def _show_welcome(self):
        """Show welcome content"""
        self.content_area.setHtml(self._wrap_html(self._get_topic_content("welcome")))

    def _get_topic_content(self, topic: str) -> str:
        """Get HTML content for a topic"""
        content_map: Dict[str, str] = {
            "welcome": self._welcome_content(),
            "getting_started": self._getting_started_content(),
            "quick_start": self._quick_start_content(),
            "requirements": self._requirements_content(),
            "adb_drivers": self._adb_drivers_content(),
            "virus_remover": self._virus_remover_content(),
            "connect_device": self._connect_device_content(),
            "select_apps": self._select_apps_content(),
            "user_zero": self._user_zero_content(),
            "virus_troubleshoot": self._virus_troubleshoot_content(),
            "finance_guide": self._finance_guide_content(),
            "finance_usage": self._finance_usage_content(),
            "finance_transsion": self._finance_transsion_content(),
            "finance_honor": self._finance_honor_content(),
            "finance_xiaomi": self._finance_xiaomi_content(),
            "finance_oppo": self._finance_oppo_content(),
            "finance_vivo": self._finance_vivo_content(),
            "finance_permanent": self._finance_permanent_content(),
            "finance_tools": self._finance_tools_content(),
            "advanced": self._advanced_content(),
            "adb_commands": self._adb_commands_content(),
            "backup": self._backup_content(),
            "recovery": self._recovery_content(),
            "resources": self._resources_content(),
            "url_gms": self._url_content("GMS Reseller", "https://gmsreseller.com/", "FRP server for unlocking finance locks"),
            "url_adb": self._url_content("ADB Official", "https://developer.android.com/tools/adb", "Official ADB downloads and documentation"),
            "url_xda": self._url_content("XDA Developers", "https://xdaforums.com/", "Community forum for Android development and modding"),
        }
        return content_map.get(topic, self._welcome_content())

    def _welcome_content(self) -> str:
        return """
        <h2>Welcome to PhoneToolKit</h2>
        <p><b>PhoneToolKit</b> is an all-in-one desktop application for Android device management,
        combining a Virus Remover (ADB-based app uninstaller) and a comprehensive Finance Lock Removal Guide.</p>

        <h3>📋 What's Included</h3>
        <ul>
            <li><b>Virus Remover</b> - Safely uninstall unwanted/bloatware apps from your Android device using ADB</li>
            <li><b>Finance Lock Guide</b> - Step-by-step methods for removing finance locks (Payjoy, Home Credit, Billease, etc.) from major phone brands</li>
            <li><b>Built-in Help</b> - Complete documentation and troubleshooting guides</li>
        </ul>

        <h3>🚀 Quick Start</h3>
        <ol>
            <li>Enable <b>USB Debugging</b> on your Android device (Settings → Developer Options)</li>
            <li>Install <b>ADB drivers</b> on your PC (see <a href="#adb_drivers">Installing ADB Drivers</a>)</li>
            <li>Connect your device via USB</li>
            <li>Click <b>Refresh Devices</b> in the Virus Remover tab</li>
            <li>Select apps and click <b>Uninstall Selected</b></li>
        </ol>

        <h3>⚠️ Important Warnings</h3>
        <ul>
            <li><b>Finance lock removal</b> may void warranty and carries risks</li>
            <li><b>Semi-permanent unlocks</b> (Xiaomi/Redmi) will RELOCK after factory reset or system update</li>
            <li><b>Payjoy on Honor/Oppo/Vivo</b> has high relock risk - proceed with caution</li>
            <li>Always <b>backup your data</b> before attempting any unlock</li>
            <li>Some methods require <b>paid tools/services</b> (AMT, UT, TSM, FCKTOOL, GMS Reseller)</li>
        </ul>

        <p style="color: #666; font-size: 12px;">Use the navigation panel on the left to explore detailed guides.</p>

        <hr>
        <p style="font-size: 11px; color: #888; text-align: center;">
            <b>Developed by jstndcllrc</b> &nbsp;|&nbsp;
            📘 <a href="https://www.facebook.com/jstndcllrc/">facebook.com/jstndcllrc</a>
        </p>
        """

    def _getting_started_content(self) -> str:
        return """
        <h2>Getting Started</h2>
        <p>PhoneToolKit requires minimal setup. Follow these steps to get started:</p>

        <h3>1. Enable Developer Options & USB Debugging</h3>
        <ol>
            <li>Go to <b>Settings → About Phone</b></li>
            <li>Tap <b>Build Number</b> 7 times to enable Developer Options</li>
            <li>Go to <b>Settings → System → Developer Options</b></li>
            <li>Enable <b>USB Debugging</b></li>
            <li>Enable <b>Install via USB</b> (if available)</li>
        </ol>

        <h3>2. Install ADB Drivers</h3>
        <p>See <a href="#adb_drivers">Installing ADB Drivers</a> for detailed instructions.</p>

        <h3>3. Connect Device</h3>
        <ol>
            <li>Connect phone via USB cable</li>
            <li>On phone, allow USB debugging when prompted</li>
            <li>In PhoneToolKit, click <b>Refresh Devices</b></li>
        </ol>
        """

    def _quick_start_content(self) -> str:
        return """
        <h2>Quick Start Guide</h2>

        <h3>Virus Remover (5 minutes)</h3>
        <ol>
            <li>Connect device with USB debugging enabled</li>
            <li>Click <b>Refresh Devices</b> → select your device</li>
            <li>Wait for app list to load</li>
            <li>Search or browse for apps to remove</li>
            <li>Check boxes next to unwanted apps</li>
            <li>Keep <b>Current User Only (--user 0)</b> checked (recommended)</li>
            <li>Click <b>Uninstall Selected</b> → confirm</li>
        </ol>

        <h3>Finance Lock Guide (reference)</h3>
        <ol>
            <li>Go to <b>Finance Guide</b> tab</li>
            <li>Select your <b>Brand</b> and <b>Lock Type</b></li>
            <li>Or use <b>Wizard Mode</b> for step-by-step</li>
            <li>Read method, warnings, and required tools</li>
            <li>Click tool links to open download/purchase pages</li>
        </ol>
        """

    def _requirements_content(self) -> str:
        return """
        <h2>System Requirements</h2>

        <h3>Minimum Requirements</h3>
        <ul>
            <li><b>OS:</b> Windows 10/11 (64-bit)</li>
            <li><b>RAM:</b> 4 GB minimum, 8 GB recommended</li>
            <li><b>Storage:</b> 500 MB free space</li>
            <li><b>USB:</b> USB 2.0 or higher port</li>
            <li><b>Internet:</b> Required for tool downloads and FRP servers</li>
        </ul>

        <h3>Phone Requirements</h3>
        <ul>
            <li><b>Android:</b> 5.0 (Lollipop) or higher</li>
            <li><b>USB Debugging:</b> Must be enabled</li>
            <li><b>OEM Unlock:</b> May be required for some methods</li>
            <li><b>Battery:</b> 50%+ charge recommended</li>
        </ul>

        <h3>Software Dependencies</h3>
        <ul>
            <li>ADB (included with Android SDK Platform Tools)</li>
            <li>Device-specific drivers (OEM USB drivers)</li>
            <li>For finance unlocks: AMT/UT/TSM/FCKTOOL (separate tools)</li>
        </ul>
        """

    def _adb_drivers_content(self) -> str:
        return """
        <h2>Installing ADB Drivers</h2>

        <h3>Method 1: Universal ADB Driver (Recommended)</h3>
        <ol>
            <li>Download <b>Universal ADB Driver</b> from <a href="https://adb.clockworkmod.com/">adb.clockworkmod.com</a></li>
            <li>Run installer as Administrator</li>
            <li>Restart computer</li>
        </ol>

        <h3>Method 2: OEM-Specific Drivers</h3>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background:#f5f5f5;"><th>Brand</th><th>Driver Download</th></tr>
            <tr><td>Samsung</td><td><a href="https://developer.samsung.com/android-usb-driver">Samsung USB Driver</a></td></tr>
            <tr><td>Xiaomi/Redmi/POCO</td><td><a href="https://xiaomiusbdriver.com/">Xiaomi USB Driver</a></td></tr>
            <tr><td>Oppo/Realme</td><td><a href="https://www.oppo.com/en/support/software/">Oppo USB Driver</a></td></tr>
            <tr><td>Vivo</td><td><a href="https://www.vivo.com/en/support/software">Vivo USB Driver</a></td></tr>
            <tr><td>Transsion (Tecno/Infinix/Itel)</td><td><a href="https://www.transsion.com/">Transsion USB Driver</a></td></tr>
            <tr><td>Honor</td><td><a href="https://www.honor.com/support/">Honor USB Driver</a></td></tr>
            <tr><td>Google Pixel</td><td><a href="https://developer.android.com/studio/run/win-usb">Google USB Driver</a></td></tr>
        </table>

        <h3>Method 3: Android SDK Platform Tools</h3>
        <ol>
            <li>Download <a href="https://developer.android.com/studio/releases/platform-tools">Platform Tools</a></li>
            <li>Extract to folder (e.g., C:\\platform-tools)</li>
            <li>Add folder to System PATH</li>
            <li>Run <code>adb devices</code> in terminal to verify</li>
        </ol>

        <h3>Verify Installation</h3>
        <pre style="background:#f5f5f5; padding:10px; border-radius:4px;">
adb version
adb devices
        </pre>
        <p>Should show your device serial when connected with USB debugging enabled.</p>
        """

    def _virus_remover_content(self) -> str:
        return """
        <h2>Virus Remover (ADB App Uninstaller)</h2>
        <p>This module uses ADB to safely uninstall user-installed apps from your Android device
        without requiring root access (for <b>--user 0</b> mode).</p>

        <h3>Features</h3>
        <ul>
            <li>Auto-detects connected devices</li>
            <li>Lists all third-party (user) apps</li>
            <li>Optional: Show system apps</li>
            <li>Multi-select with search/filter</li>
            <li>Batch uninstall with progress tracking</li>
            <li>Detailed activity log with export</li>
        </ul>

        <h3>How It Works</h3>
        <p>Uses <code>adb shell pm uninstall --user 0 <package></code> which removes the app
        for the current user (user 0) but keeps the system copy. This is safer than full uninstall
        and doesn't require root.</p>

        <h3>See Also</h3>
        <ul>
            <li><a href="#connect_device">Connecting Your Device</a></li>
            <li><a href="#select_apps">Selecting Apps to Remove</a></li>
            <li><a href="#user_zero">Understanding --user 0</a></li>
            <li><a href="#virus_troubleshoot">Troubleshooting</a></li>
        </ul>
        """

    def _connect_device_content(self) -> str:
        return """
        <h2>Connecting Your Device</h2>

        <h3>Step-by-Step</h3>
        <ol>
            <li><b>Enable USB Debugging</b> (see Getting Started)</li>
            <li><b>Use a quality USB cable</b> (data cable, not charge-only)</li>
            <li><b>Connect to PC</b> - avoid USB hubs if possible</li>
            <li><b>Allow debugging</b> - check "Always allow from this computer" on phone</li>
            <li><b>Click Refresh Devices</b> in Virus Remover tab</li>
        </ol>

        <h3>Common Issues</h3>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background:#f5f5f5;"><th>Issue</th><th>Solution</th></tr>
            <tr><td>Device shows "unauthorized"</td><td>Check phone screen, allow USB debugging prompt</td></tr>
            <tr><td>Device not listed</td><td>Try different cable/port, reinstall drivers, restart ADB: <code>adb kill-server && adb start-server</code></td></tr>
            <tr><td>Shows "offline"</td><td>Reconnect cable, toggle USB debugging off/on</td></tr>
            <tr><td>Multiple devices</td><td>Only one device supported at a time; disconnect others</td></tr>
        </table>

        <h3>Wireless ADB (Advanced)</h3>
        <p>For Android 11+: Settings → Developer Options → Wireless Debugging → Pair with pairing code.</p>
        """

    def _select_apps_content(self) -> str:
        return """
        <h2>Selecting Apps to Remove</h2>

        <h3>Interface Overview</h3>
        <ul>
            <li><b>Search box:</b> Type to filter by app name or package name</li>
            <li><b>Show System Apps:</b> Toggle to see pre-installed system apps (use caution!)</li>
            <li><b>Select All / Deselect All:</b> Quick selection buttons</li>
            <li><b>Checkboxes:</b> Check apps you want to uninstall</li>
            <li><b>Type column:</b> Shows "User" (safe) or "System" (caution)</li>
        </ul>

        <h3>Safe to Remove (Examples)</h3>
        <ul>
            <li>Bloatware from carrier/manufacturer</li>
            <li>Unused social media apps</li>
            <li>Pre-installed games</li>
            <li>Duplicate/alternative apps</li>
        </ul>

        <h3>⚠️ DO NOT Remove (Critical System Apps)</h3>
        <ul>
            <li><code>com.android.settings</code> - Settings app</li>
            <li><code>com.android.phone</code> - Phone/dialer</li>
            <li><code>com.android.systemui</code> - System UI</li>
            <li><code>com.google.android.gms</code> - Google Play Services</li>
            <li>Any app with "System" type unless you're certain</li>
        </ul>

        <h3>Tip</h3>
        <p>Google the package name if unsure. Format: <code>com.company.appname</code></p>
        """

    def _user_zero_content(self) -> str:
        return """
        <h2>Understanding --user 0</h2>

        <h3>What is --user 0?</h3>
        <p>Android supports multiple users. User 0 is the primary/owner user.
        The flag <code>--user 0</code> uninstalls the app <b>only for the current user</b>,
        not system-wide.</p>

        <h3>Comparison</h3>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background:#f5f5f5;"><th>Mode</th><th>Command</th><th>Effect</th><th>Requires Root</th></tr>
            <tr><td><b>Current User Only</b></td><td><code>pm uninstall --user 0 pkg</code></td><td>App hidden for user 0, data kept for other users</td><td>No</td></tr>
            <tr><td>All Users</td><td><code>pm uninstall pkg</code></td><td>App completely removed from system</td><td>Yes (usually)</td></tr>
        </table>

        <h3>Why Use --user 0 (Recommended)</h3>
        <ul>
            <li><b>No root required</b> - works on stock devices</li>
            <li><b>Reversible</b> - can reinstall from Play Store</li>
            <li><b>Safer</b> - system apps remain intact</li>
            <li><b>Preserves data</b> - other users unaffected</li>
        </ul>

        <h3>When to Uncheck (All Users)</h3>
        <ul>
            <li>You have root access (Magisk, etc.)</li>
            <li>You want to completely remove system bloatware</li>
            <li>You understand the risks (potential bootloop, OTA update issues)</li>
        </ul>
        """

    def _virus_troubleshoot_content(self) -> str:
        return """
        <h2>Virus Remover Troubleshooting</h2>

        <h3>Common Errors</h3>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background:#f5f5f5;"><th>Error</th><th>Cause</th><th>Solution</th></tr>
            <tr><td>DELETE_FAILED_INTERNAL_ERROR</td><td>App is device admin</td><td>Settings → Security → Device Admin Apps → Disable</td></tr>
            <tr><td>DELETE_FAILED_DEVICE_POLICY_MANAGER</td><td>Work profile/MDM</td><td>Remove work profile first</td></tr>
            <tr><td>Failure [not installed for 0]</td><td>Already uninstalled for user</td><td>App already removed, ignore</td></tr>
            <tr><td>Permission denied</td><td>No root, trying all-users</td><td>Enable --user 0 mode</td></tr>
            <tr><td>Device not found</td><td>Connection lost</td><td>Reconnect, check cable, restart ADB</td></tr>
        </table>

        <h3>ADB Reset Commands</h3>
        <pre style="background:#f5f5f5; padding:10px; border-radius:4px;">
adb kill-server
adb start-server
adb devices
        </pre>

        <h3>Log Analysis</h3>
        <p>Use <b>Export Log</b> to save activity log for troubleshooting.
        Share log when reporting issues.</p>
        """

    def _finance_guide_content(self) -> str:
        return """
        <h2>Finance Lock Removal Guide</h2>
        <p>This guide covers methods for removing finance locks (Payjoy, Home Credit, Billease, Salmon, etc.)
        from various phone brands. <b>Read all warnings before attempting.</b></p>

        <h3>🎯 Guide Structure</h3>
        <ul>
            <li><b>Reference Cards</b> - Browse all methods with expandable details</li>
            <li><b>Table View</b> - Compact comparison of all methods</li>
            <li><b>Wizard Mode</b> - Step-by-step: Select Brand → Select Lock → Get Instructions</li>
        </ul>

        <h3>🔑 Key Concepts</h3>
        <ul>
            <li><b>Permanent Unlock:</b> Stays unlocked after reset/update</li>
            <li><b>Semi-Permanent:</b> Relocks after factory reset or system update</li>
            <li><b>FRP (Factory Reset Protection):</b> Google account lock after reset</li>
            <li><b>FRP Server:</b> Paid online service to bypass FRP</li>
        </ul>

        <h3>⚠️ Universal Warnings</h3>
        <ul>
            <li>May void warranty</li>
            <li>Risk of bricking device</li>
            <li>Some methods require paid tools/services</li>
            <li>Semi-permanent unlocks will relock on reset/update</li>
            <li>Payjoy on Honor/Oppo/Vivo has high relock risk</li>
        </ul>
        """

    def _finance_usage_content(self) -> str:
        return """
        <h2>How to Use the Finance Guide</h2>

        <h3>Method 1: Reference Cards (Default View)</h3>
        <ol>
            <li>Use <b>Search</b> to find your device/lock</li>
            <li>Filter by <b>Brand</b> and <b>Lock Type</b></li>
            <li>Click <b>▼</b> to expand a card for full details</li>
            <li>Click <b>Open</b> on tools to visit download/purchase page</li>
            <li>Click <b>Copy Method</b> to copy instructions to clipboard</li>
        </ol>

        <h3>Method 2: Table View</h3>
        <p>Switch to "Table View" for a compact comparison.
        Scroll horizontally to see all columns.</p>

        <h3>Method 3: Wizard Mode (Easiest)</h3>
        <ol>
            <li>Select "Wizard Mode" from View dropdown</li>
            <li>Step 1: Choose your <b>Phone Brand</b></li>
            <li>Step 2: Choose <b>Finance Lock Type</b></li>
            <li>Step 3: Read formatted instructions</li>
        </ol>

        <h3>Filter Options</h3>
        <ul>
            <li><b>Show Permanent Only:</b> Hide semi-permanent methods</li>
            <li><b>Search:</b> Finds matches in brand, model, method, tools, notes</li>
        </ul>
        """

    def _finance_transsion_content(self) -> str:
        return """
        <h2>Transsion Devices (Tecno, Infinix, Itel)</h2>

        <h3>Payjoy Lock</h3>
        <p><b>Models:</b> Camon 40/40 Pro (CM5/CM6), all Transsion with Payjoy</p>
        <p><b>Method:</b></p>
        <ol>
            <li>Flash OLD Android 15 version using AMT Tool iFlash</li>
            <li>After flashing, perform System Update</li>
            <li>After restart, Factory Reset the phone</li>
            <li>This removes Developer Menu from homescreen</li>
        </ol>
        <p><b>Tools:</b> AMT Tool (paid), iFlash component</p>
        <p><b>⚠️ Warning:</b> Must flash OLD Android 15 specifically. Factory reset mandatory.</p>

        <h3>Salmon / Home Credit / Billease</h3>
        <p><b>Models:</b> All Transsion models</p>
        <p><b>Method:</b> Format via FRP using AMT/UT/TSM Tool (any FRP-supported online tool)</p>
        <p><b>Tools:</b> AMT Tool, UT Tool, TSM Tool</p>
        <p><b>Note:</b> Not limited to specific tool - any FRP-capable tool works</p>
        """

    def _finance_honor_content(self) -> str:
        return """
        <h2>Honor Devices</h2>

        <h3>Payjoy Lock ⚠️ HIGH RISK</h3>
        <p><b>AVOID - May cause relock.</b> Not recommended for Payjoy on Honor devices.</p>
        <p>Any Honor model with Payjoy finance lock - proceed with extreme caution.</p>

        <h3>Salmon / Home Credit / Billease</h3>
        <p><b>Models:</b> All Honor models</p>
        <p><b>Method:</b> Format via FRP Server using serial registration</p>
        <p><b>Tool:</b> <a href="https://gmsreseller.com/">GMS Reseller</a> (Pricy - paid service)</p>
        <p><b>Process:</b> Register device serial on server → FRP bypass</p>
        <p><b>⚠️ Warning:</b> Requires paid server access. Service is expensive.</p>
        """

    def _finance_xiaomi_content(self) -> str:
        return """
        <h2>Xiaomi / Redmi / POCO Devices</h2>

        <h3>⚠️ CRITICAL: ALL METHODS ARE SEMI-PERMANENT</h3>
        <p><b>Finance lock WILL RETURN after factory reset or system update.</b></p>
        <p><b>DO NOT RESET or do SYSTEM UPDATE</b> - phone will get stuck in recovery!</p>

        <h3>All Finance Locks (Payjoy, Salmon, Home Credit, Billease)</h3>
        <p><b>Models:</b> All Redmi/Xiaomi/POCO models</p>
        <p><b>Method:</b> Format via FRP Server using FCKTOOL</p>
        <p><b>Tools:</b></p>
        <ul>
            <li>FCKTOOL (FRP server tool)</li>
            <li>Credits from <a href="https://gmsreseller.com/">GMS Reseller</a> (Paid)</li>
        </ul>

        <h3>After Unlock</h3>
        <ul>
            <li>Phone works normally</li>
            <li>✅ Can use apps, calls, data</li>
            <li>❌ <b>NEVER factory reset</b></li>
            <li>❌ <b>NEVER system update</b></li>
            <li>❌ Finance lock returns if you do either</li>
        </ul>
        """

    def _finance_oppo_content(self) -> str:
        return """
        <h2>Oppo & Realme Devices</h2>

        <h3>Payjoy Lock ⚠️ HIGH RISK</h3>
        <p><b>AVOID - May cause relock.</b> Not recommended for Payjoy on Oppo/Realme.</p>

        <h3>Salmon / Home Credit / Billease</h3>
        <p><b>Models:</b> All Oppo & Realme (MTK devices)</p>
        <p><b>Method:</b> Format via FRP/FRP Server</p>
        <p><b>Tools:</b></p>
        <ul>
            <li><b>UT Tool</b> - New update for MTK devices (TRY THIS FIRST)</li>
            <li><b>FRP Server</b> - Paid option (Pricy, especially for Realme)</li>
        </ul>
        <p><b>Note:</b> New UT Tool update for MTK Oppo/Realme - try this before paid server.</p>
        """

    def _finance_vivo_content(self) -> str:
        return """
        <h2>Vivo Devices</h2>

        <h3>Payjoy Lock ⚠️ HIGH RISK</h3>
        <p><b>AVOID - May cause relock.</b> Not recommended for Payjoy on Vivo.</p>

        <h3>Salmon / Home Credit / Billease</h3>
        <p><b>Models:</b> All Vivo models</p>
        <p><b>Method:</b> Format via FRP/FRP Server</p>
        <p><b>Tools:</b></p>
        <ul>
            <li><b>TSM Tool</b> - Latest update for Vivo models (TRY THIS FIRST)</li>
            <li><b>GMS Reseller</b> - Remote service available (<a href="https://gmsreseller.com/">Pricy</a>)</li>
        </ul>
        <p><b>Note:</b> Latest TSM Tool update for Vivo models available.</p>
        """

    def _finance_permanent_content(self) -> str:
        return """
        <h2>Permanent vs Semi-Permanent Unlocks</h2>

        <h3>Permanent Unlock ✅</h3>
        <ul>
            <li>Stays unlocked after factory reset</li>
            <li>Stays unlocked after system update</li>
            <li>Transsion (Salmon/HC/Billease) - via FRP tools</li>
            <li>Honor (Salmon/HC/Billease) - via FRP server</li>
            <li>Oppo/Realme (Salmon/HC/Billease) - via UT Tool/FRP server</li>
            <li>Vivo (Salmon/HC/Billease) - via TSM Tool/FRP server</li>
        </ul>

        <h3>Semi-Permanent Unlock ⚠️</h3>
        <ul>
            <li><b>Relocks after factory reset</b></li>
            <li><b>Relocks after system update</b></li>
            <li><b>ALL Xiaomi/Redmi/POCO finance locks</b></li>
            <li>Phone works normally otherwise</li>
            <li>Must avoid reset/update forever</li>
        </ul>

        <h3>What Triggers Relock (Semi-Permanent)</h3>
        <ul>
            <li>Factory Reset (Settings → Reset)</li>
            <li>System Update (OTA)</li>
            <li>Recovery Mode → Wipe Data</li>
            <li>Flashing stock ROM</li>
        </ul>

        <h3>What's Safe After Semi-Permanent Unlock</h3>
        <ul>
            <li>Normal daily use</li>
            <li>App installs/uninstalls</li>
            <li>Restarting phone</li>
            <li>Security patch updates (sometimes)</li>
        </ul>
        """

    def _finance_tools_content(self) -> str:
        return """
        <h2>Tool References</h2>

        <h3>AMT Tool (Transsion)</h3>
        <p><b>Purpose:</b> Flashing, unlocking, FRP bypass for Tecno/Infinix/Itel<br>
        <b>Components:</b> iFlash (flashing), FRP bypass<br>
        <b>Availability:</b> Paid/authorized distributors</p>

        <h3>UT Tool (Universal Tool)</h3>
        <p><b>Purpose:</b> Multi-brand FRP bypass, unlocking<br>
        <b>Brands:</b> Transsion, Oppo/Realme (MTK), others<br>
        <b>Note:</b> New update for MTK Oppo/Realme devices</p>

        <h3>TSM Tool (Transsion Service Module)</h3>
        <p><b>Purpose:</b> Transsion-specific service operations<br>
        <b>Brands:</b> Tecno/Infinix/Itel, Vivo (latest update)<br>
        <b>Features:</b> FRP, unlock, repair</p>

        <h3>FCKTOOL (Xiaomi)</h3>
        <p><b>Purpose:</b> FRP server for Xiaomi/Redmi/POCO<br>
        <b>Note:</b> Semi-permanent only. Credits from GMS Reseller.</p>

        <h3>GMS Reseller (FRP Server)</h3>
        <p><b>URL:</b> <a href="https://gmsreseller.com/">https://gmsreseller.com/</a><br>
        <b>Purpose:</b> Paid FRP bypass via serial registration<br>
        <b>Brands:</b> Honor, Xiaomi, Vivo, others<br>
        <b>Cost:</b> Pricy - varies by model/lock type</p>

        <h3>Other Resources</h3>
        <ul>
            <li><b>XDA Developers:</b> <a href="https://xdaforums.com/">xdaforums.com</a> - Community guides</li>
            <li><b>GSM Forum:</b> <a href="https://forum.gsmhosting.com/">gsmhosting.com</a> - Technician discussions</li>
            <li><b>ADB Official:</b> <a href="https://developer.android.com/tools/adb">developer.android.com</a></li>
        </ul>
        """

    def _advanced_content(self) -> str:
        return """
        <h2>Advanced Topics</h2>
        <p>For experienced users and technicians.</p>
        <ul>
            <li><a href="#adb_commands">ADB Command Reference</a></li>
            <li><a href="#backup">Backup Before Uninstall</a></li>
            <li><a href="#recovery">Recovering from Bootloop</a></li>
        </ul>
        """

    def _adb_commands_content(self) -> str:
        return """
        <h2>ADB Command Reference</h2>

        <h3>Device Management</h3>
        <pre style="background:#f5f5f5; padding:10px; border-radius:4px;">
adb devices -l           # List devices with details
adb get-state            # Check device state
adb kill-server          # Restart ADB server
adb start-server         # Start ADB server
adb usb                  # Restart in USB mode
adb tcpip 5555           # Enable wireless debugging
        </pre>

        <h3>Package Management</h3>
        <pre style="background:#f5f5f5; padding:10px; border-radius:4px;">
adb shell pm list packages           # All packages
adb shell pm list packages -3        # Third-party only
adb shell pm list packages -s        # System only
adb shell pm list packages -d        # Disabled only
adb shell pm uninstall --user 0 pkg  # Uninstall for user 0
adb shell pm uninstall pkg           # Uninstall all users (root)
adb shell pm disable-user --user 0 pkg  # Disable instead of uninstall
adb shell pm enable --user 0 pkg     # Re-enable
adb shell pm clear pkg               # Clear app data
adb shell pm path pkg                # Get APK path
        </pre>

        <h3>File Transfer</h3>
        <pre style="background:#f5f5f5; padding:10px; border-radius:4px;">
adb push local remote    # Copy file to device
adb pull remote local    # Copy file from device
adb shell                # Open shell on device
        </pre>

        <h3>System Info</h3>
        <pre style="background:#f5f5f5; padding:10px; border-radius:4px;">
adb shell getprop ro.product.model       # Device model
adb shell getprop ro.build.version.release  # Android version
adb shell getprop ro.build.id            # Build ID
adb shell dumpsys battery                # Battery info
        </pre>
        """

    def _backup_content(self) -> str:
        return """
        <h2>Backup Before Uninstall</h2>
        <p><b>Always backup before removing apps or attempting finance unlocks!</b></p>

        <h3>ADB Backup (No Root)</h3>
        <pre style="background:#f5f5f5; padding:10px; border-radius:4px;">
# Backup specific app
adb shell bu backup com.example.app -f backup.ab

# Backup all apps (shared storage)
adb shell bu backup -all -shared -f full_backup.ab

# Restore
adb shell bu restore backup.ab
        </pre>

        <h3>Google Backup</h3>
        <p>Settings → System → Backup → Back up to Google Drive</p>

        <h3>Manufacturer Backup Tools</h3>
        <ul>
            <li>Samsung: Smart Switch</li>
            <li>Xiaomi: Mi Cloud / Mi Mover</li>
            <li>Oppo/Realme: Clone Phone</li>
            <li>Vivo: Vivo Cloud / EasyShare</li>
            <li>Transsion: Phone Clone</li>
        </ul>

        <h3>Manual Backup (Important Data)</h3>
        <ul>
            <li>Photos/Videos: Google Photos, copy to PC</li>
            <li>Contacts: Export to .vcf or Google Contacts</li>
            <li>Messages: SMS Backup & Restore app</li>
            <li>App data: Helium (requires ADB), or app-specific export</li>
        </ul>
        """

    def _recovery_content(self) -> str:
        return """
        <h2>Recovering from Bootloop / Soft Brick</h2>
        <p>If device won't boot after uninstall/flash:</p>

        <h3>1. Force Restart</h3>
        <p>Hold Power + Volume Down for 10-20 seconds</p>

        <h3>2. Recovery Mode</h3>
        <ul>
            <li>Power off → Hold Power + Volume Up</li>
            <li>Navigate with Volume, select with Power</li>
            <li>Try: "Wipe Cache Partition" (NOT factory reset)</li>
        </ul>

        <h3>3. Fastboot Mode</h3>
        <pre style="background:#f5f5f5; padding:10px; border-radius:4px;">
fastboot devices          # Check connection
fastboot reboot           # Normal reboot
fastboot reboot recovery  # Boot to recovery
        </pre>

        <h3>4. Flash Stock ROM (Last Resort)</h3>
        <ul>
            <li>Download official firmware for exact model</li>
            <li>Use manufacturer flash tool (Odin, Mi Flash, SP Flash Tool, etc.)</li>
            <li><b>WARNING:</b> This WILL erase all data</li>
        </ul>

        <h3>5. EDL Mode (Emergency Download)</h3>
        <p>For Qualcomm devices - requires test points or special cable. Professional service recommended.</p>

        <h3>When to Seek Professional Help</h3>
        <ul>
            <li>Device doesn't enter any mode</li>
            <li>Hardware damage suspected</li>
            <li>EDL mode required</li>
            <li>Data recovery needed</li>
        </ul>
        """

    def _resources_content(self) -> str:
        return """
        <h2>External Resources</h2>
        <p>Click links to open in browser.</p>
        <ul>
            <li><a href="https://gmsreseller.com/">GMS Reseller</a> - FRP server (paid)</li>
            <li><a href="https://developer.android.com/tools/adb">ADB Official</a> - Downloads & docs</li>
            <li><a href="https://xdaforums.com/">XDA Developers</a> - Community forum</li>
            <li><a href="https://forum.gsmhosting.com/">GSM Hosting</a> - Technician forum</li>
        </ul>
        """

    def _url_content(self, title: str, url: str, description: str) -> str:
        return f"""
        <h2>{title}</h2>
        <p>{description}</p>
        <p><a href="{url}" style="font-size: 14px; font-weight: bold;">🔗 Open: {url}</a></p>
        <p><button onclick="window.open('{url}')" style="padding: 10px 20px; font-size: 14px;">Open in Browser</button></p>
        """

    def _check_updates(self):
        QMessageBox.information(self, "Updates",
            "Update checking not implemented in this version.\n"
            "Check the project repository for new releases.")

    def _report_issue(self):
        QMessageBox.information(self, "Report Issue",
            "Please report issues with:\n"
            "1. PhoneToolKit version\n"
            "2. Windows version\n"
            "3. Device model & Android version\n"
            "4. Steps to reproduce\n"
            "5. Exported log file (from Virus Remover tab)")

    def _show_about(self):
        QMessageBox.about(self, "About PhoneToolKit",
            "<h3>PhoneToolKit v1.0.0</h3>"
            "<p>All-in-One Android Device Management Tool</p>"
            "<p><b>Modules:</b></p>"
            "<ul>"
            "<li>Virus Remover — ADB-based app uninstaller with dynamic app icons</li>"
            "<li>Finance Lock Guide — Removal methods for Transsion, Honor, Xiaomi, Oppo/Realme, Vivo</li>"
            "<li>Built-in Help &amp; Documentation</li>"
            "</ul>"
            "<p><b>Built with:</b> Python, PySide6 (Qt for Python)</p>"
            "<hr>"
            "<p><b>Developed by:</b> <b>jstndcllrc</b></p>"
            "<p>📘 Facebook: <a href='https://www.facebook.com/jstndcllrc/'>https://www.facebook.com/jstndcllrc/</a></p>"
            "<hr>"
            "<p><b>License:</b> For educational/technician use only</p>"
            "<p>⚠️ Use at your own risk. Finance lock removal may void warranty.</p>"
        )