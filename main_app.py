import streamlit as st
from streamlit_lottie import st_lottie
import requests
import base64
import os

# === App Config ===
st.set_page_config(page_title="🔐 Login & Tool Suite", layout="wide")

# === Lottie Loader ===
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# === Logo Loader ===
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# === Load Logo ===
logo_path = os.path.join("assets", "consulta_logo.png")
logo_base64 = get_base64_image(logo_path)

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

# === User DB ===
USER_CREDENTIALS = {
    "admin": "admin123",
    "user": "user123"
}

# === Session Init ===
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'selected_tool' not in st.session_state:
    st.session_state.selected_tool = ""

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

# === Tool Suite ===
else:
    st.success(f"👋 Welcome, {st.session_state.username}")
    st.markdown("### 🛠 Select a Tool")

    tools = {
        "📁 Single File Filter": "Tool1",
        "📂 Dual File Filter": "Tool2",
        "📊 Exact Match Comparator": "Tool3",
        "🔍 Contains Match Comparator": "Tool4"
    }

    # === Card Row for Tool Selection ===
    cols = st.columns(len(tools))
    for idx, (tool_name, tool_key) in enumerate(tools.items()):
        with cols[idx]:
            if st.button(tool_name, key=tool_key):
                st.session_state.selected_tool = tool_name
                st.rerun()

    # === Show Selected Tool ===
    if st.session_state.selected_tool:
        st.markdown(f"### 🚀 Running: **{st.session_state.selected_tool}**")

        if st.session_state.selected_tool == "📁 Single File Filter":
            from Tool1 import run_tool1
            run_tool1()

        elif st.session_state.selected_tool == "📂 Dual File Filter":
            from Tool2 import run_tool2
            run_tool2()

        elif st.session_state.selected_tool == "📊 Exact Match Comparator":
            from Tool3 import run_tool3
            run_tool3()

        elif st.session_state.selected_tool == "🔍 Contains Match Comparator":
            from Tool4 import run_tool4
            run_tool4()

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
