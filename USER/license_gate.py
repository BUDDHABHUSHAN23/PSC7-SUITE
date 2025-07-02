from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox
from datetime import datetime
import json
import hashlib
import platform
import uuid
import os

def get_machine_id():
    """
    Generate a secure and stable machine ID using system details.
    """
    components = [
        platform.node(),
        platform.system(),
        platform.release(),
        platform.machine(),
        str(uuid.getnode()),
        os.getenv("PROCESSOR_IDENTIFIER", "")
    ]
    raw_id = "-".join(components)
    return hashlib.sha256(raw_id.encode()).hexdigest()

def validate_license_file(data):
    try:
        required_keys = {"features", "valid_till"}
        if not required_keys.issubset(set(data.keys())):
            return False, "Missing required license keys"

        expiry_str = data['valid_till']
        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
        if datetime.now() > expiry_date:
            return False, "License has expired"

        if not isinstance(data['features'], list):
            return False, "Features must be a list"

        return True, data
    except Exception as e:
        return False, f"Error validating license: {e}"


class LicenseChecker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("License Activation")
        self.license_data = None

        layout = QVBoxLayout()
        self.info_label = QLabel("Please upload your license file")
        layout.addWidget(self.info_label)

        self.upload_btn = QPushButton("Upload License JSON")
        self.upload_btn.clicked.connect(self.load_license)
        layout.addWidget(self.upload_btn)

        self.setLayout(layout)

    def load_license(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open License File", "", "JSON Files (*.json)")
        if not file_path:
            return
        try:
            with open(file_path, 'r') as f:
                license_json = json.load(f)

            valid, result = validate_license_file(license_json)
            if valid:
                features = result['features']
                expiry = result['valid_till']
                self.info_label.setText(f"✅ License valid till {expiry}. Features enabled: {', '.join(features)}")
                # You can emit a signal or call method to enable features in main app
            else:
                QMessageBox.warning(self, "Invalid License", result)
                self.info_label.setText("❌ License invalid or expired")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load license file: {e}")
