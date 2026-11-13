# PhoneToolKit - Development Progress Log

## Project Overview
Windows EXE application combining Virus Remover (ADB-based Android app uninstaller) and Finance Lock Guide (phone finance lock removal methods for major brands).

**Tech Stack:** Python 3.10+, PySide6 (Qt for Python), PyInstaller, ADB subprocess

---

## Completed Tasks

### ✅ Task 1: Project Structure & Requirements
- Created modular architecture: `src/main.py`, `src/services/`, `src/ui/`, `src/utils/`
- `requirements.txt`: PySide6, pyinstaller, pillow
- `PhoneToolKit.spec` for PyInstaller single-file EXE build
- `build_exe.bat` / `build_exe.ps1` with PATH detection

### ✅ Task 2: Virus Remover Module (ADB Integration)
- `src/services/adb_service.py`: ADBService with Device/Package dataclasses
- Subprocess wrapper with `CREATE_NO_WINDOW` flag (Windows)
- `get_devices()`, `get_packages()`, `uninstall_package()`, `get_device_model()`
- Global singleton pattern via `get_adb_service()`

### ✅ Task 3: Finance Guide Module
- `src/services/finance_guide.py`: 18 UnlockMethod dataclasses across 5 brands
  - Transsion (Tecno/Infinix/Itel), Honor, Xiaomi, Oppo/Realme, Vivo
- LockType enum: FRP, Mi Account, Screen Lock, MDM
- Search/filter functions, wizard mode support

### ✅ Task 4: Main GUI with Tabs & Help System
- `src/ui/main_window.py`: QMainWindow with QTabWidget (3 tabs)
- Menu bar (File/View/Tools/Help), Status bar with auto-detect indicator
- Theme system: Light (black text on white) / Dark (white text on black) with persistence
- `src/ui/virus_remover_tab.py`: PackageTableWidget with checkboxes, ADBWorker threads
- `src/ui/finance_guide_tab.py`: MethodCard expandable cards + table view + wizard
- `src/ui/help_tab.py`: Tree navigation with 18 topics, HTML content

### ✅ Task 5: Package as Windows EXE
- Multi-resolution ICO generation via `create_icon.py` (16-256px)
- PyInstaller spec with hiddenimports, excludes, console=False
- Successful Linux & Windows build test

---

## Bug Fixes & Improvements

### ✅ Task 6: Auto-Detect Device Functionality
- Only refresh UI when device list actually changes (serial set or count differs)
- Silent refresh mode suppresses "Scanning..." logs during auto-detect
- Status bar updates device status without triggering full refresh

### ✅ Task 7: App Crash on Phone Disconnect
- ADB stderr/stdout parsing detects: unauthorized, offline, not found, no device, disconnected
- Worker emits `device_error` signal instead of generic error
- UI handles disconnection: clears device state, resets controls
- Pre-operation device verification in `_load_packages()`, `_uninstall_selected()`

### ✅ Task 8: State Management Improvements
- `_on_device_changed()`: Only reload if device actually changed (prevents redundant loads)
- Worker cancellation in `refresh_devices()` and `_load_packages()` (prevents race conditions)
- `_on_packages_finished()`: Don't clear table if packages loaded successfully
- Proper worker cleanup in `closeEvent()` for all tabs

---

## Comprehensive Code Review & Stability Overhaul (Latest Session)

### 1. Fix: "Scanned apps not showing after USB debugging detected"
- **Root Cause:** `ADBService.get_packages()` was calling `_get_package_label()` (which ran `pm dump` with a 5s timeout) for every single package. On devices with 50-100 packages, this caused 50-100 sequential ADB subprocess executions, taking 1 to 2+ minutes to return any data to the GUI. For system apps, `_is_third_party()` was also executing `pm list packages -3` hundreds of times sequentially.
- **Fix:**
  - `pm list packages -3` is now executed **once** in a single call to populate a set of third-party package names, enabling O(1) instantaneous classification.
  - Implemented `clean_package_label()` with dictionary mapping for popular Android and Finance Lock apps, plus clean CamelCase/PascalCase word parsing.
  - Package listing now loads in **< 1 second** instead of 1-2 minutes.

### 2. Fix: "Need to click Clear Selection before it shows" & Table Freezing
- **Root Cause:** In `PackageTableWidget`, `self.setSortingEnabled(True)` was enabled during initial construction. Populating a `QTableWidget` row-by-row via `setItem()` while sorting is enabled triggers Qt's internal sort comparison on every single item insertion. This corrupted row layout and suppressed painting until an external widget event (such as clicking "Clear Selection") forced a repaint.
- **Fix:**
  - Disabled sorting before table population (`self.setSortingEnabled(False)`) and re-enabled it only after all rows are populated (`self.setSortingEnabled(True)`).

