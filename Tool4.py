import streamlit as st
import pandas as pd
from utils import load_excel, load_sheet, load_csv  # ✅ Use load_sheet instead of parse_excel


def run_tool4():
    st.set_page_config(page_title="🔍 Partial Match Comparator", layout="wide")
    st.title("🔍 Excel Files Partial Match (Contains) Comparator")

    file1 = st.file_uploader("📁 Upload Excel File 1", type=["xlsx"])
    file2 = st.file_uploader("📁 Upload Excel File 2", type=["xlsx"])

    if file1 and file2:
        xls1 = load_excel(file1)
        xls2 = load_excel(file2)

        sheet1 = st.selectbox("📄 Select Sheet from File 1", list(xls1.keys()))
        sheet2 = st.selectbox("📄 Select Sheet from File 2", list(xls2.keys()))

        df1 = xls1[sheet1]
        df2 = xls2[sheet2]
            
        col1 = st.selectbox("🔍 Column from File 1", df1.columns)
        col2 = st.selectbox("🔍 Column from File 2", df2.columns)

        df1["__cmp__"] = df1[col1].astype(str).str.lower()
        df2["__cmp__"] = df2[col2].astype(str).str.lower()

        matched_rows = []
        for _, row in df1.iterrows():
            val1 = row["__cmp__"]
            matches = df2[df2["__cmp__"].str.contains(val1, na=False)]
            for _, match_row in matches.iterrows():
                combined = pd.concat([row.drop("__cmp__"), match_row.drop("__cmp__")])
                matched_rows.append(combined)

        if matched_rows:
            result_df = pd.DataFrame(matched_rows)
            st.success(f"✅ {len(result_df)} matches found")
        else:
            st.warning("⚠️ No matches found.")
            result_df = pd.DataFrame()

        if not result_df.empty:
            selected_cols = st.multiselect("📌 Select output columns", result_df.columns.tolist(), default=result_df.columns.tolist())
            final_output = result_df[selected_cols]
            st.dataframe(final_output)

            csv = final_output.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Output CSV", data=csv, file_name="partial_match_output.csv", mime="text/csv")
