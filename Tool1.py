import streamlit as st
import pandas as pd
from utils import load_excel, load_sheet, load_csv  # ✅ Correct functions

def run_tool1():
    st.title("🧮 CSV/Excel Filter Tool")
    
    uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

    if uploaded_file is not None:
        file_ext = uploaded_file.name.split('.')[-1].lower()

        if file_ext == 'xlsx':
            xls = load_excel(uploaded_file)  # Returns dict of {sheet_name: DataFrame}
            sheet_name = st.selectbox("Select Excel Sheet", list(xls.keys()))
            df = xls[sheet_name]  # ✅ Select DataFrame from dict
        elif file_ext == 'csv':
            df = load_csv(uploaded_file)
        else:
            st.error("Unsupported file type")
            return

        st.session_state['uploaded_df'] = df  # Store in session state

        # === UI for filtering ===
        st.subheader("1️⃣ Select Filter Column")
        filter_col = st.selectbox("Choose column to filter on", df.columns)

        st.subheader("2️⃣ Enter Values to Filter (comma separated)")
        filter_values_raw = st.text_input(f"Enter values to match in `{filter_col}`")
        filter_values = [v.strip() for v in filter_values_raw.split(',') if v.strip()]

        st.subheader("3️⃣ Select Columns to Display")
        display_cols = st.multiselect("Choose columns to include in output", df.columns, default=list(df.columns))

        if st.button("🔍 Apply Filter"):
            if filter_values:
                filtered_df = df[df[filter_col].astype(str).isin(filter_values)]
                st.success(f"✅ Found {len(filtered_df)} matching row(s)")
                st.dataframe(filtered_df[display_cols])
            else:
                st.warning("⚠️ Please enter at least one value to filter.")

        st.markdown("---")
        st.subheader("📋 Preview of Uploaded Data")
        st.dataframe(df.head())