### 3. Fix: "App closes after apps show" (Hard Python GIL Crash)
- **Root Cause:** `VirusRemoverTab` and `MainWindow` used `self.worker.terminate()`. In Python/PySide6, terminating a QThread forcibly terminates the OS thread while it holds the Python GIL or during memory allocation, causing an immediate Access Violation / Segmentation Fault. Additionally, sorting while rows were partially populated caused null pointer dereferences inside Qt's model comparison.
- **Fix:**
  - Implemented safe, cooperative thread cancellation via `worker.cancel()`, `_is_cancelled` flags, signal disconnection, and clean `worker.wait(1000)` in `_stop_worker()`. `QThread.terminate()` was completely removed.

### 4. Fix: Checkbox Desynchronization on Column Sorting
- **Root Cause:** `QTableWidget.setCellWidget()` creates floating child QWidgets positioned at cell coordinates rather than model data. When the user sorted the table by clicking a column header, `QTableWidgetItem` rows moved, but `QCheckBox` widgets remained fixed at their initial row indices, causing selected checkboxes to correspond to the wrong apps!
- **Fix:**
  - Replaced `setCellWidget()` with native `QTableWidgetItem` checkable state (`Qt.ItemFlag.ItemIsUserCheckable`). Check states and UserRole data now sort natively and reliably with rows.

### 5. Fix: Dark Mode Contrast Issues in Finance Guide & Help Tabs
- **Root Cause:** `MethodCard` and `HelpTab.content_area` had hardcoded light backgrounds (`#fafafa`, `#f5f5f5`), resulting in white text on light backgrounds in Dark Mode.
- **Fix:**
  - Added dynamic theme listeners (`update_theme(dark_mode)`), providing dedicated dark-mode backgrounds, code styling, and high-contrast text.

### 6. Fix: Main Thread Freezing on Auto-Detect
- **Root Cause:** `MainWindow._auto_detect_devices()` was calling `adb.get_devices()` synchronously on the main GUI thread every 5 seconds.
- **Fix:**
  - Delegated device detection to the non-blocking background worker thread and connected status bar updates via `virus_tab.devices_updated`.

### 7. Fix: Dev Mode Resource Path Resolution
- **Root Cause:** `src/utils/resources.py` resolved `get_base_path()` to `src/` instead of the project root in development, failing to locate `resources/icon.ico`.
- **Fix:**
  - Corrected path resolution to inspect project root for `resources/`.

### 8. Fix: Subprocess Encoding & Path Auto-Discovery
- **Fix:**
  - Added `encoding="utf-8", errors="replace"` to all ADB subprocess calls to prevent `UnicodeDecodeError` on non-ASCII app or device names.
  - Added auto-discovery for `adb.exe` in common Android SDK directories if not present in System PATH.

### 9. Fix: "Installed Applications window only showing one line of apps installed"
- **Root Cause:**
  - 4 separate `QGroupBox`es were vertically stacked in `VirusRemoverTab` (`Device Connection`, `Installed Applications`, `Uninstall Options`, and `Activity Log`).
  - `Activity Log` took up ~220px, `Uninstall Options` took up ~90px, and `Device Connection` took up ~120px. On typical window heights (700-800px), these consumed ~430px of vertical space, leaving as little as 20-30px for the `PackageTableWidget` inside `pkg_group`!
  - `QTableWidget::item` had excessive CSS padding (`padding: 10px`), resulting in ~42px tall rows.
- **Fix:**
  - Condensed `Device Connection` from a 2-row grid into a sleek, single-row layout saving ~65px.
  - Merged the standalone `Uninstall Options` groupbox directly into the `Installed Applications` bottom action bar (`[Total count] [Current User Only] [Uninstall Selected]`), reclaiming ~90px of vertical space.
  - Embedded `pkg_group` and `log_group` into a draggable `QSplitter` with an 85%/15% stretch ratio (`setSizes([600, 110])`), giving the table the vast majority of window space.
  - Set `PackageTableWidget.setMinimumHeight(350)` and `defaultSectionSize(32)` so rows are crisp and the table cannot be compressed below 350px.
  - Added an interactive "▲ Hide Log / ▼ Show Log" toggle button to allow dedicating 100% of the screen height to the applications list.
  - Adjusted CSS item padding (`padding: 6px 10px;`) and header padding (`8px 10px;`) in both light and dark themes, showing 13–15+ visible rows simultaneously in windowed mode and 25+ rows when maximized.
  - Enforced minimum window geometry in `MainWindow` (`1000x720`, default `1200x850`).

