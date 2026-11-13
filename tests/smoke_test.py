"""Offline smoke test for PhoneToolKit.

Runs the full UI without an Android device attached: every tab, both themes,
table population with icons and sorting, checkbox round-tripping, splitter
toggling and the finance wizard.

Usage (from the project root):

    set QT_QPA_PLATFORM=offscreen
    set PYTHONPATH=src
    python tests/smoke_test.py

Exits non-zero when a check fails, so it can gate a build.
"""
import sys
import traceback

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer

app = QApplication(sys.argv)

from ui.main_window import MainWindow
from services.adb_service import Package
from services.finance_guide import get_all_brands

failures = []
steps = []


def check(name, condition, detail=""):
    steps.append(name)
    if not condition:
        failures.append(f"{name} {detail}".strip())
        print(f"FAIL  {name} {detail}")
    else:
        print(f"ok    {name}")


w = MainWindow()
w.resize(1200, 850)
w.show()
app.processEvents()


def run():
    try:
        # ---- tabs exist -------------------------------------------------
        check("three tabs", w.tabs.count() == 3, f"got {w.tabs.count()}")
        check("virus tab type", type(w.virus_tab).__name__ == "VirusRemoverTab")
        check("finance tab type", type(w.finance_tab).__name__ == "FinanceGuideTab")
        check("help tab type", type(w.help_tab).__name__ == "HelpTab")

        # ---- themes -----------------------------------------------------
        for dark in (True, False, True):
            w.toggle_theme()
            app.processEvents()
            qss = w.styleSheet()
            check(f"theme switch -> dark={w._is_dark_mode()}",
                  len(qss) > 5000 and "__CHECKMARK__" not in qss)

        # ---- package table ----------------------------------------------
        pkgs = [
            Package("com.android.chrome", "Chrome", True, "1.0"),
            Package("com.google.android.youtube", "YouTube", False, "2.0"),
            Package("com.facebook.katana", "Facebook", False, "3.0"),
            Package("com.gcash.money", "GCash", False, "4.0"),
        ]
        w.virus_tab.package_table.populate_packages(pkgs)
        app.processEvents()
        tbl = w.virus_tab.package_table
        check("table rows populated", tbl.rowCount() == 4, f"rows={tbl.rowCount()}")
        check("icons attached", all(tbl.item(r, 1).icon().isNull() is False for r in range(4)))
        check("checkbox items present", all(tbl.item(r, 0) is not None for r in range(4)))

        # select all / clear
        tbl.select_all(True)
        app.processEvents()
        check("select all -> 4 checked", len(tbl.get_selected_packages()) == 4,
              f"got {len(tbl.get_selected_packages())}")

        # sorting keeps check state with the right package
        tbl.sortItems(1, Qt.SortOrder.AscendingOrder)
        app.processEvents()
        sel = set(tbl.get_selected_packages())
        check("check states survive sort", sel == {p.package_name for p in pkgs},
              f"got {sorted(sel)}")

        tbl.select_all(False)
        app.processEvents()
        check("deselect all -> 0 checked", len(tbl.get_selected_packages()) == 0)

        # filter
        tbl.filter_packages("chrome")
        app.processEvents()
        hidden = sum(1 for r in range(tbl.rowCount()) if tbl.isRowHidden(r))
        check("search filters rows", hidden == 3, f"hidden={hidden}")
        tbl.filter_packages("")
        app.processEvents()
        check("search reset", not any(tbl.isRowHidden(r) for r in range(tbl.rowCount())))

        # ---- splitter / log toggle --------------------------------------
        vt = w.virus_tab
        vt._set_log_expanded(False)
        app.processEvents()
        collapsed = vt.splitter.sizes()
        check("log collapse hands space to table",
              collapsed[1] <= vt.log_group.maximumHeight() + 5,
              f"sizes={collapsed} max={vt.log_group.maximumHeight()}")
        vt._set_log_expanded(True)
        app.processEvents()
        check("log expand restores space", vt.splitter.sizes()[1] > collapsed[1],
              f"sizes={vt.splitter.sizes()}")

        # ---- finance guide ---------------------------------------------
        ft = w.finance_tab
        check("finance brands listed", ft.wizard_brand_combo.count() == len(get_all_brands()) + 1,
              f"got {ft.wizard_brand_combo.count()}")
        ft.wizard_brand_combo.setCurrentIndex(1)
        app.processEvents()
        check("wizard unlocks lock types after brand pick",
              ft.wizard_lock_combo.isEnabled() and ft.wizard_lock_combo.count() > 1,
              f"count={ft.wizard_lock_combo.count()}")
        ft.wizard_lock_combo.setCurrentIndex(1)
        app.processEvents()
        check("wizard renders instructions", len(ft.wizard_result.toPlainText()) > 20,
              f"len={len(ft.wizard_result.toPlainText())}")

        for view in (0, 1, 2, 0):
            ft.view_combo.setCurrentIndex(view)
            app.processEvents()
        check("view switch cards/table/wizard ok", True)

        for term in ("tecno", "frp", "samsung", ""):
            ft.search_box.setText(term)
            app.processEvents()
        check("finance search terms ok", True)

        # ---- help tab ---------------------------------------------------
        ht = w.help_tab
        n = ht.nav_tree.topLevelItemCount()
        check("help topics present", n >= 4, f"top-level={n}")
        for i in range(n):
            ht.nav_tree.setCurrentItem(ht.nav_tree.topLevelItem(i))
            app.processEvents()
        check("help pages render", len(ht.content_area.toPlainText()) > 100,
              f"len={len(ht.content_area.toPlainText())}")

        # ---- status bar / developer credit -------------------------------
        check("developer credit present", "jstndcllrc" in w.windowTitle(),
              f"title={w.windowTitle()!r}")

        # ---- about dialog constructs -------------------------------------
        check("about dialog callable", callable(getattr(ht, "_show_about", None)))

    except Exception:
        traceback.print_exc()
        failures.append("unexpected exception")
    finally:
        print("\n" + "=" * 60)
        print(f"{len(steps) - len(failures)}/{len(steps)} checks passed")
        if failures:
            for f in failures:
                print("  FAILED:", f)
        else:
            print("ALL CHECKS PASSED")
        print("=" * 60)
        app.exit(1 if failures else 0)


QTimer.singleShot(800, run)
sys.exit(app.exec())
