import sys
import os
import json
import hashlib
import platform
import uuid
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QStackedWidget, QFileDialog,
                             QMessageBox, QComboBox, QCheckBox, QTextEdit, QTableWidget,
                             QTableWidgetItem, QGroupBox, QRadioButton, QListWidget,
                             QFrame, QButtonGroup, QSpinBox, QTabWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
import pandas as pd

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
        """Generate a unique machine ID based on system characteristics"""
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
        """Validate license file with robust error checking"""
        required_fields = ["machine_id", "valid_till", "features"]
        for field in required_fields:
            if field not in license_data:
                return False, f"License missing required field: {field}"

        try:
            machine_id = license_data["machine_id"]
            valid_till = license_data["valid_till"]
            features = license_data.get("features", [])

            if not isinstance(features, list):
                return False, "Features must be a list"

            if machine_id != LicenseGate.get_machine_id():
                return False, "License is not valid for this machine."

            expiry_date = datetime.strptime(valid_till, "%Y-%m-%d")
            if expiry_date < datetime.now():
                return False, f"License expired on {valid_till}"

            return True, {
                "features": features,
                "valid_till": expiry_date.strftime("%Y-%m-%d")
            }
        except ValueError as e:
            return False, f"Invalid date format in license: {str(e)}"
        except Exception as e:
            return False, f"License validation error: {str(e)}"