### 10. Fix: "Scanning should stop as soon as device is detected"
- **Root Cause:**
  - Auto-detect timer (`auto_detect_timer`, 5-second interval) continued firing indefinitely even after a device was detected, repeatedly executing `refresh_devices()` and calling `_stop_worker()`.
  - In `VirusRemoverTab.refresh_devices()`, `self.refresh_btn.setText("🔄 Scanning...")` was set, but when devices were detected and packages started loading, `_stop_worker()` disconnected the worker's `finished` signal. As a result, the lambda resetting the button back to `"🔄 Refresh Devices"` was never executed, leaving the button stuck on `"🔄 Scanning..."` indefinitely.
- **Fix:**
  - In `MainWindow` and `VirusRemoverTab`: The moment connected devices are returned, `self.auto_detect_timer.stop()` is invoked immediately, stopping all background polling.
  - The status bar auto-detect indicator transitions to `"📱 Device Connected"` (green) and pauses scanning.
  - If the device is ever unplugged or disconnected, `self.auto_detect_timer.start()` automatically resumes polling to detect when the device is plugged back in.
  - In `VirusRemoverTab._on_devices_found`, `_on_error`, `_on_device_error`, and `_stop_worker`, the refresh button text and enabled state are guaranteed to be restored to `"🔄 Refresh Devices"` immediately.

### 11. Feature: Dynamic App Icons in Installed Applications Table
- **Added:** `src/utils/icon_provider.py` — zero-dependency icon engine using `QPainter` to generate 48×48 high-DPI icons entirely in-process without any ADB calls.
- **Icon rendering pipeline:**
  1. **Exact resource match**: Checks `resources/icons/<package_name>.png` first so custom icons can be dropped in.
  2. **Specialized brand icons**: 30+ hard-coded authentic-style icons for major apps (YouTube, Chrome, Facebook, Messenger, Instagram, WhatsApp, Telegram, TikTok, Spotify, Netflix, Twitter/X, Discord, Gmail, Maps, GCash, Maya, Shopee, Lazada, Payjoy, Home Credit, BillEase, Salmon, Tala, Settings, Camera, Phone, Messages, Calculator, Clock, Contacts, Files).
  3. **Category fallback**: Finance/Lock apps → red shield with 🔒; System apps → grey ⚙; User apps → colored squircle with uppercase initial derived from app label.
- **Color scheme:** 20-color Material Design palette; deterministic hash on package name so each app always gets the same consistent color.
- **Performance:** 100 icons generate in ~430ms on first run; subsequent calls return from `_ICON_CACHE` dict in O(1). No network, no ADB, no disk reads for generated icons.
- **Integration:** `PackageTableWidget.populate_packages()` now calls `get_package_icon()` and passes the result to `QTableWidgetItem(icon, label)` so icons sort with rows correctly.
- **Table row height:** `setIconSize(QSize(24, 24))` so icons display crisp at 24px inside each row.

### 12. Feature: Developer Credit — Developed by jstndcllrc
- **Added** developer attribution across the application:
  - **About dialog** (`src/ui/help_tab.py` → `_show_about()`): Updated with developer name, Facebook link, and tool description.
  - **Welcome screen** (`_welcome_content()`): Added footer credit with clickable Facebook link.
  - **Status bar** (`src/ui/main_window.py`): Persistent "Built by jstndcllrc" label on bottom right.
  - **Window title bar**: Now reads `PhoneToolKit v1.0.0 — by jstndcllrc`.

### 13. Feature: APK Installation
- **Added** `install_apk()` method to `ADBService` (`src/services/adb_service.py`):
  - Supports `-r` (replace), `-d` (downgrade), `-t` (test packages) flags
  - 120-second timeout for large APKs
  - UTF-8 encoding with error replacement for non-ASCII paths
- **Added** "install" operation to `ADBWorker` with `install_result` signal
- **UI Integration** in `VirusRemoverTab`:
  - "📥 Install APK" button in action bar (enabled when device connected)
  - File picker dialog filtering for `.apk` files
  - Options dialog for "Allow downgrade (-d)" and "Allow test packages (-t)"
  - Indeterminate progress bar during install
  - Success/failure message boxes with detailed ADB output
  - Automatic package list refresh after successful install
  - Device disconnection handling during install

