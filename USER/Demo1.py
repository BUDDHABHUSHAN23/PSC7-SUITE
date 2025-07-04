import sys
import json
from datetime import datetime, timedelta
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QLineEdit,
    QPushButton, QCheckBox, QFileDialog, QMessageBox, QComboBox,
    QHBoxLayout, QStackedWidget, QTextEdit, QListWidget, QSplitter, 
    QListWidgetItem, QAbstractItemView, QFrame, QSpacerItem, QSizePolicy,
    QDialog, QDialogButtonBox, QGridLayout
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

from license_gate import validate_license_file, get_machine_id
from tools.tool1_ui import Tool1UI
from tools.tool2_ui import Tool2UI
from tools.tool3_ui import Tool3UI
from tools.tool4_ui import Tool4UI

from security.secure_license_system import (
    save_encrypted_license,
    load_encrypted_license,
    validate_license_file,
    delete_saved_license,
    get_valid_license_on_start
)


def resource_path(relative_path):
    """ Get path to resource whether in development or PyInstaller bundle """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)


class LicenseDetailsDialog(QDialog):
    def __init__(self, license_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("License Details")
        self.setWindowIcon(QIcon(resource_path("assets/info.png")))
        self.resize(500, 300)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Current License Information")
        header.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(header)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)
        
        # License details grid
        grid = QGridLayout()
        grid.setSpacing(10)
        
        details = [
            ("Issued On:", license_data.get("issued_on", "N/A")),
            ("Valid Until:", license_data.get("valid_till", "N/A")),
            ("Enabled Features:", ", ".join(license_data.get("features", []))),
            ("License Type:", "Full" if len(license_data.get("features", [])) == 4 else "Partial")
        ]
        
        for row, (label, value) in enumerate(details):
            lbl = QLabel(label)
            lbl.setFont(QFont('Arial', 10, QFont.Bold))
            val = QLabel(value)
            val.setFont(QFont('Arial', 10))
            grid.addWidget(lbl, row, 0)
            grid.addWidget(val, row, 1)
        
        layout.addLayout(grid)
        
        # Warning if license is near expiry
        expiry_date = license_data.get("valid_till")
        if expiry_date:
            try:
                expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
                days_left = (expiry - datetime.now()).days
                if days_left <= 7:
                    warning = QLabel(f"⚠️ License expires in {days_left} day(s)!")
                    warning.setStyleSheet("color: #e74c3c; font-weight: bold;")
                    layout.addWidget(warning)
            except ValueError:
                pass
        
        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(self.close)
        layout.addWidget(btn_box)
        self.setLayout(layout)


class LicenseManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("License Management")
        self.setWindowIcon(QIcon(resource_path("assets/license.png")))
        self.resize(500, 300)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("License Management")
        header.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(header)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)
        
        # Current license status
        self.status_label = QLabel()
        self.status_label.setFont(QFont('Arial', 10))
        layout.addWidget(self.status_label)
        
        # Initialize buttons first
        self.view_btn = QPushButton("View Details")
        self.view_btn.setIcon(QIcon(resource_path("assets/info.png")))
        self.view_btn.clicked.connect(self.view_license_details)
        
        self.upload_btn = QPushButton("Upload New")
        self.upload_btn.setIcon(QIcon(resource_path("assets/upload.png")))
        self.upload_btn.clicked.connect(self.upload_license)
        
        self.delete_btn = QPushButton("Remove License")
        self.delete_btn.setIcon(QIcon(resource_path("assets/delete.png")))
        self.delete_btn.clicked.connect(self.delete_license)
        self.delete_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        
        # Action buttons layout
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.view_btn)
        btn_layout.addWidget(self.upload_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)
        
        # Close button
        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(self.close)
        layout.addWidget(btn_box)
        
        self.setLayout(layout)
        
        # Now update status which will use the buttons
        self.update_status()
    
    def update_status(self):
        license_data = load_encrypted_license()
        if license_data:
            expiry_date = license_data.get("valid_till", "N/A")
            features = license_data.get("features", [])
            self.status_label.setText(
                f"Current License: {len(features)} tools enabled\n"
                f"Valid until: {expiry_date}"
            )
            self.delete_btn.setEnabled(True)
            self.view_btn.setEnabled(True)
        else:
            self.status_label.setText("No active license found")
            self.delete_btn.setEnabled(False)
            self.view_btn.setEnabled(False)
    
    def view_license_details(self):
        license_data = load_encrypted_license()
        if license_data:
            dialog = LicenseDetailsDialog(license_data, self)
            dialog.exec_()
    
    def upload_license(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select License File", 
            "", 
            "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, "r") as f:
                    license_data = json.load(f)
                
                # Validate before saving
                valid, result = validate_license_file(license_data)
                if not valid:
                    QMessageBox.critical(self, "Invalid License", result)
                    return
                
                # Confirm license change
                reply = QMessageBox.question(
                    self, 'Confirm License Change',
                    'Are you sure you want to replace your current license?',
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    if save_encrypted_license(license_data):
                        QMessageBox.information(self, "Success", "License updated successfully!")
                        self.parent().license_updated()
                        self.update_status()
                    else:
                        QMessageBox.critical(self, "Error", "Failed to save license.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to process license file:\n{str(e)}")
    
    def delete_license(self):
        license_data = load_encrypted_license()
        if not license_data:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 'Confirm License Removal',
            'Are you sure you want to remove your current license?\n'
            'This will disable all premium features.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if delete_saved_license():
                QMessageBox.information(self, "Success", "License removed successfully!")
                self.parent().license_updated()
                self.update_status()
            else:
                QMessageBox.critical(self, "Error", "Failed to remove license.")


class LoginWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header
        header = QLabel("Welcome to Consulta Solution PCS7 Suite")
        header.setFont(QFont('Arial', 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Input fields
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setStyleSheet("padding: 8px; border-radius: 4px;")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("padding: 8px; border-radius: 4px;")
        
        self.show_pass = QCheckBox("Show Password")
        self.show_pass.stateChanged.connect(
            lambda: self.password_input.setEchoMode(
                QLineEdit.Normal if self.show_pass.isChecked() else QLineEdit.Password
            )
        )
        
        # Login button
        self.login_btn = QPushButton("Login")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)

        # Add widgets to layout
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.show_pass)
        layout.addSpacing(10)
        layout.addWidget(self.login_btn)
        
        # Add vertical spacer to center the form
        layout.addStretch(1)
        
        self.setLayout(layout)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if username in self.parent.USER_CREDENTIALS and self.parent.USER_CREDENTIALS[username] == password:
            self.parent.username = username
            self.parent.logged_in = True
            self.parent.post_login()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")


class MainApp(QMainWindow):
    USER_CREDENTIALS = {
        "CONSULTA": "Consulta@123",
        "DEMO": "Demo@123"
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCS7 TurboSift")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon(resource_path("assets/LOGO.ico")))
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QListWidget {
                background-color: #2c3e50;
                color: white;
                border: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #34495e;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QLabel {
                font-size: 14px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)

        self.username = ""
        self.logged_in = False
        self.license_valid = False
        self.license_features = []
        self.license_expiry = ""
        self.tool_widgets = {}

        # Main stacked widget
        self.stack = QStackedWidget()
        
        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setIconSize(QSize(24, 24))
        
        # Add sidebar items with icons
        items = [
            ("Home", "assets/home.png"),
            ("Tool1", "assets/tool1.png"),
            ("Tool2", "assets/tool2.png"),
            ("Tool3", "assets/tool3.png"),
            ("Tool4", "assets/tool4.png"),
            ("User Manual", "assets/manual.png"),
            ("Logout", "assets/logout.png")
        ]
        
        for text, icon_path in items:
            item = QListWidgetItem(QIcon(resource_path(icon_path)), text)
            self.sidebar.addItem(item)
        
        self.sidebar.currentItemChanged.connect(self.handle_sidebar_selection)

        # Splitter for sidebar and main content
        self.splitter = QSplitter()
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.stack)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setHandleWidth(1)
        
        self.setCentralWidget(self.splitter)

        # Login widget
        self.login_widget = LoginWidget(self)
        self.stack.addWidget(self.login_widget)
        self.stack.setCurrentWidget(self.login_widget)

        # Initially disable sidebar items (except Home and Logout)
        self.update_sidebar_access()

        # Try loading existing secure license
        license_data, valid, features, expiry = get_valid_license_on_start()
        if valid:
            self.license_valid = True
            self.license_features = features
            self.license_expiry = expiry

    def post_login(self):
        # Load license info
        self.license_updated()
        
        # Enable sidebar items after login
        self.update_sidebar_access()

        if self.username == "CONSULTA":
            self.show_admin_panel()
        else:
            self.show_license_panel()
    
    def license_updated(self):
        """Called whenever license status changes"""
        license_data, valid, features, expiry = get_valid_license_on_start()
        self.license_valid = valid
        self.license_features = features
        self.license_expiry = expiry
        
        # Update status bar
        if hasattr(self, 'statusBar'):
            self.statusBar().clearMessage()
            if valid:
                self.statusBar().showMessage(
                    f"License valid until: {expiry} | "
                    f"Enabled tools: {', '.join(features)}"
                )
            else:
                self.statusBar().showMessage("⚠️ No valid license found")

    def show_admin_panel(self):
        self.admin_panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # Header
        header = QLabel(f"👋 Welcome {self.username} (Admin)")
        header.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(header)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        # License configuration
        config_group = QWidget()
        config_layout = QVBoxLayout()
        config_layout.setSpacing(15)
        
        # Expiry selection
        expiry_label = QLabel("📅 License Duration (Days)")
        expiry_label.setFont(QFont('Arial', 10, QFont.Bold))
        self.expiry_combo = QComboBox()
        self.expiry_combo.addItems(["30", "90", "180", "365"])
        self.expiry_combo.setCurrentIndex(3)
        config_layout.addWidget(expiry_label)
        config_layout.addWidget(self.expiry_combo)

        # Tools selection
        tools_label = QLabel("⚙️ Select Tools to Enable")
        tools_label.setFont(QFont('Arial', 10, QFont.Bold))
        self.tools_list = QListWidget()
        self.tools_list.setSelectionMode(QAbstractItemView.MultiSelection)
        for tool in ["Tool1", "Tool2", "Tool3", "Tool4"]:
            item = QListWidgetItem(tool)
            item.setCheckState(Qt.Checked)
            self.tools_list.addItem(item)
        config_layout.addWidget(tools_label)
        config_layout.addWidget(self.tools_list)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Output area
        output_label = QLabel("Generated License:")
        output_label.setFont(QFont('Arial', 10, QFont.Bold))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(150)
        layout.addWidget(output_label)
        layout.addWidget(self.output)

        # Generate button
        gen_btn = QPushButton("Generate License")
        gen_btn.setStyleSheet("background-color: #27ae60; color: white;")
        gen_btn.clicked.connect(self.generate_license)
        layout.addWidget(gen_btn, alignment=Qt.AlignRight)

        self.admin_panel.setLayout(layout)
        self.stack.addWidget(self.admin_panel)
        self.animated_set_current_widget(self.admin_panel)

    def show_license_panel(self):
        self.license_panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Welcome message
        welcome = QLabel(f"👋 Welcome {self.username}")
        welcome.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(welcome)

        # License management button
        license_btn = QPushButton("Manage License")
        license_btn.setIcon(QIcon(resource_path("assets/license.png")))
        license_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        license_btn.clicked.connect(self.show_license_management)
        layout.addWidget(license_btn, alignment=Qt.AlignLeft)

        if not self.license_valid:
            # License upload prompt
            upload_frame = QFrame()
            upload_frame.setFrameShape(QFrame.StyledPanel)
            upload_frame.setStyleSheet("background-color: white; padding: 20px; border-radius: 5px;")
            upload_layout = QVBoxLayout()
            
            upload_label = QLabel("Please upload your license file to continue")
            upload_label.setFont(QFont('Arial', 12))
            upload_layout.addWidget(upload_label, alignment=Qt.AlignCenter)
            
            btn = QPushButton("Upload License File")
            btn.setFixedSize(200, 40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    font-size: 14px;
                    padding: 10px 20px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            btn.clicked.connect(self.show_license_management)
            upload_layout.addWidget(btn, alignment=Qt.AlignCenter)
            
            upload_frame.setLayout(upload_layout)
            layout.addWidget(upload_frame)
        else:
            # License info section
            info_frame = QFrame()
            info_frame.setFrameShape(QFrame.StyledPanel)
            info_frame.setStyleSheet("background-color: #e8f4f8; padding: 15px; border-radius: 5px;")
            info_layout = QVBoxLayout()
            
            status = QLabel("✅ License Valid")
            status.setFont(QFont('Arial', 12, QFont.Bold))
            info_layout.addWidget(status)
            
            expiry = QLabel(f"Valid Till: {self.license_expiry}")
            expiry.setFont(QFont('Arial', 11))
            info_layout.addWidget(expiry)
            
            features = QLabel(f"Enabled Tools: {', '.join(self.license_features)}")
            features.setFont(QFont('Arial', 11))
            info_layout.addWidget(features)
            
            info_frame.setLayout(info_layout)
            layout.addWidget(info_frame)
            
            # Show available tools
            self.show_tool_buttons(layout)

        # Add logo and footer
        self.add_logo_and_footer(layout)

        self.license_panel.setLayout(layout)
        self.stack.addWidget(self.license_panel)
        self.animated_set_current_widget(self.license_panel)
    
    def show_license_management(self):
        dialog = LicenseManagementDialog(self)
        dialog.exec_()

    def show_user_manual_panel(self):
        pdf_path = resource_path("assets/user_manual.pdf")
        if os.path.exists(pdf_path):
            import webbrowser
            webbrowser.open(pdf_path)
        else:
            QMessageBox.critical(self, "Error", "User manual PDF not found.")

    def generate_license(self):
        try:
            selected_tools = []
            for i in range(self.tools_list.count()):
                if self.tools_list.item(i).checkState() == Qt.Checked:
                    selected_tools.append(self.tools_list.item(i).text())
            
            selected_days = int(self.expiry_combo.currentText())

            license_payload = {
                "machine_id": get_machine_id(),
                "issued_on": str(datetime.now()),
                "valid_till": (datetime.now() + timedelta(days=selected_days)).strftime("%Y-%m-%d"),
                "features": selected_tools
            }

            json_data = json.dumps(license_payload, indent=4)
            self.output.setPlainText(json_data)

            save_path, _ = QFileDialog.getSaveFileName(
                self, "Save License File", "activation_key.json", "JSON Files (*.json)"
            )
            if save_path:
                save_encrypted_license(license_payload)  # save encrypted copy internally
                with open(save_path, "w") as f:
                    json.dump(license_payload, f, indent=4)  # save readable version
                QMessageBox.information(self, "Saved", "License file saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred:\n{str(e)}")

    def show_tool_buttons(self, layout):
        tool_map = {
            "Tool1": (Tool1UI, "assets/tool1_large.png"),
            "Tool2": (Tool2UI, "assets/tool2_large.png"),
            "Tool3": (Tool3UI, "assets/tool3_large.png"),
            "Tool4": (Tool4UI, "assets/tool4_large.png")
        }

        tools_label = QLabel("🛠 Available Tools")
        tools_label.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(tools_label)
        
        # Add horizontal line separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        # Tools grid
        tools_grid = QWidget()
        grid_layout = QHBoxLayout()
        grid_layout.setSpacing(20)
        
        for tool_name, (tool_cls, icon_path) in tool_map.items():
            if tool_name in self.license_features:
                tool_btn = QPushButton()
                tool_btn.setFixedSize(120, 120)
                tool_btn.setStyleSheet("""
                    QPushButton {
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        background-color: white;
                    }
                    QPushButton:hover {
                        background-color: #f0f0f0;
                    }
                """)
                
                btn_layout = QVBoxLayout()
                btn_layout.setContentsMargins(10, 10, 10, 10)
                btn_layout.setSpacing(10)
                
                icon = QLabel()
                pixmap = QPixmap(resource_path(icon_path)).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon.setPixmap(pixmap)
                icon.setAlignment(Qt.AlignCenter)
                
                label = QLabel(tool_name)
                label.setAlignment(Qt.AlignCenter)
                label.setFont(QFont('Arial', 10))
                
                btn_layout.addWidget(icon)
                btn_layout.addWidget(label)
                btn_layout.addStretch()
                
                tool_btn.setLayout(btn_layout)
                tool_btn.clicked.connect(lambda _, cls=tool_cls: self.launch_tool(cls))
                grid_layout.addWidget(tool_btn)
        
        tools_grid.setLayout(grid_layout)
        layout.addWidget(tools_grid, alignment=Qt.AlignCenter)
        layout.addStretch()

    def launch_tool(self, tool_cls):
        tool_name = tool_cls.__name__
        if tool_name not in self.tool_widgets or self.tool_widgets[tool_name] is None:
            widget = tool_cls()
            self.tool_widgets[tool_name] = widget
            self.stack.addWidget(widget)

        self.animated_set_current_widget(self.tool_widgets[tool_name])

    def update_sidebar_access(self):
        for i in range(self.sidebar.count()):
            item = self.sidebar.item(i)
            if not self.logged_in:
                if item.text() in ["Home", "Logout"]:
                    item.setFlags(item.flags() | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                else:
                    item.setFlags(item.flags() & ~(Qt.ItemIsEnabled | Qt.ItemIsSelectable))
            else:
                item.setFlags(item.flags() | Qt.ItemIsEnabled | Qt.ItemIsSelectable)

    def handle_sidebar_selection(self, item):
        if not item:
            return
            
        text = item.text()
        if text == "Home":
            if self.logged_in:
                if self.username == "CONSULTA":
                    self.animated_set_current_widget(self.admin_panel)
                else:
                    self.animated_set_current_widget(self.license_panel)
            else:
                self.animated_set_current_widget(self.login_widget)  
        elif text == "Logout":
            self.logout()
        elif text in ["Tool1", "Tool2", "Tool3", "Tool4"]:
            if self.license_valid and text in self.license_features:
                if text not in self.tool_widgets or self.tool_widgets[text] is None:
                    tool_map = {
                        "Tool1": Tool1UI,
                        "Tool2": Tool2UI,
                        "Tool3": Tool3UI,
                        "Tool4": Tool4UI
                    }
                    tool_instance = tool_map[text]()
                    self.tool_widgets[text] = tool_instance
                    self.stack.addWidget(tool_instance)

                self.animated_set_current_widget(self.tool_widgets[text])
            else:
                QMessageBox.warning(self, "Access Denied", f"You do not have access to {text} or your license has expired.")
        elif text == "User Manual":
            self.show_user_manual_panel()

    def logout(self):
        reply = QMessageBox.question(
            self, 'Logout', 'Are you sure you want to logout?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logged_in = False
            self.license_valid = False
            self.username = ""
            self.tool_widgets.clear()
            self.animated_set_current_widget(self.login_widget)
            self.update_sidebar_access()

    def add_logo_and_footer(self, layout):
        layout.addStretch(1)
        
        # Add logo
        logo = QLabel()
        logo_pix = QPixmap(resource_path("assets/consulta_logo.png")).scaledToHeight(60, Qt.SmoothTransformation)
        logo.setPixmap(logo_pix)
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        # Footer with copyright
        footer = QLabel(
            '<a href="https://www.consulta.in/" style="color: #7f8c8d; text-decoration: none;">© 2025 Consulta. All Rights Reserved.</a>'
        )
        footer.setOpenExternalLinks(True)
        footer.setAlignment(Qt.AlignCenter)
        footer.setFont(QFont('Arial', 9))
        layout.addWidget(footer)

    def animated_set_current_widget(self, widget):
        current_widget = self.stack.currentWidget()
        if current_widget is widget:
            return

        self.fade_out = QPropertyAnimation(current_widget, b"windowOpacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.fade_out.finished.connect(lambda: self._fade_in_new_widget(widget))
        self.fade_out.start()

    def _fade_in_new_widget(self, widget):
        self.stack.setCurrentWidget(widget)
        widget.setWindowOpacity(0)
        
        self.fade_in = QPropertyAnimation(widget, b"windowOpacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = MainApp()
    win.show()
    sys.exit(app.exec_())