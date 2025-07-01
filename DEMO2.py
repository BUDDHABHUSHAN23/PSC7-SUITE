import sys
import os
import json
import hashlib
import platform
import uuid
import shutil
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QStackedWidget, QFileDialog,
                             QMessageBox, QComboBox, QCheckBox, QTextEdit, QTableWidget,
                             QTableWidgetItem, QGroupBox, QRadioButton, QListWidget,
                             QFrame, QButtonGroup, QSpinBox, QTabWidget)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon, QFont
import pandas as pd
from pandas import DataFrame  

# =============================================
#  Important functions for resource management
# =============================================

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
# =============================================
# License Gate Module
# =============================================
class LicenseGate:
    @staticmethod
    def get_machine_id():
        components = [
            platform.node(),
            platform.system(),
            platform.release(),
            platform.machine(),
            str(uuid.getnode()),
            os.getenv("PROCESSOR_IDENTIFIER", ""),
        ]
        raw_id = "-".join(components)
        return hashlib.sha256(raw_id.encode()).hexdigest()

    @staticmethod
    def validate_license_file(license_data):
        try:
            machine_id = license_data.get("machine_id")
            valid_till = license_data.get("valid_till")
            features = license_data.get("features", [])

            if machine_id != LicenseGate.get_machine_id():
                return False, "License is not valid for this machine."

            if not valid_till:
                return False, "License missing expiry date."

            expiry_date = datetime.strptime(valid_till, "%Y-%m-%d")
            if expiry_date < datetime.now():
                return False, "License has expired."

            return True, {
                "features": features,
                "valid_till": expiry_date.strftime("%Y-%m-%d")
            }

        except Exception as e:
            return False, f"License validation error: {str(e)}"
        
# =============================================
# Base Tool Class
# =============================================
class BaseTool(QWidget):
    """Base class for all tools with common functionality"""
    def __init__(self, tool_name, description):
        super().__init__()
        self.tool_name = tool_name
        self.description = description
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.init_ui()

    def init_ui(self):
        """Initialize the tool UI"""
        self.setup_header()
        self.setup_tool_ui()

    def setup_header(self):
        """Setup the tool header section"""
        header = QLabel(self.tool_name)
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        self.layout.addWidget(header)
        
        desc = QLabel(self.description)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 15px;")
        self.layout.addWidget(desc)
        
        self.add_separator()

    def setup_tool_ui(self):
        """To be implemented by each tool"""
        pass

    def add_separator(self):
        """Add a horizontal line separator"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #ecf0f1;")
        self.layout.addWidget(line)

    def create_form_row(self, label, widget):
        """Create a form row with label and widget"""
        row = QHBoxLayout()
        label_widget = QLabel(label)
        label_widget.setFixedWidth(150)
        row.addWidget(label_widget)
        row.addWidget(widget)
        self.layout.addLayout(row)
        return row

    def create_button(self, text, callback=None, style="primary"):
        """Create a styled button"""
        btn = QPushButton(text)
        if callback:
            btn.clicked.connect(callback)
        
        if style == "primary":
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
        elif style == "success":
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2ecc71;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #27ae60;
                }
            """)
        return btn

    def create_table(self):
        """Create a styled table widget"""
        table = QTableWidget()
        table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #eee;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 5px;
                border: 1px solid #ddd;
            }
        """)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        return table

    def show_dataframe(self, table, df):
        """Display pandas DataFrame in QTableWidget"""
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                table.setItem(row, col, QTableWidgetItem(str(df.iloc[row, col])))
        
        table.resizeColumnsToContents()

# =============================================
# Tool 1: CSV/Excel Filter Tool
# =============================================
class CSVExcelFilterTool(BaseTool):
    def __init__(self):
        super().__init__("CSV/Excel Filter", "Filter data from CSV or Excel files")

    def setup_tool_ui(self):
        # File Upload Section
        upload_group = QGroupBox("File Upload")
        upload_layout = QVBoxLayout()
        
        self.upload_btn = self.create_button("Upload File", self.handle_upload)
        upload_layout.addWidget(self.upload_btn)
        
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        upload_layout.addWidget(self.file_label)
        
        self.sheet_combo = QComboBox()
        self.sheet_combo.hide()
        upload_layout.addWidget(self.sheet_combo)
        
        upload_group.setLayout(upload_layout)
        self.layout.addWidget(upload_group)

        # Filter Configuration
        config_group = QGroupBox("Filter Configuration")
        config_layout = QVBoxLayout()
        
        self.filter_col_combo = QComboBox()
        self.create_form_row("Filter Column:", self.filter_col_combo)
        
        self.filter_values = QLineEdit()
        self.filter_values.setPlaceholderText("Enter values separated by commas")
        self.create_form_row("Filter Values:", self.filter_values)
        
        self.display_cols = QListWidget()
        self.display_cols.setSelectionMode(QListWidget.MultiSelection)
        self.create_form_row("Columns to Display:", self.display_cols)
        
        config_group.setLayout(config_layout)
        self.layout.addWidget(config_group)

        # Action Button
        self.filter_btn = self.create_button("Apply Filter", self.apply_filter, "primary")
        self.layout.addWidget(self.filter_btn)

        # Results Section
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        self.results_table = self.create_table()
        results_layout.addWidget(self.results_table)
        results_group.setLayout(results_layout)
        self.layout.addWidget(results_group)

    def handle_upload(self):
        """Handle file upload"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Excel/CSV Files (*.xlsx *.csv)")
        
        if file_path:
            self.file_label.setText(f"Selected: {os.path.basename(file_path)}")
            
            try:
                if file_path.endswith('.xlsx'):
                    self.df_dict = pd.read_excel(file_path, sheet_name=None)
                    self.sheet_combo.clear()
                    self.sheet_combo.addItems(list(self.df_dict.keys()))
                    self.sheet_combo.show()
                    self.sheet_combo.currentTextChanged.connect(self.update_sheet)
                    self.current_df = self.df_dict[self.sheet_combo.currentText()]
                else:
                    self.current_df = pd.read_csv(file_path)
                    self.sheet_combo.hide()
                
                self.update_ui()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")

    def update_sheet(self, sheet_name):
        """Update when sheet selection changes"""
        self.current_df = self.df_dict[sheet_name]
        self.update_ui()

    def update_ui(self):
        """Update UI with current data"""
        self.filter_col_combo.clear()
        self.filter_col_combo.addItems(self.current_df.columns.tolist())
        
        self.display_cols.clear()
        self.display_cols.addItems(self.current_df.columns.tolist())

    def apply_filter(self):
        """Apply the filter to the data"""
        if not hasattr(self, 'current_df'):
            QMessageBox.warning(self, "Warning", "Please upload a file first.")
            return
            
        filter_col = self.filter_col_combo.currentText()
        filter_values = [v.strip() for v in self.filter_values.text().split(',') if v.strip()]
        
        if not filter_values:
            QMessageBox.warning(self, "Warning", "Please enter filter values.")
            return
            
        try:
            filtered_df = self.current_df[self.current_df[filter_col].astype(str).isin(filter_values)]
            
            selected_cols = [item.text() for item in self.display_cols.selectedItems()]
            if not selected_cols:
                selected_cols = self.current_df.columns.tolist()
            
            self.show_dataframe(self.results_table, filtered_df[selected_cols])
            QMessageBox.information(self, "Success", f"Found {len(filtered_df)} matching rows")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Filtering failed: {str(e)}")