### 14. Feature: Modern UI Theme Overhaul
- **Complete redesign** of color palette across all tabs (`src/ui/main_window.py`):
  - **Light Mode**: Sophisticated slate/teal palette (`#f8fafc` surface, `#1e3a5f` primary, `#00b4a6` accent)
  - **Dark Mode**: Deep charcoal/teal palette (`#121212` surface, `#00d4aa` primary/accent)
  - Softer borders, refined shadows, consistent 8-12px border radius
  - Modern typography with Segoe UI / system font stack
- **Updated components**:
  - Tabs: Clean underline indicator, hover states
  - Buttons: Primary (teal), Danger (rose), subtle hover/pressed states
  - Inputs: Focus rings with accent color, consistent padding
  - Tables: Alternating rows, selection highlighting with accent
  - Checkboxes: Custom SVG checkmarks, smooth transitions
  - Scrollbars: Slim, themed handles
  - Progress bars: Rounded, accent-colored chunks
  - GroupBoxes: Rounded corners, titled with accent color
  - Status bar: Themed indicators (teal=scanning, green=connected, rose=off)
- **Applied to all tabs**: Virus Remover, Finance Guide, Help & Docs
- **Dynamic theme switching** with instant updates (no restart needed)

### 15. Fix: Checkboxes Rendered as Blank Coloured Squares (Checkmark Never Painted)
- **Root Cause:** Both theme stylesheets drew the tick with
  `image: url(data:image/svg+xml;base64,…)`. Qt's stylesheet engine does **not**
  load `data:` URIs for the `image` property — it fails silently, so every
  checked checkbox in the app showed an empty teal (or white) square with no
  tick. Verified by pixel-probing a rendered `QCheckBox`: 0 glyph pixels.
- **Fix:**
  - Added `src/utils/theme_assets.py`: paints the checkmark once with `QPainter`
    at 4× resolution (crisp on high-DPI), saves it as a PNG in
    `data/theme/checkmark_<colour>.png`, and caches both the file and the URL.
  - Stylesheets now receive the asset through a `__CHECKMARK__` placeholder that
    `_apply_light_theme()` / `_apply_dark_theme()` substitute at runtime
    (white tick on light, near-black tick on dark).
  - Also discovered Qt **ignores `file:///` URLs** in QSS; only plain absolute
    paths load. `_as_url()` therefore emits `url("C:/…")` with double quotes so
    spaces in paths survive.
  - Falls back to `~/.phonetoolkit/theme` if the data directory is read-only
    (e.g. installs under `Program Files`).

### 16. Fix: 72 Malformed Declarations Silently Dropped in Dark Mode
- **Root Cause:** The dark theme's QSS terminated **72 declarations with `.`
  instead of `;`** (`spacing: 10px.`, `background: #1a1a1a.`, …). Qt's parser
  discards any declaration it cannot parse, so the entire scrollbar block,
  progress-bar sizing, menu/menu-bar padding, splitter handle size, tooltip
  chrome and all checkbox styling were missing in dark mode — while the light
  theme was unaffected.
- **Fix:** Rewrote every offending declaration with a proper semicolon and added
  a guard to the smoke test that fails the build if a declaration is missing
  `;`, if a `data:image` URI reappears, or if the checkmark stops painting.
- Verified: light theme 11 088 chars / dark 11 083 chars, both parse with
  0 malformed declarations and paint the full checkmark glyph.

### 17. Layout: Installed Applications Action Bar No Longer Overlaps the Table
- **Root Cause:** `PackageTableWidget` carried a hard `setMinimumHeight(350)`,
  which exceeded the room the parent group box could offer at 1000×720. Qt
  honoured the table's minimum and pushed the action bar out past the group
  frame, painting it over the last table rows.
- **Fix:**
  - Dropped the hard floor to `96px` and let the `QSplitter` decide how much
    height the list receives; `pkg_group` keeps a `300px` minimum so the
    toolbar, table and action bar always fit inside the frame.
  - Splitter sizing is resolved from the splitter's *real* height
    (`_apply_splitter_sizes`) instead of absolute pixel guesses, so the
    app-list/log ratio holds at any window size.
  - Collapsing the log now shrink-wraps the group to its own
    `minimumSizeHint()` rather than a hand-computed constant.
- Verified at 1200×850 and 1000×720, with the log both expanded and collapsed.

---

## File Structure

