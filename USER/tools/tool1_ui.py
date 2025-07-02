from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QComboBox, QLineEdit, QListWidget, QListWidgetItem, QAbstractItemView,
    QTableWidget, QTableWidgetItem, QMessageBox, QHBoxLayout, QApplication
)
from PyQt5.QtCore import Qt
import pandas as pd
import os

from utils import load_excel, load_csv


class Tool1UI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧮 CSV/Excel Filter Tool")
        self.df = None
        self.filtered_df = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.file_label = QLabel("No file loaded")
        layout.addWidget(self.file_label)

        self.upload_btn = QPushButton("Upload CSV or Excel File")
        self.upload_btn.clicked.connect(self.load_file)
        layout.addWidget(self.upload_btn)

        self.sheet_selector = QComboBox()
        self.sheet_selector.currentTextChanged.connect(self.load_sheet)
        layout.addWidget(self.sheet_selector)
        self.sheet_selector.hide()

        layout.addWidget(QLabel("Select Filter Column"))
        self.column_selector = QComboBox()
        layout.addWidget(self.column_selector)

        layout.addWidget(QLabel("Enter comma-separated filter values"))
        self.filter_input = QLineEdit()
        layout.addWidget(self.filter_input)

        hlayout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All Columns")
        self.select_all_btn.clicked.connect(self.select_all_columns)
        hlayout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Deselect All Columns")
        self.deselect_all_btn.clicked.connect(self.deselect_all_columns)
        hlayout.addWidget(self.deselect_all_btn)

        layout.addLayout(hlayout)

        layout.addWidget(QLabel("Select Columns to Display"))
        self.column_multiselect = QListWidget()
        self.column_multiselect.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.column_multiselect)

        self.filter_btn = QPushButton("Apply Filter")
        self.filter_btn.clicked.connect(self.apply_filter)
        self.filter_btn.setEnabled(False)
        layout.addWidget(self.filter_btn)

        self.clear_filter_btn = QPushButton("Clear Filter")
        self.clear_filter_btn.clicked.connect(self.clear_filter)
        self.clear_filter_btn.setEnabled(False)
        layout.addWidget(self.clear_filter_btn)

        self.save_btn = QPushButton("Save Filtered Data")
        self.save_btn.clicked.connect(self.save_filtered_data)
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)

        layout.addWidget(QLabel("📋 Filtered Data Preview"))
        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_file(self):
        """Open file dialog and load Excel or CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Excel (*.xlsx);;CSV (*.csv)")
        if not file_path:
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".xlsx":
                self.excel_data = load_excel(file_path)
                self.sheet_selector.clear()
                self.sheet_selector.addItems(self.excel_data.keys())
                self.sheet_selector.show()
                self.load_sheet(self.sheet_selector.currentText())
            elif ext == ".csv":
                self.df = load_csv(file_path)
                self.sheet_selector.hide()
                self.update_ui_after_load()
            else:
                QMessageBox.warning(self, "Unsupported", "Unsupported file type.")
                return
            self.file_label.setText(f"Loaded: {os.path.basename(file_path)}")
            self.filter_btn.setEnabled(True)
            self.save_btn.setEnabled(False)
            self.clear_filter_btn.setEnabled(False)
            self.filter_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            QApplication.restoreOverrideCursor()

    def load_sheet(self, sheet_name):
        """Load selected sheet from Excel dict and update UI."""
        if hasattr(self, 'excel_data') and sheet_name in self.excel_data:
            self.df = self.excel_data[sheet_name]
            self.update_ui_after_load()

    def update_ui_after_load(self):
        """Update UI widgets with DataFrame columns after file load or sheet change."""
        self.column_selector.clear()
        self.column_multiselect.clear()

        if self.df is not None:
            self.column_selector.addItems(self.df.columns)
            for col in self.df.columns:
                item = QListWidgetItem(col)
                item.setSelected(True)
                self.column_multiselect.addItem(item)
            self.preview_table(self.df.head())

    def select_all_columns(self):
        """Select all columns in the multiselect."""
        for i in range(self.column_multiselect.count()):
            self.column_multiselect.item(i).setSelected(True)

    def deselect_all_columns(self):
        """Deselect all columns in the multiselect."""
        for i in range(self.column_multiselect.count()):
            self.column_multiselect.item(i).setSelected(False)

    def apply_filter(self):
        """Apply filter to the DataFrame and show filtered results."""
        if self.df is None:
            QMessageBox.warning(self, "No Data", "Please upload a file first.")
            return
        filter_col = self.column_selector.currentText()
        filter_values = [v.strip() for v in self.filter_input.text().split(',') if v.strip()]
        selected_cols = [item.text() for item in self.column_multiselect.selectedItems()]
        if not filter_values:
            QMessageBox.warning(self, "Missing", "Enter at least one filter value.")
            return
        if not selected_cols:
            QMessageBox.warning(self, "Missing", "Please select at least one column to display.")
            return
        try:
            filtered_df = self.df[self.df[filter_col].astype(str).isin(filter_values)]
            self.filtered_df = filtered_df[selected_cols]

            # Show max 100 rows to keep UI responsive
            max_rows = 100
            if len(self.filtered_df) > max_rows:
                display_df = self.filtered_df.head(max_rows)
                QMessageBox.information(self, "Info", f"Showing first {max_rows} rows of {len(self.filtered_df)} total.")
            else:
                display_df = self.filtered_df

            self.preview_table(display_df)
            QMessageBox.information(self, "Success", f"Found {len(self.filtered_df)} matching row(s).")
            self.save_btn.setEnabled(True)
            self.clear_filter_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Filter failed: {e}")

    def clear_filter(self):
        """Clear filter input and reset preview table."""
        self.filter_input.clear()
        if self.df is not None:
            self.preview_table(self.df.head())
        self.save_btn.setEnabled(False)
        self.clear_filter_btn.setEnabled(False)

    def preview_table(self, df):
        """Populate the QTableWidget with the DataFrame content."""
        self.table.setColumnCount(len(df.columns))
        self.table.setRowCount(len(df))

        self.table.setHorizontalHeaderLabels(df.columns)

        for i in range(len(df)):
            for j, col in enumerate(df.columns):
                self.table.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))

        self.table.resizeColumnsToContents()

    def save_filtered_data(self):
        """Open save dialog and save filtered DataFrame as CSV or Excel."""
        if self.filtered_df is None or self.filtered_df.empty:
            QMessageBox.warning(self, "No Data", "No filtered data to save.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Filtered Data", "", "CSV Files (*.csv);;Excel Files (*.xlsx)")
        if not file_path:
            return
        try:
            if file_path.endswith(".csv"):
                self.filtered_df.to_csv(file_path, index=False)
            elif file_path.endswith(".xlsx"):
                self.filtered_df.to_excel(file_path, index=False)
            else:
                QMessageBox.warning(self, "Invalid Format", "Please save as .csv or .xlsx")
                return
            QMessageBox.information(self, "Saved", f"Filtered data saved to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")
