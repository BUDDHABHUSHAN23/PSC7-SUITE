import streamlit as st
import pandas as pd
from utils import load_excel, load_sheet, load_csv  # ✅ Use load_sheet instead of parse_excel


def run_tool2():
    st.title("📊 Dual Excel Filter Tool")

    file1 = st.file_uploader("📁 Upload Excel File 1 (Sheet1)", type=["xlsx"])
    file2 = st.file_uploader("📁 Upload Excel File 2 (Sheet2)", type=["xlsx"])

    if file1 and file2:
        xls1 = load_excel(file1)
        xls2 = load_excel(file2)
        sheet1 = st.selectbox("📄 Select Sheet from File 1",  list(xls1.keys()))
        sheet2 = st.selectbox("📄 Select Sheet from File 2",  list(xls2.keys()))

        df1 = xls1[sheet1]
        df2 = xls2[sheet2]



        st.subheader("🔗 Step 1: Filter Sheet2 using values from Sheet1")
        col_sheet1 = st.selectbox("Select Column from Sheet1", df1.columns)
        col_sheet2 = st.selectbox("Select Column from Sheet2", df2.columns)

        first_filter_mode = st.radio("First Filter Mode", ["Starts With", "Contains"], key="first_filter")
        values_to_match = df1[col_sheet1].dropna().astype(str).unique()

        if first_filter_mode == "Starts With":
            df2_step1 = df2[df2[col_sheet2].astype(str).apply(lambda x: any(x.startswith(v) for v in values_to_match))]
        else:
            df2_step1 = df2[df2[col_sheet2].astype(str).apply(lambda x: any(v in x for v in values_to_match))]

        st.info(f"🔎 Step 1: {len(df2_step1)} rows matched")
        st.dataframe(df2_step1.head(50))

        st.subheader("🧪 Step 2: Additional Filter")
        add_filter_col = st.selectbox("Column to Filter", df2.columns)
        filter_mode = st.radio("Filter Mode", ["Contains Filter", "Exact Match"], key="second_filter")
        user_input = st.text_area("Enter values (comma separated)")
        filter_values = [v.strip() for v in user_input.split(",") if v.strip()]

        st.subheader("📤 Step 3: Select Output Columns")
        selected_output_cols = st.multiselect("Columns to Display", df2.columns, default=df2.columns)

        if st.button("✅ Apply All Filters"):
            df2_filtered = df2_step1.copy()

            if filter_values:
                if filter_mode == "Contains Filter":
                    df2_filtered = df2_filtered[df2_filtered[add_filter_col].astype(str).apply(
                        lambda x: any(val in x for val in filter_values))]
                else:
                    df2_filtered = df2_filtered[df2_filtered[add_filter_col].astype(str).isin(filter_values)]

            st.success(f"🎯 Final Rows: {len(df2_filtered)}")
            st.dataframe(df2_filtered[selected_output_cols])
            csv = df2_filtered[selected_output_cols].to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv, "filtered_output.csv", "text/csv")