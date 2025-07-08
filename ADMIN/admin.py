import sys
import json
import hashlib
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                            QVBoxLayout, QPushButton, QFileDialog, QMessageBox,
                            QListWidget, QComboBox, QTextEdit, QLineEdit, 
                            QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin Login")
        self.setWindowIcon(QIcon("assets/lock.png"))
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
        "CONSULTA": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"  # SHA-256 of "123"
    }

    def __init__(self):
        super().__init__()
        if not self.authenticate():
            sys.exit(1)
            
        self.setWindowTitle("PCS7 TurboSift - Admin Console")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("assets/admin.png"))
        self.init_ui()
        self.current_request = None
    
    def authenticate(self):
        login = LoginDialog()
        if login.exec_() == QDialog.Accepted:
            username, password = login.get_credentials()
            hashed_pw = hashlib.sha256(password.encode()).hexdigest()
            return username in self.ADMIN_CREDENTIALS and self.ADMIN_CREDENTIALS[username] == hashed_pw
        return False
    
    def init_ui(self):
        central = QWidget()
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("PCS7 TurboSift - Admin Console")
        header.setFont(QFont('Arial', 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Load request button
        load_btn = QPushButton("Load User Request File")
        load_btn.clicked.connect(self.load_request)
        layout.addWidget(load_btn)
        
        # User info display
        self.user_info = QTextEdit()
        self.user_info.setReadOnly(True)
        layout.addWidget(self.user_info)
        
        # License configuration
        self.duration = QComboBox()
        self.duration.addItems(["7", "30", "90", "180", "365"])
        self.duration.setCurrentIndex(1)  # Default to 30 days
        
        self.features = QListWidget()
        self.features.addItems(["Tool1", "Tool2", "Tool3", "Tool4"])
        self.features.setSelectionMode(QListWidget.MultiSelection)
        
        # Select all features by default
        for i in range(self.features.count()):
            self.features.item(i).setSelected(True)
        
        # Generate license button
        gen_btn = QPushButton("Generate License")
        gen_btn.clicked.connect(self.generate_license)
        
        # Add to layout
        layout.addWidget(QLabel("License Duration (days):"))
        layout.addWidget(self.duration)
        layout.addWidget(QLabel("Select Features:"))
        layout.addWidget(self.features)
        layout.addWidget(gen_btn)
        
        # License output
        self.license_output = QTextEdit()
        self.license_output.setReadOnly(True)
        layout.addWidget(self.license_output)
        
        central.setLayout(layout)
        self.setCentralWidget(central)
    
    def load_request(self):
        """Load and validate user request file"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Request File", "", "JSON Files (*.json)"
            )
            
            if not file_path:
                return
                
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract information from your specific JSON format
            self.current_request = {
                'name': data['requester']['name'],
                'email': data['requester']['email'],
                'machine_id': data['system']['machine_id'],
                'request_date': data['metadata']['request_date'],
                'requested_features': [feature['name'] for feature in data['request']['requested_features']],
                'requested_duration': data['request']['requested_duration_days'],
                'metadata': data['metadata']  # Preserve original metadata
            }
            
            # Display user info
            self.user_info.clear()
            self.user_info.append("=== User Information ===")
            self.user_info.append(f"Name: {self.current_request['name']}")
            self.user_info.append(f"Email: {self.current_request['email']}")
            self.user_info.append(f"Machine ID: {self.current_request['machine_id']}")
            self.user_info.append(f"Request Date: {self.current_request['request_date']}")
            self.user_info.append("\n=== Requested Features ===")
            for feature in self.current_request['requested_features']:
                self.user_info.append(f"- {feature}")
            self.user_info.append(f"\nRequested Duration: {self.current_request['requested_duration']} days")
            
            # Auto-set the duration combo box
            duration_index = self.duration.findText(str(self.current_request['requested_duration']))
            if duration_index >= 0:
                self.duration.setCurrentIndex(duration_index)
                
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Invalid JSON file format")
        except KeyError as e:
            QMessageBox.critical(self, "Error", f"Missing required field: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load request: {str(e)}")
    
    def generate_license(self):
        """Generate and save license file"""
        if not self.current_request:
            QMessageBox.warning(self, "Warning", "Please load a user request first")
            return
        
        try:
            duration_days = int(self.duration.currentText())
            if duration_days <= 0:
                raise ValueError("Duration must be positive")
                
            selected_features = [item.text() for item in self.features.selectedItems()]
            if not selected_features:
                QMessageBox.warning(self, "Warning", "Please select at least one feature")
                return
                
            # Generate license data
            license_data = {
                "license_version": "1.0",
                "machine_id": self.current_request['machine_id'],
                "issued_to": self.current_request['name'],
                "issued_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "valid_till": (datetime.now() + timedelta(days=duration_days)).strftime("%Y-%m-%d"),
                "features": selected_features,
                "metadata": {
                    "original_request_id": self.current_request['metadata']['request_id'],
                    "software_version": self.current_request['metadata']['software_version']
                },
                "signature": self.generate_signature(self.current_request['machine_id'])
            }
            
            json_data = json.dumps(license_data, indent=4)
            self.license_output.setPlainText(json_data)
            
            # Save to file
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Save License File", 
                f"license_{self.current_request['machine_id']}.json", 
                "JSON Files (*.json)"
            )
            
            if save_path:
                with open(save_path, 'w') as f:
                    f.write(json_data)
                QMessageBox.information(self, "Success", f"License saved to:\n{save_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"License generation failed: {str(e)}")
    
    def generate_signature(self, machine_id):
        """Generate a simple signature (in production use proper cryptography)"""
        secret_key = "PCS7TurboSiftSecret2023"
        signature_string = f"{machine_id}{secret_key}{datetime.now().strftime('%Y%m%d')}"
        return hashlib.sha256(signature_string.encode()).hexdigest()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdminApp()
    window.show()
    sys.exit(app.exec_())