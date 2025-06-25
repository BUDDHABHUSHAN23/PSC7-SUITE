import pandas as pd
import streamlit as st

# ✅ Safe to cache: Returns a dictionary of DataFrames (serializable)
@st.cache_data
def load_excel(file):
    return pd.read_excel(file, sheet_name=None)  # Already returns a dict of DataFrames

# ❌ DON'T use ExcelFile object in a cached function
# ❌ This line below is NOT safe because `xls` is not serializable:
# @st.cache_data
# def parse_excel(xls, sheet_name):
#     return xls.parse(sheet_name)

# ✅ Instead, just read the sheet again directly if needed:
@st.cache_data
def load_sheet(file, sheet_name):
    return pd.read_excel(file, sheet_name=sheet_name)

# ✅ Safe to cache
@st.cache_data
def load_csv(file):
    return pd.read_csv(file)
