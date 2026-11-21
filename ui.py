"""Qt window for Data Sorter."""
from __future__ import annotations

import numbers
from pathlib import Path

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QPushButton, QTableView, QToolButton,
    QVBoxLayout, QWidget,
)

import sorter
from sorter import SortRule

PREVIEW_ROWS = 1000
OPEN_FILTER = "Spreadsheets (*.xlsx *.xlsm *.xls *.csv *.tsv *.txt);;All files (*)"


class PandasModel(QAbstractTableModel):
    """Read-only preview of the first PREVIEW_ROWS rows."""

    def __init__(self) -> None:
        super().__init__()
        self._df = pd.DataFrame()

    def set_frame(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        self._df = df.head(PREVIEW_ROWS)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        value = self._df.iat[index.row(), index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            return sorter.format_cell(value)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            if isinstance(value, numbers.Real) and not isinstance(value, bool):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return str(self._df.columns[section])
        return str(section + 1)


class RuleRow(QWidget):
    move_up = Signal(object)
    move_down = Signal(object)
    remove = Signal(object)

    def __init__(self, columns: list[str], detector) -> None:
        super().__init__()
        self._detector = detector

        self.label = QLabel("Sort by")
        self.label.setMinimumWidth(55)
        self.column_combo = QComboBox()
        self.column_combo.addItems(columns)
        self.column_combo.setMinimumWidth(240)
        self.column_combo.setSizePolicy(self.column_combo.sizePolicy().horizontalPolicy().Expanding,
                                        self.column_combo.sizePolicy().verticalPolicy())
        self.order_combo = QComboBox()
        self.order_combo.addItems(["Ascending", "Descending"])
        self.date_check = QCheckBox("Date")
        self.date_check.setToolTip("Sort this column by real dates instead of text")
        self.dayfirst_check = QCheckBox("Day first")
        self.dayfirst_check.setToolTip("Read 03/04/2024 as 3 April (tick) or March 4 (untick)")
        self.up_btn = QToolButton(); self.up_btn.setText("▲")
        self.down_btn = QToolButton(); self.down_btn.setText("▼")
        self.del_btn = QToolButton(); self.del_btn.setText("✕")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        for w in (self.label, self.column_combo, self.order_combo, self.date_check,
                  self.dayfirst_check, self.up_btn, self.down_btn, self.del_btn):
            layout.addWidget(w)
        layout.setStretchFactor(self.column_combo, 1)

        self.column_combo.currentIndexChanged.connect(self._column_changed)
        self.date_check.toggled.connect(self.dayfirst_check.setEnabled)
        self.up_btn.clicked.connect(lambda: self.move_up.emit(self))
        self.down_btn.clicked.connect(lambda: self.move_down.emit(self))
        self.del_btn.clicked.connect(lambda: self.remove.emit(self))
        self._column_changed()

    def _column_changed(self) -> None:
        is_date, dayfirst = self._detector(self.column_combo.currentIndex())
        self.date_check.setChecked(is_date)
        self.dayfirst_check.setChecked(dayfirst)
        self.dayfirst_check.setEnabled(is_date)

    def set_position(self, index: int, total: int) -> None:
        self.label.setText("Sort by" if index == 0 else "Then by")
        self.up_btn.setEnabled(index > 0)
        self.down_btn.setEnabled(index < total - 1)

    def column_index(self) -> int:
        return self.column_combo.currentIndex()

    def ascending(self) -> bool:
        return self.order_combo.currentIndex() == 0


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Data Sorter")
        self.resize(1050, 720)
        self.setAcceptDrops(True)

        self.df: pd.DataFrame | None = None
        self.sorted_df: pd.DataFrame | None = None
        self.path: str | None = None
        self.sheet_name = "Sorted"
        self.delimiter = ","
        self.rows: list[RuleRow] = []
        self._detect_cache: dict[int, tuple[bool, bool]] = {}

        # --- top bar
        self.open_btn = QPushButton("Open File…")
        self.open_btn.clicked.connect(self.open_dialog)
        self.file_label = QLabel("No file loaded. Click Open File or drag a file into this window.")
        self.sheet_label = QLabel("Sheet:")
        self.sheet_combo = QComboBox()
        self.sheet_label.hide(); self.sheet_combo.hide()
        self.sheet_combo.currentTextChanged.connect(self._sheet_changed)
        top = QHBoxLayout()
        top.addWidget(self.open_btn)
        top.addWidget(self.file_label, 1)
        top.addWidget(self.sheet_label)
        top.addWidget(self.sheet_combo)

        # --- rules
        self.rules_layout = QVBoxLayout()
        self.add_btn = QPushButton("+ Add Sort Rule")
        self.add_btn.clicked.connect(self.add_rule)
        box = QGroupBox("Sort rules (top rule is the main sort, the next ones break ties)")
        box_layout = QVBoxLayout(box)
        box_layout.addLayout(self.rules_layout)
        row = QHBoxLayout(); row.addWidget(self.add_btn); row.addStretch(1)
        box_layout.addLayout(row)

        # --- actions
        self.sort_btn = QPushButton("Sort")
        self.reset_btn = QPushButton("Show Original")
        self.save_btn = QPushButton("Save As…")
        self.sort_btn.clicked.connect(self.do_sort)
        self.reset_btn.clicked.connect(self.do_reset)
        self.save_btn.clicked.connect(self.do_save)
        actions = QHBoxLayout()
        actions.addWidget(self.sort_btn); actions.addWidget(self.reset_btn)
        actions.addStretch(1); actions.addWidget(self.save_btn)

        # --- preview
        self.info_label = QLabel("")
        self.model = PandasModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)

        central = QWidget()
        main = QVBoxLayout(central)
        main.addLayout(top)
        main.addWidget(box)
        main.addLayout(actions)
        main.addWidget(self.info_label)
        main.addWidget(self.table, 1)
        self.setCentralWidget(central)

        self._set_controls_enabled(False)

    # ------------------------------------------------------------------ loading
    def _set_controls_enabled(self, on: bool) -> None:
        for w in (self.add_btn, self.sort_btn, self.reset_btn, self.save_btn):
            w.setEnabled(on)

    def open_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "", OPEN_FILTER)
        if path:
            self.load_path(path)

    def load_path(self, path: str) -> None:
        ext = Path(path).suffix.lower()
        if ext not in sorter.EXCEL_EXTS | sorter.CSV_EXTS:
            QMessageBox.warning(self, "Unsupported file", "Please choose an Excel (.xlsx/.xls) or CSV file.")
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            if sorter.is_excel(path):
                names = sorter.excel_sheet_names(path)
                self.path = path
                self.sheet_combo.blockSignals(True)
                self.sheet_combo.clear()
                self.sheet_combo.addItems(names)
                self.sheet_combo.blockSignals(False)
                multi = len(names) > 1
                self.sheet_label.setVisible(multi); self.sheet_combo.setVisible(multi)
                df = sorter.load_excel(path, names[0])
                self.sheet_name = names[0]
            else:
                df, self.delimiter = sorter.load_csv(path)
                self.path = path
                self.sheet_label.hide(); self.sheet_combo.hide()
        except Exception as exc:  # noqa: BLE001
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Could not open file", str(exc))
            return
        QApplication.restoreOverrideCursor()
        self.file_label.setText(path)
        self._set_data(df)

    def _sheet_changed(self, name: str) -> None:
        if not self.path or not name or not sorter.is_excel(self.path):
            return
        try:
            df = sorter.load_excel(self.path, name)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Could not read sheet", str(exc))
            return
        self.sheet_name = name
        self._set_data(df)

    def _set_data(self, df: pd.DataFrame) -> None:
        self.df = df
        self.sorted_df = None
        self._detect_cache.clear()
        for r in list(self.rows):
            self._drop_row(r)
        self._set_controls_enabled(True)
        self._refresh_preview("Original order")
        if len(df.columns):
            self.add_rule()

    def _refresh_preview(self, note: str) -> None:
        shown = self.sorted_df if self.sorted_df is not None else self.df
        self.model.set_frame(shown)
        total = len(shown)
        extra = f" (showing first {PREVIEW_ROWS:,})" if total > PREVIEW_ROWS else ""
        self.info_label.setText(f"{note} - {total:,} rows, {len(shown.columns)} columns{extra}")

    # --------------------------------------------------------------- rule rows
    def detect_column(self, idx: int) -> tuple[bool, bool]:
        if self.df is None or idx < 0 or idx >= len(self.df.columns):
            return False, True
        if idx not in self._detect_cache:
            series = self.df.iloc[:, idx]
            is_date = sorter.looks_like_date(series)
            dayfirst = sorter.detect_dayfirst(series) if is_date else True
            self._detect_cache[idx] = (is_date, dayfirst)
        return self._detect_cache[idx]

    def add_rule(self) -> None:
        if self.df is None:
            return
        row = RuleRow([str(c) for c in self.df.columns], self.detect_column)
        row.move_up.connect(lambda r: self._move(r, -1))
        row.move_down.connect(lambda r: self._move(r, +1))
        row.remove.connect(self._remove)
        used = {r.column_index() for r in self.rows}
        free = [i for i in range(len(self.df.columns)) if i not in used]
        if free:
            row.column_combo.setCurrentIndex(free[0])
        self.rows.append(row)
        self._relayout()

    def _relayout(self) -> None:
        while self.rules_layout.count():
            self.rules_layout.takeAt(0)
        for i, row in enumerate(self.rows):
            self.rules_layout.addWidget(row)
            row.set_position(i, len(self.rows))

    def _move(self, row: RuleRow, delta: int) -> None:
        i = self.rows.index(row)
        j = i + delta
        if 0 <= j < len(self.rows):
            self.rows[i], self.rows[j] = self.rows[j], self.rows[i]
            self._relayout()

    def _drop_row(self, row: RuleRow) -> None:
        self.rows.remove(row)
        self.rules_layout.removeWidget(row)
        row.setParent(None)
        row.deleteLater()

    def _remove(self, row: RuleRow) -> None:
        self._drop_row(row)
        self._relayout()

    # ---------------------------------------------------------- sort / save
    def do_sort(self) -> None:
        if self.df is None:
            return
        if not self.rows:
            QMessageBox.information(self, "No sort rules", "Add at least one sort rule first.")
            return
        cols = [r.column_index() for r in self.rows]
        if len(set(cols)) != len(cols):
            QMessageBox.warning(self, "Duplicate column", "The same column is used in more than one rule. Remove the duplicate.")
            return
        rules = [
            SortRule(
                column=self.df.columns[r.column_index()],
                ascending=r.ascending(),
                as_date=r.date_check.isChecked(),
                dayfirst=r.dayfirst_check.isChecked(),
            )
            for r in self.rows
        ]
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.sorted_df = sorter.sort_dataframe(self.df, rules)
        except Exception as exc:  # noqa: BLE001
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Sort failed", str(exc))
            return
        QApplication.restoreOverrideCursor()
        desc = ", ".join(f"{r.column} {'↑' if r.ascending else '↓'}" for r in rules)
        self._refresh_preview(f"Sorted by {desc}")

    def do_reset(self) -> None:
        if self.df is not None:
            self.sorted_df = None
            self._refresh_preview("Original order")

    def do_save(self) -> None:
        if self.df is None:
            return
        if self.sorted_df is None:
            QMessageBox.information(self, "Nothing to save", "Click Sort first, then save the result.")
            return
        src = Path(self.path or "data.xlsx")
        default_ext = ".csv" if src.suffix.lower() in sorter.CSV_EXTS else ".xlsx"
        default = str(src.with_name(f"{src.stem}_sorted{default_ext}"))
        filters = "Excel Workbook (*.xlsx);;CSV (*.csv)"
        if default_ext == ".csv":
            filters = "CSV (*.csv);;Excel Workbook (*.xlsx)"
        path, selected = QFileDialog.getSaveFileName(self, "Save sorted file", default, filters)
        if not path:
            return
        if Path(path).suffix.lower() not in (".xlsx", ".csv"):
            path += ".xlsx" if "xlsx" in selected else ".csv"
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            sorter.save_dataframe(self.sorted_df, path, self.delimiter, self.sheet_name)
        except PermissionError:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Cannot save", "The file is open in another program (e.g. Excel). Close it and try again.")
            return
        except Exception as exc:  # noqa: BLE001
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        QApplication.restoreOverrideCursor()
        self.statusBar().showMessage(f"Saved {path}", 8000)

    # ------------------------------------------------------------ drag & drop
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if urls:
            self.load_path(urls[0].toLocalFile())