# =============================================
# Base Tool Class (Improved)
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

    def create_form_row(self, label_text, widget, parent_layout=None):
        """Standardized method to create form rows"""
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(150)
        row.addWidget(label)
        row.addWidget(widget)
        
        target_layout = parent_layout if parent_layout else self.layout
        target_layout.addLayout(row)
        return row

    def create_button(self, text, callback=None, style="primary"):
        """Create a styled button with consistent sizing"""
        btn = QPushButton(text)
        btn.setMinimumHeight(30)
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
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:disabled {
                    background-color: #bdc3c7;
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
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #27ae60;
                }
            """)
        return btn

    def create_table(self):
        """Create a styled table widget with consistent appearance"""
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
        table.setSelectionBehavior(QTableWidget.SelectRows)
        return table

    def show_dataframe(self, table, df):
        """Safely display pandas DataFrame in QTableWidget"""
        if df.empty:
            table.clear()
            table.setRowCount(0)
            table.setColumnCount(0)
            return

        try:
            table.setRowCount(df.shape[0])
            table.setColumnCount(df.shape[1])
            table.setHorizontalHeaderLabels(df.columns.tolist())
            
            for row in range(df.shape[0]):
                for col in range(df.shape[1]):
                    value = str(df.iloc[row, col]) if not pd.isna(df.iloc[row, col]) else ""
                    item = QTableWidgetItem(value)
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    table.setItem(row, col, item)
            
            table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to display data: {str(e)}")

# =============================================
# Consolidated Excel Comparison Tool
# =============================================
class ExcelComparisonTool(BaseTool):
    def __init__(self):
        super().__init__("Excel Comparison Tool", 
                        "Compare and analyze data between Excel files with various matching options")
        self.df1_dict = {}
        self.df2_dict = {}
        self.df1 = None
        self.df2 = None
        self.result_df = pd.DataFrame()
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components"""
        # File Upload Section
        self.create_file_upload_section()
        
        # Sheet Selection
        self.create_sheet_selection()
        
        # Comparison Configuration
        self.create_comparison_config()
        
        # Results Display
        self.create_results_section()
        
        # Final Output
        self.create_output_section()

    def create_file_upload_section(self):
        """Create file upload widgets"""
        files_group = QGroupBox("File Upload")
        files_layout = QVBoxLayout()
        
        # File 1
        file1_layout = QHBoxLayout()
        self.file1_btn = self.create_button("Select File 1", lambda: self.handle_upload(1))
        file1_layout.addWidget(self.file1_btn)
        self.file1_label = QLabel("No file selected")
        self.file1_label.setStyleSheet("color: #7f8c8d;")
        file1_layout.addWidget(self.file1_label)
        files_layout.addLayout(file1_layout)
        
        # File 2
        file2_layout = QHBoxLayout()
        self.file2_btn = self.create_button("Select File 2", lambda: self.handle_upload(2))
        file2_layout.addWidget(self.file2_btn)
        self.file2_label = QLabel("No file selected")
        self.file2_label.setStyleSheet("color: #7f8c8d;")
        file2_layout.addWidget(self.file2_label)
        files_layout.addLayout(file2_layout)
        
        files_group.setLayout(files_layout)
        self.layout.addWidget(files_group)

    def create_sheet_selection(self):
        """Create sheet selection widgets"""
        sheets_group = QGroupBox("Sheet Selection")
        sheets_layout = QVBoxLayout()
        
        # File 1 Sheet
        self.sheet1_combo = QComboBox()
        self.create_form_row("File 1 Sheet:", self.sheet1_combo, sheets_layout)
        
        # File 2 Sheet
        self.sheet2_combo = QComboBox()
        self.create_form_row("File 2 Sheet:", self.sheet2_combo, sheets_layout)
        
        sheets_group.setLayout(sheets_layout)
        self.layout.addWidget(sheets_group)
        
        # Connect signals
        self.sheet1_combo.currentTextChanged.connect(lambda: self.update_df(1))
        self.sheet2_combo.currentTextChanged.connect(lambda: self.update_df(2))

    def create_comparison_config(self):
        """Create comparison configuration widgets"""
        config_group = QGroupBox("Comparison Configuration")
        config_layout = QVBoxLayout()
        
        # Column Selection
        self.col1_combo = QComboBox()
        self.create_form_row("File 1 Column:", self.col1_combo, config_layout)
        
        self.col2_combo = QComboBox()
        self.create_form_row("File 2 Column:", self.col2_combo, config_layout)
        
        # Match Type
        self.match_type_group = QButtonGroup()
        exact_match = QRadioButton("Exact Match")
        case_insensitive = QRadioButton("Case-insensitive")
        partial_match = QRadioButton("Partial Match")
        
        self.match_type_group.addButton(exact_match)
        self.match_type_group.addButton(case_insensitive)
        self.match_type_group.addButton(partial_match)
        exact_match.setChecked(True)
        
        match_layout = QHBoxLayout()
        match_layout.addWidget(QLabel("Match Type:"))
        match_layout.addWidget(exact_match)
        match_layout.addWidget(case_insensitive)
        match_layout.addWidget(partial_match)
        config_layout.addLayout(match_layout)
        
        # Compare Button
        self.compare_btn = self.create_button("Compare Files", self.compare_files, "primary")
        config_layout.addWidget(self.compare_btn)
        
        config_group.setLayout(config_layout)
        self.layout.addWidget(config_group)

    def create_results_section(self):
        """Create results display widgets"""
        results_group = QGroupBox("Comparison Results")
        results_layout = QVBoxLayout()
        
        self.result_label = QLabel()
        self.result_label.setStyleSheet("font-weight: bold;")
        results_layout.addWidget(self.result_label)
        
        self.results_table = self.create_table()
        results_layout.addWidget(self.results_table)
        
        results_group.setLayout(results_layout)
        self.layout.addWidget(results_group)

    def create_output_section(self):
        """Create output configuration widgets"""
        output_group = QGroupBox("Output Configuration")
        output_layout = QVBoxLayout()
        
        # Column Selection
        self.output_cols_list = QListWidget()
        self.output_cols_list.setSelectionMode(QListWidget.MultiSelection)
        self.create_form_row("Select Output Columns:", self.output_cols_list, output_layout)
        
        # Update and Export Buttons
        btn_layout = QHBoxLayout()
        self.update_btn = self.create_button("Update Output", self.update_output)
        self.export_btn = self.create_button("Export Results", self.export_results, "success")
        
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(self.export_btn)
        output_layout.addLayout(btn_layout)
        
        # Final Output Table
        self.final_table = self.create_table()
        output_layout.addWidget(self.final_table)
        
        output_group.setLayout(output_layout)
        self.layout.addWidget(output_group)

    def handle_upload(self, file_num):
        """Handle file upload with error checking"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Open File {file_num}", "", 
            "Excel Files (*.xlsx *.xls);;CSV Files (*.csv)")
        
        if not file_path:
            return
            
        try:
            if file_num == 1:
                self.file1_label.setText(os.path.basename(file_path))
                if file_path.endswith('.csv'):
                    self.df1_dict = {"CSV Data": pd.read_csv(file_path)}
                else:
                    self.df1_dict = pd.read_excel(file_path, sheet_name=None)
                
                self.sheet1_combo.clear()
                self.sheet1_combo.addItems(list(self.df1_dict.keys()))
                self.df1 = self.df1_dict[self.sheet1_combo.currentText()]
            else:
                self.file2_label.setText(os.path.basename(file_path))
                if file_path.endswith('.csv'):
                    self.df2_dict = {"CSV Data": pd.read_csv(file_path)}
                else:
                    self.df2_dict = pd.read_excel(file_path, sheet_name=None)
                
                self.sheet2_combo.clear()
                self.sheet2_combo.addItems(list(self.df2_dict.keys()))
                self.df2 = self.df2_dict[self.sheet2_combo.currentText()]
            
            self.update_column_combos()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")

    def update_df(self, df_num):
        """Update the current dataframe when sheet changes"""
        try:
            if df_num == 1 and self.sheet1_combo.currentText() in self.df1_dict:
                self.df1 = self.df1_dict[self.sheet1_combo.currentText()]
            elif df_num == 2 and self.sheet2_combo.currentText() in self.df2_dict:
                self.df2 = self.df2_dict[self.sheet2_combo.currentText()]
            
            self.update_column_combos()
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to update data:\n{str(e)}")

    def update_column_combos(self):
        """Update column selection comboboxes"""
        if self.df1 is not None:
            self.col1_combo.clear()
            self.col1_combo.addItems(self.df1.columns.astype(str).tolist())
        
        if self.df2 is not None:
            self.col2_combo.clear()
            self.col2_combo.addItems(self.df2.columns.astype(str).tolist())

    def compare_files(self):
        """Compare files based on selected options"""
        if self.df1 is None or self.df2 is None:
            QMessageBox.warning(self, "Warning", "Please upload both files first.")
            return
            
        col1 = self.col1_combo.currentText()
        col2 = self.col2_combo.currentText()
        match_type = self.match_type_group.checkedButton().text()
        
        try:
            df1 = self.df1.copy()
            df2 = self.df2.copy()
            
            if match_type == "Exact Match":
                # Standard exact match merge
                self.result_df = pd.merge(
                    df1, df2,
                    left_on=col1, right_on=col2,
                    how='inner'
                )
            elif match_type == "Case-insensitive":
                # Case-insensitive match
                df1["__merge_key__"] = df1[col1].astype(str).str.lower()
                df2["__merge_key__"] = df2[col2].astype(str).str.lower()
                self.result_df = pd.merge(
                    df1, df2,
                    on="__merge_key__",
                    how='inner'
                ).drop(columns=["__merge_key__"])
            else:  # Partial Match
                # Find rows where one value contains the other
                df1["__cmp__"] = df1[col1].astype(str).str.lower()
                df2["__cmp__"] = df2[col2].astype(str).str.lower()
                
                matched_rows = []
                for _, row1 in df1.iterrows():
                    val1 = row1["__cmp__"]
                    matches = df2[df2["__cmp__"].str.contains(val1, na=False)]
                    for _, row2 in matches.iterrows():
                        combined = pd.concat([row1.drop("__cmp__"), row2.drop("__cmp__")])
                        matched_rows.append(combined)
                
                self.result_df = pd.DataFrame(matched_rows) if matched_rows else pd.DataFrame()
            
            # Update results display
            self.show_dataframe(self.results_table, self.result_df)
            self.result_label.setText(f"Found {len(self.result_df)} matching rows")
            
            # Update output columns list
            self.output_cols_list.clear()
            if not self.result_df.empty:
                self.output_cols_list.addItems(self.result_df.columns.tolist())
                # Select all columns by default
                for i in range(self.output_cols_list.count()):
                    self.output_cols_list.item(i).setSelected(True)
            
            self.update_output()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Comparison failed:\n{str(e)}")

    def update_output(self):
        """Update the final output table based on selected columns"""
        if self.result_df.empty:
            self.show_dataframe(self.final_table, pd.DataFrame())
            return
            
        selected_cols = [item.text() for item in self.output_cols_list.selectedItems()]
        if not selected_cols:  # If nothing selected, show all
            selected_cols = self.result_df.columns.tolist()
            
        try:
            output_df = self.result_df[selected_cols]
            self.show_dataframe(self.final_table, output_df)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to update output:\n{str(e)}")

    def export_results(self):
        """Export the final results to CSV"""
        if self.result_df.empty:
            QMessageBox.warning(self, "Warning", "No results to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Results", "", 
            "CSV Files (*.csv)")
            
        if not file_path:
            return
            
        try:
            selected_cols = [item.text() for item in self.output_cols_list.selectedItems()]
            output_df = self.result_df[selected_cols] if selected_cols else self.result_df
            output_df.to_csv(file_path, index=False)
            QMessageBox.information(self, "Success", "Results exported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export results:\n{str(e)}")

# =============================================
# CSV/Excel Filter Tool (Improved)
# =============================================
class CSVExcelFilterTool(BaseTool):
    def __init__(self):
        super().__init__("CSV/Excel Filter", "Filter data from CSV or Excel files based on column values")

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
        self.create_form_row("Filter Column:", self.filter_col_combo, config_layout)
        
        self.filter_values = QLineEdit()
        self.filter_values.setPlaceholderText("Enter values separated by commas")
        self.create_form_row("Filter Values:", self.filter_values, config_layout)
        
        self.display_cols = QListWidget()
        self.display_cols.setSelectionMode(QListWidget.MultiSelection)
        self.create_form_row("Columns to Display:", self.display_cols, config_layout)
        
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

        # Connect signals
        self.sheet_combo.currentTextChanged.connect(self.update_sheet)

    def handle_upload(self):
        """Handle file upload with error checking"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", 
            "Excel/CSV Files (*.xlsx *.csv)")
        
        if not file_path:
            return
            
        try:
            self.file_label.setText(f"Selected: {os.path.basename(file_path)}")
            
            if file_path.endswith('.xlsx'):
                self.df_dict = pd.read_excel(file_path, sheet_name=None)
                self.sheet_combo.clear()
                self.sheet_combo.addItems(list(self.df_dict.keys()))
                self.sheet_combo.show()
                self.current_df = self.df_dict[self.sheet_combo.currentText()]
            else:
                self.current_df = pd.read_csv(file_path)
                self.sheet_combo.hide()
            
            self.update_ui()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")

    def update_sheet(self, sheet_name):
        """Update when sheet selection changes"""
        try:
            self.current_df = self.df_dict[sheet_name]
            self.update_ui()
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to load sheet:\n{str(e)}")

    def update_ui(self):
        """Update UI with current data"""
        try:
            self.filter_col_combo.clear()
            self.filter_col_combo.addItems(self.current_df.columns.tolist())
            
            self.display_cols.clear()
            self.display_cols.addItems(self.current_df.columns.tolist())
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to update UI:\n{str(e)}")

    def apply_filter(self):
        """Apply the filter to the data with error checking"""
        if not hasattr(self, 'current_df'):
            QMessageBox.warning(self, "Warning", "Please upload a file first.")
            return
            
        filter_col = self.filter_col_combo.currentText()
        filter_values = [v.strip() for v in self.filter_values.text().split(',') if v.strip()]
        
        if not filter_values:
            QMessageBox.warning(self, "Warning", "Please enter filter values.")
            return
            
        try:
            # Convert both to string for comparison to handle mixed types
            filtered_df = self.current_df[
                self.current_df[filter_col].astype(str).str.lower().isin(
                    [v.lower() for v in filter_values]
                )
            ]
            
            selected_cols = [item.text() for item in self.display_cols.selectedItems()]
            if not selected_cols:  # If none selected, show all
                selected_cols = self.current_df.columns.tolist()
            
            self.show_dataframe(self.results_table, filtered_df[selected_cols])
            QMessageBox.information(
                self, "Success", 
                f"Found {len(filtered_df)} matching rows\n"
                f"Showing {len(selected_cols)} of {len(self.current_df.columns)} columns"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Filtering failed:\n{str(e)}")

# =============================================
# Main Application Window (Improved)
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
        
        # Available tools with complete descriptions
        self.TOOL_RUNNERS = {
            "CSV/Excel Filter": CSVExcelFilterTool,
            "Dual Excel Filter": DualExcelFilterTool,
            "Excel Comparator": ExcelComparatorTool,
            "Partial Match Finder": PartialMatchTool
        }
        
        self.TOOL_DESCRIPTIONS = {
            "CSV/Excel Filter": "Filter data from CSV or Excel files based on column values",
            "Excel Comparison": "Compare Excel files with multiple matching options:\n"
                            "- Exact match\n"
                            "- Case-insensitive match\n"
                            "- Partial match"
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
        # Removed update_sidebar() call as it wasn't implemented

    def create_header(self):
        """Create the application header with logo and login status"""
        header = QWidget()
        header.setObjectName("appHeader")
        header_layout = QHBoxLayout()
        header.setLayout(header_layout)
        
        # Logo (with fallback to text)
        logo_label = QLabel()
        try:
            logo_pixmap = QPixmap(resource_path("assets/consulta_logo.png"))
            if not logo_pixmap.isNull():
                logo_label.setPixmap(logo_pixmap.scaledToHeight(40, Qt.SmoothTransformation))
            else:
                raise FileNotFoundError
        except:
            logo_label.setText("PCS7 TurboSift")
            logo_label.setStyleSheet("color: white; font-weight: bold;")
        
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
        """Create the main content area with stacked widget"""
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

    def create_footer(self):
        """Create the application footer"""
        footer = QWidget()
        footer.setObjectName("appFooter")
        footer_layout = QHBoxLayout()
        footer.setLayout(footer_layout)
        
        # Copyright notice
        copyright = QLabel("© 2023 CONSULTA TECHNOLOGIES PVT LTD. All Rights Reserved.")
        footer_layout.addWidget(copyright, alignment=Qt.AlignLeft)
        
        # Support info
        support = QLabel("Support: support@consulta.com")
        footer_layout.addWidget(support, alignment=Qt.AlignCenter)
        
        # Version info
        version = QLabel("Version 1.0.0")
        footer_layout.addWidget(version, alignment=Qt.AlignRight)
        
        self.main_layout.addWidget(footer)

    def create_pages(self):
        """Create all application pages"""
        self.create_login_page()
        self.create_admin_page()
        self.create_user_page()
        self.create_tool_pages()
        
        # Show login page initially
        self.stacked_widget.setCurrentIndex(0)

    def create_login_page(self):
        """Create the login page"""
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
        """Create the admin dashboard page"""
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
        self.features_list.addItems(list(self.TOOL_RUNNERS.keys()))
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

    def create_user_page(self):
        """Create the user dashboard page"""
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
        """Create pages for all available tools"""
        self.tool_pages = {}
        for tool_name, tool_class in self.TOOL_RUNNERS.items():
            try:
                tool_page = tool_class()
                self.tool_pages[tool_name] = tool_page
                self.stacked_widget.addWidget(tool_page)
            except Exception as e:
                print(f"Failed to initialize tool {tool_name}: {str(e)}")

    def toggle_password_visibility(self, state):
        """Toggle password field visibility"""
        if state == Qt.Checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def handle_login(self):
        """Handle login attempt"""
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
        """Generate a new license file"""
        expiry_days = self.expiry_days_input.value()
        selected_features = [item.text() for item in self.features_list.selectedItems()]
        
        if not selected_features:
            QMessageBox.warning(self, "Warning", "Please select at least one feature")
            return
            
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
                QMessageBox.critical(self, "Error", f"Failed to save license file:\n{str(e)}")

    def update_user_page(self):
        """Update the user page based on current state"""
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
        """Update the list of available tools based on license"""
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
        for tool_name in self.license_features:
            if tool_name in self.TOOL_RUNNERS:
                tool_btn = QPushButton(self.TOOL_DESCRIPTIONS.get(tool_name, tool_name))
                tool_btn.setToolTip(f"Launch {tool_name}")
                tool_btn.clicked.connect(lambda _, name=tool_name: self.show_tool(name))
                self.tools_layout.addWidget(tool_btn)
        
        # Add stretch to push buttons to top
        self.tools_layout.addStretch()

    def show_license_upload(self):
        """Show dialog to upload license file"""
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
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Error", "Invalid JSON file format")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load license file:\n{str(e)}")

    def show_tool(self, tool_name):
        """Show the specified tool page"""
        if tool_name in self.tool_pages:
            self.stacked_widget.setCurrentWidget(self.tool_pages[tool_name])

    def create_form_row(self, layout, label_text, widget):
        """Helper method to create consistent form rows"""
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(200)
        row.addWidget(label)
        row.addWidget(widget)
        layout.addLayout(row)

    def apply_styles(self):
        """Apply consistent styling across the application"""
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
            
            .pageTitle {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 15px;
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