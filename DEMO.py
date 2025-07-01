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
                             QFrame, QButtonGroup, QSpinBox, QTabWidget, QComboBox)
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
# Tool Modules (Improved UI Versions)
# =============================================
class BaseToolWidget(QWidget):
    """Base class for all tools with common UI elements"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # Tool title
        self.title_label = QLabel(self.get_tool_name())
        self.title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px 0;
        """)
        self.main_layout.addWidget(self.title_label)
        
        # Description
        self.desc_label = QLabel(self.get_tool_description())
        self.desc_label.setStyleSheet("color: #7f8c8d;")
        self.desc_label.setWordWrap(True)
        self.main_layout.addWidget(self.desc_label)
        
        # Horizontal line
        self.add_separator()
        
        # Setup tool-specific UI
        self.setup_tool_ui()
        
    def get_tool_name(self):
        return "Base Tool"
        
    def get_tool_description(self):
        return "Tool description goes here"
        
    def setup_tool_ui(self):
        pass
        
    def add_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #ecf0f1;")
        self.main_layout.addWidget(line)
        
    def create_form_row(self, label_text, widget):
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(200)
        label.setStyleSheet("padding: 5px;")
        row.addWidget(label)
        row.addWidget(widget)
        self.main_layout.addLayout(row)
        return row
        
    def create_button(self, text, callback=None, style="primary"):
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
                    min-width: 100px;
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
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #27ae60;
                }
            """)
        elif style == "danger":
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            
        return btn
        
    def create_table(self):
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
        table.setSelectionMode(QTableWidget.SingleSelection)
        return table
        
    def show_data_in_table(self, table, df):
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns.tolist())
        
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                table.setItem(row, col, QTableWidgetItem(str(df.iloc[row, col])))
        
        table.resizeColumnsToContents()

class CSVExcelFilterTool(BaseToolWidget):
    def get_tool_name(self):
        return "CSV/Excel Filter Tool"
        
    def get_tool_description(self):
        return "Filter data from CSV or Excel files based on column values and display selected columns"
        
    def setup_tool_ui(self):
        # File Upload Section
        upload_group = QGroupBox("File Upload")
        upload_layout = QVBoxLayout()
        
        self.file_upload_btn = self.create_button("Upload CSV/Excel File", self.upload_file)
        upload_layout.addWidget(self.file_upload_btn)
        
        self.file_info_label = QLabel("No file selected")
        self.file_info_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        upload_layout.addWidget(self.file_info_label)
        
        self.sheet_combo = QComboBox()
        self.sheet_combo.hide()
        upload_layout.addWidget(self.sheet_combo)
        
        upload_group.setLayout(upload_layout)
        self.main_layout.addWidget(upload_group)
        
        # Filter Configuration Section
        config_group = QGroupBox("Filter Configuration")
        config_layout = QVBoxLayout()
        
        # Filter Column Selection
        self.filter_col_combo = QComboBox()
        self.create_form_row("Filter Column:", self.filter_col_combo)
        
        # Filter Values
        self.filter_values_input = QLineEdit()
        self.create_form_row("Filter Values (comma separated):", self.filter_values_input)
        
        # Display Columns
        self.display_cols_list = QListWidget()
        self.display_cols_list.setSelectionMode(QListWidget.MultiSelection)
        self.create_form_row("Columns to Display:", self.display_cols_list)
        
        config_group.setLayout(config_layout)
        self.main_layout.addWidget(config_group)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        self.apply_filter_btn = self.create_button("Apply Filter", self.apply_filter, "primary")
        btn_layout.addWidget(self.apply_filter_btn)
        self.main_layout.addLayout(btn_layout)
        
        # Results Section
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        self.results_table = self.create_table()
        results_layout.addWidget(self.results_table)
        results_group.setLayout(results_layout)
        self.main_layout.addWidget(results_group)
        
        # Preview Section
        preview_group = QGroupBox("Data Preview")
        preview_layout = QVBoxLayout()
        self.preview_table = self.create_table()
        preview_layout.addWidget(self.preview_table)
        preview_group.setLayout(preview_layout)
        self.main_layout.addWidget(preview_group)
        
    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Excel/CSV Files (*.xlsx *.csv)")
        if file_path:
            self.file_info_label.setText(f"Selected: {os.path.basename(file_path)}")
            
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
            QMessageBox.warning(self, "Warning", "Please enter at least one value to filter.")
            return
            
        filtered_df = self.current_df[self.current_df[filter_col].astype(str).isin(filter_values)]
        
        selected_cols = [item.text() for item in self.display_cols_list.selectedItems()]
        if not selected_cols:
            selected_cols = self.current_df.columns.tolist()
        
        self.show_data_in_table(self.results_table, filtered_df[selected_cols])
        QMessageBox.information(self, "Success", f"Found {len(filtered_df)} matching row(s)")

# class DualExcelFilterTool(BaseTool):
#     """Tool for filtering data across two Excel files"""
#     def __init__(self):
#         super().__init__("Dual Excel Filter", 
#                         "Compare and filter data between two Excel files")
#         self.setup_tool_ui()

#     def setup_tool_ui(self):
#         # File Upload Section
#         self.create_file_upload_section()
        
#         # Sheet Selection
#         self.create_sheet_selection()
        
#         # Filter Configuration
#         self.create_filter_configuration()
        
#         # Results Display
#         self.create_results_section()

#     def create_file_upload_section(self):
#         # [Implementation similar to original Tool2 but using BaseTool methods]
#         # ... create file upload widgets and layouts ...
    
#     def create_sheet_selection(self):
#         # [Implementation for sheet selection]
#         # ... create sheet combo boxes ...
    
#     def create_filter_configuration(self):
#         # [Implementation for filter configuration]
#         # ... create filter widgets and logic ...
    
#     def create_results_section(self):
#         # [Implementation for results display]
#         # ... create tables and output widgets ...



# class ExcelComparatorTool(BaseTool):
#     """Tool for comparing Excel files with exact matching"""
#     def __init__(self):
#         super().__init__("Excel Comparator", 
#                         "Compare two Excel files with exact or case-insensitive matching")
#         self.setup_tool_ui()

#     def setup_tool_ui(self):
#         # File Upload
#         self.create_file_upload()
        
#         # Matching Options
#         self.create_matching_options()
        
#         # Results Display
#         self.create_results_display()
    
#     def create_file_upload(self):
#         # [Implementation for file upload]
#         # ... similar to previous tools ...
    
#     def create_matching_options(self):
#         # [Implementation for matching type selection]
#         # ... radio buttons for exact/case-insensitive matching ...
    
#     def create_results_display(self):
#         # [Implementation for results tables]
#         # ... tables for comparison results ...


# class PartialMatchTool(BaseTool):
#     """Tool for finding partial matches between files"""
#     def __init__(self):
#         super().__init__("Partial Match Finder", 
#                         "Find partial matches (contains) between two Excel files")
#         self.setup_tool_ui()

#     def setup_tool_ui(self):
#         # File Input Section
#         self.create_file_inputs()
        
#         # Comparison Configuration
#         self.create_comparison_config()
        
#         # Results Management
#         self.create_results_management()
    
#     def create_file_inputs(self):
#         # [Implementation for file inputs]
#         # ... file selection widgets ...
    
#     def create_comparison_config(self):
#         # [Implementation for comparison settings]
#         # ... column selection and matching options ...
    
#     def create_results_management(self):
#         # [Implementation for results display and export]
#         # ... tables and export buttons ...

# =============================================
# Main Application Window (Improved)
# =============================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.logged_in = False
        self.username = ""
        self.license_valid = False
        self.license_features = []
        self.license_expiry = ""
        
        self.USER_CREDENTIALS = {
            "CONSULTA": "Consulta@123",
            "DEMO": "Demo@123"
        }
        
        self.TOOL_RUNNERS = {
            "Tool1": CSVExcelFilterTool,
            # Add other tools here following the same pattern
        }
        
        self.init_ui()
        self.setWindowProperties()
    
    def setWindowProperties(self):
        self.setWindowTitle("PCS7 TurboSift - Data Processing Toolkit")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set window icon if available
        icon_path = resource_path("assets/LOGO.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
    
    def init_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout()
        central_widget.setLayout(self.main_layout)
        
        # Create application header
        self.create_header()
        
        # Create main content area
        self.create_content_area()
        
        # Create footer
        self.create_footer()
        
        # Create all pages
        self.create_pages()
        
        # Apply styles
        self.apply_styles()
    
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