# =============================================
# Tool 2: Dual Excel Filter Tool
# =============================================
class DualExcelFilterTool(BaseTool):
    def __init__(self):
        super().__init__("Dual Excel Filter", "Filter data between two Excel files")

    def setup_tool_ui(self):
        self.create_file_upload_section()
        self.create_sheet_selection()
        self.create_filter_configuration()
        self.create_results_section()

    def create_file_upload_section(self):
        files_group = QGroupBox("File Upload")
        files_layout = QVBoxLayout()

        # File 1
        file1_layout = QHBoxLayout()
        self.file1_btn = self.create_button("Select File 1", lambda: self.handle_upload(1))
        file1_layout.addWidget(self.file1_btn)
        self.file1_label = QLabel("No file selected")
        file1_layout.addWidget(self.file1_label)
        files_layout.addLayout(file1_layout)

        # File 2
        file2_layout = QHBoxLayout()
        self.file2_btn = self.create_button("Select File 2", lambda: self.handle_upload(2))
        file2_layout.addWidget(self.file2_btn)
        self.file2_label = QLabel("No file selected")
        file2_layout.addWidget(self.file2_label)
        files_layout.addLayout(file2_layout)

        files_group.setLayout(files_layout)
        self.layout.addWidget(files_group)

    def create_sheet_selection(self):
        sheets_group = QGroupBox("Sheet Selection")
        sheets_layout = QVBoxLayout()

        # File 1 Sheet
        self.sheet1_combo = QComboBox()
        self.create_form_row("File 1 Sheet:", self.sheet1_combo, parent_layout=sheets_layout)

        # File 2 Sheet
        self.sheet2_combo = QComboBox()
        self.create_form_row("File 2 Sheet:", self.sheet2_combo, parent_layout=sheets_layout)

        sheets_group.setLayout(sheets_layout)
        self.layout.addWidget(sheets_group)

    def create_filter_configuration(self):
        filter_group = QGroupBox("Filter Configuration")
        filter_layout = QVBoxLayout()

        # Column selection
        self.col1_combo = QComboBox()
        self.create_form_row("File 1 Column:", self.col1_combo, parent_layout=filter_layout)

        self.col2_combo = QComboBox()
        self.create_form_row("File 2 Column:", self.col2_combo, parent_layout=filter_layout)

        # Filter type
        self.filter_type = QButtonGroup()
        exact = QRadioButton("Exact Match")
        contains = QRadioButton("Contains")
        exact.setChecked(True)

        self.filter_type.addButton(exact)
        self.filter_type.addButton(contains)

        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Match Type:"))
        type_layout.addWidget(exact)
        type_layout.addWidget(contains)
        filter_layout.addLayout(type_layout)

        # Apply button
        self.apply_btn = self.create_button("Apply Filter", self.apply_filter, "primary")
        filter_layout.addWidget(self.apply_btn)

        filter_group.setLayout(filter_layout)
        self.layout.addWidget(filter_group)

    def create_results_section(self):
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()

        self.results_table = self.create_table()
        results_layout.addWidget(self.results_table)

        self.export_btn = self.create_button("Export Results", self.export_results, "success")
        results_layout.addWidget(self.export_btn)

        results_group.setLayout(results_layout)
        self.layout.addWidget(results_group)

    def handle_upload(self, file_num):
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Open File {file_num}", "", "Excel Files (*.xlsx *.xls)"
        )

        if file_path:
            if file_num == 1:
                self.file1_label.setText(f"Selected: {os.path.basename(file_path)}")
                self.df1_dict = pd.read_excel(file_path, sheet_name=None)
                self.sheet1_combo.clear()
                self.sheet1_combo.addItems(self.df1_dict.keys())
                self.sheet1_combo.currentTextChanged.connect(lambda: self.update_df(1))
                self.df1 = self.df1_dict[self.sheet1_combo.currentText()]
            else:
                self.file2_label.setText(f"Selected: {os.path.basename(file_path)}")
                self.df2_dict = pd.read_excel(file_path, sheet_name=None)
                self.sheet2_combo.clear()
                self.sheet2_combo.addItems(self.df2_dict.keys())
                self.sheet2_combo.currentTextChanged.connect(lambda: self.update_df(2))
                self.df2 = self.df2_dict[self.sheet2_combo.currentText()]

            self.update_columns()

    def update_df(self, file_num):
        if file_num == 1:
            self.df1 = self.df1_dict[self.sheet1_combo.currentText()]
        else:
            self.df2 = self.df2_dict[self.sheet2_combo.currentText()]
        self.update_columns()

    def update_columns(self):
        if hasattr(self, 'df1'):
            self.col1_combo.clear()
            self.col1_combo.addItems(self.df1.columns.astype(str).tolist())
        if hasattr(self, 'df2'):
            self.col2_combo.clear()
            self.col2_combo.addItems(self.df2.columns.astype(str).tolist())

    def apply_filter(self):
        if not hasattr(self, 'df1') or not hasattr(self, 'df2'):
            QMessageBox.warning(self, "Warning", "Please upload both files first.")
            return

        col1 = self.col1_combo.currentText()
        col2 = self.col2_combo.currentText()
        match_type = self.filter_type.checkedButton().text()

        try:
            if match_type == "Exact Match":
                self.merged = pd.merge(
                    self.df1, self.df2,
                    left_on=col1, right_on=col2,
                    how='inner'
                )
            else:
                # Contains match logic
                df1_col = self.df1[col1].astype(str)
                df2_col = self.df2[col2].astype(str)

                mask = df1_col.apply(lambda x: self.df2[df2_col.str.contains(x, na=False, case=False)])
                result_rows = []

                for i, matches in mask.items():
                    if not matches.empty:
                        for _, row2 in matches.iterrows():
                            row_combined = pd.concat([self.df1.iloc[i], row2], axis=0)
                            result_rows.append(row_combined)

                self.merged = pd.DataFrame(result_rows)

            self.show_dataframe(self.results_table, self.merged)
            QMessageBox.information(self, "Success", f"Found {len(self.merged)} matching rows")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Filtering failed: {str(e)}")

    def export_results(self):
        if not hasattr(self, 'merged') or self.merged.empty:
            QMessageBox.warning(self, "Warning", "No results to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV Files (*.csv)"
        )

        if file_path:
            try:
                self.merged.to_csv(file_path, index=False)
                QMessageBox.information(self, "Success", "File saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

# =============================================
# Tool 3: Excel Comparator Tool
# =============================================
class ExcelComparatorTool(BaseTool):
    def __init__(self):
        super().__init__("Excel Comparator Tool","Filter data between two Excel files" )
        self.df1_dict = {}
        self.df2_dict = {}
        self.df1 = None
        self.df2 = None
        self.merged_df = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🔍 Excel Files Comparator & Filter Tool")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # File Uploads
        file1_group = QGroupBox("📁 Upload Excel File 1")
        file1_layout = QVBoxLayout()
        self.file1_btn = QPushButton("Select File 1")
        self.file1_btn.clicked.connect(lambda: self.upload_file(1))
        file1_layout.addWidget(self.file1_btn)
        self.file1_label = QLabel("No file selected")
        file1_layout.addWidget(self.file1_label)
        file1_group.setLayout(file1_layout)
        layout.addWidget(file1_group)
        
        file2_group = QGroupBox("📁 Upload Excel File 2")
        file2_layout = QVBoxLayout()
        self.file2_btn = QPushButton("Select File 2")
        self.file2_btn.clicked.connect(lambda: self.upload_file(2))
        file2_layout.addWidget(self.file2_btn)
        self.file2_label = QLabel("No file selected")
        file2_layout.addWidget(self.file2_label)
        file2_group.setLayout(file2_layout)
        layout.addWidget(file2_group)
        
        # Sheet selection
        self.sheet1_combo = QComboBox()
        self.sheet2_combo = QComboBox()
        layout.addWidget(QLabel("📄 Select Sheet from File 1"))
        layout.addWidget(self.sheet1_combo)
        layout.addWidget(QLabel("📄 Select Sheet from File 2"))
        layout.addWidget(self.sheet2_combo)
        
        # Column selection
        self.col1_combo = QComboBox()
        self.col2_combo = QComboBox()
        layout.addWidget(QLabel("📌 Column from File 1"))
        layout.addWidget(self.col1_combo)
        layout.addWidget(QLabel("📌 Column from File 2"))
        layout.addWidget(self.col2_combo)
        
        # Matching type
        self.match_type_group = QButtonGroup()
        exact_match = QRadioButton("Exact Match")
        case_insensitive = QRadioButton("Case-insensitive Match")
        self.match_type_group.addButton(exact_match)
        self.match_type_group.addButton(case_insensitive)
        exact_match.setChecked(True)
        
        layout.addWidget(QLabel("🎯 Matching Type:"))
        layout.addWidget(exact_match)
        layout.addWidget(case_insensitive)
        
        # Compare Button
        self.compare_btn = QPushButton("Compare Files")
        self.compare_btn.clicked.connect(self.compare_files)
        layout.addWidget(self.compare_btn)
        
        # Results
        self.result_label = QLabel()
        self.result_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(self.result_label)
        
        # Results Table
        self.results_table = QTableWidget()
        layout.addWidget(self.results_table)
        
        # Column selection for output
        layout.addWidget(QLabel("📌 Columns from File 1"))
        self.f1_cols_list = QListWidget()
        self.f1_cols_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.f1_cols_list)
        
        layout.addWidget(QLabel("📌 Columns from File 2"))
        self.f2_cols_list = QListWidget()
        self.f2_cols_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.f2_cols_list)
        
        # Update output button
        self.update_output_btn = QPushButton("Update Output")
        self.update_output_btn.clicked.connect(self.update_output)
        layout.addWidget(self.update_output_btn)
        
        # Final output table
        self.final_table = QTableWidget()
        layout.addWidget(self.final_table)
        
        # Download Button
        self.download_btn = QPushButton("📥 Download Final CSV")
        self.download_btn.clicked.connect(self.download_results)
        layout.addWidget(self.download_btn)
        
        self.setLayout(layout)
        
        # Connect sheet combo changes to update dataframes and columns
        self.sheet1_combo.currentTextChanged.connect(lambda: self.update_df(1))
        self.sheet2_combo.currentTextChanged.connect(lambda: self.update_df(2))
    
    def upload_file(self, file_num):
        file_path, _ = QFileDialog.getOpenFileName(self, f"Open File {file_num}", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            try:
                if file_num == 1:
                    self.file1_label.setText(f"Selected: {os.path.basename(file_path)}")
                    self.df1_dict = pd.read_excel(file_path, sheet_name=None)
                    self.sheet1_combo.clear()
                    self.sheet1_combo.addItems(list(self.df1_dict.keys()))
                    # Load first sheet by default
                    self.df1 = self.df1_dict[self.sheet1_combo.currentText()]
                else:
                    self.file2_label.setText(f"Selected: {os.path.basename(file_path)}")
                    self.df2_dict = pd.read_excel(file_path, sheet_name=None)
                    self.sheet2_combo.clear()
                    self.sheet2_combo.addItems(list(self.df2_dict.keys()))
                    self.df2 = self.df2_dict[self.sheet2_combo.currentText()]
                self.update_column_combos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Excel file:\n{str(e)}")
    
    def update_df(self, df_num):
        try:
            if df_num == 1 and self.sheet1_combo.currentText() in self.df1_dict:
                self.df1 = self.df1_dict[self.sheet1_combo.currentText()]
            elif df_num == 2 and self.sheet2_combo.currentText() in self.df2_dict:
                self.df2 = self.df2_dict[self.sheet2_combo.currentText()]
            self.update_column_combos()
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to update data for File {df_num}:\n{str(e)}")
    
    def update_column_combos(self):
        if self.df1 is not None:
            self.col1_combo.clear()
            self.col1_combo.addItems(self.df1.columns.astype(str).tolist())
        if self.df2 is not None:
            self.col2_combo.clear()
            self.col2_combo.addItems(self.df2.columns.astype(str).tolist())
    
    def compare_files(self):
        if self.df1 is None or self.df2 is None:
            QMessageBox.warning(self, "Warning", "Please upload and select sheets for both files first.")
            return
        
        col1 = self.col1_combo.currentText()
        col2 = self.col2_combo.currentText()
        match_type = self.match_type_group.checkedButton().text()
        
        if col1 == "" or col2 == "":
            QMessageBox.warning(self, "Warning", "Please select columns to match on from both files.")
            return
        
        try:
            df1 = self.df1.copy()
            df2 = self.df2.copy()
            
            # Prepare merge keys according to match type
            if match_type == "Case-insensitive Match":
                df1["__merge_key__"] = df1[col1].astype(str).str.lower()
                df2["__merge_key__"] = df2[col2].astype(str).str.lower()
            else:
                df1["__merge_key__"] = df1[col1].astype(str)
                df2["__merge_key__"] = df2[col2].astype(str)
            
            # Prefix columns to identify source
            df1_prefixed = df1.add_prefix("F1_")
            df2_prefixed = df2.add_prefix("F2_")
            df1_prefixed["__merge_key__"] = df1["__merge_key__"]
            df2_prefixed["__merge_key__"] = df2["__merge_key__"]
            
            # Merge on merge key - inner join to get matching rows
            self.merged_df = pd.merge(df1_prefixed, df2_prefixed, on="__merge_key__", how="inner")
            
            self.result_label.setText(f"✅ {len(self.merged_df)} matched rows found")
            self.show_data_in_table(self.results_table, self.merged_df)
            
            # Populate columns lists for selection of output columns
            self.f1_cols_list.clear()
            self.f2_cols_list.clear()
            
            f1_cols = [c for c in self.merged_df.columns if c.startswith("F1_") and c != "__merge_key__"]
            f2_cols = [c for c in self.merged_df.columns if c.startswith("F2_") and c != "__merge_key__"]
            
            self.f1_cols_list.addItems(f1_cols)
            self.f2_cols_list.addItems(f2_cols)
            
            # Select all columns by default
            for i in range(self.f1_cols_list.count()):
                self.f1_cols_list.item(i).setSelected(True)
            for i in range(self.f2_cols_list.count()):
                self.f2_cols_list.item(i).setSelected(True)
            
            # Show initial output
            self.update_output()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Comparison failed:\n{str(e)}")
    
    def update_output(self):
        if self.merged_df is None:
            return
        
        selected_f1_cols = [item.text() for item in self.f1_cols_list.selectedItems()]
        selected_f2_cols = [item.text() for item in self.f2_cols_list.selectedItems()]
        
        final_output = self.merged_df[selected_f1_cols + selected_f2_cols]
        self.show_data_in_table(self.final_table, final_output)
    
    def download_results(self):
        if self.merged_df is None:
            QMessageBox.warning(self, "Warning", "No results to download.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if file_path:
            selected_f1_cols = [item.text() for item in self.f1_cols_list.selectedItems()]
            selected_f2_cols = [item.text() for item in self.f2_cols_list.selectedItems()]
            final_output = self.merged_df[selected_f1_cols + selected_f2_cols]
            try:
                final_output.to_csv(file_path, index=False)
                QMessageBox.information(self, "Success", "File saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")
    
    def show_data_in_table(self, table, df):
        table.clear()
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iat[row, col]))
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                table.setItem(row, col, item)
        
        table.resizeColumnsToContents()

