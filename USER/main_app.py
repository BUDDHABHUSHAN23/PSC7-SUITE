import sys
import json
from datetime import datetime, timedelta
<<<<<<< HEAD

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QLineEdit,
    QPushButton, QCheckBox, QFileDialog, QMessageBox, QComboBox,
    QHBoxLayout, QStackedWidget, QTextEdit, QListWidget, QSplitter, 
    QListWidgetItem, QAbstractItemView, QFrame, QSpacerItem, QSizePolicy
=======
import os
import sys

from license_gate import validate_license_file, get_machine_id
from Tool1 import run_tool1
from Tool2 import run_tool2
from Tool3 import run_tool3
from Tool4 import run_tool4

# === PyInstaller Resource Path Fix ===
def resource_path(relative_path):
    """Get absolute path to resource (works for dev and PyInstaller EXE)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# === Tool Runner Mapping ===
TOOL_RUNNERS = {
    "Tool1": run_tool1,
    "Tool2": run_tool2,
    "Tool3": run_tool3,
    "Tool4": run_tool4
}

# === App Config ===
st.set_page_config(page_title="🔐 Login & Tool Suite", layout="wide")

# === User DB ===
USER_CREDENTIALS = {
    "CONSULTA": "Consulta@123",
    "DEMO": "Demo@123"
}

# === Session Init ===
def init_state():
    default_keys = {
        'logged_in': False,
        'username': "",
        'license_valid': False,
        'license_features': [],
        'license_expiry': "",
        'selected_tool': "",
        'tool1_data': None,
        'tool2_data': None,
        'tool3_data': None,
        'tool4_data': None
    }
    for k, v in default_keys.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# === Logo Loader ===
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_path = resource_path(os.path.join("USER", "assets", "consulta_logo.png"))
logo_base64 = get_base64_image(logo_path)

# === Sidebar Info ===
with st.sidebar:
    if st.session_state.logged_in:
        st.markdown(f"👋 **Welcome, {st.session_state.username}**")

        # License info
        if st.session_state.license_valid and st.session_state.license_expiry:
            expiry_date = datetime.strptime(st.session_state.license_expiry, "%Y-%m-%d")
            days_left = (expiry_date - datetime.now()).days
            st.markdown("### 📅 License Status")
            st.info(f"🔒 Valid till: {expiry_date.strftime('%d %b %Y')}")
            if days_left <= 7:
                st.warning(f"⚠️ Expires in {days_left} day(s)")

        # Logout
        if st.button("🔓 Logout"):
            for key in ['logged_in', 'username', 'license_valid', 'license_features', 'license_expiry', 'selected_tool']:
                st.session_state[key] = False if isinstance(st.session_state[key], bool) else ""
            st.rerun()

        # User Manual Download
        user_manual_path = resource_path(os.path.join("USER", "assets", "PCS7 UserManual.pdf"))
        with open(user_manual_path, "rb") as pdf_file:
            pdf_base64 = base64.b64encode(pdf_file.read()).decode()

        st.markdown(f"""
            <a href="data:application/pdf;base64,{pdf_base64}" download="PCS7_TurboSift_User_Manual.pdf" target="_blank" style="text-decoration:none;">
                <button style='padding:10px 16px; font-weight:bold;'>📘 Download User Manual</button>
            </a>
        """, unsafe_allow_html=True)

# === Header ===
st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 30px;">
        <a href="https://www.consulta.in/" target="_blank">
            <img src="data:image/png;base64,{logo_base64}" alt="Consulta Logo" height="50">
        </a>
        <h1 style="margin: 0; font-size: 2rem; color: #333;">PCS7 TurboSift</h1>
    </div>
    <hr>
    """,
    unsafe_allow_html=True
>>>>>>> e2c95af25f92ae7b4cdbb9b1c8ae555f9efa970a
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor

from license_gate import validate_license_file, get_machine_id
from tools.tool1_ui import Tool1UI
from tools.tool2_ui import Tool2UI
from tools.tool3_ui import Tool3UI
from tools.tool4_ui import Tool4UI


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
        header = QLabel("🔐 Secure Login")
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
        
        # Set window icon
        self.setWindowIcon(QIcon("assets/icon.png"))
        
        # Set style
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
            ("Logout", "assets/logout.png")
        ]
        
        for text, icon_path in items:
            item = QListWidgetItem(QIcon(icon_path), text)
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

    def post_login(self):
        if self.username == "CONSULTA":
            self.show_admin_panel()
        else:
            self.show_license_panel()

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
        gen_btn.setStyleSheet("background-color: #27ae60;")
        gen_btn.clicked.connect(self.generate_license)
        layout.addWidget(gen_btn, alignment=Qt.AlignRight)

        self.admin_panel.setLayout(layout)
        self.stack.addWidget(self.admin_panel)
        self.stack.setCurrentWidget(self.admin_panel)

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
                with open(save_path, "w") as f:
                    f.write(json_data)
                QMessageBox.information(self, "Saved", "License file saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred:\n{str(e)}")

    def show_license_panel(self):
        self.license_panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Welcome message
        welcome = QLabel(f"👋 Welcome {self.username}")
        welcome.setFont(QFont('Arial', 16, QFont.Bold))
        layout.addWidget(welcome)

        if not self.license_valid:
            # License upload section
            upload_frame = QFrame()
            upload_frame.setFrameShape(QFrame.StyledPanel)
            upload_frame.setStyleSheet("background-color: white; padding: 20px; border-radius: 5px;")
            upload_layout = QVBoxLayout()
            
            upload_label = QLabel("Please upload your license file to continue")
            upload_label.setFont(QFont('Arial', 12))
            upload_layout.addWidget(upload_label, alignment=Qt.AlignCenter)
            
            btn = QPushButton("Upload License File")
            btn.setFixedSize(200, 40)  # Make it visible enough
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
            btn.clicked.connect(self.upload_license)
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
            
            info_frame.setLayout(info_layout)
            layout.addWidget(info_frame)
            
            # Show available tools
            self.show_tool_buttons(layout)

        # Add logo and footer
        self.add_logo_and_footer(layout)

        self.license_panel.setLayout(layout)
        self.stack.addWidget(self.license_panel)
        self.stack.setCurrentWidget(self.license_panel)

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
                valid, result = validate_license_file(license_data)
                if valid:
                    self.license_valid = True
                    self.license_features = result["features"]
                    self.license_expiry = result["valid_till"]
                    QMessageBox.information(self, "Success", "License validated successfully!")
                    self.show_license_panel()
                else:
                    QMessageBox.critical(self, "Error", f"License validation failed:\n{result}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read license file:\n{str(e)}")

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
                pixmap = QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
        # Clear previous tools from stack if any
        for i in range(self.stack.count()):
            widget = self.stack.widget(i)
            if widget not in [self.login_widget, getattr(self, 'license_panel', None), getattr(self, 'admin_panel', None)]:
                self.stack.removeWidget(widget)
                widget.deleteLater()

        tool_widget = tool_cls()
        self.stack.addWidget(tool_widget)
        self.stack.setCurrentWidget(tool_widget)

    def handle_sidebar_selection(self, item):
        if not item:
            return
            
        text = item.text()
        if text == "Home":
            if self.logged_in:
                if self.username == "CONSULTA":
                    self.stack.setCurrentWidget(self.admin_panel)
                else:
                    self.stack.setCurrentWidget(self.license_panel)
            else:
                self.stack.setCurrentWidget(self.login_widget)
        elif text == "Logout":
            self.logout()
        elif text in ["Tool1", "Tool2", "Tool3", "Tool4"]:
            if self.license_valid and text in self.license_features:
                if text not in self.tool_widgets:
                    tool_map = {
                        "Tool1": Tool1UI,
                        "Tool2": Tool2UI,
                        "Tool3": Tool3UI,
                        "Tool4": Tool4UI
                    }
                    self.tool_widgets[text] = tool_map[text]()
                    self.stack.addWidget(self.tool_widgets[text])
                self.stack.setCurrentWidget(self.tool_widgets[text])
            else:
                QMessageBox.warning(self, "Access Denied", f"You do not have access to {text} or your license has expired.")

    def logout(self):
        reply = QMessageBox.question(
            self, 'Logout', 'Are you sure you want to logout?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logged_in = False
            self.license_valid = False
            self.username = ""
            self.stack.setCurrentWidget(self.login_widget)

    def add_logo_and_footer(self, layout):
        # Add vertical spacer to push content up
        layout.addStretch(1)
        
        # Add logo
        logo = QLabel()
        logo_pix = QPixmap("assets/consulta_logo.png").scaledToHeight(60, Qt.SmoothTransformation)
        logo.setPixmap(logo_pix)
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

<<<<<<< HEAD
        # Footer with copyright
        footer = QLabel(
            '<a href="https://www.consulta.in/" style="color: #7f8c8d; text-decoration: none;">© 2025 Consulta. All Rights Reserved.</a>'
        )
        footer.setOpenExternalLinks(True)
        footer.setAlignment(Qt.AlignCenter)
        footer.setFont(QFont('Arial', 9))
        layout.addWidget(footer)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    win = MainApp()
    win.show()
    
    sys.exit(app.exec_())
=======
# === Footer ===
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        text-align: center;
        padding: 10px;
        font-size: 0.9rem;
        background-color: white;
        z-index: 100;
        border-top: 1px solid #eee;
    }
    </style>
    <div class="footer">
        © 2016 All Rights Reserved CONSULTA TECHNOLOGIES PVT LTD.
    </div>
    """,
    unsafe_allow_html=True
)
>>>>>>> e2c95af25f92ae7b4cdbb9b1c8ae555f9efa970a
