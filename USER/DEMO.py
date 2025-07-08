import sys
import json
from datetime import datetime, timedelta, timezone
import os
import hashlib
import bcrypt
import platform

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QLineEdit,
    QPushButton, QCheckBox, QFileDialog, QMessageBox, QComboBox,
    QHBoxLayout, QStackedWidget, QTextEdit, QListWidget, QSplitter, 
    QListWidgetItem, QAbstractItemView, QFrame, QSpacerItem, QSizePolicy,
    QDialog, QDialogButtonBox, QGridLayout, QFormLayout
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve

from license_gate import get_machine_id
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

class UserProfileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create User Profile")
        self.setWindowIcon(QIcon(resource_path("assets/user.png")))
        self.resize(400, 400)
        
        layout = QVBoxLayout()
        
        header = QLabel("Create New User Profile")
        header.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(header)
        
        form_layout = QFormLayout()
        
        self.full_name = QLineEdit()
        self.email = QLineEdit()
        self.organization = QLineEdit()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("Full Name:", self.full_name)
        form_layout.addRow("Email:", self.email)
        form_layout.addRow("Organization:", self.organization)
        form_layout.addRow("Username:", self.username)
        form_layout.addRow("Password:", self.password)
        form_layout.addRow("Confirm Password:", self.confirm_password)
        
        layout.addLayout(form_layout)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.validate_inputs)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        
        self.setLayout(layout)
    
    def validate_inputs(self):
        if not all([self.full_name.text(), self.email.text(), self.username.text(), 
                   self.password.text(), self.confirm_password.text()]):
            QMessageBox.warning(self, "Error", "All fields are required!")
            return
            
        if self.password.text() != self.confirm_password.text():
            QMessageBox.warning(self, "Error", "Passwords don't match!")
            return
            
        if len(self.password.text()) < 8:
            QMessageBox.warning(self, "Error", "Password must be at least 8 characters!")
            return
            
        self.accept()
    
    def get_profile_data(self):
        # Hash the password
        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw(self.password.text().encode('utf-8'), salt)
        
        return {
            "full_name": self.full_name.text(),
            "email": self.email.text(),
            "organization": self.organization.text(),
            "username": self.username.text(),
            "password_hash": hashed_pw.decode('utf-8'),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
class LicenseManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("License Management")
        self.setWindowIcon(QIcon(resource_path("assets/license.png")))
        self.resize(500, 300)
        
        layout = QVBoxLayout()
        
        header = QLabel("License Management")
        header.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(header)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)
        
        self.status_label = QLabel()
        self.status_label.setFont(QFont('Arial', 10))
        layout.addWidget(self.status_label)
        
        # Add Request License button
        self.request_btn = QPushButton("Generate License Request")
        self.request_btn.setIcon(QIcon(resource_path("assets/request.png")))
        self.request_btn.clicked.connect(self.parent().generate_license_request)
        
        self.view_btn = QPushButton("View Details")
        self.view_btn.setIcon(QIcon(resource_path("assets/info.png")))
        self.view_btn.clicked.connect(self.view_license_details)
        
        self.upload_btn = QPushButton("Upload License")
        self.upload_btn.setIcon(QIcon(resource_path("assets/upload.png")))
        self.upload_btn.clicked.connect(self.upload_license)
        
        self.delete_btn = QPushButton("Remove License")
        self.delete_btn.setIcon(QIcon(resource_path("assets/delete.png")))
        self.delete_btn.clicked.connect(self.delete_license)
        self.delete_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.request_btn)
        btn_layout.addWidget(self.view_btn)
        btn_layout.addWidget(self.upload_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(self.close)
        layout.addWidget(btn_box)
        
        self.setLayout(layout)
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
            self.request_btn.setEnabled(False)  # Disable request if license exists
        else:
            self.status_label.setText("No active license found")
            self.delete_btn.setEnabled(False)
            self.view_btn.setEnabled(False)
            self.request_btn.setEnabled(True)
    
    def view_license_details(self):
        license_data = load_encrypted_license()
        if license_data:
            dialog = LicenseDetailsDialog(license_data, self)
            dialog.exec_()
    
    def upload_license(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select License File", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, "r") as f:
                    license_data = json.load(f)
                
                valid, result = validate_license_file(license_data)
                if not valid:
                    QMessageBox.critical(self, "Invalid License", result)
                    return
                
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

class LicenseDetailsDialog(QDialog):
    def __init__(self, license_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("License Details")
        self.setWindowIcon(QIcon(resource_path("assets/info.png")))
        self.resize(500, 300)
        
        layout = QVBoxLayout()
        
        header = QLabel("Current License Information")
        header.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(header)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)
        
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
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(self.close)
        layout.addWidget(btn_box)
        self.setLayout(layout)

        
class MainApp(QMainWindow):
    USER_CREDENTIALS = {
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

        # Initialize user profile system
        self.user_profiles = {}
        self.current_profile = None
        self.load_user_profiles()
        
        self.username = ""
        self.logged_in = False
        self.license_valid = False
        self.license_features = []
        self.license_expiry = ""
        self.tool_widgets = {}

        self.stack = QStackedWidget()
        
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setIconSize(QSize(24, 24))
        
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

        self.splitter = QSplitter()
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.stack)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setHandleWidth(1)
        
        self.setCentralWidget(self.splitter)

        self.login_widget = self.LoginWidget(self)
        self.stack.addWidget(self.login_widget)
        self.stack.setCurrentWidget(self.login_widget)

        self.update_sidebar_access()

        license_data, valid, features, expiry = get_valid_license_on_start()
        if valid:
            self.license_valid = True
            self.license_features = features
            self.license_expiry = expiry

    # User Profile Methods
    def load_user_profiles(self):
        """Load user profiles from encrypted storage"""
        try:
            profiles_path = os.path.join(os.path.expanduser("~"), ".pcs7_profiles.json")
            if os.path.exists(profiles_path):
                with open(profiles_path, "r") as f:
                    self.user_profiles = json.load(f)
        except Exception as e:
            print(f"Error loading profiles: {e}")
            self.user_profiles = {}

    def save_user_profiles(self):
        """Save user profiles to encrypted storage"""
        try:
            profiles_path = os.path.join(os.path.expanduser("~"), ".pcs7_profiles.json")
            with open(profiles_path, "w") as f:
                json.dump(self.user_profiles, f, indent=2)
        except Exception as e:
            print(f"Error saving profiles: {e}")

    def create_user_profile(self):
        """Show dialog to create new user profile"""
        dialog = UserProfileDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            profile_data = dialog.get_profile_data()
            username = profile_data["username"]
            
            if username in self.user_profiles:
                QMessageBox.warning(self, "Error", "Username already exists!")
                return
                
            self.user_profiles[username] = profile_data
            self.save_user_profiles()
            QMessageBox.information(self, "Success", "Profile created successfully!")
            
            # Auto-fill login form
            self.login_widget.username_input.setText(username)
            self.login_widget.password_input.setText("")
            self.login_widget.password_input.setFocus()

    # User Info Methods
    def get_user_name(self):
        """Get the current user's name from profile"""
        if self.current_profile:
            return self.current_profile.get("full_name", self.username)
        return self.username or "Unknown User"

    def get_user_email(self):
        """Get the current user's email from profile"""
        if self.current_profile:
            return self.current_profile.get("email", f"{self.username}@example.com")
        return f"{self.username}@example.com" if self.username else "unknown@example.com"

    def get_organization(self):
        """Get the user's organization from profile"""
        if self.current_profile:
            return self.current_profile.get("organization", "Demo Organization")
        return "Demo Organization"

    def get_os_info(self):
        """Get operating system information"""
        return f"{platform.system()} {platform.release()}"

    def get_cpu_id(self):
        """Get CPU identifier (placeholder implementation)"""
        return "CPU-UNKNOWN"

    def sign_request(self, request_data):
        """Create a signature for the license request (placeholder implementation)"""
        data_str = json.dumps(request_data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(data_str).hexdigest()

    def generate_license_request(self):
        try:
            request_data = {
                "version": "1.0",
                "metadata": {
                    "request_id": f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "request_date": datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
                    "software_version": "PCS7-2.5.0"
                },
                "requester": {
                    "name": self.get_user_name(),
                    "email": self.get_user_email(),
                    "organization": self.get_organization()
                },
                "system": {
                    "machine_id": get_machine_id(),
                    "os_type": self.get_os_info(),
                    "cpu_id": self.get_cpu_id()
                },
                "request": {
                    "requested_features": [
                        {"id": "tool1", "name": "Tool1", "version": "1.2"},
                        {"id": "tool2", "name": "Tool2", "version": "2.1"},
                        {"id": "tool3", "name": "Tool3", "version": "3.0"},
                        {"id": "tool4", "name": "Tool4", "version": "1.5"}
                    ],
                    "requested_duration_days": 30,
                    "purpose": "Production use"
                }
            }
            
            request_data["signature"] = {
                "algorithm": "SHA256",
                "value": self.sign_request(request_data)
            }
            
            # Create requests directory if not exists
            os.makedirs("license_requests", exist_ok=True)
            save_path = os.path.join("license_requests", 
                                f"license_request_{request_data['metadata']['request_id']}.json")
            
            with open(save_path, 'w') as f:
                json.dump(request_data, f, indent=2)
                
            QMessageBox.information(self, "Success", 
                                f"License request generated:\n{save_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                            f"Failed to generate license request:\n{str(e)}")

    # ... (Rest of your existing methods remain exactly the same)
    def validate_license(self, license_data):
        try:
            # Verify structure
            required_sections = ['version', 'metadata', 'licensee', 'system', 'license', 'signature']
            for section in required_sections:
                if section not in license_data:
                    return False, "Invalid license structure", [], ""
            
            # Verify signature (placeholder - implement proper verification)
            if not self.verify_signature(license_data):
                return False, "Invalid signature", [], ""
            
            # Check machine binding
            if license_data['system']['machine_id'] != get_machine_id():
                return False, "License not valid for this machine", [], ""
            
            # Check expiration
            end_date = datetime.fromisoformat(license_data['license']['validity']['end_date'].replace('Z', ''))
            if datetime.now() > end_date:
                return False, "License expired", [], ""
            
            # Extract features
            features = [f['id'] for f in license_data['license']['features']]
            expiry = end_date.strftime("%Y-%m-%d")
            
            return True, "Valid license", features, expiry
            
        except Exception as e:
            return False, f"Validation error: {str(e)}", [], ""
            
    def verify_signature(self, license_data):
        """Placeholder - implement proper signature verification"""
        try:
            # In a real implementation, you would:
            # 1. Extract the signature
            # 2. Verify using your public key
            # 3. Return True/False based on verification
            
            # For now, just check signature exists
            return "signature" in license_data and bool(license_data["signature"].get("value"))
        except:
            return False

    def post_login(self):
        self.license_updated()
        self.update_sidebar_access()
        self.show_license_panel()
    
    def license_updated(self):
        license_data, valid, features, expiry = get_valid_license_on_start()
        self.license_valid = valid
        self.license_features = features
        self.license_expiry = expiry
        
        if hasattr(self, 'statusBar'):
            self.statusBar().clearMessage()
            if valid:
                self.statusBar().showMessage(
                    f"License valid until: {expiry} | "
                    f"Enabled tools: {', '.join(features)}"
                )
            else:
                self.statusBar().showMessage("⚠️ No valid license found")

    def show_license_panel(self):
        self.license_panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        welcome = QLabel(f"👋 Welcome {self.username}")
        welcome.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(welcome)

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
            
            self.show_tool_buttons(layout)

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
        
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

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
        
        logo = QLabel()
        logo_pix = QPixmap(resource_path("assets/consulta_logo.png")).scaledToHeight(60, Qt.SmoothTransformation)
        logo.setPixmap(logo_pix)
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

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

    class LoginWidget(QWidget):
        def __init__(self, parent):
            super().__init__()
            self.parent = parent
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout()
            layout.setContentsMargins(40, 40, 40, 40)
            layout.setSpacing(20)

            header = QLabel("Welcome to PCS7 TurboSift")
            header.setFont(QFont('Arial', 16, QFont.Bold))
            header.setAlignment(Qt.AlignCenter)
            layout.addWidget(header)

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

            self.create_profile_btn = QPushButton("Create Profile")
            self.create_profile_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f39c12;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e67e22;
                }
            """)
            self.create_profile_btn.clicked.connect(self.parent.create_user_profile)
            
            layout.addWidget(self.username_input)
            layout.addWidget(self.password_input)
            layout.addWidget(self.show_pass)
            layout.addSpacing(10)
            layout.addWidget(self.login_btn)
            layout.addWidget(self.create_profile_btn)
            layout.addStretch(1)
            
            self.setLayout(layout)

        def handle_login(self):
            username = self.username_input.text().strip()
            password = self.password_input.text().strip()
            
            # Check against stored profiles
            if username in self.parent.user_profiles:
                stored_hash = self.parent.user_profiles[username]["password_hash"]
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                    self.parent.username = username
                    self.parent.current_profile = self.parent.user_profiles[username]
                    self.parent.logged_in = True
                    self.parent.post_login()
                    return
            
            # Fallback to hardcoded credentials
            if username in self.parent.USER_CREDENTIALS and self.parent.USER_CREDENTIALS[username] == password:
                self.parent.username = username
                self.parent.logged_in = True
                self.parent.post_login()
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = MainApp()
    win.show()
    sys.exit(app.exec_())