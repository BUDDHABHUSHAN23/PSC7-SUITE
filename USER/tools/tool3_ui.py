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
        self.final_output = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # File 1 upload
        self.file1_label = QLabel("No File 1 loaded")
        self.upload_file1_btn = QPushButton("Upload Excel File 1")
        self.upload_file1_btn.clicked.connect(self.load_file1)
        layout.addWidget(self.file1_label)
        layout.addWidget(self.upload_file1_btn)

        # File 2 upload
        self.file2_label = QLabel("No File 2 loaded")
        self.upload_file2_btn = QPushButton("Upload Excel File 2")
        self.upload_file2_btn.clicked.connect(self.load_file2)
        layout.addWidget(self.file2_label)
        layout.addWidget(self.upload_file2_btn)

        # Sheet selectors
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

        # Column selectors for matching
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

        # Matching type radio buttons
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

        # Columns selection for final output - file1 and file2 columns separately
        layout.addWidget(QLabel("Select Columns from File 1"))
        self.file1_columns_list = QListWidget()
        self.file1_columns_list.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.file1_columns_list)

        layout.addWidget(QLabel("Select Columns from File 2"))
        self.file2_columns_list = QListWidget()
        self.file2_columns_list.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.file2_columns_list)

        # Button to perform merge/filter
        self.merge_btn = QPushButton("🔍 Compare and Merge")
        self.merge_btn.clicked.connect(self.compare_and_merge)
        self.merge_btn.setEnabled(False)
        layout.addWidget(self.merge_btn)

        # Table preview
        layout.addWidget(QLabel("Merged Data Preview"))
        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_file1(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File 1", "", "Excel (*.xlsx)")
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
            self.check_ready_to_merge()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            QApplication.restoreOverrideCursor()

    def load_file2(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File 2", "", "Excel (*.xlsx)")
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
            self.check_ready_to_merge()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            QApplication.restoreOverrideCursor()

    def load_sheet1(self, sheet_name):
        if hasattr(self, 'excel1') and sheet_name in self.excel1:
            self.df1 = self.excel1[sheet_name]
            self.col1_selector.clear()
            self.col1_selector.addItems(self.df1.columns)

            # Populate file1 columns selection list with prefix
            self.file1_columns_list.clear()
            for col in self.df1.columns:
                item = QListWidgetItem(f"F1_{col}")
                item.setSelected(True)
                self.file1_columns_list.addItem(item)
            self.check_ready_to_merge()

    def load_sheet2(self, sheet_name):
        if hasattr(self, 'excel2') and sheet_name in self.excel2:
            self.df2 = self.excel2[sheet_name]
            self.col2_selector.clear()
            self.col2_selector.addItems(self.df2.columns)

            # Populate file2 columns selection list with prefix
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
            self.col2_selector.currentText() != "",
            self.file1_columns_list.selectedItems(),
            self.file2_columns_list.selectedItems()
        ])
        self.merge_btn.setEnabled(ready)

    def compare_and_merge(self):
        if self.df1 is None or self.df2 is None:
            QMessageBox.warning(self, "Missing Data", "Please load both files and sheets.")
            return

        col1 = self.col1_selector.currentText()
        col2 = self.col2_selector.currentText()
        match_type = "exact" if self.exact_match_radio.isChecked() else "case_insensitive"

        # Prepare merge key columns
        if match_type == "case_insensitive":
            self.df1["__merge_key__"] = self.df1[col1].astype(str).str.lower()
            self.df2["__merge_key__"] = self.df2[col2].astype(str).str.lower()
        else:
            self.df1["__merge_key__"] = self.df1[col1].astype(str)
            self.df2["__merge_key__"] = self.df2[col2].astype(str)

        # Add prefix to avoid column name conflicts
        df1_prefixed = self.df1.add_prefix("F1_")
        df2_prefixed = self.df2.add_prefix("F2_")

        df1_prefixed["__merge_key__"] = self.df1["__merge_key__"]
        df2_prefixed["__merge_key__"] = self.df2["__merge_key__"]

        # Merge inner join on merge key
        try:
            merged = pd.merge(df1_prefixed, df2_prefixed, on="__merge_key__", how="inner")
        except Exception as e:
            QMessageBox.critical(self, "Merge Error", str(e))
            return

        # Get selected output columns without prefix
        selected_f1_cols = [item.text() for item in self.file1_columns_list.selectedItems()]
        selected_f2_cols = [item.text() for item in self.file2_columns_list.selectedItems()]

        final_cols = selected_f1_cols + selected_f2_cols

        # Check if final_cols exist in merged dataframe
        missing_cols = [col for col in final_cols if col not in merged.columns]
        if missing_cols:
            QMessageBox.warning(self, "Missing Columns", f"Columns missing in merged data: {missing_cols}")
            return

        self.merged_df = merged[final_cols]
        self.preview_table(self.merged_df)
        QMessageBox.information(self, "Success", f"Found {len(self.merged_df)} matching rows.")

    def preview_table(self, df):
        self.table.setColumnCount(len(df.columns))
        self.table.setRowCount(len(df))

        self.table.setHorizontalHeaderLabels(df.columns)

        for i in range(len(df)):
            for j, col in enumerate(df.columns):
                self.table.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))

        self.table.resizeColumnsToContents()