# =============================================
# Tool 4: Partial Match Comparator
# =============================================
class PartialMatchTool(BaseTool):
    def __init__(self):
        super().__init__("Partial Match Finder", "Find partial matches between files")
        self.df1_dict = {}
        self.df2_dict = {}
        self.df1 = None
        self.df2 = None
        self.result_df = pd.DataFrame()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🔍 Excel Files Partial Match (Contains) Comparator")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # File 1 Upload
        file1_group = QGroupBox("📁 Upload Excel File 1")
        file1_layout = QVBoxLayout()
        self.file1_btn = QPushButton("Select File 1")
        self.file1_btn.clicked.connect(lambda: self.upload_file(1))
        self.file1_label = QLabel("No file selected")
        file1_layout.addWidget(self.file1_btn)
        file1_layout.addWidget(self.file1_label)
        file1_group.setLayout(file1_layout)
        layout.addWidget(file1_group)
        
        # File 2 Upload
        file2_group = QGroupBox("📁 Upload Excel File 2")
        file2_layout = QVBoxLayout()
        self.file2_btn = QPushButton("Select File 2")
        self.file2_btn.clicked.connect(lambda: self.upload_file(2))
        self.file2_label = QLabel("No file selected")
        file2_layout.addWidget(self.file2_btn)
        file2_layout.addWidget(self.file2_label)
        file2_group.setLayout(file2_layout)
        layout.addWidget(file2_group)
        
        # Sheet selectors
        self.sheet1_combo = QComboBox()
        self.sheet2_combo = QComboBox()
        layout.addWidget(QLabel("📄 Select Sheet from File 1"))
        layout.addWidget(self.sheet1_combo)
        layout.addWidget(QLabel("📄 Select Sheet from File 2"))
        layout.addWidget(self.sheet2_combo)
        
        # Column selectors
        self.col1_combo = QComboBox()
        self.col2_combo = QComboBox()
        layout.addWidget(QLabel("🔍 Column from File 1"))
        layout.addWidget(self.col1_combo)
        layout.addWidget(QLabel("🔍 Column from File 2"))
        layout.addWidget(self.col2_combo)
        
        # Compare button
        self.compare_btn = QPushButton("Find Partial Matches")
        self.compare_btn.clicked.connect(self.find_partial_matches)
        layout.addWidget(self.compare_btn)
        
        # Result label
        self.result_label = QLabel()
        self.result_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(self.result_label)
        
        # Results table
        self.results_table = QTableWidget()
        layout.addWidget(self.results_table)
        
        # Output columns selector
        layout.addWidget(QLabel("📌 Select output columns"))
        self.output_cols_list = QListWidget()
        self.output_cols_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.output_cols_list)
        
        # Update output button
        self.update_output_btn = QPushButton("Update Output")
        self.update_output_btn.clicked.connect(self.update_output)
        layout.addWidget(self.update_output_btn)
        
        # Final output table
        self.final_table = QTableWidget()
        layout.addWidget(self.final_table)
        
        # Download button
        self.download_btn = QPushButton("📥 Download Output CSV")
        self.download_btn.clicked.connect(self.download_results)
        layout.addWidget(self.download_btn)
        
        self.setLayout(layout)
        
        # Connect sheet combo changes to update dataframes and columns
        self.sheet1_combo.currentTextChanged.connect(lambda: self.update_df(1))
        self.sheet2_combo.currentTextChanged.connect(lambda: self.update_df(2))
    
    def upload_file(self, file_num):
        file_path, _ = QFileDialog.getOpenFileName(self, f"Open File {file_num}", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            try:
                if file_num == 1:
                    self.file1_label.setText(f"Selected: {os.path.basename(file_path)}")
                    self.df1_dict = pd.read_excel(file_path, sheet_name=None)
                    self.sheet1_combo.clear()
                    self.sheet1_combo.addItems(list(self.df1_dict.keys()))
                    self.df1 = self.df1_dict[self.sheet1_combo.currentText()]
                else:
                    self.file2_label.setText(f"Selected: {os.path.basename(file_path)}")
                    self.df2_dict = pd.read_excel(file_path, sheet_name=None)
                    self.sheet2_combo.clear()
                    self.sheet2_combo.addItems(list(self.df2_dict.keys()))
                    self.df2 = self.df2_dict[self.sheet2_combo.currentText()]
                self.update_column_combos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load Excel file:\n{str(e)}")
    
    def update_df(self, df_num):
        try:
            if df_num == 1 and self.sheet1_combo.currentText() in self.df1_dict:
                self.df1 = self.df1_dict[self.sheet1_combo.currentText()]
            elif df_num == 2 and self.sheet2_combo.currentText() in self.df2_dict:
                self.df2 = self.df2_dict[self.sheet2_combo.currentText()]
            self.update_column_combos()
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to update data for File {df_num}:\n{str(e)}")
    
    def update_column_combos(self):
        if self.df1 is not None:
            self.col1_combo.clear()
            self.col1_combo.addItems(self.df1.columns.astype(str).tolist())
        if self.df2 is not None:
            self.col2_combo.clear()
            self.col2_combo.addItems(self.df2.columns.astype(str).tolist())
    
    def find_partial_matches(self):
        if self.df1 is None or self.df2 is None:
            QMessageBox.warning(self, "Warning", "Please upload and select sheets for both files first.")
            return
        
        col1 = self.col1_combo.currentText()
        col2 = self.col2_combo.currentText()
        
        if col1 == "" or col2 == "":
            QMessageBox.warning(self, "Warning", "Please select columns from both files.")
            return
        
        df1 = self.df1.copy()
        df2 = self.df2.copy()
        
        # Normalize for case-insensitive matching
        df1["__cmp__"] = df1[col1].astype(str).str.lower()
        df2["__cmp__"] = df2[col2].astype(str).str.lower()
        
        matched_rows = []
        for _, row in df1.iterrows():
            val1 = row["__cmp__"]
            # Find all rows in df2 where df2[col2] contains val1
            matches = df2[df2["__cmp__"].str.contains(val1, na=False)]
            for _, match_row in matches.iterrows():
                # Combine rows side-by-side
                combined = pd.concat([row.drop("__cmp__"), match_row.drop("__cmp__")])
                matched_rows.append(combined)
        
        if matched_rows:
            self.result_df = pd.DataFrame(matched_rows)
            self.result_label.setText(f"✅ {len(self.result_df)} matches found")
        else:
            self.result_df = pd.DataFrame()
            self.result_label.setText("⚠️ No matches found.")
        
        # Update output columns list
        self.output_cols_list.clear()
        if not self.result_df.empty:
            self.output_cols_list.addItems(self.result_df.columns.tolist())
            # Select all by default
            for i in range(self.output_cols_list.count()):
                self.output_cols_list.item(i).setSelected(True)
        
        self.update_output()
    
    def update_output(self):
        if self.result_df.empty:
            self.show_data_in_table(self.final_table, pd.DataFrame())
            return
        
        selected_cols = [item.text() for item in self.output_cols_list.selectedItems()]
        if not selected_cols:
            selected_cols = self.result_df.columns.tolist()
        
        final_output = self.result_df[selected_cols]
        self.show_data_in_table(self.final_table, final_output)
    
    def download_results(self):
        if self.result_df.empty:
            QMessageBox.warning(self, "Warning", "No results to download.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if file_path:
            selected_cols = [item.text() for item in self.output_cols_list.selectedItems()]
            if not selected_cols:
                selected_cols = self.result_df.columns.tolist()
            final_output = self.result_df[selected_cols]
            try:
                final_output.to_csv(file_path, index=False)
                QMessageBox.information(self, "Success", "File saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")
    
    def show_data_in_table(self, table, df):
        table.clear()
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iat[row, col]))
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                table.setItem(row, col, item)
        
        table.resizeColumnsToContents()
