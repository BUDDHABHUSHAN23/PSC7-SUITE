from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QComboBox, QRadioButton, QButtonGroup, QTextEdit, QListWidget,
    QListWidgetItem, QAbstractItemView, QTableWidget, QTableWidgetItem,
    QMessageBox, QHBoxLayout, QApplication
)
from PyQt5.QtCore import Qt
import pandas as pd
import os

from utils import load_excel  # Assumes it returns a dict of {sheet_name: dataframe}


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

        # Upload buttons
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

        # Step 1
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

        # Step 2
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

        # Step 3
        layout.addWidget(QLabel("📤 Step 3: Select Output Columns (Sheet2)"))
        self.output_columns_list = QListWidget()
        self.output_columns_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.output_columns_list.itemSelectionChanged.connect(self.enable_apply_if_ready)
        layout.addWidget(self.output_columns_list)

        # Apply Filter Button
        self.apply_filter_btn = QPushButton("✅ Apply All Filters")
        self.apply_filter_btn.clicked.connect(self.apply_filters)
        self.apply_filter_btn.setEnabled(False)
        layout.addWidget(self.apply_filter_btn)

        # Table to show results
        layout.addWidget(QLabel("🔎 Filtered Result Preview"))
        self.table = QTableWidget()
        layout.addWidget(self.table)

        
        # Export Button
        self.export_btn = QPushButton("📥 Export Filtered Data to CSV")
        self.export_btn.setEnabled(True)
        self.export_btn.clicked.connect(self.export_to_csv)
        layout.addWidget(self.export_btn)


        self.setLayout(layout)


    def load_file1(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Excel File 1", "", "Excel Files (*.xlsx)")
        if path:
            self.excel1 = load_excel(path)
            self.file1_label.setText(f"Loaded: {os.path.basename(path)}")
            self.sheet1_selector.clear()
            self.sheet1_selector.addItems(self.excel1.keys())
            self.sheet1_selector.setEnabled(True)
            self.load_sheet1(self.sheet1_selector.currentText())

    def load_file2(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Excel File 2", "", "Excel Files (*.xlsx)")
        if path:
            self.excel2 = load_excel(path)
            self.file2_label.setText(f"Loaded: {os.path.basename(path)}")
            self.sheet2_selector.clear()
            self.sheet2_selector.addItems(self.excel2.keys())
            self.sheet2_selector.setEnabled(True)
            self.load_sheet2(self.sheet2_selector.currentText())

    def load_sheet1(self, sheet):
        if hasattr(self, 'excel1') and sheet in self.excel1:
            self.df1 = self.excel1[sheet]
            self.col_sheet1_selector.clear()
            self.col_sheet1_selector.addItems(self.df1.columns)
            self.enable_apply_if_ready()

    def load_sheet2(self, sheet):
        if hasattr(self, 'excel2') and sheet in self.excel2:
            self.df2 = self.excel2[sheet]
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
        if all([
            self.df1 is not None,
            self.df2 is not None,
            self.col_sheet1_selector.currentText(),
            self.col_sheet2_selector.currentText(),
            self.add_filter_col_selector.currentText(),
            bool(self.output_columns_list.selectedItems())
        ]):
            self.apply_filter_btn.setEnabled(True)
        else:
            self.apply_filter_btn.setEnabled(False)

    def apply_filters(self):
        try:
            col1 = self.col_sheet1_selector.currentText()
            col2 = self.col_sheet2_selector.currentText()

            values_to_match = self.df1[col1].dropna().astype(str).unique()
            mode1 = "starts" if self.starts_with_radio.isChecked() else "contains"

            if mode1 == "starts":
                df2_step1 = self.df2[self.df2[col2].astype(str).apply(lambda x: any(x.startswith(v) for v in values_to_match))]
            else:
                df2_step1 = self.df2[self.df2[col2].astype(str).apply(lambda x: any(v in x for v in values_to_match))]

            filter_col = self.add_filter_col_selector.currentText()
            user_input = self.filter_values_text.toPlainText()
            filter_values = [v.strip() for v in user_input.split(",") if v.strip()]
            mode2 = "contains" if self.contains_filter_radio.isChecked() else "exact"

            df2_filtered = df2_step1.copy()
            if filter_values:
                if mode2 == "contains":
                    df2_filtered = df2_filtered[df2_filtered[filter_col].astype(str).apply(lambda x: any(val in x for val in filter_values))]
                else:
                    df2_filtered = df2_filtered[df2_filtered[filter_col].astype(str).isin(filter_values)]

            selected_columns = [item.text() for item in self.output_columns_list.selectedItems()]
            self.filtered_df = df2_filtered[selected_columns]
            self.preview_table(self.filtered_df)

            QMessageBox.information(self, "Filter Result", f"🎯 Final Rows: {len(self.filtered_df)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def preview_table(self, df):
        self.table.clear()
        self.table.setColumnCount(len(df.columns))
        self.table.setRowCount(len(df.index))
        self.table.setHorizontalHeaderLabels(df.columns.tolist())

        for row_idx in range(len(df)):
            for col_idx, col in enumerate(df.columns):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(df.iloc[row_idx, col_idx])))

        self.table.resizeColumnsToContents()


    def export_to_csv(self):
        if self.filtered_df is None or self.filtered_df.empty:
            QMessageBox.warning(self, "No Data", "No filtered data available to export.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "filtered_output.csv", "CSV Files (*.csv)")
        if path:
            try:
                self.filtered_df.to_csv(path, index=False, encoding='utf-8')
                QMessageBox.information(self, "Success", f"CSV exported successfully to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to save CSV: {str(e)}")

