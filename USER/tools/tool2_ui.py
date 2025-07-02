from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QComboBox, QRadioButton, QButtonGroup, QTextEdit, QListWidget,
    QListWidgetItem, QAbstractItemView, QTableWidget, QTableWidgetItem,
    QMessageBox, QHBoxLayout, QApplication
)
from PyQt5.QtCore import Qt
import pandas as pd
import os

from utils import load_excel


class Tool2UI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📊 Dual Excel Filter Tool")
        self.df1 = None
        self.df2 = None
        self.filtered_df = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # File upload buttons and labels
        self.file1_label = QLabel("No File 1 loaded")
        self.upload_file1_btn = QPushButton("Upload Excel File 1")
        self.upload_file1_btn.clicked.connect(self.load_file1)

        self.file2_label = QLabel("No File 2 loaded")
        self.upload_file2_btn = QPushButton("Upload Excel File 2")
        self.upload_file2_btn.clicked.connect(self.load_file2)

        layout.addWidget(self.file1_label)
        layout.addWidget(self.upload_file1_btn)
        layout.addWidget(self.file2_label)
        layout.addWidget(self.upload_file2_btn)

        # Sheet selectors for both files
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

        # Step 1 filter UI
        layout.addWidget(QLabel("🔗 Step 1: Filter Sheet2 using values from Sheet1"))

        hlayout1 = QHBoxLayout()
        hlayout1.addWidget(QLabel("Column from Sheet1"))
        self.col_sheet1_selector = QComboBox()
        hlayout1.addWidget(self.col_sheet1_selector)
        layout.addLayout(hlayout1)

        hlayout2 = QHBoxLayout()
        hlayout2.addWidget(QLabel("Column from Sheet2"))
        self.col_sheet2_selector = QComboBox()
        hlayout2.addWidget(self.col_sheet2_selector)
        layout.addLayout(hlayout2)

        # First filter mode radio buttons
        self.first_filter_group = QButtonGroup()
        self.starts_with_radio = QRadioButton("Starts With")
        self.contains_radio = QRadioButton("Contains")
        self.first_filter_group.addButton(self.starts_with_radio)
        self.first_filter_group.addButton(self.contains_radio)
        self.starts_with_radio.setChecked(True)

        hlayout3 = QHBoxLayout()
        hlayout3.addWidget(self.starts_with_radio)
        hlayout3.addWidget(self.contains_radio)
        layout.addLayout(hlayout3)

        # Step 2 filter UI
        layout.addWidget(QLabel("🧪 Step 2: Additional Filter"))

        hlayout4 = QHBoxLayout()
        hlayout4.addWidget(QLabel("Column to Filter (Sheet2)"))
        self.add_filter_col_selector = QComboBox()
        hlayout4.addWidget(self.add_filter_col_selector)
        layout.addLayout(hlayout4)

        self.second_filter_group = QButtonGroup()
        self.contains_filter_radio = QRadioButton("Contains Filter")
        self.exact_match_radio = QRadioButton("Exact Match")
        self.second_filter_group.addButton(self.contains_filter_radio)
        self.second_filter_group.addButton(self.exact_match_radio)
        self.contains_filter_radio.setChecked(True)

        hlayout5 = QHBoxLayout()
        hlayout5.addWidget(self.contains_filter_radio)
        hlayout5.addWidget(self.exact_match_radio)
        layout.addLayout(hlayout5)

        layout.addWidget(QLabel("Enter values (comma separated)"))
        self.filter_values_text = QTextEdit()
        self.filter_values_text.setFixedHeight(50)
        layout.addWidget(self.filter_values_text)

        # Step 3 output columns
        layout.addWidget(QLabel("📤 Step 3: Select Output Columns (Sheet2)"))
        self.output_columns_list = QListWidget()
        self.output_columns_list.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.output_columns_list)

        # Apply Filter Button
        self.apply_filter_btn = QPushButton("✅ Apply All Filters")
        self.apply_filter_btn.clicked.connect(self.apply_filters)
        self.apply_filter_btn.setEnabled(False)
        layout.addWidget(self.apply_filter_btn)

        # Table preview
        layout.addWidget(QLabel("🔎 Filtered Result Preview"))
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
            self.enable_apply_if_ready()
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
            self.enable_apply_if_ready()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            QApplication.restoreOverrideCursor()

    def load_sheet1(self, sheet_name):
        if hasattr(self, 'excel1') and sheet_name in self.excel1:
            self.df1 = self.excel1[sheet_name]
            self.col_sheet1_selector.clear()
            self.col_sheet1_selector.addItems(self.df1.columns)
            self.enable_apply_if_ready()

    def load_sheet2(self, sheet_name):
        if hasattr(self, 'excel2') and sheet_name in self.excel2:
            self.df2 = self.excel2[sheet_name]
            self.col_sheet2_selector.clear()
            self.col_sheet2_selector.addItems(self.df2.columns)
            self.add_filter_col_selector.clear()
            self.add_filter_col_selector.addItems(self.df2.columns)
            self.output_columns_list.clear()
            for col in self.df2.columns:
                item = QListWidgetItem(col)
                item.setSelected(True)
                self.output_columns_list.addItem(item)
            self.enable_apply_if_ready()

    def enable_apply_if_ready(self):
        ready = all([
            self.df1 is not None,
            self.df2 is not None,
            self.col_sheet1_selector.currentText() != "",
            self.col_sheet2_selector.currentText() != "",
            self.add_filter_col_selector.currentText() != "",
            self.output_columns_list.selectedItems()
        ])
        self.apply_filter_btn.setEnabled(ready)

    def apply_filters(self):
        if self.df1 is None or self.df2 is None:
            QMessageBox.warning(self, "Missing Data", "Please load both Excel files and sheets first.")
            return

        col1 = self.col_sheet1_selector.currentText()
        col2 = self.col_sheet2_selector.currentText()

        first_filter_mode = "starts_with" if self.starts_with_radio.isChecked() else "contains"

        # Get unique filter values from df1[col1]
        values_to_match = self.df1[col1].dropna().astype(str).unique()

        # Step 1 filter
        if first_filter_mode == "starts_with":
            df2_step1 = self.df2[self.df2[col2].astype(str).apply(lambda x: any(x.startswith(v) for v in values_to_match))]
        else:
            df2_step1 = self.df2[self.df2[col2].astype(str).apply(lambda x: any(v in x for v in values_to_match))]

        # Step 2 filter
        add_filter_col = self.add_filter_col_selector.currentText()
        filter_mode = "contains" if self.contains_filter_radio.isChecked() else "exact"
        user_input = self.filter_values_text.toPlainText()
        filter_values = [v.strip() for v in user_input.split(",") if v.strip()]

        df2_filtered = df2_step1.copy()
        if filter_values:
            if filter_mode == "contains":
                df2_filtered = df2_filtered[df2_filtered[add_filter_col].astype(str).apply(lambda x: any(val in x for val in filter_values))]
            else:
                df2_filtered = df2_filtered[df2_filtered[add_filter_col].astype(str).isin(filter_values)]

        selected_output_cols = [item.text() for item in self.output_columns_list.selectedItems()]
        if not selected_output_cols:
            QMessageBox.warning(self, "No Columns", "Please select at least one output column.")
            return

        self.filtered_df = df2_filtered[selected_output_cols]
        self.preview_table(self.filtered_df)
        QMessageBox.information(self, "Filter Result", f"Final Rows: {len(self.filtered_df)}")

    def preview_table(self, df):
        self.table.setColumnCount(len(df.columns))
        self.table.setRowCount(len(df))

        self.table.setHorizontalHeaderLabels(df.columns)

        for i in range(len(df)):
            for j, col in enumerate(df.columns):
                self.table.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))

        self.table.resizeColumnsToContents()
