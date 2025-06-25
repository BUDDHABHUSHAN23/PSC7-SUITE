import streamlit as st
import pandas as pd
from utils import load_excel, load_sheet, load_csv  # ✅ Use load_sheet instead of parse_excel


def run_tool3():
    st.set_page_config(page_title="🔍 Excel Comparator", layout="wide")
    st.title("🔍 Excel Files Comparator & Filter Tool")

    file1 = st.file_uploader("📁 Upload Excel File 1", type=["xlsx"])
    file2 = st.file_uploader("📁 Upload Excel File 2", type=["xlsx"])

    if file1 and file2:
        xls1 = load_excel(file1)
        xls2 = load_excel(file2)

        sheet1 = st.selectbox("📄 Select Sheet from File 1", list(xls1.keys()))
        sheet2 = st.selectbox("📄 Select Sheet from File 2", list(xls2.keys()))


        df1 = xls1[sheet1]
        df2 = xls2[sheet2]


        col1 = st.selectbox("📌 Column from File 1", df1.columns)
        col2 = st.selectbox("📌 Column from File 2", df2.columns)
        match_type = st.radio("🎯 Matching Type", ["Exact Match", "Case-insensitive Match"])

        df1["__merge_key__"] = df1[col1].astype(str).str.lower() if match_type != "Exact Match" else df1[col1].astype(str)
        df2["__merge_key__"] = df2[col2].astype(str).str.lower() if match_type != "Exact Match" else df2[col2].astype(str)

        df1_prefixed = df1.add_prefix("F1_")
        df2_prefixed = df2.add_prefix("F2_")
        df1_prefixed["__merge_key__"] = df1["__merge_key__"]
        df2_prefixed["__merge_key__"] = df2["__merge_key__"]

        merged_df = pd.merge(df1_prefixed, df2_prefixed, on="__merge_key__", how="inner")
        st.success(f"✅ {len(merged_df)} matched rows found")

        with st.expander("📋 Preview Merged Data"):
            st.dataframe(merged_df)

        f1_cols = [c for c in merged_df.columns if c.startswith("F1_") and "merge_key" not in c]
        f2_cols = [c for c in merged_df.columns if c.startswith("F2_") and "merge_key" not in c]

        selected_f1_cols = st.multiselect("📌 Columns from File 1", f1_cols, default=f1_cols)
        selected_f2_cols = st.multiselect("📌 Columns from File 2", f2_cols, default=f2_cols)

        final_output = merged_df[selected_f1_cols + selected_f2_cols]
        st.dataframe(final_output)

        csv = final_output.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Final CSV", data=csv, file_name="matched_output.csv", mime="text/csv")
