from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QComboBox, QRadioButton, QButtonGroup, QListWidget,
    QListWidgetItem, QAbstractItemView, QTableWidget, QTableWidgetItem,
    QMessageBox, QHBoxLayout, QApplication
)
from PyQt5.QtCore import Qt
import pandas as pd
import os

from utils import load_excel


class Tool3UI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔍 Excel Comparator & Filter Tool")
        self.df1 = None
        self.df2 = None
        self.merged_df = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # File upload widgets
        self.file1_label = QLabel("No File 1 loaded")
        self.upload_file1_btn = QPushButton("Upload Excel File 1")
        self.upload_file1_btn.clicked.connect(self.load_file1)
        layout.addWidget(self.file1_label)
        layout.addWidget(self.upload_file1_btn)

        self.file2_label = QLabel("No File 2 loaded")
        self.upload_file2_btn = QPushButton("Upload Excel File 2")
        self.upload_file2_btn.clicked.connect(self.load_file2)
        layout.addWidget(self.file2_label)
        layout.addWidget(self.upload_file2_btn)

        # Sheet selection
        self.sheet1_selector = QComboBox()
        self.sheet1_selector.currentTextChanged.connect(self.load_sheet1)
        self.sheet1_selector.setEnabled(False)

        self.sheet2_selector = QComboBox()
        self.sheet2_selector.currentTextChanged.connect(self.load_sheet2)
        self.sheet2_selector.setEnabled(False)

        layout.addWidget(QLabel("Select Sheet from File 1"))
        layout.addWidget(self.sheet1_selector)
        layout.addWidget(QLabel("Select Sheet from File 2"))
        layout.addWidget(self.sheet2_selector)

        # Column selection
        hlayout1 = QHBoxLayout()
        hlayout1.addWidget(QLabel("Column from File 1"))
        self.col1_selector = QComboBox()
        hlayout1.addWidget(self.col1_selector)
        layout.addLayout(hlayout1)

        hlayout2 = QHBoxLayout()
        hlayout2.addWidget(QLabel("Column from File 2"))
        self.col2_selector = QComboBox()
        hlayout2.addWidget(self.col2_selector)
        layout.addLayout(hlayout2)

        # Match type
        self.match_type_group = QButtonGroup()
        self.exact_match_radio = QRadioButton("Exact Match")
        self.case_insensitive_radio = QRadioButton("Case-insensitive Match")
        self.match_type_group.addButton(self.exact_match_radio)
        self.match_type_group.addButton(self.case_insensitive_radio)
        self.exact_match_radio.setChecked(True)

        hlayout3 = QHBoxLayout()
        hlayout3.addWidget(self.exact_match_radio)
        hlayout3.addWidget(self.case_insensitive_radio)
        layout.addLayout(hlayout3)

        # Output column selection
        layout.addWidget(QLabel("Select Columns from File 1"))
        self.file1_columns_list = QListWidget()
        self.file1_columns_list.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.file1_columns_list)

        layout.addWidget(QLabel("Select Columns from File 2"))
        self.file2_columns_list = QListWidget()
        self.file2_columns_list.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.file2_columns_list)

        # Merge and Export buttons
        self.merge_btn = QPushButton("🔍 Compare and Merge")
        self.merge_btn.clicked.connect(self.compare_and_merge)
        self.merge_btn.setEnabled(False)
        layout.addWidget(self.merge_btn)

        layout.addWidget(QLabel("Merged Data Preview"))
        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.export_btn = QPushButton("📥 Export Merged Data to CSV")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_to_csv)
        layout.addWidget(self.export_btn)

        self.setLayout(layout)

    def load_file1(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File 1", "", "Excel Files (*.xlsx)")
        if not file_path:
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.excel1 = load_excel(file_path)
            self.sheet1_selector.clear()
            self.sheet1_selector.addItems(self.excel1.keys())
            self.sheet1_selector.setEnabled(True)
            self.file1_label.setText(f"Loaded: {os.path.basename(file_path)}")
            self.load_sheet1(self.sheet1_selector.currentText())
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            QApplication.restoreOverrideCursor()

    def load_file2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File 2", "", "Excel Files (*.xlsx)")
        if not file_path:
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.excel2 = load_excel(file_path)
            self.sheet2_selector.clear()
            self.sheet2_selector.addItems(self.excel2.keys())
            self.sheet2_selector.setEnabled(True)
            self.file2_label.setText(f"Loaded: {os.path.basename(file_path)}")
            self.load_sheet2(self.sheet2_selector.currentText())
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            QApplication.restoreOverrideCursor()

    def load_sheet1(self, sheet_name):
        if hasattr(self, "excel1") and sheet_name in self.excel1:
            self.df1 = self.excel1[sheet_name]
            self.col1_selector.clear()
            self.col1_selector.addItems(self.df1.columns)

            self.file1_columns_list.clear()
            for col in self.df1.columns:
                item = QListWidgetItem(f"F1_{col}")
                item.setSelected(True)
                self.file1_columns_list.addItem(item)

            self.check_ready_to_merge()

    def load_sheet2(self, sheet_name):
        if hasattr(self, "excel2") and sheet_name in self.excel2:
            self.df2 = self.excel2[sheet_name]
            self.col2_selector.clear()
            self.col2_selector.addItems(self.df2.columns)

            self.file2_columns_list.clear()
            for col in self.df2.columns:
                item = QListWidgetItem(f"F2_{col}")
                item.setSelected(True)
                self.file2_columns_list.addItem(item)

            self.check_ready_to_merge()

    def check_ready_to_merge(self):
        ready = all([
            self.df1 is not None,
            self.df2 is not None,
            self.col1_selector.currentText() != "",
            self.col2_selector.currentText() != ""
        ])
        self.merge_btn.setEnabled(ready)

    def compare_and_merge(self):
        col1 = self.col1_selector.currentText()
        col2 = self.col2_selector.currentText()
        match_type = "case_insensitive" if self.case_insensitive_radio.isChecked() else "exact"

        # Prepare merge key
        df1 = self.df1.copy()
        df2 = self.df2.copy()
        df1["__merge_key__"] = df1[col1].astype(str).str.lower() if match_type == "case_insensitive" else df1[col1].astype(str)
        df2["__merge_key__"] = df2[col2].astype(str).str.lower() if match_type == "case_insensitive" else df2[col2].astype(str)

        df1_prefixed = df1.add_prefix("F1_")
        df2_prefixed = df2.add_prefix("F2_")

        # Ensure merge key remains after prefixing
        df1_prefixed["__merge_key__"] = df1["__merge_key__"]
        df2_prefixed["__merge_key__"] = df2["__merge_key__"]

        try:
            merged = pd.merge(df1_prefixed, df2_prefixed, on="__merge_key__", how="inner")
        except Exception as e:
            QMessageBox.critical(self, "Merge Error", str(e))
            return

        selected_f1_cols = [item.text() for item in self.file1_columns_list.selectedItems()]
        selected_f2_cols = [item.text() for item in self.file2_columns_list.selectedItems()]
        final_cols = selected_f1_cols + selected_f2_cols

        # Filter out invalid/missing columns
        final_cols = [col for col in final_cols if col in merged.columns]

        if not final_cols:
            QMessageBox.warning(self, "No Columns", "No selected columns available in merged data.")
            self.export_btn.setEnabled(False)
            self.preview_table(pd.DataFrame())
            return

        self.merged_df = merged[final_cols]
        self.preview_table(self.merged_df)
        self.export_btn.setEnabled(True)
        QMessageBox.information(self, "Success", f"Found {len(self.merged_df)} matching rows.")

    def preview_table(self, df):
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        if df.empty:
            return

        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)

        for i in range(len(df)):
            for j, col in enumerate(df.columns):
                self.table.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))

        self.table.resizeColumnsToContents()

    def export_to_csv(self):
        if self.merged_df is None or self.merged_df.empty:
            QMessageBox.warning(self, "No Data", "No data to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "merged_output.csv", "CSV Files (*.csv)")
        if file_path:
            try:
                self.merged_df.to_csv(file_path, index=False)
                QMessageBox.information(self, "Exported", f"CSV successfully saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e))
