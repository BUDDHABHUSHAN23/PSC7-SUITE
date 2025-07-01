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
                             QFrame, QButtonGroup,QSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
import pandas as pd

# =============================================
#  Important fuctions for resource management
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
# Tool Modules To Tool4
# =============================================
class Tool1(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("🧮 CSV/Excel Filter Tool")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        self.file_upload_btn = QPushButton("Upload a CSV or Excel file")
        self.file_upload_btn.clicked.connect(self.upload_file)
        layout.addWidget(self.file_upload_btn)
        
        self.file_info_label = QLabel("No file uploaded")
        layout.addWidget(self.file_info_label)
        
        self.sheet_combo = QComboBox()
        self.sheet_combo.hide()
        layout.addWidget(self.sheet_combo)
        
        self.filter_col_combo = QComboBox()
        layout.addWidget(QLabel("1️⃣ Select Filter Column"))
        layout.addWidget(self.filter_col_combo)
        
        layout.addWidget(QLabel("2️⃣ Enter Values to Filter (comma separated)"))
        self.filter_values_input = QLineEdit()
        layout.addWidget(self.filter_values_input)
        
        layout.addWidget(QLabel("3️⃣ Select Columns to Display"))
        self.display_cols_list = QListWidget()
        self.display_cols_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.display_cols_list)
        
        self.apply_filter_btn = QPushButton("🔍 Apply Filter")
        self.apply_filter_btn.clicked.connect(self.apply_filter)
        layout.addWidget(self.apply_filter_btn)
        
        self.results_table = QTableWidget()
        layout.addWidget(self.results_table)
        
        preview_title = QLabel("📋 Preview of Uploaded Data")
        preview_title.setStyleSheet("font-weight: bold;")
        layout.addWidget(preview_title)
        
        self.preview_table = QTableWidget()
        layout.addWidget(self.preview_table)

        self.download_btn = QPushButton("💾 Download Filtered Result")
        self.download_btn.clicked.connect(self.download_filtered_result)
        layout.addWidget(self.download_btn)
        self.download_btn.setEnabled(False)  # Disabled until filter is applied
                
        self.setLayout(layout)
        
    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Excel/CSV Files (*.xlsx *.csv)")
        if file_path:
            self.file_info_label.setText(f"Uploaded: {os.path.basename(file_path)}")
            
            if file_path.endswith('.xlsx'):
                actual_path = resource_path(file_path) if not os.path.isabs(file_path) else file_path
                self.df_dict = pd.read_excel(file_path, sheet_name=None)
                self.sheet_combo.clear()
                self.sheet_combo.addItems(list(self.df_dict.keys()))
                self.sheet_combo.show()
                self.sheet_combo.currentTextChanged.connect(self.update_sheet)
                self.current_df = self.df_dict[self.sheet_combo.currentText()]
            else:
                self.current_df = pd.read_csv(file_path)
                self.sheet_combo.hide()
            
            self.update_ui_with_data()
    
    def update_sheet(self, sheet_name):
        self.current_df = self.df_dict[sheet_name]
        self.update_ui_with_data()
    
    def update_ui_with_data(self):
        self.filter_col_combo.clear()
        self.filter_col_combo.addItems(self.current_df.columns.tolist())
        
        self.display_cols_list.clear()
        self.display_cols_list.addItems(self.current_df.columns.tolist())
        
        self.show_data_in_table(self.preview_table, self.current_df.head())
    
    def apply_filter(self):
        filter_col = self.filter_col_combo.currentText()
        filter_values = [v.strip() for v in self.filter_values_input.text().split(',') if v.strip()]
        
        if not filter_values:
            QMessageBox.warning(self, "Warning", "⚠️ Please enter at least one value to filter.")
            return
            
        filtered_df = self.current_df[self.current_df[filter_col].astype(str).isin(filter_values)]
        
        selected_cols = [item.text() for item in self.display_cols_list.selectedItems()]
        if not selected_cols:
            selected_cols = self.current_df.columns.tolist()
        
        self.filtered_df_to_download = filtered_df[selected_cols]
        self.show_data_in_table(self.results_table, self.filtered_df_to_download)
        self.download_btn.setEnabled(True)
        QMessageBox.information(self, "Success", f"✅ Found {len(filtered_df)} matching row(s)")
    
    def show_data_in_table(self, table, df):
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                table.setItem(row, col, QTableWidgetItem(str(df.iloc[row, col])))
        
        table.resizeColumnsToContents()

    def download_filtered_result(self):
        if hasattr(self, 'filtered_df_to_download') and not self.filtered_df_to_download.empty:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv);;Excel Files (*.xlsx)")
            if file_path:
                try:
                    if file_path.endswith('.csv'):
                        self.filtered_df_to_download.to_csv(file_path, index=False)
                    elif file_path.endswith('.xlsx'):
                        self.filtered_df_to_download.to_excel(file_path, index=False)
                    else:
                        # Default to CSV if no extension
                        file_path += ".csv"
                        self.filtered_df_to_download.to_csv(file_path, index=False)
                    QMessageBox.information(self, "Success", "✅ File saved successfully!")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"❌ Failed to save file: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "⚠️ No data available to download.")


