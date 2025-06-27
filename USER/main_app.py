import streamlit as st
import base64
import json
from datetime import datetime, timedelta
import os
from license_gate import validate_license_file, get_machine_id
from Tool1 import run_tool1
from Tool2 import run_tool2
from Tool3 import run_tool3
from Tool4 import run_tool4

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

logo_path = os.path.join("assets", "consulta_logo.png")
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
        with open("assets/PCS7 UserManual.pdf", "rb") as pdf_file:
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
)

# === Login Page ===
if not st.session_state.logged_in:
    st.title("🔐 Secure Login")
    username = st.text_input("Username").strip()
    show_password = st.checkbox("Show Password")
    password = st.text_input("Password", type="default" if show_password else "password").strip()

    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password!")

# === After Login ===
else:
    if st.session_state.username == "CONSULTA":
        st.title("🔧 Admin Dashboard")
        st.subheader("🔧 Admin License Generator")

        expiry_days = st.number_input("📅 Expiry Days", min_value=1, max_value=9999, value=365)
        features = st.multiselect("⚙️ Enable Tools", ["Tool1", "Tool2", "Tool3", "Tool4"], default=["Tool1", "Tool2"])

        if st.button("Generate License File"):
            license_payload = {
                "machine_id": get_machine_id(),
                "issued_on": str(datetime.now()),
                "valid_till": (datetime.now() + timedelta(days=expiry_days)).strftime("%Y-%m-%d"),
                "features": features
            }

            license_json = json.dumps(license_payload, indent=4)
            st.download_button("📥 Download License", data=license_json, file_name="activation_key.json", mime="application/json")
            st.code(license_json, language="json")

    else:
        if not st.session_state.license_valid:
            st.warning("⚠️ License not activated or expired. Please upload your activation key.")
            uploaded_file = st.file_uploader("Upload Activation Key JSON", type="json")
            if uploaded_file is not None:
                try:
                    license_data = json.load(uploaded_file)
                    valid, result = validate_license_file(license_data)
                    if valid:
                        st.session_state.license_valid = True
                        st.session_state.license_features = result["features"]
                        st.session_state.license_expiry = result["valid_till"]
                        st.success("✅ License activated successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ License invalid: {result}")
                except Exception as e:
                    st.error(f"Error loading license file: {e}")
        else:
            st.subheader("🛠 Select a Tool")
            all_tools = {
                "📁 Single File Filter": "Tool1",
                "📂 Dual File Filter": "Tool2",
                "📊 Exact Match Comparator": "Tool3",
                "🔍 Contains Match Comparator": "Tool4"
            }

            allowed_tools = {name: key for name, key in all_tools.items() if key in st.session_state.license_features}

            if not allowed_tools:
                st.warning("⚠️ No tools enabled in your license.")
            else:
                cols = st.columns(len(allowed_tools))
                for idx, (tool_name, tool_key) in enumerate(allowed_tools.items()):
                    with cols[idx]:
                        if st.button(tool_name, key=tool_key):
                            st.session_state.selected_tool = tool_key
                            st.rerun()

            if st.session_state.selected_tool:
                tool_display_name = [name for name, key in allowed_tools.items() if key == st.session_state.selected_tool]
                if tool_display_name:
                    st.markdown(f"### 🚀 Running: **{tool_display_name[0]}**")

                TOOL_RUNNERS.get(
                    st.session_state.selected_tool,
                    lambda: st.error("❌ Tool not found or not enabled.")
                )()

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