# =============================================
# Main Application Window
# =============================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_app()
        self.init_ui()

    def setup_app(self):
        """Initialize application settings"""
        self.setWindowTitle("PCS7 TurboSift")
        self.setGeometry(100, 100, 1200, 800)
        
        # Application state
        self.logged_in = False
        self.username = ""
        self.license_valid = False
        self.license_features = []
        self.license_expiry = ""
        
        # User credentials
        self.USER_CREDENTIALS = {
            "CONSULTA": "Consulta@123",
            "DEMO": "Demo@123"
        }
        
        # Available tools
        self.TOOL_RUNNERS = {
            "CSV/Excel Filter": CSVExcelFilterTool,
            "Dual Excel Filter": DualExcelFilterTool,
            "Excel Comparator": ExcelComparatorTool,
            "Partial Match Finder": PartialMatchTool
        }

    def init_ui(self):
        """Initialize the main UI"""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        
        self.create_header()
        self.create_content_area()
        self.create_footer()
        self.create_pages()
        
        self.apply_styles()
        self.update_sidebar()


    def create_header(self):
        header = QWidget()
        header.setObjectName("appHeader")
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)
        
        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("assets/consulta_logo.png"))
        logo_label.setPixmap(logo_pixmap.scaledToHeight(40, Qt.SmoothTransformation))
        header_layout.addWidget(logo_label)
        
        # Title
        title = QLabel("PCS7 TurboSift")
        title.setObjectName("appTitle")
        header_layout.addWidget(title, alignment=Qt.AlignLeft)
        
        # Spacer
        header_layout.addStretch()
        
        # Login status
        self.login_status_label = QLabel("Not logged in")
        self.login_status_label.setObjectName("loginStatus")
        header_layout.addWidget(self.login_status_label)
        
        self.main_layout.addWidget(header)
    
    def create_content_area(self):
        # Create a stacked widget for the main content
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
    
    def create_footer(self):
        footer = QWidget()
        footer.setObjectName("appFooter")
        footer_layout = QHBoxLayout()
        footer.setLayout(footer_layout)
        
        # Copyright notice
        copyright = QLabel("© 2023 CONSULTA TECHNOLOGIES PVT LTD. All Rights Reserved.")
        footer_layout.addWidget(copyright, alignment=Qt.AlignRight)
        
        # Support info
        support = QLabel("Support: support@consulta.com")
        footer_layout.addWidget(support, alignment=Qt.AlignCenter)
        
        # Version info
        version = QLabel("Version 1.0.0")
        footer_layout.addWidget(version, alignment=Qt.AlignRight)
        
        self.main_layout.addWidget(footer)
    
    def create_pages(self):
        # Create login page
        self.create_login_page()
        
        # Create admin dashboard page
        self.create_admin_page()
        
        # Create user dashboard page
        self.create_user_page()
        
        # Create tool pages
        self.create_tool_pages()
        
        # Show login page initially
        self.stacked_widget.setCurrentIndex(0)
    
    def create_login_page(self):
        self.login_page = QWidget()
        layout = QVBoxLayout()
        self.login_page.setLayout(layout)
        
        # Container for login form
        login_container = QWidget()
        login_container.setObjectName("loginContainer")
        login_container_layout = QVBoxLayout()
        login_container.setLayout(login_container_layout)
        login_container.setMaximumWidth(400)
        
        # Title
        title = QLabel("Login to PCS7 TurboSift")
        title.setObjectName("loginTitle")
        login_container_layout.addWidget(title, alignment=Qt.AlignCenter)
        
        # Username field
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        login_container_layout.addWidget(self.username_input)
        
        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        login_container_layout.addWidget(self.password_input)
        
        # Show password checkbox
        show_password = QCheckBox("Show password")
        show_password.stateChanged.connect(self.toggle_password_visibility)
        login_container_layout.addWidget(show_password)
        
        # Login button
        login_btn = QPushButton("Login")
        login_btn.setObjectName("loginButton")
        login_btn.clicked.connect(self.handle_login)
        login_container_layout.addWidget(login_btn)
        
        # Add container to layout with centering
        layout.addStretch()
        layout.addWidget(login_container, alignment=Qt.AlignCenter)
        layout.addStretch()
        
        self.stacked_widget.addWidget(self.login_page)
    
    def create_admin_page(self):
        self.admin_page = QWidget()
        layout = QVBoxLayout()
        self.admin_page.setLayout(layout)
        
        # Title
        title = QLabel("Admin Dashboard")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        # Tab widget for different admin sections
        tab_widget = QTabWidget()
        
        # License Management Tab
        license_tab = QWidget()
        license_layout = QVBoxLayout()
        license_tab.setLayout(license_layout)
        
        # License generator section
        license_group = QGroupBox("License Generator")
        license_group_layout = QVBoxLayout()
        license_group.setLayout(license_group_layout)
        
        # Expiry days
        self.expiry_days_input = QSpinBox()
        self.create_form_row(license_group_layout, "License Duration (days):", self.expiry_days_input)
        self.expiry_days_input.setRange(1, 3650)
        self.expiry_days_input.setValue(365)
        
        # Features selection
        features_label = QLabel("Enabled Features:")
        license_group_layout.addWidget(features_label)
        
        self.features_list = QListWidget()
        self.features_list.addItems(["Tool1", "Tool2", "Tool3", "Tool4"])
        self.features_list.setSelectionMode(QListWidget.MultiSelection)
        license_group_layout.addWidget(self.features_list)
        
        # Generate button
        generate_btn = QPushButton("Generate License")
        generate_btn.clicked.connect(self.generate_license)
        license_group_layout.addWidget(generate_btn)
        
        # License preview
        preview_label = QLabel("License Preview:")
        license_group_layout.addWidget(preview_label)
        
        self.license_preview = QTextEdit()
        self.license_preview.setReadOnly(True)
        license_group_layout.addWidget(self.license_preview)
        
        license_layout.addWidget(license_group)
        
        # Add tabs
        tab_widget.addTab(license_tab, "License Management")
        
        layout.addWidget(tab_widget)
        self.stacked_widget.addWidget(self.admin_page)
    
    def create_form_row(self, layout, label_text, widget):
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(200)
        row.addWidget(label)
        row.addWidget(widget)
        layout.addLayout(row)
    
    def create_user_page(self):
        self.user_page = QWidget()
        layout = QVBoxLayout()
        self.user_page.setLayout(layout)
        
        # Title
        title = QLabel("Welcome to PCS7 TurboSift")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        
        # License status panel
        self.license_panel = QGroupBox("License Status")
        self.license_panel_layout = QVBoxLayout()
        self.license_panel.setLayout(self.license_panel_layout)
        
        self.license_status_label = QLabel("No active license")
        self.license_status_label.setWordWrap(True)
        self.license_panel_layout.addWidget(self.license_status_label)
        
        self.license_action_btn = QPushButton("Activate License")
        self.license_action_btn.clicked.connect(self.show_license_upload)
        self.license_panel_layout.addWidget(self.license_action_btn)
        
        layout.addWidget(self.license_panel)
        
        # Tools panel
        self.tools_panel = QGroupBox("Available Tools")
        self.tools_panel_layout = QVBoxLayout()
        self.tools_panel.setLayout(self.tools_panel_layout)
        
        self.tools_container = QWidget()
        self.tools_layout = QVBoxLayout()
        self.tools_container.setLayout(self.tools_layout)
        
        self.tools_panel_layout.addWidget(self.tools_container)
        layout.addWidget(self.tools_panel)
        
        self.stacked_widget.addWidget(self.user_page)
    
    def create_tool_pages(self):
        self.tool_pages = {}
        print("TOOL_RUNNERS exists?", hasattr(self, "TOOL_RUNNERS"))
        print("TOOL_RUNNERS:", getattr(self, "TOOL_RUNNERS", None))
        for tool_name, tool_class in self.TOOL_RUNNERS.items():
            tool_page = tool_class()
            self.tool_pages[tool_name] = tool_page
            self.stacked_widget.addWidget(tool_page)
    
    def toggle_password_visibility(self, state):
        if state == Qt.Checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
    
    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if username in self.USER_CREDENTIALS and self.USER_CREDENTIALS[username] == password:
            self.logged_in = True
            self.username = username
            
            # Update login status
            self.login_status_label.setText(f"Logged in as: {username}")
            
            if username == "CONSULTA":
                self.stacked_widget.setCurrentWidget(self.admin_page)
            else:
                self.update_user_page()
                self.stacked_widget.setCurrentWidget(self.user_page)
            
            # Clear password field
            self.password_input.clear()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password")
    
    def generate_license(self):
        expiry_days = self.expiry_days_input.value()
        selected_features = [item.text() for item in self.features_list.selectedItems()]
        
        license_payload = {
            "machine_id": LicenseGate.get_machine_id(),
            "issued_on": datetime.now().strftime("%Y-%m-%d"),
            "valid_till": (datetime.now() + timedelta(days=expiry_days)).strftime("%Y-%m-%d"),
            "features": selected_features
        }
        
        # Show preview
        self.license_preview.setPlainText(json.dumps(license_payload, indent=4))
        
        # Save to file
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save License File", 
            f"pcs7_license_{datetime.now().strftime('%Y%m%d')}.json", 
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(license_payload, f, indent=4)
                QMessageBox.information(self, "Success", "License file generated successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save license file: {str(e)}")
    
    def update_user_page(self):
        # Update license status
        if self.license_valid and self.license_expiry:
            expiry_date = datetime.strptime(self.license_expiry, "%Y-%m-%d")
            days_left = (expiry_date - datetime.now()).days
            
            status_text = f"""
                <b>License Status:</b> Active<br>
                <b>Expiry Date:</b> {expiry_date.strftime('%d %b %Y')}<br>
                <b>Days Remaining:</b> {days_left}
            """
            
            if days_left <= 30:
                status_text += "<br><span style='color: #e74c3c;'><b>Warning:</b> License expiring soon</span>"
            
            self.license_status_label.setText(status_text)
            self.license_action_btn.setText("Update License")
        else:
            self.license_status_label.setText("<b>License Status:</b> Not Active")
            self.license_action_btn.setText("Activate License")
        
        # Update available tools
        self.update_available_tools()
    
    def update_available_tools(self):
        # Clear existing tools
        while self.tools_layout.count():
            child = self.tools_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.license_valid:
            no_tools_label = QLabel("Please activate a license to access tools")
            no_tools_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
            self.tools_layout.addWidget(no_tools_label)
            return
        
        # Add available tools based on license
        tool_descriptions = {
            "Tool1": "CSV/Excel Filter - Filter data from CSV or Excel files",
            # Add descriptions for other tools
        }
        
        for tool_name in self.license_features:
            if tool_name in self.TOOL_RUNNERS:
                tool_btn = QPushButton(tool_descriptions.get(tool_name, tool_name))
                tool_btn.setToolTip(f"Launch {tool_name}")
                tool_btn.clicked.connect(lambda _, name=tool_name: self.show_tool(name))
                self.tools_layout.addWidget(tool_btn)
        
        # Add stretch to push buttons to top
        self.tools_layout.addStretch()
    
    def show_license_upload(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select License File", 
            "", 
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    license_data = json.load(f)
                
                valid, result = LicenseGate.validate_license_file(license_data)
                if valid:
                    self.license_valid = True
                    self.license_features = result["features"]
                    self.license_expiry = result["valid_till"]
                    self.update_user_page()
                    QMessageBox.information(self, "Success", "License activated successfully")
                else:
                    QMessageBox.warning(self, "Invalid License", result)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load license file: {str(e)}")
    
    def show_tool(self, tool_name):
        if tool_name in self.tool_pages:
            self.stacked_widget.setCurrentWidget(self.tool_pages[tool_name])
    
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            #appHeader {
                background-color: #2c3e50;
                padding: 10px;
                border-bottom: 1px solid #34495e;
            }
            
            #appTitle {
                font-size: 18px;
                font-weight: bold;
                color: #ecf0f1;
                margin-left: 10px;
                txt-transform: uppercase;
            }
            
            #loginStatus {
                color: #bdc3c7;
                font-size: 12px;
            }
            
            #appFooter {
                background-color: #f8f9fa;
                padding: 8px;
                border-top: 1px solid #dee2e6;
                font-size: 11px;
                color: #6c757d;
                txt-transform: uppercase;
                align-items: center;
                justify-content: center;
            }
            
            #loginContainer {
                background-color: white;
                padding: 30px;
                border-radius: 5px;
                border: 1px solid #dee2e6;
            }
            
            #loginTitle {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 20px;
            }
            
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                min-width: 200px;
            }
            
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
                min-width: 100px;
            }
            
            #loginButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                margin-top: 15px;
            }
            
            #loginButton:hover {
                background-color: #2980b9;
            }
            
            QGroupBox {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2c3e50;
                font-weight: bold;
            }
            
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 0 0 5px 5px;
                margin-top: -1px;
            }
            
            QTabBar::tab {
                padding: 8px 16px;
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-radius: 5px 5px 0 0;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background: white;
                border-bottom: 1px solid white;
                margin-bottom: -1px;
            }
            
            QTableWidget {
                border: 1px solid #dee2e6;
                gridline-color: #dee2e6;
                selection-background-color: #e3f2fd;
            }
            
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #dee2e6;
            }
        """)

# =============================================
# Application Entry Point
# =============================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())