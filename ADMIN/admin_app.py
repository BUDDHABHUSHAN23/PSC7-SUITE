
## this is for the admin 
import sys
import json
from datetime import datetime, timedelta
import os
import hashlib
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, 
    QVBoxLayout, QPushButton, QFileDialog, QMessageBox,
    QListWidget, QComboBox, QTextEdit, QLineEdit, 
    QDialog, QDialogButtonBox
)

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

def resource_path(relative_path):
    """ Get path to resource whether in development or PyInstaller bundle """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin Login")
        self.setWindowIcon(QIcon(resource_path("assets/lock.png")))
        self.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(QLabel("Admin Credentials:"))
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_credentials(self):
        return self.username.text(), self.password.text()

class AdminApp(QMainWindow):
    ADMIN_CREDENTIALS = {
        "CONSULTA": "Consulta@123"
    }

    def __init__(self):
        super().__init__()
        if not self.authenticate():
            sys.exit(1)
            
        self.setWindowTitle("PCS7 TurboSift - Admin Console")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon(resource_path("assets/admin.png")))
        self.init_ui()
        self.current_request = None
    
    def authenticate(self):
        login = LoginDialog()
        if login.exec_() == QDialog.Accepted:
            username, password = login.get_credentials()
            return username in self.ADMIN_CREDENTIALS and self.ADMIN_CREDENTIALS[username] == password
        return False
    
    def init_ui(self):
        central = QWidget()
        layout = QVBoxLayout()
        
        header = QLabel("PCS7 TurboSift - Admin Console")
        header.setFont(QFont('Arial', 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        load_btn = QPushButton("Load User Request File")
        load_btn.clicked.connect(self.load_request)
        layout.addWidget(load_btn)
        
        self.user_info = QTextEdit()
        self.user_info.setReadOnly(True)
        layout.addWidget(self.user_info)
        
        self.duration = QComboBox()
        self.duration.addItems(["10", "30", "90", "180", "365"])
        self.duration.setCurrentIndex(3)
        
        self.features = QListWidget()
        self.features.addItems(["Tool1", "Tool2", "Tool3", "Tool4"])
        self.features.setSelectionMode(QListWidget.MultiSelection)
        
        for i in range(self.features.count()):
            self.features.item(i).setSelected(True)
        
        gen_btn = QPushButton("Generate License")
        gen_btn.clicked.connect(self.generate_license)
        
        layout.addWidget(QLabel("License Duration (days):"))
        layout.addWidget(self.duration)
        layout.addWidget(QLabel("Select Features:"))
        layout.addWidget(self.features)
        layout.addWidget(gen_btn)
        
        self.license_output = QTextEdit()
        self.license_output.setReadOnly(True)
        layout.addWidget(self.license_output)
        
        central.setLayout(layout)
        self.setCentralWidget(central)
    
    def load_request(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Request File", "", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.current_request = json.load(f)
                
                # Validate required fields
                required_fields = ['name', 'email', 'machine_id', 'request_date']
                for field in required_fields:
                    if field not in self.current_request:
                        raise ValueError(f"Missing required field: {field}")
                
                self.user_info.clear()
                self.user_info.append("User Information:")
                self.user_info.append(f"Name: {self.current_request.get('name', '')}")
                self.user_info.append(f"Email: {self.current_request.get('email', '')}")
                self.user_info.append(f"Machine ID: {self.current_request.get('machine_id', '')}")
                self.user_info.append(f"Request Date: {self.current_request.get('request_date', '')}")
                
                # Auto-select requested features if specified
                if 'requested_features' in self.current_request:
                    for i in range(self.features.count()):
                        item = self.features.item(i)
                        item.setSelected(item.text() in self.current_request['requested_features'])
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Invalid request file: {str(e)}")
                self.current_request = None
    
def generate_license(self):
    """Generate standardized license from request"""
    if not self.current_request:
        QMessageBox.warning(self, "Warning", "No request file loaded!")
        return

    try:
        license_data = {
            "version": "1.0",
            "metadata": {
                "license_id": f"LIC-{datetime.now().strftime('%Y%m%d')}-001",
                "issue_date": datetime.utcnow().isoformat() + "Z",
                "issuer": "Consulta Admin",
                "software_version": self.current_request.get('software_version', '1.0')
            },
            "licensee": {
                "name": self.current_request.get('name', ''),
                "email": self.current_request.get('email', ''),
                "organization": self.current_request.get('organization', '')
            },
            "system": {
                "machine_id": self.current_request.get('machine_id', ''),
                "binding_type": "SingleMachine"
            },
            "license": {
                "features": [item.text() for item in self.features.selectedItems()],
                "validity": self.calculate_validity(),
                "terms": {
                    "max_instances": 1,
                    "allow_updates": True,
                    "allow_transfer": False
                }
            }
        }
        
        # Add cryptographic signature
        license_data["signature"] = {
            "algorithm": "RSA-SHA256",
            "value": self.generate_signature(),
            "public_key": "your_public_key_here"  # Replace with actual public key
        }
        
        self.license_output.clear()
        self.license_output.append("Generated License:")
        self.license_output.append(json.dumps(license_data, indent=2))
        
        return license_data
        
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to generate license: {str(e)}")
        return None
    
    def generate_signature(self):
        """Generate a simple hash-based signature (replace with proper crypto in production)"""
        secret_key = "your_secret_key_here"  # Should be securely stored in production
        data = {
            "machine_id": self.current_request.get('machine_id'),
            "duration": self.duration.currentText(),
            "features": [item.text() for item in self.features.selectedItems()]
        }
        data_str = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(secret_key.encode() + data_str).hexdigest()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdminApp()
    window.show()
    sys.exit(app.exec_())