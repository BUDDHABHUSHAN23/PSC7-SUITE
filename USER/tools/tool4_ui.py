from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QComboBox, QListWidget, QListWidgetItem, QAbstractItemView,
    QTableWidget, QTableWidgetItem, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt
import pandas as pd
import os

from utils import load_excel


class Tool4UI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔍 Excel Files Partial Match Comparator")
        self.df1 = None
        self.df2 = None
        self.matched_df = None
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

        # Column selectors for partial matching
        layout.addWidget(QLabel("Select Column from File 1"))
        self.col1_selector = QComboBox()
        layout.addWidget(self.col1_selector)

        layout.addWidget(QLabel("Select Column from File 2"))
        self.col2_selector = QComboBox()
        layout.addWidget(self.col2_selector)

        # Columns multiselect for output
        layout.addWidget(QLabel("Select Columns to Display in Output"))
        self.output_columns_list = QListWidget()
        self.output_columns_list.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.output_columns_list)

        # Button to run partial match
        self.match_btn = QPushButton("🔍 Find Partial Matches")
        self.match_btn.clicked.connect(self.find_partial_matches)
        self.match_btn.setEnabled(False)
        layout.addWidget(self.match_btn)

        # Table preview
        layout.addWidget(QLabel("Partial Matches Preview"))
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
            self.update_match_ready()
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
            self.update_match_ready()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            QApplication.restoreOverrideCursor()

    def load_sheet1(self, sheet_name):
        if hasattr(self, "excel1") and sheet_name in self.excel1:
            self.df1 = self.excel1[sheet_name]
            self.col1_selector.clear()
            self.col1_selector.addItems(self.df1.columns)
            self.update_output_columns()
            self.update_match_ready()

    def load_sheet2(self, sheet_name):
        if hasattr(self, "excel2") and sheet_name in self.excel2:
            self.df2 = self.excel2[sheet_name]
            self.col2_selector.clear()
            self.col2_selector.addItems(self.df2.columns)
            self.update_output_columns()
            self.update_match_ready()

    def update_output_columns(self):
        # Update output columns list from both dataframes (combined columns)
        self.output_columns_list.clear()
        if self.df1 is not None and self.df2 is not None:
            combined_cols = list(self.df1.columns) + list(self.df2.columns)
            for col in combined_cols:
                item = QListWidgetItem(col)
                item.setSelected(True)
                self.output_columns_list.addItem(item)

    def update_match_ready(self):
        ready = (
            self.df1 is not None
            and self.df2 is not None
            and self.col1_selector.currentText() != ""
            and self.col2_selector.currentText() != ""
        )
        self.match_btn.setEnabled(ready)

    def find_partial_matches(self):
        if self.df1 is None or self.df2 is None:
            QMessageBox.warning(self, "No Data", "Please load both files and sheets.")
            return

        col1 = self.col1_selector.currentText()
        col2 = self.col2_selector.currentText()

        matched_rows = []

        try:
            df1_cmp = self.df1[col1].astype(str).str.lower()
            df2_cmp = self.df2[col2].astype(str).str.lower()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to convert columns to string: {e}")
            return

        for idx1, val1 in df1_cmp.items():
            matches = self.df2[df2_cmp.str.contains(val1, na=False)]
            for idx2, match_row in matches.iterrows():
                combined = pd.concat([self.df1.loc[idx1], match_row], axis=0)
                matched_rows.append(combined)

        if matched_rows:
            result_df = pd.DataFrame(matched_rows)
            self.matched_df = result_df
            QMessageBox.information(self, "Success", f"Found {len(result_df)} matches.")
            self.show_preview(result_df)
        else:
            QMessageBox.warning(self, "No Matches", "No partial matches found.")
            self.matched_df = pd.DataFrame()
            self.show_preview(pd.DataFrame())

    def show_preview(self, df):
        if df.empty:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        selected_cols = [item.text() for item in self.output_columns_list.selectedItems()]
        if not selected_cols:
            selected_cols = df.columns.tolist()

        df = df[selected_cols]

        self.table.setColumnCount(len(df.columns))
        self.table.setRowCount(len(df))

        self.table.setHorizontalHeaderLabels(df.columns)

        for i in range(len(df)):
            for j, col in enumerate(df.columns):
                self.table.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))

        self.table.resizeColumnsToContents()