class Tool2(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📊 Dual Excel Filter Tool")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # File Uploads
        file1_group = QGroupBox("📁 Upload Excel File 1 (Sheet1)")
        file1_layout = QVBoxLayout()
        self.file1_btn = QPushButton("Select File 1")
        self.file1_btn.clicked.connect(lambda: self.upload_file(1))
        file1_layout.addWidget(self.file1_btn)
        self.file1_label = QLabel("No file selected")
        file1_layout.addWidget(self.file1_label)
        file1_group.setLayout(file1_layout)
        layout.addWidget(file1_group)
        
        file2_group = QGroupBox("📁 Upload Excel File 2 (Sheet2)")
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
        
        # Step 1: Filter
        step1_group = QGroupBox("🔗 Step 1: Filter Sheet2 using values from Sheet1")
        step1_layout = QVBoxLayout()
        
        self.col_sheet1_combo = QComboBox()
        self.col_sheet2_combo = QComboBox()
        step1_layout.addWidget(QLabel("Select Column from Sheet1"))
        step1_layout.addWidget(self.col_sheet1_combo)
        step1_layout.addWidget(QLabel("Select Column from Sheet2"))
        step1_layout.addWidget(self.col_sheet2_combo)
        
        self.first_filter_mode = QButtonGroup()
        starts_with = QRadioButton("Starts With")
        contains = QRadioButton("Contains")
        self.first_filter_mode.addButton(starts_with)
        self.first_filter_mode.addButton(contains)
        starts_with.setChecked(True)
        
        step1_layout.addWidget(QLabel("First Filter Mode:"))
        step1_layout.addWidget(starts_with)
        step1_layout.addWidget(contains)
        
        self.apply_step1_btn = QPushButton("Apply Step 1 Filter")
        self.apply_step1_btn.clicked.connect(self.apply_step1_filter)
        step1_layout.addWidget(self.apply_step1_btn)
        
        self.step1_result_label = QLabel("🔎 Step 1: No filter applied yet")
        step1_layout.addWidget(self.step1_result_label)
        
        self.step1_table = QTableWidget()
        step1_layout.addWidget(self.step1_table)
        
        step1_group.setLayout(step1_layout)
        layout.addWidget(step1_group)
        
        # Step 2: Additional Filter
        step2_group = QGroupBox("🧪 Step 2: Additional Filter")
        step2_layout = QVBoxLayout()
        
        self.add_filter_col_combo = QComboBox()
        step2_layout.addWidget(QLabel("Column to Filter"))
        step2_layout.addWidget(self.add_filter_col_combo)
        
        self.second_filter_mode = QButtonGroup()
        contains_filter = QRadioButton("Contains Filter")
        exact_match = QRadioButton("Exact Match")
        self.second_filter_mode.addButton(contains_filter)
        self.second_filter_mode.addButton(exact_match)
        contains_filter.setChecked(True)
        
        step2_layout.addWidget(QLabel("Filter Mode:"))
        step2_layout.addWidget(contains_filter)
        step2_layout.addWidget(exact_match)
        
        step2_layout.addWidget(QLabel("Enter values (comma separated)"))
        self.filter_values_input = QTextEdit()
        self.filter_values_input.setMaximumHeight(100)
        step2_layout.addWidget(self.filter_values_input)
        
        step2_group.setLayout(step2_layout)
        layout.addWidget(step2_group)
        
        # Step 3: Output Columns
        step3_group = QGroupBox("📤 Step 3: Select Output Columns")
        step3_layout = QVBoxLayout()
        
        self.output_cols_list = QListWidget()
        self.output_cols_list.setSelectionMode(QListWidget.MultiSelection)
        step3_layout.addWidget(self.output_cols_list)
        
        step3_group.setLayout(step3_layout)
        layout.addWidget(step3_group)
        
        # Final Apply Button
        self.final_apply_btn = QPushButton("✅ Apply All Filters")
        self.final_apply_btn.clicked.connect(self.apply_all_filters)
        layout.addWidget(self.final_apply_btn)
        
        # Results
        self.final_result_label = QLabel()
        self.final_result_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.final_result_label)
        
        self.final_table = QTableWidget()
        layout.addWidget(self.final_table)
        
        # Download Button
        self.download_btn = QPushButton("📥 Download CSV")
        self.download_btn.clicked.connect(self.download_results)
        layout.addWidget(self.download_btn)
        
        self.setLayout(layout)
    
    def upload_file(self, file_num):
        file_path, _ = QFileDialog.getOpenFileName(self, f"Open File {file_num}", "", "Excel Files (*.xlsx)")
        if file_path:
            if file_num == 1:
                self.file1_label.setText(f"Selected: {os.path.basename(file_path)}")
                self.df1_dict = pd.read_excel(file_path, sheet_name=None)
                self.sheet1_combo.clear()
                self.sheet1_combo.addItems(list(self.df1_dict.keys()))
                self.sheet1_combo.currentTextChanged.connect(lambda: self.update_df(1))
                self.df1 = self.df1_dict[self.sheet1_combo.currentText()]
            else:
                self.file2_label.setText(f"Selected: {os.path.basename(file_path)}")
                self.df2_dict = pd.read_excel(file_path, sheet_name=None)
                self.sheet2_combo.clear()
                self.sheet2_combo.addItems(list(self.df2_dict.keys()))
                self.sheet2_combo.currentTextChanged.connect(lambda: self.update_df(2))
                self.df2 = self.df2_dict[self.sheet2_combo.currentText()]
            
            self.update_column_combos()
    
    def update_df(self, df_num):
        if df_num == 1:
            self.df1 = self.df1_dict[self.sheet1_combo.currentText()]
        else:
            self.df2 = self.df2_dict[self.sheet2_combo.currentText()]
        self.update_column_combos()
    
    def update_column_combos(self):
        if hasattr(self, 'df1'):
            self.col_sheet1_combo.clear()
            self.col_sheet1_combo.addItems(self.df1.columns.tolist())
        
        if hasattr(self, 'df2'):
            self.col_sheet2_combo.clear()
            self.col_sheet2_combo.addItems(self.df2.columns.tolist())
            self.add_filter_col_combo.clear()
            self.add_filter_col_combo.addItems(self.df2.columns.tolist())
            self.output_cols_list.clear()
            self.output_cols_list.addItems(self.df2.columns.tolist())
    
    def apply_step1_filter(self):
        if not hasattr(self, 'df1') or not hasattr(self, 'df2'):
            QMessageBox.warning(self, "Warning", "Please upload both files first.")
            return
            
        col_sheet1 = self.col_sheet1_combo.currentText()
        col_sheet2 = self.col_sheet2_combo.currentText()
        values_to_match = self.df1[col_sheet1].dropna().astype(str).unique()
        
        if self.first_filter_mode.checkedButton().text() == "Starts With":
            self.df2_step1 = self.df2[self.df2[col_sheet2].astype(str).apply(
                lambda x: any(x.startswith(v) for v in values_to_match))]
        else:
            self.df2_step1 = self.df2[self.df2[col_sheet2].astype(str).apply(
                lambda x: any(v in x for v in values_to_match))]
        
        self.step1_result_label.setText(f"🔎 Step 1: {len(self.df2_step1)} rows matched")
        self.show_data_in_table(self.step1_table, self.df2_step1.head(50))
    
    def apply_all_filters(self):
        if not hasattr(self, 'df2_step1'):
            QMessageBox.warning(self, "Warning", "Please apply Step 1 filter first.")
            return
            
        df2_filtered = self.df2_step1.copy()
        filter_values = [v.strip() for v in self.filter_values_input.toPlainText().split(",") if v.strip()]
        
        if filter_values:
            add_filter_col = self.add_filter_col_combo.currentText()
            
            if self.second_filter_mode.checkedButton().text() == "Contains Filter":
                df2_filtered = df2_filtered[df2_filtered[add_filter_col].astype(str).apply(
                    lambda x: any(val in x for val in filter_values))]
            else:
                df2_filtered = df2_filtered[df2_filtered[add_filter_col].astype(str).isin(filter_values)]
        
        # Get selected output columns
        selected_cols = [item.text() for item in self.output_cols_list.selectedItems()]
        if not selected_cols:
            selected_cols = self.df2.columns.tolist()
        
        self.final_df = df2_filtered[selected_cols]
        self.final_result_label.setText(f"🎯 Final Rows: {len(self.final_df)}")
        self.show_data_in_table(self.final_table, self.final_df)
    
    def download_results(self):
        if not hasattr(self, 'final_df'):
            QMessageBox.warning(self, "Warning", "No results to download.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.final_df.to_csv(file_path, index=False)
            QMessageBox.information(self, "Success", "File saved successfully.")
    
    def show_data_in_table(self, table, df):
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                table.setItem(row, col, QTableWidgetItem(str(df.iloc[row, col])))
        
        table.resizeColumnsToContents()

class Tool3(QWidget):
    def __init__(self):
        super().__init__()
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
        self.result_label.setStyleSheet("font-weight: bold;")
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
    
    def upload_file(self, file_num):
        file_path, _ = QFileDialog.getOpenFileName(self, f"Open File {file_num}", "", "Excel Files (*.xlsx)")
        if file_path:
            if file_num == 1:
                self.file1_label.setText(f"Selected: {os.path.basename(file_path)}")
                self.df1_dict = pd.read_excel(file_path, sheet_name=None)
                self.sheet1_combo.clear()
                self.sheet1_combo.addItems(list(self.df1_dict.keys()))
                self.sheet1_combo.currentTextChanged.connect(lambda: self.update_df(1))
                self.df1 = self.df1_dict[self.sheet1_combo.currentText()]
            else:
                self.file2_label.setText(f"Selected: {os.path.basename(file_path)}")
                self.df2_dict = pd.read_excel(file_path, sheet_name=None)
                self.sheet2_combo.clear()
                self.sheet2_combo.addItems(list(self.df2_dict.keys()))
                self.sheet2_combo.currentTextChanged.connect(lambda: self.update_df(2))
                self.df2 = self.df2_dict[self.sheet2_combo.currentText()]
            
            self.update_column_combos()
    
    def update_df(self, df_num):
        if df_num == 1:
            self.df1 = self.df1_dict[self.sheet1_combo.currentText()]
        else:
            self.df2 = self.df2_dict[self.sheet2_combo.currentText()]
        self.update_column_combos()
    
    def update_column_combos(self):
        if hasattr(self, 'df1'):
            self.col1_combo.clear()
            self.col1_combo.addItems(self.df1.columns.tolist())
        
        if hasattr(self, 'df2'):
            self.col2_combo.clear()
            self.col2_combo.addItems(self.df2.columns.tolist())
    
    def compare_files(self):
        if not hasattr(self, 'df1') or not hasattr(self, 'df2'):
            QMessageBox.warning(self, "Warning", "Please upload both files first.")
            return
            
        col1 = self.col1_combo.currentText()
        col2 = self.col2_combo.currentText()
        match_type = self.match_type_group.checkedButton().text()
        
        # Prepare merge keys
        df1 = self.df1.copy()
        df2 = self.df2.copy()
        
        df1["__merge_key__"] = df1[col1].astype(str).str.lower() if match_type == "Case-insensitive Match" else df1[col1].astype(str)
        df2["__merge_key__"] = df2[col2].astype(str).str.lower() if match_type == "Case-insensitive Match" else df2[col2].astype(str)
        
        # Prefix columns
        df1_prefixed = df1.add_prefix("F1_")
        df2_prefixed = df2.add_prefix("F2_")
        df1_prefixed["__merge_key__"] = df1["__merge_key__"]
        df2_prefixed["__merge_key__"] = df2["__merge_key__"]
        
        # Merge
        self.merged_df = pd.merge(df1_prefixed, df2_prefixed, on="__merge_key__", how="inner")
        
        self.result_label.setText(f"✅ {len(self.merged_df)} matched rows found")
        self.show_data_in_table(self.results_table, self.merged_df)
        
        # Update column lists for output selection
        self.f1_cols_list.clear()
        self.f2_cols_list.clear()
        
        f1_cols = [c for c in self.merged_df.columns if c.startswith("F1_") and "merge_key" not in c]
        f2_cols = [c for c in self.merged_df.columns if c.startswith("F2_") and "merge_key" not in c]
        
        self.f1_cols_list.addItems(f1_cols)
        self.f2_cols_list.addItems(f2_cols)
        
        # Select all by default
        for i in range(self.f1_cols_list.count()):
            self.f1_cols_list.item(i).setSelected(True)
        for i in range(self.f2_cols_list.count()):
            self.f2_cols_list.item(i).setSelected(True)
        
        # Show initial output
        self.update_output()
    
    def update_output(self):
        if not hasattr(self, 'merged_df'):
            return
            
        selected_f1_cols = [item.text() for item in self.f1_cols_list.selectedItems()]
        selected_f2_cols = [item.text() for item in self.f2_cols_list.selectedItems()]
        
        final_output = self.merged_df[selected_f1_cols + selected_f2_cols]
        self.show_data_in_table(self.final_table, final_output)
    
    def download_results(self):
        if not hasattr(self, 'merged_df'):
            QMessageBox.warning(self, "Warning", "No results to download.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if file_path:
            selected_f1_cols = [item.text() for item in self.f1_cols_list.selectedItems()]
            selected_f2_cols = [item.text() for item in self.f2_cols_list.selectedItems()]
            final_output = self.merged_df[selected_f1_cols + selected_f2_cols]
            final_output.to_csv(file_path, index=False)
            QMessageBox.information(self, "Success", "File saved successfully.")
    
    def show_data_in_table(self, table, df):
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                table.setItem(row, col, QTableWidgetItem(str(df.iloc[row, col])))
        
        table.resizeColumnsToContents()

class Tool4(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🔍 Excel Files Partial Match (Contains) Comparator")
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
        layout.addWidget(QLabel("🔍 Column from File 1"))
        layout.addWidget(self.col1_combo)
        layout.addWidget(QLabel("🔍 Column from File 2"))
        layout.addWidget(self.col2_combo)
        
        # Compare Button
        self.compare_btn = QPushButton("Find Partial Matches")
        self.compare_btn.clicked.connect(self.find_partial_matches)
        layout.addWidget(self.compare_btn)
        
        # Results
        self.result_label = QLabel()
        self.result_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.result_label)
        
        # Results Table
        self.results_table = QTableWidget()
        layout.addWidget(self.results_table)
        
        # Column selection for output
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
        
        # Download Button
        self.download_btn = QPushButton("📥 Download Output CSV")
        self.download_btn.clicked.connect(self.download_results)
        layout.addWidget(self.download_btn)
        
        self.setLayout(layout)
    
    def upload_file(self, file_num):
        file_path, _ = QFileDialog.getOpenFileName(self, f"Open File {file_num}", "", "Excel Files (*.xlsx)")
        if file_path:
            if file_num == 1:
                self.file1_label.setText(f"Selected: {os.path.basename(file_path)}")
                self.df1_dict = pd.read_excel(file_path, sheet_name=None)
                self.sheet1_combo.clear()
                self.sheet1_combo.addItems(list(self.df1_dict.keys()))
                self.sheet1_combo.currentTextChanged.connect(lambda: self.update_df(1))
                self.df1 = self.df1_dict[self.sheet1_combo.currentText()]
            else:
                self.file2_label.setText(f"Selected: {os.path.basename(file_path)}")
                self.df2_dict = pd.read_excel(file_path, sheet_name=None)
                self.sheet2_combo.clear()
                self.sheet2_combo.addItems(list(self.df2_dict.keys()))
                self.sheet2_combo.currentTextChanged.connect(lambda: self.update_df(2))
                self.df2 = self.df2_dict[self.sheet2_combo.currentText()]
            
            self.update_column_combos()
    
    def update_df(self, df_num):
        if df_num == 1:
            self.df1 = self.df1_dict[self.sheet1_combo.currentText()]
        else:
            self.df2 = self.df2_dict[self.sheet2_combo.currentText()]
        self.update_column_combos()
    
    def update_column_combos(self):
        if hasattr(self, 'df1'):
            self.col1_combo.clear()
            self.col1_combo.addItems(self.df1.columns.tolist())
        
        if hasattr(self, 'df2'):
            self.col2_combo.clear()
            self.col2_combo.addItems(self.df2.columns.tolist())
    
    def find_partial_matches(self):
        if not hasattr(self, 'df1') or not hasattr(self, 'df2'):
            QMessageBox.warning(self, "Warning", "Please upload both files first.")
            return
            
        col1 = self.col1_combo.currentText()
        col2 = self.col2_combo.currentText()
        
        df1 = self.df1.copy()
        df2 = self.df2.copy()
        
        df1["__cmp__"] = df1[col1].astype(str).str.lower()
        df2["__cmp__"] = df2[col2].astype(str).str.lower()
        
        matched_rows = []
        for _, row in df1.iterrows():
            val1 = row["__cmp__"]
            matches = df2[df2["__cmp__"].str.contains(val1, na=False)]
            for _, match_row in matches.iterrows():
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
        if not hasattr(self, 'result_df') or self.result_df.empty:
            self.show_data_in_table(self.final_table, pd.DataFrame())
            return
            
        selected_cols = [item.text() for item in self.output_cols_list.selectedItems()]
        if not selected_cols:
            selected_cols = self.result_df.columns.tolist()
        
        final_output = self.result_df[selected_cols]
        self.show_data_in_table(self.final_table, final_output)
    
    def download_results(self):
        if not hasattr(self, 'result_df') or self.result_df.empty:
            QMessageBox.warning(self, "Warning", "No results to download.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if file_path:
            selected_cols = [item.text() for item in self.output_cols_list.selectedItems()]
            if not selected_cols:
                selected_cols = self.result_df.columns.tolist()
            final_output = self.result_df[selected_cols]
            final_output.to_csv(file_path, index=False)
            QMessageBox.information(self, "Success", "File saved successfully.")
    
    def show_data_in_table(self, table, df):
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                table.setItem(row, col, QTableWidgetItem(str(df.iloc[row, col])))
        
        table.resizeColumnsToContents()

# =============================================
# Main Application Window
# =============================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.logged_in = False
        self.username = ""
        self.license_valid = False
        self.license_features = []
        self.license_expiry = ""
        self.selected_tool = ""
        
        self.USER_CREDENTIALS = {
            "CONSULTA": "Consulta@123",
            "DEMO": "Demo@123"
        }
        
        self.TOOL_RUNNERS = {
            "Tool1": Tool1,
            # Other tools would be added here
            "Tool2": Tool2,
            "Tool3": Tool3,
            "Tool4": Tool4
        }
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("PCS7 TurboSift")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main container with header, content and footer
        main_container = QWidget()
        main_layout = QVBoxLayout()
        main_container.setLayout(main_layout)
        self.setCentralWidget(main_container)
        
        # Header
        main_layout.addWidget(self.create_header())
        
        # Horizontal line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Main content area
        content_widget = QWidget()
        content_layout = QHBoxLayout()
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)
        
        # Sidebar
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(250)
        self.sidebar_layout = QVBoxLayout()
        self.sidebar.setLayout(self.sidebar_layout)
        content_layout.addWidget(self.sidebar)
        
        # # Sidebar logo
        # logo_label = QLabel()
        # # logo_pixmap = QPixmap(os.path.join("assets", "consulta_logo.png"))
        # logo_label.setPixmap(logo_pixmap.scaledToWidth(200))
        # self.sidebar_layout.addWidget(logo_label)
        
        # Sidebar content
        self.sidebar_content = QWidget()
        self.sidebar_content_layout = QVBoxLayout()
        self.sidebar_content.setLayout(self.sidebar_content_layout)
        if self.sidebar_layout.indexOf(self.sidebar_content) == -1:
            self.sidebar_layout.addWidget(self.sidebar_content)
            self.sidebar_content_layout.setContentsMargins(10, 10, 10, 10)
        # Stacked widget for main content
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        
        # Create pages
        self.create_login_page()
        self.create_admin_page()
        self.create_user_page()
        self.create_tool_pages()
        
        # Footer
        main_layout.addWidget(self.create_footer())
        
        # Show login page initially
        self.stacked_widget.setCurrentIndex(0)
        
        # Apply styles and initialize sidebar
        self.apply_styles()
        self.create_sidebar_content()
        self.sidebar_content_layout.update()
        self.sidebar_content.update()
        self.sidebar.update()
        self.sidebar.repaint()

    
    def create_header(self):
        header = QWidget()
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)
        
        logo_label = QLabel()
        logo_pixmap = QPixmap(os.path.join("assets", "consulta_logo.png"))
        logo_label.setPixmap(logo_pixmap.scaledToHeight(50))
        header_layout.addWidget(logo_label)
        
        title = QLabel("PCS7 TurboSift")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title, alignment=Qt.AlignCenter)
        
        header_layout.addStretch()
        return header
    
    def create_footer(self):
        footer = QWidget()
        footer.setObjectName("footer")
        footer_layout = QHBoxLayout()
        footer.setLayout(footer_layout)
        
        copyright = QLabel("© 2016 All Rights Reserved CONSULTA TECHNOLOGIES PVT LTD.")
        copyright.setStyleSheet("font-size: 0.9rem;")
        footer_layout.addWidget(copyright, alignment=Qt.AlignCenter)
        
        return footer
    
    def create_sidebar_content(self):
        # Clear previous content
        while self.sidebar_content_layout.count():
            child = self.sidebar_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if self.logged_in:
            # Sidebar header
            sidebar_header = QLabel("PCS7 TurboSift")
            sidebar_header.setStyleSheet("""
                font-size: 18px;
                font-weight: bold;
                color: black
                padding: 15px 0;
                background-color: #2c3e50;
                text-align: center;
                border-bottom: 1px solid #34495e;
            """)
            self.sidebar_content_layout.addWidget(sidebar_header)
            
            # Welcome message
            welcome_label = QLabel(f"👤 {self.username}")
            welcome_label.setStyleSheet("""
                font-size: 14px;
                color:black;    
                padding: 10px 5px;
                background-color: rgba(255,255,255,0.1);
                border-radius: 4px;
            """)
            self.sidebar_content_layout.addWidget(welcome_label)
            
            # License status
            if self.license_valid and self.license_expiry:
                expiry_date = datetime.strptime(self.license_expiry, "%Y-%m-%d")
                days_left = (expiry_date - datetime.now()).days
                
                license_group = QGroupBox("License Status")
                license_group.setStyleSheet("""
                    QGroupBox {
                        color: #bdc3c7;
                        border: 1px solid #34495e;
                        margin-top: 15px;
                    }
                    QGroupBox::title {
                        color: #3498db;
                        subcontrol-origin: margin;
                        left: 5px;
                    }
                """)
                
                license_layout = QVBoxLayout()
                
                status_label = QLabel(f"Valid till: {expiry_date.strftime('%d %b %Y')}")
                status_label.setStyleSheet("color: #ecf0f1;")
                license_layout.addWidget(status_label)
                
                if days_left <= 7:
                    warning_label = QLabel(f"⚠️ Expires in {days_left} day(s)")
                    warning_label.setStyleSheet("""
                        color: #f39c12;
                        font-weight: bold;
                        padding-top: 5px;
                    """)
                    license_layout.addWidget(warning_label)
                    self.show_license_warning(days_left, expiry_date)
                
                license_group.setLayout(license_layout)
                self.sidebar_content_layout.addWidget(license_group)
            
            # User Manual Download
            manual_btn = QPushButton("📘 User Manual")
            manual_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    padding: 8px;
                    border: none;
                    border-radius: 4px;
                    text-align: left;
                    margin-top: 10px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            manual_btn.clicked.connect(self.download_user_manual)
            self.sidebar_content_layout.addWidget(manual_btn)
            
            # Spacer
            self.sidebar_content_layout.addStretch()
            
            # Logout Button (fixed at bottom)
            logout_btn = QPushButton("🚪 Logout")
            logout_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    padding: 10px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    margin-top: 20px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            logout_btn.clicked.connect(self.handle_logout)
            self.sidebar_content_layout.addWidget(logout_btn)
    
    def show_license_warning(self, days_left, expiry_date):
        warning_dialog = QMessageBox()
        warning_dialog.setIcon(QMessageBox.Warning)
        warning_dialog.setWindowTitle("License Expiry Warning")
        warning_dialog.setText(f"⚠️ Your license will expire in {days_left} day(s)")
        warning_dialog.setInformativeText(f"License valid until: {expiry_date.strftime('%d %b %Y')}")
        warning_dialog.exec_()
    
    def download_user_manual(self):
        manual_path = resource_path(os.path.join("assets", "PCS7 UserManual.pdf"))  
        if os.path.exists(manual_path):
            save_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Save User Manual", 
                "PCS7_TurboSift_User_Manual.pdf", 
                "PDF Files (*.pdf)"
            )
            if save_path:
                try:
                    shutil.copyfile(manual_path, save_path)
                    QMessageBox.information(self, "Success", "User manual downloaded successfully!")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save manual: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "User manual file not found!")
    
    def handle_logout(self):
        self.logged_in = False
        self.username = ""
        self.license_valid = False
        self.license_features = []
        self.license_expiry = ""
        
        self.username_input.clear()
        self.password_input.clear()
        
        self.stacked_widget.setCurrentWidget(self.login_page)
        self.create_sidebar_content()
    
    # ... [Rest of the methods remain the same as previous implementation] ...
    def create_login_page(self):
        self.login_page = QWidget()
        layout = QVBoxLayout()
        self.login_page.setLayout(layout)
        
        # Title
        title = QLabel("🔐 Secure Login")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title, alignment=Qt.AlignCenter)
        
        # Username
        layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        
        # Show password checkbox
        self.show_password_check = QCheckBox("Show Password")
        self.show_password_check.stateChanged.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password_check)
        
        # Login button
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)
        
        # Add to stacked widget
        self.stacked_widget.addWidget(self.login_page)
    
    def create_admin_page(self):
        self.admin_page = QWidget()
        layout = QVBoxLayout()
        self.admin_page.setLayout(layout)
        
        # Title
        title = QLabel("🔧 Admin Dashboard")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title, alignment=Qt.AlignCenter)
        
        # Subtitle
        subtitle = QLabel("🔧 Admin License Generator")
        subtitle.setStyleSheet("font-size: 16px;")
        layout.addWidget(subtitle, alignment=Qt.AlignCenter)
        
        # Expiry days
        layout.addWidget(QLabel("📅 Expiry Days:"))
        self.expiry_days_input = QSpinBox()
        self.expiry_days_input.setRange(1, 9999)
        self.expiry_days_input.setValue(365)
        layout.addWidget(self.expiry_days_input)
        
        # Features
        layout.addWidget(QLabel("⚙️ Enable Tools:"))
        self.features_list = QListWidget()
        self.features_list.addItems(["Tool1", "Tool2", "Tool3", "Tool4"])
        self.features_list.setSelectionMode(QListWidget.MultiSelection)
        # Select Tool1 and Tool2 by default
        for i in range(self.features_list.count()):
            item = self.features_list.item(i)
            if item.text() in ["Tool1", "Tool2"]:
                item.setSelected(True)
        layout.addWidget(self.features_list)
        
        # Generate button
        generate_btn = QPushButton("Generate License File")
        generate_btn.clicked.connect(self.generate_license)
        layout.addWidget(generate_btn)
        
        # License preview
        self.license_preview = QTextEdit()
        self.license_preview.setReadOnly(True)
        layout.addWidget(self.license_preview)
        
        # Add to stacked widget
        self.stacked_widget.addWidget(self.admin_page)
    
    def create_user_page(self):
        self.user_page = QWidget()
        layout = QVBoxLayout()
        self.user_page.setLayout(layout)
        
        # Title
        title = QLabel("PCS7 TurboSift")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title, alignment=Qt.AlignCenter)
        
        # License status
        self.license_status_label = QLabel()
        self.license_status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.license_status_label)
        
        # Tool selection
        self.tool_selection_widget = QWidget()
        self.tool_selection_layout = QVBoxLayout()
        self.tool_selection_widget.setLayout(self.tool_selection_layout)
        layout.addWidget(self.tool_selection_widget)
        
        # Add to stacked widget
        self.stacked_widget.addWidget(self.user_page)
    
    def create_tool_pages(self):
        # Create tool pages and add to stacked widget
        self.tool_pages = {}
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
            
            if username == "CONSULTA":
                self.create_sidebar_content()  # <-- Force sidebar update after login  
                self.stacked_widget.setCurrentWidget(self.admin_page)
            else:
                self.create_sidebar_content()  # <-- Same for user
                self.update_user_page()
                self.stacked_widget.setCurrentWidget(self.user_page)
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password!")
    
    def generate_license(self):
        expiry_days = self.expiry_days_input.value()
        selected_features = [item.text() for item in self.features_list.selectedItems()]
        
        license_payload = {
            "machine_id": LicenseGate.get_machine_id(),
            "issued_on": str(datetime.now()),
            "valid_till": (datetime.now() + timedelta(days=expiry_days)).strftime("%Y-%m-%d"),
            "features": selected_features
        }
        
        # Show preview
        self.license_preview.setPlainText(json.dumps(license_payload, indent=4))
        
        # Save to file
        file_path, _ = QFileDialog.getSaveFileName(self, "Save License File", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(license_payload, f, indent=4)
            QMessageBox.information(self, "Success", "License file saved successfully!")
    
    def update_user_page(self):
        # Clear previous content
        while self.tool_selection_layout.count():
            child = self.tool_selection_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # License status
        if self.license_valid and self.license_expiry:
            expiry_date = datetime.strptime(self.license_expiry, "%Y-%m-%d")
            days_left = (expiry_date - datetime.now()).days
            self.license_status_label.setText(f"📅 License valid till: {expiry_date.strftime('%d %b %Y')}")
            
            if days_left <= 7:
                QMessageBox.warning(self, "Warning", f"⚠️ License expires in {days_left} day(s)")
        else:
            self.license_status_label.setText("⚠️ License not activated or expired")
            self.show_license_upload()
            return
        
        # Tool selection
        all_tools = {
            "📁 Single File Filter": "Tool1",
            "📂 Dual File Filter": "Tool2",
            "📊 Exact Match Comparator": "Tool3",
            "🔍 Contains Match Comparator": "Tool4"
        }
        
        allowed_tools = {name: key for name, key in all_tools.items() if key in self.license_features}
        
        if not allowed_tools:
            QMessageBox.warning(self, "Warning", "⚠️ No tools enabled in your license.")
            return
        
        # Create tool buttons
        for tool_name, tool_key in allowed_tools.items():
            btn = QPushButton(tool_name)
            btn.clicked.connect(lambda _, key=tool_key: self.show_tool(key))
            self.tool_selection_layout.addWidget(btn)
    
    def show_license_upload(self):
        # Clear previous content
        while self.tool_selection_layout.count():
            child = self.tool_selection_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add license upload UI
        self.tool_selection_layout.addWidget(QLabel("Please upload your activation key:"))
        
        self.license_upload_btn = QPushButton("Upload Activation Key JSON")
        self.license_upload_btn.clicked.connect(self.upload_license_file)
        self.tool_selection_layout.addWidget(self.license_upload_btn)
    
    def upload_license_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open License File", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    license_data = json.load(f)
                
                valid, result = LicenseGate.validate_license_file(license_data)
                if valid:
                    self.license_valid = True
                    self.license_features = result["features"]
                    self.license_expiry = result["valid_till"]
                    QMessageBox.information(self, "Success", "✅ License activated successfully!")
                    self.update_user_page()
                else:
                    QMessageBox.warning(self, "Invalid License", f"❌ {result}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading license file: {e}")
    
    def show_tool(self, tool_key):
        if tool_key in self.tool_pages:
            self.stacked_widget.setCurrentWidget(self.tool_pages[tool_key])

# =============================================
# Apply Styles
# =============================================
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                margin: 5px;
            }
            QPushButton {
                padding: 8px;
                margin: 5px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLineEdit, QTextEdit, QComboBox, QListWidget, QSpinBox {
                padding: 8px;
                margin: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QTableWidget {
                margin: 5px;
                border: 1px solid #ddd;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QWidget#footer {
                background-color: white;
                border-top: 1px solid #eee;
                padding: 10px;
            }
        """)

# =============================================
# Application Entry Point
# =============================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set window icon
    logo_path = resource_path(os.path.join("assets", "consulta_logo.png"))
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())