```
PhoneToolKit/
├── src/
│   ├── main.py                 # Entry point, high-DPI, resource loading
│   ├── services/
│   │   ├── adb_service.py      # ADB communication (FAST O(1) package list, clean labels, UTF-8, auto-discovery)
│   │   └── finance_guide.py    # 18 unlock methods, 5 brands, Brand aliases
│   ├── ui/
│   │   ├── main_window.py      # Main window, tabs, theme sync, smart scan stop, developer credit
│   │   ├── virus_remover_tab.py    # Safe thread cancellation, native sortable checkboxes, icons, instant rendering
│   │   ├── finance_guide_tab.py    # Cards, table, wizard, search, theme-aware MethodCards
│   │   └── help_tab.py         # Tree nav, theme-aware HTML renderer & styling, About dialog
│   └── utils/
│       ├── resources.py        # PyInstaller & dev resource path resolution
│       ├── icon_provider.py    # Dynamic app icon engine (QPainter, cached, 30+ brand icons)
│       └── theme_assets.py     # QPainter-generated QSS checkmark (no data: URIs)
├── tests/
│   └── smoke_test.py           # Offline UI regression suite (26 checks, no device needed)
├── resources/
│   ├── icon.ico                # Multi-resolution Windows icon
│   └── icons/                  # Optional: drop <package_name>.png files here for custom icons
├── PhoneToolKit.spec           # PyInstaller spec
├── build_exe.bat               # Windows build script with python -m PyInstaller fallback
├── build_exe.ps1               # PowerShell build script
├── create_icon.py              # Multi-resolution ICO generator
├── requirements.txt            # Dependencies
└── PROGRESS.md                 # Development & bugfix documentation
```

---

## Build Instructions

```bat
# On Windows
build_exe.bat

# Or with PowerShell
powershell -ExecutionPolicy Bypass -File build_exe.ps1

# Or manually
python -m PyInstaller PhoneToolKit.spec --clean --noconfirm

# Output: dist/PhoneToolKit.exe
```

## Running the Smoke Test

```bat
set QT_QPA_PLATFORM=offscreen
set PYTHONPATH=src
python tests\smoke_test.py
```

Runs 26 UI checks with no phone attached (tabs, both themes, icon rendering,
sorting with check states, log toggle, finance wizard, help pages) and exits
non-zero on failure.

---

## Testing Checklist

- [x] Auto-detect: Connect device → appears in combo without manual refresh
- [x] Auto-detect: Disconnect device → status updates to "No device"
- [x] Auto-detect: Non-blocking background execution, no GUI freeze
- [x] Auto-detect: No "Scanning..." log spam every 5 seconds
- [x] Auto-detect: **Scanning stops immediately when device is detected**
- [x] Auto-detect: **Scanning resumes automatically when device is unplugged**
- [x] Package list: Loads in < 1s automatically when device selected
- [x] Package list: Renders immediately without needing button click
- [x] Package list: Sortable by any column with checkboxes staying aligned with packages
- [x] Package list: **App icons displayed for each installed app**
- [x] Package list: Shows 13–15+ rows in windowed mode, 25+ when maximized
- [x] Package list: Splitter resizable between app table and activity log
- [x] Package list: Hide/Show Log toggle for maximum table space
- [x] Disconnect during load: Shows warning/status, doesn't crash
- [x] Disconnect during uninstall: Shows warning, doesn't crash
- [x] Thread safety: Clean worker cancellation without `terminate()` or GIL crashes
- [x] Theme toggle: Light/Dark persists across restarts and updates cards & help docs
- [x] **Modern theme: Sophisticated light/dark palette with teal accent**
- [x] **Modern theme: Consistent spacing, rounded corners, smooth transitions**
- [x] **Modern theme: All 3 tabs (Virus, Finance, Help) properly themed**
- [x] **Checkboxes: tick glyph actually paints in Light and Dark mode**
- [x] **Dark theme: no malformed (`.`-terminated) QSS declarations**
- [x] **Installed Applications action bar stays inside its group box at 1000×720**
- [x] **Checkbox alignment: Native checkboxes centered in Select column**
- [x] **Uninstall progress: Always visible progress bar with count**
- [x] **Uninstall completion: Success message with total apps processed**
- [x] Search/filter: Works on package table
- [x] Select All / Deselect All / Clear Selection: Work correctly
- [x] Uninstall: Confirmation dialog, progress bar, results
- [x] **Install APK: File picker, options dialog, progress, success/failure handling**
- [x] **Install APK: Automatic package list refresh after install**
- [x] **Install APK: Disconnect handling during install**
- [x] Finance Guide: Cards expand/collapse, search, filters work
- [x] Help tab: Navigation tree, content renders in Light and Dark themes
- [x] ADB Restart: Tools menu → Restart ADB works with fallback path detection
- [x] Window state: Position/size/tab persists
- [x] Resource resolution: Works in both development mode and compiled EXE
- [x] About dialog: Shows developer credit (jstndcllrc / Facebook link)

---

## Developer

**Built by:** jstndcllrc  
**Facebook:** https://www.facebook.com/jstndcllrc/
